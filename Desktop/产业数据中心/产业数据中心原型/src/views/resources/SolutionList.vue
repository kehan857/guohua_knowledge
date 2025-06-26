<template>
  <div class="solution-list list-container">
    <div class="page-header">
      <h1 class="h1-title">解决方案库</h1>
      <div class="header-actions">
        <a-button type="primary" @click="showAddModal = true">
          <template #icon><PlusOutlined /></template>
          添加解决方案
        </a-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="filters.keyword"
            placeholder="搜索解决方案名称、描述"
            @change="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.category"
            placeholder="解决方案类型"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="云计算">云计算</a-select-option>
            <a-select-option value="大数据">大数据</a-select-option>
            <a-select-option value="人工智能">人工智能</a-select-option>
            <a-select-option value="物联网">物联网</a-select-option>
            <a-select-option value="区块链">区块链</a-select-option>
            <a-select-option value="安全防护">安全防护</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.industry"
            placeholder="适用行业"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="制造业">制造业</a-select-option>
            <a-select-option value="金融业">金融业</a-select-option>
            <a-select-option value="教育">教育</a-select-option>
            <a-select-option value="医疗">医疗</a-select-option>
            <a-select-option value="零售">零售</a-select-option>
            <a-select-option value="政府">政府</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.maturity"
            placeholder="成熟度"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="概念验证">概念验证</a-select-option>
            <a-select-option value="测试版">测试版</a-select-option>
            <a-select-option value="生产就绪">生产就绪</a-select-option>
            <a-select-option value="商业化">商业化</a-select-option>
          </a-select>
        </a-col>
      </a-row>
      
      <div class="filter-actions">
        <a-button @click="resetFilters">重置</a-button>
        <a-button type="primary" @click="exportData">导出</a-button>
      </div>
    </div>

    <!-- 解决方案卡片列表 -->
    <div class="solution-grid">
      <a-row :gutter="[16, 16]">
        <a-col :span="8" v-for="solution in paginatedSolutions" :key="solution.id">
          <a-card 
            class="solution-card"
            :hoverable="true"
            @click="viewSolutionDetail(solution)"
          >
            <template #cover>
              <div class="solution-cover">
                <img :src="solution.image || '/api/placeholder/300/180'" alt="解决方案图片" />
                <div class="solution-overlay">
                  <a-tag :color="getCategoryColor(solution.category)">
                    {{ solution.category }}
                  </a-tag>
                  <a-tag :color="getMaturityColor(solution.maturity)">
                    {{ solution.maturity }}
                  </a-tag>
                </div>
              </div>
            </template>
            
            <a-card-meta 
              :title="solution.name"
              :description="solution.description"
            />
            
            <div class="solution-footer">
              <div class="solution-stats">
                <span><TeamOutlined /> {{ solution.team }}</span>
                <span><CalendarOutlined /> {{ solution.updateTime }}</span>
              </div>
              <a-rate :value="solution.rating" disabled allow-half size="small" />
            </div>
            
            <div class="solution-actions">
              <a-button type="link" size="small" @click.stop="viewSolutionDetail(solution)">
                查看详情
              </a-button>
              <a-button type="link" size="small" @click.stop="editSolution(solution)">
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个解决方案吗？"
                @confirm="deleteSolution(solution.id)"
                @click.stop
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
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
        :total="filteredSolutions.length"
        show-size-changer
        show-quick-jumper
        show-total
        @change="handlePageChange"
      />
    </div>

    <!-- 添加/编辑解决方案模态框 -->
    <a-modal
      v-model:open="showAddModal"
      :title="editingSolution ? '编辑解决方案' : '添加解决方案'"
      width="800px"
      @ok="handleSaveSolution"
      @cancel="handleCancelAdd"
    >
      <a-form
        ref="formRef"
        :model="solutionForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="解决方案名称" name="name" :rules="[{ required: true, message: '请输入解决方案名称' }]">
          <a-input v-model:value="solutionForm.name" />
        </a-form-item>
        <a-form-item label="解决方案类型" name="category" :rules="[{ required: true, message: '请选择解决方案类型' }]">
          <a-select v-model:value="solutionForm.category">
            <a-select-option value="云计算">云计算</a-select-option>
            <a-select-option value="大数据">大数据</a-select-option>
            <a-select-option value="人工智能">人工智能</a-select-option>
            <a-select-option value="物联网">物联网</a-select-option>
            <a-select-option value="区块链">区块链</a-select-option>
            <a-select-option value="安全防护">安全防护</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="适用行业" name="industry">
          <a-select v-model:value="solutionForm.industry" mode="multiple">
            <a-select-option value="制造业">制造业</a-select-option>
            <a-select-option value="金融业">金融业</a-select-option>
            <a-select-option value="教育">教育</a-select-option>
            <a-select-option value="医疗">医疗</a-select-option>
            <a-select-option value="零售">零售</a-select-option>
            <a-select-option value="政府">政府</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="成熟度" name="maturity" :rules="[{ required: true, message: '请选择成熟度' }]">
          <a-select v-model:value="solutionForm.maturity">
            <a-select-option value="概念验证">概念验证</a-select-option>
            <a-select-option value="测试版">测试版</a-select-option>
            <a-select-option value="生产就绪">生产就绪</a-select-option>
            <a-select-option value="商业化">商业化</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="负责团队" name="team" :rules="[{ required: true, message: '请输入负责团队' }]">
          <a-input v-model:value="solutionForm.team" />
        </a-form-item>
        <a-form-item label="解决方案描述" name="description" :rules="[{ required: true, message: '请输入解决方案描述' }]">
          <a-textarea v-model:value="solutionForm.description" :rows="4" />
        </a-form-item>
        <a-form-item label="核心功能" name="features">
          <a-textarea v-model:value="solutionForm.features" :rows="3" placeholder="请列出核心功能特性" />
        </a-form-item>
        <a-form-item label="技术栈" name="techStack">
          <a-input v-model:value="solutionForm.techStack" placeholder="如：Vue3, Spring Boot, MySQL" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  PlusOutlined, 
  SearchOutlined, 
  TeamOutlined, 
  CalendarOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

