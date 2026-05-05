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


def stripe_get(value: Any, key: str, default: Any = None) -> Any:
    if not value:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def parse_metadata_user_id(metadata: Any) -> int | None:
    raw_user_id = stripe_get(metadata, "user_id")
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
    return stripe_get(value, "id")


def stripe_object_metadata(value: Any) -> dict:
    if not value:
        return {}
    return stripe_get(value, "metadata", {}) or {}


def stripe_line_price_id(line_item: Any) -> str | None:
    price_id = stripe_object_id(stripe_get(line_item, "price"))
    if price_id:
        return price_id

    pricing = stripe_get(line_item, "pricing", {})
    price_details = stripe_get(pricing, "price_details", {})
    price_id = stripe_object_id(stripe_get(price_details, "price"))
    if price_id:
        return price_id

    parent = stripe_get(line_item, "parent", {})
    subscription_item_details = stripe_get(parent, "subscription_item_details", {})
    return stripe_object_id(stripe_get(subscription_item_details, "price"))


def stripe_invoice_price_id(invoice: Any) -> str | None:
    line_items = stripe_get(stripe_get(invoice, "lines", {}), "data", [])
    first_price_id = None
    for line_item in line_items or []:
        price_id = stripe_line_price_id(line_item)
        if not first_price_id:
            first_price_id = price_id
        if stripe_price_allowed(price_id):
            return price_id
    return first_price_id


def retrieve_subscription(subscription_id: str | None) -> Any | None:
    if not subscription_id:
        return None
    subscription_api = getattr(stripe, "Subscription", None)
    if subscription_api is None:
        raise RuntimeError("Stripe Subscription API unavailable")
    return subscription_api.retrieve(subscription_id)


def subscription_sync_data(subscription_id: str | None) -> dict:
    subscription = retrieve_subscription(subscription_id)
    if not subscription:
        return {}

    items = stripe_get(stripe_get(subscription, "items", {}), "data", [])
    price_id = None
    if items:
        price_id = stripe_line_price_id(items[0])

    return {
        "user_id": parse_metadata_user_id(stripe_object_metadata(subscription)),
        "customer_id": stripe_object_id(stripe_get(subscription, "customer")),
        "subscription_id": stripe_object_id(subscription),
        "price_id": price_id,
        "current_period_end": iso_from_stripe_timestamp(stripe_get(subscription, "current_period_end")),
    }


def sync_checkout_session_for_user(user_id: int, session_id: str) -> None:
    require_stripe_ready()
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    metadata = stripe_get(checkout_session, "metadata", {}) or {}
    metadata_user_id = parse_metadata_user_id(metadata)
    client_reference_id = stripe_get(checkout_session, "client_reference_id")

    if metadata_user_id != user_id and client_reference_id != str(user_id):
        raise HTTPException(status_code=403, detail="Session Stripe non liee a ce compte")
    if stripe_get(checkout_session, "status") != "complete":
        raise HTTPException(status_code=400, detail="Session Stripe incomplete")

    price_id = stripe_get(metadata, "price_id")
    if not stripe_price_allowed(price_id):
        raise HTTPException(status_code=400, detail="Prix Stripe non reconnu")

    mode = stripe_get(checkout_session, "mode")
    payment_status = stripe_get(checkout_session, "payment_status")
    if mode != "subscription" and payment_status != "paid":
        raise HTTPException(status_code=400, detail="Paiement Stripe non valide")

    mark_user_paid(
        user_id=user_id,
        customer_id=stripe_object_id(stripe_get(checkout_session, "customer")),
        subscription_id=stripe_object_id(stripe_get(checkout_session, "subscription")),
        checkout_session_id=stripe_get(checkout_session, "id"),
        price_id=price_id,
        plan=stripe_get(metadata, "plan") or stripe_plan_from_price(price_id),
        status="active",
    )
