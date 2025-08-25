<template>
  <div class="chat-context">
    <div class="context-header">
      <h4>对话上下文</h4>
      <el-button size="small" @click="clearContext">
        <i class="el-icon-delete"></i>
        清空
      </el-button>
    </div>
    
    <div class="context-content">
      <div 
        v-for="item in contextItems" 
        :key="item.id"
        class="context-item"
      >
        <div class="context-type">
          <i :class="getTypeIcon(item.type)"></i>
          {{ getTypeLabel(item.type) }}
        </div>
        <div class="context-text">{{ item.content }}</div>
        <div class="context-time">{{ formatTime(item.timestamp) }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'ChatContext',
  props: {
    contextItems: {
      type: Array,
      default: () => []
    }
  },
  emits: ['clear-context'],
  setup(props, { emit }) {
    const getTypeIcon = (type) => {
      const icons = {
        user_info: 'el-icon-user',
        product_info: 'el-icon-goods',
        conversation_history: 'el-icon-chat-dot-round',
        system_prompt: 'el-icon-setting'
      }
      return icons[type] || 'el-icon-info'
    }

    const getTypeLabel = (type) => {
      const labels = {
        user_info: '用户信息',
        product_info: '产品信息',
        conversation_history: '对话历史',
        system_prompt: '系统提示'
      }
      return labels[type] || '未知类型'
    }

    const formatTime = (timestamp) => {
      return formatDistanceToNow(timestamp, { 
        addSuffix: true, 
        locale: zhCN 
      })
    }

    const clearContext = () => {
      emit('clear-context')
    }

    return {
      getTypeIcon,
      getTypeLabel,
      formatTime,
      clearContext
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-context {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--card-bg);
  border-left: 1px solid var(--border-color);
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  
  h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
  }
}

.context-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.context-item {
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: var(--border-radius);
  background: var(--bg-color);
  border: 1px solid var(--border-color);
}

.context-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
  
  i {
    font-size: 0.875rem;
  }
}

.context-text {
  font-size: 0.875rem;
  line-height: 1.4;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  word-wrap: break-word;
}

.context-time {
  font-size: 0.625rem;
  color: var(--text-muted);
}
</style>
