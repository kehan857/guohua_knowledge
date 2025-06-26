<template>
  <div class="demand-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">需求库</h1>
        <p class="page-description">企业技术需求与合作机会</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="showCreateForm = true">
          <template #icon><plus-outlined /></template>
          发布需求
        </a-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filters">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input
            v-model:value="searchKeyword"
            placeholder="搜索需求标题或关键词"
            @input="handleSearch"
          >
            <template #prefix>
              <search-outlined />
            </template>
          </a-input>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedCategory"
            placeholder="需求类型"
            style="width: 100%"
            @change="filterDemands"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="tech">技术需求</a-select-option>
            <a-select-option value="product">产品需求</a-select-option>
            <a-select-option value="service">服务需求</a-select-option>
            <a-select-option value="cooperation">合作需求</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedStatus"
            placeholder="需求状态"
            style="width: 100%"
            @change="filterDemands"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="open">开放中</a-select-option>
            <a-select-option value="matching">匹配中</a-select-option>
            <a-select-option value="closed">已结束</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedUrgency"
            placeholder="紧急程度"
            style="width: 100%"
            @change="filterDemands"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="low">低</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">重置筛选</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 需求列表 -->
    <div class="demand-cards">
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="demand in paginatedDemands"
          :key="demand.id"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <a-card
            class="demand-card"
            :hoverable="true"
            @click="viewDemandDetail(demand)"
          >
            <template #title>
              <div class="card-title">
                <div class="demand-title">{{ demand.title }}</div>
                <a-tag
                  :color="getStatusColor(demand.status)"
                  class="status-tag"
                >
                  {{ getStatusText(demand.status) }}
                </a-tag>
              </div>
            </template>
            
            <template #extra>
              <a-tag
                :color="getUrgencyColor(demand.urgency)"
                size="small"
              >
                {{ getUrgencyText(demand.urgency) }}
              </a-tag>
            </template>

            <div class="demand-content">
              <div class="demand-type">
                <tag-outlined />
                {{ getCategoryText(demand.category) }}
              </div>
              
              <div class="demand-description">
                {{ demand.description }}
              </div>
              
              <div class="demand-meta">
                <div class="meta-item">
                  <bank-outlined />
                  <span>{{ demand.company }}</span>
                </div>
                <div class="meta-item">
                  <environment-outlined />
                  <span>{{ demand.location }}</span>
                </div>
                <div class="meta-item">
                  <calendar-outlined />
                  <span>{{ demand.publishDate }}</span>
                </div>
              </div>

              <div class="demand-budget" v-if="demand.budget">
                <wallet-outlined />
                <span class="budget-amount">预算：{{ demand.budget }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <a-pagination
        v-model:current="currentPage"
        v-model:page-size="pageSize"
        :total="filteredDemands.length"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total: number, range: [number, number]) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handlePageChange"
      />
    </div>

    <!-- 需求详情模态框 -->
    <a-modal
      v-model:open="showDetailModal"
      title="需求详情"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedDemand" class="demand-detail">
        <div class="detail-header">
          <h2>{{ selectedDemand.title }}</h2>
          <div class="header-tags">
            <a-tag :color="getStatusColor(selectedDemand.status)">
              {{ getStatusText(selectedDemand.status) }}
            </a-tag>
            <a-tag :color="getUrgencyColor(selectedDemand.urgency)">
              {{ getUrgencyText(selectedDemand.urgency) }}
            </a-tag>
            <a-tag color="blue">
              {{ getCategoryText(selectedDemand.category) }}
            </a-tag>
          </div>
        </div>

        <div class="detail-content">
          <div class="section">
            <h4>需求描述</h4>
            <p>{{ selectedDemand.description }}</p>
          </div>

          <div class="section">
            <h4>技术要求</h4>
            <p>{{ selectedDemand.requirements }}</p>
          </div>

          <div class="section">
            <h4>企业信息</h4>
            <div class="company-info">
              <div class="info-item">
                <strong>企业名称：</strong>{{ selectedDemand.company }}
              </div>
              <div class="info-item">
                <strong>联系人：</strong>{{ selectedDemand.contact }}
              </div>
              <div class="info-item">
                <strong>所在地区：</strong>{{ selectedDemand.location }}
              </div>
              <div class="info-item" v-if="selectedDemand.budget">
                <strong>预算范围：</strong>{{ selectedDemand.budget }}
              </div>
            </div>
          </div>

          <div class="section">
            <h4>期望合作方式</h4>
            <p>{{ selectedDemand.cooperationMode }}</p>
          </div>
        </div>

        <div class="detail-actions">
          <a-button type="primary" size="large">
            我有解决方案
          </a-button>
          <a-button size="large">
            联系企业
          </a-button>
          <a-button size="large">
            收藏需求
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 发布需求模态框 -->
    <a-modal
      v-model:open="showCreateForm"
      title="发布需求"
      width="600px"
      @ok="handleCreateDemand"
      @cancel="resetCreateForm"
    >
      <a-form
        :model="createForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="需求标题" required>
          <a-input v-model:value="createForm.title" placeholder="请输入需求标题" />
        </a-form-item>
        
        <a-form-item label="需求类型" required>
          <a-select v-model:value="createForm.category" placeholder="选择需求类型">
            <a-select-option value="tech">技术需求</a-select-option>
            <a-select-option value="product">产品需求</a-select-option>
            <a-select-option value="service">服务需求</a-select-option>
            <a-select-option value="cooperation">合作需求</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="紧急程度" required>
          <a-select v-model:value="createForm.urgency" placeholder="选择紧急程度">
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="low">低</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="需求描述" required>
          <a-textarea
            v-model:value="createForm.description"
            placeholder="详细描述您的需求"
            :rows="4"
          />
        </a-form-item>

        <a-form-item label="技术要求">
          <a-textarea
            v-model:value="createForm.requirements"
            placeholder="详细的技术要求和规格"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="预算范围">
          <a-input v-model:value="createForm.budget" placeholder="如：10-50万元" />
        </a-form-item>

        <a-form-item label="联系人">
          <a-input v-model:value="createForm.contact" placeholder="联系人姓名" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  TagOutlined,
  BankOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  WalletOutlined
} from '@ant-design/icons-vue'

