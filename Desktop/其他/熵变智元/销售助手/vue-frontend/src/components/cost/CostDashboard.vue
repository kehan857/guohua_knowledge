<template>
  <div class="cost-dashboard">
    <!-- 头部总览 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="header-info">
          <h2 class="dashboard-title">💰 算力管理中心</h2>
          <p class="dashboard-subtitle">实时监控AI成本消耗，智能预算管理</p>
        </div>
        <div class="header-actions">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :shortcuts="dateShortcuts"
            @change="handleDateChange"
          />
          <el-button :icon="Refresh" @click="refreshData" :loading="refreshing">
            刷新数据
          </el-button>
          <el-button type="primary" :icon="Document" @click="exportReport">
            导出报告
          </el-button>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-overview">
      <div class="metrics-grid">
        <MetricCard
          title="本月总消耗"
          :value="formatCurrency(monthlyStats.totalCost)"
          :trend="monthlyStats.costTrend"
          trend-type="warning"
          icon="💸"
          :subtitle="`预算: ${formatCurrency(monthlyStats.budget)}`"
          :progress="monthlyStats.budgetUsage"
        />
        <MetricCard
          title="今日消耗"
          :value="formatCurrency(dailyStats.todayCost)"
          :trend="dailyStats.costTrend"
          trend-type="info"
          icon="el-icon-money"
          :subtitle="`昨日: ${formatCurrency(dailyStats.yesterdayCost)}`"
        />
        <MetricCard
          title="API调用次数"
          :value="formatNumber(usageStats.totalCalls)"
          :trend="usageStats.callsTrend"
          trend-type="positive"
          icon="el-icon-refresh"
          :subtitle="`成功率: ${usageStats.successRate}%`"
        />
        <MetricCard
          title="平均成本"
          :value="formatCurrency(usageStats.avgCostPerCall)"
          :trend="usageStats.avgCostTrend"
          trend-type="neutral"
          icon="el-icon-balance-scale"
          :subtitle="`每1K Token: ${formatCurrency(usageStats.avgCostPer1K)}`"
        />
      </div>
    </div>

    <!-- 图表分析区域 -->
    <div class="charts-section">
      <div class="charts-grid">
        <!-- 成本趋势图 -->
        <ChartCard
          title="成本趋势分析"
          :controls="periodControls"
          class="chart-trend"
        >
          <CostTrendChart
            :data="trendData"
            :period="selectedPeriod"
            @period-change="handlePeriodChange"
          />
        </ChartCard>

        <!-- 模型使用分布 -->
        <ChartCard
          title="模型使用分布"
          :actions="modelActions"
          class="chart-models"
        >
          <ModelUsageChart
            :data="modelUsageData"
            @model-click="handleModelClick"
          />
        </ChartCard>

        <!-- 成本预警 -->
        <ChartCard
          title="预算预警"
          :actions="alertActions"
          class="chart-alerts"
        >
          <BudgetAlertPanel
            :alerts="budgetAlerts"
            @handle-alert="handleBudgetAlert"
          />
        </ChartCard>

        <!-- 用户排行 -->
        <ChartCard
          title="用户消耗排行"
          :actions="rankingActions"
          class="chart-ranking"
        >
          <UserCostRanking
            :data="userRankingData"
            :period="selectedPeriod"
            @user-click="handleUserClick"
          />
        </ChartCard>
      </div>
    </div>

    <!-- 详细数据表格 -->
    <div class="data-tables-section">
      <el-tabs v-model="activeTab" class="data-tabs">
        <!-- 用户配额管理 -->
        <el-tab-pane label="用户配额" name="users">
          <UserQuotaTable
            :users="usersData"
            :loading="usersLoading"
            @quota-change="handleQuotaChange"
            @user-details="handleUserDetails"
          />
        </el-tab-pane>

        <!-- 成本明细 -->
        <el-tab-pane label="成本明细" name="details">
          <CostDetailsTable
            :records="costRecords"
            :loading="recordsLoading"
            :filters="detailFilters"
            @filter-change="handleDetailFilterChange"
            @record-click="handleRecordClick"
          />
        </el-tab-pane>

        <!-- 模型配置 -->
        <el-tab-pane label="模型配置" name="models">
          <ModelConfigTable
            :models="modelsConfig"
            :loading="modelsLoading"
            @price-update="handlePriceUpdate"
            @model-toggle="handleModelToggle"
          />
        </el-tab-pane>

        <!-- 预算设置 -->
        <el-tab-pane label="预算设置" name="budgets">
          <BudgetConfigPanel
            :budgets="budgetConfig"
            :loading="budgetLoading"
            @budget-update="handleBudgetUpdate"
            @alert-config="handleAlertConfig"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 实时监控面板 -->
    <div v-if="showRealTimePanel" class="realtime-panel">
      <RealtimeMonitor
        :data="realtimeData"
        @close="showRealTimePanel = false"
      />
    </div>

    <!-- 成本详情抽屉 -->
    <CostDetailsDrawer
      v-model="detailsDrawerVisible"
      :record="selectedRecord"
      @update="refreshData"
    />

    <!-- 用户详情模态框 -->
    <UserDetailsModal
      v-model="userModalVisible"
      :user="selectedUser"
      @update="refreshUserData"
    />

    <!-- 预算配置模态框 -->
    <BudgetConfigModal
      v-model="budgetModalVisible"
      :config="budgetModalConfig"
      @save="handleBudgetSave"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Refresh, Document, Download, Settings } from '@element-plus/icons-vue'

