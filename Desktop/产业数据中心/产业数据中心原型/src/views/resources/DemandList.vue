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
            v-model:value="selectedType"
            placeholder="需求类型"
            style="width: 100%"
            @change="handleFilter"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="technology">技术需求</a-select-option>
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
            @change="handleFilter"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="open">待解决</a-select-option>
            <a-select-option value="in_progress">进行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedUrgency"
            placeholder="紧急程度"
            style="width: 100%"
            @change="handleFilter"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="high">紧急</a-select-option>
            <a-select-option value="medium">一般</a-select-option>
            <a-select-option value="low">不急</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button @click="resetFilters">
            <template #icon><reload-outlined /></template>
            重置
          </a-button>
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
          :md="8" 
          :lg="6"
        >
          <div class="demand-card" @click="showDemandDetail(demand)">
            <div class="card-header">
              <div class="demand-type">
                <a-tag :color="getTypeColor(demand.type)">
                  {{ getTypeText(demand.type) }}
                </a-tag>
                <a-tag :color="getUrgencyColor(demand.urgency)">
                  {{ getUrgencyText(demand.urgency) }}
                </a-tag>
              </div>
              <div class="demand-status">
                <a-badge :status="getStatusType(demand.status)" :text="getStatusText(demand.status)" />
              </div>
            </div>

            <div class="card-content">
              <h3 class="demand-title">{{ demand.title }}</h3>
              <p class="demand-description">{{ demand.description }}</p>
              
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
                  <span>{{ formatDate(demand.publishDate) }}</span>
                </div>
              </div>

              <div class="demand-budget">
                <span class="budget-label">预算范围：</span>
                <span class="budget-amount">{{ demand.budget }}</span>
              </div>
            </div>

            <div class="card-footer">
              <div class="footer-left">
                <a-avatar-group size="small" :max-count="3">
                  <a-avatar 
                    v-for="applicant in demand.applicants" 
                    :key="applicant.id"
                    :src="applicant.avatar"
                  >
                    {{ applicant.name.charAt(0) }}
                  </a-avatar>
                </a-avatar-group>
                <span class="applicant-count">{{ demand.applicantCount }}人申请</span>
              </div>
              <div class="footer-right">
                <a-button type="text" size="small" @click.stop="contactDemand(demand)">
                  <template #icon><message-outlined /></template>
                  联系
                </a-button>
              </div>
            </div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <a-pagination
        v-model:current="currentPage"
        v-model:page-size="pageSize"
        :total="filteredDemands.length"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handlePageChange"
        @show-size-change="handlePageSizeChange"
      />
    </div>

    <!-- 需求详情模态框 -->
    <a-modal
      v-model:open="showDetailModal"
      title="需求详情"
      :width="800"
      :footer="null"
    >
      <div v-if="selectedDemand" class="demand-detail">
        <div class="detail-header">
          <h2>{{ selectedDemand.title }}</h2>
          <div class="header-tags">
            <a-tag :color="getTypeColor(selectedDemand.type)">
              {{ getTypeText(selectedDemand.type) }}
            </a-tag>
            <a-tag :color="getUrgencyColor(selectedDemand.urgency)">
              {{ getUrgencyText(selectedDemand.urgency) }}
            </a-tag>
            <a-badge :status="getStatusType(selectedDemand.status)" :text="getStatusText(selectedDemand.status)" />
          </div>
        </div>

        <div class="detail-content">
          <h4>需求描述</h4>
          <p>{{ selectedDemand.description }}</p>

          <h4>技术要求</h4>
          <p>{{ selectedDemand.requirements }}</p>

          <div class="detail-info">
            <a-row :gutter="24">
              <a-col :span="12">
                <div class="info-item">
                  <strong>发布企业：</strong>{{ selectedDemand.company }}
                </div>
                <div class="info-item">
                  <strong>联系人：</strong>{{ selectedDemand.contact }}
                </div>
                <div class="info-item">
                  <strong>所在地区：</strong>{{ selectedDemand.location }}
                </div>
              </a-col>
              <a-col :span="12">
                <div class="info-item">
                  <strong>预算范围：</strong>{{ selectedDemand.budget }}
                </div>
                <div class="info-item">
                  <strong>期望交付：</strong>{{ selectedDemand.deliveryTime }}
                </div>
                <div class="info-item">
                  <strong>发布时间：</strong>{{ formatDate(selectedDemand.publishDate) }}
                </div>
              </a-col>
            </a-row>
          </div>
        </div>

        <div class="detail-actions">
          <a-button type="primary" @click="applyDemand(selectedDemand)">
            申请此需求
          </a-button>
          <a-button @click="contactDemand(selectedDemand)">
            联系发布方
          </a-button>
          <a-button @click="shareDemand(selectedDemand)">
            分享需求
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 发布需求模态框 -->
    <a-modal
      v-model:open="showCreateForm"
      title="发布新需求"
      :width="600"
      @ok="submitDemand"
      @cancel="resetCreateForm"
    >
      <a-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        layout="vertical"
      >
        <a-form-item label="需求标题" name="title">
          <a-input v-model:value="createForm.title" placeholder="请输入需求标题" />
        </a-form-item>

        <a-form-item label="需求类型" name="type">
          <a-select v-model:value="createForm.type" placeholder="请选择需求类型">
            <a-select-option value="technology">技术需求</a-select-option>
            <a-select-option value="product">产品需求</a-select-option>
            <a-select-option value="service">服务需求</a-select-option>
            <a-select-option value="cooperation">合作需求</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="需求描述" name="description">
          <a-textarea 
            v-model:value="createForm.description" 
            placeholder="请详细描述您的需求" 
            :rows="4"
          />
        </a-form-item>

        <a-form-item label="技术要求" name="requirements">
          <a-textarea 
            v-model:value="createForm.requirements" 
            placeholder="请描述具体的技术要求和规格" 
            :rows="3"
          />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="预算范围" name="budget">
              <a-input v-model:value="createForm.budget" placeholder="如：10-50万元" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="紧急程度" name="urgency">
              <a-select v-model:value="createForm.urgency" placeholder="请选择紧急程度">
                <a-select-option value="high">紧急</a-select-option>
                <a-select-option value="medium">一般</a-select-option>
                <a-select-option value="low">不急</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="期望交付时间" name="deliveryTime">
          <a-input v-model:value="createForm.deliveryTime" placeholder="如：3个月内" />
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
  ReloadOutlined,
  BankOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  MessageOutlined
} from '@ant-design/icons-vue'

