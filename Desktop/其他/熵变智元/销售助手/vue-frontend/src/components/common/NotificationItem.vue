<template>
  <div class="notification-item" :class="type">
    <div class="notification-icon">
      <i :class="iconClass"></i>
    </div>
    <div class="notification-content">
      <div class="notification-title">{{ title }}</div>
      <div class="notification-message">{{ message }}</div>
      <div class="notification-time">{{ formatTime }}</div>
    </div>
    <button class="notification-close" @click="$emit('close')">
      <i class="el-icon-close"></i>
    </button>
  </div>
</template>

<script>
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'NotificationItem',
  props: {
    id: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: value => ['info', 'success', 'warning', 'error'].includes(value)
    },
    timestamp: {
      type: Date,
      default: () => new Date()
    }
  },
  emits: ['close'],
  setup(props) {
    const iconClass = computed(() => {
      const icons = {
        info: 'el-icon-info',
        success: 'el-icon-success',
        warning: 'el-icon-warning',
        error: 'el-icon-error'
      }
      return icons[props.type] || icons.info
    })

    const formatTime = computed(() => {
      return formatDistanceToNow(props.timestamp, { 
        addSuffix: true, 
        locale: zhCN 
      })
    })

    return {
      iconClass,
      formatTime
    }
  }
}
</script>

<style lang="scss" scoped>
.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border-radius: var(--border-radius);
  background: var(--card-bg);
  box-shadow: var(--shadow);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }
  
  &.info {
    border-left: 4px solid var(--info-color);
  }
  
  &.success {
    border-left: 4px solid var(--success-color);
  }
  
  &.warning {
    border-left: 4px solid var(--warning-color);
  }
  
  &.error {
    border-left: 4px solid var(--danger-color);
  }
}

.notification-icon {
  margin-right: 0.75rem;
  margin-top: 0.125rem;
  
  i {
    font-size: 1.25rem;
    
    &.el-icon-info {
      color: var(--info-color);
    }
    
    &.el-icon-success {
      color: var(--success-color);
    }
    
    &.el-icon-warning {
      color: var(--warning-color);
    }
    
    &.el-icon-error {
      color: var(--danger-color);
    }
  }
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.notification-message {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.notification-time {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.notification-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.25rem;
  margin-left: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--bg-hover);
    color: var(--text-color);
  }
  
  i {
    font-size: 0.875rem;
  }
}
</style>
