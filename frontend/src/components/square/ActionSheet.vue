<template>
  <wd-popup
    v-model="visible"
    position="bottom"
    :closeOnClickModal="true"
  >
    <view class="action-sheet">
      <!-- 标题区域 -->
      <view class="sheet-header">
        <text class="sheet-title">选择发布类型</text>
        <view class="close-btn" @tap="handleClose">
          <text class="close-icon">x</text>
        </view>
      </view>

      <!-- 选项列表 -->
      <view class="option-list">
        <!-- 发布吐槽（树洞） -->
        <view
          class="option-item"
          :class="{ 'is-highlighted': highlightedType === 'treehole' }"
          @tap="handleSelect('treehole')"
        >
          <view class="option-icon treehole">
            <text class="icon-text">树洞</text>
          </view>
          <view class="option-content">
            <text class="option-title">发布吐槽</text>
            <text class="option-desc">把没处说的话丢出来</text>
          </view>
          <view v-if="highlightedType === 'treehole'" class="highlight-badge">
            <text class="badge-text">推荐</text>
          </view>
        </view>

        <!-- 发布动态（广场） -->
        <view
          class="option-item"
          :class="{ 'is-highlighted': highlightedType === 'square' }"
          @tap="handleSelect('square')"
        >
          <view class="option-icon square">
            <text class="icon-text">广场</text>
          </view>
          <view class="option-content">
            <text class="option-title">发布动态</text>
            <text class="option-desc">分享此刻的心情</text>
          </view>
          <view v-if="highlightedType === 'square'" class="highlight-badge">
            <text class="badge-text">推荐</text>
          </view>
        </view>

        <!-- 记录情绪（日记） -->
        <view
          class="option-item"
          :class="{ 'is-highlighted': highlightedType === 'diary' }"
          @tap="handleSelect('diary')"
        >
          <view class="option-icon diary">
            <text class="icon-text">日记</text>
          </view>
          <view class="option-content">
            <text class="option-title">记录情绪</text>
            <text class="option-desc">对自己说的话</text>
          </view>
          <view v-if="highlightedType === 'diary'" class="highlight-badge">
            <text class="badge-text">推荐</text>
          </view>
        </view>
      </view>

      <!-- 取消按钮 -->
      <view class="cancel-btn" @tap="handleClose">
        <text class="cancel-text">取消</text>
      </view>

      <!-- 底部安全区 -->
      <view class="safe-bottom" :style="{ height: safeAreaBottom }" />
    </view>
  </wd-popup>
</template>

<script setup lang="ts">
/**
 * 回声 - 底部分流 ActionSheet 组件
 * 文件：src/components/square/ActionSheet.vue
 * 说明：底部弹出的发布类型选择器，支持智能高亮默认选项
 * 设计要点：根据用户最近活跃模块智能高亮对应选项
 */

import { ref, computed, watch, onMounted } from 'vue'

// ==================== Types ====================

/** 发布类型 */
export type PublishType = 'treehole' | 'square' | 'diary'

// ==================== Props ====================

const props = defineProps<{
  /** 是否显示 */
  show: boolean
  /** 当前页面（用于智能高亮） */
  currentPage?: string
}>()

// ==================== Emits ====================

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'select', type: PublishType): void
  (e: 'close'): void
}>()

// ==================== 响应式状态 ====================

/** 内部可见状态 */
const visible = ref(false)

/** 安全区域底部高度 */
const safeAreaBottom = ref('0px')

/** 高亮的发布类型 */
const highlightedType = ref<PublishType>('diary')

// ==================== 计算属性 ====================

// ==================== 监听 ====================

// 监听外部 show 属性
watch(
  () => props.show,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      // 每次打开时更新高亮类型
      updateHighlightedType()
    }
  }
)

// 监听内部 visible 状态，同步到外部
watch(visible, (newVal) => {
  emit('update:show', newVal)
  if (!newVal) {
    emit('close')
  }
})

// ==================== 方法 ====================

/**
 * 获取安全区域高度
 */
function getSafeArea(): void {
  const systemInfo = uni.getSystemInfoSync()
  const bottom = systemInfo.safeAreaInsets?.bottom ?? 0
  safeAreaBottom.value = `${bottom}px`
}

/**
 * 更新高亮类型（基于用户最近活跃模块）
 */
function updateHighlightedType(): void {
  // 如果传入了当前页面，优先使用
  if (props.currentPage) {
    switch (props.currentPage) {
      case 'treehole':
        highlightedType.value = 'treehole'
        return
      case 'square':
        highlightedType.value = 'square'
        return
      case 'diary':
        highlightedType.value = 'diary'
        return
    }
  }

  // 否则从本地存储获取用户最近活跃模块
  try {
    const recentModule = uni.getStorageSync('recent_active_module')
    if (recentModule) {
      highlightedType.value = recentModule as PublishType
      return
    }
  } catch (e) {
    console.error('获取最近活跃模块失败', e)
  }

  // 默认高亮日记（门槛最低）
  highlightedType.value = 'diary'
}

/**
 * 处理选项选择
 */
function handleSelect(type: PublishType): void {
  emit('select', type)

  // 记录用户选择，用于下次智能高亮
  try {
    uni.setStorageSync('recent_active_module', type)
  } catch (e) {
    console.error('保存最近活跃模块失败', e)
  }

  handleClose()
}

/**
 * 处理关闭
 */
function handleClose(): void {
  visible.value = false
}

// ==================== 生命周期 ====================

onMounted(() => {
  getSafeArea()
})
</script>

<style lang="scss" scoped>
.action-sheet {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-primary);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

// ==================== 标题区域 ====================

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 100rpx;
  border-bottom: 1px solid var(--border-primary);
}

.sheet-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  position: absolute;
  top: 50%;
  right: var(--space-md);
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
}

.close-icon {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
}

// ==================== 选项列表 ====================

.option-list {
  display: flex;
  flex-direction: column;
  padding: var(--space-md);
}

.option-item {
  display: flex;
  align-items: center;
  padding: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  position: relative;

  &:active {
    opacity: 0.9;
  }

  &.is-highlighted {
    background-color: var(--brand-light);
    border: 1px solid var(--brand-light);
  }
}

.option-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 88rpx;
  border-radius: var(--radius-md);
  margin-right: var(--space-md);

  &.treehole {
    background-color: var(--mood-low-bg);
  }

  &.square {
    background-color: var(--brand-light);
  }

  &.diary {
    background-color: var(--mood-calm-bg);
  }
}

.icon-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.option-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--text-primary);
}

.option-desc {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-xs);
}

.highlight-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rpx 16rpx;
  background-color: var(--brand-primary);
  border-radius: var(--radius-full);
}

.badge-text {
  font-size: var(--font-size-xs);
  color: var(--text-on-brand);
}

// ==================== 取消按钮 ====================

.cancel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100rpx;
  margin-top: var(--space-sm);
  margin-left: var(--space-md);
  margin-right: var(--space-md);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);

  &:active {
    opacity: 0.9;
  }
}

.cancel-text {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
}

// ==================== 底部安全区 ====================

.safe-bottom {
  background-color: transparent;
}
</style>