<template>
  <div class="enterprise-detail">
    <!-- 企业基本信息头部 -->
    <div class="enterprise-header">
      <div class="header-left">
        <a-button type="text" @click="goBack" class="back-btn">
          <template #icon><arrow-left-outlined /></template>
          返回列表
        </a-button>
        <div class="enterprise-basic">
          <h1 class="enterprise-name">{{ enterpriseInfo.name }}</h1>
          <div class="enterprise-meta">
            <a-tag :color="getTypeColor(enterpriseInfo.type)">{{ enterpriseInfo.type }}</a-tag>
            <span class="meta-item">{{ enterpriseInfo.industry }}</span>
            <span class="meta-item">{{ enterpriseInfo.location }}</span>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <div class="enterprise-stats">
          <div class="stat-item">
            <div class="stat-value">{{ enterpriseInfo.scale }}</div>
            <div class="stat-label">企业规模</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ enterpriseInfo.founded }}</div>
            <div class="stat-label">成立时间</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签页内容 -->
    <div class="detail-content">
      <a-tabs v-model:activeKey="activeTab" type="card" @change="onTabChange">
        <!-- 基本信息 -->
        <a-tab-pane key="basic" tab="基本信息">
          <div class="basic-info">
            <div class="info-grid">
              <div class="info-card">
                <h3>工商信息</h3>
                <div class="info-items">
                  <div class="info-item">
                    <span class="label">统一社会信用代码：</span>
                    <span class="value">{{ enterpriseInfo.creditCode }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">法定代表人：</span>
                    <span class="value">{{ enterpriseInfo.legalPerson }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">注册资本：</span>
                    <span class="value">{{ enterpriseInfo.registeredCapital }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">经营状态：</span>
                    <span class="value status active">{{ enterpriseInfo.status }}</span>
                  </div>
                </div>
              </div>

              <div class="info-card">
                <h3>联系信息</h3>
                <div class="info-items">
                  <div class="info-item">
                    <span class="label">注册地址：</span>
                    <span class="value">{{ enterpriseInfo.address }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">联系电话：</span>
                    <span class="value">{{ enterpriseInfo.phone }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">电子邮箱：</span>
                    <span class="value">{{ enterpriseInfo.email }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">官方网站：</span>
                    <span class="value link">{{ enterpriseInfo.website }}</span>
                  </div>
                </div>
              </div>

              <div class="info-card full-width">
                <h3>企业简介</h3>
                <div class="description">
                  {{ enterpriseInfo.description }}
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 产品与服务 -->
        <a-tab-pane key="products" tab="产品与服务">
          <div class="products-section">
            <div class="section-header">
              <h3>产品列表</h3>
              <a-input 
                v-model:value="productSearch" 
                placeholder="搜索产品"
                style="width: 200px"
                @input="filterProducts"
              >
                <template #prefix><search-outlined /></template>
              </a-input>
            </div>
            
            <div class="product-grid">
              <div 
                v-for="product in filteredProducts" 
                :key="product.id"
                class="product-card"
                @click="viewProduct(product.id)"
              >
                <div class="product-header">
                  <h4 class="product-name">{{ product.name }}</h4>
                  <a-tag :color="getCategoryColor(product.category)">
                    {{ product.category }}
                  </a-tag>
                </div>
                <div class="product-description">{{ product.description }}</div>
                <div class="product-footer">
                  <span class="product-price">{{ product.price }}</span>
                  <a-button type="link" size="small">查看详情</a-button>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 解决方案 -->
        <a-tab-pane key="solutions" tab="解决方案">
          <div class="solutions-section">
            <div class="solution-list">
              <div 
                v-for="solution in solutions" 
                :key="solution.id"
                class="solution-card"
              >
                <div class="solution-header">
                  <h4 class="solution-title">{{ solution.title }}</h4>
                  <div class="solution-tags">
                    <a-tag v-for="tag in solution.tags" :key="tag">{{ tag }}</a-tag>
                  </div>
                </div>
                <div class="solution-content">
                  <p class="solution-summary">{{ solution.summary }}</p>
                  <div class="solution-features">
                    <h5>核心特性：</h5>
                    <ul>
                      <li v-for="feature in solution.features" :key="feature">{{ feature }}</li>
                    </ul>
                  </div>
                </div>
                <div class="solution-footer">
                  <a-button type="primary" ghost>了解详情</a-button>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 相关需求 -->
        <a-tab-pane key="demands" tab="相关需求">
          <div class="demands-section">
            <div class="demand-list">
              <div 
                v-for="demand in demands" 
                :key="demand.id"
                class="demand-card"
                @click="viewDemand(demand.id)"
              >
                <div class="demand-header">
                  <h4 class="demand-title">{{ demand.title }}</h4>
                  <div class="demand-status" :class="demand.status">
                    {{ getStatusText(demand.status) }}
                  </div>
                </div>
                <div class="demand-info">
                  <div class="info-row">
                    <span class="label">预算金额：</span>
                    <span class="value budget">{{ demand.budget }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">发布时间：</span>
                    <span class="value">{{ demand.publishTime }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">截止时间：</span>
                    <span class="value">{{ demand.deadline }}</span>
                  </div>
                </div>
                <div class="demand-description">{{ demand.description }}</div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 核心专家 -->
        <a-tab-pane key="experts" tab="核心专家">
          <div class="experts-section">
            <div class="expert-grid">
              <div 
                v-for="expert in experts" 
                :key="expert.id"
                class="expert-card"
              >
                <div class="expert-avatar">
                  <a-avatar :size="60">{{ expert.name.charAt(0) }}</a-avatar>
                </div>
                <div class="expert-info">
                  <h4 class="expert-name">{{ expert.name }}</h4>
                  <div class="expert-title">{{ expert.title }}</div>
                  <div class="expert-department">{{ expert.department }}</div>
                  <div class="expert-specialties">
                    <a-tag v-for="specialty in expert.specialties" :key="specialty" size="small">
                      {{ specialty }}
                    </a-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 产业链定位 -->
        <a-tab-pane key="chain" tab="产业链定位">
          <div class="chain-section">
            <div class="chain-position">
              <h3>产业链定位</h3>
              <div class="position-path">
                <a-breadcrumb separator=">">
                  <a-breadcrumb-item>{{ enterpriseInfo.industryChain.industry }}</a-breadcrumb-item>
                  <a-breadcrumb-item>{{ enterpriseInfo.industryChain.segment }}</a-breadcrumb-item>
                  <a-breadcrumb-item>{{ enterpriseInfo.industryChain.subsegment }}</a-breadcrumb-item>
                </a-breadcrumb>
              </div>
              
              <div class="chain-description">
                <p>{{ enterpriseInfo.industryChain.description }}</p>
              </div>
              
              <div class="related-companies">
                <h4>同产业链企业</h4>
                <div class="company-list">
                  <a-tag 
                    v-for="company in enterpriseInfo.industryChain.relatedCompanies" 
                    :key="company"
                    @click="viewRelatedCompany(company)"
                    style="cursor: pointer; margin-bottom: 8px;"
                  >
                    {{ company }}
                  </a-tag>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeftOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'

interface EnterpriseInfo {
  id: string
  name: string
  type: string
  industry: string
  location: string
  scale: string
  founded: string
  creditCode: string
  legalPerson: string
  registeredCapital: string
  status: string
  address: string
  phone: string
  email: string
  website: string
  description: string
  industryChain: {
    industry: string
    segment: string
    subsegment: string
    description: string
    relatedCompanies: string[]
  }
}

const router = useRouter()
const route = useRoute()

const activeTab = ref('basic')
const productSearch = ref('')

// 模拟企业详情数据
const enterpriseInfo = ref<EnterpriseInfo>({
  id: route.params.id as string,
  name: '河北宇意科技股份有限公司',
  type: '民营企业',
  industry: '石油化工',
  location: '河北省石家庄市',
  scale: '大型企业',
  founded: '2008年',
  creditCode: '91130100123456789X',
  legalPerson: '张三',
  registeredCapital: '5000万元',
  status: '存续',
  address: '河北省石家庄市高新技术产业开发区',
  phone: '0311-88888888',
  email: 'info@yuyi-tech.com',
  website: 'www.yuyi-tech.com',
  description: '河北宇意科技股份有限公司是一家专注于石油化工智能装备研发、制造和服务的高新技术企业。公司成立于2008年，主要从事防爆电气设备、工业自动化控制系统、安全监测设备等产品的研发、生产和销售。',
  industryChain: {
    industry: '石油化工',
    segment: '下游',
    subsegment: '化工设备制造',
    description: '位于石油化工产业链下游，专注于化工设备的智能化升级和安全防护解决方案。',
    relatedCompanies: ['万华化学', '中石化', '海化集团', '东明石化', '恒力石化']
  }
})

// 产品数据
const products = ref([
  {
    id: '1',
    name: '防爆控制柜',
    category: '防爆设备',
    description: '适用于石油化工等易燃易爆场所的电气控制设备',
    price: '面议'
  },
  {
    id: '2',
    name: '智能安全监测系统',
    category: '监测系统',
    description: '实时监测化工生产过程中的安全参数',
    price: '50-200万元'
  },
  {
    id: '3',
    name: '工业自动化控制系统',
    category: '自动化设备',
    description: '化工生产线智能化控制解决方案',
    price: '100-500万元'
  }
])

// 解决方案数据
const solutions = ref([
  {
    id: '1',
    title: '石化企业智能安全管理解决方案',
    summary: '基于物联网和人工智能技术的石化企业全方位安全管理系统',
    tags: ['智能安全', '物联网', 'AI监测'],
    features: [
      '实时安全参数监测',
      '智能预警和报警',
      '应急响应联动',
      '数据分析和决策支持'
    ]
  },
  {
    id: '2',
    title: '化工装置数字化改造方案',
    summary: '传统化工装置的智能化、数字化升级改造整体解决方案',
    tags: ['数字化改造', '智能装置', '工业4.0'],
    features: [
      '设备状态实时监控',
      '预测性维护',
      '生产优化控制',
      '能效管理'
    ]
  }
])

// 需求数据
const demands = ref([
  {
    id: '1',
    title: '化工设备安全监测系统采购',
    budget: '300万元',
    publishTime: '2024-06-01',
    deadline: '2024-07-15',
    status: 'active',
    description: '采购一套完整的化工设备安全监测系统，用于生产装置的实时监控。'
  },
  {
    id: '2',
    title: '防爆电气设备维护服务',
    budget: '80万元',
    publishTime: '2024-05-15',
    deadline: '2024-06-30',
    status: 'closed',
    description: '现有防爆电气设备的定期维护和检修服务。'
  }
])

// 专家数据
const experts = ref([
  {
    id: '1',
    name: '李工程师',
    title: '高级工程师',
    department: '技术研发部',
    specialties: ['防爆技术', '自动化控制', '安全监测']
  },
  {
    id: '2',
    name: '王总工',
    title: '总工程师',
    department: '技术中心',
    specialties: ['石化工艺', '设备设计', '项目管理']
  },
  {
    id: '3',
    name: '张博士',
    title: '技术总监',
    department: '研发中心',
    specialties: ['AI算法', '物联网', '大数据分析']
  }
])

// 计算属性
const filteredProducts = computed(() => {
  if (!productSearch.value) return products.value
  return products.value.filter(product => 
    product.name.includes(productSearch.value) ||
    product.category.includes(productSearch.value) ||
    product.description.includes(productSearch.value)
  )
})

// 方法
const goBack = () => {
  router.go(-1)
}

const onTabChange = (key: string) => {
  activeTab.value = key
}

const filterProducts = () => {
  // 产品搜索逻辑已在计算属性中实现
}

const viewProduct = (productId: string) => {
  router.push(`/resources/products/${productId}`)
}

const viewDemand = (demandId: string) => {
  router.push(`/resources/demands/${demandId}`)
}

const viewRelatedCompany = (companyName: string) => {
  console.log('查看相关企业:', companyName)
}

const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    '民营企业': 'blue',
    '国有企业': 'red',
    '外资企业': 'green',
    '合资企业': 'orange'
  }
  return colorMap[type] || 'default'
}

const getCategoryColor = (category: string) => {
  const colors = ['blue', 'green', 'orange', 'purple', 'cyan']
  return colors[category.length % colors.length]
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
.enterprise-detail {
  background: var(--light-bg);
  min-height: 100vh;
}

.enterprise-header {
  background: #fff;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-left {
    display: flex;
    align-items: center;
    
    .back-btn {
      margin-right: 16px;
      color: var(--light-primary);
    }
    
    .enterprise-basic {
      .enterprise-name {
        font-size: 24px;
        font-weight: bold;
        color: var(--light-text-primary);
        margin: 0 0 8px 0;
      }
      
      .enterprise-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .meta-item {
          color: var(--light-text-secondary);
          font-size: 14px;
        }
      }
    }
  }
  
  .header-right {
    .enterprise-stats {
      display: flex;
      gap: 24px;
      
      .stat-item {
        text-align: center;
        
        .stat-value {
          font-size: 18px;
          font-weight: bold;
          color: var(--light-primary);
        }
        
        .stat-label {
          font-size: 12px;
          color: var(--light-text-secondary);
          margin-top: 4px;
        }
      }
    }
  }
}

.detail-content {
  padding: 24px;
  
  .ant-tabs {
    background: #fff;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
}

// 基本信息样式
.basic-info {
  .info-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
    
    .info-card {
      background: #f9f9f9;
      border-radius: 8px;
      padding: 20px;
      
      &.full-width {
        grid-column: 1 / -1;
      }
      
      h3 {
        color: var(--light-text-primary);
        margin-bottom: 16px;
        font-size: 16px;
        border-bottom: 1px solid #e4e7ed;
        padding-bottom: 8px;
      }
      
      .info-items {
        .info-item {
          display: flex;
          margin-bottom: 12px;
          
          .label {
            width: 120px;
            color: var(--light-text-secondary);
            font-size: 14px;
          }
          
          .value {
            color: var(--light-text-primary);
            font-size: 14px;
            
            &.status.active {
              color: #52c41a;
            }
            
            &.link {
              color: var(--light-primary);
              cursor: pointer;
            }
          }
        }
      }
      
      .description {
        color: var(--light-text-primary);
        line-height: 1.6;
        font-size: 14px;
      }
    }
  }
}

// 产品列表样式
.products-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h3 {
      color: var(--light-text-primary);
      margin: 0;
    }
  }
  
  .product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    
    .product-card {
      background: #f9f9f9;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--light-primary);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }
      
      .product-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        
        .product-name {
          color: var(--light-text-primary);
          font-size: 16px;
          margin: 0;
        }
      }
      
      .product-description {
        color: var(--light-text-secondary);
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 12px;
      }
      
      .product-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .product-price {
          color: var(--light-primary);
          font-weight: bold;
        }
      }
    }
  }
}

