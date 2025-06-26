<template>
  <div class="role-management">
    <div class="page-header">
      <div class="header-content">
        <h1>角色管理</h1>
        <p>管理系统角色和权限配置</p>
      </div>
      <a-button type="primary" @click="showAddModal = true">
        <template #icon><PlusOutlined /></template>
        添加角色
      </a-button>
    </div>

    <!-- 角色列表 -->
    <div class="role-list">
      <a-row :gutter="[16, 16]">
        <a-col :span="8" v-for="role in roles" :key="role.id">
          <a-card class="role-card" :hoverable="true">
            <div class="role-header">
              <div class="role-info">
                <h3>{{ role.name }}</h3>
                <p>{{ role.description }}</p>
              </div>
              <a-dropdown>
                <a-button type="text" size="small">
                  <template #icon><MoreOutlined /></template>
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="editRole(role)">
                      <EditOutlined /> 编辑
                    </a-menu-item>
                    <a-menu-item @click="viewPermissions(role)">
                      <SafetyOutlined /> 权限配置
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item @click="deleteRole(role.id)" danger>
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
            
            <div class="role-stats">
              <div class="stat-item">
                <UserOutlined />
                <span>{{ role.userCount }}个用户</span>
              </div>
              <div class="stat-item">
                <SafetyOutlined />
                <span>{{ role.permissions.length }}个权限</span>
              </div>
            </div>
            
            <div class="role-permissions">
              <h4>主要权限：</h4>
              <div class="permission-tags">
                <a-tag 
                  v-for="permission in role.permissions.slice(0, 4)" 
                  :key="permission"
                  color="blue"
                >
                  {{ getPermissionLabel(permission) }}
                </a-tag>
                <a-tag v-if="role.permissions.length > 4">
                  +{{ role.permissions.length - 4 }}
                </a-tag>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 添加/编辑角色模态框 -->
    <a-modal
      v-model:open="showAddModal"
      :title="editingRole ? '编辑角色' : '添加角色'"
      width="600px"
      @ok="handleSaveRole"
      @cancel="handleCancelAdd"
    >
      <a-form
        ref="formRef"
        :model="roleForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="角色名称" name="name" :rules="[{ required: true, message: '请输入角色名称' }]">
          <a-input v-model:value="roleForm.name" />
        </a-form-item>
        <a-form-item label="角色描述" name="description" :rules="[{ required: true, message: '请输入角色描述' }]">
          <a-textarea v-model:value="roleForm.description" :rows="3" />
        </a-form-item>
        <a-form-item label="角色状态" name="status">
          <a-radio-group v-model:value="roleForm.status">
            <a-radio value="active">启用</a-radio>
            <a-radio value="inactive">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 权限配置模态框 -->
    <a-modal
      v-model:open="showPermissionModal"
      title="权限配置"
      width="800px"
      @ok="handleSavePermissions"
      @cancel="showPermissionModal = false"
    >
      <div class="permission-config">
        <h3>{{ selectedRole?.name }} - 权限配置</h3>
        <a-tree
          v-model:checkedKeys="checkedPermissions"
          :tree-data="permissionTree"
          checkable
          :default-expand-all="true"
        />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  PlusOutlined, 
  MoreOutlined, 
  EditOutlined, 
  DeleteOutlined,
  SafetyOutlined,
  UserOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
  userCount: number
  status: string
  createTime: string
}

interface PermissionTreeNode {
  title: string
  key: string
  children?: PermissionTreeNode[]
}

// 响应式数据
const roles = ref<Role[]>([])
const showAddModal = ref(false)
const showPermissionModal = ref(false)
const editingRole = ref<Role | null>(null)
const selectedRole = ref<Role | null>(null)
const checkedPermissions = ref<string[]>([])

const roleForm = reactive<Partial<Role>>({
  name: '',
  description: '',
  status: 'active'
})

// 权限树数据
const permissionTree: PermissionTreeNode[] = [
  {
    title: '数据概览',
    key: 'dashboard',
    children: [
      { title: '查看数据概览', key: 'dashboard:view' },
      { title: '导出数据', key: 'dashboard:export' }
    ]
  },
  {
    title: '资源库管理',
    key: 'resources',
    children: [
      { title: '企业库管理', key: 'enterprise:manage' },
      { title: '需求库管理', key: 'demand:manage' },
      { title: '产品库管理', key: 'product:manage' },
      { title: '解决方案管理', key: 'solution:manage' },
      { title: '专家库管理', key: 'expert:manage' }
    ]
  },
  {
    title: '战略洞察',
    key: 'insights',
    children: [
      { title: '产业链概览', key: 'industry:overview' },
      { title: '产业链图谱', key: 'industry:chain' },
      { title: '企业地图', key: 'enterprise:map' }
    ]
  },
  {
    title: '机会引擎',
    key: 'opportunities',
    children: [
      { title: '供需地图', key: 'supply:demand' },
      { title: '智能匹配', key: 'smart:match' }
    ]
  },
  {
    title: '系统管理',
    key: 'admin',
    children: [
      { title: '用户管理', key: 'user:manage' },
      { title: '角色管理', key: 'role:manage' },
      { title: '权限管理', key: 'permission:manage' },
      { title: '系统配置', key: 'system:config' }
    ]
  }
]

