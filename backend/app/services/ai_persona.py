"""性格管理模块。

提供 AI 性格的管理和切换功能，包括：
- Prompt 模板加载
- 时间段动态开场白
- 性格信息查询
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# 中国时区
CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


# ---------------------------------------------------------------------------
# 性格信息数据类
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class PersonaInfo:
    """性格信息。"""
    id: str                    # 性格标识
    name: str                  # 显示名称
    description: str           # 性格描述
    greeting_preview: str      # 开场白预览
    traits: list[str]          # 性格特点标签


# ---------------------------------------------------------------------------
# 时间段枚举
# ---------------------------------------------------------------------------

class TimeSlot:
    """时间段常量。"""
    LATE_NIGHT = "late_night"       # 23:00-02:00 深夜
    EARLY_MORNING = "early_morning"  # 02:00-05:00 极深夜
    MORNING = "morning"              # 05:00-07:00 清晨
    DEFAULT = "default"              # 其他时间


def _get_time_slot(hour: int) -> str:
    """根据小时判断时间段。

    Args:
        hour: 当前小时 (0-23)

    Returns:
        时间段标识
    """
    if 23 <= hour or hour < 2:
        return TimeSlot.LATE_NIGHT
    elif 2 <= hour < 5:
        return TimeSlot.EARLY_MORNING
    elif 5 <= hour < 7:
        return TimeSlot.MORNING
    else:
        return TimeSlot.DEFAULT


# ---------------------------------------------------------------------------
# 开场白配置
# ---------------------------------------------------------------------------

# 三种性格按时间段的开场白
GREETINGS_BY_TIME: dict[str, dict[str, str]] = {
    "xiaowen": {
        TimeSlot.LATE_NIGHT: "这么晚还没睡，是不是心里有事？我在听。",
        TimeSlot.EARLY_MORNING: "你也睡不着吗？这个时间醒着的人，大多心里装着点事。想说说吗？",
        TimeSlot.MORNING: "早安。醒这么早，是没睡好还是有什么心事？",
        TimeSlot.DEFAULT: "嗨，不管外面多吵，在这里，你可以安心说话。你现在感觉怎么样？",
    },
    "laohei": {
        TimeSlot.LATE_NIGHT: "大半夜不睡觉，又想什么呢？",
        TimeSlot.EARLY_MORNING: "凌晨了？你可真行。说吧，什么事让你这么晚还醒着。",
        TimeSlot.MORNING: "这谁啊，大清早的就醒了？说说怎么回事。",
        TimeSlot.DEFAULT: "哟，又来找我聊天了？你那破事还没解决呢？说说吧，让我开心一下。",
    },
    "ali": {
        TimeSlot.LATE_NIGHT: "深夜了还在想事情？我们来理一理。",
        TimeSlot.EARLY_MORNING: "凌晨还醒着，说明脑子里有事。说出来，我们拆解一下。",
        TimeSlot.MORNING: "早起的人，通常脑子很清醒。有什么想理清的？",
        TimeSlot.DEFAULT: "嗨，脑子乱的时候，我们可以一起理一理。你最近在烦恼什么？",
    },
}

# 性格信息配置
PERSONA_INFO: dict[str, PersonaInfo] = {
    "xiaowen": PersonaInfo(
        id="xiaowen",
        name="小温",
        description="温柔倾听者，善于共情，让你感到被理解",
        greeting_preview=GREETINGS_BY_TIME["xiaowen"][TimeSlot.DEFAULT],
        traits=["温柔", "细腻", "共情", "不评判"],
    ),
    "laohei": PersonaInfo(
        id="laohei",
        name="老黑",
        description="毒舌吐槽者，嘴损心热，一针见血",
        greeting_preview=GREETINGS_BY_TIME["laohei"][TimeSlot.DEFAULT],
        traits=["毒舌", "直接", "损友感", "关键时刻认真"],
    ),
    "ali": PersonaInfo(
        id="ali",
        name="阿理",
        description="理性开导者，结构化思考，帮你理清思路",
        greeting_preview=GREETINGS_BY_TIME["ali"][TimeSlot.DEFAULT],
        traits=["理性", "结构化", "提问引导", "分析问题"],
    ),
}


# ---------------------------------------------------------------------------
# 性格管理器
# ---------------------------------------------------------------------------

class PersonaManager:
    """性格管理器，负责 Prompt 加载、切换和开场白生成。

    Attributes:
        prompts_dir: Prompt 文件目录路径
        _prompts: 缓存的 System Prompt 内容
    """

    # Prompt 文件名映射
    PROMPT_FILES: dict[str, str] = {
        "xiaowen": "xiaowen.txt",
        "laohei": "laohei.txt",
        "ali": "ali.txt",
    }

    # 有效的性格标识
    VALID_PERSONALITIES = ("xiaowen", "laohei", "ali")

    def __init__(self, prompts_dir: str | Path = "app/prompts") -> None:
        """初始化性格管理器。

        Args:
            prompts_dir: Prompt 文件目录路径，可以是字符串或 Path 对象
        """
        self._prompts_dir = Path(prompts_dir)
        self._prompts: dict[str, str] = {}
        self._loaded = False

        logger.info(
            "[PersonaManager] 初始化完成，Prompt 目录: %s",
            self._prompts_dir
        )

    def _load_prompt(self, personality: str) -> str:
        """加载指定性格的 Prompt 文件。

        Args:
            personality: 性格标识

        Returns:
            Prompt 文本内容

        Raises:
            FileNotFoundError: Prompt 文件不存在
            ValueError: 性格标识无效
        """
        if personality not in self.PROMPT_FILES:
            available = ", ".join(self.VALID_PERSONALITIES)
            raise ValueError(f"未知的性格类型: {personality}，可用选项: [{available}]")

        # 检查缓存
        if personality in self._prompts:
            return self._prompts[personality]

        # 加载文件
        filename = self.PROMPT_FILES[personality]
        filepath = self._prompts_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Prompt 文件不存在: {filepath}")

        content = filepath.read_text(encoding="utf-8")
        self._prompts[personality] = content

        logger.debug(
            "[PersonaManager] 加载 Prompt: %s，长度: %d 字符",
            personality,
            len(content)
        )

        return content

    def _load_all_prompts(self) -> None:
        """加载所有性格的 Prompt 文件。"""
        if self._loaded:
            return

        for personality in self.VALID_PERSONALITIES:
            try:
                self._load_prompt(personality)
            except FileNotFoundError as e:
                logger.warning("[PersonaManager] %s", e)

        self._loaded = True

    def get_system_prompt(self, personality: str) -> str:
        """获取指定性格的完整 System Prompt。

        Args:
            personality: 性格标识 (xiaowen/laohei/ali)

        Returns:
            System Prompt 字符串

        Raises:
            ValueError: 当 personality 无效时
            FileNotFoundError: Prompt 文件不存在时
        """
        return self._load_prompt(personality)

    def get_greeting(self, personality: str, hour: int | None = None) -> str:
        """获取指定性格的开场白，支持按时间段动态变化。

        Args:
            personality: 性格标识 (xiaowen/laohei/ali)
            hour: 当前小时 (0-23)，None 则使用中国时区当前时间

        Returns:
            开场白文本

        Raises:
            ValueError: 当 personality 无效时
        """
        if personality not in self.VALID_PERSONALITIES:
            available = ", ".join(self.VALID_PERSONALITIES)
            raise ValueError(f"未知的性格类型: {personality}，可用选项: [{available}]")

        # 确定小时
        if hour is None:
            hour = datetime.now(CHINA_TIMEZONE).hour
        else:
            hour = hour % 24  # 确保在 0-23 范围内

        # 获取时间段
        time_slot = _get_time_slot(hour)

        # 返回对应时间段的开场白
        greetings = GREETINGS_BY_TIME.get(personality, GREETINGS_BY_TIME["xiaowen"])
        return greetings.get(time_slot, greetings[TimeSlot.DEFAULT])

    def get_available_personalities(self) -> list[dict[str, Any]]:
        """返回所有可用性格的列表（含名称、描述、开场白预览）。

        Returns:
            性格信息列表，每个元素包含：
            - id: 性格标识
            - name: 显示名称
            - description: 性格描述
            - greeting_preview: 开场白预览
            - traits: 性格特点标签
        """
        self._load_all_prompts()

        result = []
        for persona_id, info in PERSONA_INFO.items():
            result.append({
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "greeting_preview": info.greeting_preview,
                "traits": info.traits,
            })

        return result

    def get_persona_info(self, personality: str) -> PersonaInfo | None:
        """获取指定性格的信息。

        Args:
            personality: 性格标识

        Returns:
            PersonaInfo 对象，不存在则返回 None
        """
        return PERSONA_INFO.get(personality)

    def is_valid_personality(self, personality: str) -> bool:
        """检查性格标识是否有效。

        Args:
            personality: 性格标识

        Returns:
            是否有效
        """
        return personality in self.VALID_PERSONALITIES


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

# 默认实例
_default_manager: PersonaManager | None = None


def get_persona_manager(prompts_dir: str | Path | None = None) -> PersonaManager:
    """获取全局性格管理器实例。

    Args:
        prompts_dir: Prompt 文件目录路径，仅首次调用时有效

    Returns:
        PersonaManager 实例
    """
    global _default_manager

    if _default_manager is None:
        if prompts_dir is None:
            # 使用默认路径
            prompts_dir = Path(__file__).parent.parent / "prompts"
        _default_manager = PersonaManager(prompts_dir)

    return _default_manager


def reset_persona_manager() -> None:
    """重置全局性格管理器实例（用于测试）。"""
    global _default_manager
    _default_manager = None
