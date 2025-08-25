<template>
  <div class="message-trend-chart">
    <div class="chart-header">
      <h4>消息趋势</h4>
      <el-select v-model="timeRange" size="small">
        <el-option label="今日" value="today" />
        <el-option label="本周" value="week" />
        <el-option label="本月" value="month" />
      </el-select>
    </div>
    <div class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'MessageTrendChart',
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    const timeRange = ref('week')
    let chart = null
    
    const createChart = () => {
      if (chart) {
        chart.destroy()
      }
      
      const ctx = chartCanvas.value.getContext('2d')
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: props.data.map(item => item.time),
          datasets: [
            {
              label: '接收消息',
              data: props.data.map(item => item.received),
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              tension: 0.4
            },
            {
              label: '发送消息',
              data: props.data.map(item => item.sent),
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              tension: 0.4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      })
    }
    
    onMounted(() => {
      createChart()
    })
    
    watch(() => props.data, createChart, { deep: true })
    watch(timeRange, () => {
      // 这里可以触发数据更新
    })
    
    return {
      chartCanvas,
      timeRange
    }
  }
}
</script>

<style lang="scss" scoped>
.message-trend-chart {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}

.chart-header {
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

.chart-container {
  height: 300px;
  position: relative;
}
</style>
