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
from app.services.chat_service import create_chat_service
from app.services.connection_manager import create_connection_manager
from app.services.image import create_image_service
from app.services.providers import build_provider_registry
from app.services.scheduler import SchedulerManager
from app.services.storage import create_storage_service
from app.services.admin.admin_service import AdminAuthService

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

        # 初始化管理员认证服务（独立 secret/issuer）
        app.state.admin_auth_service = AdminAuthService(
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

        # 初始化图片服务
        app.state.image_service = create_image_service()

        # 初始化存储服务
        app.state.storage_service = create_storage_service(
            provider=resolved_settings.storage_provider,
        )

        # 初始化聊天服务
        app.state.chat_service = create_chat_service(redis=redis_client)

        # 初始化 WebSocket 连接管理器
        connection_manager = create_connection_manager(
            redis=redis_client,
            auth_service=app.state.auth_service,
            chat_service=app.state.chat_service,
        )
        app.state.connection_manager = connection_manager
        await connection_manager.start()

        # 配置定时任务
        scheduler_manager: SchedulerManager = app.state.scheduler
        scheduler_manager.add_weekly_report_job(
            settings=resolved_settings,
            db_session_factory=session_factory,
            redis_client=redis_client,
        )

        try:
            app.state.scheduler.start()
            logger.info(
                "Application started",
                extra={"env": resolved_settings.app_env},
            )
            yield
        finally:
            # 停止 WebSocket 连接管理器
            await connection_manager.stop()
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
        self._lists: dict[str, list[str]] = {}  # List 数据结构
        self._list_expires: dict[str, int | None] = {}  # List TTL 管理
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

    def _is_list_expired(self, key: str) -> bool:
        """检查 List key 是否已过期。"""
        if key not in self._lists:
            return True
        expire_at = self._list_expires.get(key)
        if expire_at is not None and self._time() > expire_at:
            del self._lists[key]
            del self._list_expires[key]
            return True
        return False

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._data[key][0]

    async def setex(self, key: str, ttl: int, value: str) -> None:
        expire_at = self._time() + ttl
        self._data[key] = (value, expire_at)

    async def delete(self, key: str) -> int:
        """删除 key，返回被删除的数量。"""
        count = 0
        if key in self._data:
            del self._data[key]
            count += 1
        if key in self._counter:
            del self._counter[key]
        if key in self._lists:
            del self._lists[key]
            count += 1
        if key in self._list_expires:
            del self._list_expires[key]
        return count

    async def incr(self, key: str) -> int:
        self._is_expired(key)
        val = self._counter.get(key, 0) + 1
        self._counter[key] = val
        return val

    async def expire(self, key: str, ttl: int) -> None:
        """设置 key 的过期时间。"""
        expire_at = self._time() + ttl
        # 处理 string 类型
        if key in self._data:
            value, _ = self._data[key]
            self._data[key] = (value, expire_at)
        # 处理 counter 类型（可能在 _data 或 _counter 中）
        if key in self._counter:
            self._data[key] = (str(self._counter[key]), expire_at)
        # 处理 list 类型
        if key in self._lists:
            self._list_expires[key] = expire_at

    async def ttl(self, key: str) -> int:
        if self._is_expired(key) and self._is_list_expired(key):
            return -2
        _, expire_at = self._data.get(key, (None, None))
        if expire_at is None:
            # 检查 List TTL
            list_expire = self._list_expires.get(key)
            if list_expire is None:
                return -1
            remaining = int(list_expire - self._time())
            return max(0, remaining)
        remaining = int(expire_at - self._time())
        return max(0, remaining)

    async def exists(self, key: str) -> int:
        """检查 key 是否存在。"""
        # 检查 string 类型
        if key in self._data and not self._is_expired(key):
            return 1
        # 检查 counter 类型
        if key in self._counter:
            return 1
        # 检查 list 类型
        if key in self._lists and not self._is_list_expired(key):
            return 1
        return 0

    # List 操作
    async def rpush(self, key: str, value: str) -> int:
        """向列表尾部添加元素。"""
        self._is_list_expired(key)
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key].append(value)
        return len(self._lists[key])

    async def ltrim(self, key: str, start: int, stop: int) -> None:
        """裁剪列表，保留指定范围内的元素。"""
        self._is_list_expired(key)
        if key in self._lists:
            # 处理负索引
            lst = self._lists[key]
            length = len(lst)

            # 转换负索引为正索引
            if start < 0:
                start = max(0, length + start)
            if stop < 0:
                stop = length + stop

            # Redis 的 stop 是包含的
            self._lists[key] = lst[start:stop + 1]

    async def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """获取列表指定范围内的元素。"""
        self._is_list_expired(key)
        if key not in self._lists:
            return []

        lst = self._lists[key]
        length = len(lst)

        # 转换负索引
        if start < 0:
            start = max(0, length + start)
        if stop < 0:
            stop = length + stop

        # Redis 的 stop 是包含的
        return lst[start:stop + 1]

    async def close(self) -> None:
        self._data.clear()
        self._counter.clear()
        self._lists.clear()
        self._list_expires.clear()
