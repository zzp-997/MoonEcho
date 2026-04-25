from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import os

from dotenv import dotenv_values

EnvironmentName = Literal["development", "test", "production"]

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


@dataclass(slots=True)
class AppSettings:
    app_name: str = "Echo API"
    app_env: EnvironmentName = "development"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./echo.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] | None = None
    mock_enabled: bool = True
    sms_provider: str = "mock"
    content_audit_provider: str = "pass"
    storage_provider: str = "local"
    push_provider: str = "mock"
    ai_provider: str = "mock"
    zhipu_api_key: str = ""
    ai_daily_limit: int = 10
    ai_daily_limit_vip: int = 100

    def __post_init__(self) -> None:
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]


def _parse_bool(value: str | bool | None, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | int | None, default: int) -> int:
    """解析整数值，优先级：环境变量 > .env 文件 > 默认值"""
    if isinstance(value, int):
        return value
    if value is None:
        return default
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default


def _parse_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _environment_name() -> EnvironmentName:
    return os.getenv("APP_ENV", "development").strip().lower() or "development"


def _load_env_file(environment: EnvironmentName) -> dict[str, str]:
    env_path = BASE_DIR / f".env.{environment}"
    if not env_path.exists():
        return {}
    values = dotenv_values(env_path)
    return {key: value for key, value in values.items() if value is not None}


def _get_value(key: str, env_values: dict[str, str], default: str | None = None) -> str | None:
    """获取配置值，优先级：环境变量 > .env 文件 > 默认值"""
    # 最高优先级：系统环境变量
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    # 次优先级：.env 文件
    if key in env_values and env_values[key] is not None:
        return env_values[key]
    # 默认值
    return default


def load_settings() -> AppSettings:
    environment = _environment_name()
    values = _load_env_file(environment)

    return AppSettings(
        app_env=environment,
        debug=_parse_bool(_get_value("DEBUG", values), environment == "development"),
        database_url=_get_value("DATABASE_URL", values, "sqlite+aiosqlite:///./echo.db") or "sqlite+aiosqlite:///./echo.db",
        redis_url=_get_value("REDIS_URL", values, "redis://localhost:6379/0") or "redis://localhost:6379/0",
        cors_origins=_parse_list(_get_value("CORS_ORIGINS", values), ["http://localhost:3000"]),
        mock_enabled=_parse_bool(_get_value("MOCK_ENABLED", values), environment == "development"),
        sms_provider=_get_value(
            "SMS_PROVIDER",
            values,
            "mock" if environment == "development" else ("console" if environment == "test" else "aliyun"),
        ) or ("mock" if environment == "development" else ("console" if environment == "test" else "aliyun")),
        content_audit_provider=_get_value(
            "CONTENT_AUDIT_PROVIDER",
            values,
            "pass" if environment == "development" else ("local" if environment == "test" else "aliyun"),
        ) or ("pass" if environment == "development" else ("local" if environment == "test" else "aliyun")),
        storage_provider=_get_value(
            "STORAGE_PROVIDER",
            values,
            "local" if environment == "development" else ("minio" if environment == "test" else "oss"),
        ) or ("local" if environment == "development" else ("minio" if environment == "test" else "oss")),
        push_provider=_get_value(
            "PUSH_PROVIDER",
            values,
            "mock" if environment == "development" else ("jpush_free" if environment == "test" else "jpush"),
        ) or ("mock" if environment == "development" else ("jpush_free" if environment == "test" else "jpush")),
        ai_provider=_get_value(
            "AI_PROVIDER",
            values,
            "mock" if environment == "development" else ("glm_free" if environment == "test" else "glm"),
        ) or ("mock" if environment == "development" else ("glm_free" if environment == "test" else "glm")),
        zhipu_api_key=_get_value("ZHIPU_API_KEY", values, "") or "",
        ai_daily_limit=_parse_int(_get_value("AI_DAILY_LIMIT", values), 10),
        ai_daily_limit_vip=_parse_int(_get_value("AI_DAILY_LIMIT_VIP", values), 100),
    )


def get_settings(app) -> AppSettings:
    return app.state.settings
