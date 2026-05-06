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
            <wd-icon name="bell" size="20px" color="var(--text-primary)" />
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
        <wd-icon name="arrow-right" size="18px" color="var(--text-muted)" />
      </view>

      <!-- 快捷功能入口 -->
      <view class="quick-actions">
        <view class="action-item" @tap="handleQuickAction('diary')">
          <view class="action-icon diary-icon">
            <wd-icon name="calendar" size="24px" color="var(--mood-warm)" />
          </view>
          <text class="action-label">记日记</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('treehole')">
          <view class="action-icon treehole-icon">
            <wd-icon name="chat" size="24px" color="var(--mood-low)" />
          </view>
          <text class="action-label">树洞</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('square')">
          <view class="action-icon square-icon">
            <wd-icon name="star" size="24px" color="var(--brand-primary)" />
          </view>
          <text class="action-label">动态</text>
        </view>
        <view class="action-item" @tap="handleQuickAction('report')">
          <view class="action-icon report-icon">
            <wd-icon name="chart" size="24px" color="var(--mood-calm)" />
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
            <wd-icon name="arrow-right" size="14px" color="var(--text-muted)" />
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
                <text class="feed-avatar-text">{{ feed.isAnonymous ? '匿' : feed.authorNickname?.charAt(0) || '用' }}</text>
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
        <wd-icon name="moon" size="48px" color="var(--brand-primary)" custom-style="margin-bottom: var(--space-sm)" />
        <text class="empty-title">开始你的情绪之旅</text>
        <text class="empty-hint">记录心情，与AI朋友聊聊</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom + 'px' }" />
    </scroll-view>

    <!-- ActionSheet 发布选择 -->
    <wd-action-sheet v-model="showActionSheet" title="选择发布类型">
      <view class="sheet-options">
        <view class="sheet-option" @tap="handlePublishOption('treehole')">
          <view class="option-icon-wrapper treehole-option">
            <wd-icon name="chat" size="24px" color="var(--mood-low)" />
          </view>
          <view class="option-content">
            <text class="option-title">发布树洞吐槽</text>
            <text class="option-desc">匿名宣泄，获得共鸣</text>
          </view>
        </view>
        <view class="sheet-option" @tap="handlePublishOption('dynamic')">
          <view class="option-icon-wrapper dynamic-option">
            <wd-icon name="star" size="24px" color="var(--brand-primary)" />
          </view>
          <view class="option-content">
            <text class="option-title">发布动态</text>
            <text class="option-desc">实名分享，连接好友</text>
          </view>
        </view>
        <view class="sheet-option" @tap="handlePublishOption('diary')">
          <view class="option-icon-wrapper diary-option">
            <wd-icon name="calendar" size="24px" color="var(--mood-warm)" />
          </view>
          <view class="option-content">
            <text class="option-title">记录情绪</text>
            <text class="option-desc">写下今天的心情</text>
          </view>
        </view>
      </view>
    </wd-action-sheet>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 首页
 * 文件：src/pages/home/index.vue
 * 说明：应用主首页，入口A — 首页轻引导
 * 功能：情绪色调条、AI对话入口、通知入口、快捷功能、底部ActionSheet
 * 设计风格：纯净白 · 暖橘
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
    xiaowen: '#FFB5BA',
    laohei: '#8B9DC3',
    ali: '#7CB9A0',
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

function getSystemInfo(): void {
  const systemInfo = uni.getSystemInfoSync()
  statusBarHeight.value = systemInfo.statusBarHeight || 44
  safeAreaBottom.value = systemInfo.safeAreaInsets?.bottom || 0
}

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

    if (stats) {
      streakDays.value = calculateStreak(diaryList.data)
    }
  } catch (error) {
    console.error('加载今日记录状态失败', error)
  }
}

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

function handleEmotionBarTap(): void {
  uni.navigateTo({ url: '/pages/diary/edit' })
}

function handleAIEntry(): void {
  track(EventName.PAGE_VIEW, { page: 'chat_entry' })
  uni.navigateTo({ url: '/pages/chat/index' })
}

function handleNotification(): void {
  track(EventName.NOTIFICATION_LIST_VIEW, { action: 'from_home' })
  uni.navigateTo({ url: '/pages/notification/list' })
}

function handleQuickAction(action: string): void {
  if (action === 'treehole' && !checkAccess('treehole')) {
    return
  }

  const routeConfig: Record<string, { url: string; type: 'navigate' | 'switchTab' }> = {
    diary: { url: '/pages/diary/edit', type: 'navigate' },
    treehole: { url: '/pagesSocial/treehole/index', type: 'navigate' },
    square: { url: '/pagesSocial/square/index', type: 'switchTab' },
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

function handleMoreFeeds(): void {
  uni.switchTab({ url: '/pagesSocial/square/index' })
}

function handleFeedTap(feed: FeedItem): void {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

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

function openActionSheet(): void {
  showActionSheet.value = true
}

function closeActionSheet(): void {
  showActionSheet.value = false
}

function handlePublishOption(type: string): void {
  closeActionSheet()

  if (type === 'treehole' && !checkAccess('treehole')) {
    return
  }

  const routeConfig: Record<string, { url: string; type: 'navigate' | 'switchTab' }> = {
    treehole: { url: '/pagesSocial/treehole/index', type: 'navigate' },
    dynamic: { url: '/pagesSocial/square/index', type: 'switchTab' },
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
// ==================== 纯净白 · 暖橘 首页样式 ====================

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
  color: var(--text-primary);
}

.brand-slogan {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
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
  min-width: 72rpx;
  height: 64rpx;
  padding: 0 var(--space-xs);
  border-radius: var(--radius-std);
  background-color: var(--bg-elevated);
  box-shadow: var(--shadow-card);

  &:active {
    opacity: 0.8;
  }
}

.nav-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
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
  color: var(--text-inverse);
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
  padding: var(--space-md);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);

  &:active {
    opacity: 0.8;
  }
}

.ai-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-sm);
}

.avatar-text {
  font-size: 36rpx;
  font-weight: 600;
  color: var(--text-inverse);
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
  gap: var(--space-2xs);
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
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

// ==================== 快捷功能入口 ====================

.quick-actions {
  display: flex;
  justify-content: space-around;
  margin: var(--space-sm);
  padding: var(--space-md);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2xs);

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

.diary-icon {
  background-color: var(--mood-warm-bg);
}

.treehole-icon {
  background-color: var(--mood-low-bg);
}

.square-icon {
  background-color: var(--brand-light);
}

.report-icon {
  background-color: var(--mood-calm-bg);
}

.action-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
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
  color: var(--text-muted);
}

.feeds-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.feed-card {
  padding: var(--space-md);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);

  &:active {
    opacity: 0.8;
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
  background-color: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-xs);
}

.feed-avatar-text {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
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
  color: var(--text-muted);
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
  color: var(--text-muted);
}

// ==================== 空状态 ====================

.empty-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
  margin: var(--space-sm);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.empty-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  text-align: center;
}

// ==================== ActionSheet ====================

.sheet-options {
  padding: var(--space-xs);
}

.sheet-option {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  border-radius: var(--radius-md);

  &:active {
    background-color: var(--bg-tertiary);
  }
}

.option-icon-wrapper {
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: var(--space-sm);
}

.treehole-option {
  background-color: var(--mood-low-bg);
}

.dynamic-option {
  background-color: var(--brand-light);
}

.diary-option {
  background-color: var(--mood-warm-bg);
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
  color: var(--text-muted);
  margin-top: 4rpx;
}

// ==================== 安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>
