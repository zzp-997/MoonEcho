"""树洞相关请求/响应模型。

包含树洞帖子创建、列表、详情等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 话题标签枚举
# ---------------------------------------------------------------------------

class TopicTag(str, Enum):
    """树洞话题标签枚举。

    预设话题标签，用于内容分类和筛选。
    """

    WORK = "work"           # 工作吐槽
    FAMILY = "family"       # 家庭关系
    RELATIONSHIP = "relationship"  # 情感恋爱
    FRIENDS = "friends"     # 友情人际
    SELF = "self"           # 自我成长
    LIFE = "life"           # 生活琐事
    SCHOOL = "school"       # 学业压力
    MONEY = "money"         # 经济压力
    HEALTH = "health"       # 健康身心
    OTHER = "other"         # 其他


# 话题标签显示名称映射
TOPIC_TAG_LABELS: dict[str, str] = {
    TopicTag.WORK.value: "工作吐槽",
    TopicTag.FAMILY.value: "家庭关系",
    TopicTag.RELATIONSHIP.value: "情感恋爱",
    TopicTag.FRIENDS.value: "友情人际",
    TopicTag.SELF.value: "自我成长",
    TopicTag.LIFE.value: "生活琐事",
    TopicTag.SCHOOL.value: "学业压力",
    TopicTag.MONEY.value: "经济压力",
    TopicTag.HEALTH.value: "健康身心",
    TopicTag.OTHER.value: "其他",
}


# ---------------------------------------------------------------------------
# 帖子状态枚举
# ---------------------------------------------------------------------------

class PostStatus(str, Enum):
    """树洞帖子状态枚举。"""

    ACTIVE = "active"       # 正常显示
    EXPIRED = "expired"     # 已过期
    DELETED = "deleted"     # 已删除


# ---------------------------------------------------------------------------
# 匿名身份响应模型
# ---------------------------------------------------------------------------

class AnonymousIdentityResponse(BaseSchema):
    """匿名身份响应模型。

    显示虚拟昵称、气质标签和 AI 生成的小图标。
    """

    anon_id: str = Field(..., description="匿名身份ID")
    anon_nickname: str = Field(..., description="匿名昵称，如「温柔的月亮」")
    persona_tag: str | None = Field(None, description="气质标签，如「倾听者」")
    anon_avatar_url: str | None = Field(None, description="AI 生成的小图标URL")


# ---------------------------------------------------------------------------
# 模糊时间显示
# ---------------------------------------------------------------------------

class FuzzyTimeResponse(BaseSchema):
    """模糊时间显示模型。

    不显示精确时间，使用"刚刚"、"5分钟前"等模糊表达。
    """

    fuzzy_display: str = Field(..., description="模糊时间显示，如'刚刚'、'5分钟前'")
    # actual_minutes 仅用于内部计算，通过 exclude=True 不暴露给前端
    actual_minutes: int | None = Field(
        None,
        description="实际分钟数（内部使用，不暴露给前端）",
        exclude=True,  # 排除该字段，不序列化到响应中
    )


def format_fuzzy_time(
    created_at: datetime,
    now: datetime | None = None,
    random_delay_minutes: int = 0,
) -> FuzzyTimeResponse:
    """格式化模糊时间显示。

    发布时间随机化（0-15分钟随机延迟显示），不显示精确时间。

    Args:
        created_at: 实际创建时间
        now: 当前时间（可选，默认使用 datetime.now()）
        random_delay_minutes: 随机延迟分钟数（0-15）

    Returns:
        FuzzyTimeResponse 实例
    """
    from datetime import datetime as dt, timezone

    if now is None:
        now = dt.now(timezone.utc)

    # 计算实际显示时间（加上随机延迟）
    display_time = created_at
    if random_delay_minutes > 0:
        from datetime import timedelta
        display_time = created_at + timedelta(minutes=random_delay_minutes)

    # 计算时间差
    diff = now - display_time
    total_seconds = int(diff.total_seconds())
    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24

    # 模糊时间文案
    if minutes < 1:
        fuzzy_display = "刚刚"
    elif minutes < 5:
        fuzzy_display = "几分钟前"
    elif minutes < 15:
        fuzzy_display = "十几分钟前"
    elif minutes < 30:
        fuzzy_display = "半小时前"
    elif minutes < 60:
        fuzzy_display = f"{minutes}分钟前"
    elif hours < 2:
        fuzzy_display = "1小时前"
    elif hours < 24:
        fuzzy_display = f"{hours}小时前"
    elif days == 1:
        fuzzy_display = "昨天"
    elif days < 7:
        fuzzy_display = f"{days}天前"
    elif days < 30:
        fuzzy_display = f"{days // 7}周前"
    else:
        fuzzy_display = "很久了"

    return FuzzyTimeResponse(
        fuzzy_display=fuzzy_display,
        actual_minutes=minutes,
    )


# ---------------------------------------------------------------------------
# 帖子创建请求
# ---------------------------------------------------------------------------

class TreeholePostCreateRequest(BaseSchema):
    """创建树洞帖子请求模型。

    仅支持匿名发布，自动生成虚拟身份。
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="帖子内容，最多500字",
        examples=["今天又被领导骂了，好委屈..."],
    )
    topic_tag: TopicTag | None = Field(
        default=None,
        description="话题标签（可选）",
        examples=["work"],
    )
    image_urls: list[str] | None = Field(
        default=None,
        max_length=3,
        description="图片URL列表，最多3张",
    )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证内容不为空且去除首尾空格。"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()

    @field_validator("image_urls", mode="before")
    @classmethod
    def validate_image_urls(cls, v: list[str] | None) -> list[str] | None:
        """验证图片URL列表。"""
        if v is None:
            return None
        # 去重并去空
        urls = [url.strip() for url in v if url and url.strip()]
        if len(urls) == 0:
            return None
        return urls[:3]  # 最多3张


