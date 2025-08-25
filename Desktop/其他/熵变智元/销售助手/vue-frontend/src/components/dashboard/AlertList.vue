<template>
  <div class="alert-list">
    <div class="list-header">
      <h4>系统告警</h4>
      <el-button size="small" @click="markAllRead">
        <i class="el-icon-check"></i>
        全部已读
      </el-button>
    </div>
    <div class="list-content">
      <div 
        v-for="alert in alerts" 
        :key="alert.id"
        class="alert-item"
        :class="alert.level"
      >
        <div class="alert-icon">
          <i :class="getAlertIcon(alert.level)"></i>
        </div>
        <div class="alert-content">
          <div class="alert-title">{{ alert.title }}</div>
          <div class="alert-message">{{ alert.message }}</div>
          <div class="alert-time">{{ formatTime(alert.timestamp) }}</div>
        </div>
        <div class="alert-actions">
          <el-button 
            size="mini" 
            @click="markRead(alert.id)"
            v-if="!alert.read"
          >
            已读
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default {
  name: 'AlertList',
  setup() {
    const alerts = ref([
      {
        id: 1,
        title: 'API调用频率过高',
        message: 'GPT-4 API调用频率超过限制，请检查配置',
        level: 'warning',
        timestamp: new Date(Date.now() - 1000 * 60 * 30),
        read: false
      },
      {
        id: 2,
        title: '设备离线',
        message: '微信账号"张经理"已离线超过10分钟',
        level: 'error',
        timestamp: new Date(Date.now() - 1000 * 60 * 60),
        read: false
      },
      {
        id: 3,
        title: '成本预警',
        message: '本月AI成本已超过预算的80%',
        level: 'info',
        timestamp: new Date(Date.now() - 1000 * 60 * 120),
        read: true
      }
    ])
    
    const getAlertIcon = (level) => {
      const icons = {
        info: 'el-icon-info',
        warning: 'el-icon-warning',
        error: 'el-icon-error',
        success: 'el-icon-success'
      }
      return icons[level] || icons.info
    }
    
    const formatTime = (timestamp) => {
      return formatDistanceToNow(timestamp, { 
        addSuffix: true, 
        locale: zhCN 
      })
    }
    
    const markRead = (id) => {
      const alert = alerts.value.find(a => a.id === id)
      if (alert) {
        alert.read = true
      }
    }
    
    const markAllRead = () => {
      alerts.value.forEach(alert => {
        alert.read = true
      })
    }
    
    return {
      alerts,
      getAlertIcon,
      formatTime,
      markRead,
      markAllRead
    }
  }
}
</script>

<style lang="scss" scoped>
.alert-list {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  
  h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
  }
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: var(--border-radius);
  border-left: 4px solid;
  
  &.info {
    background: rgba(59, 130, 246, 0.1);
    border-left-color: var(--info-color);
  }
  
  &.warning {
    background: rgba(245, 158, 11, 0.1);
    border-left-color: var(--warning-color);
  }
  
  &.error {
    background: rgba(239, 68, 68, 0.1);
    border-left-color: var(--danger-color);
  }
  
  &.success {
    background: rgba(16, 185, 129, 0.1);
    border-left-color: var(--success-color);
  }
}

.alert-icon {
  margin-right: 0.75rem;
  margin-top: 0.125rem;
  
  i {
    font-size: 1.25rem;
    
    &.el-icon-info {
      color: var(--info-color);
    }
    
    &.el-icon-warning {
      color: var(--warning-color);
    }
    
    &.el-icon-error {
      color: var(--danger-color);
    }
    
    &.el-icon-success {
      color: var(--success-color);
    }
  }
}

.alert-content {
  flex: 1;
  margin-right: 0.75rem;
}

.alert-title {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.alert-message {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.alert-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.alert-actions {
  flex-shrink: 0;
}
</style>
