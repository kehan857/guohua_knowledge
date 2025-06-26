<template>
  <div class="demand-list-container">
    <div class="page-header">
      <h2>需求库</h2>
      <p>企业技术需求与解决方案匹配平台</p>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索需求标题、描述或技术领域"
            size="large"
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedIndustry"
            placeholder="选择行业"
            size="large"
            style="width: 100%"
            @change="handleIndustryChange"
          >
            <a-select-option value="">全部行业</a-select-option>
            <a-select-option value="制造业">制造业</a-select-option>
            <a-select-option value="信息技术">信息技术</a-select-option>
            <a-select-option value="新能源">新能源</a-select-option>
            <a-select-option value="生物医药">生物医药</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedStatus"
            placeholder="需求状态"
            size="large"
            style="width: 100%"
            @change="handleStatusChange"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="待解决">待解决</a-select-option>
            <a-select-option value="进行中">进行中</a-select-option>
            <a-select-option value="已解决">已解决</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="selectedUrgency"
            placeholder="紧急程度"
            size="large"
            style="width: 100%"
            @change="handleUrgencyChange"
          >
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="高">高</a-select-option>
            <a-select-option value="中">中</a-select-option>
            <a-select-option value="低">低</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" size="large" style="width: 100%" @click="resetFilters">
            重置筛选
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 需求列表 -->
    <div class="demand-grid">
      <a-row :gutter="[16, 16]">
        <a-col :span="8" v-for="demand in filteredDemands" :key="demand.id">
          <a-card 
            class="demand-card" 
            hoverable
            @click="viewDemandDetail(demand)"
          >
            <template #title>
              <div class="card-title">
                <span>{{ demand.title }}</span>
                <a-tag :color="getStatusColor(demand.status)">{{ demand.status }}</a-tag>
              </div>
            </template>
            
            <div class="demand-content">
              <div class="demand-info">
                <div class="info-row">
                  <span class="label">发布企业：</span>
                  <span class="value">{{ demand.company }}</span>
                </div>
                <div class="info-row">
                  <span class="label">技术领域：</span>
                  <span class="value">{{ demand.techField }}</span>
                </div>
                <div class="info-row">
                  <span class="label">预算范围：</span>
                  <span class="value">{{ demand.budget }}</span>
                </div>
                <div class="info-row">
                  <span class="label">紧急程度：</span>
                  <a-tag :color="getUrgencyColor(demand.urgency)">{{ demand.urgency }}</a-tag>
                </div>
              </div>
              
              <div class="demand-description">
                {{ demand.description }}
              </div>
              
              <div class="demand-meta">
                <span class="publish-time">发布时间：{{ demand.publishTime }}</span>
                <span class="deadline">截止时间：{{ demand.deadline }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <a-pagination
        v-model:current="currentPage"
        v-model:page-size="pageSize"
        :total="totalDemands"
        show-size-changer
        show-quick-jumper
        :show-total="(total: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
        @change="handlePageChange"
        @show-size-change="handlePageSizeChange"
      />
    </div>

    <!-- 需求详情模态框 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="需求详情"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedDemand" class="demand-detail">
        <div class="detail-header">
          <h3>{{ selectedDemand.title }}</h3>
          <div class="header-tags">
            <a-tag :color="getStatusColor(selectedDemand.status)">{{ selectedDemand.status }}</a-tag>
            <a-tag :color="getUrgencyColor(selectedDemand.urgency)">{{ selectedDemand.urgency }}</a-tag>
          </div>
        </div>
        
        <div class="detail-content">
          <div class="detail-section">
            <h4>基本信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">发布企业：</span>
                <span class="value">{{ selectedDemand.company }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系人：</span>
                <span class="value">{{ selectedDemand.contact }}</span>
              </div>
              <div class="info-item">
                <span class="label">技术领域：</span>
                <span class="value">{{ selectedDemand.techField }}</span>
              </div>
              <div class="info-item">
                <span class="label">预算范围：</span>
                <span class="value">{{ selectedDemand.budget }}</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <h4>需求描述</h4>
            <p>{{ selectedDemand.fullDescription }}</p>
          </div>
          
          <div class="detail-section">
            <h4>技术要求</h4>
            <ul>
              <li v-for="requirement in selectedDemand.requirements" :key="requirement">
                {{ requirement }}
              </li>
            </ul>
          </div>
          
          <div class="detail-section">
            <h4>时间信息</h4>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">发布时间：</span>
                <span class="value">{{ selectedDemand.publishTime }}</span>
              </div>
              <div class="info-item">
                <span class="label">截止时间：</span>
                <span class="value">{{ selectedDemand.deadline }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="detail-actions">
          <a-button type="primary" size="large">
            联系企业
          </a-button>
          <a-button size="large" style="margin-left: 12px;">
            收藏需求
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Demand {
  id: number
  title: string
  company: string
  contact: string
  techField: string
  industry: string
  budget: string
  urgency: string
  status: string
  description: string
  fullDescription: string
  requirements: string[]
  publishTime: string
  deadline: string
}

// 响应式数据
const searchText = ref('')
const selectedIndustry = ref('')
const selectedStatus = ref('')
const selectedUrgency = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const detailModalVisible = ref(false)
const selectedDemand = ref<Demand | null>(null)

// 模拟数据
const demands = ref<Demand[]>([
  {
    id: 1,
    title: '智能制造生产线优化系统',
    company: '江苏智造科技有限公司',
    contact: '张工程师',
    techField: '工业互联网',
    industry: '制造业',
    budget: '50-100万',
    urgency: '高',
    status: '待解决',
    description: '需要开发一套智能制造生产线优化系统，提升生产效率...',
    fullDescription: '我们需要开发一套智能制造生产线优化系统，能够实时监控生产线状态，自动调整生产参数，提升生产效率和产品质量。系统需要集成现有的MES系统，支持多种设备协议，具备预测性维护功能。',
    requirements: ['支持OPC-UA协议', '实时数据处理能力', '机器学习算法集成', '可视化监控界面'],
    publishTime: '2024-01-15',
    deadline: '2024-03-15'
  },
  {
    id: 2,
    title: '新能源汽车电池管理系统',
    company: '绿色动力新能源',
    contact: '李总工',
    techField: '电池技术',
    industry: '新能源',
    budget: '100-200万',
    urgency: '中',
    status: '进行中',
    description: '开发高效的电池管理系统，提升电池安全性和使用寿命...',
    fullDescription: '需要开发新一代电池管理系统（BMS），具备精确的电池状态估算、热管理、安全保护等功能。系统要求高可靠性、低功耗，支持快充技术。',
    requirements: ['SOC/SOH精确估算', '热管理算法', '故障诊断功能', 'CAN通信协议'],
    publishTime: '2024-01-10',
    deadline: '2024-04-10'
  },
  {
    id: 3,
    title: '医疗影像AI识别算法',
    company: '智慧医疗科技',
    contact: '王主任',
    techField: '人工智能',
    industry: '生物医药',
    budget: '80-150万',
    urgency: '高',
    status: '待解决',
    description: '开发基于深度学习的医疗影像识别算法，提高诊断准确率...',
    fullDescription: '需要开发基于深度学习的医疗影像识别算法，主要用于CT、MRI影像的病灶检测和分类。要求算法准确率高、处理速度快，能够集成到现有PACS系统中。',
    requirements: ['深度学习模型', '高准确率识别', 'DICOM格式支持', 'GPU加速计算'],
    publishTime: '2024-01-20',
    deadline: '2024-05-20'
  }
])

// 计算属性
const filteredDemands = computed(() => {
  let filtered = demands.value

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(demand => 
      demand.title.toLowerCase().includes(search) ||
      demand.description.toLowerCase().includes(search) ||
      demand.techField.toLowerCase().includes(search)
    )
  }

  if (selectedIndustry.value) {
    filtered = filtered.filter(demand => demand.industry === selectedIndustry.value)
  }

  if (selectedStatus.value) {
    filtered = filtered.filter(demand => demand.status === selectedStatus.value)
  }

  if (selectedUrgency.value) {
    filtered = filtered.filter(demand => demand.urgency === selectedUrgency.value)
  }

  return filtered
})

const totalDemands = computed(() => filteredDemands.value.length)

// 方法
const handleSearch = () => {
  currentPage.value = 1
}

const handleIndustryChange = () => {
  currentPage.value = 1
}

const handleStatusChange = () => {
  currentPage.value = 1
}

const handleUrgencyChange = () => {
  currentPage.value = 1
}

const resetFilters = () => {
  searchText.value = ''
  selectedIndustry.value = ''
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

const viewDemandDetail = (demand: Demand) => {
  selectedDemand.value = demand
  detailModalVisible.value = true
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    '待解决': 'orange',
    '进行中': 'blue',
    '已解决': 'green'
  }
  return colors[status] || 'default'
}

const getUrgencyColor = (urgency: string) => {
  const colors: Record<string, string> = {
    '高': 'red',
    '中': 'orange',
    '低': 'green'
  }
  return colors[urgency] || 'default'
}

onMounted(() => {
  // 组件挂载后的初始化逻辑
})
</script>

<style scoped lang="less">
.demand-list-container {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;

  .page-header {
    margin-bottom: 32px;
    text-align: center;

    h2 {
      color: var(--text-primary);
      font-size: 32px;
      font-weight: 600;
      margin-bottom: 8px;
    }

    p {
      color: var(--text-secondary);
      font-size: 16px;
    }
  }

  .search-section {
    background: var(--component-bg);
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .demand-grid {
    margin-bottom: 32px;

    .demand-card {
      height: 100%;
      border-radius: 12px;
      transition: all 0.3s ease;
      cursor: pointer;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      }

      .card-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 16px;
        font-weight: 600;
      }

      .demand-content {
        .demand-info {
          margin-bottom: 16px;

          .info-row {
            display: flex;
            margin-bottom: 8px;
            font-size: 14px;

            .label {
              color: var(--text-secondary);
              width: 80px;
              flex-shrink: 0;
            }

            .value {
              color: var(--text-primary);
              flex: 1;
            }
          }
        }

        .demand-description {
          color: var(--text-secondary);
          font-size: 14px;
          line-height: 1.6;
          margin-bottom: 16px;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .demand-meta {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: var(--text-tertiary);
        }
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    padding: 24px 0;
  }
}

.demand-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);

    h3 {
      color: var(--text-primary);
      margin: 0;
    }

    .header-tags {
      display: flex;
      gap: 8px;
    }
  }

  .detail-content {
    .detail-section {
      margin-bottom: 24px;

      h4 {
        color: var(--text-primary);
        margin-bottom: 12px;
        font-size: 16px;
        font-weight: 600;
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;

        .info-item {
          display: flex;
          font-size: 14px;

          .label {
            color: var(--text-secondary);
            width: 100px;
            flex-shrink: 0;
          }

          .value {
            color: var(--text-primary);
            flex: 1;
          }
        }
      }

      p {
        color: var(--text-primary);
        line-height: 1.6;
        margin: 0;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          color: var(--text-primary);
          line-height: 1.6;
          margin-bottom: 4px;
        }
      }
    }
  }

  .detail-actions {
    display: flex;
    justify-content: center;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .demand-grid {
    :deep(.ant-col) {
      width: 50% !important;
      max-width: 50% !important;
      flex: 0 0 50% !important;
    }
  }
}

@media (max-width: 768px) {
  .demand-list-container {
    padding: 16px;

    .search-section {
      padding: 16px;

      :deep(.ant-row) {
        flex-direction: column;

        .ant-col {
          width: 100% !important;
          margin-bottom: 12px;
        }
      }
    }

    .demand-grid {
      :deep(.ant-col) {
        width: 100% !important;
        max-width: 100% !important;
        flex: 0 0 100% !important;
      }
    }
  }
}
</style> 