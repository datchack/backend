from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import hashlib
import json
import os
import secrets
import sqlite3
import time
from typing import Any
from zoneinfo import ZoneInfo

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

import aiohttp
import feedparser
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas configurée")
    if psycopg2 is None:
        raise RuntimeError("psycopg2 n'est pas installe")
    
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )
PARIS = ZoneInfo("Europe/Paris")

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

FMP_API_KEY = "JIUCkZ8STWgYWPA03dt64CxksXRVHWyX"
FMP_URL = f"https://financialmodelingprep.com/stable/economic-calendar?country=US&apikey={FMP_API_KEY}"
CALENDAR_TZ = PARIS

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30
_context_cache: dict = {"data": None, "ts": 0.0}
CONTEXT_CACHE_TTL = 30
ACCOUNT_DB_PATH = os.path.join(os.path.dirname(__file__), "terminal_users.db")
ACCOUNT_DB_BACKEND = "postgres" if DATABASE_URL else "sqlite"
SESSION_COOKIE = "tt_session"
TRIAL_DAYS = 7
OWNER_EMAILS = {
    email.strip().lower()
    for email in os.getenv("OWNER_EMAILS", os.getenv("OWNER_EMAIL", "")).split(",")
    if email.strip()
}
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "")

MARKET_SYMBOLS = {
    "gold": {"symbol": "GC=F", "label": "GOLD"},
    "silver": {"symbol": "SI=F", "label": "SILVER"},
    "dxy": {"symbol": "DX-Y.NYB", "label": "DXY"},
    "us10y": {"symbol": "^TNX", "label": "US10Y"},
    "oil": {"symbol": "CL=F", "label": "WTI"},
    "spy": {"symbol": "SPY", "label": "SPY"},
    "qqq": {"symbol": "QQQ", "label": "QQQ"},
}


class AccountAuthPayload(BaseModel):
    email: str
    password: str


class PreferencesPayload(BaseModel):
    prefs: dict[str, Any]


def db_connection():
    if DATABASE_URL:
        if psycopg2 is None:
            raise RuntimeError("psycopg2 n'est pas installe")
        return psycopg2.connect(
            DATABASE_URL,
            sslmode="require",
            cursor_factory=RealDictCursor,
        )

    conn = sqlite3.connect(ACCOUNT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_integrity_errors() -> tuple[type[Exception], ...]:
    errors: tuple[type[Exception], ...] = (sqlite3.IntegrityError,)
    if psycopg2 is not None:
        errors = errors + (psycopg2.IntegrityError,)
    return errors


def init_account_db() -> None:
    if ACCOUNT_DB_BACKEND == "postgres":
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        trial_started_at TEXT NOT NULL,
                        trial_ends_at TEXT NOT NULL,
                        plan TEXT NOT NULL DEFAULT 'trial',
                        status TEXT NOT NULL DEFAULT 'trialing',
                        prefs_json TEXT NOT NULL DEFAULT '{}'
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    )
                    """
                )
        seed_owner_accounts()
        return

    with db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                trial_started_at TEXT NOT NULL,
                trial_ends_at TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT 'trial',
                status TEXT NOT NULL DEFAULT 'trialing',
                prefs_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
    seed_owner_accounts()


def execute_one(query: str, params: tuple = ()) -> dict | sqlite3.Row | None:
    with db_connection() as conn:
        if ACCOUNT_DB_BACKEND == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(query.replace("?", "%s"), params)
                return cursor.fetchone()
        return conn.execute(query, params).fetchone()


def execute_write(query: str, params: tuple = (), *, returning: bool = False):
    with db_connection() as conn:
        if ACCOUNT_DB_BACKEND == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(query.replace("?", "%s"), params)
                return cursor.fetchone() if returning else None
        cursor = conn.execute(query, params)
        return cursor.lastrowid if returning else None


def seed_owner_accounts() -> None:
    if not OWNER_EMAILS or not OWNER_PASSWORD:
        return

    created_at = utc_now()
    trial_ends_at = created_at + timedelta(days=365 * 100)
    for email in OWNER_EMAILS:
        existing = execute_one("SELECT id FROM users WHERE email = ?", (email,))
        if existing:
            execute_write(
                "UPDATE users SET password_hash = ?, plan = ?, status = ? WHERE email = ?",
                (hash_password(OWNER_PASSWORD), "owner", "active", email),
            )
            continue

        execute_write(
            """
            INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, plan, status, prefs_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                hash_password(OWNER_PASSWORD),
                created_at.isoformat(),
                created_at.isoformat(),
                trial_ends_at.isoformat(),
                "owner",
                "active",
                "{}",
            ),
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_owner_row(row) -> bool:
    email = str(row["email"]).strip().lower()
    return email in OWNER_EMAILS or row["plan"] == "owner" or (not OWNER_EMAILS and int(row["id"]) == 1)


