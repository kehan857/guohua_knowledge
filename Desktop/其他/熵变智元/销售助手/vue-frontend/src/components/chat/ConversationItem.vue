<template>
  <div
    class="conversation-item"
    :class="{
      active,
      'has-unread': conversation.unreadCount > 0,
      'needs-intervention': conversation.needsIntervention,
      important: conversation.isImportant,
      muted: conversation.isMuted
    }"
    @click="handleClick"
    @contextmenu="handleContextMenu"
  >
    <!-- 左侧头像区域 -->
    <div class="avatar-container">
      <el-avatar
        :size="48"
        :src="conversation.avatar"
        :alt="conversation.name"
      >
        <template #default>
          <el-icon v-if="conversation.type === 'group'">
            <UserFilled />
          </el-icon>
          <span v-else>{{ getAvatarText(conversation.name) }}</span>
        </template>
      </el-avatar>
      
      <!-- 状态指示器 -->
      <div class="status-indicators">
        <div
          v-if="conversation.aiEnabled"
          class="ai-indicator"
          title="AI接管中"
        >
          🤖
        </div>
        <div
          v-if="conversation.needsIntervention"
          class="intervention-indicator"
          title="需要人工介入"
        >
          ⚠️
        </div>
        <div
          v-if="conversation.isImportant"
          class="important-indicator"
          title="重要会话"
        >
          ⭐
        </div>
      </div>
    </div>

    <!-- 中间内容区域 -->
    <div class="content-area">
      <div class="conversation-header">
        <div class="name-section">
          <span class="conversation-name">{{ conversation.name }}</span>
          <div v-if="conversation.tags?.length" class="tags-section">
            <el-tag
              v-for="tag in conversation.tags.slice(0, 2)"
              :key="tag"
              size="small"
              :type="getTagType(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </div>
        <div class="time-section">
          <span class="last-time">{{ formatTime(conversation.lastMessageTime) }}</span>
        </div>
      </div>

      <div class="conversation-preview">
        <!-- 最后消息预览 -->
        <div class="message-preview">
          <span
            v-if="conversation.lastMessageSender"
            class="sender-name"
            :class="{ 'is-self': conversation.lastMessageSender === 'self' }"
          >
            {{ getSenderDisplayName(conversation.lastMessageSender) }}:
          </span>
          <span class="message-content">{{ getMessagePreview(conversation.lastMessage) }}</span>
        </div>

        <!-- 输入状态 -->
        <div v-if="conversation.isTyping" class="typing-indicator">
          <TypingAnimation />
          <span>正在输入...</span>
        </div>
      </div>
    </div>

    <!-- 右侧信息区域 -->
    <div class="info-area">
      <!-- 未读数量 -->
      <el-badge
        v-if="conversation.unreadCount > 0"
        :value="conversation.unreadCount > 99 ? '99+' : conversation.unreadCount"
        :max="99"
        class="unread-badge"
      />

      <!-- 静音图标 -->
      <el-icon v-if="conversation.isMuted" class="mute-icon">
        <MuteNotification />
      </el-icon>

      <!-- 置顶图标 -->
      <el-icon v-if="conversation.isPinned" class="pin-icon">
        <Top />
      </el-icon>
    </div>

    <!-- 优先级指示条 -->
    <div
      v-if="conversation.needsIntervention"
      class="priority-bar intervention"
    />
    <div
      v-else-if="conversation.isImportant"
      class="priority-bar important"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import { UserFilled, MuteNotification, Top } from '@element-plus/icons-vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

import TypingAnimation from '@/components/common/TypingAnimation.vue'

