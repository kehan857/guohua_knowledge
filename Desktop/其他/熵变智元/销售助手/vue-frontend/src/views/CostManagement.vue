<template>
  <div class="cost-management">
    <div class="page-header">
      <h2>成本管理</h2>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
        />
        <el-button type="primary" @click="exportReport">
          <i class="el-icon-download"></i>
          导出报告
        </el-button>
      </div>
    </div>
    
    <div class="cost-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="cost-card">
            <div class="cost-title">总成本</div>
            <div class="cost-amount">¥{{ totalCost.toFixed(2) }}</div>
            <div class="cost-trend" :class="costTrend.type">
              <i :class="getTrendIcon(costTrend.type)"></i>
              {{ costTrend.percent }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="cost-card">
            <div class="cost-title">API调用</div>
            <div class="cost-amount">¥{{ apiCost.toFixed(2) }}</div>
            <div class="cost-trend" :class="apiTrend.type">
              <i :class="getTrendIcon(apiTrend.type)"></i>
              {{ apiTrend.percent }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="cost-card">
            <div class="cost-title">存储费用</div>
            <div class="cost-amount">¥{{ storageCost.toFixed(2) }}</div>
            <div class="cost-trend" :class="storageTrend.type">
              <i :class="getTrendIcon(storageTrend.type)"></i>
              {{ storageTrend.percent }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="cost-card">
            <div class="cost-title">其他费用</div>
            <div class="cost-amount">¥{{ otherCost.toFixed(2) }}</div>
            <div class="cost-trend" :class="otherTrend.type">
              <i :class="getTrendIcon(otherTrend.type)"></i>
              {{ otherTrend.percent }}%
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <div class="cost-details">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="cost-chart">
            <h3>成本趋势</h3>
            <canvas ref="costChart"></canvas>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="cost-breakdown">
            <h3>成本明细</h3>
            <el-table :data="costDetails" style="width: 100%">
              <el-table-column prop="service" label="服务" />
              <el-table-column prop="cost" label="费用">
                <template #default="scope">
                  ¥{{ scope.row.cost.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="usage" label="使用量" />
              <el-table-column prop="percentage" label="占比">
                <template #default="scope">
                  {{ scope.row.percentage }}%
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'CostManagement',
  setup() {
    const dateRange = ref([])
    const costChart = ref(null)
    
    const totalCost = ref(2580.50)
    const apiCost = ref(1850.30)
    const storageCost = ref(450.20)
    const otherCost = ref(280.00)
    
    const costTrend = ref({ type: 'up', percent: 12.5 })
    const apiTrend = ref({ type: 'up', percent: 8.7 })
    const storageTrend = ref({ type: 'down', percent: -3.2 })
    const otherTrend = ref({ type: 'up', percent: 15.8 })
    
    const costDetails = ref([
      {
        service: 'GPT-4 API',
        cost: 1250.50,
        usage: '1,250次调用',
        percentage: 48.5
      },
      {
        service: 'Claude API',
        cost: 599.80,
        usage: '800次调用',
        percentage: 23.2
      },
      {
        service: '图片生成',
        cost: 456.80,
        usage: '150张图片',
        percentage: 17.7
      },
      {
        service: '数据存储',
        cost: 450.20,
        usage: '50GB',
        percentage: 17.4
      },
      {
        service: '其他服务',
        cost: 280.00,
        usage: '杂项',
        percentage: 10.8
      }
    ])
    
    const getTrendIcon = (type) => {
      return type === 'up' ? 'el-icon-top' : 'el-icon-bottom'
    }
    
    const exportReport = () => {
      // 导出报告逻辑
    }
    
    onMounted(() => {
      const ctx = costChart.value.getContext('2d')
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
          datasets: [
            {
              label: '总成本',
              data: [1800, 2100, 1950, 2400, 2200, 2580],
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              tension: 0.4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    })
    
    return {
      dateRange,
      costChart,
      totalCost,
      apiCost,
      storageCost,
      otherCost,
      costTrend,
      apiTrend,
      storageTrend,
      otherTrend,
      costDetails,
      getTrendIcon,
      exportReport
    }
  }
}
</script>

<style lang="scss" scoped>
.cost-management {
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
  
  .header-actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
}

.cost-overview {
  margin-bottom: 2rem;
}

.cost-card {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  box-shadow: var(--shadow);
  text-align: center;
}

.cost-title {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.cost-amount {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.5rem;
}

.cost-trend {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  
  &.up {
    color: var(--success-color);
  }
  
  &.down {
    color: var(--danger-color);
  }
}

.cost-details {
  .cost-chart,
  .cost-breakdown {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    
    h3 {
      margin: 0 0 1rem 0;
      color: var(--text-color);
    }
  }
  
  .cost-chart {
    height: 400px;
  }
}
</style>
