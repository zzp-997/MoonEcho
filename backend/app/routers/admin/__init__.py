"""管理后台路由模块。"""

from app.routers.admin.auth import router as admin_auth_router
from app.routers.admin.users import router as admin_users_router
from app.routers.admin.reports import router as admin_reports_router
from app.routers.admin.crisis import router as admin_crisis_router
from app.routers.admin.contents import router as admin_contents_router

__all__ = [
    "admin_auth_router",
    "admin_users_router",
    "admin_reports_router",
    "admin_crisis_router",
    "admin_contents_router",
]
