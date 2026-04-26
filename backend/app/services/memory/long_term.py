"""长期记忆服务。

使用 MySQL 永久存储用户画像和重要事件，支持：
- 用户画像管理（性格偏好、兴趣、情绪模式、生活状态）
- 重要事件记录（生日、纪念日、人生大事件）
- 记住/忘记规则判断（PRD 2.3）
- 永不过期（expires_at 为 None）
- 人工/事件触发更新
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIMemory
from app.services.ai_chat import MockAIChat, GLMChatService, create_ai_chat_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------

# 长期记忆类型
MEMORY_TYPE_LONG_TERM = "long_term"
MEMORY_TYPE_PERSON_INFO = "person_info"
MEMORY_TYPE_EVENT = "event"

# 默认重要度
DEFAULT_IMPORTANCE = 8

# 事件类型
EVENT_TYPE_BIRTHDAY = "birthday"
EVENT_TYPE_ANNIVERSARY = "anniversary"
EVENT_TYPE_MILESTONE = "milestone"


# ---------------------------------------------------------------------------
# 记住/忘记规则（PRD 2.3）
# ---------------------------------------------------------------------------

# 记住什么
REMEMBER_PATTERNS = {
    # 人物关系：名字、关系、重要事件
    "person_relations": [
        r"(?:我(?:的)?(?:妈妈|爸爸|哥哥|姐姐|弟弟|妹妹|老公|老婆|男朋友|女朋友|男友|女友|孩子|儿子|女儿))",
        r"(?:叫[一-龥]{1,3})",
        r"(?:我(?:有个|有一位|和一个)(?:同事|朋友|室友))",
        r"(?:和[一-龥]{1,3}(?:在一起|认识|结婚))",
        r"(?:妈妈|爸爸|哥哥|姐姐|弟弟|妹妹|老公|老婆|男票|女票)(?:的(?:生日|名字))",
    ],
    # 生活状态：职业、城市、作息、宠物、爱好
    "life_status": [
        r"(?:我(?:是|做|在|住)(?:工作|程序员|设计师|老师|医生|学生|公司))",
        r"(?:我(?:在|住)(?:北京|上海|广州|深圳|[一-龥]+市))",
        r"(?:我(?:有|养)(?:猫|狗|宠物))",
        r"(?:我(?:喜欢|爱好|平时)(?:看书|听歌|跑步|健身|游戏|旅行|音乐))",
        r"(?:我(?:上班|工作|作息|睡觉|起床)(?:时间|点))",
        r"(?:996|早九晚五|加班)",
    ],
    # 重要事件：生日、纪念日、人生大事件
    "important_events": [
        r"(?:生日(?:是|在))",
        r"(?:纪念日)",
        r"(?:结婚|订婚|毕业|入职|升职|跳槽|离职)",
        r"(?:考研|考公|面试)",
        r"(?:重要(?:的)?日子)",
    ],
    # 情绪模式：常在什么时间情绪低落、什么话题触发负面情绪
    "emotion_patterns": [
        r"(?:深夜|晚上|凌晨)(?:容易|总是|经常)(?:难过|焦虑|失眠|想太多)",
        r"(?:周一|周末|假期)(?:焦虑|抑郁|不想上班)",
        r"(?:工作|领导|同事|考试|论文)(?:压力|焦虑|烦躁)",
        r"(?:一(?:想到|提到|聊到)[一-龥]+就)",
        r"(?:最近(?:压力|焦虑|状态)(?:很|比较))",
    ],
    # 对话偏好：喜欢什么回应风格
    "preferences": [
        r"(?:我喜欢(?:你|你(?:的))(?:倾听|安慰|陪伴|建议))",
        r"(?:不要(?:给我)?建议)",
        r"(?:只想(?:有人)?(?:听|说|聊聊))",
        r"(?:希望(?:你|你能))",
        r"(?:别(?:评判|评价|说教))",
    ],
}

# 忘记什么
FORGET_PATTERNS = {
    # 随口提的不重要人物
    "trivial_persons": [
        r"(?:刚遇到(?:一个|个)(?:路人|陌生人))",
        r"(?:今天(?:外卖|快递|司机)(?:小哥|师傅))",
    ],
    # 临时状态（今天吃了什么）
    "temp_status": [
        r"(?:今天(?:吃|喝|买)(?:了|过))",
        r"(?:中午|晚上|早上)(?:吃|喝)(?:了|过))",
        r"(?:刚(?:去|买|看)(?:了|过))",
    ],
    # 琐碎日常
    "trivial_daily": [
        r"(?:今天(?:天气|阴|晴|雨))",
        r"(?:路上(?:堵车|没堵))",
        r"(?:刚(?:刷完|洗完|收拾完))",
    ],
}


# ---------------------------------------------------------------------------
# 用户画像提取 Prompt 模板
# ---------------------------------------------------------------------------

PROFILE_EXTRACT_SYSTEM_PROMPT = """你是一个用户画像分析助手，负责从对话中提取用户的长期记忆信息。

