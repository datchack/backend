from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import os
import time
from datetime import datetime, timezone
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


# ====== ECONOMIC CALENDAR (ForexFactory HTML, PRO) ======
FF_URL = "https://www.forexfactory.com/calendar?week=this"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
ET_TZ = ZoneInfo("America/New_York")
CALENDAR_DISK_CACHE = "/tmp/tt_calendar_cache.json"
_calendar_cache: dict = {"data": [], "ts": 0.0, "next_event_ts": 0.0}


def _load_disk_cache() -> None:
    try:
        if os.path.exists(CALENDAR_DISK_CACHE):
            with open(CALENDAR_DISK_CACHE, "r") as f:
                cached = json.load(f)
            if isinstance(cached, dict) and isinstance(cached.get("data"), list):
                _calendar_cache["data"] = cached["data"]
                _calendar_cache["ts"] = float(cached.get("ts") or 0.0)
                _calendar_cache["next_event_ts"] = float(cached.get("next_event_ts") or 0.0)
    except Exception:
        pass


def _save_disk_cache() -> None:
    try:
        with open(CALENDAR_DISK_CACHE, "w") as f:
            json.dump(_calendar_cache, f)
    except Exception:
        pass


_load_disk_cache()


def _parse_ff_html(html: str) -> list[dict]:
    """
    Parse le HTML ForexFactory et renvoie une liste d'événements
    au format attendu par ton frontend :
    ts, country, impact, title, actual, forecast, previous
    """
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []

    # FF structure typique : lignes avec class "calendar__row"
    rows = soup.select(".calendar__row")
    if not rows:
        return []

    current_date = None  # date du jour courant dans le calendrier

    for row in rows:
        # Certaines lignes sont des séparateurs de jour
        day_cell = row.select_one(".calendar__cell.calendar__date")
        if day_cell and day_cell.get_text(strip=True):
            # Exemple de texte : "Mon Jan 6"
            current_date = day_cell.get_text(strip=True)
            continue

        # On ne parse que les vraies lignes d'événements
        time_cell = row.select_one(".calendar__cell.calendar__time")
        country_cell = row.select_one(".calendar__cell.calendar__country")
        impact_cell = row.select_one(".calendar__cell.calendar__impact")
        event_cell = row.select_one(".calendar__cell.calendar__event")
        actual_cell = row.select_one(".calendar__cell.calendar__actual")
        forecast_cell = row.select_one(".calendar__cell.calendar__forecast")
        previous_cell = row.select_one(".calendar__cell.calendar__previous")

        if not event_cell or not country_cell or not time_cell:
            continue

        title = event_cell.get_text(strip=True)
        if not title:
            continue

        country = country_cell.get_text(strip=True).upper() or "USD"

        impact_text = impact_cell.get_text(strip=True) if impact_cell else ""
        # FF utilise souvent des icônes, on normalise
        if "High" in impact_text:
            impact = "High"
        elif "Medium" in impact_text:
            impact = "Medium"
        elif "Low" in impact_text:
            impact = "Low"
        else:
            impact = "Low"

        time_text = time_cell.get_text(strip=True)
        # Gestion des cas "All Day", "Tentative", etc.
        if time_text.lower() in ("all day", "allday", "tentative", ""):
            hour = 0
            minute = 0
        else:
            try:
                # FF : "2:30pm", "8:00am"
                dt_time = datetime.strptime(time_text.lower().replace(" ", ""), "%I:%M%p")
                hour = dt_time.hour
                minute = dt_time.minute
            except Exception:
                hour = 0
                minute = 0

        # current_date peut être du style "Mon Jan 6"
        if current_date:
            try:
                # On ajoute l'année courante
                year = datetime.now(ET_TZ).year
                dt_day = datetime.strptime(f"{current_date} {year}", "%a %b %d %Y")
            except Exception:
                dt_day = datetime.now(ET_TZ)
        else:
            dt_day = datetime.now(ET_TZ)

        dt = datetime(
            dt_day.year, dt_day.month, dt_day.day,
            hour, minute, tzinfo=ET_TZ
        )
        ts = dt.timestamp()

        def clean(cell):
            if not cell:
                return ""
            return cell.get_text(strip=True) or ""

        actual = clean(actual_cell)
        forecast = clean(forecast_cell)
        previous = clean(previous_cell)

        events.append({
            "title": title,
            "country": country,
            "impact": impact,
            "forecast": forecast,
            "previous": previous,
            "actual": actual,
            "ts": ts,
        })

    events.sort(key=lambda x: x["ts"])
    return events


async def _fetch_calendar() -> list[dict]:
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.forexfactory.com/",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(FF_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
        except Exception:
            return []

    events = _parse_ff_html(html)
    return events


@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    upcoming_ts = _calendar_cache.get("next_event_ts", 0.0)
    cache_age = now - _calendar_cache["ts"]

    # Hot window : event dans ±90s → on rafraîchit plus souvent
    in_hot_window = bool(upcoming_ts and -90 < (upcoming_ts - now) < 120)
    ttl = 10 if in_hot_window else 60

    # Cache encore valide
    if _calendar_cache["data"] and cache_age < ttl:
        return {
            "events": _calendar_cache["data"],
            "cached": True,
            "age": int(cache_age),
            "hot": in_hot_window,
            "stale": False,
        }

    # Sinon, on refetch
    events = await _fetch_calendar()
    if events:
        _calendar_cache["data"] = events
        _calendar_cache["ts"] = now
        # prochain event sans actual
        nxt = next((e["ts"] for e in events if not e.get("actual") and e["ts"] > now), 0.0)
        _calendar_cache["next_event_ts"] = nxt
        _save_disk_cache()
    else:
        _calendar_cache["ts"] = now  # on marque l'heure du dernier essai

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
