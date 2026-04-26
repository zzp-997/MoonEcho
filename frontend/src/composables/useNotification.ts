/**
 * 回声 - 通知状态管理
 * 文件：src/composables/useNotification.ts
 * 说明：通知列表、未读数量、通知设置的响应式状态管理
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  getNotificationSettings,
  updateNotificationSettings,
  type NotificationItem,
  type NotificationSettings,
  type GetNotificationsParams
} from '@/api/modules/notification'
import { track, EventName } from '@/utils/tracking'

// ==================== 全局状态 ====================

/** 默认通知类型开关配置 */
export function getDefaultTypesEnabled(): NotificationSettings['types_enabled'] {
  return {
    ai_care: true,
    crisis_alert: true,
    crisis_follow: true,
    friend_request: true,
    friend_accept: true,
    treehole_reply: true,
    square_comment: true,
    square_like: true,
    weekly_report: true,
    system: true,
    update: true
  }
}

/** 通知列表 */
const notificationList = ref<NotificationItem[]>([])

/** 分页信息 */
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
  hasMore: true,
  unreadCount: 0
})

/** 加载状态 */
const isLoading = ref(false)
const isRefreshing = ref(false)
const isLoadingMore = ref(false)

/** 设置状态 */
const settings = ref<NotificationSettings | null>(null)
const isSettingsLoading = ref(false)

// ==================== Composable ====================

