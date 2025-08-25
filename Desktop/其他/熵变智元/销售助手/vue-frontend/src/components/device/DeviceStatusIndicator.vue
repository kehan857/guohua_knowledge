<template>
  <div class="device-status-indicator">
    <div class="status-badge" :class="statusClass">
      <div class="status-dot" :class="{ pulse: isPulsing }"></div>
      <span class="status-text">{{ statusText }}</span>
    </div>
    
    <!-- 详细状态信息 -->
    <div v-if="showDetails" class="status-details">
      <div class="detail-item">
        <span class="detail-label">状态:</span>
        <span class="detail-value">{{ statusDescription }}</span>
      </div>
      <div v-if="lastSeen" class="detail-item">
        <span class="detail-label">最后在线:</span>
        <span class="detail-value">{{ formatLastSeen(lastSeen) }}</span>
      </div>
      <div v-if="onlineDuration" class="detail-item">
        <span class="detail-label">在线时长:</span>
        <span class="detail-value">{{ formatDuration(onlineDuration) }}</span>
      </div>
    </div>

    <!-- 状态操作按钮 -->
    <div v-if="showActions" class="status-actions">
      <el-button
        v-if="status === 'OFFLINE' || status === 'AWAITING_RELOGIN'"
        type="primary"
        size="small"
        :icon="Refresh"
        @click="handleReconnect"
      >
        重连
      </el-button>
      
      <el-button
        v-if="status === 'ONLINE'"
        type="warning"
        size="small"
        :icon="PowerOff"
        @click="handleDisconnect"
      >
        下线
      </el-button>

      <el-button
        v-if="status === 'RISK_CONTROLLED'"
        type="info"
        size="small"
        :icon="Warning"
        @click="handleCheckRisk"
      >
        检查风控
      </el-button>
    </div>

    <!-- 状态变化历史 -->
    <div v-if="showHistory && statusHistory.length" class="status-history">
      <div class="history-title">状态变化历史</div>
      <div class="history-timeline">
        <div
          v-for="(change, index) in statusHistory.slice(0, 5)"
          :key="index"
          class="history-item"
        >
          <div class="history-dot" :class="getStatusClass(change.status)"></div>
          <div class="history-content">
            <div class="history-status">{{ getStatusText(change.status) }}</div>
            <div class="history-time">{{ formatChangeTime(change.timestamp) }}</div>
            <div v-if="change.reason" class="history-reason">{{ change.reason }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { Refresh, PowerOff, Warning } from '@element-plus/icons-vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'DeviceStatusIndicator',
  components: {
    Refresh,
    PowerOff,
    Warning
  },
  props: {
    status: {
      type: String,
      required: true,
      validator: (value) => [
        'ONLINE',
        'OFFLINE',
        'AWAITING_RELOGIN',
        'RISK_CONTROLLED',
        'BANNED'
      ].includes(value)
    },
    lastSeen: {
      type: [String, Date],
      default: null
    },
    onlineDuration: {
      type: Number,
      default: null
    },
    statusHistory: {
      type: Array,
      default: () => []
    },
    showDetails: {
      type: Boolean,
      default: false
    },
    showActions: {
      type: Boolean,
      default: false
    },
    showHistory: {
      type: Boolean,
      default: false
    }
  },
  emits: ['reconnect', 'disconnect', 'check-risk'],

  setup(props, { emit }) {
    // 状态配置映射
    const statusConfig = {
      ONLINE: {
        class: 'online',
        text: '在线',
        description: '设备正常在线，可正常收发消息',
        color: 'var(--success-500)',
        pulse: true
      },
      OFFLINE: {
        class: 'offline',
        text: '离线',
        description: '设备断开连接，无法收发消息',
        color: 'var(--gray-500)',
        pulse: false
      },
      AWAITING_RELOGIN: {
        class: 'awaiting',
        text: '等待登录',
        description: '需要重新扫码登录',
        color: 'var(--warning-500)',
        pulse: true
      },
      RISK_CONTROLLED: {
        class: 'risk',
        text: '风控中',
        description: '账号被微信风控，功能受限',
        color: 'var(--error-500)',
        pulse: true
      },
      BANNED: {
        class: 'banned',
        text: '已封禁',
        description: '账号被永久封禁',
        color: 'var(--gray-800)',
        pulse: false
      }
    }

    // 计算属性
    const statusClass = computed(() => statusConfig[props.status]?.class || 'unknown')
    const statusText = computed(() => statusConfig[props.status]?.text || '未知')
    const statusDescription = computed(() => statusConfig[props.status]?.description || '状态未知')
    const isPulsing = computed(() => statusConfig[props.status]?.pulse || false)

    // 方法
    const formatLastSeen = (timestamp) => {
      if (!timestamp) return '从未在线'
      
      try {
        const date = new Date(timestamp)
        return formatDistanceToNow(date, { 
          addSuffix: true, 
          locale: zhCN 
        })
      } catch (error) {
        return '时间格式错误'
      }
    }

    const formatDuration = (seconds) => {
      if (!seconds || seconds < 0) return '0分钟'
      
      const days = Math.floor(seconds / (24 * 60 * 60))
      const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
      const minutes = Math.floor((seconds % (60 * 60)) / 60)
      
      if (days > 0) {
        return `${days}天${hours}小时${minutes}分钟`
      } else if (hours > 0) {
        return `${hours}小时${minutes}分钟`
      } else {
        return `${minutes}分钟`
      }
    }

    const formatChangeTime = (timestamp) => {
      if (!timestamp) return ''
      
      try {
        const date = new Date(timestamp)
        return date.toLocaleString('zh-CN', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return '时间错误'
      }
    }

    const getStatusClass = (status) => {
      return statusConfig[status]?.class || 'unknown'
    }

    const getStatusText = (status) => {
      return statusConfig[status]?.text || status
    }

    const handleReconnect = () => {
      emit('reconnect')
    }

    const handleDisconnect = () => {
      emit('disconnect')
    }

    const handleCheckRisk = () => {
      emit('check-risk')
    }

    return {
      statusClass,
      statusText,
      statusDescription,
      isPulsing,
      formatLastSeen,
      formatDuration,
      formatChangeTime,
      getStatusClass,
      getStatusText,
      handleReconnect,
      handleDisconnect,
      handleCheckRisk
    }
  }
}
</script>

<style lang="scss" scoped>
.device-status-indicator {
  display: inline-block;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 500;
  border: 1px solid;
  transition: all var(--transition-fast);

  &.online {
    background-color: var(--success-50);
    color: var(--success-700);
    border-color: var(--success-200);
  }

  &.offline {
    background-color: var(--gray-100);
    color: var(--gray-700);
    border-color: var(--gray-300);
  }

  &.awaiting {
    background-color: var(--warning-50);
    color: var(--warning-700);
    border-color: var(--warning-200);
  }

  &.risk {
    background-color: var(--error-50);
    color: var(--error-700);
    border-color: var(--error-200);
  }

  &.banned {
    background-color: var(--gray-200);
    color: var(--gray-800);
    border-color: var(--gray-400);
  }

  &.unknown {
    background-color: var(--gray-100);
    color: var(--gray-600);
    border-color: var(--gray-300);
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  .status-badge.online & {
    background-color: var(--success-500);
  }

  .status-badge.offline & {
    background-color: var(--gray-500);
  }

  .status-badge.awaiting & {
    background-color: var(--warning-500);
  }

  .status-badge.risk & {
    background-color: var(--error-500);
  }

  .status-badge.banned & {
    background-color: var(--gray-700);
  }

  .status-badge.unknown & {
    background-color: var(--gray-500);
  }

  &.pulse {
    animation: pulse 2s infinite;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 currentColor;
    opacity: 1;
  }
  70% {
    box-shadow: 0 0 0 4px transparent;
    opacity: 0.8;
  }
  100% {
    box-shadow: 0 0 0 0 transparent;
    opacity: 1;
  }
}

.status-text {
  white-space: nowrap;
}

// 详细信息
.status-details {
  margin-top: var(--space-3);
  padding: var(--space-3);
  background-color: var(--gray-50);
  border-radius: var(--radius-md);
  border: 1px solid var(--gray-200);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-2);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.detail-label {
  font-size: var(--text-xs);
  color: var(--gray-600);
  font-weight: 500;
}

.detail-value {
  font-size: var(--text-xs);
  color: var(--gray-900);
}

// 状态操作
.status-actions {
  margin-top: var(--space-3);
  display: flex;
  gap: var(--space-2);
}

// 状态历史
.status-history {
  margin-top: var(--space-4);
}

.history-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: var(--space-3);
}

.history-timeline {
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    left: 6px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, var(--gray-300), var(--gray-200));
  }
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  position: relative;

  &:last-child {
    margin-bottom: 0;
    
    &::after {
      display: none;
    }
  }
}

