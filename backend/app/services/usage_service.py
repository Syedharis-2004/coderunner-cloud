"""
Usage tracking service.

Responsibilities:
- Check whether a user can run a new execution (plan limit check).
- Record compute usage after each execution.
- Return current monthly usage stats.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.models.user import User, UserPlan
from app.models.usage import UsageRecord

logger = logging.getLogger(__name__)


@dataclass
class PlanLimits:
    monthly_executions: int
    timeout_seconds: int
    memory_limit: str


PLAN_LIMITS_MAP: dict[UserPlan, PlanLimits] = {
    UserPlan.FREE: PlanLimits(
        monthly_executions=100,
        timeout_seconds=5,
        memory_limit="128m",
    ),
    UserPlan.DEVELOPER: PlanLimits(
        monthly_executions=5000,
        timeout_seconds=10,
        memory_limit="256m",
    ),
    UserPlan.PRO: PlanLimits(
        monthly_executions=25000,
        timeout_seconds=30,
        memory_limit="512m",
    ),
}


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

        Returns:
            (True, "") if allowed, or (False, reason_message) if denied.
        """
        limits = PLAN_LIMITS_MAP.get(user.plan)
        if not limits:
            return False, f"Unknown plan: {user.plan}"

        record = _get_or_create_record(db, user.id)
        db.commit()

        if record.total_executions >= limits.monthly_executions:
            return False, (
                f"Monthly execution limit reached ({limits.monthly_executions} executions). "
                "Please upgrade your plan."
            )

        return True, ""

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
        record = _get_or_create_record(db, user.id)
        db.commit()
        limits = PLAN_LIMITS_MAP.get(user.plan, PLAN_LIMITS_MAP[UserPlan.FREE])
        return {
            "billing_period": record.billing_period,
            "plan": user.plan,
            "total_executions": record.total_executions,
            "successful_executions": record.successful_executions,
            "failed_executions": record.failed_executions,
            "api_executions": record.api_executions,
            "total_compute_seconds": round(record.total_compute_seconds, 2),
            "monthly_limit": limits.monthly_executions,
            "remaining": max(0, limits.monthly_executions - record.total_executions),
            "timeout_seconds": limits.timeout_seconds,
            "memory_limit": limits.memory_limit,
        }


usage_service = UsageService()
