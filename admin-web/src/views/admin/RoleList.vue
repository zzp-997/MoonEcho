<template>
  <div class="role-list">
    <!-- 角色列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
        </div>
      </template>
      <el-table :data="roleList" v-loading="loading" stripe>
        <el-table-column prop="key" label="角色标识" width="150">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.key)">{{ row.key }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="user_count" label="用户数" width="100">
          <template #default="{ row }">
            {{ row.user_count }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleViewPermission(row)">
              查看权限
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 权限详情对话框 -->
    <el-dialog v-model="permissionDialogVisible" :title="`${currentRole?.name} - 权限配置`" width="700px">
      <div class="permission-content">
        <div v-for="(actions, resource) in currentRole?.permissions" :key="resource" class="permission-item">
          <span class="resource-name">{{ getResourceName(resource as string) }}</span>
          <div class="action-list">
            <el-tag v-for="action in actions" :key="action" class="action-tag">
              {{ getActionName(action) }}
            </el-tag>
          </div>
        </div>
        <el-empty v-if="!currentRole?.permissions || Object.keys(currentRole.permissions).length === 0" description="暂无权限配置" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getRoleList } from '@/api/admin'
import type { RoleInfo } from '@/types/admin'

const loading = ref(false)
const roleList = ref<RoleInfo[]>([])
const permissionDialogVisible = ref(false)
const currentRole = ref<RoleInfo | null>(null)

function getRoleType(role: string): 'danger' | 'warning' | 'info' {
  const typeMap: Record<string, 'danger' | 'warning' | 'info'> = {
    super_admin: 'danger',
    admin: 'warning',
    operator: 'info',
  }
  return typeMap[role] || 'info'
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

function handleViewPermission(role: RoleInfo) {
  currentRole.value = role
  permissionDialogVisible.value = true
}

async function fetchRoleList() {
  loading.value = true
  try {
    const result = await getRoleList()
    roleList.value = result
  } catch (error) {
    console.error('获取角色列表失败', error)
    // Mock 数据
    roleList.value = [
      {
        key: 'super_admin',
        name: '超级管理员',
        description: '拥有系统所有权限，可管理其他管理员',
        user_count: 1,
        permissions: {
          user: ['*'],
          content: ['*'],
          report: ['*'],
          crisis: ['*'],
          admin: ['*'],
          push: ['*'],
          dashboard: ['*'],
        },
      },
      {
        key: 'admin',
        name: '管理员',
        description: '拥有常规管理权限，无法管理其他管理员',
        user_count: 3,
        permissions: {
          user: ['view', 'ban'],
          content: ['view', 'delete'],
          report: ['view', 'process'],
          crisis: ['view', 'resolve'],
          push: ['view', 'create'],
          dashboard: ['view'],
        },
      },
      {
        key: 'operator',
        name: '运营人员',
        description: '基础运营权限，负责日常内容审核',
        user_count: 5,
        permissions: {
          user: ['view'],
          content: ['view', 'delete'],
          report: ['view', 'process'],
          dashboard: ['view'],
        },
      },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchRoleList()
})
</script>

<style scoped lang="scss">
.role-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .permission-content {
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
}
</style>
