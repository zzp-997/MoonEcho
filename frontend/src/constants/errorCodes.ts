/**
 * 回声 - 错误码常量定义
 * 文件：src/constants/errorCodes.ts
 * 说明：前后端统一使用语义化错误码，便于定位问题和国际化处理
 * 参考：tech_architecture.md 第三章
 */

// ==================== 错误码枚举 ====================

/**
 * 错误码常量
 * 与后端 tech_architecture.md 保持一致
 */
export const ErrorCodes = {
  // ========== 通用错误 ==========
  /** 参数验证失败 */
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  /** 参数格式无效 */
  INVALID_PARAMETER: 'INVALID_PARAMETER',
  /** 缺少必填参数 */
  MISSING_PARAMETER: 'MISSING_PARAMETER',
  /** 请求频率超限 */
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  /** 服务器内部错误 */
  INTERNAL_ERROR: 'INTERNAL_ERROR',

  // ========== 认证相关 ==========
  /** 未授权访问 */
  UNAUTHORIZED: 'UNAUTHORIZED',
  /** Token已过期 */
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  /** Token无效 */
  TOKEN_INVALID: 'TOKEN_INVALID',
  /** 缺少Token */
  TOKEN_MISSING: 'TOKEN_MISSING',
  /** 验证码已过期 */
  VERIFICATION_CODE_EXPIRED: 'VERIFICATION_CODE_EXPIRED',
  /** 验证码错误 */
  VERIFICATION_CODE_INVALID: 'VERIFICATION_CODE_INVALID',
  /** 验证码发送过于频繁 */
  VERIFICATION_CODE_TOO_FREQUENT: 'VERIFICATION_CODE_TOO_FREQUENT',
  /** 密码错误 */
  PASSWORD_INCORRECT: 'PASSWORD_INCORRECT',

  // ========== 用户相关 ==========
  /** 用户不存在 */
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  /** 用户已存在 */
  USER_ALREADY_EXISTS: 'USER_ALREADY_EXISTS',
  /** 用户已被禁用 */
  USER_DISABLED: 'USER_DISABLED',
  /** 用户未成年限制 */
  USER_UNDERAGE: 'USER_UNDERAGE',
  /** 用户资料不完整 */
  PROFILE_INCOMPLETE: 'PROFILE_INCOMPLETE',

  // ========== 内容相关 ==========
  /** 内容包含敏感信息 */
  CONTENT_SENSITIVE: 'CONTENT_SENSITIVE',
  /** 内容超出长度限制 */
  CONTENT_TOO_LONG: 'CONTENT_TOO_LONG',
  /** 内容为空 */
  CONTENT_EMPTY: 'CONTENT_EMPTY',
  /** 内容审核未通过 */
  CONTENT_AUDIT_FAILED: 'CONTENT_AUDIT_FAILED',
  /** 动态不存在 */
  POST_NOT_FOUND: 'POST_NOT_FOUND',
  /** 动态已被删除 */
  POST_DELETED: 'POST_DELETED',
  /** 无权访问该动态 */
  POST_ACCESS_DENIED: 'POST_ACCESS_DENIED',
  /** 发布频率过高 */
  PUBLISH_TOO_FREQUENT: 'PUBLISH_TOO_FREQUENT',

  // ========== 社交相关 ==========
  /** 好友申请不存在 */
  FRIEND_REQUEST_NOT_FOUND: 'FRIEND_REQUEST_NOT_FOUND',
  /** 好友申请已过期 */
  FRIEND_REQUEST_EXPIRED: 'FRIEND_REQUEST_EXPIRED',
  /** 好友申请已处理 */
  FRIEND_REQUEST_ALREADY_HANDLED: 'FRIEND_REQUEST_ALREADY_HANDLED',
  /** 已经是好友关系 */
  ALREADY_FRIENDS: 'ALREADY_FRIENDS',
  /** 不能添加自己为好友 */
  CANNOT_ADD_SELF: 'CANNOT_ADD_SELF',
  /** 好友数量达到上限 */
  FRIEND_LIMIT_EXCEEDED: 'FRIEND_LIMIT_EXCEEDED',
  /** 被对方拉黑 */
  BLOCKED_BY_USER: 'BLOCKED_BY_USER',
  /** 权限不足 */
  PERMISSION_DENIED: 'PERMISSION_DENIED',

  // ========== AI服务相关 ==========
  /** AI服务暂时不可用 */
  AI_SERVICE_UNAVAILABLE: 'AI_SERVICE_UNAVAILABLE',
  /** AI服务响应超时 */
  AI_SERVICE_TIMEOUT: 'AI_SERVICE_TIMEOUT',
  /** AI使用额度已用尽 */
  AI_QUOTA_EXCEEDED: 'AI_QUOTA_EXCEEDED',
  /** AI对话上下文过长 */
  AI_CONTEXT_TOO_LONG: 'AI_CONTEXT_TOO_LONG',

  // ========== 文件相关 ==========
  /** 文件大小超限 */
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  /** 文件类型不允许 */
  FILE_TYPE_NOT_ALLOWED: 'FILE_TYPE_NOT_ALLOWED',
  /** 文件上传失败 */
  FILE_UPLOAD_FAILED: 'FILE_UPLOAD_FAILED',

  // ========== 日记相关 ==========
  /** 日记不存在 */
  DIARY_NOT_FOUND: 'DIARY_NOT_FOUND',
  /** 无权访问该日记 */
  DIARY_ACCESS_DENIED: 'DIARY_ACCESS_DENIED',
  /** 当日日记已存在 */
  DIARY_ALREADY_EXISTS: 'DIARY_ALREADY_EXISTS',
  /** 日记加密/解密失败 */
  DIARY_ENCRYPTION_ERROR: 'DIARY_ENCRYPTION_ERROR',
} as const

