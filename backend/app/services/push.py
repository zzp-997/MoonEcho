"""推送服务模块。

提供推送通知能力，支持 Mock 控制台日志和极光推送两种 Provider。
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol 定义 — 推送服务接口契约
# ---------------------------------------------------------------------------

class PushProtocol(Protocol):
    """推送通知服务接口。"""

    async def send(self, user_id: str, title: str, content: str) -> dict[str, Any]:
        """发送推送通知，返回结构化结果。

        Args:
            user_id: 目标用户 ID
            title: 推送标题
            content: 推送内容

        Returns:
            {"success": bool, "message_id": str}
        """
        ...

    async def send_batch(
        self, user_ids: list[str], title: str, content: str
    ) -> dict[str, Any]:
        """批量发送推送通知。

        Args:
            user_ids: 目标用户 ID 列表
            title: 推送标题
            content: 推送内容

        Returns:
            {"success": bool, "success_count": int, "fail_count": int, "message_id": str}
        """
        ...


# ---------------------------------------------------------------------------
# Mock 实现 — 控制台日志输出
# ---------------------------------------------------------------------------

class MockPushService:
    """Mock 推送通知服务，输出到控制台日志。

    适用于开发和测试环境，无需真实推送通道。
    """

    async def send(self, user_id: str, title: str, content: str) -> dict[str, Any]:
        message_id = f"mock-push-{uuid.uuid4().hex[:8]}"
        logger.info(
            "[MockPush] 推送通知 -> 用户: %s, 标题: %s, 内容: %s, ID: %s",
            user_id, title, content[:50] if len(content) > 50 else content, message_id,
        )
        return {
            "success": True,
            "message_id": message_id,
        }

    async def send_batch(
        self, user_ids: list[str], title: str, content: str
    ) -> dict[str, Any]:
        message_id = f"mock-batch-push-{uuid.uuid4().hex[:8]}"
        logger.info(
            "[MockPush] 批量推送 -> 用户数: %d, 标题: %s, 内容: %s, ID: %s",
            len(user_ids), title, content[:50] if len(content) > 50 else content, message_id,
        )
        return {
            "success": True,
            "success_count": len(user_ids),
            "fail_count": 0,
            "message_id": message_id,
        }


# ---------------------------------------------------------------------------
# 极光推送 — 真实调用占位
# ---------------------------------------------------------------------------

class JPushService:
    """极光推送服务（真实调用占位）。

    TODO: 接入极光推送 SDK (jpush)
    - 需要配置 app_key、master_secret
    - 支持别名推送、标签推送、广播推送
    - 支持安卓和 iOS 平台差异化配置
    """

    def __init__(
        self,
        app_key: str = "",
        master_secret: str = "",
    ) -> None:
        self._app_key = app_key
        self._master_secret = master_secret

    async def send(self, user_id: str, title: str, content: str) -> dict[str, Any]:
        # TODO: 接入极光推送 SDK
        # import jpush
        # _jpush = jpush.JPush(self._app_key, self._master_secret)
        # push = _jpush.create_push()
        # push.audience = jpush.audience(jpush.alias(user_id))
        # push.message = jpush.message(content, title=title)
        logger.warning("[JPush] 极光推送 SDK 尚未接入，返回占位响应")
        return {
            "success": True,
            "message_id": f"jpush-{uuid.uuid4().hex[:8]}",
        }

    async def send_batch(
        self, user_ids: list[str], title: str, content: str
    ) -> dict[str, Any]:
        # TODO: 接入极光推送 SDK 批量推送
        logger.warning("[JPush] 极光推送 SDK 尚未接入，返回占位响应")
        return {
            "success": True,
            "success_count": len(user_ids),
            "fail_count": 0,
            "message_id": f"jpush-batch-{uuid.uuid4().hex[:8]}",
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

PUSH_SERVICES: dict[str, type[MockPushService | JPushService]] = {
    "mock": MockPushService,
    "jpush_free": JPushService,
    "jpush": JPushService,
}


def create_push_service(
    provider: str = "mock",
    **kwargs: Any,
) -> MockPushService | JPushService:
    """根据配置创建推送服务实例。

    Args:
        provider: 服务提供者名称，可选 mock / jpush_free / jpush
        **kwargs: 传递给推送服务构造函数的额外参数

    Returns:
        推送服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in PUSH_SERVICES:
        available = ", ".join(PUSH_SERVICES.keys())
        raise ValueError(f"未知的推送服务 Provider: {provider}，可用选项: [{available}]")
    return PUSH_SERVICES[provider](**kwargs)
