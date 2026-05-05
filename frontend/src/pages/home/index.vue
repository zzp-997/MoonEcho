<template>
  <view class="home-page">
    <!-- 顶部状态栏 -->
    <view class="status-bar" :style="{ height: statusBarHeight + 'px' }" />

    <!-- 自定义导航栏 -->
    <view class="nav-header">
      <view class="header-left">
        <text class="brand-name">回声</text>
        <text class="brand-slogan">深夜情绪急救站</text>
      </view>
      <view class="header-right">
        <!-- 通知入口 -->
        <view class="notification-btn" @tap="handleNotification">
          <view class="nav-icon-wrapper">
            <text class="nav-icon-text">通知</text>
          </view>
          <view v-if="unreadCount > 0" class="unread-badge">
            <text class="badge-text">{{ unreadCount > 99 ? '99+' : unreadCount }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 下拉刷新区域 -->
    <scroll-view
      class="page-content"
      scroll-y
      :refresher-enabled="true"
      :refresher-triggered="isRefreshing"
      @refresherrefresh="handleRefresh"
    >
      <!-- 情绪色调条 -->
      <EmotionBar
        :has-record-today="hasRecordToday"
        :today-emotion="todayEmotion"
        :streak-days="streakDays"
        @tap="handleEmotionBarTap"
      />

      <!-- AI 对话入口 -->
      <view class="ai-entry-card" @tap="handleAIEntry">
        <view class="ai-avatar" :style="{ backgroundColor: currentPersonalityColor }">
          <text class="avatar-text">{{ currentPersonalityName.charAt(0) }}</text>
        </view>
        <view class="ai-content">
          <view class="ai-header">
            <text class="ai-name">{{ currentPersonalityName }}</text>
            <view class="online-dot" />
          </view>
          <text class="ai-preview">{{ lastMessagePreview || greetingText }}</text>
        </view>
        <view class="ai-arrow">
          <text class="arrow-text">&gt;</text>
        </view>
      </view>

      <!-- 快捷功能入口 -->
      <view class="quick-actions">
        <view class="action-item" @tap="handleQuickAction('diary')">
          <view class="action-icon diary-icon">
            <text class="action-icon-text">记</text>
          </view>
          <text class="action-label">记日记</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('treehole')">
          <view class="action-icon treehole-icon">
            <text class="action-icon-text">洞</text>
          </view>
          <text class="action-label">树洞</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('square')">
          <view class="action-icon square-icon">
            <text class="action-icon-text">动</text>
          </view>
          <text class="action-label">动态</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('report')">
          <view class="action-icon report-icon">
            <text class="action-icon-text">报</text>
          </view>
          <text class="action-label">周报</text>
        </view>
      </view>

      <!-- 近期动态预览 -->
      <view v-if="recentFeeds.length > 0" class="recent-section">
        <view class="section-header">
          <text class="section-title">近期动态</text>
          <view class="section-more" @tap="handleMoreFeeds">
            <text class="more-text">更多</text>
            <text class="more-arrow">&gt;</text>
          </view>
        </view>
        <view class="feeds-preview">
          <view
            v-for="feed in recentFeeds.slice(0, 3)"
            :key="feed.id"
            class="feed-card"
            @tap="handleFeedTap(feed)"
          >
            <view class="feed-header">
              <view class="feed-avatar">
                <text class="avatar-text">{{ feed.isAnonymous ? '匿' : feed.authorNickname?.charAt(0) || '用' }}</text>
              </view>
              <view class="feed-info">
                <text class="feed-author">{{ feed.isAnonymous ? '匿名用户' : feed.authorNickname }}</text>
                <text class="feed-time">{{ formatTime(feed.createdAt) }}</text>
              </view>
            </view>
            <text class="feed-content">{{ feed.content }}</text>
            <view class="feed-stats">
              <text class="stat-item">{{ feed.likeCount || 0 }} 赞</text>
              <text class="stat-item">{{ feed.commentCount || 0 }} 评论</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 空状态提示 -->
      <view v-else class="empty-section">
        <view class="empty-illustration">
          <text class="empty-icon">深夜</text>
        </view>
        <text class="empty-title">开始你的情绪之旅</text>
        <text class="empty-hint">记录心情，与AI朋友聊聊</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom + 'px' }" />
    </scroll-view>

    <!-- ActionSheet 发布选择 -->
    <view v-if="showActionSheet" class="action-sheet-overlay" @tap="closeActionSheet">
      <view class="action-sheet" @tap.stop>
        <view class="sheet-title">
          <text class="title-text">选择发布类型</text>
        </view>
        <view class="sheet-options">
          <view class="sheet-option" @tap="handlePublishOption('treehole')">
            <view class="option-icon-wrapper treehole-option">
              <text class="option-icon-text">洞</text>
            </view>
            <view class="option-content">
              <text class="option-title">发布树洞吐槽</text>
              <text class="option-desc">匿名宣泄，获得共鸣</text>
            </view>
          </view>
          <view class="sheet-option" @tap="handlePublishOption('dynamic')">
            <view class="option-icon-wrapper dynamic-option">
              <text class="option-icon-text">动</text>
            </view>
            <view class="option-content">
              <text class="option-title">发布动态</text>
              <text class="option-desc">实名分享，连接好友</text>
            </view>
          </view>
          <view class="sheet-option" @tap="handlePublishOption('diary')">
            <view class="option-icon-wrapper diary-option">
              <text class="option-icon-text">记</text>
            </view>
            <view class="option-content">
              <text class="option-title">记录情绪</text>
              <text class="option-desc">写下今天的心情</text>
            </view>
          </view>
        </view>
        <view class="sheet-cancel" @tap="closeActionSheet">
          <text class="cancel-text">取消</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 首页
 * 文件：src/pages/home/index.vue
 * 说明：应用主首页，入口A — 首页轻引导
 * 功能：情绪色调条、AI对话入口、通知入口、快捷功能、底部ActionSheet
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onHide, onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { useNotification } from '@/composables/useNotification'
import { useMinorGuard } from '@/composables/useMinorGuard'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import { getDiaryList, getDiaryStats, type EmotionTone } from '@/api/diary'
import EmotionBar from '@/components/home/EmotionBar.vue'

