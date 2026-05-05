from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
import sqlite3
import time

from fastapi import HTTPException, Request, Response

from app.config import (
    ACCOUNT_DB_BACKEND,
    ACCOUNT_DB_PATH,
    AUTH_RATE_LIMIT_MAX,
    DATABASE_URL,
    EMAIL_CONFIRMATION_EXPIRES_HOURS,
    IS_PRODUCTION,
    OWNER_EMAILS,
    OWNER_PASSWORD,
    RATE_LIMIT_WINDOW_SECONDS,
    SESSION_COOKIE,
)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # pragma: no cover
    psycopg2 = None
    RealDictCursor = None


_rate_limits: dict[str, list[float]] = {}


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL n'est pas configurée")
    if psycopg2 is None:
        raise RuntimeError("psycopg2 n'est pas installe")

    return psycopg2.connect(DATABASE_URL, sslmode="require")


def db_connection():
    if DATABASE_URL:
        if psycopg2 is None:
            raise RuntimeError("psycopg2 n'est pas installe")
        return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)

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
                    "email_confirmed BOOLEAN NOT NULL DEFAULT FALSE",
                    "email_confirmation_code TEXT",
                    "email_confirmation_expires_at TEXT",
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
            "email_confirmed INTEGER NOT NULL DEFAULT 0",
            "email_confirmation_code TEXT",
            "email_confirmation_expires_at TEXT",
        ):
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {column_def}")
            except sqlite3.OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise
    seed_owner_accounts()


def execute_one(query: str, params: tuple = ()):
    with db_connection() as conn:
        if ACCOUNT_DB_BACKEND == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(query.replace("?", "%s"), params)
                return cursor.fetchone()
        return conn.execute(query, params).fetchone()


def execute_all(query: str, params: tuple = ()):
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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_email_confirmation_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def email_confirmation_expires_at() -> str:
    return (utc_now() + timedelta(hours=EMAIL_CONFIRMATION_EXPIRES_HOURS)).isoformat()


def seed_owner_accounts() -> None:
    if not OWNER_EMAILS or not OWNER_PASSWORD:
        return

    created_at = utc_now()
    trial_ends_at = created_at + timedelta(days=365 * 100)
    for email in OWNER_EMAILS:
        existing = execute_one("SELECT id FROM users WHERE email = ?", (email,))
        if existing:
            execute_write(
                "UPDATE users SET password_hash = ?, plan = ?, status = ?, email_confirmed = ? WHERE email = ?",
                (hash_password(OWNER_PASSWORD), "owner", "active", True, email),
            )
            continue

        execute_write(
            """
            INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, plan, status, prefs_json, email_confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                True,
            ),
        )


def is_owner_row(row) -> bool:
    email = str(row["email"]).strip().lower()
    return email in OWNER_EMAILS or row["plan"] == "owner" or (not OWNER_EMAILS and int(row["id"]) == 1)


def derive_access_state(row) -> tuple[str, str, bool, bool, int]:
    if is_owner_row(row):
        return "owner", "owner", True, True, 999

    row_keys = row.keys()
    trial_ends_at = datetime.fromisoformat(row["trial_ends_at"])
    now = utc_now()
    trial_active = trial_ends_at > now
    trial_days_left = max(0, int(((trial_ends_at - now).total_seconds() + 86399) // 86400))
    plan = row["plan"]
    status = row["status"]
    has_stripe_link = any(
        column in row_keys and row[column]
        for column in ("stripe_customer_id", "stripe_subscription_id", "stripe_checkout_session_id")
    )

    if plan in {"active", "monthly", "yearly", "lifetime"} or status == "active":
        return "member", "active", True, trial_active, trial_days_left
    if plan == "trial" and status == "trialing" and trial_active and has_stripe_link:
        return "trial", "trialing", True, True, trial_days_left
    if status == "confirmed":
        return "confirmed", "confirmed", False, False, 0
    if status == "pending":
        return "pending", "pending", False, False, 0
    return "expired", "expired", False, False, 0


def hash_password(password: str, salt: str | None = None) -> str:
    actual_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt.encode("utf-8"), 200_000).hex()
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
        "email_confirmed": bool(row["email_confirmed"]) if "email_confirmed" in row.keys() else False,
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
    execute_write("INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)", (token, user_id, utc_now().isoformat(), expires_at.isoformat()))
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
    session_row = execute_one("SELECT expires_at FROM sessions WHERE token = ?", (token,))
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


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(key: str, *, limit: int = AUTH_RATE_LIMIT_MAX, window: int = RATE_LIMIT_WINDOW_SECONDS) -> None:
    now = time.time()
    hits = [hit for hit in _rate_limits.get(key, []) if now - hit < window]
    if len(hits) >= limit:
        raise HTTPException(status_code=429, detail="Trop de tentatives. Reessaie dans quelques minutes.")
    hits.append(now)
    _rate_limits[key] = hits


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
        secure=IS_PRODUCTION,
        path="/",
    )
