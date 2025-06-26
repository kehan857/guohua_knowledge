<template>
  <div class="user-management">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">用户管理</h1>
        <p class="page-description">管理系统用户账户、角色权限和访问控制</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="showAddUser">
          <template #icon><plus-outlined /></template>
          新增用户
        </a-button>
      </div>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <div class="filter-row">
        <a-input 
          v-model:value="searchKeyword" 
          placeholder="搜索用户名、姓名或邮箱"
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix><search-outlined /></template>
        </a-input>
        
        <a-select 
          v-model:value="selectedRole" 
          placeholder="选择角色"
          style="width: 150px"
          @change="handleRoleFilter"
        >
          <a-select-option value="">全部角色</a-select-option>
          <a-select-option value="admin">超级管理员</a-select-option>
          <a-select-option value="analyst">数据分析师</a-select-option>
          <a-select-option value="business">业务用户</a-select-option>
          <a-select-option value="viewer">只读观察员</a-select-option>
        </a-select>
        
        <a-select 
          v-model:value="selectedStatus" 
          placeholder="选择状态"
          style="width: 120px"
          @change="handleStatusFilter"
        >
          <a-select-option value="">全部状态</a-select-option>
          <a-select-option value="active">启用</a-select-option>
          <a-select-option value="inactive">禁用</a-select-option>
        </a-select>
        
        <a-button @click="resetFilters">重置</a-button>
        <a-button type="primary" @click="exportUsers">导出用户</a-button>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="user-table">
      <a-table 
        :columns="columns" 
        :data-source="filteredUsers" 
        :pagination="pagination"
        :loading="loading"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'avatar'">
            <a-avatar :size="40">
              {{ record.username.charAt(0).toUpperCase() }}
            </a-avatar>
          </template>
          
          <template v-else-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ getRoleText(record.role) }}
            </a-tag>
          </template>
          
          <template v-else-if="column.key === 'status'">
            <a-badge 
              :status="record.status === 'active' ? 'success' : 'error'" 
              :text="record.status === 'active' ? '启用' : '禁用'" 
            />
          </template>
          
          <template v-else-if="column.key === 'lastLogin'">
            <span v-if="record.lastLogin">{{ formatDateTime(record.lastLogin) }}</span>
            <span v-else class="text-placeholder">从未登录</span>
          </template>
          
          <template v-else-if="column.key === 'actions'">
            <div class="action-buttons">
              <a-button type="link" size="small" @click="editUser(record)">
                编辑
              </a-button>
              <a-button type="link" size="small" @click="viewUserDetail(record)">
                详情
              </a-button>
              <a-dropdown>
                <a-button type="link" size="small">
                  更多 <down-outlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="resetPassword(record)">
                      重置密码
                    </a-menu-item>
                    <a-menu-item @click="toggleUserStatus(record)">
                      {{ record.status === 'active' ? '禁用' : '启用' }}
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="deleteUser(record)">
                      删除用户
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 添加/编辑用户弹窗 -->
    <a-modal
      v-model:open="userModalVisible"
      :title="isEditing ? '编辑用户' : '新增用户'"
      width="600px"
      @ok="handleUserSubmit"
      @cancel="handleUserCancel"
    >
      <a-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户名" name="username">
              <a-input 
                v-model:value="userForm.username" 
                placeholder="请输入用户名"
                :disabled="isEditing"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="真实姓名" name="realName">
              <a-input v-model:value="userForm.realName" placeholder="请输入真实姓名" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="邮箱地址" name="email">
              <a-input v-model:value="userForm.email" placeholder="请输入邮箱地址" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="手机号码" name="phone">
              <a-input v-model:value="userForm.phone" placeholder="请输入手机号码" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用户角色" name="role">
              <a-select v-model:value="userForm.role" placeholder="选择用户角色">
                <a-select-option value="admin">超级管理员</a-select-option>
                <a-select-option value="analyst">数据分析师</a-select-option>
                <a-select-option value="business">业务用户</a-select-option>
                <a-select-option value="viewer">只读观察员</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="部门" name="department">
              <a-input v-model:value="userForm.department" placeholder="请输入部门" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item v-if="!isEditing" label="初始密码" name="password">
          <a-input-password 
            v-model:value="userForm.password" 
            placeholder="请输入初始密码"
          />
        </a-form-item>
        
        <a-form-item label="备注" name="remark">
          <a-textarea 
            v-model:value="userForm.remark" 
            placeholder="用户备注信息"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 用户详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="用户详情"
      width="800px"
      :footer="null"
    >
      <div v-if="selectedUser" class="user-detail">
        <div class="detail-header">
          <a-avatar :size="60">
            {{ selectedUser.username.charAt(0).toUpperCase() }}
          </a-avatar>
          <div class="user-info">
            <h3>{{ selectedUser.realName }}</h3>
            <p>{{ selectedUser.username }} | {{ getRoleText(selectedUser.role) }}</p>
          </div>
        </div>
        
        <a-descriptions title="基本信息" :column="2">
          <a-descriptions-item label="用户名">{{ selectedUser.username }}</a-descriptions-item>
          <a-descriptions-item label="真实姓名">{{ selectedUser.realName }}</a-descriptions-item>
          <a-descriptions-item label="邮箱地址">{{ selectedUser.email }}</a-descriptions-item>
          <a-descriptions-item label="手机号码">{{ selectedUser.phone }}</a-descriptions-item>
          <a-descriptions-item label="部门">{{ selectedUser.department }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDateTime(selectedUser.createdAt) }}</a-descriptions-item>
          <a-descriptions-item label="最后登录">
            <span v-if="selectedUser.lastLogin">{{ formatDateTime(selectedUser.lastLogin) }}</span>
            <span v-else>从未登录</span>
          </a-descriptions-item>
          <a-descriptions-item label="账户状态">
            <a-badge 
              :status="selectedUser.status === 'active' ? 'success' : 'error'" 
              :text="selectedUser.status === 'active' ? '启用' : '禁用'" 
            />
          </a-descriptions-item>
        </a-descriptions>
        
        <a-descriptions title="权限信息" :column="1">
          <a-descriptions-item label="角色权限">
            <div class="role-permissions">
              <a-tag :color="getRoleColor(selectedUser.role)">
                {{ getRoleText(selectedUser.role) }}
              </a-tag>
              <div class="permission-list">
                <span v-for="permission in getRolePermissions(selectedUser.role)" :key="permission">
                  {{ permission }}
                </span>
              </div>
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { TableColumnsType, FormInstance } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  DownOutlined
} from '@ant-design/icons-vue'

