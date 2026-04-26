/**
 * 回声 - 格式化工具
 * 文件：src/utils/format.ts
 * 说明：通用格式化函数
 */

/**
 * 手机号脱敏
 * 13812345678 -> 138****5678
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 截断文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * 格式化数字（带单位）
 */
export function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return String(num)
}

/**
 * 格式化时长（秒 -> 可读格式）
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  if (remainingMinutes === 0) return `${hours}小时`
  return `${hours}小时${remainingMinutes}分钟`
}

/**
 * 格式化相对时间
 * 将 ISO 时间字符串转换为相对时间描述
 * @param time ISO 格式时间字符串
 * @returns 相对时间描述（刚刚、几分钟前、几小时前、昨天、几天前、具体日期）
 */
export function formatRelativeTime(time: string | Date): string {
  if (!time) return ''

  // 解析时间
  const date = typeof time === 'string' ? new Date(time) : time
  const now = new Date()

  // 计算时间差（毫秒）
  const diff = now.getTime() - date.getTime()

  // 1分钟内
  if (diff < 60 * 1000) {
    return '刚刚'
  }

  // 1小时内
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes}分钟前`
  }

  // 今天内
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  if (date >= todayStart) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours}小时前`
  }

  // 昨天
  const yesterdayStart = new Date(todayStart.getTime() - 24 * 60 * 60 * 1000)
  if (date >= yesterdayStart) {
    return '昨天'
  }

  // 7天内
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days}天前`
  }

  // 今年内
  if (date.getFullYear() === now.getFullYear()) {
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}-${day}`
  }

  // 更早
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
