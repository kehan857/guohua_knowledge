<template>
  <div class="expert-list">
    <div class="page-header">
      <div class="header-content">
        <h1>专家库</h1>
        <p>汇聚行业专家资源，支撑技术决策和项目实施</p>
      </div>
      <a-button type="primary" @click="showAddModal = true">
        <template #icon><PlusOutlined /></template>
        添加专家
      </a-button>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input
            v-model:value="filters.keyword"
            placeholder="搜索专家姓名、专业领域"
            @change="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </a-input>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.expertise"
            placeholder="专业领域"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="云计算">云计算</a-select-option>
            <a-select-option value="大数据">大数据</a-select-option>
            <a-select-option value="人工智能">人工智能</a-select-option>
            <a-select-option value="物联网">物联网</a-select-option>
            <a-select-option value="区块链">区块链</a-select-option>
            <a-select-option value="网络安全">网络安全</a-select-option>
            <a-select-option value="软件架构">软件架构</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.level"
            placeholder="专家等级"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="初级">初级</a-select-option>
            <a-select-option value="中级">中级</a-select-option>
            <a-select-option value="高级">高级</a-select-option>
            <a-select-option value="资深">资深</a-select-option>
            <a-select-option value="首席">首席</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select
            v-model:value="filters.status"
            placeholder="状态"
            @change="handleSearch"
            allow-clear
          >
            <a-select-option value="可用">可用</a-select-option>
            <a-select-option value="忙碌">忙碌</a-select-option>
            <a-select-option value="休假">休假</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-space>
            <a-button @click="resetFilters">重置</a-button>
            <a-button type="primary" @click="exportData">导出</a-button>
          </a-space>
        </a-col>
      </a-row>
    </div>

    <!-- 专家卡片列表 -->
    <div class="expert-grid">
      <a-row :gutter="[16, 16]">
        <a-col :span="6" v-for="expert in paginatedExperts" :key="expert.id">
          <a-card 
            class="expert-card"
            :hoverable="true"
            @click="viewExpertDetail(expert)"
          >
            <div class="expert-avatar">
              <a-avatar 
                :size="80" 
                :src="expert.avatar || '/api/placeholder/80/80'"
                :style="{ backgroundColor: expert.avatar ? 'transparent' : '#1890ff' }"
              >
                {{ !expert.avatar ? expert.name.charAt(0) : '' }}
              </a-avatar>
              <div class="expert-status">
                <a-badge 
                  :status="getStatusBadge(expert.status)" 
                  :text="expert.status"
                />
              </div>
            </div>
            
            <div class="expert-info">
              <h3>{{ expert.name }}</h3>
              <p class="expert-title">{{ expert.title }}</p>
              <p class="expert-company">{{ expert.company }}</p>
              
              <div class="expert-tags">
                <a-tag 
                  v-for="skill in expert.expertise.slice(0, 3)" 
                  :key="skill"
                  :color="getExpertiseColor(skill)"
                >
                  {{ skill }}
                </a-tag>
                <a-tag v-if="expert.expertise.length > 3">
                  +{{ expert.expertise.length - 3 }}
                </a-tag>
              </div>
              
              <div class="expert-stats">
                <div class="stat-item">
                  <span class="stat-label">项目经验</span>
                  <span class="stat-value">{{ expert.projectCount }}+</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">专业年限</span>
                  <span class="stat-value">{{ expert.experience }}年</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">评分</span>
                  <a-rate :value="expert.rating" disabled allow-half size="small" />
                </div>
              </div>
            </div>
            
            <div class="expert-actions">
              <a-button type="link" size="small" @click.stop="contactExpert(expert)">
                联系
              </a-button>
              <a-button type="link" size="small" @click.stop="viewExpertDetail(expert)">
                详情
              </a-button>
              <a-button type="link" size="small" @click.stop="editExpert(expert)">
                编辑
              </a-button>
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
        :total="filteredExperts.length"
        show-size-changer
        show-quick-jumper
        show-total
        @change="handlePageChange"
      />
    </div>

    <!-- 添加/编辑专家模态框 -->
    <a-modal
      v-model:open="showAddModal"
      :title="editingExpert ? '编辑专家' : '添加专家'"
      width="600px"
      @ok="handleSaveExpert"
      @cancel="handleCancelAdd"
    >
      <a-form
        ref="formRef"
        :model="expertForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="专家姓名" name="name" :rules="[{ required: true, message: '请输入专家姓名' }]">
          <a-input v-model:value="expertForm.name" />
        </a-form-item>
        <a-form-item label="职位" name="title" :rules="[{ required: true, message: '请输入职位' }]">
          <a-input v-model:value="expertForm.title" />
        </a-form-item>
        <a-form-item label="所属公司" name="company" :rules="[{ required: true, message: '请输入所属公司' }]">
          <a-input v-model:value="expertForm.company" />
        </a-form-item>
        <a-form-item label="专家等级" name="level" :rules="[{ required: true, message: '请选择专家等级' }]">
          <a-select v-model:value="expertForm.level">
            <a-select-option value="初级">初级</a-select-option>
            <a-select-option value="中级">中级</a-select-option>
            <a-select-option value="高级">高级</a-select-option>
            <a-select-option value="资深">资深</a-select-option>
            <a-select-option value="首席">首席</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="专业领域" name="expertise" :rules="[{ required: true, message: '请选择专业领域' }]">
          <a-select v-model:value="expertForm.expertise" mode="multiple">
            <a-select-option value="云计算">云计算</a-select-option>
            <a-select-option value="大数据">大数据</a-select-option>
            <a-select-option value="人工智能">人工智能</a-select-option>
            <a-select-option value="物联网">物联网</a-select-option>
            <a-select-option value="区块链">区块链</a-select-option>
            <a-select-option value="网络安全">网络安全</a-select-option>
            <a-select-option value="软件架构">软件架构</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="工作经验" name="experience" :rules="[{ required: true, message: '请输入工作经验年限' }]">
          <a-input-number v-model:value="expertForm.experience" :min="0" :max="50" /> 年
        </a-form-item>
        <a-form-item label="联系方式" name="contact" :rules="[{ required: true, message: '请输入联系方式' }]">
          <a-input v-model:value="expertForm.contact" />
        </a-form-item>
        <a-form-item label="专家简介" name="bio">
          <a-textarea v-model:value="expertForm.bio" :rows="4" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-select v-model:value="expertForm.status">
            <a-select-option value="可用">可用</a-select-option>
            <a-select-option value="忙碌">忙碌</a-select-option>
            <a-select-option value="休假">休假</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

