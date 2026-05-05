from datetime import timedelta

from fastapi import APIRouter, Request
from fastapi import HTTPException

from app.config import OWNER_EMAILS, TRIAL_DAYS
from app.schemas import AdminAccessPayload
from app.services.accounts import (
    execute_all,
    execute_one,
    execute_write,
    normalize_account_row,
    require_owner,
    utc_now,
)

router = APIRouter()

@router.get("/api/admin/users")
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

    updated = execute_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return {"user": normalize_account_row(updated)}
