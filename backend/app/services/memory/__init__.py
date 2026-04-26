"""记忆系统模块。

提供短期记忆（Redis）、中期记忆（数据库）和长期记忆的统一管理。

三层记忆架构（PRD 2.3）：
- 短期记忆：最近5轮对话 + 当前上下文，Redis存储，24小时TTL
- 中期记忆：最近30天对话摘要 + 关键事实，MySQL存储，30天滚动
- 长期记忆：用户画像 + 重要事件 + 人物关系，MySQL存储，永久保存
"""

from app.services.memory.short_term import ShortTermMemory
from app.services.memory.mid_term import MidTermMemory, create_mid_term_memory
from app.services.memory.long_term import LongTermMemory, create_long_term_memory

__all__ = [
    "ShortTermMemory",
    "MidTermMemory",
    "create_mid_term_memory",
    "LongTermMemory",
    "create_long_term_memory",
]