// 组件导入
import MetricCard from '@/components/dashboard/MetricCard.vue'
import ChartCard from '@/components/dashboard/ChartCard.vue'
import CostTrendChart from './CostTrendChart.vue'
import ModelUsageChart from './ModelUsageChart.vue'
import BudgetAlertPanel from './BudgetAlertPanel.vue'
import UserCostRanking from './UserCostRanking.vue'
import UserQuotaTable from './UserQuotaTable.vue'
import CostDetailsTable from './CostDetailsTable.vue'
import ModelConfigTable from './ModelConfigTable.vue'
import BudgetConfigPanel from './BudgetConfigPanel.vue'
import RealtimeMonitor from './RealtimeMonitor.vue'
import CostDetailsDrawer from './CostDetailsDrawer.vue'
import UserDetailsModal from './UserDetailsModal.vue'
import BudgetConfigModal from './BudgetConfigModal.vue'

export default {
  name: 'CostDashboard',
  components: {
    MetricCard,
    ChartCard,
    CostTrendChart,
    ModelUsageChart,
    BudgetAlertPanel,
    UserCostRanking,
    UserQuotaTable,
    CostDetailsTable,
    ModelConfigTable,
    BudgetConfigPanel,
    RealtimeMonitor,
    CostDetailsDrawer,
    UserDetailsModal,
    BudgetConfigModal,
    Refresh,
    Document,
    Download,
    Settings
  },

  setup() {
    const store = useStore()

    // 响应式数据
    const refreshing = ref(false)
    const dateRange = ref([
      new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      new Date()
    ])
    const selectedPeriod = ref('30d')
    const activeTab = ref('users')
    const showRealTimePanel = ref(false)
    const detailsDrawerVisible = ref(false)
    const userModalVisible = ref(false)
    const budgetModalVisible = ref(false)
    const selectedRecord = ref(null)
    const selectedUser = ref(null)
    const budgetModalConfig = ref(null)

    // 加载状态
    const usersLoading = ref(false)
    const recordsLoading = ref(false)
    const modelsLoading = ref(false)
    const budgetLoading = ref(false)

    // 筛选条件
    const detailFilters = ref({
      userId: '',
      modelName: '',
      dateRange: null
    })

    // 计算属性
    const monthlyStats = computed(() => store.state.cost.monthlyStats || {})
    const dailyStats = computed(() => store.state.cost.dailyStats || {})
    const usageStats = computed(() => store.state.cost.usageStats || {})
    const trendData = computed(() => store.state.cost.trendData || [])
    const modelUsageData = computed(() => store.state.cost.modelUsageData || [])
    const budgetAlerts = computed(() => store.state.cost.budgetAlerts || [])
    const userRankingData = computed(() => store.state.cost.userRankingData || [])
    const usersData = computed(() => store.state.cost.usersData || [])
    const costRecords = computed(() => store.state.cost.costRecords || [])
    const modelsConfig = computed(() => store.state.cost.modelsConfig || [])
    const budgetConfig = computed(() => store.state.cost.budgetConfig || {})
    const realtimeData = computed(() => store.state.cost.realtimeData || {})

    // 配置项
    const dateShortcuts = [
      {
        text: '最近7天',
        value: () => [
          new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
          new Date()
        ]
      },
      {
        text: '最近30天',
        value: () => [
          new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
          new Date()
        ]
      },
      {
        text: '本月',
        value: () => {
          const now = new Date()
          const start = new Date(now.getFullYear(), now.getMonth(), 1)
          return [start, new Date()]
        }
      },
      {
        text: '上月',
        value: () => {
          const now = new Date()
          const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
          const end = new Date(now.getFullYear(), now.getMonth(), 0)
          return [start, end]
        }
      }
    ]

    const periodControls = [
      { label: '7天', value: '7d' },
      { label: '30天', value: '30d' },
      { label: '90天', value: '90d' }
    ]

    const modelActions = [
      {
        label: '配置模型',
        type: 'text',
        icon: Settings,
        onClick: () => activeTab.value = 'models'
      }
    ]

    const alertActions = [
      {
        label: '配置预警',
        type: 'text',
        onClick: () => budgetModalVisible.value = true
      }
    ]

    const rankingActions = [
      {
        label: '查看详情',
        type: 'text',
        onClick: () => activeTab.value = 'users'
      }
    ]

    // 方法
    const refreshData = async () => {
      refreshing.value = true
      try {
        await Promise.all([
          store.dispatch('cost/fetchDashboardStats', {
            startDate: dateRange.value[0],
            endDate: dateRange.value[1]
          }),
          store.dispatch('cost/fetchTrendData', { period: selectedPeriod.value }),
          store.dispatch('cost/fetchModelUsageData'),
          store.dispatch('cost/fetchBudgetAlerts'),
          store.dispatch('cost/fetchUserRanking', { period: selectedPeriod.value })
        ])
      } catch (error) {
        ElMessage.error('数据加载失败: ' + error.message)
      } finally {
        refreshing.value = false
      }
    }

    const handleDateChange = (dates) => {
      if (dates && dates.length === 2) {
        refreshData()
      }
    }

    const handlePeriodChange = (period) => {
      selectedPeriod.value = period
      store.dispatch('cost/fetchTrendData', { period })
      store.dispatch('cost/fetchUserRanking', { period })
    }

    const exportReport = async () => {
      try {
        const reportData = await store.dispatch('cost/generateReport', {
          startDate: dateRange.value[0],
          endDate: dateRange.value[1],
          period: selectedPeriod.value
        })
        
        // 创建下载链接
        const blob = new Blob([JSON.stringify(reportData, null, 2)], {
          type: 'application/json'
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `cost-report-${new Date().toISOString().split('T')[0]}.json`
        a.click()
        URL.revokeObjectURL(url)
        
        ElMessage.success('报告导出成功')
      } catch (error) {
        ElMessage.error('报告导出失败: ' + error.message)
      }
    }

    const handleModelClick = (model) => {
      // 显示模型详细使用情况
      store.dispatch('cost/fetchModelDetails', model.name)
      activeTab.value = 'details'
      detailFilters.value.modelName = model.name
    }

    const handleUserClick = (user) => {
      selectedUser.value = user
      userModalVisible.value = true
    }

    const handleBudgetAlert = async (alert) => {
      try {
        await store.dispatch('cost/handleBudgetAlert', {
          alertId: alert.id,
          action: 'acknowledge'
        })
        ElMessage.success('预警已处理')
        refreshData()
      } catch (error) {
        ElMessage.error('处理失败: ' + error.message)
      }
    }

    const handleQuotaChange = async (userId, newQuota) => {
      try {
        await store.dispatch('cost/updateUserQuota', {
          userId,
          quota: newQuota
        })
        ElMessage.success('配额更新成功')
        refreshUserData()
      } catch (error) {
        ElMessage.error('配额更新失败: ' + error.message)
      }
    }

    const handleUserDetails = (user) => {
      selectedUser.value = user
      userModalVisible.value = true
    }

    const handleDetailFilterChange = (filters) => {
      detailFilters.value = { ...filters }
      loadCostRecords()
    }

    const handleRecordClick = (record) => {
      selectedRecord.value = record
      detailsDrawerVisible.value = true
    }

    const handlePriceUpdate = async (modelId, newPrice) => {
      try {
        await store.dispatch('cost/updateModelPrice', {
          modelId,
          price: newPrice
        })
        ElMessage.success('模型价格更新成功')
        loadModelsConfig()
      } catch (error) {
        ElMessage.error('价格更新失败: ' + error.message)
      }
    }

    const handleModelToggle = async (modelId, enabled) => {
      try {
        await store.dispatch('cost/toggleModel', {
          modelId,
          enabled
        })
        ElMessage.success(`模型已${enabled ? '启用' : '禁用'}`)
        loadModelsConfig()
      } catch (error) {
        ElMessage.error('操作失败: ' + error.message)
      }
    }

    const handleBudgetUpdate = async (config) => {
      try {
        await store.dispatch('cost/updateBudgetConfig', config)
        ElMessage.success('预算配置更新成功')
        loadBudgetConfig()
      } catch (error) {
        ElMessage.error('配置更新失败: ' + error.message)
      }
    }

    const handleAlertConfig = () => {
      budgetModalConfig.value = { ...budgetConfig.value }
      budgetModalVisible.value = true
    }

    const handleBudgetSave = async (config) => {
      try {
        await store.dispatch('cost/saveBudgetConfig', config)
        ElMessage.success('预算配置保存成功')
        budgetModalVisible.value = false
        loadBudgetConfig()
      } catch (error) {
        ElMessage.error('配置保存失败: ' + error.message)
      }
    }

    const refreshUserData = () => {
      loadUsersData()
    }

    // 数据加载方法
    const loadUsersData = async () => {
      usersLoading.value = true
      try {
        await store.dispatch('cost/fetchUsersData')
      } finally {
        usersLoading.value = false
      }
    }

    const loadCostRecords = async () => {
      recordsLoading.value = true
      try {
        await store.dispatch('cost/fetchCostRecords', detailFilters.value)
      } finally {
        recordsLoading.value = false
      }
    }

    const loadModelsConfig = async () => {
      modelsLoading.value = true
      try {
        await store.dispatch('cost/fetchModelsConfig')
      } finally {
        modelsLoading.value = false
      }
    }

    const loadBudgetConfig = async () => {
      budgetLoading.value = true
      try {
        await store.dispatch('cost/fetchBudgetConfig')
      } finally {
        budgetLoading.value = false
      }
    }

    // 格式化函数
    const formatCurrency = (amount) => {
      if (typeof amount !== 'number') return '¥0.00'
      return `¥${amount.toFixed(2)}`
    }

    const formatNumber = (num) => {
      if (typeof num !== 'number') return '0'
      return num.toLocaleString()
    }

    // 监听tab变化，加载对应数据
    watch(activeTab, (newTab) => {
      switch (newTab) {
        case 'users':
          loadUsersData()
          break
        case 'details':
          loadCostRecords()
          break
        case 'models':
          loadModelsConfig()
          break
        case 'budgets':
          loadBudgetConfig()
          break
      }
    })

    // 生命周期
    onMounted(() => {
      refreshData()
      loadUsersData()
    })

    return {
      // 数据
      refreshing,
      dateRange,
      selectedPeriod,
      activeTab,
      showRealTimePanel,
      detailsDrawerVisible,
      userModalVisible,
      budgetModalVisible,
      selectedRecord,
      selectedUser,
      budgetModalConfig,
      usersLoading,
      recordsLoading,
      modelsLoading,
      budgetLoading,
      detailFilters,
      
      // 计算属性
      monthlyStats,
      dailyStats,
      usageStats,
      trendData,
      modelUsageData,
      budgetAlerts,
      userRankingData,
      usersData,
      costRecords,
      modelsConfig,
      budgetConfig,
      realtimeData,
      
      // 配置
      dateShortcuts,
      periodControls,
      modelActions,
      alertActions,
      rankingActions,
      
      // 方法
      refreshData,
      handleDateChange,
      handlePeriodChange,
      exportReport,
      handleModelClick,
      handleUserClick,
      handleBudgetAlert,
      handleQuotaChange,
      handleUserDetails,
      handleDetailFilterChange,
      handleRecordClick,
      handlePriceUpdate,
      handleModelToggle,
      handleBudgetUpdate,
      handleAlertConfig,
      handleBudgetSave,
      refreshUserData,
      formatCurrency,
      formatNumber
    }
  }
}
</script>

<style lang="scss" scoped>
.cost-dashboard {
  padding: var(--space-6);
  background-color: var(--gray-50);
  min-height: calc(100vh - var(--header-height));
}

// 头部区域
.dashboard-header {
  margin-bottom: var(--space-8);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: var(--space-6);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

.header-info {
  flex: 1;
}

.dashboard-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dashboard-subtitle {
  color: var(--gray-600);
  font-size: var(--text-base);
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

// 指标总览
.metrics-overview {
  margin-bottom: var(--space-8);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

// 图表区域
.charts-section {
  margin-bottom: var(--space-8);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--space-6);
}

.chart-trend {
  grid-column: span 2;
}

// 数据表格区域
.data-tables-section {
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.data-tabs {
  :deep(.el-tabs__header) {
    padding: 0 var(--space-6);
    margin: 0;
    background-color: var(--gray-50);
    border-bottom: 1px solid var(--gray-200);
  }
  
  :deep(.el-tabs__content) {
    padding: var(--space-6);
  }
  
  :deep(.el-tab-pane) {
    min-height: 400px;
  }
}

// 实时监控面板
.realtime-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  z-index: var(--z-modal);
  background: white;
  box-shadow: var(--shadow-xl);
  border-left: 1px solid var(--gray-200);
  transform: translateX(100%);
  transition: transform var(--transition-normal);
  
  &.show {
    transform: translateX(0);
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-trend {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .cost-dashboard {
    padding: var(--space-4);
  }
  
  .header-content {
    flex-direction: column;
    gap: var(--space-4);
    align-items: stretch;
  }
  
  .header-actions {
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
  
  .realtime-panel {
    width: 100%;
    top: var(--header-height);
    height: calc(100vh - var(--header-height));
  }
}

// 动画效果
.cost-dashboard {
  animation: fadeInUp var(--duration-normal) var(--ease-out-cubic);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 加载状态
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

// 悬停效果
.metrics-grid > *,
.charts-grid > * {
  transition: all var(--transition-fast);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }
}
</style>

