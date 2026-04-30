from fastapi import APIRouter, Request, Response

from app.core import *

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

    token, expires_at = create_session(int(row["id"]))
    set_session_cookie(response, token, expires_at)
    return {"authenticated": True, "account": normalize_account_row(row)}


@router.post("/api/account/logout")
async def account_logout(request: Request, response: Response):
    clear_session(response, request.cookies.get(SESSION_COOKIE))
    return {"ok": True}


@router.get("/api/account/preferences")
async def account_preferences(request: Request):
    user = require_user(request)
    return {"prefs": user["prefs"]}


@router.post("/api/account/preferences")
async def account_preferences_save(payload: PreferencesPayload, request: Request):
    user = require_user(request)
    prefs = validate_preferences_payload(payload.prefs)
    prefs_json = json.dumps(prefs)
    execute_write("UPDATE users SET prefs_json = ? WHERE id = ?", (prefs_json, user["id"]))
    return {"ok": True}