export function useNotification() {
  // ==================== 计算属性 ====================

  /** 未读通知数量 */
  const unreadCount = computed(() => pagination.value.unreadCount)

  /** 是否有未读通知 */
  const hasUnread = computed(() => unreadCount.value > 0)

  /** 是否有更多数据 */
  const hasMore = computed(() => pagination.value.hasMore)

  /** 已读通知列表 */
  const readNotifications = computed(() =>
    notificationList.value.filter(n => n.is_read)
  )

  /** 未读通知列表 */
  const unreadNotifications = computed(() =>
    notificationList.value.filter(n => !n.is_read)
  )

  // ==================== 列表操作 ====================

  /**
   * 加载通知列表
   * @param params 参数
   * @param append 是否追加模式
   */
  async function loadNotifications(
    params: GetNotificationsParams = {},
    append = false
  ): Promise<boolean> {
    if (isLoading.value) return false

    const page = params.page ?? (append ? pagination.value.page + 1 : 1)
    const pageSize = params.pageSize ?? pagination.value.pageSize

    if (append) {
      isLoadingMore.value = true
    } else {
      isLoading.value = true
    }

    try {
      const result = await getNotifications({ page, pageSize })

      if (append) {
        notificationList.value = [...notificationList.value, ...result.items]
      } else {
        notificationList.value = result.items || []
      }

      pagination.value = {
        page: result.pagination.page,
        pageSize: result.pagination.pageSize,
        total: result.pagination.total,
        hasMore: result.pagination.hasMore,
        unreadCount: result.pagination.unreadCount
      }

      // 追踪页面查看
      if (!append) {
        track(EventName.PAGE_VIEW, { page: 'notification_list' })
      }

      return true
    } catch (error: any) {
      console.error('加载通知列表失败:', error)
      uni.showToast({
        title: '加载失败，请稍后重试',
        icon: 'none',
        duration: 2000
      })
      return false
    } finally {
      isLoading.value = false
      isLoadingMore.value = false
    }
  }

  /**
   * 下拉刷新
   */
  async function refresh(): Promise<boolean> {
    if (isRefreshing.value) return false

    isRefreshing.value = true

    try {
      await loadNotifications({ page: 1 })
      return true
    } finally {
      isRefreshing.value = false
    }
  }

  /**
   * 上拉加载更多
   */
  async function loadMore(): Promise<boolean> {
    if (!hasMore.value || isLoadingMore.value) return false

    return loadNotifications({ page: pagination.value.page + 1 }, true)
  }

  // ==================== 单条通知操作 ====================

  /**
   * 标记单条通知为已读
   * @param id 通知ID
   */
  async function readNotification(id: string): Promise<boolean> {
    const notification = notificationList.value.find(n => n.id === id)
    if (!notification || notification.is_read) return true

    try {
      await markAsRead(id)

      // 更新本地状态
      notification.is_read = true
      pagination.value.unreadCount = Math.max(0, pagination.value.unreadCount - 1)

      // 追踪事件
      track(EventName.SETTINGS_CHANGE, {
        action: 'mark_notification_read',
        type: notification.type
      })

      return true
    } catch (error: any) {
      console.error('标记已读失败:', error)
      return false
    }
  }

  /**
   * 全部标记已读
   */
  async function readAllNotifications(): Promise<boolean> {
    if (!hasUnread.value) return true

    try {
      await markAllAsRead()

      // 更新本地状态
      notificationList.value.forEach(n => {
        n.is_read = true
      })
      pagination.value.unreadCount = 0

      // 追踪事件
      track(EventName.SETTINGS_CHANGE, {
        action: 'mark_all_read'
      })

      uni.showToast({
        title: '已全部标记已读',
        icon: 'success'
      })

      return true
    } catch (error: any) {
      console.error('全部标记已读失败:', error)
      return false
    }
  }

  /**
   * 删除单条通知（本地操作）
   * @param id 通知ID
   */
  function deleteNotification(id: string): void {
    const index = notificationList.value.findIndex(n => n.id === id)
    if (index === -1) return

    const notification = notificationList.value[index]

    // 如果是未读，更新未读数量
    if (!notification.is_read) {
      pagination.value.unreadCount = Math.max(0, pagination.value.unreadCount - 1)
    }

    // 从列表移除
    notificationList.value.splice(index, 1)
    pagination.value.total = Math.max(0, pagination.value.total - 1)

    // 追踪事件
    track(EventName.SETTINGS_CHANGE, {
      action: 'delete_notification',
      type: notification.type
    })
  }

  /**
   * 点击通知处理
   * @param notification 通知项
   */
  async function handleNotificationClick(notification: NotificationItem): Promise<void> {
    // 标记已读
    await readNotification(notification.id)

    // 追踪点击事件
    track(EventName.PAGE_VIEW, {
      page: 'notification_click',
      type: notification.type
    })
  }

  // ==================== 设置操作 ====================

  /**
   * 加载通知设置
   */
  async function loadSettings(): Promise<boolean> {
    if (isSettingsLoading.value) return false

    isSettingsLoading.value = true

    try {
      const result = await getNotificationSettings()
      settings.value = {
        push_enabled: result.push_enabled ?? true,
        types_enabled: result.types_enabled ?? getDefaultTypesEnabled()
      }
      return true
    } catch (error: any) {
      console.error('加载通知设置失败:', error)
      uni.showToast({
        title: '加载设置失败',
        icon: 'none',
        duration: 2000
      })
      return false
    } finally {
      isSettingsLoading.value = false
    }
  }

  /**
   * 更新推送总开关
   * @param enabled 是否开启
   */
  async function updatePushEnabled(enabled: boolean): Promise<boolean> {
    try {
      await updateNotificationSettings({ push_enabled: enabled })

      if (settings.value) {
        settings.value.push_enabled = enabled
      }

      // 追踪设置变更
      track(EventName.SETTINGS_CHANGE, {
        setting: 'push_enabled',
        value: enabled
      })

      return true
    } catch (error: any) {
      console.error('更新推送设置失败:', error)
      return false
    }
  }

  /**
   * 更新单类型通知开关
   * @param type 通知类型
   * @param enabled 是否开启
   */
  async function updateTypeEnabled(
    type: keyof NotificationSettings['types_enabled'],
    enabled: boolean
  ): Promise<boolean> {
    // 危机干预类型不可关闭
    if (type === 'crisis_alert' || type === 'crisis_follow') {
      uni.showToast({
        title: '危机干预通知不可关闭',
        icon: 'none'
      })
      return false
    }

    try {
      await updateNotificationSettings({
        types_enabled: { [type]: enabled }
      })

      if (settings.value) {
        settings.value.types_enabled[type] = enabled
      }

      // 追踪设置变更
      track(EventName.SETTINGS_CHANGE, {
        setting: `type_${type}`,
        value: enabled
      })

      uni.showToast({
        title: '设置已保存',
        icon: 'success',
        duration: 1500
      })

      return true
    } catch (error: any) {
      console.error('更新通知类型设置失败:', error)
      return false
    }
  }

  // ==================== 轮询刷新 ====================

/** 轮询定时器和引用计数（模块级，避免多实例冲突） */
let pollingTimer: ReturnType<typeof setInterval> | null = null
let pollingRefCount = 0

/**
 * 开始轮询未读数量
 * @param interval 轮询间隔（毫秒）
 */
function startPolling(interval = 30000): void {
  pollingRefCount++

  // 如果已有定时器在运行，不重复创建
  if (pollingTimer) {
    return
  }

  // 立即刷新一次
  refreshUnreadCount()

  pollingTimer = setInterval(() => {
    refreshUnreadCount()
  }, interval)
}

/**
 * 停止轮询
 */
function stopPolling(): void {
  pollingRefCount--

  // 只有当所有调用方都停止时才清除定时器
  if (pollingRefCount <= 0 && pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
    pollingRefCount = 0
  }
}

  /**
   * 仅刷新未读数量
   */
  async function refreshUnreadCount(): Promise<void> {
    try {
      const result = await getUnreadCount()
      pagination.value.unreadCount = result.count
    } catch (error) {
      console.error('刷新未读数量失败:', error)
    }
  }

  /**
   * 获取未读数量（别名方法，用于简化调用）
   */
  async function fetchUnreadCount(): Promise<number> {
    await refreshUnreadCount()
    return pagination.value.unreadCount
  }

  // ==================== 生命周期 ====================

  /**
   * 在页面中使用时的初始化
   */
  function useNotificationPage() {
    onMounted(() => {
      loadNotifications()
    })

    onUnmounted(() => {
      stopPolling()
    })
  }

  /**
   * 在设置页中使用时的初始化
   */
  function useNotificationSettingsPage() {
    onMounted(() => {
      loadSettings()
    })
  }

  return {
    // 状态
    notificationList,
    pagination,
    isLoading,
    isRefreshing,
    isLoadingMore,
    settings,
    isSettingsLoading,

    // 计算属性
    unreadCount,
    hasUnread,
    hasMore,
    readNotifications,
    unreadNotifications,

    // 列表操作
    loadNotifications,
    refresh,
    loadMore,
    readNotification,
    readAllNotifications,
    deleteNotification,
    handleNotificationClick,

    // 设置操作
    loadSettings,
    updatePushEnabled,
    updateTypeEnabled,

    // 轮询
    startPolling,
    stopPolling,
    refreshUnreadCount,
    fetchUnreadCount,

    // 生命周期
    useNotificationPage,
    useNotificationSettingsPage
  }
}

export default useNotification