// 解决方案样式
.solutions-section {
  .solution-list {
    .solution-card {
      background: #f9f9f9;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
      
      .solution-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
        
        .solution-title {
          color: var(--light-text-primary);
          font-size: 18px;
          margin: 0;
        }
        
        .solution-tags {
          display: flex;
          gap: 8px;
        }
      }
      
      .solution-content {
        margin-bottom: 16px;
        
        .solution-summary {
          color: var(--light-text-secondary);
          line-height: 1.6;
          margin-bottom: 16px;
        }
        
        .solution-features {
          h5 {
            color: var(--light-text-primary);
            margin-bottom: 8px;
          }
          
          ul {
            color: var(--light-text-secondary);
            padding-left: 20px;
            
            li {
              margin-bottom: 4px;
            }
          }
        }
      }
    }
  }
}

// 需求列表样式
.demands-section {
  .demand-list {
    .demand-card {
      background: #f9f9f9;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--light-primary);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }
      
      .demand-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
        
        .demand-title {
          color: var(--light-text-primary);
          font-size: 16px;
          margin: 0;
        }
        
        .demand-status {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          
          &.active {
            background: #f6ffed;
            color: #52c41a;
          }
          
          &.closed {
            background: #f5f5f5;
            color: #999;
          }
        }
      }
      
      .demand-info {
        margin-bottom: 12px;
        
        .info-row {
          display: flex;
          margin-bottom: 4px;
          font-size: 14px;
          
          .label {
            width: 80px;
            color: var(--light-text-secondary);
          }
          
          .value {
            color: var(--light-text-primary);
            
            &.budget {
              color: var(--light-primary);
              font-weight: bold;
            }
          }
        }
      }
      
      .demand-description {
        color: var(--light-text-secondary);
        font-size: 14px;
        line-height: 1.5;
      }
    }
  }
}

