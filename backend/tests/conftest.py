"""Pytest 配置文件和 fixtures。

提供 API 测试所需的通用 fixtures：
- 测试客户端
- 测试数据库会话
- 认证 token
- 测试用户数据
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import AppSettings


# ============================================================================
# 测试配置
# ============================================================================

# 使用内存 SQLite 数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def get_test_settings() -> AppSettings:
    """获取测试环境配置。"""
    return AppSettings(
        app_env="test",
        debug=True,
        database_url=TEST_DATABASE_URL,
        # 使用无效的 Redis URL，这样会触发 MockRedis
        redis_url="redis://localhost:9999/0",
        cors_origins=["http://localhost:3000"],
        mock_enabled=True,
        sms_provider="mock",
        content_audit_provider="pass",
        storage_provider="local",
        push_provider="mock",
        ai_provider="mock",
    )


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环 fixture，支持异步测试。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """创建 MockRedis 实例用于测试。"""
    from app.main import MockRedis
    return MockRedis()


@pytest.fixture
def app(mock_redis) -> FastAPI:
    """创建测试 FastAPI 应用，使用 MockRedis。

    注意：此 fixture 每个 test function 都会创建新的 app 实例，
    确保测试之间的数据库会话隔离，避免 SQLAlchemy 会话冲突。
    """
    from app.main import MockRedis
    from app.services.auth_service import AuthService
    from app.services.admin.admin_service import AdminAuthService
    from app.services.providers import build_provider_registry
    from app.services.image import create_image_service
    from app.services.storage import create_storage_service
    from app.services.chat_service import create_chat_service
    from app.services.connection_manager import create_connection_manager
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    settings = get_test_settings()

    # 创建应用但不启动 lifespan
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )
    app.state.settings = settings
    app.state.provider_registry = build_provider_registry(settings)
    app.state.scheduler = MagicMock()

    # 使用 MockRedis
    app.state.redis = mock_redis

    # 初始化认证服务
    app.state.auth_service = AuthService(
        sms_service=app.state.provider_registry.sms,
        settings=settings,
        redis=mock_redis,
    )

    # 初始化管理员认证服务
    app.state.admin_auth_service = AdminAuthService(
        settings=settings,
        redis=mock_redis,
    )

    # 初始化图片服务
    app.state.image_service = create_image_service()

    # 初始化存储服务
    app.state.storage_service = create_storage_service(
        provider=settings.storage_provider,
    )

    # 初始化聊天服务和 WebSocket 连接管理器
    app.state.chat_service = create_chat_service(redis=mock_redis)
    connection_manager = create_connection_manager(
        redis=mock_redis,
        auth_service=app.state.auth_service,
        chat_service=app.state.chat_service,
    )
    app.state.connection_manager = connection_manager

    # 初始化数据库引擎和会话工厂
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
    )

    # 创建所有表 - 使用同步方式在当前事件循环中执行
    from app.models import Base

    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # 在当前线程的事件循环中创建表
    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(create_tables())
    except RuntimeError:
        # 如果没有运行中的循环，创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(create_tables())
        finally:
            loop.close()

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )
    app.state.db_session = session_factory
    app.state.async_session_factory = session_factory
    app.state.db_engine = engine

    # 注册路由
    from app.routers import register_routers
    register_routers(app)

    # 添加中间件 - 注意：中间件顺序很重要，后添加的先执行
    from app.middleware.request_context import RequestContextMiddleware
    app.add_middleware(RequestContextMiddleware)

    # 添加异常处理器
    from app.core.errors import AppError
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error_handler(request, exc):
        from app.core.responses import error_response
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc, request_id),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(exc)}
        )

    return app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """创建测试客户端。

    注意：每个测试函数使用独立的 client 实例，
    确保请求之间的状态隔离。
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """测试用户数据。"""
    return {
        "phone": "13800138000",
        "nickname": "测试用户",
        "age_group": "18-25",
        "gender": "male",
    }


@pytest.fixture
def test_admin_data() -> dict[str, Any]:
    """测试管理员数据。"""
    return {
        "username": "admin",
        "password": "admin123",
    }


@pytest.fixture
def auth_token(client: TestClient, test_user_data: dict) -> str | None:
    """获取测试用户认证 token。

    重要：每个测试函数会使用独立的数据库会话，
    避免跨会话的用户对象复用问题。

    如果需要登录获取 token，使用此 fixture。
    """
    # 发送验证码
    response = client.post(
        "/api/v1/auth/send-code",
        json={"phone": test_user_data["phone"]}
    )
    if response.status_code != 200:
        return None

    # 验证验证码（开发环境固定为 123456）
    response = client.post(
        "/api/v1/auth/verify-code",
        json={
            "phone": test_user_data["phone"],
            "code": "123456"
        }
    )
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("data", {}).get("access_token")


@pytest.fixture
def admin_token(client: TestClient, test_admin_data: dict) -> str | None:
    """获取测试管理员认证 token。"""
    response = client.post(
        "/api/v1/admin/auth/login",
        json=test_admin_data
    )
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("data", {}).get("access_token")


@pytest.fixture
def auth_headers(auth_token: str | None) -> dict[str, str]:
    """获取认证请求头。

    注意：返回的是新的字典实例，避免跨测试复用。
    """
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture
def admin_headers(admin_token: str | None) -> dict[str, str]:
    """获取管理员认证请求头。"""
    if admin_token:
        return {"Authorization": f"Bearer {admin_token}"}
    return {}
