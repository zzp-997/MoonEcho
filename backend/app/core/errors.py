from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.enums.error_codes import ErrorCode


@dataclass(slots=True)
class AppError(Exception):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = field(default=None)
    status_code: int = field(default=400)