你的任务是分析对话内容，提取以下类型的信息：

1. **person_relations（人物关系）**：用户提到的亲密关系人物，如家人、伴侣、好友等
   - 需要包含：人物称呼、关系、重要信息

2. **life_status（生活状态）**：用户的职业、城市、作息、宠物、爱好等
   - 需要包含：具体内容和状态

3. **important_events（重要事件）**：生日、纪念日、人生大事件
   - 需要包含：事件类型、日期、相关人物

4. **emotion_patterns（情绪模式）**：用户在特定时间或话题下的情绪反应规律
   - 需要包含：触发条件、情绪状态

5. **preferences（对话偏好）**：用户喜欢的回应风格
   - 需要包含：偏好类型

请以JSON格式返回结果：
{
    "person_relations": [
        {"relation": "妈妈", "info": "生日是3月15日"}
    ],
    "life_status": {
        "occupation": "程序员",
        "city": "北京",
        "pets": "有一只猫",
        "hobbies": ["阅读", "跑步"]
    },
    "important_events": [
        {"type": "birthday", "name": "妈妈的生日", "date": "03-15", "related_person": "妈妈"}
    ],
    "emotion_patterns": {
        "low_energy_times": ["深夜"],
        "trigger_topics": ["工作压力", "周一"]
    },
    "preferences": {
        "response_style": "倾听而非建议"
    },
    "importance": 8
}

注意事项：
1. 只提取用户明确表达的信息，不要推测
2. 如果没有明显的可提取信息，返回空对象/数组
3. importance 取值 1-10，重要的人生事件取 8-10，一般偏好取 5-7
4. 日期格式：月日用 MM-DD 格式，完整日期用 YYYY-MM-DD 格式
5. 不要提取临时状态（如今天吃了什么）、琐碎日常、随口提的不重要人物"""

PROFILE_EXTRACT_USER_PROMPT_TEMPLATE = """请分析以下对话内容，提取用户的长期记忆信息：

{conversation_text}

