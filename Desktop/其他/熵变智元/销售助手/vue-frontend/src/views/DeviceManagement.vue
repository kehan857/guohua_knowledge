<template>
  <div class="device-management">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button type="primary" @click="addDevice">
        <i class="el-icon-plus"></i>
        添加设备
      </el-button>
    </div>
    
    <div class="device-content">
      <el-row :gutter="20">
        <el-col :span="8" v-for="device in devices" :key="device.id">
          <div class="device-card" :class="device.status">
            <div class="device-header">
              <div class="device-avatar">
                <img :src="device.avatar" :alt="device.name" />
                <div class="status-indicator" :class="device.status"></div>
              </div>
              <div class="device-info">
                <h4>{{ device.name }}</h4>
                <p>{{ device.description }}</p>
              </div>
            </div>
            <div class="device-stats">
              <div class="stat-item">
                <span class="stat-label">在线时长</span>
                <span class="stat-value">{{ device.uptime }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">消息数</span>
                <span class="stat-value">{{ device.messageCount }}</span>
              </div>
            </div>
            <div class="device-actions">
              <el-button size="small" @click="viewDevice(device)">查看</el-button>
              <el-button size="small" @click="editDevice(device)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeDevice(device)">移除</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'DeviceManagement',
  setup() {
    const devices = ref([
      {
        id: 1,
        name: '张经理微信',
        description: '主要销售账号',
        avatar: '/images/avatar1.jpg',
        status: 'online',
        uptime: '2小时30分',
        messageCount: 156
      },
      {
        id: 2,
        name: '李助理微信',
        description: '客服账号',
        avatar: '/images/avatar2.jpg',
        status: 'offline',
        uptime: '0小时0分',
        messageCount: 89
      },
      {
        id: 3,
        name: '王总监微信',
        description: '管理层账号',
        avatar: '/images/avatar3.jpg',
        status: 'online',
        uptime: '1小时45分',
        messageCount: 234
      }
    ])
    
    const addDevice = () => {
      // 添加设备逻辑
    }
    
    const viewDevice = (device) => {
      // 查看设备详情逻辑
    }
    
    const editDevice = (device) => {
      // 编辑设备逻辑
    }
    
    const removeDevice = (device) => {
      // 移除设备逻辑
    }
    
    return {
      devices,
      addDevice,
      viewDevice,
      editDevice,
      removeDevice
    }
  }
}
</script>

<style lang="scss" scoped>
.device-management {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  h2 {
    margin: 0;
    color: var(--text-color);
  }
}

.device-card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow);
  border: 2px solid transparent;
  
  &.online {
    border-color: var(--success-color);
  }
  
  &.offline {
    border-color: var(--danger-color);
  }
}

.device-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.device-avatar {
  position: relative;
  margin-right: 1rem;
  
  img {
    width: 3rem;
    height: 3rem;
    border-radius: 50%;
    object-fit: cover;
  }
  
  .status-indicator {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 50%;
    border: 2px solid white;
    
    &.online {
      background: var(--success-color);
    }
    
    &.offline {
      background: var(--danger-color);
    }
  }
}

.device-info {
  h4 {
    margin: 0 0 0.25rem 0;
    color: var(--text-color);
  }
  
  p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
}

.device-stats {
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  
  .stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .stat-value {
    font-weight: 600;
    color: var(--text-color);
  }
}

.device-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
