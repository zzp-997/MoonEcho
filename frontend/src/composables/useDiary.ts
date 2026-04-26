/**
 * 回声 - 日记编辑组合式函数
 * 文件：src/composables/useDiary.ts
 * 说明：日记编辑相关的状态管理和业务逻辑
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import {
  createDiary,
  getPrivacyConsent,
  setPrivacyConsent,
  EMOTION_TONE_META,
  EMOTION_TONE_LIST,
  EMOTION_LABELS_POOL,
  type EmotionTone,
  type SyncMode,
} from '@/api/diary'
import { track, EventName } from '@/utils/tracking'
import { getStorage, setStorage } from '@/utils/storage'

// ==================== 存储键 ====================

/** 隐私同意状态本地缓存键 */
const PRIVACY_CONSENT_KEY = 'huisheng_diary_privacy_consent'

// ==================== 组合式函数 ====================

export function useDiary() {
  // ==================== 响应式状态 ====================

  /** 当前选中的情绪色调 */
  const selectedTone = ref<EmotionTone | null>(null)

  /** 当前选中的情绪标签列表 */
  const selectedLabels = ref<string[]>([])

  /** 日记内容文字 */
  const contentText = ref('')

  /** 是否正在提交 */
  const isSubmitting = ref(false)

  /** 是否显示隐私弹窗 */
  const showPrivacyDialog = ref(false)

  /** 是否已同意隐私声明 */
  const hasConsented = ref(false)

  /** 同步模式 */
  const syncMode = ref<SyncMode>('local_only')

  /** 是否正在检查隐私状态 */
  const isCheckingPrivacy = ref(false)

  /** 提交成功后的日记ID */
  const lastCreatedId = ref<string | null>(null)

  // ==================== 计算属性 ====================

  /** 当前色调的元数据 */
  const currentToneMeta = computed(() => {
    if (!selectedTone.value) return null
    return EMOTION_TONE_META[selectedTone.value]
  })

  /** 当前色调对应的标签池 */
  const currentLabelsPool = computed(() => {
    if (!selectedTone.value) return []
    return EMOTION_LABELS_POOL[selectedTone.value]
  })

  /** 当前色调的颜色 */
  const currentToneColor = computed(() => {
    return currentToneMeta.value?.color || '#808080'
  })

  /** 当前色调的提示语 */
  const currentHint = computed(() => {
    return currentToneMeta.value?.hint || '说说今天的心情吧'
  })

  /** 内容字数 */
  const contentLength = computed(() => contentText.value.length)

  /** 是否可以提交 */
  const canSubmit = computed(() => {
    return selectedTone.value !== null && !isSubmitting.value
  })

  /** 是否为空内容 */
  const isEmptyContent = computed(() => contentLength.value === 0)

  /** 是否超过500字 */
  const isOverLong = computed(() => contentLength.value > 500)

  /** 是否达到最大字数限制 */
  const isMaxLength = computed(() => contentLength.value >= 2000)

  // ==================== 方法 ====================

  /**
   * 选择情绪色调
   */
  function selectTone(tone: EmotionTone): void {
    if (selectedTone.value === tone) {
      // 取消选择
      selectedTone.value = null
      selectedLabels.value = []
    } else {
      // 选择新色调，清空之前的标签
      selectedTone.value = tone
      selectedLabels.value = []
    }

    // 追踪色调选择
    track(EventName.DIARY_CREATE, {
      action: 'select_tone',
      tone,
    })
  }

  /**
   * 切换情绪标签选择
   */
  function toggleLabel(label: string): void {
    const index = selectedLabels.value.indexOf(label)
    if (index > -1) {
      // 取消选择
      selectedLabels.value.splice(index, 1)
    } else {
      // 选择标签（最多3个）
      if (selectedLabels.value.length < 3) {
        selectedLabels.value.push(label)
      } else {
        // 已选满3个，提示用户
        uni.showToast({
          title: '最多选择3个标签',
          icon: 'none',
        })
      }
    }
  }

  /**
   * 检查隐私同意状态
   */
  async function checkPrivacyConsent(): Promise<boolean> {
    // 先检查本地缓存
    const localConsent = getStorage<boolean>(PRIVACY_CONSENT_KEY, false)
    if (localConsent) {
      hasConsented.value = true
      return true
    }

    // 请求服务端状态
    isCheckingPrivacy.value = true
    try {
      const response = await getPrivacyConsent()
      hasConsented.value = response.has_consented
      syncMode.value = response.sync_mode

      if (response.has_consented) {
        // 缓存到本地
        setStorage(PRIVACY_CONSENT_KEY, true)
        return true
      }

      // 未同意，显示弹窗
      showPrivacyDialog.value = true
      return false
    } catch (error) {
      console.error('检查隐私同意状态失败', error)
      // 请求失败时显示弹窗
      showPrivacyDialog.value = true
      return false
    } finally {
      isCheckingPrivacy.value = false
    }
  }

  /**
   * 处理隐私同意
   */
  async function handlePrivacyConsent(mode: SyncMode): Promise<boolean> {
    try {
      const response = await setPrivacyConsent({ sync_mode: mode })
      hasConsented.value = true
      syncMode.value = mode
      showPrivacyDialog.value = false

      // 缓存到本地
      setStorage(PRIVACY_CONSENT_KEY, true)

      // 追踪隐私同意
      track(EventName.DIARY_CREATE, {
        action: 'privacy_consent',
        sync_mode: mode,
      })

      return true
    } catch (error) {
      console.error('设置隐私同意失败', error)
      uni.showToast({
        title: '设置失败，请重试',
        icon: 'none',
      })
      return false
    }
  }

  /**
   * 提交日记
   */
  async function submitDiary(): Promise<boolean> {
    // 检查是否可以选择色调
    if (!selectedTone.value) {
      uni.showToast({
        title: '请先选择情绪色调',
        icon: 'none',
      })
      return false
    }

    // 检查隐私同意
    if (!hasConsented.value) {
      showPrivacyDialog.value = true
      return false
    }

    isSubmitting.value = true

    try {
      const response = await createDiary({
        emotion_tone: selectedTone.value,
        emotion_labels: selectedLabels.value.length > 0 ? selectedLabels.value : undefined,
        content_text: contentText.value || undefined,
        record_date: new Date().toISOString().split('T')[0],
      })

      lastCreatedId.value = response.id

      // 追踪日记创建
      track(EventName.DIARY_CREATE, {
        tone: selectedTone.value,
        labels_count: selectedLabels.value.length,
        content_length: contentLength.value,
        is_zero_record: isEmptyContent.value,
      })

      // 显示成功提示
      if (isEmptyContent.value) {
        uni.showToast({
          title: '写点什么让记录更有意义',
          icon: 'none',
        })
      } else {
        uni.showToast({
          title: '记录成功',
          icon: 'success',
        })
      }

      return true
    } catch (error) {
      console.error('提交日记失败', error)
      uni.showToast({
        title: '提交失败，请重试',
        icon: 'none',
      })
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  /**
   * 重置表单
   */
  function resetForm(): void {
    selectedTone.value = null
    selectedLabels.value = []
    contentText.value = ''
    lastCreatedId.value = null
  }

  /**
   * 初始化日记编辑页
   */
  async function initDiaryEditor(): Promise<void> {
    await checkPrivacyConsent()
  }

  // ==================== 监听 ====================

  // 监听内容字数变化
  watch(contentLength, (length) => {
    if (length > 500 && length <= 510) {
      // 刚超过500字时提示
      uni.showToast({
        title: '要不要发给AI朋友聊聊',
        icon: 'none',
        duration: 3000,
      })
    }
  })

  // ==================== 返回 ====================

  return {
    // 状态
    selectedTone,
    selectedLabels,
    contentText,
    isSubmitting,
    showPrivacyDialog,
    hasConsented,
    syncMode,
    isCheckingPrivacy,
    lastCreatedId,

    // 计算属性
    currentToneMeta,
    currentLabelsPool,
    currentToneColor,
    currentHint,
    contentLength,
    canSubmit,
    isEmptyContent,
    isOverLong,
    isMaxLength,

    // 方法
    selectTone,
    toggleLabel,
    checkPrivacyConsent,
    handlePrivacyConsent,
    submitDiary,
    resetForm,
    initDiaryEditor,
  }
}

// ==================== 语音输入相关 ====================

/**
 * 语音输入组合式函数
 */
export function useVoiceInput() {
  /** 是否正在录音 */
  const isRecording = ref(false)

  /** 录音时长（秒） */
  const recordingDuration = ref(0)

  /** 录音计时器 */
  let recordingTimer: ReturnType<typeof setInterval> | null = null

  /**
   * 开始录音
   */
  function startRecording(): void {
    // 检查录音权限
    // #ifdef APP-PLUS || MP-WEIXIN
    uni.authorize({
      scope: 'scope.record',
      success: () => {
        doStartRecording()
      },
      fail: () => {
        uni.showModal({
          title: '需要录音权限',
          content: '请在设置中开启录音权限',
          confirmText: '去设置',
          success: (res) => {
            if (res.confirm) {
              uni.openSetting()
            }
          },
        })
      },
    })
    // #endif

    // #ifdef H5
    // H5 端使用 navigator.mediaDevices 检查权限
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(() => {
          doStartRecording()
        })
        .catch(() => {
          uni.showToast({
            title: '请允许使用麦克风',
            icon: 'none',
          })
        })
    } else {
      uni.showToast({
        title: '当前浏览器不支持录音',
        icon: 'none',
      })
    }
    // #endif
  }

  /**
   * 执行开始录音
   */
  function doStartRecording(): void {
    isRecording.value = true
    recordingDuration.value = 0

    // 开始计时
    recordingTimer = setInterval(() => {
      recordingDuration.value++
      // 最长60秒
      if (recordingDuration.value >= 60) {
        stopRecording()
      }
    }, 1000)

    // 追踪语音输入开始
    track(EventName.DIARY_CREATE, {
      action: 'voice_start',
    })
  }

  /**
   * 停止录音
   */
  function stopRecording(): void {
    if (!isRecording.value) return

    isRecording.value = false

    // 停止计时
    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }

    // 追踪语音输入结束
    track(EventName.DIARY_CREATE, {
      action: 'voice_stop',
      duration: recordingDuration.value,
    })

    // TODO: 实际的语音识别逻辑
    // 这里需要调用语音识别API将语音转换为文字
    // uni-app 支持的语音识别插件或服务

    uni.showToast({
      title: '语音识别功能开发中',
      icon: 'none',
    })
  }

  /**
   * 切换录音状态
   */
  function toggleRecording(): void {
    if (isRecording.value) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  /**
   * 清理资源（组件卸载时调用）
   */
  function cleanup(): void {
    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }
    isRecording.value = false
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    cleanup()
  })

  return {
    isRecording,
    recordingDuration,
    startRecording,
    stopRecording,
    toggleRecording,
    cleanup,
  }
}

// ==================== 导出常量 ====================

export { EMOTION_TONE_META, EMOTION_TONE_LIST, EMOTION_LABELS_POOL }
export type { EmotionTone, SyncMode }
