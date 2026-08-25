from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standard API response wrapper for all endpoints.

    Success:  {"success": true, "data": {...}}
    Error:    {"success": false, "error": {"code": "...", "message": "..."}}
    """
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
