<template>
  <div class="admin-detail">
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
          <span>基本信息</span>
          <el-button v-if="hasPermission('admin:update')" type="primary" @click="handleEdit">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ adminDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ adminDetail.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ adminDetail.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ adminDetail.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="getRoleType(adminDetail.role)">{{ getRoleName(adminDetail.role) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag v-if="adminDetail.is_active" type="success">启用</el-tag>
          <el-tag v-else type="danger">禁用</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后登录时间">
          {{ adminDetail.last_login_at ? formatDate(adminDetail.last_login_at) : '从未登录' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后登录IP">
          {{ adminDetail.last_login_ip || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(adminDetail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(adminDetail.updated_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ adminDetail.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 权限信息 -->
    <el-card class="permission-card">
      <template #header>
        <span>权限配置</span>
      </template>
      <div class="permission-list">
        <div v-for="(actions, resource) in adminDetail.permissions" :key="resource" class="permission-item">
          <span class="resource-name">{{ getResourceName(resource as string) }}</span>
          <div class="action-list">
            <el-tag v-for="action in actions" :key="action" class="action-tag">
              {{ getActionName(action) }}
            </el-tag>
          </div>
        </div>
        <el-empty v-if="!adminDetail.permissions || Object.keys(adminDetail.permissions).length === 0" description="暂无权限配置" />
      </div>
    </el-card>

    <!-- 操作日志 -->
    <el-card class="log-card">
      <template #header>
        <span>最近操作日志</span>
      </template>
      <el-table :data="logs" stripe>
        <el-table-column prop="action" label="操作" width="120" />
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="target_type" label="目标类型" width="120">
          <template #default="{ row }">
            {{ row.target_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="200">
          <template #default="{ row }">
            {{ row.target_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="130" />
        <el-table-column prop="created_at" label="操作时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="详情">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="showLogDetail(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="logDetailVisible" title="日志详情" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作">{{ currentLog?.action }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ currentLog?.module }}</el-descriptions-item>
        <el-descriptions-item label="目标类型">{{ currentLog?.target_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="目标ID">{{ currentLog?.target_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog?.ip }}</el-descriptions-item>
        <el-descriptions-item label="User Agent">{{ currentLog?.user_agent }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ currentLog?.created_at ? formatDate(currentLog.created_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="详细信息">
          <pre class="detail-json">{{ JSON.stringify(currentLog?.detail, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑管理员" width="600px">
      <el-form ref="formRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editForm.nickname" placeholder="请输入昵称" maxlength="50" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="管理员" value="admin" />
            <el-option label="运营人员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="editForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'
import { getAdminDetail, updateAdmin, getAdminLogs } from '@/api/admin'
import { useAdminStore } from '@/stores/admin'
import type { AdminDetail, AdminLogItem, UpdateAdminRequest } from '@/types/admin'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const loading = ref(false)
const saving = ref(false)
const adminId = route.params.id as string

const adminDetail = ref<AdminDetail>({
  id: '',
  username: '',
  nickname: null,
  email: null,
  role: 'operator',
  is_active: true,
  last_login_at: null,
  last_login_ip: null,
  created_at: '',
  updated_at: '',
  permissions: {},
  remark: null,
})

const logs = ref<AdminLogItem[]>([])
const logDetailVisible = ref(false)
const currentLog = ref<AdminLogItem | null>(null)

// 编辑对话框
const editDialogVisible = ref(false)
const formRef = ref<FormInstance>()
const editForm = reactive<UpdateAdminRequest>({
  nickname: '',
  email: '',
  role: 'operator',
  is_active: true,
  remark: '',
})

const editRules: FormRules = {
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
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

function getResourceName(resource: string): string {
  const nameMap: Record<string, string> = {
    user: '用户管理',
    content: '内容管理',
    report: '举报管理',
    crisis: '危机干预',
    admin: '管理员管理',
    push: '推送管理',
    dashboard: '数据看板',
  }
  return nameMap[resource] || resource
}

function getActionName(action: string): string {
  const nameMap: Record<string, string> = {
    view: '查看',
    create: '创建',
    update: '更新',
    delete: '删除',
    ban: '封禁',
    process: '处理',
    resolve: '解决',
    cancel: '取消',
    export: '导出',
    '*': '全部',
  }
  return nameMap[action] || action
}

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function handleBack() {
  router.push('/admins')
}

function showLogDetail(log: AdminLogItem) {
  currentLog.value = log
  logDetailVisible.value = true
}

function handleEdit() {
  editForm.nickname = adminDetail.value.nickname || ''
  editForm.email = adminDetail.value.email || ''
  editForm.role = adminDetail.value.role
  editForm.is_active = adminDetail.value.is_active
  editForm.remark = adminDetail.value.remark || ''
  editDialogVisible.value = true
}

async function handleSaveEdit() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  saving.value = true
  try {
    await updateAdmin(adminId, editForm)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    console.error('保存失败', error)
  } finally {
    saving.value = false
  }
}

async function fetchDetail() {
  loading.value = true
  try {
    const result = await getAdminDetail(adminId)
    adminDetail.value = result
  } catch (error) {
    console.error('获取管理员详情失败', error)
    // Mock 数据
    adminDetail.value = {
      id: adminId,
      username: 'admin01',
      nickname: '管理员一',
      email: 'admin1@example.com',
      role: 'admin',
      is_active: true,
      last_login_at: '2024-01-15T10:30:00Z',
      last_login_ip: '192.168.1.100',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T10:30:00Z',
      permissions: {
        user: ['view', 'ban'],
        content: ['view', 'delete'],
        report: ['view', 'process'],
      },
      remark: '这是一个测试管理员账号',
    }
  } finally {
    loading.value = false
  }
}

async function fetchLogs() {
  try {
    const result = await getAdminLogs({ admin_id: adminId, page: 1, page_size: 10 })
    logs.value = result.data
  } catch (error) {
    console.error('获取操作日志失败', error)
    // Mock 数据
    logs.value = [
      {
        id: '1',
        admin_id: adminId,
        admin_username: 'admin01',
        admin_nickname: '管理员一',
        action: '封禁用户',
        module: '用户管理',
        target_type: 'user',
        target_id: 'user_123',
        detail: { reason: '违规行为' },
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0',
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: '2',
        admin_id: adminId,
        admin_username: 'admin01',
        admin_nickname: '管理员一',
        action: '删除内容',
        module: '内容管理',
        target_type: 'diary',
        target_id: 'diary_456',
        detail: { reason: '内容违规' },
        ip: '192.168.1.100',
        user_agent: 'Mozilla/5.0',
        created_at: '2024-01-14T15:20:00Z',
      },
    ]
  }
}

onMounted(() => {
  fetchDetail()
  fetchLogs()
})
</script>

<style scoped lang="scss">
.admin-detail {
  .back-card {
    margin-bottom: 20px;
  }

  .info-card,
  .permission-card,
  .log-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .permission-list {
    .permission-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .resource-name {
        width: 120px;
        font-weight: 500;
        color: #303133;
      }

      .action-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;

        .action-tag {
          margin: 0;
        }
      }
    }
  }

  .detail-json {
    background: #f5f7fa;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    max-height: 300px;
    overflow: auto;
  }
}
</style>
