<template>
  <div class="report-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" clearable placeholder="全部">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item label="举报类型">
          <el-select v-model="queryParams.report_type" clearable placeholder="全部">
            <el-option label="色情低俗" value="porn" />
            <el-option label="广告骚扰" value="ad" />
            <el-option label="恶意骚扰" value="harassment" />
            <el-option label="人身攻击" value="abuse" />
            <el-option label="诈骗欺诈" value="scam" />
            <el-option label="自残自杀" value="self_harm" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容类型">
          <el-select v-model="queryParams.content_type" clearable placeholder="全部">
            <el-option label="动态" value="post" />
            <el-option label="树洞" value="treehole_post" />
            <el-option label="评论" value="comment" />
            <el-option label="用户" value="user" />
          </el-select>
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
        <el-table-column prop="id" label="举报ID" width="200" show-overflow-tooltip />
        <el-table-column prop="report_type" label="举报类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ reportTypeText(row.report_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content_type" label="内容类型" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ contentTypeText(row.content_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="举报原因" min-width="150" show-overflow-tooltip />
        <el-table-column prop="reporter_nickname" label="举报人" width="120" show-overflow-tooltip />
        <el-table-column prop="reported_user_nickname" label="被举报人" width="120" show-overflow-tooltip />
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
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewDetail(row)">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { getReportList } from '@/api/report'
import type { ReportListItem, ReportType, ContentType, ReportStatus } from '@/types/report'

const router = useRouter()

const loading = ref(false)
const tableData = ref<ReportListItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  status: '' as ReportStatus | '',
  report_type: '' as ReportType | '',
  content_type: '' as ContentType | '',
  timeRange: [] as string[],
})

// 类型映射
function reportTypeText(type: ReportType): string {
  const map: Record<ReportType, string> = {
    porn: '色情低俗',
    ad: '广告骚扰',
    harassment: '恶意骚扰',
    abuse: '人身攻击',
    scam: '诈骗欺诈',
    self_harm: '自残自杀',
    other: '其他',
  }
  return map[type] || type
}

function contentTypeText(type: ContentType): string {
  const map: Record<ContentType, string> = {
    post: '动态',
    treehole_post: '树洞',
    comment: '评论',
    user: '用户',
  }
  return map[type] || type
}

function statusText(status: ReportStatus): string {
  const map: Record<ReportStatus, string> = {
    pending: '待处理',
    processing: '处理中',
    approved: '已通过',
    rejected: '已驳回',
  }
  return map[status] || status
}

function statusType(status: ReportStatus): 'danger' | 'warning' | 'success' | 'info' {
  const map: Record<ReportStatus, 'danger' | 'warning' | 'success' | 'info'> = {
    pending: 'danger',
    processing: 'warning',
    approved: 'success',
    rejected: 'info',
  }
  return map[status] || 'info'
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = {
      page: queryParams.page,
      page_size: queryParams.page_size,
    }
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.report_type) params.report_type = queryParams.report_type
    if (queryParams.content_type) params.content_type = queryParams.content_type
    if (queryParams.timeRange.length === 2) {
      params.start_time = queryParams.timeRange[0] + 'T00:00:00Z'
      params.end_time = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getReportList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取举报列表失败', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchList()
}

function handleReset() {
  queryParams.status = ''
  queryParams.report_type = ''
  queryParams.content_type = ''
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

function handleViewDetail(row: ReportListItem) {
  router.push(`/reports/${row.id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.report-list {
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
}
</style>