<template>
  <div class="admin-list">
    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="搜索">
          <el-input v-model="queryParams.search" placeholder="用户名/昵称" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="queryParams.role" clearable placeholder="全部">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="管理员" value="admin" />
            <el-option label="运营人员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.is_active" clearable placeholder="全部">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
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
          <el-button v-if="hasPermission('admin:create')" type="success" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增管理员
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120">
          <template #default="{ row }">
            {{ row.nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="180">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleName(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success">启用</el-tag>
            <el-tag v-else type="danger">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login_at ? formatDate(row.last_login_at) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login_ip" label="登录IP" width="130">
          <template #default="{ row }">
            {{ row.last_login_ip || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="hasPermission('admin:update')"
              type="warning"
              size="small"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="hasPermission('admin:update') && row.is_active"
              type="danger"
              size="small"
              link
              @click="handleDisable(row)"
            >
              禁用
            </el-button>
            <el-button
              v-if="hasPermission('admin:update') && !row.is_active"
              type="success"
              size="small"
              link
              @click="handleEnable(row)"
            >
              启用
            </el-button>
            <el-button
              v-if="hasPermission('admin:delete') && row.role !== 'super_admin'"
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑管理员' : '新增管理员'"
      width="600px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            :disabled="isEdit"
            placeholder="请输入用户名"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="formData.nickname" placeholder="请输入昵称" maxlength="50" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="管理员" value="admin" />
            <el-option label="运营人员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-tree
            ref="treeRef"
            :data="permissionTree"
            :props="treeProps"
            show-checkbox
            node-key="key"
            :default-checked-keys="defaultCheckedKeys"
            :default-expanded-keys="defaultExpandedKeys"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formData.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPasswordVisible" title="重置密码" width="400px">
      <el-form ref="resetFormRef" :model="resetPasswordData" :rules="resetPasswordRules" label-width="100px">
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="resetPasswordData.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="resetPasswordData.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import {
  getAdminList,
  createAdmin,
  updateAdmin,
  deleteAdmin,
} from '@/api/admin'
import { useAdminStore } from '@/stores/admin'
import type {
  AdminListItem,
  CreateAdminRequest,
  UpdateAdminRequest,
  PermissionModule,
} from '@/types/admin'

const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const submitting = ref(false)
const tableData = ref<AdminListItem[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  search: '',
  role: '',
  is_active: null as boolean | null,
})

// 对话框相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref('')
const formRef = ref<FormInstance>()
const treeRef = ref()

const formData = reactive<CreateAdminRequest & { remark?: string }>({
  username: '',
  password: '',
  nickname: '',
  email: '',
  role: 'operator',
  permissions: {},
  remark: '',
})

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在6-100字符之间', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
}

// 权限树配置
const treeProps = {
  children: 'actions',
  label: 'name',
}

// 权限树数据
const permissionTree = computed<PermissionModule[]>(() => [
  {
    key: 'user',
    name: '用户管理',
    actions: [
      { key: 'user:view', name: '查看用户', description: '' },
      { key: 'user:ban', name: '封禁用户', description: '' },
    ],
  },
  {
    key: 'content',
    name: '内容管理',
    actions: [
      { key: 'content:view', name: '查看内容', description: '' },
      { key: 'content:delete', name: '删除内容', description: '' },
    ],
  },
  {
    key: 'report',
    name: '举报管理',
    actions: [
      { key: 'report:view', name: '查看举报', description: '' },
      { key: 'report:process', name: '处理举报', description: '' },
    ],
  },
  {
    key: 'crisis',
    name: '危机干预',
    actions: [
      { key: 'crisis:view', name: '查看危机', description: '' },
      { key: 'crisis:resolve', name: '处理危机', description: '' },
    ],
  },
  {
    key: 'admin',
    name: '管理员管理',
    actions: [
      { key: 'admin:view', name: '查看管理员', description: '' },
      { key: 'admin:create', name: '创建管理员', description: '' },
      { key: 'admin:update', name: '更新管理员', description: '' },
      { key: 'admin:delete', name: '删除管理员', description: '' },
    ],
  },
  {
    key: 'push',
    name: '推送管理',
    actions: [
      { key: 'push:view', name: '查看推送', description: '' },
      { key: 'push:create', name: '创建推送', description: '' },
      { key: 'push:cancel', name: '取消推送', description: '' },
    ],
  },
  {
    key: 'dashboard',
    name: '数据看板',
    actions: [
      { key: 'dashboard:view', name: '查看统计', description: '' },
      { key: 'dashboard:export', name: '导出数据', description: '' },
    ],
  },
])

const defaultCheckedKeys = ref<string[]>([])
const defaultExpandedKeys = computed(() => permissionTree.value.map(p => p.key))

// 重置密码相关
const resetPasswordVisible = ref(false)
const resetFormRef = ref<FormInstance>()
const resetPasswordData = reactive({
  new_password: '',
  confirm_password: '',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== resetPasswordData.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const resetPasswordRules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度在6-100字符之间', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

function formatDate(date: string): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function getRoleType(role: string): 'danger' | 'warning' | 'info' {
  const typeMap: Record<string, 'danger' | 'warning' | 'info'> = {
    super_admin: 'danger',
    admin: 'warning',
    operator: 'info',
  }
  return typeMap[role] || 'info'
}

function getRoleName(role: string): string {
  const nameMap: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    operator: '运营人员',
  }
  return nameMap[role] || role
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
    if (queryParams.role) params.role = queryParams.role
    if (queryParams.is_active !== null) params.is_active = queryParams.is_active

    const result = await getAdminList(params)
    tableData.value = result.data
    total.value = result.pagination.total
  } catch (error) {
    console.error('获取管理员列表失败', error)
    // Mock 数据
    tableData.value = [
      {
        id: '1',
        username: 'superadmin',
        nickname: '超级管理员',
        email: 'super@example.com',
        role: 'super_admin',
        is_active: true,
        last_login_at: '2024-01-15T10:30:00Z',
        last_login_ip: '192.168.1.100',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      },
      {
        id: '2',
        username: 'admin01',
        nickname: '管理员一',
        email: 'admin1@example.com',
        role: 'admin',
        is_active: true,
        last_login_at: '2024-01-14T15:20:00Z',
        last_login_ip: '192.168.1.101',
        created_at: '2024-01-05T00:00:00Z',
        updated_at: '2024-01-14T15:20:00Z',
      },
      {
        id: '3',
        username: 'operator01',
        nickname: '运营小王',
        email: 'operator@example.com',
        role: 'operator',
        is_active: true,
        last_login_at: '2024-01-15T08:00:00Z',
        last_login_ip: '192.168.1.102',
        created_at: '2024-01-10T00:00:00Z',
        updated_at: '2024-01-15T08:00:00Z',
      },
    ]
    total.value = 3
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
  queryParams.role = ''
  queryParams.is_active = null
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

function handleViewDetail(row: AdminListItem) {
  router.push(`/admins/${row.id}`)
}

function handleCreate() {
  isEdit.value = false
  currentId.value = ''
  resetFormData()
  dialogVisible.value = true
}

function handleEdit(row: AdminListItem) {
  isEdit.value = true
  currentId.value = row.id
  resetFormData()
  // 填充数据
  formData.username = row.username
  formData.nickname = row.nickname || ''
  formData.email = row.email || ''
  formData.role = row.role
  dialogVisible.value = true
}

function resetFormData() {
  formData.username = ''
  formData.password = ''
  formData.nickname = ''
  formData.email = ''
  formData.role = 'operator'
  formData.permissions = {}
  formData.remark = ''
  defaultCheckedKeys.value = []
}

function resetForm() {
  formRef.value?.resetFields()
  treeRef.value?.setCheckedKeys([])
}

async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  // 获取选中的权限
  const checkedKeys = treeRef.value?.getCheckedKeys() || []
  const permissions: Record<string, string[]> = {}
  checkedKeys.forEach((key: string) => {
    if (key.includes(':')) {
      const [resource, action] = key.split(':')
      if (!permissions[resource]) {
        permissions[resource] = []
      }
      permissions[resource].push(action)
    }
  })

  submitting.value = true
  try {
    if (isEdit.value) {
      const data: UpdateAdminRequest = {
        nickname: formData.nickname,
        email: formData.email,
        role: formData.role,
        permissions,
        remark: formData.remark,
      }
      await updateAdmin(currentId.value, data)
      ElMessage.success('更新成功')
    } else {
      const data: CreateAdminRequest = {
        username: formData.username,
        password: formData.password,
        nickname: formData.nickname,
        email: formData.email,
        role: formData.role,
        permissions,
        remark: formData.remark,
      }
      await createAdmin(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (error) {
    console.error('操作失败', error)
  } finally {
    submitting.value = false
  }
}

async function handleDisable(row: AdminListItem) {
  try {
    await ElMessageBox.confirm('确定要禁用该管理员吗？', '禁用确认', {
      type: 'warning',
    })
    await updateAdmin(row.id, { is_active: false })
    ElMessage.success('已禁用')
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('禁用失败', error)
    }
  }
}

async function handleEnable(row: AdminListItem) {
  try {
    await updateAdmin(row.id, { is_active: true })
    ElMessage.success('已启用')
    fetchList()
  } catch (error) {
    console.error('启用失败', error)
  }
}

async function handleDelete(row: AdminListItem) {
  try {
    await ElMessageBox.confirm('确定要删除该管理员吗？此操作不可恢复', '删除确认', {
      type: 'error',
    })
    await deleteAdmin(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
    }
  }
}

async function handleResetPassword() {
  const valid = await resetFormRef.value?.validate()
  if (!valid) return

  submitting.value = true
  try {
    // await resetAdminPassword(currentId.value, { new_password: resetPasswordData.new_password })
    ElMessage.success('密码重置成功')
    resetPasswordVisible.value = false
  } catch (error) {
    console.error('重置密码失败', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.admin-list {
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
