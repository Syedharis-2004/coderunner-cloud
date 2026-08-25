"""
Payments API Router
===================
SafePay checkout, webhook, and payment management.

Flow:
  POST /payments/create-checkout-session  → returns SafePay checkout URL
  GET  /payments/verify                   → called after SafePay redirect (sig + tracker)
  POST /payments/webhook                  → SafePay webhook (payment confirmation)
  POST /payments/cancel                   → user cancels subscription
  POST /payments/reactivate               → user reactivates subscription
  GET  /payments/history                  → user's payment history
"""
import logging
import uuid
from typing import List
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.plan import Plan
from app.models.payment import Payment
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.payment import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PaymentRead,
)
from app.schemas.common import ResponseEnvelope
from app.api.deps import get_current_user
from app.services.safepay_service import safepay_service
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/payments", tags=["Payments"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helper — PKR amount from plan price
# ─────────────────────────────────────────────────────────────────────────────
PKR_RATE = 278  # 1 USD ≈ 278 PKR  (update as needed)

def usd_to_pkr_paisas(usd_price: float) -> int:
    """Convert USD price to PKR paisas (smallest unit SafePay expects)."""
    pkr = usd_price * PKR_RATE
    return int(pkr * 100)   # paisas


# ─────────────────────────────────────────────────────────────────────────────
# 1. Create checkout session
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/create-checkout-session",
    response_model=ResponseEnvelope[CheckoutSessionResponse],
    summary="Create SafePay checkout session",
)
def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a SafePay Checkout session.
    Returns a ``checkout_url`` — redirect the user there to complete payment.
    """
    # Validate plan
    plan = db.query(Plan).filter(
        Plan.id == request.plan_id,
        Plan.is_active == True,
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")

    if plan.price_monthly == 0:
        raise HTTPException(status_code=400, detail="Free plan does not require payment")

    # Build callback URLs
    base = settings.ALLOWED_ORIGINS.split(",")[0].strip()
    success_url = request.success_url or f"{base}/dashboard?payment=success"
    cancel_url  = request.cancel_url  or f"{base}/pricing?payment=cancelled"

    # Unique order ID embeds user + plan so we can activate on redirect
    order_id = safepay_service.build_order_id(current_user.id, plan.id)

    # Create SafePay session
    session = safepay_service.create_checkout_session(
        usd_price=float(plan.price_monthly),
        plan_id=plan.id,
        user_id=current_user.id,
        order_id=order_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if not session:
        raise HTTPException(status_code=500, detail="Failed to create SafePay checkout session")

    # Persist a pending subscription record so verify endpoint can find it
    existing_sub = subscription_service.get_user_subscription(db, current_user.id)
    if existing_sub:
        existing_sub.plan_id = plan.id
        existing_sub.safepay_tracker = session["tracker"]
        existing_sub.safepay_order_id = order_id
        existing_sub.status = SubscriptionStatus.INCOMPLETE
        existing_sub.updated_at = datetime.now(timezone.utc)
        db.commit()
    else:
        subscription_service.create_subscription(
            db=db,
            user_id=current_user.id,
            plan_id=plan.id,
            safepay_tracker=session["tracker"],
            safepay_order_id=order_id,
            status="incomplete",
        )

    logger.info(
        f"SafePay checkout: user={current_user.id}, plan={plan.key}, "
        f"order={order_id}, tracker={session['tracker']}"
    )

    return ResponseEnvelope(
        success=True,
        message="Checkout session created",
        data=CheckoutSessionResponse(
            checkout_url=session["checkout_url"],
            session_id=session["tracker"],
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Verify payment after SafePay redirect
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/verify",
    response_model=ResponseEnvelope[dict],
    summary="Verify SafePay payment after redirect",
)
def verify_payment(
    tracker: str = Query(..., description="tracker param from SafePay redirect"),
    sig:     str = Query(..., description="sig param from SafePay redirect"),
    ref:     str = Query(None, description="order_id / ref param"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Called after SafePay redirects back with ?tracker=...&sig=...
    Verifies the HMAC signature and activates the subscription.
    Frontend should call this endpoint immediately after redirect.
    """
    # Verify signature
    if not safepay_service.verify_payment(sig=sig, tracker=tracker):
        raise HTTPException(status_code=400, detail="Invalid payment signature — payment not verified")

    # Find the subscription by tracker
    sub = db.query(Subscription).filter(
        Subscription.safepay_tracker == tracker,
        Subscription.user_id == current_user.id,
    ).first()

    if not sub:
        # Fallback: find latest incomplete subscription for user
        sub = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
        ).order_by(Subscription.created_at.desc()).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription record not found")

    # Activate subscription
    now = datetime.now(timezone.utc)
    sub.status = SubscriptionStatus.ACTIVE
    sub.current_period_start = now
    # Set period end to 30 days from now (monthly subscription)
    from datetime import timedelta
    sub.current_period_end = now + timedelta(days=30)
    sub.updated_at = now
    db.commit()

    # Record payment
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    amount = Decimal(str(plan.price_monthly)) if plan else Decimal("0")
    subscription_service.record_payment(
        db=db,
        user_id=current_user.id,
        subscription_id=sub.id,
        amount=amount,
        currency="USD",
        status="succeeded",
        payment_type="subscription",
        safepay_tracker=tracker,
        safepay_order_id=sub.safepay_order_id,
        description=f"SafePay subscription: {plan.name if plan else 'Unknown'}",
    )

    logger.info(f"Payment verified & subscription activated: user={current_user.id}, tracker={tracker}")

    return ResponseEnvelope(
        success=True,
        message="Payment verified. Subscription activated.",
        data={"status": "active", "plan": plan.key if plan else "unknown"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. SafePay Webhook (server-to-server confirmation)
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/webhook",
    summary="SafePay webhook endpoint",
    status_code=200,
)
async def safepay_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    SafePay calls this endpoint after payment is processed.
    Verify webhook signature, then activate subscription.
    """
    payload = await request.json()
    headers = dict(request.headers)

    # Verify webhook authenticity
    if settings.SAFEPAY_WEBHOOK_SECRET:
        if not safepay_service.verify_webhook(headers, payload):
            logger.warning("SafePay webhook: Invalid signature")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Extract data from SafePay webhook payload
    data     = payload.get("data", payload)
    tracker  = data.get("tracker") or data.get("token")
    order_id = data.get("order_id") or data.get("orderId")
    state    = data.get("state") or data.get("status", "")

    logger.info(f"SafePay webhook: tracker={tracker}, order={order_id}, state={state}")

    if not tracker:
        return {"received": True}

    # Only process successful payments
    if state.lower() not in ("paid", "success", "succeeded", "completed", ""):
        logger.info(f"SafePay webhook: non-success state '{state}', skipping")
        return {"received": True}

    # Find subscription by tracker
    sub = db.query(Subscription).filter(
        Subscription.safepay_tracker == tracker,
    ).first()

    if not sub and order_id:
        # Fallback: parse user_id from order_id
        user_id, plan_id = safepay_service.parse_order_id(order_id)
        if user_id:
            sub = db.query(Subscription).filter(
                Subscription.user_id == user_id,
            ).order_by(Subscription.updated_at.desc()).first()

    if sub and sub.status != SubscriptionStatus.ACTIVE:
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        sub.status = SubscriptionStatus.ACTIVE
        sub.safepay_tracker = tracker
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.updated_at = now
        db.commit()

        # Record payment
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
        amount = Decimal(str(plan.price_monthly)) if plan else Decimal("0")
        subscription_service.record_payment(
            db=db,
            user_id=sub.user_id,
            subscription_id=sub.id,
            amount=amount,
            currency="USD",
            status="succeeded",
            payment_type="subscription",
            safepay_tracker=tracker,
            safepay_order_id=order_id,
            description=f"SafePay webhook: {plan.name if plan else 'Unknown'}",
        )
        logger.info(f"Webhook: subscription activated for user={sub.user_id}")

    return {"received": True}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Cancel subscription
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/cancel",
    response_model=ResponseEnvelope[dict],
    summary="Cancel subscription at period end",
)
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark subscription to cancel at end of current billing period."""
    success, message = subscription_service.cancel_subscription(db, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return ResponseEnvelope(success=True, message=message, data={})


# ─────────────────────────────────────────────────────────────────────────────
# 5. Reactivate subscription
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/reactivate",
    response_model=ResponseEnvelope[dict],
    summary="Reactivate a cancelled subscription",
)
def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Undo cancel_at_period_end — keep subscription active."""
    sub = subscription_service.get_user_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")

    if sub.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Subscription is not active")

    sub.cancel_at_period_end = False
    sub.canceled_at = None
    sub.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ResponseEnvelope(success=True, message="Subscription reactivated", data={})


# ─────────────────────────────────────────────────────────────────────────────
# 6. Payment history
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/history",
    response_model=ResponseEnvelope[List[PaymentRead]],
    summary="Get payment history",
)
def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the user's payment transaction history."""
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )

    return ResponseEnvelope(
        success=True,
        message=f"Retrieved {len(payments)} payments",
        data=payments,
    )
