<template>
  <div class="chat-main">
    <div class="chat-header">
      <div class="chat-info">
        <h3>{{ currentConversation?.title || '选择对话' }}</h3>
        <div class="chat-meta">
          <span class="status-indicator" :class="currentConversation?.status">
            {{ currentConversation?.status === 'online' ? '在线' : '离线' }}
          </span>
          <span class="last-active">
            {{ formatLastActive }}
          </span>
        </div>
      </div>
      <div class="chat-actions">
        <el-button size="small" @click="toggleAI">
          <i class="el-icon-robot"></i>
          {{ isAIEnabled ? '关闭AI' : '开启AI' }}
        </el-button>
        <el-button size="small" @click="showSettings">
          <i class="el-icon-setting"></i>
          设置
        </el-button>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message-item"
        :class="message.type"
      >
        <div class="message-avatar">
          <img :src="message.avatar" :alt="message.sender" />
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-sender">{{ message.sender }}</span>
            <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
          </div>
          <div class="message-text">{{ message.content }}</div>
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <div class="input-toolbar">
        <el-button size="small" @click="showMaterials">
          <i class="el-icon-paperclip"></i>
          素材
        </el-button>
        <el-button size="small" @click="showEmoji">
          <i class="el-icon-sunny"></i>
          表情
        </el-button>
      </div>
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          @keydown.enter.prevent="sendMessage"
        />
        <el-button 
          type="primary" 
          @click="sendMessage"
          :disabled="!inputMessage.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, watch } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'ChatMain',
  props: {
    currentConversation: {
      type: Object,
      default: null
    },
    messages: {
      type: Array,
      default: () => []
    },
    isAIEnabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['send-message', 'toggle-ai', 'show-settings', 'show-materials'],
  setup(props, { emit }) {
    const messagesContainer = ref(null)
    const inputMessage = ref('')

    const formatLastActive = computed(() => {
      if (!props.currentConversation?.lastActive) return ''
      return formatDistanceToNow(props.currentConversation.lastActive, { 
        addSuffix: true, 
        locale: zhCN 
      })
    })

    const formatMessageTime = (timestamp) => {
      return formatDistanceToNow(timestamp, { 
        addSuffix: true, 
        locale: zhCN 
      })
    }

    const sendMessage = () => {
      if (!inputMessage.value.trim()) return
      
      emit('send-message', {
        content: inputMessage.value,
        conversationId: props.currentConversation?.id
      })
      
      inputMessage.value = ''
    }

    const toggleAI = () => {
      emit('toggle-ai')
    }

    const showSettings = () => {
      emit('show-settings')
    }

    const showMaterials = () => {
      emit('show-materials')
    }

    const showEmoji = () => {
      // 表情选择功能
    }

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    watch(() => props.messages.length, scrollToBottom)
    watch(() => props.currentConversation?.id, scrollToBottom)

    return {
      messagesContainer,
      inputMessage,
      formatLastActive,
      formatMessageTime,
      sendMessage,
      toggleAI,
      showSettings,
      showMaterials,
      showEmoji
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-main {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--card-bg);
}

.chat-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-color);
}

.chat-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.chat-actions {
  display: flex;
  gap: 0.5rem;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-item {
  display: flex;
  gap: 0.75rem;
  
  &.user {
    flex-direction: row-reverse;
    
    .message-content {
      background: var(--primary-color);
      color: white;
      border-radius: 1rem 1rem 0.25rem 1rem;
    }
  }
  
  &.assistant {
    .message-content {
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 1rem 1rem 1rem 0.25rem;
    }
  }
}

.message-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
}

.message-sender {
  font-weight: 600;
}

.message-time {
  opacity: 0.7;
}

.message-text {
  line-height: 1.4;
  word-wrap: break-word;
}

.chat-input {
  border-top: 1px solid var(--border-color);
  background: var(--card-bg);
  padding: 1rem;
}

.input-toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.input-area {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  
  .el-textarea {
    flex: 1;
  }
}
</style>
