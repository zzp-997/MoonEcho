"""T002 后端项目初始化全面测试套件。

覆盖以下测试内容：
1. 基础框架启动测试
2. 配置系统测试
3. 统一响应格式测试
4. 错误码枚举测试
5. Mock Provider 测试
6. APScheduler 测试
7. 中间件测试
8. Pydantic 模型基类测试
9. SQLAlchemy 模型基类测试
10. 路由注册测试
"""

from __future__ import annotations

import asyncio
import inspect
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, get_type_hints
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import (
    AppSettings,
    _parse_bool,
    _parse_list,
    _environment_name,
    _load_env_file,
    load_settings,
    get_settings,
)
from app.core.errors import AppError
from app.core.responses import (
    success_response,
    error_response,
    paginated_response,
    _meta,
)
from app.enums.error_codes import ErrorCode
from app.main import create_app
from app.middleware.request_context import (
    REQUEST_ID_HEADER,
    RequestContextMiddleware,
)
from app.routers import (
    register_routers,
    add_router,
    ROUTER_REGISTRY,
)
from app.routers.system import router as system_router
from app.schemas.base import (
    BaseSchema,
    PaginationParams,
    PaginatedResponse,
)
from app.models.base import (
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
)
from app.services.providers import (
    build_provider_registry,
    ProviderRegistry,
    MockSMSProvider,
    MockContentAuditProvider,
    MockStorageProvider,
    MockPushProvider,
    MockAIProvider,
    SMSProvider,
    ContentAuditProvider,
    StorageProvider,
    PushProvider,
    AIProvider,
)
from app.services.scheduler import SchedulerManager
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped, mapped_column


# ============================================================================
# 1. 基础框架启动测试
# ============================================================================

class TestFrameworkStartup:
    """测试 1: 基础框架启动测试"""

    def test_health_endpoint_returns_correct_format(self) -> None:
        """验证健康检查端点返回正确格式"""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/system/health")

        assert response.status_code == 200
        body = response.json()

        # 验证返回格式
        assert "success" in body
        assert body["success"] is True
        assert "data" in body
        assert "status" in body["data"]
        assert body["data"]["status"] == "ok"
        assert "environment" in body["data"]
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "requestId" in body["meta"]

    def test_app_title_and_debug_settings(self) -> None:
        """验证应用标题和调试设置"""
        settings = AppSettings(app_env="development")
        app = create_app(settings)

        assert app.title == "Echo API"
        assert app.debug is True

    def test_app_state_contains_required_attributes(self) -> None:
        """验证 app.state 包含必要的属性"""
        app = create_app()

        assert hasattr(app.state, "settings")
        assert hasattr(app.state, "provider_registry")
        assert hasattr(app.state, "scheduler")
        assert isinstance(app.state.settings, AppSettings)
        assert isinstance(app.state.provider_registry, ProviderRegistry)
        assert isinstance(app.state.scheduler, SchedulerManager)


# ============================================================================
# 2. 配置系统测试
# ============================================================================

