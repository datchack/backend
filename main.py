import asyncio
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import aiohttp
import feedparser
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

PARIS = ZoneInfo("Europe/Paris")

# ============================
#        NEWS SOURCES
# ============================

ALERTS_CRITICAL = [
    "FED", "POWELL", "FOMC", "RATE", "TAUX", "CPI", "NFP", "INFLATION",
    "WAR", "URGENT", "BREAKING", "TRUMP", "GOLD", "XAU", "IRAN", "ISRAEL",
    "ECB", "BOJ", "BOE", "GDP", "RECESSION", "CRASH", "HACK", "ATTACK"
]

NEWS_SOURCES = {
    "INVESTING": "https://www.investing.com/rss/news.rss",
    "REUTERS": "https://news.google.com/rss/search?q=finance+source:reuters&hl=en-US&gl=US&ceid=US:en",
    "FOREXLIVE": "https://www.forexlive.com/feed/news",
    "BLOOMBERG": "https://news.google.com/rss/search?q=markets+source:bloomberg&hl=en-US&gl=US&ceid=US:en",
    "COINDESK": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CNBC": "https://news.google.com/rss/search?q=markets+source:cnbc&hl=en-US&gl=US&ceid=US:en",
}

_news_cache = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30  # seconds


async def _fetch_source(session: aiohttp.ClientSession, name: str, url: str):
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

    items = []
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

    all_news = [item for sub in results for item in sub]
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


# ============================
#     ECONOMIC CALENDAR
# ============================

FINNHUB_API_KEY = "d49nh5hr01qlaebi8n50d49nh5hr01qlaebi8n5g"
FINNHUB_URL = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_API_KEY}"

_calendar_cache = {"data": [], "ts": 0.0}
CAL_TTL = 30  # seconds


async def _fetch_finnhub_calendar():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FINNHUB_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        except Exception:
            return []

    events = data.get("economicCalendar", [])
    out = []

    # Conversion pays → devise
    country_map = {
        "AU": "AUD",
        "NZ": "NZD",
        "CN": "CNY",
        "JP": "JPY",
        "GB": "GBP",
        "EU": "EUR",
        "US": "USD",
        "CA": "CAD",
        "CH": "CHF",
    }

    for e in events:
        try:
            dt = datetime.fromisoformat(e["time"].replace("Z", "+00:00"))
        except Exception:
            continue

        ts = dt.timestamp()

        raw_country = e.get("country", "").upper()
        currency = country_map.get(raw_country, raw_country)

        out.append({
            "title": e.get("event", ""),
            "country": currency,
            "impact": e.get("impact", "Low").capitalize(),
            "forecast": e.get("forecast", ""),
            "previous": e.get("previous", ""),
            "actual": e.get("actual", ""),
            "ts": ts,
        })

    out.sort(key=lambda x: x["ts"])
    return out


@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    cache_age = now - _calendar_cache["ts"]

    if _calendar_cache["data"] and cache_age < CAL_TTL:
        events = _calendar_cache["data"]
        cached = True
    else:
        events = await _fetch_finnhub_calendar()
        if events:
            _calendar_cache["data"] = events
            _calendar_cache["ts"] = now
            cache_age = 0
        cached = False

    hot = False
    for e in events:
        if e.get("actual"):
            continue
        delta = e["ts"] - now
        if -120 <= delta <= 90:
            hot = True
            break

    return {
        "events": events,
        "cached": cached,
        "age": int(cache_age),
        "hot": hot,
    }


