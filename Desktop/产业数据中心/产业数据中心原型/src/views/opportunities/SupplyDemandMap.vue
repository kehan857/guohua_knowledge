<template>
  <div class="supply-demand-map">
    <!-- 左侧KPI统计 -->
    <div class="left-panel">
      <div class="kpi-stats">
        <h2 class="panel-title">供需概览</h2>
        
        <div class="stat-card glass-card glow-element">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">{{ totalDemands.toLocaleString() }}</div>
            <div class="stat-label">总需求量</div>
          </div>
        </div>
        
        <div class="stat-card glass-card glow-element">
          <div class="stat-icon">🆕</div>
          <div class="stat-content">
            <div class="stat-value">{{ todayNew.toLocaleString() }}</div>
            <div class="stat-label">今日新增</div>
          </div>
        </div>
        
        <div class="stat-card glass-card glow-element">
          <div class="stat-icon">🔥</div>
          <div class="stat-content">
            <div class="stat-value">{{ hotDemands.toLocaleString() }}</div>
            <div class="stat-label">热门需求</div>
          </div>
        </div>
        
        <div class="stat-card glass-card glow-element">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <div class="stat-value">{{ matchedCount.toLocaleString() }}</div>
            <div class="stat-label">已匹配</div>
          </div>
        </div>
      </div>
      
      <!-- 需求分类筛选 -->
      <div class="filter-section">
        <h3 class="filter-title">需求分类</h3>
        <div class="category-filters">
          <div 
            v-for="category in demandCategories" 
            :key="category.id"
            class="category-item"
            :class="{ active: selectedCategory === category.id }"
            @click="selectCategory(category.id)"
          >
            <div class="category-icon">{{ category.icon }}</div>
            <div class="category-info">
              <div class="category-name">{{ category.name }}</div>
              <div class="category-count">{{ category.count }}个</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 中间地图区域 -->
    <div class="map-section">
      <div class="map-header">
        <h1 class="map-title">全国供需分布地图</h1>
        <div class="map-controls">
          <a-select v-model:value="timeRange" style="width: 120px">
            <a-select-option value="all">全部时间</a-select-option>
            <a-select-option value="week">最近一周</a-select-option>
            <a-select-option value="month">最近一月</a-select-option>
          </a-select>
        </div>
      </div>
      
      <div ref="mapContainer" class="demand-map">
        <div class="map-placeholder">
          <div class="placeholder-content">
            <div class="map-icon">🌍</div>
            <h3>供需分布热力图</h3>
            <p>点击省份查看具体需求信息</p>
            
            <!-- 模拟需求热力图 -->
            <div class="demand-heatmap">
              <div 
                v-for="region in demandRegions" 
                :key="region.code"
                class="region-item"
                :class="{ 
                  'high-demand': region.demands > 100, 
                  'medium-demand': region.demands > 50,
                  'selected': selectedRegion === region.code
                }"
                @click="selectRegion(region)"
              >
                <div class="region-name">{{ region.name }}</div>
                <div class="region-demands">{{ region.demands }}个需求</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧需求列表 -->
    <div class="right-panel">
      <div class="demand-list">
        <div class="list-header">
          <h3>{{ selectedRegionName || '全国' }}需求列表</h3>
          <a-button type="text" size="small" @click="refreshDemands">
            <template #icon><reload-outlined /></template>
          </a-button>
        </div>
        
        <div class="demand-filters">
          <a-input 
            v-model:value="searchKeyword" 
            placeholder="搜索需求关键词"
            size="small"
            @input="onSearch"
          >
            <template #prefix><search-outlined /></template>
          </a-input>
        </div>
        
        <div class="demand-items">
          <div 
            v-for="demand in filteredDemands" 
            :key="demand.id"
            class="demand-item glass-card"
            @click="viewDemandDetail(demand.id)"
          >
            <div class="demand-header">
              <div class="demand-title">{{ demand.title }}</div>
              <div class="demand-status" :class="demand.status">
                {{ getStatusText(demand.status) }}
              </div>
            </div>
            
            <div class="demand-meta">
              <div class="meta-item">
                <span class="meta-label">发布单位：</span>
                <span class="meta-value">{{ demand.publisher }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">预算金额：</span>
                <span class="meta-value budget">{{ demand.budget }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">截止时间：</span>
                <span class="meta-value">{{ demand.deadline }}</span>
              </div>
            </div>
            
            <div class="demand-tags">
              <a-tag v-for="tag in demand.tags" :key="tag" size="small">
                {{ tag }}
              </a-tag>
            </div>
            
            <!-- 智能匹配显示 -->
            <div v-if="demand.matchScore" class="match-info">
              <div class="match-score">
                <span class="score-label">匹配度：</span>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: demand.matchScore + '%' }"></div>
                </div>
                <span class="score-text">{{ demand.matchScore }}%</span>
              </div>
              <div class="match-reason">{{ demand.matchReason }}</div>
            </div>
          </div>
        </div>
        
        <div class="list-footer">
          <a-pagination 
            v-model:current="currentPage"
            :total="totalCount"
            :page-size="pageSize"
            size="small"
            show-size-changer
            @change="onPageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ReloadOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'

interface DemandCategory {
  id: string
  name: string
  icon: string
  count: number
}

interface DemandRegion {
  code: string
  name: string
  demands: number
}

interface Demand {
  id: string
  title: string
  publisher: string
  budget: string
  deadline: string
  status: 'active' | 'closed' | 'pending'
  tags: string[]
  location: string
  matchScore?: number
  matchReason?: string
}

const router = useRouter()

// 响应式数据
const selectedCategory = ref('all')
const selectedRegion = ref('')
const timeRange = ref('all')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const mapContainer = ref<HTMLElement>()

// KPI数据
const totalDemands = ref(1257)
const todayNew = ref(68)
const hotDemands = ref(234)
const matchedCount = ref(89)

// 需求分类数据
const demandCategories = ref<DemandCategory[]>([
  { id: 'all', name: '全部需求', icon: '📋', count: 1257 },
  { id: 'equipment', name: '设备采购', icon: '⚙️', count: 456 },
  { id: 'service', name: '服务招标', icon: '🛠️', count: 234 },
  { id: 'project', name: '工程项目', icon: '🏗️', count: 189 },
  { id: 'maintenance', name: '维修保养', icon: '🔧', count: 156 },
  { id: 'consulting', name: '咨询服务', icon: '💡', count: 122 },
  { id: 'technology', name: '技术开发', icon: '🔬', count: 100 }
])

// 地区需求数据
const demandRegions = ref<DemandRegion[]>([
  { code: 'BJ', name: '北京', demands: 156 },
  { code: 'SH', name: '上海', demands: 134 },
  { code: 'GD', name: '广东', demands: 189 },
  { code: 'JS', name: '江苏', demands: 145 },
  { code: 'ZJ', name: '浙江', demands: 123 },
  { code: 'SD', name: '山东', demands: 167 },
  { code: 'HB', name: '河北', demands: 89 },
  { code: 'HN', name: '河南', demands: 78 },
  { code: 'SC', name: '四川', demands: 67 },
  { code: 'HUB', name: '湖北', demands: 56 }
])

// 需求列表数据
const demandList = ref<Demand[]>([
  {
    id: '1',
    title: '化工设备维护保养服务招标',
    publisher: '中石化胜利油田',
    budget: '500万元',
    deadline: '2024-07-15',
    status: 'active',
    tags: ['化工设备', '维护保养', '胜利油田'],
    location: '山东',
    matchScore: 95,
    matchReason: '公司具有丰富的化工设备维护经验'
  },
  {
    id: '2',
    title: '石油化工智能监控系统采购',
    publisher: '万华化学集团',
    budget: '1200万元',
    deadline: '2024-07-20',
    status: 'active',
    tags: ['智能监控', '化工系统', '万华化学'],
    location: '山东',
    matchScore: 87,
    matchReason: '产品符合化工行业智能化需求'
  },
  {
    id: '3',
    title: '炼油厂环保设备升级改造',
    publisher: '中海油天津炼化',
    budget: '800万元',
    deadline: '2024-08-01',
    status: 'pending',
    tags: ['环保设备', '炼油厂', '升级改造'],
    location: '天津',
    matchScore: 78,
    matchReason: '环保技术与项目需求匹配度较高'
  },
  {
    id: '4',
    title: '化工园区安全监测平台建设',
    publisher: '上海化工区管委会',
    budget: '2000万元',
    deadline: '2024-08-10',
    status: 'active',
    tags: ['安全监测', '化工园区', '平台建设'],
    location: '上海'
  },
  {
    id: '5',
    title: '石化企业数字化转型咨询服务',
    publisher: '浙江石化有限公司',
    budget: '300万元',
    deadline: '2024-07-25',
    status: 'closed',
    tags: ['数字化转型', '咨询服务', '浙江石化'],
    location: '浙江'
  }
])

// 计算属性
const selectedRegionName = computed(() => {
  if (!selectedRegion.value) return null
  const region = demandRegions.value.find(r => r.code === selectedRegion.value)
  return region?.name
})

const filteredDemands = computed(() => {
  let filtered = demandList.value

  // 按地区筛选
  if (selectedRegion.value) {
    filtered = filtered.filter(demand => 
      demand.location.includes(selectedRegionName.value || '')
    )
  }

  // 按分类筛选
  if (selectedCategory.value !== 'all') {
    // 这里可以根据实际需求分类逻辑进行筛选
    filtered = filtered.filter(demand => {
      // 简单的关键词匹配
      const categoryMap: Record<string, string[]> = {
        equipment: ['设备', '采购'],
        service: ['服务', '招标'],
        project: ['项目', '建设'],
        maintenance: ['维护', '保养'],
        consulting: ['咨询', '服务'],
        technology: ['技术', '开发']
      }
      const keywords = categoryMap[selectedCategory.value] || []
      return keywords.some(keyword => demand.title.includes(keyword))
    })
  }

  // 按关键词搜索
  if (searchKeyword.value) {
    filtered = filtered.filter(demand =>
      demand.title.includes(searchKeyword.value) ||
      demand.publisher.includes(searchKeyword.value) ||
      demand.tags.some(tag => tag.includes(searchKeyword.value))
    )
  }

  return filtered
})

const totalCount = computed(() => filteredDemands.value.length)

// 方法
const selectCategory = (categoryId: string) => {
  selectedCategory.value = categoryId
  currentPage.value = 1
}

const selectRegion = (region: DemandRegion) => {
  selectedRegion.value = selectedRegion.value === region.code ? '' : region.code
}

const refreshDemands = () => {
  console.log('刷新需求列表')
}

const onSearch = () => {
  currentPage.value = 1
}

const onPageChange = (page: number) => {
  currentPage.value = page
}

const viewDemandDetail = (demandId: string) => {
  router.push(`/resources/demands/${demandId}`)
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '进行中',
    closed: '已结束',
    pending: '待开始'
  }
  return statusMap[status] || status
}
</script>

