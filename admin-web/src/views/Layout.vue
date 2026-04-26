<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-menu
      :default-active="activeMenu"
      class="sidebar-container"
      :collapse="isCollapse"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
      router
    >
      <div class="sidebar-header">
        <h2 v-if="!isCollapse">回声后台</h2>
        <span v-else>回声</span>
      </div>
      <el-menu-item index="/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <span>工作台</span>
      </el-menu-item>
      <el-menu-item index="/reports" v-if="hasPermission('report:view')">
        <el-icon><Warning /></el-icon>
        <span>举报管理</span>
      </el-menu-item>
      <el-menu-item index="/crisis" v-if="hasPermission('crisis:view')">
        <el-icon><FirstAidKit /></el-icon>
        <span>危机干预</span>
      </el-menu-item>
      <el-menu-item index="/contents" v-if="hasPermission('content:view')">
        <el-icon><Document /></el-icon>
        <span>内容管理</span>
      </el-menu-item>
      <el-menu-item index="/users" v-if="hasPermission('user:view')">
        <el-icon><User /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
    </el-menu>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 头部 -->
      <div class="header-container">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          <span class="breadcrumb">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="nickname">{{ nickname }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <span class="role-tag">{{ roleText }}</span>
                </el-dropdown-item>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="content-container">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const route = useRoute()
const adminStore = useAdminStore()

const isCollapse = ref(false)

const activeMenu = computed(() => {
  const path = route.path
  // 隐藏的路由映射到父级菜单
  if (path.startsWith('/reports')) return '/reports'
  if (path.startsWith('/crisis')) return '/crisis'
  if (path.startsWith('/contents')) return '/contents'
  if (path.startsWith('/users')) return '/users'
  return path
})

const currentTitle = computed(() => {
  return route.meta?.title as string || ''
})

const nickname = computed(() => adminStore.nickname)
const role = computed(() => adminStore.role)

const roleText = computed(() => {
  const roleMap: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    operator: '运营人员',
  }
  return roleMap[role.value] || '未知角色'
})

function hasPermission(permission: string) {
  return adminStore.hasPermission(permission)
}

function handleCommand(command: string) {
  if (command === 'logout') {
    adminStore.logoutAction()
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  display: flex;
  height: 100vh;
}

.sidebar-container {
  width: 220px;
  height: 100%;
  border-right: none;
  transition: width 0.3s;

  &:not(.el-menu--collapse) {
    width: 220px;
  }

  .sidebar-header {
    height: 50px;
    line-height: 50px;
    text-align: center;
    color: #fff;
    font-weight: bold;
    background-color: #263445;

    h2 {
      font-size: 16px;
      margin: 0;
    }

    span {
      font-size: 14px;
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header-container {
  height: 50px;
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;

  .collapse-btn {
    font-size: 20px;
    cursor: pointer;
    color: #606266;

    &:hover {
      color: #409eff;
    }
  }

  .breadcrumb {
    font-size: 16px;
    color: #303133;
  }
}

.header-right {
  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;

    .nickname {
      color: #303133;
    }
  }

  .role-tag {
    color: #909399;
    font-size: 12px;
  }
}

.content-container {
  flex: 1;
  padding: 20px;
  background-color: #f5f7fa;
  overflow-y: auto;
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>