export default {
  name: 'ConversationItem',
  components: {
    UserFilled,
    MuteNotification,
    Top,
    TypingAnimation
  },
  props: {
    conversation: {
      type: Object,
      required: true
    },
    active: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click', 'context-menu'],

  setup(props, { emit }) {
    // 计算属性
    const avatarText = computed(() => {
      return getAvatarText(props.conversation.name)
    })

    // 方法
    const handleClick = () => {
      emit('click', props.conversation)
    }

    const handleContextMenu = (event) => {
      emit('context-menu', event, props.conversation)
    }

    const getAvatarText = (name) => {
      if (!name) return '?'
      // 取中文名字的最后一个字，或英文名的首字母
      const chars = name.trim()
      if (/[\u4e00-\u9fa5]/.test(chars)) {
        return chars.slice(-1)
      } else {
        return chars.charAt(0).toUpperCase()
      }
    }

    const formatTime = (time) => {
      if (!time) return ''
      
      const date = new Date(time)
      const now = new Date()
      const diffInHours = (now - date) / (1000 * 60 * 60)

      if (diffInHours < 24) {
        // 24小时内显示时间
        return date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      } else if (diffInHours < 24 * 7) {
        // 一周内显示星期
        return date.toLocaleDateString('zh-CN', { weekday: 'short' })
      } else {
        // 超过一周显示日期
        return date.toLocaleDateString('zh-CN', {
          month: 'short',
          day: 'numeric'
        })
      }
    }

    const getSenderDisplayName = (sender) => {
      if (sender === 'self') return '我'
      if (sender === 'ai') return 'AI'
      return sender || '对方'
    }

    const getMessagePreview = (message) => {
      if (!message) return '暂无消息'

      // 处理不同类型的消息
      if (typeof message === 'object') {
        switch (message.type) {
          case 'image':
            return '[图片]'
          case 'file':
            return '[文件]'
          case 'voice':
            return '[语音]'
          case 'video':
            return '[视频]'
          case 'miniprogram':
            return '[小程序]'
          default:
            return message.content || '[消息]'
        }
      }

      // 文本消息截断处理
      const text = String(message).replace(/\n/g, ' ')
      return text.length > 30 ? text.substring(0, 30) + '...' : text
    }

    const getTagType = (tag) => {
      const tagTypeMap = {
        'VIP客户': 'warning',
        '高意向': 'success',
        '潜在客户': 'info',
        '已付费': 'success',
        '需跟进': 'danger'
      }
      return tagTypeMap[tag] || 'info'
    }

    return {
      avatarText,
      handleClick,
      handleContextMenu,
      getAvatarText,
      formatTime,
      getSenderDisplayName,
      getMessagePreview,
      getTagType
    }
  }
}
</script>

<style lang="scss" scoped>
.conversation-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  cursor: pointer;
  transition: all var(--transition-fast);
  border-left: 3px solid transparent;
  position: relative;
  background: white;
  border-bottom: 1px solid var(--gray-100);

  &:hover {
    background-color: var(--gray-50);
  }

  &.active {
    background-color: var(--primary-50);
    border-left-color: var(--primary-500);
  }

  &.needs-intervention {
    background-color: var(--error-50);
    border-left-color: var(--error-500);
    animation: pulse-intervention 2s infinite;
  }

  &.important {
    border-left-color: var(--warning-500);
  }

  &.muted {
    opacity: 0.7;
  }

  &.has-unread {
    .conversation-name {
      font-weight: 700;
    }
  }
}

.avatar-container {
  position: relative;
  flex-shrink: 0;
}

.status-indicators {
  position: absolute;
  bottom: -2px;
  right: -2px;
  display: flex;
  gap: 2px;
}

.ai-indicator,
.intervention-indicator,
.important-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-sm);
}

.content-area {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-1);
}

.name-section {
  flex: 1;
  min-width: 0;
}

.conversation-name {
  font-size: var(--text-sm);
  color: var(--gray-900);
  font-weight: 500;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: var(--space-1);
}

.tags-section {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.time-section {
  flex-shrink: 0;
  margin-left: var(--space-2);
}

.last-time {
  font-size: var(--text-xs);
  color: var(--gray-500);
  white-space: nowrap;
}

.conversation-preview {
  min-height: 20px;
}

.message-preview {
  font-size: var(--text-sm);
  color: var(--gray-600);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.sender-name {
  color: var(--gray-500);
  
  &.is-self {
    color: var(--primary-600);
  }
}

.message-content {
  margin-left: var(--space-1);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--primary-600);
  font-size: var(--text-xs);
  font-style: italic;
}

.info-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  flex-shrink: 0;
}

.unread-badge {
  :deep(.el-badge__content) {
    font-size: var(--text-xs);
    padding: 0 var(--space-1);
    min-width: 16px;
    height: 16px;
    line-height: 16px;
  }
}

.mute-icon,
.pin-icon {
  font-size: var(--text-sm);
  color: var(--gray-400);
}

.priority-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;

  &.intervention {
    background: linear-gradient(
      to bottom,
      var(--error-500),
      var(--error-400)
    );
  }

  &.important {
    background: linear-gradient(
      to bottom,
      var(--warning-500),
      var(--warning-400)
    );
  }
}

// 动画效果
@keyframes pulse-intervention {
  0%, 100% {
    background-color: var(--error-50);
  }
  50% {
    background-color: var(--error-100);
  }
}

// 响应式适配
@media (max-width: 768px) {
  .conversation-item {
    padding: var(--space-2) var(--space-3);
    gap: var(--space-2);
  }

  .avatar-container {
    :deep(.el-avatar) {
      width: 40px !important;
      height: 40px !important;
      font-size: var(--text-sm);
    }
  }

  .conversation-name {
    font-size: var(--text-xs);
  }

  .message-preview {
    font-size: var(--text-xs);
  }

  .tags-section {
    display: none; // 移动端隐藏标签
  }
}

// 暗色模式适配
@media (prefers-color-scheme: dark) {
  .conversation-item {
    background: var(--gray-800);
    border-bottom-color: var(--gray-700);

    &:hover {
      background-color: var(--gray-700);
    }

    &.active {
      background-color: var(--primary-900);
    }
  }

  .conversation-name {
    color: var(--gray-100);
  }

  .message-preview {
    color: var(--gray-300);
  }

  .last-time {
    color: var(--gray-400);
  }
}
</style>