// 数据定义
interface Demand {
  id: string
  title: string
  description: string
  requirements: string
  category: string
  status: string
  urgency: string
  company: string
  contact: string
  location: string
  budget?: string
  publishDate: string
  cooperationMode: string
}

// 响应式数据
const searchKeyword = ref('')
const selectedCategory = ref('')
const selectedStatus = ref('')
const selectedUrgency = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const showDetailModal = ref(false)
const showCreateForm = ref(false)
const selectedDemand = ref<Demand | null>(null)

// 创建表单
const createForm = ref({
  title: '',
  category: '',
  urgency: '',
  description: '',
  requirements: '',
  budget: '',
  contact: ''
})

// 模拟数据
const demandList = ref<Demand[]>([
  {
    id: '1',
    title: '新型催化剂技术开发',
    description: '寻求高效、环保的催化剂技术，用于石油化工生产过程的优化。要求具有高活性、长寿命特点。',
    requirements: '1. 催化效率提升20%以上\n2. 使用寿命延长30%\n3. 环保无毒\n4. 可工业化生产',
    category: 'tech',
    status: 'open',
    urgency: 'high',
    company: '中石化上海分公司',
    contact: '张工程师',
    location: '上海市',
    budget: '100-500万元',
    publishDate: '2024-01-15',
    cooperationMode: '技术转让或合作开发'
  },
  {
    id: '2',
    title: '智能设备维护系统',
    description: '开发基于AI的设备预测性维护系统，提前发现设备故障，降低维护成本。',
    requirements: '支持多种设备类型，具备机器学习能力，可视化界面友好',
    category: 'product',
    status: 'matching',
    urgency: 'medium',
    company: '华东石化装备公司',
    contact: '李经理',
    location: '江苏省南京市',
    budget: '50-200万元',
    publishDate: '2024-01-12',
    cooperationMode: '产品采购或定制开发'
  },
  {
    id: '3',
    title: '环保废气处理咨询',
    description: '需要专业的环保咨询服务，优化现有废气处理工艺，满足新环保标准要求。',
    requirements: '具有石化行业经验，熟悉最新环保法规，能提供完整解决方案',
    category: 'service',
    status: 'open',
    urgency: 'high',
    company: '山东石化集团',
    contact: '王主任',
    location: '山东省淄博市',
    publishDate: '2024-01-10',
    cooperationMode: '咨询服务'
  },
  {
    id: '4',
    title: '新材料应用合作',
    description: '寻求在新型聚合物材料方面的合作伙伴，共同开发高性能化工材料。',
    requirements: '具备材料研发能力，有成功案例，愿意长期合作',
    category: 'cooperation',
    status: 'open',
    urgency: 'low',
    company: '华南新材料研究院',
    contact: '刘博士',
    location: '广东省深圳市',
    budget: '200-1000万元',
    publishDate: '2024-01-08',
    cooperationMode: '合资或战略合作'
  },
  {
    id: '5',
    title: '生产线自动化改造',
    description: '对现有生产线进行自动化改造，提高生产效率，降低人工成本。',
    requirements: '工业自动化经验丰富，支持定制化方案，有成功案例',
    category: 'tech',
    status: 'closed',
    urgency: 'medium',
    company: '北方化工有限公司',
    contact: '赵总工',
    location: '河北省石家庄市',
    budget: '300-800万元',
    publishDate: '2024-01-05',
    cooperationMode: '工程承包'
  },
  {
    id: '6',
    title: '质量检测设备采购',
    description: '采购先进的化工产品质量检测设备，提升产品质量控制水平。',
    requirements: '检测精度高，操作简便，维护成本低，提供培训服务',
    category: 'product',
    status: 'open',
    urgency: 'medium',
    company: '东北精细化工厂',
    contact: '孙主管',
    location: '辽宁省大连市',
    budget: '80-300万元',
    publishDate: '2024-01-03',
    cooperationMode: '设备采购'
  }
])

