<template>
  <div class="device-status-monitor">
    <!-- 设备状态总览 -->
    <div class="status-overview">
      <div class="overview-cards">
        <div
          v-for="stat in statusStats"
          :key="stat.status"
          class="status-card"
          :class="stat.status.toLowerCase()"
        >
          <div class="card-icon">
            <el-icon :size="24">
              <component :is="stat.icon" />
            </el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ stat.count }}</div>
            <div class="card-label">{{ stat.label }}</div>
          </div>
          <div class="card-indicator" :class="stat.status.toLowerCase()"></div>
        </div>
      </div>
    </div>

    <!-- 设备列表 -->
    <div class="device-list-container">
      <div class="list-header">
        <div class="header-title">
          <h3>设备监控列表</h3>
          <el-badge :value="alertCount" :hidden="alertCount === 0">
            <el-button type="text" :icon="Warning" @click="showAlerts">
              异常告警
            </el-button>
          </el-badge>
        </div>
        
        <div class="header-actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索设备..."
            :prefix-icon="Search"
            clearable
            style="width: 200px;"
          />
          <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px;">
            <el-option label="全部" value="all" />
            <el-option label="在线" value="ONLINE" />
            <el-option label="离线" value="OFFLINE" />
            <el-option label="异常" value="ERROR" />
          </el-select>
          <el-button :icon="Refresh" @click="refreshDevices" :loading="refreshing">
            刷新
          </el-button>
        </div>
      </div>

      <!-- 设备表格 -->
      <el-table
        :data="filteredDevices"
        v-loading="loading"
        row-key="id"
        class="device-table"
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
      >
        <el-table-column type="selection" width="50" />
        
        <el-table-column label="设备信息" min-width="200">
          <template #default="{ row }">
            <div class="device-info">
              <el-avatar :src="row.avatar" :size="40">
                {{ row.nickname?.charAt(0) || '?' }}
              </el-avatar>
              <div class="device-details">
                <div class="device-name">{{ row.nickname || '未知设备' }}</div>
                <div class="device-id">{{ row.wxid }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="归属员工" prop="ownerName" width="120" />

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <DeviceStatusIndicator :status="row.status" :last-seen="row.lastSeenAt" />
          </template>
        </el-table-column>

        <el-table-column label="网络信息" width="150">
          <template #default="{ row }">
            <div class="network-info">
              <div class="ip-address">{{ formatIPAddress(row.ipAddress) }}</div>
              <div class="location">{{ row.location || '未知位置' }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="上线时长" width="120">
          <template #default="{ row }">
            <div class="uptime">
              {{ formatUptime(row.onlineTime) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最后活跃" width="140">
          <template #default="{ row }">
            <div class="last-active">
              {{ formatLastActive(row.lastActiveAt) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.status === 'OFFLINE' || row.status === 'AWAITING_RELOGIN'"
                type="primary"
                size="small"
                :icon="QrCode"
                @click.stop="getQRCode(row)"
              >
                获取二维码
              </el-button>
              
              <el-button
                v-if="row.status === 'ONLINE'"
                type="warning"
                size="small"
                :icon="PowerOff"
                @click.stop="forceOffline(row)"
              >
                强制下线
              </el-button>

              <el-dropdown @command="(command) => handleDeviceAction(command, row)">
                <el-button type="text" :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="logs">
                      <el-icon><Document /></el-icon>
                      查看日志
                    </el-dropdown-item>
                    <el-dropdown-item command="details">
                      <el-icon><View /></el-icon>
                      设备详情
                    </el-dropdown-item>
                    <el-dropdown-item command="edit">
                      <el-icon><Edit /></el-icon>
                      编辑设备
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除设备
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalDevices"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedDevices.length > 0" class="batch-actions">
      <div class="batch-info">
        已选择 {{ selectedDevices.length }} 个设备
      </div>
      <div class="batch-buttons">
        <el-button @click="clearSelection">取消选择</el-button>
        <el-button type="primary" @click="batchReconnect">批量重连</el-button>
        <el-button type="warning" @click="batchOffline">批量下线</el-button>
        <el-button type="danger" @click="batchDelete">批量删除</el-button>
      </div>
    </div>

    <!-- 二维码模态框 -->
    <QRCodeModal
      v-model="qrCodeModalVisible"
      :device="currentDevice"
      @success="handleQRCodeSuccess"
    />

    <!-- 设备详情抽屉 -->
    <DeviceDetailsDrawer
      v-model="detailsDrawerVisible"
      :device="currentDevice"
      @update="handleDeviceUpdate"
    />

    <!-- 日志查看器 -->
    <DeviceLogsModal
      v-model="logsModalVisible"
      :device="currentDevice"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Warning,
  QrCode,
  PowerOff,
  MoreFilled,
  Document,
  View,
  Edit,
  Delete,
  Phone,
  WifiOff,
  Clock,
  AlertTriangle
} from '@element-plus/icons-vue'

import DeviceStatusIndicator from './DeviceStatusIndicator.vue'
import QRCodeModal from './QRCodeModal.vue'
import DeviceDetailsDrawer from './DeviceDetailsDrawer.vue'
import DeviceLogsModal from './DeviceLogsModal.vue'

export default {
  name: 'DeviceStatusMonitor',
  components: {
    DeviceStatusIndicator,
    QRCodeModal,
    DeviceDetailsDrawer,
    DeviceLogsModal,
    Search,
    Refresh,
    Warning,
    QrCode,
    PowerOff,
    MoreFilled,
    Document,
    View,
    Edit,
    Delete
  },

  setup() {
    const store = useStore()

    // 响应式数据
    const loading = ref(false)
    const refreshing = ref(false)
    const searchQuery = ref('')
    const statusFilter = ref('all')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const selectedDevices = ref([])
    const qrCodeModalVisible = ref(false)
    const detailsDrawerVisible = ref(false)
    const logsModalVisible = ref(false)
    const currentDevice = ref(null)
    const refreshTimer = ref(null)

    // 计算属性
    const devices = computed(() => store.state.devices.list || [])
    const totalDevices = computed(() => store.state.devices.total || 0)

    const filteredDevices = computed(() => {
      let result = [...devices.value]

      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(device =>
          device.nickname?.toLowerCase().includes(query) ||
          device.wxid?.toLowerCase().includes(query) ||
          device.ownerName?.toLowerCase().includes(query)
        )
      }

      // 状态过滤
      if (statusFilter.value !== 'all') {
        result = result.filter(device => device.status === statusFilter.value)
      }

      return result
    })

    const statusStats = computed(() => {
      const stats = devices.value.reduce((acc, device) => {
        acc[device.status] = (acc[device.status] || 0) + 1
        return acc
      }, {})

      return [
        {
          status: 'ONLINE',
          label: '在线设备',
          count: stats.ONLINE || 0,
          icon: Phone
        },
        {
          status: 'OFFLINE',
          label: '离线设备',
          count: stats.OFFLINE || 0,
          icon: WifiOff
        },
        {
          status: 'AWAITING_RELOGIN',
          label: '等待登录',
          count: stats.AWAITING_RELOGIN || 0,
          icon: Clock
        },
        {
          status: 'ERROR',
          label: '异常设备',
          count: (stats.RISK_CONTROLLED || 0) + (stats.BANNED || 0),
          icon: AlertTriangle
        }
      ]
    })

    const alertCount = computed(() => 
      devices.value.filter(device => 
        device.status === 'RISK_CONTROLLED' || 
        device.status === 'BANNED' ||
        device.hasAlert
      ).length
    )

    // 方法
    const loadDevices = async (showLoading = true) => {
      try {
        if (showLoading) loading.value = true

        await store.dispatch('devices/fetchDevices', {
          page: currentPage.value,
          size: pageSize.value,
          search: searchQuery.value,
          status: statusFilter.value !== 'all' ? statusFilter.value : undefined
        })
      } catch (error) {
        ElMessage.error('设备数据加载失败: ' + error.message)
      } finally {
        if (showLoading) loading.value = false
      }
    }

    const refreshDevices = async () => {
      refreshing.value = true
      try {
        await loadDevices(false)
        ElMessage.success('设备状态已刷新')
      } finally {
        refreshing.value = false
      }
    }

    const handleSelectionChange = (selection) => {
      selectedDevices.value = selection
    }

    const handleRowClick = (row) => {
      currentDevice.value = row
      detailsDrawerVisible.value = true
    }

    const handleSizeChange = (size) => {
      pageSize.value = size
      loadDevices()
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadDevices()
    }

    const getQRCode = (device) => {
      currentDevice.value = device
      qrCodeModalVisible.value = true
    }

    const forceOffline = async (device) => {
      try {
        await ElMessageBox.confirm(
          `确定要强制下线设备"${device.nickname}"吗？`,
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await store.dispatch('devices/forceOffline', device.id)
        ElMessage.success('设备已强制下线')
        await refreshDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败: ' + error.message)
        }
      }
    }

    const handleDeviceAction = (command, device) => {
      currentDevice.value = device

      switch (command) {
        case 'logs':
          logsModalVisible.value = true
          break
        case 'details':
          detailsDrawerVisible.value = true
          break
        case 'edit':
          // 编辑设备信息
          break
        case 'delete':
          deleteDevice(device)
          break
      }
    }

    const deleteDevice = async (device) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除设备"${device.nickname}"吗？删除后将无法恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await store.dispatch('devices/deleteDevice', device.id)
        ElMessage.success('设备已删除')
        await loadDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }

    const clearSelection = () => {
      selectedDevices.value = []
    }

    const batchReconnect = async () => {
      try {
        const deviceIds = selectedDevices.value.map(d => d.id)
        await store.dispatch('devices/batchReconnect', deviceIds)
        ElMessage.success(`已向 ${deviceIds.length} 个设备发送重连指令`)
        clearSelection()
        await refreshDevices()
      } catch (error) {
        ElMessage.error('批量重连失败: ' + error.message)
      }
    }

    const batchOffline = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要批量下线 ${selectedDevices.value.length} 个设备吗？`,
          '确认操作',
          { type: 'warning' }
        )

        const deviceIds = selectedDevices.value.map(d => d.id)
        await store.dispatch('devices/batchOffline', deviceIds)
        ElMessage.success(`已成功下线 ${deviceIds.length} 个设备`)
        clearSelection()
        await refreshDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量下线失败: ' + error.message)
        }
      }
    }

    const batchDelete = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要批量删除 ${selectedDevices.value.length} 个设备吗？删除后将无法恢复。`,
          '确认删除',
          { 
            type: 'warning',
            confirmButtonText: '确定删除',
            confirmButtonClass: 'el-button--danger'
          }
        )

        const deviceIds = selectedDevices.value.map(d => d.id)
        await store.dispatch('devices/batchDelete', deviceIds)
        ElMessage.success(`已成功删除 ${deviceIds.length} 个设备`)
        clearSelection()
        await loadDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量删除失败: ' + error.message)
        }
      }
    }

    const showAlerts = () => {
      // 显示异常告警详情
      const alertDevices = devices.value.filter(device => 
        device.status === 'RISK_CONTROLLED' || 
        device.status === 'BANNED' ||
        device.hasAlert
      )
      
      store.dispatch('notifications/showDeviceAlerts', alertDevices)
    }

    const handleQRCodeSuccess = () => {
      ElMessage.success('设备重连成功')
      refreshDevices()
    }

    const handleDeviceUpdate = () => {
      loadDevices()
    }

    // 格式化函数
    const formatIPAddress = (ip) => {
      if (!ip) return '未知'
      return ip.includes(':') ? ip : ip
    }

    const formatUptime = (seconds) => {
      if (!seconds) return '-'
      
      const days = Math.floor(seconds / (24 * 60 * 60))
      const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
      const minutes = Math.floor((seconds % (60 * 60)) / 60)
      
      if (days > 0) {
        return `${days}天${hours}小时`
      } else if (hours > 0) {
        return `${hours}小时${minutes}分钟`
      } else {
        return `${minutes}分钟`
      }
    }

    const formatLastActive = (timestamp) => {
      if (!timestamp) return '从未活跃'
      
      const now = new Date()
      const active = new Date(timestamp)
      const diffMs = now - active
      const diffMins = Math.floor(diffMs / (1000 * 60))
      
      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return `${diffHours}小时前`
      
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays}天前`
    }

    // 自动刷新
    const startAutoRefresh = () => {
      refreshTimer.value = setInterval(() => {
        loadDevices(false)
      }, 30000) // 30秒刷新一次
    }

    const stopAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
        refreshTimer.value = null
      }
    }

    // 监听搜索和筛选变化
    watch([searchQuery, statusFilter], () => {
      currentPage.value = 1
      loadDevices()
    }, { debounce: 500 })

    // 生命周期
    onMounted(() => {
      loadDevices()
      startAutoRefresh()
    })

    onUnmounted(() => {
      stopAutoRefresh()
    })

    return {
      // 数据
      loading,
      refreshing,
      searchQuery,
      statusFilter,
      currentPage,
      pageSize,
      selectedDevices,
      qrCodeModalVisible,
      detailsDrawerVisible,
      logsModalVisible,
      currentDevice,
      
      // 计算属性
      filteredDevices,
      totalDevices,
      statusStats,
      alertCount,
      
      // 方法
      refreshDevices,
      handleSelectionChange,
      handleRowClick,
      handleSizeChange,
      handleCurrentChange,
      getQRCode,
      forceOffline,
      handleDeviceAction,
      clearSelection,
      batchReconnect,
      batchOffline,
      batchDelete,
      showAlerts,
      handleQRCodeSuccess,
      handleDeviceUpdate,
      formatIPAddress,
      formatUptime,
      formatLastActive
    }
  }
}
</script>

<style lang="scss" scoped>
.device-status-monitor {
  padding: var(--space-6);
}

// 状态总览
.status-overview {
  margin-bottom: var(--space-8);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.status-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  border-left: 4px solid var(--gray-300);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;

  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  &.online {
    border-left-color: var(--success-500);
    
    .card-icon {
      color: var(--success-500);
    }
    
    .card-indicator {
      background: linear-gradient(135deg, var(--success-500), var(--success-400));
    }
  }

  &.offline {
    border-left-color: var(--gray-500);
    
    .card-icon {
      color: var(--gray-500);
    }
    
    .card-indicator {
      background: linear-gradient(135deg, var(--gray-500), var(--gray-400));
    }
  }

  &.awaiting_relogin {
    border-left-color: var(--warning-500);
    
    .card-icon {
      color: var(--warning-500);
    }
    
    .card-indicator {
      background: linear-gradient(135deg, var(--warning-500), var(--warning-400));
    }
  }

  &.error {
    border-left-color: var(--error-500);
    
    .card-icon {
      color: var(--error-500);
    }
    
    .card-indicator {
      background: linear-gradient(135deg, var(--error-500), var(--error-400));
    }
  }
}

.card-icon {
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-1);
}

.card-label {
  font-size: var(--text-sm);
  color: var(--gray-600);
}

.card-indicator {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
}

// 设备列表
.device-list-container {
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-6);
  border-bottom: 1px solid var(--gray-200);
  background: white;
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  
  h3 {
    margin: 0;
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--gray-900);
  }
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

// 设备表格
.device-table {
  .device-info {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .device-details {
    flex: 1;
    min-width: 0;
  }

  .device-name {
    font-weight: 600;
    color: var(--gray-900);
    margin-bottom: var(--space-1);
  }

  .device-id {
    font-size: var(--text-xs);
    color: var(--gray-500);
    font-family: var(--font-family-mono);
  }

  .network-info {
    .ip-address {
      font-family: var(--font-family-mono);
      font-size: var(--text-sm);
      color: var(--gray-900);
      margin-bottom: var(--space-1);
    }

    .location {
      font-size: var(--text-xs);
      color: var(--gray-500);
    }
  }

  .uptime,
  .last-active {
    font-size: var(--text-sm);
    color: var(--gray-700);
  }

  .action-buttons {
    display: flex;
    gap: var(--space-2);
    align-items: center;
  }
}

// 分页
.pagination-container {
  padding: var(--space-4) var(--space-6);
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--gray-200);
  background: var(--gray-50);
}

// 批量操作
.batch-actions {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  z-index: 100;
  animation: slideUp var(--transition-normal);
}

.batch-info {
  font-size: var(--text-sm);
  color: var(--gray-600);
  font-weight: 500;
}

.batch-buttons {
  display: flex;
  gap: var(--space-2);
}

// 动画
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

// 响应式适配
@media (max-width: 768px) {
  .device-status-monitor {
    padding: var(--space-4);
  }

  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .list-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
    gap: var(--space-2);
  }

  .device-table {
    :deep(.el-table__body-wrapper) {
      overflow-x: auto;
    }
  }

  .batch-actions {
    position: static;
    transform: none;
    border-radius: 0;
    margin-top: var(--space-4);
    flex-direction: column;
    gap: var(--space-3);
  }

  .batch-buttons {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }

  .status-card {
    padding: var(--space-4);
  }

  .card-value {
    font-size: var(--text-xl);
  }
}
</style>