请提取人物关系、生活状态、重要事件、情绪模式和对话偏好。"""


# ---------------------------------------------------------------------------
# 长期记忆服务类
# ---------------------------------------------------------------------------

class LongTermMemory:
    """长期记忆服务，永久存储用户画像和重要事件。

    功能：
    1. 用户画像管理 - 性格偏好、兴趣、情绪模式
    2. 重要事件记录 - 生日、纪念日、人生大事件
    3. 记住/忘记规则 - PRD 定义的记住什么/忘记什么
    4. 永不过期 - expires_at 为 None

    注意：
    - 长期记忆永不过期，expires_at 设为 None
    - 用户画像更新是增量式的，不覆盖已有信息
    - 重要度（importance）用于排序，默认为 8
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
    ) -> None:
        """初始化长期记忆服务。

        Args:
            db: 数据库会话
            ai_provider: AI 服务提供者（mock/glm_free/glm）
            zhipu_api_key: 智谱 API Key
        """
        self._db = db
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key

        # AI 服务实例（延迟初始化）
        self._ai_service: MockAIChat | GLMChatService | None = None

        logger.info(
            "[LongTermMemory] 初始化完成，AI Provider: %s",
            ai_provider
        )

    def _get_ai_service(self) -> MockAIChat | GLMChatService:
        """获取 AI 服务实例（延迟初始化）。

        使用 GLM-4-Flash 模型进行信息提取，成本较低。

        Returns:
            AI 服务实例
        """
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-flash",  # 使用便宜的模型
                personality="xiaowen",  # 使用温柔的风格
            )
        return self._ai_service

    # -----------------------------------------------------------------------
    # 用户画像管理
    # -----------------------------------------------------------------------

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """获取用户的完整画像。

        合并所有 person_info 类型的记忆，构建完整的用户画像。

        Args:
            user_id: 用户 ID

        Returns:
            用户画像字典，包含 personality、interests、emotion_patterns、life_status
        """
        stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                AIMemory.memory_type == MEMORY_TYPE_PERSON_INFO,
            )
            .order_by(desc(AIMemory.importance), desc(AIMemory.created_at))
        )
        result = await self._db.execute(stmt)
        memories = result.scalars().all()

        # 合并所有画像信息
        profile: dict[str, Any] = {
            "personality": {
                "preferred_style": None,
                "response_preference": None,
            },
            "interests": [],
            "emotion_patterns": {
                "low_energy_times": [],
                "trigger_topics": [],
            },
            "life_status": {
                "occupation": None,
                "city": None,
                "schedule": None,
                "pets": None,
            },
            "person_relations": [],
        }

        for mem in memories:
            if mem.key_facts:
                # 增量合并 key_facts
                profile = self._merge_profile(profile, mem.key_facts)

        logger.debug(
            "[LongTermMemory] 获取用户画像，用户: %s，记忆数: %d",
            user_id,
            len(memories)
        )

        return profile

    async def update_user_profile(
        self,
        user_id: str,
        profile_data: dict[str, Any],
        source: str = "chat",
    ) -> AIMemory:
        """更新用户画像。

        增量式更新，不覆盖已有信息。先删除旧画像记录再创建合并后的新记录。

        Args:
            user_id: 用户 ID
            profile_data: 画像数据
            source: 来源（chat/manual/diary）

        Returns:
            创建或更新的 AIMemory 对象
        """
        # 获取现有画像
        existing_profile = await self.get_user_profile(user_id)

        # 合并新数据
        merged_profile = self._merge_profile(existing_profile, profile_data)

        # 先删除旧的 person_info 记录，避免累积
        delete_stmt = delete(AIMemory).where(
            AIMemory.user_id == user_id,
            AIMemory.memory_type == MEMORY_TYPE_PERSON_INFO,
        )
        await self._db.execute(delete_stmt)

        # 创建新的合并后的记忆记录
        memory = AIMemory(
            id=str(uuid.uuid4()),
            conversation_id=None,  # 画像不一定关联特定对话
            user_id=user_id,
            memory_type=MEMORY_TYPE_PERSON_INFO,
            content=self._profile_to_content(merged_profile),
            key_facts=merged_profile,
            importance=DEFAULT_IMPORTANCE,
            source=source,
            expires_at=None,  # 永不过期
            access_count=0,
        )

        self._db.add(memory)
        await self._db.flush()

        logger.debug(
            "[LongTermMemory] 更新用户画像，用户: %s，来源: %s",
            user_id,
            source
        )

        return memory

    def _merge_profile(
        self,
        existing: dict[str, Any],
        new_data: dict[str, Any],
    ) -> dict[str, Any]:
        """合并用户画像数据。

        增量合并策略：
        - 列表类型：合并去重
        - 字典类型：递归合并
        - 字符串类型：新值覆盖旧值

        Args:
            existing: 现有画像
            new_data: 新数据

        Returns:
            合并后的画像
        """
        result = existing.copy()

        for key, value in new_data.items():
            if value is None:
                continue

            if key not in result:
                result[key] = value
                continue

            if isinstance(value, dict) and isinstance(result[key], dict):
                # 递归合并字典
                result[key] = self._merge_profile(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                # 合并列表并去重
                combined = result[key] + value
                # 对于字典列表，尝试去重
                if all(isinstance(item, dict) for item in combined):
                    seen = set()
                    unique_list = []
                    for item in combined:
                        # 使用 json 字符串作为去重键
                        item_key = json.dumps(item, sort_keys=True, ensure_ascii=False)
                        if item_key not in seen:
                            seen.add(item_key)
                            unique_list.append(item)
                    result[key] = unique_list
                else:
                    # 简单列表去重
                    result[key] = list(set(combined))
            else:
                # 其他类型：新值覆盖旧值
                result[key] = value

        return result

    def _profile_to_content(self, profile: dict[str, Any]) -> str:
        """将画像字典转换为可读的内容文本。

        Args:
            profile: 画像字典

        Returns:
            可读的内容文本
        """
        parts = []

        # 生活状态
        life_status = profile.get("life_status", {})
        if life_status:
            status_parts = []
            if life_status.get("occupation"):
                status_parts.append(f"职业是{life_status['occupation']}")
            if life_status.get("city"):
                status_parts.append(f"住在{life_status['city']}")
            if life_status.get("pets"):
                status_parts.append(life_status["pets"])
            if status_parts:
                parts.append("生活状态：" + "，".join(status_parts))

        # 兴趣爱好
        interests = profile.get("interests", [])
        if interests:
            parts.append("兴趣爱好：" + "、".join(interests[:5]))

        # 人物关系
        relations = profile.get("person_relations", [])
        if relations:
            rel_parts = []
            for rel in relations[:5]:
                if isinstance(rel, dict):
                    relation = rel.get("relation", "")
                    info = rel.get("info", "")
                    if relation:
                        rel_parts.append(f"{relation}({info})" if info else relation)
                else:
                    rel_parts.append(str(rel))
            if rel_parts:
                parts.append("重要关系：" + "、".join(rel_parts))

        # 情绪模式
        emotion_patterns = profile.get("emotion_patterns", {})
        if emotion_patterns:
            pattern_parts = []
            low_times = emotion_patterns.get("low_energy_times", [])
            if low_times:
                pattern_parts.append(f"{'+'.join(low_times)}容易情绪低落")
            triggers = emotion_patterns.get("trigger_topics", [])
            if triggers:
                pattern_parts.append(f"{'+'.join(triggers)}会触发负面情绪")
            if pattern_parts:
                parts.append("情绪模式：" + "，".join(pattern_parts))

        # 对话偏好
        preferences = profile.get("preferences", {})
        if preferences:
            pref_parts = []
            if preferences.get("response_style"):
                pref_parts.append(f"偏好{preferences['response_style']}")
            if pref_parts:
                parts.append("对话偏好：" + "、".join(pref_parts))

        return "。".join(parts) if parts else "暂无画像信息"

    # -----------------------------------------------------------------------
    # 重要事件管理
    # -----------------------------------------------------------------------

    async def add_important_event(
        self,
        user_id: str,
        event_type: str,
        event_name: str,
        event_date: str,
        related_person: str | None = None,
        reminder: bool = True,
        importance: int = DEFAULT_IMPORTANCE,
        source: str = "manual",
    ) -> AIMemory:
        """添加重要事件。

        Args:
            user_id: 用户 ID
            event_type: 事件类型（birthday/anniversary/milestone）
            event_name: 事件名称
            event_date: 事件日期（MM-DD 或 YYYY-MM-DD）
            related_person: 相关人物（可选）
            reminder: 是否需要提醒
            importance: 重要度（1-10）
            source: 来源（manual/chat）

        Returns:
            创建的 AIMemory 对象
        """
        key_facts = {
            "event_type": event_type,
            "event_name": event_name,
            "event_date": event_date,
            "related_person": related_person,
            "reminder": reminder,
        }

        content = f"{event_name}"
        if related_person:
            content = f"{related_person}的{event_name}"
        content += f"（{event_date}）"

        memory = AIMemory(
            id=str(uuid.uuid4()),
            conversation_id=None,
            user_id=user_id,
            memory_type=MEMORY_TYPE_EVENT,
            content=content,
            key_facts=key_facts,
            importance=max(1, min(10, importance)),
            source=source,
            expires_at=None,  # 永不过期
            access_count=0,
        )

        self._db.add(memory)
        await self._db.flush()

        logger.info(
            "[LongTermMemory] 添加重要事件，用户: %s，事件: %s，日期: %s",
            user_id,
            event_name,
            event_date
        )

        return memory

    async def get_important_events(
        self,
        user_id: str,
        event_type: str | None = None,
    ) -> list[AIMemory]:
        """获取用户的重要事件列表。

        Args:
            user_id: 用户 ID
            event_type: 事件类型过滤（可选）

        Returns:
            AIMemory 对象列表
        """
        stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                AIMemory.memory_type == MEMORY_TYPE_EVENT,
            )
        )

        if event_type:
            # 使用 content 字段匹配事件类型（更安全的查询方式）
            # content 格式为 "{event_name}（{related_person}）" 或类似
            stmt = stmt.where(AIMemory.content.contains(event_type))

        stmt = stmt.order_by(desc(AIMemory.importance), desc(AIMemory.created_at))

        result = await self._db.execute(stmt)
        memories = result.scalars().all()

        logger.debug(
            "[LongTermMemory] 获取重要事件，用户: %s，类型: %s，数量: %d",
            user_id,
            event_type or "全部",
            len(memories)
        )

        return list(memories)

    async def get_upcoming_events(
        self,
        user_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """获取即将到来的重要事件。

        用于提醒和关怀触发。

        Args:
            user_id: 用户 ID
            days: 未来多少天内的事件

        Returns:
            事件列表，包含 days_until 字段
        """
        events = await self.get_important_events(user_id)

        upcoming = []
        now = datetime.now()

        for event in events:
            if not event.key_facts:
                continue

            event_date_str = event.key_facts.get("event_date", "")
            if not event_date_str:
                continue

            try:
                # 解析日期（支持 MM-DD 和 YYYY-MM-DD）
                if len(event_date_str) == 5:  # MM-DD 格式
                    month, day = event_date_str.split("-")
                    event_date = datetime(now.year, int(month), int(day))
                    # 如果已经过去，计算下一年的
                    if event_date < now:
                        event_date = datetime(now.year + 1, int(month), int(day))
                else:  # YYYY-MM-DD 格式
                    event_date = datetime.strptime(event_date_str, "%Y-%m-%d")

                days_until = (event_date - now).days

                if 0 <= days_until <= days:
                    upcoming.append({
                        "id": event.id,
                        "event_type": event.key_facts.get("event_type"),
                        "event_name": event.key_facts.get("event_name"),
                        "event_date": event_date_str,
                        "related_person": event.key_facts.get("related_person"),
                        "reminder": event.key_facts.get("reminder", True),
                        "days_until": days_until,
                        "importance": event.importance,
                    })

            except (ValueError, TypeError) as e:
                logger.warning(
                    "[LongTermMemory] 日期解析失败: %s，事件: %s",
                    event_date_str,
                    event.key_facts.get("event_name")
                )
                continue

        # 按距离天数排序
        upcoming.sort(key=lambda x: x["days_until"])

        return upcoming

    async def delete_event(self, user_id: str, event_id: str) -> bool:
        """删除重要事件。

        Args:
            user_id: 用户 ID
            event_id: 事件 ID

        Returns:
            是否删除成功
        """
        stmt = (
            delete(AIMemory)
            .where(
                AIMemory.id == event_id,
                AIMemory.user_id == user_id,
                AIMemory.memory_type == MEMORY_TYPE_EVENT,
            )
        )

        result = await self._db.execute(stmt)
        await self._db.commit()

        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "[LongTermMemory] 删除重要事件，用户: %s，事件: %s",
                user_id,
                event_id
            )

        return deleted

    # -----------------------------------------------------------------------
    # 记住/忘记规则判断
    # -----------------------------------------------------------------------

    def should_remember(self, content: str) -> tuple[bool, str | None]:
        """判断内容是否值得记住。

        根据 PRD 2.3 定义的记住/忘记规则判断。

        Args:
            content: 待判断的内容

        Returns:
            (是否值得记住, 匹配的类型)
        """
        # 先检查是否应该忘记
        for forget_type, patterns in FORGET_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    logger.debug(
                        "[LongTermMemory] 内容应被忘记，类型: %s，匹配: %s",
                        forget_type,
                        pattern
                    )
                    return False, forget_type

        # 检查是否值得记住
        for remember_type, patterns in REMEMBER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    logger.debug(
                        "[LongTermMemory] 内容值得记住，类型: %s，匹配: %s",
                        remember_type,
                        pattern
                    )
                    return True, remember_type

        # 默认不记住
        return False, None

    # -----------------------------------------------------------------------
    # 从对话中提取
    # -----------------------------------------------------------------------

    async def extract_and_save(
        self,
        user_id: str,
        conversation_id: str | None,
        messages: list[dict[str, str]],
    ) -> dict[str, Any] | None:
        """从对话中提取长期记忆信息。

        使用 AI 分析对话内容，提取用户画像和重要事件信息。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID（可选）
            messages: 对话消息列表

        Returns:
            提取结果字典，包含 profile_updates 和 events；
            如果提取失败返回 None
        """
        if not messages:
            logger.debug(
                "[LongTermMemory] 无消息内容，跳过提取"
            )
            return None

        # 先用规则快速过滤
        conversation_text = self._format_conversation(messages)

        # 检查是否有值得记住的内容
        should_remember_flag, _ = self.should_remember(conversation_text)

        if not should_remember_flag:
            logger.debug(
                "[LongTermMemory] 对话内容不符合记住规则，跳过提取"
            )
            return None

        try:
            # 调用 AI 提取信息
            ai_service = self._get_ai_service()

            prompt = PROFILE_EXTRACT_USER_PROMPT_TEMPLATE.format(
                conversation_text=conversation_text
            )

            context = {
                "history": [],
            }

            response = await ai_service.chat(prompt, context)

            # 解析响应
            result = self._parse_extract_response(response)

            if not result:
                return None

            # 保存提取的信息
            profile_updates = {}
            events_created = []

            # 处理人物关系
            person_relations = result.get("person_relations", [])
            if person_relations:
                profile_updates["person_relations"] = person_relations

            # 处理生活状态
            life_status = result.get("life_status", {})
            if life_status:
                profile_updates["life_status"] = life_status

            # 处理情绪模式
            emotion_patterns = result.get("emotion_patterns", {})
            if emotion_patterns:
                profile_updates["emotion_patterns"] = emotion_patterns

            # 处理对话偏好
            preferences = result.get("preferences", {})
            if preferences:
                profile_updates["preferences"] = preferences

            # 更新用户画像
            if profile_updates:
                await self.update_user_profile(
                    user_id=user_id,
                    profile_data=profile_updates,
                    source="chat",
                )

            # 处理重要事件
            important_events = result.get("important_events", [])
            for event_data in important_events:
                event_type = event_data.get("type", EVENT_TYPE_MILESTONE)
                event_name = event_data.get("name", "")
                event_date = event_data.get("date", "")
                related_person = event_data.get("related_person")

                if event_name and event_date:
                    event = await self.add_important_event(
                        user_id=user_id,
                        event_type=event_type,
                        event_name=event_name,
                        event_date=event_date,
                        related_person=related_person,
                        source="chat",
                        importance=result.get("importance", DEFAULT_IMPORTANCE),
                    )
                    events_created.append({
                        "id": event.id,
                        "event_name": event_name,
                        "event_date": event_date,
                    })

            logger.info(
                "[LongTermMemory] 从对话提取长期记忆，用户: %s，画像更新: %s，事件数: %d",
                user_id,
                bool(profile_updates),
                len(events_created)
            )

            return {
                "profile_updates": profile_updates,
                "events_created": events_created,
            }

        except Exception as e:
            logger.warning(
                "[LongTermMemory] 提取长期记忆失败: %s",
                str(e)
            )
            return None

    # -----------------------------------------------------------------------
    # 记忆检索
    # -----------------------------------------------------------------------

    async def get_memories_for_context(
        self,
        user_id: str,
        max_memories: int = 10,
    ) -> list[dict[str, Any]]:
        """获取用于上下文注入的长期记忆。

        Args:
            user_id: 用户 ID
            max_memories: 最大记忆数量

        Returns:
            记忆列表
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                AIMemory.memory_type.in_([
                    MEMORY_TYPE_LONG_TERM,
                    MEMORY_TYPE_PERSON_INFO,
                    MEMORY_TYPE_EVENT,
                ]),
                # 长期记忆永不过期，但仍然检查以防万一
                (AIMemory.expires_at.is_(None)) | (AIMemory.expires_at > now),
            )
            .order_by(
                desc(AIMemory.importance),
                desc(AIMemory.last_accessed_at),
            )
            .limit(max_memories)
        )

        result = await self._db.execute(stmt)
        memories = result.scalars().all()

        # 更新访问计数
        for mem in memories:
            mem.access_count += 1
            mem.last_accessed_at = now

        if memories:
            await self._db.flush()

        # 格式化返回
        memory_list = []
        for mem in memories:
            memory_list.append({
                "type": mem.memory_type,
                "content": mem.content,
                "importance": mem.importance,
                "key_facts": mem.key_facts,
            })

        logger.debug(
            "[LongTermMemory] 获取上下文记忆，用户: %s，数量: %d",
            user_id,
            len(memory_list)
        )

        return memory_list

    async def get_all_long_term_memories(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """分页获取用户的所有长期记忆。

        用于用户查看和管理自己的记忆。

        Args:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量

        Returns:
            分页结果
        """
        # 计数
        count_stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                AIMemory.memory_type.in_([
                    MEMORY_TYPE_LONG_TERM,
                    MEMORY_TYPE_PERSON_INFO,
                    MEMORY_TYPE_EVENT,
                ]),
            )
        )
        count_result = await self._db.execute(count_stmt)
        total = len(count_result.all())

        # 分页查询
        offset = (page - 1) * page_size
        stmt = (
            select(AIMemory)
            .where(
                AIMemory.user_id == user_id,
                AIMemory.memory_type.in_([
                    MEMORY_TYPE_LONG_TERM,
                    MEMORY_TYPE_PERSON_INFO,
                    MEMORY_TYPE_EVENT,
                ]),
            )
            .order_by(desc(AIMemory.importance), desc(AIMemory.created_at))
            .offset(offset)
            .limit(page_size)
        )

        result = await self._db.execute(stmt)
        memories = result.scalars().all()

        items = []
        for mem in memories:
            items.append({
                "id": mem.id,
                "type": mem.memory_type,
                "content": mem.content,
                "key_facts": mem.key_facts,
                "importance": mem.importance,
                "source": mem.source,
                "created_at": mem.created_at.isoformat() if mem.created_at else None,
                "access_count": mem.access_count,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """删除指定的长期记忆。

        Args:
            user_id: 用户 ID
            memory_id: 记忆 ID

        Returns:
            是否删除成功
        """
        stmt = (
            delete(AIMemory)
            .where(
                AIMemory.id == memory_id,
                AIMemory.user_id == user_id,
                AIMemory.memory_type.in_([
                    MEMORY_TYPE_LONG_TERM,
                    MEMORY_TYPE_PERSON_INFO,
                    MEMORY_TYPE_EVENT,
                ]),
            )
        )

        result = await self._db.execute(stmt)
        await self._db.commit()

        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "[LongTermMemory] 删除长期记忆，用户: %s，记忆: %s",
                user_id,
                memory_id
            )

        return deleted

    # -----------------------------------------------------------------------
    # 私有方法
    # -----------------------------------------------------------------------

    def _format_conversation(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """将消息列表格式化为对话文本。

        Args:
            messages: 消息列表

        Returns:
            格式化后的对话文本
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"AI: {content}")

        return "\n".join(lines)

    def _parse_extract_response(
        self,
        response: str,
    ) -> dict[str, Any] | None:
        """解析 AI 返回的提取响应。

        Args:
            response: AI 返回的文本

        Returns:
            解析后的字典
        """
        if not response:
            return None

        try:
            # 尝试直接解析为 JSON
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, response)

        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.warning(
            "[LongTermMemory] 无法解析 AI 响应为 JSON"
        )

        return None


# ---------------------------------------------------------------------------
# 便捷函数
# ---------------------------------------------------------------------------

def create_long_term_memory(
    db: AsyncSession,
    ai_provider: str = "mock",
    zhipu_api_key: str = "",
) -> LongTermMemory:
    """创建长期记忆服务实例。

    Args:
        db: 数据库会话
        ai_provider: AI 服务提供者
        zhipu_api_key: 智谱 API Key

    Returns:
        LongTermMemory 实例
    """
    return LongTermMemory(
        db=db,
        ai_provider=ai_provider,
        zhipu_api_key=zhipu_api_key,
    )
