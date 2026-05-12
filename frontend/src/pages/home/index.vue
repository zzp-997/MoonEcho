<template>
  <view class="home-page tn-safe-area-inset-bottom">
    <!-- 顶部自定义导航 — 半透明磨砂覆盖在轮播图上 -->
    <view class="custom-nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="custom-nav-content">
        <view class="custom-nav__logo" @tap="handleAbout">
          <image class="logo-pic tn-shadow-blur" :src="logoUrl" mode="aspectFill" />
        </view>
        <view class="custom-nav__search" @tap="handleNotification">
          <view class="custom-nav__search__box">
            <text class="nav-bell-icon">🔔</text>
            <text v-if="unreadCount > 0" class="nav-badge">{{ unreadCount }}</text>
            <text class="search-text">
              {{ unreadCount > 0 ? `${unreadCount}条新消息` : '暂无新消息' }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 英雄区轮播 -->
    <swiper
      class="hero-swiper"
      :circular="true"
      :autoplay="true"
      duration="500"
      interval="6000"
      @change="onSwiperChange"
    >
      <swiper-item
        v-for="(item, index) in heroList"
        :key="index"
        :class="currentSwiper === index ? 'cur' : ''"
      >
        <view class="hero-item image-banner">
          <image :src="item.url" mode="aspectFill" />
        </view>
        <view class="hero-item-text">
          <view class="tn-text-bold tn-color-white" style="font-size: 46rpx;">{{ item.title }}</view>
          <view class="tn-color-white tn-padding-top" style="font-size: 28rpx;">{{ item.subtitle }}</view>
        </view>
        <!-- 指示点移入轮播内部底部 -->
        <view v-if="index === currentSwiper" class="hero-indication-inner">
          <view
            v-for="(_, dotIdx) in heroList"
            :key="dotIdx"
            class="hero-spot"
            :class="currentSwiper === dotIdx ? 'active' : ''"
          />
        </view>
      </swiper-item>
    </swiper>

    <!-- 问候语 + 情绪状态 -->
    <view class="section-greeting">
      <text class="greeting-text">{{ greetingText }}</text>
      <EmotionBar
        :has-record-today="hasRecordToday"
        :today-emotion="todayEmotion"
        :streak-days="streakDays"
        @tap="handleEmotionBarTap"
      />
    </view>

    <!-- 快捷入口 — 渐变图标容器 -->
    <view class="shortcuts-grid tn-flex tn-margin-top-sm">
      <view
        class="shortcut-item tn-flex-1 tn-padding-sm tn-margin-xs tn-radius"
        @tap="handleQuickAction('diary')"
      >
        <view class="tn-flex tn-flex-direction-column tn-flex-row-center tn-flex-col-center">
          <view class="tn-icon-gradient-9 tn-color-white">
            <view style="font-size: 48rpx;">📅</view>
          </view>
          <view class="tn-color-black tn-text-center tn-padding-top-xs">
            <text class="tn-text-ellipsis tn-text-sm tn-text-bold">记日记</text>
          </view>
        </view>
      </view>
      <view
        class="shortcut-item tn-flex-1 tn-padding-sm tn-margin-xs tn-radius"
        @tap="handleQuickAction('treehole')"
      >
        <view class="tn-flex tn-flex-direction-column tn-flex-row-center tn-flex-col-center">
          <view class="tn-icon-gradient-5 tn-color-white">
            <view style="font-size: 48rpx;">🕳️</view>
          </view>
          <view class="tn-color-black tn-text-center tn-padding-top-xs">
            <text class="tn-text-ellipsis tn-text-sm tn-text-bold">树洞</text>
          </view>
        </view>
      </view>
      <view
        class="shortcut-item tn-flex-1 tn-padding-sm tn-margin-xs tn-radius"
        @tap="handleQuickAction('square')"
      >
        <view class="tn-flex tn-flex-direction-column tn-flex-row-center tn-flex-col-center">
          <view class="tn-icon-gradient-13 tn-color-white">
            <view style="font-size: 48rpx;">⭐</view>
          </view>
          <view class="tn-color-black tn-text-center tn-padding-top-xs">
            <text class="tn-text-ellipsis tn-text-sm tn-text-bold">广场</text>
          </view>
        </view>
      </view>
      <view
        class="shortcut-item tn-flex-1 tn-padding-sm tn-margin-xs tn-radius"
        @tap="handleQuickAction('report')"
      >
        <view class="tn-flex tn-flex-direction-column tn-flex-row-center tn-flex-col-center">
          <view class="tn-icon-gradient-6 tn-color-white">
            <view style="font-size: 48rpx;">📊</view>
          </view>
          <view class="tn-color-black tn-text-center tn-padding-top-xs">
            <text class="tn-text-ellipsis tn-text-sm tn-text-bold">周报</text>
          </view>
        </view>
      </view>
    </view>

    <!-- AI 入口卡片 — 带彩色阴影 -->
    <view class="ai-card tn-card tn-margin-top tn-margin-left tn-margin-right" @tap="handleAIEntry">
      <view class="tn-flex tn-flex-row-between tn-flex-col-center">
        <view class="tn-flex tn-flex-col-center">
          <view
            class="ai-avatar"
            :class="aiShadowClass"
            :style="{ backgroundImage: `linear-gradient(45deg, ${aiGradientStart}, ${aiGradientEnd})` }"
          >
            <text class="ai-avatar-text">{{ currentPersonalityName.charAt(0) }}</text>
          </view>
          <view class="tn-padding-left">
            <view class="tn-text-bold tn-text-lg">{{ currentPersonalityName }}</view>
            <view class="tn-color-gray tn-padding-top-xs">{{ lastMessagePreview || '想聊聊吗' }}</view>
          </view>
        </view>
        <view class="tn-flex tn-flex-col-center">
          <text class="ai-go-btn tn-gradient-5">对话 ▸</text>
        </view>
      </view>
    </view>

    <!-- 近期动态 -->
    <view v-if="recentFeeds.length > 0" class="feeds-section tn-margin-top-xl">
      <view class="tn-flex tn-flex-row-between" @tap="handleMoreFeeds">
        <view class="tn-margin tn-text-bold tn-text-xl">近期动态</view>
        <view class="tn-margin tn-color-gray">
          <text class="tn-padding-xs">更多</text>
          <text>▸</text>
        </view>
      </view>
      <block v-for="(feed, index) in recentFeeds.slice(0, 3)" :key="feed.id">
        <view class="feed-item" @tap="handleFeedTap(feed)">
          <view class="tn-flex tn-flex-col-center">
            <view class="feed-avatar tn-shadow-blur" :style="{ backgroundImage: `url(${feed.authorAvatar || defaultAvatar})` }" />
            <view class="feed-content tn-flex-1 tn-margin-left-sm">
              <view class="tn-text-bold tn-text-df">{{ feed.isAnonymous ? '匿名' : feed.authorNickname }}</view>
              <view class="tn-color-gray tn-padding-top-xs tn-text-sm" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {{ feed.content }}
              </view>
            </view>
            <view class="tn-color-gray tn-text-xs tn-margin-left">{{ formatTime(feed.createdAt) }}</view>
          </view>
        </view>
        <view v-if="index < Math.min(recentFeeds.length, 3) - 1" class="feed-divider" />
      </block>
    </view>

    <!-- 空状态 -->
    <view v-else class="empty-state tn-margin-top-xl">
      <view class="tn-icon-gradient-6">
        <text style="font-size: 60rpx;">✨</text>
      </view>
      <text class="tn-text-bold tn-text-lg tn-margin-top">开始你的情绪之旅</text>
      <text class="tn-color-gray tn-margin-top-xs tn-text-sm">记录心情，与 AI 朋友聊聊</text>
      <view class="tn-btn-gradient tn-margin-top-lg tn-gradient-9" @tap="handleEmotionBarTap">
        写第一篇日记
      </view>
    </view>

    <!-- TabBar 占位 -->
    <view class="tn-tabbar-height" />

    <CustomTabBar />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { useNotification } from '@/composables/useNotification'
import { useMinorGuard } from '@/composables/useMinorGuard'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import { track, EventName, trackPageEnter, trackPageLeave } from '@/utils/tracking'
import { getDiaryList, getDiaryStats, type EmotionTone } from '@/api/diary'
import EmotionBar from '@/components/home/EmotionBar.vue'
import CustomTabBar from '@/components/common/CustomTabBar.vue'

const userStore = useUserStore()
const chatStore = useChatStore()
const { unreadCount, fetchUnreadCount } = useNotification()
const { checkAccess } = useMinorGuard()

const currentSwiper = ref(0)
const isRefreshing = ref(false)
const hasRecordToday = ref(false)
const todayEmotion = ref<EmotionTone | null>(null)
const streakDays = ref(0)
const isInitialLoad = ref(true)
const defaultAvatar = 'https://resource.tuniaokj.com/images/blogger/avatar_1.jpeg'
const logoUrl = '/static/logo.png'

// 状态栏高度，用于导航栏定位
const statusBarHeight = ref(0)
const sysInfo = uni.getSystemInfoSync()
statusBarHeight.value = sysInfo.statusBarHeight || 0

interface FeedItem {
  id: string
  content: string
  authorNickname?: string
  authorAvatar?: string
  isAnonymous: boolean
  createdAt: string
  likeCount?: number
  commentCount?: number
}

const recentFeeds = ref<FeedItem[]>([])

// 英雄区轮播数据
const heroList = ref([
  {
    title: '回声',
    subtitle: '你的情绪，有人懂',
    url: 'https://resource.tuniaokj.com/images/new/banner1.jpg',
  },
  {
    title: '记一笔',
    subtitle: '今天的感受，值得被记住',
    url: 'https://resource.tuniaokj.com/images/swiper/adno3.jpg',
  },
  {
    title: '有人听',
    subtitle: 'AI 朋友，随时陪你聊',
    url: 'https://resource.tuniaokj.com/images/swiper/adno2.jpg',
  },
])

const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 23 || hour < 5) return '夜深了，今天还好吗'
  if (hour >= 5 && hour < 9) return '早安，新的一天'
  if (hour >= 18) return '晚上好，辛苦了'
  return '嗨，随时都在'
})

