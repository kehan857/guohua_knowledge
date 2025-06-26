<template>
  <div class="product-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">产品库</h1>
        <p class="page-description">公司产品与解决方案统一展示平台</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="refreshData">
          <template #icon><reload-outlined /></template>
          刷新数据
        </a-button>
        <a-button type="primary" @click="exportData">
          <template #icon><download-outlined /></template>
          导出数据
        </a-button>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <div class="filter-row">
        <a-input 
          v-model:value="searchKeyword" 
          placeholder="搜索产品名称、类别或关键词"
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix><search-outlined /></template>
        </a-input>
        
        <a-select 
          v-model:value="selectedCategory" 
          placeholder="产品分类"
          style="width: 150px"
          @change="handleFilter"
        >
          <a-select-option value="">全部分类</a-select-option>
          <a-select-option value="software">软件产品</a-select-option>
          <a-select-option value="hardware">硬件设备</a-select-option>
          <a-select-option value="solution">解决方案</a-select-option>
          <a-select-option value="service">技术服务</a-select-option>
        </a-select>
        
        <a-select 
          v-model:value="selectedStatus" 
          placeholder="产品状态"
          style="width: 120px"
          @change="handleFilter"
        >
          <a-select-option value="">全部状态</a-select-option>
          <a-select-option value="active">在售</a-select-option>
          <a-select-option value="developing">开发中</a-select-option>
          <a-select-option value="discontinued">已停产</a-select-option>
        </a-select>
        
        <a-select 
          v-model:value="selectedIndustry" 
          placeholder="适用行业"
          style="width: 150px"
          @change="handleFilter"
        >
          <a-select-option value="">全部行业</a-select-option>
          <a-select-option value="petrochemical">石油化工</a-select-option>
          <a-select-option value="energy">新能源</a-select-option>
          <a-select-option value="manufacturing">智能制造</a-select-option>
          <a-select-option value="government">政务服务</a-select-option>
        </a-select>
        
        <a-button @click="resetFilters">重置</a-button>
      </div>
    </div>

    <!-- KPI统计 -->
    <div class="kpi-section">
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon">📦</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ filteredProducts.length }}</div>
            <div class="kpi-label">当前显示</div>
          </div>
        </div>
        
        <div class="kpi-card">
          <div class="kpi-icon">🚀</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ activeProducts }}</div>
            <div class="kpi-label">在售产品</div>
          </div>
        </div>
        
        <div class="kpi-card">
          <div class="kpi-icon">⭐</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ hottestProducts }}</div>
            <div class="kpi-label">热门产品</div>
          </div>
        </div>
        
        <div class="kpi-card">
          <div class="kpi-icon">🔧</div>
          <div class="kpi-content">
            <div class="kpi-value">{{ developingProducts }}</div>
            <div class="kpi-label">开发中</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 产品展示区域 -->
    <div class="products-grid">
      <div class="product-card glass-card glow-element" v-for="product in paginatedProducts" :key="product.id">
        <div class="product-image">
          <!-- 软件产品图标 -->
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none" v-if="product.category === 'software'">
            <defs>
              <linearGradient id="software-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#00E5FF"/>
                <stop offset="100%" style="stop-color:#1976D2"/>
              </linearGradient>
            </defs>
            <rect x="10" y="15" width="60" height="50" fill="url(#software-gradient)" rx="8"/>
            <rect x="15" y="20" width="50" height="40" fill="rgba(13, 17, 23, 0.9)" rx="4"/>
            <rect x="20" y="25" width="40" height="3" fill="#4CAF50" rx="1"/>
            <rect x="20" y="30" width="35" height="3" fill="#FFD700" rx="1"/>
            <rect x="20" y="35" width="30" height="3" fill="#FF5722" rx="1"/>
            <rect x="20" y="40" width="25" height="3" fill="#9C27B0" rx="1"/>
            <rect x="20" y="45" width="20" height="3" fill="#00E5FF" rx="1"/>
            <circle cx="25" cy="52" r="2" fill="#4CAF50"/>
            <circle cx="35" cy="52" r="2" fill="#FFD700"/>
            <circle cx="45" cy="52" r="2" fill="#FF5722"/>
          </svg>
          
          <!-- 硬件设备图标 -->
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none" v-else-if="product.category === 'hardware'">
            <defs>
              <linearGradient id="hardware-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#4CAF50"/>
                <stop offset="100%" style="stop-color:#2E7D32"/>
              </linearGradient>
            </defs>
            <circle cx="40" cy="40" r="25" fill="url(#hardware-gradient)"/>
            <circle cx="40" cy="40" r="15" fill="rgba(255,255,255,0.2)"/>
            <circle cx="40" cy="40" r="8" fill="#FFD700"/>
            <rect x="8" y="38" width="15" height="4" fill="#00E5FF" rx="2"/>
            <rect x="57" y="38" width="15" height="4" fill="#00E5FF" rx="2"/>
            <rect x="38" y="8" width="4" height="15" fill="#00E5FF" rx="2"/>
            <rect x="38" y="57" width="4" height="15" fill="#00E5FF" rx="2"/>
            <circle cx="25" cy="25" r="2" fill="#FFD700"/>
            <circle cx="55" cy="25" r="2" fill="#FFD700"/>
            <circle cx="25" cy="55" r="2" fill="#FFD700"/>
            <circle cx="55" cy="55" r="2" fill="#FFD700"/>
          </svg>
          
          <!-- 解决方案图标 -->
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none" v-else-if="product.category === 'solution'">
            <defs>
              <linearGradient id="solution-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#FF9800"/>
                <stop offset="100%" style="stop-color:#F57C00"/>
              </linearGradient>
            </defs>
            <rect x="15" y="20" width="50" height="35" fill="url(#solution-gradient)" rx="4"/>
            <rect x="20" y="25" width="40" height="25" fill="rgba(13, 17, 23, 0.9)" rx="2"/>
            <rect x="25" y="30" width="30" height="3" fill="#4CAF50" rx="1"/>
            <rect x="25" y="35" width="25" height="3" fill="#FFD700" rx="1"/>
            <rect x="25" y="40" width="20" height="3" fill="#FF5722" rx="1"/>
            <circle cx="60" cy="30" r="2" fill="#00E5FF"/>
            <circle cx="60" cy="40" r="2" fill="#4CAF50"/>
            <rect x="30" y="60" width="20" height="8" fill="#666" rx="2"/>
            <!-- 网络连接线 -->
            <path d="M10,15 Q25,10 40,15 Q55,20 70,15" stroke="#00E5FF" stroke-width="2" fill="none"/>
            <path d="M10,65 Q25,70 40,65 Q55,60 70,65" stroke="#00E5FF" stroke-width="2" fill="none"/>
          </svg>
          
          <!-- 默认服务图标 -->
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none" v-else>
            <defs>
              <linearGradient id="service-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#9C27B0"/>
                <stop offset="100%" style="stop-color:#6A1B9A"/>
              </linearGradient>
            </defs>
            <rect x="20" y="20" width="40" height="40" fill="url(#service-gradient)" rx="8"/>
            <rect x="25" y="25" width="30" height="30" fill="rgba(255,255,255,0.1)" rx="4"/>
            <circle cx="40" cy="40" r="8" fill="#FFD700"/>
            <circle cx="30" cy="30" r="2" fill="#00E5FF"/>
            <circle cx="50" cy="30" r="2" fill="#00E5FF"/>
            <circle cx="30" cy="50" r="2" fill="#4CAF50"/>
            <circle cx="50" cy="50" r="2" fill="#4CAF50"/>
          </svg>
        </div>
        
        <div class="product-info">
          <h4 class="product-name">{{ product.name }}</h4>
          <div class="product-category">{{ getCategoryText(product.category) }}</div>
          <div class="product-description">{{ product.description }}</div>
          
          <div class="product-specs">
            <div class="spec-item">
              <span class="spec-label">价格</span>
              <span class="spec-value">{{ product.price || '暂无报价' }}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">供应商</span>
              <span class="spec-value">{{ product.supplier }}</span>
            </div>
          </div>
          
          <div class="product-tags">
            <span class="tag" v-for="tag in product.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        
        <div class="product-actions">
          <a-button type="primary" size="small" @click="viewDetails(product.id)">
            查看详情
          </a-button>
          <a-button size="small" @click="contact(product.supplier)">
            联系供应商
          </a-button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.pageSize"
        :total="filteredProducts.length"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total: number) => `共 ${total} 条记录`"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  StarOutlined,
  EyeOutlined
} from '@ant-design/icons-vue'

