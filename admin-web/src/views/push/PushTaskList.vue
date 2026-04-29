<template>
  <div class="push-task-list">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ stats.total_tasks }}</div>
          <div class="stat-label">总任务数</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card pending" shadow="hover">
          <div class="stat-value">{{ stats.pending_tasks }}</div>
          <div class="stat-label">待发送</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card completed" shadow="hover">
          <div class="stat-value">{{ stats.completed_tasks }}</div>
          <div class="stat-label">已完成</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card failed" shadow="hover">
          <div class="stat-value">{{ stats.failed_tasks }}</div>
          <div class="stat-label">失败</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ formatNumber(stats.total_success) }}</div>
          <div class="stat-label">成功送达</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-value">{{ stats.today_tasks }}</div>
          <div class="stat-label">今日任务</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="搜索">
          <el-input v-model="queryParams.search" placeholder="任务标题" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" clearable placeholder="全部">
            <el-option label="待发送" value="pending" />
            <el-option label="发送中" value="sending" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryParams.type" clearable placeholder="全部">
            <el-option label="广播推送" value="broadcast" />
            <el-option label="定向推送" value="targeted" />
            <el-option label="定时推送" value="scheduled" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="queryParams.channel" clearable placeholder="全部">
            <el-option label="APP推送" value="app" />
            <el-option label="短信" value="sms" />
            <el-option label="邮件" value="email" />
            <el-option label="全部渠道" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker
            v-model="queryParams.timeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button v-if="hasPermission('push:create')" type="success" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建推送
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
        <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">{{ getTypeName(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getChannelName(row.channel) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">{{ getStatusName(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_count" label="目标用户" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.target_count) }}
          </template>
        </el-table-column>
        <el-table-column label="发送进度" width="180">
          <template #default="{ row }">
            <div class="progress-info">
              <el-progress
                :percentage="getProgress(row)"
                :status="row.status === 'failed' ? 'exception' : (row.status === 'completed' ? 'success' : '')"
                :show-text="false"
              />
              <span class="progress-text">
                {{ row.sent_count }}/{{ row.target_count }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="success_count" label="成功数" width="100">
          <template #default="{ row }">
            <span class="success-count">{{ formatNumber(row.success_count) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="fail_count" label="失败数" width="100">
          <template #default="{ row }">
            <span class="fail-count">{{ row.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="scheduled_at" label="计划发送" width="160">
          <template #default="{ row }">
            {{ row.scheduled_at ? formatDate(row.scheduled_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending' && hasPermission('push:cancel')"
              type="danger"
              size="small"
              link
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status === 'failed' && hasPermission('push:create')"
              type="warning"
              size="small"
              link
              @click="handleRetry(row)"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getPushTaskList, getPushTaskStats, cancelPushTask, retryPushTask } from '@/api/push'
import { useAdminStore } from '@/stores/admin'
import type { PushTaskItem, PushTaskStats, CancelPushTaskRequest } from '@/types/push'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const tableData = ref<PushTaskItem[]>([])
const total = ref(0)

const stats = ref<PushTaskStats>({
  total_tasks: 0,
  pending_tasks: 0,
  completed_tasks: 0,
  failed_tasks: 0,
  total_sent: 0,
  total_success: 0,
  today_tasks: 0,
  today_sent: 0,
  today_success: 0,
})

const queryParams = reactive({
  page: 1,
  page_size: 20,
  search: '',
  status: '',
  type: '',
  channel: '',
  timeRange: [] as string[],
})

// 取消对话框
const cancelDialogVisible = ref(false)
const cancelFormRef = ref<FormInstance>()
const currentTask = ref<PushTaskItem | null>(null)
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

function getProgress(row: PushTaskItem): number {
  if (row.target_count === 0) return 0
  return Math.round((row.sent_count / row.target_count) * 100)
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
    app: 'APP',
    sms: '短信',
    email: '邮件',
    all: '全部',
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

async function fetchStats() {
  try {
    const result = await getPushTaskStats()
    stats.value = result
  } catch (error) {
    console.error('获取统计数据失败', error)
    // Mock 数据
    stats.value = {
      total_tasks: 50,
      pending_tasks: 5,
      completed_tasks: 40,
      failed_tasks: 3,
      total_sent: 50000,
      total_success: 48000,
      today_tasks: 2,
      today_sent: 2000,
      today_success: 1900,
    }
  }
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = {
      page: queryParams.page,
      page_size: queryParams.page_size,
    }
    if (queryParams.search) params.search = queryParams.search
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.type) params.type = queryParams.type
    if (queryParams.channel) params.channel = queryParams.channel
    if (queryParams.timeRange.length === 2) {
      params.start_date = queryParams.timeRange[0] + 'T00:00:00Z'
      params.end_date = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getPushTaskList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取推送任务列表失败', error)
    // Mock 数据
    tableData.value = [
      {
        id: '1',
        title: '新年活动通知',
        content: '新年活动即将开始，快来参与吧！',
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
      },
      {
        id: '2',
        title: 'VIP用户专属优惠',
        content: '尊敬的VIP用户，您的专属优惠已送达',
        type: 'targeted',
        channel: 'all',
        status: 'completed',
        target_count: 500,
        sent_count: 500,
        success_count: 480,
        fail_count: 20,
        scheduled_at: null,
        sent_at: '2024-01-05T14:00:00Z',
        created_by: 'admin_2',
        created_by_name: '运营小王',
        created_at: '2024-01-05T12:00:00Z',
        updated_at: '2024-01-05T14:30:00Z',
      },
      {
        id: '3',
        title: '系统维护通知',
        content: '系统将于今晚22:00进行维护，请提前做好准备',
        type: 'scheduled',
        channel: 'app',
        status: 'pending',
        target_count: 50000,
        sent_count: 0,
        success_count: 0,
        fail_count: 0,
        scheduled_at: '2024-01-15T22:00:00Z',
        sent_at: null,
        created_by: 'admin_1',
        created_by_name: '管理员一',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: '4',
        title: '签到提醒',
        content: '别忘了今天签到哦！',
        type: 'broadcast',
        channel: 'app',
        status: 'sending',
        target_count: 20000,
        sent_count: 15000,
        success_count: 14500,
        fail_count: 500,
        scheduled_at: null,
        sent_at: null,
        created_by: 'admin_2',
        created_by_name: '运营小王',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-15T08:30:00Z',
      },
      {
        id: '5',
        title: '活动推送失败测试',
        content: '这是一条测试推送',
        type: 'broadcast',
        channel: 'sms',
        status: 'failed',
        target_count: 1000,
        sent_count: 200,
        success_count: 150,
        fail_count: 850,
        scheduled_at: null,
        sent_at: null,
        created_by: 'admin_3',
        created_by_name: '测试用户',
        created_at: '2024-01-10T15:00:00Z',
        updated_at: '2024-01-10T15:30:00Z',
      },
    ]
    total.value = 5
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchList()
}

function handleReset() {
  queryParams.search = ''
  queryParams.status = ''
  queryParams.type = ''
  queryParams.channel = ''
  queryParams.timeRange = []
  queryParams.page = 1
  fetchList()
}

function handleSizeChange(size: number) {
  queryParams.page_size = size
  fetchList()
}

function handleCurrentChange(page: number) {
  queryParams.page = page
  fetchList()
}

function handleCreate() {
  router.push('/push/create')
}

function handleViewDetail(row: PushTaskItem) {
  router.push(`/push/${row.id}`)
}

function handleCancel(row: PushTaskItem) {
  currentTask.value = row
  cancelForm.reason = ''
  cancelDialogVisible.value = true
}

async function confirmCancel() {
  const valid = await cancelFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await cancelPushTask(currentTask.value!.id, cancelForm)
    ElMessage.success('已取消推送任务')
    cancelDialogVisible.value = false
    fetchList()
    fetchStats()
  } catch (error) {
    console.error('取消推送任务失败', error)
  } finally {
    processing.value = false
  }
}

async function handleRetry(row: PushTaskItem) {
  try {
    await ElMessageBox.confirm('确定要重新发送该推送任务吗？', '重试确认', {
      type: 'warning',
    })
    await retryPushTask(row.id)
    ElMessage.success('已开始重试')
    fetchList()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试推送任务失败', error)
    }
  }
}

onMounted(() => {
  fetchStats()
  fetchList()
})
</script>

<style scoped lang="scss">
.push-task-list {
  .stat-cards {
    margin-bottom: 20px;

    .stat-card {
      text-align: center;
      padding: 20px;

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

      &.pending {
        .stat-value {
          color: #e6a23c;
        }
      }

      &.completed {
        .stat-value {
          color: #67c23a;
        }
      }

      &.failed {
        .stat-value {
          color: #f56c6c;
        }
      }
    }
  }

  .search-card {
    margin-bottom: 20px;
  }

  .table-card {
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }

    .progress-info {
      display: flex;
      align-items: center;
      gap: 10px;

      .el-progress {
        flex: 1;
      }

      .progress-text {
        font-size: 12px;
        color: #909399;
      }
    }

    .success-count {
      color: #67c23a;
    }

    .fail-count {
      color: #f56c6c;
    }
  }
}
</style>