<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="dashboard-title">产业数据中心</h1>
        <p class="dashboard-subtitle">Industry Data Center - 数据驱动的智能决策平台</p>
      </div>
      <div class="dashboard-filters">
        <a-select
          v-model:value="selectedIndustry"
          placeholder="选择产业链"
          style="width: 200px"
          @change="handleIndustryChange"
        >
          <a-select-option value="all">全部产业链</a-select-option>
          <a-select-option value="petrochemical">石油化工</a-select-option>
          <a-select-option value="bigdata">大数据</a-select-option>
          <a-select-option value="new-energy">新能源</a-select-option>
        </a-select>
        
        <a-range-picker
          v-model:value="dateRange"
          style="margin-left: 16px"
          @change="handleDateChange"
        />
      </div>
    </div>

    <!-- KPI指标卡片网格 -->
    <div class="kpi-grid">
      <div class="kpi-card glass-card glow-element">
        <div class="kpi-icon">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <defs>
              <linearGradient id="enterpriseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#00E5FF;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#1976D2;stop-opacity:1" />
              </linearGradient>
            </defs>
            <rect x="8" y="12" width="32" height="28" rx="4" fill="url(#enterpriseGradient)" opacity="0.8"/>
            <rect x="12" y="16" width="8" height="2" fill="white" opacity="0.9"/>
            <rect x="12" y="20" width="12" height="2" fill="white" opacity="0.7"/>
            <rect x="12" y="24" width="6" height="2" fill="white" opacity="0.7"/>
            <circle cx="32" cy="20" r="6" fill="#FFD700" opacity="0.9"/>
            <text x="32" y="24" text-anchor="middle" fill="white" font-size="8" font-weight="bold">企</text>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-value pulse-effect">{{ formatNumber(totalEnterprises) }}</div>
          <div class="kpi-label">企业总数</div>
          <div class="kpi-trend">
            <arrow-up-outlined style="color: #00E5FF" />
            <span>+12.5%</span>
          </div>
        </div>
      </div>
      
      <div class="kpi-card glass-card glow-element">
        <div class="kpi-icon">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <defs>
              <linearGradient id="demandGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#FF6B35;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#F7931E;stop-opacity:1" />
              </linearGradient>
            </defs>
            <path d="M24 8 L32 16 L24 24 L16 16 Z" fill="url(#demandGradient)" opacity="0.8"/>
            <circle cx="24" cy="32" r="8" fill="url(#demandGradient)" opacity="0.6"/>
            <path d="M20 28 Q24 24 28 28 Q24 32 20 28" fill="white" opacity="0.9"/>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-value pulse-effect">{{ formatNumber(totalDemands) }}</div>
          <div class="kpi-label">需求总量</div>
          <div class="kpi-trend">
            <arrow-up-outlined style="color: #FF6B35" />
            <span>+8.3%</span>
          </div>
        </div>
      </div>
      
      <div class="kpi-card glass-card glow-element">
        <div class="kpi-icon">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <defs>
              <linearGradient id="productGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#2E7D32;stop-opacity:1" />
              </linearGradient>
            </defs>
            <rect x="10" y="14" width="12" height="20" rx="2" fill="url(#productGradient)" opacity="0.8"/>
            <rect x="26" y="10" width="12" height="24" rx="2" fill="url(#productGradient)" opacity="0.6"/>
            <circle cx="16" cy="18" r="2" fill="white" opacity="0.9"/>
            <circle cx="32" cy="16" r="2" fill="white" opacity="0.9"/>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-value pulse-effect">{{ formatNumber(totalProducts) }}</div>
          <div class="kpi-label">产品数量</div>
          <div class="kpi-trend">
            <arrow-up-outlined style="color: #4CAF50" />
            <span>+15.2%</span>
          </div>
        </div>
      </div>
      
      <div class="kpi-card glass-card glow-element">
        <div class="kpi-icon">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <defs>
              <linearGradient id="matchGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#FF8F00;stop-opacity:1" />
              </linearGradient>
            </defs>
            <path d="M24 8 L30 20 L42 20 L33 29 L36 41 L24 35 L12 41 L15 29 L6 20 L18 20 Z" fill="url(#matchGradient)" opacity="0.8"/>
            <circle cx="24" cy="24" r="6" fill="white" opacity="0.9"/>
            <text x="24" y="28" text-anchor="middle" fill="#FFD700" font-size="10" font-weight="bold">匹</text>
          </svg>
        </div>
        <div class="kpi-content">
          <div class="kpi-value pulse-effect">{{ formatNumber(todayMatches) }}</div>
          <div class="kpi-label">今日匹配</div>
          <div class="kpi-trend">
            <arrow-up-outlined style="color: #FFD700" />
            <span>+23.1%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要图表区域 -->
    <div class="charts-main-grid">
      <!-- 左侧：产业分布饼图 -->
      <div class="chart-container glass-card">
        <div class="chart-header">
          <h3 class="h3-title">产业链分布</h3>
          <div class="chart-controls">
            <a-tooltip title="查看详细数据">
              <a-button type="text" size="small">
                <template #icon><bar-chart-outlined /></template>
              </a-button>
            </a-tooltip>
          </div>
        </div>
        <div ref="industryChartRef" class="chart-content"></div>
      </div>
      
      <!-- 右侧：地域分布条形图 -->
      <div class="chart-container glass-card">
        <div class="chart-header">
          <h3 class="h3-title">区域企业分布</h3>
          <div class="chart-controls">
            <a-tooltip title="查看地图视图">
              <a-button type="text" size="small">
                <template #icon><global-outlined /></template>
              </a-button>
            </a-tooltip>
          </div>
        </div>
        <div ref="regionChartRef" class="chart-content"></div>
      </div>
    </div>

    <!-- 全宽趋势图 -->
    <div class="chart-container glass-card chart-full-width">
      <div class="chart-header">
        <h3 class="h3-title">数据增长趋势</h3>
        <div class="trend-indicators">
          <div class="trend-indicator">
            <span class="trend-label">月增长率</span>
            <span class="trend-value positive">+24.8%</span>
          </div>
          <div class="trend-indicator">
            <span class="trend-label">年增长率</span>
            <span class="trend-value positive">+156.3%</span>
          </div>
        </div>
      </div>
      <div ref="trendChartRef" class="chart-content chart-trend"></div>
    </div>

    <!-- 快速导航网格 -->
    <div class="quick-nav-section">
      <h2 class="section-title">快速导航</h2>
      <div class="quick-nav-grid">
        <div class="nav-card glass-card glow-element" @click="navigateTo('/insights/industry-overview')">
          <div class="nav-icon">
            <fund-view-outlined />
          </div>
          <div class="nav-content">
            <h4>产业链图谱</h4>
            <p>可视化产业链结构与关联关系</p>
          </div>
          <div class="nav-arrow">
            <arrow-right-outlined />
          </div>
        </div>
        
        <div class="nav-card glass-card glow-element" @click="navigateTo('/insights/enterprise-map')">
          <div class="nav-icon">
            <global-outlined />
          </div>
          <div class="nav-content">
            <h4>企业地图</h4>
            <p>地理分布与聚集度分析</p>
          </div>
          <div class="nav-arrow">
            <arrow-right-outlined />
          </div>
        </div>
        
        <div class="nav-card glass-card glow-element" @click="navigateTo('/opportunities/supply-demand-map')">
          <div class="nav-icon">
            <rocket-outlined />
          </div>
          <div class="nav-content">
            <h4>供需匹配</h4>
            <p>智能化机会发现引擎</p>
          </div>
          <div class="nav-arrow">
            <arrow-right-outlined />
          </div>
        </div>
        
        <div class="nav-card glass-card glow-element" @click="navigateTo('/resources/enterprises')">
          <div class="nav-icon">
            <database-outlined />
          </div>
          <div class="nav-content">
            <h4>数据资源库</h4>
            <p>企业、产品、需求数据查询</p>
          </div>
          <div class="nav-arrow">
            <arrow-right-outlined />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { Dayjs } from 'dayjs'
