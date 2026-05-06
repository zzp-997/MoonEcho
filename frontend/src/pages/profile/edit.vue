<template>
  <view class="edit-profile-page">
    <!-- 顶部导航栏 -->
    <view class="page-header">
      <view class="back-btn" @tap="handleBack">
        <wd-icon name="arrow-left" size="20px" color="var(--text-primary)" />
      </view>
      <text class="header-title">编辑资料</text>
      <view class="save-btn" :class="{ 'is-disabled': !canSave }" @tap="handleSave">
        <text class="save-text">保存</text>
      </view>
    </view>

    <!-- 头像 -->
    <view class="avatar-section" @tap="handleChangeAvatar">
      <image
        class="avatar-image"
        :src="formData.avatar_url || defaultAvatar"
        mode="aspectFill"
      />
      <view class="avatar-hint">
        <text class="hint-text">点击更换头像</text>
      </view>
    </view>

    <!-- 表单 -->
    <view class="form-section">
      <!-- 昵称 -->
      <view class="form-item">
        <text class="form-label">昵称</text>
        <input
          v-model="formData.nickname"
          class="form-input"
          placeholder="请输入昵称"
          maxlength="12"
        />
        <text class="form-count">{{ formData.nickname?.length || 0 }}/12</text>
      </view>

      <!-- 城市 -->
      <view class="form-item" @tap="handleSelectCity">
        <text class="form-label">城市</text>
        <text class="form-value">{{ formData.city || '请选择' }}</text>
        <wd-icon class="form-arrow" name="arrow-right" size="16px" color="var(--text-muted)" />
      </view>

      <!-- 职业 -->
      <view class="form-item">
        <text class="form-label">职业</text>
        <input
          v-model="formData.occupation"
          class="form-input"
          placeholder="请输入职业"
          maxlength="20"
        />
      </view>
    </view>

    <!-- AI画像标签 -->
    <view class="profile-tags-section">
      <view class="section-header">
        <text class="section-title">AI画像标签</text>
        <text class="section-hint">由AI根据你的行为生成</text>
      </view>

      <!-- 加载中 -->
      <view v-if="isLoadingTags" class="loading-area">
        <wd-loading />
      </view>

      <!-- 标签列表 -->
      <view v-else-if="profileTags.length > 0" class="tags-list">
        <view
          v-for="(tag, index) in profileTags"
          :key="index"
          class="tag-item"
          :class="{ 'is-hidden': !tag.is_visible }"
        >
          <view class="tag-info">
            <text class="tag-type">{{ getTagTypeName(tag.tag_type) }}</text>
            <text class="tag-value">{{ tag.tag_value }}</text>
          </view>
          <view class="tag-visibility" @tap="handleToggleTagVisibility(index)">
            <text class="visibility-text">{{ tag.is_visible ? '公开' : '隐藏' }}</text>
            <wd-switch :model-value="tag.is_visible" size="small" />
          </view>
        </view>
      </view>

      <!-- 无标签 -->
      <view v-else class="empty-tags">
        <text class="empty-text">暂无画像数据，继续使用应用后AI会为你生成画像</text>
      </view>
    </view>

    <!-- 兴趣标签 -->
    <view class="interest-tags-section">
      <view class="section-header">
        <text class="section-title">兴趣标签</text>
        <view class="add-tag-btn" @tap="handleAddInterestTag">
          <wd-icon name="add" size="14px" color="var(--brand-primary)" /><text class="add-text">添加</text>
        </view>
      </view>

      <view v-if="interestTags.length > 0" class="interest-tags">
        <view
          v-for="tag in interestTags"
          :key="tag.id"
          class="interest-tag"
        >
          <text class="interest-tag-text">{{ tag.tag_value }}</text>
          <wd-icon class="interest-tag-delete" name="close" size="14px" color="var(--text-muted)" @tap="handleDeleteInterestTag(tag.id)" />
        </view>
      </view>
      <view v-else class="empty-interest">
        <text class="empty-text">点击添加你感兴趣的内容</text>
      </view>
    </view>

    <!-- 城市选择器 -->
    <wd-picker
      v-model="showCityPicker"
      :columns="cityColumns"
      @confirm="handleCityConfirm"
    />

    <!-- 添加兴趣标签弹窗 -->
    <wd-message-box />
  </view>
</template>

<script setup lang="ts">
/**
 * 回声 - 编辑资料页
 * 文件：src/pages/profile/edit.vue
 * 说明：编辑用户资料，包括昵称、头像、画像标签等
 */

