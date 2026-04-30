from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import hashlib
import json
import os
import secrets
import sqlite3
import time
from typing import Any, Optional
from zoneinfo import ZoneInfo

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

try:
    import stripe
except ImportError:
    stripe = None

import aiohttp
import feedparser
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response as FastAPIResponse
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

FMP_API_KEY = os.getenv("FMP_API_KEY", "JIUCkZ8STWgYWPA03dt64CxksXRVHWyX")
CALENDAR_TZ = PARIS

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30
NEWS_MAX_AGE_HOURS = 72
_calendar_cache: dict[str, dict] = {}
CALENDAR_CACHE_TTL = 30
CALENDAR_HOT_CACHE_TTL = 2
_quotes_cache: dict = {"data": None, "ts": 0.0}
QUOTES_CACHE_TTL = 5
_quote_latest_by_key: dict[str, dict] = {}
_quote_ws_clients: set[WebSocket] = set()
_fmp_ws_tasks: list[asyncio.Task] = []
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
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_MONTHLY = os.getenv("STRIPE_PRICE_MONTHLY", "")
STRIPE_PRICE_YEARLY = os.getenv("STRIPE_PRICE_YEARLY", "")
STRIPE_PRICE_LIFETIME = os.getenv("STRIPE_PRICE_LIFETIME", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://xauterminal.com").rstrip("/")

if stripe is not None and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

MARKET_SYMBOLS = {
    "gold": {"symbol": "GC=F", "label": "GOLD"},
    "silver": {"symbol": "SI=F", "label": "SILVER"},
    "dxy": {"symbol": "DX-Y.NYB", "label": "DXY"},
    "us10y": {"symbol": "^TNX", "label": "US10Y"},
    "oil": {"symbol": "CL=F", "label": "WTI"},
    "spy": {"symbol": "SPY", "label": "SPY"},
    "qqq": {"symbol": "QQQ", "label": "QQQ"},
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


class AccountAuthPayload(BaseModel):
    email: str
    password: str


class PreferencesPayload(BaseModel):
    prefs: dict[str, Any]


class AdminAccessPayload(BaseModel):
    action: str


class BillingCheckoutPayload(BaseModel):
    plan: str


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
                for column_def in (
                    "stripe_customer_id TEXT",
                    "stripe_subscription_id TEXT",
                    "stripe_price_id TEXT",
                    "stripe_checkout_session_id TEXT",
                    "stripe_current_period_end TEXT",
                ):
                    cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_def}")
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
        for column_def in (
            "stripe_customer_id TEXT",
            "stripe_subscription_id TEXT",
            "stripe_price_id TEXT",
            "stripe_checkout_session_id TEXT",
            "stripe_current_period_end TEXT",
        ):
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {column_def}")
            except sqlite3.OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise
    seed_owner_accounts()


def execute_one(query: str, params: tuple = ()) -> dict | sqlite3.Row | None:
    with db_connection() as conn:
        if ACCOUNT_DB_BACKEND == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(query.replace("?", "%s"), params)
                return cursor.fetchone()
        return conn.execute(query, params).fetchone()


def execute_all(query: str, params: tuple = ()) -> list[dict | sqlite3.Row]:
    with db_connection() as conn:
        if ACCOUNT_DB_BACKEND == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(query.replace("?", "%s"), params)
                return list(cursor.fetchall())
        return list(conn.execute(query, params).fetchall())


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
        "stripe_customer_id": row["stripe_customer_id"] if "stripe_customer_id" in row.keys() else None,
        "stripe_subscription_id": row["stripe_subscription_id"] if "stripe_subscription_id" in row.keys() else None,
        "stripe_price_id": row["stripe_price_id"] if "stripe_price_id" in row.keys() else None,
        "stripe_current_period_end": row["stripe_current_period_end"] if "stripe_current_period_end" in row.keys() else None,
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


def require_owner(request: Request) -> dict:
    user = require_user(request)
    if user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Acces owner requis")
    return user


def stripe_checkout_plans() -> dict[str, dict[str, str]]:
    return {
        "monthly": {"price": STRIPE_PRICE_MONTHLY, "mode": "subscription", "plan": "monthly"},
        "yearly": {"price": STRIPE_PRICE_YEARLY, "mode": "subscription", "plan": "yearly"},
        "lifetime": {"price": STRIPE_PRICE_LIFETIME, "mode": "payment", "plan": "lifetime"},
    }


def require_stripe_ready() -> None:
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe n'est pas installe sur le serveur")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="STRIPE_SECRET_KEY manquant")


def stripe_plan_from_price(price_id: str | None, fallback: str = "active") -> str:
    if price_id == STRIPE_PRICE_MONTHLY:
        return "monthly"
    if price_id == STRIPE_PRICE_YEARLY:
        return "yearly"
    if price_id == STRIPE_PRICE_LIFETIME:
        return "lifetime"
    return fallback


def iso_from_stripe_timestamp(value: Any) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def mark_user_paid(
    *,
    user_id: int | None = None,
    customer_id: str | None = None,
    subscription_id: str | None = None,
    checkout_session_id: str | None = None,
    price_id: str | None = None,
    plan: str = "active",
    status: str = "active",
    current_period_end: str | None = None,
) -> None:
    now = utc_now()
    if plan == "lifetime":
        current_period_end = (now + timedelta(days=365 * 100)).isoformat()

    assignments = ["plan = ?", "status = ?"]
    params: list[Any] = [plan, status]
    optional_values = {
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "stripe_checkout_session_id": checkout_session_id,
        "stripe_price_id": price_id,
        "stripe_current_period_end": current_period_end,
    }
    for column, value in optional_values.items():
        if value:
            assignments.append(f"{column} = ?")
            params.append(value)

    if user_id is not None:
        params.append(user_id)
        execute_write(f"UPDATE users SET {', '.join(assignments)} WHERE id = ?", tuple(params))
        return

    if subscription_id:
        params.append(subscription_id)
        execute_write(f"UPDATE users SET {', '.join(assignments)} WHERE stripe_subscription_id = ?", tuple(params))
        return

    if customer_id:
        params.append(customer_id)
        execute_write(f"UPDATE users SET {', '.join(assignments)} WHERE stripe_customer_id = ?", tuple(params))


def update_user_billing_status(customer_id: str | None, subscription_id: str | None, status: str) -> None:
    local_status = "active" if status in {"active", "trialing"} else status
    if subscription_id:
        execute_write(
            "UPDATE users SET status = ? WHERE stripe_subscription_id = ?",
            (local_status, subscription_id),
        )
        return
    if customer_id:
        execute_write(
            "UPDATE users SET status = ? WHERE stripe_customer_id = ?",
            (local_status, customer_id),
        )


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


def get_market_profile(profile_id: Optional[str]) -> dict:
    key = (profile_id or "xauusd").strip().lower()
    return MARKET_PROFILES.get(key, MARKET_PROFILES["xauusd"])


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
    events, _error = await fetch_calendar(["US"])
    context = build_gold_context(markets, events)
    _context_cache["data"] = context
    _context_cache["ts"] = now
    return context


@app.on_event("startup")
async def startup_event() -> None:
    init_account_db()
    await fetch_quote_cards()
    start_fmp_quote_websockets()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    for task in _fmp_ws_tasks:
        task.cancel()
    if _fmp_ws_tasks:
        await asyncio.gather(*_fmp_ws_tasks, return_exceptions=True)


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
        existing = execute_one("SELECT * FROM users WHERE email = ?", (email,))
        if existing and verify_password(password, existing["password_hash"]):
            token, expires_at = create_session(int(existing["id"]))
            set_session_cookie(response, token, expires_at)
            return {"authenticated": True, "account": normalize_account_row(existing), "existing": True}
        raise HTTPException(
            status_code=409,
            detail="Compte deja existant. Connecte-toi avec ce compte pour reprendre le paiement.",
        ) from exc

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


@app.post("/api/billing/checkout")
async def billing_checkout(payload: BillingCheckoutPayload, request: Request):
    require_stripe_ready()
    user = require_user(request)

    plan_key = payload.plan.strip().lower()
    plan_cfg = stripe_checkout_plans().get(plan_key)
    if not plan_cfg:
        raise HTTPException(status_code=400, detail="Formule inconnue")
    if not plan_cfg["price"]:
        raise HTTPException(status_code=503, detail=f"Prix Stripe manquant pour {plan_key}")

    session_payload: dict[str, Any] = {
        "mode": plan_cfg["mode"],
        "line_items": [{"price": plan_cfg["price"], "quantity": 1}],
        "success_url": f"{APP_BASE_URL}/terminal?billing=success",
        "cancel_url": f"{APP_BASE_URL}/#pricing",
        "client_reference_id": str(user["id"]),
        "metadata": {
            "user_id": str(user["id"]),
            "plan": plan_cfg["plan"],
            "price_id": plan_cfg["price"],
        },
        "allow_promotion_codes": True,
    }

    if user.get("stripe_customer_id"):
        session_payload["customer"] = user["stripe_customer_id"]
    else:
        session_payload["customer_email"] = user["email"]

    if plan_cfg["mode"] == "subscription":
        session_payload["payment_method_collection"] = "always"
        session_payload["subscription_data"] = {
            "trial_period_days": TRIAL_DAYS,
            "metadata": {
                "user_id": str(user["id"]),
                "plan": plan_cfg["plan"],
                "price_id": plan_cfg["price"],
            }
        }
    else:
        session_payload["customer_creation"] = "always"
        session_payload["invoice_creation"] = {"enabled": True}
        session_payload["payment_intent_data"] = {
            "metadata": {
                "user_id": str(user["id"]),
                "plan": plan_cfg["plan"],
                "price_id": plan_cfg["price"],
            }
        }

    checkout_session = stripe.checkout.Session.create(**session_payload)
    return {"url": checkout_session.url}


@app.post("/api/billing/webhook")
async def billing_webhook(request: Request):
    require_stripe_ready()
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET manquant")

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Webhook Stripe invalide") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Signature Stripe invalide") from exc

    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        metadata = obj.get("metadata") or {}
        user_id = int(metadata["user_id"]) if metadata.get("user_id") else None
        plan = metadata.get("plan") or stripe_plan_from_price(metadata.get("price_id"))
        price_id = metadata.get("price_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        mode = obj.get("mode")
        payment_status = obj.get("payment_status")

        if mode == "subscription" or payment_status == "paid":
            mark_user_paid(
                user_id=user_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                checkout_session_id=obj.get("id"),
                price_id=price_id,
                plan=plan,
                status="active",
            )

    elif event_type == "invoice.paid":
        subscription_id = obj.get("subscription")
        customer_id = obj.get("customer")
        line_items = ((obj.get("lines") or {}).get("data") or [])
        price_id = None
        if line_items:
            price = line_items[0].get("price") or {}
            price_id = price.get("id")
        plan = stripe_plan_from_price(price_id, "active")
        mark_user_paid(
            customer_id=customer_id,
            subscription_id=subscription_id,
            price_id=price_id,
            plan=plan,
            status="active",
        )

    elif event_type == "invoice.payment_failed":
        update_user_billing_status(obj.get("customer"), obj.get("subscription"), "past_due")

    elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        subscription_id = obj.get("id")
        customer_id = obj.get("customer")
        status = "canceled" if event_type.endswith("deleted") else obj.get("status", "inactive")
        current_period_end = iso_from_stripe_timestamp(obj.get("current_period_end"))
        price_id = None
        items = ((obj.get("items") or {}).get("data") or [])
        if items:
            price = items[0].get("price") or {}
            price_id = price.get("id")

        if status in {"active", "trialing"}:
            mark_user_paid(
                customer_id=customer_id,
                subscription_id=subscription_id,
                price_id=price_id,
                plan=stripe_plan_from_price(price_id, "active"),
                status="active",
                current_period_end=current_period_end,
            )
        else:
            update_user_billing_status(customer_id, subscription_id, status)

    return {"received": True}


@app.get("/api/admin/users")
async def admin_users(request: Request):
    require_owner(request)
    rows = execute_all(
        """
        SELECT id, email, created_at, trial_started_at, trial_ends_at, plan, status, prefs_json
        FROM users
        ORDER BY id DESC
        """
    )
    return {"users": [normalize_account_row(row) for row in rows]}


@app.post("/api/admin/users/{user_id}/access")
async def admin_update_user_access(user_id: int, payload: AdminAccessPayload, request: Request):
    require_owner(request)
    row = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    email = str(row["email"]).strip().lower()
    action = payload.action.strip().lower()
    now = utc_now()

    if email in OWNER_EMAILS and action != "owner":
        raise HTTPException(status_code=400, detail="Ce compte owner configure ne peut pas etre retrograde")

    if action == "owner":
        execute_write(
            "UPDATE users SET plan = ?, status = ?, trial_ends_at = ? WHERE id = ?",
            ("owner", "active", (now + timedelta(days=365 * 100)).isoformat(), user_id),
        )
    elif action == "active":
        execute_write(
            "UPDATE users SET plan = ?, status = ? WHERE id = ?",
            ("active", "active", user_id),
        )
    elif action == "trial":
        execute_write(
            "UPDATE users SET plan = ?, status = ?, trial_started_at = ?, trial_ends_at = ? WHERE id = ?",
            ("trial", "trialing", now.isoformat(), (now + timedelta(days=TRIAL_DAYS)).isoformat(), user_id),
        )
    elif action == "expire":
        execute_write(
            "UPDATE users SET plan = ?, status = ?, trial_ends_at = ? WHERE id = ?",
            ("trial", "expired", (now - timedelta(seconds=1)).isoformat(), user_id),
        )
    else:
        raise HTTPException(status_code=400, detail="Action admin inconnue")

    updated = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return {"user": normalize_account_row(updated)}


@app.get("/api/market-profiles")
async def market_profiles(request: Request):
    require_terminal_access(request)
    return {"profiles": list(MARKET_PROFILES.values())}


@app.get("/api/market-quotes")
async def market_quotes(request: Request):
    require_terminal_access(request)
    quotes = await fetch_quote_cards()
    return {
        "items": quotes,
        "count": len(quotes),
        "cached": bool(_quotes_cache["data"]),
        "age": int(time.time() - _quotes_cache["ts"]) if _quotes_cache["ts"] else 0,
    }


@app.websocket("/ws/market-quotes")
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


@app.get("/api/news")
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
    all_news.sort(key=lambda item: item["ts"], reverse=True)
    all_news = all_news[:80]

    _news_cache["data"] = all_news
    _news_cache["ts"] = now
    return {
        "items": personalize_news_items(all_news, market_profile),
        "profile": market_profile["id"],
        "window_hours": NEWS_MAX_AGE_HOURS,
        "cached": False,
        "age": 0,
    }


@app.get("/api/calendar")
async def get_calendar(request: Request, profile: Optional[str] = None):
    require_terminal_access(request)
    market_profile = get_market_profile(profile)
    events, error = await fetch_calendar(market_profile.get("calendar_countries", ["US"]))
    week_start, week_end = get_current_week_bounds()
    if error:
        return {
            "events": [],
            "count": 0,
            "timezone": "Europe/Paris",
            "profile": market_profile["id"],
            "countries": market_profile.get("calendar_countries", ["US"]),
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
        "countries": market_profile.get("calendar_countries", ["US"]),
        "hot": hot,
        "release_watch": release_watch,
        "refresh_ms": refresh_ms,
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
    return FileResponse("templates/landing.html")


@app.get("/terminal", response_class=HTMLResponse)
async def terminal():
    return FileResponse("templates/index.html")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return """User-agent: *
Allow: /

Sitemap: https://xauterminal.com/sitemap.xml
"""


@app.get("/sitemap.xml")
async def sitemap_xml():
    today = utc_now().date().isoformat()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://xauterminal.com/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://xauterminal.com/terminal</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
"""
    return FastAPIResponse(content=xml, media_type="application/xml")


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    require_owner(request)
    return FileResponse("templates/admin.html")


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
