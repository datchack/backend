from datetime import datetime, timedelta
import json

from fastapi import APIRouter, Request, Response
from fastapi import HTTPException

from app.config import ACCOUNT_DB_BACKEND, EMAIL_CONFIRMATION_REQUIRED, SESSION_COOKIE, TRIAL_DAYS
from app.preferences import validate_preferences_payload
from app.schemas import (
    AccountAuthPayload,
    AccountConfirmEmailPayload,
    AccountResendConfirmationPayload,
    PreferencesPayload,
)
from app.services.accounts import (
    check_rate_limit,
    clear_session,
    client_ip,
    create_session,
    db_integrity_errors,
    email_confirmation_expires_at,
    execute_one,
    execute_write,
    generate_email_confirmation_code,
    get_user_by_session,
    hash_password,
    normalize_account_row,
    require_owner,
    require_user,
    set_session_cookie,
    utc_now,
    verify_password,
)
from app.services.email import send_confirmation_email

router = APIRouter()

@router.get("/api/account/me")
async def account_me(request: Request):
    user = get_user_by_session(request.cookies.get(SESSION_COOKIE))
    return {"authenticated": bool(user), "account": user}


@router.post("/api/account/register")
async def account_register(payload: AccountAuthPayload, response: Response, request: Request):
    email = payload.email.strip().lower()
    password = payload.password.strip()
    check_rate_limit(f"register:{client_ip(request)}")
    check_rate_limit(f"register-email:{email}", limit=4)

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Email invalide")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Mot de passe trop court")

    created_at = utc_now()
    trial_start = created_at
    trial_end = created_at if EMAIL_CONFIRMATION_REQUIRED else created_at + timedelta(days=TRIAL_DAYS)
    code = generate_email_confirmation_code() if EMAIL_CONFIRMATION_REQUIRED else None
    expires_at = email_confirmation_expires_at() if EMAIL_CONFIRMATION_REQUIRED else None
    status = "pending" if EMAIL_CONFIRMATION_REQUIRED else "trialing"

    try:
        if ACCOUNT_DB_BACKEND == "postgres":
            inserted = execute_write(
                """
                INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, status, email_confirmed, email_confirmation_code, email_confirmation_expires_at, prefs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    email,
                    hash_password(password),
                    created_at.isoformat(),
                    trial_start.isoformat(),
                    trial_end.isoformat(),
                    status,
                    False,
                    code,
                    expires_at,
                    "{}",
                ),
                returning=True,
            )
            user_id = int(inserted["id"])
        else:
            user_id = int(
                execute_write(
                    """
                    INSERT INTO users (email, password_hash, created_at, trial_started_at, trial_ends_at, status, email_confirmed, email_confirmation_code, email_confirmation_expires_at, prefs_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        hash_password(password),
                        created_at.isoformat(),
                        trial_start.isoformat(),
                        trial_end.isoformat(),
                        status,
                        False,
                        code,
                        expires_at,
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

    if EMAIL_CONFIRMATION_REQUIRED:
        try:
            send_confirmation_email(email, code)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Impossible d'envoyer le code de confirmation par email") from exc

    token, expires_at = create_session(user_id)
    set_session_cookie(response, token, expires_at)

    row = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    account = normalize_account_row(row)
    return {
        "authenticated": True,
        "pending": EMAIL_CONFIRMATION_REQUIRED,
        "account": account,
        "message": "Un code de confirmation a ete envoye par email." if EMAIL_CONFIRMATION_REQUIRED else "Compte cree avec essai actif.",
    }


@router.post("/api/account/login")
async def account_login(payload: AccountAuthPayload, response: Response, request: Request):
    email = payload.email.strip().lower()
    password = payload.password
    check_rate_limit(f"login:{client_ip(request)}")
    check_rate_limit(f"login-email:{email}", limit=8)

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Email invalide")

    row = execute_one("SELECT * FROM users WHERE email = ?", (email,))

    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    # Si le compte n'est pas confirme, envoyer un code de confirmation
    if "email_confirmed" not in row.keys() or not row["email_confirmed"]:
        code = generate_email_confirmation_code()
        expires_at = email_confirmation_expires_at()
        execute_write(
            "UPDATE users SET email_confirmation_code = ?, email_confirmation_expires_at = ? WHERE id = ?",
            (code, expires_at, int(row["id"])),
        )
        try:
            send_confirmation_email(email, code)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Impossible d'envoyer le code de confirmation par email") from exc

        token, expires_at = create_session(int(row["id"]))
        set_session_cookie(response, token, expires_at)

        account = normalize_account_row(row)
        return {
            "authenticated": True,
            "pending": True,
            "account": account,
            "message": "Un code de confirmation a ete envoye par email.",
        }

    token, expires_at = create_session(int(row["id"]))
    set_session_cookie(response, token, expires_at)
    return {"authenticated": True, "account": normalize_account_row(row)}


@router.post("/api/account/confirm-email")
async def account_confirm_email(payload: AccountConfirmEmailPayload, response: Response, request: Request):
    email = payload.email.strip().lower()
    code = payload.code.strip()
    check_rate_limit(f"confirm-email:{client_ip(request)}")
    check_rate_limit(f"confirm-email-email:{email}", limit=6)

    if not email or not code:
        raise HTTPException(status_code=400, detail="Email ou code manquant")

    row = execute_one("SELECT * FROM users WHERE email = ?", (email,))
    if not row:
        raise HTTPException(status_code=404, detail="Compte introuvable")

    if "email_confirmed" in row.keys() and row["email_confirmed"]:
        raise HTTPException(status_code=400, detail="Email deja confirme")

    if str(row["email_confirmation_code"] or "").strip() != code:
        raise HTTPException(status_code=400, detail="Code de confirmation invalide")

    expires_at = row["email_confirmation_expires_at"]
    if not expires_at or datetime.fromisoformat(expires_at) <= utc_now():
        raise HTTPException(status_code=400, detail="Code de confirmation expire")

    now = utc_now()
    execute_write(
        "UPDATE users SET email_confirmed = ?, status = ?, trial_started_at = ?, trial_ends_at = ?, email_confirmation_code = ?, email_confirmation_expires_at = ? WHERE id = ?",
        (True, "confirmed", now.isoformat(), now.isoformat(), None, None, int(row["id"])),
    )

    token, expires_at = create_session(int(row["id"]))
    set_session_cookie(response, token, expires_at)

    updated = execute_one("SELECT * FROM users WHERE id = ?", (int(row["id"]),))
    account = normalize_account_row(updated)
    message = "Email confirme. Choisis une formule Stripe pour demarrer ton essai." if not account.get("has_access") else "Email confirme. Ton essai commence."
    return {"authenticated": True, "account": account, "message": message}


@router.post("/api/account/resend-confirmation")
async def account_resend_confirmation(payload: AccountResendConfirmationPayload, request: Request):
    email = payload.email.strip().lower()
    check_rate_limit(f"resend-confirmation:{client_ip(request)}")
    check_rate_limit(f"resend-confirmation-email:{email}", limit=6)

    row = execute_one("SELECT * FROM users WHERE email = ?", (email,))
    if not row:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    if "email_confirmed" in row.keys() and row["email_confirmed"]:
        raise HTTPException(status_code=400, detail="Email deja confirme")

    code = generate_email_confirmation_code()
    expires_at = email_confirmation_expires_at()
    execute_write(
        "UPDATE users SET email_confirmation_code = ?, email_confirmation_expires_at = ? WHERE id = ?",
        (code, expires_at, int(row["id"])),
    )
    try:
        send_confirmation_email(email, code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Impossible de renvoyer le code de confirmation") from exc

    return {"ok": True, "message": "Un nouveau code de confirmation a ete envoye."}


@router.post("/api/account/logout")
async def account_logout(request: Request, response: Response):
    clear_session(response, request.cookies.get(SESSION_COOKIE))
    return {"ok": True}


@router.get("/api/account/preferences")
async def account_preferences(request: Request):
    user = require_user(request)
    return {"prefs": user["prefs"]}


@router.get("/api/test-email-config")
async def test_email_config(request: Request):
    """Debug endpoint to check email configuration"""
    require_owner(request)
    from app.config import (
        EMAIL_FROM_ADDRESS,
        EMAIL_CONFIRMATION_REQUIRED,
    )
    from app.services.email import RESEND_API_KEY
    from app.services.email import is_email_confirmation_enabled

    return {
        "EMAIL_CONFIRMATION_REQUIRED": EMAIL_CONFIRMATION_REQUIRED,
        "EMAIL_FROM_ADDRESS": EMAIL_FROM_ADDRESS,
        "RESEND_API_KEY": bool(RESEND_API_KEY),
        "is_email_enabled": is_email_confirmation_enabled(),
    }