const currentPersonality = computed(() => chatStore.currentPersonality)

const currentPersonalityName = computed(() => {
  const personalityMap: Record<string, string> = {
    xiaowen: '小温',
    laohei: '老黑',
    ali: '阿理',
  }
  return personalityMap[currentPersonality.value] || '小温'
})

const aiGradientStart = computed(() => {
  const map: Record<string, string> = { xiaowen: '#FF71D2', laohei: '#78909C', ali: '#3D7EFF' }
  return map[currentPersonality.value] || '#FF71D2'
})

const aiGradientEnd = computed(() => {
  const map: Record<string, string> = { xiaowen: '#F360A7', laohei: '#5F7E8B', ali: '#31C9E8' }
  return map[currentPersonality.value] || '#F360A7'
})

const aiShadowClass = computed(() => {
  const map: Record<string, string> = { xiaowen: 'tn-shadow-purplered', laohei: 'tn-shadow-grey', ali: 'tn-shadow-blue' }
  return map[currentPersonality.value] || 'tn-shadow-purplered'
})

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

function onSwiperChange(e: any) {
  currentSwiper.value = e.detail.current
}

async function initPageData(): Promise<void> {
  if (!isInitialLoad.value) return
  try {
    await Promise.all([loadTodayRecordStatus(), fetchUnreadCount()])
  } finally {
    isInitialLoad.value = false
  }
}

