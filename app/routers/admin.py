from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Request
from fastapi import HTTPException

from app.config import OWNER_EMAILS, TRIAL_DAYS
from app.schemas import AdminAccessPayload, AdminActivationReminderPayload
from app.services.accounts import (
    email_confirmation_expires_at,
    execute_all,
    execute_one,
    execute_write,
    generate_email_confirmation_code,
    normalize_account_row,
    require_owner,
    utc_now,
)
from app.services.billing import sync_user_stripe_billing
from app.services.email import is_email_confirmation_enabled, send_activation_reminder_email

router = APIRouter()

REMINDER_COOLDOWN_HOURS = 24
REMINDER_MIN_ACCOUNT_AGE_HOURS = 2


def stripe_dashboard_url(kind: str, object_id: str | None) -> str | None:
    if not object_id:
        return None
    if kind == "customer":
        return f"https://dashboard.stripe.com/customers/{object_id}"
    if kind == "subscription":
        return f"https://dashboard.stripe.com/subscriptions/{object_id}"
    if kind == "payment":
        return f"https://dashboard.stripe.com/payments/{object_id}"
    return None


def admin_enrich_user(user: dict | None) -> dict | None:
    if not user:
        return None

    has_stripe = bool(user.get("stripe_customer_id") or user.get("stripe_subscription_id") or user.get("stripe_checkout_session_id"))
    issues = []
    if user.get("email_confirmed") and not has_stripe and user.get("role") != "owner":
        issues.append("confirmed_no_stripe")
    if has_stripe and user.get("email_confirmed") and not user.get("has_access"):
        issues.append("stripe_without_access")
    if user.get("stripe_subscription_id") and not user.get("stripe_current_period_end") and user.get("plan") != "lifetime":
        issues.append("missing_period_end")

    user["admin"] = {
        "has_stripe": has_stripe,
        "issues": issues,
        "needs_review": bool(issues),
        "stripe_customer_url": stripe_dashboard_url("customer", user.get("stripe_customer_id")),
        "stripe_subscription_url": stripe_dashboard_url("subscription", user.get("stripe_subscription_id")),
    }
    return user


def admin_user_from_row(row):
    return admin_enrich_user(normalize_account_row(row))

@router.get("/api/admin/users")
async def admin_users(request: Request):
    require_owner(request)
    rows = execute_all(
        """
        SELECT *
        FROM users
        ORDER BY id DESC
        """
    )
    return {"users": [admin_user_from_row(row) for row in rows]}


@router.post("/api/admin/users/{user_id}/access")
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
    elif action == "confirm":
        execute_write(
            "UPDATE users SET email_confirmed = ?, status = ?, trial_started_at = ?, trial_ends_at = ? WHERE id = ?",
            (True, "confirmed", now.isoformat(), now.isoformat(), user_id),
        )
    elif action == "expire":
        execute_write(
            "UPDATE users SET plan = ?, status = ?, trial_ends_at = ? WHERE id = ?",
            ("trial", "expired", now.isoformat(), user_id),
        )
    else:
        raise HTTPException(status_code=400, detail="Action admin inconnue")

    updated = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return {"user": admin_user_from_row(updated)}


def parse_datetime(value: str | None, fallback_tz=None):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None and fallback_tz is not None:
            parsed = parsed.replace(tzinfo=fallback_tz)
        return parsed
    except ValueError:
        return None


def should_send_activation_reminder(row, now) -> tuple[bool, str]:
    user = normalize_account_row(row)
    if not user:
        return False, "invalid"

    email = str(user["email"]).strip().lower()
    if email in OWNER_EMAILS or user.get("role") == "owner":
        return False, "owner"
    if user.get("email_confirmed"):
        return False, "confirmed"
    if user.get("has_access"):
        return False, "has_access"
    if user.get("stripe_customer_id") or user.get("stripe_subscription_id"):
        return False, "stripe_linked"

    created_at = parse_datetime(user.get("created_at"), now.tzinfo)
    if created_at and created_at + timedelta(hours=REMINDER_MIN_ACCOUNT_AGE_HOURS) > now:
        return False, "too_recent"

    reminder_sent_at = parse_datetime(user.get("email_confirmation_reminder_sent_at"), now.tzinfo)
    if reminder_sent_at and reminder_sent_at + timedelta(hours=REMINDER_COOLDOWN_HOURS) > now:
        return False, "cooldown"

    return True, "eligible"


@router.post("/api/admin/users/resend-activation")
async def admin_resend_activation_reminders(payload: AdminActivationReminderPayload, request: Request):
    require_owner(request)
    if not is_email_confirmation_enabled():
        raise HTTPException(status_code=503, detail="Service email de confirmation indisponible")

    limit = max(1, min(int(payload.limit or 50), 100))
    rows = execute_all("SELECT * FROM users ORDER BY id DESC")
    now = utc_now()
    sent = []
    skipped = {}
    errors = []

    for row in rows:
        if len(sent) >= limit:
            skipped["limit"] = skipped.get("limit", 0) + 1
            continue

        eligible, reason = should_send_activation_reminder(row, now)
        if not eligible:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue

        email = str(row["email"]).strip().lower()
        code = generate_email_confirmation_code()
        expires_at = email_confirmation_expires_at()

        try:
            execute_write(
                """
                UPDATE users
                SET email_confirmation_code = ?,
                    email_confirmation_expires_at = ?
                WHERE id = ?
                """,
                (code, expires_at, int(row["id"])),
            )
            send_activation_reminder_email(email, code)
            execute_write(
                "UPDATE users SET email_confirmation_reminder_sent_at = ? WHERE id = ?",
                (now.isoformat(), int(row["id"])),
            )
            sent.append({"id": int(row["id"]), "email": email})
        except Exception as exc:
            errors.append({"id": int(row["id"]), "email": email, "error": type(exc).__name__})

    updated_rows = execute_all("SELECT * FROM users ORDER BY id DESC")
    return {
        "sent": sent,
        "sent_count": len(sent),
        "skipped": skipped,
        "error_count": len(errors),
        "errors": errors[:10],
        "users": [admin_user_from_row(row) for row in updated_rows],
    }


@router.post("/api/admin/users/{user_id}/resend-activation")
async def admin_resend_user_activation(user_id: int, request: Request):
    require_owner(request)
    if not is_email_confirmation_enabled():
        raise HTTPException(status_code=503, detail="Service email de confirmation indisponible")

    row = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    now = utc_now()
    eligible, reason = should_send_activation_reminder(row, now)
    if not eligible:
        raise HTTPException(status_code=400, detail=f"Compte non eligible a la relance: {reason}")

    email = str(row["email"]).strip().lower()
    code = generate_email_confirmation_code()
    expires_at = email_confirmation_expires_at()
    execute_write(
        """
        UPDATE users
        SET email_confirmation_code = ?,
            email_confirmation_expires_at = ?
        WHERE id = ?
        """,
        (code, expires_at, user_id),
    )
    try:
        send_activation_reminder_email(email, code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Email de relance non envoye") from exc

    execute_write(
        "UPDATE users SET email_confirmation_reminder_sent_at = ? WHERE id = ?",
        (now.isoformat(), user_id),
    )
    updated = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return {"user": admin_user_from_row(updated), "sent": True}


@router.post("/api/admin/users/{user_id}/sync-stripe")
async def admin_sync_user_stripe(user_id: int, request: Request):
    require_owner(request)
    sync_result = sync_user_stripe_billing(user_id)
    updated = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return {"user": admin_user_from_row(updated), "sync": sync_result}
