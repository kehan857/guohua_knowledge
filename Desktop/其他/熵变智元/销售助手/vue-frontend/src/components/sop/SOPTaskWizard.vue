<template>
  <div class="sop-task-wizard">
    <el-card class="wizard-container">
      <!-- 步骤指示器 -->
      <div class="wizard-header">
        <el-steps
          :active="currentStep"
          :space="200"
          finish-status="success"
          process-status="process"
        >
          <el-step title="基本信息" description="设置任务名称和类型" />
          <el-step title="选择目标" description="选择执行账号和目标对象" />
          <el-step title="设计流程" description="配置SOP执行步骤" />
          <el-step title="预览确认" description="检查并确认任务配置" />
        </el-steps>
      </div>

      <!-- 步骤内容 -->
      <div class="wizard-content">
        <!-- 步骤1: 基本信息 -->
        <div v-show="currentStep === 0" class="step-content">
          <div class="step-title">
            <h3>📝 基本信息配置</h3>
            <p>为您的SOP任务设置基本信息</p>
          </div>

          <el-form
            ref="basicFormRef"
            :model="taskData.basic"
            :rules="basicRules"
            label-width="100px"
            class="basic-form"
          >
            <el-form-item label="任务名称" prop="name" required>
              <el-input
                v-model="taskData.basic.name"
                placeholder="请输入任务名称，如：新客户破冰SOP"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="任务描述" prop="description">
              <el-input
                v-model="taskData.basic.description"
                type="textarea"
                :rows="4"
                placeholder="描述这个SOP任务的目的和适用场景..."
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="目标类型" prop="targetType" required>
              <el-radio-group v-model="taskData.basic.targetType">
                <el-radio-button label="friend">
                  <el-icon><User /></el-icon>
                  好友
                </el-radio-button>
                <el-radio-button label="group">
                  <el-icon><UserFilled /></el-icon>
                  群组
                </el-radio-button>
                <el-radio-button label="tag">
                  <el-icon><PriceTag /></el-icon>
                  标签分组
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="执行优先级" prop="priority">
              <el-select v-model="taskData.basic.priority" placeholder="选择优先级">
                <el-option label="低优先级" value="low" />
                <el-option label="普通优先级" value="normal" />
                <el-option label="高优先级" value="high" />
                <el-option label="紧急" value="urgent" />
              </el-select>
            </el-form-item>

            <el-form-item label="任务标签" prop="tags">
              <el-select
                v-model="taskData.basic.tags"
                multiple
                filterable
                allow-create
                placeholder="添加标签便于分类管理"
              >
                <el-option
                  v-for="tag in predefinedTags"
                  :key="tag"
                  :label="tag"
                  :value="tag"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 选择目标 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="step-title">
            <h3>👥 选择执行目标</h3>
            <p>选择要执行此任务的微信账号和目标对象</p>
          </div>

          <div class="target-selection">
            <!-- 执行账号选择 -->
            <div class="section">
              <h4 class="section-title">执行账号 *</h4>
              <div class="accounts-grid">
                <div
                  v-for="account in availableAccounts"
                  :key="account.id"
                  class="account-item"
                  :class="{ selected: isAccountSelected(account.id) }"
                  @click="toggleAccount(account.id)"
                >
                  <el-avatar :src="account.avatar" :alt="account.name">
                    {{ account.name.charAt(0) }}
                  </el-avatar>
                  <div class="account-info">
                    <div class="account-name">{{ account.name }}</div>
                    <div class="account-status" :class="account.status">
                      {{ getStatusText(account.status) }}
                    </div>
                  </div>
                  <el-icon v-if="isAccountSelected(account.id)" class="selected-icon">
                    <Check />
                  </el-icon>
                </div>
              </div>
            </div>

            <!-- 目标对象选择 -->
            <div class="section">
              <h4 class="section-title">
                目标{{ getTargetTypeName(taskData.basic.targetType) }} *
              </h4>
              
              <!-- 搜索和筛选 -->
              <div class="target-filters">
                <el-input
                  v-model="targetSearch"
                  placeholder="搜索..."
                  :prefix-icon="Search"
                  clearable
                />
                <el-select v-model="targetFilter" placeholder="筛选">
                  <el-option label="全部" value="all" />
                  <el-option label="最近联系" value="recent" />
                  <el-option label="高意向" value="high_intent" />
                  <el-option label="VIP客户" value="vip" />
                </el-select>
              </div>

              <!-- 目标列表 -->
              <div class="targets-container">
                <el-checkbox-group v-model="taskData.targets.selectedIds">
                  <div class="targets-list">
                    <div
                      v-for="target in filteredTargets"
                      :key="target.id"
                      class="target-item"
                    >
                      <el-checkbox :label="target.id">
                        <div class="target-content">
                          <el-avatar :src="target.avatar" :size="32">
                            {{ target.name.charAt(0) }}
                          </el-avatar>
                          <div class="target-info">
                            <div class="target-name">{{ target.name }}</div>
                            <div class="target-meta">
                              <el-tag
                                v-for="tag in target.tags"
                                :key="tag"
                                size="small"
                                type="info"
                              >
                                {{ tag }}
                              </el-tag>
                            </div>
                          </div>
                        </div>
                      </el-checkbox>
                    </div>
                  </div>
                </el-checkbox-group>
              </div>

              <!-- 选择统计 -->
              <div class="selection-summary">
                已选择 {{ taskData.targets.selectedIds.length }} 个目标
                <el-button
                  v-if="taskData.targets.selectedIds.length > 0"
                  type="text"
                  @click="clearSelection"
                >
                  清空选择
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤3: 设计流程 -->
        <div v-show="currentStep === 2" class="step-content">
          <div class="step-title">
            <h3>⚙️ 设计SOP流程</h3>
            <p>配置自动化执行的步骤和时机</p>
          </div>

          <div class="workflow-designer">
            <!-- 工具栏 -->
            <div class="designer-toolbar">
              <el-button type="primary" :icon="Plus" @click="addStep">
                添加步骤
              </el-button>
              <el-button :icon="View" @click="previewWorkflow">
                预览流程
              </el-button>
              <el-button :icon="Download" @click="exportWorkflow">
                导出配置
              </el-button>
            </div>

            <!-- 时间线设计器 -->
            <div class="timeline-designer">
              <div class="timeline-start">
                <div class="timeline-node start">
                  <el-icon><Notification /></el-icon>
                </div>
                <div class="timeline-label">任务开始</div>
              </div>

              <!-- 执行步骤 -->
              <TransitionGroup name="step" tag="div" class="steps-container">
                <div
                  v-for="(step, index) in taskData.workflow.steps"
                  :key="step.id"
                  class="step-item"
                >
                  <!-- 连接线 -->
                  <div class="timeline-connector">
                    <div class="connector-line"></div>
                    <div class="delay-label">
                      等待 {{ step.delay.value }}{{ step.delay.unit }}
                    </div>
                  </div>

                  <!-- 步骤节点 -->
                  <div class="timeline-node">
                    <span class="step-number">{{ index + 1 }}</span>
                  </div>

                  <!-- 步骤卡片 -->
                  <div class="step-card">
                    <div class="step-header">
                      <div class="step-title">{{ step.name || `步骤 ${index + 1}` }}</div>
                      <div class="step-actions">
                        <el-button
                          type="text"
                          :icon="Edit"
                          @click="editStep(index)"
                        />
                        <el-button
                          type="text"
                          :icon="Delete"
                          @click="deleteStep(index)"
                        />
                      </div>
                    </div>
                    <div class="step-body">
                      <div class="step-detail">
                        <span class="detail-label">⏰ 时间:</span>
                        <span>{{ formatStepTiming(step) }}</span>
                      </div>
                      <div class="step-detail">
                        <span class="detail-label">📝 内容:</span>
                        <span>{{ getStepContentPreview(step) }}</span>
                      </div>
                      <div v-if="step.condition" class="step-detail">
                        <span class="detail-label">🎯 条件:</span>
                        <span>{{ step.condition.description }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </TransitionGroup>

              <!-- 结束节点 -->
              <div class="timeline-end">
                <div class="timeline-connector">
                  <div class="connector-line"></div>
                </div>
                <div class="timeline-node end">
                  <el-icon><Check /></el-icon>
                </div>
                <div class="timeline-label">任务完成</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤4: 预览确认 -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="step-title">
            <h3>👀 预览确认</h3>
            <p>检查任务配置，确认无误后即可创建</p>
          </div>

          <div class="preview-container">
            <TaskPreview :task-data="taskData" />
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="wizard-footer">
        <div class="footer-content">
          <el-button v-if="currentStep > 0" @click="prevStep">
            上一步
          </el-button>
          <div class="spacer"></div>
          <el-button @click="handleCancel">取消</el-button>
          <el-button
            v-if="currentStep < 3"
            type="primary"
            @click="nextStep"
            :disabled="!canProceed"
          >
            下一步
          </el-button>
          <el-button
            v-else
            type="primary"
            @click="handleSubmit"
            :loading="submitting"
          >
            创建任务
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 步骤编辑对话框 -->
    <StepEditDialog
      v-model="stepEditVisible"
      :step="editingStep"
      :step-index="editingStepIndex"
      @save="handleStepSave"
    />
  </div>
</template>

<script>
import { ref, computed, reactive, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import {
  User,
  UserFilled,
  PriceTag,
  Check,
  Search,
  Plus,
  View,
  Download,
  Edit,
  Delete,
  Notification
} from '@element-plus/icons-vue'

import TaskPreview from './TaskPreview.vue'
import StepEditDialog from './StepEditDialog.vue'

export default {
  name: 'SOPTaskWizard',
  components: {
    TaskPreview,
    StepEditDialog,
    User,
    UserFilled,
    PriceTag,
    Check,
    Search,
    Plus,
    View,
    Download,
    Edit,
    Delete,
    Notification
  },

  setup() {
    const store = useStore()
    const router = useRouter()

    // 响应式数据
    const currentStep = ref(0)
    const submitting = ref(false)
    const stepEditVisible = ref(false)
    const editingStep = ref(null)
    const editingStepIndex = ref(-1)
    const targetSearch = ref('')
    const targetFilter = ref('all')

    // 表单引用
    const basicFormRef = ref(null)

    // 任务数据
    const taskData = reactive({
      basic: {
        name: '',
        description: '',
        targetType: 'friend',
        priority: 'normal',
        tags: []
      },
      accounts: {
        selectedIds: []
      },
      targets: {
        selectedIds: []
      },
      workflow: {
        steps: []
      }
    })

    // 预定义标签
    const predefinedTags = [
      '客户跟进',
      '新客破冰',
      '产品介绍',
      '节日问候',
      '活动推广',
      '回访调研'
    ]

    // 表单验证规则
    const basicRules = {
      name: [
        { required: true, message: '请输入任务名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      targetType: [
        { required: true, message: '请选择目标类型', trigger: 'change' }
      ]
    }

    // 计算属性
    const availableAccounts = computed(() => 
      store.getters['devices/onlineDevices']
    )

    const availableTargets = computed(() => {
      const type = taskData.basic.targetType
      switch (type) {
        case 'friend':
          return store.getters['chat/friendsList']
        case 'group':
          return store.getters['chat/groupsList']
        case 'tag':
          return store.getters['chat/tagGroupsList']
        default:
          return []
      }
    })

    const filteredTargets = computed(() => {
      let result = [...availableTargets.value]

      // 搜索过滤
      if (targetSearch.value) {
        const query = targetSearch.value.toLowerCase()
        result = result.filter(target =>
          target.name.toLowerCase().includes(query) ||
          target.tags?.some(tag => tag.toLowerCase().includes(query))
        )
      }

      // 类型过滤
      if (targetFilter.value !== 'all') {
        result = result.filter(target => {
          switch (targetFilter.value) {
            case 'recent':
              return target.lastContactTime && 
                Date.now() - new Date(target.lastContactTime) < 7 * 24 * 60 * 60 * 1000
            case 'high_intent':
              return target.tags?.includes('高意向')
            case 'vip':
              return target.tags?.includes('VIP客户')
            default:
              return true
          }
        })
      }

      return result
    })

    const canProceed = computed(() => {
      switch (currentStep.value) {
        case 0:
          return taskData.basic.name && taskData.basic.targetType
        case 1:
          return taskData.accounts.selectedIds.length > 0 && 
                 taskData.targets.selectedIds.length > 0
        case 2:
          return taskData.workflow.steps.length > 0
        case 3:
          return true
        default:
          return false
      }
    })

    // 方法
    const nextStep = async () => {
      // 验证当前步骤
      if (currentStep.value === 0) {
        const valid = await basicFormRef.value?.validate()
        if (!valid) return
      }

      if (currentStep.value < 3) {
        currentStep.value++
      }
    }

    const prevStep = () => {
      if (currentStep.value > 0) {
        currentStep.value--
      }
    }

    const isAccountSelected = (accountId) => {
      return taskData.accounts.selectedIds.includes(accountId)
    }

    const toggleAccount = (accountId) => {
      const index = taskData.accounts.selectedIds.indexOf(accountId)
      if (index > -1) {
        taskData.accounts.selectedIds.splice(index, 1)
      } else {
        taskData.accounts.selectedIds.push(accountId)
      }
    }

    const clearSelection = () => {
      taskData.targets.selectedIds = []
    }

    const getTargetTypeName = (type) => {
      const names = {
        friend: '好友',
        group: '群组',
        tag: '标签分组'
      }
      return names[type] || '对象'
    }

    const getStatusText = (status) => {
      const statusMap = {
        ONLINE: '在线',
        OFFLINE: '离线',
        AWAITING_RELOGIN: '等待登录'
      }
      return statusMap[status] || status
    }

    const addStep = () => {
      const newStep = {
        id: Date.now().toString(),
        name: '',
        delay: { value: 1, unit: '天' },
        executeTime: '09:00',
        content: { type: 'text', value: '' },
        condition: null
      }
      
      taskData.workflow.steps.push(newStep)
      editStep(taskData.workflow.steps.length - 1)
    }

    const editStep = (index) => {
      editingStepIndex.value = index
      editingStep.value = { ...taskData.workflow.steps[index] }
      stepEditVisible.value = true
    }

    const deleteStep = (index) => {
      taskData.workflow.steps.splice(index, 1)
    }

    const handleStepSave = (stepData) => {
      if (editingStepIndex.value >= 0) {
        taskData.workflow.steps[editingStepIndex.value] = { ...stepData }
      }
      stepEditVisible.value = false
    }

    const formatStepTiming = (step) => {
      return `任务开始后${step.delay.value}${step.delay.unit}的${step.executeTime}执行`
    }

    const getStepContentPreview = (step) => {
      if (!step.content) return '未设置内容'
      
      switch (step.content.type) {
        case 'text':
          return step.content.value || '文本消息'
        case 'material':
          return '物料内容'
        case 'template':
          return '消息模板'
        default:
          return '内容'
      }
    }

    const previewWorkflow = () => {
      // 显示流程预览
      console.log('预览工作流:', taskData.workflow)
    }

    const exportWorkflow = () => {
      // 导出工作流配置
      const config = JSON.stringify(taskData, null, 2)
      const blob = new Blob([config], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${taskData.basic.name || 'SOP任务'}.json`
      a.click()
      URL.revokeObjectURL(url)
    }

    const handleCancel = () => {
      router.go(-1)
    }

    const handleSubmit = async () => {
      try {
        submitting.value = true
        
        await store.dispatch('sop/createTask', taskData)
        
        store.dispatch('notifications/addNotification', {
          type: 'success',
          title: '任务创建成功',
          message: `SOP任务"${taskData.basic.name}"已创建并开始执行`
        })
        
        router.push({ name: 'SOPManagement' })
      } catch (error) {
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '创建失败',
          message: error.message
        })
      } finally {
        submitting.value = false
      }
    }

    // 监听目标类型变化，清空已选择的目标
    watch(() => taskData.basic.targetType, () => {
      taskData.targets.selectedIds = []
    })

    return {
      // 数据
      currentStep,
      submitting,
      stepEditVisible,
      editingStep,
      editingStepIndex,
      targetSearch,
      targetFilter,
      taskData,
      predefinedTags,
      basicRules,
      basicFormRef,
      
      // 计算属性
      availableAccounts,
      filteredTargets,
      canProceed,
      
      // 方法
      nextStep,
      prevStep,
      isAccountSelected,
      toggleAccount,
      clearSelection,
      getTargetTypeName,
      getStatusText,
      addStep,
      editStep,
      deleteStep,
      handleStepSave,
      formatStepTiming,
      getStepContentPreview,
      previewWorkflow,
      exportWorkflow,
      handleCancel,
      handleSubmit
    }
  }
}
</script>

<style lang="scss" scoped>
.sop-task-wizard {
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

.wizard-container {
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.wizard-header {
  padding: var(--space-8) var(--space-6) var(--space-6);
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%);
  border-bottom: 1px solid var(--gray-200);
}

.wizard-content {
  padding: var(--space-8) var(--space-6);
  min-height: 500px;
}

.step-content {
  max-width: 800px;
  margin: 0 auto;
}

.step-title {
  text-align: center;
  margin-bottom: var(--space-8);
  
  h3 {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--gray-900);
    margin-bottom: var(--space-2);
  }
  
  p {
    color: var(--gray-600);
    font-size: var(--text-base);
  }
}

// 基本信息表单
.basic-form {
  :deep(.el-form-item__label) {
    font-weight: 600;
  }
}

// 目标选择
.target-selection {
  .section {
    margin-bottom: var(--space-8);
  }
  
  .section-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--gray-900);
    margin-bottom: var(--space-4);
  }
}

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
}

.account-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  
  &:hover {
    border-color: var(--primary-300);
    box-shadow: var(--shadow-md);
  }
  
  &.selected {
    border-color: var(--primary-500);
    background-color: var(--primary-50);
  }
}

.account-info {
  flex: 1;
}

.account-name {
  font-weight: 600;
  color: var(--gray-900);
  font-size: var(--text-sm);
}

.account-status {
  font-size: var(--text-xs);
  
  &.ONLINE {
    color: var(--success-600);
  }
  
  &.OFFLINE {
    color: var(--gray-500);
  }
}

.selected-icon {
  color: var(--primary-500);
  font-size: var(--text-lg);
}

.target-filters {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.targets-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

.targets-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.target-item {
  :deep(.el-checkbox) {
    width: 100%;
    
    .el-checkbox__label {
      width: 100%;
      padding-left: var(--space-2);
    }
  }
}

.target-content {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: background-color var(--transition-fast);
  
  &:hover {
    background-color: var(--gray-50);
  }
}

.target-info {
  flex: 1;
}

.target-name {
  font-weight: 500;
  color: var(--gray-900);
  margin-bottom: var(--space-1);
}

.target-meta {
  display: flex;
  gap: var(--space-1);
}

.selection-summary {
  margin-top: var(--space-4);
  padding: var(--space-3);
  background-color: var(--gray-50);
  border-radius: var(--radius-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-sm);
  color: var(--gray-600);
}

// 工作流设计器
.workflow-designer {
  .designer-toolbar {
    display: flex;
    gap: var(--space-3);
    margin-bottom: var(--space-6);
    padding: var(--space-4);
    background-color: var(--gray-50);
    border-radius: var(--radius-lg);
  }
}

.timeline-designer {
  position: relative;
  padding: var(--space-4);
}

.timeline-start,
.timeline-end {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-4) 0;
}

.timeline-node {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  box-shadow: var(--shadow-md);
  
  &.start {
    background: linear-gradient(135deg, var(--success-500), var(--success-400));
    color: white;
  }
  
  &.end {
    background: linear-gradient(135deg, var(--primary-500), var(--primary-400));
    color: white;
  }
  
  .step-number {
    font-size: var(--text-sm);
    color: white;
  }
}

.timeline-label {
  font-weight: 600;
  color: var(--gray-700);
}

.steps-container {
  margin: var(--space-6) 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin: var(--space-6) 0;
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: var(--space-2) 0;
  
  .connector-line {
    width: 2px;
    height: 40px;
    background: linear-gradient(to bottom, var(--gray-300), var(--gray-400));
  }
  
  .delay-label {
    margin-top: var(--space-2);
    font-size: var(--text-xs);
    color: var(--gray-500);
    background: white;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    border: 1px solid var(--gray-200);
  }
}

.step-card {
  flex: 1;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
  
  &:hover {
    box-shadow: var(--shadow-md);
  }
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  background-color: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
}

.step-title {
  font-weight: 600;
  color: var(--gray-900);
}

.step-actions {
  display: flex;
  gap: var(--space-1);
}

.step-body {
  padding: var(--space-4);
}

.step-detail {
  display: flex;
  margin-bottom: var(--space-2);
  
  .detail-label {
    min-width: 60px;
    color: var(--gray-600);
    font-weight: 500;
  }
}

// 预览容器
.preview-container {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

// 底部操作栏
.wizard-footer {
  padding: var(--space-6);
  background-color: var(--gray-50);
  border-top: 1px solid var(--gray-200);
}

.footer-content {
  display: flex;
  align-items: center;
  max-width: 800px;
  margin: 0 auto;
}

.spacer {
  flex: 1;
}

// 过渡动画
.step-enter-active,
.step-leave-active {
  transition: all var(--transition-normal);
}

.step-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.step-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

// 响应式适配
@media (max-width: 768px) {
  .sop-task-wizard {
    padding: var(--space-4);
  }
  
  .wizard-content {
    padding: var(--space-4);
  }
  
  .accounts-grid {
    grid-template-columns: 1fr;
  }
  
  .target-filters {
    flex-direction: column;
  }
  
  .step-item {
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .timeline-node {
    align-self: flex-start;
  }
}
</style>

