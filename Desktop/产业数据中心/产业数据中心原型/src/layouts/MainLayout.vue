<template>
  <a-layout style="min-height: 100vh;">
    <!-- 侧边栏 -->
    <a-layout-sider 
      v-model:collapsed="collapsed" 
      :trigger="null" 
      collapsible
      width="280"
      collapsed-width="80"
      theme="light"
      style="box-shadow: 2px 0 8px rgba(0,0,0,0.1);"
    >
      <!-- Logo区域 -->
      <div class="logo-section">
        <div class="logo-container">
          <div class="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#00E5FF;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <!-- 数据中心图标：服务器机架 + 连接线 -->
              <rect x="4" y="6" width="8" height="20" rx="2" fill="url(#logoGradient)" opacity="0.8"/>
              <rect x="12" y="8" width="8" height="16" rx="2" fill="url(#logoGradient)" opacity="0.9"/>
              <rect x="20" y="10" width="8" height="12" rx="2" fill="url(#logoGradient)"/>
              
              <!-- 连接线 -->
              <circle cx="8" cy="12" r="1.5" fill="#00E5FF"/>
              <circle cx="16" cy="12" r="1.5" fill="#00E5FF"/>
              <circle cx="24" cy="12" r="1.5" fill="#00E5FF"/>
              <line x1="9.5" y1="12" x2="14.5" y2="12" stroke="#00E5FF" stroke-width="1"/>
              <line x1="17.5" y1="12" x2="22.5" y2="12" stroke="#00E5FF" stroke-width="1"/>
              
              <!-- 数据流动效果 -->
              <circle cx="6" cy="16" r="1" fill="#FFD700" opacity="0.8"/>
              <circle cx="14" cy="18" r="1" fill="#FFD700" opacity="0.8"/>
              <circle cx="22" cy="20" r="1" fill="#FFD700" opacity="0.8"/>
            </svg>
          </div>
          <transition name="logo-text">
            <div v-show="!collapsed" class="logo-text">
              <div class="logo-title">产业数据中心</div>
              <div class="logo-subtitle">Industry Data Center</div>
            </div>
          </transition>
        </div>
      </div>
      
      <!-- 导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        :inline-collapsed="collapsed"
        @click="handleMenuClick"
      >
        <!-- 数据概览 -->
        <a-menu-item key="/dashboard">
          <template #icon><DashboardOutlined /></template>
          数据概览
        </a-menu-item>
        
        <!-- 资源库 -->
        <a-sub-menu key="resources">
          <template #icon><DatabaseOutlined /></template>
          <template #title>资源库</template>
          <a-menu-item key="/resources/enterprises">
            <template #icon><BankOutlined /></template>
            企业库
          </a-menu-item>
          <a-menu-item key="/resources/demands">
            <template #icon><FileTextOutlined /></template>
            需求库
          </a-menu-item>
          <a-menu-item key="/resources/products">
            <template #icon><AppstoreOutlined /></template>
            产品库
          </a-menu-item>
          <a-menu-item key="/resources/solutions">
            <template #icon><BulbOutlined /></template>
            解决方案库
          </a-menu-item>
          <a-menu-item key="/resources/experts">
            <template #icon><UserOutlined /></template>
            专家库
          </a-menu-item>
        </a-sub-menu>
        
        <!-- 战略洞察 -->
        <a-sub-menu key="insights">
          <template #icon><BarChartOutlined /></template>
          <template #title>战略洞察</template>
          <a-menu-item key="/insights/industry-overview">
            <template #icon><PieChartOutlined /></template>
            产业链概览
          </a-menu-item>
          <a-menu-item key="/insights/industry-map">
            <template #icon><GlobalOutlined /></template>
            产业链地图
          </a-menu-item>
          <a-menu-item key="/insights/industry-chain">
            <template #icon><NodeIndexOutlined /></template>
            产业链图谱
          </a-menu-item>
          <a-menu-item key="/insights/enterprise-map">
            <template #icon><EnvironmentOutlined /></template>
            企业地图
          </a-menu-item>
        </a-sub-menu>
        
        <!-- 机会引擎 -->
        <a-sub-menu key="opportunities">
          <template #icon><RocketOutlined /></template>
          <template #title>机会引擎</template>
          <a-menu-item key="/opportunities/supply-demand-map">
            <template #icon><GlobalOutlined /></template>
            供需地图
          </a-menu-item>
        </a-sub-menu>
        
        <!-- 后台管理 -->
        <a-sub-menu key="admin">
          <template #icon><SettingOutlined /></template>
          <template #title>后台管理</template>
          <a-menu-item key="/admin/users">
            <template #icon><TeamOutlined /></template>
            用户管理
          </a-menu-item>
          <a-menu-item key="/admin/roles">
            <template #icon><SafetyOutlined /></template>
            角色管理
          </a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>
    
    <!-- 主内容区 -->
    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <!-- 折叠按钮 -->
          <a-button
            type="text"
            @click="collapsed = !collapsed"
            class="collapse-btn"
          >
            <template #icon>
              <MenuUnfoldOutlined v-if="collapsed" />
              <MenuFoldOutlined v-else />
            </template>
          </a-button>
          
          <!-- 面包屑导航 -->
          <a-breadcrumb class="breadcrumb">
            <a-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path">
              <component :is="item.icon" v-if="item.icon" style="margin-right: 4px;" />
              {{ item.title }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 用户信息 -->
          <a-dropdown>
            <a-button type="text" class="user-btn">
              <template #icon><UserOutlined /></template>
              <span>管理员</span>
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">
                  <UserOutlined />
                  个人资料
                </a-menu-item>
                <a-menu-item key="settings">
                  <SettingOutlined />
                  系统设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout">
                  <LogoutOutlined />
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      
      <!-- 内容区域 -->
      <a-layout-content class="content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  BankOutlined,
  FileTextOutlined,
  AppstoreOutlined,
  BulbOutlined,
  UserOutlined,
  BarChartOutlined,
  PieChartOutlined,
  NodeIndexOutlined,
  EnvironmentOutlined,
  RocketOutlined,
  GlobalOutlined,
  SettingOutlined,
  TeamOutlined,
  SafetyOutlined,
  DownOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const collapsed = ref(false)
const selectedKeys = ref<string[]>([])
const openKeys = ref<string[]>([])

// 菜单配置类型定义
interface MenuConfig {
  title: string
  icon: string
  parent?: string
}

// 菜单配置
const menuConfig: Record<string, MenuConfig> = {
  '/dashboard': { title: '数据概览', icon: 'DashboardOutlined' },
  '/resources/enterprises': { title: '企业库', icon: 'BankOutlined', parent: '资源库' },
  '/resources/demands': { title: '需求库', icon: 'FileTextOutlined', parent: '资源库' },
  '/resources/products': { title: '产品库', icon: 'AppstoreOutlined', parent: '资源库' },
  '/resources/solutions': { title: '解决方案库', icon: 'BulbOutlined', parent: '资源库' },
  '/resources/experts': { title: '专家库', icon: 'UserOutlined', parent: '资源库' },
  '/insights/industry-overview': { title: '产业链概览', icon: 'PieChartOutlined', parent: '战略洞察' },
  '/insights/industry-map': { title: '产业链地图', icon: 'GlobalOutlined', parent: '战略洞察' },
  '/insights/industry-chain': { title: '产业链图谱', icon: 'NodeIndexOutlined', parent: '战略洞察' },
  '/insights/enterprise-map': { title: '企业地图', icon: 'EnvironmentOutlined', parent: '战略洞察' },
  '/opportunities/supply-demand-map': { title: '供需地图', icon: 'GlobalOutlined', parent: '机会引擎' },
  '/admin/users': { title: '用户管理', icon: 'TeamOutlined', parent: '后台管理' },
  '/admin/roles': { title: '角色管理', icon: 'SafetyOutlined', parent: '后台管理' }
}

// 面包屑数据
const breadcrumbItems = computed(() => {
  const currentPath = route.path
  const menuItem = menuConfig[currentPath as keyof typeof menuConfig]
  
  if (!menuItem) return [{ title: '未知页面' }]
  
  const items = []
  if (menuItem.parent) {
    items.push({ title: menuItem.parent })
  }
  items.push({ 
    title: menuItem.title, 
    path: currentPath,
    icon: menuItem.icon
  })
  
  return items
})

// 菜单点击处理
const handleMenuClick = ({ key }: { key: string }) => {
  router.push(key)
}

// 更新选中的菜单项
const updateSelectedKeys = () => {
  const currentPath = route.path
  selectedKeys.value = [currentPath]
  
  // 根据当前路径设置展开的子菜单
  if (currentPath.startsWith('/resources')) {
    openKeys.value = ['resources']
  } else if (currentPath.startsWith('/insights')) {
    openKeys.value = ['insights']
  } else if (currentPath.startsWith('/opportunities')) {
    openKeys.value = ['opportunities']
  } else if (currentPath.startsWith('/admin')) {
    openKeys.value = ['admin']
  }
}

// 监听路由变化
watch(route, () => {
  updateSelectedKeys()
}, { immediate: true })

// 组件挂载时初始化
onMounted(() => {
  updateSelectedKeys()
})
</script>

<style lang="less" scoped>
.logo-section {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--bg-tertiary);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.05), rgba(25, 118, 210, 0.05));
  
  .logo-container {
    display: flex;
    align-items: center;
    gap: 16px;
    width: 100%;
    
    .logo-icon {
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: rgba(0, 229, 255, 0.1);
      border: 1px solid rgba(0, 229, 255, 0.3);
      
      svg {
        animation: logoGlow 3s ease-in-out infinite;
        
        circle[fill="#FFD700"] {
          animation: dataFlow 2s ease-in-out infinite;
        }
      }
    }
    
    .logo-text {
      .logo-title {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 2px;
        background: linear-gradient(135deg, #00E5FF, #1976D2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .logo-subtitle {
        font-size: 12px;
        color: var(--text-tertiary);
        font-weight: 400;
        letter-spacing: 0.5px;
      }
    }
  }
}

