<template>
  <view class="mine-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <text class="header-title">回声</text>
      <view class="header-right">
        <view class="settings-btn" @tap="handleGoSettings">
          <text class="settings-icon">[设置]</text>
        </view>
      </view>
    </view>

    <!-- 用户信息卡片 -->
    <view class="user-card">
      <view class="user-info" @tap="handleEditProfile">
        <image
          class="user-avatar"
          :src="userInfo?.avatar_url || defaultAvatar"
          mode="aspectFill"
          @tap.stop="handleViewAvatar"
        />
        <view class="user-details">
          <text class="user-nickname">{{ userInfo?.nickname || '回声用户' }}</text>
          <text class="user-meta">{{ formatUserMeta }}</text>
        </view>
        <text class="edit-arrow">></text>
      </view>

      <!-- 社交能量 -->
      <view class="energy-section" @tap="handleShowEnergyDetail">
        <view class="energy-header">
          <text class="energy-label">社交能量</text>
          <text class="energy-percent" :style="{ color: energyColor }">{{ energyPercent }}%</text>
        </view>
        <view class="energy-bar">
          <view
            class="energy-fill"
            :style="{ width: energyPercent + '%', backgroundColor: energyColor }"
          />
        </view>
        <view class="energy-footer">
          <text class="energy-status">{{ energyStatusText }}</text>
          <view v-if="canRest" class="rest-btn" @tap.stop="handleRest">
            <text class="rest-text">休息一下</text>
          </view>
        </view>
      </view>

      <!-- 统计数据 -->
      <view class="stats-row">
        <view class="stat-item" @tap="handleGoFriends">
          <text class="stat-value">{{ friendCount }}</text>
          <text class="stat-label">好友</text>
        </view>
        <view class="stat-divider" />
        <view class="stat-item" @tap="handleGoDiary">
          <text class="stat-value">{{ diaryDays }}</text>
          <text class="stat-label">日记天数</text>
        </view>
      </view>
    </view>

    <!-- 渐进式社交暴露级别 -->
    <view class="social-level-card" @tap="handleShowSocialLevel">
      <view class="level-header">
        <text class="level-title">社交进度</text>
        <text class="level-current">Level {{ socialLevel?.current_level || 1 }}</text>
      </view>
      <view class="level-progress">
        <view
          v-for="i in 6"
          :key="i"
          class="level-dot"
          :class="{ 'is-unlocked': isLevelUnlocked(i) }"
        >
          <text class="level-dot-num">{{ i }}</text>
        </view>
      </view>
      <view class="level-hint">
        <text class="level-hint-text">{{ socialLevel?.progress_description || '开始你的社交旅程' }}</text>
        <text class="level-hint-arrow">></text>
      </view>
    </view>

    <!-- AI画像标签预览 -->
    <view class="ai-profile-section" @tap="handleGoAITags">
      <view class="section-header">
        <text class="section-title">AI画像</text>
        <text class="section-arrow">></text>
      </view>
      <view v-if="profileTags && profileTags.length > 0" class="profile-tags-preview">
        <text
          v-for="(tag, index) in visibleProfileTags"
          :key="index"
          class="profile-tag"
        >{{ tag.tag_value }}</text>
        <text v-if="profileTags.length > 3" class="more-tags">+{{ profileTags.length - 3 }}</text>
      </view>
      <view v-else class="empty-profile">
        <text class="empty-text">暂无画像数据，继续使用后会生成</text>
      </view>
    </view>

    <!-- 功能入口列表 -->
    <view class="menu-list">
      <!-- 情绪日记 -->
      <view class="menu-item" @tap="handleGoDiary">
        <view class="menu-icon diary-icon">
          <text class="icon-emoji">[日记]</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">情绪日记</text>
          <text class="menu-desc">已记录 {{ diaryDays }} 天</text>
        </view>
        <text class="menu-arrow">></text>
      </view>

      <!-- 好友 -->
      <view class="menu-item" @tap="handleGoFriends">
        <view class="menu-icon friends-icon">
          <text class="icon-emoji">[好友]</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">好友</text>
          <text class="menu-desc">{{ friendDesc }}</text>
        </view>
        <view v-if="pendingRequestCount > 0" class="menu-badge">
          <text class="badge-text">{{ pendingRequestCount }}</text>
        </view>
        <text class="menu-arrow">></text>
      </view>

      <!-- 收藏 -->
      <view class="menu-item" @tap="handleGoFavorites">
        <view class="menu-icon favorite-icon">
          <text class="icon-emoji">[收藏]</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">收藏</text>
          <text class="menu-desc">已收藏 {{ favoriteCount }} 条内容</text>
        </view>
        <text class="menu-arrow">></text>
      </view>

      <!-- 我的动态 -->
      <view class="menu-item" @tap="handleGoMyPosts">
        <view class="menu-icon posts-icon">
          <text class="icon-emoji">[动态]</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">我的动态</text>
          <text class="menu-desc">已发布 {{ postCount }} 条动态</text>
        </view>
        <text class="menu-arrow">></text>
      </view>
    </view>

    <!-- 社交能量详情弹窗 -->
    <wd-popup v-model="showEnergyDetail" position="bottom" closable>
      <view class="energy-detail-popup">
        <text class="popup-title">社交能量详情</text>
        <view class="energy-info">
          <text class="energy-value" :style="{ color: energyColor }">{{ energyPercent }}%</text>
          <text class="energy-status">{{ energyStatusText }}</text>
        </view>
        <view class="energy-tips">
          <text class="tips-text">社交能量会随着你的社交活动消耗，休息可以恢复能量。当能量过低时，建议适当休息。</text>
        </view>
        <view class="energy-levels">
          <text class="levels-title">能量状态参考</text>
          <view class="level-item">
            <view class="level-indicator" style="background-color: var(--color-success);" />
            <text class="level-text">80-100%：能量充足，可以自由社交</text>
          </view>
          <view class="level-item">
            <view class="level-indicator" style="background-color: var(--mood-calm);" />
            <text class="level-text">60-80%：能量良好，适度社交</text>
          </view>
          <view class="level-item">
            <view class="level-indicator" style="background-color: var(--mood-warm);" />
            <text class="level-text">40-60%：能量一般，注意休息</text>
          </view>
          <view class="level-item">
            <view class="level-indicator" style="background-color: var(--color-warning);" />
            <text class="level-text">20-40%：能量较低，建议休息</text>
          </view>
          <view class="level-item">
            <view class="level-indicator" style="background-color: var(--color-error);" />
            <text class="level-text">0-20%：能量不足，请立即休息</text>
          </view>
        </view>
        <view v-if="canRest" class="popup-action">
          <wd-button type="primary" block @click="handleRest">休息一下，恢复能量</wd-button>
        </view>
        <view v-else class="popup-action">
          <view class="cooldown-info">
            <text class="cooldown-text">冷却中，还需等待 {{ cooldownRemaining }}</text>
          </view>
          <wd-button type="default" block disabled>冷却中，请稍后再试</wd-button>
        </view>
      </view>
    </wd-popup>

    <!-- 社交级别详情弹窗 -->
    <wd-popup v-model="showSocialLevel" position="bottom" closable>
      <view class="social-level-popup">
        <text class="popup-title">社交进度详情</text>
        <view class="level-detail">
          <text class="level-value">Level {{ socialLevel?.current_level || 1 }}</text>
          <text class="level-name">{{ socialLevel?.level_name || getSocialLevelName(1) }}</text>
          <text class="level-desc">{{ socialLevel?.description }}</text>
        </view>
        <view class="level-steps">
          <view
            v-for="i in 6"
            :key="i"
            class="step-item"
            :class="{ 'is-current': i === socialLevel?.current_level, 'is-unlocked': isLevelUnlocked(i) }"
          >
            <view class="step-dot">
              <text class="step-num">{{ i }}</text>
            </view>
            <text class="step-desc">{{ getSocialLevelDescription(i) }}</text>
          </view>
        </view>
        <view class="level-stats">
          <text class="stats-title">行为统计</text>
          <view class="stats-grid">
            <view class="stats-item">
              <text class="stats-value">{{ socialLevel?.behavior_stats?.browse_count || 0 }}</text>
              <text class="stats-label">浏览</text>
            </view>
            <view class="stats-item">
              <text class="stats-value">{{ socialLevel?.behavior_stats?.like_count || 0 }}</text>
              <text class="stats-label">共鸣</text>
            </view>
            <view class="stats-item">
              <text class="stats-value">{{ socialLevel?.behavior_stats?.comment_count || 0 }}</text>
              <text class="stats-label">评论</text>
            </view>
            <view class="stats-item">
              <text class="stats-value">{{ socialLevel?.behavior_stats?.friend_request_count || 0 }}</text>
              <text class="stats-label">好友申请</text>
            </view>
          </view>
        </view>
        <view v-if="socialLevel?.next_action" class="next-action">
          <text class="action-hint">建议下一步：{{ socialLevel.next_action }}</text>
        </view>
      </view>
    </wd-popup>

    <!-- 下拉刷新 -->
    <wd-refresh-control v-model="isRefreshing" @refresh="handleRefresh" />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 个人中心主页
 * 文件：src/pages/mine/index.vue
 * 说明：展示用户信息、社交能量、功能入口等
 */

