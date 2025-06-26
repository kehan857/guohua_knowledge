<template>
  <div class="industry-map">
    <!-- 头部搜索和标题 -->
    <div class="map-header">
      <div class="header-left">
        <h1 class="page-title">{{ pageTitle }}</h1>
      </div>
      <div class="header-right">
        <a-input-search
          v-model:value="searchText"
          placeholder="产业链名称"
          style="width: 300px"
          @search="handleIndustrySearch"
        >
          <template #enterButton>
            <a-button type="primary">搜索</a-button>
          </template>
        </a-input-search>
      </div>
    </div>

    <!-- KPI指标卡片 -->
    <div class="kpi-section">
      <a-row :gutter="16">
        <a-col :span="4" v-for="(kpi, index) in kpiData" :key="index">
          <div class="kpi-card">
            <div class="kpi-value">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <a-row :gutter="24">
        <!-- 左侧统计面板 -->
        <a-col :span="6">
          <div class="stats-panel">
            <!-- 产业链排行 -->
            <a-card title="产业链排行" size="small" class="ranking-card">
              <div class="ranking-list">
                <div 
                  v-for="(item, index) in industryRanking" 
                  :key="index"
                  class="ranking-item"
                  @click="selectIndustry(item.name)"
                >
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ item.name }}</span>
                  <span class="count">{{ item.count }}家</span>
                </div>
              </div>
            </a-card>

            <!-- 企业类型排行 -->
            <a-card title="企业类型排行" size="small" class="ranking-card">
              <div class="ranking-list">
                <div 
                  v-for="(item, index) in enterpriseTypeRanking" 
                  :key="index"
                  class="ranking-item"
                >
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ item.name }}</span>
                  <span class="count">{{ item.count }}家</span>
                </div>
              </div>
            </a-card>
          </div>
        </a-col>

        <!-- 中间地图区域 -->
        <a-col :span="12">
          <div class="map-container">
            <div ref="mapContainer" class="china-map"></div>
          </div>
        </a-col>

        <!-- 右侧统计面板 -->
        <a-col :span="6">
          <div class="stats-panel">
            <!-- 企业融资状态统计 -->
            <a-card title="企业融资状态统计" size="small" class="chart-card">
              <div ref="financingChart" class="chart-container"></div>
              <div class="total-count">总计 {{ financingData.total }}</div>
            </a-card>

            <!-- 要素资源数量 -->
            <a-card title="要素资源数量" size="small" class="resources-card">
              <div class="resource-grid">
                <div 
                  v-for="(resource, index) in resourceData" 
                  :key="index"
                  class="resource-item"
                >
                  <div class="resource-count">{{ resource.count }}</div>
                  <div class="resource-label">{{ resource.label }}</div>
                </div>
              </div>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 省份详情模态框 -->
    <a-modal
      v-model:open="provinceModalVisible"
      :title="`${selectedProvince}产业链`"
      width="600px"
      :footer="null"
    >
      <a-table
        :columns="provinceTableColumns"
        :data-source="provinceIndustryData"
        :pagination="false"
        size="small"
      >
        <template #name="{ record }">
          <a @click="navigateToChain(record.key)">{{ record.name }}</a>
        </template>
      </a-table>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

const router = useRouter()

// 定义接口类型
interface KpiItem {
  label: string
  value: string | number
}

interface RankingItem {
  name: string
  count: number
}

interface ResourceItem {
  label: string
  count: number
}

interface FinancingData {
  total: number
  unfinanced: number
  financing: number
  listed: number
}

// 响应式数据
const searchText = ref('')
const pageTitle = ref('产业链地图')
const selectedIndustry = ref('')
const provinceModalVisible = ref(false)
const selectedProvince = ref('')

// 地图容器
const mapContainer = ref<HTMLElement>()
const financingChart = ref<HTMLElement>()

// KPI数据
const kpiData = reactive<KpiItem[]>([
  { label: '产业链数量', value: 35 },
  { label: '企业总数量', value: 510 },
  { label: '上游企业数量', value: 210 },
  { label: '中游企业数量', value: 180 },
  { label: '下游企业数量', value: 120 }
])