/* Logo动画 */
@keyframes logoGlow {
  0%, 100% {
    filter: drop-shadow(0 0 5px rgba(0, 229, 255, 0.3));
  }
  50% {
    filter: drop-shadow(0 0 15px rgba(0, 229, 255, 0.6));
  }
}

@keyframes dataFlow {
  0%, 100% {
    opacity: 0.4;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.logo-text-enter-active,
.logo-text-leave-active {
  transition: all 0.3s ease;
}

.logo-text-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.logo-text-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 10;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 24px;
    
    .collapse-btn {
      color: var(--text-primary, #303133);
      
      &:hover {
        color: var(--primary-color, #409EFF);
        background: rgba(64, 158, 255, 0.1);
      }
    }
    
    .breadcrumb {
      color: var(--text-secondary, #606266);
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .user-btn {
      color: var(--text-primary, #303133);
      
      &:hover {
        color: var(--primary-color, #409EFF);
        background: rgba(64, 158, 255, 0.1);
      }
    }
  }
}

.content {
  .content-wrapper {
    min-height: calc(100vh - 64px);
    background: var(--component-bg);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
    
    .header-left {
      gap: 16px;
    }
    
    .header-right {
      gap: 12px;
    }
  }
  
  .content {
    .content-wrapper {
      min-height: calc(100vh - 64px);
    }
  }
}
</style> 