from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import AppSettings, get_settings, load_settings
from app.core.errors import AppError
from app.core.responses import error_response, paginated_response, success_response
from app.enums.error_codes import ErrorCode
from app.main import create_app
from app.middleware.request_context import REQUEST_ID_HEADER, RequestContextMiddleware
from app.services.providers import (
    MockAIProvider,
    MockContentAuditProvider,
    MockPushProvider,
    MockSMSProvider,
    MockStorageProvider,
    build_provider_registry,
)

EXPECTED_ERROR_CODES = {
    # 通用错误
    "VALIDATION_ERROR",
    "INVALID_PARAMETER",
    "MISSING_PARAMETER",
    "RATE_LIMIT_EXCEEDED",
    "INTERNAL_ERROR",
    # 认证相关
    "UNAUTHORIZED",
    "TOKEN_EXPIRED",
    "TOKEN_INVALID",
    "TOKEN_MISSING",
    "VERIFICATION_CODE_EXPIRED",
    "VERIFICATION_CODE_INVALID",
    "VERIFICATION_CODE_TOO_FREQUENT",
    "PASSWORD_INCORRECT",
    # 用户相关
    "USER_NOT_FOUND",
    "USER_ALREADY_EXISTS",
    "USER_DISABLED",
    "USER_UNDERAGE",
    "PROFILE_INCOMPLETE",
    # 内容相关
    "CONTENT_SENSITIVE",
    "CONTENT_TOO_LONG",
    "CONTENT_EMPTY",
    "CONTENT_AUDIT_FAILED",
    "POST_NOT_FOUND",
    "POST_DELETED",
    "POST_ACCESS_DENIED",
    "PUBLISH_TOO_FREQUENT",
    # 社交相关
    "FRIEND_REQUEST_NOT_FOUND",
    "FRIEND_REQUEST_EXPIRED",
    "FRIEND_REQUEST_ALREADY_HANDLED",
    "ALREADY_FRIENDS",
    "CANNOT_ADD_SELF",
    "FRIEND_LIMIT_EXCEEDED",
    "BLOCKED_BY_USER",
    "PERMISSION_DENIED",
    # AI服务相关
    "AI_SERVICE_UNAVAILABLE",
    "AI_SERVICE_TIMEOUT",
    "AI_QUOTA_EXCEEDED",
    "AI_CONVERSATION_NOT_FOUND",
    "AI_CONTEXT_TOO_LONG",
    # 文件相关
    "FILE_TOO_LARGE",
    "FILE_TYPE_NOT_ALLOWED",
    "FILE_UPLOAD_FAILED",
    "FILE_NOT_FOUND",
    # 日记相关
    "DIARY_NOT_FOUND",
    "DIARY_ACCESS_DENIED",
    "DIARY_ALREADY_EXISTS",
    "DIARY_ENCRYPTION_ERROR",
    "DIARY_SYNC_CONFLICT",
    # 通知相关
    "NOTIFICATION_NOT_FOUND",
    "NOTIFICATION_ALREADY_READ",
    "PUSH_FAILED",
    # 举报相关
    "REPORT_NOT_FOUND",
    "REPORT_ALREADY_PROCESSED",
    "APPEAL_NOT_FOUND",
    # 管理后台
    "ADMIN_AUTH_FAILED",
    "ADMIN_PERMISSION_DENIED",
    "ADMIN_ACCOUNT_LOCKED",
    # 对话/私聊相关
    "CONVERSATION_NOT_FOUND",
    "MESSAGE_NOT_FOUND",
    "MESSAGE_TOO_FREQUENT",
    "WEBSOCKET_CONNECTION_FAILED",
    # 树洞相关
    "TREEHOLE_POST_NOT_FOUND",
    "RESONATE_ALREADY_EXISTS",
    "COMMENT_TOO_LONG",
    # 动态相关补充
    "POST_VISIBILITY_DENIED",
    "FOLLOW_ALREADY_EXISTS",
    # 加密相关
    "ENCRYPTION_KEY_NOT_FOUND",
    "DECRYPTION_FAILED",
}


def test_error_code_enum_covers_architecture_contract() -> None:
    assert {code.value for code in ErrorCode} == EXPECTED_ERROR_CODES


def test_success_response_contains_request_meta() -> None:
    payload = success_response({"message": "ok"}, request_id="req-success")

    assert payload["success"] is True
    assert payload["data"] == {"message": "ok"}
    assert payload["meta"]["requestId"] == "req-success"
    assert "timestamp" in payload["meta"]


def test_error_response_contains_error_meta_and_details() -> None:
    payload = error_response(
        AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数错误",
            details={"field": "phone"},
        ),
        request_id="req-error",
    )

    assert payload == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "参数错误",
            "details": {"field": "phone"},
        },
        "meta": {
            "timestamp": payload["meta"]["timestamp"],
            "requestId": "req-error",
        },
    }


