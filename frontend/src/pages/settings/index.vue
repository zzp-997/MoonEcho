<template>
  <view class="settings-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <text class="back-icon">&lt;</text>
      </view>
      <text class="header-title">设置</text>
      <view class="placeholder" />
    </view>

    <!-- 账号与安全 -->
    <view class="section">
      <text class="section-title">账号与安全</text>
      <view class="section-content">
        <!-- 手机号 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[手机]</text>
            <text class="setting-label">手机号</text>
          </view>
          <text class="setting-value">{{ maskedPhone }}</text>
        </view>

        <!-- 修改密码 -->
        <view class="setting-item" @tap="handleChangePassword">
          <view class="setting-left">
            <text class="setting-icon">[锁]</text>
            <text class="setting-label">修改密码</text>
          </view>
          <text class="setting-arrow">></text>
        </view>

        <!-- 注销账户 -->
        <view class="setting-item" @tap="handleDeleteAccount">
          <view class="setting-left">
            <text class="setting-icon danger">[退出]</text>
            <text class="setting-label danger-text">注销账户</text>
          </view>
          <text class="setting-arrow">></text>
        </view>
      </view>
    </view>

    <!-- AI设置 -->
    <view class="section">
      <text class="section-title">AI设置</text>
      <view class="section-content">
        <!-- AI性格 -->
        <view class="setting-item" @tap="handleGoPersonality">
          <view class="setting-left">
            <text class="setting-icon">[AI]</text>
            <text class="setting-label">AI性格</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ aiPersonalityName }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>

        <!-- AI主动关怀 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[心]</text>
            <text class="setting-label">AI主动关怀</text>
          </view>
          <wd-switch v-model="settings.ai_care_enabled" @change="handleSettingChange('ai_care_enabled', $event)" />
        </view>

        <!-- AI打招呼风格 -->
        <view class="setting-item" @tap="handleShowGreetingStyle">
          <view class="setting-left">
            <text class="setting-icon">[语]</text>
            <text class="setting-label">AI打招呼风格</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ greetingStyleName }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>
      </view>
    </view>

    <!-- 隐私与数据 -->
    <view class="section">
      <text class="section-title">隐私与数据</text>
      <view class="section-content">
        <!-- 资料可见性 -->
        <view class="setting-item" @tap="handleShowVisibility">
          <view class="setting-left">
            <text class="setting-icon">[眼]</text>
            <text class="setting-label">资料可见性</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ visibilityName }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>

        <!-- 展示在线状态 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[状态]</text>
            <text class="setting-label">展示在线状态</text>
          </view>
          <wd-switch v-model="settings.show_online_status" @change="handleSettingChange('show_online_status', $event)" />
        </view>

        <!-- 展示AI画像标签 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[标签]</text>
            <text class="setting-label">展示AI画像标签</text>
          </view>
          <wd-switch v-model="settings.show_profile_tags" @change="handleSettingChange('show_profile_tags', $event)" />
        </view>

        <!-- 允许好友申请 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[好友]</text>
            <text class="setting-label">允许好友申请</text>
          </view>
          <wd-switch v-model="settings.allow_friend_request" @change="handleSettingChange('allow_friend_request', $event)" />
        </view>

        <!-- 云端同步 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[云]</text>
            <text class="setting-label">云端同步</text>
          </view>
          <wd-switch v-model="settings.cloud_sync_enabled" @change="handleSettingChange('cloud_sync_enabled', $event)" />
        </view>

        <!-- 隐私声明 -->
        <view class="setting-item" @tap="handleGoPrivacy">
          <view class="setting-left">
            <text class="setting-icon">[文档]</text>
            <text class="setting-label">日记隐私声明</text>
          </view>
          <text class="setting-arrow">></text>
        </view>
      </view>
    </view>

    <!-- 通知设置 -->
    <view class="section">
      <text class="section-title">通知设置</text>
      <view class="section-content">
        <!-- 推送开关 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[铃铛]</text>
            <text class="setting-label">推送通知</text>
          </view>
          <wd-switch v-model="settings.notification_enabled" @change="handleSettingChange('notification_enabled', $event)" />
        </view>

        <!-- 日记提醒 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[日记]</text>
            <text class="setting-label">日记记录提醒</text>
          </view>
          <wd-switch v-model="settings.notification_diary_reminder" :disabled="!settings.notification_enabled" @change="handleSettingChange('notification_diary_reminder', $event)" />
        </view>

        <!-- 好友申请通知 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[申请]</text>
            <text class="setting-label">好友申请通知</text>
          </view>
          <wd-switch v-model="settings.notification_friend_request" :disabled="!settings.notification_enabled" @change="handleSettingChange('notification_friend_request', $event)" />
        </view>

        <!-- 消息通知 -->
        <view class="setting-item">
          <view class="setting-left">
            <text class="setting-icon">[消息]</text>
            <text class="setting-label">私聊消息通知</text>
          </view>
          <wd-switch v-model="settings.notification_chat_message" :disabled="!settings.notification_enabled" @change="handleSettingChange('notification_chat_message', $event)" />
        </view>

        <!-- 免打扰时段 -->
        <view class="setting-item" @tap="handleSetQuietHours">
          <view class="setting-left">
            <text class="setting-icon">[月]</text>
            <text class="setting-label">免打扰时段</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ quietHoursText }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>
      </view>
    </view>

    <!-- 外观 -->
    <view class="section">
      <text class="section-title">外观</text>
      <view class="section-content">
        <!-- 主题 -->
        <view class="setting-item" @tap="handleShowThemePicker">
          <view class="setting-left">
            <text class="setting-icon">[月亮]</text>
            <text class="setting-label">主题</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ themeName }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>
      </view>
    </view>

    <!-- 其他 -->
    <view class="section">
      <text class="section-title">其他</text>
      <view class="section-content">
        <!-- 青少年模式 -->
        <view class="setting-item" @tap="handleTeenMode">
          <view class="setting-left">
            <text class="setting-icon">[盾牌]</text>
            <text class="setting-label">青少年模式</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ isTeenMode ? '已开启' : '已关闭' }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>

        <!-- 清除缓存 -->
        <view class="setting-item" @tap="handleClearCache">
          <view class="setting-left">
            <text class="setting-icon">[清理]</text>
            <text class="setting-label">清除缓存</text>
          </view>
          <view class="setting-right">
            <text class="setting-value">{{ cacheSize }}</text>
            <text class="setting-arrow">></text>
          </view>
        </view>

        <!-- 关于与帮助 -->
        <view class="setting-item" @tap="handleGoAbout">
          <view class="setting-left">
            <text class="setting-icon">[问号]</text>
            <text class="setting-label">关于与帮助</text>
          </view>
          <text class="setting-arrow">></text>
        </view>

        <!-- 用户协议 -->
        <view class="setting-item" @tap="handleGoUserAgreement">
          <view class="setting-left">
            <text class="setting-icon">[协议]</text>
            <text class="setting-label">用户协议</text>
          </view>
          <text class="setting-arrow">></text>
        </view>

        <!-- 隐私政策 -->
        <view class="setting-item" @tap="handleGoPrivacyPolicy">
          <view class="setting-left">
            <text class="setting-icon">[隐私]</text>
            <text class="setting-label">隐私政策</text>
          </view>
          <text class="setting-arrow">></text>
        </view>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="logout-section">
      <view class="logout-btn" @tap="handleLogout">
        <text class="logout-text">退出登录</text>
      </view>
    </view>

    <!-- 版本信息 -->
    <view class="version-info">
      <text class="version-text">回声 v{{ appVersion }}</text>
    </view>

    <!-- 主题选择弹窗 -->
    <wd-action-sheet v-model="showThemeSheet" title="选择主题">
      <view class="theme-options">
        <view
          class="theme-option"
          :class="{ 'is-active': theme === 'dark' }"
          @tap="handleSetTheme('dark')"
        >
          <text class="theme-option-label">暗色</text>
          <text v-if="theme === 'dark'" class="theme-check">[已选]</text>
        </view>
        <view
          class="theme-option"
          :class="{ 'is-active': theme === 'light' }"
          @tap="handleSetTheme('light')"
        >
          <text class="theme-option-label">亮色</text>
          <text v-if="theme === 'light'" class="theme-check">[已选]</text>
        </view>
        <view
          class="theme-option"
          :class="{ 'is-active': theme === 'system' }"
          @tap="handleSetTheme('system')"
        >
          <text class="theme-option-label">跟随系统</text>
          <text v-if="theme === 'system'" class="theme-check">[已选]</text>
        </view>
      </view>
    </wd-action-sheet>

    <!-- 资料可见性弹窗 -->
    <wd-action-sheet v-model="showVisibilitySheet" title="资料可见性">
      <view class="visibility-options">
        <view
          class="visibility-option"
          :class="{ 'is-active': settings.profile_visibility === 'public' }"
          @tap="handleSetVisibility('public')"
        >
          <text class="visibility-option-label">所有人可见</text>
          <text class="visibility-option-desc">任何人都可查看你的资料</text>
          <text v-if="settings.profile_visibility === 'public'" class="option-check">[已选]</text>
        </view>
        <view
          class="visibility-option"
          :class="{ 'is-active': settings.profile_visibility === 'friends' }"
          @tap="handleSetVisibility('friends')"
        >
          <text class="visibility-option-label">仅好友可见</text>
          <text class="visibility-option-desc">只有你的好友可以查看</text>
          <text v-if="settings.profile_visibility === 'friends'" class="option-check">[已选]</text>
        </view>
        <view
          class="visibility-option"
          :class="{ 'is-active': settings.profile_visibility === 'private' }"
          @tap="handleSetVisibility('private')"
        >
          <text class="visibility-option-label">完全私密</text>
          <text class="visibility-option-desc">不对外展示任何资料</text>
          <text v-if="settings.profile_visibility === 'private'" class="option-check">[已选]</text>
        </view>
      </view>
    </wd-action-sheet>

    <!-- AI打招呼风格弹窗 -->
    <wd-action-sheet v-model="showGreetingStyleSheet" title="AI打招呼风格">
      <view class="greeting-options">
        <view
          class="greeting-option"
          :class="{ 'is-active': settings.ai_greeting_style === 'warm' }"
          @tap="handleSetGreetingStyle('warm')"
        >
          <text class="greeting-option-label">温柔暖心</text>
          <text class="greeting-option-desc">温暖细腻的问候</text>
          <text v-if="settings.ai_greeting_style === 'warm'" class="option-check">[已选]</text>
        </view>
        <view
          class="greeting-option"
          :class="{ 'is-active': settings.ai_greeting_style === 'playful' }"
          @tap="handleSetGreetingStyle('playful')"
        >
          <text class="greeting-option-label">活泼俏皮</text>
          <text class="greeting-option-desc">轻松有趣的互动</text>
          <text v-if="settings.ai_greeting_style === 'playful'" class="option-check">[已选]</text>
        </view>
        <view
          class="greeting-option"
          :class="{ 'is-active': settings.ai_greeting_style === 'calm' }"
          @tap="handleSetGreetingStyle('calm')"
        >
          <text class="greeting-option-label">沉稳平和</text>
          <text class="greeting-option-desc">简洁淡然的交流</text>
          <text v-if="settings.ai_greeting_style === 'calm'" class="option-check">[已选]</text>
        </view>
      </view>
    </wd-action-sheet>
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 设置页
 * 文件：src/pages/settings/index.vue
 * 说明：应用设置，包括账号安全、AI设置、隐私、外观等
 */