// ==================== Store ====================

const userStore = useUserStore()
const chatStore = useChatStore()
const { unreadCount, fetchUnreadCount } = useNotification()
const { checkAccess } = useMinorGuard()

// ==================== 响应式状态 ====================

/** 状态栏高度 */
const statusBarHeight = ref(44)

/** 安全区域底部高度 */
const safeAreaBottom = ref(0)

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 今日是否已记录 */
const hasRecordToday = ref(false)

/** 今日情绪色调 */
const todayEmotion = ref<EmotionTone | null>(null)

/** 连续记录天数 */
const streakDays = ref(0)

/** 未读消息数 */
// unreadCount 已通过 useNotification 获取

/** 最近动态列表 */
interface FeedItem {
  id: string
  content: string
  authorNickname?: string
  isAnonymous: boolean
  createdAt: string
  likeCount?: number
  commentCount?: number
}

const recentFeeds = ref<FeedItem[]>([])

/** 是否显示ActionSheet */
const showActionSheet = ref(false)

/** 开场白 */
const greetingText = ref('嗨，随时都在，想聊聊吗？')

// ==================== 计算属性 ====================

/** 当前AI性格 */
const currentPersonality = computed(() => chatStore.currentPersonality)

/** 当前AI性格名称 */
const currentPersonalityName = computed(() => {
  const personalityMap: Record<string, string> = {
    xiaowen: '小温',
    laohei: '老黑',
    ali: '阿理',
  }
  return personalityMap[currentPersonality.value] || '小温'
})

/** 当前AI性格颜色 */
const currentPersonalityColor = computed(() => {
  const colorMap: Record<string, string> = {
    xiaowen: '#FFB5BA',  // 小温 - 温暖粉
    laohei: '#8B9DC3',   // 老黑 - 冷静灰蓝
    ali: '#7CB9A0',      // 阿理 - 沉稳绿
  }
  return colorMap[currentPersonality.value] || '#FFB5BA'
})

/** 最近消息预览 */
const lastMessagePreview = computed(() => {
  const messages = chatStore.messages
  if (messages.length > 0) {
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
    if (lastUserMsg) {
      return lastUserMsg.content.length > 20
        ? lastUserMsg.content.substring(0, 20) + '...'
        : lastUserMsg.content
    }
  }
  return ''
})

// ==================== 方法 ====================

/**
 * 获取系统信息
 */
function getSystemInfo(): void {
  const systemInfo = uni.getSystemInfoSync()
  statusBarHeight.value = systemInfo.statusBarHeight || 44
  safeAreaBottom.value = systemInfo.safeAreaInsets?.bottom || 0
}

/**
 * 加载今日记录状态
 */