interface Product {
  id: string
  name: string
  description: string
  category: string
  status: 'active' | 'developing' | 'discontinued'
  industry: string
  version: string
  tags: string[]
  image: string
  rating: number
  views: number
  price?: string
  supplier: string
}

const router = useRouter()

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const selectedCategory = ref('')
const selectedStatus = ref('')
const selectedIndustry = ref('')

// 统计数据
const activeProducts = ref(45)
const hottestProducts = ref(12)
const developingProducts = ref(8)

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 12
})

// 模拟产品数据
const productList = ref<Product[]>([
  {
    id: '1',
    name: '智能化工监控平台',
    description: '基于AI技术的化工安全监控与预警系统，提供全方位安全保障',
    category: 'software',
    status: 'active',
    industry: 'petrochemical',
    version: 'v3.2.1',
    tags: ['AI监控', '安全预警', '智能分析'],
    image: 'https://via.placeholder.com/300x200?text=智能监控平台',
    rating: 4.8,
    views: 2340,
    price: '面议',
    supplier: 'ABC公司'
  },
  {
    id: '2',
    name: '石化设备运维系统',
    description: '专业的石化设备全生命周期管理系统，提升设备效率',
    category: 'solution',
    status: 'active',
    industry: 'petrochemical',
    version: 'v2.1.0',
    tags: ['设备管理', '预测维护', '数据分析'],
    image: 'https://via.placeholder.com/300x200?text=运维系统',
    rating: 4.6,
    views: 1890,
    price: '680万起',
    supplier: 'DEF公司'
  },
  {
    id: '3',
    name: '工业物联网网关',
    description: '高性能工业级物联网数据采集与传输设备',
    category: 'hardware',
    status: 'active',
    industry: 'manufacturing',
    version: 'v1.5.2',
    tags: ['物联网', '数据采集', '边缘计算'],
    image: 'https://via.placeholder.com/300x200?text=物联网网关',
    rating: 4.7,
    views: 1560,
    price: '12,800元/台',
    supplier: 'GHI公司'
  },
  {
    id: '4',
    name: '新能源管理平台',
    description: '综合新能源发电、储能、配电的智能管理平台',
    category: 'software',
    status: 'developing',
    industry: 'energy',
    version: 'v1.0.0-beta',
    tags: ['新能源', '智能调度', '能效管理'],
    image: 'https://via.placeholder.com/300x200?text=新能源平台',
    rating: 4.5,
    views: 980,
    price: '开发中',
    supplier: 'JKL公司'
  },
  {
    id: '5',
    name: '政务数据治理平台',
    description: '政府数据资源统一管理与共享平台',
    category: 'solution',
    status: 'active',
    industry: 'government',
    version: 'v2.3.1',
    tags: ['数据治理', '政务服务', '数据共享'],
    image: 'https://via.placeholder.com/300x200?text=政务平台',
    rating: 4.9,
    views: 3210,
    price: '定制化',
    supplier: 'MNO公司'
  },
  {
    id: '6',
    name: '云原生微服务框架',
    description: '企业级云原生应用开发框架，支持快速构建微服务应用',
    category: 'software',
    status: 'active',
    industry: 'manufacturing',
    version: 'v4.1.0',
    tags: ['云原生', '微服务', '容器化'],
    image: 'https://via.placeholder.com/300x200?text=微服务框架',
    rating: 4.4,
    views: 1120,
    price: '开源免费',
    supplier: 'PQR公司'
  }
])

