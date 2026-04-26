"""路由注册汇总。

所有业务路由模块统一在此注册，方便 main.py 引用和管理。
后续新增路由模块只需：
1. 在 routers/ 目录下创建新模块（如 diaries.py）
2. 在 ROUTER_REGISTRY 中添加条目
3. 调用 register_routers(app) 即可自动挂载
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRouter

from app.routers.auth import router as auth_router
from app.routers.system import router as system_router
from app.routers.ai import router as ai_router
from app.routers.diaries import router as diaries_router
from app.routers.notifications import router as notifications_router
from app.routers.reports import router as reports_router
from app.routers.treehole import router as treehole_router
from app.routers.admin.auth import router as admin_auth_router
from app.routers.admin.users import router as admin_users_router
from app.routers.admin.reports import router as admin_reports_router
from app.routers.admin.crisis import router as admin_crisis_router
from app.routers.admin.contents import router as admin_contents_router


# 路由注册表 — (router实例, 前缀, 标签列表)
# 后续新增路由模块时在此追加条目
ROUTER_REGISTRY: list[tuple[APIRouter, str, list[str]]] = [
    (system_router, "", ["system"]),
    (auth_router, "", ["auth"]),
    (ai_router, "", ["ai"]),
    (diaries_router, "", ["diaries"]),
    (notifications_router, "", ["notifications"]),
    (reports_router, "", ["reports"]),
    (treehole_router, "", ["treehole"]),
    (admin_auth_router, "", ["admin-auth"]),
    (admin_users_router, "", ["admin-users"]),
    (admin_reports_router, "", ["admin-reports"]),
    (admin_crisis_router, "", ["admin-crisis"]),
    (admin_contents_router, "", ["admin-contents"]),
]


def register_routers(app: FastAPI) -> None:
    """将路由注册表中所有路由模块挂载到 FastAPI 应用实例。

    使用方式:
        from app.routers import register_routers
        register_routers(app)
    """
    for router, prefix, tags in ROUTER_REGISTRY:
        app.include_router(router, prefix=prefix, tags=tags)


def add_router(router: APIRouter, prefix: str = "", tags: list[str] | None = None) -> None:
    """动态添加路由到注册表。

    使用方式:
        from app.routers import add_router
        from app.routers.diary import router as diary_router
        add_router(diary_router, "", ["diary"])
    """
    ROUTER_REGISTRY.append((router, prefix, tags or []))
