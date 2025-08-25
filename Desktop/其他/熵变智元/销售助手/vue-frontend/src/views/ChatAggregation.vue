<template>
  <div class="chat-aggregation">
    <!-- 聊天布局容器 -->
    <div class="chat-layout" :class="{ 'mobile-view': isMobile }">
      <!-- 左侧会话列表 -->
      <ChatSidebar
        v-show="!isMobile || showSidebar"
        :conversations="conversations"
        :loading="conversationsLoading"
        @conversation-select="handleConversationSelect"
        @search="handleSearch"
        @filter-change="handleFilterChange"
      />

      <!-- 中间聊天窗口 -->
      <ChatMain
        :current-conversation="currentConversation"
        :messages="messages"
        :loading="messagesLoading"
        :ai-enabled="aiEnabled"
        @send-message="handleSendMessage"
        @toggle-ai="handleToggleAI"
        @manual-intervention="handleManualIntervention"
      />

      <!-- 右侧信息面板 -->
      <ChatContext
        v-show="!isMobile || showContext"
        :conversation="currentConversation"
        :contact-info="contactInfo"
        @update-tags="handleUpdateTags"
        @create-task="handleCreateTask"
      />
    </div>

    <!-- 移动端控制按钮 -->
    <div v-if="isMobile" class="mobile-controls">
      <el-button
        type="primary"
        :icon="List"
        circle
        @click="showSidebar = !showSidebar"
      />
      <el-button
        type="info"
        :icon="User"
        circle
        @click="showContext = !showContext"
      />
    </div>

    <!-- 物料选择模态框 -->
    <MaterialModal
      v-model="materialModalVisible"
      @select="handleMaterialSelect"
    />

    <!-- AI设置模态框 -->
    <AISettingsModal
      v-model="aiSettingsVisible"
      :settings="aiSettings"
      @save="handleAISettingsChange"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { List, User } from '@element-plus/icons-vue'
import { useBreakpoints } from '@/composables/useBreakpoints'

// 组件导入
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMain from '@/components/chat/ChatMain.vue'
import ChatContext from '@/components/chat/ChatContext.vue'
import MaterialModal from '@/components/chat/MaterialModal.vue'
import AISettingsModal from '@/components/chat/AISettingsModal.vue'