import { ref, computed, onMounted } from 'vue'
import {
  getMyProfile,
  updateMyProfile,
  getMyProfileTags,
  getMyTags,
  addMyTag,
  deleteMyTag,
  getProfileTagTypeName,
  type UserDetail,
  type AIProfileTagResponse,
  type ProfileTagItem,
  type UserTag,
} from '@/api/modules/user'
import { track, EventName } from '@/utils/tracking'
import { useUserStore } from '@/stores/user'

// ==================== 组合式函数 ====================

const userStore = useUserStore()

// ==================== 响应式状态 ====================

/** 表单数据 */
const formData = ref({
  nickname: '',
  avatar_url: '',
  city: '',
  occupation: '',
})

/** 原始数据（用于比较是否修改） */
const originalData = ref({
  nickname: '',
  avatar_url: '',
  city: '',
  occupation: '',
})

/** AI画像标签 */
const profileTags = ref<ProfileTagItem[]>([])

/** 兴趣标签 */
const interestTags = ref<UserTag[]>([])

/** 是否正在加载 */
const isLoading = ref(false)

/** 是否正在加载画像标签 */
const isLoadingTags = ref(false)

/** 默认头像 */
const defaultAvatar = '/static/images/default-avatar.png'

/** 城市选择器 */
const showCityPicker = ref(false)

/** 城市列表 */
const cityColumns = [
  { values: ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '苏州', '重庆', '天津', '其他'] }
]

// ==================== 计算属性 ====================

/** 是否可以保存 */
const canSave = computed(() => {
  return (
    formData.value.nickname !== originalData.value.nickname ||
    formData.value.avatar_url !== originalData.value.avatar_url ||
    formData.value.city !== originalData.value.city ||
    formData.value.occupation !== originalData.value.occupation
  )
})

// ==================== 方法 ====================

/**
 * 加载用户数据
 */
async function loadUserData(): Promise<void> {
  isLoading.value = true
  isLoadingTags.value = true

  try {
    const [profileRes, tagsRes, interestRes] = await Promise.all([
      getMyProfile(),
      getMyProfileTags(),
      getMyTags(),
    ])

    // 设置表单数据
    formData.value = {
      nickname: profileRes.nickname || '',
      avatar_url: profileRes.avatar_url || '',
      city: profileRes.city || '',
      occupation: profileRes.occupation || '',
    }

    originalData.value = { ...formData.value }

    // 设置画像标签
    profileTags.value = tagsRes.tags || []

    // 设置兴趣标签
    interestTags.value = interestRes.tags || []
  } catch (error) {
    console.error('加载用户数据失败', error)
  } finally {
    isLoading.value = false
    isLoadingTags.value = false
  }
}

/**
 * 获取标签类型名称
 */
function getTagTypeName(tagType: string): string {
  return getProfileTagTypeName(tagType as any)
}

/**
 * 切换标签可见性
 */
async function handleToggleTagVisibility(index: number): Promise<void> {
  profileTags.value[index].is_visible = !profileTags.value[index].is_visible

  // TODO: 调用后端API保存可见性设置
  track(EventName.SETTING_CHANGE, {
    setting: 'profile_tag_visibility',
    tag_type: profileTags.value[index].tag_type,
    is_visible: profileTags.value[index].is_visible,
  })
}

/**
 * 更换头像
 */
function handleChangeAvatar(): void {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const tempFilePath = res.tempFilePaths[0]

      // 上传头像
      uni.showLoading({ title: '上传中...' })

      // TODO: 调用上传API
      setTimeout(() => {
        uni.hideLoading()
        // 模拟上传成功
        formData.value.avatar_url = tempFilePath
        uni.showToast({ title: '头像已更新', icon: 'success' })
      }, 1000)
    },
  })
}

/**
 * 选择城市
 */
function handleSelectCity(): void {
  showCityPicker.value = true
}

/**
 * 确认城市选择
 */
function handleCityConfirm(value: { value: string }): void {
  formData.value.city = value.value
  showCityPicker.value = false
}

/**
 * 添加兴趣标签
 */
function handleAddInterestTag(): void {
  if (interestTags.value.length >= 10) {
    uni.showToast({ title: '最多添加10个标签', icon: 'none' })
    return
  }

  uni.showModal({
    title: '添加兴趣标签',
    editable: true,
    placeholderText: '请输入兴趣标签',
    success: async (res) => {
      if (res.confirm && res.content) {
        const tagValue = res.content.trim()
        if (!tagValue) return

        try {
          const newTag = await addMyTag({ tag_value: tagValue })
          interestTags.value.push(newTag)

          uni.showToast({ title: '添加成功', icon: 'success' })
        } catch (error: any) {
          uni.showToast({ title: error.message || '添加失败', icon: 'none' })
        }
      }
    },
  })
}