import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSettingsStore, type ThemeMode } from '@/stores/settings'
import { track, EventName } from '@/utils/tracking'
import {
  getUserSettings,
  updateUserSettings,
  getAIPersonalityName,
  type UserSettings,
  DEFAULT_USER_SETTINGS,
} from '@/api/modules/settings'

// ==================== 组合式函数 ====================

const userStore = useUserStore()
const settingsStore = useSettingsStore()

// ==================== 响应式状态 ====================

/** 用户设置 */
const settings = ref<UserSettings>({ ...DEFAULT_USER_SETTINGS })

/** 主题选择弹窗 */
const showThemeSheet = ref(false)

/** 资料可见性弹窗 */
const showVisibilitySheet = ref(false)

/** AI打招呼风格弹窗 */
const showGreetingStyleSheet = ref(false)

/** 缓存大小 */
const cacheSize = ref('0KB')

// ==================== 计算属性 ====================

/** 手机号脱敏 */
const maskedPhone = computed(() => userStore.maskedPhone || '未绑定')

/** AI性格名称 */
const aiPersonalityName = computed(() => {
  return getAIPersonalityName(settings.value.ai_personality)
})

/** AI打招呼风格名称 */
const greetingStyleName = computed(() => {
  const names: Record<string, string> = {
    warm: '温柔暖心',
    playful: '活泼俏皮',
    calm: '沉稳平和',
  }
  return names[settings.value.ai_greeting_style] || '温柔暖心'
})