def test_paginated_response_contains_pagination_block() -> None:
    payload = paginated_response(
        [{"id": 1}],
        page=2,
        page_size=10,
        total=21,
        request_id="req-page",
    )

    assert payload["success"] is True
    assert payload["data"] == [{"id": 1}]
    assert payload["pagination"] == {
        "page": 2,
        "pageSize": 10,
        "total": 21,
        "hasMore": True,
    }
    assert payload["meta"]["requestId"] == "req-page"


@pytest.mark.parametrize(
    ("environment", "expected_provider", "expected_debug", "expected_mock_enabled"),
    [
        ("development", "mock", True, True),
        ("test", "console", False, False),
        ("production", "aliyun", False, False),
    ],
)
def test_environment_layers_load_expected_values(
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
    expected_provider: str,
    expected_debug: bool,
    expected_mock_enabled: bool,
) -> None:
    monkeypatch.setenv("APP_ENV", environment)

    settings = load_settings()

    assert settings.app_env == environment
    assert settings.debug is expected_debug
    assert settings.sms_provider == expected_provider
    assert settings.mock_enabled is expected_mock_enabled


def test_provider_registry_uses_mock_providers_in_development() -> None:
    settings = AppSettings(
        app_env="development",
        mock_enabled=True,
        sms_provider="mock",
        content_audit_provider="pass",
        storage_provider="local",
        push_provider="mock",
        ai_provider="mock",
        cors_origins=["http://localhost:3000"],
        database_url="sqlite+aiosqlite:///./echo.db",
        redis_url="redis://localhost:6379/0",
    )

    registry = build_provider_registry(settings)

    assert isinstance(registry.sms, MockSMSProvider)
    assert isinstance(registry.content_audit, MockContentAuditProvider)
    assert isinstance(registry.storage, MockStorageProvider)
    assert isinstance(registry.push, MockPushProvider)
    assert isinstance(registry.ai, MockAIProvider)


def test_scheduler_starts_and_stops_with_application_lifespan() -> None:
    app = create_app()
    scheduler = app.state.scheduler

    assert scheduler.started_count == 0
    assert scheduler.shutdown_count == 0

    with TestClient(app) as client:
        assert scheduler.started_count == 1
        assert scheduler.is_running is True
        health = client.get("/api/v1/system/health")
        assert health.status_code == 200

    assert scheduler.shutdown_count == 1
    assert scheduler.is_running is False


def test_request_context_middleware_generates_and_echoes_request_id() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/system/health")

    request_id = response.headers[REQUEST_ID_HEADER]
    body = response.json()
    assert request_id
    assert body["meta"]["requestId"] == request_id


def test_request_context_middleware_uses_incoming_request_id() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/system/health",
            headers={REQUEST_ID_HEADER: "req-from-client"},
        )

    assert response.headers[REQUEST_ID_HEADER] == "req-from-client"
    assert response.json()["meta"]["requestId"] == "req-from-client"


def test_request_context_middleware_adds_header_on_plain_route() -> None:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/probe")
    async def probe(request):
        return success_response({"requestId": request.state.request_id}, request.state.request_id)

    with TestClient(app) as client:
        response = client.get("/probe")

    assert REQUEST_ID_HEADER in response.headers


def test_application_registers_expected_project_structure_hooks() -> None:
    app = create_app()

    assert get_settings(app).cors_origins
    assert hasattr(app.state, "provider_registry")
    assert hasattr(app.state, "scheduler")


def test_config_directory_contains_environment_modules() -> None:
    config_dir = PROJECT_ROOT / "config"

    assert (config_dir / "__init__.py").exists()
    assert (config_dir / "development.py").exists()
    assert (config_dir / "test.py").exists()
    assert (config_dir / "production.py").exists()


def test_env_example_documents_required_bootstrap_variables() -> None:
    content = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    for key in {
        "APP_ENV=development",
        "DEBUG=true",
        "DATABASE_URL=",
        "REDIS_URL=",
        "CORS_ORIGINS=",
        "SMS_PROVIDER=",
        "CONTENT_AUDIT_PROVIDER=",
        "STORAGE_PROVIDER=",
        "PUSH_PROVIDER=",
        "AI_PROVIDER=",
        "MOCK_ENABLED=",
    }:
        assert key in content


def test_provider_registry_exposes_all_provider_slots() -> None:
    registry = build_provider_registry(load_settings())

    assert hasattr(registry, "sms")
    assert hasattr(registry, "content_audit")
    assert hasattr(registry, "storage")
    assert hasattr(registry, "push")
    assert hasattr(registry, "ai")


def test_scheduler_manager_wraps_apscheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler

    app = create_app()

    assert isinstance(app.state.scheduler.scheduler, BackgroundScheduler)
