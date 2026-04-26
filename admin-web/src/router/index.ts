import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' },
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/reports/ReportList.vue'),
        meta: { title: '举报管理', icon: 'Warning', permission: 'report:view' },
      },
      {
        path: 'reports/:id',
        name: 'ReportDetail',
        component: () => import('@/views/reports/ReportDetail.vue'),
        meta: { title: '举报详情', hidden: true, permission: 'report:view' },
      },
      {
        path: 'crisis',
        name: 'Crisis',
        component: () => import('@/views/crisis/CrisisList.vue'),
        meta: { title: '危机干预', icon: 'FirstAidKit', permission: 'crisis:view' },
      },
      {
        path: 'crisis/:id',
        name: 'CrisisDetail',
        component: () => import('@/views/crisis/CrisisDetail.vue'),
        meta: { title: '危机详情', hidden: true, permission: 'crisis:view' },
      },
      {
        path: 'contents',
        name: 'Contents',
        component: () => import('@/views/contents/ContentList.vue'),
        meta: { title: '内容管理', icon: 'Document', permission: 'content:view' },
      },
      {
        path: 'contents/:type/:id',
        name: 'ContentDetail',
        component: () => import('@/views/contents/ContentDetail.vue'),
        meta: { title: '内容详情', hidden: true, permission: 'content:view' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UserList.vue'),
        meta: { title: '用户管理', icon: 'User', permission: 'user:view' },
      },
      {
        path: 'users/:id',
        name: 'UserDetail',
        component: () => import('@/views/users/UserDetail.vue'),
        meta: { title: '用户详情', hidden: true, permission: 'user:view' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const adminStore = useAdminStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const permission = to.meta.permission as string | undefined

  // 不需要登录的页面
  if (!requiresAuth) {
    // 已登录状态下访问登录页，重定向到首页
    if (to.path === '/login' && adminStore.isLoggedIn) {
      next('/')
      return
    }
    next()
    return
  }

  // 需要登录但未登录
  if (!adminStore.isLoggedIn) {
    next('/login')
    return
  }

  // 检查 Token 是否过期，如果过期尝试刷新
  if (adminStore.isTokenExpired()) {
    const refreshed = await adminStore.refreshAccessToken()
    if (!refreshed) {
      next('/login')
      return
    }
  }

  // 已登录但没有管理员信息，尝试获取
  if (!adminStore.adminInfo) {
    const result = await adminStore.fetchAdminInfo()
    if (!result) {
      next('/login')
      return
    }
  }

  // 权限检查
  if (permission && !adminStore.hasPermission(permission)) {
    next('/')
    return
  }

  next()
})

export default router