# ============================
#   HTML (Bloc 2 viendra ici)
# ============================

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>MDTrading Terminal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <style>
    :root {
      --bg: #05070b;
      --bg-alt: #0b0f18;
      --panel: #101522;
      --panel-soft: #151b2b;
      --border: #222a3d;
      --text: #e5ecff;
      --muted: #7f8aad;
      --accent: #3b82f6;
      --accent-soft: rgba(59,130,246,0.15);
      --buy: #22c55e;
      --sell: #ef4444;
      --warn: #facc15;
      --chip-off: #1f2937;
      --chip-on: #2563eb;
      --chip-on-text: #e5ecff;
      --fresh: #22c55e;
    }

    * {
      box-sizing: border-box;
    }

    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #111827 0, #020617 55%);
      color: var(--text);
    }

    body {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    a {
      color: var(--accent);
      text-decoration: none;
    }

    a:hover {
      text-decoration: underline;
    }

    .app-shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: 12px 12px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    /* HEADER / TOP BAR */

    .top-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .brand-logo {
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: radial-gradient(circle at 30% 20%, #60a5fa, #1d4ed8 55%, #020617 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #e5ecff;
      font-weight: 700;
      font-size: 16px;
      box-shadow: 0 0 18px rgba(37,99,235,0.7);
    }

    .brand-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .brand-title {
      font-size: 17px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .brand-sub {
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .top-right {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 11px;
      color: var(--muted);
    }

    .clock {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 2px;
    }

    .clock-label {
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 10px;
      color: var(--muted);
    }

    .clock-time {
      font-variant-numeric: tabular-nums;
      font-size: 13px;
    }

    .status-pill {
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(15,23,42,0.9);
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
    }

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 10px rgba(34,197,94,0.7);
    }

    /* TICKER */

    .ticker {
      border-radius: 999px;
      border: 1px solid var(--border);
      background: linear-gradient(90deg, rgba(15,23,42,0.95), rgba(15,23,42,0.85));
      padding: 4px 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      overflow: hidden;
      position: relative;
    }

    .ticker-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
      flex-shrink: 0;
    }

    .ticker-sep {
      width: 1px;
      height: 18px;
      background: radial-gradient(circle, #4b5563, transparent);
      flex-shrink: 0;
    }

    .ticker-track {
      display: flex;
      gap: 24px;
      white-space: nowrap;
      animation: ticker-scroll 40s linear infinite;
      font-size: 12px;
      color: var(--muted);
    }

    .ticker-item {
      display: inline-flex;
      align-items: baseline;
      gap: 6px;
    }

    .ticker-sym {
      color: var(--text);
      font-weight: 500;
    }

    .ticker-val {
      font-variant-numeric: tabular-nums;
    }

    .ticker-chg {
      font-variant-numeric: tabular-nums;
    }

    .ticker-chg.up {
      color: var(--buy);
    }

    .ticker-chg.down {
      color: var(--sell);
    }

    @keyframes ticker-scroll {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }

    /* GRID LAYOUT */

    .main-grid {
      display: grid;
      grid-template-columns: minmax(0, 2.1fr) minmax(0, 1.4fr);
      gap: 10px;
      align-items: stretch;
    }

    @media (max-width: 1024px) {
      .main-grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }

    .panel {
      background: radial-gradient(circle at top left, #111827 0, #020617 60%);
      border-radius: 14px;
      border: 1px solid rgba(31,41,55,0.9);
      box-shadow:
        0 18px 40px rgba(0,0,0,0.85),
        0 0 0 1px rgba(15,23,42,0.9);
      padding: 10px 10px 8px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      position: relative;
      overflow: hidden;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid rgba(31,41,55,0.9);
    }

    .panel-title {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .panel-title span.label {
      color: var(--text);
      font-weight: 500;
    }

    .panel-badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 999px;
      border: 1px solid rgba(55,65,81,0.9);
      background: rgba(15,23,42,0.9);
      color: var(--muted);
    }

    .panel-body {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    /* NEWS */

    .news-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 520px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .news-item {
      display: grid;
      grid-template-columns: 52px minmax(0, 1fr);
      gap: 6px;
      padding: 5px 6px;
      border-radius: 8px;
      background: radial-gradient(circle at top left, rgba(15,23,42,0.9), rgba(15,23,42,0.7));
      border: 1px solid rgba(31,41,55,0.9);
      font-size: 12px;
      align-items: center;
    }

    .news-meta {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 11px;
      color: var(--muted);
    }

    .news-time {
      font-variant-numeric: tabular-nums;
    }

    .news-source {
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 10px;
    }

    .news-title a {
      color: var(--text);
      text-decoration: none;
    }

    .news-title a:hover {
      text-decoration: underline;
    }

    .news-item.crit {
      border-color: rgba(248,250,252,0.9);
      box-shadow: 0 0 18px rgba(248,250,252,0.35);
    }

    .news-item.crit .news-title a {
      color: #fefce8;
    }

    .news-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      color: var(--muted);
      padding-top: 2px;
    }

    .news-status {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--buy);
      box-shadow: 0 0 10px rgba(34,197,94,0.7);
    }

    .dot.offline {
      background: var(--sell);
      box-shadow: 0 0 10px rgba(239,68,68,0.7);
    }

    .news-alert {
      color: var(--warn);
    }

    /* CALENDAR */

    .cal-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 11px;
      color: var(--muted);
    }

    .cal-filters {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .cal-chip {
      padding: 3px 7px;
      border-radius: 999px;
      border: 1px solid rgba(55,65,81,0.9);
      background: rgba(15,23,42,0.9);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      cursor: pointer;
      user-select: none;
    }

    .cal-chip.on {
      background: var(--chip-on);
      border-color: rgba(59,130,246,0.9);
      color: var(--chip-on-text);
      box-shadow: 0 0 14px rgba(37,99,235,0.7);
    }

    .cal-chip.sep {
      cursor: default;
      padding-inline: 4px;
      opacity: 0.6;
    }

    .cal-live-pill {
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid rgba(55,65,81,0.9);
      background: rgba(15,23,42,0.9);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .cal-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--buy);
      box-shadow: 0 0 10px rgba(34,197,94,0.7);
    }

    .cal-live-dot.hot {
      background: var(--warn);
      box-shadow: 0 0 10px rgba(250,204,21,0.8);
    }

    .cal-live-dot.offline {
      background: var(--sell);
      box-shadow: 0 0 10px rgba(239,68,68,0.8);
    }

    .cal-container {
      border-radius: 10px;
      background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.85));
      border: 1px solid rgba(31,41,55,0.9);
      padding: 6px 6px 4px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 520px;
      overflow: hidden;
    }

    .cal-scroll {
      overflow-y: auto;
      padding-right: 2px;
    }

    .cal-day {
      margin-top: 6px;
      padding: 4px 4px 3px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: var(--muted);
      border-bottom: 1px solid rgba(31,41,55,0.9);
      position: sticky;
      top: 0;
      background: linear-gradient(to bottom, rgba(15,23,42,0.98), rgba(15,23,42,0.9));
      z-index: 2;
    }

    .cal-row {
      display: grid;
      grid-template-columns: 80px 70px minmax(0, 1.7fr) 80px 80px 80px;
      gap: 6px;
      align-items: center;
      padding: 4px 4px;
      font-size: 11px;
      border-radius: 6px;
      margin-top: 2px;
      background: rgba(15,23,42,0.7);
    }

    .cal-row.past {
      opacity: 0.55;
    }

    .cal-row.due {
      border: 1px solid rgba(250,204,21,0.8);
      box-shadow: 0 0 14px rgba(250,204,21,0.4);
    }

    .cal-row.fresh-result {
      border: 1px solid rgba(34,197,94,0.9);
      box-shadow: 0 0 16px rgba(34,197,94,0.5);
    }

    .cal-time {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-variant-numeric: tabular-nums;
    }

    .cal-countdown {
      font-size: 10px;
      color: var(--muted);
    }

    .cal-countdown.urgent {
      color: var(--warn);
    }

    .cal-flag-wrap {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
    }

    .cal-flag {
      font-size: 16px;
    }

    .cal-ccy {
      font-size: 11px;
      color: var(--muted);
    }

    .cal-title {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }

    .cal-title-text {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .cal-impact {
      display: inline-flex;
      gap: 1px;
    }

    .cal-impact i {
      width: 4px;
      height: 10px;
      border-radius: 999px;
      background: rgba(55,65,81,0.9);
      display: inline-block;
    }

    .cal-impact.high i {
      background: var(--sell);
    }

    .cal-impact.medium i:nth-child(-n+2) {
      background: #f97316;
    }

    .cal-impact.low i:nth-child(1) {
      background: var(--warn);
    }

    .cal-num {
      font-variant-numeric: tabular-nums;
      text-align: right;
    }

    .cal-num.muted {
      color: var(--muted);
    }

    .cal-num.up {
      color: var(--buy);
    }

    .cal-num.down {
      color: var(--sell);
    }

    .cal-empty {
      padding: 10px 6px;
      font-size: 12px;
      color: var(--muted);
    }

    /* FOOT STATUS */

    .foot-status {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 11px;
      color: var(--muted);
      padding-top: 4px;
      border-top: 1px solid rgba(31,41,55,0.9);
      margin-top: 4px;
    }

    .foot-left, .foot-right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .sound-toggle {
      padding: 3px 8px;
      border-radius: 999px;
      border: 1px solid rgba(55,65,81,0.9);
      background: rgba(15,23,42,0.9);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
    }

    .sound-toggle.on {
      border-color: rgba(34,197,94,0.9);
      box-shadow: 0 0 14px rgba(34,197,94,0.5);
    }

    .sound-dot {
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: var(--muted);
    }

    .sound-toggle.on .sound-dot {
      background: var(--buy);
    }

    .small-label {
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 10px;
    }

    .link-muted {
      color: var(--muted);
      text-decoration: none;
    }

    .link-muted:hover {
      color: var(--accent);
      text-decoration: underline;
    }

    /* SCROLLBARS */

    ::-webkit-scrollbar {
      width: 6px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: #1f2937;
      border-radius: 999px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: #374151;
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <!-- TOP BAR -->
    <div class="top-bar">
      <div class="brand">
        <div class="brand-logo">MD</div>
        <div class="brand-text">
          <div class="brand-title">MDTrading Terminal</div>
          <div class="brand-sub">Multi‑asset market dashboard</div>
        </div>
      </div>
      <div class="top-right">
        <div class="clock">
          <div class="clock-label">Paris</div>
          <div class="clock-time" id="clock-paris">--:--:--</div>
        </div>
        <div class="clock">
          <div class="clock-label">New York</div>
          <div class="clock-time" id="clock-ny">--:--:--</div>
        </div>
        <div class="clock">
          <div class="clock-label">Tokyo</div>
          <div class="clock-time" id="clock-tokyo">--:--:--</div>
        </div>
        <div class="status-pill">
          <div class="status-dot" id="health-dot"></div>
          <span id="health-text">Backend: checking…</span>
        </div>
      </div>
    </div>

    <!-- TICKER (statique pour l’instant) -->
    <div class="ticker">
      <div class="ticker-label">Market overview</div>
      <div class="ticker-sep"></div>
      <div class="ticker-track">
        <div class="ticker-item">
          <span class="ticker-sym">EUR/USD</span>
          <span class="ticker-val">1.0724</span>
          <span class="ticker-chg up">+0.18%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">DXY</span>
          <span class="ticker-val">104.32</span>
          <span class="ticker-chg down">-0.12%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">XAU/USD</span>
          <span class="ticker-val">2354.10</span>
          <span class="ticker-chg up">+0.42%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">BTC/USD</span>
          <span class="ticker-val">64210</span>
          <span class="ticker-chg up">+1.85%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">SPX</span>
          <span class="ticker-val">5284</span>
          <span class="ticker-chg down">-0.24%</span>
        </div>

        <!-- duplication pour scroll infini -->
        <div class="ticker-item">
          <span class="ticker-sym">EUR/USD</span>
          <span class="ticker-val">1.0724</span>
          <span class="ticker-chg up">+0.18%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">DXY</span>
          <span class="ticker-val">104.32</span>
          <span class="ticker-chg down">-0.12%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">XAU/USD</span>
          <span class="ticker-val">2354.10</span>
          <span class="ticker-chg up">+0.42%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">BTC/USD</span>
          <span class="ticker-val">64210</span>
          <span class="ticker-chg up">+1.85%</span>
        </div>
        <div class="ticker-item">
          <span class="ticker-sym">SPX</span>
          <span class="ticker-val">5284</span>
          <span class="ticker-chg down">-0.24%</span>
        </div>
      </div>
    </div>

    <!-- MAIN GRID -->
    <div class="main-grid">
      <!-- LEFT: CALENDAR -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="label">Economic calendar</span>
            <span class="panel-badge">Finnhub</span>
          </div>
          <div class="cal-toolbar">
            <div class="cal-filters" id="cal-filters"></div>
            <div class="cal-live-pill">
              <div class="cal-live-dot" id="cal-live-dot"></div>
              <span id="cal-live">LIVE</span>
            </div>
          </div>
        </div>
        <div class="panel-body">
          <div class="cal-container">
            <div class="cal-scroll" id="calendar-content">
              <div class="cal-empty">Chargement du calendrier…</div>
            </div>
          </div>
          <div class="foot-status">
            <div class="foot-left">
              <span class="small-label">Calendar backend</span>
              <span id="cal-meta" class="link-muted">/api/calendar</span>
            </div>
            <div class="foot-right">
              <button class="sound-toggle on" id="sound-toggle">
                <span class="sound-dot"></span>
                <span>Alertes sonores</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT: NEWS -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span class="label">Market news</span>
            <span class="panel-badge">Multi‑sources</span>
          </div>
        </div>
        <div class="panel-body">
          <ul class="news-list" id="news-list">
            <li class="news-item">
              <div class="news-meta">
                <div class="news-time">--:--:--</div>
                <div class="news-source">Loading</div>
              </div>
              <div class="news-title">
                Chargement des dernières actualités de marché…
              </div>
            </li>
          </ul>
          <div class="news-footer">
            <div class="news-status">
              <div class="dot" id="news-dot"></div>
              <span id="news-status-text">/api/news</span>
            </div>
            <div class="news-alert" id="news-alert"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <div class="foot-status">
      <div class="foot-left">
        <span class="small-label">MDTrading Terminal</span>
        <span class="link-muted">Prototype – données Finnhub &amp; flux RSS</span>
      </div>
      <div class="foot-right">
        <span class="small-label">Backend</span>
        <span id="health-meta" class="link-muted">/api/health</span>
      </div>
    </div>
  </div>

  <script>
    /* ============================================================
   CLOCKS
============================================================ */
function updateClocks() {
  const now = new Date();

  const paris = now.toLocaleTimeString("fr-FR", { timeZone: "Europe/Paris" });
  const ny = now.toLocaleTimeString("fr-FR", { timeZone: "America/New_York" });
  const tokyo = now.toLocaleTimeString("fr-FR", { timeZone: "Asia/Tokyo" });

  document.getElementById("clock-paris").textContent = paris;
  document.getElementById("clock-ny").textContent = ny;
  document.getElementById("clock-tokyo").textContent = tokyo;
}
setInterval(updateClocks, 1000);
updateClocks();

/* ============================================================
   HEALTH CHECK
============================================================ */
async function checkHealth() {
  try {
    const r = await fetch("/api/health");
    const j = await r.json();

    document.getElementById("health-dot").classList.remove("offline");
    document.getElementById("health-text").textContent = "Backend OK";
  } catch (e) {
    document.getElementById("health-dot").classList.add("offline");
    document.getElementById("health-text").textContent = "Backend OFFLINE";
  }
}
setInterval(checkHealth, 5000);
checkHealth();

/* ============================================================
   NEWS
============================================================ */
let lastNewsTs = 0;

async function loadNews() {
  try {
    const r = await fetch("/api/news");
    const j = await r.json();

    const list = document.getElementById("news-list");
    list.innerHTML = "";

    j.items.forEach(n => {
      const li = document.createElement("li");
      li.className = "news-item" + (n.crit ? " crit" : "");

      li.innerHTML = `
        <div class="news-meta">
          <div class="news-time">${n.time}</div>
          <div class="news-source">${n.s}</div>
        </div>
        <div class="news-title">
          <a href="${n.l}" target="_blank">${n.t}</a>
        </div>
      `;

      list.appendChild(li);

      if (n.ts > lastNewsTs && n.crit && soundEnabled) {
        ensureAudio();
        beep();
      }
    });

    lastNewsTs = Math.max(...j.items.map(n => n.ts));

    document.getElementById("news-dot").classList.remove("offline");
    document.getElementById("news-status-text").textContent =
      j.cached ? "cached" : "live";
  } catch (e) {
    document.getElementById("news-dot").classList.add("offline");
    document.getElementById("news-status-text").textContent = "offline";
  }
}
setInterval(loadNews, 8000);
loadNews();

/* ============================================================
   SOUND ALERTS
============================================================ */
let soundEnabled = true;
let audioCtx = null;

function ensureAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}

function beep() {
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.frequency.value = 880;
  gain.gain.value = 0.2;
  osc.start();
  setTimeout(() => {
    osc.stop();
  }, 120);
}

document.getElementById("sound-toggle").addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById("sound-toggle");
  if (soundEnabled) btn.classList.add("on");
  else btn.classList.remove("on");
});

