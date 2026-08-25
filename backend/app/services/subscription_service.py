"""
Subscription Service
====================
Business logic for managing user subscriptions (SafePay).
"""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.payment import Payment, PaymentStatus, PaymentType

logger = logging.getLogger(__name__)


class SubscriptionService:

    @staticmethod
    def get_free_plan(db: Session) -> Optional[Plan]:
        return db.query(Plan).filter(Plan.key == "free", Plan.is_active == True).first()

    @staticmethod
    def get_user_subscription(db: Session, user_id: str) -> Optional[Subscription]:
        return db.query(Subscription).filter(Subscription.user_id == user_id).first()

    @staticmethod
    def get_user_plan(db: Session, user: User) -> Plan:
        if user.subscription and user.subscription.is_active:
            return user.subscription.plan
        free_plan = SubscriptionService.get_free_plan(db)
        if not free_plan:
            raise ValueError("System configuration error: Free plan missing")
        return free_plan

    # ── Gating checks ────────────────────────────────────────────────────────

    @staticmethod
    def can_generate_api_key(db: Session, user: User) -> Tuple[bool, str]:
        subscription = SubscriptionService.get_user_subscription(db, user.id)

        if not subscription:
            return False, "An active paid subscription is required to generate API keys."

        if not subscription.is_active:
            msg = f"Your subscription is {subscription.status}."
            if subscription.status == SubscriptionStatus.PAST_DUE:
                return False, f"{msg} Please renew your subscription."
            elif subscription.status == SubscriptionStatus.CANCELED:
                return False, f"{msg} Please subscribe again."
            return False, f"{msg} An active subscription is required."

        if not subscription.plan.api_access_enabled:
            return False, f"Your {subscription.plan.name} plan does not include API access. Please upgrade."

        from app.models.api_key import APIKey
        active_keys = db.query(func.count(APIKey.id)).filter(
            APIKey.user_id == user.id,
            APIKey.is_active == True,
        ).scalar()

        if active_keys >= subscription.plan.max_api_keys:
            return False, (
                f"API key limit reached ({subscription.plan.max_api_keys} keys). "
                "Revoke an existing key or upgrade your plan."
            )

        return True, ""

    @staticmethod
    def can_execute_code(db: Session, user: User, is_api: bool = False) -> Tuple[bool, str]:
        plan = SubscriptionService.get_user_plan(db, user)

        if is_api:
            subscription = SubscriptionService.get_user_subscription(db, user.id)
            if not subscription or not subscription.is_active:
                return False, "Production API access requires an active paid subscription."
            if not plan.api_access_enabled:
                return False, f"Your {plan.name} plan does not include API access."

        from app.models.usage import UsageRecord
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = db.query(UsageRecord).filter(
            UsageRecord.user_id == user.id,
            UsageRecord.billing_period == current_month,
        ).first()

        if usage and usage.total_executions >= plan.monthly_executions:
            return False, (
                f"Monthly execution limit reached ({plan.monthly_executions} executions). "
                "Please upgrade your plan or wait for the next billing period."
            )

        return True, ""

    # ── CRUD ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create_subscription(
        db: Session,
        user_id: str,
        plan_id: str,
        safepay_tracker:  Optional[str] = None,
        safepay_order_id: Optional[str] = None,
        status: str = "incomplete",
    ) -> Subscription:
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            safepay_tracker=safepay_tracker,
            safepay_order_id=safepay_order_id,
            status=SubscriptionStatus(status),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        logger.info(f"Created subscription {subscription.id} for user {user_id}")
        return subscription

    @staticmethod
    def record_payment(
        db: Session,
        user_id: str,
        subscription_id: Optional[str],
        amount: Decimal,
        currency: str,
        status: str,
        payment_type: str = "subscription",
        safepay_tracker:  Optional[str] = None,
        safepay_order_id: Optional[str] = None,
        description:      Optional[str] = None,
        receipt_url:      Optional[str] = None,
        failure_reason:   Optional[str] = None,
    ) -> Payment:
        payment = Payment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus(status),
            payment_type=PaymentType(payment_type),
            safepay_tracker=safepay_tracker,
            safepay_order_id=safepay_order_id,
            description=description,
            receipt_url=receipt_url,
            failure_reason=failure_reason,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        logger.info(f"Recorded payment {payment.id}: {amount} {currency} ({status})")
        return payment

    @staticmethod
    def cancel_subscription(
        db: Session,
        user_id: str,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None,
    ) -> Tuple[bool, str]:
        subscription = SubscriptionService.get_user_subscription(db, user_id)

        if not subscription:
            return False, "No active subscription found"

        if not subscription.is_active:
            return False, "Subscription is not currently active"

        now = datetime.now(timezone.utc)
        subscription.cancel_at_period_end = cancel_at_period_end
        subscription.canceled_at = now
        if not cancel_at_period_end:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = now
        subscription.updated_at = now
        db.commit()

        msg = (
            "Subscription will cancel at the end of the current billing period"
            if cancel_at_period_end
            else "Subscription canceled immediately"
        )
        logger.info(f"{msg} for user {user_id}. Reason: {reason}")
        return True, msg


subscription_service = SubscriptionService()