async function loadTodayRecordStatus(): Promise<void> {
  try {
    const today = new Date().toISOString().split('T')[0]
    const [diaryList, stats] = await Promise.all([
      getDiaryList({ page: 1, page_size: 1 }),
      getDiaryStats(),
    ])

    const todayDiary = diaryList.data.find(d => d.record_date === today)
    hasRecordToday.value = !!todayDiary
    todayEmotion.value = todayDiary?.emotion_tone || null

    // 计算连续天数
    if (stats) {
      streakDays.value = calculateStreak(diaryList.data)
    }
  } catch (error) {
    console.error('加载今日记录状态失败', error)
    // 静默失败，不影响用户使用其他功能
  }
}

/**
 * 计算连续记录天数
 */
function calculateStreak(diaries: any[]): number {
  if (diaries.length === 0) return 0

  const dates = [...new Set(diaries.map(d => d.record_date))].sort().reverse()
  let streak = 0
  const today = new Date()

  for (let i = 0; i < dates.length; i++) {
    const checkDate = new Date(today)
    checkDate.setDate(checkDate.getDate() - i)
    const checkDateStr = checkDate.toISOString().split('T')[0]

    if (dates.includes(checkDateStr)) {
      streak++
    } else {
      break
    }
  }

  return streak
}

/**
 * 处理下拉刷新
 */
async function handleRefresh(): Promise<void> {
  isRefreshing.value = true

  try {
    await Promise.all([
      loadTodayRecordStatus(),
      fetchUnreadCount(),
    ])
  } finally {
    isRefreshing.value = false
    uni.stopPullDownRefresh()
  }
}

/**
 * 处理情绪色调条点击
 */
function handleEmotionBarTap(): void {
  if (hasRecordToday.value) {
    // 查看今日日记
    uni.navigateTo({ url: '/pages/diary/edit' })
  } else {
    // 去记录
    uni.navigateTo({ url: '/pages/diary/edit' })
  }
}

/**
 * 处理AI对话入口点击
 */
function handleAIEntry(): void {
  track(EventName.PAGE_VIEW, { page: 'chat_entry' })
  uni.switchTab({ url: '/pages/chat/index' })
}

/**
 * 处理通知点击
 */
function handleNotification(): void {
  track(EventName.NOTIFICATION_LIST_VIEW, { action: 'from_home' })
  uni.navigateTo({ url: '/pages/notification/list' })
}

/**
 * 处理快捷功能点击
 */
function handleQuickAction(action: string): void {
  // 青少年模式检查
  if (action === 'treehole' && !checkAccess('treehole')) {
    return
  }

  const routeConfig: Record<string, { url: string; type: 'navigate' | 'switchTab' }> = {
    diary: { url: '/pages/diary/edit', type: 'navigate' },
    treehole: { url: '/pages/treehole/index', type: 'navigate' },
    square: { url: '/pages/community/index', type: 'switchTab' },
    report: { url: '/pages/diary/weekly-report', type: 'navigate' },
  }

  const config = routeConfig[action]
  if (config) {
    if (config.type === 'switchTab') {
      uni.switchTab({ url: config.url })
    } else {
      uni.navigateTo({ url: config.url })
    }
  }
}

/**
 * 处理更多动态点击
 */
function handleMoreFeeds(): void {
  uni.switchTab({ url: '/pages/community/index' })
}

/**
 * 处理动态点击
 */
function handleFeedTap(feed: FeedItem): void {
  // 动态详情页待实现
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 格式化时间
 */
function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

/**
 * 打开发布选择
 */
function openActionSheet(): void {
  showActionSheet.value = true
}

/**
 * 关闭发布选择
 */
function closeActionSheet(): void {
  showActionSheet.value = false
}

/**
 * 处理发布选项
 */
function handlePublishOption(type: string): void {
  closeActionSheet()

  // 青少年模式检查
  if (type === 'treehole' && !checkAccess('treehole')) {
    return
  }

  const routeConfig: Record<string, { url: string; type: 'navigate' | 'switchTab' }> = {
    treehole: { url: '/pages/treehole/index', type: 'switchTab' },
    dynamic: { url: '/pages/community/index', type: 'switchTab' },
    diary: { url: '/pages/diary/edit', type: 'navigate' },
  }

  const config = routeConfig[type]
  if (config) {
    if (config.type === 'switchTab') {
      uni.switchTab({ url: config.url })
    } else {
      uni.navigateTo({ url: config.url })
    }
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSystemInfo()
})

onShow(() => {
  trackPageEnter('home')
  loadTodayRecordStatus()
  fetchUnreadCount()
})

onHide(() => {
  trackPageLeave('home')
})

onPullDownRefresh(() => {
  handleRefresh()
})
</script>

<style lang="scss" scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
}