interface Expert {
  id: string
  name: string
  title: string
  company: string
  level: string
  expertise: string[]
  experience: number
  contact: string
  bio: string
  status: string
  avatar?: string
  rating: number
  projectCount: number
}

// 响应式数据
const experts = ref<Expert[]>([])
const showAddModal = ref(false)
const editingExpert = ref<Expert | null>(null)

const filters = reactive({
  keyword: '',
  expertise: '',
  level: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
})

const expertForm = reactive<Partial<Expert>>({
  name: '',
  title: '',
  company: '',
  level: '',
  expertise: [],
  experience: 0,
  contact: '',
  bio: '',
  status: '可用'
})

// 计算属性
const filteredExperts = computed(() => {
  return experts.value.filter(expert => {
    return (!filters.keyword || 
            expert.name.includes(filters.keyword) || 
            expert.expertise.some(e => e.includes(filters.keyword))) &&
           (!filters.expertise || expert.expertise.includes(filters.expertise)) &&
           (!filters.level || expert.level === filters.level) &&
           (!filters.status || expert.status === filters.status)
  })
})

const paginatedExperts = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredExperts.value.slice(start, end)
})

// 方法
const getExpertiseColor = (expertise: string) => {
  const colors: Record<string, string> = {
    '云计算': 'blue',
    '大数据': 'green',
    '人工智能': 'purple',
    '物联网': 'orange',
    '区块链': 'red',
    '网络安全': 'volcano',
    '软件架构': 'geekblue'
  }
  return colors[expertise] || 'default'
}

const getStatusBadge = (status: string) => {
  const badges: Record<string, string> = {
    '可用': 'success',
    '忙碌': 'warning',
    '休假': 'default'
  }
  return badges[status] || 'default'
}

