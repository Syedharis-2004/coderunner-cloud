# Import all models here so Alembic can detect them for autogenerate
from app.core.database import Base  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.execution import Execution, ExecutionStatus, ExecutionSource  # noqa: F401
from app.models.api_key import APIKey  # noqa: F401
from app.models.usage import UsageRecord  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.subscription import Subscription, SubscriptionStatus  # noqa: F401
from app.models.payment import Payment, PaymentStatus, PaymentType  # noqa: F401

__all__ = [
    "Base",
    "User", "UserRole",
    "Project",
    "Execution", "ExecutionStatus", "ExecutionSource",
    "APIKey",
    "UsageRecord",
    "Plan",
    "Subscription", "SubscriptionStatus",
    "Payment", "PaymentStatus", "PaymentType",
]