// 产业链排行数据
const industryRanking = reactive<RankingItem[]>([
  { name: '石油化工', count: 156 },
  { name: '电子信息', count: 143 },
  { name: '装备制造', count: 128 },
  { name: '生物医药', count: 95 },
  { name: '新材料', count: 87 },
  { name: '新能源', count: 76 }
])

// 企业类型排行数据
const enterpriseTypeRanking = reactive<RankingItem[]>([
  { name: '制造业单项冠军企业', count: 89 },
  { name: '专精特新小巨人企业', count: 156 },
  { name: '高新技术企业', count: 234 },
  { name: '独角兽企业', count: 12 },
  { name: '上市公司', count: 67 }
])

// 融资状态数据
const financingData = reactive<FinancingData>({
  total: 510,
  unfinanced: 234,
  financing: 187,
  listed: 89
})

// 要素资源数据
const resourceData = reactive<ResourceItem[]>([
  { label: '企业', count: 510 },
  { label: '产业', count: 35 },
  { label: '方案', count: 128 },
  { label: '需求', count: 89 },
  { label: '专家', count: 67 },
  { label: '政策', count: 45 },
  { label: '知识', count: 234 }
])

// 省份产业链数据
const provinceIndustryData = ref([
  { key: 'petrochemical', name: '石油化工', count: 45 },
  { key: 'electronics', name: '电子信息', count: 38 },
  { key: 'manufacturing', name: '装备制造', count: 32 },
  { key: 'biotech', name: '生物医药', count: 28 }
])

// 省份表格列配置
const provinceTableColumns = [
  {
    title: '序号',
    dataIndex: 'index',
    key: 'index',
    width: 60,
    customRender: ({ index }: { index: number }) => index + 1
  },
  {
    title: '产业链名称',
    dataIndex: 'name',
    key: 'name',
    slots: { customRender: 'name' }
  },
  {
    title: '企业数量',
    dataIndex: 'count',
    key: 'count',
    render: (count: number) => `${count}家`
  }
]

// 方法
const handleIndustrySearch = (value: string) => {
  if (value.trim()) {
    selectIndustry(value)
  }
}

const selectIndustry = (industryName: string) => {
  selectedIndustry.value = industryName
  pageTitle.value = `${industryName} - 产业链地图`
  
  // 更新KPI数据为特定产业链的数据
  updateKpiForIndustry(industryName)
  
  // 重新渲染地图，高亮该产业链的省份分布
  renderMapForIndustry(industryName)
  
  message.success(`已切换到${industryName}产业链视图`)
}

const updateKpiForIndustry = (industryName: string) => {
  // 模拟根据产业链更新KPI数据
  const industryKpiMap: Record<string, Partial<KpiItem>[]> = {
    '石油化工': [
      { value: 1 },
      { value: 156 },
      { value: 68 },
      { value: 54 },
      { value: 34 }
    ],
    '电子信息': [
      { value: 1 },
      { value: 143 },
      { value: 62 },
      { value: 49 },
      { value: 32 }
    ]
  }

  const updates = industryKpiMap[industryName]
  if (updates) {
    updates.forEach((update, index) => {
      if (kpiData[index] && update.value !== undefined) {
        kpiData[index].value = update.value
      }
    })
  }
}

