<template>
  <div class="enterprise-map">
    <!-- 顶部控制栏 -->
    <div class="map-header">
      <div class="header-left">
        <h1 class="map-title">企业地图</h1>
        <p class="map-subtitle">产业地理分布分析</p>
      </div>
      <div class="header-right">
        <a-select v-model:value="selectedIndustry" style="width: 150px" @change="onIndustryChange">
          <a-select-option value="all">全部产业链</a-select-option>
          <a-select-option value="petrochemical">石油化工</a-select-option>
          <a-select-option value="bigdata">大数据</a-select-option>
          <a-select-option value="newenergy">新能源</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- KPI指标卡片 -->
    <div class="kpi-section">
      <div class="kpi-grid">
        <div class="kpi-card glass-card glow-element">
          <div class="kpi-icon">🏢</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ totalEnterprises.toLocaleString() }}</div>
            <div class="kpi-label">企业总数</div>
          </div>
        </div>
        
        <div class="kpi-card glass-card glow-element">
          <div class="kpi-icon">⬆️</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ upstreamCount.toLocaleString() }}</div>
            <div class="kpi-label">上游企业</div>
          </div>
        </div>
        
        <div class="kpi-card glass-card glow-element">
          <div class="kpi-icon">🔄</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ midstreamCount.toLocaleString() }}</div>
            <div class="kpi-label">中游企业</div>
          </div>
        </div>
        
        <div class="kpi-card glass-card glow-element">
          <div class="kpi-icon">⬇️</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ downstreamCount.toLocaleString() }}</div>
            <div class="kpi-label">下游企业</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主地图区域 -->
    <div class="map-container">
      <div class="map-content">
        <!-- 中国地图占位 -->
        <div ref="mapContainer" class="china-map">
          <div class="map-placeholder">
            <div class="placeholder-content">
              <div class="map-icon">🗺️</div>
              <h3>中国产业分布地图</h3>
              <p>点击省份查看详细企业信息</p>
              
              <!-- 模拟省份热力图 -->
              <div class="mock-provinces">
                <div 
                  v-for="province in provinces" 
                  :key="province.code"
                  class="province-item"
                  :class="{ 'high-density': province.enterprises > 2000, 'medium-density': province.enterprises > 1000 }"
                  @click="selectProvince(province)"
                >
                  <div class="province-name">{{ province.name }}</div>
                  <div class="province-count">{{ province.enterprises }}家</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 企业列表面板 -->
        <div v-if="selectedProvince" class="enterprise-panel glass-card">
          <div class="panel-header">
            <h3>{{ selectedProvince.name }} - {{ selectedIndustryName }}企业</h3>
            <a-button type="text" size="small" @click="closeProvincePanel">
              <template #icon><close-outlined /></template>
            </a-button>
          </div>
          
          <div class="panel-content">
            <div class="province-stats">
              <div class="stat-row">
                <span class="stat-label">企业总数：</span>
                <span class="stat-value">{{ selectedProvince.enterprises }}家</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">主要城市：</span>
                <span class="stat-value">{{ selectedProvince.cities.join('、') }}</span>
              </div>
            </div>
            
            <div class="enterprise-list">
              <h4>重点企业</h4>
              <div 
                v-for="enterprise in selectedProvince.keyEnterprises" 
                :key="enterprise.id"
                class="enterprise-item"
                @click="viewEnterpriseDetail(enterprise.id)"
              >
                <div class="enterprise-info">
                  <div class="enterprise-name">{{ enterprise.name }}</div>
                  <div class="enterprise-meta">
                    <span class="enterprise-type">{{ enterprise.type }}</span>
                    <span class="enterprise-city">{{ enterprise.city }}</span>
                  </div>
                </div>
                <div class="enterprise-scale">{{ enterprise.scale }}</div>
              </div>
            </div>
            
            <div class="panel-footer">
              <a-button type="primary" block @click="viewAllEnterprises">
                查看全部企业
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 地图控制工具 -->
    <div class="map-controls">
      <div class="zoom-controls">
        <a-button @click="zoomIn" size="small">
          <template #icon><plus-outlined /></template>
        </a-button>
        <a-button @click="zoomOut" size="small">
          <template #icon><minus-outlined /></template>
        </a-button>
        <a-button @click="resetMapView" size="small">
          <template #icon><aim-outlined /></template>
        </a-button>
      </div>
      
      <div class="layer-controls">
        <a-switch v-model:checked="showHeatmap" size="small" />
        <span class="control-label">热力图</span>
      </div>
    </div>

    <!-- 图例 -->
    <div class="map-legend glass-card">
      <h4>企业密度</h4>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-color high"></div>
          <span>高密度 (>2000家)</span>
        </div>
        <div class="legend-item">
          <div class="legend-color medium"></div>
          <span>中密度 (1000-2000家)</span>
        </div>
        <div class="legend-item">
          <div class="legend-color low"></div>
          <span>低密度 (<1000家)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  CloseOutlined,
  PlusOutlined,
  MinusOutlined,
  AimOutlined
} from '@ant-design/icons-vue'