export default {
  name: 'ChatAggregation',
  components: {
    ChatSidebar,
    ChatMain,
    ChatContext,
    MaterialModal,
    AISettingsModal,
    List,
    User
  },

  setup() {
    const store = useStore()
    const router = useRouter()
    const { isMobile } = useBreakpoints()

    // 响应式数据
    const showSidebar = ref(false)
    const showContext = ref(false)
    const materialModalVisible = ref(false)
    const aiSettingsVisible = ref(false)
    const currentConversationId = ref(null)
    const searchQuery = ref('')
    const activeFilter = ref('all')

    // 计算属性
    const conversations = computed(() => 
      store.getters['chat/filteredConversations'](searchQuery.value, activeFilter.value)
    )
    
    const currentConversation = computed(() => 
      store.getters['chat/currentConversation']
    )
    
    const messages = computed(() => 
      store.getters['chat/currentMessages']
    )
    
    const contactInfo = computed(() => 
      store.getters['chat/currentContactInfo']
    )
    
    const aiEnabled = computed(() => 
      store.getters['chat/isAIEnabled']
    )
    
    const aiSettings = computed(() => 
      store.state.chat.aiSettings
    )
    
    const conversationsLoading = computed(() => 
      store.state.chat.conversationsLoading
    )
    
    const messagesLoading = computed(() => 
      store.state.chat.messagesLoading
    )

    // 方法
    const handleConversationSelect = async (conversation) => {
      currentConversationId.value = conversation.id
      
      // 更新当前会话
      await store.dispatch('chat/setCurrentConversation', conversation.id)
      
      // 加载消息历史
      await store.dispatch('chat/loadMessages', {
        conversationId: conversation.id,
        page: 1,
        size: 50
      })
      
      // 标记为已读
      await store.dispatch('chat/markAsRead', conversation.id)
      
      // 移动端自动隐藏侧边栏
      if (isMobile.value) {
        showSidebar.value = false
      }
    }

    const handleSendMessage = async (messageData) => {
      try {
        await store.dispatch('chat/sendMessage', {
          conversationId: currentConversationId.value,
          ...messageData
        })
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '发送失败',
          message: error.message
        })
      }
    }

    const handleToggleAI = async (enabled) => {
      try {
        await store.dispatch('chat/toggleAI', {
          conversationId: currentConversationId.value,
          enabled
        })
        
        store.dispatch('notifications/addNotification', {
          type: 'success',
          title: 'AI状态更新',
          message: enabled ? 'AI接管已启用' : '已切换为人工模式'
        })
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '状态切换失败',
          message: error.message
        })
      }
    }

    const handleManualIntervention = () => {
      // 强制切换为人工模式
      handleToggleAI(false)
      
      // 发送介入通知
      store.dispatch('notifications/addNotification', {
        type: 'info',
        title: '人工介入',
        message: '已切换为人工模式，AI回复已暂停'
      })
    }

    const handleSearch = (query) => {
      searchQuery.value = query
    }

    const handleFilterChange = (filter) => {
      activeFilter.value = filter
    }

    const handleUpdateTags = async (tags) => {
      try {
        await store.dispatch('chat/updateContactTags', {
          conversationId: currentConversationId.value,
          tags
        })
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '标签更新失败',
          message: error.message
        })
      }
    }

    const handleCreateTask = (taskData) => {
      router.push({
        name: 'SOPManagement',
        query: {
          action: 'create',
          targetId: currentConversationId.value,
          targetType: currentConversation.value?.type || 'friend'
        }
      })
    }

    const handleMaterialSelect = (material) => {
      // 发送选中的物料
      handleSendMessage({
        type: material.type,
        content: material.content,
        materialId: material.id
      })
      
      materialModalVisible.value = false
    }

    const handleAISettingsChange = async (settings) => {
      try {
        await store.dispatch('chat/updateAISettings', settings)
        
        store.dispatch('notifications/addNotification', {
          type: 'success',
          title: 'AI设置已更新',
          message: '新的AI配置将在下次对话中生效'
        })
        
        aiSettingsVisible.value = false
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '设置保存失败',
          message: error.message
        })
      }
    }

    // 数据加载
    const loadInitialData = async () => {
      try {
        // 并行加载会话列表和AI设置
        await Promise.all([
          store.dispatch('chat/loadConversations'),
          store.dispatch('chat/loadAISettings')
        ])

        // 如果有路由参数指定的会话ID，自动选择
        const { conversationId } = router.currentRoute.value.query
        if (conversationId) {
          const conversation = conversations.value.find(c => c.id === conversationId)
          if (conversation) {
            await handleConversationSelect(conversation)
          }
        }
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '数据加载失败',
          message: error.message
        })
      }
    }

    // WebSocket事件监听
    const setupWebSocketListeners = () => {
      const wsManager = store.state.websocket.manager
      
      if (wsManager) {
        // 新消息事件
        wsManager.on('new_message', (data) => {
          store.dispatch('chat/handleNewMessage', data)
        })
        
        // AI状态变化
        wsManager.on('ai_toggle', (data) => {
          store.dispatch('chat/updateAIStatus', data)
        })
        
        // 输入状态
        wsManager.on('typing_status', (data) => {
          store.dispatch('chat/updateTypingStatus', data)
        })
      }
    }

    // 生命周期
    onMounted(() => {
      loadInitialData()
      setupWebSocketListeners()
    })

    onUnmounted(() => {
      // 清理WebSocket监听器
      const wsManager = store.state.websocket.manager
      if (wsManager) {
        wsManager.off('new_message')
        wsManager.off('ai_toggle')
        wsManager.off('typing_status')
      }
    })

    // 监听路由变化
    watch(() => router.currentRoute.value.query, (newQuery) => {
      if (newQuery.conversationId && newQuery.conversationId !== currentConversationId.value) {
        const conversation = conversations.value.find(c => c.id === newQuery.conversationId)
        if (conversation) {
          handleConversationSelect(conversation)
        }
      }
    })

    return {
      // 数据
      isMobile,
      showSidebar,
      showContext,
      materialModalVisible,
      aiSettingsVisible,
      currentConversationId,
      
      // 计算属性
      conversations,
      currentConversation,
      messages,
      contactInfo,
      aiEnabled,
      aiSettings,
      conversationsLoading,
      messagesLoading,
      
      // 方法
      handleConversationSelect,
      handleSendMessage,
      handleToggleAI,
      handleManualIntervention,
      handleSearch,
      handleFilterChange,
      handleUpdateTags,
      handleCreateTask,
      handleMaterialSelect,
      handleAISettingsChange,
      
      // 图标
      List,
      User
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-aggregation {
  height: calc(100vh - 64px);
  position: relative;
  overflow: hidden;
}

.chat-layout {
  display: grid;
  grid-template-columns: 320px 1fr 280px;
  height: 100%;
  background-color: var(--gray-100);
  gap: 1px;

  &.mobile-view {
    grid-template-columns: 1fr;
    position: relative;
  }
}

// 移动端控制按钮
.mobile-controls {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  z-index: 100;

  .el-button {
    box-shadow: var(--shadow-lg);
  }
}

// 响应式适配
@media (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: 280px 1fr;
  }
}

@media (max-width: 768px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }
}

// 过渡动画
.chat-layout > * {
  transition: transform var(--transition-normal);
}

.mobile-view {
  .chat-sidebar,
  .chat-context {
    position: absolute;
    top: 0;
    bottom: 0;
    z-index: 50;
    box-shadow: var(--shadow-lg);
  }

  .chat-sidebar {
    left: 0;
    width: 280px;
    transform: translateX(-100%);

    &.show {
      transform: translateX(0);
    }
  }

  .chat-context {
    right: 0;
    width: 280px;
    transform: translateX(100%);

    &.show {
      transform: translateX(0);
    }
  }
}
</style>

