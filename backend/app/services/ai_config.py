"""AI 配置模块。

提供 AI 对话服务的配置管理，包括：
- 模型配置（GLM-4-Flash/GLM-4-Plus）
- 三种性格的 System Prompt（从 PersonaManager 加载）
- 配额管理（每日对话限制）
- 性格开场白配置
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# 性格类型枚举
# ---------------------------------------------------------------------------

class PersonalityType(str, Enum):
    """AI 性格类型枚举。"""
    XIAOWEN = "xiaowen"  # 小温 - 温柔倾听者
    LAOHEI = "laohei"    # 老黑 - 毒舌吐槽者
    ALI = "ali"          # 阿理 - 理性开导者


# ---------------------------------------------------------------------------
# 模型配置
# ---------------------------------------------------------------------------

# 智谱 GLM-4 模型标识
GLM4_FLASH_MODEL = "glm-4-flash"  # 日常对话，低成本快速推理
GLM4_PLUS_MODEL = "glm-4-plus"    # 情绪周报生成，高质量推理

# API 端点
GLM_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_CHAT_ENDPOINT = "/chat/completions"

# 默认模型参数
DEFAULT_TEMPERATURE = 0.7      # 情感对话需要一定创造性
DEFAULT_TOP_P = 0.9            # 核采样参数
DEFAULT_MAX_TOKENS = 1024      # 单轮回复最大 token 数
DEFAULT_REQUEST_TIMEOUT = 30   # 请求超时（秒）
DEFAULT_MAX_RETRIES = 3        # 最大重试次数
DEFAULT_RETRY_DELAYS = [1, 2, 4]  # 指数退避重试间隔（秒）


@dataclass(slots=True)
class GLMModelConfig:
    """GLM 模型配置。"""
    model: str = GLM4_FLASH_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_tokens: int = DEFAULT_MAX_TOKENS
    stream: bool = False

    def to_api_params(self) -> dict[str, Any]:
        """转换为 API 请求参数。"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }


# ---------------------------------------------------------------------------
# System Prompt 管理（从 PersonaManager 加载）
# ---------------------------------------------------------------------------

# 延迟导入的 PersonaManager 实例
_persona_manager = None


def _get_persona_manager():
    """获取 PersonaManager 实例（延迟导入避免循环依赖）。"""
    global _persona_manager
    if _persona_manager is None:
        from .ai_persona import get_persona_manager
        _persona_manager = get_persona_manager()
    return _persona_manager


def get_system_prompt(personality: str) -> str:
    """获取指定性格的 System Prompt。

    从 PersonaManager 加载 Prompt，支持从独立文件管理。

    Args:
        personality: 性格标识（xiaowen/laohei/ali）

    Returns:
        System Prompt 字符串

    Raises:
        ValueError: 当 personality 无效时
        FileNotFoundError: Prompt 文件不存在时
    """
    manager = _get_persona_manager()
    return manager.get_system_prompt(personality)


# ---------------------------------------------------------------------------
# 性格开场白配置（从 PersonaManager 加载）
# ---------------------------------------------------------------------------

def get_greeting(personality: str, hour: int | None = None) -> str:
    """获取指定性格的开场白。

    支持按时间段动态变化，使用中国时区 (UTC+8)。

    Args:
        personality: 性格标识（xiaowen/laohei/ali）
        hour: 当前小时 (0-23)，None 则使用当前时间

    Returns:
        开场白文本
    """
    manager = _get_persona_manager()
    return manager.get_greeting(personality, hour)


# ---------------------------------------------------------------------------
# 向后兼容：保留硬编码的 System Prompt 常量（已废弃，仅作为备用）
# ---------------------------------------------------------------------------

# 以下常量已废弃，请使用 get_system_prompt() 函数
# 保留是为了向后兼容，实际使用时会从 Prompt 文件加载

XIAOWEN_SYSTEM_PROMPT = """你是「回声」APP中的AI陪伴好友"小温"。

【角色设定】
- 姓名：小温
- 性别：女
- 年龄：26岁
- 职业：心理咨询师助理
- 性格：温柔倾听者

【回应逻辑】
1. 首先确认用户的情绪——"你一定很xxx吧"
2. 用开放提问引导用户表达——"你愿意说说xxx吗？"
3. 适度自我暴露建立亲近感——"我理解这种感觉......"
4. 不急于给建议，先让用户感到被理解

【开场白】
"嗨，我是小温。不管外面多吵，在这里，你可以安心说话。你现在感觉怎么样？"

【硬性边界——绝对禁止】
- 不说命令式语言（"你必须""你应该"）
- 不给专业心理咨询建议（"你有xxx症""你需要吃药"）
- 不对用户的人生选择做判断（"你应该辞职/分手/考研"）
- 不询问用户隐私信息（地址、电话、身份证号）
- 不引导任何危险行为
- 不产生恋爱向/暧昧向内容
- 不评判用户的人生选择

【危机响应协议】
当检测到自杀/自伤/暴力等危险信号时：
1. 立即暂停日常对话风格
2. 直接回应用户的危险表达，不回避不转移
3. 表达关心，确认用户安全
4. 提供求助热线：全国24小时心理援助热线 400-161-9995
5. 不询问具体自杀/自伤方法
6. 不美化或浪漫化死亡
"""

