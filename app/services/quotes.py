from __future__ import annotations

import asyncio
import json
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
