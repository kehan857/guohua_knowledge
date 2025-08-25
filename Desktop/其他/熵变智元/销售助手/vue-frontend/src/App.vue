<template>
  <div id="app">
    <!-- 全局加载层 -->
    <div v-if="$store.state.app.loading" class="global-loading">
      <el-loading-spinner size="large" />
      <p>{{ $store.state.app.loadingText }}</p>
    </div>

    <!-- 全局通知容器 -->
    <div class="notification-container" v-if="notifications.length">
      <NotificationItem 
        v-for="notification in notifications"
        :key="notification.id"
        :id="notification.id"
        :title="notification.title"
        :message="notification.message"
        :type="notification.type"
        :timestamp="notification.timestamp"
        @close="closeNotification(notification.id)"
      />
    </div>

    <!-- 路由视图 -->
    <router-view />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import NotificationItem from '@/components/common/NotificationItem.vue'

export default {
  name: 'App',
  components: {
    NotificationItem
  },
  setup() {
    const store = useStore()

    // 计算属性
    const notifications = computed(() => store.state.notifications.notifications || [])

    // 方法
    const closeNotification = (id) => {
      store.dispatch('notifications/removeNotification', id)
    }

    // 初始化应用
    const initApp = async () => {
      try {
        // 获取系统配置
        await store.dispatch('app/loadConfig')
        
        // 初始化用户信息（如果有token）
        const token = localStorage.getItem('token')
        if (token) {
          await store.dispatch('auth/checkAuth')
        }
        
        // 暂时跳过WebSocket连接，避免连接错误
        // await store.dispatch('websocket/connect')
        
      } catch (error) {
        console.error('应用初始化失败:', error)
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '初始化失败',
          message: '应用启动时发生错误，请刷新页面重试'
        })
      }
    }

    // 生命周期
    initApp()

    return {
      notifications,
      closeNotification
    }
  }
}
</script>

<style lang="scss">
#app {
  font-family: var(--font-family-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--gray-900);
  background-color: var(--gray-50);
  min-height: 100vh;
}

// 全局加载层
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;

  p {
    margin-top: var(--space-4);
    color: var(--gray-600);
    font-size: var(--text-sm);
  }
}

// 通知容器
.notification-container {
  position: fixed;
  top: var(--space-4);
  right: var(--space-4);
  z-index: 3000;
  max-width: 400px;
}

// 响应式适配
@media (max-width: 768px) {
  .notification-container {
    top: var(--space-3);
    right: var(--space-3);
    left: var(--space-3);
    max-width: none;
  }
}
</style>

