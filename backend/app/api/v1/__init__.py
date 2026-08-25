from fastapi import APIRouter
from app.api.v1 import auth, executions, admin, projects, api_keys, usage, plans, subscriptions, payments

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(executions.router)
api_router.include_router(admin.router)
api_router.include_router(projects.router)
api_router.include_router(api_keys.router)
api_router.include_router(usage.router)
api_router.include_router(plans.router)
api_router.include_router(subscriptions.router)
api_router.include_router(payments.router)
