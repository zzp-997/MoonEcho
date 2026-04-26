<template>
  <div class="user-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="搜索">
          <el-input v-model="queryParams.search" placeholder="昵称/手机号" clearable />
        </el-form-item>
        <el-form-item label="年龄段">
          <el-select v-model="queryParams.age_range" clearable placeholder="全部">
            <el-option label="18岁以下" value="under_18" />
            <el-option label="18-25岁" value="18-25" />
            <el-option label="26-35岁" value="26-35" />
            <el-option label="36-45岁" value="36-45" />
            <el-option label="45岁以上" value="above_45" />
          </el-select>
        </el-form-item>
        <el-form-item label="青少年模式">
          <el-select v-model="queryParams.is_minor" clearable placeholder="全部">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="封禁状态">
          <el-select v-model="queryParams.is_banned" clearable placeholder="全部">
            <el-option label="已封禁" :value="true" />
            <el-option label="正常" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="注册时间">
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
        <el-table-column prop="id" label="用户ID" width="200" show-overflow-tooltip />
        <el-table-column prop="nickname" label="昵称" width="120" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column prop="age_range" label="年龄段" width="100">
          <template #default="{ row }">
            {{ row.age_range || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="city" label="城市" width="100">
          <template #default="{ row }">
            {{ row.city || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_minor" label="青少年模式" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_minor" type="warning">是</el-tag>
            <span v-else>否</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_banned" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_banned" type="danger">已封禁</el-tag>
            <el-tag v-else type="success">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_active_at" label="最后活跃" width="160">
          <template #default="{ row }">
            {{ row.last_active_at ? formatDate(row.last_active_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="!row.is_banned && hasPermission('user:ban')"
              type="danger"
              size="small"
              link
              @click="handleBan(row)"
            >
              封禁
            </el-button>
            <el-button
              v-if="row.is_banned && hasPermission('user:ban')"
              type="success"
              size="small"
              link
              @click="handleUnban(row)"
            >
              解封
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

    <!-- 封禁对话框 -->
    <el-dialog v-model="banDialogVisible" title="封禁用户" width="500px">
      <el-form ref="banFormRef" :model="banForm" :rules="banRules" label-width="100px">
        <el-form-item label="封禁原因" prop="reason">
          <el-input
            v-model="banForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入封禁原因"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="封禁天数">
          <el-input-number v-model="banForm.duration_days" :min="1" :max="365" />
          <span class="ml-10 text-muted">不填则永久封禁</span>
        </el-form-item>
        <el-form-item label="通知用户">
          <el-switch v-model="banForm.notify_user" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="banDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmBan" :loading="processing">确认封禁</el-button>
      </template>
    </el-dialog>

    <!-- 解封对话框 -->
    <el-dialog v-model="unbanDialogVisible" title="解封用户" width="500px">
      <el-form ref="unbanFormRef" :model="unbanForm" :rules="unbanRules" label-width="100px">
        <el-form-item label="解封原因" prop="reason">
          <el-input
            v-model="unbanForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入解封原因"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="通知用户">
          <el-switch v-model="unbanForm.notify_user" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="unbanDialogVisible = false">取消</el-button>
        <el-button type="success" @click="confirmUnban" :loading="processing">确认解封</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getUserList, banUser, unbanUser } from '@/api/user'
import { useAdminStore } from '@/stores/admin'
import type { UserListItem, BanUserRequest, UnbanUserRequest } from '@/types/user'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const processing = ref(false)
const tableData = ref<UserListItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  search: '',
  age_range: '',
  is_minor: null as boolean | null,
  is_banned: null as boolean | null,
  timeRange: [] as string[],
})

// 封禁对话框
const banDialogVisible = ref(false)
const banFormRef = ref<FormInstance>()
const currentUser = ref<UserListItem | null>(null)
const banForm = reactive<BanUserRequest>({
  reason: '',
  duration_days: undefined,
  notify_user: true,
})
const banRules: FormRules = {
  reason: [
    { required: true, message: '请输入封禁原因', trigger: 'blur' },
    { min: 5, max: 500, message: '原因长度在5-500字符之间', trigger: 'blur' },
  ],
}

// 解封对话框
const unbanDialogVisible = ref(false)
const unbanFormRef = ref<FormInstance>()
const unbanForm = reactive<UnbanUserRequest>({
  reason: '',
  notify_user: true,
})
const unbanRules: FormRules = {
  reason: [
    { required: true, message: '请输入解封原因', trigger: 'blur' },
    { min: 5, max: 500, message: '原因长度在5-500字符之间', trigger: 'blur' },
  ],
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
    if (queryParams.search) params.search = queryParams.search
    if (queryParams.age_range) params.age_range = queryParams.age_range
    if (queryParams.is_minor !== null) params.is_minor = queryParams.is_minor
    if (queryParams.is_banned !== null) params.is_banned = queryParams.is_banned
    if (queryParams.timeRange.length === 2) {
      params.register_start = queryParams.timeRange[0] + 'T00:00:00Z'
      params.register_end = queryParams.timeRange[1] + 'T23:59:59Z'
    }

    const result = await getUserList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取用户列表失败', error)
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
  queryParams.age_range = ''
  queryParams.is_minor = null
  queryParams.is_banned = null
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

function handleViewDetail(row: UserListItem) {
  router.push(`/users/${row.id}`)
}

function handleBan(row: UserListItem) {
  currentUser.value = row
  banForm.reason = ''
  banForm.duration_days = undefined
  banForm.notify_user = true
  banDialogVisible.value = true
}

async function confirmBan() {
  const valid = await banFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await banUser(currentUser.value!.id, banForm)
    ElMessage.success('用户已封禁')
    banDialogVisible.value = false
    fetchList()
  } catch (error) {
    console.error('封禁用户失败', error)
  } finally {
    processing.value = false
  }
}

function handleUnban(row: UserListItem) {
  currentUser.value = row
  unbanForm.reason = ''
  unbanForm.notify_user = true
  unbanDialogVisible.value = true
}

async function confirmUnban() {
  const valid = await unbanFormRef.value?.validate()
  if (!valid) return

  processing.value = true
  try {
    await unbanUser(currentUser.value!.id, unbanForm)
    ElMessage.success('用户已解封')
    unbanDialogVisible.value = false
    fetchList()
  } catch (error) {
    console.error('解封用户失败', error)
  } finally {
    processing.value = false
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.user-list {
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

  .ml-10 {
    margin-left: 10px;
  }

  .text-muted {
    color: #909399;
    font-size: 12px;
  }
}
</style>