// 计算属性
const filteredDemands = computed(() => {
  let result = demandList.value

  if (searchKeyword.value) {
    result = result.filter(demand =>
      demand.title.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      demand.description.toLowerCase().includes(searchKeyword.value.toLowerCase())
    )
  }

  if (selectedCategory.value) {
    result = result.filter(demand => demand.category === selectedCategory.value)
  }

  if (selectedStatus.value) {
    result = result.filter(demand => demand.status === selectedStatus.value)
  }

  if (selectedUrgency.value) {
    result = result.filter(demand => demand.urgency === selectedUrgency.value)
  }

  return result
})

const paginatedDemands = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDemands.value.slice(start, end)
})

// 方法
const handleSearch = () => {
  currentPage.value = 1
}

const filterDemands = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedCategory.value = ''
  selectedStatus.value = ''
  selectedUrgency.value = ''
  currentPage.value = 1
}

const handlePageChange = () => {
  // 页面变化处理
}

const viewDemandDetail = (demand: Demand) => {
  selectedDemand.value = demand
  showDetailModal.value = true
}

const handleCreateDemand = () => {
  // 验证表单
  if (!createForm.value.title || !createForm.value.category || 
      !createForm.value.urgency || !createForm.value.description) {
    message.error('请填写必填项')
    return
  }

  // 创建新需求
  const newDemand: Demand = {
    id: Date.now().toString(),
    title: createForm.value.title,
    description: createForm.value.description,
    requirements: createForm.value.requirements,
    category: createForm.value.category,
    status: 'open',
    urgency: createForm.value.urgency,
    company: '我的企业', // 这里应该从用户信息获取
    contact: createForm.value.contact,
    location: '待填写',
    budget: createForm.value.budget,
    publishDate: new Date().toISOString().split('T')[0],
    cooperationMode: '待商议'
  }

  demandList.value.unshift(newDemand)
  message.success('需求发布成功')
  showCreateForm.value = false
  resetCreateForm()
}

