from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "coderunner_cloud",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_soft_time_limit=120,   # 2 min soft limit — triggers SoftTimeLimitExceeded
    task_time_limit=150,        # 2.5 min hard kill
    worker_prefetch_multiplier=1,
    task_acks_late=True,        # Only ack after successful processing
)
