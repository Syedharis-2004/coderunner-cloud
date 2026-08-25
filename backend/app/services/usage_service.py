"""
Usage tracking service.

Responsibilities:
- Check whether a user can run a new execution (plan limit check).
- Record compute usage after each execution.
- Return current monthly usage stats.
"""
import logging
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.usage import UsageRecord

logger = logging.getLogger(__name__)


def _current_period() -> str:
    """Return current billing period as YYYY-MM string."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_or_create_record(db: Session, user_id: str) -> UsageRecord:
    """Fetch or lazily create the UsageRecord for the current billing period."""
    period = _current_period()
    record = (
        db.query(UsageRecord)
        .filter(UsageRecord.user_id == user_id, UsageRecord.billing_period == period)
        .first()
    )
    if not record:
        record = UsageRecord(
            user_id=user_id,
            billing_period=period,
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
            api_executions=0,
            total_compute_seconds=0.0,
        )
        db.add(record)
        db.flush()
    return record


class UsageService:
    def can_execute(self, db: Session, user: User, is_api: bool = False) -> Tuple[bool, str]:
        """
        Check whether the user has remaining quota for this billing period.
        Now uses subscription-based plan limits.

        Returns:
            (True, "") if allowed, or (False, reason_message) if denied.
        """
        # Import here to avoid circular imports
        from app.services.subscription_service import subscription_service
        
        return subscription_service.can_execute_code(db, user, is_api)

    def record_execution(
        self,
        db: Session,
        user_id: str,
        execution_time: float,
        is_api: bool,
        success: bool = True,
    ) -> None:
        """
        Increment usage counters after a completed execution.
        Should be called immediately after execution finishes.
        """
        try:
            record = _get_or_create_record(db, user_id)
            record.total_executions += 1
            record.total_compute_seconds += execution_time

            if success:
                record.successful_executions += 1
            else:
                record.failed_executions += 1

            if is_api:
                record.api_executions += 1

            db.commit()
            logger.debug(
                f"[Usage] user={user_id} period={record.billing_period} "
                f"total={record.total_executions}"
            )
        except Exception as exc:
            logger.error(f"[Usage] Failed to record execution for user {user_id}: {exc}")
            db.rollback()

    def get_current_usage(self, db: Session, user: User) -> dict:
        """Return current month usage stats and plan limits for the user."""
        from app.services.subscription_service import subscription_service
        
        record = _get_or_create_record(db, user.id)
        db.commit()
        
        # Get plan from subscription
        plan = subscription_service.get_user_plan(db, user)
        
        return {
            "billing_period": record.billing_period,
            "plan_name": plan.name,
            "plan_key": plan.key,
            "total_executions": record.total_executions,
            "successful_executions": record.successful_executions,
            "failed_executions": record.failed_executions,
            "api_executions": record.api_executions,
            "total_compute_seconds": round(record.total_compute_seconds, 2),
            "monthly_limit": plan.monthly_executions,
            "remaining": max(0, plan.monthly_executions - record.total_executions),
            "timeout_seconds": plan.timeout_seconds,
            "memory_limit_mb": plan.memory_limit_mb,
            "api_access_enabled": plan.api_access_enabled,
        }


usage_service = UsageService()
