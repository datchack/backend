import json
from typing import Any

from fastapi import HTTPException


PREFS_MAX_BYTES = 32 * 1024
PREFS_ALLOWED_KEYS = {
    "marketProfile",
    "symbol",
    "soundEnabled",
    "soundType",
    "centerTab",
    "impactFilters",
    "calendarCountries",
    "watchlistKeys",
    "widgets",
    "layout",
}


def validate_preferences_payload(prefs: Any) -> dict[str, Any]:
    if not isinstance(prefs, dict):
        raise HTTPException(status_code=400, detail="Preferences invalides")

    unknown_keys = set(prefs) - PREFS_ALLOWED_KEYS
    if unknown_keys:
        raise HTTPException(status_code=400, detail="Preferences non reconnues")

    try:
        encoded = json.dumps(prefs)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Preferences invalides") from exc

    if len(encoded.encode("utf-8")) > PREFS_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Preferences trop volumineuses")

    return prefs