interface Solution {
  id: string
  name: string
  category: string
  industry: string[]
  maturity: string
  team: string
  description: string
  features: string
  techStack: string
  image?: string
  rating: number
  updateTime: string
}

// 响应式数据
const solutions = ref<Solution[]>([])
const showAddModal = ref(false)
const editingSolution = ref<Solution | null>(null)

const filters = reactive({
  keyword: '',
  category: '',
  industry: '',
  maturity: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 9,
  total: 0
})

const solutionForm = reactive<Partial<Solution>>({
  name: '',
  category: '',
  industry: [],
  maturity: '',
  team: '',
  description: '',
  features: '',
  techStack: ''
})

// 计算属性
const filteredSolutions = computed(() => {
  return solutions.value.filter(solution => {
    const matchKeyword = !filters.keyword || 
      solution.name.toLowerCase().includes(filters.keyword.toLowerCase()) ||
      solution.description.toLowerCase().includes(filters.keyword.toLowerCase())
    
    const matchCategory = !filters.category || solution.category === filters.category
    const matchIndustry = !filters.industry || solution.industry.includes(filters.industry)
    const matchMaturity = !filters.maturity || solution.maturity === filters.maturity
    
    return matchKeyword && matchCategory && matchIndustry && matchMaturity
  })
})

const paginatedSolutions = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredSolutions.value.slice(start, end)
})

// 方法
const handleSearch = () => {
  pagination.current = 1
}

const resetFilters = () => {
  filters.keyword = ''
  filters.category = ''
  filters.industry = ''
  filters.maturity = ''
  pagination.current = 1
}

const handlePageChange = () => {
  // 分页变化处理
}

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    '云计算': 'blue',
    '大数据': 'green',
    '人工智能': 'purple',
    '物联网': 'orange',
    '区块链': 'red',
    '安全防护': 'cyan'
  }
  return colors[category] || 'default'
}

const getMaturityColor = (maturity: string) => {
  const colors: Record<string, string> = {
    '概念验证': 'red',
    '测试版': 'orange',
    '生产就绪': 'blue',
    '商业化': 'green'
  }
  return colors[maturity] || 'default'
}