/* ============================================================
   ECONOMIC CALENDAR
============================================================ */

const FLAGS = {
  USD: "🇺🇸",
  EUR: "🇪🇺",
  GBP: "🇬🇧",
  JPY: "🇯🇵",
  CHF: "🇨🇭",
  CAD: "🇨🇦",
  AUD: "🇦🇺",
  NZD: "🇳🇿",
  CNY: "🇨🇳",
};

const CCY_LIST = ["USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD","CNY"];
const IMPACTS = ["High","Medium","Low"];

const calFilters = {
  impact: new Set(["High","Medium","Low"]),
  ccy: new Set(["USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD","CNY"]),
};

let calEvents = [];
let calLastSeenActual = new Set();
let calPollTimer = null;
let calFirstLoad = true;

function buildCalToolbar() {
  const root = document.getElementById("cal-filters");
  root.innerHTML = "";

  IMPACTS.forEach(imp => {
    const c = document.createElement("span");
    c.className = "cal-chip" + (calFilters.impact.has(imp) ? " on" : "");
    c.textContent = imp.toUpperCase();
    c.onclick = () => {
      if (calFilters.impact.has(imp)) calFilters.impact.delete(imp);
      else calFilters.impact.add(imp);
      buildCalToolbar();
      renderCalendar();
    };
    root.appendChild(c);
  });

  const sep = document.createElement("span");
  sep.className = "cal-chip sep";
  sep.textContent = "|";
  root.appendChild(sep);

  CCY_LIST.forEach(ccy => {
    const c = document.createElement("span");
    c.className = "cal-chip" + (calFilters.ccy.has(ccy) ? " on" : "");
    c.textContent = ccy;
    c.onclick = () => {
      if (calFilters.ccy.has(ccy)) calFilters.ccy.delete(ccy);
      else calFilters.ccy.add(ccy);
      buildCalToolbar();
      renderCalendar();
    };
    root.appendChild(c);
  });
}

