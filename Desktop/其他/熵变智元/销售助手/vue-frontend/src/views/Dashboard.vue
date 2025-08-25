<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <PageHeader
      title="主控面板"
      :actions="headerActions"
    />

    <!-- 核心指标卡片 -->
    <section class="metrics-section">
      <div class="metrics-grid">
        <MetricCard
          v-for="metric in metrics"
          :key="metric.id"
          :metric="metric"
          @click="handleMetricClick"
        />
      </div>
    </section>

    <!-- 数据分析区域 -->
    <section class="analytics-section">
      <div class="analytics-grid">
        <!-- 消息趋势图 -->
        <ChartCard
          title="消息量趋势"
          :controls="chartControls"
          class="chart-messages"
        >
          <MessageTrendChart
            :data="messageTrendData"
            :period="selectedPeriod"
            @period-change="handlePeriodChange"
          />
        </ChartCard>

        <!-- 算力消耗排行 -->
        <ChartCard
          title="算力消耗排行"
          :actions="rankingActions"
          class="chart-ranking"
        >
          <CostRankingList
            :data="costRankingData"
            @view-details="handleViewCostDetails"
          />
        </ChartCard>

        <!-- 系统告警 -->
        <ChartCard
          title="系统告警"
          :actions="alertActions"
          class="chart-alerts"
        >
          <AlertList
            :alerts="recentAlerts"
            @handle-alert="handleAlert"
            @view-all="handleViewAllAlerts"
          />
        </ChartCard>

        <!-- 快捷操作 -->
        <ChartCard
          title="快捷操作"
          class="chart-shortcuts"
        >
          <ShortcutPanel
            :shortcuts="shortcuts"
            @shortcut-click="handleShortcutClick"
          />
        </ChartCard>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

// 组件导入
import PageHeader from '@/components/layout/PageHeader.vue'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import ChartCard from '@/components/dashboard/ChartCard.vue'
import MessageTrendChart from '@/components/dashboard/MessageTrendChart.vue'
import CostRankingList from '@/components/dashboard/CostRankingList.vue'
import AlertList from '@/components/dashboard/AlertList.vue'
import ShortcutPanel from '@/components/dashboard/ShortcutPanel.vue'

