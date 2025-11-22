from __future__ import annotations

from .schemas import ApiResponse


def ok(data: dict) -> ApiResponse:
    """Helper to return success response."""
    return ApiResponse(success=True, data=data)


def error(code: str, message: str) -> ApiResponse:
    """Helper to return error response."""
    return ApiResponse(success=False, error_code=code, error_message=message)