import { ref, computed, onMounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { useSettingsStore } from '@/stores/settings'
import {
  getMyProfile,
  getSocialEnergy,
  getSocialLevel,
  getMyProfileTags,
  getSocialLevelName,
  getSocialLevelDescription,
  getEnergyColor,
  getEnergyStatusText,
  type UserDetail,
  type SocialEnergyResponse,
  type SocialLevelResponse,
  type AIProfileTagResponse,
} from '@/api/modules/user'
import { getFriendRequests, type FriendRequestListResponse } from '@/api/modules/friend'
import { track, EventName } from '@/utils/tracking'

// ==================== 响应式状态 ====================

/** 用户信息 */
const userInfo = ref<UserDetail | null>(null)

/** 社交能量 */
const energyData = ref<SocialEnergyResponse | null>(null)

/** 社交级别 */
const socialLevel = ref<SocialLevelResponse | null>(null)

/** AI画像标签 */
const profileTags = ref<AIProfileTagResponse | null>(null)

/** 好友申请列表（获取待处理数量） */
const friendRequests = ref<FriendRequestListResponse | null>(null)

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否正在刷新 */
const isRefreshing = ref(false)

/** 默认头像 */
const defaultAvatar = '/static/images/default-avatar.png'

/** 社交能量详情弹窗 */
const showEnergyDetail = ref(false)

/** 社交级别详情弹窗 */
const showSocialLevel = ref(false)

// ==================== 计算属性 ====================

/** 用户元信息（年龄城市） */
const formatUserMeta = computed(() => {
  const parts: string[] = []
  if (userInfo.value?.age_range) {
    parts.push(userInfo.value.age_range)
  }
  if (userInfo.value?.city) {
    parts.push(userInfo.value.city)
  }
  return parts.length > 0 ? parts.join(' · ') : '点击编辑资料'
})

/** 能量百分比 */
const energyPercent = computed(() => {
  return Math.round(energyData.value?.energy || 0)
})

/** 能量状态文本 */
const energyStatusText = computed(() => {
  return energyData.value?.status || getEnergyStatusText(energyPercent.value)
})

/** 能量颜色 */
const energyColor = computed(() => {
  return getEnergyColor(energyPercent.value)
})

/** 是否可以休息 */
const canRest = computed(() => {
  return energyData.value?.can_rest ?? false
})

/** 冷却剩余时间 */
const cooldownRemaining = computed(() => {
  const seconds = energyData.value?.rest_cooldown_remaining || 0
  if (seconds <= 0) return ''
  const minutes = Math.floor(seconds / 60)
  if (minutes > 0) {
    return `${minutes}分${seconds % 60}秒`
  }
  return `${seconds}秒`
})

/** 好友数量 */
const friendCount = computed(() => {
  // TODO: 从好友列表接口获取
  return 0
})

/** 日记天数 */
const diaryDays = computed(() => {
  // TODO: 从日记接口获取
  return 0
})

/** 待处理好友申请数量 */
const pendingRequestCount = computed(() => {
  return friendRequests.value?.unread_count || 0
})

/** 好友描述 */
const friendDesc = computed(() => {
  if (pendingRequestCount.value > 0) {
    return `${pendingRequestCount.value} 条好友申请待处理`
  }
  return `${friendCount.value} 位好友`
})

/** 收藏数量 */
const favoriteCount = computed(() => {
  // TODO: 从收藏接口获取
  return 0
})

/** 动态数量 */
const postCount = computed(() => {
  // TODO: 从动态接口获取
  return 0
})

/** 可见的画像标签 */
const visibleProfileTags = computed(() => {
  const tags = profileTags.value?.tags || []
  return tags.filter(tag => tag.is_visible !== false).slice(0, 3)
})

// ==================== 方法 ====================

/**
 * 加载用户数据
 */
async function loadUserData(): Promise<void> {
  const userStore = useUserStore()
  if (!userStore.isLoggedIn) {
    uni.navigateTo({ url: '/pages/auth/login' })
    return
  }

  isLoading.value = true

  try {
    // 并行请求多个接口
    const [profileRes, energyRes, levelRes, tagsRes, requestsRes] = await Promise.all([
      getMyProfile(),
      getSocialEnergy(),
      getSocialLevel(),
      getMyProfileTags(),
      getFriendRequests(),
    ])

    userInfo.value = profileRes
    energyData.value = energyRes
    socialLevel.value = levelRes
    profileTags.value = tagsRes
    friendRequests.value = requestsRes

    // 更新 store
    userStore.setUserInfo({
      id: profileRes.id,
      phone: profileRes.phone,
      nickname: profileRes.nickname || '',
      avatarUrl: profileRes.avatar_url || undefined,
      ageRange: profileRes.age_range || undefined,
      city: profileRes.city || undefined,
      occupation: profileRes.occupation || undefined,
      is_minor: profileRes.is_minor,
      createdAt: profileRes.created_at,
    })

    track(EventName.PAGE_VIEW, { page: 'mine' })
  } catch (error) {
    console.error('加载用户数据失败', error)
  } finally {
    isLoading.value = false
  }
}

/**
 * 判断级别是否解锁
 */
function isLevelUnlocked(level: number): boolean {
  if (!socialLevel.value) return level === 1
  const status = socialLevel.value.unlock_status
  switch (level) {
    case 1: return status.level_1
    case 2: return status.level_2
    case 3: return status.level_3
    case 4: return status.level_4
    case 5: return status.level_5
    case 6: return status.level_6
    default: return false
  }
}

/**
 * 处理休息
 */
async function handleRest(): Promise<void> {
  try {
    const { restSocialEnergy } = await import('@/api/modules/user')
    const result = await restSocialEnergy()

    // 刷新能量数据
    energyData.value = {
      energy: result.new_energy,
      percentage: Math.round(result.new_energy) + '%',
      status: getEnergyStatusText(result.new_energy),
      can_rest: false,
      rest_cooldown_remaining: Math.floor(result.cooldown_until / 1000),
      updated_at: new Date().toISOString(),
    }

    uni.showToast({
      title: result.message,
      icon: 'success',
    })

    showEnergyDetail.value = false

    track(EventName.SOCIAL_ENERGY_REST, {
      old_energy: result.old_energy,
      new_energy: result.new_energy,
    })
  } catch (error) {
    console.error('休息失败', error)
  }
}

/**
 * 显示能量详情
 */
function handleShowEnergyDetail(): void {
  showEnergyDetail.value = true
}

/**
 * 显示社交级别详情
 */
function handleShowSocialLevel(): void {
  showSocialLevel.value = true
}

/**
 * 跳转设置页
 */
function handleGoSettings(): void {
  uni.navigateTo({ url: '/pages/settings/index' })
}

/**
 * 编辑资料
 */
function handleEditProfile(): void {
  uni.navigateTo({ url: '/pages/profile/edit' })
}

/**
 * 跳转AI画像页
 */
function handleGoAITags(): void {
  uni.navigateTo({ url: '/pages/profile/ai-tags' })
}

/**
 * 跳转好友页
 */
function handleGoFriends(): void {
  uni.navigateTo({ url: '/pages/friends/index' })
}

/**
 * 跳转日记页
 */
function handleGoDiary(): void {
  uni.switchTab({ url: '/pages/diary/index' })
}

/**
 * 跳转收藏页
 */
function handleGoFavorites(): void {
  // TODO: 实现收藏页
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 跳转我的动态页
 */
function handleGoMyPosts(): void {
  // TODO: 实现我的动态页
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 查看头像
 */
function handleViewAvatar(): void {
  if (userInfo.value?.avatar_url) {
    uni.previewImage({
      urls: [userInfo.value.avatar_url],
    })
  }
}

/**
 * 下拉刷新
 */
async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  await loadUserData()
  isRefreshing.value = false
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadUserData()
})

onShow(() => {
  // 每次显示时刷新数据
  loadUserData()
})

onPullDownRefresh(() => {
  loadUserData().finally(() => {
    uni.stopPullDownRefresh()
  })
})
</script>

<style lang="scss" scoped>
.mine-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-primary);
  padding-bottom: env(safe-area-inset-bottom);
}

