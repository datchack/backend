from __future__ import annotations

import asyncio
from datetime import datetime
import time

import aiohttp

from app.config import FMP_API_KEY, PARIS
from app.services.accounts import utc_now
from app.services.calendar import fetch_calendar
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
from app.services.profiles import get_market_profile
from app.services.quotes import fetch_quote_cards


_pulse_cache: dict = {"data": None, "ts": 0.0}
PULSE_CACHE_TTL = 90


def _priority_weight(item: dict) -> int:
    priority = str(item.get("priority") or "low")
    return {"high": 3, "medium": 2, "low": 1}.get(priority, 1)


def _format_time(ts: float | int | None) -> str:
    if not ts:
        return "--:--"
    return datetime.fromtimestamp(float(ts), tz=PARIS).strftime("%H:%M")


def _minutes_until(ts: float | int | None) -> int | None:
    if not ts:
        return None
    return max(0, int((float(ts) - time.time()) / 60))


def _quote_direction(change_pct: float | int | None) -> str:
    value = float(change_pct or 0)
    if value >= 0.35:
        return "UP"
    if value <= -0.35:
        return "DOWN"
    return "MIXED"


def _quote_activity(change_pct: float | int | None) -> str:
    value = abs(float(change_pct or 0))
    if value >= 1.0:
        return "Active"
    if value >= 0.35:
        return "Watch"
    return "Calm"


async def _fetch_public_news() -> list[dict]:
    now = time.time()
    profile = get_market_profile("xauusd")
    if _news_cache["data"] and (now - _news_cache["ts"]) < NEWS_CACHE_TTL:
        return personalize_news_items(_news_cache["data"], profile)

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        results = await asyncio.gather(*(_fetch_source(session, name, config) for name, config in NEWS_SOURCES.items()))

    all_news = dedupe_news_items([item for chunk in results for item in chunk])[:100]
    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return personalize_news_items(all_news, profile)


async def _fetch_public_calendar() -> tuple[list[dict], str | None]:
    if not FMP_API_KEY:
        return [], "Calendrier indisponible"
    events, error = await fetch_calendar(["US", "EU", "GB", "JP"])
    return events, error


def _public_news_items(items: list[dict]) -> list[dict]:
    public_items = sorted(
        items,
        key=lambda item: (_priority_weight(item), int(item.get("news_score") or 0), float(item.get("ts") or 0)),
        reverse=True,
    )
    return [
        {
            "title": item.get("t") or "Market news",
            "source": item.get("s") or "NEWS",
            "url": item.get("l") or "",
            "time": item.get("time") or _format_time(item.get("ts")),
            "priority": item.get("priority") or "low",
            "tags": (item.get("tags") or [])[:3],
        }
        for item in public_items[:5]
    ]


def _public_calendar_items(events: list[dict]) -> list[dict]:
    now_ts = time.time()
    upcoming = [
        event for event in events
        if float(event.get("ts") or 0) >= now_ts and event.get("impact") in {"High", "Medium"}
    ]
    upcoming.sort(key=lambda event: (
        float(event.get("ts") or 0),
        {"High": 0, "Medium": 1, "Low": 2}.get(event.get("impact"), 3),
        -int(event.get("market_priority") or 0),
    ))
    return [
        {
            "title": event.get("title") or "Economic event",
            "country": event.get("country") or "-",
            "impact": event.get("impact") or "-",
            "time": _format_time(event.get("ts")),
            "minutes": _minutes_until(event.get("ts")),
            "label": event.get("market_label") or "WATCH",
        }
        for event in upcoming[:5]
    ]


def _public_assets(quotes: list[dict], context: dict) -> list[dict]:
    quote_by_key = {item.get("key"): item for item in quotes if item.get("key")}
    driver_by_key = {item.get("key"): item for item in context.get("drivers") or []}
    assets = [
        ("xauusd", "XAU/USD", "gold_momo"),
        ("dxy", "DXY", "dxy"),
        ("tlt", "TLT", "us10y"),
        ("eurusd", "EUR/USD", None),
        ("qqq", "NASDAQ", None),
        ("spy", "S&P 500", None),
    ]
    public_assets = []
    for key, label, driver_key in assets:
        quote = quote_by_key.get(key)
        if not quote:
            continue
        change_pct = quote.get("change_pct")
        driver = driver_by_key.get(driver_key or key, {})
        public_assets.append({
            "key": key,
            "label": label,
            "direction": _quote_direction(change_pct),
            "activity": _quote_activity(change_pct),
            "bias": driver.get("bias") or "neutral",
            "note": driver.get("note") or "Lecture complète dans le terminal",
        })
    return public_assets[:6]


def _build_public_summary(news: list[dict], calendar: list[dict], context: dict) -> dict:
    event_risk = ((context.get("layers") or {}).get("event_risk") or {})
    high_news = sum(1 for item in news if item.get("priority") == "high")
    risk_points = 35
    if event_risk.get("level") == "High":
        risk_points += 35
    elif event_risk.get("level") == "Elevated":
        risk_points += 22
    if calendar:
        risk_points += min(20, len(calendar) * 4)
    risk_points += min(12, high_news * 4)
    risk_score = max(20, min(94, risk_points))
    if risk_score >= 72:
        risk_label = "Risque élevé"
    elif risk_score >= 52:
        risk_label = "Risque actif"
    else:
        risk_label = "Risque modéré"

    next_event = calendar[0] if calendar else None
    top_news = news[0] if news else None
    if next_event and top_news:
        headline = f"{next_event['country']} {next_event['impact']} à {next_event['time']} / news {top_news['source']}"
    elif next_event:
        headline = f"{next_event['country']} {next_event['impact']} à {next_event['time']}"
    elif top_news:
        headline = f"News prioritaire: {top_news['source']}"
    else:
        headline = "Marché à surveiller"

    return {
        "risk_score": risk_score,
        "risk_label": risk_label,
        "headline": headline,
        "bias": context.get("bias") or "Neutral",
        "action": context.get("action") or "WAIT",
        "summary": context.get("summary") or "Les signaux publics restent limités. Le détail complet est disponible dans le terminal.",
    }


async def build_public_market_pulse(force: bool = False) -> dict:
    now = time.time()
    if not force and _pulse_cache["data"] and (now - _pulse_cache["ts"]) < PULSE_CACHE_TTL:
        return _pulse_cache["data"]

    news_result, calendar_result, quotes, context = await asyncio.gather(
        _fetch_public_news(),
        _fetch_public_calendar(),
        fetch_quote_cards(),
        fetch_market_context("xauusd", "US,EU,GB,JP"),
    )
    calendar_events, calendar_error = calendar_result
    public_news = _public_news_items(news_result)
    public_calendar = _public_calendar_items(calendar_events)
    public_assets = _public_assets(quotes, context)
    summary = _build_public_summary(public_news, public_calendar, context)

    data = {
        "generated_at": utc_now().astimezone(PARIS).strftime("%d/%m/%Y %H:%M"),
        "window_hours": NEWS_MAX_AGE_HOURS,
        "summary": summary,
        "news": public_news,
        "calendar": public_calendar,
        "assets": public_assets,
        "drivers": (context.get("drivers") or [])[:4],
        "calendar_error": calendar_error,
        "locked_note": "Les chiffres actual/forecast/previous, le Bias Desk complet et les filtres avancés sont réservés au terminal.",
    }
    _pulse_cache["data"] = data
    _pulse_cache["ts"] = now
    return data
