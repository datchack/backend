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


# ====== ECONOMIC CALENDAR (Finnhub API) ======

FINNHUB_API_KEY = "d49nh5hr01qlaebi8n50d49nh5hr01qlaebi8n5g"
FINNHUB_URL = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_API_KEY}"

_calendar_cache = {"data": [], "ts": 0.0}
CAL_TTL = 30  # rafraîchit toutes les 30 secondes


async def _fetch_finnhub_calendar() -> dict:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FINNHUB_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
        except Exception:
            return {}

    events = data.get("economicCalendar", [])
    grouped = {}

    for e in events:
        # Convert timestamp
        try:
            dt = datetime.fromisoformat(e["time"].replace("Z", "+00:00"))
        except Exception:
            continue

        date_key = dt.strftime("%Y-%m-%d")
        ts = dt.timestamp()

        item = {
            "title": e.get("event", ""),
            "country": e.get("country", "").upper(),
            "impact": e.get("impact", "Low").capitalize(),
            "forecast": e.get("forecast", ""),
            "previous": e.get("previous", ""),
            "actual": e.get("actual", ""),
            "ts": ts,
        }

        if date_key not in grouped:
            grouped[date_key] = []

        grouped[date_key].append(item)

    # Tri par timestamp dans chaque journée
    for d in grouped:
        grouped[d].sort(key=lambda x: x["ts"])

    return grouped



@app.get("/api/calendar")
async def get_calendar():
    now = time.time()
    cache_age = now - _calendar_cache["ts"]

    if _calendar_cache["data"] and cache_age < CAL_TTL:
        return {
            "days": _calendar_cache["data"],
            "cached": True,
            "age": int(cache_age),
        }

    days = await _fetch_finnhub_calendar()

    if days:
        _calendar_cache["data"] = days
        _calendar_cache["ts"] = now

    return {
        "days": _calendar_cache["data"],
        "cached": False,
        "age": 0,
    }




