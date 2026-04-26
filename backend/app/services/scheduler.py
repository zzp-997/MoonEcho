"""调度器管理模块。

管理后台定时任务：
- 周报生成：每周日晚 22:00 静默生成
- 晚安问候：每日 22:30 扫描活跃用户，22:30-23:30 随机发送
- 早安问候：每日 7:00 扫描活跃用户，7:00-8:00 发送
- 情绪低谷关怀：每日 10:00 检查连续 2 天未登录+近期情绪负面用户
- 节日问候：节日当天 10:00 发送
- 重要事件跟进：每日 20:00 检查当天有重要事件的用户
- 社交能量重置：每日 00:00 重置所有用户社交能量为 50

使用 APScheduler 实现后台定时任务调度。
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

if TYPE_CHECKING:
    from app.core.config import AppSettings

logger = logging.getLogger(__name__)


class SchedulerManager:
    """调度器管理器。

    管理所有后台定时任务：
    - 周报生成任务：每周日晚 22:00 执行
    - 晚安问候任务：每日 22:30 执行
    - 早安问候任务：每日 7:00 执行
    - 情绪低谷关怀任务：每日 10:00 执行
    - 节日问候任务：每日 10:00 执行
    - 重要事件跟进任务：每日 20:00 执行
    - 社交能量重置任务：每日 00:00 执行
    """

    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()
        self.started_count = 0
        self.shutdown_count = 0
        self.is_running = False

    def start(self) -> None:
        """启动调度器。"""
        self.started_count += 1
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("[Scheduler] 调度器已启动")
        self.is_running = True

    def shutdown(self) -> None:
        """关闭调度器。"""
        self.shutdown_count += 1
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("[Scheduler] 调度器已关闭")
        self.is_running = False

    def add_weekly_report_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
    ) -> None:
        """添加周报生成定时任务。

        每周日晚 22:00 执行，为本周有日记的用户生成周报。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
        """
        from app.services.weekly_report_service import WeeklyReportService

        async def generate_weekly_reports() -> None:
            """执行周报生成任务。"""
            logger.info("[Scheduler] 开始执行周报生成任务")
            start_time = datetime.now(timezone.utc)

            # 获取分布式锁，避免多实例重复执行
            lock_key = "scheduler:weekly_report_lock"
            lock_acquired = False

            try:
                # 尝试获取锁（30分钟过期）
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行周报生成任务，跳过")
                        return

                service = WeeklyReportService(
                    settings=settings,
                    redis=redis_client,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.batch_generate_reports(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 周报生成任务完成，成功: %d，失败: %d，跳过: %d，耗时: %.2f 秒",
                    stats["success"],
                    stats["failed"],
                    stats["skipped"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 周报生成任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                # 释放锁
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器，用于在同步调度器中执行异步任务。"""
            try:
                # 尝试获取现有的 event loop
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # 没有运行中的 loop，创建新的
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(generate_weekly_reports())
                finally:
                    loop.close()
            else:
                # 已有运行中的 loop，创建任务在其中执行
                asyncio.ensure_future(generate_weekly_reports(), loop=loop)

        # 每周日晚 22:00 执行（周日是 day_of_week=6）
        trigger = CronTrigger(
            day_of_week="sun",
            hour=22,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="weekly_report_generation",
            name="周报生成任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 周报生成任务已添加，执行时间：每周日晚 22:00")

    def add_good_night_care_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加晚安问候定时任务。

        每日 22:30 执行，扫描过去 24 小时内活跃的用户，
        在 22:30-23:30 时间窗口内随机发送晚安问候。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        from app.services.care_service import CareService

        async def send_good_night_care() -> None:
            """执行晚安问候任务。"""
            logger.info("[Scheduler] 开始执行晚安问候任务")
            start_time = datetime.now(timezone.utc)

            # 获取分布式锁
            lock_key = "scheduler:good_night_care_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行晚安问候任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=push_provider,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.send_good_night_care(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 晚安问候任务完成，成功: %d，跳过: %d，失败: %d，耗时: %.2f 秒",
                    stats["success"],
                    stats["skipped"],
                    stats["failed"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 晚安问候任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_good_night_care())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(send_good_night_care(), loop=loop)

        # 每日 22:30 执行
        trigger = CronTrigger(
            hour=22,
            minute=30,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="good_night_care",
            name="晚安问候任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 晚安问候任务已添加，执行时间：每日 22:30")

    def add_good_morning_care_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加早安问候定时任务。

        每日 7:00 执行，扫描过去 24 小时内活跃的用户发送早安问候。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        from app.services.care_service import CareService

        async def send_good_morning_care() -> None:
            """执行早安问候任务。"""
            logger.info("[Scheduler] 开始执行早安问候任务")
            start_time = datetime.now(timezone.utc)

            lock_key = "scheduler:good_morning_care_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行早安问候任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=push_provider,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.send_good_morning_care(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 早安问候任务完成，成功: %d，跳过: %d，失败: %d，耗时: %.2f 秒",
                    stats["success"],
                    stats["skipped"],
                    stats["failed"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 早安问候任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_good_morning_care())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(send_good_morning_care(), loop=loop)

        # 每日 7:00 执行
        trigger = CronTrigger(
            hour=7,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="good_morning_care",
            name="早安问候任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 早安问候任务已添加，执行时间：每日 7:00")

    def add_low_mood_care_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加情绪低谷关怀定时任务。

        每日 10:00 执行，检查连续 2 天未登录且近期情绪负面的用户。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        from app.services.care_service import CareService

        async def send_low_mood_care() -> None:
            """执行情绪低谷关怀任务。"""
            logger.info("[Scheduler] 开始执行情绪低谷关怀任务")
            start_time = datetime.now(timezone.utc)

            lock_key = "scheduler:low_mood_care_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行情绪低谷关怀任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=push_provider,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.send_low_mood_care(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 情绪低谷关怀任务完成，成功: %d，跳过: %d，失败: %d，耗时: %.2f 秒",
                    stats["success"],
                    stats["skipped"],
                    stats["failed"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 情绪低谷关怀任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_low_mood_care())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(send_low_mood_care(), loop=loop)

        # 每日 10:00 执行
        trigger = CronTrigger(
            hour=10,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="low_mood_care",
            name="情绪低谷关怀任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 情绪低谷关怀任务已添加，执行时间：每日 10:00")

    def add_holiday_care_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加节日问候定时任务。

        每日 10:00 执行，检查今天是否有节日，有则发送问候。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        from app.services.care_service import CareService

        async def send_holiday_care() -> None:
            """执行节日问候任务。"""
            logger.info("[Scheduler] 开始执行节日问候任务")
            start_time = datetime.now(timezone.utc)

            lock_key = "scheduler:holiday_care_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行节日问候任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=push_provider,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    # 发送系统节日问候
                    stats = await service.send_holiday_care(db=db)
                    # 发送用户自定义节日问候
                    user_stats = await service.send_user_holiday_care(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 节日问候任务完成，系统节日数: %d，系统成功: %d，"
                    "用户节日数: %d，用户成功: %d，耗时: %.2f 秒",
                    stats.get("holidays", 0),
                    stats["success"],
                    user_stats.get("holidays", 0),
                    user_stats["success"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 节日问候任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_holiday_care())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(send_holiday_care(), loop=loop)

        # 每日 10:00 执行
        trigger = CronTrigger(
            hour=10,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="holiday_care",
            name="节日问候任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 节日问候任务已添加，执行时间：每日 10:00")

    def add_event_follow_care_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加重要事件跟进定时任务。

        每日 20:00 执行，检查用户提到的重要事件，在事件当天发送跟进。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        from app.services.care_service import CareService

        async def send_event_follow_care() -> None:
            """执行重要事件跟进任务。"""
            logger.info("[Scheduler] 开始执行重要事件跟进任务")
            start_time = datetime.now(timezone.utc)

            lock_key = "scheduler:event_follow_care_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行重要事件跟进任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=push_provider,
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.send_event_follow_care(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 重要事件跟进任务完成，事件数: %d，成功: %d，跳过: %d，失败: %d，耗时: %.2f 秒",
                    stats.get("events", 0),
                    stats["success"],
                    stats["skipped"],
                    stats["failed"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 重要事件跟进任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(send_event_follow_care())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(send_event_follow_care(), loop=loop)

        # 每日 20:00 执行
        trigger = CronTrigger(
            hour=20,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="event_follow_care",
            name="重要事件跟进任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 重要事件跟进任务已添加，执行时间：每日 20:00")

    def add_social_energy_reset_job(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
    ) -> None:
        """添加社交能量重置定时任务。

        每日 00:00 执行，将所有用户的社交能量重置为 50。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
        """
        from app.services.care_service import CareService

        async def reset_social_energy() -> None:
            """执行社交能量重置任务。"""
            logger.info("[Scheduler] 开始执行社交能量重置任务")
            start_time = datetime.now(timezone.utc)

            lock_key = "scheduler:social_energy_reset_lock"
            lock_acquired = False

            try:
                if redis_client:
                    lock_acquired = await redis_client.set(
                        lock_key, "1", nx=True, ex=1800
                    )
                    if not lock_acquired:
                        logger.info("[Scheduler] 其他实例正在执行社交能量重置任务，跳过")
                        return

                service = CareService(
                    settings=settings,
                    redis=redis_client,
                    push_provider=None,  # 重置任务不需要推送服务
                    ai_provider=settings.ai_provider,
                    zhipu_api_key=settings.zhipu_api_key,
                )

                async with db_session_factory() as db:
                    stats = await service.reset_social_energy(db=db)

                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "[Scheduler] 社交能量重置任务完成，影响用户数: %d，耗时: %.2f 秒",
                    stats["success"],
                    elapsed,
                )

            except Exception as e:
                logger.error(
                    "[Scheduler] 社交能量重置任务失败: %s",
                    str(e),
                    exc_info=True,
                )
            finally:
                if lock_acquired and redis_client:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.warning("[Scheduler] 释放锁失败: %s", str(e))

        def job_wrapper() -> None:
            """任务包装器。"""
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(reset_social_energy())
                finally:
                    loop.close()
            else:
                asyncio.ensure_future(reset_social_energy(), loop=loop)

        # 每日 00:00 执行
        trigger = CronTrigger(
            hour=0,
            minute=0,
            timezone="Asia/Shanghai",
        )

        self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id="social_energy_reset",
            name="社交能量重置任务",
            replace_existing=True,
        )

        logger.info("[Scheduler] 社交能量重置任务已添加，执行时间：每日 00:00")

    def add_all_care_jobs(
        self,
        settings: "AppSettings",
        db_session_factory,
        redis_client,
        push_provider,
    ) -> None:
        """添加所有关怀相关定时任务。

        一次性添加所有关怀推送相关任务。

        Args:
            settings: 应用配置
            db_session_factory: 数据库会话工厂
            redis_client: Redis 客户端
            push_provider: 推送服务提供者
        """
        self.add_good_night_care_job(settings, db_session_factory, redis_client, push_provider)
        self.add_good_morning_care_job(settings, db_session_factory, redis_client, push_provider)
        self.add_low_mood_care_job(settings, db_session_factory, redis_client, push_provider)
        self.add_holiday_care_job(settings, db_session_factory, redis_client, push_provider)
        self.add_event_follow_care_job(settings, db_session_factory, redis_client, push_provider)
        self.add_social_energy_reset_job(settings, db_session_factory, redis_client)

        logger.info("[Scheduler] 所有关怀任务已添加")


def create_scheduler_manager() -> SchedulerManager:
    """创建调度器管理器实例。"""
    return SchedulerManager()
