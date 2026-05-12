<template>
  <view class="container">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-left" @click="handleBack">
        <wd-icon name="arrow-left" size="20px" color="#080808" />
      </view>
      <view class="header-title">通知设置</view>
      <view class="header-right" />
    </view>

    <!-- 设置内容 -->
    <view class="settings-content">
      <!-- 推送总开关 -->
      <view class="settings-section">
        <view class="setting-item main-switch">
          <view class="setting-info">
            <text class="setting-title">推送通知</text>
            <text class="setting-desc">接收各类通知推送</text>
          </view>
          <wd-switch
            v-model="pushEnabled"
            :loading="isLoading"
            @change="handlePushChange"
          />
        </view>
      </view>

      <!-- 分类开关 -->
      <view class="settings-section">
        <view class="section-title">通知类型</view>

        <!-- AI关怀 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">AI关怀</text>
            <text class="setting-desc">AI主动关怀提醒</text>
          </view>
          <wd-switch
            v-model="typesEnabled.ai_care"
            :disabled="!pushEnabled"
            @change="handleTypeChange('ai_care', $event)"
          />
        </view>

        <!-- 危机干预（强制开启） -->
        <view class="setting-item forced">
          <view class="setting-info">
            <view class="setting-title-row">
              <text class="setting-title">危机干预</text>
              <view class="forced-tag">必开</view>
            </view>
            <text class="setting-desc">危机干预相关通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.crisis_alert"
            :disabled="true"
          />
        </view>

        <!-- 好友相关 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">好友请求</text>
            <text class="setting-desc">收到好友请求时通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.friend_request"
            :disabled="!pushEnabled"
            @change="handleTypeChange('friend_request', $event)"
          />
        </view>

        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">好友接受</text>
            <text class="setting-desc">好友请求被接受时通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.friend_accept"
            :disabled="!pushEnabled"
            @change="handleTypeChange('friend_accept', $event)"
          />
        </view>

        <!-- 社交互动 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">树洞回复</text>
            <text class="setting-desc">树洞收到回复时通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.treehole_reply"
            :disabled="!pushEnabled"
            @change="handleTypeChange('treehole_reply', $event)"
          />
        </view>

        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">广场评论</text>
            <text class="setting-desc">动态收到评论时通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.square_comment"
            :disabled="!pushEnabled"
            @change="handleTypeChange('square_comment', $event)"
          />
        </view>

        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">广场点赞</text>
            <text class="setting-desc">动态收到点赞时通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.square_like"
            :disabled="!pushEnabled"
            @change="handleTypeChange('square_like', $event)"
          />
        </view>

        <!-- 周报 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">周报通知</text>
            <text class="setting-desc">情绪周报生成提醒</text>
          </view>
          <wd-switch
            v-model="typesEnabled.weekly_report"
            :disabled="!pushEnabled"
            @change="handleTypeChange('weekly_report', $event)"
          />
        </view>

        <!-- 系统通知 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">系统通知</text>
            <text class="setting-desc">重要系统更新通知</text>
          </view>
          <wd-switch
            v-model="typesEnabled.system"
            :disabled="!pushEnabled"
            @change="handleTypeChange('system', $event)"
          />
        </view>

        <!-- 更新通知 -->
        <view class="setting-item">
          <view class="setting-info">
            <text class="setting-title">更新通知</text>
            <text class="setting-desc">应用版本更新提醒</text>
          </view>
          <wd-switch
            v-model="typesEnabled.update"
            :disabled="!pushEnabled"
            @change="handleTypeChange('update', $event)"
          />
        </view>
      </view>

      <!-- 提示说明 -->
      <view class="tips-section">
        <text class="tips-text">
          危机干预通知为强制开启，确保您在需要时能够及时获得帮助。
        </text>
      </view>
    </view>

    <!-- 加载状态 -->
    <wd-loading v-if="isSettingsLoading && !settings" class="page-loading" />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 通知设置页
 * 文件：src/pages/notification/settings.vue
 * 说明：推送通知开关设置，危机干预类型强制开启
 */
