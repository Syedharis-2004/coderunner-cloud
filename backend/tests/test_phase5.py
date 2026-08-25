import asyncio
import sys
import os

from sqlalchemy import select

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.user import User, UserPlan, UserRole
from app.models.api_key import APIKey
from app.services.usage_service import usage_service

def test_imports_and_db():
    print("Testing DB session...")
    db = SessionLocal()
    
    # Try fetching a user
    user = db.query(User).first()
    print("User query successful:", user is not None)

    # Check celery app
    from app.workers.celery_app import celery_app
    print("Celery app initialized:", celery_app.main)

    from app.workers.tasks import run_sandboxed_execution
    print("Task registered:", run_sandboxed_execution.name)
    
    print("Phase 5 verification: PASSED")
    db.close()

if __name__ == "__main__":
    test_imports_and_db()
