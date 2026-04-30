from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import hashlib
import html
import json
import re
import time
from typing import Any, Optional

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from fastapi import HTTPException, WebSocket

from app.config import *
from app.services.accounts import utc_now


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

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30
NEWS_MAX_AGE_HOURS = 72
NEWS_DEDUP_WINDOW_SECONDS = 2 * 60 * 60
_calendar_cache: dict[str, dict] = {}
CALENDAR_CACHE_TTL = 30
CALENDAR_HOT_CACHE_TTL = 2
_quotes_cache: dict = {"data": None, "ts": 0.0}
QUOTES_CACHE_TTL = 5
_quote_latest_by_key: dict[str, dict] = {}
_quote_ws_clients: set[WebSocket] = set()
_fmp_ws_tasks: list[asyncio.Task] = []
_context_cache: dict[str, dict] = {}
CONTEXT_CACHE_TTL = 30
MARKET_SYMBOLS = {
    "gold": {"symbol": "GC=F", "label": "GOLD"},
    "silver": {"symbol": "SI=F", "label": "SILVER"},
    "dxy": {"symbol": "DX-Y.NYB", "label": "DXY"},
    "us10y": {"symbol": "^TNX", "label": "US10Y"},
    "oil": {"symbol": "CL=F", "label": "WTI"},
    "spy": {"symbol": "SPY", "label": "SPY"},
    "qqq": {"symbol": "QQQ", "label": "QQQ"},
    "tlt": {"symbol": "TLT", "label": "TLT"},
    "eurusd": {"symbol": "EURUSD=X", "label": "EUR/USD"},
    "gbpusd": {"symbol": "GBPUSD=X", "label": "GBP/USD"},
    "usdjpy": {"symbol": "JPY=X", "label": "USD/JPY"},
    "btc": {"symbol": "BTC-USD", "label": "BTC"},
}

QUOTE_CARDS = [
    {"key": "xauusd", "label": "XAUUSD", "name": "OR / DOLLAR AMERICAIN", "fmp_symbol": "GCUSD", "fallback_symbol": "GC=F", "tv_symbol": "OANDA:XAUUSD", "decimals": 2, "ws_cluster": "forex", "ws_symbol": "xauusd"},
    {"key": "xagusd", "label": "XAGUSD", "name": "ARGENT / DOLLAR AMERICAIN", "fmp_symbol": "SIUSD", "fallback_symbol": "SI=F", "tv_symbol": "OANDA:XAGUSD", "decimals": 4, "ws_cluster": "forex", "ws_symbol": "xagusd"},
    {"key": "dxy", "label": "DXY", "name": "US DOLLAR INDEX", "fmp_symbol": "^DXY", "fallback_symbol": "DX-Y.NYB", "tv_symbol": "CAPITALCOM:DXY", "decimals": 3},
    {"key": "usoil", "label": "USOIL", "name": "CFD SUR PETROLE WTI", "fmp_symbol": "CLUSD", "fallback_symbol": "CL=F", "tv_symbol": "TVC:USOIL", "decimals": 2},
    {"key": "eurusd", "label": "EURUSD", "name": "EURO / DOLLAR AMERICAIN", "fmp_symbol": "EURUSD", "fallback_symbol": "EURUSD=X", "tv_symbol": "FX:EURUSD", "decimals": 5, "ws_cluster": "forex", "ws_symbol": "eurusd"},
    {"key": "tlt", "label": "TLT", "name": "OBLIGATIONS DU TRESOR US", "fmp_symbol": "TLT", "fallback_symbol": "TLT", "tv_symbol": "NASDAQ:TLT", "decimals": 2, "ws_cluster": "us-stocks", "ws_symbol": "tlt"},
    {"key": "spy", "label": "SPY", "name": "S&P 500 ETF", "fmp_symbol": "SPY", "fallback_symbol": "SPY", "tv_symbol": "AMEX:SPY", "decimals": 2, "ws_cluster": "us-stocks", "ws_symbol": "spy"},
    {"key": "qqq", "label": "QQQ", "name": "NASDAQ 100 ETF", "fmp_symbol": "QQQ", "fallback_symbol": "QQQ", "tv_symbol": "NASDAQ:QQQ", "decimals": 2, "ws_cluster": "us-stocks", "ws_symbol": "qqq"},
]
QUOTE_CARD_BY_KEY = {card["key"]: card for card in QUOTE_CARDS}
QUOTE_CARD_BY_WS = {card["ws_symbol"]: card for card in QUOTE_CARDS if card.get("ws_symbol")}