// 接口定义
interface Demand {
  id: string
  title: string
  description: string
  requirements: string
  type: 'technology' | 'product' | 'service' | 'cooperation'
  status: 'open' | 'in_progress' | 'completed'
  urgency: 'high' | 'medium' | 'low'
  company: string
  contact: string
  location: string
  budget: string
  deliveryTime: string
  publishDate: string
  applicantCount: number
  applicants: Array<{
    id: string
    name: string
    avatar?: string
  }>
}

// 响应式数据
const searchKeyword = ref('')
const selectedType = ref('')
const selectedStatus = ref('')
const selectedUrgency = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const showDetailModal = ref(false)
const showCreateForm = ref(false)
const selectedDemand = ref<Demand | null>(null)

// 表单相关
const createFormRef = ref()
const createForm = ref({
  title: '',
  type: '',
  description: '',
  requirements: '',
  budget: '',
  urgency: '',
  deliveryTime: ''
})

const createRules = {
  title: [{ required: true, message: '请输入需求标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择需求类型', trigger: 'change' }],
  description: [{ required: true, message: '请输入需求描述', trigger: 'blur' }],
  requirements: [{ required: true, message: '请输入技术要求', trigger: 'blur' }],
  budget: [{ required: true, message: '请输入预算范围', trigger: 'blur' }],
  urgency: [{ required: true, message: '请选择紧急程度', trigger: 'change' }],
  deliveryTime: [{ required: true, message: '请输入期望交付时间', trigger: 'blur' }]
}

