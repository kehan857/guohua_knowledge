<template>
  <div class="enterprise-list list-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="h1-title">企业库</h1>
      <div class="header-actions">
        <a-button type="primary" @click="handleExport">
          <template #icon><download-outlined /></template>
          导出数据
        </a-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <a-form layout="horizontal">
        <a-row :gutter="16" align="bottom">
          <a-col :span="6">
            <a-form-item label="企业名称">
              <a-input
                v-model:value="filters.name"
                placeholder="请输入企业名称"
                allow-clear
                @change="handleSearch"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="产业链">
              <a-select
                v-model:value="filters.industry"
                placeholder="请选择产业链"
                allow-clear
                @change="handleSearch"
              >
                <a-select-option value="petrochemical">石油化工</a-select-option>
                <a-select-option value="bigdata">大数据</a-select-option>
                <a-select-option value="new-energy">新能源</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="省份">
              <a-select
                v-model:value="filters.province"
                placeholder="请选择省份"
                allow-clear
                @change="handleSearch"
              >
                <a-select-option value="guangdong">广东省</a-select-option>
                <a-select-option value="jiangsu">江苏省</a-select-option>
                <a-select-option value="shandong">山东省</a-select-option>
                <a-select-option value="zhejiang">浙江省</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="成立时间">
              <a-range-picker
                v-model:value="filters.establishDate"
                @change="handleSearch"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <div class="filter-actions">
          <a-button @click="handleReset">重置</a-button>
          <a-button type="primary" @click="handleSearch">查询</a-button>
        </div>
      </a-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-section">
      <a-table
        :columns="columns"
        :data-source="tableData"
        :pagination="pagination"
        :loading="loading"
        row-key="id"
        @change="handleTableChange"
      >
        <!-- 企业名称列 -->
        <template #name="{ record }">
          <a-button type="link" @click="handleViewDetail(record.id)">
            {{ record.name }}
          </a-button>
        </template>
        
        <!-- 产业链列 -->
        <template #industry="{ record }">
          <a-tag :color="getIndustryColor(record.industry)">
            {{ getIndustryName(record.industry) }}
          </a-tag>
        </template>
        
        <!-- 规模列 -->
        <template #scale="{ record }">
          <a-tag :color="getScaleColor(record.scale)">
            {{ getScaleName(record.scale) }}
          </a-tag>
        </template>
        
        <!-- 操作列 -->
        <template #action="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="handleViewDetail(record.id)">
              详情
            </a-button>
            <a-button type="link" size="small" @click="handleViewProducts(record.id)">
              产品
            </a-button>
            <a-button type="link" size="small" @click="handleAddToFavorites(record.id)">
              收藏
            </a-button>
          </a-space>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import type { TableColumnType, TableProps } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'

const router = useRouter()

// 筛选条件
const filters = reactive({
  name: '',
  industry: undefined,
  province: undefined,
  establishDate: null as [Dayjs, Dayjs] | null
})

// 表格数据
const tableData = ref([
  {
    id: 1,
    name: '河北宇意科技股份有限公司',
    industry: 'petrochemical',
    province: '河北省',
    city: '石家庄市',
    scale: 'large',
    establishDate: '2010-03-15',
    registeredCapital: '5000万元',
    businessScope: '化工产品生产、销售'
  },
  {
    id: 2,
    name: '江苏华达化工有限公司',
    industry: 'petrochemical',
    province: '江苏省',
    city: '南京市',
    scale: 'medium',
    establishDate: '2015-08-20',
    registeredCapital: '2000万元',
    businessScope: '精细化工、化学原料'
  },
  {
    id: 3,
    name: '广东智联大数据科技有限公司',
    industry: 'bigdata',
    province: '广东省',
    city: '深圳市',
    scale: 'large',
    establishDate: '2018-12-10',
    registeredCapital: '1亿元',
    businessScope: '大数据分析、云计算服务'
  },
  {
    id: 4,
    name: '山东绿能新能源股份有限公司',
    industry: 'new-energy',
    province: '山东省',
    city: '青岛市',
    scale: 'large',
    establishDate: '2012-06-05',
    registeredCapital: '3亿元',
    businessScope: '太阳能、风能设备制造'
  },
  {
    id: 5,
    name: '浙江创新材料科技有限公司',
    industry: 'petrochemical',
    province: '浙江省',
    city: '杭州市',
    scale: 'small',
    establishDate: '2020-01-18',
    registeredCapital: '500万元',
    businessScope: '新材料研发、生产'
  }
])

