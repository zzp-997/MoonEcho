from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.errors import AppError


def _meta(request_id: str) -> dict[str, str]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requestId": request_id,
    }


def success_response(data: Any, request_id: str) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": _meta(request_id),
    }


def error_response(error: AppError, request_id: str) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": error.code.value,
            "message": error.message,
            "details": error.details,
        },
        "meta": _meta(request_id),
    }


def paginated_response(
    data: list[Any],
    *,
    page: int,
    page_size: int,
    total: int,
    request_id: str,
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": page * page_size < total,
        },
        "meta": _meta(request_id),
    }