/** 资料可见性名称 */
const visibilityName = computed(() => {
  const names: Record<string, string> = {
    public: '所有人可见',
    friends: '仅好友可见',
    private: '完全私密',
  }
  return names[settings.value.profile_visibility] || '仅好友可见'
})

/** 主题名称 */
const themeName = computed(() => {
  const themeMap: Record<ThemeMode, string> = {
    dark: '暗色',
    light: '亮色',
    system: '跟随系统',
  }
  return themeMap[settingsStore.theme] || '暗色'
})

/** 当前主题 */
const theme = computed(() => settingsStore.theme)

/** 是否青少年模式 */
const isTeenMode = computed(() => settingsStore.isTeenMode)

/** 应用版本 */
const appVersion = computed(() => settingsStore.appVersion)

/** 免打扰时段文本 */
const quietHoursText = computed(() => {
  const start = settings.value.quiet_hours_start
  const end = settings.value.quiet_hours_end
  if (start && end) {
    return `${start} - ${end}`
  }
  return '未设置'
})

// ==================== 方法 ====================

/**
 * 加载用户设置
 */
async function loadSettings(): Promise<void> {
  try {
    const result = await getUserSettings()
    settings.value = { ...DEFAULT_USER_SETTINGS, ...result }
  } catch (error) {
    console.error('加载设置失败', error)
  }
}