export default {
  name: 'Dashboard',
  components: {
    PageHeader,
    MetricCard,
    ChartCard,
    MessageTrendChart,
    CostRankingList,
    AlertList,
    ShortcutPanel
  },

  setup() {
    const store = useStore()
    const router = useRouter()

    // 响应式数据
    const selectedPeriod = ref('7days')
    const refreshTimer = ref(null)

    // 计算属性
    const metrics = computed(() => [
      {
        id: 'online-devices',
        title: '在线账号数',
        value: `${store.getters['devices/onlineCount']}/${store.getters['devices/totalCount']}`,
        trend: '+2.3%',
        trendType: 'positive',
        icon: '📱',
        subtitle: '🟢 实时状态',
        route: 'DeviceManagement'
      },
      {
        id: 'messages-today',
        title: '今日消息量',
        value: {
          primary: `收 ${store.state.chat.todayStats.received}`,
          secondary: `发 ${store.state.chat.todayStats.sent}`
        },
        trend: '+15.7%',
        trendType: 'positive',
        icon: '💬',
        subtitle: '📊 增长趋势良好',
        route: 'ChatAggregation'
      },
      {
        id: 'active-tasks',
        title: '进行中任务',
        value: store.getters['sop/activeTasksCount'],
        trend: '持平',
        trendType: 'neutral',
        icon: '📋',
        subtitle: '📈 执行顺利',
        route: 'SOPManagement'
      },
      {
        id: 'monthly-cost',
        title: '本月算力',
        value: `${store.getters['cost/usagePercentage']}%`,
        trend: store.getters['cost/usageProgress'],
        trendType: 'warning',
        icon: '💰',
        subtitle: '💡 使用合理',
        route: 'CostManagement'
      }
    ])

    const messageTrendData = computed(() => store.state.chat.trendData)
    const costRankingData = computed(() => store.state.cost.rankingData)
    const recentAlerts = computed(() => store.getters['notifications/recentAlerts'])

    // 页面操作
    const headerActions = [
      {
        label: '生成报告',
        type: 'default',
        onClick: handleGenerateReport
      },
      {
        label: '快速添加设备',
        type: 'primary',
        onClick: handleQuickAddDevice
      }
    ]

    const chartControls = [
      { label: '7天', value: '7days' },
      { label: '30天', value: '30days' }
    ]

    const rankingActions = [
      {
        label: '查看详情',
        type: 'text',
        onClick: () => router.push('/cost')
      }
    ]

    const alertActions = [
      {
        label: '查看全部',
        type: 'text',
        onClick: handleViewAllAlerts
      }
    ]

    const shortcuts = [
      {
        id: 'get-qr-code',
        icon: 'el-icon-mobile-phone',
        label: '获取登录码',
        onClick: handleGetQRCode
      },
      {
        id: 'create-task',
        icon: 'el-icon-document-add',
        label: '创建任务',
        onClick: handleCreateTask
      },
      {
        id: 'emergency-intervention',
        icon: 'el-icon-warning',
        label: '紧急介入',
        onClick: handleEmergencyIntervention
      },
      {
        id: 'post-moments',
        icon: 'el-icon-picture',
        label: '发朋友圈',
        onClick: () => router.push('/moments')
      }
    ]

    // 方法
    const handleMetricClick = (metric) => {
      if (metric.route) {
        router.push({ name: metric.route })
      }
    }

    const handlePeriodChange = (period) => {
      selectedPeriod.value = period
      loadChartData()
    }

    const handleViewCostDetails = (userId) => {
      router.push({ name: 'CostManagement', query: { userId } })
    }

    const handleAlert = async (alert) => {
      try {
        await store.dispatch('notifications/handleAlert', {
          alertId: alert.id,
          action: 'resolve'
        })
        
        store.dispatch('notifications/addNotification', {
          type: 'success',
          title: '告警处理成功',
          message: `告警 "${alert.title}" 已被标记为已处理`
        })
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '处理失败',
          message: error.message
        })
      }
    }

    function handleGenerateReport() {
      store.dispatch('app/showLoading', '正在生成报告...')
      
      setTimeout(() => {
        store.dispatch('app/hideLoading')
        store.dispatch('notifications/addNotification', {
          type: 'success',
          title: '报告生成成功',
          message: '数据报告已生成完成，请查收'
        })
      }, 2000)
    }

    function handleQuickAddDevice() {
      router.push({ name: 'DeviceManagement', query: { action: 'add' } })
    }

    function handleViewAllAlerts() {
      // 打开告警管理页面或弹窗
      console.log('查看所有告警')
    }

    function handleGetQRCode() {
      store.dispatch('devices/showQRCodeModal')
    }

    function handleCreateTask() {
      router.push({ name: 'SOPManagement', query: { action: 'create' } })
    }

    function handleEmergencyIntervention() {
      store.dispatch('chat/enableEmergencyMode')
      router.push('/chat')
    }

    function handleShortcutClick(shortcut) {
      if (shortcut.onClick) {
        shortcut.onClick()
      }
    }

    // 数据加载
    const loadDashboardData = async () => {
      try {
        await Promise.all([
          store.dispatch('devices/fetchDevices'),
          store.dispatch('chat/fetchTodayStats'),
          store.dispatch('sop/fetchActiveTasks'),
          store.dispatch('cost/fetchDashboardData'),
          loadChartData()
        ])
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '数据加载失败',
          message: error.message
        })
      }
    }

    const loadChartData = async () => {
      try {
        await Promise.all([
          store.dispatch('chat/fetchTrendData', { period: selectedPeriod.value }),
          store.dispatch('cost/fetchRankingData')
        ])
      } catch (error) {
        console.error('图表数据加载失败:', error)
      }
    }

    // 自动刷新
    const startAutoRefresh = () => {
      refreshTimer.value = setInterval(() => {
        loadDashboardData()
      }, store.state.app.config.autoRefreshInterval)
    }

    const stopAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value)
        refreshTimer.value = null
      }
    }

    // 生命周期
    onMounted(() => {
      loadDashboardData()
      startAutoRefresh()
    })

    onUnmounted(() => {
      stopAutoRefresh()
    })

    return {
      // 数据
      selectedPeriod,
      metrics,
      messageTrendData,
      costRankingData,
      recentAlerts,
      headerActions,
      chartControls,
      rankingActions,
      alertActions,
      shortcuts,

      // 方法
      handleMetricClick,
      handlePeriodChange,
      handleViewCostDetails,
      handleAlert,
      handleShortcutClick
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard {
  padding: var(--space-6) var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

.metrics-section {
  margin-bottom: var(--space-10);
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
}

.analytics-section {
  margin-bottom: var(--space-10);
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-6);
}

// 响应式适配
@media (max-width: 1024px) {
  .analytics-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: var(--space-4);
  }

  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: var(--space-4);
  }

  .analytics-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>