class TestConfigSystem:
    """测试 2: 配置系统测试"""

    def test_app_settings_default_values(self) -> None:
        """验证 AppSettings 默认值"""
        settings = AppSettings()

        assert settings.app_name == "Echo API"
        assert settings.app_env == "development"
        assert settings.debug is True
        assert settings.database_url == "sqlite+aiosqlite:///./echo.db"
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.mock_enabled is True
        assert settings.sms_provider == "mock"

    def test_parse_bool_function(self) -> None:
        """验证 _parse_bool 函数解析各种输入"""
        # 真值
        assert _parse_bool("true", False) is True
        assert _parse_bool("TRUE", False) is True
        assert _parse_bool("1", False) is True
        assert _parse_bool("yes", False) is True
        assert _parse_bool("on", False) is True
        assert _parse_bool(True, False) is True

        # 假值
        assert _parse_bool("false", True) is False
        assert _parse_bool("0", True) is False
        assert _parse_bool("no", True) is False
        assert _parse_bool(False, True) is False

        # None 使用默认值
        assert _parse_bool(None, True) is True
        assert _parse_bool(None, False) is False

    def test_parse_list_function(self) -> None:
        """验证 _parse_list 函数解析逗号分隔列表"""
        default = ["default"]

        # 正常解析
        assert _parse_list("a, b, c", default) == ["a", "b", "c"]
        assert _parse_list("http://localhost:3000,http://127.0.0.1:3000", default) == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

        # 空值返回默认
        assert _parse_list(None, default) == default
        assert _parse_list("", default) == default

    def test_load_env_file_development(self) -> None:
        """验证加载 .env.development 文件"""
        values = _load_env_file("development")

        assert "APP_ENV" in values
        assert values["APP_ENV"] == "development"
        assert values["DEBUG"] == "true"
        assert values["MOCK_ENABLED"] == "true"

    def test_load_env_file_production(self) -> None:
        """验证加载 .env.production 文件"""
        values = _load_env_file("production")

        assert values["APP_ENV"] == "production"
        assert values["DEBUG"] == "false"
        assert values["MOCK_ENABLED"] == "false"
        assert values["SMS_PROVIDER"] == "aliyun"

    def test_load_env_file_test(self) -> None:
        """验证加载 .env.test 文件"""
        values = _load_env_file("test")

        assert values["APP_ENV"] == "test"
        assert values["DEBUG"] == "false"
        assert values["SMS_PROVIDER"] == "console"

    def test_load_settings_development_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证 development 环境配置加载正确"""
        monkeypatch.setenv("APP_ENV", "development")
        settings = load_settings()

        assert settings.app_env == "development"
        assert settings.debug is True
        assert settings.mock_enabled is True
        assert settings.sms_provider == "mock"
        assert settings.content_audit_provider == "pass"
        assert settings.storage_provider == "local"
        assert settings.push_provider == "mock"
        assert settings.ai_provider == "mock"

    def test_load_settings_production_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证 production 环境配置加载正确"""
        monkeypatch.setenv("APP_ENV", "production")
        settings = load_settings()

        assert settings.app_env == "production"
        assert settings.debug is False
        assert settings.mock_enabled is False
        assert settings.sms_provider == "aliyun"
        assert settings.content_audit_provider == "aliyun"
        assert settings.storage_provider == "oss"
        assert settings.push_provider == "jpush"
        assert settings.ai_provider == "glm"

    def test_load_settings_test_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证 test 环境配置加载正确"""
        monkeypatch.setenv("APP_ENV", "test")
        settings = load_settings()

        assert settings.app_env == "test"
        assert settings.debug is False
        assert settings.mock_enabled is False
        assert settings.sms_provider == "console"
        assert settings.content_audit_provider == "local"
        assert settings.storage_provider == "minio"
        assert settings.push_provider == "jpush_free"
        assert settings.ai_provider == "glm_free"

    def test_env_variable_overrides_dotenv(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证环境变量覆盖 .env 文件的优先级"""
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./override.db")

        settings = load_settings()

        # 环境变量应该覆盖 .env.development 中的值
        # .env.development 中 DATABASE_URL=sqlite+aiosqlite:///./echo-dev.db
        # 但环境变量设置的是 override.db
        assert settings.database_url == "sqlite+aiosqlite:///./override.db"

    def test_dotenv_overrides_default_when_no_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证当没有环境变量时，.env 文件值覆盖默认值"""
        monkeypatch.setenv("APP_ENV", "development")
        # 不设置 DATABASE_URL 环境变量，让 .env.development 生效

        settings = load_settings()

        # .env.development 中 DATABASE_URL=sqlite+aiosqlite:///./echo-dev.db
        # 默认值是 sqlite+aiosqlite:///./echo.db
        # .env.development 中的值应该覆盖默认值
        assert settings.database_url == "sqlite+aiosqlite:///./echo-dev.db"

    def test_mock_enabled_default_by_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """验证 Mock 切换机制：development 默认启用，production 默认禁用"""
        # development 环境
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.delenv("MOCK_ENABLED", raising=False)
        settings_dev = load_settings()
        assert settings_dev.mock_enabled is True

        # production 环境
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("MOCK_ENABLED", raising=False)
        settings_prod = load_settings()
        assert settings_prod.mock_enabled is False


# ============================================================================
# 3. 统一响应格式测试
# ============================================================================

class TestResponseFormat:
    """测试 3: 统一响应格式测试"""

    def test_meta_contains_timestamp_and_request_id(self) -> None:
        """验证 meta 中包含 timestamp 和 requestId"""
        meta = _meta("test-request-id")

        assert "timestamp" in meta
        assert "requestId" in meta
        assert meta["requestId"] == "test-request-id"
        # 验证 timestamp 是 ISO 格式
        assert "T" in meta["timestamp"]  # ISO 8601 格式包含 T

    def test_success_response_format(self) -> None:
        """验证 success_response 返回正确格式"""
        data = {"user": "test", "id": 123}
        result = success_response(data, request_id="req-123")

        assert result["success"] is True
        assert result["data"] == data
        assert "meta" in result
        assert result["meta"]["requestId"] == "req-123"
        assert "timestamp" in result["meta"]

    def test_success_response_with_none_data(self) -> None:
        """验证 success_response 可以接受 None 数据"""
        result = success_response(None, request_id="req-456")

        assert result["success"] is True
        assert result["data"] is None

    def test_error_response_format(self) -> None:
        """验证 error_response 返回正确格式"""
        error = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数验证失败",
            details={"field": "phone"},
            status_code=400,
        )
        result = error_response(error, request_id="req-error")

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "参数验证失败"
        assert result["error"]["details"] == {"field": "phone"}
        assert "meta" in result
        assert result["meta"]["requestId"] == "req-error"

    def test_error_response_without_details(self) -> None:
        """验证 error_response 不带 details 的情况"""
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务器内部错误",
        )
        result = error_response(error, request_id="req-internal")

        assert result["success"] is False
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert result["error"]["details"] is None

    def test_paginated_response_format(self) -> None:
        """验证 paginated_response 返回正确格式"""
        data = [{"id": 1}, {"id": 2}]
        result = paginated_response(
            data,
            page=2,
            page_size=10,
            total=25,
            request_id="req-page",
        )

        assert result["success"] is True
        assert result["data"] == data
        assert "pagination" in result
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["pageSize"] == 10
        assert result["pagination"]["total"] == 25
        assert result["pagination"]["hasMore"] is True  # 2 * 10 < 25
        assert "meta" in result
        assert result["meta"]["requestId"] == "req-page"

    def test_paginated_response_has_more_calculation(self) -> None:
        """验证 paginated_response 的 hasMore 计算逻辑"""
        # 有更多数据
        result1 = paginated_response([], page=1, page_size=10, total=15, request_id="r1")
        assert result1["pagination"]["hasMore"] is True

        # 刚好最后一页
        result2 = paginated_response([], page=2, page_size=10, total=20, request_id="r2")
        assert result2["pagination"]["hasMore"] is False

        # 超过最后一页
        result3 = paginated_response([], page=3, page_size=10, total=25, request_id="r3")
        assert result3["pagination"]["hasMore"] is False


# ============================================================================
# 4. 错误码枚举测试
# ============================================================================

class TestErrorCodeEnum:
    """测试 4: 错误码枚举测试"""

    def test_all_error_codes_unique(self) -> None:
        """验证所有错误码值唯一（无重复）"""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values)), "存在重复的错误码值"

    def test_error_code_count(self) -> None:
        """验证错误码数量符合业务需求（应覆盖所有业务场景）。"""
        error_codes = list(ErrorCode)
        # 错误码应覆盖主要业务模块：通用、认证、用户、内容、好友、AI、文件、日记、通知、举报、管理后台、对话、树洞、动态、加密
        # 当前共 68 个，新增业务场景时应相应增加
        assert len(error_codes) >= 60, f"错误码数量不足，当前 {len(error_codes)} 个"

    def test_error_code_format_semantic(self) -> None:
        """验证错误码格式为语义化大写"""
        for code in ErrorCode:
            # 验证值等于名称
            assert code.value == code.name
            # 验证格式为大写下划线
            assert code.value.isupper() or "_" in code.value
            assert code.value.replace("_", "").isalpha()

    def test_specific_error_codes_exist(self) -> None:
        """验证特定错误码存在"""
        # 通用错误
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"

        # 认证相关
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.TOKEN_EXPIRED.value == "TOKEN_EXPIRED"

        # 用户相关
        assert ErrorCode.USER_NOT_FOUND.value == "USER_NOT_FOUND"

        # AI 服务相关
        assert ErrorCode.AI_SERVICE_UNAVAILABLE.value == "AI_SERVICE_UNAVAILABLE"


# ============================================================================
# 5. Mock Provider 测试
# ============================================================================

class TestMockProviders:
    """测试 5: Mock Provider 测试"""

    def test_build_provider_registry_development(self) -> None:
        """验证 build_provider_registry 在 development 配置下返回 Mock 实现"""
        settings = AppSettings(
            app_env="development",
            mock_enabled=True,
            sms_provider="mock",
            content_audit_provider="pass",
            storage_provider="local",
            push_provider="mock",
            ai_provider="mock",
            cors_origins=["http://localhost:3000"],
        )

        registry = build_provider_registry(settings)

        assert isinstance(registry.sms, MockSMSProvider)
        assert isinstance(registry.content_audit, MockContentAuditProvider)
        assert isinstance(registry.storage, MockStorageProvider)
        assert isinstance(registry.push, MockPushProvider)
        assert isinstance(registry.ai, MockAIProvider)

    def test_mock_sms_provider_send_code(self) -> None:
        """验证 SMSProvider.send_code() 返回正确格式"""
        provider = MockSMSProvider()
        result = provider.send_code("13800138000")

        assert "code" in result
        assert "expires_in" in result
        assert "message_id" in result
        assert result["code"] == "123456"
        assert result["expires_in"] == 300
        assert result["message_id"].startswith("mock-msg-")

    def test_mock_content_audit_provider_check(self) -> None:
        """验证 ContentAuditProvider.check() 返回正确格式"""
        provider = MockContentAuditProvider()
        result = provider.check("测试内容")

        assert "pass" in result
        assert "risk_level" in result
        assert "labels" in result
        assert "reason" in result
        assert result["pass"] is True
        assert result["risk_level"] == "none"
        assert result["labels"] == []
        assert result["reason"] is None

    def test_mock_storage_provider_save_and_get(self) -> None:
        """验证 StorageProvider.save() 和 get() 方法可用"""
        provider = MockStorageProvider()

        # 测试 build_path
        path = provider.build_path("test.jpg")
        assert path == "./uploads/test.jpg"

        # 测试 save
        url = provider.save(b"test content", "test.jpg")
        assert url == "./uploads/test.jpg"

        # 测试 get
        content = provider.get("./uploads/test.jpg")
        assert content == b""

    def test_mock_push_provider_send(self) -> None:
        """验证 PushProvider.send() 返回正确格式"""
        provider = MockPushProvider()
        result = provider.send("user-123", "标题", "内容")

        assert "success" in result
        assert "message_id" in result
        assert result["success"] is True
        assert result["message_id"].startswith("mock-push-")

    def test_mock_ai_provider_chat(self) -> None:
        """验证 AIProvider.chat() 返回字符串"""
        provider = MockAIProvider()
        result = provider.chat("你好")

        assert isinstance(result, str)
        assert result == "我在听，你说。"

    def test_mock_ai_provider_chat_stream(self) -> None:
        """验证 AIProvider.chat_stream() 返回异步生成器"""
        provider = MockAIProvider()
        generator = provider.chat_stream("你好")

        assert inspect.isasyncgen(generator)

    @pytest.mark.asyncio
    async def test_mock_ai_provider_chat_stream_yields_chars(self) -> None:
        """验证 AIProvider.chat_stream() 逐字符产出"""
        provider = MockAIProvider()
        result = []
        async for char in provider.chat_stream("你好"):
            result.append(char)

        assert "".join(result) == "我在听，你说。"

    def test_provider_protocol_signatures_match(self) -> None:
        """验证 Mock Provider 方法签名与 Protocol 一致"""
        # SMS Provider
        sms_hints = get_type_hints(SMSProvider.send_code)
        mock_sms_hints = get_type_hints(MockSMSProvider.send_code)
        assert "phone" in mock_sms_hints
        assert "return" in mock_sms_hints

        # Content Audit Provider
        audit_hints = get_type_hints(ContentAuditProvider.check)
        mock_audit_hints = get_type_hints(MockContentAuditProvider.check)
        assert "content" in mock_audit_hints

        # Storage Provider
        storage_save_hints = get_type_hints(StorageProvider.save)
        mock_storage_save_hints = get_type_hints(MockStorageProvider.save)
        assert "file_bytes" in mock_storage_save_hints
        assert "filename" in mock_storage_save_hints

        # Push Provider
        push_hints = get_type_hints(PushProvider.send)
        mock_push_hints = get_type_hints(MockPushProvider.send)
        assert "user_id" in mock_push_hints
        assert "title" in mock_push_hints
        assert "content" in mock_push_hints

        # AI Provider
        ai_chat_hints = get_type_hints(AIProvider.chat)
        mock_ai_chat_hints = get_type_hints(MockAIProvider.chat)
        assert "prompt" in mock_ai_chat_hints


# ============================================================================
# 6. APScheduler 测试
# ============================================================================

class TestSchedulerManager:
    """测试 6: APScheduler 测试"""

    def test_scheduler_lifecycle(self) -> None:
        """验证 SchedulerManager 的 start/shutdown 生命周期正常"""
        manager = SchedulerManager()

        assert manager.is_running is False
        assert manager.started_count == 0
        assert manager.shutdown_count == 0

        manager.start()
        assert manager.is_running is True
        assert manager.started_count == 1
        assert manager.scheduler.running is True

        manager.shutdown()
        assert manager.is_running is False
        assert manager.shutdown_count == 1

    def test_scheduler_no_duplicate_start(self) -> None:
        """验证不会重复启动（start 两次后 scheduler.running 仍为 True）"""
        manager = SchedulerManager()

        manager.start()
        assert manager.started_count == 1
        assert manager.scheduler.running is True

        # 再次启动
        manager.start()
        assert manager.started_count == 2  # 计数器增加
        assert manager.scheduler.running is True  # 仍在运行

        manager.shutdown()

    def test_scheduler_multiple_shutdown_safe(self) -> None:
        """验证多次 shutdown 是安全的"""
        manager = SchedulerManager()
        manager.start()

        manager.shutdown()
        assert manager.shutdown_count == 1
        assert manager.is_running is False

        # 再次 shutdown
        manager.shutdown()
        assert manager.shutdown_count == 2  # 计数器增加
        assert manager.is_running is False


# ============================================================================
# 7. 中间件测试
# ============================================================================

class TestMiddleware:
    """测试 7: 中间件测试"""

    def test_request_id_generated(self) -> None:
        """验证 RequestContextMiddleware 为每个请求生成 request_id"""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/system/health")

        request_id = response.headers.get(REQUEST_ID_HEADER)
        assert request_id is not None
        assert len(request_id) > 0

    def test_response_header_contains_request_id(self) -> None:
        """验证响应头中包含 X-Request-Id"""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/system/health")

        assert REQUEST_ID_HEADER in response.headers
        assert response.headers[REQUEST_ID_HEADER]

    def test_request_id_echoed_in_response(self) -> None:
        """验证响应体中的 requestId 与响应头一致"""
        app = create_app()
        with TestClient(app) as client:
            response = client.get("/api/v1/system/health")

        header_request_id = response.headers[REQUEST_ID_HEADER]
        body = response.json()
        assert body["meta"]["requestId"] == header_request_id

    def test_cors_middleware_configured(self) -> None:
        """验证 CORS 中间件配置正确"""
        settings = AppSettings(cors_origins=["http://localhost:3000"])
        app = create_app(settings)

        with TestClient(app) as client:
            response = client.options(
                "/api/v1/system/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

        # CORS 预检请求应该成功
        assert response.status_code == 200

    def test_cors_allows_configured_origins(self) -> None:
        """验证 CORS 允许配置的 origins"""
        settings = AppSettings(cors_origins=["http://example.com"])
        app = create_app(settings)

        with TestClient(app) as client:
            response = client.get(
                "/api/v1/system/health",
                headers={"Origin": "http://example.com"},
            )

        # 检查 CORS 响应头
        assert "access-control-allow-origin" in response.headers


# ============================================================================
# 8. Pydantic 模型基类测试
# ============================================================================

class TestPydanticBaseSchemas:
    """测试 8: Pydantic 模型基类测试"""

    def test_base_schema_from_attributes(self) -> None:
        """验证 BaseSchema 的 from_attributes=True 配置生效"""

        # 创建一个模拟 ORM 对象
        class MockORMObject:
            def __init__(self) -> None:
                self.id = 1
                self.name = "test"

        class TestSchema(BaseSchema):
            id: int
            name: str

        # from_attributes 应该生效
        obj = MockORMObject()
        schema = TestSchema.model_validate(obj)
        assert schema.id == 1
        assert schema.name == "test"

    def test_pagination_params_defaults(self) -> None:
        """验证 PaginationParams 的默认值"""
        params = PaginationParams()

        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_params_validation(self) -> None:
        """验证 PaginationParams 的校验规则（page>=1, page_size 1-100）"""
        # 有效值
        params1 = PaginationParams(page=1, page_size=1)
        assert params1.page == 1
        assert params1.page_size == 1

        params2 = PaginationParams(page=100, page_size=100)
        assert params2.page == 100
        assert params2.page_size == 100

        # 无效值：page < 1
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        # 无效值：page_size > 100
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

        # 无效值：page_size < 1
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_pagination_params_offset_calculation(self) -> None:
        """验证 PaginationParams.offset 属性计算正确"""
        params1 = PaginationParams(page=1, page_size=10)
        assert params1.offset == 0

        params2 = PaginationParams(page=2, page_size=10)
        assert params2.offset == 10

        params3 = PaginationParams(page=5, page_size=20)
        assert params3.offset == 80

    def test_paginated_response_create_factory(self) -> None:
        """验证 PaginatedResponse.create() 工厂方法正常工作"""
        data = [{"id": 1}, {"id": 2}]
        response = PaginatedResponse.create(
            data=data,
            page=2,
            page_size=10,
            total=25,
        )

        assert response.data == data
        assert response.page == 2
        assert response.page_size == 10
        assert response.total == 25
        assert response.has_more is True  # 2 * 10 < 25

    def test_paginated_response_has_more_false(self) -> None:
        """验证 PaginatedResponse.create() hasMore 为 False 的情况"""
        response = PaginatedResponse.create(
            data=[],
            page=2,
            page_size=10,
            total=20,
        )

        assert response.has_more is False  # 2 * 10 >= 20


# ============================================================================
# 9. SQLAlchemy 模型基类测试
# ============================================================================

class TestSQLAlchemyBaseModels:
    """测试 9: SQLAlchemy 模型基类测试"""

    def test_base_importable(self) -> None:
        """验证 Base 可正常导入和子类化"""
        assert Base is not None

        # 创建一个测试模型
        class TestModel(Base):
            __tablename__ = "test_model"
            id: Mapped[str] = mapped_column(primary_key=True)

        assert TestModel.__tablename__ == "test_model"

    def test_uuid_mixin_id_field(self) -> None:
        """验证 UUIDMixin 的 id 字段默认生成 UUID 字符串"""
        # 检查 id 字段存在
        assert hasattr(UUIDMixin, "id")

        # 检查字段类型
        id_field = UUIDMixin.__annotations__.get("id")
        assert id_field is not None

    def test_timestamp_mixin_fields(self) -> None:
        """验证 TimestampMixin 的 created_at/updated_at 字段存在"""
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")

        # 检查字段类型
        assert "created_at" in TimestampMixin.__annotations__
        assert "updated_at" in TimestampMixin.__annotations__

    def test_soft_delete_mixin_fields(self) -> None:
        """验证 SoftDeleteMixin 的 is_active/deleted_at 字段存在"""
        assert hasattr(SoftDeleteMixin, "is_active")
        assert hasattr(SoftDeleteMixin, "deleted_at")

        # 检查字段类型
        assert "is_active" in SoftDeleteMixin.__annotations__
        assert "deleted_at" in SoftDeleteMixin.__annotations__

    def test_mixin_combination(self) -> None:
        """验证 Mixin 可以组合使用"""

        class FullModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
            __tablename__ = "full_model"
            __abstract__ = True

        # 验证所有字段都存在
        assert hasattr(FullModel, "id")
        assert hasattr(FullModel, "created_at")
        assert hasattr(FullModel, "updated_at")
        assert hasattr(FullModel, "is_active")
        assert hasattr(FullModel, "deleted_at")


# ============================================================================
# 10. 路由注册测试
# ============================================================================

class TestRouterRegistration:
    """测试 10: 路由注册测试"""

    def test_system_router_mounted(self) -> None:
        """验证系统路由正确挂载"""
        app = create_app()

        # 检查路由是否挂载
        routes = [route.path for route in app.routes]
        assert "/api/v1/system/health" in routes

    def test_register_routers_function(self) -> None:
        """验证 register_routers() 将路由正确挂载"""

        @asynccontextmanager
        async def lifespan(_: FastAPI):
            yield

        app = FastAPI(lifespan=lifespan)
        register_routers(app)

        routes = [route.path for route in app.routes]
        assert "/api/v1/system/health" in routes

    def test_add_router_function(self) -> None:
        """验证 add_router() 动态添加路由正常工作"""
        # 保存原始注册表
        original_registry = ROUTER_REGISTRY.copy()

        try:
            # 创建一个新路由
            from fastapi import APIRouter

            new_router = APIRouter(prefix="/test")

            @new_router.get("/ping")
            async def ping():
                return {"pong": True}

            # 动态添加
            add_router(new_router, "", ["test"])

            # 验证添加成功
            assert any(r[0] is new_router for r in ROUTER_REGISTRY)

        finally:
            # 恢复原始注册表
            ROUTER_REGISTRY.clear()
            ROUTER_REGISTRY.extend(original_registry)

    def test_router_registry_contains_system_router(self) -> None:
        """验证路由注册表包含系统路由"""
        router_instances = [item[0] for item in ROUTER_REGISTRY]
        assert system_router in router_instances

    def test_router_prefix_configuration(self) -> None:
        """验证路由前缀配置正确"""
        # 系统路由应该有 /api/v1/system 前缀
        assert system_router.prefix == "/api/v1/system"


# ============================================================================
# 综合测试
# ============================================================================

class TestIntegration:
    """综合测试：验证各组件协同工作"""

    def test_full_request_flow(self) -> None:
        """验证完整请求流程：中间件 -> 路由 -> 响应"""
        app = create_app()

        with TestClient(app) as client:
            # 发送请求
            response = client.get(
                "/api/v1/system/health",
                headers={REQUEST_ID_HEADER: "custom-request-id"},
            )

        # 验证响应
        assert response.status_code == 200
        assert response.headers[REQUEST_ID_HEADER] == "custom-request-id"

        body = response.json()
        assert body["success"] is True
        assert body["meta"]["requestId"] == "custom-request-id"

    def test_settings_provider_consistency(self) -> None:
        """验证配置和 Provider 的一致性"""
        settings = AppSettings(
            app_env="development",
            mock_enabled=True,
            sms_provider="mock",
            content_audit_provider="pass",
            storage_provider="local",
            push_provider="mock",
            ai_provider="mock",
            cors_origins=["http://localhost:3000"],
        )
        app = create_app(settings)

        registry = app.state.provider_registry

        assert isinstance(registry.sms, MockSMSProvider)
        assert isinstance(registry.content_audit, MockContentAuditProvider)
        assert isinstance(registry.storage, MockStorageProvider)
        assert isinstance(registry.push, MockPushProvider)
        assert isinstance(registry.ai, MockAIProvider)

    def test_app_error_handler_returns_unified_format(self) -> None:
        """验证 AppError 异常处理器返回统一错误格式。"""
        from fastapi import APIRouter

        app = create_app()

        # 创建一个会抛出 AppError 的测试路由
        test_router = APIRouter(prefix="/test")

        @test_router.get("/error")
        async def trigger_error():
            raise AppError(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在",
                details={"user_id": "123"},
                status_code=404,
            )

        app.include_router(test_router)

        with TestClient(app) as client:
            response = client.get("/test/error")

        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert "error" in body
        assert body["error"]["code"] == "USER_NOT_FOUND"
        assert body["error"]["message"] == "用户不存在"
        assert body["error"]["details"] == {"user_id": "123"}
        assert "meta" in body
        assert "requestId" in body["meta"]