// 模拟数据
const demands = ref<Demand[]>([
  {
    id: '1',
    title: '工业机器人控制系统优化',
    description: '需要对现有的工业机器人控制系统进行优化，提高精度和稳定性，降低故障率。',
    requirements: '具备工业机器人控制系统开发经验，熟悉PLC编程，了解伺服控制技术。',
    type: 'technology',
    status: 'open',
    urgency: 'high',
    company: '智能制造有限公司',
    contact: '张工程师',
    location: '苏州市',
    budget: '20-50万元',
    deliveryTime: '6个月内',
    publishDate: '2024-01-15',
    applicantCount: 12,
    applicants: [
      { id: '1', name: '李专家', avatar: '' },
      { id: '2', name: '王博士', avatar: '' },
      { id: '3', name: '陈工程师', avatar: '' }
    ]
  },
  {
    id: '2',
    title: '环保设备污水处理技术',
    description: '寻求先进的污水处理技术，能够高效处理工业废水，达到环保排放标准。',
    requirements: '具备污水处理技术研发能力，有成功案例，技术成熟度高。',
    type: 'technology',
    status: 'in_progress',
    urgency: 'medium',
    company: '绿色环保科技',
    contact: '刘总工',
    location: '南京市',
    budget: '100-200万元',
    deliveryTime: '12个月内',
    publishDate: '2024-01-10',
    applicantCount: 8,
    applicants: [
      { id: '4', name: '赵专家', avatar: '' },
      { id: '5', name: '钱博士', avatar: '' }
    ]
  },
  {
    id: '3',
    title: '新能源汽车电池管理系统',
    description: '开发高效的新能源汽车电池管理系统，提高电池寿命和安全性。',
    requirements: '熟悉电池管理系统设计，具备汽车电子产品开发经验。',
    type: 'product',
    status: 'open',
    urgency: 'high',
    company: '新能源汽车公司',
    contact: '孙经理',
    location: '无锡市',
    budget: '50-100万元',
    deliveryTime: '8个月内',
    publishDate: '2024-01-12',
    applicantCount: 15,
    applicants: [
      { id: '6', name: '周工程师', avatar: '' },
      { id: '7', name: '吴博士', avatar: '' },
      { id: '8', name: '郑专家', avatar: '' }
    ]
  },
  // 添加更多模拟数据...
  {
    id: '4',
    title: '智能物流仓储管理系统',
    description: '需要开发智能化的物流仓储管理系统，提高仓储效率和准确性。',
    requirements: '具备WMS系统开发经验，熟悉RFID、条码技术，了解物流行业流程。',
    type: 'service',
    status: 'open',
    urgency: 'medium',
    company: '智慧物流集团',
    contact: '王经理',
    location: '常州市',
    budget: '30-80万元',
    deliveryTime: '10个月内',
    publishDate: '2024-01-08',
    applicantCount: 6,
    applicants: [
      { id: '9', name: '冯工程师', avatar: '' },
      { id: '10', name: '陈博士', avatar: '' }
    ]
  }
])