interface User {
  id: string
  username: string
  realName: string
  email: string
  phone: string
  role: string
  department: string
  status: 'active' | 'inactive'
  createdAt: string
  lastLogin?: string
  remark?: string
}

// 响应式数据
const loading = ref(false)
const searchKeyword = ref('')
const selectedRole = ref('')
const selectedStatus = ref('')
const userModalVisible = ref(false)
const detailModalVisible = ref(false)
const isEditing = ref(false)
const selectedUser = ref<User | null>(null)
const userFormRef = ref<FormInstance>()

// 用户表单
const userForm = ref({
  username: '',
  realName: '',
  email: '',
  phone: '',
  role: '',
  department: '',
  password: '',
  remark: ''
})

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址' },
    { type: 'email', message: '请输入正确的邮箱格式' }
  ],
  phone: [
    { required: true, message: '请输入手机号码' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码' }
  ],
  role: [
    { required: true, message: '请选择用户角色' }
  ],
  password: [
    { required: true, message: '请输入初始密码' },
    { min: 6, message: '密码长度不能少于6位' }
  ]
}

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

// 模拟用户数据
const users = ref<User[]>([
  {
    id: '1',
    username: 'admin',
    realName: '系统管理员',
    email: 'admin@company.com',
    phone: '13800138000',
    role: 'admin',
    department: '信息技术部',
    status: 'active',
    createdAt: '2024-01-01 10:00:00',
    lastLogin: '2024-06-24 09:30:00',
    remark: '系统超级管理员账户'
  },
  {
    id: '2',
    username: 'analyst01',
    realName: '张数据',
    email: 'zhang@company.com',
    phone: '13800138001',
    role: 'analyst',
    department: '数据分析部',
    status: 'active',
    createdAt: '2024-02-15 14:30:00',
    lastLogin: '2024-06-23 16:45:00'
  },
  {
    id: '3',
    username: 'sales01',
    realName: '李销售',
    email: 'li@company.com',
    phone: '13800138002',
    role: 'business',
    department: '销售部',
    status: 'active',
    createdAt: '2024-03-01 09:15:00',
    lastLogin: '2024-06-24 08:20:00'
  },
  {
    id: '4',
    username: 'viewer01',
    realName: '王观察',
    email: 'wang@company.com',
    phone: '13800138003',
    role: 'viewer',
    department: '战略规划部',
    status: 'inactive',
    createdAt: '2024-04-10 11:20:00'
  }
])

// 表格列配置
const columns: TableColumnsType = [
  {
    title: '头像',
    key: 'avatar',
    width: 80,
    align: 'center'
  },
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    width: 120
  },
  {
    title: '真实姓名',
    dataIndex: 'realName',
    key: 'realName',
    width: 120
  },
  {
    title: '邮箱地址',
    dataIndex: 'email',
    key: 'email',
    width: 200
  },
  {
    title: '角色',
    key: 'role',
    width: 120,
    align: 'center'
  },
  {
    title: '部门',
    dataIndex: 'department',
    key: 'department',
    width: 120
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center'
  },
  {
    title: '最后登录',
    key: 'lastLogin',
    width: 160
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
]

