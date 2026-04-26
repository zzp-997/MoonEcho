"""初始化管理员账户。

创建默认的超级管理员账户，用于首次部署后登录管理后台。

环境变量：
- ADMIN_INITIAL_USERNAME: 管理员用户名（默认: superadmin）
- ADMIN_INITIAL_PASSWORD: 管理员密码（默认: admin123456）
- ADMIN_INITIAL_NICKNAME: 管理员昵称（默认: 超级管理员）

使用方式：
    # 在应用启动时调用
    from app.services.admin.init_admin import init_admin_account
    await init_admin_account(db_session, settings)

    # 或单独执行
    python -m app.services.admin.init_admin
"""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.services.admin.admin_service import AdminAuthService

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_USERNAME = "superadmin"
DEFAULT_PASSWORD = "admin123456"  # 生产环境务必修改
DEFAULT_NICKNAME = "超级管理员"


async def init_admin_account(db: AsyncSession) -> Admin | None:
    """初始化管理员账户。

    如果管理员表为空，创建默认的超级管理员账户。

    Args:
        db: 数据库会话

    Returns:
        创建的管理员对象，若已存在则返回 None
    """
    # 检查是否已有管理员
    stmt = select(Admin).limit(1)
    result = await db.execute(stmt)
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        logger.info("管理员账户已存在，无需初始化")
        return None

    # 从环境变量获取配置
    username = os.getenv("ADMIN_INITIAL_USERNAME", DEFAULT_USERNAME)
    password = os.getenv("ADMIN_INITIAL_PASSWORD", DEFAULT_PASSWORD)
    nickname = os.getenv("ADMIN_INITIAL_NICKNAME", DEFAULT_NICKNAME)

    # 创建超级管理员
    password_hash = AdminAuthService.hash_password(password)

    admin = Admin(
        id=str(uuid4()),
        username=username,
        password_hash=password_hash,
        nickname=nickname,
        role="super_admin",
        is_active=True,
    )

    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    logger.warning(
        "已创建初始超级管理员账户！"
        "用户名: %s"
        "请立即登录并修改默认密码！"
        "如果使用了环境变量配置的密码，请确保已妥善保管。",
        username,
    )
    # 仅在开发环境输出密码提示
    if os.getenv("ENVIRONMENT", "development").lower() not in ("production", "prod"):
        logger.info("默认密码: %s（仅限开发环境，生产环境请使用环境变量配置）", password)

    return admin


async def main() -> None:
    """独立执行初始化脚本。"""
    from app.core.config import load_settings
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    settings = load_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with session_factory() as db:
        admin = await init_admin_account(db)
        if admin:
            print(f"已创建管理员账户: {admin.username}")
        else:
            print("管理员账户已存在")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())