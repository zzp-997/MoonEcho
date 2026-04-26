"""树洞核心服务。

实现树洞帖子 CRUD、温度排序算法、共鸣/评论功能。

温度排序算法（modules_design.md 4.7）：
- 排序权重 = 时间衰减因子 × 0.4 + 共鸣权重 × 0.3 + 评论权重 × 0.2 + 随机因子 × 0.1
- 新发布获得曝光加成
- 无互动内容4小时后衰减但不完全淹没
- 7天后不进默认信息流

低谷时段守护（2-5点）：
- 降低新鲜度权重
- 提升共鸣数权重

T017-B 增强：
- 集成 TreeholeContentAudit（树洞专用审核，替代通用审核）
- 审核拦截时返回温和反馈文案
- 集成脱敏提醒（发布前检测可识别信息，建议性提醒不阻止）
- 集成骚扰规则引擎（树洞场景频率控制）
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.enums.error_codes import ErrorCode
from app.models.treehole import TreeholeComment, TreeholePost
from app.schemas.treehole import (
    AnonymousIdentityResponse,
    AuditFeedbackInfo,
    FuzzyTimeResponse,
    IdentityWarningInfo,
    format_fuzzy_time,
    ResonanceResponse,
    TopicTag,
    TOPIC_TAG_LABELS,
    TreeholeCommentCreateRequest,
    TreeholeCommentCreateResponse,
    TreeholeCommentResponse,
    TreeholePostCreateRequest,
    TreeholePostCreateResponse,
    TreeholePostDetailResponse,
    TreeholePostListResponse,
    TreeholePostResponse,
)
from app.services.anonymous_identity import AnonymousIdentityService
from app.services.content_audit import (
    AuditResult,
    ContentAuditProtocol,
    TreeholeContentAudit,
    create_content_audit_service,
    get_audit_feedback,
)
from app.services.crisis_detection import CrisisDetector, get_crisis_detector
from app.services.harassment_detector import (
    HarassmentDetector,
    HarassmentDetectionResult,
    create_harassment_detector,
)
from app.services.identity_detector import (
    IdentityDetector,
    IdentityDetectionResult,
    create_identity_detector,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 温度排序算法参数
# ---------------------------------------------------------------------------

# 权重配置
WEIGHT_TIME_DECAY = 0.4       # 时间衰减权重
WEIGHT_RESONANCE = 0.3        # 共鸣权重
WEIGHT_COMMENT = 0.2          # 评论权重
WEIGHT_RANDOM = 0.1           # 随机因子权重

# 低谷时段权重调整（2:00 - 5:00）
LOW_PERIOD_TIME_DECAY = 0.2   # 降低新鲜度权重
LOW_PERIOD_RESONANCE = 0.4    # 提升共鸣数权重
LOW_PERIOD_COMMENT = 0.25     # 评论权重
LOW_PERIOD_RANDOM = 0.15     # 随机因子权重

# 时间参数
NEW_POST_BOOST_HOURS = 2      # 新帖子曝光加成时长（小时）
DECAY_START_HOURS = 4        # 开始衰减的小时数
ARCHIVE_DAYS = 7             # 归档天数（不进默认信息流）

# 低谷时段定义（小时，24小时制）
LOW_PERIOD_START = 2
LOW_PERIOD_END = 5


# ---------------------------------------------------------------------------
# 树洞核心服务
# ---------------------------------------------------------------------------

class TreeholeService:
    """树洞核心服务。

    实现：
    1. 树洞帖子 CRUD
    2. 温度排序算法
    3. 低谷时段守护
    4. 共鸣/评论功能
    5. 内容审核集成

    使用示例：
        service = TreeholeService(settings, redis)
        result = await service.create_post(user_id, request, db)
    """

    def __init__(
        self,
        settings: Any,
        redis: Any,
        content_audit_provider: str = "treehole",
        anon_identity_service: AnonymousIdentityService | None = None,
        crisis_detector: CrisisDetector | None = None,
        harassment_detector: HarassmentDetector | None = None,
        identity_detector: IdentityDetector | None = None,
    ) -> None:
        """初始化树洞服务。

        Args:
            settings: 应用配置
            redis: Redis 客户端
            content_audit_provider: 内容审核服务提供者（默认 treehole）
            anon_identity_service: 匿名身份服务（可选）
            crisis_detector: 危机检测器（可选）
            harassment_detector: 骚扰规则引擎（可选）
            identity_detector: 脱敏提醒服务（可选）
        """
        self._settings = settings
        self._redis = redis
        self._content_audit: ContentAuditProtocol = create_content_audit_service(
            content_audit_provider
        )
        self._anon_identity_service = anon_identity_service
        self._crisis_detector = crisis_detector or get_crisis_detector()
        self._harassment_detector = harassment_detector or create_harassment_detector(redis)
        self._identity_detector = identity_detector or create_identity_detector()

        logger.info(
            "[TreeholeService] 初始化完成，内容审核 Provider: %s",
            content_audit_provider
        )

    def _get_anon_identity_service(self) -> AnonymousIdentityService:
        """获取匿名身份服务实例。"""
        if self._anon_identity_service is None:
            self._anon_identity_service = AnonymousIdentityService(self._settings)
        return self._anon_identity_service

    # =========================================================================
    # 温度排序算法
    # =========================================================================

    def _is_low_period(self, dt: datetime | None = None) -> bool:
        """判断是否处于低谷时段（2:00 - 5:00）。

        Args:
            dt: 时间点（可选，默认当前时间）

        Returns:
            是否处于低谷时段
        """
        if dt is None:
            dt = datetime.now(timezone.utc)
        hour = dt.hour
        return LOW_PERIOD_START <= hour < LOW_PERIOD_END

    def _calculate_time_decay_factor(
        self,
        created_at: datetime,
        now: datetime | None = None,
    ) -> float:
        """计算时间衰减因子。

        公式：1 / (发布小时数 + 1)

        Args:
            created_at: 创建时间
            now: 当前时间

        Returns:
            时间衰减因子 (0.0 - 1.0)
        """
        if now is None:
            now = datetime.now(timezone.utc)

        hours_elapsed = (now - created_at).total_seconds() / 3600

        # 新帖子曝光加成
        if hours_elapsed < NEW_POST_BOOST_HOURS:
            return 1.0

        # 计算衰减因子，上限24小时
        hours_for_calc = min(hours_elapsed, 24)
        return 1.0 / (hours_for_calc + 1)

    def _calculate_resonance_weight(
        self,
        resonance_count: int,
        active_user_count: int = 100,
    ) -> float:
        """计算共鸣权重。

        公式：共鸣数 / 活跃用户数（归一化到 0-1）

        Args:
            resonance_count: 共鸣数
            active_user_count: 活跃用户数（归一化基数）

        Returns:
            共鸣权重 (0.0 - 1.0)
        """
        if active_user_count <= 0:
            active_user_count = 100

        weight = resonance_count * 2 / active_user_count
        return min(weight, 1.0)

    def _calculate_comment_weight(
        self,
        comment_count: int,
        active_user_count: int = 100,
    ) -> float:
        """计算评论权重。

        公式：评论数 × 3 / 活跃用户数（归一化到 0-1）

        Args:
            comment_count: 评论数
            active_user_count: 活跃用户数（归一化基数）

        Returns:
            评论权重 (0.0 - 1.0)
        """
        if active_user_count <= 0:
            active_user_count = 100

        weight = comment_count * 3 / active_user_count
        return min(weight, 1.0)

    def _calculate_random_factor(self) -> float:
        """计算随机因子。

        给冷启动内容机会。

        Returns:
            随机因子 (0.0 - 1.0)
        """
        return random.random()

    def calculate_temperature_score(
        self,
        post: TreeholePost,
        now: datetime | None = None,
    ) -> float:
        """计算帖子温度分。

        温度分 = 时间衰减因子 × 0.4 + 共鸣权重 × 0.3 + 评论权重 × 0.2 + 随机因子 × 0.1

        低谷时段（2-5点）调整：
        - 时间衰减权重降低到 0.2
        - 共鸣权重提升到 0.4

        Args:
            post: 帖子对象
            now: 当前时间（可选）

        Returns:
            温度分
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # 判断是否低谷时段
        is_low = self._is_low_period(now)

        # 计算各因子
        time_decay = self._calculate_time_decay_factor(post.created_at, now)
        resonance_weight = self._calculate_resonance_weight(post.resonance_count)
        comment_weight = self._calculate_comment_weight(post.comment_count)
        random_factor = self._calculate_random_factor()

        # 根据时段选择权重
        if is_low:
            w_time = LOW_PERIOD_TIME_DECAY
            w_resonance = LOW_PERIOD_RESONANCE
            w_comment = LOW_PERIOD_COMMENT
            w_random = LOW_PERIOD_RANDOM
        else:
            w_time = WEIGHT_TIME_DECAY
            w_resonance = WEIGHT_RESONANCE
            w_comment = WEIGHT_COMMENT
            w_random = WEIGHT_RANDOM

        # 计算温度分
        temperature = (
            time_decay * w_time +
            resonance_weight * w_resonance +
            comment_weight * w_comment +
            random_factor * w_random
        )

        return round(temperature, 4)

    # =========================================================================
    # 内容审核集成
    # =========================================================================

    async def _audit_content(
        self,
        content: str,
    ) -> dict[str, Any]:
        """审核内容。

        根据 modules_design.md 7.3 差异化审核策略：
        - 使用 TreeholeContentAudit（树洞专用审核）
        - 树洞审核严格度：中高
        - 自残触发关怀流程（不拦截，发布后关怀）
        - 人身攻击拦截
        - 审核拦截时返回温和反馈文案（feedback 字段）

        Args:
            content: 待审核内容

        Returns:
            审核结果，包含 feedback 温和反馈文案
        """
        # 调用内容审核服务（TreeholeContentAudit 已返回 feedback 字段）
        audit_result = await self._content_audit.check(content)

        # 检测危机信号（自伤内容）— 作为双重保障
        try:
            crisis_result = self._crisis_detector.detect(content)

            if crisis_result:
                audit_result["crisis_detected"] = True
                audit_result["crisis_level"] = crisis_result.get("level")
                audit_result["crisis_response"] = crisis_result.get("response")

                # 自伤内容允许发布但触发关怀流程
                audit_result["pass"] = True
                audit_result["trigger_care"] = True

                logger.warning(
                    "[TreeholeService] 检测到自伤内容，允许发布但触发关怀，级别: %s",
                    crisis_result.get("level")
                )
        except Exception as e:
            # 危机检测失败不应阻断发布流程，记录日志即可
            logger.error(
                "[TreeholeService] 危机检测异常，跳过检测: %s",
                str(e)
            )
            # 不设置危机相关字段，继续正常审核流程

        # 如果审核不通过且没有 feedback，使用默认温和反馈
        if not audit_result.get("pass") and not audit_result.get("feedback"):
            labels = audit_result.get("labels", [])
            label = labels[0] if labels else None
            audit_result["feedback"] = get_audit_feedback(
                result=AuditResult.BLOCK,
                label=label,
            )

        return audit_result

    def _detect_identity_info(
        self,
        content: str,
    ) -> IdentityDetectionResult:
        """检测内容中的可识别信息（脱敏提醒）。

        建议性提醒，不阻止发布。返回检测结果供前端展示提醒弹窗。

        Args:
            content: 待检测内容

        Returns:
            脱敏检测结果
        """
        try:
            result = self._identity_detector.detect(content)
            if result.has_warning:
                logger.info(
                    "[TreeholeService] 检测到可识别信息，类型: %s",
                    ", ".join(d.info_type.value for d in result.detections),
                )
            return result
        except Exception as e:
            # 脱敏检测失败不应阻断发布流程
            logger.error(
                "[TreeholeService] 脱敏检测异常，跳过检测: %s",
                str(e)
            )
            return IdentityDetectionResult()

    # =========================================================================
    # 帖子 CRUD
    # =========================================================================

    async def list_posts(
        self,
        db: AsyncSession,
        current_user_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
        topic_tag: str | None = None,
        include_archived: bool = False,
    ) -> TreeholePostListResponse:
        """获取树洞帖子列表。

        使用温度排序算法，支持话题标签筛选。

        Args:
            db: 数据库会话
            current_user_id: 当前用户ID（可选）
            page: 页码
            page_size: 每页数量
            topic_tag: 话题标签筛选
            include_archived: 是否包含已归档帖子

        Returns:
            帖子列表响应
        """
        now = datetime.now(timezone.utc)

        # 构建查询条件
        conditions = [
            TreeholePost.deleted_at.is_(None),
            TreeholePost.status == "active",
        ]

        # 7天归档逻辑
        if not include_archived:
            archive_cutoff = now - timedelta(days=ARCHIVE_DAYS)
            conditions.append(TreeholePost.created_at >= archive_cutoff)

        # 话题筛选
        if topic_tag:
            conditions.append(TreeholePost.topic_tag == topic_tag)

        # 查询帖子（不排序，后续按温度分排序）
        stmt = (
            select(TreeholePost)
            .where(and_(*conditions))
            .offset((page - 1) * page_size)
            .limit(page_size + 1)  # 多查一条判断是否有更多
        )

        result = await db.execute(stmt)
        posts = result.scalars().all()

        # 查询总数
        count_stmt = select(func.count(TreeholePost.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 计算温度分并排序
        posts_with_score = []
        for post in posts:
            score = self.calculate_temperature_score(post, now)
            posts_with_score.append((post, score))

        # 按温度分降序排序
        posts_with_score.sort(key=lambda x: x[1], reverse=True)

        # 构建响应
        post_responses = []
        for post, score in posts_with_score[:page_size]:
            response = await self._build_post_response(post, now, db)
            response.temperature_score = score
            post_responses.append(response)

        # 构建分页信息
        pagination = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "hasMore": len(posts) > page_size,
        }

        return TreeholePostListResponse(
            data=post_responses,
            pagination=pagination,
            topic_tags=TOPIC_TAG_LABELS,
        )

    async def get_post(
        self,
        post_id: str,
        db: AsyncSession,
        current_user_id: str | None = None,
    ) -> TreeholePostDetailResponse:
        """获取树洞帖子详情。

        包含帖子信息和评论列表。

        Args:
            post_id: 帖子ID
            db: 数据库会话
            current_user_id: 当前用户ID（可选）

        Returns:
            帖子详情响应

        Raises:
            AppError: 帖子不存在
        """
        # 查询帖子
        stmt = select(TreeholePost).where(
            TreeholePost.id == post_id,
            TreeholePost.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.TREEHOLE_POST_NOT_FOUND,
                message="帖子不存在",
                status_code=404,
            )

        # 查询评论
        comment_stmt = (
            select(TreeholeComment)
            .where(
                TreeholeComment.post_id == post_id,
                TreeholeComment.deleted_at.is_(None),
            )
            .order_by(TreeholeComment.created_at)
            .limit(50)
        )
        comment_result = await db.execute(comment_stmt)
        comments = comment_result.scalars().all()

        # 构建响应
        now = datetime.now(timezone.utc)
        post_response = await self._build_post_response(post, now, db)

        comment_responses = [
            TreeholeCommentResponse(
                id=comment.id,
                content=comment.content,
                is_resonance=comment.is_resonance,
                fuzzy_time=format_fuzzy_time(comment.created_at, now),
            )
            for comment in comments
            if not comment.is_resonance  # 共鸣类型不在评论列表显示
        ]

        return TreeholePostDetailResponse(
            post=post_response,
            comments=comment_responses,
        )

    async def create_post(
        self,
        user_id: str,
        request: TreeholePostCreateRequest,
        db: AsyncSession,
    ) -> TreeholePostCreateResponse:
        """创建树洞帖子。

        仅支持匿名发布，自动生成虚拟身份。
        T017-B 增强：
        - 审核拦截时返回温和反馈文案（audit_feedback）
        - 发布前脱敏提醒（identity_warning，不影响发布）
        - 骚扰频率检测（树洞发布频率限速）

        Args:
            user_id: 用户ID
            request: 创建请求
            db: 数据库会话

        Returns:
            帖子创建响应（包含帖子信息、审核反馈、脱敏提醒）

        Raises:
            AppError: 审核不通过或频率超限
        """
        # 1. 骚扰频率检测
        harassment_result = await self._harassment_detector.check_treehole_post_rate(
            user_id
        )
        if harassment_result.has_rate_limit:
            raise AppError(
                code=ErrorCode.PUBLISH_TOO_FREQUENT,
                message=harassment_result.rate_limit_message or "发布过于频繁，请稍后再试",
                status_code=429,
            )

        # 2. 内容审核（使用 TreeholeContentAudit）
        audit_result = await self._audit_content(request.content)

        # 3. 脱敏提醒检测（不影响发布）
        identity_result = self._detect_identity_info(request.content)

        # 4. 审核不通过时，返回温和反馈文案而非抛异常
        audit_feedback = None
        if not audit_result.get("pass"):
            # 构建审核反馈信息
            audit_feedback = AuditFeedbackInfo(
                result=audit_result.get("result", "block"),
                feedback=audit_result.get("feedback", "这条内容好像不太适合在这里发出来。"),
                labels=audit_result.get("labels", []),
            )

            logger.info(
                "[TreeholeService] 帖子审核不通过，用户: %s，反馈: %s",
                user_id, audit_feedback.feedback,
            )

            # 返回审核反馈（不创建帖子，但前端可以获取反馈文案）
            return TreeholePostCreateResponse(
                post=TreeholePostResponse(
                    id="",
                    content=request.content,
                    topic_tag=request.topic_tag.value if request.topic_tag else None,
                ),
                audit_feedback=audit_feedback,
                identity_warning=None,
                trigger_care=False,
            )

        # 5. 获取或创建匿名身份
        anon_service = self._get_anon_identity_service()
        anon_identity = await anon_service.get_or_create_treehole_identity(
            user_id, db
        )

        # 6. 生成随机延迟（0-15分钟）
        random_delay_minutes = random.randint(0, 15)

        # 7. 创建帖子
        post = TreeholePost(
            id=str(uuid.uuid4()),
            user_id=user_id,
            anon_identity_id=anon_identity.id,
            content=request.content,
            topic_tag=request.topic_tag.value if request.topic_tag else None,
            image_urls=request.image_urls,
            status="active",
        )
        db.add(post)
        await db.flush()

        # 8. 构建响应
        now = datetime.now(timezone.utc)
        post_response = await self._build_post_response(post, now, db)
        post_response.fuzzy_time = format_fuzzy_time(
            post.created_at, now, random_delay_minutes
        )

        # 9. 构建脱敏提醒信息
        identity_warning = None
        if identity_result.has_warning:
            identity_warning = IdentityWarningInfo(
                has_warning=True,
                warning_message=identity_result.warning_message,
                detected_types=[
                    d.info_type.value for d in identity_result.detections
                ],
            )

        # 10. 判断是否触发关怀
        trigger_care = audit_result.get("trigger_care", False)

        logger.info(
            "[TreeholeService] 创建帖子成功，帖子: %s，用户: %s，触发关怀: %s，"
            "脱敏提醒: %s",
            post.id, user_id, trigger_care,
            identity_result.has_warning,
        )

        return TreeholePostCreateResponse(
            post=post_response,
            audit_feedback=None,  # 通过时无审核反馈
            identity_warning=identity_warning,
            trigger_care=trigger_care,
        )

    # =========================================================================
    # 误判申诉
    # =========================================================================

    async def create_appeal(
        self,
        user_id: str,
        post_id: str,
        reason: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """创建审核结果申诉。

        被拦截/删除后可申诉，人工复核。
        申诉记录存储到 reports 表，type 设为 audit_appeal。

        Args:
            user_id: 用户ID
            post_id: 帖子ID
            reason: 申诉理由
            db: 数据库会话

        Returns:
            申诉结果，包含 id 和 status

        Raises:
            AppError: 帖子不存在或重复申诉
        """
        from app.models.report import Report

        # 1. 验证帖子存在
        post_stmt = select(TreeholePost).where(
            TreeholePost.id == post_id,
        )
        post_result = await db.execute(post_stmt)
        post = post_result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.TREEHOLE_POST_NOT_FOUND,
                message="帖子不存在",
                status_code=404,
            )

        # 2. 验证帖子属于该用户（只有帖子作者可以申诉）
        if post.user_id != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="只能对自己的帖子发起申诉",
                status_code=403,
            )

        # 3. 检查是否已有待处理的申诉
        existing_appeal_stmt = select(Report).where(
            Report.reported_content_id == post_id,
            Report.report_type == "audit_appeal",
            Report.reporter_id == user_id,
            Report.appeal_status == "pending",
        )
        existing_result = await db.execute(existing_appeal_stmt)
        existing_appeal = existing_result.scalar_one_or_none()

        if existing_appeal:
            raise AppError(
                code=ErrorCode.REPORT_DUPLICATE,
                message="该帖子已有待处理的申诉",
                status_code=409,
            )

        # 4. 创建申诉记录（复用 reports 表）
        appeal = Report(
            id=str(uuid.uuid4()),
            reporter_id=user_id,
            reported_user_id=user_id,  # 申诉场景下，举报人和被举报人相同
            reported_content_type="treehole_post",
            reported_content_id=post_id,
            report_type="audit_appeal",
            reason=reason,
            status="pending",
            appeal_status="pending",
            appeal_reason=reason,
        )
        db.add(appeal)
        await db.flush()

        logger.info(
            "[TreeholeService] 创建审核申诉，帖子: %s，用户: %s，申诉ID: %s",
            post_id, user_id, appeal.id,
        )

        return {
            "id": appeal.id,
            "status": "pending",
            "message": "申诉已提交，我们会尽快审核",
        }

    async def delete_post(
        self,
        user_id: str,
        post_id: str,
        db: AsyncSession,
    ) -> bool:
        """删除树洞帖子（软删除）。

        Args:
            user_id: 用户ID
            post_id: 帖子ID
            db: 数据库会话

        Returns:
            是否成功

        Raises:
            AppError: 帖子不存在或无权限
        """
        # 查询帖子
        stmt = select(TreeholePost).where(
            TreeholePost.id == post_id,
            TreeholePost.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.TREEHOLE_POST_NOT_FOUND,
                message="帖子不存在",
                status_code=404,
            )

        # 验证所有者
        if post.user_id != user_id:
            raise AppError(
                code=ErrorCode.PERMISSION_DENIED,
                message="无权限删除此帖子",
                status_code=403,
            )

        # 软删除
        post.deleted_at = datetime.now(timezone.utc)
        post.status = "deleted"

        logger.info(
            "[TreeholeService] 删除帖子，帖子: %s，用户: %s",
            post_id, user_id
        )

        return True

    # =========================================================================
    # 共鸣功能
    # =========================================================================

    async def create_resonance(
        self,
        user_id: str,
        post_id: str,
        db: AsyncSession,
    ) -> ResonanceResponse:
        """创建共鸣（"我懂你"）。

        Args:
            user_id: 用户ID
            post_id: 帖子ID
            db: 数据库会话

        Returns:
            共鸣响应

        Raises:
            AppError: 帖子不存在或已共鸣
        """
        # 检查帖子是否存在
        post_stmt = select(TreeholePost).where(
            TreeholePost.id == post_id,
            TreeholePost.deleted_at.is_(None),
        )
        post_result = await db.execute(post_stmt)
        post = post_result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.TREEHOLE_POST_NOT_FOUND,
                message="帖子不存在",
                status_code=404,
            )

        # 检查是否已共鸣
        check_stmt = select(TreeholeComment).where(
            TreeholeComment.post_id == post_id,
            TreeholeComment.user_id == user_id,
            TreeholeComment.is_resonance.is_(True),
            TreeholeComment.deleted_at.is_(None),
        )
        check_result = await db.execute(check_stmt)
        existing = check_result.scalar_one_or_none()

        if existing:
            return ResonanceResponse(
                resonance_count=post.resonance_count,
                message="你已经表达过共鸣了",
                already_resonated=True,
            )

        # 创建共鸣记录
        resonance = TreeholeComment(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
            content="",
            is_resonance=True,
        )
        db.add(resonance)

        # 更新帖子共鸣数
        post.resonance_count += 1

        logger.info(
            "[TreeholeService] 创建共鸣，帖子: %s，用户: %s",
            post_id, user_id
        )

        return ResonanceResponse(
            resonance_count=post.resonance_count,
            message="有人懂你",
            already_resonated=False,
        )

    # =========================================================================
    # 评论功能
    # =========================================================================

    async def create_comment(
        self,
        user_id: str,
        post_id: str,
        request: TreeholeCommentCreateRequest,
        db: AsyncSession,
    ) -> TreeholeCommentCreateResponse:
        """创建评论。

        评论限50字，不支持回复评论。
        T017-B 增强：
        - 审核拦截时返回温和反馈文案（audit_feedback）
        - 发布前脱敏提醒（identity_warning，不影响发布）
        - 骚扰频率检测（树洞评论频率、针对性评论频率）

        Args:
            user_id: 用户ID
            post_id: 帖子ID
            request: 创建请求
            db: 数据库会话

        Returns:
            评论创建响应（包含评论信息、审核反馈、脱敏提醒）

        Raises:
            AppError: 帖子不存在
        """
        # 1. 检查帖子是否存在
        post_stmt = select(TreeholePost).where(
            TreeholePost.id == post_id,
            TreeholePost.deleted_at.is_(None),
        )
        post_result = await db.execute(post_stmt)
        post = post_result.scalar_one_or_none()

        if not post:
            raise AppError(
                code=ErrorCode.TREEHOLE_POST_NOT_FOUND,
                message="帖子不存在",
                status_code=404,
            )

        # 2. 骚扰频率检测
        harassment_result = await self._harassment_detector.check_treehole_interaction(
            user_id=user_id,
            action="comment",
            target_user_id=post.user_id,
        )
        harassment_warning = None
        if harassment_result.has_warning and not harassment_result.has_rate_limit:
            harassment_warning = "; ".join(harassment_result.warning_messages)
        if harassment_result.has_rate_limit:
            raise AppError(
                code=ErrorCode.PUBLISH_TOO_FREQUENT,
                message=harassment_result.rate_limit_message or "评论过于频繁，请稍后再试",
                status_code=429,
            )

        # 3. 内容审核（使用 TreeholeContentAudit）
        audit_result = await self._audit_content(request.content)

        # 4. 脱敏提醒检测（不影响发布）
        identity_result = self._detect_identity_info(request.content)

        # 5. 审核不通过时，返回温和反馈文案
        audit_feedback = None
        if not audit_result.get("pass"):
            audit_feedback = AuditFeedbackInfo(
                result=audit_result.get("result", "block"),
                feedback=audit_result.get("feedback", "这条内容好像不太适合在这里发出来。"),
                labels=audit_result.get("labels", []),
            )

            logger.info(
                "[TreeholeService] 评论审核不通过，用户: %s，帖子: %s，反馈: %s",
                user_id, post_id, audit_feedback.feedback,
            )

            return TreeholeCommentCreateResponse(
                comment=TreeholeCommentResponse(
                    id="",
                    content=request.content,
                    is_resonance=False,
                ),
                audit_feedback=audit_feedback,
                identity_warning=None,
                harassment_warning=None,
            )

        # 6. 创建评论
        comment = TreeholeComment(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
            content=request.content,
            is_resonance=False,
        )
        db.add(comment)

        # 更新帖子评论数
        post.comment_count += 1

        now = datetime.now(timezone.utc)
        comment_response = TreeholeCommentResponse(
            id=comment.id,
            content=comment.content,
            is_resonance=False,
            fuzzy_time=format_fuzzy_time(comment.created_at, now),
        )

        # 7. 构建脱敏提醒信息
        identity_warning = None
        if identity_result.has_warning:
            identity_warning = IdentityWarningInfo(
                has_warning=True,
                warning_message=identity_result.warning_message,
                detected_types=[
                    d.info_type.value for d in identity_result.detections
                ],
            )

        logger.info(
            "[TreeholeService] 创建评论，帖子: %s，用户: %s，脱敏提醒: %s",
            post_id, user_id, identity_result.has_warning,
        )

        return TreeholeCommentCreateResponse(
            comment=comment_response,
            audit_feedback=None,
            identity_warning=identity_warning,
            harassment_warning=harassment_warning,
        )

    # =========================================================================
    # 辅助方法
    # =========================================================================

    async def _build_post_response(
        self,
        post: TreeholePost,
        now: datetime,
        db: AsyncSession,
    ) -> TreeholePostResponse:
        """构建帖子响应对象。

        Args:
            post: 帖子对象
            now: 当前时间
            db: 数据库会话

        Returns:
            帖子响应
        """
        # 获取匿名身份信息
        anon_identity = None
        if post.anon_identity_id:
            anon_service = self._get_anon_identity_service()
            anon = await anon_service.get_anonymous_identity(
                post.anon_identity_id, db
            )
            if anon:
                anon_identity = AnonymousIdentityResponse(
                    anon_id=anon.id,
                    anon_nickname=anon.anon_nickname,
                    persona_tag=anon.persona_type,
                    anon_avatar_url=anon.anon_avatar_url,
                )

        # 生成随机延迟
        random_delay = random.randint(0, 15)

        return TreeholePostResponse(
            id=post.id,
            content=post.content,
            topic_tag=post.topic_tag,
            topic_tag_label=TOPIC_TAG_LABELS.get(post.topic_tag) if post.topic_tag else None,
            image_urls=post.image_urls,
            anon_identity=anon_identity,
            resonance_count=post.resonance_count,
            comment_count=post.comment_count,
            fuzzy_time=format_fuzzy_time(post.created_at, now, random_delay),
        )


# ---------------------------------------------------------------------------
# 服务工厂
# ---------------------------------------------------------------------------

def create_treehole_service(
    settings: Any,
    redis: Any,
    content_audit_provider: str = "treehole",
    harassment_detector: HarassmentDetector | None = None,
    identity_detector: IdentityDetector | None = None,
) -> TreeholeService:
    """创建树洞服务实例。

    Args:
        settings: 应用配置
        redis: Redis 客户端
        content_audit_provider: 内容审核服务提供者（默认 treehole）
        harassment_detector: 骚扰规则引擎（可选）
        identity_detector: 脱敏提醒服务（可选）

    Returns:
        TreeholeService 实例
    """
    return TreeholeService(
        settings=settings,
        redis=redis,
        content_audit_provider=content_audit_provider,
        harassment_detector=harassment_detector,
        identity_detector=identity_detector,
    )
