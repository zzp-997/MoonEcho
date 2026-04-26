"""情绪周报服务模块。

核心业务逻辑层，封装以下能力：
- 周报生成（基于本周日记数据分析）
- 周报缓存（Redis 7天有效期）
- 周报历史查询
- 定时任务支持（每周日晚22:00生成）
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import AppSettings
from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.diary import EmotionDiary
from app.models.weekly_report import WeeklyReport
from app.schemas.diary import EMOTION_TONE_META
from app.schemas.weekly_report import (
    EmptyWeeklyReportResponse,
    WeeklyReportGenerateRequest,
    WeeklyReportResponse,
)
from app.services.ai_chat import GLMChatService, create_ai_chat_service
from app.services.encryption import decrypt_content_server_side, is_encrypted_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Redis Key 定义
# ---------------------------------------------------------------------------

def _weekly_report_cache_key(user_id: str, week_start: str) -> str:
    """周报缓存存储 key。"""
    return f"diary:report:{user_id}:{week_start}"


def _get_week_start(target_date: date | None = None) -> date:
    """获取本周起始日期（周一）。

    Args:
        target_date: 目标日期，默认为今天

    Returns:
        本周周一的日期
    """
    if target_date is None:
        target_date = date.today()
    # weekday(): 周一=0, 周日=6
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


def _get_week_end(week_start: date) -> date:
    """获取本周结束日期（周日）。"""
    return week_start + timedelta(days=6)


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

WEEKLY_REPORT_SYSTEM_PROMPT = """你是一个专业的心理健康助手，正在为用户生成本周的情绪周报。

## 输出要求
请以 JSON 格式输出周报内容，包含以下字段：
- title: 一个简短的动态标题（10字以内），概括本周情绪特点，如"这周像一场漫长的周三"、"后半周好像慢慢回来了"
- story_line: 情绪故事线，用叙事体描述本周情绪走势（100-150字），语气温和、有温度
- keywords: 情绪关键词列表，从日记中提取3-5个高频词
- insight: 一句看见，提炼核心感受（30字以内），用引用格式突出
- suggestion: 温和建议，措辞谨慎，不评判不说教（50字以内）
- outlook: 下周展望，一句话收束（30字以内），如"下周不一定更好，但至少不用一个人扛"

## 注意事项
- 语气温和、不评判、不说教
- 如果只有少量记录，诚实说明"本周记录较少"
- 避免对用户情绪做负面评价
- 提供积极、支持性的反馈
- 不要使用过于华丽的词藻，保持真诚朴实
"""

WEEKLY_REPORT_USER_PROMPT_TEMPLATE = """请根据用户本周的日记数据生成情绪周报。

## 用户本周日记数据
{diary_data}

## 情绪分布
{emotion_distribution}

