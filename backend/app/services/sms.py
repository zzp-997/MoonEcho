"""短信验证码服务模块。

提供短信验证码发送能力，支持 Mock、控制台日志、阿里云三种 Provider。

安全说明：
- MockSMSService 固定返回验证码 123456，仅允许在开发/测试环境使用
- 生产环境必须使用真实短信服务（如 AliyunSMSService）
- create_sms_service 函数会在生产环境强制检查 Provider 类型
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol 定义 — 短信验证码服务接口契约
# ---------------------------------------------------------------------------

class SMSServiceProtocol(Protocol):
    """短信验证码发送服务接口。"""

    async def send_code(self, phone: str) -> dict[str, Any]:
        """发送验证码，返回结构化结果。

        Args:
            phone: 手机号码

        Returns:
            {"code": "123456", "expires_in": 300, "message_id": "..."}
        """
        ...


# ---------------------------------------------------------------------------
# Mock 实现 — 固定返回验证码 123456
# ---------------------------------------------------------------------------

class MockSMSService:
    """Mock 短信验证码服务，固定返回验证码 123456。

    仅适用于开发和测试环境，生产环境禁止使用。

    安全风险：
    - 固定验证码 123456 可能被攻击者猜测并用于登录绕过
    - 生产环境使用此类将抛出 RuntimeError
    """

    async def send_code(self, phone: str) -> dict[str, Any]:
        # 检查是否为生产环境
        from app.core.config import _environment_name
        env = _environment_name()
        if env == "production":
            raise RuntimeError(
                "生产环境禁止使用 MockSMSService！"
                "请配置 SMS_PROVIDER=aliyun 或其他真实短信服务。"
                "固定验证码 123456 存在被猜测风险，严重威胁账户安全。"
            )
        logger.info("[MockSMS] 向 %s 发送验证码: 123456", phone)
        return {
            "code": "123456",
            "expires_in": 300,
            "message_id": f"mock-msg-{uuid.uuid4().hex[:8]}",
        }


# ---------------------------------------------------------------------------
# Console 实现 — 验证码输出到日志
# ---------------------------------------------------------------------------

class ConsoleSMSService:
    """控制台短信验证码服务，验证码输出到日志。

    适用于测试环境，通过日志查看验证码内容。
    """

    async def send_code(self, phone: str) -> dict[str, Any]:
        import random

        code = f"{random.randint(100000, 999999)}"
        logger.info("[ConsoleSMS] 向 %s 发送验证码: %s", phone, code)
        return {
            "code": code,
            "expires_in": 300,
            "message_id": f"console-msg-{uuid.uuid4().hex[:8]}",
        }


# ---------------------------------------------------------------------------
# 阿里云短信 — 真实调用占位
# ---------------------------------------------------------------------------

class AliyunSMSService:
    """阿里云短信验证码服务（真实调用占位）。

    TODO: 接入阿里云短信 SDK
    - 需要配置 AccessKey、SecretKey、签名、模板 Code
    - 验证码由服务端生成后通过模板参数传递
    """

    async def send_code(self, phone: str) -> dict[str, Any]:
        # TODO: 接入阿里云短信 SDK
        # from alibabacloud_dysmsapi20170525.client import Client
        # from alibabacloud_dysmsapi20170525 import models as dysms_models
        logger.warning("[AliyunSMS] 阿里云短信 SDK 尚未接入，返回占位响应")
        return {
            "code": "aliyun-placeholder",
            "expires_in": 300,
            "message_id": f"aliyun-msg-{uuid.uuid4().hex[:8]}",
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

SMS_SERVICES: dict[str, type[MockSMSService | ConsoleSMSService | AliyunSMSService]] = {
    "mock": MockSMSService,
    "console": ConsoleSMSService,
    "aliyun": AliyunSMSService,
}


def create_sms_service(provider: str = "mock") -> MockSMSService | ConsoleSMSService | AliyunSMSService:
    """根据配置创建短信验证码服务实例。

    生产环境强制检查 Provider 类型，禁止使用 Mock 服务。

    Args:
        provider: 服务提供者名称，可选 mock / console / aliyun

    Returns:
        短信验证码服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
        RuntimeError: 生产环境使用 mock provider 时抛出
    """
    from app.core.config import _environment_name

    if provider not in SMS_SERVICES:
        available = ", ".join(SMS_SERVICES.keys())
        raise ValueError(f"未知的短信服务 Provider: {provider}，可用选项: [{available}]")

    # 生产环境强制检查
    env = _environment_name()
    if env == "production" and provider == "mock":
        raise RuntimeError(
            "生产环境禁止使用 Mock Provider！"
            "请配置 SMS_PROVIDER=aliyun 或 console。"
            "固定验证码 123456 存在被猜测风险，严重威胁账户安全。"
        )

    return SMS_SERVICES[provider]()
