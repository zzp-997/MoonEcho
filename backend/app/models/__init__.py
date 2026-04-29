"""ORM 模型包。

统一导出所有模型类，确保 SQLAlchemy 元数据注册完整。
导入顺序按外键依赖排列：无外键依赖的模型优先导入。
"""

# 基类（必须最先导入，提供 Base / Mixin）
from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin

# 用户模块（被其他模块外键引用，优先导入）
from .user import User, UserTag, AnonymousIdentity, UserAnonMapping

# 情绪日记模块
from .diary import EmotionDiary

# 树洞模块
from .treehole import TreeholePost, TreeholeComment

# 动态广场模块
from .post import Post, PostComment, PostLike, PostFavorite, PostFollow

# 聊天模块
from .chat import Friendship, FriendRequest, UserBlock, Conversation, ChatMessage

# AI 对话模块
from .ai import AIConversation, AIMessage, AIMemory

# 通知模块
from .notification import Notification, PushRecord

# 管理后台模块（被 report 外键引用）
from .admin import Admin, AdminLog

# 举报模块
from .report import Report

# 情绪周报模块
from .weekly_report import WeeklyReport

# 节日模块
from .holiday import Holiday, UserHoliday

__all__ = [
    # 基类
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # 用户
    "User",
    "UserTag",
    "AnonymousIdentity",
    "UserAnonMapping",
    # 情绪日记
    "EmotionDiary",
    # 树洞
    "TreeholePost",
    "TreeholeComment",
    # 动态广场
    "Post",
    "PostComment",
    "PostLike",
    "PostFavorite",
    "PostFollow",
    # 聊天
    "Friendship",
    "FriendRequest",
    "UserBlock",
    "Conversation",
    "ChatMessage",
    # AI 对话
    "AIConversation",
    "AIMessage",
    "AIMemory",
    # 通知
    "Notification",
    "PushRecord",
    # 管理后台
    "Admin",
    "AdminLog",
    # 举报
    "Report",
    # 情绪周报
    "WeeklyReport",
    # 节日
    "Holiday",
    "UserHoliday",
]
