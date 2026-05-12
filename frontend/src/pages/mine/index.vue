<template>
  <view class="mine-page">
    <!-- 顶部渐变背景 + 用户卡片 -->
    <view class="mine-header" :style="{ paddingTop: (statusBarHeight + 20) + 'px' }">
      <!-- 导航栏 -->
      <view class="page-nav">
        <text class="nav-title">回声</text>
        <view class="nav-action" @tap="handleGoSettings">
          <text style="font-size: 40rpx;">⚙️</text>
        </view>
      </view>

      <!-- 用户信息 -->
      <view class="user-card" @tap="handleEditProfile">
        <image
          class="user-avatar tn-shadow-blur"
          :src="userInfo?.avatar_url || defaultAvatar"
          mode="aspectFill"
          @tap.stop="handleViewAvatar"
        />
        <view class="user-info">
          <text class="user-nickname">{{ userInfo?.nickname || '回声用户' }}</text>
          <text class="user-meta">{{ formatUserMeta }}</text>
        </view>
        <text class="go-edit">></text>
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

    <!-- 社交能量卡片 -->
    <view class="energy-card tn-shadow-card" @tap="handleShowEnergyDetail">
      <view class="energy-header">
        <view class="energy-left">
          <view class="energy-icon tn-icon-container tn-gradient-6 tn-shadow-blur">
            <text style="font-size: 40rpx;">⚡</text>
          </view>
          <text class="energy-label">社交能量</text>
        </view>
        <text class="energy-percent" :style="{ color: energyColor }">{{ energyPercent }}%</text>
      </view>
      <view class="energy-bar">
        <view
          class="energy-fill"
          :style="{ width: energyPercent + '%', background: energyGradient }"
        />
      </view>
      <view class="energy-footer">
        <text class="energy-status">{{ energyStatusText }}</text>
        <view v-if="canRest" class="rest-btn tn-gradient-1" @tap.stop="handleRest">
          <text class="rest-text">休息一下</text>
        </view>
      </view>
    </view>

    <!-- 社交进度 -->
    <view class="social-level-card tn-shadow-card" @tap="handleShowSocialLevel">
      <view class="level-header">
        <view class="level-left">
          <view class="level-icon tn-icon-container tn-gradient-9 tn-shadow-blur">
            <text style="font-size: 40rpx;">🏆</text>
          </view>
          <text class="level-title">社交进度</text>
        </view>
        <text class="level-current tn-color-purplered">Level {{ socialLevel?.current_level || 1 }}</text>
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
        <text class="level-go">></text>
      </view>
    </view>

    <!-- AI画像 -->
    <view class="ai-profile-card tn-shadow-card" @tap="handleGoAITags">
      <view class="profile-header">
        <view class="profile-left">
          <view class="profile-icon tn-icon-container tn-gradient-5 tn-shadow-blur">
            <text style="font-size: 40rpx;">🤖</text>
          </view>
          <text class="profile-title">AI画像</text>
        </view>
        <text class="profile-go">></text>
      </view>
      <view v-if="profileTags && profileTags.length > 0" class="profile-tags">
        <text
          v-for="(tag, index) in visibleProfileTags"
          :key="index"
          class="profile-tag"
          :class="`tn-color-${getTagColor(index)}`"
        >{{ tag.tag_value }}</text>
        <text v-if="profileTags.length > 3" class="more-tags">+{{ profileTags.length - 3 }}</text>
      </view>
      <view v-else class="empty-profile">
        <text class="empty-text">暂无画像数据，继续使用后会生成</text>
      </view>
    </view>

    <!-- 功能入口列表 -->
    <view class="menu-list tn-shadow-card">
      <view class="menu-item" @tap="handleGoDiary">
        <view class="menu-icon tn-gradient-9 tn-shadow-blur">
          <text style="font-size: 36rpx;">📅</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">情绪日记</text>
          <text class="menu-desc">已记录 {{ diaryDays }} 天</text>
        </view>
        <text class="menu-arrow">></text>
      </view>

      <view class="menu-divider" />

      <view class="menu-item" @tap="handleGoFriends">
        <view class="menu-icon tn-gradient-1 tn-shadow-blur">
          <text style="font-size: 36rpx;">👫</text>
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

      <view class="menu-divider" />

      <view class="menu-item" @tap="handleGoFavorites">
        <view class="menu-icon tn-gradient-13 tn-shadow-blur">
          <text style="font-size: 36rpx;">⭐</text>
        </view>
        <view class="menu-content">
          <text class="menu-title">收藏</text>
          <text class="menu-desc">已收藏 {{ favoriteCount }} 条内容</text>
        </view>
        <text class="menu-arrow">></text>
      </view>

      <view class="menu-divider" />

      <view class="menu-item" @tap="handleGoMyPosts">
        <view class="menu-icon tn-gradient-15 tn-shadow-blur">
          <text style="font-size: 36rpx;">💬</text>
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
            <view class="level-indicator tn-bg-green" />
            <text class="level-text">80-100%：能量充足，可以自由社交</text>
          </view>
          <view class="level-item">
            <view class="level-indicator tn-bg-blue" />
            <text class="level-text">60-80%：能量良好，适度社交</text>
          </view>
          <view class="level-item">
            <view class="level-indicator tn-bg-yellow" />
            <text class="level-text">40-60%：能量一般，注意休息</text>
          </view>
          <view class="level-item">
            <view class="level-indicator tn-bg-orange" />
            <text class="level-text">20-40%：能量较低，建议休息</text>
          </view>
          <view class="level-item">
            <view class="level-indicator tn-bg-red" />
            <text class="level-text">0-20%：能量不足，请立即休息</text>
          </view>
        </view>
        <view v-if="canRest" class="popup-action">
          <view class="popup-action-btn tn-gradient-1 tn-shadow-blur" @tap="handleRest">
            <text class="popup-action-text">休息一下，恢复能量</text>
          </view>
        </view>
        <view v-else class="popup-action">
          <view class="cooldown-info">
            <text class="cooldown-text">冷却中，还需等待 {{ cooldownRemaining }}</text>
          </view>
        </view>
      </view>
    </wd-popup>

    <!-- 社交级别详情弹窗 -->
    <wd-popup v-model="showSocialLevel" position="bottom" closable>
      <view class="social-level-popup">
        <text class="popup-title">社交进度详情</text>
        <view class="level-detail">
          <text class="level-value tn-color-purplered">Level {{ socialLevel?.current_level || 1 }}</text>
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
            <view class="step-dot" :class="isLevelUnlocked(i) ? 'tn-bg-purplered' : ''">
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

    <!-- 自定义TabBar -->
    <CustomTabBar />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
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
import CustomTabBar from '@/components/common/CustomTabBar.vue'