import * as echarts from 'echarts'
import {
  ArrowUpOutlined,
  ArrowRightOutlined,
  FundViewOutlined,
  GlobalOutlined,
  RocketOutlined,
  DatabaseOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

const router = useRouter()

// 响应式数据
const selectedIndustry = ref('all')
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// KPI数据
const totalEnterprises = ref(15432)
const totalDemands = ref(8765)
const totalProducts = ref(23456)
const todayMatches = ref(234)

// 图表引用
const industryChartRef = ref()
const regionChartRef = ref()
const trendChartRef = ref()

// ECharts实例
let industryChart: echarts.ECharts | null = null
let regionChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// 方法
const formatNumber = (num: number) => {
  return num.toLocaleString()
}

const handleIndustryChange = (value: string) => {
  console.log('Industry changed:', value)
  // 这里会触发数据重新加载和图表更新
  updateCharts()
}

const handleDateChange = (dates: [Dayjs, Dayjs] | null) => {
  console.log('Date range changed:', dates)
  // 这里会触发数据重新加载
  updateCharts()
}

const navigateTo = (path: string) => {
  router.push(path)
}

// 初始化产业链分布饼图
const initIndustryChart = () => {
  if (!industryChartRef.value) return
  
  industryChart = echarts.init(industryChartRef.value)
  
  const option = {
    title: {
      text: '产业链分布',
      left: 'center',
      top: 20,
      textStyle: {
        color: '#C9D1D9',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)',
      backgroundColor: 'rgba(10, 15, 42, 0.9)',
      borderColor: '#00E5FF',
      textStyle: {
        color: '#C9D1D9'
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center',
      textStyle: {
        color: '#C9D1D9'
      },
      itemGap: 15
    },
    series: [
      {
        name: '产业分布',
        type: 'pie',
        radius: ['30%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold',
            color: '#C9D1D9'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: 45,
            name: '石油化工',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                { offset: 0, color: '#00E5FF' },
                { offset: 1, color: '#1976D2' }
              ])
            }
          },
          {
            value: 30,
            name: '大数据',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                { offset: 0, color: '#FFD700' },
                { offset: 1, color: '#FF8F00' }
              ])
            }
          },
          {
            value: 25,
            name: '新能源',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
                { offset: 0, color: '#4CAF50' },
                { offset: 1, color: '#2E7D32' }
              ])
            }
          }
        ]
      }
    ],
    backgroundColor: 'transparent'
  }
  
  industryChart.setOption(option)
}

