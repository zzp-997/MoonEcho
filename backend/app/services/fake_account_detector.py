"""虚假信息预警服务。

实现 modules_design.md 7.6 规定的虚假信息预警机制：

1. 注册环节检测
   - 异常手机号模式检测（虚拟号段、高频注册）
   - 设备指纹关联检测

2. 行为检测
   - 批量注册特征检测
   - 异常行为模式检测

3. SimHash相似内容检测
   - 重复发布相似内容检测
   - 跨用户相似内容检测

设计要点：
- 使用 Redis 进行频率统计和行为分析
- SimHash 算法检测文本相似度
- 支持可配置的阈值参数
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 风险级别枚举
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    """虚假信息风险级别。"""

    LOW = "low"          # 低风险，正常
    MEDIUM = "medium"    # 中风险，需要关注
    HIGH = "high"        # 高风险，需要处理
    CRITICAL = "critical"  # 极高风险，立即处理


class FakeType(str, Enum):
    """虚假信息类型。"""

    # 注册相关
    SUSPICIOUS_PHONE = "suspicious_phone"        # 可疑手机号
    DEVICE_REUSE = "device_reuse"                # 设备重复使用
    IP_CLUSTER = "ip_cluster"                    # IP聚集

    # 行为相关
    BATCH_REGISTER = "batch_register"            # 批量注册
    ABNORMAL_BEHAVIOR = "abnormal_behavior"      # 异常行为

    # 内容相关
    DUPLICATE_CONTENT = "duplicate_content"      # 重复内容
    SPAM_CONTENT = "spam_content"                # 垃圾内容


# ---------------------------------------------------------------------------
# 检测结果数据类
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FakeDetectionResult:
    """虚假信息检测结果。"""

    risk_level: RiskLevel = RiskLevel.LOW
    fake_types: list[FakeType] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)

    @property
    def is_risky(self) -> bool:
        """是否存在风险。"""
        return self.risk_level != RiskLevel.LOW

    @property
    def needs_action(self) -> bool:
        """是否需要立即处理。"""
        return self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)


# ---------------------------------------------------------------------------
# 可疑手机号配置
# ---------------------------------------------------------------------------

# 虚拟运营商号段（部分）
VIRTUAL_OPERATOR_PREFIXES: list[str] = [
    # 阿里通信
    "1705", "1709", "1710", "1711", "1712", "1713", "1714", "1715", "1716", "1717", "1718", "1719",
    # 京东通信
    "1706", "1716",
    # 分享通信
    "1708", "1709",
    # 迪信通
    "1707",
    # 乐语通讯
    "1703",
    # 国美
    "1704", "1707",
    # 中信
    "1701", "1702",
]

# 疑似营销/批量注册号段（根据实际情况调整）
SUSPICIOUS_PREFIXES: list[str] = [
    # 可根据实际业务添加
]


# ---------------------------------------------------------------------------
# SimHash 实现
# ---------------------------------------------------------------------------

class SimHash:
    """SimHash 相似度检测算法。

    用于检测文本内容的相似度，识别重复发布的内容。

    使用示例：
        hash1 = SimHash.calculate("文本内容1")
        hash2 = SimHash.calculate("文本内容2")
        distance = SimHash.hamming_distance(hash1, hash2)
        if distance < 3:
            # 内容相似
            pass
    """

    # 分词大小
    TOKEN_SIZE = 2

    @classmethod
    def calculate(cls, text: str, hash_bits: int = 64) -> int:
        """计算文本的 SimHash 值。

        Args:
            text: 待计算的文本
            hash_bits: Hash 位数，默认 64 位

        Returns:
            SimHash 值（整数）
        """
        if not text or not text.strip():
            return 0

        # 分词
        tokens = cls._tokenize(text)

        # 初始化向量
        v = [0] * hash_bits

        # 计算每个 token 的 hash 并累加
        for token in tokens:
            token_hash = hash(token)
            for i in range(hash_bits):
                bit = (token_hash >> i) & 1
                if bit:
                    v[i] += 1
                else:
                    v[i] -= 1

        # 生成最终 hash
        result = 0
        for i in range(hash_bits):
            if v[i] > 0:
                result |= (1 << i)

        return result

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """分词。

        Args:
            text: 待分词的文本

        Returns:
            token 列表
        """
        # 简单的 n-gram 分词
        tokens = []
        text = text.strip()

        # 移除标点符号和空白
        text = re.sub(r"[^\w一-鿿]", "", text)

        # 生成 n-gram
        for i in range(len(text) - cls.TOKEN_SIZE + 1):
            tokens.append(text[i:i + cls.TOKEN_SIZE])

        return tokens

    @classmethod
    def hamming_distance(cls, hash1: int, hash2: int) -> int:
        """计算两个 SimHash 值的海明距离。

        Args:
            hash1: 第一个 SimHash 值
            hash2: 第二个 SimHash 值

        Returns:
            海明距离
        """
        xor = hash1 ^ hash2
        distance = 0
        while xor:
            distance += 1
            xor &= xor - 1  # 移除最低位的 1
        return distance

    @classmethod
    def similarity(cls, hash1: int, hash2: int) -> float:
        """计算两个 SimHash 值的相似度。

        Args:
            hash1: 第一个 SimHash 值
            hash2: 第二一个 SimHash 值

        Returns:
            相似度（0.0 - 1.0）
        """
        distance = cls.hamming_distance(hash1, hash2)
        return 1.0 - (distance / 64.0)


# ---------------------------------------------------------------------------
# 虚假信息检测器
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FakeAccountThresholds:
    """虚假信息检测阈值配置。"""

    # 手机号检测
    virtual_prefix_check: bool = True          # 是否检测虚拟运营商号段
    same_ip_register_limit: int = 5            # 同一 IP 注册限制
    same_device_register_limit: int = 3        # 同一设备注册限制
    ip_register_window_hours: int = 24         # IP 注册时间窗口（小时）

    # 行为检测
    batch_register_time_window: int = 60       # 批量注册时间窗口（分钟）
    batch_register_count_threshold: int = 10   # 批量注册数量阈值

    # 内容检测
    simhash_distance_threshold: int = 3        # SimHash 海明距离阈值
    duplicate_content_window_hours: int = 24   # 重复内容检测时间窗口（小时）
    duplicate_content_count_threshold: int = 5 # 重复内容数量阈值


class FakeAccountDetector:
    """虚假信息检测器。

    提供注册、行为、内容三个维度的虚假信息检测。

    使用示例：
        detector = FakeAccountDetector(redis)

        # 检测注册
        result = await detector.check_registration(
            phone="13800138000",
            ip="192.168.1.1",
            device_fingerprint="abc123",
        )

        # 检测内容相似度
        simhash = detector.calculate_simhash("内容")
        is_duplicate = await detector.check_duplicate_content(user_id, simhash)
    """

    def __init__(
        self,
        redis: Any,
        thresholds: FakeAccountThresholds | None = None,
    ) -> None:
        """初始化检测器。

        Args:
            redis: Redis 客户端
            thresholds: 阈值配置
        """
        self._redis = redis
        self._thresholds = thresholds or FakeAccountThresholds()

        logger.info(
            "[FakeAccountDetector] 初始化完成，阈值: "
            "IP限制=%d, 设备限制=%d, SimHash阈值=%d",
            self._thresholds.same_ip_register_limit,
            self._thresholds.same_device_register_limit,
            self._thresholds.simhash_distance_threshold,
        )

    # =========================================================================
    # Redis 操作封装
    # =========================================================================

    async def _incr_and_get(
        self,
        key: str,
        ttl_seconds: int,
    ) -> int:
        """原子递增并获取计数值。"""
        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, ttl_seconds)
            return count
        except Exception as e:
            logger.error("[FakeAccountDetector] Redis incr 异常: %s", str(e))
            return 0

    async def _get_count(self, key: str) -> int:
        """获取当前计数值。"""
        try:
            value = await self._redis.get(key)
            if value is not None:
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                return int(value)
            return 0
        except Exception as e:
            logger.error("[FakeAccountDetector] Redis get 异常: %s", str(e))
            return 0

    async def _add_to_set(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> int:
        """添加元素到集合并返回集合大小。"""
        try:
            await self._redis.sadd(key, value)
            await self._redis.expire(key, ttl_seconds)
            return await self._redis.scard(key)
        except Exception as e:
            logger.error("[FakeAccountDetector] Redis sadd 异常: %s", str(e))
            return 0

    async def _set_with_ttl(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        """设置值并指定过期时间。"""
        try:
            await self._redis.set(key, value, ex=ttl_seconds)
        except Exception as e:
            logger.error("[FakeAccountDetector] Redis set 异常: %s", str(e))

    # =========================================================================
    # 注册环节检测
    # =========================================================================

    def _check_virtual_operator(self, phone: str) -> bool:
        """检查是否为虚拟运营商号段。

        Args:
            phone: 手机号

        Returns:
            是否为虚拟运营商号段
        """
        if not self._thresholds.virtual_prefix_check:
            return False

        for prefix in VIRTUAL_OPERATOR_PREFIXES:
            if phone.startswith(prefix):
                return True
        return False

    async def check_registration(
        self,
        phone: str,
        ip: str | None = None,
        device_fingerprint: str | None = None,
    ) -> FakeDetectionResult:
        """检测注册请求的风险。

        Args:
            phone: 手机号
            ip: 注册IP
            device_fingerprint: 设备指纹

        Returns:
            检测结果
        """
        result = FakeDetectionResult()
        details: dict[str, Any] = {}

        # 1. 检测虚拟运营商号段
        if self._check_virtual_operator(phone):
            result.fake_types.append(FakeType.SUSPICIOUS_PHONE)
            result.risk_level = RiskLevel.MEDIUM
            details["virtual_operator"] = True
            result.suggestions.append("虚拟运营商号段，建议人工审核")

        # 2. 检测同一IP注册次数
        if ip:
            ip_key = f"fake:ip_register:{ip}"
            window = self._thresholds.ip_register_window_hours * 3600
            ip_count = await self._incr_and_get(ip_key, window)

            details["ip_register_count"] = ip_count

            if ip_count > self._thresholds.same_ip_register_limit:
                result.fake_types.append(FakeType.IP_CLUSTER)
                result.risk_level = max(result.risk_level.value, RiskLevel.HIGH.value)
                result.risk_level = RiskLevel(result.risk_level)
                result.suggestions.append(f"同一IP注册次数过多({ip_count}次)")

        # 3. 检测同一设备注册次数
        if device_fingerprint:
            device_key = f"fake:device_register:{device_fingerprint}"
            window = self._thresholds.ip_register_window_hours * 3600
            device_count = await self._incr_and_get(device_key, window)

            details["device_register_count"] = device_count

            if device_count > self._thresholds.same_device_register_limit:
                result.fake_types.append(FakeType.DEVICE_REUSE)
                result.risk_level = max(result.risk_level.value, RiskLevel.HIGH.value)
                result.risk_level = RiskLevel(result.risk_level)
                result.suggestions.append(f"同一设备注册次数过多({device_count}次)")

        result.details = details

        if result.is_risky:
            logger.warning(
                "[FakeAccountDetector] 检测到风险注册，手机: %s, IP: %s, "
                "风险级别: %s, 类型: %s",
                phone[:3] + "****" + phone[-4:], ip, result.risk_level.value,
                [t.value for t in result.fake_types],
            )

        return result

    # =========================================================================
    # 行为检测
    # =========================================================================

    async def check_batch_register(
        self,
        ip: str,
    ) -> FakeDetectionResult:
        """检测批量注册行为。

        Args:
            ip: 注册IP

        Returns:
            检测结果
        """
        result = FakeDetectionResult()

        window = self._thresholds.batch_register_time_window * 60
        key = f"fake:batch_register:{ip}"
        count = await self._incr_and_get(key, window)

        if count >= self._thresholds.batch_register_count_threshold:
            result.fake_types.append(FakeType.BATCH_REGISTER)
            result.risk_level = RiskLevel.CRITICAL
            result.details = {"register_count": count}
            result.suggestions.append(f"疑似批量注册({count}次)，建议封禁IP")

            logger.warning(
                "[FakeAccountDetector] 检测到批量注册，IP: %s, 次数: %d",
                ip, count
            )

        return result

    # =========================================================================
    # 内容相似度检测
    # =========================================================================

    def calculate_simhash(self, content: str) -> int:
        """计算内容的 SimHash 值。

        Args:
            content: 文本内容

        Returns:
            SimHash 值
        """
        return SimHash.calculate(content)

    async def check_duplicate_content(
        self,
        user_id: str,
        content: str,
        content_type: str = "post",
    ) -> FakeDetectionResult:
        """检测重复内容。

        Args:
            user_id: 用户ID
            content: 文本内容
            content_type: 内容类型（post/comment/treehole）

        Returns:
            检测结果
        """
        result = FakeDetectionResult()

        # 计算内容的 SimHash
        simhash = self.calculate_simhash(content)

        # 存储用户的历史 SimHash
        history_key = f"fake:simhash_history:{user_id}:{content_type}"
        window = self._thresholds.duplicate_content_window_hours * 3600

        # 获取历史 SimHash 列表
        try:
            history = await self._redis.lrange(history_key, 0, -1)
            if history:
                for h in history:
                    if isinstance(h, bytes):
                        h = h.decode("utf-8")
                    try:
                        old_simhash = int(h)
                        distance = SimHash.hamming_distance(simhash, old_simhash)

                        if distance < self._thresholds.simhash_distance_threshold:
                            result.fake_types.append(FakeType.DUPLICATE_CONTENT)
                            result.risk_level = RiskLevel.MEDIUM
                            result.details = {
                                "simhash_distance": distance,
                                "content_type": content_type,
                            }
                            result.suggestions.append("检测到相似内容，请勿重复发布")

                            logger.info(
                                "[FakeAccountDetector] 检测到相似内容，用户: %s, "
                                "距离: %d, 类型: %s",
                                user_id, distance, content_type
                            )
                            break
                    except ValueError:
                        continue
        except Exception as e:
            logger.error("[FakeAccountDetector] 获取 SimHash 历史异常: %s", str(e))

        # 将当前 SimHash 加入历史
        try:
            await self._redis.lpush(history_key, str(simhash))
            await self._redis.ltrim(history_key, 0, 49)  # 保留最近50条
            await self._redis.expire(history_key, window)
        except Exception as e:
            logger.error("[FakeAccountDetector] 存储 SimHash 异常: %s", str(e))

        return result

    async def record_simhash(
        self,
        user_id: str,
        content: str,
        content_type: str = "post",
    ) -> int:
        """记录内容的 SimHash。

        Args:
            user_id: 用户ID
            content: 文本内容
            content_type: 内容类型

        Returns:
            SimHash 值
        """
        simhash = self.calculate_simhash(content)

        history_key = f"fake:simhash_history:{user_id}:{content_type}"
        window = self._thresholds.duplicate_content_window_hours * 3600

        try:
            await self._redis.lpush(history_key, str(simhash))
            await self._redis.ltrim(history_key, 0, 49)
            await self._redis.expire(history_key, window)
        except Exception as e:
            logger.error("[FakeAccountDetector] 记录 SimHash 异常: %s", str(e))

        return simhash

    async def check_cross_user_duplicate(
        self,
        content: str,
        content_type: str = "post",
    ) -> FakeDetectionResult:
        """检测跨用户的重复内容（垃圾内容检测）。

        Args:
            content: 文本内容
            content_type: 内容类型

        Returns:
            检测结果
        """
        result = FakeDetectionResult()

        simhash = self.calculate_simhash(content)

        # 全局 SimHash 索引
        global_key = f"fake:global_simhash:{content_type}"
        window = self._thresholds.duplicate_content_window_hours * 3600

        # 检查是否有相同或相似的 SimHash
        try:
            # 使用 Redis 的 SCAN 命令遍历（对于大量数据，可以考虑使用专门的索引）
            # 这里简化处理：检查是否存在完全相同的 SimHash
            exists = await self._redis.sismember(global_key, str(simhash))

            if exists:
                result.fake_types.append(FakeType.SPAM_CONTENT)
                result.risk_level = RiskLevel.HIGH
                result.details = {"content_type": content_type}
                result.suggestions.append("检测到跨用户重复内容，可能为垃圾内容")

                logger.info(
                    "[FakeAccountDetector] 检测到跨用户重复内容，类型: %s",
                    content_type
                )
            else:
                # 将 SimHash 加入全局索引
                await self._redis.sadd(global_key, str(simhash))
                await self._redis.expire(global_key, window)

        except Exception as e:
            logger.error("[FakeAccountDetector] 跨用户检测异常: %s", str(e))

        return result


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_fake_account_detector(
    redis: Any,
    thresholds: FakeAccountThresholds | None = None,
) -> FakeAccountDetector:
    """创建虚假信息检测器实例。

    Args:
        redis: Redis 客户端
        thresholds: 阈值配置（可选）

    Returns:
        FakeAccountDetector 实例
    """
    return FakeAccountDetector(redis=redis, thresholds=thresholds)
