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
# ===============   ECONOMIC CALENDAR (MyFXBook)   ===========
# ============================================================

MYFXBOOK_URL = "https://www.myfxbook.com/api/get-economic-calendar.json"
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


async def _fetch_myfxbook():
    headers = {
        "User-Agent": "Mozilla/5.0 TradingTerminal",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(MYFXBOOK_URL, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        except:
            return []

    events = data.get("calendar", [])
    if not events:
        return []

    now = datetime.now(timezone.utc)
    limit = now + timedelta(days=7)

    parsed = []
    for e in events:
        try:
            ts = int(e.get("timestamp", 0)) / 1000
        except:
            continue

        dt = datetime.fromtimestamp(ts, timezone.utc)
        if not (now <= dt <= limit):
            continue

        parsed.append({
            "title": e.get("title", ""),
            "country": e.get("country", ""),
            "impact": e.get("impact", ""),
            "actual": e.get("actual", ""),
            "forecast": e.get("forecast", ""),
            "previous": e.get("previous", ""),
            "ts": ts,
        })

    parsed.sort(key=lambda x: x["ts"])
    return parsed


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