import { ref, onMounted } from 'vue'
import { useNotification, getDefaultTypesEnabled } from '@/composables/useNotification'
import { usePageVisibleRefresh } from '@/composables/usePageVisibleRefresh'
import type { NotificationSettings } from '@/api/modules/notification'
import { track, EventName } from '@/utils/tracking'

// ==================== 组合式函数 ====================

const {
  settings,
  isSettingsLoading,
  loadSettings,
  updatePushEnabled,
  updateTypeEnabled
} = useNotification()

// ==================== 响应式状态 ====================

/** 推送总开关 */
const pushEnabled = ref(true)

/** 各类型开关状态 */
const typesEnabled = ref<NotificationSettings['types_enabled']>(getDefaultTypesEnabled())

/** 是否正在加载 */
const isLoading = ref(false)

// ==================== 生命周期 ====================

onMounted(async () => {
  await initSettings()
})

usePageVisibleRefresh({
  onVisible() {
    track(EventName.PAGE_VIEW, { page: 'notification_settings' })
  }
})

// ==================== 初始化 ====================

async function initSettings() {
  isLoading.value = true
  try {
    await loadSettings()

    // 同步设置到本地状态
    if (settings.value) {
      pushEnabled.value = settings.value.push_enabled
      typesEnabled.value = { ...settings.value.types_enabled }
    }
  } finally {
    isLoading.value = false
  }
}

// ==================== 事件处理 ====================

async function handlePushChange(value: boolean) {
  isLoading.value = true
  try {
    const success = await updatePushEnabled(value)
    if (!success) {
      // 恢复原状态
      pushEnabled.value = !value
    }
  } finally {
    isLoading.value = false
  }
}

async function handleTypeChange(
  type: keyof NotificationSettings['types_enabled'],
  value: boolean
) {
  isLoading.value = true
  try {
    const success = await updateTypeEnabled(type, value)
    if (!success) {
      // 恢复原状态
      typesEnabled.value[type] = !value
    }
  } finally {
    isLoading.value = false
  }
}

function handleBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #F8F8FA;
}

// ==================== 头部 ====================

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 32rpx;
  padding-top: calc(env(safe-area-inset-top));
  background: linear-gradient(135deg, #FFBE28, #FF9A5C);
}

.header-left {
  display: flex;
  align-items: center;
  width: 80rpx;
  height: 88rpx;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #FFFFFF;
}

.header-right {
  width: 80rpx;
}

// ==================== 设置内容 ====================

.settings-content {
  flex: 1;
  padding: 24rpx 32rpx;
}

.settings-section {
  margin-bottom: 32rpx;
  background-color: #FFFFFF;
  border-radius: 20rpx;
  box-shadow: 0rpx 4rpx 20rpx 0rpx rgba(0,0,0,0.05);
  overflow: hidden;
}

.section-title {
  padding: 24rpx 32rpx 16rpx;
  font-size: 26rpx;
  color: #838383;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  border-bottom: 1rpx solid #F4F4F5;

  &:last-child {
    border-bottom: none;
  }

  &.main-switch {
    padding: 40rpx 32rpx;
  }

  &.forced {
    opacity: 0.7;
  }
}

.setting-info {
  flex: 1;
  min-width: 0;
}

.setting-title-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.setting-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #080808;
}

.setting-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #838383;
}

.forced-tag {
  padding: 4rpx 12rpx;
  font-size: 22rpx;
  color: #FFBE28;
  background-color: rgba(255,190,40,0.1);
  border-radius: 10rpx;
}

// ==================== 提示说明 ====================

.tips-section {
  margin-top: 48rpx;
  padding: 24rpx;
  background-color: rgba(1,190,255,0.1);
  border-radius: 20rpx;
}

.tips-text {
  font-size: 26rpx;
  line-height: 1.6;
  color: #01BEFF;
}

// ==================== 加载状态 ====================

.page-loading {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