def derive_access_state(row) -> tuple[str, str, bool, bool, int]:
    if is_owner_row(row):
        return "owner", "owner", True, True, 999

    trial_ends_at = datetime.fromisoformat(row["trial_ends_at"])
    now = utc_now()
    trial_active = trial_ends_at > now
    trial_days_left = max(0, int(((trial_ends_at - now).total_seconds() + 86399) // 86400))

    if row["plan"] == "active" or row["status"] == "active":
        return "member", "active", True, trial_active, trial_days_left
    if trial_active:
        return "trial", "trialing", True, True, trial_days_left
    return "expired", "expired", False, False, 0


def hash_password(password: str, salt: str | None = None) -> str:
    actual_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        actual_salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"{actual_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hash_password(password, salt).split("$", 1)[1]
    return secrets.compare_digest(candidate, expected)


def normalize_account_row(row) -> dict | None:
    if row is None:
        return None

    role, status, has_access, trial_active, days_left = derive_access_state(row)
    prefs = {}
    try:
        prefs = json.loads(row["prefs_json"] or "{}")
    except json.JSONDecodeError:
        prefs = {}

    return {
        "id": row["id"],
        "email": row["email"],
        "created_at": row["created_at"],
        "plan": row["plan"],
        "status": status,
        "role": role,
        "has_access": has_access,
        "trial_started_at": row["trial_started_at"],
        "trial_ends_at": row["trial_ends_at"],
        "trial_active": trial_active,
        "trial_days_left": days_left,
        "prefs": prefs,
    }


def create_session(user_id: int) -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(days=30)
    execute_write(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, utc_now().isoformat(), expires_at.isoformat()),
    )
    return token, expires_at.isoformat()


def get_user_by_session(token: str | None) -> dict | None:
    if not token:
        return None

    row = execute_one(
        """
        SELECT users.*
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    )
    session_row = execute_one(
        "SELECT expires_at FROM sessions WHERE token = ?",
        (token,),
    )

    if not session_row:
        return None

    expires_at = datetime.fromisoformat(session_row["expires_at"])
    if expires_at <= utc_now():
        execute_write("DELETE FROM sessions WHERE token = ?", (token,))
        return None

    return normalize_account_row(row)


def require_user(request: Request) -> dict:
    user = get_user_by_session(request.cookies.get(SESSION_COOKIE))
    if not user:
        raise HTTPException(status_code=401, detail="Authentification requise")
    return user


def require_terminal_access(request: Request) -> dict:
    user = require_user(request)
    if not user.get("has_access"):
        raise HTTPException(status_code=403, detail="Acces reserve aux membres en essai ou abonnes")
    return user


def clear_session(response: Response, token: str | None) -> None:
    if token:
        execute_write("DELETE FROM sessions WHERE token = ?", (token,))
    response.delete_cookie(SESSION_COOKIE, path="/")


def set_session_cookie(response: Response, token: str, expires_at: str) -> None:
    expires_dt = datetime.fromisoformat(expires_at)
    max_age = int((expires_dt - utc_now()).total_seconds())
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


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

    return {
        "title": event.get("event") or "",
        "country": event.get("country") or "US",
        "currency": event.get("currency") or "",
        "impact": impact,
        "actual": event.get("actual"),
        "forecast": estimate,
        "previous": event.get("previous"),
        "unit": event.get("unit"),
        "ts": int(dt.timestamp()),
        "date_utc": dt.isoformat(),
    }


def get_current_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now.astimezone(CALENDAR_TZ) if now else datetime.now(CALENDAR_TZ)
    week_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


def _format_news_item(name: str, title: str, link: str, dt: datetime) -> dict:
    title_upper = title.upper()
    return {
        "s": name,
        "t": title,
        "l": link,
        "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
        "ts": dt.timestamp(),
        "crit": any(keyword in title_upper for keyword in ALERTS_CRITICAL),
        **classify_news_item(name, title_upper),
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
    if source in {"FED", "TREASURY", "DOL"}:
        categories.append("OFFICIAL")
        score += 2

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
    }


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


async def fetch_calendar() -> tuple[list[dict], str | None]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FMP_URL, timeout=20) as resp:
                if resp.status != 200:
                    return [], f"Calendar feed HTTP {resp.status}"
                payload = await resp.json()
        except Exception:
            return [], "Calendar feed unavailable"

    raw_events = payload.get("value", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_events, list):
        return [], "Calendar payload invalid"

    events: list[dict] = []
    for event in raw_events:
        if not isinstance(event, dict):
            continue
        normalized = normalize_calendar_event(event)
        if normalized:
            events.append(normalized)

    week_start, week_end = get_current_week_bounds()
    week_start_ts = int(week_start.timestamp())
    week_end_ts = int(week_end.timestamp())

    filtered_events = [
        event for event in events
        if week_start_ts <= event["ts"] < week_end_ts
    ]
    filtered_events.sort(key=lambda item: item["ts"])
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


def build_gold_context(markets: dict[str, dict]) -> dict:
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


async def fetch_xau_context() -> dict:
    now = time.time()
    if _context_cache["data"] and (now - _context_cache["ts"]) < CONTEXT_CACHE_TTL:
        return _context_cache["data"]

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
    context = build_gold_context(markets)
    _context_cache["data"] = context
    _context_cache["ts"] = now
    return context


@app.on_event("startup")
async def startup_event() -> None:
    init_account_db()


@app.get("/api/account/me")
async def account_me(request: Request):
    user = get_user_by_session(request.cookies.get(SESSION_COOKIE))
    return {"authenticated": bool(user), "account": user}


@app.post("/api/account/register")
async def account_register(payload: AccountAuthPayload, response: Response):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Email invalide")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Mot de passe trop court")

    created_at = utc_now()
    trial_ends_at = created_at + timedelta(days=TRIAL_DAYS)

    try:
        if ACCOUNT_DB_BACKEND == "postgres":
            inserted = execute_write(
                """
                INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, prefs_json)
                VALUES (?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    email,
                    hash_password(password),
                    created_at.isoformat(),
                    created_at.isoformat(),
                    trial_ends_at.isoformat(),
                    "{}",
                ),
                returning=True,
            )
            user_id = int(inserted["id"])
        else:
            user_id = int(
                execute_write(
                    """
                    INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, prefs_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        hash_password(password),
                        created_at.isoformat(),
                        created_at.isoformat(),
                        trial_ends_at.isoformat(),
                        "{}",
                    ),
                    returning=True,
                )
            )
    except db_integrity_errors() as exc:
        raise HTTPException(status_code=409, detail="Compte deja existant") from exc

    token, expires_at = create_session(user_id)
    set_session_cookie(response, token, expires_at)

    row = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))

    return {"authenticated": True, "account": normalize_account_row(row)}


@app.post("/api/account/login")
async def account_login(payload: AccountAuthPayload, response: Response):
    email = payload.email.strip().lower()
    password = payload.password

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Email invalide")

    row = execute_one("SELECT * FROM users WHERE email = ?", (email,))

    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    token, expires_at = create_session(int(row["id"]))
    set_session_cookie(response, token, expires_at)
    return {"authenticated": True, "account": normalize_account_row(row)}


@app.post("/api/account/logout")
async def account_logout(request: Request, response: Response):
    clear_session(response, request.cookies.get(SESSION_COOKIE))
    return {"ok": True}


@app.get("/api/account/preferences")
async def account_preferences(request: Request):
    user = require_user(request)
    return {"prefs": user["prefs"]}


@app.post("/api/account/preferences")
async def account_preferences_save(payload: PreferencesPayload, request: Request):
    user = require_user(request)
    prefs_json = json.dumps(payload.prefs)
    execute_write("UPDATE users SET prefs_json = ? WHERE id = ?", (prefs_json, user["id"]))
    return {"ok": True}


@app.get("/api/news")
async def get_news(request: Request):
    require_terminal_access(request)
    now = time.time()
    if _news_cache["data"] and (now - _news_cache["ts"]) < NEWS_CACHE_TTL:
        return {
            "items": _news_cache["data"],
            "cached": True,
            "age": int(now - _news_cache["ts"]),
        }

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 TradingTerminal"}) as session:
        results = await asyncio.gather(*(_fetch_source(session, name, url) for name, url in NEWS_SOURCES.items()))

    all_news = [item for chunk in results for item in chunk]
    all_news.sort(key=lambda item: item["ts"], reverse=True)
    all_news = all_news[:80]

    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return {"items": all_news, "cached": False, "age": 0}


@app.get("/api/calendar")
async def get_calendar(request: Request):
    require_terminal_access(request)
    events, error = await fetch_calendar()
    week_start, week_end = get_current_week_bounds()
    if error:
        return {
            "events": [],
            "count": 0,
            "timezone": "Europe/Paris",
            "hot": False,
            "error": error,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }

    now_ts = int(time.time())
    hot = any(0 <= (event["ts"] - now_ts) <= 3600 for event in events)

    return {
        "events": events,
        "count": len(events),
        "timezone": "Europe/Paris",
        "hot": hot,
        "error": None,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "cached_items": len(_news_cache["data"]),
        "cache_age": int(time.time() - _news_cache["ts"]) if _news_cache["ts"] else None,
    }


@app.get("/api/context")
async def get_context(request: Request):
    require_terminal_access(request)
    context = await fetch_xau_context()
    return context


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/index.html")

@app.get("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {"database": "ok", "result": result[0]}
    except Exception as e:
        return {"database": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
