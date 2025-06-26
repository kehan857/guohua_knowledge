import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录' }
  },
  
  // 主应用布局
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      // 仪表板首页
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据概览' }
      },
      
      // V1.0 资源库模块
      {
        path: '/resources',
        name: 'Resources',
        redirect: '/resources/enterprises',
        meta: { title: '资源库' },
        children: [
          // 企业库
          {
            path: '/resources/enterprises',
            name: 'EnterpriseList',
            component: () => import('@/views/resources/EnterpriseList.vue'),
            meta: { title: '企业库' }
          },
          {
            path: '/resources/enterprises/:id',
            name: 'EnterpriseDetail',
            component: () => import('@/views/resources/EnterpriseDetail.vue'),
            meta: { title: '企业详情' }
          },
          // 需求库
          {
            path: '/resources/demands',
            name: 'DemandList',
            component: () => import('@/views/resources/DemandList.vue'),
            meta: { title: '需求库' }
          },
          {
            path: '/resources/demands/:id',
            name: 'DemandDetail',
            component: () => import('@/views/resources/DemandDetail.vue'),
            meta: { title: '需求详情' }
          },
          // 产品库
          {
            path: '/resources/products',
            name: 'ProductList',
            component: () => import('@/views/resources/ProductList.vue'),
            meta: { title: '产品库' }
          },
          // 解决方案库
          {
            path: '/resources/solutions',
            name: 'SolutionList',
            component: () => import('@/views/resources/SolutionList.vue'),
            meta: { title: '解决方案库' }
          },
          // 专家库
          {
            path: '/resources/experts',
            name: 'ExpertList',
            component: () => import('@/views/resources/ExpertList.vue'),
            meta: { title: '专家库' }
          }
        ]
      },
      
      // V1.1 战略洞察模块
      {
        path: '/insights',
        name: 'Insights',
        meta: { title: '战略洞察' },
        children: [
          // 产业链概览
          {
            path: '/insights/industry-overview',
            name: 'IndustryOverview',
            component: () => import('@/views/insights/IndustryOverview.vue'),
            meta: { title: '产业链概览' }
          },
          // 产业链地图
          {
            path: '/insights/industry-map',
            name: 'IndustryMap',
            component: () => import('@/views/insights/IndustryMap.vue'),
            meta: { title: '产业链地图' }
          },
          // 产业链图谱
          {
            path: '/insights/industry-chain',
            name: 'IndustryChainDefault',
            component: () => import('@/views/insights/IndustryChain.vue'),
            meta: { title: '产业链图谱' }
          },
          {
            path: '/insights/industry-chain/:industry',
            name: 'IndustryChain',
            component: () => import('@/views/insights/IndustryChain.vue'),
            meta: { title: '产业链图谱' }
          },
          // 企业地图
          {
            path: '/insights/enterprise-map',
            name: 'EnterpriseMap',
            component: () => import('@/views/insights/EnterpriseMap.vue'),
            meta: { title: '企业地图' }
          }
        ]
      },
      
      // V1.2 机会引擎模块
      {
        path: '/opportunities',
        name: 'Opportunities',
        meta: { title: '机会引擎' },
        children: [
          // 供需地图
          {
            path: '/opportunities/supply-demand-map',
            name: 'SupplyDemandMap',
            component: () => import('@/views/opportunities/SupplyDemandMap.vue'),
            meta: { title: '供需地图' }
          }
        ]
      },
      
      // 后台管理
      {
        path: '/admin',
        name: 'Admin',
        meta: { title: '后台管理', requiresAuth: true, requiresAdmin: true },
        children: [
          {
            path: '/admin/users',
            name: 'UserManagement',
            component: () => import('@/views/admin/UserManagement.vue'),
            meta: { title: '用户管理' }
          },
          {
            path: '/admin/roles',
            name: 'RoleManagement',
            component: () => import('@/views/admin/RoleManagement.vue'),
            meta: { title: '角色管理' }
          }
        ]
      }
    ]
  },
  
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 天云聚合产业数据中心`
  }
  
  // 权限验证逻辑
  const isAuthenticated = localStorage.getItem('token')
  
  if (to.path === '/login') {
    // 如果已登录，重定向到首页
    if (isAuthenticated) {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    // 需要登录的页面
    if (!isAuthenticated) {
      next('/login')
    } else {
      next()
    }
  }
})

export default router 