from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import AppSettings, load_settings
from app.core.errors import AppError
from app.core.responses import error_response
from app.middleware.request_context import RequestContextMiddleware
from app.routers import register_routers
from app.services.auth_service import AuthService
from app.services.providers import build_provider_registry
from app.services.scheduler import SchedulerManager

logger = logging.getLogger("echo.app")


def _create_redis_client(settings: AppSettings):
    """创建 Redis 客户端实例。

    优先使用 aioredis（redis.asyncio），若未安装则回退到 mock 实现。
    """
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
        )
        logger.info("Redis 客户端已创建: %s", settings.redis_url)
        return client
    except ImportError:
        logger.warning(
            "未安装 redis.asyncio，使用 MockRedis。"
            "请安装: pip install redis"
        )
        return MockRedis()


def create_app(settings: AppSettings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """应用生命周期管理：启动时初始化各服务，关闭时清理资源。"""
        # 初始化 Redis 客户端
        redis_client = _create_redis_client(resolved_settings)
        app.state.redis = redis_client

        # 初始化认证服务
        provider_registry = app.state.provider_registry
        app.state.auth_service = AuthService(
            sms_service=provider_registry.sms,
            settings=resolved_settings,
            redis=redis_client,
        )

        # 初始化数据库会话工厂
        engine = create_async_engine(
            resolved_settings.database_url,
            echo=resolved_settings.debug,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False,
        )
        app.state.async_session_factory = session_factory
        app.state.db_session = session_factory
        app.state.db_engine = engine

        try:
            app.state.scheduler.start()
            logger.info(
                "Application started",
                extra={"env": resolved_settings.app_env},
            )
            yield
        finally:
            # 关闭 Redis 连接
            if redis_client:
                await redis_client.close()
            # 关闭数据库引擎
            if engine:
                await engine.dispose()
            app.state.scheduler.shutdown()
            logger.info("Application shutdown complete")

    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.provider_registry = build_provider_registry(resolved_settings)
    app.state.scheduler = SchedulerManager()

    # 注册异常处理器：捕获 AppError 并返回统一格式
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """处理业务异常，返回统一错误响应格式。"""
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc, request_id),
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.add_middleware(RequestContextMiddleware)

    # 通过路由注册表统一注册所有路由
    register_routers(app)

    return app


app = create_app()


# ---------------------------------------------------------------------------
# MockRedis — 开发环境无 Redis 时的降级实现
# ---------------------------------------------------------------------------

class MockRedis:
    """Mock Redis 客户端，用于开发环境无 Redis 时的降级。

    使用内存字典模拟 Redis 操作，不支持持久化和分布式场景。
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, int | None]] = {}  # key -> (value, expire_at_timestamp or None)
        self._counter: dict[str, int] = {}
        import time
        self._time = time.time

    def _is_expired(self, key: str) -> bool:
        """检查 key 是否已过期。"""
        if key not in self._data:
            return True
        _, expire_at = self._data[key]
        if expire_at is not None and self._time() > expire_at:
            del self._data[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._data[key][0]

    async def setex(self, key: str, ttl: int, value: str) -> None:
        expire_at = self._time() + ttl
        self._data[key] = (value, expire_at)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._counter.pop(key, None)

    async def incr(self, key: str) -> int:
        self._is_expired(key)
        val = self._counter.get(key, 0) + 1
        self._counter[key] = val
        return val

    async def expire(self, key: str, ttl: int) -> None:
        if key in self._counter:
            expire_at = self._time() + ttl
            self._data[key] = (str(self._counter[key]), expire_at)

    async def ttl(self, key: str) -> int:
        if self._is_expired(key):
            return -2
        _, expire_at = self._data.get(key, (None, None))
        if expire_at is None:
            return -1
        remaining = int(expire_at - self._time())
        return max(0, remaining)

    async def exists(self, key: str) -> int:
        return 0 if self._is_expired(key) else 1

    async def close(self) -> None:
        self._data.clear()
        self._counter.clear()
