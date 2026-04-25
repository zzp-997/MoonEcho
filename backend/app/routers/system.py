from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.responses import success_response

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health")
async def health_check(request: Request) -> dict[str, object]:
    return success_response(
        {"status": "ok", "environment": request.app.state.settings.app_env},
        request_id=request.state.request_id,
    )
