<template>
  <div class="crisis-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="危机级别">
          <el-select v-model="queryParams.level" clearable placeholder="全部">
            <el-option label="高危" value="high" />
            <el-option label="中危" value="medium" />
            <el-option label="低危" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="queryParams.status" clearable placeholder="全部">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="intervening" />
            <el-option label="已解决" value="resolved" />
            <el-option label="误报" value="false_positive" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model="queryParams.user_id" placeholder="请输入用户ID" clearable />
        </el-form-item>
        <el-form-item label="时间范围">
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
        <el-table-column prop="message_id" label="消息ID" width="200" show-overflow-tooltip />
        <el-table-column prop="level" label="危机级别" width="100">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)" effect="dark">
              {{ levelText(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_keywords" label="触发关键词" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="kw in row.trigger_keywords.slice(0, 3)" :key="kw" size="small" class="keyword-tag">
              {{ kw }}
            </el-tag>
            <span v-if="row.trigger_keywords.length > 3">...</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_nickname" label="用户" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="intervening_admin" label="处理人" width="120">
          <template #default="{ row }">
            {{ row.intervening_admin || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending' && hasPermission('crisis:resolve')"
              type="warning"
              size="small"
              link
              @click="handleIntervene(row)"
            >
              介入
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { getCrisisList, markIntervention } from '@/api/crisis'
import { useAdminStore } from '@/stores/admin'
import type { CrisisListItem, CrisisLevel, CrisisStatus } from '@/types/crisis'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const tableData = ref<CrisisListItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  level: '' as CrisisLevel | '',
  status: '' as CrisisStatus | '',
  user_id: '',
  timeRange: [] as string[],
})

// 类型映射
function levelText(level: CrisisLevel): string {
  const map: Record<CrisisLevel, string> = {
    high: '高危',
    medium: '中危',
    low: '低危',
  }
  return map[level] || level
}

function levelType(level: CrisisLevel): string {
  const map: Record<CrisisLevel, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[level] || ''
}

function statusText(status: CrisisStatus): string {
  const map: Record<CrisisStatus, string> = {
    pending: '待处理',
    intervening: '处理中',
    resolved: '已解决',
    false_positive: '误报',
  }
  return map[status] || status
}

function statusType(status: CrisisStatus): string {
  const map: Record<CrisisStatus, string> = {
    pending: 'danger',
    intervening: 'warning',
    resolved: 'success',
    false_positive: 'info',
  }
  return map[status] || ''
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = {
      page: queryParams.page,
      page_size: queryParams.page_size,
    }
    if (queryParams.level) params.level = queryParams.level
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.user_id) params.user_id = queryParams.user_id
    if (queryParams.timeRange.length === 2) {
      params.start_time = queryParams.timeRange[0] + 'T00:00:00Z'
      params.end_time = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getCrisisList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取危机列表失败', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchList()
}

function handleReset() {
  queryParams.level = ''
  queryParams.status = ''
  queryParams.user_id = ''
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

function handleViewDetail(row: CrisisListItem) {
  router.push(`/crisis/${row.message_id}`)
}

async function handleIntervene(row: CrisisListItem) {
  try {
    await markIntervention(row.message_id)
    ElMessage.success('已标记介入')
    fetchList()
  } catch (error) {
    console.error('标记介入失败', error)
    ElMessage.error('标记介入失败，请稍后重试')
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.crisis-list {
  .search-card {
    margin-bottom: 20px;
  }

  .table-card {
    .keyword-tag {
      margin-right: 4px;
      margin-bottom: 4px;
    }

    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }
}
</style>