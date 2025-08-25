<template>
  <div class="sop-management">
    <div class="page-header">
      <h2>SOP管理</h2>
      <el-button type="primary" @click="createSOP">
        <i class="el-icon-plus"></i>
        新建SOP
      </el-button>
    </div>
    
    <div class="sop-content">
      <el-table :data="sopList" style="width: 100%">
        <el-table-column prop="name" label="SOP名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editSOP(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteSOP(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'SOPManagement',
  setup() {
    const sopList = ref([
      {
        id: 1,
        name: '客户咨询处理流程',
        description: '处理客户咨询的标准操作流程',
        status: 'active',
        createdAt: '2024-01-15'
      },
      {
        id: 2,
        name: '产品介绍SOP',
        description: '产品介绍的标准话术和流程',
        status: 'draft',
        createdAt: '2024-01-10'
      }
    ])
    
    const getStatusType = (status) => {
      const types = {
        active: 'success',
        draft: 'warning',
        inactive: 'info'
      }
      return types[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const texts = {
        active: '启用',
        draft: '草稿',
        inactive: '停用'
      }
      return texts[status] || '未知'
    }
    
    const createSOP = () => {
      // 创建SOP逻辑
    }
    
    const editSOP = (sop) => {
      // 编辑SOP逻辑
    }
    
    const deleteSOP = (sop) => {
      // 删除SOP逻辑
    }
    
    return {
      sopList,
      getStatusType,
      getStatusText,
      createSOP,
      editSOP,
      deleteSOP
    }
  }
}
</script>

<style lang="scss" scoped>
.sop-management {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  h2 {
    margin: 0;
    color: var(--text-color);
  }
}

.sop-content {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}
</style>