const userInfo = ref<UserDetail | null>(null)
const energyData = ref<SocialEnergyResponse | null>(null)
const socialLevel = ref<SocialLevelResponse | null>(null)
const profileTags = ref<AIProfileTagResponse | null>(null)
const friendRequests = ref<FriendRequestListResponse | null>(null)
const isLoading = ref(false)
const isRefreshing = ref(false)
const defaultAvatar = '/static/images/default-avatar.png'
const showEnergyDetail = ref(false)
const showSocialLevel = ref(false)

const statusBarHeight = ref(0)
const sysInfo = uni.getSystemInfoSync()
statusBarHeight.value = sysInfo.statusBarHeight || 0

const formatUserMeta = computed(() => {
  const parts: string[] = []
  if (userInfo.value?.age_range) parts.push(userInfo.value.age_range)
  if (userInfo.value?.city) parts.push(userInfo.value.city)
  return parts.length > 0 ? parts.join(' · ') : '点击编辑资料'
})

const energyPercent = computed(() => Math.round(energyData.value?.energy || 0))
const energyStatusText = computed(() => energyData.value?.status || getEnergyStatusText(energyPercent.value))
const energyColor = computed(() => getEnergyColor(energyPercent.value))

const energyGradient = computed(() => {
  const p = energyPercent.value
  if (p >= 80) return 'linear-gradient(45deg, #36B349, #7BD437)'
  if (p >= 60) return 'linear-gradient(45deg, #01BEFF, #3D7EFF)'
  if (p >= 40) return 'linear-gradient(45deg, #FFBE28, #FF9A5C)'
  if (p >= 20) return 'linear-gradient(45deg, #FF9A5C, #F3683A)'
  return 'linear-gradient(45deg, #E83A30, #E72F8C)'
})

