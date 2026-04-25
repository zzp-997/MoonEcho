"""生产环境配置参考。

注意：实际运行时由系统环境变量驱动，不应依赖 .env 文件。
load_settings() 不会读取此文件。此文件仅作为配置参考。
生产环境敏感信息必须通过 CI/CD 系统环境变量注入，切勿硬编码。
"""

from app.core.config import AppSettings

# 生产环境配置参考（实际配置以系统环境变量为准）
settings = AppSettings(
    app_env="production",
    debug=False,
    mock_enabled=False,
    sms_provider="aliyun",
    content_audit_provider="aliyun",
    storage_provider="oss",
    push_provider="jpush",
    ai_provider="glm",
)
