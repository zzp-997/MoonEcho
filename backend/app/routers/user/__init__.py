"""用户子路由模块。

包含用户账户相关的 API 端点：
- account: 账户注销相关路由
"""

from __future__ import annotations

from .account import router as account_router

__all__ = ["account_router"]