interface Province {
  code: string
  name: string
  enterprises: number
  cities: string[]
  keyEnterprises: {
    id: string
    name: string
    type: string
    city: string
    scale: string
  }[]
}

const router = useRouter()

// 响应式数据
const selectedIndustry = ref('petrochemical')
const selectedProvince = ref<Province | null>(null)
const showHeatmap = ref(true)
const mapContainer = ref<HTMLElement>()

// KPI数据
const totalEnterprises = ref(15432)
const upstreamCount = ref(3245)
const midstreamCount = ref(5678)
const downstreamCount = ref(6509)

// 产业名称映射
const industryNames: Record<string, string> = {
  all: '全部',
  petrochemical: '石油化工',
  bigdata: '大数据',
  newenergy: '新能源'
}

const selectedIndustryName = computed(() => {
  return industryNames[selectedIndustry.value] || '全部'
})

// 省份数据
const provinces = ref<Province[]>([
  {
    code: 'SD',
    name: '山东省',
    enterprises: 3245,
    cities: ['青岛', '济南', '烟台'],
    keyEnterprises: [
      { id: '1', name: '山东海化', type: '国企', city: '烟台', scale: '大型' },
      { id: '2', name: '东明石化', type: '民企', city: '菏泽', scale: '大型' },
      { id: '3', name: '万华化学', type: '民企', city: '烟台', scale: '大型' }
    ]
  },
  {
    code: 'GD',
    name: '广东省',
    enterprises: 2856,
    cities: ['深圳', '广州', '东莞'],
    keyEnterprises: [
      { id: '4', name: '中海油', type: '央企', city: '深圳', scale: '特大型' },
      { id: '5', name: '巴斯夫', type: '外企', city: '湛江', scale: '大型' }
    ]
  },
  {
    code: 'JS',
    name: '江苏省',
    enterprises: 2634,
    cities: ['南京', '苏州', '无锡'],
    keyEnterprises: [
      { id: '6', name: '扬子石化', type: '央企', city: '南京', scale: '大型' },
      { id: '7', name: '恒力石化', type: '民企', city: '苏州', scale: '大型' }
    ]
  },
  {
    code: 'ZJ',
    name: '浙江省',
    enterprises: 1967,
    cities: ['杭州', '宁波', '嘉兴'],
    keyEnterprises: [
      { id: '8', name: '浙江石化', type: '民企', city: '舟山', scale: '大型' },
      { id: '9', name: '新和成', type: '民企', city: '绍兴', scale: '中型' }
    ]
  },
  {
    code: 'HB',
    name: '河北省',
    enterprises: 1543,
    cities: ['石家庄', '唐山', '邯郸'],
    keyEnterprises: [
      { id: '10', name: '河北宇意', type: '民企', city: '石家庄', scale: '中型' }
    ]
  },
  {
    code: 'LN',
    name: '辽宁省',
    enterprises: 1234,
    cities: ['大连', '沈阳', '盘锦'],
    keyEnterprises: [
      { id: '11', name: '大连化工', type: '国企', city: '大连', scale: '大型' }
    ]
  }
])

// 产业切换
const onIndustryChange = (value: string) => {
  selectedIndustry.value = value
  selectedProvince.value = null
  console.log('切换产业:', value)
}

// 选择省份
const selectProvince = (province: Province) => {
  selectedProvince.value = province
}

// 关闭省份面板
const closeProvincePanel = () => {
  selectedProvince.value = null
}

// 查看企业详情
const viewEnterpriseDetail = (enterpriseId: string) => {
  router.push(`/resources/enterprises/${enterpriseId}`)
}

// 查看全部企业
const viewAllEnterprises = () => {
  if (selectedProvince.value) {
    router.push({
      path: '/resources/enterprises',
      query: { 
        province: selectedProvince.value.code,
        industry: selectedIndustry.value
      }
    })
  }
}

// 地图控制
const zoomIn = () => {
  console.log('放大地图')
}

const zoomOut = () => {
  console.log('缩小地图')
}

const resetMapView = () => {
  console.log('重置地图视图')
  selectedProvince.value = null
}
</script>

<style scoped lang="less">
.enterprise-map {
  height: 100vh;
  background: var(--primary-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 229, 255, 0.2);
  
  .header-left {
    .map-title {
      font-size: 24px;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }
    
    .map-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
      margin: 0;
    }
  }
}