# ---------------------------------------------------------------------------
# 帖子响应模型
# ---------------------------------------------------------------------------

class TreeholePostResponse(BaseSchema):
    """树洞帖子响应模型。

    用于列表和详情显示，包含匿名身份和模糊时间。
    """

    id: str = Field(..., description="帖子ID")
    content: str = Field(..., description="帖子内容")
    topic_tag: str | None = Field(None, description="话题标签")
    topic_tag_label: str | None = Field(None, description="话题标签显示名称")
    image_urls: list[str] | None = Field(None, description="图片URL列表")
    anon_identity: AnonymousIdentityResponse | None = Field(
        None,
        description="匿名身份信息",
    )
    resonance_count: int = Field(default=0, description="共鸣数（'我懂你'数）")
    comment_count: int = Field(default=0, description="评论数")
    fuzzy_time: FuzzyTimeResponse | None = Field(
        None,
        description="模糊时间显示",
    )
    # 温度分（用于排序，不暴露给前端）
    temperature_score: float | None = Field(
        None,
        description="温度分（内部排序用）",
    )


class TreeholePostListResponse(BaseSchema):
    """树洞帖子列表响应模型。"""

    data: list[TreeholePostResponse] = Field(
        default_factory=list,
        description="帖子列表",
    )
    pagination: dict[str, Any] = Field(..., description="分页信息")
    topic_tags: dict[str, str] | None = Field(
        None,
        description="可用话题标签列表",
    )


class TreeholePostDetailResponse(BaseSchema):
    """树洞帖子详情响应模型。

    包含帖子详情和评论列表。
    """

    post: TreeholePostResponse = Field(..., description="帖子信息")
    comments: list["TreeholeCommentResponse"] = Field(
        default_factory=list,
        description="评论列表",
    )


# ---------------------------------------------------------------------------
# 评论相关模型
# ---------------------------------------------------------------------------

class TreeholeCommentCreateRequest(BaseSchema):
    """创建树洞评论请求模型。

    评论限50字，不支持回复评论。
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="评论内容，最多50字",
        examples=["我懂你，加油"],
    )
    is_resonance: bool = Field(
        default=False,
        description="是否为共鸣类型（'我懂你'按钮）",
    )

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """验证内容不为空且去除首尾空格。"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()


class TreeholeCommentResponse(BaseSchema):
    """树洞评论响应模型。

    评论不显示发布者身份信息（保持树洞匿名性）。
    """

    id: str = Field(..., description="评论ID")
    content: str = Field(..., description="评论内容")
    is_resonance: bool = Field(
        default=False,
        description="是否为共鸣类型",
    )
    fuzzy_time: FuzzyTimeResponse | None = Field(
        None,
        description="模糊时间显示",
    )


