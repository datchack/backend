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

FMP_API_KEY = "JIUCkZ8STWgYWPA03dt64CxksXRVHWyX"
FMP_URL = f"https://financialmodelingprep.com/stable/economic-calendar?country=US&apikey={FMP_API_KEY}"


@app.get("/api/calendar")
async def get_calendar():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FMP_URL, timeout=10) as resp:
                data = await resp.json()

        events = []

        for e in data:
            try:
                # ⚠️ FMP renvoie souvent "2026-04-28 14:30:00"
                dt = datetime.fromisoformat(e["date"])

                impact_raw = (e.get("impact") or "").lower()

                if "high" in impact_raw:
                    impact = "High"
                elif "medium" in impact_raw:
                    impact = "Medium"
                else:
                    impact = "Low"

                events.append({
                    "title": e.get("event", ""),
                    "country": e.get("country", "US"),
                    "impact": impact,
                    "actual": e.get("actual", ""),
                    "forecast": e.get("forecast", ""),
                    "previous": e.get("previous", ""),
                    "ts": dt.timestamp()
                })

            except:
                continue

        # 🔥 TRI IMPORTANT
        events.sort(key=lambda x: x["ts"])

        return {
            "events": events,
            "count": len(events)
        }

    except Exception as e:
        return {
            "events": [],
            "error": str(e)
        }


async def _fetch_calendar():
    API_KEY = "JIUCkZ8STWgYWPA03dt64CxksXRVHWyX"
    url = f"https://financialmodelingprep.com/stable/economic-calendar?country=US&apikey={API_KEY}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=20) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        except Exception as e:
            print("Request error:", e)
            return []

    events = []

    for e in data:
        try:
            raw_date = e.get("date", "")

            # 🔥 FIX IMPORTANT : gestion multi-format
            dt = None
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d"
            ):
                try:
                    dt = datetime.strptime(raw_date, fmt)
                    break
                except:
                    continue

            if not dt:
                continue

            ts = int(dt.replace(tzinfo=timezone.utc).timestamp())

            impact_raw = str(e.get("impact", "")).lower()

            if "high" in impact_raw:
                impact = "High"
            elif "medium" in impact_raw:
                impact = "Medium"
            else:
                impact = "Low"

            events.append({
                "title": e.get("event", ""),
                "country": e.get("country", "US"),
                "impact": impact,
                "actual": e.get("actual", ""),
                "forecast": e.get("forecast", ""),   # ✅ FIX ICI
                "previous": e.get("previous", ""),
                "ts": ts,
            })

        except:
            continue

    # 🔥 TRI GARANTI
    events.sort(key=lambda x: x["ts"])

    return events

# ====== SERVE INDEX.HTML ======
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