MARKET_PROFILES = {
    "xauusd": {
        "id": "xauusd",
        "label": "XAU/USD",
        "symbol": "OANDA:XAUUSD",
        "calendar_countries": ["US"],
        "keywords": ["gold", "xau", "bullion", "fed", "fomc", "powell", "cpi", "inflation", "nfp", "yields", "dollar", "dxy", "war"],
        "tags": ["XAU", "FED", "MACRO", "GEO", "OFFICIAL"],
    },
    "usdjpy": {
        "id": "usdjpy",
        "label": "USD/JPY",
        "symbol": "FX:USDJPY",
        "calendar_countries": ["US", "JP"],
        "keywords": ["yen", "jpy", "japan", "boj", "ueda", "intervention", "fed", "fomc", "powell", "yields", "treasury", "dollar"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "eurusd": {
        "id": "eurusd",
        "label": "EUR/USD",
        "symbol": "FX:EURUSD",
        "calendar_countries": ["US", "EU"],
        "keywords": ["euro", "eur", "ecb", "lagarde", "fed", "fomc", "inflation", "cpi", "pmi", "dollar"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "gbpusd": {
        "id": "gbpusd",
        "label": "GBP/USD",
        "symbol": "FX:GBPUSD",
        "calendar_countries": ["US", "GB"],
        "keywords": ["pound", "sterling", "gbp", "boe", "bailey", "uk", "britain", "fed", "inflation", "cpi", "gilts"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "nasdaq": {
        "id": "nasdaq",
        "label": "NASDAQ",
        "symbol": "NASDAQ:QQQ",
        "calendar_countries": ["US"],
        "keywords": ["nasdaq", "qqq", "tech", "ai", "semiconductor", "earnings", "fed", "yields", "rates", "risk", "nvidia"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "btcusd": {
        "id": "btcusd",
        "label": "BTC/USD",
        "symbol": "BITSTAMP:BTCUSD",
        "calendar_countries": ["US"],
        "keywords": ["bitcoin", "btc", "crypto", "etf", "sec", "fed", "liquidity", "dollar", "rates", "risk"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
}

BIAS_PROFILES = {
    "xauusd": {
        "title": "XAU/USD",
        "target_key": "gold",
        "target_label": "XAU",
        "momentum_key": "gold_momo",
        "bias_name": "XAU",
        "bullish_action": "LONG XAU",
        "bearish_action": "SHORT XAU",
        "drivers": [
            {"key": "dxy", "label": "Dollar", "bullish_when": "down", "weight": 3.0, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Dollar softer supports XAU", "bearish": "Dollar strength pressures XAU", "neutral": "Dollar impact limited"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "down", "weight": 3.0, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "Yields easing supports XAU", "bearish": "Yields rising pressures XAU", "neutral": "Yield pressure mixed"},
            {"key": "gold", "driver_key": "gold_momo", "label": "Gold", "bullish_when": "up", "weight": 2.0, "strong": 0.90, "medium": 0.35, "layer": "momentum", "bullish": "XAU momentum confirms buyers", "bearish": "XAU momentum confirms sellers", "neutral": "XAU momentum undecided"},
            {"key": "silver", "label": "Silver", "bullish_when": "up", "weight": 1.0, "strong": 1.00, "medium": 0.40, "layer": "momentum", "bullish": "Silver confirms metals bid", "bearish": "Silver weakens metals tone", "neutral": "Silver not confirming"},
            {"key": "oil", "label": "WTI", "bullish_when": "up", "weight": 1.0, "strong": 1.20, "medium": 0.50, "layer": "macro", "bullish": "Energy stress can lift XAU", "bearish": "Oil easing cools stress bid", "neutral": "Oil impact limited"},
        ],
    },
    "usdjpy": {
        "title": "USD/JPY",
        "target_key": "usdjpy",
        "target_label": "USD/JPY",
        "momentum_key": "usdjpy_momo",
        "bias_name": "USDJPY",
        "bullish_action": "LONG USDJPY",
        "bearish_action": "SHORT USDJPY",
        "drivers": [
            {"key": "usdjpy", "driver_key": "usdjpy_momo", "label": "USDJPY", "bullish_when": "up", "weight": 2.2, "strong": 0.55, "medium": 0.20, "layer": "momentum", "bullish": "USDJPY momentum confirms upside", "bearish": "USDJPY momentum confirms downside", "neutral": "USDJPY momentum undecided"},
            {"key": "dxy", "label": "Dollar", "bullish_when": "up", "weight": 2.4, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Dollar strength supports USDJPY", "bearish": "Dollar softness weighs on USDJPY", "neutral": "Dollar impact limited"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "up", "weight": 3.0, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "Higher US yields support USDJPY", "bearish": "Lower US yields pressure USDJPY", "neutral": "Yield signal mixed"},
            {"key": "spy", "label": "Risk", "bullish_when": "up", "weight": 1.2, "strong": 0.90, "medium": 0.35, "layer": "risk", "bullish": "Risk appetite supports carry", "bearish": "Risk-off weighs on USDJPY", "neutral": "Risk tone mixed"},
        ],
    },
    "eurusd": {
        "title": "EUR/USD",
        "target_key": "eurusd",
        "target_label": "EUR/USD",
        "momentum_key": "eurusd_momo",
        "bias_name": "EURUSD",
        "bullish_action": "LONG EURUSD",
        "bearish_action": "SHORT EURUSD",
        "drivers": [
            {"key": "eurusd", "driver_key": "eurusd_momo", "label": "EURUSD", "bullish_when": "up", "weight": 2.2, "strong": 0.45, "medium": 0.18, "layer": "momentum", "bullish": "EURUSD momentum confirms buyers", "bearish": "EURUSD momentum confirms sellers", "neutral": "EURUSD momentum undecided"},
            {"key": "dxy", "label": "Dollar", "bullish_when": "down", "weight": 3.0, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Dollar weakness supports EURUSD", "bearish": "Dollar strength pressures EURUSD", "neutral": "Dollar impact limited"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "down", "weight": 1.8, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "US yields easing helps EURUSD", "bearish": "US yields rising weighs on EURUSD", "neutral": "Yield signal mixed"},
            {"key": "gold", "label": "Anti-USD", "bullish_when": "up", "weight": 1.0, "strong": 0.90, "medium": 0.35, "layer": "risk", "bullish": "Anti-dollar tone supports EURUSD", "bearish": "Anti-dollar tone weakens", "neutral": "Cross-asset confirmation limited"},
        ],
    },
    "gbpusd": {
        "title": "GBP/USD",
        "target_key": "gbpusd",
        "target_label": "GBP/USD",
        "momentum_key": "gbpusd_momo",
        "bias_name": "GBPUSD",
        "bullish_action": "LONG GBPUSD",
        "bearish_action": "SHORT GBPUSD",
        "drivers": [
            {"key": "gbpusd", "driver_key": "gbpusd_momo", "label": "GBPUSD", "bullish_when": "up", "weight": 2.2, "strong": 0.45, "medium": 0.18, "layer": "momentum", "bullish": "GBPUSD momentum confirms buyers", "bearish": "GBPUSD momentum confirms sellers", "neutral": "GBPUSD momentum undecided"},
            {"key": "dxy", "label": "Dollar", "bullish_when": "down", "weight": 2.8, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Dollar weakness supports GBPUSD", "bearish": "Dollar strength pressures GBPUSD", "neutral": "Dollar impact limited"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "down", "weight": 1.6, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "US yields easing helps GBPUSD", "bearish": "US yields rising weighs on GBPUSD", "neutral": "Yield signal mixed"},
            {"key": "spy", "label": "Risk", "bullish_when": "up", "weight": 1.0, "strong": 0.90, "medium": 0.35, "layer": "risk", "bullish": "Risk appetite supports GBP", "bearish": "Risk-off pressures GBP", "neutral": "Risk tone mixed"},
        ],
    },
    "nasdaq": {
        "title": "NASDAQ",
        "target_key": "qqq",
        "target_label": "NASDAQ",
        "momentum_key": "nasdaq_momo",
        "bias_name": "NASDAQ",
        "bullish_action": "LONG NASDAQ",
        "bearish_action": "SHORT NASDAQ",
        "drivers": [
            {"key": "qqq", "driver_key": "nasdaq_momo", "label": "QQQ", "bullish_when": "up", "weight": 2.4, "strong": 1.00, "medium": 0.35, "layer": "momentum", "bullish": "Nasdaq momentum confirms buyers", "bearish": "Nasdaq momentum confirms sellers", "neutral": "Nasdaq momentum undecided"},
            {"key": "spy", "label": "SPY", "bullish_when": "up", "weight": 1.6, "strong": 0.90, "medium": 0.35, "layer": "risk", "bullish": "Broad risk appetite supports tech", "bearish": "Broad risk-off pressures tech", "neutral": "Equity breadth mixed"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "down", "weight": 2.6, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "Lower yields support duration assets", "bearish": "Higher yields pressure tech multiples", "neutral": "Yield signal mixed"},
            {"key": "dxy", "label": "Dollar", "bullish_when": "down", "weight": 1.0, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Softer dollar helps risk appetite", "bearish": "Stronger dollar tightens conditions", "neutral": "Dollar impact limited"},
            {"key": "tlt", "label": "TLT", "bullish_when": "up", "weight": 1.0, "strong": 0.80, "medium": 0.30, "layer": "macro", "bullish": "Bond bid supports growth equities", "bearish": "Bond selloff pressures growth equities", "neutral": "Bond tone mixed"},
        ],
    },
    "btcusd": {
        "title": "BTC/USD",
        "target_key": "btc",
        "target_label": "BTC",
        "momentum_key": "btc_momo",
        "bias_name": "BTC",
        "bullish_action": "LONG BTC",
        "bearish_action": "SHORT BTC",
        "drivers": [
            {"key": "btc", "driver_key": "btc_momo", "label": "BTC", "bullish_when": "up", "weight": 2.6, "strong": 2.00, "medium": 0.80, "layer": "momentum", "bullish": "BTC momentum confirms buyers", "bearish": "BTC momentum confirms sellers", "neutral": "BTC momentum undecided"},
            {"key": "qqq", "label": "QQQ", "bullish_when": "up", "weight": 1.6, "strong": 1.00, "medium": 0.35, "layer": "risk", "bullish": "Tech risk appetite supports crypto", "bearish": "Tech weakness pressures crypto beta", "neutral": "Risk beta mixed"},
            {"key": "dxy", "label": "Dollar", "bullish_when": "down", "weight": 2.0, "strong": 0.25, "medium": 0.10, "layer": "macro", "bullish": "Dollar weakness supports liquidity assets", "bearish": "Dollar strength pressures crypto", "neutral": "Dollar impact limited"},
            {"key": "us10y", "label": "US10Y", "bullish_when": "down", "weight": 1.6, "strong": 0.30, "medium": 0.12, "layer": "macro", "bullish": "Lower yields support risk assets", "bearish": "Higher yields tighten liquidity", "neutral": "Yield signal mixed"},
            {"key": "gold", "label": "Gold", "bullish_when": "up", "weight": 0.7, "strong": 0.90, "medium": 0.35, "layer": "risk", "bullish": "Hard-asset tone supportive", "bearish": "Hard-asset tone weak", "neutral": "Hard-asset confirmation limited"},
        ],
    },
}


def require_fmp_key() -> None:
    if not FMP_API_KEY:
        raise HTTPException(status_code=503, detail="FMP_API_KEY manquant")


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


CALENDAR_HIGH_KEYWORDS = (
    "core cpi", "consumer price index", "core pce price index", "nonfarm",
    "nfp", "payroll", "unemployment rate", "fomc", "fed interest rate",
    "fed press", "powell", "gdp growth rate", "gross domestic product qoq",
    "retail sales", "ism manufacturing", "ism services", "ppi",
    "employment cost index",
)

CALENDAR_MEDIUM_KEYWORDS = (
    "pce price index", "initial jobless claims", "continuing jobless",
    "chicago pmi", "leading index", "gdp price", "personal income",
    "personal spending", "durable goods", "consumer confidence",
    "jolts", "adp", "beige book", "treasury refunding", "pce prices qoq",
    "core pce prices qoq",
)

CALENDAR_LOW_KEYWORDS = (
    "4-week average", "4 week average", "mortgage rate", "bill auction",
    "fed balance sheet", "real consumer spending", "gdp sales",
)

CALENDAR_KEY_EVENT_KEYWORDS = (
    "core cpi", "consumer price index", "core pce price index",
    "nonfarm", "nfp", "payroll", "unemployment rate", "fomc",
    "fed interest rate", "fed press", "powell", "gdp growth rate",
    "gross domestic product qoq", "retail sales", "ism manufacturing",
    "ism services", "ppi", "employment cost index",
)


def calendar_impact_override(title: str, original: str) -> str:
    clean = title.lower()
    if any(keyword in clean for keyword in CALENDAR_LOW_KEYWORDS):
        return "Low"
    if any(keyword in clean for keyword in CALENDAR_HIGH_KEYWORDS):
        return "High"
    if any(keyword in clean for keyword in CALENDAR_MEDIUM_KEYWORDS):
        return "Medium"
    return original


def calendar_market_priority(title: str, impact: str) -> tuple[int, str]:
    clean = title.lower()
    priority = {"High": 70, "Medium": 45, "Low": 20}.get(impact, 10)

    if any(keyword in clean for keyword in CALENDAR_KEY_EVENT_KEYWORDS):
        priority += 25
    if "core pce price index mom" in clean or "core cpi" in clean:
        priority += 16
    if "gross domestic product qoq" in clean or "gdp growth rate qoq" in clean:
        priority += 14
    if "employment cost index" in clean:
        priority += 12
    if "pce price index" in clean:
        priority += 10
    if "initial jobless claims" in clean:
        priority += 8
    if "personal income" in clean or "personal spending" in clean:
        priority += 6
    if any(keyword in clean for keyword in CALENDAR_LOW_KEYWORDS):
        priority -= 15

    if priority >= 90:
        label = "KEY"
    elif priority >= 50:
        label = "WATCH"
    else:
        label = ""

    return priority, label


def parse_calendar_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        cleaned = str(value).replace(",", "").replace("%", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def calendar_lower_is_better(title: str) -> bool:
    clean = title.lower()
    lower_is_better = (
        "unemployment", "jobless", "claims", "claimant", "layoffs",
        "challenger job cuts", "inventories", "stock change", "deficit",
        "debt", "delinquency", "bankruptcy", "default",
    )
    return any(keyword in clean for keyword in lower_is_better)


def calendar_surprise(actual: Any, forecast: Any, title: str) -> dict:
    actual_num = parse_calendar_number(actual)
    forecast_num = parse_calendar_number(forecast)
    if actual_num is None or forecast_num is None or actual_num == forecast_num:
        return {
            "surprise": None,
            "surprise_pct": None,
            "surprise_label": "",
            "result_tone": "",
            "market_read": "",
        }

    delta = actual_num - forecast_num
    surprise_pct = (delta / abs(forecast_num) * 100) if forecast_num else None
    lower_better = calendar_lower_is_better(title)
    better = delta < 0 if lower_better else delta > 0
    tone = "good" if better else "bad"
    direction = "USD+" if better else "USD-"
    if any(keyword in title.lower() for keyword in ("cpi", "pce", "ppi", "inflation")):
        direction = "HOT DATA" if delta > 0 else "COOL DATA"
    if "jobless" in title.lower() or "claims" in title.lower() or "unemployment" in title.lower():
        direction = "LABOR STRONG" if better else "LABOR WEAK"

    return {
        "surprise": round(delta, 4),
        "surprise_pct": round(surprise_pct, 2) if surprise_pct is not None else None,
        "surprise_label": f"{delta:+.3g}",
        "result_tone": tone,
        "market_read": direction,
    }


def calendar_event_family(title: str) -> str:
    clean = " ".join(title.lower().replace("-", " ").split())
    replacements = {
        "gross domestic product qoq": "gdp growth rate qoq",
        "gdp growth rate qoq": "gdp growth rate qoq",
        "initial jobless claims": "initial jobless claims",
        "jobless claims 4 week average": "jobless claims 4 week average",
        "continuing jobless claims": "continuing jobless claims",
        "employment cost wages qoq": "employment cost wages qoq",
        "employment wages qoq": "employment cost wages qoq",
        "employment cost benefits qoq": "employment cost benefits qoq",
        "employment benefits qoq": "employment cost benefits qoq",
    }
    for needle, family in replacements.items():
        if needle in clean:
            return family
    return clean


def event_quality_score(event: dict) -> int:
    score = {"High": 300, "Medium": 200, "Low": 100}.get(event.get("impact"), 0)
    score += int(event.get("market_priority") or 0)
    title = str(event.get("title") or "").lower()
    if "gross domestic product" in title:
        score += 12
    if "gdp growth rate" in title:
        score += 10
    if "core pce" in title:
        score += 10
    if event.get("forecast") not in (None, ""):
        score += 4
    if event.get("previous") not in (None, ""):
        score += 2
    return score


def dedupe_calendar_events(events: list[dict]) -> list[dict]:
    best: dict[tuple, dict] = {}
    passthrough: list[dict] = []
    dedupe_families = {
        "gdp growth rate qoq",
        "employment cost wages qoq",
        "employment cost benefits qoq",
    }
    for event in events:
        family = calendar_event_family(event.get("title") or "")
        key = (event.get("country"), event.get("ts"), family)
        if family in dedupe_families:
            current = best.get(key)
            if current is None or event_quality_score(event) > event_quality_score(current):
                best[key] = event
        else:
            passthrough.append(event)

    deduped = passthrough + list(best.values())
    deduped.sort(key=lambda item: (
        item["ts"],
        -int(item.get("market_priority") or 0),
        {"High": 0, "Medium": 1, "Low": 2}.get(item.get("impact"), 3),
        item.get("title", ""),
    ))
    return deduped


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
    title = event.get("event") or ""
    impact = calendar_impact_override(title, impact)
    market_priority, market_label = calendar_market_priority(title, impact)
    surprise = calendar_surprise(event.get("actual"), estimate, title)

    return {
        "title": title,
        "country": event.get("country") or "US",
        "currency": event.get("currency") or "",
        "impact": impact,
        "actual": event.get("actual"),
        "forecast": estimate,
        "previous": event.get("previous"),
        "unit": event.get("unit"),
        "ts": int(dt.timestamp()),
        "date_utc": dt.isoformat(),
        "market_priority": market_priority,
        "market_label": market_label,
        **surprise,
    }


def get_current_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now.astimezone(CALENDAR_TZ) if now else datetime.now(CALENDAR_TZ)
    week_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


def calendar_cache_ttl(events: list[dict], now_ts: float | None = None) -> int:
    now_value = now_ts or time.time()
    if any(abs(float(event.get("ts", 0)) - now_value) <= 900 and event.get("impact") in {"High", "Medium"} for event in events):
        return CALENDAR_HOT_CACHE_TTL
    return CALENDAR_CACHE_TTL


def calendar_refresh_ms(events: list[dict], now_ts: float | None = None) -> int:
    now_value = now_ts or time.time()
    if any(abs(float(event.get("ts", 0)) - now_value) <= 900 and event.get("impact") in {"High", "Medium"} for event in events):
        return 2000
    if any(0 <= float(event.get("ts", 0)) - now_value <= 3600 and event.get("impact") in {"High", "Medium"} for event in events):
        return 10000
    return 60000


OFFICIAL_NEWS_SOURCES = {"FED", "TREASURY", "DOL"}


def clean_news_title(title: str) -> str:
    clean = " ".join((title or "").split())
    if " - " in clean:
        head, tail = clean.rsplit(" - ", 1)
        if tail.strip().lower() in {"reuters", "bloomberg", "cnbc", "investing.com", "forexlive"}:
            clean = head.strip()
    return clean


def news_fingerprint(title: str) -> str:
    clean = clean_news_title(title).lower()
    clean = re.sub(r"https?://\S+", " ", clean)
    clean = re.sub(r"[^a-z0-9%$]+", " ", clean)
    stopwords = {
        "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "as",
        "by", "with", "from", "at", "is", "are", "be", "will", "says", "say",
    }
    tokens = [token for token in clean.split() if len(token) > 2 and token not in stopwords]
    return " ".join(tokens[:18])


def news_similarity(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def stable_news_id(title: str) -> str:
    fingerprint = news_fingerprint(title) or clean_news_title(title).lower()
    return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:16]


def _format_news_item(name: str, title: str, link: str, dt: datetime) -> dict:
    clean_title = clean_news_title(title)
    title_upper = clean_title.upper()
    classification = classify_news_item(name, title_upper)
    item_id = stable_news_id(clean_title)
    return {
        "id": item_id,
        "s": name,
        "t": clean_title,
        "l": link,
        "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
        "ts": dt.timestamp(),
        "crit": any(keyword in title_upper for keyword in ALERTS_CRITICAL),
        "duplicate_count": 1,
        "related_sources": [name],
        **classification,
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
    if source in OFFICIAL_NEWS_SOURCES:
        categories.append("OFFICIAL")
        score += 4
    if any(keyword in title_upper for keyword in ("BREAKING", "URGENT", "EXCLUSIVE", "STATEMENT", "HOLDS RATES", "RATE DECISION", "PRESS CONFERENCE")):
        categories.append("MOVING")
        score += 3

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
        "news_score": score,
        "market_moving": priority == "high" or "MOVING" in categories or source in OFFICIAL_NEWS_SOURCES,
    }


def news_item_rank(item: dict) -> tuple[int, float]:
    source_rank = {
        "FED": 7,
        "DOL": 6,
        "TREASURY": 6,
        "REUTERS": 5,
        "BLOOMBERG": 5,
        "FOREXLIVE": 4,
        "CNBC": 3,
        "INVESTING": 2,
    }.get(str(item.get("s") or ""), 1)
    return int(item.get("news_score") or 0) + source_rank, float(item.get("ts") or 0)


def dedupe_news_items(items: list[dict]) -> list[dict]:
    clusters: list[dict] = []

    for item in sorted(items, key=lambda row: row.get("ts", 0), reverse=True):
        fingerprint = news_fingerprint(item.get("t") or "")
        matched = None
        for cluster in clusters:
            if abs(float(cluster["best"].get("ts", 0)) - float(item.get("ts", 0))) > NEWS_DEDUP_WINDOW_SECONDS:
                continue
            if fingerprint and fingerprint == cluster["fingerprint"]:
                matched = cluster
                break
            if fingerprint and news_similarity(fingerprint, cluster["fingerprint"]) >= 0.82:
                matched = cluster
                break

        if matched is None:
            clusters.append({"fingerprint": fingerprint, "items": [item], "best": item})
            continue

        matched["items"].append(item)
        if news_item_rank(item) > news_item_rank(matched["best"]):
            matched["best"] = item

    deduped = []
    for cluster in clusters:
        best = dict(cluster["best"])
        sources = list(dict.fromkeys(str(item.get("s") or "") for item in cluster["items"] if item.get("s")))
        tags = []
        for item in cluster["items"]:
            tags.extend(item.get("tags") or [])
        best["id"] = stable_news_id(best.get("t") or "")
        best["duplicate_count"] = len(cluster["items"])
        best["related_sources"] = sources
        best["tags"] = list(dict.fromkeys(tags))
        best["crit"] = any(item.get("crit") for item in cluster["items"])
        best["market_moving"] = any(item.get("market_moving") for item in cluster["items"])
        best["news_score"] = max(int(item.get("news_score") or 0) for item in cluster["items"])
        if any(item.get("priority") == "high" for item in cluster["items"]):
            best["priority"] = "high"
        elif any(item.get("priority") == "medium" for item in cluster["items"]):
            best["priority"] = "medium"
        else:
            best["priority"] = "low"
        deduped.append(best)

    deduped.sort(key=lambda item: (float(item.get("ts") or 0), int(item.get("news_score") or 0)), reverse=True)
    return deduped


def get_market_profile(profile_id: Optional[str]) -> dict:
    key = (profile_id or "xauusd").strip().lower()
    return MARKET_PROFILES.get(key, MARKET_PROFILES["xauusd"])


def parse_country_filter(raw: Optional[str], fallback: list[str]) -> list[str]:
    if not raw:
        return fallback
    countries = [
        country.strip().upper()
        for country in raw.split(",")
        if country.strip()
    ]
    return countries[:8] or fallback


def score_news_for_profile(item: dict, profile: dict) -> int:
    title = str(item.get("t", "")).lower()
    tags = set(item.get("tags") or [])
    score = 0

    for keyword in profile.get("keywords", []):
        if keyword.lower() in title:
            score += 3

    for tag in profile.get("tags", []):
        if tag in tags:
            score += 2

    if item.get("priority") == "high":
        score += 1
    if item.get("crit"):
        score += 1

    return score


def personalize_news_items(items: list[dict], profile: dict) -> list[dict]:
    cutoff_ts = (utc_now() - timedelta(hours=NEWS_MAX_AGE_HOURS)).timestamp()
    recent_items = [item for item in items if float(item.get("ts", 0)) >= cutoff_ts]
    personalized = []

    relevant_items = []
    fallback_items = []
    for item in recent_items:
        score = score_news_for_profile(item, profile)
        next_item = {**item, "profile_score": score}
        if score > 0:
            next_item["priority"] = "high" if score >= 7 else "medium" if score >= 3 else next_item.get("priority", "low")
            next_item["market_moving"] = next_item.get("market_moving") or score >= 7
            relevant_items.append(next_item)
        elif item.get("priority") == "high" or item.get("crit"):
            fallback_items.append(next_item)

    if relevant_items:
        personalized = relevant_items + fallback_items
    else:
        personalized = [{**item, "profile_score": 0} for item in recent_items]

    personalized.sort(key=lambda item: item.get("ts", 0), reverse=True)
    return personalized[:80]


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


async def fetch_calendar(countries: list[str]) -> tuple[list[dict], str | None]:
    country_key = ",".join(sorted(set(countries or ["US"])))
    now = time.time()
    week_start, week_end = get_current_week_bounds()
    from_date = week_start.date().isoformat()
    to_date = (week_end - timedelta(days=1)).date().isoformat()
    cache_key = f"{country_key}:{from_date}:{to_date}"
    cached = _calendar_cache.get(cache_key)
    if cached and (now - cached["ts"]) < calendar_cache_ttl(cached["events"], now):
        return cached["events"], cached["error"]

    errors = []
    async with aiohttp.ClientSession() as session:
        payloads = []
        for country in countries or ["US"]:
            params = {
                "country": country,
                "from": from_date,
                "to": to_date,
                "apikey": FMP_API_KEY,
            }
            try:
                async with session.get("https://financialmodelingprep.com/stable/economic-calendar", params=params, timeout=20) as resp:
                    if resp.status == 429:
                        error = "Limite API calendrier atteinte"
                        _calendar_cache[cache_key] = {"events": [], "error": error, "ts": now}
                        return [], error
                    if resp.status != 200:
                        errors.append(f"{country}: HTTP {resp.status}")
                        continue
                    payloads.append(await resp.json())
            except Exception:
                errors.append(f"{country}: indisponible")
                continue

    if not payloads:
        error = "Calendar feed unavailable"
        if errors:
            error = f"Calendar feed unavailable ({', '.join(errors[:3])})"
        _calendar_cache[cache_key] = {"events": [], "error": error, "ts": now}
        return [], error

    events: list[dict] = []
    for payload in payloads:
        raw_events = payload.get("value", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_events, list):
            continue
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            normalized = normalize_calendar_event(event)
            if normalized:
                events.append(normalized)

    week_start_ts = int(week_start.timestamp())
    week_end_ts = int(week_end.timestamp())

    filtered_events = [
        event for event in events
        if week_start_ts <= event["ts"] < week_end_ts
    ]
    filtered_events = dedupe_calendar_events(filtered_events)
    _calendar_cache[cache_key] = {"events": filtered_events, "error": None, "ts": now}
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


def parse_float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(str(value).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def remember_quote_snapshot(quote: dict) -> dict:
    key = quote.get("key")
    if not key:
        return quote

    existing = _quote_latest_by_key.get(key, {})
    merged = {**existing, **quote, "received_at": time.time()}
    _quote_latest_by_key[key] = merged
    return merged


def public_quote_snapshot(quote: dict) -> dict:
    return {
        key: value
        for key, value in quote.items()
        if key not in {"ws_cluster", "ws_symbol", "fallback_symbol", "received_at"}
    }


def quote_price_from_ws_message(message: dict) -> float | None:
    last = parse_float(message.get("lp"))
    if last is not None:
        return last
    bid = parse_float(message.get("bp"))
    ask = parse_float(message.get("ap"))
    if bid is not None and ask is not None:
        return (bid + ask) / 2
    return bid if bid is not None else ask


async def broadcast_quote_update(quote: dict) -> None:
    if not _quote_ws_clients:
        return

    payload = json.dumps({"type": "quote", "item": public_quote_snapshot(quote)})
    disconnected: list[WebSocket] = []
    for websocket in list(_quote_ws_clients):
        try:
            await websocket.send_text(payload)
        except Exception:
            disconnected.append(websocket)

    for websocket in disconnected:
        _quote_ws_clients.discard(websocket)


async def handle_fmp_ws_message(raw: Any) -> None:
    messages = raw if isinstance(raw, list) else [raw]
    for message in messages:
        if not isinstance(message, dict):
            continue

        ws_symbol = str(message.get("s") or message.get("symbol") or "").lower()
        card = QUOTE_CARD_BY_WS.get(ws_symbol)
        if not card:
            continue

        price = quote_price_from_ws_message(message)
        if price is None:
            continue

        existing = _quote_latest_by_key.get(card["key"], {})
        previous = parse_float(existing.get("previous_close"))
        change = price - previous if previous not in (None, 0) else parse_float(existing.get("change")) or 0
        change_pct = (change / previous) * 100 if previous not in (None, 0) else parse_float(existing.get("change_pct")) or 0

        quote = remember_quote_snapshot({
            **card,
            "symbol": card["fmp_symbol"],
            "price": round(price, 6),
            "previous_close": previous,
            "change": round(change, 6),
            "change_pct": round(change_pct, 4),
            "high": existing.get("high"),
            "low": existing.get("low"),
            "time": message.get("t") or int(time.time()),
            "source": "FMP WS",
        })
        await broadcast_quote_update(quote)


async def run_fmp_quote_websocket(cluster: str, url: str, symbols: list[str]) -> None:
    if not symbols or not FMP_API_KEY:
        return

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url, heartbeat=25) as ws:
                    await ws.send_json({"event": "login", "data": {"apiKey": FMP_API_KEY}})
                    await ws.send_json({"event": "subscribe", "data": {"ticker": symbols}})
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                payload = json.loads(msg.data)
                            except json.JSONDecodeError:
                                continue
                            payloads = payload if isinstance(payload, list) else [payload]
                            if any(isinstance(item, dict) and int(item.get("status") or 0) >= 400 for item in payloads):
                                print(f"FMP websocket {cluster} refused subscription: {payload}")
                                break
                            await handle_fmp_ws_message(payload)
                        elif msg.type in {aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR}:
                            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"FMP websocket {cluster} disconnected: {exc}")

        await asyncio.sleep(5)


def start_fmp_quote_websockets() -> None:
    if _fmp_ws_tasks:
        return

    clusters = {
        "forex": "wss://forex.financialmodelingprep.com",
        "us-stocks": "wss://websockets.financialmodelingprep.com",
    }
    for cluster, url in clusters.items():
        symbols = sorted({
            card["ws_symbol"]
            for card in QUOTE_CARDS
            if card.get("ws_cluster") == cluster and card.get("ws_symbol")
        })
        if symbols:
            _fmp_ws_tasks.append(asyncio.create_task(run_fmp_quote_websocket(cluster, url, symbols)))


async def fetch_fmp_quote(session: aiohttp.ClientSession, card: dict) -> dict | None:
    symbol = card["fmp_symbol"]
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={FMP_API_KEY}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
    except Exception:
        return None

    raw = payload[0] if isinstance(payload, list) and payload else payload if isinstance(payload, dict) else None
    if not raw:
        return None

    price = parse_float(raw.get("price"))
    change = parse_float(raw.get("change"))
    change_pct = parse_float(raw.get("changePercentage", raw.get("changesPercentage")))
    previous = parse_float(raw.get("previousClose"))

    if price is None:
        return None
    if change is None and previous not in (None, 0):
        change = price - previous
    if change_pct is None and previous not in (None, 0) and change is not None:
        change_pct = (change / previous) * 100

    return {
        **card,
        "symbol": symbol,
        "price": round(price, 6),
        "previous_close": round(previous, 6) if previous is not None else None,
        "change": round(change or 0, 6),
        "change_pct": round(change_pct or 0, 4),
        "high": parse_float(raw.get("dayHigh")),
        "low": parse_float(raw.get("dayLow")),
        "time": raw.get("timestamp"),
        "source": "FMP",
    }


async def fetch_quote_card(session: aiohttp.ClientSession, card: dict) -> dict:
    fmp_quote = await fetch_fmp_quote(session, card)
    if fmp_quote:
        return fmp_quote

    fallback = await fetch_market_snapshot(session, card["fallback_symbol"])
    if fallback:
        return {
            **card,
            **fallback,
            "source": "YAHOO",
        }

    return {
        **card,
        "symbol": card["fmp_symbol"],
        "price": None,
        "previous_close": None,
        "change": 0,
        "change_pct": 0,
        "high": None,
        "low": None,
        "time": None,
        "source": "UNAVAILABLE",
    }


async def fetch_quote_cards() -> list[dict]:
    now = time.time()
    if _quotes_cache["data"] and (now - _quotes_cache["ts"]) < QUOTES_CACHE_TTL:
        return [public_quote_snapshot(_quote_latest_by_key.get(item["key"], item)) for item in _quotes_cache["data"]]

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        quotes = await asyncio.gather(*(fetch_quote_card(session, card) for card in QUOTE_CARDS))

    merged_quotes = []
    for quote in quotes:
        existing = _quote_latest_by_key.get(quote["key"])
        if existing and existing.get("source") == "FMP WS" and (now - float(existing.get("received_at", 0))) < 60:
            quote = {**quote, **existing}
        merged_quotes.append(remember_quote_snapshot(quote))

    _quotes_cache["data"] = merged_quotes
    _quotes_cache["ts"] = now
    return [public_quote_snapshot(quote) for quote in merged_quotes]


def evaluate_driver(
    *,
    key: str,
    label: str,
    value: float,
    change_pct: float,
    bullish_when: str,
    weight: float,
    strong_threshold: float,
    medium_threshold: float,
    bullish_note: str,
    bearish_note: str,
    neutral_note: str,
) -> dict:
    magnitude = abs(change_pct)
    if magnitude >= strong_threshold:
        intensity = 1.0
    elif magnitude >= medium_threshold:
        intensity = 0.5
    else:
        intensity = 0.0

    direction = 0
    if intensity > 0:
        if bullish_when == "down":
            direction = 1 if change_pct < 0 else -1
        else:
            direction = 1 if change_pct > 0 else -1

    contribution = round(direction * weight * intensity, 2)
    bias = "bullish" if contribution > 0 else "bearish" if contribution < 0 else "neutral"
    note = bullish_note if contribution > 0 else bearish_note if contribution < 0 else neutral_note

    return {
        "key": key,
        "label": label,
        "value": value,
        "change_pct": round(change_pct, 3),
        "bias": bias,
        "contribution": contribution,
        "weight": weight,
        "note": note,
    }


def score_bucket(score: float, bullish_label: str = "Bullish", bearish_label: str = "Bearish") -> str:
    if score >= 1.2:
        return bullish_label
    if score <= -1.2:
        return bearish_label
    return "Neutral"


def build_event_risk(events: list[dict] | None = None) -> dict:
    now_ts = int(time.time())
    upcoming = [
        event for event in events or []
        if event.get("ts", 0) >= now_ts and event.get("impact") in {"High", "Medium"}
    ]
    upcoming.sort(key=lambda item: item["ts"])
    next_high = next((event for event in upcoming if event.get("impact") == "High"), None)
    next_event = next_high or (upcoming[0] if upcoming else None)

    if not next_event:
        return {
            "level": "Low",
            "score": 0,
            "minutes": None,
            "title": "No high-impact event nearby",
            "action": "Tradeable",
        }

    minutes = max(0, int((next_event["ts"] - now_ts) / 60))
    if next_event.get("impact") == "High" and minutes <= 45:
        level = "High"
        score = 3
        action = "No Trade"
    elif next_event.get("impact") == "High" and minutes <= 120:
        level = "Elevated"
        score = 2
        action = "Reduce Risk"
    elif next_event.get("impact") == "Medium" and minutes <= 45:
        level = "Elevated"
        score = 1
        action = "Caution"
    else:
        level = "Low"
        score = 0
        action = "Tradeable"

    return {
        "level": level,
        "score": score,
        "minutes": minutes,
        "title": next_event.get("title") or "Upcoming macro event",
        "impact": next_event.get("impact"),
        "country": next_event.get("country"),
        "action": action,
    }


def build_gold_context(markets: dict[str, dict], events: list[dict] | None = None) -> dict:
    gold = markets.get("gold")
    silver = markets.get("silver")
    dxy = markets.get("dxy")
    us10y = markets.get("us10y")
    oil = markets.get("oil")
    spy = markets.get("spy")
    qqq = markets.get("qqq")

    drivers = []

    if dxy:
        drivers.append(evaluate_driver(
            key="dxy",
            label="Dollar",
            value=dxy["price"],
            change_pct=dxy["change_pct"],
            bullish_when="down",
            weight=3.0,
            strong_threshold=0.25,
            medium_threshold=0.10,
            bullish_note="Dollar softer supports gold",
            bearish_note="Dollar strength pressures gold",
            neutral_note="Dollar impact limited",
        ))

    if us10y:
        drivers.append(evaluate_driver(
            key="us10y",
            label="US10Y",
            value=us10y["price"],
            change_pct=us10y["change_pct"],
            bullish_when="down",
            weight=3.0,
            strong_threshold=0.30,
            medium_threshold=0.12,
            bullish_note="Yields easing supports gold",
            bearish_note="Yields rising pressures gold",
            neutral_note="Yield pressure mixed",
        ))

    if gold:
        drivers.append(evaluate_driver(
            key="gold_momo",
            label="Gold",
            value=gold["price"],
            change_pct=gold["change_pct"],
            bullish_when="up",
            weight=2.0,
            strong_threshold=0.90,
            medium_threshold=0.35,
            bullish_note="Gold momentum confirms buyers",
            bearish_note="Gold momentum confirms sellers",
            neutral_note="Gold momentum undecided",
        ))

    if silver:
        drivers.append(evaluate_driver(
            key="silver",
            label="Silver",
            value=silver["price"],
            change_pct=silver["change_pct"],
            bullish_when="up",
            weight=1.0,
            strong_threshold=1.00,
            medium_threshold=0.40,
            bullish_note="Silver confirms metals bid",
            bearish_note="Silver weakens metals tone",
            neutral_note="Silver not confirming",
        ))

    if oil:
        drivers.append(evaluate_driver(
            key="oil",
            label="WTI",
            value=oil["price"],
            change_pct=oil["change_pct"],
            bullish_when="up",
            weight=1.0,
            strong_threshold=1.20,
            medium_threshold=0.50,
            bullish_note="Energy stress can lift gold",
            bearish_note="Oil easing cools stress bid",
            neutral_note="Oil impact limited",
        ))

    if spy and qqq:
        risk_change = (spy["change_pct"] + qqq["change_pct"]) / 2
        drivers.append(evaluate_driver(
            key="risk",
            label="Risk",
            value=round(risk_change, 3),
            change_pct=risk_change,
            bullish_when="down",
            weight=1.5,
            strong_threshold=0.90,
            medium_threshold=0.35,
            bullish_note="Risk-off tone supports gold",
            bearish_note="Risk appetite weighs on gold",
            neutral_note="Risk tone mixed",
        ))

    score = round(sum(driver["contribution"] for driver in drivers), 2)
    max_score = round(sum(driver["weight"] for driver in drivers), 2) or 1.0
    macro_keys = {"dxy", "us10y", "oil"}
    momentum_keys = {"gold_momo", "silver", "risk"}
    macro_score = round(sum(driver["contribution"] for driver in drivers if driver["key"] in macro_keys), 2)
    momentum_score = round(sum(driver["contribution"] for driver in drivers if driver["key"] in momentum_keys), 2)
    event_risk = build_event_risk(events)

    if score >= 2.5:
        bias = "Bullish"
        tone = "macro support building"
    elif score <= -2.5:
        bias = "Bearish"
        tone = "macro pressure building"
    else:
        bias = "Neutral"
        tone = "signals mixed"

    directional_drivers = [driver for driver in drivers if driver["contribution"] != 0]
    if directional_drivers:
        bias_sign = 1 if score > 0 else -1 if score < 0 else 0
        aligned = sum(
            1 for driver in directional_drivers
            if (driver["contribution"] > 0 and bias_sign > 0) or (driver["contribution"] < 0 and bias_sign < 0)
        )
        alignment_ratio = aligned / len(directional_drivers) if bias_sign != 0 else 0.5
    else:
        alignment_ratio = 0.0

    magnitude_ratio = min(1.0, abs(score) / max_score)
    if bias == "Neutral":
        confidence = int(round((0.25 + magnitude_ratio * 0.35 + alignment_ratio * 0.15) * 100))
    else:
        confidence = int(round((magnitude_ratio * 0.6 + alignment_ratio * 0.4) * 100))
    confidence = max(18, min(confidence, 92))
    if event_risk["level"] == "High":
        confidence = min(confidence, 58)
    elif event_risk["level"] == "Elevated":
        confidence = min(confidence, 72)

    top_reasons = [
        driver["note"]
        for driver in sorted(directional_drivers, key=lambda item: abs(item["contribution"]), reverse=True)[:3]
    ]
    if not top_reasons:
        top_reasons = ["Cross-asset signals are not decisive"]

    if bias == "Bullish":
        summary = " / ".join(top_reasons[:2])
    elif bias == "Bearish":
        summary = " / ".join(top_reasons[:2])
    else:
        summary = " / ".join(top_reasons[:2])

    conflicting = (
        (macro_score > 1.2 and momentum_score < -1.2)
        or (macro_score < -1.2 and momentum_score > 1.2)
    )
    if event_risk["level"] == "High":
        action = "NO TRADE"
        action_reason = f"{event_risk['title']} in {event_risk['minutes']} min"
    elif confidence < 45 or conflicting or bias == "Neutral":
        action = "WAIT"
        action_reason = "Drivers mixed or confidence too low"
    elif bias == "Bullish":
        action = "LONG ONLY"
        action_reason = "Macro/momentum alignment favors upside"
    else:
        action = "SHORT ONLY"
        action_reason = "Macro/momentum alignment favors downside"

    if bias == "Bullish":
        invalidation = "XAU loses momentum while DXY/yields turn higher"
    elif bias == "Bearish":
        invalidation = "XAU reclaims momentum while DXY/yields roll over"
    else:
        invalidation = "Wait for macro and price momentum to align"

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
        "confidence": confidence,
        "summary": summary,
        "reasons": top_reasons,
        "action": action,
        "action_reason": action_reason,
        "invalidation": invalidation,
        "layers": {
            "macro": {"label": score_bucket(macro_score), "score": macro_score},
            "momentum": {"label": score_bucket(momentum_score), "score": momentum_score},
            "event_risk": event_risk,
        },
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


def build_market_context(profile_id: str, markets: dict[str, dict], events: list[dict] | None = None) -> dict:
    config = BIAS_PROFILES.get(profile_id, BIAS_PROFILES["xauusd"])
    drivers = []

    for spec in config["drivers"]:
        market = markets.get(spec["key"])
        if not market:
            continue
        drivers.append({
            **evaluate_driver(
                key=spec.get("driver_key", spec["key"]),
                label=spec["label"],
                value=market["price"],
                change_pct=market["change_pct"],
                bullish_when=spec["bullish_when"],
                weight=spec["weight"],
                strong_threshold=spec["strong"],
                medium_threshold=spec["medium"],
                bullish_note=spec["bullish"],
                bearish_note=spec["bearish"],
                neutral_note=spec["neutral"],
            ),
            "layer": spec.get("layer", "momentum"),
        })

    score = round(sum(driver["contribution"] for driver in drivers), 2)
    max_score = round(sum(driver["weight"] for driver in drivers), 2) or 1.0
    macro_score = round(sum(driver["contribution"] for driver in drivers if driver.get("layer") == "macro"), 2)
    momentum_score = round(sum(driver["contribution"] for driver in drivers if driver.get("layer") in {"momentum", "risk"}), 2)
    event_risk = build_event_risk(events)

    if score >= 2.5:
        bias = "Bullish"
        tone = "support building"
    elif score <= -2.5:
        bias = "Bearish"
        tone = "pressure building"
    else:
        bias = "Neutral"
        tone = "signals mixed"

    directional_drivers = [driver for driver in drivers if driver["contribution"] != 0]
    if directional_drivers:
        bias_sign = 1 if score > 0 else -1 if score < 0 else 0
        aligned = sum(
            1 for driver in directional_drivers
            if (driver["contribution"] > 0 and bias_sign > 0) or (driver["contribution"] < 0 and bias_sign < 0)
        )
        alignment_ratio = aligned / len(directional_drivers) if bias_sign != 0 else 0.5
    else:
        alignment_ratio = 0.0

    magnitude_ratio = min(1.0, abs(score) / max_score)
    if bias == "Neutral":
        confidence = int(round((0.25 + magnitude_ratio * 0.35 + alignment_ratio * 0.15) * 100))
    else:
        confidence = int(round((magnitude_ratio * 0.6 + alignment_ratio * 0.4) * 100))
    confidence = max(18, min(confidence, 92))
    if event_risk["level"] == "High":
        confidence = min(confidence, 58)
    elif event_risk["level"] == "Elevated":
        confidence = min(confidence, 72)

    top_reasons = [
        driver["note"]
        for driver in sorted(directional_drivers, key=lambda item: abs(item["contribution"]), reverse=True)[:3]
    ] or ["Cross-asset signals are not decisive"]
    summary = " / ".join(top_reasons[:2])

    conflicting = (
        (macro_score > 1.2 and momentum_score < -1.2)
        or (macro_score < -1.2 and momentum_score > 1.2)
    )
    if event_risk["level"] == "High":
        action = "NO TRADE"
        action_reason = f"{event_risk['title']} in {event_risk['minutes']} min"
    elif confidence < 45 or conflicting or bias == "Neutral":
        action = "WAIT"
        action_reason = "Drivers mixed or confidence too low"
    elif bias == "Bullish":
        action = config["bullish_action"]
        action_reason = "Macro/momentum alignment favors upside"
    else:
        action = config["bearish_action"]
        action_reason = "Macro/momentum alignment favors downside"

    if bias == "Bullish":
        invalidation = f"{config['target_label']} loses momentum while macro drivers reverse"
    elif bias == "Bearish":
        invalidation = f"{config['target_label']} reclaims momentum while macro drivers reverse"
    else:
        invalidation = "Wait for macro and price momentum to align"

    now_hour = datetime.now(PARIS).hour
    if 14 <= now_hour < 17:
        active_session = "LONDON / NEW YORK"
        volatility = "HIGH"
    elif 17 <= now_hour < 22:
        active_session = "NEW YORK"
        volatility = "ELEVATED"
    elif 8 <= now_hour < 14:
        active_session = "LONDON"
        volatility = "ACTIVE"
    else:
        active_session = "ASIA"
        volatility = "QUIET"

    target = markets.get(config["target_key"])
    watch_keys = list(dict.fromkeys([config["target_key"], "dxy", "us10y", "gold", "qqq", "spy", "oil", "btc"]))
    return {
        "profile": profile_id,
        "title": config["title"],
        "bias_name": config["bias_name"],
        "target_label": config["target_label"],
        "bias": bias,
        "score": score,
        "tone": tone,
        "confidence": confidence,
        "summary": summary,
        "reasons": top_reasons,
        "action": action,
        "action_reason": action_reason,
        "invalidation": invalidation,
        "layers": {
            "macro": {"label": score_bucket(macro_score), "score": macro_score},
            "momentum": {"label": score_bucket(momentum_score), "score": momentum_score},
            "event_risk": event_risk,
        },
        "volatility": volatility,
        "session": active_session,
        "drivers": drivers,
        "watchlist": [
            {"key": key, "label": MARKET_SYMBOLS[key]["label"], **markets[key]}
            for key in watch_keys
            if key in markets and key in MARKET_SYMBOLS
        ],
        "available_watchlist": [
            {"key": key, "label": MARKET_SYMBOLS[key]["label"], **markets[key]}
            for key in MARKET_SYMBOLS
            if key in markets
        ],
        "target": target,
        "gold": markets.get("gold"),
    }


async def fetch_market_context(profile_id: Optional[str] = None, countries: Optional[str] = None) -> dict:
    profile = get_market_profile(profile_id)
    bias_profile_id = profile["id"] if profile["id"] in BIAS_PROFILES else "xauusd"
    event_countries = parse_country_filter(countries, profile.get("calendar_countries", ["US"]))
    cache_key = f"{bias_profile_id}:{','.join(event_countries)}"
    now = time.time()
    cached = _context_cache.get(cache_key)
    if cached and (now - cached["ts"]) < CONTEXT_CACHE_TTL:
        return cached["data"]

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
    events, _error = await fetch_calendar(event_countries)
    context = build_market_context(bias_profile_id, markets, events)
    _context_cache[cache_key] = {"data": context, "ts": now}
    return context