// 初始化区域企业分布柱状图
const initRegionChart = () => {
  if (!regionChartRef.value) return
  
  regionChart = echarts.init(regionChartRef.value)
  
  const option = {
    title: {
      text: '区域企业分布',
      left: 'center',
      top: 20,
      textStyle: {
        color: '#C9D1D9',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 15, 42, 0.9)',
      borderColor: '#00E5FF',
      textStyle: {
        color: '#C9D1D9'
      },
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#8B949E'
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#30363D'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#30363D'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: ['山东省', '江苏省', '广东省', '浙江省', '河南省'],
      axisLabel: {
        color: '#8B949E'
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#30363D'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: [3256, 2834, 2567, 2123, 1876],
        barWidth: '60%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#00E5FF' },
            { offset: 1, color: '#1976D2' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          color: '#C9D1D9',
          formatter: '{c}'
        }
      }
    ],
    backgroundColor: 'transparent'
  }
  
  regionChart.setOption(option)
}

// 初始化数据增长趋势折线图
const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    title: {
      text: '数据增长趋势',
      left: 'center',
      top: 20,
      textStyle: {
        color: '#C9D1D9',
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 15, 42, 0.9)',
      borderColor: '#00E5FF',
      textStyle: {
        color: '#C9D1D9'
      }
    },
    legend: {
      data: ['企业数量', '需求数量', '产品数量'],
      top: 50,
      textStyle: {
        color: '#C9D1D9'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月'],
      axisLabel: {
        color: '#8B949E'
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#30363D'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#8B949E'
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#30363D'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#30363D'
        }
      }
    },
    series: [
      {
        name: '企业数量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        data: [1200, 1350, 1580, 1720, 1890, 2100, 2380, 2650, 2890],
        itemStyle: {
          color: '#00E5FF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 229, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 229, 255, 0.1)' }
          ])
        }
      },
      {
        name: '需求数量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        data: [800, 950, 1100, 1250, 1400, 1600, 1800, 2000, 2200],
        itemStyle: {
          color: '#FFD700'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 215, 0, 0.3)' },
            { offset: 1, color: 'rgba(255, 215, 0, 0.1)' }
          ])
        }
      },
      {
        name: '产品数量',
        type: 'line',
        stack: 'Total',
        smooth: true,
        data: [600, 750, 900, 1080, 1280, 1500, 1750, 2000, 2300],
        itemStyle: {
          color: '#4CAF50'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(76, 175, 80, 0.3)' },
            { offset: 1, color: 'rgba(76, 175, 80, 0.1)' }
          ])
        }
      }
    ],
    backgroundColor: 'transparent'
  }
  
  trendChart.setOption(option)
}

