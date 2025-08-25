<template>
  <div class="chat-sidebar">
    <!-- 侧边栏头部 -->
    <div class="sidebar-header">
      <h2 class="sidebar-title">聊天会话</h2>
      <div class="header-actions">
        <el-button
          type="text"
          :icon="Refresh"
          @click="handleRefresh"
          :loading="loading"
        />
        <el-dropdown trigger="click">
          <el-button type="text" :icon="MoreFilled" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleMarkAllRead">
                <el-icon><Check /></el-icon>
                全部标记已读
              </el-dropdown-item>
              <el-dropdown-item @click="handleExportChats">
                <el-icon><Download /></el-icon>
                导出聊天记录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="sidebar-filters">
      <div class="search-container">
        <el-input
          v-model="searchQuery"
          placeholder="搜索昵称/备注/群名..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          @clear="handleSearchClear"
        />
      </div>
      
      <div class="filter-tabs">
        <el-radio-group v-model="activeFilter" @change="handleFilterChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
          <el-radio-button label="managed">已托管</el-radio-button>
          <el-radio-button label="intervention">需介入</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="conversations-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredConversations.length === 0" class="empty-state">
        <el-empty
          :image-size="80"
          description="暂无会话"
        >
          <el-button type="primary" @click="handleRefresh">
            刷新列表
          </el-button>
        </el-empty>
      </div>

      <!-- 会话列表 -->
      <el-scrollbar v-else class="conversations-list">
        <TransitionGroup name="conversation" tag="div">
          <ConversationItem
            v-for="conversation in filteredConversations"
            :key="conversation.id"
            :conversation="conversation"
            :active="conversation.id === selectedId"
            @click="handleConversationClick"
            @context-menu="handleContextMenu"
          />
        </TransitionGroup>
      </el-scrollbar>
    </div>

    <!-- 底部统计信息 -->
    <div class="sidebar-footer">
      <div class="stats-info">
        <span class="stat-item">
          <el-icon><ChatDotRound /></el-icon>
          总会话: {{ totalCount }}
        </span>
        <span class="stat-item">
          <el-icon><Bell /></el-icon>
          未读: {{ unreadCount }}
        </span>
      </div>
    </div>

    <!-- 右键菜单 -->
    <el-dropdown
      ref="contextMenuRef"
      trigger="contextmenu"
      :virtual-ref="contextMenuTarget"
      virtual-triggering
    >
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item @click="handleMarkAsRead">
            <el-icon><Check /></el-icon>
            标记已读
          </el-dropdown-item>
          <el-dropdown-item @click="handleSetPriority">
            <el-icon><Star /></el-icon>
            设为重要
          </el-dropdown-item>
          <el-dropdown-item @click="handleMute">
            <el-icon><MuteNotification /></el-icon>
            静音通知
          </el-dropdown-item>
          <el-dropdown-item divided @click="handleDeleteConversation">
            <el-icon><Delete /></el-icon>
            删除会话
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import {
  Search,
  Refresh,
  MoreFilled,
  Check,
  Download,
  ChatDotRound,
  Bell,
  Star,
  MuteNotification,
  Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import ConversationItem from './ConversationItem.vue'

export default {
  name: 'ChatSidebar',
  components: {
    ConversationItem,
    Search,
    Refresh,
    MoreFilled,
    Check,
    Download,
    ChatDotRound,
    Bell,
    Star,
    MuteNotification,
    Delete
  },
  props: {
    conversations: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['conversation-select', 'search', 'filter-change'],

  setup(props, { emit }) {
    const store = useStore()

    // 响应式数据
    const searchQuery = ref('')
    const activeFilter = ref('all')
    const selectedId = ref(null)
    const contextMenuRef = ref(null)
    const contextMenuTarget = ref(null)
    const contextConversation = ref(null)

    // 计算属性
    const filteredConversations = computed(() => {
      let result = [...props.conversations]

      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(conv =>
          conv.name?.toLowerCase().includes(query) ||
          conv.remark?.toLowerCase().includes(query) ||
          conv.lastMessage?.toLowerCase().includes(query)
        )
      }

      // 状态过滤
      switch (activeFilter.value) {
        case 'unread':
          result = result.filter(conv => conv.unreadCount > 0)
          break
        case 'managed':
          result = result.filter(conv => conv.aiEnabled)
          break
        case 'intervention':
          result = result.filter(conv => conv.needsIntervention)
          break
      }

      // 排序：需要介入的置顶，然后按最后消息时间排序
      return result.sort((a, b) => {
        if (a.needsIntervention && !b.needsIntervention) return -1
        if (!a.needsIntervention && b.needsIntervention) return 1
        return new Date(b.lastMessageTime) - new Date(a.lastMessageTime)
      })
    })

    const totalCount = computed(() => props.conversations.length)
    const unreadCount = computed(() => 
      props.conversations.reduce((sum, conv) => sum + (conv.unreadCount || 0), 0)
    )

    // 方法
    const handleSearch = (value) => {
      emit('search', value)
    }

    const handleSearchClear = () => {
      searchQuery.value = ''
      emit('search', '')
    }

    const handleFilterChange = (filter) => {
      emit('filter-change', filter)
    }

    const handleRefresh = () => {
      store.dispatch('chat/loadConversations', { force: true })
    }

    const handleConversationClick = (conversation) => {
      selectedId.value = conversation.id
      emit('conversation-select', conversation)
    }

    const handleContextMenu = (event, conversation) => {
      event.preventDefault()
      contextMenuTarget.value = event.target
      contextConversation.value = conversation
      contextMenuRef.value?.handleOpen()
    }

    const handleMarkAllRead = async () => {
      try {
        await store.dispatch('chat/markAllAsRead')
        ElMessage.success('已标记全部会话为已读')
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }

    const handleExportChats = () => {
      store.dispatch('chat/exportChats')
    }

    const handleMarkAsRead = async () => {
      if (!contextConversation.value) return
      
      try {
        await store.dispatch('chat/markAsRead', contextConversation.value.id)
        ElMessage.success('已标记为已读')
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }

    const handleSetPriority = async () => {
      if (!contextConversation.value) return
      
      try {
        await store.dispatch('chat/setPriority', {
          conversationId: contextConversation.value.id,
          priority: !contextConversation.value.isImportant
        })
        ElMessage.success(contextConversation.value.isImportant ? '已取消重要标记' : '已标记为重要')
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }

    const handleMute = async () => {
      if (!contextConversation.value) return
      
      try {
        await store.dispatch('chat/toggleMute', contextConversation.value.id)
        ElMessage.success(contextConversation.value.isMuted ? '已取消静音' : '已设置静音')
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }

    const handleDeleteConversation = async () => {
      if (!contextConversation.value) return

      try {
        await ElMessageBox.confirm(
          '确定要删除这个会话吗？删除后将无法恢复。',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await store.dispatch('chat/deleteConversation', contextConversation.value.id)
        ElMessage.success('会话已删除')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }

    // 监听搜索变化
    watch(searchQuery, (newValue) => {
      handleSearch(newValue)
    }, { debounce: 300 })

    return {
      // 数据
      searchQuery,
      activeFilter,
      selectedId,
      contextMenuRef,
      contextMenuTarget,
      contextConversation,
      
      // 计算属性
      filteredConversations,
      totalCount,
      unreadCount,
      
      // 方法
      handleSearch,
      handleSearchClear,
      handleFilterChange,
      handleRefresh,
      handleConversationClick,
      handleContextMenu,
      handleMarkAllRead,
      handleExportChats,
      handleMarkAsRead,
      handleSetPriority,
      handleMute,
      handleDeleteConversation
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-sidebar {
  background: white;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-right: 1px solid var(--gray-200);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--gray-200);
  background: white;
  z-index: 10;
}

.sidebar-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-1);
}

.sidebar-filters {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--gray-200);
  background: white;
  z-index: 9;
}

.search-container {
  margin-bottom: var(--space-3);
}

.filter-tabs {
  :deep(.el-radio-group) {
    width: 100%;
    
    .el-radio-button {
      flex: 1;
    }
    
    .el-radio-button__inner {
      width: 100%;
      font-size: var(--text-xs);
      padding: var(--space-1) var(--space-2);
    }
  }
}

.conversations-container {
  flex: 1;
  overflow: hidden;
  background: var(--gray-50);
}

.loading-container {
  padding: var(--space-4) var(--space-5);
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.conversations-list {
  height: 100%;
  
  :deep(.el-scrollbar__view) {
    padding: var(--space-2) 0;
  }
}

.sidebar-footer {
  padding: var(--space-3) var(--space-5);
  border-top: 1px solid var(--gray-200);
  background: white;
}

.stats-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--gray-600);
  
  .el-icon {
    font-size: var(--text-sm);
  }
}

// 过渡动画
.conversation-enter-active,
.conversation-leave-active {
  transition: all var(--transition-normal);
}

.conversation-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.conversation-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.conversation-move {
  transition: transform var(--transition-normal);
}

// 响应式适配
@media (max-width: 768px) {
  .filter-tabs {
    :deep(.el-radio-button__inner) {
      font-size: 10px;
      padding: var(--space-1);
    }
  }
  
  .sidebar-header {
    padding: var(--space-3) var(--space-4);
  }
  
  .sidebar-filters {
    padding: var(--space-3) var(--space-4);
  }
}
</style>

