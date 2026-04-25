"""测试环境配置参考。

注意：实际运行时由 .env.test 文件和系统环境变量驱动，
load_settings() 不会读取此文件。此文件仅作为配置参考。
"""

from app.core.config import AppSettings

# 测试环境配置参考（实际配置以 .env.test 为准）
settings = AppSettings(
    app_env="test",
    debug=False,
    mock_enabled=False,
    sms_provider="console",
    content_audit_provider="local",
    storage_provider="minio",
    push_provider="jpush_free",
    ai_provider="glm_free",
)
