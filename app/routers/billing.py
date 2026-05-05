from typing import Any
import traceback

from fastapi import APIRouter, Request
from fastapi import HTTPException

from app.config import (
    APP_BASE_URL,
    STRIPE_ALLOWED_WEBHOOK_EVENTS,
    STRIPE_WEBHOOK_MAX_BYTES,
    STRIPE_WEBHOOK_SECRET,
    TRIAL_DAYS,
)
from app.schemas import BillingCheckoutPayload, BillingCheckoutSyncPayload
from app.services.accounts import require_user
from app.services.billing import (
    iso_from_stripe_timestamp,
    mark_user_paid,
    parse_metadata_user_id,
    require_stripe_ready,
    stripe,
    stripe_checkout_plans,
    stripe_get,
    stripe_invoice_price_id,
    stripe_object_id,
    stripe_plan_from_price,
    stripe_price_allowed,
    subscription_sync_data,
    sync_checkout_session_for_user,
    update_user_billing_status,
)

router = APIRouter()

@router.post("/api/billing/checkout")
async def billing_checkout(payload: BillingCheckoutPayload, request: Request):
    require_stripe_ready()
    user = require_user(request)

    if not user.get("email_confirmed"):
        raise HTTPException(status_code=403, detail="Email non confirme. Confirme ton adresse email avant de payer.")

    plan_key = payload.plan.strip().lower()
    plan_cfg = stripe_checkout_plans().get(plan_key)
    if not plan_cfg:
        raise HTTPException(status_code=400, detail="Formule inconnue")
    if not plan_cfg["price"]:
        raise HTTPException(status_code=503, detail=f"Prix Stripe manquant pour {plan_key}")

    session_payload: dict[str, Any] = {
        "mode": plan_cfg["mode"],
        "line_items": [{"price": plan_cfg["price"], "quantity": 1}],
        "success_url": f"{APP_BASE_URL}/terminal?billing=success&session_id={{CHECKOUT_SESSION_ID}}",
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


@router.post("/api/billing/sync-checkout")
async def billing_sync_checkout(payload: BillingCheckoutSyncPayload, request: Request):
    user = require_user(request)
    session_id = payload.session_id.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="Session Stripe manquante")

    sync_checkout_session_for_user(int(user["id"]), session_id)
    return {"ok": True}


@router.post("/api/billing/portal")
async def billing_portal(request: Request):
    require_stripe_ready()
    user = require_user(request)

    if not user.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="Aucun compte Stripe lie a ce profil.")

    session = stripe.billing_portal.Session.create(
        customer=user["stripe_customer_id"],
        return_url=f"{APP_BASE_URL}/terminal",
    )
    return {"url": session.url}


@router.post("/api/billing/webhook")
async def billing_webhook(request: Request):
    require_stripe_ready()
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET manquant")

    payload = await request.body()
    if len(payload) > STRIPE_WEBHOOK_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Webhook Stripe trop volumineux")
    signature = request.headers.get("stripe-signature", "")
    if not signature:
        raise HTTPException(status_code=400, detail="Signature Stripe manquante")

    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Webhook Stripe invalide") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Signature Stripe invalide") from exc

    event_type = event["type"]
    if event_type not in STRIPE_ALLOWED_WEBHOOK_EVENTS:
        return {"received": True, "ignored": True}

    try:
        obj = stripe_get(stripe_get(event, "data", {}), "object")

        if event_type == "checkout.session.completed":
            metadata = stripe_get(obj, "metadata", {}) or {}
            user_id = parse_metadata_user_id(metadata)
            plan = metadata.get("plan") or stripe_plan_from_price(metadata.get("price_id"))
            price_id = metadata.get("price_id")
            customer_id = stripe_object_id(stripe_get(obj, "customer"))
            subscription_id = stripe_object_id(stripe_get(obj, "subscription"))
            mode = stripe_get(obj, "mode")
            payment_status = stripe_get(obj, "payment_status")

            if not stripe_price_allowed(price_id):
                return {"received": True, "ignored": True}

            if mode == "subscription" or payment_status == "paid":
                mark_user_paid(
                    user_id=user_id,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    checkout_session_id=stripe_get(obj, "id"),
                    price_id=price_id,
                    plan=plan,
                    status="active",
                )

        elif event_type == "invoice.paid":
            subscription_id = stripe_object_id(stripe_get(obj, "subscription"))
            customer_id = stripe_object_id(stripe_get(obj, "customer"))
            price_id = stripe_invoice_price_id(obj)
            sync_data = subscription_sync_data(subscription_id)
            user_id = sync_data.get("user_id")
            customer_id = customer_id or sync_data.get("customer_id")
            subscription_id = subscription_id or sync_data.get("subscription_id")
            price_id = price_id or sync_data.get("price_id")
            if not stripe_price_allowed(price_id):
                return {"received": True, "ignored": True}
            plan = stripe_plan_from_price(price_id, "active")
            mark_user_paid(
                user_id=user_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                price_id=price_id,
                plan=plan,
                status="active",
                current_period_end=sync_data.get("current_period_end"),
            )

        elif event_type == "invoice.payment_failed":
            update_user_billing_status(stripe_object_id(stripe_get(obj, "customer")), stripe_object_id(stripe_get(obj, "subscription")), "past_due")

        elif event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
            subscription_id = stripe_object_id(obj)
            customer_id = stripe_object_id(stripe_get(obj, "customer"))
            status = "canceled" if event_type.endswith("deleted") else stripe_get(obj, "status", "inactive")
            current_period_end = iso_from_stripe_timestamp(stripe_get(obj, "current_period_end"))
            price_id = None
            items = stripe_get(stripe_get(obj, "items", {}), "data", [])
            if items:
                price_id = stripe_object_id(stripe_get(items[0], "price"))

            if status in {"active", "trialing"}:
                if not stripe_price_allowed(price_id):
                    return {"received": True, "ignored": True}
                mark_user_paid(
                    user_id=parse_metadata_user_id(stripe_get(obj, "metadata", {}) or {}),
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    price_id=price_id,
                    plan=stripe_plan_from_price(price_id, "active"),
                    status="active",
                    current_period_end=current_period_end,
                )
            else:
                update_user_billing_status(customer_id, subscription_id, status)
    except Exception as exc:
        print(f"Stripe webhook processing failed for {event_type}: {exc}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur traitement webhook Stripe: {type(exc).__name__}") from exc

    return {"received": True}
