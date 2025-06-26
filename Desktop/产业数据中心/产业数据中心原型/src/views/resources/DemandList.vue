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
            <a-select-option value="open">开放中</a-select-option>
            <a-select-option value="matched">已匹配</a-select-option>
            <a-select-option value="closed">已关闭</a-select-option>
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
          <a-button type="primary" @click="resetFilters" size="large">
            重置筛选
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 需求列表 -->
    <div class="demand-cards">
      <a-row :gutter="[16, 16]">
        <a-col 
          v-for="demand in filteredDemands" 
          :key="demand.id" 
          :xs="24" 
          :sm="12" 
          :lg="8" 
          :xl="6"
        >
          <a-card 
            class="demand-card" 
            hoverable
            @click="showDemandDetail(demand)"
          >
            <template #title>
              <div class="card-title">
                {{ demand.title }}
                <a-tag :color="getStatusColor(demand.status)">
                  {{ getStatusText(demand.status) }}
                </a-tag>
              </div>
            </template>
            
            <div class="demand-content">
              <div class="demand-info">
                <p class="description">{{ demand.description }}</p>
                
                <div class="meta-info">
                  <div class="info-row">
                    <span class="label">企业：</span>
                    <span class="value">{{ demand.company }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">行业：</span>
                    <span class="value">{{ demand.industry }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">预算：</span>
                    <span class="value budget">{{ demand.budget }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">紧急程度：</span>
                    <a-tag :color="getUrgencyColor(demand.urgency)">
                      {{ demand.urgency }}
                    </a-tag>
                  </div>
                </div>
              </div>
              
              <div class="demand-footer">
                <div class="tech-tags">
                  <a-tag 
                    v-for="tech in demand.technologies.slice(0, 2)" 
                    :key="tech"
                    size="small"
                  >
                    {{ tech }}
                  </a-tag>
                  <span v-if="demand.technologies.length > 2" class="more-tags">
                    +{{ demand.technologies.length - 2 }}
                  </span>
                </div>
                
                <div class="action-buttons">
                  <a-button size="small" @click.stop="viewDemand(demand)">
                    查看详情
                  </a-button>
                  <a-button 
                    v-if="demand.status === 'open'" 
                    type="primary" 
                    size="small"
                    @click.stop="matchDemand(demand)"
                  >
                    立即匹配
                  </a-button>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :show-size-changer="true"
        :show-quick-jumper="true"
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
      <div v-if="selectedDemand" class="demand-detail-modal">
        <div class="detail-header">
          <h3>{{ selectedDemand.title }}</h3>
          <a-tag :color="getStatusColor(selectedDemand.status)">
            {{ getStatusText(selectedDemand.status) }}
          </a-tag>
        </div>
        
        <div class="detail-content">
          <div class="basic-info">
            <h4>基本信息</h4>
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="发布企业">{{ selectedDemand.company }}</a-descriptions-item>
              <a-descriptions-item label="所属行业">{{ selectedDemand.industry }}</a-descriptions-item>
              <a-descriptions-item label="项目预算">{{ selectedDemand.budget }}</a-descriptions-item>
              <a-descriptions-item label="紧急程度">
                <a-tag :color="getUrgencyColor(selectedDemand.urgency)">
                  {{ selectedDemand.urgency }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="发布时间">{{ selectedDemand.publishTime }}</a-descriptions-item>
              <a-descriptions-item label="截止时间">{{ selectedDemand.deadline }}</a-descriptions-item>
            </a-descriptions>
          </div>
          
          <div class="demand-description">
            <h4>需求描述</h4>
            <p>{{ selectedDemand.description }}</p>
          </div>
          
          <div class="tech-requirements">
            <h4>技术要求</h4>
            <div class="tech-list">
              <a-tag 
                v-for="tech in selectedDemand.technologies" 
                :key="tech"
                color="blue"
              >
                {{ tech }}
              </a-tag>
            </div>
          </div>
          
          <div class="contact-info">
            <h4>联系方式</h4>
            <p>联系人：{{ selectedDemand.contact }}</p>
            <p>电话：{{ selectedDemand.phone }}</p>
            <p>邮箱：{{ selectedDemand.email }}</p>
          </div>
        </div>
        
        <div class="modal-actions">
          <a-button @click="detailModalVisible = false">关闭</a-button>
          <a-button 
            v-if="selectedDemand.status === 'open'" 
            type="primary"
            @click="matchDemand(selectedDemand)"
          >
            立即匹配
          </a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// 响应式数据
const searchText = ref('')
const selectedIndustry = ref('')
const selectedStatus = ref('')
const selectedUrgency = ref('')
const detailModalVisible = ref(false)
const selectedDemand = ref<any>(null)

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

// 模拟需求数据
const demands = ref([
  {
    id: 1,
    title: '智能制造生产线自动化改造',
    description: '需要对传统生产线进行智能化改造，实现自动化生产和质量控制',
    company: '华东制造股份有限公司',
    industry: '制造业',
    budget: '500-1000万',
    urgency: '高',
    status: 'open',
    technologies: ['工业互联网', '机器视觉', 'PLC控制', '数据采集'],
    publishTime: '2024-01-15',
    deadline: '2024-03-15',
    contact: '张经理',
    phone: '138****1234',
    email: 'zhang@company.com'
  },
  {
    id: 2,
    title: '医疗影像AI诊断系统开发',
    description: '开发基于深度学习的医疗影像自动诊断系统，提升诊断准确率',
    company: '仁和医疗集团',
    industry: '生物医药',
    budget: '200-500万',
    urgency: '中',
    status: 'open',
    technologies: ['深度学习', '医疗影像', 'Python', 'TensorFlow'],
    publishTime: '2024-01-20',
    deadline: '2024-06-20',
    contact: '李主任',
    phone: '139****5678',
    email: 'li@hospital.com'
  },
  {
    id: 3,
    title: '新能源汽车电池管理系统',
    description: '研发高效的动力电池管理系统，提升电池使用寿命和安全性',
    company: '绿驰新能源科技',
    industry: '新能源',
    budget: '1000-2000万',
    urgency: '高',
    status: 'matched',
    technologies: ['BMS系统', '电池技术', '嵌入式开发', '热管理'],
    publishTime: '2024-01-10',
    deadline: '2024-05-10',
    contact: '王总工',
    phone: '137****9012',
    email: 'wang@newenergy.com'
  }
])

// 计算属性：过滤后的需求列表
const filteredDemands = computed(() => {
  let filtered = demands.value

  if (searchText.value) {
    filtered = filtered.filter(demand => 
      demand.title.includes(searchText.value) ||
      demand.description.includes(searchText.value) ||
      demand.technologies.some(tech => tech.includes(searchText.value))
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

// 方法
const handleSearch = () => {
  pagination.current = 1
}

const handleIndustryChange = () => {
  pagination.current = 1
}

const handleStatusChange = () => {
  pagination.current = 1
}

const handleUrgencyChange = () => {
  pagination.current = 1
}

const resetFilters = () => {
  searchText.value = ''
  selectedIndustry.value = ''
  selectedStatus.value = ''
  selectedUrgency.value = ''
  pagination.current = 1
}

const showDemandDetail = (demand: any) => {
  selectedDemand.value = demand
  detailModalVisible.value = true
}

const viewDemand = (demand: any) => {
  showDemandDetail(demand)
}

const matchDemand = (demand: any) => {
  message.success(`正在为需求"${demand.title}"寻找匹配的解决方案...`)
  detailModalVisible.value = false
}

const handlePageChange = (page: number) => {
  pagination.current = page
}

const handlePageSizeChange = (current: number, size: number) => {
  pagination.pageSize = size
  pagination.current = 1
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    open: 'green',
    matched: 'blue',
    closed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    open: '开放中',
    matched: '已匹配',
    closed: '已关闭'
  }
  return texts[status] || status
}

const getUrgencyColor = (urgency: string) => {
  const colors: Record<string, string> = {
    高: 'red',
    中: 'orange',
    低: 'green'
  }
  return colors[urgency] || 'default'
}

// 生命周期
onMounted(() => {
  pagination.total = demands.value.length
})
</script>

<style scoped lang="less">
.demand-list-container {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;

  .page-header {
    margin-bottom: 24px;
    
    h2 {
      color: var(--text-primary);
      margin-bottom: 8px;
    }
    
    p {
      color: var(--text-secondary);
      margin: 0;
    }
  }

  .search-section {
    margin-bottom: 24px;
    padding: 20px;
    background: var(--component-bg);
    border-radius: 12px;
    border: 1px solid var(--border-color);
  }

  .demand-cards {
    margin-bottom: 32px;

    .demand-card {
      height: 100%;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      background: var(--component-bg);
      transition: all 0.3s ease;

      &:hover {
        border-color: var(--primary-color);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
      }

      .card-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        font-weight: 600;
      }

      .demand-content {
        .description {
          color: var(--text-secondary);
          margin-bottom: 16px;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .meta-info {
          margin-bottom: 16px;

          .info-row {
            display: flex;
            margin-bottom: 4px;
            font-size: 12px;

            .label {
              color: var(--text-secondary);
              min-width: 60px;
            }

            .value {
              color: var(--text-primary);
              
              &.budget {
                color: var(--success-color);
                font-weight: 600;
              }
            }
          }
        }

        .demand-footer {
          .tech-tags {
            margin-bottom: 12px;

            .more-tags {
              color: var(--text-secondary);
              font-size: 12px;
            }
          }

          .action-buttons {
            display: flex;
            gap: 8px;
          }
        }
      }
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }
}

.demand-detail-modal {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h3 {
      margin: 0;
      color: var(--text-primary);
    }
  }

  .detail-content {
    h4 {
      color: var(--text-primary);
      margin-bottom: 12px;
      margin-top: 24px;
      
      &:first-child {
        margin-top: 0;
      }
    }

    .tech-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .demand-list-container {
    padding: 16px;

    .search-section {
      .ant-row > .ant-col {
        margin-bottom: 12px;
      }
    }
  }
}
</style> 