async function loadTodayRecordStatus(): Promise<void> {
  if (!userStore.isLoggedIn) {
    hasRecordToday.value = false
    todayEmotion.value = null
    streakDays.value = 0
    return
  }

  const today = new Date().toISOString().split('T')[0]
  try {
    let diaryList: any = null
    let stats: any = null

    try { diaryList = await getDiaryList({ page: 1, page_size: 1 }, { silent: true }) } catch {}
    try { stats = await getDiaryStats({ silent: true }) } catch {}

    if (diaryList?.data) {
      const todayDiary = diaryList.data.find((d: any) => d.record_date === today)
      hasRecordToday.value = !!todayDiary
      todayEmotion.value = todayDiary?.emotion_tone || null
      if (stats) streakDays.value = calculateStreak(diaryList.data)
    } else {
      hasRecordToday.value = false
      todayEmotion.value = null
      streakDays.value = 0
    }
  } catch {
    hasRecordToday.value = false
    todayEmotion.value = null
    streakDays.value = 0
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
    if (dates.includes(checkDateStr)) streak++
    else break
  }
  return streak
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  try {
    await Promise.all([loadTodayRecordStatus(), fetchUnreadCount()])
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

function handleAbout(): void {
  // 点击logo
}

function handleQuickAction(action: string): void {
  if (action === 'treehole' && !checkAccess('treehole')) return
  const routeConfig: Record<string, { url: string; type: 'navigate' | 'switchTab' }> = {
    diary: { url: '/pages/diary/edit', type: 'navigate' },
    treehole: { url: '/pagesSocial/treehole/index', type: 'navigate' },
    square: { url: '/pagesSocial/square/index', type: 'switchTab' },
    report: { url: '/pages/diary/weekly-report', type: 'navigate' },
  }
  const config = routeConfig[action]
  if (config) {
    if (config.type === 'switchTab') uni.switchTab({ url: config.url })
    else uni.navigateTo({ url: config.url })
  }
}

function handleMoreFeeds(): void {
  uni.switchTab({ url: '/pagesSocial/square/index' })
}

function handleFeedTap(_feed: FeedItem): void {
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

onMounted(() => {
  initPageData()
  trackPageEnter('home')
})

usePageVisibleRefresh({
  onVisible() {
    if (!isInitialLoad.value) {
      trackPageEnter('home')
      loadTodayRecordStatus()
      fetchUnreadCount()
    }
  },
  onHidden() {
    trackPageLeave('home')
  },
})

onPullDownRefresh(() => {
  handleRefresh()
})
</script>

<style lang="scss" scoped>
.home-page {
  max-height: 100vh;
  background-color: #FFFFFF;
}

.tn-tabbar-height {
  min-height: 100rpx;
  height: calc(120rpx + env(safe-area-inset-bottom) / 2);
}

// ==================== 导航栏 ====================

.custom-nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  background: transparent;
}

.custom-nav-content {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 30rpx;
}

.custom-nav__logo {
  margin-right: 10rpx;
  flex-shrink: 0;

  .logo-pic {
    width: 65rpx;
    height: 65rpx;
    border-radius: 50%;
  }
}

.custom-nav__search {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;

  &__box {
    display: flex;
    align-items: center;
    width: 100%;
    height: 66rpx;
    padding: 0 24rpx;
    border-radius: 60rpx 60rpx 0 60rpx;
    background-color: rgba(255, 255, 255, 0.25);
    backdrop-filter: blur(20rpx);
    -webkit-backdrop-filter: blur(20rpx);
    position: relative;

    .search-text {
      padding-left: 12rpx;
      color: #FFFFFF;
      font-size: 24rpx;
    }
  }
}

.nav-bell-icon {
  font-size: 36rpx;
}

.nav-badge {
  position: absolute;
  top: 10rpx;
  left: 36rpx;
  min-width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  padding: 0 8rpx;
  border-radius: 5000rpx;
  background-color: var(--color-red, #E83A30);
  color: #FFFFFF;
  font-size: 18rpx;
  font-weight: 600;
  text-align: center;
}

// ==================== 英雄区轮播 ====================

.hero-swiper {
  height: 540rpx !important;
}

.hero-swiper swiper-item {
  width: 750rpx !important;
  left: 0rpx;
  box-sizing: border-box;
  overflow: initial;
}

.hero-swiper swiper-item .hero-item {
  width: 100%;
  display: block;
  height: 100%;
  transform: scale(1);
  transition: all 0.2s ease-in 0s;
  will-change: transform;
  overflow: hidden;
}

.hero-swiper swiper-item.cur .hero-item {
  transform: none;
  transition: all 0.2s ease-in 0s;
}

.hero-swiper swiper-item .hero-item-text {
  position: absolute;
  bottom: 60rpx;
  left: 0;
  right: 0;
  text-align: center;
  width: 100%;
  opacity: 0;
  transform: translateY(20rpx);
  transition: all 0.6s ease-out 0s;
  will-change: transform, opacity;
  text-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.3);
}

.hero-swiper swiper-item.cur .hero-item-text {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.6s ease-out 0.2s;
}

.image-banner {
  display: flex;
  align-items: center;
  justify-content: center;

  image {
    width: 100%;
    height: 100%;
  }
}

// 轮播指示点（移入轮播底部内部）
.hero-indication-inner {
  position: absolute;
  bottom: 24rpx;
  left: 0;
  right: 0;
  width: 100%;
  height: 36rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.hero-spot {
  background-color: rgba(255, 255, 255, 0.6);
  width: 10rpx;
  height: 10rpx;
  border-radius: 20rpx;
  margin: 0 8rpx !important;
  transition: all 0.3s ease-out;
}

.hero-spot.active {
  opacity: 1;
  width: 30rpx;
  background-color: #FFFFFF;
}

// ==================== 问候语区 ====================

.section-greeting {
  padding: 30rpx 30rpx 0;
}

.greeting-text {
  font-size: 46rpx;
  font-weight: bold;
  color: var(--color-black, #080808);
  line-height: 1.3;
  display: block;
  margin-bottom: 20rpx;
}

// ==================== 快捷入口 ====================

.shortcuts-grid {
  padding: 0 10rpx;
}

.shortcut-item {
  &:active {
    transform: scale(0.93);
  }
}

// ==================== AI 入口卡片 ====================

.ai-card {
  margin-top: 20rpx;

  &:active {
    opacity: 0.92;
    transform: scale(0.98);
  }
}

.ai-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background-size: cover;
}

.ai-avatar-text {
  font-size: 32rpx;
  font-weight: bold;
  color: #FFFFFF;
}

.ai-go-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 32rpx;
  border-radius: 5000rpx;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 24rpx;

  &:active {
    transform: scale(0.95);
    opacity: 0.85;
  }
}

// ==================== 近期动态 ====================

.feeds-section {
  padding-bottom: 20rpx;
}

.feed-item {
  padding: 30rpx;

  &:active {
    opacity: 0.85;
  }
}

.feed-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background-size: cover;
  background-repeat: no-repeat;
  background-position: top;
  flex-shrink: 0;
}

.feed-content {
  overflow: hidden;
}

.feed-divider {
  border-bottom: 1rpx solid var(--border-light, #eee);
  margin: 0 30rpx;
}

// ==================== 空状态 ====================

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0;
}
</style>