const resetCreateForm = () => {
  createForm.value = {
    title: '',
    category: '',
    urgency: '',
    description: '',
    requirements: '',
    budget: '',
    contact: ''
  }
}

// 辅助方法
const getStatusColor = (status: string) => {
  const colors = {
    open: 'green',
    matching: 'orange',
    closed: 'gray'
  }
  return colors[status as keyof typeof colors] || 'blue'
}

const getStatusText = (status: string) => {
  const texts = {
    open: '开放中',
    matching: '匹配中',
    closed: '已结束'
  }
  return texts[status as keyof typeof texts] || status
}

const getUrgencyColor = (urgency: string) => {
  const colors = {
    high: 'red',
    medium: 'orange',
    low: 'green'
  }
  return colors[urgency as keyof typeof colors] || 'blue'
}

const getUrgencyText = (urgency: string) => {
  const texts = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return texts[urgency as keyof typeof texts] || urgency
}

const getCategoryText = (category: string) => {
  const texts = {
    tech: '技术需求',
    product: '产品需求',
    service: '服务需求',
    cooperation: '合作需求'
  }
  return texts[category as keyof typeof texts] || category
}

onMounted(() => {
  // 页面初始化
})
</script>

<style scoped lang="less">
.demand-list {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);

    .header-left {
      .page-title {
        margin: 0;
        color: var(--text-primary);
        font-size: 24px;
        font-weight: 600;
      }

      .page-description {
        margin: 8px 0 0 0;
        color: var(--text-secondary);
        font-size: 14px;
      }
    }
  }

  .search-filters {
    background: var(--component-bg);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .demand-cards {
    margin-bottom: 24px;

    .demand-card {
      height: 100%;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      transition: all 0.3s ease;
      background: var(--component-bg);

      &:hover {
        border-color: var(--primary-color);
        box-shadow: 0 8px 24px rgba(35, 134, 54, 0.1);
        transform: translateY(-2px);
      }

      .card-title {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;

        .demand-title {
          flex: 1;
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          line-height: 1.4;
        }

        .status-tag {
          flex-shrink: 0;
        }
      }

      .demand-content {
        .demand-type {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 12px;
          color: var(--primary-color);
          font-size: 13px;
          font-weight: 500;
        }

        .demand-description {
          color: var(--text-secondary);
          font-size: 14px;
          line-height: 1.5;
          margin-bottom: 16px;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .demand-meta {
          .meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
            color: var(--text-tertiary);
            font-size: 12px;

            &:last-child {
              margin-bottom: 0;
            }
          }
        }

        .demand-budget {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid var(--border-color);

          .budget-amount {
            color: var(--primary-color);
            font-weight: 600;
            font-size: 13px;
          }
        }
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px;
    background: var(--component-bg);
    border-radius: 8px;
  }
}

.demand-detail {
  .detail-header {
    margin-bottom: 24px;

    h2 {
      margin: 0 0 12px 0;
      color: var(--text-primary);
    }

    .header-tags {
      display: flex;
      gap: 8px;
    }
  }

  .detail-content {
    .section {
      margin-bottom: 20px;

      h4 {
        margin: 0 0 12px 0;
        color: var(--text-primary);
        font-size: 16px;
      }

      p {
        margin: 0;
        color: var(--text-secondary);
        line-height: 1.6;
      }

      .company-info {
        .info-item {
          margin-bottom: 8px;
          color: var(--text-secondary);

          strong {
            color: var(--text-primary);
          }
        }
      }
    }
  }

  .detail-actions {
    display: flex;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .demand-list {
    padding: 16px;

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }

    .search-filters {
      padding: 16px;

      .ant-row {
        .ant-col {
          margin-bottom: 12px;
        }
      }
    }
  }
}
</style> 