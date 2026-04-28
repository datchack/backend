from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import os
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import feedparser
import uvicorn
from bs4 import BeautifulSoup  # pip install beautifulsoup4

app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")

PARIS = ZoneInfo("Europe/Paris")

ALERTS_CRITICAL = [
    "FED", "POWELL", "FOMC", "RATE", "TAUX", "CPI", "NFP", "INFLATION",
    "WAR", "URGENT", "BREAKING", "TRUMP", "GOLD", "XAU", "IRAN", "ISRAEL",
    "ECB", "BOJ", "BOE", "GDP", "RECESSION", "CRASH", "HACK", "ATTACK",
]

NEWS_SOURCES = {
    "INVESTING": "https://www.investing.com/rss/news.rss",
    "REUTERS": "https://news.google.com/rss/search?q=finance+source:reuters&hl=en-US&gl=US&ceid=US:en",
    "FOREXLIVE": "https://www.forexlive.com/feed/news",
    "BLOOMBERG": "https://news.google.com/rss/search?q=markets+source:bloomberg&hl=en-US&gl=US&ceid=US:en",
    "COINDESK": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CNBC": "https://news.google.com/rss/search?q=markets+source:cnbc&hl=en-US&gl=US&ceid=US:en",
}

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30  # secondes


async def _fetch_source(session: aiohttp.ClientSession, name: str, url: str) -> list[dict]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except Exception:
        return []

    try:
        feed = await asyncio.to_thread(feedparser.parse, text)
    except Exception:
        return []

    items: list[dict] = []
    for e in feed.entries[:8]:
        published = getattr(e, "published_parsed", None)
        if not published:
            continue
        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        except Exception:
            continue

        title = getattr(e, "title", "") or ""
        link = getattr(e, "link", "") or ""
        if not title or not link:
            continue

        items.append({
            "s": name,
            "t": title,
            "l": link,
            "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
            "ts": dt.timestamp(),
            "crit": any(k in title.upper() for k in ALERTS_CRITICAL),
        })
    return items


@app.get("/api/news")
async def get_news():
    now = time.time()
    if _news_cache["data"] and (now - _news_cache["ts"]) < NEWS_CACHE_TTL:
        return {
            "items": _news_cache["data"],
            "cached": True,
            "age": int(now - _news_cache["ts"]),
        }

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        results = await asyncio.gather(
            *(_fetch_source(session, n, u) for n, u in NEWS_SOURCES.items())
        )

    all_news = [item for sublist in results for item in sublist]
    all_news.sort(key=lambda x: x["ts"], reverse=True)
    all_news = all_news[:80]

    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return {"items": all_news, "cached": False, "age": 0}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "cached_items": len(_news_cache["data"]),
        "cache_age": int(time.time() - _news_cache["ts"]) if _news_cache["ts"] else None,
    }


# ============================================================
# ===============   ECONOMIC CALENDAR (MyFXBook HTML)   ======
# ============================================================

MYFXBOOK_URL = "https://www.myfxbook.com/forex-economic-calendar"
CALENDAR_CACHE_FILE = "/tmp/tt_calendar_cache.json"

_calendar_cache = {"data": [], "ts": 0.0, "next_event_ts": 0.0}


def _load_calendar_cache():
    try:
        if os.path.exists(CALENDAR_CACHE_FILE):
            with open(CALENDAR_CACHE_FILE, "r") as f:
                data = json.load(f)
            _calendar_cache.update(data)
    except:
        pass


def _save_calendar_cache():
    try:
        with open(CALENDAR_CACHE_FILE, "w") as f:
            json.dump(_calendar_cache, f)
    except:
        pass


_load_calendar_cache()