// 权限标签映射
const permissionLabels: Record<string, string> = {
  'dashboard:view': '数据概览',
  'dashboard:export': '数据导出',
  'enterprise:manage': '企业管理',
  'demand:manage': '需求管理',
  'product:manage': '产品管理',
  'solution:manage': '解决方案',
  'expert:manage': '专家管理',
  'industry:overview': '产业概览',
  'industry:chain': '产业图谱',
  'enterprise:map': '企业地图',
  'supply:demand': '供需地图',
  'smart:match': '智能匹配',
  'user:manage': '用户管理',
  'role:manage': '角色管理',
  'permission:manage': '权限管理',
  'system:config': '系统配置'
}

// 方法
const getPermissionLabel = (permission: string) => {
  return permissionLabels[permission] || permission
}

const editRole = (role: Role) => {
  editingRole.value = role
  Object.assign(roleForm, role)
  showAddModal.value = true
}

const viewPermissions = (role: Role) => {
  selectedRole.value = role
  checkedPermissions.value = [...role.permissions]
  showPermissionModal.value = true
}

const deleteRole = (id: string) => {
  const index = roles.value.findIndex(r => r.id === id)
  if (index > -1) {
    roles.value.splice(index, 1)
    message.success('角色删除成功')
  }
}

const handleSaveRole = () => {
  if (editingRole.value) {
    // 编辑现有角色
    const index = roles.value.findIndex(r => r.id === editingRole.value!.id)
    if (index > -1) {
      roles.value[index] = { 
        ...roles.value[index], 
        ...roleForm,
        id: editingRole.value.id 
      } as Role
    }
    message.success('角色更新成功')
  } else {
    // 添加新角色
    const newRole: Role = {
      ...roleForm as Role,
      id: Date.now().toString(),
      permissions: [],
      userCount: 0,
      createTime: new Date().toLocaleDateString()
    }
    roles.value.unshift(newRole)
    message.success('角色添加成功')
  }
  
  handleCancelAdd()
}

const handleCancelAdd = () => {
  showAddModal.value = false
  editingRole.value = null
  Object.assign(roleForm, {
    name: '',
    description: '',
    status: 'active'
  })
}

const handleSavePermissions = () => {
  if (selectedRole.value) {
    const index = roles.value.findIndex(r => r.id === selectedRole.value!.id)
    if (index > -1) {
      roles.value[index].permissions = [...checkedPermissions.value]
    }
    message.success('权限配置保存成功')
  }
  showPermissionModal.value = false
}

// 初始化数据
const initData = () => {
  roles.value = [
    {
      id: '1',
      name: '系统管理员',
      description: '拥有系统所有权限，可以管理用户、角色和系统配置',
      permissions: [
        'dashboard:view', 'dashboard:export',
        'enterprise:manage', 'demand:manage', 'product:manage', 'solution:manage', 'expert:manage',
        'industry:overview', 'industry:chain', 'enterprise:map',
        'supply:demand', 'smart:match',
        'user:manage', 'role:manage', 'permission:manage', 'system:config'
      ],
      userCount: 2,
      status: 'active',
      createTime: '2024-01-01'
    },
    {
      id: '2',
      name: '数据分析师',
      description: '可以查看和分析所有数据，使用战略洞察和机会引擎功能',
      permissions: [
        'dashboard:view', 'dashboard:export',
        'enterprise:manage', 'demand:manage', 'product:manage',
        'industry:overview', 'industry:chain', 'enterprise:map',
        'supply:demand', 'smart:match'
      ],
      userCount: 8,
      status: 'active',
      createTime: '2024-01-02'
    },
    {
      id: '3',
      name: '销售专员',
      description: '可以查看企业和需求信息，使用基础的数据查询功能',
      permissions: [
        'dashboard:view',
        'enterprise:manage', 'demand:manage',
        'supply:demand'
      ],
      userCount: 15,
      status: 'active',
      createTime: '2024-01-03'
    },
    {
      id: '4',
      name: '访客',
      description: '只能查看基础的数据概览信息',
      permissions: [
        'dashboard:view'
      ],
      userCount: 5,
      status: 'active',
      createTime: '2024-01-04'
    }
  ]
}

onMounted(() => {
  initData()
})
</script>

<style scoped>
.role-management {
  padding: 24px;
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
}

.header-content p {
  margin: 0;
  color: #666;
}

.role-list {
  margin-bottom: 24px;
}

.role-card {
  height: 100%;
  transition: all 0.3s ease;
}

.role-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.role-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.role-info p {
  margin: 0;
  color: #666;
  font-size: 12px;
}

.role-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.role-permissions h4 {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #333;
}

.permission-tags .ant-tag {
  margin-bottom: 4px;
}

.permission-config h3 {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
</style> 