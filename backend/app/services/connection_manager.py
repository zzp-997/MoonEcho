"""WebSocket 连接管理器模块。

提供 WebSocket 连接管理能力：
- 用户连接管理（支持多设备）
- 心跳机制（30秒 ping/pong，90秒超时检测）
- 消息广播与定向推送
- 僵尸连接清理

设计要点：
1. 同一用户可建立多个连接（多设备支持）
2. 使用 Redis 存储连接状态（支持分布式部署）
3. 心跳超时自动断开僵尸连接
4. 线程安全的连接管理
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from fastapi import WebSocket, WebSocketDisconnect

from app.enums.error_codes import ErrorCode
from app.schemas.chat import (
    MessageResponse,
    MessageType,
    WsErrorMessage,
    WsEventType,
    WsPongMessage,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 30

# 心跳超时阈值（秒）- 超过此时间未收到心跳则断开连接
HEARTBEAT_TIMEOUT = 90

# 僵尸连接检测间隔（秒）
ZOMBIE_CHECK_INTERVAL = 30

# WebSocket 消息最大大小（字节）- 64KB
MAX_MESSAGE_SIZE = 64 * 1024

# Redis 键前缀
REDIS_KEY_PREFIX = "ws:connection:"


# ---------------------------------------------------------------------------
# Protocol 定义
# ---------------------------------------------------------------------------

class AuthServiceProtocol(Protocol):
    """认证服务接口协议。"""

    async def verify_access_token(self, token: str) -> dict[str, Any]:
        """验证 access_token 有效性。"""
        ...


class ChatServiceProtocol(Protocol):
    """聊天服务接口协议。"""

    async def get_offline_messages(
        self,
        user_id: str,
        after_message_id: str | None,
        limit: int,
    ) -> list[MessageResponse]:
        """获取离线消息。"""
        ...


# ---------------------------------------------------------------------------
# 连接信息数据类
# ---------------------------------------------------------------------------

@dataclass
class ConnectionInfo:
    """WebSocket 连接信息。

    Attributes:
        websocket: WebSocket 连接对象
        user_id: 用户ID
        device_id: 设备ID（用于区分多设备）
        connected_at: 连接时间
        last_heartbeat: 最后心跳时间
    """

    websocket: WebSocket
    user_id: str
    device_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: float = field(default_factory=time.time)

    def is_alive(self, timeout: float = HEARTBEAT_TIMEOUT) -> bool:
        """检查连接是否存活。

        Args:
            timeout: 超时时间（秒）

        Returns:
            连接是否存活
        """
        return time.time() - self.last_heartbeat < timeout

    def update_heartbeat(self) -> None:
        """更新心跳时间。"""
        self.last_heartbeat = time.time()


# ---------------------------------------------------------------------------
# ConnectionManager 核心类
# ---------------------------------------------------------------------------

class ConnectionManager:
    """WebSocket 连接管理器。

    功能：
    1. 管理用户 WebSocket 连接（支持多设备）
    2. 心跳机制（ping/pong）
    3. 消息广播与定向推送
    4. 僵尸连接清理

    使用示例：
        manager = ConnectionManager(redis_client, auth_service)
        await manager.connect(websocket, user_id, device_id)
        await manager.send_personal_message(user_id, message)
        await manager.broadcast_to_conversation(conversation_id, message)
    """

    def __init__(
        self,
        redis: Any,
        auth_service: AuthServiceProtocol,
        chat_service: ChatServiceProtocol | None = None,
    ) -> None:
        """初始化连接管理器。

        Args:
            redis: Redis 客户端（aioredis）
            auth_service: 认证服务
            chat_service: 聊天服务（可选）
        """
        # 用户连接映射：user_id -> list[ConnectionInfo]
        self._connections: dict[str, list[ConnectionInfo]] = {}
        # WebSocket -> ConnectionInfo 反向映射
        self._websocket_to_info: dict[WebSocket, ConnectionInfo] = {}
        # Redis 客户端
        self._redis = redis
        # 认证服务
        self._auth_service = auth_service
        # 聊天服务
        self._chat_service = chat_service
        # 僵尸检测任务
        self._zombie_task: asyncio.Task | None = None
        # 运行状态
        self._running = False

        logger.info("[ConnectionManager] 初始化完成")

    # =========================================================================
    # 生命周期管理
    # =========================================================================

    async def start(self) -> None:
        """启动连接管理器。

        启动僵尸连接检测任务。
        """
        if self._running:
            return

        self._running = True
        self._zombie_task = asyncio.create_task(self._zombie_checker())
        logger.info("[ConnectionManager] 已启动")

    async def stop(self) -> None:
        """停止连接管理器。

        停止僵尸连接检测任务，关闭所有连接。
        """
        self._running = False

        if self._zombie_task:
            self._zombie_task.cancel()
            try:
                await self._zombie_task
            except asyncio.CancelledError:
                pass
            self._zombie_task = None

        # 关闭所有连接
        for user_id, connections in list(self._connections.items()):
            for conn in connections[:]:
                try:
                    await conn.websocket.close(code=1001, reason="服务关闭")
                except Exception:
                    pass

        self._connections.clear()
        self._websocket_to_info.clear()
        logger.info("[ConnectionManager] 已停止")

    # =========================================================================
    # 连接管理
    # =========================================================================

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        device_id: str = "default",
    ) -> ConnectionInfo:
        """接受 WebSocket 连接。

        Args:
            websocket: WebSocket 连接对象
            user_id: 用户ID
            device_id: 设备ID

        Returns:
            连接信息对象
        """
        # 接受连接
        await websocket.accept()

        # 创建连接信息
        conn_info = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            device_id=device_id,
        )

        # 添加到连接映射
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(conn_info)
        self._websocket_to_info[websocket] = conn_info

        # 更新 Redis 在线状态
        await self._update_online_status(user_id, device_id, online=True)

        logger.info(
            "[ConnectionManager] 用户连接: user_id=%s, device_id=%s, 当前连接数=%d",
            user_id, device_id, len(self._connections[user_id])
        )

        return conn_info

    async def disconnect(self, websocket: WebSocket) -> None:
        """断开 WebSocket 连接。

        Args:
            websocket: WebSocket 连接对象
        """
        conn_info = self._websocket_to_info.pop(websocket, None)
        if not conn_info:
            return

        user_id = conn_info.user_id
        device_id = conn_info.device_id

        # 从用户连接列表中移除
        if user_id in self._connections:
            connections = self._connections[user_id]
            connections = [c for c in connections if c.websocket != websocket]
            if connections:
                self._connections[user_id] = connections
            else:
                del self._connections[user_id]

        # 更新 Redis 在线状态
        await self._update_online_status(user_id, device_id, online=False)

        logger.info(
            "[ConnectionManager] 用户断开: user_id=%s, device_id=%s, 剩余连接数=%d",
            user_id, device_id, len(self._connections.get(user_id, []))
        )

    def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线。

        Args:
            user_id: 用户ID

        Returns:
            用户是否在线
        """
        return user_id in self._connections and len(self._connections[user_id]) > 0

    def get_user_connections(self, user_id: str) -> list[ConnectionInfo]:
        """获取用户的所有连接。

        Args:
            user_id: 用户ID

        Returns:
            用户连接列表
        """
        return self._connections.get(user_id, [])

    # =========================================================================
    # 消息发送
    # =========================================================================

    async def send_personal_message(
        self,
        user_id: str,
        message: dict[str, Any],
    ) -> bool:
        """向用户发送消息（推送到所有设备）。

        Args:
            user_id: 用户ID
            message: 消息内容

        Returns:
            是否发送成功（至少一个设备）
        """
        connections = self.get_user_connections(user_id)
        if not connections:
            logger.debug("[ConnectionManager] 用户不在线: user_id=%s", user_id)
            return False

        message_json = json.dumps(message, ensure_ascii=False, default=str)
        success = False

        # 收集发送失败的连接，循环结束后统一处理（避免竞态条件）
        failed_connections: list[WebSocket] = []

        for conn in connections[:]:
            try:
                await conn.websocket.send_text(message_json)
                success = True
            except Exception as e:
                logger.warning(
                    "[ConnectionManager] 发送消息失败: user_id=%s, error=%s",
                    user_id, str(e)
                )
                failed_connections.append(conn.websocket)

        # 统一断开失败的连接
        for ws in failed_connections:
            await self.disconnect(ws)

        return success

    async def broadcast_to_conversation(
        self,
        conversation_id: str,
        user_ids: list[str],
        message: dict[str, Any],
        exclude_user_id: str | None = None,
    ) -> dict[str, bool]:
        """向会话中的所有用户广播消息。

        Args:
            conversation_id: 会话ID
            user_ids: 用户ID列表
            message: 消息内容
            exclude_user_id: 排除的用户ID（通常是发送者）

        Returns:
            各用户的发送结果
        """
        results: dict[str, bool] = {}

        for user_id in user_ids:
            if user_id == exclude_user_id:
                results[user_id] = True
                continue

            results[user_id] = await self.send_personal_message(user_id, message)

        return results

    async def send_pong(self, websocket: WebSocket) -> None:
        """发送心跳响应。

        Args:
            websocket: WebSocket 连接对象
        """
        pong = WsPongMessage()
        try:
            await websocket.send_json(pong.model_dump(mode="json"))
        except Exception as e:
            logger.warning("[ConnectionManager] 发送 PONG 失败: %s", str(e))

    async def send_error(
        self,
        websocket: WebSocket,
        code: str,
        message: str,
    ) -> None:
        """发送错误消息。

        Args:
            websocket: WebSocket 连接对象
            code: 错误码
            message: 错误信息
        """
        error = WsErrorMessage(code=code, message=message)
        try:
            await websocket.send_json(error.model_dump(mode="json"))
        except Exception as e:
            logger.warning("[ConnectionManager] 发送错误消息失败: %s", str(e))

    # =========================================================================
    # 心跳处理
    # =========================================================================

    async def handle_heartbeat(self, websocket: WebSocket) -> None:
        """处理心跳消息。

        更新连接的最后心跳时间，发送 pong 响应。

        Args:
            websocket: WebSocket 连接对象
        """
        conn_info = self._websocket_to_info.get(websocket)
        if conn_info:
            conn_info.update_heartbeat()
            await self.send_pong(websocket)
            logger.debug(
                "[ConnectionManager] 心跳更新: user_id=%s, device_id=%s",
                conn_info.user_id, conn_info.device_id
            )

    # =========================================================================
    # 消息循环
    # =========================================================================

    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        device_id: str = "default",
    ) -> None:
        """处理 WebSocket 连接的消息循环。

        Args:
            websocket: WebSocket 连接对象
            user_id: 用户ID
            device_id: 设备ID
        """
        conn_info = await self.connect(websocket, user_id, device_id)

        try:
            # 连接成功后，发送离线消息
            if self._chat_service:
                await self._send_offline_messages(websocket, user_id)

            while True:
                try:
                    # 接收消息
                    data = await websocket.receive_text()

                    # 检查消息大小
                    if len(data) > MAX_MESSAGE_SIZE:
                        await self.send_error(
                            websocket,
                            ErrorCode.CONTENT_TOO_LONG.value,
                            f"消息大小超过限制（最大 {MAX_MESSAGE_SIZE // 1024}KB）"
                        )
                        continue

                    # 解析消息
                    try:
                        message = json.loads(data)
                    except json.JSONDecodeError:
                        await self.send_error(
                            websocket,
                            ErrorCode.INVALID_PARAMETER.value,
                            "无效的消息格式"
                        )
                        continue

                    # 处理消息
                    await self._handle_message(websocket, conn_info, message)

                except WebSocketDisconnect:
                    logger.info(
                        "[ConnectionManager] 客户端主动断开: user_id=%s",
                        user_id
                    )
                    break
                except Exception as e:
                    logger.error(
                        "[ConnectionManager] 消息处理异常: user_id=%s, error=%s",
                        user_id, str(e)
                    )
                    await self.send_error(
                        websocket,
                        ErrorCode.INTERNAL_ERROR.value,
                        "服务器内部错误"
                    )

        finally:
            await self.disconnect(websocket)

    async def _handle_message(
        self,
        websocket: WebSocket,
        conn_info: ConnectionInfo,
        message: dict[str, Any],
    ) -> None:
        """处理单条消息。

        Args:
            websocket: WebSocket 连接对象
            conn_info: 连接信息
            message: 消息内容
        """
        msg_type = message.get("type")

        if not msg_type:
            await self.send_error(
                websocket,
                ErrorCode.INVALID_PARAMETER.value,
                "缺少消息类型"
            )
            return

        try:
            event_type = WsEventType(msg_type)
        except ValueError:
            await self.send_error(
                websocket,
                ErrorCode.INVALID_PARAMETER.value,
                f"未知的消息类型: {msg_type}"
            )
            return

        # 处理心跳
        if event_type == WsEventType.PING:
            await self.handle_heartbeat(websocket)
            return

        # 其他消息类型需要通过回调处理（在路由层实现）
        # 这里只是分发，具体业务逻辑在 ChatRouter 中实现
        if hasattr(self, '_message_handler') and self._message_handler:
            await self._message_handler(websocket, conn_info, event_type, message)
        else:
            logger.warning(
                "[ConnectionManager] 未处理的消息类型: type=%s, user_id=%s",
                event_type, conn_info.user_id
            )

    def set_message_handler(self, handler: Any) -> None:
        """设置消息处理器。

        Args:
            handler: 异步消息处理函数
        """
        self._message_handler = handler

    async def _send_offline_messages(
        self,
        websocket: WebSocket,
        user_id: str,
    ) -> None:
        """发送离线消息。

        Args:
            websocket: WebSocket 连接对象
            user_id: 用户ID
        """
        if not self._chat_service:
            return

        try:
            messages = await self._chat_service.get_offline_messages(
                user_id=user_id,
                after_message_id=None,
                limit=100,
            )

            for msg in messages:
                await websocket.send_json({
                    "type": WsEventType.NEW_MESSAGE.value,
                    "data": msg.model_dump(mode="json"),
                })

            if messages:
                logger.info(
                    "[ConnectionManager] 发送离线消息: user_id=%s, count=%d",
                    user_id, len(messages)
                )

        except Exception as e:
            logger.error(
                "[ConnectionManager] 发送离线消息失败: user_id=%s, error=%s",
                user_id, str(e)
            )

    # =========================================================================
    # 僵尸连接检测
    # =========================================================================

    async def _zombie_checker(self) -> None:
        """僵尸连接检测任务。

        定期检查所有连接，清理超时的僵尸连接。
        """
        logger.info("[ConnectionManager] 僵尸检测任务启动")

        while self._running:
            try:
                await asyncio.sleep(ZOMBIE_CHECK_INTERVAL)

                now = time.time()
                zombies: list[WebSocket] = []

                # 收集所有僵尸连接
                for user_id, connections in self._connections.items():
                    for conn in connections:
                        if not conn.is_alive(HEARTBEAT_TIMEOUT):
                            zombies.append(conn.websocket)

                # 清理僵尸连接
                for ws in zombies:
                    logger.warning(
                        "[ConnectionManager] 检测到僵尸连接，正在关闭"
                    )
                    try:
                        await ws.close(code=1001, reason="心跳超时")
                    except Exception:
                        pass
                    await self.disconnect(ws)

                if zombies:
                    logger.info(
                        "[ConnectionManager] 僵尸连接清理完成: count=%d",
                        len(zombies)
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "[ConnectionManager] 僵尸检测任务异常: %s",
                    str(e)
                )

    # =========================================================================
    # Redis 状态管理
    # =========================================================================

    async def _update_online_status(
        self,
        user_id: str,
        device_id: str,
        online: bool,
    ) -> None:
        """更新用户在线状态到 Redis。

        Args:
            user_id: 用户ID
            device_id: 设备ID
            online: 是否在线
        """
        try:
            key = f"{REDIS_KEY_PREFIX}{user_id}:{device_id}"
            if online:
                # 设置在线状态，30秒过期（心跳间隔）
                await self._redis.setex(key, HEARTBEAT_TIMEOUT, "1")
            else:
                # 删除在线状态
                await self._redis.delete(key)
        except Exception as e:
            logger.warning(
                "[ConnectionManager] 更新在线状态失败: %s",
                str(e)
            )

    async def is_user_online_in_redis(self, user_id: str) -> bool:
        """检查用户是否在线（基于 Redis）。

        用于分布式场景，检查其他节点的用户在线状态。

        Args:
            user_id: 用户ID

        Returns:
            用户是否在线
        """
        try:
            # 扫描所有设备的在线状态
            pattern = f"{REDIS_KEY_PREFIX}{user_id}:*"
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    return True
                if cursor == 0:
                    break
            return False
        except Exception as e:
            logger.warning(
                "[ConnectionManager] 检查在线状态失败: %s",
                str(e)
            )
            return False


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_connection_manager(
    redis: Any,
    auth_service: AuthServiceProtocol,
    chat_service: ChatServiceProtocol | None = None,
) -> ConnectionManager:
    """创建 WebSocket 连接管理器实例。

    Args:
        redis: Redis 客户端
        auth_service: 认证服务
        chat_service: 聊天服务（可选）

    Returns:
        ConnectionManager 实例
    """
    return ConnectionManager(
        redis=redis,
        auth_service=auth_service,
        chat_service=chat_service,
    )
