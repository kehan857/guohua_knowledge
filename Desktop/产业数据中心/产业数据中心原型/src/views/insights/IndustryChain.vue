<template>
  <div class="industry-chain">
    <!-- 顶部工具栏 -->
    <div class="chain-header">
      <div class="header-left">
        <a-button type="text" @click="goBack" class="back-btn">
          <template #icon><arrow-left-outlined /></template>
          返回地图
        </a-button>
        <h1 class="chain-title">石油化工 - 产业链图谱</h1>
      </div>
      <div class="header-right">
        <a-select v-model:value="selectedLevel" style="width: 120px" @change="filterByLevel">
          <a-select-option value="all">全部层级</a-select-option>
          <a-select-option value="1">一级节点</a-select-option>
          <a-select-option value="2">二级节点</a-select-option>
          <a-select-option value="3">三级节点</a-select-option>
        </a-select>
        <a-select v-model:value="selectedSegment" style="width: 120px" @change="filterBySegment">
          <a-select-option value="all">全部环节</a-select-option>
          <a-select-option value="upstream">上游</a-select-option>
          <a-select-option value="midstream">中游</a-select-option>
          <a-select-option value="downstream">下游</a-select-option>
        </a-select>
        <a-button type="primary" ghost @click="resetView">
          重置视图
        </a-button>
        <a-button type="primary" @click="toggleSearch">
          <template #icon><search-outlined /></template>
          搜索
        </a-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="chain-main">
      <!-- 左侧信息面板 -->
      <div class="left-panel">
        <!-- 产业链概览 -->
        <div class="panel-card overview-card">
          <div class="card-header">
            <h3><node-index-outlined /> 产业链概览</h3>
          </div>
          <div class="card-content">
            <div class="overview-stats">
              <div class="stat-item">
                <div class="stat-number">{{ chainData.originalOil.enterpriseCount }}</div>
                <div class="stat-label">原油开采</div>
                <div class="stat-detail">{{ chainData.originalOil.productCount }}个产品</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ chainData.refining.enterpriseCount }}</div>
                <div class="stat-label">炼油加工</div>
                <div class="stat-detail">{{ chainData.refining.productCount }}个产品</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ chainData.chemical.enterpriseCount }}</div>
                <div class="stat-label">石化生产</div>
                <div class="stat-detail">{{ chainData.chemical.productCount }}个产品</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ chainData.downstream.enterpriseCount }}</div>
                <div class="stat-label">化工产品</div>
                <div class="stat-detail">{{ chainData.downstream.productCount }}个产品</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ chainData.retail.enterpriseCount }}</div>
                <div class="stat-label">成品油销售</div>
                <div class="stat-detail">{{ chainData.retail.productCount }}个产品</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 节点类型说明 -->
        <div class="panel-card types-card">
          <div class="card-header">
            <h3><apartment-outlined /> 节点类型</h3>
          </div>
          <div class="card-content">
            <div class="type-item upstream">
              <div class="type-dot"></div>
              <div class="type-info">
                <div class="type-name">上游节点</div>
                <div class="type-desc">原材料和资源开采</div>
              </div>
            </div>
            <div class="type-item midstream">
              <div class="type-dot"></div>
              <div class="type-info">
                <div class="type-name">中游节点</div>
                <div class="type-desc">加工和制造环节</div>
              </div>
            </div>
            <div class="type-item downstream">
              <div class="type-dot"></div>
              <div class="type-info">
                <div class="type-name">下游节点</div>
                <div class="type-desc">终端产品和销售</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="panel-card stats-card">
          <div class="card-header">
            <h3><bar-chart-outlined /> 统计信息</h3>
          </div>
          <div class="card-content">
            <div class="stats-grid">
              <div class="stat-row">
                <span class="stat-label">总节点数</span>
                <span class="stat-value">5</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">总企业数</span>
                <span class="stat-value">6170</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">平均连接数</span>
                <span class="stat-value">3.2</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">总产值</span>
                <span class="stat-value">2.8万亿</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 连接强度说明 -->
        <div class="panel-card connection-card">
          <div class="card-header">
            <h3><share-alt-outlined /> 连接强度</h3>
          </div>
          <div class="card-content">
            <div class="connection-item">
              <div class="connection-line strong"></div>
              <span>强关联 (>70%)</span>
            </div>
            <div class="connection-item">
              <div class="connection-line medium"></div>
              <span>中关联 (30-70%)</span>
            </div>
            <div class="connection-item">
              <div class="connection-line weak"></div>
              <span>弱关联 (<30%)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中心图谱区域 -->
      <div class="center-content">
        <div class="chart-container">
          <div class="chart-placeholder">
            <div class="placeholder-content">
              <div class="placeholder-icon">
                <deployment-unit-outlined />
              </div>
              <h3>石油化工产业链图谱</h3>
              <p>显示从原油开采到终端销售的完整产业链结构，包括企业关系和产品流向</p>
              
              <!-- 模拟节点展示 -->
              <div class="mock-chain">
                <div class="chain-flow">
                  <div class="mock-node upstream" @click="selectNode('originalOil')">
                    <div class="node-name">原油开采</div>
                    <div class="node-stats">680家<br/>450个产品<br/>3200亿产值</div>
                  </div>
                  <div class="flow-arrow">→</div>
                  <div class="mock-node midstream" @click="selectNode('refining')">
                    <div class="node-name">炼油加工</div>
                    <div class="node-stats">1200家<br/>800个产品<br/>4500亿产值</div>
                  </div>
                  <div class="flow-arrow">→</div>
                  <div class="mock-node downstream" @click="selectNode('chemical')">
                    <div class="node-name">石化生产</div>
                    <div class="node-stats">1140家<br/>760个产品<br/>5200亿产值</div>
                  </div>
                </div>
                <div class="chain-branches">
                  <div class="branch">
                    <div class="mock-node small downstream" @click="selectNode('downstream')">
                      <div class="node-name">化工产品</div>
                      <div class="node-stats">850家<br/>1200个产品</div>
                    </div>
                  </div>
                  <div class="branch">
                    <div class="mock-node small downstream" @click="selectNode('retail')">
                      <div class="node-name">成品油销售</div>
                      <div class="node-stats">2300家<br/>180个产品</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 控制面板 -->
        <div class="control-panel">
          <div class="control-group">
            <div class="control-title">缩放控制</div>
            <a-button @click="zoomIn" size="small" class="control-btn" title="放大">
              <template #icon><plus-outlined /></template>
            </a-button>
            <a-button @click="zoomOut" size="small" class="control-btn" title="缩小">
              <template #icon><minus-outlined /></template>
            </a-button>
            <a-button @click="resetZoom" size="small" class="control-btn" title="重置">
              <template #icon><aim-outlined /></template>
            </a-button>
          </div>
          
          <div class="control-group">
            <div class="control-title">布局类型</div>
            <a-tooltip title="树形布局">
              <a-button 
                @click="setLayout('tree')" 
                size="small" 
                class="control-btn"
                :type="layoutType === 'tree' ? 'primary' : 'default'"
              >
                <template #icon><partition-outlined /></template>
              </a-button>
            </a-tooltip>
            <a-tooltip title="力导向布局">
              <a-button 
                @click="setLayout('force')" 
                size="small" 
                class="control-btn"
                :type="layoutType === 'force' ? 'primary' : 'default'"
              >
                <template #icon><deployment-unit-outlined /></template>
              </a-button>
            </a-tooltip>
            <a-tooltip title="圆形布局">
              <a-button 
                @click="setLayout('circle')" 
                size="small" 
                class="control-btn"
                :type="layoutType === 'circle' ? 'primary' : 'default'"
              >
                <template #icon><border-outlined /></template>
              </a-button>
            </a-tooltip>
          </div>
        </div>
      </div>
    </div>

    <!-- 节点详情模态框 -->
    <a-modal
      v-model:open="showNodeModal"
      :title="selectedNodeData?.name || '节点详情'"
      width="600px"
      :footer="null"
      class="node-modal"
    >
      <div v-if="selectedNodeData" class="node-details">
        <div class="detail-header">
          <a-tag :color="getNodeTypeColor(selectedNodeData.type)" size="large">
            {{ getNodeTypeName(selectedNodeData.type) }}
          </a-tag>
          <span class="node-level">{{ selectedNodeData.level }}级节点</span>
        </div>

        <div class="detail-stats">
          <div class="stat-box">
            <div class="stat-number">{{ selectedNodeData.enterpriseCount }}</div>
            <div class="stat-label">企业数量</div>
          </div>
          <div class="stat-box">
            <div class="stat-number">{{ selectedNodeData.productCount }}</div>
            <div class="stat-label">产品数量</div>
          </div>
          <div class="stat-box">
            <div class="stat-number">{{ selectedNodeData.outputValue }}</div>
            <div class="stat-label">年产值</div>
          </div>
        </div>

        <div v-if="selectedNodeData.keyEnterprises?.length" class="key-enterprises">
          <h4>关键企业</h4>
          <div class="enterprise-grid">
            <div 
              v-for="enterprise in selectedNodeData.keyEnterprises" 
              :key="enterprise.id"
              class="enterprise-card"
            >
              <div class="enterprise-name">{{ enterprise.name }}</div>
              <a-tag size="small" :color="getEnterpriseTypeColor(enterprise.type)">
                {{ enterprise.type }}
              </a-tag>
              <div class="enterprise-details">
                <div>市值: {{ enterprise.marketValue || 'N/A' }}</div>
                <div>员工: {{ enterprise.employees || 'N/A' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  PlusOutlined,
  MinusOutlined,
  AimOutlined,
  SearchOutlined,
  PartitionOutlined,
  DeploymentUnitOutlined,
  BorderOutlined,
  NodeIndexOutlined,
  ApartmentOutlined,
  BarChartOutlined,
  ShareAltOutlined
} from '@ant-design/icons-vue'

interface ChainNodeData {
  enterpriseCount: number
  productCount: number
  outputValue: string
  type: 'upstream' | 'midstream' | 'downstream'
  level: number
  name: string
  keyEnterprises?: {
    id: string
    name: string
    type: string
    marketValue?: string
    employees?: string
  }[]
}

const router = useRouter()

// 响应式数据
const selectedLevel = ref('all')
const selectedSegment = ref('all')
const layoutType = ref('tree')
const showNodeModal = ref(false)
const selectedNodeData = ref<ChainNodeData | null>(null)

// 产业链数据
const chainData = reactive({
  originalOil: {
    name: '原油开采',
    type: 'upstream' as const,
    level: 2,
    enterpriseCount: 680,
    productCount: 450,
    outputValue: '3200亿',
    keyEnterprises: [
      { id: 'e1', name: '中国石油', type: '央企', marketValue: '8900亿', employees: '15.2万' },
      { id: 'e2', name: '中国石化', type: '央企', marketValue: '6800亿', employees: '12.8万' },
      { id: 'e3', name: '中国海油', type: '央企', marketValue: '4500亿', employees: '8.9万' }
    ]
  },
  refining: {
    name: '炼油加工',
    type: 'midstream' as const,
    level: 2,
    enterpriseCount: 1200,
    productCount: 800,
    outputValue: '4500亿',
    keyEnterprises: [
      { id: 'e4', name: '恒力炼化', type: '民企', marketValue: '1200亿', employees: '4.2万' },
      { id: 'e5', name: '浙江石化', type: '民企', marketValue: '980亿', employees: '3.8万' },
      { id: 'e6', name: '盛虹炼化', type: '民企', marketValue: '720亿', employees: '2.9万' }
    ]
  },
  chemical: {
    name: '石化生产',
    type: 'midstream' as const,
    level: 2,
    enterpriseCount: 1140,
    productCount: 760,
    outputValue: '5200亿',
    keyEnterprises: [
      { id: 'e7', name: '万华化学', type: '民企', marketValue: '2800亿', employees: '2.8万' },
      { id: 'e8', name: '荣盛石化', type: '民企', marketValue: '1500亿', employees: '3.2万' },
      { id: 'e9', name: '桐昆股份', type: '民企', marketValue: '890亿', employees: '1.9万' }
    ]
  },
  downstream: {
    name: '化工产品',
    type: 'downstream' as const,
    level: 3,
    enterpriseCount: 850,
    productCount: 1200,
    outputValue: '3800亿',
    keyEnterprises: [
      { id: 'e10', name: '巴斯夫(中国)', type: '外企', marketValue: 'N/A', employees: '0.9万' },
      { id: 'e11', name: '陶氏化学', type: '外企', marketValue: 'N/A', employees: '0.7万' }
    ]
  },
  retail: {
    name: '成品油销售',
    type: 'downstream' as const,
    level: 3,
    enterpriseCount: 2300,
    productCount: 180,
    outputValue: '6800亿',
    keyEnterprises: [
      { id: 'e12', name: '中石油销售', type: '央企', marketValue: 'N/A', employees: '8.5万' },
      { id: 'e13', name: '中石化销售', type: '央企', marketValue: 'N/A', employees: '7.2万' }
    ]
  }
})

// 方法
const goBack = () => {
  router.push('/insights/industry-map')
}

const toggleSearch = () => {
  message.info('搜索功能开发中...')
}

const filterByLevel = (value: string) => {
  message.info(`按层级筛选: ${value}`)
}

const filterBySegment = (value: string) => {
  message.info(`按环节筛选: ${value}`)
}

const resetView = () => {
  selectedLevel.value = 'all'
  selectedSegment.value = 'all'
  message.success('视图已重置')
}

const zoomIn = () => {
  message.info('放大图谱')
}

const zoomOut = () => {
  message.info('缩小图谱')
}

const resetZoom = () => {
  message.info('重置缩放')
}

const setLayout = (type: string) => {
  layoutType.value = type
  message.info(`切换到${type}布局`)
}

const selectNode = (nodeKey: keyof typeof chainData) => {
  selectedNodeData.value = chainData[nodeKey]
  showNodeModal.value = true
}

const getNodeTypeColor = (type: string) => {
  const colors = {
    upstream: 'blue',
    midstream: 'orange',
    downstream: 'green'
  }
  return colors[type as keyof typeof colors] || 'default'
}

const getNodeTypeName = (type: string) => {
  const names = {
    upstream: '上游节点',
    midstream: '中游节点',
    downstream: '下游节点'
  }
  return names[type as keyof typeof names] || type
}

const getEnterpriseTypeColor = (type: string) => {
  const colors = {
    央企: 'red',
    民企: 'blue',
    外企: 'green',
    合资: 'orange'
  }
  return colors[type as keyof typeof colors] || 'default'
}

onMounted(() => {
  message.success('产业链图谱加载完成')
})
</script>

<style scoped lang="less">
.industry-chain {
  height: calc(100vh - 64px);
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--component-bg);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .back-btn {
      color: var(--text-primary);
      
      &:hover {
        color: var(--primary-color);
        background: rgba(35, 134, 54, 0.1);
      }
    }

    .chain-title {
      margin: 0;
      color: var(--text-primary);
      font-size: 20px;
      font-weight: 600;
    }
  }

  .header-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.chain-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 320px;
  background: var(--component-bg);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  padding: 20px;
  flex-shrink: 0;

  .panel-card {
    background: var(--component-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    margin-bottom: 16px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .card-header {
      padding: 16px;
      background: rgba(35, 134, 54, 0.05);
      border-bottom: 1px solid var(--border-color);

      h3 {
        margin: 0;
        color: var(--text-primary);
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .card-content {
      padding: 16px;
    }
  }

  .overview-stats {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .stat-item {
      padding: 12px;
      background: var(--bg-secondary);
      border-radius: 8px;
      text-align: center;

      .stat-number {
        font-size: 18px;
        font-weight: bold;
        color: var(--primary-color);
      }

      .stat-label {
        color: var(--text-primary);
        font-weight: 500;
        margin-top: 4px;
      }

      .stat-detail {
        color: var(--text-secondary);
        font-size: 12px;
        margin-top: 2px;
      }
    }
  }

  .type-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;

    .type-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }

    &.upstream .type-dot {
      background: #1890ff;
    }

    &.midstream .type-dot {
      background: #fa8c16;
    }

    &.downstream .type-dot {
      background: #52c41a;
    }

    .type-info {
      .type-name {
        color: var(--text-primary);
        font-weight: 500;
        font-size: 13px;
      }

      .type-desc {
        color: var(--text-secondary);
        font-size: 12px;
      }
    }
  }

  .stats-grid {
    .stat-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border-color-light);

      &:last-child {
        border-bottom: none;
      }

      .stat-label {
        color: var(--text-secondary);
        font-size: 13px;
      }

      .stat-value {
        color: var(--text-primary);
        font-weight: 600;
      }
    }
  }

  .connection-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;

    .connection-line {
      width: 24px;
      height: 3px;
      border-radius: 2px;

      &.strong {
        background: #52c41a;
      }

      &.medium {
        background: #fa8c16;
      }

      &.weak {
        background: #d9d9d9;
      }
    }

    span {
      color: var(--text-secondary);
      font-size: 12px;
    }
  }
}