// ==================== 状态栏 ====================

.status-bar {
  background-color: var(--bg-primary);
}

// ==================== 导航栏 ====================

.nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 var(--space-sm);
  background-color: var(--bg-primary);
}

.header-left {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--brand-primary);
}

.brand-slogan {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.header-right {
  display: flex;
  align-items: center;
}

.notification-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80rpx;
  height: 64rpx;
  padding: 0 var(--space-2xs);
  border-radius: var(--radius-md);
  background-color: var(--bg-secondary);

  &:active {
    opacity: 0.8;
  }
}

.nav-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.unread-badge {
  position: absolute;
  top: -6rpx;
  right: -6rpx;
  min-width: 32rpx;
  height: 32rpx;
  border-radius: var(--radius-full);
  background-color: var(--color-error);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6rpx;
}

.badge-text {
  font-size: 18rpx;
  color: var(--text-on-brand);
  font-weight: 600;
}

// ==================== 内容区域 ====================

.page-content {
  flex: 1;
}

// ==================== AI对话入口 ====================

.ai-entry-card {
  display: flex;
  align-items: center;
  margin: var(--space-sm);
  padding: var(--space-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.9;
  }
}

.ai-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.avatar-text {
  font-size: 36rpx;
  font-weight: 600;
  color: #1E1E1E;
}

.ai-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: var(--space-3xs);
  margin-bottom: 4rpx;
}

.ai-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.online-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background-color: var(--color-success);
}

.ai-preview {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.ai-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: var(--space-xs);
}

.arrow-text {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

// ==================== 快捷功能入口 ====================

.quick-actions {
  display: flex;
  justify-content: space-around;
  margin: var(--space-sm);
  padding: var(--space-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3xs);

  &:active {
    opacity: 0.8;
  }
}

.action-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4rpx;
}

.action-icon-text {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.diary-icon {
  background-color: rgba(255, 154, 92, 0.2);
}

.treehole-icon {
  background-color: rgba(139, 167, 196, 0.2);
}

.square-icon {
  background-color: rgba(124, 111, 224, 0.2);
}

.report-icon {
  background-color: rgba(143, 204, 160, 0.2);
}

.action-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

// ==================== 近期动态 ====================

.recent-section {
  margin: var(--space-sm);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xs);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.section-more {
  display: flex;
  align-items: center;
  gap: 4rpx;

  &:active {
    opacity: 0.8;
  }
}

.more-text {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.more-arrow {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

.feeds-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.feed-card {
  padding: var(--space-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.9;
  }
}

.feed-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.feed-avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.avatar-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.feed-info {
  display: flex;
  flex-direction: column;
}

.feed-author {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.feed-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.feed-content {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  line-height: 1.6;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: var(--space-xs);
}

.feed-stats {
  display: flex;
  gap: var(--space-sm);
}

.stat-item {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

// ==================== 空状态 ====================

.empty-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  margin: var(--space-sm);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.empty-illustration {
  margin-bottom: var(--space-sm);
}

.empty-icon {
  font-size: 48rpx;
  color: var(--text-tertiary);
}

.empty-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  text-align: center;
}

// ==================== ActionSheet ====================

.action-sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: var(--z-modal);
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.action-sheet {
  width: 100%;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding-bottom: env(safe-area-inset-bottom);
}

.sheet-title {
  padding: var(--space-sm);
  text-align: center;
  border-bottom: 1px solid var(--border-primary);
}

.title-text {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.sheet-options {
  padding: var(--space-xs);
}

.sheet-option {
  display: flex;
  align-items: center;
  padding: var(--space-sm);
  border-radius: var(--radius-md);

  &:active {
    background-color: var(--bg-secondary);
  }
}

.option-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.option-icon-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #1E1E1E;
}

.treehole-option {
  background-color: rgba(139, 167, 196, 0.3);
}

.dynamic-option {
  background-color: rgba(124, 111, 224, 0.3);
}

.diary-option {
  background-color: rgba(255, 154, 92, 0.3);
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.option-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.option-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-top: 4rpx;
}

.sheet-cancel {
  margin: var(--space-xs);
  padding: var(--space-sm);
  text-align: center;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.8;
  }
}

.cancel-text {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
