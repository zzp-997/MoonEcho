/**
 * 回声 - 日记接口
 * 文件：src/api/modules/diary.ts
 * 说明：情绪日记相关接口（重定向到顶层 api/diary.ts）
 *
 * 注意：此文件已废弃，请使用 @/api/diary 中的接口。
 * 保留此文件仅为向后兼容，实际接口路径以 api/diary.ts 为准。
 */

// 从顶层 api/diary.ts 重新导出，保持兼容性
export {
  createDiary,
  getDiaryDetail,
  updateDiary,
  deleteDiary,
  getDiaryList,
  getDiaryStats,
  getPrivacyConsent,
  setPrivacyConsent,
  deleteAllDiaries,
  exportDiaries,
  getWeeklyReport,
  getWeeklyReportHistory,
  // 类型
  type EmotionTone,
  type CreateDiaryParams,
  type DiaryResponse,
  type WeeklyReportResponse,
  type EmptyWeeklyReportResponse,
} from '../diary'
