from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import aiohttp
import feedparser
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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


# ====== ECONOMIC CALENDAR (Forex Factory weekly feed — JSON primary, XML fallback) ======
CALENDAR_JSON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_XML_URL  = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
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


def _parse_ff_xml(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []
    out: list[dict] = []
    for ev in root.findall("event"):
        def g(tag: str) -> str:
            el = ev.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        date_s = g("date")     # "04-26-2026"
        time_s = g("time")     # "8:00pm" / "All Day" / "Tentative"
        if not date_s:
            continue
        try:
            month, day, year = [int(x) for x in date_s.split("-")]
        except Exception:
            continue
        time_norm = time_s.lower().replace(" ", "")
        if time_norm in ("", "allday", "tentative"):
            dt = datetime(year, month, day, 0, 0, tzinfo=ET_TZ)
        else:
            try:
                dt = datetime.strptime(time_norm, "%I:%M%p").replace(
                    year=year, month=month, day=day, tzinfo=ET_TZ
                )
            except Exception:
                dt = datetime(year, month, day, 0, 0, tzinfo=ET_TZ)
        out.append({
            "title": g("title"),
            "country": g("country").upper(),
            "impact": (g("impact") or "Low").capitalize(),
            "forecast": g("forecast"),
            "previous": g("previous"),
            "actual": g("actual"),
            "ts": dt.timestamp(),
        })
    out.sort(key=lambda x: x["ts"])
    return out


def _parse_ff_json(data: list) -> list[dict]:
    out: list[dict] = []
    for e in data:
        try:
            dt = datetime.fromisoformat(e["date"])
            ts = dt.timestamp()
        except Exception:
            continue
        out.append({
            "title": e.get("title", "") or "",
            "country": (e.get("country", "") or "").upper(),
            "impact": (e.get("impact", "") or "Low").capitalize(),
            "forecast": e.get("forecast", "") or "",
            "previous": e.get("previous", "") or "",
            "actual": e.get("actual", "") or "",
            "ts": ts,
        })
    out.sort(key=lambda x: x["ts"])
    return out


async def _fetch_calendar() -> list[dict]:
    headers = {"User-Agent": BROWSER_UA, "Accept": "application/json, text/xml, */*"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # Try JSON first (richer / native ISO dates)
        try:
            async with session.get(CALENDAR_JSON_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    parsed = _parse_ff_json(data)
                    if parsed:
                        return parsed
        except Exception:
            pass
        # Fallback to XML when JSON is unavailable / rate-limited
        try:
            async with session.get(CALENDAR_XML_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                raw = await resp.read()
                txt = raw.decode("windows-1252", errors="replace")
                return _parse_ff_xml(txt)
        except Exception:
            return []


@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    upcoming_ts = _calendar_cache.get("next_event_ts", 0.0)
    cache_age = now - _calendar_cache["ts"]
    # Adaptive cache: 10s when an event is between -90s and +120s of now, else 60s
    in_hot_window = bool(upcoming_ts and -90 < (upcoming_ts - now) < 120)
    ttl = 10 if in_hot_window else 60

    if _calendar_cache["data"] and cache_age < ttl:
        return {"events": _calendar_cache["data"], "cached": True, "age": int(cache_age), "hot": in_hot_window}

    events = await _fetch_calendar()
    if events:
        _calendar_cache["data"] = events
        _calendar_cache["ts"] = now
        nxt = next((e["ts"] for e in events if not e["actual"] and e["ts"] > now), 0.0)
        _calendar_cache["next_event_ts"] = nxt
        _save_disk_cache()
    else:
        # Source unreachable / rate-limited → keep serving last known data, mark TS
        # so we don't keep hammering it within the same TTL.
        _calendar_cache["ts"] = now
    return {
        "events": _calendar_cache["data"],
        "cached": not events,
        "age": int(now - _calendar_cache["ts"]) if events else 0,
        "hot": in_hot_window,
        "stale": not events and bool(_calendar_cache["data"]),
    }





@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