const canRest = computed(() => energyData.value?.can_rest ?? false)

const cooldownRemaining = computed(() => {
  const seconds = energyData.value?.rest_cooldown_remaining || 0
  if (seconds <= 0) return ''
  const minutes = Math.floor(seconds / 60)
  if (minutes > 0) return `${minutes}分${seconds % 60}秒`
  return `${seconds}秒`
})

const friendCount = computed(() => 0)
const diaryDays = computed(() => 0)
const pendingRequestCount = computed(() => friendRequests.value?.unread_count || 0)

const friendDesc = computed(() => {
  if (pendingRequestCount.value > 0) return `${pendingRequestCount.value} 条好友申请待处理`
  return `${friendCount.value} 位好友`
})

const favoriteCount = computed(() => 0)
const postCount = computed(() => 0)

const visibleProfileTags = computed(() => {
  const tags = profileTags.value?.tags || []
  return tags.filter(tag => tag.is_visible !== false).slice(0, 3)
})

const TAG_COLORS = ['purplered', 'purple', 'blue', 'indigo', 'cyan', 'teal', 'green']

function getTagColor(index: number): string {
  return TAG_COLORS[index % TAG_COLORS.length]
}

async function loadUserData(): Promise<void> {
  const userStore = useUserStore()
  if (!userStore.isLoggedIn) { uni.navigateTo({ url: '/pages/auth/login' }); return }
  isLoading.value = true
  try {
    const [profileRes, energyRes, levelRes, tagsRes, requestsRes] = await Promise.all([
      getMyProfile(), getSocialEnergy(), getSocialLevel(), getMyProfileTags(), getFriendRequests(),
    ])
    userInfo.value = profileRes
    energyData.value = energyRes
    socialLevel.value = levelRes
    profileTags.value = tagsRes
    friendRequests.value = requestsRes
    userStore.setUserInfo({
      id: profileRes.id, phone: profileRes.phone, nickname: profileRes.nickname || '',
      avatarUrl: profileRes.avatar_url || undefined, ageRange: profileRes.age_range || undefined,
      city: profileRes.city || undefined, occupation: profileRes.occupation || undefined,
      is_minor: profileRes.is_minor, createdAt: profileRes.created_at,
    })
    track(EventName.PAGE_VIEW, { page: 'mine' })
  } catch (error) { console.error('加载用户数据失败', error) }
  finally { isLoading.value = false }
}

function isLevelUnlocked(level: number): boolean {
  if (!socialLevel.value) return level === 1
  const status = socialLevel.value.unlock_status
  switch (level) {
    case 1: return status.level_1; case 2: return status.level_2
    case 3: return status.level_3; case 4: return status.level_4
    case 5: return status.level_5; case 6: return status.level_6
    default: return false
  }
}

async function handleRest(): Promise<void> {
  try {
    const { restSocialEnergy } = await import('@/api/modules/user')
    const result = await restSocialEnergy()
    energyData.value = {
      energy: result.new_energy, percentage: Math.round(result.new_energy) + '%',
      status: getEnergyStatusText(result.new_energy), can_rest: false,
      rest_cooldown_remaining: Math.floor(result.cooldown_until / 1000),
      updated_at: new Date().toISOString(),
    }
    uni.showToast({ title: result.message, icon: 'success' })
    showEnergyDetail.value = false
    track(EventName.SOCIAL_ENERGY_REST, { old_energy: result.old_energy, new_energy: result.new_energy })
  } catch (error) { console.error('休息失败', error) }
}

function handleShowEnergyDetail(): void { showEnergyDetail.value = true }
function handleShowSocialLevel(): void { showSocialLevel.value = true }
function handleGoSettings(): void { uni.navigateTo({ url: '/pages/settings/index' }) }
function handleEditProfile(): void { uni.navigateTo({ url: '/pages/profile/edit' }) }
function handleGoAITags(): void { uni.navigateTo({ url: '/pages/profile/ai-tags' }) }
function handleGoFriends(): void { uni.navigateTo({ url: '/pages/friends/index' }) }
function handleGoDiary(): void { uni.switchTab({ url: '/pages/diary/index' }) }
function handleGoFavorites(): void { uni.showToast({ title: '功能开发中', icon: 'none' }) }
function handleGoMyPosts(): void { uni.showToast({ title: '功能开发中', icon: 'none' }) }