const renderChinaMap = () => {
  if (!mapContainer.value) return
  
  mapContainer.value.innerHTML = `
    <div class="map-placeholder">
      <div class="map-title">中国产业链分布图</div>
      <div class="map-background">
        <svg width="100%" height="100%" viewBox="0 0 600 400" style="position: absolute; top: 0; left: 0;">
          <!-- 简化的中国地图轮廓 -->
          <defs>
            <pattern id="mapPattern" patternUnits="userSpaceOnUse" width="20" height="20">
              <circle cx="10" cy="10" r="1" fill="#e8f5e8" opacity="0.3"/>
            </pattern>
          </defs>
          <path d="M100,80 L500,80 L520,120 L480,180 L520,220 L500,280 L450,320 L350,340 L250,320 L150,300 L100,250 L80,200 L90,150 Z" 
                fill="url(#mapPattern)" 
                stroke="#d0f0d0" 
                stroke-width="2"/>
        </svg>
      </div>
      <div class="provinces">
        ${[
          { name: '河南', count: 950, x: 45, y: 40, color: '#ff6b6b' },
          { name: '山东', count: 820, x: 50, y: 25, color: '#4ecdc4' },
          { name: '江苏', count: 750, x: 55, y: 35, color: '#45b7d1' },
          { name: '广东', count: 680, x: 48, y: 75, color: '#f9ca24' },
          { name: '浙江', count: 620, x: 58, y: 45, color: '#6c5ce7' },
          { name: '四川', count: 580, x: 25, y: 55, color: '#a0e7e5' }
        ].map(province => `
          <div class="province-marker" 
               style="left: ${province.x}%; top: ${province.y}%"
               data-province="${province.name}"
               data-count="${province.count}">
            <div class="marker-dot" style="background: ${province.color};">
              <div class="pulse"></div>
            </div>
            <div class="marker-label">${province.name}<br/><strong>${province.count}</strong></div>
          </div>
        `).join('')}
      </div>
    </div>
  `
  
  // 添加省份点击事件
  mapContainer.value.querySelectorAll('.province-marker').forEach(marker => {
    marker.addEventListener('click', (e) => {
      e.stopPropagation()
      const provinceName = (e.currentTarget as HTMLElement).dataset.province
      if (provinceName) {
        showProvinceDetail(provinceName)
      }
    })
    
    // 添加悬停效果
    marker.addEventListener('mouseenter', (e) => {
      const dot = (e.currentTarget as HTMLElement).querySelector('.marker-dot') as HTMLElement
      if (dot) {
        dot.style.transform = 'scale(1.3)'
        dot.style.zIndex = '20'
      }
    })
    
    marker.addEventListener('mouseleave', (e) => {
      const dot = (e.currentTarget as HTMLElement).querySelector('.marker-dot') as HTMLElement
      if (dot) {
        dot.style.transform = 'scale(1)'
        dot.style.zIndex = '10'
      }
    })
  })
}

const renderMapForIndustry = (industryName: string) => {
  // 重新渲染地图，突出显示特定产业链的分布
  renderChinaMap()
  
  // 可以根据产业链调整省份数据和颜色
  message.info(`地图已更新为${industryName}产业链分布`)
}

const renderFinancingChart = () => {
  if (!financingChart.value) return
  
  // 模拟饼图渲染
  financingChart.value.innerHTML = `
    <div class="pie-chart">
      <div class="chart-legend">
        <div class="legend-item">
          <span class="legend-color" style="background: #ff4d4f"></span>
          <span>未融资 ${financingData.unfinanced}</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #1890ff"></span>
          <span>融资中 ${financingData.financing}</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #52c41a"></span>
          <span>已上市 ${financingData.listed}</span>
        </div>
      </div>
    </div>
  `
}

const showProvinceDetail = (provinceName: string) => {
  selectedProvince.value = provinceName
  provinceModalVisible.value = true
}

const navigateToChain = (industryKey: string) => {
  provinceModalVisible.value = false
  router.push(`/insights/industry-chain/${industryKey}`)
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    renderChinaMap()
    renderFinancingChart()
  })
})
</script>

<style scoped lang="less">
.industry-map {
  padding: 24px;
  background: var(--bg-primary);
  min-height: calc(100vh - 64px);
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.kpi-section {
  margin-bottom: 24px;
  
  .kpi-card {
    background: var(--component-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--primary-color);
      box-shadow: 0 4px 16px rgba(35, 134, 54, 0.1);
    }
    
    .kpi-value {
      font-size: 32px;
      font-weight: bold;
      color: var(--primary-color);
      margin-bottom: 8px;
    }
    
    .kpi-label {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }
}

.main-content {
  .stats-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
    
    .ranking-card,
    .chart-card,
    .resources-card {
      :deep(.ant-card-body) {
        padding: 16px;
      }
    }
    
    .ranking-list {
      .ranking-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:last-child {
          border-bottom: none;
        }
        
        &:hover {
          background: rgba(35, 134, 54, 0.05);
          transform: translateX(4px);
        }
        
        .rank {
          width: 24px;
          height: 24px;
          background: var(--primary-color);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: bold;
          margin-right: 12px;
          flex-shrink: 0;
        }
        
        .name {
          flex: 1;
          color: var(--text-primary);
          font-weight: 500;
        }
        
        .count {
          color: var(--primary-color);
          font-weight: bold;
          font-size: 12px;
        }
      }
    }
    
    .chart-container {
      height: 200px;
      
      .pie-chart {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        
        .chart-legend {
          .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 12px;
            color: var(--text-secondary);
            
            .legend-color {
              width: 12px;
              height: 12px;
              border-radius: 50%;
              margin-right: 8px;
            }
          }
        }
      }
    }
    
    .total-count {
      text-align: center;
      color: var(--text-secondary);
      font-size: 12px;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid var(--border-color);
    }
    
    .resource-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      
      .resource-item {
        text-align: center;
        padding: 12px;
        background: var(--bg-tertiary);
        border-radius: 6px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(35, 134, 54, 0.1);
          transform: translateY(-2px);
        }
        
        .resource-count {
          font-size: 18px;
          font-weight: bold;
          color: var(--primary-color);
          margin-bottom: 4px;
        }
        
        .resource-label {
          font-size: 12px;
          color: var(--text-secondary);
        }
      }
    }
  }
}

