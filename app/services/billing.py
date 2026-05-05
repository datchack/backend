from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from app.config import (
    STRIPE_ALLOWED_WEBHOOK_EVENTS,
    STRIPE_PRICE_LIFETIME,
    STRIPE_PRICE_MONTHLY,
    STRIPE_PRICE_YEARLY,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_MAX_BYTES,
    STRIPE_WEBHOOK_SECRET,
)
from app.services.accounts import execute_write, utc_now

try:
    import stripe
except ImportError:
    stripe = None

if stripe is not None and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


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


def stripe_price_allowed(price_id: str | None) -> bool:
    if not price_id:
        return False
    return price_id in {STRIPE_PRICE_MONTHLY, STRIPE_PRICE_YEARLY, STRIPE_PRICE_LIFETIME}


def parse_metadata_user_id(metadata: dict) -> int | None:
    raw_user_id = metadata.get("user_id")
    if not raw_user_id:
        return None
    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


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


def stripe_object_id(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id")
    return getattr(value, "id", None)


def sync_checkout_session_for_user(user_id: int, session_id: str) -> None:
    require_stripe_ready()
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    metadata = checkout_session.get("metadata") or {}
    metadata_user_id = parse_metadata_user_id(metadata)
    client_reference_id = checkout_session.get("client_reference_id")

    if metadata_user_id != user_id and client_reference_id != str(user_id):
        raise HTTPException(status_code=403, detail="Session Stripe non liee a ce compte")
    if checkout_session.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Session Stripe incomplete")

    price_id = metadata.get("price_id")
    if not stripe_price_allowed(price_id):
        raise HTTPException(status_code=400, detail="Prix Stripe non reconnu")

    mode = checkout_session.get("mode")
    payment_status = checkout_session.get("payment_status")
    if mode != "subscription" and payment_status != "paid":
        raise HTTPException(status_code=400, detail="Paiement Stripe non valide")

    mark_user_paid(
        user_id=user_id,
        customer_id=stripe_object_id(checkout_session.get("customer")),
        subscription_id=stripe_object_id(checkout_session.get("subscription")),
        checkout_session_id=checkout_session.get("id"),
        price_id=price_id,
        plan=metadata.get("plan") or stripe_plan_from_price(price_id),
        status="active",
    )