function handleViewAvatar(): void {
  if (userInfo.value?.avatar_url) uni.previewImage({ urls: [userInfo.value.avatar_url] })
}

async function handleRefresh(): Promise<void> {
  isRefreshing.value = true
  await loadUserData()
  isRefreshing.value = false
}

onMounted(() => { loadUserData() })

usePageVisibleRefresh({ onVisible() { loadUserData() } })

onPullDownRefresh(() => { loadUserData().finally(() => uni.stopPullDownRefresh()) })
</script>

<style lang="scss" scoped>
.mine-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #F8F8FA;
  padding-bottom: env(safe-area-inset-bottom);
}

// ==================== 顶部渐变背景 ====================

.mine-header {
  background: linear-gradient(135deg, #01BEFF 0%, #3D7EFF 50%, #892FE8 100%);
  padding-bottom: 60rpx;
  border-radius: 0 0 40rpx 40rpx;
}

.page-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30rpx;
  height: 88rpx;
}

.nav-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #FFFFFF;
}

.nav-action {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

// ==================== 用户卡片 ====================

.user-card {
  display: flex;
  align-items: center;
  padding: 30rpx;
  margin: 20rpx 30rpx 0;

  &:active {
    opacity: 0.9;
  }
}

.user-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.3);
  margin-right: 24rpx;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.user-nickname {
  font-size: 36rpx;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 8rpx;
}

.user-meta {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.go-edit {
  font-size: 32rpx;
  color: rgba(255, 255, 255, 0.6);
}

// ==================== 统计数据 ====================

.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 60rpx;
  margin: 20rpx 30rpx 0;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: 20rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;

  &:active { opacity: 0.8; }
}

.stat-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.7);
}

.stat-divider {
  width: 2rpx;
  height: 50rpx;
  background-color: rgba(255, 255, 255, 0.2);
}

// ==================== 社交能量卡片 ====================

.energy-card {
  margin: -30rpx 30rpx 20rpx;
  padding: 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  position: relative;
  z-index: 10;

  &:active {
    transform: scale(0.98);
    transition: transform 0.3s ease;
  }
}

.energy-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.energy-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.energy-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.energy-percent {
  font-size: 36rpx;
  font-weight: 700;
}

.energy-bar {
  height: 16rpx;
  background-color: #F4F4F5;
  border-radius: 5000rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
}

.energy-fill {
  height: 100%;
  border-radius: 5000rpx;
  transition: width 0.3s ease;
}

.energy-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.energy-status {
  font-size: 22rpx;
  color: #838383;
}

.rest-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8rpx 24rpx;
  border-radius: 5000rpx;

  &:active { opacity: 0.8; }
}

.rest-text {
  font-size: 22rpx;
  color: #FFFFFF;
  font-weight: 600;
}

// ==================== 社交进度卡片 ====================