请生成周报内容。"""


# ---------------------------------------------------------------------------
# 周报服务
# ---------------------------------------------------------------------------

class WeeklyReportService:
    """情绪周报服务，封装所有周报相关业务逻辑。

    依赖外部注入：
    - settings: 应用配置
    - redis: Redis 客户端
    - ai_provider: AI 提供者（mock/glm_free/glm）
    """

    def __init__(
        self,
        settings: AppSettings,
        redis: Any,
        ai_provider: str = "mock",
        zhipu_api_key: str = "",
    ) -> None:
        """初始化周报服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            ai_provider: AI 服务提供者
            zhipu_api_key: 智谱 API Key
        """
        self._settings = settings
        self._redis = redis
        self._ai_provider = ai_provider
        self._zhipu_api_key = zhipu_api_key

        # AI 服务实例缓存
        self._ai_service: GLMChatService | None = None

        logger.info(
            "[WeeklyReportService] 初始化完成，AI Provider: %s",
            ai_provider,
        )

    def _get_ai_service(self) -> GLMChatService:
        """获取 AI 服务实例。"""
        if self._ai_service is None:
            self._ai_service = create_ai_chat_service(
                provider=self._ai_provider,
                api_key=self._zhipu_api_key,
                model="glm-4-plus",  # 使用 GLM-4-Plus 生成周报
                personality="xiaowen",  # 使用温和的小温性格
            )
        return self._ai_service

    # -----------------------------------------------------------------------
    # 周报生成核心方法
    # -----------------------------------------------------------------------

    async def get_or_generate_weekly_report(
        self,
        user_id: str,
        db: AsyncSession,
        *,
        force_refresh: bool = False,
        target_date: date | None = None,
    ) -> WeeklyReportResponse | EmptyWeeklyReportResponse:
        """获取或生成本周周报。

        优先从缓存获取，如果缓存不存在或 force_refresh=True 则重新生成。

        Args:
            user_id: 用户ID
            db: 数据库会话
            force_refresh: 是否强制重新生成
            target_date: 目标日期，默认为今天

        Returns:
            周报响应或空周报提示
        """
        week_start = _get_week_start(target_date)
        week_end = _get_week_end(week_start)
        cache_key = _weekly_report_cache_key(user_id, week_start.isoformat())

        # 尝试从缓存获取
        if not force_refresh and self._redis:
            try:
                cached_data = await self._redis.get(cache_key)
                if cached_data:
                    if isinstance(cached_data, bytes):
                        cached_data = cached_data.decode("utf-8")
                    data = json.loads(cached_data)
                    logger.info(
                        "[WeeklyReportService] 从缓存获取周报，用户: %s，周起始: %s",
                        user_id,
                        week_start,
                    )
                    response = WeeklyReportResponse(**data)
                    response.is_cached = True
                    return response
            except Exception as e:
                logger.warning(
                    "[WeeklyReportService] 读取缓存失败: %s",
                    str(e),
                )

        # 从数据库获取或生成
        report = await self._get_or_create_report(
            user_id=user_id,
            week_start=week_start,
            db=db,
            force_refresh=force_refresh,
        )

        if report is None:
            # 本周无有效日记
            return EmptyWeeklyReportResponse(
                week_start_date=week_start,
                week_end_date=week_end,
                diary_count=0,
            )

        # 构建响应
        response = WeeklyReportResponse(
            id=report.id,
            week_start_date=report.week_start_date,
            week_end_date=week_end,
            title=report.title,
            story_line=report.story_line,
            keywords=report.keywords,
            insight=report.insight,
            suggestion=report.suggestion,
            outlook=report.outlook,
            diary_count=report.diary_count,
            created_at=report.created_at,
            is_cached=False,
        )

        # 缓存结果
        await self._cache_report(cache_key, response)

        return response

    async def _get_or_create_report(
        self,
        user_id: str,
        week_start: date,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> WeeklyReport | None:
        """从数据库获取或创建周报。

        Args:
            user_id: 用户ID
            week_start: 周起始日期
            db: 数据库会话
            force_refresh: 是否强制重新生成

        Returns:
            周报对象，如果无有效日记则返回 None
        """
        # 查询现有周报
        if not force_refresh:
            stmt = (
                select(WeeklyReport)
                .where(
                    WeeklyReport.user_id == user_id,
                    WeeklyReport.week_start_date == week_start,
                )
            )
            result = await db.execute(stmt)
            existing_report = result.scalar_one_or_none()

            if existing_report:
                logger.debug(
                    "[WeeklyReportService] 从数据库获取现有周报，ID: %s",
                    existing_report.id,
                )
                return existing_report

        # 获取本周日记数据
        diaries = await self._get_week_diaries(user_id, week_start, db)

        if not diaries:
            logger.info(
                "[WeeklyReportService] 本周无有效日记，用户: %s，周起始: %s",
                user_id,
                week_start,
            )
            return None

        # 生成周报内容
        report_content = await self._generate_report_content(diaries, week_start)

        # 保存到数据库
        if force_refresh:
            # 删除旧周报
            stmt = select(WeeklyReport).where(
                WeeklyReport.user_id == user_id,
                WeeklyReport.week_start_date == week_start,
            )
            result = await db.execute(stmt)
            old_report = result.scalar_one_or_none()
            if old_report:
                await db.delete(old_report)

        report = WeeklyReport(
            id=str(uuid.uuid4()),
            user_id=user_id,
            week_start_date=week_start,
            title=report_content.get("title"),
            story_line=report_content.get("story_line"),
            keywords=report_content.get("keywords", []),
            insight=report_content.get("insight"),
            suggestion=report_content.get("suggestion"),
            outlook=report_content.get("outlook"),
            diary_count=len(diaries),
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info(
            "[WeeklyReportService] 周报已生成，用户: %s，周起始: %s，日记数: %d",
            user_id,
            week_start,
            len(diaries),
        )

        return report

    async def _get_week_diaries(
        self,
        user_id: str,
        week_start: date,
        db: AsyncSession,
    ) -> list[EmotionDiary]:
        """获取本周有效日记（有文字内容的记录）。

        0 字记录规则：纯色调记录可提交，但不计入周报分析。

        Args:
            user_id: 用户ID
            week_start: 周起始日期
            db: 数据库会话

        Returns:
            有效日记列表
        """
        week_end = _get_week_end(week_start)

        stmt = (
            select(EmotionDiary)
            .where(
                EmotionDiary.user_id == user_id,
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.record_date >= week_start,
                EmotionDiary.record_date <= week_end,
                # 只查询有内容的记录
                and_(
                    EmotionDiary.content_text.isnot(None),
                    EmotionDiary.content_text != "",
                ),
            )
            .order_by(EmotionDiary.record_date.asc())
        )

        result = await db.execute(stmt)
        diaries = result.scalars().all()

        # 过滤掉空内容
        valid_diaries = []
        for diary in diaries:
            content = self._decrypt_diary_content(diary)
            if content and content.strip():
                valid_diaries.append(diary)

        return valid_diaries

    def _decrypt_diary_content(self, diary: EmotionDiary) -> str | None:
        """解密日记内容。

        Args:
            diary: 日记对象

        Returns:
            解密后的内容
        """
        if not diary.content_text:
            return None

        if is_encrypted_content(diary.content_text):
            try:
                return decrypt_content_server_side(diary.content_text)
            except Exception as e:
                logger.warning(
                    "[WeeklyReportService] 解密日记内容失败: %s",
                    str(e),
                )
                return diary.content_text

        return diary.content_text

    async def _generate_report_content(
        self,
        diaries: list[EmotionDiary],
        week_start: date,
    ) -> dict[str, Any]:
        """调用 AI 生成周报内容。

        Args:
            diaries: 本周日记列表
            week_start: 周起始日期

        Returns:
            周报内容字典
        """
        # 准备日记数据
        diary_data = []
        emotion_counts: dict[str, int] = {}

        for diary in diaries:
            content = self._decrypt_diary_content(diary)
            if content:
                diary_data.append({
                    "date": str(diary.record_date),
                    "tone": diary.emotion_tone,
                    "labels": diary.emotion_labels or [],
                    "content": content[:500],  # 限制长度
                })

                # 统计情绪分布
                if diary.emotion_tone:
                    emotion_counts[diary.emotion_tone] = emotion_counts.get(diary.emotion_tone, 0) + 1

        # 构建情绪分布描述
        emotion_distribution = self._build_emotion_distribution(emotion_counts)

        # 构建用户提示
        user_prompt = WEEKLY_REPORT_USER_PROMPT_TEMPLATE.format(
            diary_data=json.dumps(diary_data, ensure_ascii=False, indent=2),
            emotion_distribution=emotion_distribution,
        )

        try:
            # 调用 AI 服务
            ai_service = self._get_ai_service()

            # 使用 memory 字段传递周报专用的 System Prompt
            # GLMChatService 会将 memory 追加到默认 system prompt 之后
            response_text = await ai_service.chat(
                prompt=user_prompt,
                context={
                    "memory": WEEKLY_REPORT_SYSTEM_PROMPT,
                },
            )

            # 解析 JSON 响应
            # 尝试提取 JSON 内容
            json_content = self._extract_json_from_response(response_text)

            if json_content:
                return json_content

            # 如果解析失败，使用默认结构
            logger.warning(
                "[WeeklyReportService] AI 响应解析失败，使用默认结构"
            )
            return self._get_default_report_content(response_text)

        except Exception as e:
            logger.error(
                "[WeeklyReportService] AI 生成失败: %s",
                str(e),
            )
            # 返回基础结构
            return self._get_fallback_report_content(diaries, week_start)

    def _build_emotion_distribution(self, counts: dict[str, int]) -> str:
        """构建情绪分布描述。"""
        if not counts:
            return "本周没有情绪数据"

        lines = []
        total = sum(counts.values())

        for tone, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            meta = EMOTION_TONE_META.get(tone, {})
            meaning = meta.get("meaning", tone)
            percentage = round(count / total * 100)
            lines.append(f"- {meaning}（{tone}）: {count} 次（{percentage}%）")

        return "\n".join(lines)

    def _extract_json_from_response(self, response: str) -> dict[str, Any] | None:
        """从 AI 响应中提取 JSON 内容。"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        import re
        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, response)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... } 块（匹配最外层完整 JSON 对象）
        brace_pattern = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
        match = re.search(brace_pattern, response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _get_default_report_content(self, ai_response: str) -> dict[str, Any]:
        """获取默认周报结构（AI 响应解析失败时）。"""
        return {
            "title": "本周情绪回顾",
            "story_line": ai_response[:200] if len(ai_response) > 200 else ai_response,
            "keywords": ["情绪", "记录"],
            "insight": "记录本身就是一种自我关怀。",
            "suggestion": "也许可以试试跟AI朋友聊聊你的感受。",
            "outlook": "下周继续记录，慢慢来。",
        }

    def _get_fallback_report_content(
        self,
        diaries: list[EmotionDiary],
        week_start: date,
    ) -> dict[str, Any]:
        """获取降级周报内容（AI 调用失败时）。"""
        # 基于日记数据生成简单统计
        tone_counts: dict[str, int] = {}
        all_labels: list[str] = []

        for diary in diaries:
            if diary.emotion_tone:
                tone_counts[diary.emotion_tone] = tone_counts.get(diary.emotion_tone, 0) + 1
            if diary.emotion_labels:
                all_labels.extend(diary.emotion_labels)

        # 找出主要情绪
        main_tone = max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else "未知"
        main_tone_meta = EMOTION_TONE_META.get(main_tone, {"meaning": "情绪"})

        # 高频标签
        from collections import Counter
        label_counter = Counter(all_labels)
        top_labels = [label for label, _ in label_counter.most_common(5)]

        return {
            "title": f"本周主要{main_tone_meta.get('meaning', '情绪')}",
            "story_line": f"本周共记录了 {len(diaries)} 天的情绪变化，主要以{main_tone_meta.get('meaning', '情绪')}为主。每一天的记录都是对自己的关注和照顾。",
            "keywords": top_labels if top_labels else ["记录", "情绪"],
            "insight": "坚持记录本身就是一种力量。",
            "suggestion": "也许可以试试跟AI朋友聊聊你的感受。",
            "outlook": "下周继续，慢慢来。",
        }

    async def _cache_report(
        self,
        cache_key: str,
        response: WeeklyReportResponse,
    ) -> None:
        """缓存周报结果到 Redis。"""
        if not self._redis:
            return

        try:
            # 缓存 7 天
            await self._redis.setex(
                cache_key,
                7 * 24 * 60 * 60,
                json.dumps(response.model_dump(), ensure_ascii=False, default=str),
            )
            logger.debug(
                "[WeeklyReportService] 周报已缓存，key: %s",
                cache_key,
            )
        except Exception as e:
            logger.warning(
                "[WeeklyReportService] 缓存周报失败: %s",
                str(e),
            )

    # -----------------------------------------------------------------------
    # 周报历史查询
    # -----------------------------------------------------------------------

    async def get_report_history(
        self,
        user_id: str,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """获取用户的周报历史。

        Args:
            user_id: 用户ID
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            分页响应字典
        """
        # 统计总数
        count_stmt = (
            select(func.count())
            .where(WeeklyReport.user_id == user_id)
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询列表
        offset = (page - 1) * page_size
        stmt = (
            select(WeeklyReport)
            .where(WeeklyReport.user_id == user_id)
            .order_by(WeeklyReport.week_start_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # 构建响应
        items = []
        for report in reports:
            items.append(
                WeeklyReportResponse(
                    id=report.id,
                    week_start_date=report.week_start_date,
                    week_end_date=_get_week_end(report.week_start_date),
                    title=report.title,
                    story_line=report.story_line,
                    keywords=report.keywords,
                    insight=report.insight,
                    suggestion=report.suggestion,
                    outlook=report.outlook,
                    diary_count=report.diary_count,
                    created_at=report.created_at,
                    is_cached=False,
                ).model_dump()
            )

        return {
            "data": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": page * page_size < total,
            },
        }

    # -----------------------------------------------------------------------
    # 定时任务方法
    # -----------------------------------------------------------------------

    async def generate_report_for_user(
        self,
        user_id: str,
        db: AsyncSession,
        week_start: date | None = None,
    ) -> WeeklyReport | None:
        """为指定用户生成周报（定时任务调用）。

        Args:
            user_id: 用户ID
            db: 数据库会话
            week_start: 周起始日期，默认为本周

        Returns:
            生成的周报对象，如果无有效日记则返回 None
        """
        if week_start is None:
            week_start = _get_week_start()

        # 强制重新生成
        return await self._get_or_create_report(
            user_id=user_id,
            week_start=week_start,
            db=db,
            force_refresh=True,
        )

    async def batch_generate_reports(
        self,
        db: AsyncSession,
        week_start: date | None = None,
    ) -> dict[str, int]:
        """批量生成所有用户的周报（定时任务调用）。

        Args:
            db: 数据库会话
            week_start: 周起始日期，默认为本周

        Returns:
            生成统计：成功数、失败数、跳过数
        """
        if week_start is None:
            week_start = _get_week_start()

        # 查询本周有日记的用户
        week_end = _get_week_end(week_start)

        stmt = (
            select(EmotionDiary.user_id, func.count().label("count"))
            .where(
                EmotionDiary.deleted_at.is_(None),
                EmotionDiary.record_date >= week_start,
                EmotionDiary.record_date <= week_end,
                and_(
                    EmotionDiary.content_text.isnot(None),
                    EmotionDiary.content_text != "",
                ),
            )
            .group_by(EmotionDiary.user_id)
        )

        result = await db.execute(stmt)
        user_diary_counts = result.all()

        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        for user_id, diary_count in user_diary_counts:
            try:
                report = await self.generate_report_for_user(
                    user_id=user_id,
                    db=db,
                    week_start=week_start,
                )
                if report:
                    stats["success"] += 1
                    logger.info(
                        "[WeeklyReportService] 批量生成成功，用户: %s，日记数: %d",
                        user_id,
                        diary_count,
                    )
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "[WeeklyReportService] 批量生成失败，用户: %s，错误: %s",
                    user_id,
                    str(e),
                )

        logger.info(
            "[WeeklyReportService] 批量生成完成，成功: %d，失败: %d，跳过: %d",
            stats["success"],
            stats["failed"],
            stats["skipped"],
        )

        return stats