INDEX_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TERMINAL HAUTE FRÉQUENCE</title>
    <style>
        :root {
            --bg: #05070a;
            --panel: #0d1015;
            --card: #111419;
            --card-2: #161b22;
            --border: #1e2229;
            --border-hot: #2a2f3a;
            --text: #e6e8ee;
            --muted: #6b7280;
            --accent: #a259ff;
            --warn: #ffcc00;
            --buy: #00f2ad;
            --sell: #ff4d6d;
            --info: #4facfe;
        }

        * { box-sizing: border-box; }
        html, body { margin: 0; padding: 0; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
            overflow-x: hidden;
            font-size: 13px;
        }

        /* === TICKER TAPE === */
        .ticker-tape {
            border-bottom: 1px solid var(--border);
            background: #06080c;
            height: 46px;
        }

        /* === TOP BAR (command + clocks) === */
        .top-bar {
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
            padding: 6px;
            border-bottom: 1px solid var(--border);
            background: var(--panel);
        }
        @media (min-width: 900px) {
            .top-bar { grid-template-columns: 1.2fr 2fr; }
        }

        .cmd-bar {
            display: flex;
            align-items: center;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 0 10px;
            height: 38px;
        }
        .cmd-bar .prompt {
            color: var(--accent);
            font-family: "Courier New", monospace;
            font-weight: 900;
            margin-right: 8px;
            font-size: 13px;
        }
        .cmd-bar input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text);
            font-family: "Courier New", monospace;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .cmd-bar input::placeholder { color: var(--muted); text-transform: none; letter-spacing: 0; }
        .cmd-bar .hint { color: var(--muted); font-size: 10px; margin-left: 8px; white-space: nowrap; }

        .clocks {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
        }
        .clock {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 5px 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            min-width: 0;
        }
        .clock .city {
            font-size: 10px;
            font-weight: 800;
            color: var(--muted);
            letter-spacing: 0.5px;
        }
        .clock .time {
            font-family: "Courier New", monospace;
            color: var(--text);
            font-size: 13px;
        }
        .clock .dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--muted);
            margin-right: 6px;
            display: inline-block;
        }
        .clock.open .dot { background: var(--buy); box-shadow: 0 0 6px var(--buy); }

        /* === HEADER QUOTES (8 cards, 4 cols) === */
        .header {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
            padding: 6px;
        }
        @media (min-width: 700px) { .header { grid-template-columns: repeat(4, 1fr); } }
        @media (min-width: 1300px) { .header { grid-template-columns: repeat(8, 1fr); } }

        .qcard {
            position: relative;
            background: var(--card);
            border-radius: 4px;
            border: 1px solid var(--border);
            overflow: hidden;
            height: 78px;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .qcard:hover { border-color: var(--border-hot); }
        .qcard.active {
            border-color: var(--accent);
            box-shadow: 0 0 10px rgba(162, 89, 255, 0.25);
        }
        .click-overlay {
            position: absolute; inset: 0; z-index: 10; cursor: pointer;
        }

        /* === MAIN GRID === */
        .main-layout {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 0 6px 6px;
        }
        @media (min-width: 1024px) {
            .main-layout {
                flex-direction: row;
                height: calc(100vh - 280px);
                min-height: 480px;
            }
        }

        .col {
            background: var(--card);
            border-radius: 4px;
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .col-left   { flex: 1.5; min-height: 460px; height: 460px; }
        .col-center { flex: 3.2; min-height: 480px; height: 480px; }
        .col-right  { flex: 1.5; min-height: 380px; height: 380px; }
        @media (min-width: 1024px) {
            .col-left, .col-center, .col-right { height: auto; min-height: 0; }
        }

        .p-header {
            padding: 7px 12px;
            background: var(--card-2);
            font-size: 10px;
            font-weight: 900;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--muted);
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }
        .p-header .live {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            color: var(--buy);
            font-size: 10px;
        }
        .p-header .live::before {
            content: "";
            width: 6px; height: 6px; border-radius: 50%;
            background: var(--buy);
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .scroll {
            flex: 1;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }

        /* === NEWS === */
        .n-item {
            padding: 9px 12px;
            border-bottom: 1px solid #161b22;
            font-size: 12.5px;
            border-left: 3px solid transparent;
            transition: background 0.4s;
        }
        .n-item.critical {
            border-left-color: var(--warn);
            background: rgba(255, 204, 0, 0.05);
        }
        .n-item.fresh {
            animation: flash 1.6s ease-out;
        }
        @keyframes flash {
            0%   { background: rgba(162, 89, 255, 0.35); }
            100% { background: transparent; }
        }
        .n-item.critical.fresh {
            animation: flash-crit 1.6s ease-out;
        }
        @keyframes flash-crit {
            0%   { background: rgba(255, 204, 0, 0.4); }
            100% { background: rgba(255, 204, 0, 0.05); }
        }
        .n-meta {
            font-size: 10px;
            color: var(--muted);
            margin-bottom: 4px;
            font-weight: 700;
            display: flex;
            gap: 6px;
            align-items: center;
        }
        .tag {
            font-size: 9px;
            padding: 1px 5px;
            border-radius: 2px;
            border: 1px solid currentColor;
            font-weight: 900;
            letter-spacing: 0.4px;
        }
        .INVESTING { color: #ffa726; }
        .REUTERS   { color: #4facfe; }
        .FOREXLIVE { color: #00f2ad; }
        .BLOOMBERG { color: #ff7849; }
        .COINDESK  { color: #f7931a; }
        .CNBC      { color: #d946ef; }

        .n-item a {
            color: #efefef;
            text-decoration: none;
            line-height: 1.4;
            display: block;
        }
        .n-item a:hover { color: var(--accent); }

        /* === STATUS BAR === */
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 10px;
            background: var(--panel);
            border-top: 1px solid var(--border);
            font-size: 10px;
            color: var(--muted);
            font-family: "Courier New", monospace;
            letter-spacing: 0.4px;
            min-height: 24px;
            flex-wrap: wrap;
            gap: 6px;
        }
        .status-bar .ok { color: var(--buy); }
        .status-bar .warn { color: var(--warn); }
        .status-bar .err { color: var(--sell); }

        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-thumb { background: #2a2f3a; border-radius: 2px; }
        ::-webkit-scrollbar-track { background: transparent; }

        /* === ECONOMIC CALENDAR === */
        .cal-toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 3px;
            padding: 5px 6px;
            background: var(--card-2);
            border-bottom: 1px solid var(--border);
        }
        .cal-chip {
            padding: 2px 5px;
            border-radius: 3px;
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--muted);
            cursor: pointer;
            user-select: none;
            font-weight: 800;
            font-size: 9px;
            letter-spacing: 0.3px;
            transition: all 0.15s;
        }
        .cal-chip:hover { border-color: var(--border-hot); color: var(--text); }
        .cal-chip.on {
            background: rgba(162, 89, 255, 0.18);
            border-color: var(--accent);
            color: #e6e8ee;
        }
        .cal-chip.sep {
            border: none;
            background: transparent;
            color: var(--muted);
            cursor: default;
            padding: 3px 2px;
        }
        .cal-head-row, .cal-row {
            display: grid;
            grid-template-columns: 44px 24px 1fr 50px 50px 50px;
            gap: 4px;
            padding: 6px 6px;
            align-items: center;
        }
        .cal-head-row {
            background: var(--panel);
            border-bottom: 1px solid var(--border);
            font-size: 9px;
            color: var(--muted);
            font-weight: 900;
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }
        .cal-day {
            position: sticky;
            top: 0;
            background: #161b22;
            color: #e6e8ee;
            font-size: 10px;
            font-weight: 900;
            padding: 6px 10px;
            letter-spacing: 1px;
            border-bottom: 1px solid var(--border);
            border-top: 1px solid var(--border);
            z-index: 5;
            text-transform: uppercase;
        }
        .cal-row {
            border-bottom: 1px solid #161b22;
            font-size: 11.5px;
            transition: background 0.4s;
        }
        .cal-row.past { opacity: 0.55; }
        .cal-row.due {
            background: rgba(255, 204, 0, 0.08);
            border-left: 3px solid var(--warn);
            padding-left: 5px;
        }
        .cal-row.fresh-result { animation: cal-flash 2.4s ease-out; }
        @keyframes cal-flash {
            0%   { background: rgba(0, 242, 173, 0.4); }
            100% { background: transparent; }
        }
        .cal-time {
            font-family: "Courier New", monospace;
            color: var(--muted);
            font-size: 11px;
            display: flex;
            flex-direction: column;
            line-height: 1.2;
        }
        .cal-row.due .cal-time > span:first-child { color: var(--warn); font-weight: 900; }
        .cal-flag-wrap { text-align: center; line-height: 1; }
        .cal-flag { font-size: 14px; }
        .cal-ccy { font-size: 8px; color: var(--muted); display: block; margin-top: 2px; letter-spacing: 0.3px; }
        .cal-title {
            display: flex;
            align-items: center;
            gap: 6px;
            min-width: 0;
            color: var(--text);
        }
        .cal-title-text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .cal-impact {
            display: inline-flex;
            gap: 2px;
            flex-shrink: 0;
        }
        .cal-impact i {
            width: 5px; height: 5px; border-radius: 50%;
            background: #2a2f3a;
            display: inline-block;
        }
        .cal-impact.high   i:nth-child(-n+3) { background: #ff4d6d; }
        .cal-impact.medium i:nth-child(-n+2) { background: #ffa726; }
        .cal-impact.low    i:nth-child(-n+1) { background: #ffd54f; }
        .cal-num {
            font-family: "Courier New", monospace;
            font-size: 11px;
            color: var(--text);
            text-align: right;
        }
        .cal-num.muted { color: var(--muted); }
        .cal-num.up    { color: var(--buy);  font-weight: 900; }
        .cal-num.down  { color: var(--sell); font-weight: 900; }
        .cal-countdown {
            display: inline-block;
            margin-top: 2px;
            padding: 1px 4px;
            background: rgba(255, 204, 0, 0.18);
            color: var(--warn);
            border-radius: 2px;
            font-family: "Courier New", monospace;
            font-weight: 900;
            font-size: 10px;
            letter-spacing: 0.5px;
        }
        .cal-countdown.urgent {
            background: rgba(255, 77, 109, 0.28);
            color: var(--sell);
            animation: pulse 0.8s ease-in-out infinite;
        }
        .cal-empty { padding: 24px 12px; text-align: center; color: var(--muted); font-size: 11px; }
    </style>
</head>
<body>

    <!-- TICKER TAPE -->
    <div class="ticker-tape">
        <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
            {
              "symbols": [
                {"proName": "OANDA:XAUUSD", "title": "XAU/USD"},
                {"proName": "OANDA:XAGUSD", "title": "SILVER"},
                {"proName": "TVC:USOIL", "title": "OIL"},
                {"proName": "CAPITALCOM:DXY", "title": "DXY"},
                {"proName": "NASDAQ:TLT", "title": "US10Y"},
                {"proName": "NASDAQ:QQQ", "title": "NASDAQ"},
                {"proName": "AMEX:SPY", "title": "S&P 500"}
              ],
              "showSymbolLogo": false,
              "isTransparent": true,
              "displayMode": "regular",
              "colorTheme": "dark",
              "locale": "fr"
            }
            </script>
        </div>
    </div>

    <!-- TOP BAR : COMMAND + WORLD CLOCKS -->
    <div class="top-bar">
        <div class="cmd-bar">
            <span class="prompt">&gt;</span>
            <input id="cmd" type="text" placeholder="Saisir un symbole (ex: NASDAQ:AAPL, BINANCE:SOLUSDT, FX:EURJPY) puis Entrée…" autocomplete="off" spellcheck="false">
            <span class="hint">↵ pour charger</span>
        </div>
        <div class="clocks">
            <div class="clock" id="mk-NY"><span><span class="dot"></span><span class="city">NEW YORK</span></span><span class="time" id="time-NY">--:--:--</span></div>
            <div class="clock" id="mk-LDN"><span><span class="dot"></span><span class="city">LONDON</span></span><span class="time" id="time-LDN">--:--:--</span></div>
            <div class="clock" id="mk-TKY"><span><span class="dot"></span><span class="city">TOKYO</span></span><span class="time" id="time-TKY">--:--:--</span></div>
            <div class="clock" id="mk-SYD"><span><span class="dot"></span><span class="city">SYDNEY</span></span><span class="time" id="time-SYD">--:--:--</span></div>
        </div>
    </div>

    <!-- QUOTE GRID (8 cards) -->
    <div class="header">
        <div class="qcard active" data-symbol="OANDA:XAUUSD">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "OANDA:XAUUSD", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="OANDA:XAGUSD">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "OANDA:XAGUSD", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="CAPITALCOM:DXY">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "CAPITALCOM:DXY", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="TVC:USOIL">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "TVC:USOIL", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="FX:EURUSD">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "FX:EURUSD", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="NASDAQ:TLT">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "NASDAQ:TLT", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="AMEX:SPY">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "AMEX:SPY", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
        <div class="qcard" data-symbol="BINANCE:BTCUSDT">
            <div class="click-overlay"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-single-quote.js" async>
            {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": true, "locale": "fr", "width": "100%"}
            </script>
        </div>
    </div>

    <!-- MAIN PANELS -->
    <div class="main-layout">
        <div class="col col-left">
            <div class="p-header">
                <span>📅 CALENDRIER ÉCONOMIQUE</span>
                <span class="live" id="cal-live">LIVE</span>
            </div>
            <div class="cal-toolbar" id="cal-filters"></div>
            <div class="cal-head-row">
                <span>HEURE</span>
                <span></span>
                <span>ÉVÉNEMENT</span>
                <span style="text-align:right;">ACTUEL</span>
                <span style="text-align:right;">PRÉV.</span>
                <span style="text-align:right;">PRÉC.</span>
            </div>
            <div id="calendar-content" class="scroll"></div>
        </div>
        <div class="col col-center" id="chart_container">
            <div class="p-header"><span id="chart-symbol">— CHART —</span><span class="live">LIVE</span></div>
            <div id="tv_main_wrap" style="flex:1; min-height:0;"></div>
        </div>
        <div class="col col-right">
            <div class="p-header"><span>🚨 FIL INFO MULTI-SOURCE</span><span class="live">LIVE</span></div>
            <div id="news-content" class="scroll"></div>
        </div>
    </div>

    <!-- STATUS BAR -->
    <div class="status-bar">
        <span>● <span class="ok">CONNECTED</span> · 6 sources RSS · cache 30s</span>
        <span id="status-news">News: —</span>
        <span id="status-sound" style="cursor:pointer;user-select:none;" title="Activer/couper le son sur nouvelles">🔇 SOUND OFF</span>
        <select id="sound-pick" title="Choisir le son d'alerte" style="background:#0a0a0a;color:#e7e7e7;border:1px solid #2a2a2a;font-family:inherit;font-size:11px;padding:1px 4px;cursor:pointer;">
            <option value="ping">PING</option>
            <option value="chime" selected>CHIME</option>
            <option value="siren">SIREN</option>
            <option value="bloop">BLOOP</option>
            <option value="alert">ALERT</option>
        </select>
        <span id="status-clock">--:--:--</span>
    </div>

    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>
        // ====== STATE + PERSISTENCE ======
        const PREFS_KEY = 'tt_prefs_v1';
        function loadPrefs() {
            try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; }
            catch (e) { return {}; }
        }
        function savePrefs(patch) {
            try {
                const cur = loadPrefs();
                const next = Object.assign({}, cur, patch);
                localStorage.setItem(PREFS_KEY, JSON.stringify(next));
            } catch (e) {}
        }
        const PREFS = loadPrefs();

        let lastSeenTs = 0;
        let currentSymbol = PREFS.symbol || "OANDA:XAUUSD";
        let soundEnabled = !!PREFS.soundEnabled;
        let soundType = PREFS.soundType || 'chime';
        let audioCtx = null;

        // ====== AUDIO ALERT ======
        function ensureAudio() {
            if (!audioCtx) {
                try {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                } catch (e) { audioCtx = null; }
            }
            if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        }
        function tone(freq, startOffset, duration, peak, type) {
            const now = audioCtx.currentTime;
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = type || 'sine';
            o.frequency.value = freq;
            g.gain.setValueAtTime(0.0001, now + startOffset);
            g.gain.exponentialRampToValueAtTime(peak, now + startOffset + 0.01);
            g.gain.exponentialRampToValueAtTime(0.0001, now + startOffset + duration);
            o.connect(g).connect(audioCtx.destination);
            o.start(now + startOffset);
            o.stop(now + startOffset + duration + 0.02);
        }
        function playSound(kind) {
            if (!audioCtx) return;
            switch (kind) {
                case 'ping':
                    tone(1760, 0, 0.18, 0.22, 'sine');
                    break;
                case 'chime':
                    tone(880,  0,    0.20, 0.25, 'sine');
                    tone(1320, 0.12, 0.20, 0.25, 'sine');
                    break;
                case 'siren':
                    [0, 0.18, 0.36].forEach(t => {
                        tone(700,  t,        0.10, 0.22, 'square');
                        tone(1100, t + 0.09, 0.10, 0.22, 'square');
                    });
                    break;
                case 'bloop':
                    tone(440, 0,    0.15, 0.22, 'triangle');
                    tone(660, 0.10, 0.15, 0.22, 'triangle');
                    tone(880, 0.20, 0.20, 0.22, 'triangle');
                    break;
                case 'alert':
                    [0, 0.14, 0.28].forEach(t => tone(2000, t, 0.08, 0.28, 'sawtooth'));
                    break;
            }
        }
        function beep() {
            if (!soundEnabled || !audioCtx) return;
            playSound(soundType);
        }
        function renderSoundToggle() {
            const el = document.getElementById('status-sound');
            if (soundEnabled) {
                el.textContent = '🔔 SOUND ON';
                el.style.color = '#22c55e';
            } else {
                el.textContent = '🔇 SOUND OFF';
                el.style.color = '';
            }
        }
        document.getElementById('status-sound').addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            savePrefs({ soundEnabled });
            renderSoundToggle();
            if (soundEnabled) {
                ensureAudio();
                beep();
            }
        });
        const soundPick = document.getElementById('sound-pick');
        soundPick.value = soundType;
        soundPick.addEventListener('change', (e) => {
            soundType = e.target.value;
            savePrefs({ soundType });
            ensureAudio();
            if (audioCtx) playSound(soundType);  // preview the chosen sound
        });
        renderSoundToggle();

        // ====== CHART ======
        function initChart(symbol) {
            currentSymbol = symbol;
            const wrap = document.getElementById('tv_main_wrap');
            wrap.innerHTML = '<div id="tv_main" style="height:100%;"></div>';
            document.getElementById('chart-symbol').textContent = symbol;
            new TradingView.widget({
                "autosize": true, "symbol": symbol, "interval": "1", "theme": "dark",
                "style": "1", "locale": "fr", "container_id": "tv_main",
                "hide_side_toolbar": false, "allow_symbol_change": true, "details": true,
                "studies": ["Volume@tv-basicstudies"]
            });
        }

        function selectCard(card) {
            document.querySelectorAll('.qcard').forEach(c => c.classList.remove('active'));
            if (card) card.classList.add('active');
        }

        function changeChart(symbol, fromCard) {
            initChart(symbol);
            savePrefs({ symbol });
            const card = fromCard || document.querySelector(`.qcard[data-symbol="${symbol}"]`);
            selectCard(card || null);
            if (window.innerWidth < 1024) window.scrollTo({top: 0, behavior: 'smooth'});
        }

        // Wire quote cards
        document.querySelectorAll('.qcard').forEach(card => {
            card.addEventListener('click', () => changeChart(card.dataset.symbol, card));
        });

        // Command bar
        const cmd = document.getElementById('cmd');
        cmd.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                const v = cmd.value.trim().toUpperCase();
                if (v) {
                    changeChart(v, null);
                    cmd.value = '';
                    cmd.blur();
                }
            }
        });

        // ====== WORLD CLOCKS + MARKET STATUS ======
        // Stock-market hours (local time, weekdays)
        const MARKETS = {
            NY:  { tz: 'America/New_York', open: [9, 30], close: [16, 0] },
            LDN: { tz: 'Europe/London',    open: [8, 0],  close: [16, 30] },
            TKY: { tz: 'Asia/Tokyo',       open: [9, 0],  close: [15, 0] },
            SYD: { tz: 'Australia/Sydney', open: [10, 0], close: [16, 0] },
        };

        function getTzParts(tz) {
            const fmt = new Intl.DateTimeFormat('en-GB', {
                timeZone: tz, hour12: false,
                weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            const parts = Object.fromEntries(fmt.formatToParts(new Date()).map(p => [p.type, p.value]));
            return parts;
        }

        function isMarketOpen(m) {
            const p = getTzParts(m.tz);
            const dow = p.weekday;
            if (dow === 'Sat' || dow === 'Sun') return false;
            const h = parseInt(p.hour, 10), min = parseInt(p.minute, 10);
            const cur = h * 60 + min;
            const op = m.open[0] * 60 + m.open[1];
            const cl = m.close[0] * 60 + m.close[1];
            return cur >= op && cur < cl;
        }

        function updateClocks() {
            for (const [code, m] of Object.entries(MARKETS)) {
                const p = getTzParts(m.tz);
                document.getElementById('time-' + code).textContent = `${p.hour}:${p.minute}:${p.second}`;
                const el = document.getElementById('mk-' + code);
                el.classList.toggle('open', isMarketOpen(m));
            }
            const now = new Date();
            document.getElementById('status-clock').textContent =
                String(now.getHours()).padStart(2, '0') + ':' +
                String(now.getMinutes()).padStart(2, '0') + ':' +
                String(now.getSeconds()).padStart(2, '0') + ' LOCAL';
        }

        // ====== NEWS (safe DOM, fresh-flash) ======
        function buildNewsItem(n, isFresh) {
            const item = document.createElement('div');
            item.className = 'n-item' + (n.crit ? ' critical' : '') + (isFresh ? ' fresh' : '');

            const meta = document.createElement('div');
            meta.className = 'n-meta';
            const timeSpan = document.createElement('span');
            timeSpan.textContent = n.time;
            const tag = document.createElement('span');
            tag.className = 'tag ' + n.s;
            tag.textContent = n.s;
            meta.appendChild(timeSpan);
            meta.appendChild(tag);

            const link = document.createElement('a');
            link.href = n.l;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = (n.crit ? '⚠️ ' : '') + n.t; // textContent escapes safely

            item.appendChild(meta);
            item.appendChild(link);
            return item;
        }

        async function getNews() {
            try {
                const r = await fetch('/api/news');
                const data = await r.json();
                const items = data.items || [];
                const container = document.getElementById('news-content');

                const previousLastSeen = lastSeenTs;
                let maxTs = lastSeenTs;
                let freshCount = 0;
                container.innerHTML = '';
                items.forEach(n => {
                    const isFresh = previousLastSeen > 0 && n.ts > previousLastSeen;
                    if (isFresh) freshCount++;
                    if (n.ts > maxTs) maxTs = n.ts;
                    container.appendChild(buildNewsItem(n, isFresh));
                });
                lastSeenTs = maxTs;

                const status = document.getElementById('status-news');
                const cacheTag = data.cached ? `cache ${data.age}s` : 'fresh';
                status.innerHTML = `News: <span class="ok">${items.length}</span> · ${cacheTag}` +
                    (freshCount > 0 ? ` · <span class="warn">+${freshCount} new</span>` : '');
                if (freshCount > 0) beep();
            } catch (e) {
                document.getElementById('status-news').innerHTML = 'News: <span class="err">offline</span>';
            }
        }

        // ====== ECONOMIC CALENDAR ======
        const FLAGS = {
            USD: '\u{1F1FA}\u{1F1F8}', EUR: '\u{1F1EA}\u{1F1FA}', GBP: '\u{1F1EC}\u{1F1E7}',
            JPY: '\u{1F1EF}\u{1F1F5}', CHF: '\u{1F1E8}\u{1F1ED}', CAD: '\u{1F1E8}\u{1F1E6}',
            AUD: '\u{1F1E6}\u{1F1FA}', NZD: '\u{1F1F3}\u{1F1FF}', CNY: '\u{1F1E8}\u{1F1F3}',
        };
        const CCY_LIST = ['USD','EUR','GBP','JPY','CHF','CAD','AUD','NZD','CNY'];
        const IMPACTS = ['High','Medium','Low'];

        const calFilters = {
            impact: new Set(Array.isArray(PREFS.calImpact) ? PREFS.calImpact : ['High','Medium']),
            ccy:    new Set(Array.isArray(PREFS.calCcy)    ? PREFS.calCcy    : ['USD','EUR','GBP','JPY']),
        };
        let calEvents = [];
        let calLastSeenActual = new Set();
        let calPollTimer = null;
        let calFirstLoad = true;

        function persistCalFilters() {
            savePrefs({ calImpact: [...calFilters.impact], calCcy: [...calFilters.ccy] });
        }
        function buildCalToolbar() {
            const root = document.getElementById('cal-filters');
            root.innerHTML = '';
            IMPACTS.forEach(imp => {
                const c = document.createElement('span');
                c.className = 'cal-chip' + (calFilters.impact.has(imp) ? ' on' : '');
                c.textContent = imp.toUpperCase();
                c.addEventListener('click', () => {
                    if (calFilters.impact.has(imp)) calFilters.impact.delete(imp);
                    else calFilters.impact.add(imp);
                    persistCalFilters();
                    buildCalToolbar();
                    renderCalendar();
                });
                root.appendChild(c);
            });
            const sep = document.createElement('span');
            sep.className = 'cal-chip sep';
            sep.textContent = '|';
            root.appendChild(sep);
            CCY_LIST.forEach(ccy => {
                const c = document.createElement('span');
                c.className = 'cal-chip' + (calFilters.ccy.has(ccy) ? ' on' : '');
                c.textContent = ccy;
                c.addEventListener('click', () => {
                    if (calFilters.ccy.has(ccy)) calFilters.ccy.delete(ccy);
                    else calFilters.ccy.add(ccy);
                    persistCalFilters();
                    buildCalToolbar();
                    renderCalendar();
                });
                root.appendChild(c);
            });
        }
        function calToNum(s) {
            if (s === null || s === undefined || s === '') return null;
            const m = String(s).match(/-?\d+(?:\.\d+)?/);
            if (!m) return null;
            let n = parseFloat(m[0]);
            const u = String(s).slice(-1).toUpperCase();
            if (u === 'T') n *= 1e12;
            else if (u === 'B') n *= 1e9;
            else if (u === 'M') n *= 1e6;
            else if (u === 'K') n *= 1e3;
            return n;
        }
        function compareActual(actual, forecast) {
            const a = calToNum(actual), f = calToNum(forecast);
            if (a === null || f === null) return 'eq';
            if (a > f) return 'up';
            if (a < f) return 'down';
            return 'eq';
        }
        function fmtCountdown(secs) {
            if (secs < 0) secs = 0;
            const m = Math.floor(secs / 60);
            const s = secs % 60;
            return `${m}:${String(s).padStart(2,'0')}`;
        }
        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        }
        function renderCalendar() {
            const root = document.getElementById('calendar-content');
            if (!calEvents.length) {
                root.innerHTML = '<div class="cal-empty">Chargement…</div>';
                return;
            }
            const filtered = calEvents.filter(e =>
                calFilters.impact.has(e.impact) && calFilters.ccy.has(e.country)
            );
            if (!filtered.length) {
                root.innerHTML = '<div class="cal-empty">Aucun événement avec les filtres actuels.</div>';
                return;
            }
            const now = Date.now() / 1000;
            const newFreshTriggers = [];
            let html = '';
            let lastDay = '';
            filtered.forEach(e => {
                const dt = new Date(e.ts * 1000);
                const dayKey = dt.toLocaleDateString('fr-FR', { weekday:'long', day:'numeric', month:'long' });
                if (dayKey !== lastDay) {
                    html += `<div class="cal-day">${dayKey}</div>`;
                    lastDay = dayKey;
                }
                const localTime = dt.toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' });
                const flag = FLAGS[e.country] || '\u{1F3F3}';
                const impClass = e.impact.toLowerCase();
                const isPast = !!e.actual || (e.ts < now - 60);
                const isDue  = !e.actual && (e.ts - now) <= 75 && (e.ts - now) >= -10;
                const cmp = e.actual ? compareActual(e.actual, e.forecast) : 'eq';
                const fresh = !!e.actual && !calLastSeenActual.has(e.ts) && !calFirstLoad;
                if (e.actual) {
                    if (fresh) newFreshTriggers.push(e);
                    calLastSeenActual.add(e.ts);
                }
                const cls = ['cal-row'];
                if (isPast && !fresh) cls.push('past');
                if (isDue) cls.push('due');
                if (fresh) cls.push('fresh-result');

                let cdHtml = '';
                if (isDue) {
                    const secs = Math.max(0, Math.floor(e.ts - now));
                    const urgent = secs < 30 ? ' urgent' : '';
                    cdHtml = `<span class="cal-countdown${urgent}" data-cd-target="${e.ts}">T-${fmtCountdown(secs)}</span>`;
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
                const safeTitle = escapeHtml(e.title || '');

                html += `<div class="${cls.join(' ')}">
                    <span class="cal-time"><span>${localTime}</span>${cdHtml}</span>
                    <span class="cal-flag-wrap"><span class="cal-flag">${flag}</span><span class="cal-ccy">${e.country}</span></span>
                    <span class="cal-title">
                        <span class="cal-impact ${impClass}"><i></i><i></i><i></i></span>
                        <span class="cal-title-text" title="${safeTitle}">${safeTitle}</span>
                    </span>
                    ${actualHtml}
                    ${forecastHtml}
                    ${previousHtml}
                </div>`;
            });
            root.innerHTML = html;

            // Sound triggers (only after first load — avoid mass-flash on first paint)
            if (!calFirstLoad && newFreshTriggers.some(e => e.impact === 'High' || e.impact === 'Medium')) {
                if (soundEnabled) { ensureAudio(); beep(); }
            }
            calFirstLoad = false;
        }
        function tickCountdowns() {
            const now = Date.now() / 1000;
            let crossedZero = false;
            document.querySelectorAll('[data-cd-target]').forEach(el => {
                const ts = parseFloat(el.dataset.cdTarget);
                const secs = Math.floor(ts - now);
                if (secs < -2) { crossedZero = true; return; }
                el.textContent = `T-${fmtCountdown(Math.max(0, secs))}`;
                if (secs < 30 && !el.classList.contains('urgent')) el.classList.add('urgent');
            });
            if (crossedZero) fetchCalendar();
        }
        function nextHotMomentSec() {
            // Returns: 0 if currently in hot window (event within ±90s), else seconds until hot window starts
            const now = Date.now() / 1000;
            for (const e of calEvents) {
                if (e.actual) continue;
                if (!calFilters.impact.has(e.impact) || !calFilters.ccy.has(e.country)) continue;
                const delta = e.ts - now;
                if (delta < -120) continue;
                if (delta <= 90) return 0;
                return delta - 90;
            }
            return Infinity;
        }
        function scheduleCalPoll() {
            clearTimeout(calPollTimer);
            const hot = nextHotMomentSec();
            let delay;
            if (hot === 0) delay = 3000;
            else if (hot < 60) delay = Math.max(2000, hot * 1000);
            else delay = 60000;
            calPollTimer = setTimeout(fetchCalendar, delay);
        }
        async function fetchCalendar() {
            try {
                const r = await fetch('/api/calendar');
                const j = await r.json();
                calEvents = j.events || [];
                document.getElementById('cal-live').innerHTML = j.hot
                    ? '<span style="color:var(--warn);">HOT</span>' : 'LIVE';
                renderCalendar();
            } catch (e) {
                document.getElementById('cal-live').innerHTML = '<span style="color:var(--sell);">OFFLINE</span>';
            } finally {
                scheduleCalPoll();
            }
        }
        buildCalToolbar();
        fetchCalendar();
        setInterval(tickCountdowns, 1000);

        // ====== BOOT ======
        const startSymbol = currentSymbol;
        const startCard = document.querySelector(`.qcard[data-symbol="${startSymbol}"]`);
        initChart(startSymbol);
        selectCard(startCard || document.querySelector('.qcard'));
        updateClocks();
        getNews();
        setInterval(updateClocks, 1000);
        setInterval(getNews, 5000);   // safe — server-side cache makes this cheap
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX_HTML


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
