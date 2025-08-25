import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

// 路由组件懒加载
const Dashboard = () => import('@/views/Dashboard.vue')
const ChatAggregation = () => import('@/views/ChatAggregation.vue')
const SOPManagement = () => import('@/views/SOPManagement.vue')
const MomentsMarketing = () => import('@/views/MomentsMarketing.vue')
const DeviceManagement = () => import('@/views/DeviceManagement.vue')
const CostManagement = () => import('@/views/CostManagement.vue')
const Login = () => import('@/views/Login.vue')

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录',
      requiresAuth: false,
      layout: 'blank'
    }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '主控面板',
      requiresAuth: true,
      icon: '📊'
    }
  },
  {
    path: '/chat',
    name: 'ChatAggregation',
    component: ChatAggregation,
    meta: {
      title: 'AI客服',
      requiresAuth: true,
      icon: '💬'
    }
  },
  {
    path: '/sop',
    name: 'SOPManagement',
    component: SOPManagement,
    meta: {
      title: 'AI销售',
      requiresAuth: true,
      icon: '🤖'
    }
  },
  {
    path: '/moments',
    name: 'MomentsMarketing',
    component: MomentsMarketing,
    meta: {
      title: '朋友圈营销',
      requiresAuth: true,
      icon: '🌟'
    }
  },
  {
    path: '/devices',
    name: 'DeviceManagement',
    component: DeviceManagement,
    meta: {
      title: '设备管理',
      requiresAuth: true,
      icon: '📱'
    }
  },
  {
    path: '/cost',
    name: 'CostManagement',
    component: CostManagement,
    meta: {
      title: '算力管理',
      requiresAuth: true,
      icon: '💰'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到',
      requiresAuth: false
    }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 熵变智元AI销售助手` : '熵变智元AI销售助手'

  // 检查登录状态
  const token = localStorage.getItem('token')
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!token && !isAuthenticated) {
      // 未登录，跳转到登录页
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // 验证token有效性
    if (token && !isAuthenticated) {
      try {
        await store.dispatch('auth/verifyToken')
      } catch (error) {
        // token无效，清除并跳转登录
        localStorage.removeItem('token')
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
  }

  // 已登录用户访问登录页，重定向到首页
  if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
    return
  }

  next()
})

// 全局后置钩子
router.afterEach((to, from) => {
  // 页面切换完成后的处理
  store.commit('app/SET_CURRENT_ROUTE', to)
})

export default router