function calToNum(s) {
  if (!s) return null;
  const m = String(s).match(/-?\d+(\.\d+)?/);
  if (!m) return null;
  let n = parseFloat(m[0]);
  const u = s.slice(-1).toUpperCase();
  if (u === "T") n *= 1e12;
  else if (u === "B") n *= 1e9;
  else if (u === "M") n *= 1e6;
  else if (u === "K") n *= 1e3;
  return n;
}

function compareActual(a, f) {
  const A = calToNum(a), F = calToNum(f);
  if (A === null || F === null) return "eq";
  if (A > F) return "up";
  if (A < F) return "down";
  return "eq";
}

function fmtCountdown(secs) {
  if (secs < 0) secs = 0;
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2,"0")}`;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
  }[c]));
}

function renderCalendar() {
  const root = document.getElementById("calendar-content");

  if (!calEvents.length) {
    root.innerHTML = `<div class="cal-empty">Chargement…</div>`;
    return;
  }

  const filtered = calEvents.filter(e =>
    calFilters.impact.has(e.impact) &&
    calFilters.ccy.has(e.country)
  );

  if (!filtered.length) {
    root.innerHTML = `<div class="cal-empty">Aucun événement avec les filtres actuels.</div>`;
    return;
  }

  const now = Date.now() / 1000;
  let html = "";
  let lastDay = "";
  const newFresh = [];

  filtered.forEach(e => {
    const dt = new Date(e.ts * 1000);
    const dayKey = dt.toLocaleDateString("fr-FR", {
      weekday:"long", day:"numeric", month:"long"
    });

    if (dayKey !== lastDay) {
      html += `<div class="cal-day">${dayKey}</div>`;
      lastDay = dayKey;
    }

    const localTime = dt.toLocaleTimeString("fr-FR", {
      hour:"2-digit", minute:"2-digit"
    });

    const flag = FLAGS[e.country] || "🏳️";
    const impClass = e.impact.toLowerCase();
    const isPast = !!e.actual || (e.ts < now - 60);
    const isDue = !e.actual && (e.ts - now) <= 75 && (e.ts - now) >= -10;

    const cmp = e.actual ? compareActual(e.actual, e.forecast) : "eq";
    const fresh = !!e.actual && !calLastSeenActual.has(e.ts) && !calFirstLoad;

    if (e.actual) {
      if (fresh) newFresh.push(e);
      calLastSeenActual.add(e.ts);
    }

    const cls = ["cal-row"];
    if (isPast && !fresh) cls.push("past");
    if (isDue) cls.push("due");
    if (fresh) cls.push("fresh-result");

    let cdHtml = "";
    if (isDue) {
      const secs = Math.max(0, Math.floor(e.ts - now));
      cdHtml = `<span class="cal-countdown${secs < 30 ? " urgent" : ""}" data-cd="${e.ts}">T-${fmtCountdown(secs)}</span>`;
    }

    const actualHtml = e.actual
      ? `<span class="cal-num ${cmp}">${escapeHtml(e.actual)}</span>`
      : `<span class="cal-num muted">—</span>`;

    const forecastHtml = e.forecast
      ? `<span class="cal-num">${escapeHtml(e.forecast)}</span>`
      : `<span class="cal-num muted">—</span>`;

    const previousHtml = e.previous
      ? `<span class="cal-num muted">${escapeHtml(e.previous)}</span>`
      : `<span class="cal-num muted">—</span>`;

    html += `
      <div class="${cls.join(" ")}">
        <span class="cal-time">
          <span>${localTime}</span>
          ${cdHtml}
        </span>
        <span class="cal-flag-wrap">
          <span class="cal-flag">${flag}</span>
          <span class="cal-ccy">${e.country}</span>
        </span>
        <span class="cal-title">
          <span class="cal-impact ${impClass}">
            <i></i><i></i><i></i>
          </span>
          <span class="cal-title-text" title="${escapeHtml(e.title)}">${escapeHtml(e.title)}</span>
        </span>
        ${actualHtml}
        ${forecastHtml}
        ${previousHtml}
      </div>
    `;
  });

  root.innerHTML = html;

  if (!calFirstLoad && newFresh.some(e => e.impact !== "Low") && soundEnabled) {
    ensureAudio();
    beep();
  }

  calFirstLoad = false;
}

function tickCountdowns() {
  const now = Date.now() / 1000;
  let reload = false;

  document.querySelectorAll("[data-cd]").forEach(el => {
    const ts = parseFloat(el.dataset.cd);
    const secs = Math.floor(ts - now);

    if (secs < -2) {
      reload = true;
      return;
    }

    el.textContent = `T-${fmtCountdown(Math.max(0, secs))}`;
    if (secs < 30) el.classList.add("urgent");
  });

  if (reload) fetchCalendar();
}
setInterval(tickCountdowns, 1000);

function nextHotMoment() {
  const now = Date.now() / 1000;
  for (const e of calEvents) {
    if (e.actual) continue;
    if (!calFilters.impact.has(e.impact) || !calFilters.ccy.has(e.country)) continue;
    const d = e.ts - now;
    if (d < -120) continue;
    if (d <= 90) return 0;
    return d - 90;
  }
  return Infinity;
}

function scheduleCalPoll() {
  clearTimeout(calPollTimer);
  const hot = nextHotMoment();
  let delay;

  if (hot === 0) delay = 3000;
  else if (hot < 60) delay = Math.max(2000, hot * 1000);
  else delay = 60000;

  calPollTimer = setTimeout(fetchCalendar, delay);
}

async function fetchCalendar() {
  try {
    const r = await fetch("/api/calendar");
    const j = await r.json();

    calEvents = j.events || [];

    const dot = document.getElementById("cal-live-dot");
    dot.classList.remove("offline", "hot");

    if (j.hot) dot.classList.add("hot");

    renderCalendar();
  } catch (e) {
    const dot = document.getElementById("cal-live-dot");
    dot.classList.add("offline");
  } finally {
    scheduleCalPoll();
  }
}

buildCalToolbar();
fetchCalendar();

  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