# ---------------------------------------------------------------------------
# 共鸣（"我懂你"）相关模型
# ---------------------------------------------------------------------------

class ResonanceCreateRequest(BaseSchema):
    """创建共鸣请求模型。

    点击"我懂你"按钮，等同于发送共鸣类型评论。
    """

    # 空请求体，只需要帖子ID即可


class ResonanceResponse(BaseSchema):
    """共鸣响应模型。"""

    resonance_count: int = Field(..., description="当前共鸣数")
    message: str = Field(
        default="有人懂你",
        description="提示信息",
    )
    already_resonated: bool = Field(
        default=False,
        description="是否已共鸣过",
    )


# ---------------------------------------------------------------------------
# 统计响应模型
# ---------------------------------------------------------------------------

class TreeholeStatsResponse(BaseSchema):
    """树洞统计响应模型。"""

    total_posts: int = Field(..., description="总帖子数")
    total_resonances: int = Field(..., description="总共鸣数")
    total_comments: int = Field(..., description="总评论数")
    topic_distribution: dict[str, int] | None = Field(
        None,
        description="话题分布统计",
    )


# ---------------------------------------------------------------------------
# 审核反馈与脱敏提醒模型
# ---------------------------------------------------------------------------

class AuditFeedbackInfo(BaseSchema):
    """审核反馈信息模型。

    审核不通过时，返回温和反馈文案引导用户修改或与AI朋友聊聊。
    """

    result: str = Field(..., description="审核结果：block/warn")
    feedback: str = Field(..., description="温和的审核反馈文案")
    labels: list[str] = Field(
        default_factory=list,
        description="审核标签列表",
    )


class IdentityWarningInfo(BaseSchema):
    """脱敏提醒信息模型。

    检测到可识别信息时，返回提醒信息（不影响发布）。
    """

    has_warning: bool = Field(..., description="是否检测到可识别信息")
    warning_message: str = Field(
        default="",
        description="脱敏提醒文案",
    )
    detected_types: list[str] = Field(
        default_factory=list,
        description="检测到的可识别信息类型列表",
    )


class TreeholePostCreateResponse(BaseSchema):
    """创建树洞帖子响应模型。

    在原有帖子响应基础上增加审核反馈和脱敏提醒。
    """

    post: TreeholePostResponse = Field(..., description="帖子信息")
    audit_feedback: AuditFeedbackInfo | None = Field(
        None,
        description="审核反馈信息（审核不通过时）",
    )
    identity_warning: IdentityWarningInfo | None = Field(
        None,
        description="脱敏提醒信息（检测到可识别信息时）",
    )
    trigger_care: bool = Field(
        default=False,
        description="是否触发关怀流程",
    )


class TreeholeCommentCreateResponse(BaseSchema):
    """创建树洞评论响应模型。

    在原有评论响应基础上增加审核反馈和脱敏提醒。
    """

    comment: TreeholeCommentResponse = Field(..., description="评论信息")
    audit_feedback: AuditFeedbackInfo | None = Field(
        None,
        description="审核反馈信息（审核不通过时）",
    )
    identity_warning: IdentityWarningInfo | None = Field(
        None,
        description="脱敏提醒信息（检测到可识别信息时）",
    )
    harassment_warning: str | None = Field(
        None,
        description="骚扰频率提醒文案（频率超限时）",
    )


# ---------------------------------------------------------------------------
# 误判申诉模型
# ---------------------------------------------------------------------------

class AuditAppealCreateRequest(BaseSchema):
    """审核结果申诉请求模型。

    被拦截/删除后可申诉，人工复核。
    """

    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="申诉理由，5-500字",
        examples=["这条内容是情绪表达，并非人身攻击"],
    )

    @field_validator("reason", mode="before")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """验证申诉理由不为空且去除首尾空格。"""
        if not v or not v.strip():
            raise ValueError("申诉理由不能为空")
        return v.strip()


class AuditAppealCreateResponse(BaseSchema):
    """审核结果申诉响应模型。"""

    id: str = Field(..., description="申诉记录ID")
    status: str = Field(
        default="pending",
        description="申诉状态：pending/approved/rejected",
    )
    message: str = Field(
        default="申诉已提交，我们会尽快审核",
        description="提示信息",
    )