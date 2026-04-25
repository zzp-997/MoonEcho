"""内容审核服务模块。

提供内容安全审核能力，支持直接通过、本地关键词过滤、阿里云内容安全三种 Provider。
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol 定义 — 内容审核服务接口契约
# ---------------------------------------------------------------------------

class ContentAuditProtocol(Protocol):
    """内容审核服务接口。"""

    async def check(self, content: str) -> dict[str, Any]:
        """审核内容，返回审核结果。

        Args:
            content: 待审核的文本内容

        Returns:
            {"pass": bool, "risk_level": str, "labels": [...], "reason": str|None}
        """
        ...


# ---------------------------------------------------------------------------
# Pass 实现 — 直接通过，不做审核
# ---------------------------------------------------------------------------

class PassAudit:
    """直接通过的内容审核服务。

    适用于开发环境或无需审核的场景，所有内容默认通过。
    """

    async def check(self, content: str) -> dict[str, Any]:
        logger.debug("[PassAudit] 跳过审核，直接通过: %s", content[:50] if len(content) > 50 else content)
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": None,
        }


# ---------------------------------------------------------------------------
# Local 实现 — 本地关键词过滤
# ---------------------------------------------------------------------------

class LocalContentAudit:
    """本地关键词内容审核服务。

    基于敏感词列表进行本地匹配，适用于测试环境或低风险场景。
    """

    # 敏感词列表 - 实际生产环境应从数据库或配置文件加载
    SENSITIVE_KEYWORDS: list[str] = [
        # 违禁词
        "违规", "违禁", "敏感词", "广告",
        # 政治敏感词（示例）
        "政治敏感", "反动",
        # 色情暴力
        "色情", "暴力", "血腥",
        # 赌博诈骗
        "赌博", "诈骗", "传销",
        # 毒品
        "毒品", "吸毒",
        # 其他违规内容
        "代开发票", "刷单", "兼职赚钱",
    ]

    # 正则表达式模式 - 用于检测更复杂的违规模式
    PATTERNS: list[tuple[str, str]] = [
        (r"\d{11}", "手机号"),  # 手机号
        (r"银行卡", "银行卡信息"),
        (r"微信号|添加微信|加微信", "微信引流"),
        (r"QQ.*群", "QQ群引流"),
    ]

    async def check(self, content: str) -> dict[str, Any]:
        matched_keywords: list[str] = []

        # 关键词匹配
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in content:
                matched_keywords.append(keyword)

        # 正则模式匹配
        for pattern, label in self.PATTERNS:
            if re.search(pattern, content):
                matched_keywords.append(label)

        if matched_keywords:
            logger.warning(
                "[LocalAudit] 内容审核不通过，匹配到敏感词: %s",
                ", ".join(matched_keywords),
            )
            return {
                "pass": False,
                "risk_level": "high",
                "labels": matched_keywords,
                "reason": f"内容包含敏感词: {', '.join(matched_keywords)}",
            }

        logger.debug("[LocalAudit] 内容审核通过")
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": None,
        }


# ---------------------------------------------------------------------------
# 阿里云内容安全 — 真实调用占位
# ---------------------------------------------------------------------------

class AliyunContentAudit:
    """阿里云内容安全审核服务（真实调用占位）。

    TODO: 接入阿里云内容安全 SDK
    - 需要配置 AccessKey、SecretKey
    - 支持文本、图片、视频等多种内容类型
    - 返回详细的审核结果和风险等级
    """

    async def check(self, content: str) -> dict[str, Any]:
        # TODO: 接入阿里云内容安全 SDK
        # from alibabacloud_green20220302.client import Client
        # from alibabacloud_green20220302 import models as green_models
        logger.warning("[AliyunAudit] 阿里云内容安全 SDK 尚未接入，返回占位响应")
        return {
            "pass": True,
            "risk_level": "none",
            "labels": [],
            "reason": "aliyun audit placeholder",
        }


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

CONTENT_AUDIT_SERVICES: dict[str, type[PassAudit | LocalContentAudit | AliyunContentAudit]] = {
    "pass": PassAudit,
    "local": LocalContentAudit,
    "aliyun": AliyunContentAudit,
}


def create_content_audit_service(
    provider: str = "pass",
) -> PassAudit | LocalContentAudit | AliyunContentAudit:
    """根据配置创建内容审核服务实例。

    Args:
        provider: 服务提供者名称，可选 pass / local / aliyun

    Returns:
        内容审核服务实例

    Raises:
        ValueError: 当 provider 名称不在可用列表中时
    """
    if provider not in CONTENT_AUDIT_SERVICES:
        available = ", ".join(CONTENT_AUDIT_SERVICES.keys())
        raise ValueError(f"未知的内容审核服务 Provider: {provider}，可用选项: [{available}]")
    return CONTENT_AUDIT_SERVICES[provider]()