.social-level-card {
  margin: 0 30rpx 20rpx;
  padding: 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;

  &:active {
    transform: scale(0.98);
    transition: transform 0.3s ease;
  }
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.level-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.level-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.level-current {
  font-size: 26rpx;
  font-weight: 700;
}

.level-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.level-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  background-color: #F4F4F5;
  border-radius: 50%;
  transition: all 0.3s ease;

  &.is-unlocked {
    background: linear-gradient(45deg, #E72F8C, #F360A7);
    box-shadow: 0rpx 8rpx 24rpx 0rpx rgba(231, 47, 140, 0.3);
  }
}

.level-dot-num {
  font-size: 24rpx;
  color: #838383;
  font-weight: 600;

  .is-unlocked & { color: #FFFFFF; }
}

.level-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.level-hint-text {
  font-size: 24rpx;
  color: #838383;
  flex: 1;
}

.level-go {
  font-size: 28rpx;
  color: #AAAAAA;
}

// ==================== AI画像 ====================

.ai-profile-card {
  margin: 0 30rpx 20rpx;
  padding: 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;

  &:active {
    transform: scale(0.98);
    transition: transform 0.3s ease;
  }
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.profile-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.profile-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
}

.profile-go {
  font-size: 28rpx;
  color: #AAAAAA;
}

.profile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.profile-tag {
  font-size: 22rpx;
  padding: 8rpx 20rpx;
  border-radius: 5000rpx;
  background-color: rgba(137, 47, 232, 0.08);
}

.more-tags {
  font-size: 22rpx;
  color: #080808;
  padding: 8rpx 20rpx;
}

.empty-profile {
  padding: 12rpx 0;
}

.empty-text {
  font-size: 24rpx;
  color: #838383;
}

// ==================== 功能入口列表 ====================

.menu-list {
  display: flex;
  flex-direction: column;
  margin: 0 30rpx 30rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx;

  &:active { background-color: #F8F8FA; }
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  margin-right: 24rpx;
  flex-shrink: 0;
}

.menu-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.menu-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #080808;
  margin-bottom: 4rpx;
}

.menu-desc {
  font-size: 24rpx;
  color: #838383;
}

.menu-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36rpx;
  height: 36rpx;
  padding: 0 12rpx;
  background-color: #E83A30;
  border-radius: 5000rpx;
  margin-right: 16rpx;
}

.badge-text {
  font-size: 22rpx;
  color: #FFFFFF;
  font-weight: 600;
}

.menu-arrow {
  font-size: 28rpx;
  color: #AAAAAA;
}

.menu-divider {
  height: 2rpx;
  background-color: #F4F4F5;
  margin: 0 30rpx;
}

// ==================== 弹窗样式 ====================

.energy-detail-popup,
.social-level-popup {
  padding: 40rpx 30rpx;
  padding-bottom: calc(env(safe-area-inset-bottom) + 40rpx);
}

.popup-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #080808;
  text-align: center;
  margin-bottom: 30rpx;
}

.energy-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30rpx;
}

.energy-value {
  font-size: 80rpx;
  font-weight: 700;
  margin-bottom: 12rpx;
}

.energy-status {
  font-size: 30rpx;
  color: #838383;
}

.energy-tips {
  padding: 24rpx;
  background-color: #F8F8FA;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

.tips-text {
  font-size: 26rpx;
  color: #838383;
  line-height: 1.6;
}

.energy-levels {
  padding: 24rpx;
  background-color: #F8F8FA;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

.levels-title {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
  font-weight: 600;
}

.level-item {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;

  &:last-child { margin-bottom: 0; }
}

.level-indicator {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.level-text {
  font-size: 24rpx;
  color: #838383;
}

.popup-action {
  margin-top: 20rpx;
}

.popup-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  border-radius: 5000rpx;
}

.popup-action-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.cooldown-info {
  text-align: center;
  margin-bottom: 16rpx;
}

.cooldown-text {
  font-size: 26rpx;
  color: #838383;
}

// ==================== 社交级别详情 ====================

.level-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30rpx;
}

.level-value {
  font-size: 56rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.level-name {
  font-size: 34rpx;
  color: #080808;
  margin-bottom: 8rpx;
  font-weight: 600;
}

.level-desc {
  font-size: 26rpx;
  color: #838383;
  text-align: center;
}

.level-steps {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-bottom: 30rpx;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background-color: #F8F8FA;
  border-radius: 16rpx;
  opacity: 0.5;

  &.is-unlocked { opacity: 1; }
  &.is-current {
    background: linear-gradient(135deg, rgba(231, 47, 140, 0.08), rgba(137, 47, 232, 0.08));
    opacity: 1;
  }
}

.step-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
  background-color: #E0E0E0;
  border-radius: 50%;
  margin-right: 20rpx;
}

.step-num {
  font-size: 24rpx;
  color: #FFFFFF;
  font-weight: 600;
}

.step-desc {
  font-size: 26rpx;
  color: #080808;
}

.level-stats {
  padding: 24rpx;
  background-color: #F8F8FA;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.stats-title {
  font-size: 26rpx;
  color: #838383;
  margin-bottom: 16rpx;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-value {
  font-size: 34rpx;
  font-weight: 700;
  color: #080808;
}

.stats-label {
  font-size: 22rpx;
  color: #838383;
  margin-top: 4rpx;
}

.next-action {
  padding: 24rpx;
  background: linear-gradient(135deg, rgba(1, 190, 255, 0.1), rgba(61, 126, 255, 0.1));
  border-radius: 16rpx;
}

.action-hint {
  font-size: 26rpx;
  color: #3D7EFF;
}
</style>