<style scoped lang="less">
.supply-demand-map {
  height: 100vh;
  background: var(--primary-bg);
  display: flex;
  overflow: hidden;
}

// 左侧面板
.left-panel {
  width: 300px;
  background: rgba(26, 32, 68, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 229, 255, 0.2);
  overflow-y: auto;
  
  .kpi-stats {
    padding: 20px;
    
    .panel-title {
      color: var(--text-primary);
      margin-bottom: 20px;
      font-size: 18px;
      text-align: center;
    }
    
    .stat-card {
      background: rgba(26, 32, 68, 0.8);
      border: 1px solid rgba(0, 229, 255, 0.3);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 16px rgba(0, 229, 255, 0.2);
      }
      
      .stat-icon {
        font-size: 24px;
        margin-right: 12px;
      }
      
      .stat-content {
        .stat-value {
          font-size: 20px;
          font-weight: bold;
          color: var(--primary-color);
          text-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
        }
        
        .stat-label {
          font-size: 12px;
          color: var(--text-secondary);
          margin-top: 2px;
        }
      }
    }
  }
  
  .filter-section {
    padding: 0 20px 20px;
    border-top: 1px solid rgba(0, 229, 255, 0.2);
    
    .filter-title {
      color: var(--text-primary);
      margin: 20px 0 16px;
      font-size: 16px;
    }
    
    .category-filters {
      .category-item {
        display: flex;
        align-items: center;
        padding: 12px;
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 6px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover,
        &.active {
          border-color: var(--primary-color);
          background: rgba(0, 229, 255, 0.1);
        }
        
        .category-icon {
          font-size: 16px;
          margin-right: 10px;
        }
        
        .category-info {
          .category-name {
            color: var(--text-primary);
            font-size: 14px;
            margin-bottom: 2px;
          }
          
          .category-count {
            color: var(--text-secondary);
            font-size: 12px;
          }
        }
      }
    }
  }
}