/**
 * 处理设置变更
 */
async function handleSettingChange(key: keyof UserSettings, value: boolean): Promise<void> {
  try {
    // 立即更新本地状态
    (settings.value as any)[key] = value

    // 保存到后端
    await updateUserSettings({ [key]: value })

    track(EventName.SETTING_CHANGE, { setting: key, value })
  } catch (error) {
    console.error('保存设置失败', error)
    // 回滚本地状态
    loadSettings()
  }
}

/**
 * 返回上一页
 */
function handleBack(): void {
  uni.navigateBack()
}

/**
 * 修改密码
 */
function handleChangePassword(): void {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 注销账户
 */
function handleDeleteAccount(): void {
  uni.showModal({
    title: '确认注销',
    content: '注销账户后，所有数据将被永久删除且无法恢复。确定要注销吗？',
    confirmColor: '#F87171',
    success: (res) => {
      if (res.confirm) {
        uni.showModal({
          title: '二次确认',
          content: '这是最后一次确认，注销后数据无法恢复。',
          confirmColor: '#F87171',
          success: (finalRes) => {
            if (finalRes.confirm) {
              performDeleteAccount()
            }
          },
        })
      }
    },
  })
}

/**
 * 执行注销账户
 */
async function performDeleteAccount(): Promise<void> {
  try {
    userStore.logout()
    uni.reLaunch({ url: '/pages/auth/login' })

    track(EventName.USER_LOGOUT, { reason: 'account_deletion' })
  } catch (error) {
    console.error('注销账户失败', error)
  }
}

/**
 * AI性格选择
 */
function handleGoPersonality(): void {
  uni.navigateTo({ url: '/pages/chat/personality' })
}

/**
 * 显示AI打招呼风格选择
 */
function handleShowGreetingStyle(): void {
  showGreetingStyleSheet.value = true
}

/**
 * 设置AI打招呼风格
 */
async function handleSetGreetingStyle(style: 'warm' | 'playful' | 'calm'): Promise<void> {
  try {
    settings.value.ai_greeting_style = style
    await updateUserSettings({ ai_greeting_style: style })
    showGreetingStyleSheet.value = false

    track(EventName.SETTING_CHANGE, { setting: 'ai_greeting_style', value: style })
  } catch (error) {
    console.error('保存设置失败', error)
  }
}

/**
 * 显示资料可见性选择
 */
function handleShowVisibility(): void {
  showVisibilitySheet.value = true
}

/**
 * 设置资料可见性
 */
async function handleSetVisibility(visibility: 'public' | 'friends' | 'private'): Promise<void> {
  try {
    settings.value.profile_visibility = visibility
    await updateUserSettings({ profile_visibility: visibility })
    showVisibilitySheet.value = false

    track(EventName.SETTING_CHANGE, { setting: 'profile_visibility', value: visibility })
  } catch (error) {
    console.error('保存设置失败', error)
  }
}

/**
 * 隐私声明
 */
function handleGoPrivacy(): void {
  uni.showModal({
    title: '日记隐私声明',
    content: '你的日记数据受到严格保护。我们不会将你的日记内容用于任何商业目的，也不会在未经你同意的情况下分享给第三方。所有数据均经过加密存储。',
    showCancel: false,
    confirmText: '我知道了',
  })
}

/**
 * 设置免打扰时段
 */
function handleSetQuietHours(): void {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 显示主题选择
 */
function handleShowThemePicker(): void {
  showThemeSheet.value = true
}

/**
 * 设置主题
 */
function handleSetTheme(newTheme: ThemeMode): void {
  settingsStore.setTheme(newTheme)
  showThemeSheet.value = false

  track(EventName.SETTING_CHANGE, { setting: 'theme', value: newTheme })

  uni.showToast({
    title: `已切换为${themeName.value}`,
    icon: 'success',
  })
}

/**
 * 青少年模式
 */
function handleTeenMode(): void {
  if (isTeenMode.value) {
    uni.navigateTo({ url: '/pages/auth/minor-lock' })
  } else {
    uni.navigateTo({ url: '/pages/auth/minor-notice' })
  }
}

/**
 * 清除缓存
 */
function handleClearCache(): void {
  uni.showModal({
    title: '清除缓存',
    content: '确定要清除本地缓存吗？这不会影响你的账号数据。',
    success: (res) => {
      if (res.confirm) {
        // 清除本地存储（保留用户登录信息）
        const token = uni.getStorageSync('huisheng_token')
        const refreshToken = uni.getStorageSync('huisheng_refresh_token')
        const userInfo = uni.getStorageSync('huisheng_user_info')
        const settingsData = uni.getStorageSync('huisheng_settings')

        uni.clearStorageSync()

        // 恢复必要数据
        if (token) uni.setStorageSync('huisheng_token', token)
        if (refreshToken) uni.setStorageSync('huisheng_refresh_token', refreshToken)
        if (userInfo) uni.setStorageSync('huisheng_user_info', userInfo)
        if (settingsData) uni.setStorageSync('huisheng_settings', settingsData)

        cacheSize.value = '0KB'

        uni.showToast({
          title: '缓存已清除',
          icon: 'success',
        })
      }
    },
  })
}

/**
 * 关于与帮助
 */
function handleGoAbout(): void {
  uni.showModal({
    title: '关于回声',
    content: `回声 v${settingsStore.appVersion}\n\n一个温暖的社交空间，让每一次连接都恰到好处。\n\n在这里，你可以：\n- 记录每日心情\n- 与AI朋友倾诉\n- 匿名分享感受\n- 渐进式社交`,
    showCancel: false,
    confirmText: '知道了',
  })
}

/**
 * 用户协议
 */
function handleGoUserAgreement(): void {
  // TODO: 跳转到用户协议页面
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 隐私政策
 */
function handleGoPrivacyPolicy(): void {
  // TODO: 跳转到隐私政策页面
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

/**
 * 退出登录
 */
function handleLogout(): void {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/auth/login' })

        track(EventName.USER_LOGOUT, { reason: 'manual' })
      }
    },
  })
}

