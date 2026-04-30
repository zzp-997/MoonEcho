"""匿名身份生成和隔离服务。

实现 modules_design.md 7.5 匿名身份架构隔离：
- 匿名内容只存 anon_id，不存 user_id（帖子表有 user_id 用于软删除和统计）
- user_id → anon_id 映射关系单独加密存储
- 内容查询API只返回 anon_id
- 每个用户在树洞中对应唯一 anon_id

虚拟身份组成：
- 虚拟昵称生成器：形容词 200 + 名词 200 = 40,000 组合
- 气质标签随机分配
- AI 生成小图标替代头像
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AnonymousIdentity, UserAnonMapping
from app.services.crypto import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 虚拟昵称词库
# ---------------------------------------------------------------------------

# 形容词列表（200个）
ADJECTIVES: list[str] = [
    # 温暖类（40个）
    "温柔的", "温暖的", "柔和的", "安静的", "平静的",
    "恬静的", "安详的", "舒适的", "惬意的", "治愈的",
    "亲切的", "友善的", "宽容的", "包容的", "理解的",
    "关怀的", "体贴的", "细腻的", "温柔的", "软糯的",
    "轻盈的", "舒缓的", "宁静的", "祥和的", "安宁的",
    "温馨的", "暖心的", "暖和的", "和煦的", "暖洋洋的",
    "暖融融的", "暖烘烘的", "暖呼呼的", "暖乎乎的", "暖洋洋的",
    "和蔼的", "和善的", "和气的", "和悦的", "和暖的",

    # 自然类（40个）
    "飘落的", "流动的", "清新的", "清澈的", "透明的",
    "纯净的", "晶莹的", "通透的", "清爽的", "清逸的",
    "清幽的", "清静的", "清雅的", "清秀的", "清丽的",
    "飘渺的", "缥缈的", "飘逸的", "飘荡的", "飘飞的",
    "流淌的", "流转的", "飘散的", "飘舞的", "清透的",
    "清明的", "纯洁的", "纯真的", "纯朴的", "纯美的",
    "清涟的", "清芬的", "清润的", "清灵的", "清婉的",
    "清馨的", "清扬的", "清朗的", "清冽的", "清澄的",

    # 夜空类（40个）
    "闪烁的", "闪耀的", "闪亮的", "闪光的", "闪动的",
    "璀璨的", "绚烂的", "绚丽的", "灿烂的", "辉煌的",
    "星辰的", "星光的", "星辉的", "星耀的", "星闪的",
    "月色的", "月光的", "月影的", "月华的", "月辉的",
    "夜色的", "夜幕的", "夜空的", "夜晚的", "夜深的",
    "深夜的", "午夜的", "子夜的", "月夜的", "星夜的",
    "朦胧的", "迷蒙的", "迷离的", "迷幻的", "梦幻的",
    "遐想的", "冥想的", "沉思的", "深思的", "冥思的",

    # 情感类（40个）
    "思念的", "想念的", "牵挂的", "惦记的", "怀念的",
    "眷恋的", "留恋的", "依恋的", "依偎的", "相依的",
    "相守的", "相伴的", "相随的", "相知的", "相惜的",
    "相爱的", "相敬的", "相扶的", "相助的", "相伴的",
    "孤独的", "寂寞的", "孤单的", "孤寂的", "落寞的",
    "忧郁的", "忧伤的", "忧愁的", "忧心的", "忧烦的",
    "悲伤的", "悲痛的", "悲愁的", "悲凉的", "悲怆的",
    "惆怅的", "怅然的", "怅惘的", "怅恨的", "怅怀的",

    # 独特类（40个）
    "神秘的", "神奇的", "神妙的", "神异的", "神灵的",
    "奇妙的", "奇幻的", "奇特的", "奇异的", "奇丽的",
    "独特的", "独有的", "独到的", "独创的", "独立的",
    "自由的", "自在的", "自然的", "自如的", "自若的",
    "超然的", "超脱的", "超逸的", "超凡的", "超俗的",
    "淡然的", "淡定的", "淡泊的", "淡雅的", "淡静的",
    "随性的", "随意的", "随缘的", "随心的", "随情的",
    "洒脱的", "飘逸的", "潇洒的", "洒脱的", "飘逸的",
]

# 名词列表（200个）
NOUNS: list[str] = [
    # 天体类（40个）
    "月亮", "星星", "流星", "彗星", "行星",
    "银河", "星云", "星尘", "星光", "月影",
    "月华", "月辉", "月光", "夜空", "星夜",
    "星辰", "星河", "星空", "宇宙", "苍穹",
    "天际", "天边", "天涯", "天穹", "天幕",
    "朝阳", "夕阳", "落日", "朝霞", "晚霞",
    "彩虹", "云朵", "白云", "彩云", "流云",
    "云霞", "云烟", "云雾", "云海", "云天",

    # 自然类（40个）
    "森林", "大海", "湖泊", "溪流", "河流",
    "山川", "山谷", "山峦", "山峰", "山崖",
    "瀑布", "泉水", "水滴", "雨滴", "雪花",
    "冰晶", "霜花", "露珠", "雾气", "烟雨",
    "微风", "清风", "和风", "晚风", "晨风",
    "夜风", "春风", "秋风", "冬雪", "花瓣",
    "树叶", "落叶", "种子", "花蕾", "青草",
    "绿植", "竹子", "松树", "梅枝", "荷塘",

    # 生物类（40个）
    "蝴蝶", "萤火虫", "蜻蜓", "蜜蜂", "飞鸟",
    "夜莺", "燕子", "海鸥", "白鹭", "天鹅",
    "游鱼", "海豚", "鲸鱼", "海龟", "珊瑚",
    "猫咪", "小猫", "兔子", "小鹿", "松鼠",
    "狐狸", "刺猬", "海獭", "水母", "章鱼",
    "蜗牛", "海星", "贝壳", "珍珠", "珊瑚",
    "鹦鹉", "画眉", "百灵", "黄鹂", "杜鹃",
    "知更鸟", "蓝鸟", "喜鹊", "凤凰", "仙鹤",

    # 抽象类（40个）
    "时光", "岁月", "流年", "光阴", "瞬间",
    "记忆", "思念", "回忆", "梦想", "希望",
    "光芒", "光辉", "光影", "光束", "晨曦",
    "影子", "身影", "背影", "足迹", "痕迹",
    "音符", "旋律", "和弦", "节拍", "乐章",
    "诗句", "文字", "篇章", "故事", "童话",
    "梦境", "幻想", "想象", "灵感", "秘密",
    "心事", "心愿", "心语", "心扉", "心弦",

    # 情感类（40个）
    "旅人", "行者", "过客", "归人", "游子",
    "守望者", "倾听者", "观察者", "记录者", "思考者",
    "梦想家", "幻想家", "冒险家", "探索者", "追寻者",
    "收藏家", "守护者", "陪伴者", "安慰者", "治愈者",
    "沉默者", "独行者", "流浪者", "漂泊者", "羁旅者",
    "孤独者", "寂寞者", "忧郁者", "惆怅者", "悲伤者",
    "追风者", "逐梦者", "追光者", "追星人", "望月者",
    "观星人", "听风者", "寻梦者", "造梦者", "织梦者",
]

# 气质标签列表
PERSONA_TAGS: list[str] = [
    "倾听者", "观察者", "思考者", "沉默者", "独行侠",
    "追风者", "逐梦者", "守望者", "记录者", "漂泊者",
    "治愈系", "温柔派", "暖萌系", "安静型", "内敛型",
    "文艺范", "浪漫派", "梦幻系", "治愈派", "暖心派",
    "孤独者", "忧郁者", "惆怅者", "沉默者", "安静者",
    "夜行者", "星尘客", "月光族", "云朵控", "风信子",
    "萤火虫", "小星星", "月光宝盒", "星河旅人", "宇宙漫步者",
    "时光收藏家", "记忆保管员", "心事收纳者", "情绪观察家", "故事收集者",
]


# ---------------------------------------------------------------------------
# 匿名身份服务接口协议
# ---------------------------------------------------------------------------

class AnonymousIdentityProtocol(Protocol):
    """匿名身份服务接口协议。"""

    async def get_or_create_treehole_identity(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> AnonymousIdentity:
        """获取或创建用户在树洞场景的匿名身份。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            AnonymousIdentity 实例
        """
        ...

    async def encrypt_user_mapping(
        self,
        user_id: str,
        anon_id: str,
    ) -> str:
        """加密用户ID与匿名ID的映射关系。

        Args:
            user_id: 用户ID
            anon_id: 匿名身份ID

        Returns:
            加密后的映射字符串
        """
        ...

    async def decrypt_user_mapping(
        self,
        encrypted_mapping: str,
    ) -> dict[str, str]:
        """解密用户ID与匿名ID的映射关系。

        Args:
            encrypted_mapping: 加密的映射字符串

        Returns:
            包含 user_id 和 anon_id 的字典
        """
        ...


# ---------------------------------------------------------------------------
# 匿名身份服务实现
# ---------------------------------------------------------------------------

class AnonymousIdentityService:
    """匿名身份生成和隔离服务。

    实现：
    1. 虚拟昵称生成器（形容词 200 + 名词 200 = 40,000 组合）
    2. 气质标签随机分配
    3. 匿名身份隔离架构
    4. AI 生成小图标（调用图片服务）

    使用示例：
        service = AnonymousIdentityService(settings)
        anon_identity = await service.get_or_create_treehole_identity(user_id, db)
    """

    # 场景常量
    SCENE_TREEHOLE = "treehole"
    SCENE_SQUARE = "square"

    def __init__(
        self,
        settings: Any,
        encryption_key: str | None = None,
    ) -> None:
        """初始化匿名身份服务。

        Args:
            settings: 应用配置
            encryption_key: 加密密钥（可选，默认使用 settings 中的密钥）
        """
        self._settings = settings
        self._encryption_key = encryption_key or getattr(
            settings, "encryption_key", "default_anon_encryption_key"
        )

        # 已使用昵称缓存（避免重复，使用 Redis 或内存）
        self._used_nicknames: set[str] = set()

        logger.info("[AnonymousIdentityService] 初始化完成")

    # =========================================================================
    # 虚拟身份生成
    # =========================================================================

    def generate_nickname(self) -> str:
        """生成虚拟昵称。

        从形容词和名词词库中随机组合，共 40,000 种可能。

        Returns:
            生成的虚拟昵称，如「温柔的月亮」
        """
        # 随机选择形容词和名词
        adjective = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)

        # 组合昵称
        nickname = f"{adjective}{noun}"

        # 检查是否已使用（内存检查，生产环境应使用 Redis）
        if nickname in self._used_nicknames:
            # 添加随机后缀确保唯一
            suffix = str(random.randint(1, 99))
            nickname = f"{nickname}{suffix}"

        self._used_nicknames.add(nickname)
        return nickname

    def generate_persona_tag(self) -> str:
        """随机分配气质标签。

        Returns:
            气质标签，如「倾听者」
        """
        return random.choice(PERSONA_TAGS)

    async def generate_avatar_url(self) -> str:
        """生成 AI 小图标 URL。

        使用预设图标或调用 AI 图片生成服务。

        Returns:
            小图标 URL
        """
        # TODO: 接入 AI 图片生成服务
        # 目前使用预设图标集合
        avatar_styles = [
            "moon", "star", "cloud", "rainbow", "aurora",
            "flower", "leaf", "butterfly", "bird", "wave",
        ]
        style = random.choice(avatar_styles)
        # 返回预设图标的相对路径
        return f"/static/avatars/anon/{style}.svg"

    async def create_anonymous_identity(
        self,
        user_id: str,
        scene: str = SCENE_TREEHOLE,
        db: AsyncSession | None = None,
    ) -> AnonymousIdentity:
        """创建新的匿名身份。

        安全设计（PRD 7.5 匿名身份架构隔离）：
        - encrypted_user_id: 加密存储的用户ID，数据库泄露后无法直接关联

        Args:
            user_id: 用户ID
            scene: 使用场景
            db: 数据库会话（可选）

        Returns:
            新创建的 AnonymousIdentity 实例
        """
        # 生成虚拟身份组件
        nickname = self.generate_nickname()
        persona_tag = self.generate_persona_tag()
        avatar_url = await self.generate_avatar_url()

        # 加密存储用户ID
        encrypted_user_id = encrypt_data(user_id)

        # 创建匿名身份记录
        anon_identity = AnonymousIdentity(
            id=str(uuid.uuid4()),
            encrypted_user_id=encrypted_user_id,
            anon_nickname=nickname,
            anon_avatar_url=avatar_url,
            persona_type=persona_tag,
        )

        if db is not None:
            db.add(anon_identity)
            await db.flush()

        logger.info(
            "[AnonymousIdentityService] 创建匿名身份，用户: %s，昵称: %s，场景: %s",
            user_id, nickname, scene
        )

        return anon_identity

    # =========================================================================
    # 身份映射管理
    # =========================================================================

    async def get_or_create_treehole_identity(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> AnonymousIdentity:
        """获取或创建用户在树洞场景的匿名身份。

        每个用户在树洞中对应唯一 anon_id。

        Args:
            user_id: 用户ID
            db: 数据库会话

        Returns:
            AnonymousIdentity 实例
        """
        # 计算用户ID哈希（用于快速查询，不暴露真实ID）
        user_id_hash = self._compute_user_id_hash(user_id)

        # 查询现有映射（通过哈希查询，满足匿名隔离要求）
        stmt = select(UserAnonMapping).where(
            UserAnonMapping.user_id_hash == user_id_hash,
            UserAnonMapping.scene == self.SCENE_TREEHOLE,
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if mapping:
            # 已存在映射，获取匿名身份
            anon_stmt = select(AnonymousIdentity).where(
                AnonymousIdentity.id == mapping.anon_identity_id,
                AnonymousIdentity.deleted_at.is_(None),
            )
            anon_result = await db.execute(anon_stmt)
            anon_identity = anon_result.scalar_one_or_none()

            if anon_identity:
                return anon_identity

        # 创建新的匿名身份和映射
        anon_identity = await self.create_anonymous_identity(
            user_id=user_id,
            scene=self.SCENE_TREEHOLE,
            db=db,
        )

        # 创建映射关系（加密存储用户ID，满足匿名隔离要求）
        new_mapping = UserAnonMapping(
            id=str(uuid.uuid4()),
            user_id_hash=self._compute_user_id_hash(user_id),
            encrypted_user_id=encrypt_data(user_id),
            anon_identity_id=anon_identity.id,
            scene=self.SCENE_TREEHOLE,
        )
        db.add(new_mapping)

        # 注意：加密映射关系当前仅用于日志记录和审计
        # 若需要存储加密映射，需要在 UserAnonMapping 模型中添加 encrypted_mapping 字段
        # 当前模型设计通过 anon_identity_id 间接关联，满足基本匿名隔离需求
        encrypted_mapping = await self.encrypt_user_mapping(
            user_id, anon_identity.id
        )
        logger.debug(
            "[AnonymousIdentityService] 创建映射，加密数据已生成（长度: %d），用于审计记录",
            len(encrypted_mapping)
        )

        return anon_identity

    async def get_anonymous_identity(
        self,
        anon_id: str,
        db: AsyncSession,
    ) -> AnonymousIdentity | None:
        """获取匿名身份信息。

        Args:
            anon_id: 匿名身份ID
            db: 数据库会话

        Returns:
            AnonymousIdentity 实例或 None
        """
        stmt = select(AnonymousIdentity).where(
            AnonymousIdentity.id == anon_id,
            AnonymousIdentity.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_id_by_anon_id(
        self,
        anon_id: str,
        db: AsyncSession,
    ) -> str | None:
        """通过匿名身份ID反查用户ID（管理后台专用）。

        安全设计：
        - 此方法需要二次认证才能调用
        - 返回解密后的真实用户ID

        Args:
            anon_id: 匿名身份ID
            db: 数据库会话

        Returns:
            用户ID或None
        """
        stmt = select(AnonymousIdentity).where(
            AnonymousIdentity.id == anon_id,
        )
        result = await db.execute(stmt)
        anon_identity = result.scalar_one_or_none()

        if not anon_identity:
            return None

        # 解密加密的用户ID
        try:
            return decrypt_data(anon_identity.encrypted_user_id)
        except Exception as e:
            logger.error(
                "[AnonymousIdentityService] 解密用户ID失败: %s",
                str(e)
            )
            return None

    # =========================================================================
    # 加密映射关系
    # =========================================================================

    async def encrypt_user_mapping(
        self,
        user_id: str,
        anon_id: str,
    ) -> str:
        """加密用户ID与匿名ID的映射关系。

        使用 AES 加密存储，确保即使数据库泄露也无法直接关联。

        Args:
            user_id: 用户ID
            anon_id: 匿名身份ID

        Returns:
            加密后的映射字符串
        """
        mapping_data = {
            "user_id": user_id,
            "anon_id": anon_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 使用加密服务
        try:
            encrypted = encrypt_data(
                json.dumps(mapping_data),
                self._encryption_key,
            )
            return encrypted
        except Exception as e:
            logger.error(
                "[AnonymousIdentityService] 加密映射失败: %s",
                str(e)
            )
            # 降级：使用哈希存储
            return self._hash_mapping(user_id, anon_id)

    def _hash_mapping(self, user_id: str, anon_id: str) -> str:
        """使用哈希存储映射（降级方案）。

        注意：哈希方案无法解密，仅供审计校验使用。
        若需可逆加密，应确保加密服务正常工作。

        Args:
            user_id: 用户ID
            anon_id: 匿名身份ID

        Returns:
            哈希字符串（不可逆）
        """
        data = f"{user_id}:{anon_id}:{self._encryption_key}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def decrypt_user_mapping(
        self,
        encrypted_mapping: str,
    ) -> dict[str, str]:
        """解密用户ID与匿名ID的映射关系。

        Args:
            encrypted_mapping: 加密的映射字符串

        Returns:
            包含 user_id 和 anon_id 的字典
        """
        try:
            decrypted = decrypt_data(
                encrypted_mapping,
                self._encryption_key,
            )
            return json.loads(decrypted)
        except Exception as e:
            logger.error(
                "[AnonymousIdentityService] 解密映射失败: %s",
                str(e)
            )
            return {}

    # =========================================================================
    # 隔离性检查
    # =========================================================================

    def _compute_user_id_hash(self, user_id: str) -> str:
        """计算用户ID的哈希值（加盐）。

        用于快速查询映射关系，不暴露真实用户ID。

        Args:
            user_id: 用户ID

        Returns:
            SHA-256 哈希值
        """
        data = f"{self._encryption_key}:{user_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def check_anonymity_isolation(
        self,
        user_id: str,
        anon_id: str,
        db: AsyncSession,
    ) -> bool:
        """检查匿名身份是否与用户真实身份隔离。

        确保匿名互动不推到实名通知流。

        Args:
            user_id: 用户ID
            anon_id: 匿名身份ID
            db: 数据库会话

        Returns:
            是否隔离
        """
        # 计算用户ID哈希
        user_id_hash = self._compute_user_id_hash(user_id)

        # 检查映射关系是否存在（通过哈希查询）
        stmt = select(UserAnonMapping).where(
            UserAnonMapping.user_id_hash == user_id_hash,
            UserAnonMapping.anon_identity_id == anon_id,
            UserAnonMapping.scene == self.SCENE_TREEHOLE,
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            logger.warning(
                "[AnonymousIdentityService] 隔离检查失败，映射不存在，匿名ID: %s",
                anon_id
            )
            return False

        return True

    async def validate_anon_access(
        self,
        user_id: str,
        anon_id: str,
        db: AsyncSession,
    ) -> bool:
        """验证用户是否有权使用该匿名身份。

        Args:
            user_id: 用户ID
            anon_id: 匿名身份ID
            db: 数据库会话

        Returns:
            是否有权限
        """
        # 计算用户ID哈希
        user_id_hash = self._compute_user_id_hash(user_id)

        stmt = select(UserAnonMapping).where(
            UserAnonMapping.user_id_hash == user_id_hash,
            UserAnonMapping.anon_identity_id == anon_id,
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        return mapping is not None


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_anonymous_identity_service(
    settings: Any,
    encryption_key: str | None = None,
) -> AnonymousIdentityService:
    """创建匿名身份服务实例。

    Args:
        settings: 应用配置
        encryption_key: 加密密钥（可选）

    Returns:
        AnonymousIdentityService 实例
    """
    return AnonymousIdentityService(
        settings=settings,
        encryption_key=encryption_key,
    )
