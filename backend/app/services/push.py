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

    async def send(
        self,
        user_id: str,
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送推送通知，返回结构化结果。

        Args:
            user_id: 目标用户 ID
            title: 推送标题
            content: 推送内容
            payload: 附加数据

        Returns:
            {"success": bool, "message_id": str}
        """
        ...

    async def send_batch(
        self,
        user_ids: list[str],
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """批量发送推送通知。

        Args:
            user_ids: 目标用户 ID 列表
            title: 推送标题
            content: 推送内容
            payload: 附加数据

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

    async def send(
        self,
        user_id: str,
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message_id = f"mock-push-{uuid.uuid4().hex[:8]}"
        logger.info(
            "[MockPush] 推送通知 -> 用户: %s, 标题: %s, 内容: %s, payload: %s, ID: %s",
            user_id,
            title,
            content[:50] if len(content) > 50 else content,
            payload,
            message_id,
        )
        return {
            "success": True,
            "message_id": message_id,
        }

    async def send_batch(
        self,
        user_ids: list[str],
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message_id = f"mock-batch-push-{uuid.uuid4().hex[:8]}"
        logger.info(
            "[MockPush] 批量推送 -> 用户数: %d, 标题: %s, 内容: %s, payload: %s, ID: %s",
            len(user_ids),
            title,
            content[:50] if len(content) > 50 else content,
            payload,
            message_id,
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

    使用示例：
        import jpush
        _jpush = jpush.JPush(self._app_key, self._master_secret)
        push = _jpush.create_push()

        # 别名推送（按用户ID）
        push.audience = jpush.audience(jpush.alias(user_id))

        # 通知内容
        push.notification = jpush.notification(
            alert=content,
            android=jpush.android(alert=content, title=title),
            ios=jpush.ios(alert=content, title=title, sound="default"),
        )

        # 附加数据
        if payload:
            push.options = jpush.options(
                extras=payload
            )

        push.send()
    """

    def __init__(
        self,
        app_key: str = "",
        master_secret: str = "",
    ) -> None:
        self._app_key = app_key
        self._master_secret = master_secret
        self._initialized = False

    def _init_jpush(self) -> bool:
        """初始化极光推送 SDK。"""
        if self._initialized:
            return True

        if not self._app_key or not self._master_secret:
            logger.warning(
                "[JPush] 缺少 app_key 或 master_secret，使用 Mock 模式"
            )
            return False

        try:
            # import jpush
            # self._jpush = jpush.JPush(self._app_key, self._master_secret)
            self._initialized = True
            return True
        except ImportError:
            logger.warning("[JPush] jpush SDK 未安装，使用 Mock 模式")
            return False

    async def send(
        self,
        user_id: str,
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送推送通知。

        Args:
            user_id: 目标用户 ID（作为极光推送的别名）
            title: 推送标题
            content: 推送内容
            payload: 附加数据

        Returns:
            推送结果
        """
        message_id = f"jpush-{uuid.uuid4().hex[:8]}"

        if not self._init_jpush():
            # Mock 模式
            logger.info(
                "[JPush-Mock] 推送通知 -> 用户: %s, 标题: %s, 内容: %s",
                user_id, title, content[:50] if len(content) > 50 else content,
            )
            return {
                "success": True,
                "message_id": message_id,
            }

        try:
            # TODO: 接入极光推送 SDK
            # import jpush
            # push = self._jpush.create_push()
            # push.audience = jpush.audience(jpush.alias(user_id))
            # push.notification = jpush.notification(
            #     alert=content,
            #     android=jpush.android(alert=content, title=title),
            #     ios=jpush.ios(alert=content, title=title, sound="default"),
            # )
            # if payload:
            #     push.options = jpush.options(extras=payload)
            # result = push.send()
            # message_id = result.msg_id

            logger.info(
                "[JPush] 推送通知 -> 用户: %s, 标题: %s, 内容: %s",
                user_id, title, content[:50] if len(content) > 50 else content,
            )
            return {
                "success": True,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error("[JPush] 推送发送失败: %s", str(e))
            return {
                "success": False,
                "message_id": None,
                "error": str(e),
            }

    async def send_batch(
        self,
        user_ids: list[str],
        title: str,
        content: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """批量发送推送通知。

        Args:
            user_ids: 目标用户 ID 列表
            title: 推送标题
            content: 推送内容
            payload: 附加数据

        Returns:
            推送结果
        """
        message_id = f"jpush-batch-{uuid.uuid4().hex[:8]}"

        if not self._init_jpush():
            # Mock 模式
            logger.info(
                "[JPush-Mock] 批量推送 -> 用户数: %d, 标题: %s",
                len(user_ids), title,
            )
            return {
                "success": True,
                "success_count": len(user_ids),
                "fail_count": 0,
                "message_id": message_id,
            }

        try:
            # TODO: 接入极光推送 SDK 批量推送
            # 极光推送支持批量别名推送
            # import jpush
            # push = self._jpush.create_push()
            # push.audience = jpush.audience(*[jpush.alias(uid) for uid in user_ids])
            # push.notification = jpush.notification(alert=content)
            # result = push.send()

            logger.info(
                "[JPush] 批量推送 -> 用户数: %d, 标题: %s",
                len(user_ids), title,
            )
            return {
                "success": True,
                "success_count": len(user_ids),
                "fail_count": 0,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error("[JPush] 批量推送发送失败: %s", str(e))
            return {
                "success": False,
                "success_count": 0,
                "fail_count": len(user_ids),
                "message_id": None,
                "error": str(e),
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
            - app_key: 极光推送 AppKey
            - master_secret: 极光推送 Master Secret

    Returns:
        推送服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in PUSH_SERVICES:
        available = ", ".join(PUSH_SERVICES.keys())
        raise ValueError(f"未知的推送服务 Provider: {provider}，可用选项: [{available}]")
    return PUSH_SERVICES[provider](**kwargs)