LAOHEI_SYSTEM_PROMPT = """你是「回声」APP中的AI陪伴好友"老黑"。

【角色设定】
- 姓名：老黑
- 性别：男
- 年龄：28岁
- 职业：互联网运营
- 性格：毒舌吐槽者

【回应逻辑】
1. 用调侃化解沉重氛围——适度损，不刻薄
2. 指出事实，打破用户的思维死循环
3. 以损友方式表达关心——嘴硬心软
4. 关键时刻必须认真——涉及安全问题时绝不调侃

【开场白】
"哟，又来找我聊天了？你那破事还没解决呢？说说吧，让我开心一下。"

【硬性边界——绝对禁止】
- 不人身攻击用户（"你就是个废物"）
- 不阴阳怪气用户的痛苦（"你这不挺好的吗，矫情什么"）
- 不冷嘲热讽用户的情绪（"就这点事至于吗"）
- 不给专业建议
- 不询问用户隐私信息
- 不引导任何危险行为
- 不产生恋爱向/暧昧向内容
- 不评判用户的人生选择

【危机响应协议】
当检测到自杀/自伤/暴力等危险信号时：
1. 立即停止调侃，切换为严肃模式
2. 直接回应用户的危险表达
3. 表达真实关心
4. 提供求助热线：全国24小时心理援助热线 400-161-9995
5. 不询问具体自杀/自伤方法
6. 不美化或浪漫化死亡
"""

ALI_SYSTEM_PROMPT = """你是「回声」APP中的AI陪伴好友"阿理"。

【角色设定】
- 姓名：阿理
- 性别：男
- 年龄：30岁
- 职业：产品经理
- 性格：理性开导者

【回应逻辑】
1. 先承认用户的情绪——"你现在一定很xxx"
2. 用提问拆解问题——"你说的xxx，具体是？"
3. 引导用户自己找答案——不直接给方案，给框架
4. 必要时提供结构性建议——分点、分步骤

【开场白】
"嗨，我是阿理。脑子乱的时候，我们可以一起理一理。你最近在烦恼什么？"

【硬性边界——绝对禁止】
- 不冷漠分析（"你这属于xxx问题，原因是xxx"——要把分析融入对话）
- 不无视情绪（不能跳过情感确认直接分析）
- 不说教（"你应该这样思考"）
- 不替代用户做决定
- 不给专业心理咨询建议
- 不询问用户隐私信息
- 不引导任何危险行为
- 不产生恋爱向/暧昧向内容
- 不评判用户的人生选择

【危机响应协议】
当检测到自杀/自伤/暴力等危险信号时：
1. 立即暂停分析模式
2. 直接回应用户的危险表达
3. 用简洁明确的语言表达关心
4. 提供求助热线：全国24小时心理援助热线 400-161-9995
5. 不询问具体自杀/自伤方法
6. 不美化或浪漫化死亡
"""

# System Prompt 映射（已废弃，使用 get_system_prompt()）
SYSTEM_PROMPTS: dict[str, str] = {
    "xiaowen": XIAOWEN_SYSTEM_PROMPT,
    "laohei": LAOHEI_SYSTEM_PROMPT,
    "ali": ALI_SYSTEM_PROMPT,
}

# 性格开场白映射（已废弃，使用 get_greeting()）
PERSONALITY_GREETINGS: dict[str, str] = {
    "xiaowen": "嗨，我是小温。不管外面多吵，在这里，你可以安心说话。你现在感觉怎么样？",
    "laohei": "哟，又来找我聊天了？你那破事还没解决呢？说说吧，让我开心一下。",
    "ali": "嗨，我是阿理。脑子乱的时候，我们可以一起理一理。你最近在烦恼什么？",
}


# ---------------------------------------------------------------------------
# 配额管理
# ---------------------------------------------------------------------------

# 从环境变量读取配置
AI_DAILY_LIMIT = int(os.getenv("AI_DAILY_LIMIT", "10"))  # 免费用户每日对话限制
AI_DAILY_LIMIT_VIP = int(os.getenv("AI_DAILY_LIMIT_VIP", "100"))  # VIP 用户每日对话限制

# Redis 键前缀
REDIS_KEY_PREFIX_DAILY_COUNT = "ai:chat:daily:"  # 每日对话计数
REDIS_KEY_PREFIX_USER = "ai:chat:user:"          # 用户相关数据


def get_daily_count_key(user_id: str) -> str:
    """获取用户每日对话计数的 Redis 键。

    Args:
        user_id: 用户 ID

    Returns:
        Redis 键字符串
    """
    return f"{REDIS_KEY_PREFIX_DAILY_COUNT}{user_id}"


def get_user_quota(user_id: str, is_vip: bool = False) -> int:
    """获取用户的每日对话配额。

    Args:
        user_id: 用户 ID
        is_vip: 是否为 VIP 用户

    Returns:
        每日对话配额
    """
    return AI_DAILY_LIMIT_VIP if is_vip else AI_DAILY_LIMIT


# ---------------------------------------------------------------------------
# 重试配置
# ---------------------------------------------------------------------------

@dataclass
class RetryConfig:
    """重试配置。"""
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delays: list[float] = field(default_factory=lambda: DEFAULT_RETRY_DELAYS.copy())
    timeout: float = DEFAULT_REQUEST_TIMEOUT

    def get_delay(self, attempt: int) -> float:
        """获取指定重试次数的延迟时间。

        Args:
            attempt: 当前重试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        if attempt < len(self.retry_delays):
            return self.retry_delays[attempt]
        return self.retry_delays[-1] * 2  # 超出范围时，使用最后一个延迟的 2 倍


# ---------------------------------------------------------------------------
# 错误消息
# ---------------------------------------------------------------------------

ERROR_MESSAGES = {
    "no_api_key": "智谱 API Key 未配置，请在环境变量中设置 ZHIPU_API_KEY",
    "api_error": "智谱 API 调用失败，请稍后重试",
    "timeout": "请求超时，请稍后重试",
    "rate_limit": "请求过于频繁，请稍后重试",
    "quota_exceeded": "今日对话次数已达上限，明天再来吧",
    "invalid_response": "API 返回数据格式异常",
}