/**
 * 删除兴趣标签
 */
async function handleDeleteInterestTag(tagId: string): Promise<void> {
  uni.showModal({
    title: '确认删除',
    content: '确定要删除这个标签吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteMyTag(tagId)
          interestTags.value = interestTags.value.filter(tag => tag.id !== tagId)

          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (error: any) {
          uni.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      }
    },
  })
}

/**
 * 保存资料
 */
async function handleSave(): Promise<void> {
  if (!canSave.value) return

  // 验证昵称
  if (!formData.value.nickname || formData.value.nickname.length < 2) {
    uni.showToast({ title: '昵称至少2个字符', icon: 'none' })
    return
  }

  isLoading.value = true

  try {
    await updateMyProfile({
      nickname: formData.value.nickname,
      avatar_url: formData.value.avatar_url || undefined,
      city: formData.value.city || undefined,
      occupation: formData.value.occupation || undefined,
    })

    // 更新本地存储
    userStore.updateUserInfo({
      nickname: formData.value.nickname,
      avatarUrl: formData.value.avatar_url,
      city: formData.value.city,
      occupation: formData.value.occupation,
    })

    originalData.value = { ...formData.value }

    uni.showToast({ title: '保存成功', icon: 'success' })

    track(EventName.SETTING_CHANGE, { setting: 'profile' })

    setTimeout(() => {
      uni.navigateBack()
    }, 500)
  } catch (error: any) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  } finally {
    isLoading.value = false
  }
}

/**
 * 返回
 */
function handleBack(): void {
  if (canSave.value) {
    uni.showModal({
      title: '提示',
      content: '有未保存的修改，确定要离开吗？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateBack()
        }
      },
    })
  } else {
    uni.navigateBack()
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadUserData()

  track(EventName.PAGE_VIEW, { page: 'edit_profile' })
})
</script>

<style lang="scss" scoped>
.edit-profile-page {
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
  border-bottom: 1rpx solid var(--border-standard);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
}

.back-icon {
  // 已替换为 wd-icon，此样式保留以防兼容
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-primary);
}

.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xs) var(--space-md);
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);

  &.is-disabled {
    background-color: var(--bg-tertiary);
  }

  &:active:not(.is-disabled) {
    opacity: 0.9;
  }
}

.save-text {
  font-size: var(--font-size-sm);
  color: var(--text-on-brand);

  .is-disabled & {
    color: var(--text-disabled);
  }
}

// ==================== 头像 ====================

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-xl) var(--space-md);
}

.avatar-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: var(--radius-full);
  background-color: var(--bg-tertiary);
  margin-bottom: var(--space-sm);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-hint {
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-light);
  border-radius: var(--radius-full);
}

.hint-text {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
}

// ==================== 表单 ====================

.form-section {
  margin: 0 var(--space-md);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.form-item {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  border-bottom: 1rpx solid var(--border-standard);

  &:last-child {
    border-bottom: none;
  }
}

.form-label {
  width: 120rpx;
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.form-input {
  flex: 1;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  text-align: right;
}

.form-value {
  flex: 1;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  text-align: right;
}

.form-count {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-left: var(--space-xs);
}

.form-arrow {
  margin-left: var(--space-xs);
}

// ==================== AI画像标签 ====================

.profile-tags-section {
  margin: var(--space-lg) var(--space-md);
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

.section-hint {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.loading-area {
  display: flex;
  justify-content: center;
  padding: var(--space-lg);
}

.tags-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.tag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background-color: var(--bg-elevated);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);

  &.is-hidden {
    opacity: 0.6;
  }
}

.tag-info {
  display: flex;
  flex-direction: column;
}

.tag-type {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
  margin-bottom: 4rpx;
}

.tag-value {
  font-size: var(--font-size-md);
  color: var(--text-primary);
}

.tag-visibility {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.visibility-text {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.empty-tags {
  padding: var(--space-lg);
  text-align: center;
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

// ==================== 兴趣标签 ====================

.interest-tags-section {
  margin: 0 var(--space-md) var(--space-lg);
}

.add-tag-btn {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-light);
  border-radius: var(--radius-full);
}

.add-text {
  font-size: var(--font-size-xs);
  color: var(--brand-primary);
}

.interest-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.interest-tag {
  display: flex;
  align-items: center;
  padding: var(--space-xs) var(--space-sm);
  background-color: var(--brand-light);
  border-radius: var(--radius-full);
}

.interest-tag-text {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  margin-right: var(--space-xs);
}

.interest-tag-delete {
  padding: 4rpx;
}

.empty-interest {
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  text-align: center;
}
</style>