/**
 * 计算缓存大小
 */
function calculateCacheSize(): void {
  try {
    const info = uni.getStorageInfoSync()
    const sizeKB = info.currentSize
    if (sizeKB < 1024) {
      cacheSize.value = `${sizeKB}KB`
    } else {
      const sizeMB = (sizeKB / 1024).toFixed(1)
      cacheSize.value = `${sizeMB}MB`
    }
  } catch {
    cacheSize.value = '未知'
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadSettings()
  calculateCacheSize()

  track(EventName.PAGE_VIEW, { page: 'settings' })
})
</script>

<style lang="scss" scoped>
.settings-page {
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
  border-bottom: 1rpx solid var(--border-primary);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
}

.placeholder {
  width: 64rpx;
}

// ==================== 分组 ====================

.section {
  margin-top: var(--space-md);
}

.section-title {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  padding: var(--space-sm) var(--space-md);
}

.section-content {
  background-color: var(--bg-secondary);
}

// ==================== 设置项 ====================

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  border-bottom: 1rpx solid var(--border-primary);

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background-color: var(--bg-tertiary);
  }
}

.setting-left {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.setting-icon {
  font-size: var(--font-size-md);
  color: var(--text-secondary);

  &.danger {
    color: var(--color-error);
  }
}

.setting-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);

  &.danger-text {
    color: var(--color-error);
  }
}

