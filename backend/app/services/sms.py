"""短信验证码服务模块。

提供短信验证码发送能力，支持 Mock、控制台日志、阿里云三种 Provider。
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

    适用于开发和测试环境，无需真实短信通道。
    """

    async def send_code(self, phone: str) -> dict[str, Any]:
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

    Args:
        provider: 服务提供者名称，可选 mock / console / aliyun

    Returns:
        短信验证码服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in SMS_SERVICES:
        available = ", ".join(SMS_SERVICES.keys())
        raise ValueError(f"未知的短信服务 Provider: {provider}，可用选项: [{available}]")
    return SMS_SERVICES[provider]()
