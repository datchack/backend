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
_context_cache: dict = {"data": None, "ts": 0.0}
CONTEXT_CACHE_TTL = 30

MARKET_SYMBOLS = {
    "gold": {"symbol": "GC=F", "label": "GOLD"},
    "silver": {"symbol": "SI=F", "label": "SILVER"},
    "dxy": {"symbol": "DX-Y.NYB", "label": "DXY"},
    "us10y": {"symbol": "^TNX", "label": "US10Y"},
    "oil": {"symbol": "CL=F", "label": "WTI"},
    "spy": {"symbol": "SPY", "label": "SPY"},
    "qqq": {"symbol": "QQQ", "label": "QQQ"},
}


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
    title_upper = title.upper()
    return {
        "s": name,
        "t": title,
        "l": link,
        "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
        "ts": dt.timestamp(),
        "crit": any(keyword in title_upper for keyword in ALERTS_CRITICAL),
        **classify_news_item(name, title_upper),
    }


def classify_news_item(source: str, title_upper: str) -> dict:
    categories = []
    score = 0

    if any(keyword in title_upper for keyword in ("FED", "FOMC", "POWELL", "RATE", "MONETARY POLICY")):
        categories.append("FED")
        score += 5
    if any(keyword in title_upper for keyword in ("CPI", "PCE", "NFP", "PAYROLLS", "INFLATION", "UNEMPLOYMENT", "JOBLESS", "GDP", "PMI", "RETAIL SALES")):
        categories.append("MACRO")
        score += 4
    if any(keyword in title_upper for keyword in ("IRAN", "ISRAEL", "GAZA", "UKRAINE", "RUSSIA", "CHINA", "MISSILE", "ATTACK", "SANCTION", "WAR", "OIL")):
        categories.append("GEO")
        score += 4
    if any(keyword in title_upper for keyword in ("GOLD", "XAU", "BULLION", "TREASURY YIELD", "DOLLAR")):
        categories.append("XAU")
        score += 3
    if source in {"FED", "TREASURY", "DOL"}:
        categories.append("OFFICIAL")
        score += 2

    if not categories:
        categories.append("MARKETS")
        score += 1

    if score >= 7:
        priority = "high"
    elif score >= 4:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "tags": list(dict.fromkeys(categories)),
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


async def fetch_market_snapshot(session: aiohttp.ClientSession, symbol: str) -> dict | None:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
    except Exception:
        return None

    try:
        result = payload["chart"]["result"][0]
        meta = result["meta"]
    except (KeyError, IndexError, TypeError):
        return None

    current = meta.get("regularMarketPrice")
    previous = meta.get("chartPreviousClose")
    if current is None or previous in (None, 0):
        return None

    change = current - previous
    change_pct = (change / previous) * 100

    return {
        "symbol": symbol,
        "price": round(float(current), 4),
        "previous_close": round(float(previous), 4),
        "change": round(float(change), 4),
        "change_pct": round(float(change_pct), 3),
        "high": meta.get("regularMarketDayHigh"),
        "low": meta.get("regularMarketDayLow"),
        "time": meta.get("regularMarketTime"),
    }


def build_gold_context(markets: dict[str, dict]) -> dict:
    gold = markets.get("gold")
    dxy = markets.get("dxy")
    us10y = markets.get("us10y")
    oil = markets.get("oil")
    spy = markets.get("spy")
    qqq = markets.get("qqq")

    score = 0
    drivers = []

    if dxy:
        impact = 1 if dxy["change_pct"] < 0 else -1 if dxy["change_pct"] > 0 else 0
        score += impact
        drivers.append({
            "key": "dxy",
            "label": "Dollar",
            "value": dxy["price"],
            "change_pct": dxy["change_pct"],
            "bias": "bullish" if impact > 0 else "bearish" if impact < 0 else "neutral",
            "note": "Dollar down helps gold" if impact > 0 else "Dollar up pressures gold" if impact < 0 else "Dollar flat",
        })

    if us10y:
        impact = 1 if us10y["change_pct"] < 0 else -1 if us10y["change_pct"] > 0 else 0
        score += impact
        drivers.append({
            "key": "us10y",
            "label": "US10Y",
            "value": us10y["price"],
            "change_pct": us10y["change_pct"],
            "bias": "bullish" if impact > 0 else "bearish" if impact < 0 else "neutral",
            "note": "Yields down supports gold" if impact > 0 else "Yields up pressures gold" if impact < 0 else "Yields flat",
        })

    if oil:
        impact = 1 if oil["change_pct"] > 0.4 else -1 if oil["change_pct"] < -0.4 else 0
        score += impact
        drivers.append({
            "key": "oil",
            "label": "WTI",
            "value": oil["price"],
            "change_pct": oil["change_pct"],
            "bias": "bullish" if impact > 0 else "bearish" if impact < 0 else "neutral",
            "note": "Energy stress can lift gold" if impact > 0 else "Oil easing cools stress" if impact < 0 else "Oil steady",
        })

    risk_change = None
    if spy and qqq:
        risk_change = (spy["change_pct"] + qqq["change_pct"]) / 2
        impact = 1 if risk_change < -0.35 else -1 if risk_change > 0.35 else 0
        score += impact
        drivers.append({
            "key": "risk",
            "label": "Risk",
            "value": round(risk_change, 3),
            "change_pct": round(risk_change, 3),
            "bias": "bullish" if impact > 0 else "bearish" if impact < 0 else "neutral",
            "note": "Equities under pressure" if impact > 0 else "Risk appetite firm" if impact < 0 else "Risk mixed",
        })

    if score >= 2:
        bias = "Bullish"
        tone = "supportive"
    elif score <= -2:
        bias = "Bearish"
        tone = "defensive"
    else:
        bias = "Neutral"
        tone = "balanced"

    session_flags = {
        "asia": datetime.now(PARIS).hour < 8,
        "london": 8 <= datetime.now(PARIS).hour < 14,
        "ny_overlap": 14 <= datetime.now(PARIS).hour < 17,
        "ny_pm": 17 <= datetime.now(PARIS).hour < 22,
    }
    if session_flags["ny_overlap"]:
        active_session = "LONDON / NEW YORK"
        volatility = "HIGH"
    elif session_flags["ny_pm"]:
        active_session = "NEW YORK"
        volatility = "ELEVATED"
    elif session_flags["london"]:
        active_session = "LONDON"
        volatility = "ACTIVE"
    else:
        active_session = "ASIA"
        volatility = "QUIET"

    return {
        "bias": bias,
        "score": score,
        "tone": tone,
        "volatility": volatility,
        "session": active_session,
        "drivers": drivers,
        "watchlist": [
            {"key": key, "label": cfg["label"], **markets[key]}
            for key, cfg in MARKET_SYMBOLS.items()
            if key in markets
        ],
        "gold": gold,
    }


async def fetch_xau_context() -> dict:
    now = time.time()
    if _context_cache["data"] and (now - _context_cache["ts"]) < CONTEXT_CACHE_TTL:
        return _context_cache["data"]

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        snapshots = await asyncio.gather(*(
            fetch_market_snapshot(session, cfg["symbol"])
            for cfg in MARKET_SYMBOLS.values()
        ))

    markets = {
        key: snapshot
        for (key, _cfg), snapshot in zip(MARKET_SYMBOLS.items(), snapshots)
        if snapshot
    }
    context = build_gold_context(markets)
    _context_cache["data"] = context
    _context_cache["ts"] = now
    return context


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


@app.get("/api/context")
async def get_context():
    context = await fetch_xau_context()
    return context


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
