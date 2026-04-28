from datetime import datetime, timedelta, timezone
import asyncio
import time
from zoneinfo import ZoneInfo

import aiohttp
import feedparser
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

PARIS = ZoneInfo("Europe/Paris")

ALERTS_CRITICAL = [
    "FED", "POWELL", "FOMC", "RATE", "TAUX", "CPI", "NFP", "INFLATION",
    "WAR", "URGENT", "BREAKING", "TRUMP", "GOLD", "XAU", "IRAN", "ISRAEL",
    "ECB", "BOJ", "BOE", "GDP", "RECESSION", "CRASH", "HACK", "ATTACK",
]

NEWS_SOURCES = {
    "INVESTING": {"url": "https://www.investing.com/rss/news.rss", "kind": "rss"},
    "REUTERS": {"url": "https://news.google.com/rss/search?q=finance+source:reuters&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "FOREXLIVE": {"url": "https://www.forexlive.com/feed/news", "kind": "rss"},
    "BLOOMBERG": {"url": "https://news.google.com/rss/search?q=markets+source:bloomberg&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "CNBC": {"url": "https://news.google.com/rss/search?q=markets+source:cnbc&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "FED": {"url": "https://www.federalreserve.gov/feeds/press_monetary.xml", "kind": "rss"},
    "TREASURY": {"url": "https://home.treasury.gov/news/press-releases", "kind": "html_treasury"},
    "DOL": {"url": "https://www.dol.gov/rss/releases.xml", "kind": "rss"},
}

FMP_API_KEY = "JIUCkZ8STWgYWPA03dt64CxksXRVHWyX"
FMP_URL = f"https://financialmodelingprep.com/stable/economic-calendar?country=US&apikey={FMP_API_KEY}"
CALENDAR_TZ = PARIS

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30


def parse_fmp_datetime(raw_date: str) -> datetime | None:
    if not raw_date:
        return None

    candidates = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    )
    for fmt in candidates:
        try:
            return datetime.strptime(raw_date, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def normalize_calendar_event(event: dict) -> dict | None:
    dt = parse_fmp_datetime(event.get("date", ""))
    if not dt:
        return None

    impact_raw = str(event.get("impact", "")).lower()
    if "high" in impact_raw:
        impact = "High"
    elif "medium" in impact_raw:
        impact = "Medium"
    else:
        impact = "Low"

    estimate = event.get("estimate")

    return {
        "title": event.get("event") or "",
        "country": event.get("country") or "US",
        "currency": event.get("currency") or "",
        "impact": impact,
        "actual": event.get("actual"),
        "forecast": estimate,
        "previous": event.get("previous"),
        "unit": event.get("unit"),
        "ts": int(dt.timestamp()),
        "date_utc": dt.isoformat(),
    }


def get_current_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now.astimezone(CALENDAR_TZ) if now else datetime.now(CALENDAR_TZ)
    week_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


def _format_news_item(name: str, title: str, link: str, dt: datetime) -> dict:
    return {
        "s": name,
        "t": title,
        "l": link,
        "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
        "ts": dt.timestamp(),
        "crit": any(keyword in title.upper() for keyword in ALERTS_CRITICAL),
    }


def _parse_rss_items(name: str, text: str) -> list[dict]:
    try:
        feed = feedparser.parse(text)
    except Exception:
        return []

    items: list[dict] = []
    for entry in feed.entries[:8]:
        published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not published:
            continue

        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        except Exception:
            continue

        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""
        if not title or not link:
            continue

        items.append(_format_news_item(name, title, link, dt))

    return items


def _parse_treasury_items(name: str, text: str) -> list[dict]:
    soup = BeautifulSoup(text, "html.parser")
    items: list[dict] = []

    for headline in soup.select("h3.featured-stories__headline")[:8]:
        link_el = headline.find("a", href=True)
        if not link_el:
            continue

        time_el = headline.find_previous("time", class_="datetime")
        if not time_el:
            continue

        raw_dt = time_el.get("datetime", "")
        try:
            dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        except ValueError:
            continue

        title = link_el.get_text(" ", strip=True)
        href = link_el["href"]
        link = href if href.startswith("http") else f"https://home.treasury.gov{href}"

        if not title or not link:
            continue

        items.append(_format_news_item(name, title, link, dt))

    return items


async def _fetch_source(session: aiohttp.ClientSession, name: str, config: dict | str) -> list[dict]:
    if isinstance(config, str):
        url = config
        kind = "rss"
    else:
        url = config.get("url", "")
        kind = config.get("kind", "rss")

    if not url:
        return []

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except Exception:
        return []

    if kind == "html_treasury":
        return await asyncio.to_thread(_parse_treasury_items, name, text)

    return await asyncio.to_thread(_parse_rss_items, name, text)


async def fetch_calendar() -> tuple[list[dict], str | None]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FMP_URL, timeout=20) as resp:
                if resp.status != 200:
                    return [], f"Calendar feed HTTP {resp.status}"
                payload = await resp.json()
        except Exception:
            return [], "Calendar feed unavailable"

    raw_events = payload.get("value", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_events, list):
        return [], "Calendar payload invalid"

    events: list[dict] = []
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        normalized = normalize_calendar_event(event)
        if normalized:
            events.append(normalized)

    week_start, week_end = get_current_week_bounds()
    week_start_ts = int(week_start.timestamp())
    week_end_ts = int(week_end.timestamp())

    filtered_events = [
        event for event in events
        if week_start_ts <= event["ts"] < week_end_ts
    ]
    filtered_events.sort(key=lambda item: item["ts"])
    return filtered_events, None


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
        results = await asyncio.gather(*(_fetch_source(session, name, url) for name, url in NEWS_SOURCES.items()))

    all_news = [item for chunk in results for item in chunk]
    all_news.sort(key=lambda item: item["ts"], reverse=True)
    all_news = all_news[:80]

    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return {"items": all_news, "cached": False, "age": 0}


@app.get("/api/calendar")
async def get_calendar():
    events, error = await fetch_calendar()
    week_start, week_end = get_current_week_bounds()
    if error:
        return {
            "events": [],
            "count": 0,
            "timezone": "Europe/Paris",
            "hot": False,
            "error": error,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }

    now_ts = int(time.time())
    hot = any(0 <= (event["ts"] - now_ts) <= 3600 for event in events)

    return {
        "events": events,
        "count": len(events),
        "timezone": "Europe/Paris",
        "hot": hot,
        "error": None,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "cached_items": len(_news_cache["data"]),
        "cache_age": int(time.time() - _news_cache["ts"]) if _news_cache["ts"] else None,
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