.center-content {
  flex: 1;
  position: relative;
  overflow: hidden;

  .chart-container {
    width: 100%;
    height: 100%;
    position: relative;

    .chart-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-primary);

      .placeholder-content {
        text-align: center;
        max-width: 900px;
        padding: 40px 20px;

        .placeholder-icon {
          font-size: 64px;
          margin-bottom: 16px;
          color: var(--primary-color);
        }

        h3 {
          color: var(--text-primary);
          margin-bottom: 8px;
          font-size: 24px;
          font-weight: 600;
        }

        p {
          color: var(--text-secondary);
          margin-bottom: 32px;
          font-size: 16px;
          line-height: 1.6;
        }

        .mock-chain {
          .chain-flow {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;

            .flow-arrow {
              font-size: 24px;
              color: var(--primary-color);
              font-weight: bold;
            }
          }

          .chain-branches {
            display: flex;
            justify-content: center;
            gap: 40px;

            .branch {
              display: flex;
              flex-direction: column;
              align-items: center;
            }
          }

          .mock-node {
            background: var(--component-bg);
            border: 2px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 140px;
            text-align: center;

            &:hover {
              border-color: var(--primary-color);
              box-shadow: 0 8px 32px rgba(35, 134, 54, 0.2);
              transform: translateY(-2px);
            }

            &.upstream {
              border-color: #1890ff;
              background: rgba(24, 144, 255, 0.05);
            }

            &.midstream {
              border-color: #fa8c16;
              background: rgba(250, 140, 22, 0.05);
            }

            &.downstream {
              border-color: #52c41a;
              background: rgba(82, 196, 26, 0.05);
            }

            &.small {
              min-width: 120px;
              padding: 12px;
            }

            .node-name {
              color: var(--text-primary);
              font-weight: bold;
              margin-bottom: 8px;
              font-size: 14px;
            }

            .node-stats {
              color: var(--text-secondary);
              font-size: 12px;
              line-height: 1.4;
            }
          }
        }
      }
    }
  }

  .control-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 1000;

    .control-group {
      background: var(--component-bg);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

      .control-title {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 8px;
        text-align: center;
      }

      .control-btn {
        width: 32px;
        height: 32px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 4px;
        background: var(--component-bg);
        border-color: var(--border-color);
        color: var(--text-primary);

        &:last-child {
          margin-bottom: 0;
        }

        &:hover {
          border-color: var(--primary-color);
          color: var(--primary-color);
          background: rgba(35, 134, 54, 0.1);
        }
      }
    }
  }
}

.node-modal {
  .node-details {
    .detail-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;

      .node-level {
        color: var(--text-secondary);
      }
    }

    .detail-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;

      .stat-box {
        text-align: center;
        padding: 16px;
        background: var(--bg-secondary);
        border-radius: 8px;

        .stat-number {
          font-size: 20px;
          font-weight: bold;
          color: var(--primary-color);
          margin-bottom: 4px;
        }

        .stat-label {
          color: var(--text-secondary);
          font-size: 12px;
        }
      }
    }

    .key-enterprises {
      h4 {
        color: var(--text-primary);
        margin-bottom: 16px;
      }

      .enterprise-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;

        .enterprise-card {
          padding: 12px;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          background: var(--component-bg);

          .enterprise-name {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
          }

          .enterprise-details {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 8px;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .left-panel {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .chain-main {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }

  .control-panel {
    position: relative;
    top: auto;
    right: auto;
    margin: 20px;
    
    .control-group {
      display: flex;
      gap: 8px;
      
      .control-btn {
        margin-bottom: 0;
        margin-right: 4px;
      }
    }
  }
}
</style> 