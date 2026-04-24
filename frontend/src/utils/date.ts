/**
 * 回声 - 日期处理工具
 * 文件：src/utils/date.ts
 * 说明：日期格式化、时间计算等通用工具
 */

/**
 * 格式化日期
 * @param date 日期对象或时间戳
 * @param format 格式化模板
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: Date | number | string, format = 'YYYY-MM-DD HH:mm:ss'): string {
  const d = date instanceof Date ? date : new Date(date)

  const year = d.getFullYear().toString()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hours = d.getHours().toString().padStart(2, '0')
  const minutes = d.getMinutes().toString().padStart(2, '0')
  const seconds = d.getSeconds().toString().padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化相对时间
 * @param date 日期对象或时间戳
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: Date | number | string): string {
  const d = date instanceof Date ? date : new Date(date)
  const now = Date.now()
  const diff = now - d.getTime()

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  return formatDate(d, 'YYYY-MM-DD')
}

/**
 * 获取今日日期字符串
 * @returns YYYY-MM-DD 格式
 */
export function getTodayStr(): string {
  return formatDate(new Date(), 'YYYY-MM-DD')
}

/**
 * 获取当前时间段
 * @returns 时间段标识
 */
export function getTimePeriod(): 'deep_night' | 'late_night' | 'early_morning' | 'daytime' {
  const hour = new Date().getHours()
  if (hour >= 23 || hour < 2) return 'deep_night'
  if (hour >= 2 && hour < 5) return 'late_night'
  if (hour >= 5 && hour < 7) return 'early_morning'
  return 'daytime'
}

/**
 * 判断是否为深夜时段
 */
export function isLateNight(): boolean {
  const period = getTimePeriod()
  return period === 'deep_night' || period === 'late_night'
}