.map-container {
  background: var(--component-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  
  .china-map {
    height: 500px;
    position: relative;
    
    .map-placeholder {
      width: 100%;
      height: 100%;
      position: relative;
      background: linear-gradient(135deg, #f0f9f0 0%, #e8f5e8 50%, #f0f8f0 100%);
      overflow: hidden;
      
      .map-title {
        position: absolute;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        z-index: 5;
        background: rgba(255, 255, 255, 0.9);
        padding: 8px 16px;
        border-radius: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
      
      .map-background {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        
        svg {
          filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
          
          path {
            transition: all 0.3s ease;
            
            &:hover {
              fill: rgba(35, 134, 54, 0.1);
            }
          }
        }
      }
      
      .provinces {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 10;
        
        .province-marker {
          position: absolute;
          cursor: pointer;
          transform: translate(-50%, -50%);
          transition: all 0.3s ease;
          
          &:hover {
            z-index: 20;
            
            .marker-label {
              opacity: 1;
              transform: translateY(-10px);
              background: var(--primary-color);
              color: white;
              border-color: var(--primary-color);
            }
          }
          
          .marker-dot {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin: 0 auto 8px;
            position: relative;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            z-index: 10;
            
            .pulse {
              position: absolute;
              top: -2px;
              left: -2px;
              right: -2px;
              bottom: -2px;
              border: 2px solid currentColor;
              border-radius: 50%;
              opacity: 0;
              animation: pulse 2s infinite;
            }
            
            &:hover {
              transform: scale(1.2);
              box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            }
          }
          
          .marker-label {
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-primary);
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            min-width: 60px;
            opacity: 0.9;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            line-height: 1.2;
            
            strong {
              color: var(--primary-color);
              font-size: 13px;
            }
          }
          
          &:nth-child(1) .marker-dot { background: #ff6b6b; color: #ff6b6b; }
          &:nth-child(2) .marker-dot { background: #4ecdc4; color: #4ecdc4; }
          &:nth-child(3) .marker-dot { background: #45b7d1; color: #45b7d1; }
          &:nth-child(4) .marker-dot { background: #f9ca24; color: #f9ca24; }
          &:nth-child(5) .marker-dot { background: #6c5ce7; color: #6c5ce7; }
          &:nth-child(6) .marker-dot { background: #a0e7e5; color: #a0e7e5; }
        }
      }
    }
  }
}

@keyframes pulse {
  0% {
    opacity: 0;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(1.2);
  }
  100% {
    opacity: 0;
    transform: scale(1.4);
  }
}

// 响应式设计修复
@media (max-width: 1200px) {
  .main-content {
    .ant-row {
      .ant-col {
        margin-bottom: 16px;
      }
    }
  }
  
  .map-container .china-map {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .industry-map {
    padding: 12px;
  }
  
  .map-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    
    .header-right {
      width: 100%;
      
      .ant-input-search {
        width: 100% !important;
      }
    }
  }
  
  .kpi-section .ant-row .ant-col {
    span: 12 !important;
    margin-bottom: 12px;
  }
  
  .main-content .ant-row .ant-col {
    span: 24 !important;
    margin-bottom: 16px;
  }
  
  .map-container .china-map {
    height: 300px;
  }
  
  .stats-panel {
    margin-top: 16px;
    
    .resource-grid {
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
  }
}
</style> 