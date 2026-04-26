"""情绪日记相关请求/响应模型。

包含日记 CRUD、隐私同意、同步设置、导出等接口的 Schema 定义。
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema


# ---------------------------------------------------------------------------
# 情绪色调枚举
# ---------------------------------------------------------------------------

class EmotionTone(str, Enum):
    """情绪色调枚举。

    五种色调代表不同情绪能量级别：
    - warm_orange: 充满能量、开心
    - light_green: 平静、安稳
    - gray_blue: 低落、沉闷
    - deep_blue: 难过、忧伤
    - dark_purple: 崩溃、混乱
    """

    WARM_ORANGE = "warm_orange"  # 暖橘 #FF9A5C
    LIGHT_GREEN = "light_green"  # 浅绿 #8FCCA0
    GRAY_BLUE = "gray_blue"  # 灰蓝 #8BA7C4
    DEEP_BLUE = "deep_blue"  # 深蓝 #4A6FA5
    DARK_PURPLE = "dark_purple"  # 暗紫 #6B4C7A


# 情绪色调映射：色调 -> 可选标签列表
EMOTION_TONE_LABELS: dict[str, list[str]] = {
    EmotionTone.WARM_ORANGE.value: [
        "开心", "感恩", "兴奋", "被爱", "有希望", "自豪", "释然",
    ],
    EmotionTone.LIGHT_GREEN.value: [
        "平静", "放松", "专注", "安心", "满足", "无聊",
    ],
    EmotionTone.GRAY_BLUE.value: [
        "焦虑", "疲惫", "迷茫", "孤独", "委屈", "烦躁",
    ],
    EmotionTone.DEEP_BLUE.value: [
        "难过", "失望", "自责", "心疼", "想念", "害怕",
    ],
    EmotionTone.DARK_PURPLE.value: [
        "混乱", "麻木", "空洞", "矛盾", "崩溃", "说不清",
    ],
}

# 色调元数据：颜色代码和代表语
EMOTION_TONE_META: dict[str, dict[str, str]] = {
    EmotionTone.WARM_ORANGE.value: {
        "color": "#FF9A5C",
        "meaning": "充满能量、开心",
        "phrase": "今天还不错",
    },
    EmotionTone.LIGHT_GREEN.value: {
        "color": "#8FCCA0",
        "meaning": "平静、安稳",
        "phrase": "还算正常",
    },
    EmotionTone.GRAY_BLUE.value: {
        "color": "#8BA7C4",
        "meaning": "低落、沉闷",
        "phrase": "有点堵",
    },
    EmotionTone.DEEP_BLUE.value: {
        "color": "#4A6FA5",
        "meaning": "难过、忧伤",
        "phrase": "很难受",
    },
    EmotionTone.DARK_PURPLE.value: {
        "color": "#6B4C7A",
        "meaning": "崩溃、混乱",
        "phrase": "说不清",
    },
}


# ---------------------------------------------------------------------------
# 同步模式枚举
# ---------------------------------------------------------------------------

class SyncMode(str, Enum):
    """日记同步模式枚举。

    - LOCAL_ONLY: 仅存储在本地设备
    - CLOUD_SYNC: 开启云端同步
    """

    LOCAL_ONLY = "local_only"
    CLOUD_SYNC = "cloud_sync"


# ---------------------------------------------------------------------------
# 导出格式枚举
# ---------------------------------------------------------------------------

class ExportFormat(str, Enum):
    """日记导出格式枚举。"""

    JSON = "json"
    PDF = "pdf"


# ---------------------------------------------------------------------------
# 日记创建/更新请求
# ---------------------------------------------------------------------------

class DiaryCreateRequest(BaseSchema):
    """创建日记请求模型。

    三层标签结构：
    - emotion_tone: 情绪色调（必选1）
    - emotion_labels: 情绪标签（可选，最多3个）
    - content_text: 自由文字（可选，支持语音输入）
    """

    emotion_tone: EmotionTone = Field(
        ...,
        description="情绪色调",
        examples=["warm_orange"],
    )
    emotion_labels: list[str] | None = Field(
        default=None,
        max_length=3,
        description="情绪标签列表，最多3个",
        examples=[["开心", "感恩"]],
    )
    content_text: str | None = Field(
        default=None,
        max_length=2000,
        description="日记内容文字，最多2000字",
        examples=["今天天气真好，心情愉快。"],
    )
    record_date: date = Field(
        ...,
        description="记录日期",
        examples=["2024-01-15"],
    )
    client_id: str | None = Field(
        default=None,
        max_length=50,
        description="客户端唯一标识，用于离线同步去重",
        examples=["device_abc123"],
    )
    is_encrypted: bool = Field(
        default=False,
        description="内容是否已加密",
    )
    content_hash: str | None = Field(
        default=None,
        max_length=64,
        description="内容哈希，用于完整性校验",
    )

    @field_validator("emotion_labels", mode="before")
    @classmethod
    def validate_emotion_labels(cls, v: list[str] | None) -> list[str] | None:
        """验证情绪标签格式。"""
        if v is None:
            return None
        # 去重并去空
        labels = [label.strip() for label in v if label and label.strip()]
        if len(labels) == 0:
            return None
        return labels[:3]  # 最多3个

    @model_validator(mode="after")
    def validate_labels_match_tone(self) -> "DiaryCreateRequest":
        """验证标签是否与色调匹配。"""
        if self.emotion_labels:
            valid_labels = EMOTION_TONE_LABELS.get(self.emotion_tone.value, [])
            for label in self.emotion_labels:
                if label not in valid_labels:
                    raise ValueError(
                        f"情绪标签 '{label}' 不属于色调 '{self.emotion_tone.value}' 的有效标签"
                    )
        return self


class DiaryUpdateRequest(BaseSchema):
    """更新日记请求模型。"""

    emotion_tone: EmotionTone | None = Field(
        default=None,
        description="情绪色调",
    )
    emotion_labels: list[str] | None = Field(
        default=None,
        max_length=3,
        description="情绪标签列表，最多3个",
    )
    content_text: str | None = Field(
        default=None,
        max_length=2000,
        description="日记内容文字",
    )
    is_encrypted: bool = Field(
        default=False,
        description="内容是否已加密",
    )
    content_hash: str | None = Field(
        default=None,
        max_length=64,
        description="内容哈希，用于完整性校验",
    )

    @field_validator("emotion_labels", mode="before")
    @classmethod
    def validate_emotion_labels(cls, v: list[str] | None) -> list[str] | None:
        """验证情绪标签格式。"""
        if v is None:
            return None
        labels = [label.strip() for label in v if label and label.strip()]
        if len(labels) == 0:
            return None
        return labels[:3]

    @model_validator(mode="after")
    def validate_labels_match_tone(self) -> "DiaryUpdateRequest":
        """验证标签是否与色调匹配。"""
        if self.emotion_tone and self.emotion_labels:
            valid_labels = EMOTION_TONE_LABELS.get(self.emotion_tone.value, [])
            for label in self.emotion_labels:
                if label not in valid_labels:
                    raise ValueError(
                        f"情绪标签 '{label}' 不属于色调 '{self.emotion_tone.value}' 的有效标签"
                    )
        return self


# ---------------------------------------------------------------------------
# 日记响应模型
# ---------------------------------------------------------------------------

class DiaryResponse(BaseSchema):
    """日记响应模型。"""

    id: str = Field(..., description="日记ID")
    emotion_tone: str | None = Field(None, description="情绪色调")
    emotion_labels: list[str] | None = Field(None, description="情绪标签列表")
    content_text: str | None = Field(None, description="日记内容（已解密）")
    record_date: date = Field(..., description="记录日期")
    is_synced: bool = Field(..., description="是否已同步")
    is_encrypted: bool = Field(default=False, description="内容是否加密")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 计算属性：是否为 0 字记录
    is_zero_record: bool = Field(
        default=False,
        description="是否为0字记录（纯色调，不计入周报分析）",
    )


class DiaryListResponse(BaseSchema):
    """日记列表响应模型。"""

    data: list[DiaryResponse] = Field(default_factory=list, description="日记列表")
    pagination: dict[str, Any] = Field(..., description="分页信息")


class DiaryDetailResponse(BaseSchema):
    """日记详情响应模型。"""

    id: str = Field(..., description="日记ID")
    emotion_tone: str | None = Field(None, description="情绪色调")
    emotion_labels: list[str] | None = Field(None, description="情绪标签列表")
    content_text: str | None = Field(None, description="日记内容（已解密）")
    record_date: date = Field(..., description="记录日期")
    is_synced: bool = Field(..., description="是否已同步")
    is_encrypted: bool = Field(default=False, description="内容是否加密")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    client_id: str | None = Field(None, description="客户端ID")
    content_hash: str | None = Field(None, description="内容哈希")

    # 计算属性
    is_zero_record: bool = Field(
        default=False,
        description="是否为0字记录",
    )
    tone_meta: dict[str, str] | None = Field(
        None,
        description="色调元数据（颜色、含义、代表语）",
    )


# ---------------------------------------------------------------------------
# 隐私同意相关
# ---------------------------------------------------------------------------

class PrivacyConsentResponse(BaseSchema):
    """隐私同意状态响应模型。"""

    has_consented: bool = Field(..., description="是否已同意隐私声明")
    consented_at: datetime | None = Field(None, description="同意时间")
    sync_mode: SyncMode = Field(
        default=SyncMode.LOCAL_ONLY,
        description="当前同步模式",
    )


class PrivacyConsentRequest(BaseSchema):
    """同意隐私声明请求模型。"""

    sync_mode: SyncMode = Field(
        ...,
        description="选择的同步模式：local_only 或 cloud_sync",
    )


# ---------------------------------------------------------------------------
# 同步设置相关
# ---------------------------------------------------------------------------

class SyncSettingsResponse(BaseSchema):
    """同步设置响应模型。"""

    sync_mode: SyncMode = Field(..., description="当前同步模式")
    last_sync_at: datetime | None = Field(None, description="上次同步时间")
    sync_device_count: int = Field(default=0, description="已同步设备数")
    encryption_enabled: bool = Field(
        default=True,
        description="是否启用端到端加密",
    )


class SyncSettingsUpdateRequest(BaseSchema):
    """更新同步设置请求模型。"""

    sync_mode: SyncMode = Field(..., description="同步模式")


# ---------------------------------------------------------------------------
# 导出相关
# ---------------------------------------------------------------------------

class ExportRequest(BaseSchema):
    """日记导出请求模型。"""

    format: ExportFormat = Field(
        default=ExportFormat.JSON,
        description="导出格式：json 或 pdf",
    )
    start_date: date | None = Field(
        default=None,
        description="导出起始日期",
    )
    end_date: date | None = Field(
        default=None,
        description="导出结束日期",
    )
    include_encrypted: bool = Field(
        default=False,
        description="是否包含加密内容（需提供密钥）",
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "ExportRequest":
        """验证日期范围。"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("起始日期不能晚于结束日期")
        return self


class ExportResponse(BaseSchema):
    """日记导出响应模型。"""

    download_url: str = Field(..., description="下载链接")
    expires_at: datetime = Field(..., description="链接过期时间")
    file_format: str = Field(..., description="文件格式")
    record_count: int = Field(..., description="导出记录数")


# ---------------------------------------------------------------------------
# 删除相关
# ---------------------------------------------------------------------------

class DeleteAllResponse(BaseSchema):
    """删除全部日记响应模型。"""

    deleted_count: int = Field(..., description="已删除数量")
    message: str = Field(default="所有日记已删除", description="提示信息")


# ---------------------------------------------------------------------------
# 统计相关
# ---------------------------------------------------------------------------

class DiaryStatsResponse(BaseSchema):
    """日记统计响应模型。"""

    total_records: int = Field(..., description="总记录数")
    total_days: int = Field(..., description="已记录天数")
    zero_record_count: int = Field(..., description="0字记录数")
    valid_sample_count: int = Field(..., description="有效样本数（用于周报分析）")
    emotion_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="情绪分布统计",
    )
