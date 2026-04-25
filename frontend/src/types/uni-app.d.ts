/**
 * 回声 - uni-app 类型扩展
 * 文件：src/types/uni-app.d.ts
 * 说明：扩展 uni-app 官方类型定义，补充缺失的类型声明
 * 注意：此文件必须不包含任何 export 语句，否则无法进行全局接口合并
 */

// ==================== Vue 组件类型声明 ====================

declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

// ==================== Uni 接口扩展 ====================

/** 页面样式设置参数 */
interface SetPageStyleOptions {
  /** 页面样式配置 */
  style: Record<string, any>
}

/** 扩展 Uni 全局对象，补充缺失的方法 */
interface Uni {
  /** 设置当前页面样式（部分平台支持） */
  setPageStyle(options: SetPageStyleOptions): void
}

// ==================== Plus 接口扩展 ====================

/** 全局事件对象（APP-PLUS 平台专用） */
interface PlusGlobalEvent {
  /** 添加事件监听 */
  addEventListener(event: string, callback: () => void): void
  /** 移除事件监听 */
  removeEventListener(event: string, callback: () => void): void
}

/** 扩展 Plus 全局对象，补充缺失的属性 */
interface Plus {
  /** 全局事件对象 */
  globalEvent: PlusGlobalEvent
}