// ==================== 顶部导航栏 ====================

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  padding-top: calc(env(safe-area-inset-top) + var(--space-md));
  background-color: var(--bg-primary);
}

.header-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.settings-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
}

.settings-icon {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

// ==================== 用户信息卡片 ====================

.user-card {
  display: flex;
  flex-direction: column;
  margin: var(--space-md);
  padding: var(--space-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-lg);

  &:active {
    opacity: 0.9;
  }
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  margin-right: var(--space-md);
}

.user-details {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.user-nickname {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8rpx;
}

.user-meta {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.edit-arrow {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

// ==================== 社交能量 ====================

.energy-section {
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);

  &:active {
    opacity: 0.98;
  }
}

.energy-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.energy-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.energy-percent {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.energy-bar {
  height: 12rpx;
  background-color: var(--bg-primary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.energy-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.energy-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.energy-status {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.rest-btn {
  padding: 8rpx 20rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);

  &:active {
    opacity: 0.9;
  }
}

.rest-text {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
}

// ==================== 统计数据 ====================

.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md) 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;

  &:active {
    opacity: 0.9;
  }
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.stat-divider {
  width: 1rpx;
  height: 60rpx;
  background-color: var(--border-primary);
}

// ==================== 社交进度卡片 ====================

.social-level-card {
  display: flex;
  flex-direction: column;
  margin: 0 var(--space-md) var(--space-md);
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.98;
  }
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.level-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.level-current {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
  font-weight: 600;
}

.level-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.level-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-full);
  transition: all 0.3s ease;

  &.is-unlocked {
    background-color: var(--brand-primary);
  }
}

.level-dot-num {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);

  .is-unlocked & {
    color: var(--text-on-brand);
  }
}

.level-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.level-hint-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  flex: 1;
}

.level-hint-arrow {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
  margin-left: var(--space-sm);
}

// ==================== AI画像预览 ====================

.ai-profile-section {
  margin: 0 var(--space-md) var(--space-md);
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);

  &:active {
    opacity: 0.98;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--text-primary);
}

