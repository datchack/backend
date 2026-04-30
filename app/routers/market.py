import asyncio
import time
from typing import Optional

import aiohttp
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from app.config import SESSION_COOKIE
from app.services.accounts import get_user_by_session, require_terminal_access
from app.services.calendar import calendar_refresh_ms, fetch_calendar, get_current_week_bounds, require_fmp_key
from app.services.context import fetch_market_context
from app.services.news import (
    NEWS_CACHE_TTL,
    NEWS_MAX_AGE_HOURS,
    NEWS_SOURCES,
    _fetch_source,
    _news_cache,
    dedupe_news_items,
    personalize_news_items,
)
from app.services.profiles import MARKET_PROFILES, get_market_profile, parse_country_filter
from app.services.quotes import (
    QUOTE_CARDS,
    _quote_latest_by_key,
    _quote_ws_clients,
    _quotes_cache,
    fetch_quote_cards,
    public_quote_snapshot,
)

router = APIRouter()

@router.get("/api/market-profiles")
async def market_profiles(request: Request):
    require_terminal_access(request)
    return {"profiles": list(MARKET_PROFILES.values())}


@router.get("/api/market-quotes")
async def market_quotes(request: Request):
    require_terminal_access(request)
    quotes = await fetch_quote_cards()
    return {
        "items": quotes,
        "count": len(quotes),
        "cached": bool(_quotes_cache["data"]),
        "age": int(time.time() - _quotes_cache["ts"]) if _quotes_cache["ts"] else 0,
    }


@router.websocket("/ws/market-quotes")
async def market_quotes_ws(websocket: WebSocket):
    user = get_user_by_session(websocket.cookies.get(SESSION_COOKIE))
    if not user or not user.get("has_access"):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    _quote_ws_clients.add(websocket)
    try:
        await websocket.send_json({
            "type": "snapshot",
            "items": [public_quote_snapshot(_quote_latest_by_key.get(card["key"], card)) for card in QUOTE_CARDS],
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _quote_ws_clients.discard(websocket)


@router.get("/api/news")
async def get_news(request: Request, profile: Optional[str] = None):
    require_terminal_access(request)
    market_profile = get_market_profile(profile)
    now = time.time()
    if _news_cache["data"] and (now - _news_cache["ts"]) < NEWS_CACHE_TTL:
        return {
            "items": personalize_news_items(_news_cache["data"], market_profile),
            "profile": market_profile["id"],
            "window_hours": NEWS_MAX_AGE_HOURS,
            "cached": True,
            "age": int(now - _news_cache["ts"]),
        }

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        results = await asyncio.gather(*(_fetch_source(session, name, url) for name, url in NEWS_SOURCES.items()))

    all_news = [item for chunk in results for item in chunk]
    all_news = dedupe_news_items(all_news)
    all_news = all_news[:100]

    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return {
        "items": personalize_news_items(all_news, market_profile),
        "profile": market_profile["id"],
        "window_hours": NEWS_MAX_AGE_HOURS,
        "cached": False,
        "age": 0,
    }


@router.get("/api/calendar")
async def get_calendar(request: Request, profile: Optional[str] = None, countries: Optional[str] = None):
    require_terminal_access(request)
    require_fmp_key()
    market_profile = get_market_profile(profile)
    calendar_countries = parse_country_filter(countries, market_profile.get("calendar_countries", ["US"]))
    events, error = await fetch_calendar(calendar_countries)
    week_start, week_end = get_current_week_bounds()
    if error:
        return {
            "events": [],
            "count": 0,
            "timezone": "Europe/Paris",
            "profile": market_profile["id"],
            "countries": calendar_countries,
            "hot": False,
            "release_watch": False,
            "refresh_ms": 30000,
            "error": error,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }

    now_ts = int(time.time())
    hot = any(0 <= (event["ts"] - now_ts) <= 3600 for event in events)
    release_watch = any(abs(event["ts"] - now_ts) <= 900 and event.get("impact") in {"High", "Medium"} for event in events)
    refresh_ms = calendar_refresh_ms(events, now_ts)

    return {
        "events": events,
        "count": len(events),
        "timezone": "Europe/Paris",
        "profile": market_profile["id"],
        "countries": calendar_countries,
        "hot": hot,
        "release_watch": release_watch,
        "refresh_ms": refresh_ms,
        "error": None,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "cached_items": len(_news_cache["data"]),
        "cache_age": int(time.time() - _news_cache["ts"]) if _news_cache["ts"] else None,
    }


@router.get("/api/context")
async def get_context(request: Request, profile: Optional[str] = None, countries: Optional[str] = None):
    require_terminal_access(request)
    context = await fetch_market_context(profile, countries)
    return context