// 计算属性
const filteredProducts = computed(() => {
  let filtered = productList.value

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(product => 
      product.name.toLowerCase().includes(keyword) ||
      product.description.toLowerCase().includes(keyword) ||
      product.tags.some(tag => tag.toLowerCase().includes(keyword))
    )
  }

  if (selectedCategory.value) {
    filtered = filtered.filter(product => product.category === selectedCategory.value)
  }

  if (selectedStatus.value) {
    filtered = filtered.filter(product => product.status === selectedStatus.value)
  }

  if (selectedIndustry.value) {
    filtered = filtered.filter(product => product.industry === selectedIndustry.value)
  }

  return filtered
})

const paginatedProducts = computed(() => {
  const start = (pagination.value.current - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredProducts.value.slice(start, end)
})

// 方法
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    active: 'green',
    developing: 'orange',
    discontinued: 'red'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '在售',
    developing: '开发中',
    discontinued: '已停产'
  }
  return statusMap[status] || status
}

const getCategoryText = (category: string) => {
  const categoryMap: Record<string, string> = {
    software: '软件产品',
    hardware: '硬件设备',
    solution: '解决方案',
    service: '技术服务'
  }
  return categoryMap[category] || category
}

const getIndustryText = (industry: string) => {
  const industryMap: Record<string, string> = {
    petrochemical: '石油化工',
    energy: '新能源',
    manufacturing: '智能制造',
    government: '政务服务'
  }
  return industryMap[industry] || industry
}