// 初始化所有图表
const initCharts = () => {
  initIndustryChart()
  initRegionChart()
  initTrendChart()
}

// 更新图表数据
const updateCharts = () => {
  // 根据选择的产业和日期范围更新图表数据
  // 这里可以调用API获取新数据
  console.log('Updating charts with new data...')
}

// 响应式调整图表大小
const resizeCharts = () => {
  industryChart?.resize()
  regionChart?.resize()
  trendChart?.resize()
}

// 监听窗口大小变化
window.addEventListener('resize', resizeCharts)

onMounted(() => {
  nextTick(() => {
    initCharts()
  })
})
</script>

<style scoped lang="less">
.dashboard {
  min-height: 100vh;
  padding: 24px;
  background: var(--bg-primary);
  
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
    
    .header-content {
      .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 8px 0;
        background: linear-gradient(135deg, #00E5FF, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .dashboard-subtitle {
        font-size: 16px;
        color: var(--text-secondary);
        margin: 0;
        opacity: 0.8;
      }
    }
    
    .dashboard-filters {
      display: flex;
      align-items: center;
    }
  }
  
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    margin-bottom: 32px;
    
    .kpi-card {
      display: flex;
      align-items: center;
      padding: 24px;
      border-radius: 12px;
      position: relative;
      overflow: hidden;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00E5FF, #FFD700);
      }
      
      .kpi-icon {
        margin-right: 16px;
        flex-shrink: 0;
      }
      
      .kpi-content {
        flex: 1;
        
        .kpi-value {
          font-size: 28px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1;
          margin-bottom: 4px;
        }
        
        .kpi-label {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 8px;
        }
        
        .kpi-trend {
          display: flex;
          align-items: center;
          font-size: 12px;
          font-weight: 600;
          color: #00E5FF;
          
          span {
            margin-left: 4px;
          }
        }
      }
    }
  }
  
  .charts-main-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
  }
  
  .chart-container {
    padding: 24px;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
    
    &.chart-full-width {
      grid-column: 1 / -1;
    }
    
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      .h3-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
      }
      
      .chart-controls {
        display: flex;
        gap: 8px;
      }
      
      .trend-indicators {
        display: flex;
        gap: 24px;
        
        .trend-indicator {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          
          .trend-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 4px;
          }
          
          .trend-value {
            font-size: 18px;
            font-weight: 700;
            
            &.positive {
              color: #4CAF50;
            }
          }
        }
      }
    }
    
    .chart-content {
      height: 280px;
      position: relative;
      width: 100%;
      box-sizing: border-box;
      
      &.chart-trend {
        height: 320px;
      }
      
      // ECharts容器样式
      & > div {
        width: 100% !important;
        height: 100% !important;
        max-width: 100%;
        max-height: 100%;
      }
    }
  }
  
  .pie-chart-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    .chart-legend {
      margin-top: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }
        
        .legend-label {
          flex: 1;
          font-size: 12px;
          color: var(--text-primary);
        }
        
        .legend-value {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary);
        }
      }
    }
  }
  
  .bar-chart-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    padding: 8px 0;
    
    .bar-item {
      display: flex;
      align-items: center;
      gap: 12px;
      opacity: 0;
      animation: slideInLeft 0.6s ease forwards;
      
      .bar-label {
        width: 60px;
        font-size: 12px;
        color: var(--text-primary);
        text-align: right;
      }
      
      .bar-container {
        flex: 1;
        height: 24px;
        position: relative;
        
        .bar-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(13, 17, 23, 0.5);
          border-radius: 12px;
        }
        
        .bar-fill {
          position: absolute;
          top: 0;
          left: 0;
          bottom: 0;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          padding-right: 8px;
          animation: fillAnimation 1s ease-out 0.3s both;
          transform-origin: left;
          transform: scaleX(0);
          
          .bar-value {
            font-size: 10px;
            font-weight: 600;
            color: white;
          }
        }
      }
      
      .bar-percent {
        width: 40px;
        font-size: 10px;
        color: var(--text-secondary);
        text-align: right;
      }
    }
  }
  
  .trend-chart-container {
    height: 100%;
    overflow: hidden;
  }
  
  .quick-nav-section {
    margin-top: 40px;
    
    .section-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 24px;
      text-align: center;
    }
  }
  
  .quick-nav-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    
    .nav-card {
      display: flex;
      align-items: center;
      padding: 20px;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.1), transparent);
        transition: left 0.5s ease;
      }
      
      &:hover {
        transform: translateY(-4px);
        
        &::before {
          left: 100%;
        }
        
        .nav-arrow {
          transform: translateX(4px);
        }
      }
      
      .nav-icon {
        font-size: 24px;
        color: #00E5FF;
        margin-right: 16px;
        flex-shrink: 0;
      }
      
      .nav-content {
        flex: 1;
        
        h4 {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0 0 4px 0;
        }
        
        p {
          font-size: 12px;
          color: var(--text-secondary);
          margin: 0;
          opacity: 0.8;
        }
      }
      
      .nav-arrow {
        font-size: 16px;
        color: var(--text-secondary);
        transition: transform 0.3s ease;
      }
    }
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fillAnimation {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .dashboard {
    padding: 16px;
    
    .kpi-grid,
    .quick-nav-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }
    
    .charts-main-grid {
      grid-template-columns: 1fr;
    }
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
    
    .dashboard-header {
      flex-direction: column;
      gap: 16px;
      align-items: flex-start;
      
      .header-content .dashboard-title {
        font-size: 24px;
      }
      
      .dashboard-filters {
        width: 100%;
        justify-content: flex-end;
      }
    }
    
    .kpi-grid,
    .quick-nav-grid {
      grid-template-columns: 1fr;
      gap: 12px;
    }
    
    .kpi-card {
      flex-direction: column;
      text-align: center;
      
      .kpi-icon {
        margin-right: 0;
        margin-bottom: 12px;
      }
    }
    
    .quick-nav-grid .nav-card {
      .nav-content {
        h4 {
          font-size: 14px;
        }
        
        p {
          font-size: 11px;
        }
      }
    }
  }
}
</style> 