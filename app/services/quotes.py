from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

import aiohttp
from fastapi import WebSocket

from app.config import FMP_API_KEY


_quotes_cache: dict = {"data": None, "ts": 0.0}
QUOTES_CACHE_TTL = 5
_quote_latest_by_key: dict[str, dict] = {}
_quote_ws_clients: set[WebSocket] = set()
_fmp_ws_tasks: list[asyncio.Task] = []

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
QUOTE_CARD_BY_TV = {
    re.sub(r"[^A-Z0-9]", "", card["tv_symbol"].split(":")[-1].upper()): card
    for card in QUOTE_CARDS
}

CUSTOM_SYMBOLS = {
    "XAUUSD": {"symbol": "GC=F", "tv_symbol": "OANDA:XAUUSD", "label": "XAU/USD", "decimals": 2},
    "XAGUSD": {"symbol": "SI=F", "tv_symbol": "OANDA:XAGUSD", "label": "XAG/USD", "decimals": 4},
    "XPTUSD": {"symbol": "PL=F", "tv_symbol": "OANDA:XPTUSD", "label": "XPT/USD", "decimals": 2},
    "XPDUSD": {"symbol": "PA=F", "tv_symbol": "OANDA:XPDUSD", "label": "XPD/USD", "decimals": 2},
    "DXY": {"symbol": "DX-Y.NYB", "tv_symbol": "CAPITALCOM:DXY", "label": "DXY", "decimals": 3},
    "US10Y": {"symbol": "^TNX", "tv_symbol": "TVC:US10Y", "label": "US10Y", "decimals": 3},
    "SPX": {"symbol": "^GSPC", "tv_symbol": "SP:SPX", "label": "S&P 500", "decimals": 2},
    "DJI": {"symbol": "^DJI", "tv_symbol": "DJ:DJI", "label": "DOW", "decimals": 2},
    "RUT": {"symbol": "^RUT", "tv_symbol": "TVC:RUT", "label": "RUSSELL", "decimals": 2},
    "DAX": {"symbol": "^GDAXI", "tv_symbol": "XETR:DAX", "label": "DAX 40", "decimals": 2},
    "PX1": {"symbol": "^FCHI", "tv_symbol": "EURONEXT:PX1", "label": "CAC 40", "decimals": 2},
    "UKX": {"symbol": "^FTSE", "tv_symbol": "TVC:UKX", "label": "FTSE 100", "decimals": 2},
    "NI225": {"symbol": "^N225", "tv_symbol": "TVC:NI225", "label": "NIKKEI", "decimals": 2},
    "HSI": {"symbol": "^HSI", "tv_symbol": "HSI:HSI", "label": "HANG SENG", "decimals": 2},
    "VIX": {"symbol": "^VIX", "tv_symbol": "TVC:VIX", "label": "VIX", "decimals": 2},
    "USOIL": {"symbol": "CL=F", "tv_symbol": "TVC:USOIL", "label": "WTI", "decimals": 2},
    "UKOIL": {"symbol": "BZ=F", "tv_symbol": "TVC:UKOIL", "label": "BRENT", "decimals": 2},
    "NATGAS": {"symbol": "NG=F", "tv_symbol": "TVC:NATGAS", "label": "NATGAS", "decimals": 3},
    "HG1": {"symbol": "HG=F", "tv_symbol": "COMEX:HG1!", "label": "COPPER", "decimals": 4},
    "BTCUSD": {"symbol": "BTC-USD", "tv_symbol": "BITSTAMP:BTCUSD", "label": "BTC/USD", "decimals": 2},
    "ETHUSD": {"symbol": "ETH-USD", "tv_symbol": "BITSTAMP:ETHUSD", "label": "ETH/USD", "decimals": 2},
    "US02Y": {"symbol": "^IRX", "tv_symbol": "TVC:US02Y", "label": "US02Y", "decimals": 3},
    "SX5E": {"symbol": "^STOXX50E", "tv_symbol": "TVC:SX5E", "label": "EURO STOXX", "decimals": 2},
    "XJO": {"symbol": "^AXJO", "tv_symbol": "ASX:XJO", "label": "ASX 200", "decimals": 2},
    "TSX": {"symbol": "^GSPTSE", "tv_symbol": "TSX:TSX", "label": "TSX", "decimals": 2},
    "ZC1": {"symbol": "ZC=F", "tv_symbol": "CBOT:ZC1!", "label": "CORN", "decimals": 2},
    "ZW1": {"symbol": "ZW=F", "tv_symbol": "CBOT:ZW1!", "label": "WHEAT", "decimals": 2},
    "ZS1": {"symbol": "ZS=F", "tv_symbol": "CBOT:ZS1!", "label": "SOYBEANS", "decimals": 2},
    "RB1": {"symbol": "RB=F", "tv_symbol": "NYMEX:RB1!", "label": "GASOLINE", "decimals": 4},
}