// 中间地图区域
.map-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  .map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid rgba(0, 229, 255, 0.2);
    
    .map-title {
      color: var(--text-primary);
      margin: 0;
      font-size: 20px;
    }
  }
  
  .demand-map {
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
        
        .demand-heatmap {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 12px;
          max-width: 600px;
          
          .region-item {
            background: rgba(26, 32, 68, 0.6);
            border: 1px solid rgba(0, 229, 255, 0.2);
            border-radius: 6px;
            padding: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            
            &.medium-demand {
              border-color: rgba(255, 215, 0, 0.5);
              background: rgba(255, 215, 0, 0.1);
            }
            
            &.high-demand {
              border-color: rgba(255, 69, 58, 0.5);
              background: rgba(255, 69, 58, 0.1);
            }
            
            &.selected,
            &:hover {
              border-color: var(--primary-color);
              box-shadow: 0 4px 16px rgba(0, 229, 255, 0.2);
            }
            
            .region-name {
              color: var(--text-primary);
              font-weight: bold;
              margin-bottom: 4px;
              font-size: 12px;
            }
            
            .region-demands {
              color: var(--primary-color);
              font-size: 11px;
            }
          }
        }
      }
    }
  }
}

// 右侧面板
.right-panel {
  width: 400px;
  background: rgba(26, 32, 68, 0.95);
  backdrop-filter: blur(10px);
  border-left: 1px solid rgba(0, 229, 255, 0.2);
  
  .demand-list {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    .list-header {
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
    
    .demand-filters {
      padding: 16px 20px;
      border-bottom: 1px solid rgba(0, 229, 255, 0.2);
    }
    
    .demand-items {
      flex: 1;
      padding: 16px 20px;
      overflow-y: auto;
      
      .demand-item {
        background: rgba(26, 32, 68, 0.8);
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: var(--primary-color);
          box-shadow: 0 4px 16px rgba(0, 229, 255, 0.2);
        }
        
        .demand-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .demand-title {
            color: var(--text-primary);
            font-weight: 500;
            font-size: 14px;
            line-height: 1.4;
            flex: 1;
            margin-right: 8px;
          }
          
          .demand-status {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            
            &.active {
              background: rgba(0, 255, 0, 0.2);
              color: #00ff00;
            }
            
            &.pending {
              background: rgba(255, 215, 0, 0.2);
              color: #ffd700;
            }
            
            &.closed {
              background: rgba(128, 128, 128, 0.2);
              color: #808080;
            }
          }
        }
        
        .demand-meta {
          margin-bottom: 12px;
          
          .meta-item {
            display: flex;
            margin-bottom: 4px;
            font-size: 12px;
            
            .meta-label {
              color: var(--text-secondary);
              width: 70px;
            }
            
            .meta-value {
              color: var(--text-primary);
              
              &.budget {
                color: var(--primary-color);
                font-weight: bold;
              }
            }
          }
        }
        
        .demand-tags {
          margin-bottom: 12px;
          
          .ant-tag {
            background: rgba(0, 229, 255, 0.1);
            border-color: rgba(0, 229, 255, 0.3);
            color: var(--primary-color);
            font-size: 11px;
          }
        }
        
        .match-info {
          border-top: 1px solid rgba(0, 229, 255, 0.2);
          padding-top: 12px;
          
          .match-score {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            
            .score-label {
              color: var(--text-secondary);
              font-size: 12px;
              margin-right: 8px;
            }
            
            .score-bar {
              flex: 1;
              height: 4px;
              background: rgba(0, 229, 255, 0.2);
              border-radius: 2px;
              margin-right: 8px;
              overflow: hidden;
              
              .score-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary-color), var(--accent-gold));
                transition: width 0.3s ease;
              }
            }
            
            .score-text {
              color: var(--primary-color);
              font-size: 12px;
              font-weight: bold;
            }
          }
          
          .match-reason {
            color: var(--text-secondary);
            font-size: 11px;
            line-height: 1.4;
          }
        }
      }
    }
    
    .list-footer {
      padding: 16px 20px;
      border-top: 1px solid rgba(0, 229, 255, 0.2);
      
      .ant-pagination {
        text-align: center;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .left-panel {
    width: 250px;
  }
  
  .right-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .supply-demand-map {
    flex-direction: column;
  }
  
  .left-panel,
  .right-panel {
    width: 100%;
    height: 200px;
  }
  
  .map-section {
    height: 300px;
  }
}
</style> 