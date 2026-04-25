"""开发环境配置参考。

注意：实际运行时由 .env.development 文件和系统环境变量驱动，
load_settings() 不会读取此文件。此文件仅作为配置参考。
"""

from app.core.config import AppSettings

# 开发环境配置参考（实际配置以 .env.development 为准）
settings = AppSettings(
    app_env="development",
    debug=True,
    mock_enabled=True,
    sms_provider="mock",
    content_audit_provider="pass",
    storage_provider="local",
    push_provider="mock",
    ai_provider="mock",
)
