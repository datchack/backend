from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any

import aiohttp
from fastapi import HTTPException

from app.config import CALENDAR_TZ, FMP_API_KEY


_calendar_cache: dict[str, dict] = {}
CALENDAR_CACHE_TTL = 30
CALENDAR_HOT_CACHE_TTL = 2


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