const viewSolutionDetail = (solution: Solution) => {
  message.info(`查看解决方案: ${solution.name}`)
}

const editSolution = (solution: Solution) => {
  editingSolution.value = solution
  Object.assign(solutionForm, solution)
  showAddModal.value = true
}

const deleteSolution = (id: string) => {
  solutions.value = solutions.value.filter(s => s.id !== id)
  message.success('删除成功')
}

const handleSaveSolution = () => {
  if (editingSolution.value) {
    // 编辑逻辑
    const index = solutions.value.findIndex(s => s.id === editingSolution.value?.id)
    if (index !== -1) {
      solutions.value[index] = { ...solutionForm } as Solution
    }
    message.success('编辑成功')
  } else {
    // 新增逻辑
    const newSolution: Solution = {
      ...solutionForm as Solution,
      id: Date.now().toString(),
      rating: 4.5,
      updateTime: new Date().toLocaleDateString()
    }
    solutions.value.unshift(newSolution)
    message.success('添加成功')
  }
  
  handleCancelAdd()
}

const handleCancelAdd = () => {
  showAddModal.value = false
  editingSolution.value = null
  Object.assign(solutionForm, {
    name: '',
    category: '',
    industry: [],
    maturity: '',
    team: '',
    description: '',
    features: '',
    techStack: ''
  })
}

const exportData = () => {
  message.info('导出功能开发中...')
}

// 初始化数据
onMounted(() => {
  solutions.value = [
    {
      id: '1',
      name: '智能制造数据平台',
      category: '大数据',
      industry: ['制造业'],
      maturity: '生产就绪',
      team: '数据技术团队',
      description: '为制造企业提供全流程数据采集、分析和决策支持的智能平台',
      features: '实时数据采集、智能分析、可视化报表',
      techStack: 'Vue3, Spring Boot, ClickHouse',
      rating: 4.8,
      updateTime: '2024-01-15'
    },
    {
      id: '2',
      name: '金融风控AI引擎',
      category: '人工智能',
      industry: ['金融业'],
      maturity: '商业化',
      team: 'AI算法团队',
      description: '基于机器学习的金融风险评估和反欺诈解决方案',
      features: '风险建模、实时监控、智能预警',
      techStack: 'Python, TensorFlow, Redis',
      rating: 4.9,
      updateTime: '2024-01-10'
    },
    {
      id: '3',
      name: '云原生应用平台',
      category: '云计算',
      industry: ['制造业', '金融业', '教育'],
      maturity: '生产就绪',
      team: '云平台团队',
      description: '企业级云原生应用开发、部署和运维平台',
      features: '容器化部署、自动扩缩容、服务治理',
      techStack: 'Kubernetes, Docker, Istio',
      rating: 4.6,
      updateTime: '2024-01-08'
    }
  ]
})
</script>

<style lang="less" scoped>
.solution-list {
  .solution-grid {
    margin-top: 16px;
    
    .solution-card {
      height: 100%;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
      }
      
      .solution-cover {
        position: relative;
        overflow: hidden;
        
        img {
          width: 100%;
          height: 180px;
          object-fit: cover;
          transition: transform 0.3s ease;
        }
        
        &:hover img {
          transform: scale(1.05);
        }
        
        .solution-overlay {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          gap: 4px;
          flex-direction: column;
          align-items: flex-end;
        }
      }
      
      .solution-footer {
        margin-top: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .solution-stats {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: var(--text-secondary);
          
          span {
            display: flex;
            align-items: center;
            gap: 4px;
          }
        }
      }
      
      .solution-actions {
        margin-top: 12px;
        text-align: center;
        border-top: 1px solid var(--border-color);
        padding-top: 12px;
        display: flex;
        justify-content: center;
        gap: 8px;
      }
    }
  }
  
  .pagination-wrapper {
    margin-top: 32px;
    text-align: center;
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .solution-grid {
    :deep(.ant-col) {
      &:nth-child(3n) {
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .solution-grid {
    :deep(.ant-col) {
      span: 24 !important;
      margin-bottom: 16px;
    }
  }
}
</style> 