const viewDetail = (productId: string) => {
  router.push(`/resources/products/${productId}`)
}

const addToFavorites = (productId: string) => {
  message.success('已添加到收藏夹')
}

const shareProduct = (productId: string) => {
  message.success('分享链接已复制到剪贴板')
}

const handleSearch = () => {
  pagination.value.current = 1
}

const handleFilter = () => {
  pagination.value.current = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedCategory.value = ''
  selectedStatus.value = ''
  selectedIndustry.value = ''
  pagination.value.current = 1
}

const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    message.success('数据刷新成功')
  }, 1000)
}

const exportData = () => {
  message.success('数据导出成功')
}

const handlePageChange = (page: number, pageSize: number) => {
  pagination.value.current = page
  pagination.value.pageSize = pageSize
}

const viewDetails = (productId: string) => {
  router.push(`/resources/products/${productId}`)
}

const contact = (supplier: string) => {
  message.success(`已发送联系请求给供应商: ${supplier}`)
}

onMounted(() => {
  // 初始化数据
})
</script>

<style scoped lang="less">
.product-list {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: bold;
      color: var(--text-primary);
      margin: 0 0 4px 0;
    }
    
    .page-description {
      color: var(--text-secondary);
      margin: 0;
    }
  }
  
  .header-right {
    display: flex;
    gap: 12px;
  }
}

.filter-toolbar {
  background: var(--component-bg);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  .filter-row {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
}

.kpi-section {
  margin-bottom: 24px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.kpi-card {
  background: var(--component-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    border-color: var(--primary-color);
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
      line-height: 1;
      margin-bottom: 4px;
    }
    
    .kpi-label {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.product-card {
  background: var(--component-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    border-color: var(--primary-color);
  }
}

.product-image {
  position: relative;
  height: 200px;
  overflow: hidden;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.product-info {
  padding: 20px;
}

.product-name {
  font-size: 18px;
  font-weight: bold;
  color: var(--text-primary);
  margin: 0;
  margin-bottom: 12px;
}

.product-category {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
}

.product-description {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-specs {
  margin-bottom: 16px;
}

.spec-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 12px;
  
  .spec-label {
    color: var(--light-text-secondary);
    width: 50px;
  }
  
  .spec-value {
    color: var(--light-text-primary);
    font-weight: 500;
  }
}

.product-tags {
  margin-bottom: 16px;
  
  .tag {
    margin-right: 4px;
  }
}

.product-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

// 响应式设计
@media (max-width: 768px) {
  .product-list {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .filter-toolbar .filter-row {
    flex-direction: column;
    align-items: stretch;
    
    > * {
      width: 100%;
    }
  }
  
  .products-grid {
    grid-template-columns: 1fr;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 