/**
 * 回声 - 举报管理 API 模块
 * 文件：src/api/modules/report.ts
 * 说明：提供用户举报提交相关的 API 接口
 */

import { api } from '../index'

// ==================== 类型定义 ====================

/** 举报类型枚举 */
export enum ReportType {
  /** 色情低俗 */
  PORN = 'porn',
  /** 广告引流 */
  AD = 'ad',
  /** 骚扰 */
  HARASSMENT = 'harassment',
  /** 辱骂攻击 */
  ABUSE = 'abuse',
  /** 诈骗 */
  SCAM = 'scam',
  /** 自杀自残倾向 */
  SELF_HARM = 'self_harm',
  /** 其他 */
  OTHER = 'other',
}

/** 举报内容类型枚举 */
export enum ReportContentType {
  /** 广场动态 */
  POST = 'post',
  /** 树洞帖子 */
  TREEHOLE_POST = 'treehole_post',
  /** 评论 */
  COMMENT = 'comment',
  /** 用户 */
  USER = 'user',
}

/** 举报类型标签映射 */
export const ReportTypeLabels: Record<ReportType, string> = {
  [ReportType.PORN]: '色情低俗',
  [ReportType.AD]: '广告引流',
  [ReportType.HARASSMENT]: '骚扰',
  [ReportType.ABUSE]: '辱骂攻击',
  [ReportType.SCAM]: '诈骗',
  [ReportType.SELF_HARM]: '自杀自残倾向',
  [ReportType.OTHER]: '其他',
}

/** 举报类型选项列表（用于UI展示） */
export const ReportTypeOptions = [
  { value: ReportType.PORN, label: ReportTypeLabels[ReportType.PORN] },
  { value: ReportType.AD, label: ReportTypeLabels[ReportType.AD] },
  { value: ReportType.HARASSMENT, label: ReportTypeLabels[ReportType.HARASSMENT] },
  { value: ReportType.ABUSE, label: ReportTypeLabels[ReportType.ABUSE] },
  { value: ReportType.SCAM, label: ReportTypeLabels[ReportType.SCAM] },
  { value: ReportType.SELF_HARM, label: ReportTypeLabels[ReportType.SELF_HARM] },
  { value: ReportType.OTHER, label: ReportTypeLabels[ReportType.OTHER] },
]

// ==================== 请求/响应类型 ====================

/** 举报提交请求 */
export interface ReportCreateRequest {
  /** 举报内容类型 */
  reported_content_type: ReportContentType
  /** 举报内容ID（举报用户时可为空） */
  reported_content_id?: string
  /** 被举报用户ID（可选） */
  reported_user_id?: string
  /** 举报分类 */
  report_type: ReportType
  /** 详细原因（可选，最多500字） */
  reason?: string
}

/** 举报提交响应 */
export interface ReportCreateResponse {
  /** 举报记录ID */
  id: string
  /** 举报状态 */
  status: string
  /** 提示信息 */
  message: string
  /** 创建时间 */
  created_at: string
}

// ==================== API 方法 ====================

/**
 * 提交举报
 * @param data 举报请求数据
 * @returns 举报创建结果
 */
export async function createReport(data: ReportCreateRequest): Promise<ReportCreateResponse> {
  return api.post<ReportCreateResponse>('/reports', data)
}

/**
 * 举报广场动态
 * @param postId 动态ID
 * @param reportType 举报类型
 * @param reason 详细原因（可选）
 */
export async function reportPost(
  postId: string,
  reportType: ReportType,
  reason?: string
): Promise<ReportCreateResponse> {
  return createReport({
    reported_content_type: ReportContentType.POST,
    reported_content_id: postId,
    report_type: reportType,
    reason,
  })
}

/**
 * 举报树洞帖子
 * @param postId 帖子ID
 * @param reportType 举报类型
 * @param reason 详细原因（可选）
 */
export async function reportTreeholePost(
  postId: string,
  reportType: ReportType,
  reason?: string
): Promise<ReportCreateResponse> {
  return createReport({
    reported_content_type: ReportContentType.TREEHOLE_POST,
    reported_content_id: postId,
    report_type: reportType,
    reason,
  })
}

/**
 * 举报评论
 * @param commentId 评论ID
 * @param reportType 举报类型
 * @param reason 详细原因（可选）
 */
export async function reportComment(
  commentId: string,
  reportType: ReportType,
  reason?: string
): Promise<ReportCreateResponse> {
  return createReport({
    reported_content_type: ReportContentType.COMMENT,
    reported_content_id: commentId,
    report_type: reportType,
    reason,
  })
}

/**
 * 举报用户
 * @param userId 用户ID
 * @param reportType 举报类型
 * @param reason 详细原因（可选）
 */
export async function reportUser(
  userId: string,
  reportType: ReportType,
  reason?: string
): Promise<ReportCreateResponse> {
  return createReport({
    reported_content_type: ReportContentType.USER,
    reported_user_id: userId,
    report_type: reportType,
    reason,
  })
}

export default {
  createReport,
  reportPost,
  reportTreeholePost,
  reportComment,
  reportUser,
}