.section-arrow {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

.profile-tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.profile-tag {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background-color: var(--bg-tertiary);
  padding: 8rpx 16rpx;
  border-radius: var(--radius-full);
}

.more-tags {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
  padding: 8rpx 16rpx;
}

.empty-profile {
  padding: var(--space-sm) 0;
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 功能入口列表 ====================

.menu-list {
  display: flex;
  flex-direction: column;
  margin: 0 var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  border-bottom: 1rpx solid var(--border-primary);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: var(--bg-tertiary);
  }
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  border-radius: var(--radius-md);
  margin-right: var(--space-sm);
}

.icon-emoji {
  font-size: var(--font-size-lg);
}

.diary-icon {
  background-color: var(--mood-warm-bg);
}

.friends-icon {
  background-color: var(--mood-calm-bg);
}

.favorite-icon {
  background-color: rgba(124, 111, 224, 0.15);
}

.posts-icon {
  background-color: rgba(59, 130, 246, 0.15);
}

.menu-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.menu-title {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.menu-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.menu-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36rpx;
  height: 36rpx;
  padding: 0 12rpx;
  background-color: var(--color-error);
  border-radius: var(--radius-full);
  margin-right: var(--space-sm);
}

.badge-text {
  font-size: var(--font-size-xs);
  color: #fff;
}

.menu-arrow {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

// ==================== 弹窗样式 ====================

.energy-detail-popup,
.social-level-popup {
  padding: var(--space-lg);
  padding-bottom: calc(env(safe-area-inset-bottom) + var(--space-lg));
}

.popup-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: var(--space-lg);
}

.energy-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.energy-value {
  font-size: 64rpx;
  font-weight: 700;
  margin-bottom: var(--space-sm);
}

.energy-status {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

.energy-tips {
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.tips-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.6;
}

.energy-levels {
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

.levels-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
}

.level-item {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-xs);

  &:last-child {
    margin-bottom: 0;
  }
}

.level-indicator {
  width: 16rpx;
  height: 16rpx;
  border-radius: var(--radius-full);
  margin-right: var(--space-sm);
}

.level-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.popup-action {
  margin-top: var(--space-md);
}

.cooldown-info {
  text-align: center;
  margin-bottom: var(--space-sm);
}

.cooldown-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 社交级别详情 ====================

.level-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.level-value {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--brand-primary);
  margin-bottom: 8rpx;
}

.level-name {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin-bottom: 8rpx;
}

.level-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
}

.level-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.step-item {
  display: flex;
  align-items: center;
  padding: var(--space-sm);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  opacity: 0.6;

  &.is-unlocked {
    opacity: 1;
  }

  &.is-current {
    background-color: rgba(124, 111, 224, 0.2);
  }
}

.step-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
  background-color: var(--bg-primary);
  border-radius: var(--radius-full);
  margin-right: var(--space-sm);

  .is-unlocked & {
    background-color: var(--brand-primary);
  }
}

.step-num {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);

  .is-unlocked & {
    color: var(--text-on-brand);
  }
}

.step-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.level-stats {
  padding: var(--space-md);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
}

.stats-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-value {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.stats-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.next-action {
  padding: var(--space-md);
  background-color: var(--color-info-bg);
  border-radius: var(--radius-md);
}

.action-hint {
  font-size: var(--font-size-sm);
  color: var(--color-info);
}
</style>