// 专家列表样式
.experts-section {
  .expert-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 16px;
    
    .expert-card {
      background: #f9f9f9;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      
      .expert-avatar {
        margin-bottom: 16px;
      }
      
      .expert-info {
        .expert-name {
          color: var(--light-text-primary);
          margin-bottom: 4px;
        }
        
        .expert-title,
        .expert-department {
          color: var(--light-text-secondary);
          font-size: 14px;
          margin-bottom: 4px;
        }
        
        .expert-specialties {
          margin-top: 12px;
        }
      }
    }
  }
}

// 产业链定位样式
.chain-section {
  .chain-position {
    h3 {
      color: var(--light-text-primary);
      margin-bottom: 16px;
    }
    
    .position-path {
      margin-bottom: 24px;
      
      .ant-breadcrumb {
        font-size: 16px;
      }
    }
    
    .chain-description {
      background: #f9f9f9;
      padding: 16px;
      border-radius: 8px;
      margin-bottom: 24px;
      
      p {
        color: var(--light-text-secondary);
        line-height: 1.6;
        margin: 0;
      }
    }
    
    .related-companies {
      h4 {
        color: var(--light-text-primary);
        margin-bottom: 12px;
      }
      
      .company-list {
        .ant-tag {
          margin-right: 8px;
          margin-bottom: 8px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .enterprise-detail {
    padding: 16px;
  }
  
  .basic-info .info-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .product-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .enterprise-detail {
    padding: 12px;
  }
  
  .enterprise-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    padding: 16px;
    
    .header-left {
      width: 100%;
      
      .back-btn {
        margin-bottom: 12px;
      }
      
      .enterprise-basic {
        .enterprise-name {
          font-size: 20px;
        }
        
        .enterprise-meta {
          flex-direction: column;
          gap: 8px;
          align-items: flex-start;
        }
      }
    }
    
    .header-right {
      width: 100%;
      
      .enterprise-stats {
        flex-direction: row;
        gap: 20px;
      }
    }
  }
  
  .detail-content {
    padding: 0;
    
    .ant-tabs-content-holder {
      padding: 16px 0;
    }
  }
  
  .basic-info .info-grid {
    grid-template-columns: 1fr;
    gap: 12px;
    
    .info-card {
      padding: 16px;
      
      .info-items .info-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
        
        .label {
          width: auto;
          font-weight: 500;
        }
      }
    }
  }
  
  .product-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .expert-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .solution-card,
  .demand-card {
    margin-bottom: 12px;
    padding: 12px;
  }
}
</style> 