CURRENCY_CODES = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "CNY", "HKD"}
CRYPTO_CODES = {
    "BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "LINK", "LTC",
    "DOT", "BCH", "UNI", "AAVE", "NEAR", "ATOM", "TRX",
}


def normalize_custom_symbol(symbol: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(symbol or "").split(":")[-1].upper())


def forex_yahoo_symbol(base: str, quote: str) -> str:
    if base == "USD":
        return f"{quote}=X"
    return f"{base}{quote}=X"


def format_custom_label(normalized: str) -> str:
    if len(normalized) == 6 and normalized[:3] in CURRENCY_CODES and normalized[3:] in CURRENCY_CODES:
        return f"{normalized[:3]}/{normalized[3:]}"
    if normalized.endswith("USD") and normalized[:-3] in CRYPTO_CODES:
        return f"{normalized[:-3]}/USD"
    return normalized


def custom_quote_card(symbol: str) -> dict | None:
    raw_symbol = str(symbol or "").strip().upper()
    normalized = normalize_custom_symbol(raw_symbol)
    if not normalized:
        return None

    known = QUOTE_CARD_BY_TV.get(normalized)
    if known:
        return known

    special = CUSTOM_SYMBOLS.get(normalized)
    if special:
        return {
            "key": f"custom_{normalized.lower()}",
            "name": special["label"],
            "fallback_symbol": special["symbol"],
            **special,
        }

    if len(normalized) == 6 and normalized[:3] in CURRENCY_CODES and normalized[3:] in CURRENCY_CODES:
        base = normalized[:3]
        quote = normalized[3:]
        return {
            "key": f"custom_{normalized.lower()}",
            "label": f"{base}/{quote}",
            "name": "FOREX",
            "symbol": forex_yahoo_symbol(base, quote),
            "fallback_symbol": forex_yahoo_symbol(base, quote),
            "tv_symbol": raw_symbol if ":" in raw_symbol else f"FX:{normalized}",
            "decimals": 5,
        }

    if normalized.endswith("USDT") and normalized[:-4] in CRYPTO_CODES:
        normalized = f"{normalized[:-4]}USD"

    if normalized.endswith("USD") and normalized[:-3] in CRYPTO_CODES:
        base = normalized[:-3]
        return {
            "key": f"custom_{normalized.lower()}",
            "label": f"{base}/USD",
            "name": "CRYPTO",
            "symbol": f"{base}-USD",
            "fallback_symbol": f"{base}-USD",
            "tv_symbol": raw_symbol if ":" in raw_symbol else f"BITSTAMP:{normalized}",
            "decimals": 2,
        }

    return {
        "key": f"custom_{normalized.lower()}",
        "label": format_custom_label(normalized),
        "name": "CUSTOM",
        "symbol": normalized.replace(".", "-"),
        "fallback_symbol": normalized.replace(".", "-"),
        "tv_symbol": raw_symbol if ":" in raw_symbol else normalized,
        "decimals": 2,
    }


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
        "source": "YAHOO",
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
    fmp_quote = await fetch_fmp_quote(session, card) if card.get("fmp_symbol") else None
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
        "symbol": card.get("fmp_symbol") or card.get("symbol") or card.get("fallback_symbol"),
        "price": None,
        "previous_close": None,
        "change": 0,
        "change_pct": 0,
        "high": None,
        "low": None,
        "time": None,
        "source": "UNAVAILABLE",
    }


async def fetch_custom_quote_cards(symbols: list[str]) -> list[dict]:
    cards = []
    seen = set()
    for symbol in symbols[:8]:
        card = custom_quote_card(symbol)
        if not card:
            continue
        key = card["key"]
        if key in seen:
            continue
        seen.add(key)
        cards.append(card)

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        quotes = await asyncio.gather(*(fetch_quote_card(session, card) for card in cards))

    return [public_quote_snapshot(quote) for quote in quotes]


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