// 表格列配置
const columns: TableColumnType[] = [
  {
    title: '企业名称',
    dataIndex: 'name',
    key: 'name',
    width: 250,
    slots: { customRender: 'name' }
  },
  {
    title: '产业链',
    dataIndex: 'industry',
    key: 'industry',
    width: 120,
    slots: { customRender: 'industry' }
  },
  {
    title: '所在地区',
    key: 'location',
    width: 150,
    customRender: ({ record }) => `${record.province} ${record.city}`
  },
  {
    title: '企业规模',
    dataIndex: 'scale',
    key: 'scale',
    width: 100,
    slots: { customRender: 'scale' }
  },
  {
    title: '成立时间',
    dataIndex: 'establishDate',
    key: 'establishDate',
    width: 120,
    sorter: true
  },
  {
    title: '注册资本',
    dataIndex: 'registeredCapital',
    key: 'registeredCapital',
    width: 120
  },
  {
    title: '经营范围',
    dataIndex: 'businessScope',
    key: 'businessScope',
    ellipsis: true
  },
  {
    title: '操作',
    key: 'action',
    width: 180,
    fixed: 'right',
    slots: { customRender: 'action' }
  }
]

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 50,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) => 
    `共 ${total} 条记录，显示第 ${range[0]}-${range[1]} 条`
})

const loading = ref(false)

// 工具方法
const getIndustryName = (industry: string) => {
  const map: Record<string, string> = {
    petrochemical: '石油化工',
    bigdata: '大数据',
    'new-energy': '新能源'
  }
  return map[industry] || industry
}

const getIndustryColor = (industry: string) => {
  const map: Record<string, string> = {
    petrochemical: 'blue',
    bigdata: 'green',
    'new-energy': 'orange'
  }
  return map[industry] || 'default'
}

const getScaleName = (scale: string) => {
  const map: Record<string, string> = {
    large: '大型',
    medium: '中型',
    small: '小型'
  }
  return map[scale] || scale
}

const getScaleColor = (scale: string) => {
  const map: Record<string, string> = {
    large: 'red',
    medium: 'orange',
    small: 'blue'
  }
  return map[scale] || 'default'
}

// 事件处理
const handleSearch = () => {
  loading.value = true
  console.log('Search filters:', filters)
  
  // 模拟API调用
  setTimeout(() => {
    loading.value = false
    message.success('查询完成')
  }, 1000)
}

const handleReset = () => {
  filters.name = ''
  filters.industry = undefined
  filters.province = undefined
  filters.establishDate = null
  handleSearch()
}

const handleTableChange: TableProps['onChange'] = (pag, sorter) => {
  if (pag) {
    pagination.current = pag.current || 1
    pagination.pageSize = pag.pageSize || 10
  }
  console.log('Table change:', { pagination: pag, sorter })
  handleSearch()
}

const handleViewDetail = (id: number) => {
  router.push(`/resources/enterprises/${id}`)
}

const handleViewProducts = (id: number) => {
  router.push(`/resources/products?enterpriseId=${id}`)
}

const handleAddToFavorites = (id: number) => {
  message.success('已添加到收藏夹')
}

const handleExport = () => {
  message.info('正在导出数据...')
  // 实际会调用导出API
}

onMounted(() => {
  handleSearch()
})
</script>

<style lang="less" scoped>
// 企业列表特定样式
.enterprise-list {
  // 表格特定样式覆盖
  .table-section {
    :deep(.ant-table) {
      .ant-table-thead > tr > th {
        background-color: var(--component-bg);
        font-weight: 600;
      }
    }
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .enterprise-list .filter-section :deep(.ant-col) {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .enterprise-list {
    .filter-section :deep(.ant-col) {
      span: 24 !important;
    }
    
    .table-section :deep(.ant-table .ant-table-container) {
      overflow-x: auto;
    }
  }
}
</style> 