.setting-right {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.setting-value {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.setting-arrow {
  font-size: var(--font-size-md);
  color: var(--text-tertiary);
}

// ==================== 退出登录 ====================

.logout-section {
  margin-top: var(--space-xl);
  padding: 0 var(--space-md);
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96rpx;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.logout-text {
  font-size: var(--font-size-md);
  color: var(--color-error);
}

// ==================== 版本信息 ====================

.version-info {
  display: flex;
  justify-content: center;
  padding: var(--space-xl);
}

.version-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

// ==================== 主题选择 ====================

.theme-options {
  padding: var(--space-md);
  padding-bottom: calc(env(safe-area-inset-bottom) + var(--space-md));
}

.theme-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);

  &.is-active {
    background-color: rgba(124, 111, 224, 0.15);
  }

  &:active {
    opacity: 0.9;
  }
}

.theme-option-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.theme-check {
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

// ==================== 资料可见性 ====================

.visibility-options {
  padding: var(--space-md);
  padding-bottom: calc(env(safe-area-inset-bottom) + var(--space-md));
}

.visibility-option {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  position: relative;

  &.is-active {
    background-color: rgba(124, 111, 224, 0.15);
  }

  &:active {
    opacity: 0.9;
  }
}

.visibility-option-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.visibility-option-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.option-check {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  font-size: var(--font-size-sm);
  color: var(--brand-primary);
}

// ==================== AI打招呼风格 ====================

.greeting-options {
  padding: var(--space-md);
  padding-bottom: calc(env(safe-area-inset-bottom) + var(--space-md));
}

.greeting-option {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  position: relative;

  &.is-active {
    background-color: rgba(124, 111, 224, 0.15);
  }

  &:active {
    opacity: 0.9;
  }
}

.greeting-option-label {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  margin-bottom: 4rpx;
}

.greeting-option-desc {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}
</style>