.kpi-section {
  padding: 16px 24px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.kpi-card {
  background: rgba(26, 32, 68, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--primary-color);
    box-shadow: 0 8px 32px rgba(0, 229, 255, 0.2);
  }
  
  .kpi-icon {
    font-size: 32px;
    margin-right: 16px;
  }
  
  .kpi-content {
    .kpi-value {
      font-size: 24px;
      font-weight: bold;
      color: var(--primary-color);
      text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    
    .kpi-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 4px;
    }
  }
}

.map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-content {
  display: flex;
  height: 100%;
}

.china-map {
  flex: 1;
  
  .map-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .placeholder-content {
      text-align: center;
      
      .map-icon {
        font-size: 64px;
        margin-bottom: 16px;
      }
      
      h3 {
        color: var(--text-primary);
        margin-bottom: 8px;
      }
      
      p {
        color: var(--text-secondary);
        margin-bottom: 32px;
      }
      
      .mock-provinces {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        max-width: 800px;
        
        .province-item {
          background: rgba(26, 32, 68, 0.6);
          border: 1px solid rgba(0, 229, 255, 0.2);
          border-radius: 8px;
          padding: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          
          &.medium-density {
            border-color: rgba(255, 215, 0, 0.5);
            background: rgba(255, 215, 0, 0.1);
          }
          
          &.high-density {
            border-color: rgba(255, 69, 58, 0.5);
            background: rgba(255, 69, 58, 0.1);
          }
          
          &:hover {
            border-color: var(--primary-color);
            box-shadow: 0 4px 16px rgba(0, 229, 255, 0.2);
          }
          
          .province-name {
            color: var(--text-primary);
            font-weight: bold;
            margin-bottom: 4px;
          }
          
          .province-count {
            color: var(--primary-color);
            font-size: 12px;
          }
        }
      }
    }
  }
}

.enterprise-panel {
  width: 400px;
  background: rgba(26, 32, 68, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 0;
  margin: 0;
  height: 100%;
  overflow-y: auto;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(0, 229, 255, 0.2);
    
    h3 {
      color: var(--text-primary);
      margin: 0;
      font-size: 16px;
    }
  }
  
  .panel-content {
    padding: 20px;
  }
  
  .province-stats {
    margin-bottom: 24px;
    
    .stat-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      
      .stat-label {
        color: var(--text-secondary);
      }
      
      .stat-value {
        color: var(--primary-color);
        font-weight: bold;
      }
    }
  }
  
  .enterprise-list {
    h4 {
      color: var(--text-primary);
      margin-bottom: 16px;
      font-size: 14px;
    }
    
    .enterprise-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: rgba(0, 229, 255, 0.1);
      border: 1px solid rgba(0, 229, 255, 0.2);
      border-radius: 8px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--primary-color);
        background: rgba(0, 229, 255, 0.2);
      }
      
      .enterprise-info {
        .enterprise-name {
          color: var(--text-primary);
          font-weight: 500;
          margin-bottom: 4px;
        }
        
        .enterprise-meta {
          font-size: 12px;
          
          .enterprise-type,
          .enterprise-city {
            color: var(--text-secondary);
            margin-right: 8px;
          }
        }
      }
      
      .enterprise-scale {
        color: var(--primary-color);
        font-size: 12px;
        font-weight: bold;
      }
    }
  }
  
  .panel-footer {
    margin-top: 24px;
    
    .ant-btn {
      background: var(--primary-color);
      border-color: var(--primary-color);
      
      &:hover {
        background: rgba(0, 229, 255, 0.8);
        border-color: rgba(0, 229, 255, 0.8);
      }
    }
  }
}

.map-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  .zoom-controls {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .ant-btn {
      background: rgba(26, 32, 68, 0.8);
      border-color: rgba(0, 229, 255, 0.3);
      color: var(--primary-color);
      
      &:hover {
        border-color: var(--primary-color);
        background: var(--primary-color);
        color: var(--primary-bg);
      }
    }
  }
  
  .layer-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(26, 32, 68, 0.8);
    border: 1px solid rgba(0, 229, 255, 0.3);
    border-radius: 6px;
    
    .control-label {
      color: var(--text-secondary);
      font-size: 12px;
    }
  }
}

.map-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(26, 32, 68, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 12px;
  padding: 16px;
  
  h4 {
    color: var(--text-primary);
    margin-bottom: 12px;
    font-size: 14px;
  }
  
  .legend-items {
    .legend-item {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      font-size: 12px;
      color: var(--text-secondary);
      
      .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        margin-right: 8px;
        
        &.high { background: rgba(255, 69, 58, 0.6); }
        &.medium { background: rgba(255, 215, 0, 0.6); }
        &.low { background: rgba(0, 229, 255, 0.3); }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .map-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .map-content {
    flex-direction: column;
  }
  
  .enterprise-panel {
    width: 100%;
    height: 300px;
  }
  
  .map-legend {
    display: none;
  }
}
</style> 