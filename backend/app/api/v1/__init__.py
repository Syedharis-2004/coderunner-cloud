from fastapi import APIRouter
from app.api.v1 import auth, executions, admin, projects, api_keys, usage

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(executions.router)
api_router.include_router(admin.router)
api_router.include_router(projects.router)
api_router.include_router(api_keys.router)
api_router.include_router(usage.router)