def _parse_myfxbook_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    # Tableau principal du calendrier
    table = soup.find("table", {"id": "economicCalendarTable"})
    if not table:
        return []

    now_utc = datetime.now(timezone.utc)
    limit_utc = now_utc + timedelta(days=7)

    # Chaque ligne d'événement
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 7:
            continue

        # MyFXBook structure typique :
        # [0]=Date, [1]=Time, [2]=Currency, [3]=Impact, [4]=Event, [5]=Actual, [6]=Forecast, [7]=Previous (parfois)
        date_text = cols[0].get_text(strip=True)
        time_text = cols[1].get_text(strip=True)
        country = cols[2].get_text(strip=True).upper()
        impact = cols[3].get_text(strip=True)
        title = cols[4].get_text(strip=True)
        actual = cols[5].get_text(strip=True) if len(cols) > 5 else ""
        forecast = cols[6].get_text(strip=True) if len(cols) > 6 else ""
        previous = cols[7].get_text(strip=True) if len(cols) > 7 else ""

        if not title or not country:
            continue

        # Impact normalisé
        impact_u = impact.upper()
        if "HIGH" in impact_u:
            impact_norm = "High"
        elif "MEDIUM" in impact_u:
            impact_norm = "Medium"
        elif "LOW" in impact_u:
            impact_norm = "Low"
        else:
            impact_norm = "Low"

        # Date + heure → timestamp (MyFXBook est généralement en GMT)
        try:
            # Exemple de date : "Apr 28, 2026" ou "Apr 28"
            # Exemple de time : "09:00" ou "All Day"
            if time_text.lower() in ("all day", "allday", "tentative", ""):
                hh, mm = 0, 0
            else:
                hh, mm = map(int, time_text.split(":"))

            # Si l'année n'est pas dans le texte, on ajoute l'année courante
            if any(ch.isdigit() for ch in date_text):
                dt_date = datetime.strptime(date_text, "%b %d, %Y")
            else:
                year = datetime.now().year
                dt_date = datetime.strptime(f"{date_text} {year}", "%b %d %Y")

            dt = datetime(dt_date.year, dt_date.month, dt_date.day, hh, mm, tzinfo=timezone.utc)
        except Exception:
            continue

        if not (now_utc <= dt <= limit_utc):
            continue

        events.append({
            "title": title,
            "country": country,
            "impact": impact_norm,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "ts": dt.timestamp(),
        })

    events.sort(key=lambda x: x["ts"])
    return events


async def _fetch_myfxbook():
    url = "https://economic-calendar.tradingview.com/events"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print("Erreur API:", text)
                    return []
                data = await resp.json()
        except Exception as e:
            print("Exception:", e)
            return []

    events = []

    for e in data.get("result", []):
        try:
            ts = int(e.get("timestamp", 0))
            if not ts:
                continue

            events.append({
                "title": e.get("title", ""),
                "country": e.get("country", ""),
                "impact": e.get("importance", "Low"),
                "actual": e.get("actual", ""),
                "forecast": e.get("forecast", ""),
                "previous": e.get("previous", ""),
                "ts": ts,
            })
        except:
            continue

    events.sort(key=lambda x: x["ts"])
    return events


@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    upcoming = _calendar_cache.get("next_event_ts", 0)
    cache_age = now - _calendar_cache["ts"]

    in_hot_window = bool(upcoming and -90 < (upcoming - now) < 120)
    ttl = 10 if in_hot_window else 60

    if _calendar_cache["data"] and cache_age < ttl:
        return {
            "events": _calendar_cache["data"],
            "cached": True,
            "age": int(cache_age),
            "hot": in_hot_window,
            "stale": False,
        }

    events = await _fetch_myfxbook()
    if events:
        _calendar_cache["data"] = events
        _calendar_cache["ts"] = now
        nxt = next((e["ts"] for e in events if not e["actual"] and e["ts"] > now), 0)
        _calendar_cache["next_event_ts"] = nxt
        _save_calendar_cache()
    else:
        _calendar_cache["ts"] = now

    return {
        "events": _calendar_cache["data"],
        "cached": not events,
        "age": int(now - _calendar_cache["ts"]),
        "hot": in_hot_window,
        "stale": not events and bool(_calendar_cache["data"]),
    }


# ====== SERVE INDEX.HTML ======
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
