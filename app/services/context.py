from __future__ import annotations

from datetime import datetime
import asyncio
import time
from typing import Optional

import aiohttp

from app.config import *
from app.services.calendar import fetch_calendar
from app.services.profiles import get_market_profile, parse_country_filter
from app.services.quotes import fetch_market_snapshot


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
    """Score a market driver contribution toward directional bias."""
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