// 计算属性
const filteredUsers = computed(() => {
  let filtered = users.value

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.username.toLowerCase().includes(keyword) ||
      user.realName.toLowerCase().includes(keyword) ||
      user.email.toLowerCase().includes(keyword)
    )
  }

  // 角色筛选
  if (selectedRole.value) {
    filtered = filtered.filter(user => user.role === selectedRole.value)
  }

  // 状态筛选
  if (selectedStatus.value) {
    filtered = filtered.filter(user => user.status === selectedStatus.value)
  }

  return filtered
})

// 方法
const getRoleColor = (role: string) => {
  const colorMap: Record<string, string> = {
    admin: 'red',
    analyst: 'blue',
    business: 'green',
    viewer: 'orange'
  }
  return colorMap[role] || 'default'
}

const getRoleText = (role: string) => {
  const textMap: Record<string, string> = {
    admin: '超级管理员',
    analyst: '数据分析师',
    business: '业务用户',
    viewer: '只读观察员'
  }
  return textMap[role] || role
}

const getRolePermissions = (role: string) => {
  const permissionMap: Record<string, string[]> = {
    admin: ['用户管理', '角色管理', '系统设置', '数据导出', '所有数据访问'],
    analyst: ['数据治理', '高级搜索', '数据导出', '数据标注'],
    business: ['资源库查询', '图谱分析', '需求匹配', '收藏夹管理'],
    viewer: ['仪表板查看', '报告浏览']
  }
  return permissionMap[role] || []
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

const showAddUser = () => {
  isEditing.value = false
  userForm.value = {
    username: '',
    realName: '',
    email: '',
    phone: '',
    role: '',
    department: '',
    password: '',
    remark: ''
  }
  userModalVisible.value = true
}

const editUser = (user: User) => {
  isEditing.value = true
  userForm.value = {
    username: user.username,
    realName: user.realName,
    email: user.email,
    phone: user.phone,
    role: user.role,
    department: user.department,
    password: '',
    remark: user.remark || ''
  }
  selectedUser.value = user
  userModalVisible.value = true
}

const handleUserSubmit = async () => {
  try {
    await userFormRef.value?.validate()
    
    if (isEditing.value) {
      // 更新用户
      const index = users.value.findIndex(u => u.id === selectedUser.value?.id)
      if (index !== -1) {
        users.value[index] = {
          ...users.value[index],
          ...userForm.value
        }
      }
      message.success('用户更新成功')
    } else {
      // 新增用户
      const newUser: User = {
        id: Date.now().toString(),
        ...userForm.value,
        status: 'active',
        createdAt: new Date().toLocaleString('zh-CN')
      }
      users.value.unshift(newUser)
      message.success('用户创建成功')
    }
    
    userModalVisible.value = false
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleUserCancel = () => {
  userModalVisible.value = false
}

const viewUserDetail = (user: User) => {
  selectedUser.value = user
  detailModalVisible.value = true
}

const resetPassword = (user: User) => {
  message.success(`已重置用户 ${user.realName} 的密码`)
}

const toggleUserStatus = (user: User) => {
  user.status = user.status === 'active' ? 'inactive' : 'active'
  message.success(`已${user.status === 'active' ? '启用' : '禁用'}用户 ${user.realName}`)
}

const deleteUser = (user: User) => {
  const index = users.value.findIndex(u => u.id === user.id)
  if (index !== -1) {
    users.value.splice(index, 1)
    message.success(`已删除用户 ${user.realName}`)
  }
}

const handleSearch = () => {
  pagination.value.current = 1
}

const handleRoleFilter = () => {
  pagination.value.current = 1
}

const handleStatusFilter = () => {
  pagination.value.current = 1
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedRole.value = ''
  selectedStatus.value = ''
  pagination.value.current = 1
}

const exportUsers = () => {
  message.success('用户数据导出成功')
}

const handleTableChange = (pag: any) => {
  pagination.value = { ...pagination.value, ...pag }
}

onMounted(() => {
  pagination.value.total = users.value.length
})
</script>

<style scoped lang="less">
.user-management {
  padding: 24px;
  background: var(--light-bg);
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
      color: var(--light-text-primary);
      margin: 0 0 4px 0;
    }
    
    .page-description {
      color: var(--light-text-secondary);
      margin: 0;
    }
  }
}

.filter-toolbar {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  .filter-row {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }
}

.user-table {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  .action-buttons {
    display: flex;
    gap: 4px;
  }
  
  .text-placeholder {
    color: var(--light-text-secondary);
    font-style: italic;
  }
}

.user-detail {
  .detail-header {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    padding: 16px;
    background: #f9f9f9;
    border-radius: 8px;
    
    .user-info {
      margin-left: 16px;
      
      h3 {
        margin: 0 0 4px 0;
        color: var(--light-text-primary);
      }
      
      p {
        margin: 0;
        color: var(--light-text-secondary);
      }
    }
  }
  
  .role-permissions {
    .permission-list {
      margin-top: 8px;
      
      span {
        display: inline-block;
        background: #f0f0f0;
        padding: 2px 8px;
        border-radius: 4px;
        margin-right: 8px;
        margin-bottom: 4px;
        font-size: 12px;
        color: var(--light-text-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-management {
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
}
</style> 