// 计算属性
const filteredDemands = computed(() => {
  return demands.value.filter(demand => {
    const matchKeyword = !searchKeyword.value || 
      demand.title.includes(searchKeyword.value) || 
      demand.description.includes(searchKeyword.value)
    
    const matchType = !selectedType.value || demand.type === selectedType.value
    const matchStatus = !selectedStatus.value || demand.status === selectedStatus.value
    const matchUrgency = !selectedUrgency.value || demand.urgency === selectedUrgency.value
    
    return matchKeyword && matchType && matchStatus && matchUrgency
  })
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

const handleFilter = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedType.value = ''
  selectedStatus.value = ''
  selectedUrgency.value = ''
  currentPage.value = 1
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handlePageSizeChange = (current: number, size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const showDemandDetail = (demand: Demand) => {
  selectedDemand.value = demand
  showDetailModal.value = true
}

const contactDemand = (demand: Demand) => {
  message.info(`正在联系 ${demand.company} - ${demand.contact}`)
}

const applyDemand = (demand: Demand) => {
  message.success('申请已提交，请等待审核')
  showDetailModal.value = false
}

const shareDemand = (demand: Demand) => {
  message.success('需求链接已复制到剪贴板')
}

const submitDemand = async () => {
  try {
    await createFormRef.value.validateFields()
    // 这里应该调用API提交需求
    message.success('需求发布成功')
    showCreateForm.value = false
    resetCreateForm()
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const resetCreateForm = () => {
  createForm.value = {
    title: '',
    type: '',
    description: '',
    requirements: '',
    budget: '',
    urgency: '',
    deliveryTime: ''
  }
}

// 辅助方法
const getTypeColor = (type: string) => {
  const colors = {
    technology: 'blue',
    product: 'green',
    service: 'orange',
    cooperation: 'purple'
  }
  return colors[type as keyof typeof colors] || 'default'
}

const getTypeText = (type: string) => {
  const texts = {
    technology: '技术需求',
    product: '产品需求',
    service: '服务需求',
    cooperation: '合作需求'
  }
  return texts[type as keyof typeof texts] || type
}

const getUrgencyColor = (urgency: string) => {
  const colors = {
    high: 'red',
    medium: 'orange',
    low: 'green'
  }
  return colors[urgency as keyof typeof colors] || 'default'
}

const getUrgencyText = (urgency: string) => {
  const texts = {
    high: '紧急',
    medium: '一般',
    low: '不急'
  }
  return texts[urgency as keyof typeof texts] || urgency
}

const getStatusType = (status: string) => {
  const types = {
    open: 'processing',
    in_progress: 'warning',
    completed: 'success'
  }
  return types[status as keyof typeof types] || 'default'
}

const getStatusText = (status: string) => {
  const texts = {
    open: '待解决',
    in_progress: '进行中',
    completed: '已完成'
  }
  return texts[status as keyof typeof texts] || status
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  // 初始化逻辑
})
</script>

<style scoped lang="less">
.demand-list {
  padding: 24px;
  background: var(--bg-color);
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 0 24px 0;
  border-bottom: 1px solid var(--border-color);

  .header-left {
    .page-title {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .page-description {
      margin: 0;
      color: var(--text-secondary);
      font-size: 16px;
    }
  }
}

.search-filters {
  background: var(--component-bg);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.demand-cards {
  margin-bottom: 32px;
}

.demand-card {
  background: var(--component-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 280px;
  display: flex;
  flex-direction: column;

  &:hover {
    border-color: var(--primary-color);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;

    .demand-type {
      display: flex;
      gap: 8px;
    }
  }

  .card-content {
    flex: 1;
    display: flex;
    flex-direction: column;

    .demand-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 12px 0;
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .demand-description {
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.5;
      margin: 0 0 16px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      flex: 1;
    }

    .demand-meta {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 12px;

      .meta-item {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--text-secondary);
        font-size: 12px;

        .anticon {
          color: var(--primary-color);
        }
      }
    }

    .demand-budget {
      .budget-label {
        color: var(--text-secondary);
        font-size: 12px;
      }

      .budget-amount {
        color: var(--primary-color);
        font-weight: 600;
        font-size: 14px;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);

    .footer-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .applicant-count {
        color: var(--text-secondary);
        font-size: 12px;
      }
    }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px 0;
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
      align-items: center;
    }
  }

  .detail-content {
    h4 {
      color: var(--text-primary);
      margin: 20px 0 12px 0;
      font-size: 16px;
    }

    p {
      color: var(--text-secondary);
      line-height: 1.6;
      margin-bottom: 16px;
    }

    .detail-info {
      background: var(--bg-secondary);
      padding: 20px;
      border-radius: 8px;
      margin: 24px 0;

      .info-item {
        margin-bottom: 12px;
        color: var(--text-primary);

        &:last-child {
          margin-bottom: 0;
        }

        strong {
          color: var(--text-secondary);
          margin-right: 8px;
        }
      }
    }
  }

  .detail-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .demand-list {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .search-filters {
    .ant-row {
      .ant-col {
        margin-bottom: 12px;
      }
    }
  }

  .demand-card {
    height: auto;
    min-height: 260px;
  }
}
</style> 