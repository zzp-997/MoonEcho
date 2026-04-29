<template>
  <div class="push-task-detail">
    <!-- 返回按钮 -->
    <el-card class="back-card">
      <el-button type="primary" link @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </el-card>

    <!-- 基本信息 -->
    <el-card class="info-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>推送任务详情</span>
          <div class="header-actions">
            <el-button
              v-if="taskDetail.status === 'pending' && hasPermission('push:cancel')"
              type="danger"
              @click="handleCancel"
            >
              取消任务
            </el-button>
            <el-button
              v-if="taskDetail.status === 'failed' && hasPermission('push:create')"
              type="warning"
              @click="handleRetry"
            >
              重试发送
            </el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务ID">{{ taskDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(taskDetail.status)">{{ getStatusName(taskDetail.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="任务标题" :span="2">{{ taskDetail.title }}</el-descriptions-item>
        <el-descriptions-item label="推送内容" :span="2">{{ taskDetail.content }}</el-descriptions-item>
        <el-descriptions-item label="推送类型">
          <el-tag :type="getTypeTagType(taskDetail.type)">{{ getTypeName(taskDetail.type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="推送渠道">
          <el-tag size="small">{{ getChannelName(taskDetail.channel) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="计划发送时间">
          {{ taskDetail.scheduled_at ? formatDate(taskDetail.scheduled_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="实际发送时间">
          {{ taskDetail.sent_at ? formatDate(taskDetail.sent_at) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建人">{{ taskDetail.created_by_name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(taskDetail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ taskDetail.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 发送统计 -->
    <el-card class="stats-card">
      <template #header>
        <span>发送统计</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ formatNumber(taskDetail.target_count) }}</div>
            <div class="stat-label">目标用户</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ formatNumber(taskDetail.sent_count) }}</div>
            <div class="stat-label">已发送</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item success">
            <div class="stat-value">{{ formatNumber(taskDetail.success_count) }}</div>
            <div class="stat-label">成功送达</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item fail">
            <div class="stat-value">{{ formatNumber(taskDetail.fail_count) }}</div>
            <div class="stat-label">发送失败</div>
          </div>
        </el-col>
      </el-row>
      <div class="progress-section">
        <span>发送进度</span>
        <el-progress
          :percentage="getProgress()"
          :status="taskDetail.status === 'failed' ? 'exception' : (taskDetail.status === 'completed' ? 'success' : '')"
        />
      </div>
      <div class="success-rate">
        成功率: {{ getSuccessRate() }}%
      </div>
    </el-card>

    <!-- 目标条件 -->
    <el-card v-if="taskDetail.target_criteria" class="criteria-card">
      <template #header>
        <span>目标条件</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="年龄段">
          {{ taskDetail.target_criteria.age_range || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="城市">
          {{ taskDetail.target_criteria.city || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="青少年模式">
          {{ taskDetail.target_criteria.is_minor === true ? '是' : (taskDetail.target_criteria.is_minor === false ? '否' : '-') }}
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ taskDetail.target_criteria.register_start ? formatDate(taskDetail.target_criteria.register_start) : '-' }}
          至
          {{ taskDetail.target_criteria.register_end ? formatDate(taskDetail.target_criteria.register_end) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="活跃时间">
          {{ taskDetail.target_criteria.last_active_start ? formatDate(taskDetail.target_criteria.last_active_start) : '-' }}
          至
          {{ taskDetail.target_criteria.last_active_end ? formatDate(taskDetail.target_criteria.last_active_end) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="有日记">
          {{ taskDetail.target_criteria.has_diary === true ? '是' : (taskDetail.target_criteria.has_diary === false ? '否' : '-') }}
        </el-descriptions-item>
        <el-descriptions-item label="指定用户ID" :span="3">
          <div v-if="taskDetail.target_criteria.user_ids && taskDetail.target_criteria.user_ids.length > 0">
            <el-tag v-for="id in taskDetail.target_criteria.user_ids.slice(0, 10)" :key="id" class="user-id-tag">
              {{ id }}
            </el-tag>
            <span v-if="taskDetail.target_criteria.user_ids.length > 10" class="more-text">
              等共 {{ taskDetail.target_criteria.user_ids.length }} 个用户
            </span>
          </div>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 取消对话框 -->
    <el-dialog v-model="cancelDialogVisible" title="取消推送任务" width="400px">
      <el-form ref="cancelFormRef" :model="cancelForm" :rules="cancelRules" label-width="80px">
        <el-form-item label="取消原因" prop="reason">
          <el-input
            v-model="cancelForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入取消原因"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmCancel" :loading="processing">确认取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getPushTaskDetail, cancelPushTask, retryPushTask } from '@/api/push'
import { useAdminStore } from '@/stores/admin'
import type { PushTaskDetail, CancelPushTaskRequest } from '@/types/push'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const taskId = route.params.id as string

const taskDetail = ref<PushTaskDetail>({
  id: '',
  title: '',
  content: '',
  type: 'broadcast',
  channel: 'app',
  status: 'pending',
  target_count: 0,
  sent_count: 0,
  success_count: 0,
  fail_count: 0,
  scheduled_at: null,
  sent_at: null,
  created_by: '',
  created_by_name: '',
  created_at: '',
  updated_at: '',
  target_criteria: null,
  extra_data: null,
  remark: null,
})

// 取消对话框
const cancelDialogVisible = ref(false)
const cancelFormRef = ref<FormInstance>()
const cancelForm = reactive<CancelPushTaskRequest>({
  reason: '',
})

const cancelRules: FormRules = {
  reason: [
    { required: true, message: '请输入取消原因', trigger: 'blur' },
    { min: 5, max: 200, message: '原因长度在5-200字符之间', trigger: 'blur' },
  ],
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}

function getProgress(): number {
  if (taskDetail.value.target_count === 0) return 0
  return Math.round((taskDetail.value.sent_count / taskDetail.value.target_count) * 100)
}

function getSuccessRate(): string {
  if (taskDetail.value.sent_count === 0) return '0.0'
  return ((taskDetail.value.success_count / taskDetail.value.sent_count) * 100).toFixed(1)
}

function getTypeName(type: string): string {
  const nameMap: Record<string, string> = {
    broadcast: '广播',
    targeted: '定向',
    scheduled: '定时',
  }
  return nameMap[type] || type
}

function getTypeTagType(type: string): 'primary' | 'success' | 'warning' {
  const typeMap: Record<string, 'primary' | 'success' | 'warning'> = {
    broadcast: 'primary',
    targeted: 'success',
    scheduled: 'warning',
  }
  return typeMap[type] || 'primary'
}

function getChannelName(channel: string): string {
  const nameMap: Record<string, string> = {
    app: 'APP推送',
    sms: '短信',
    email: '邮件',
    all: '全部渠道',
  }
  return nameMap[channel] || channel
}

function getStatusName(status: string): string {
  const nameMap: Record<string, string> = {
    pending: '待发送',
    sending: '发送中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return nameMap[status] || status
}

function getStatusTagType(status: string): 'info' | 'warning' | 'success' | 'danger' {
  const typeMap: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    pending: 'info',
    sending: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function handleBack() {
  router.push('/push')
}

function handleCancel() {
  cancelForm.reason = ''
  cancelDialogVisible.value = true
}

async function confirmCancel() {
  const valid = await cancelFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await cancelPushTask(taskId, cancelForm)
    ElMessage.success('已取消推送任务')
    cancelDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    console.error('取消推送任务失败', error)
  } finally {
    processing.value = false
  }
}

async function handleRetry() {
  try {
    await ElMessageBox.confirm('确定要重新发送该推送任务吗？', '重试确认', {
      type: 'warning',
    })
    await retryPushTask(taskId)
    ElMessage.success('已开始重试')
    fetchDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试推送任务失败', error)
    }
  }
}

async function fetchDetail() {
  loading.value = true
  try {
    const result = await getPushTaskDetail(taskId)
    taskDetail.value = result
  } catch (error) {
    console.error('获取推送任务详情失败', error)
    // Mock 数据
    taskDetail.value = {
      id: taskId,
      title: '新年活动通知',
      content: '新年活动即将开始，快来参与吧！活动时间：2024年1月1日 - 2024年1月7日。参与活动即可获得丰厚奖励！',
      type: 'broadcast',
      channel: 'app',
      status: 'completed',
      target_count: 10000,
      sent_count: 10000,
      success_count: 9500,
      fail_count: 500,
      scheduled_at: null,
      sent_at: '2024-01-01T10:00:00Z',
      created_by: 'admin_1',
      created_by_name: '管理员一',
      created_at: '2024-01-01T09:00:00Z',
      updated_at: '2024-01-01T10:30:00Z',
      target_criteria: null,
      extra_data: null,
      remark: '新年活动首次推送',
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<style scoped lang="scss">
.push-task-detail {
  .back-card {
    margin-bottom: 20px;
  }

  .info-card,
  .stats-card,
  .criteria-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 10px;
      }
    }
  }

  .stats-card {
    .stat-item {
      text-align: center;
      padding: 20px;
      background: #f5f7fa;
      border-radius: 8px;

      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 8px;
      }

      &.success {
        background: #f0f9eb;

        .stat-value {
          color: #67c23a;
        }
      }

      &.fail {
        background: #fef0f0;

        .stat-value {
          color: #f56c6c;
        }
      }
    }

    .progress-section {
      margin-top: 20px;
      display: flex;
      align-items: center;
      gap: 15px;

      span {
        width: 80px;
        color: #606266;
      }

      .el-progress {
        flex: 1;
      }
    }

    .success-rate {
      text-align: center;
      margin-top: 15px;
      font-size: 14px;
      color: #67c23a;
    }
  }

  .user-id-tag {
    margin: 2px;
  }

  .more-text {
    color: #909399;
    font-size: 12px;
    margin-left: 5px;
  }
}
</style>