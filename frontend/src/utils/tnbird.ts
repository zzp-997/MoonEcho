/**
 * 回声 - 图鸟风格工具函数（Vue3 版本）
 * 文件：src/utils/tnbird.ts
 * 说明：颜色工具、渐变工具等，从图鸟 Vue2 迁移并简化
 */

// 命名色彩列表
const TN_COLORS = [
  'red', 'purplered', 'purple', 'bluepurple', 'aquablue',
  'blue', 'indigo', 'cyan', 'teal', 'green', 'yellowgreen',
  'lime', 'yellow', 'orangeyellow', 'orange', 'orangered',
  'brown', 'grey', 'gray'
] as const

export type TnColorName = typeof TN_COLORS[number]

// 渐变色数量
const GRADIENT_COUNT = 16

/**
 * 获取图鸟命名色彩列表
 */
export function getTnColorList(): readonly string[] {
  return TN_COLORS
}

/**
 * 随机获取一个命名色名称
 */
export function getRandomColorName(): TnColorName {
  return TN_COLORS[Math.floor(Math.random() * TN_COLORS.length)]
}

/**
 * 获取随机渐变编号（1-16）
 */
export function getRandomGradientIndex(): number {
  return Math.floor(Math.random() * GRADIENT_COUNT) + 1
}

/**
 * 获取渐变色 CSS 类名
 */
export function getGradientClass(index: number): string {
  return `tn-gradient-${index}`
}

/**
 * 获取彩色阴影 CSS 类名
 */
export function getShadowClass(colorName: TnColorName): string {
  return `tn-shadow-${colorName}`
}

/**
 * 获取背景色 CSS 类名
 */
export function getBgClass(colorName: TnColorName, variant: '' | '--light' | '--dark' = ''): string {
  return `tn-bg-${colorName}${variant}`
}

/**
 * 获取文字色 CSS 类名
 */
export function getColorClass(colorName: TnColorName): string {
  return `tn-color-${colorName}`
}