.history-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
  z-index: 1;

  &.online {
    background-color: var(--success-500);
  }

  &.offline {
    background-color: var(--gray-500);
  }

  &.awaiting {
    background-color: var(--warning-500);
  }

  &.risk {
    background-color: var(--error-500);
  }

  &.banned {
    background-color: var(--gray-700);
  }
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-status {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--gray-900);
  margin-bottom: var(--space-1);
}

.history-time {
  font-size: var(--text-xs);
  color: var(--gray-500);
  margin-bottom: var(--space-1);
}

.history-reason {
  font-size: var(--text-xs);
  color: var(--gray-600);
  font-style: italic;
}

// 响应式适配
@media (max-width: 768px) {
  .status-badge {
    font-size: var(--text-xs);
    padding: var(--space-1) var(--space-2);
  }

  .status-dot {
    width: 6px;
    height: 6px;
  }

  .status-actions {
    flex-direction: column;
    gap: var(--space-1);
  }

  .detail-item {
    flex-direction: column;
    gap: var(--space-1);
  }
}

// 暗色模式适配
@media (prefers-color-scheme: dark) {
  .status-details {
    background-color: var(--gray-800);
    border-color: var(--gray-700);
  }

  .detail-label {
    color: var(--gray-400);
  }

  .detail-value {
    color: var(--gray-100);
  }

  .history-timeline::before {
    background: linear-gradient(to bottom, var(--gray-600), var(--gray-700));
  }

  .history-status {
    color: var(--gray-100);
  }

  .history-time {
    color: var(--gray-400);
  }

  .history-reason {
    color: var(--gray-300);
  }
}
</style>

