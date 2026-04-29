<template>
  <div class="content-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="内容类型">
          <el-select v-model="queryParams.content_type" clearable placeholder="全部">
            <el-option label="动态" value="post" />
            <el-option label="树洞" value="treehole_post" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" clearable placeholder="全部">
            <el-option label="正常" value="active" />
            <el-option label="已隐藏" value="hidden" />
            <el-option label="已删除" value="deleted" />
          </el-select>
        </el-form-item>
        <el-form-item label="作者ID">
          <el-input v-model="queryParams.author_id" placeholder="请输入作者ID" clearable />
        </el-form-item>
        <el-form-item label="内容搜索">
          <el-input v-model="queryParams.search" placeholder="请输入关键词" clearable />
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
        <el-table-column prop="id" label="内容ID" width="200" show-overflow-tooltip />
        <el-table-column prop="content_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag type="info">{{ contentTypeText(row.content_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content_preview" label="内容预览" min-width="200" show-overflow-tooltip />
        <el-table-column prop="author_nickname" label="作者" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞数" width="80">
          <template #default="{ row }">
            {{ row.like_count || row.resonance_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="comment_count" label="评论数" width="80" />
        <el-table-column prop="report_count" label="举报数" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.report_count > 0" type="danger">{{ row.report_count }}</el-tag>
            <span v-else>0</span>
          </template>
        </el-table-column>
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
              v-if="row.status === 'active' && hasPermission('content:moderate')"
              type="warning"
              size="small"
              link
              @click="handleHide(row)"
            >
              隐藏
            </el-button>
            <el-button
              v-if="row.status === 'hidden' && hasPermission('content:moderate')"
              type="success"
              size="small"
              link
              @click="handleShow(row)"
            >
              显示
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
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { getContentList, updateContentStatus } from '@/api/content'
import { useAdminStore } from '@/stores/admin'
import type { ContentListItem, AdminContentType, ContentStatus } from '@/types/content'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const tableData = ref<ContentListItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  content_type: '' as AdminContentType | '',
  status: '' as ContentStatus | '',
  author_id: '',
  search: '',
  timeRange: [] as string[],
})

// 类型映射
function contentTypeText(type: AdminContentType): string {
  const map: Record<AdminContentType, string> = {
    post: '动态',
    treehole_post: '树洞',
  }
  return map[type] || type
}

function statusText(status: ContentStatus): string {
  const map: Record<ContentStatus, string> = {
    active: '正常',
    hidden: '已隐藏',
    deleted: '已删除',
  }
  return map[status] || status
}

function statusType(status: ContentStatus): 'success' | 'warning' | 'info' {
  const map: Record<ContentStatus, 'success' | 'warning' | 'info'> = {
    active: 'success',
    hidden: 'warning',
    deleted: 'info',
  }
  return map[status] || 'info'
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
    if (queryParams.content_type) params.content_type = queryParams.content_type
    if (queryParams.status) params.status = queryParams.status
    if (queryParams.author_id) params.author_id = queryParams.author_id
    if (queryParams.search) params.search = queryParams.search
    if (queryParams.timeRange.length === 2) {
      params.start_time = queryParams.timeRange[0] + 'T00:00:00Z'
      params.end_time = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getContentList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取内容列表失败', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchList()
}

function handleReset() {
  queryParams.content_type = ''
  queryParams.status = ''
  queryParams.author_id = ''
  queryParams.search = ''
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

function handleViewDetail(row: ContentListItem) {
  router.push(`/contents/${row.content_type}/${row.id}`)
}

async function handleHide(row: ContentListItem) {
  try {
    const { value } = await ElMessageBox.prompt('请输入隐藏原因', '隐藏内容', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPattern: /^.{5,200}$/,
      inputErrorMessage: '原因长度在5-200字符之间',
    })

    await updateContentStatus(row.content_type, row.id, {
      action: 'hide',
      reason: value,
    })
    ElMessage.success('内容已隐藏')
    fetchList()
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('隐藏内容失败', error)
    }
  }
}

async function handleShow(row: ContentListItem) {
  try {
    await ElMessageBox.confirm('确定要显示该内容吗？', '显示内容', { type: 'info' })

    await updateContentStatus(row.content_type, row.id, { action: 'show' })
    ElMessage.success('内容已显示')
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('显示内容失败', error)
    }
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.content-list {
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