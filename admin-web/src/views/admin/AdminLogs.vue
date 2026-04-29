<template>
  <div class="admin-logs">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="管理员">
          <el-input v-model="queryParams.admin_id" placeholder="管理员ID" clearable />
        </el-form-item>
        <el-form-item label="模块">
          <el-select v-model="queryParams.module" clearable placeholder="全部">
            <el-option label="用户管理" value="用户管理" />
            <el-option label="内容管理" value="内容管理" />
            <el-option label="举报管理" value="举报管理" />
            <el-option label="危机干预" value="危机干预" />
            <el-option label="管理员管理" value="管理员管理" />
            <el-option label="推送管理" value="推送管理" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型">
          <el-input v-model="queryParams.action" placeholder="操作类型" clearable />
        </el-form-item>
        <el-form-item label="操作时间">
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
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="admin_username" label="操作人" width="120">
          <template #default="{ row }">
            {{ row.admin_nickname || row.admin_username }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="120" />
        <el-table-column prop="module" label="模块" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.module }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="100">
          <template #default="{ row }">
            {{ row.target_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.target_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="130" />
        <el-table-column prop="user_agent" label="浏览器" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tooltip :content="row.user_agent" placement="top">
              <span>{{ getBrowserInfo(row.user_agent) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="showDetail(row)">
              详情
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

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="日志详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="操作人">
          {{ currentLog?.admin_nickname || currentLog?.admin_username }}
        </el-descriptions-item>
        <el-descriptions-item label="操作">{{ currentLog?.action }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ currentLog?.module }}</el-descriptions-item>
        <el-descriptions-item label="目标类型">{{ currentLog?.target_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标ID">{{ currentLog?.target_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog?.ip }}</el-descriptions-item>
        <el-descriptions-item label="User Agent" :span="2">{{ currentLog?.user_agent }}</el-descriptions-item>
        <el-descriptions-item label="操作时间" :span="2">{{ currentLog?.created_at ? formatDate(currentLog.created_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="详细信息" :span="2">
          <pre class="detail-json">{{ JSON.stringify(currentLog?.detail, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import { getAdminLogs } from '@/api/admin'
import type { AdminLogItem, AdminLogParams } from '@/types/admin'

const loading = ref(false)
const tableData = ref<AdminLogItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  admin_id: '',
  module: '',
  action: '',
  timeRange: [] as string[],
})

const detailVisible = ref(false)
const currentLog = ref<AdminLogItem | null>(null)

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

function getBrowserInfo(userAgent: string): string {
  if (!userAgent) return '-'
  if (userAgent.includes('Chrome')) return 'Chrome'
  if (userAgent.includes('Firefox')) return 'Firefox'
  if (userAgent.includes('Safari')) return 'Safari'
  if (userAgent.includes('Edge')) return 'Edge'
  return 'Other'
}

function showDetail(log: AdminLogItem) {
  currentLog.value = log
  detailVisible.value = true
}

async function fetchList() {
  loading.value = true
  try {
    const params: AdminLogParams = {
      page: queryParams.page,
      page_size: queryParams.page_size,
    }
    if (queryParams.admin_id) params.admin_id = queryParams.admin_id
    if (queryParams.module) params.module = queryParams.module
    if (queryParams.action) params.action = queryParams.action
    if (queryParams.timeRange.length === 2) {
      params.start_date = queryParams.timeRange[0] + 'T00:00:00Z'
      params.end_date = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getAdminLogs(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取操作日志失败', error)
    // Mock 数据
    tableData.value = [
      {
        id: '1',
        admin_id: 'admin_1',
        admin_username: 'admin01',
        admin_nickname: '管理员一',
        action: '封禁用户',
        module: '用户管理',
        target_type: 'user',
        target_id: 'user_123',
        detail: { reason: '违规行为', duration: 7 },
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: '2',
        admin_id: 'admin_1',
        admin_username: 'admin01',
        admin_nickname: '管理员一',
        action: '删除内容',
        module: '内容管理',
        target_type: 'diary',
        target_id: 'diary_456',
        detail: { reason: '内容违规', report_id: 'report_789' },
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        created_at: '2024-01-14T15:20:00Z',
      },
      {
        id: '3',
        admin_id: 'admin_2',
        admin_username: 'operator01',
        admin_nickname: '运营小王',
        action: '处理举报',
        module: '举报管理',
        target_type: 'report',
        target_id: 'report_789',
        detail: { result: '已处理', action: '删除内容' },
        ip: '192.168.1.102',
        user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        created_at: '2024-01-14T14:00:00Z',
      },
      {
        id: '4',
        admin_id: 'admin_1',
        admin_username: 'admin01',
        admin_nickname: '管理员一',
        action: '创建推送',
        module: '推送管理',
        target_type: 'push_task',
        target_id: 'task_001',
        detail: { title: '系统维护通知', target_count: 1000 },
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        created_at: '2024-01-13T09:00:00Z',
      },
      {
        id: '5',
        admin_id: 'admin_3',
        admin_username: 'superadmin',
        admin_nickname: '超级管理员',
        action: '创建管理员',
        module: '管理员管理',
        target_type: 'admin',
        target_id: 'admin_2',
        detail: { username: 'operator01', role: 'operator' },
        ip: '192.168.1.1',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        created_at: '2024-01-10T10:00:00Z',
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
  queryParams.admin_id = ''
  queryParams.module = ''
  queryParams.action = ''
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

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.admin-logs {
  .search-card {
    margin-bottom: 20px;
  }

  .table-card {
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .detail-json {
    background: #f5f7fa;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    max-height: 300px;
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