const handleSearch = () => {
  pagination.current = 1
}

const resetFilters = () => {
  Object.assign(filters, {
    keyword: '',
    expertise: '',
    level: '',
    status: ''
  })
  handleSearch()
}

const handlePageChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
}

const viewExpertDetail = (expert: Expert) => {
  message.info(`查看专家详情: ${expert.name}`)
}

const contactExpert = (expert: Expert) => {
  message.info(`联系专家: ${expert.name} (${expert.contact})`)
}

const editExpert = (expert: Expert) => {
  editingExpert.value = expert
  Object.assign(expertForm, expert)
  showAddModal.value = true
}

const handleSaveExpert = () => {
  if (editingExpert.value) {
    // 编辑现有专家
    const index = experts.value.findIndex(e => e.id === editingExpert.value!.id)
    if (index > -1) {
      experts.value[index] = { ...expertForm as Expert, id: editingExpert.value.id }
    }
    message.success('专家信息更新成功')
  } else {
    // 添加新专家
    const newExpert: Expert = {
      ...expertForm as Expert,
      id: Date.now().toString(),
      rating: 0,
      projectCount: 0
    }
    experts.value.unshift(newExpert)
    message.success('专家添加成功')
  }
  
  handleCancelAdd()
}

const handleCancelAdd = () => {
  showAddModal.value = false
  editingExpert.value = null
  Object.assign(expertForm, {
    name: '',
    title: '',
    company: '',
    level: '',
    expertise: [],
    experience: 0,
    contact: '',
    bio: '',
    status: '可用'
  })
}

const exportData = () => {
  message.info('导出功能开发中...')
}

// 初始化数据
const initData = () => {
  experts.value = [
    {
      id: '1',
      name: '张明',
      title: '首席架构师',
      company: '天云科技',
      level: '首席',
      expertise: ['云计算', '软件架构', '大数据'],
      experience: 12,
      contact: 'zhang.ming@tianyun.com',
      bio: '资深云计算架构师，在大型分布式系统设计方面有丰富经验',
      status: '可用',
      rating: 4.8,
      projectCount: 25
    },
    {
      id: '2',
      name: '李华',
      title: 'AI算法专家',
      company: '天云科技',
      level: '高级',
      expertise: ['人工智能', '机器学习', '深度学习'],
      experience: 8,
      contact: 'li.hua@tianyun.com',
      bio: '专注于计算机视觉和自然语言处理算法研究',
      status: '可用',
      rating: 4.6,
      projectCount: 18
    },
    {
      id: '3',
      name: '王强',
      title: '大数据架构师',
      company: '天云科技',
      level: '资深',
      expertise: ['大数据', '数据挖掘', '实时计算'],
      experience: 10,
      contact: 'wang.qiang@tianyun.com',
      bio: '大数据平台架构和实时数据处理专家',
      status: '忙碌',
      rating: 4.7,
      projectCount: 22
    }
  ]
}

onMounted(() => {
  initData()
})
</script>

<style scoped>
.expert-list {
  padding: 24px;
  background: var(--bg-primary);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-content p {
  margin: 0;
  color: var(--text-secondary);
}

.filter-section {
  background: var(--component-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
  border: 1px solid var(--border-color);
}

.expert-grid {
  margin-bottom: 24px;
}

.expert-card {
  height: 100%;
  transition: all 0.3s ease;
}

.expert-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.expert-avatar {
  text-align: center;
  margin-bottom: 16px;
}

.expert-status {
  margin-top: 8px;
}

.expert-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}

.expert-title {
  margin: 0 0 4px 0;
  color: var(--primary-color);
  font-weight: 500;
  text-align: center;
}

.expert-company {
  margin: 0 0 12px 0;
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
}

.expert-tags {
  text-align: center;
  margin-bottom: 16px;
}

.expert-tags .ant-tag {
  margin-bottom: 4px;
}

.expert-stats {
  padding: 12px 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-weight: 600;
  color: var(--text-primary);
}

.expert-actions {
  display: flex;
  justify-content: space-around;
  padding-top: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}
</style> 