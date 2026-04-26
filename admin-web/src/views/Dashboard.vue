<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #409eff;">
              <el-icon size="24"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.userCount }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #67c23a;">
              <el-icon size="24"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.diaryCount }}</div>
              <div class="stat-label">今日日记</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #e6a23c;">
              <el-icon size="24"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingReports }}</div>
              <div class="stat-label">待处理举报</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #f56c6c;">
              <el-icon size="24"><FirstAidKit /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.crisisCount }}</div>
              <div class="stat-label">危机事件</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快速入口</span>
          </template>
          <div class="quick-links">
            <el-button
              v-if="hasPermission('report:view')"
              type="primary"
              @click="$router.push('/reports')"
            >
              <el-icon><Warning /></el-icon>
              举报管理
            </el-button>
            <el-button
              v-if="hasPermission('crisis:view')"
              type="danger"
              @click="$router.push('/crisis')"
            >
              <el-icon><FirstAidKit /></el-icon>
              危机干预
            </el-button>
            <el-button
              v-if="hasPermission('content:view')"
              type="success"
              @click="$router.push('/contents')"
            >
              <el-icon><Document /></el-icon>
              内容管理
            </el-button>
            <el-button
              v-if="hasPermission('user:view')"
              type="info"
              @click="$router.push('/users')"
            >
              <el-icon><User /></el-icon>
              用户管理
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>待办事项</span>
          </template>
          <div class="todo-list">
            <div class="todo-item" v-if="hasPermission('report:process')">
              <el-icon><Warning /></el-icon>
              <span>{{ stats.pendingReports }} 条举报待处理</span>
              <el-button type="primary" size="small" link @click="$router.push('/reports')">去处理</el-button>
            </div>
            <div class="todo-item" v-if="hasPermission('crisis:resolve')">
              <el-icon><FirstAidKit /></el-icon>
              <span>{{ stats.pendingCrisis }} 条危机事件待处理</span>
              <el-button type="danger" size="small" link @click="$router.push('/crisis')">去处理</el-button>
            </div>
            <el-empty v-if="!hasPermission('report:process') && !hasPermission('crisis:resolve')" description="暂无待办事项" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'

const adminStore = useAdminStore()

const stats = ref({
  userCount: '-',
  diaryCount: '-',
  pendingReports: '-',
  crisisCount: '-',
  pendingCrisis: '-',
})

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

onMounted(() => {
  // 暂时使用模拟数据
  stats.value = {
    userCount: '128',
    diaryCount: '45',
    pendingReports: '12',
    crisisCount: '3',
    pendingCrisis: '3',
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }

    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }

  .quick-links {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .todo-list {
    .todo-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .el-icon {
        color: #e6a23c;
      }

      span {
        flex: 1;
      }
    }
  }
}
</style>