// ==================== 错误码类型 ====================

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes]

// ==================== 错误消息映射 ====================

/**
 * 错误消息映射（中文）
 * 用于前端用户提示
 */
export const ErrorMessageMap: Record<ErrorCode, string> = {
  // 通用错误
  VALIDATION_ERROR: '参数错误，请检查输入',
  INVALID_PARAMETER: '参数格式无效',
  MISSING_PARAMETER: '缺少必要参数',
  RATE_LIMIT_EXCEEDED: '请求过于频繁，请稍后再试',
  INTERNAL_ERROR: '服务开小差了，请稍后重试',

  // 认证相关
  UNAUTHORIZED: '请先登录',
  TOKEN_EXPIRED: '登录已过期，请重新登录',
  TOKEN_INVALID: '登录状态无效，请重新登录',
  TOKEN_MISSING: '缺少登录凭证',
  VERIFICATION_CODE_EXPIRED: '验证码已过期，请重新获取',
  VERIFICATION_CODE_INVALID: '验证码错误',
  VERIFICATION_CODE_TOO_FREQUENT: '验证码发送过于频繁，请稍后再试',
  PASSWORD_INCORRECT: '密码错误',

  // 用户相关
  USER_NOT_FOUND: '用户不存在',
  USER_ALREADY_EXISTS: '该手机号已注册',
  USER_DISABLED: '账号已被禁用',
  USER_UNDERAGE: '青少年模式下无法使用此功能',
  PROFILE_INCOMPLETE: '请先完善个人资料',

  // 内容相关
  CONTENT_SENSITIVE: '内容包含敏感信息，请修改后重试',
  CONTENT_TOO_LONG: '内容超出长度限制',
  CONTENT_EMPTY: '内容不能为空',
  CONTENT_AUDIT_FAILED: '内容审核未通过',
  POST_NOT_FOUND: '内容不存在或已删除',
  POST_DELETED: '该内容已被删除',
  POST_ACCESS_DENIED: '无权访问此内容',
  PUBLISH_TOO_FREQUENT: '发布频率过高，请稍后再试',

  // 社交相关
  FRIEND_REQUEST_NOT_FOUND: '好友申请不存在',
  FRIEND_REQUEST_EXPIRED: '好友申请已过期',
  FRIEND_REQUEST_ALREADY_HANDLED: '好友申请已处理',
  ALREADY_FRIENDS: '已经是好友了',
  CANNOT_ADD_SELF: '不能添加自己为好友',
  FRIEND_LIMIT_EXCEEDED: '好友数量已达上限',
  BLOCKED_BY_USER: '已被对方拉黑',
  PERMISSION_DENIED: '权限不足',

  // AI服务相关
  AI_SERVICE_UNAVAILABLE: 'AI服务暂时不可用，请稍后再试',
  AI_SERVICE_TIMEOUT: 'AI响应超时，请重试',
  AI_QUOTA_EXCEEDED: '今日对话次数已用完，明天再来吧',
  AI_CONTEXT_TOO_LONG: '对话内容过长，请开始新对话',

  // 文件相关
  FILE_TOO_LARGE: '文件大小超过限制',
  FILE_TYPE_NOT_ALLOWED: '文件格式不支持',
  FILE_UPLOAD_FAILED: '文件上传失败，请重试',

  // 日记相关
  DIARY_NOT_FOUND: '日记不存在',
  DIARY_ACCESS_DENIED: '无权访问此日记',
  DIARY_ALREADY_EXISTS: '今天已经写过日记了',
  DIARY_ENCRYPTION_ERROR: '日记加密处理失败',
}

/**
 * 获取错误消息
 * @param code 错误码
 * @param defaultMessage 默认消息（可选）
 * @returns 错误消息
 */
export function getErrorMessage(code: ErrorCode | string, defaultMessage?: string): string {
  return ErrorMessageMap[code as ErrorCode] || defaultMessage || '操作失败'
}

// ==================== 需要特殊处理的错误码 ====================

/**
 * 需要跳转登录页的错误码
 */
export const AuthRequiredErrors: ErrorCode[] = [
  ErrorCodes.UNAUTHORIZED,
  ErrorCodes.TOKEN_EXPIRED,
  ErrorCodes.TOKEN_INVALID,
  ErrorCodes.TOKEN_MISSING,
]

/**
 * 需要静默处理的错误码（不显示Toast）
 */
export const SilentErrors: ErrorCode[] = [
  // 可以根据需要添加
]

/**
 * 青少年模式相关错误码
 */
export const TeenModeErrors: ErrorCode[] = [
  ErrorCodes.USER_UNDERAGE,
]

/**
 * 检查是否为认证相关错误
 */
export function isAuthError(code: ErrorCode | string): boolean {
  return AuthRequiredErrors.includes(code as ErrorCode)
}

/**
 * 检查是否为青少年模式错误
 */
export function isTeenModeError(code: ErrorCode | string): boolean {
  return TeenModeErrors.includes(code as ErrorCode)
}
