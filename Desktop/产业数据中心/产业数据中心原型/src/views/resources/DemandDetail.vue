<template>
  <div class="demand-detail">
    <!-- 需求基本信息头部 -->
    <div class="demand-header">
      <div class="header-left">
        <a-button type="text" @click="goBack" class="back-btn">
          <template #icon><arrow-left-outlined /></template>
          返回需求列表
        </a-button>
        <div class="demand-basic">
          <h1 class="demand-title">{{ demandInfo.title }}</h1>
          <div class="demand-meta">
            <a-tag :color="getStatusColor(demandInfo.status)">{{ getStatusText(demandInfo.status) }}</a-tag>
            <span class="meta-item">{{ demandInfo.category }}</span>
            <span class="meta-item">{{ demandInfo.location }}</span>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <div class="demand-stats">
          <div class="stat-item">
            <div class="stat-value">{{ demandInfo.budget }}</div>
            <div class="stat-label">预算金额</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ demandInfo.deadline }}</div>
            <div class="stat-label">截止时间</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="detail-content">
      <div class="content-grid">
        <!-- 左侧：需求详情 -->
        <div class="demand-info">
          <div class="info-section">
            <h3>基础信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="label">需求编号：</span>
                <span class="value">{{ demandInfo.id }}</span>
              </div>
              <div class="info-item">
                <span class="label">招标单位：</span>
                <span class="value publisher" @click="viewPublisher">{{ demandInfo.publisher }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系人：</span>
                <span class="value">{{ demandInfo.contact }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系电话：</span>
                <span class="value">{{ demandInfo.phone }}</span>
              </div>
              <div class="info-item">
                <span class="label">发布时间：</span>
                <span class="value">{{ demandInfo.publishTime }}</span>
              </div>
              <div class="info-item">
                <span class="label">项目地点：</span>
                <span class="value">{{ demandInfo.projectLocation }}</span>
              </div>
            </div>
          </div>

          <div class="info-section">
            <h3>项目描述</h3>
            <div class="project-description">
              {{ demandInfo.description }}
            </div>
          </div>

          <div class="info-section">
            <h3>技术要求</h3>
            <div class="technical-requirements">
              <ul>
                <li v-for="requirement in demandInfo.requirements" :key="requirement">
                  {{ requirement }}
                </li>
              </ul>
            </div>
          </div>

          <div class="info-section">
            <h3>资质要求</h3>
            <div class="qualification-requirements">
              <ul>
                <li v-for="qualification in demandInfo.qualifications" :key="qualification">
                  {{ qualification }}
                </li>
              </ul>
            </div>
          </div>

          <div class="info-section">
            <h3>标签</h3>
            <div class="demand-tags">
              <a-tag v-for="tag in demandInfo.tags" :key="tag" color="blue">
                {{ tag }}
              </a-tag>
            </div>
          </div>
        </div>

        <!-- 右侧：智能匹配分析 -->
        <div class="smart-matching">
          <div class="matching-header">
            <h3>🤖 智能匹配分析</h3>
            <a-button type="text" size="small" @click="refreshMatching">
              <template #icon><reload-outlined /></template>
              重新分析
            </a-button>
          </div>

          <!-- 内部解决方案推荐 -->
          <div class="matching-section">
            <h4>📦 内部解决方案推荐</h4>
            <div class="solution-recommendations">
              <div 
                v-for="solution in recommendedSolutions" 
                :key="solution.id"
                class="solution-item"
                @click="viewSolution(solution.id)"
              >
                <div class="solution-header">
                  <div class="solution-name">{{ solution.name }}</div>
                  <div class="match-score">
                    <div class="score-circle" :style="{ background: getScoreColor(solution.matchScore) }">
                      {{ solution.matchScore }}%
                    </div>
                  </div>
                </div>
                <div class="solution-description">{{ solution.description }}</div>
                <div class="match-reasons">
                  <div class="reason-title">匹配原因：</div>
                  <ul>
                    <li v-for="reason in solution.matchReasons" :key="reason">{{ reason }}</li>
                  </ul>
                </div>
                <div class="solution-footer">
                  <a-button type="primary" size="small">查看详情</a-button>
                  <a-button type="default" size="small" @click.stop="contactSales">联系销售</a-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 潜在竞争对手分析 -->
          <div class="matching-section">
            <h4>⚔️ 潜在竞争对手分析</h4>
            <div class="competitors-analysis">
              <div 
                v-for="competitor in competitors" 
                :key="competitor.id"
                class="competitor-item"
                @click="viewCompetitor(competitor.id)"
              >
                <div class="competitor-header">
                  <div class="competitor-name">{{ competitor.name }}</div>
                  <div class="threat-level" :class="competitor.threatLevel">
                    {{ getThreatText(competitor.threatLevel) }}
                  </div>
                </div>
                <div class="competitor-info">
                  <div class="info-row">
                    <span class="label">业务领域：</span>
                    <span class="value">{{ competitor.businessArea }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">历史合作：</span>
                    <span class="value">{{ competitor.pastProjects }}个项目</span>
                  </div>
                  <div class="info-row">
                    <span class="label">优势分析：</span>
                    <span class="value">{{ competitor.advantages }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 招标单位关系网 -->
          <div class="matching-section">
            <h4>🏢 招标单位关系网</h4>
            <div class="relationship-network">
              <div class="network-info">
                <div class="publisher-profile">
                  <h5>{{ demandInfo.publisher }}</h5>
                  <div class="profile-stats">
                    <div class="stat">
                      <span class="stat-value">{{ publisherProfile.totalProjects }}</span>
                      <span class="stat-label">历史项目</span>
                    </div>
                    <div class="stat">
                      <span class="stat-value">{{ publisherProfile.averageBudget }}</span>
                      <span class="stat-label">平均预算</span>
                    </div>
                    <div class="stat">
                      <span class="stat-value">{{ publisherProfile.preferredVendors }}</span>
                      <span class="stat-label">常用供应商</span>
                    </div>
                  </div>
                </div>

                <div class="key-relationships">
                  <h6>核心合作伙伴</h6>
                  <div class="partner-list">
                    <a-tag 
                      v-for="partner in publisherProfile.keyPartners" 
                      :key="partner"
                      @click="viewPartner(partner)"
                      style="cursor: pointer; margin-bottom: 8px;"
                    >
                      {{ partner }}
                    </a-tag>
                  </div>
                </div>

                <div class="procurement-patterns">
                  <h6>采购偏好</h6>
                  <ul>
                    <li v-for="pattern in publisherProfile.procurementPatterns" :key="pattern">
                      {{ pattern }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- 策略建议 -->
          <div class="matching-section">
            <h4>💡 策略建议</h4>
            <div class="strategy-suggestions">
              <div 
                v-for="suggestion in strategySuggestions" 
                :key="suggestion.type"
                class="suggestion-item"
                :class="suggestion.type"
              >
                <div class="suggestion-icon">{{ suggestion.icon }}</div>
                <div class="suggestion-content">
                  <div class="suggestion-title">{{ suggestion.title }}</div>
                  <div class="suggestion-description">{{ suggestion.description }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeftOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'

interface DemandInfo {
  id: string
  title: string
  publisher: string
  category: string
  location: string
  status: string
  budget: string
  deadline: string
  contact: string
  phone: string
  publishTime: string
  projectLocation: string
  description: string
  requirements: string[]
  qualifications: string[]
  tags: string[]
}

const router = useRouter()
const route = useRoute()

// 模拟需求详情数据
const demandInfo = ref<DemandInfo>({
  id: route.params.id as string || 'REQ-2024-001',
  title: '化工设备维护保养服务招标',
  publisher: '中石化胜利油田',
  category: '维修保养',
  location: '山东省东营市',
  status: 'active',
  budget: '500万元',
  deadline: '2024-07-15',
  contact: '李工程师',
  phone: '0546-8888888',
  publishTime: '2024-06-01',
  projectLocation: '山东省东营市胜利油田',
  description: '本项目旨在为胜利油田各生产装置提供全面的设备维护保养服务，包括定期检修、故障维修、备件更换等。要求服务商具备丰富的石油化工设备维护经验，能够确保设备安全稳定运行。',
  requirements: [
    '具备石油化工设备维护专业资质',
    '拥有不少于50人的专业技术团队',
    '具备24小时应急响应能力',
    '提供设备状态监测和预测性维护服务',
    '建立完善的备件供应体系'
  ],
  qualifications: [
    '具有设备维修服务相关资质证书',
    '通过ISO9001质量管理体系认证',
    '具有安全生产许可证',
    '近3年内无重大安全事故记录',
    '具有类似项目经验不少于5个'
  ],
  tags: ['化工设备', '维护保养', '胜利油田', '石油化工', '设备检修']
})

// 推荐解决方案
const recommendedSolutions = ref([
  {
    id: '1',
    name: '智能化设备维护管理系统',
    description: '基于物联网和AI技术的设备预测性维护解决方案',
    matchScore: 95,
    matchReasons: [
      '完全符合石油化工设备维护需求',
      '具备24小时监控和应急响应能力',
      '拥有丰富的胜利油田项目经验'
    ]
  },
  {
    id: '2',
    name: '专业化工设备保养服务',
    description: '专门针对化工企业的设备保养和维修服务',
    matchScore: 87,
    matchReasons: [
      '专业化工设备维护团队',
      '完善的备件供应链管理',
      '符合安全生产标准'
    ]
  }
])

// 竞争对手分析
const competitors = ref([
  {
    id: '1',
    name: '中石化工程建设有限公司',
    businessArea: '石油化工设备维护',
    pastProjects: 15,
    advantages: '央企背景，技术实力强',
    threatLevel: 'high'
  },
  {
    id: '2',
    name: '海化集团维修服务公司',
    businessArea: '化工设备维修保养',
    pastProjects: 8,
    advantages: '本地企业，响应速度快',
    threatLevel: 'medium'
  },
  {
    id: '3',
    name: '山东化工设备服务有限公司',
    businessArea: '设备维护保养',
    pastProjects: 12,
    advantages: '价格优势，地理位置佳',
    threatLevel: 'medium'
  }
])

// 招标单位画像
const publisherProfile = ref({
  totalProjects: 45,
  averageBudget: '350万元',
  preferredVendors: 8,
  keyPartners: ['中石化工程', '胜利石油', '山东海化', '齐鲁石化'],
  procurementPatterns: [
    '偏好选择有央企背景的供应商',
    '注重安全生产和技术实力',
    '项目周期通常为1-2年',
    '倾向于长期合作关系'
  ]
})

// 策略建议
const strategySuggestions = ref([
  {
    type: 'strength',
    icon: '💪',
    title: '突出技术优势',
    description: '重点展示我们在化工设备智能维护方面的技术创新和成功案例'
  },
  {
    type: 'partnership',
    icon: '🤝',
    title: '寻求战略合作',
    description: '可考虑与央企合作伙伴联合投标，增强竞争优势'
  },
  {
    type: 'pricing',
    icon: '💰',
    title: '价格策略建议',
    description: '基于预算分析，建议报价区间在450-480万元之间'
  },
  {
    type: 'timing',
    icon: '⏰',
    title: '时间节点把握',
    description: '距离截止时间还有30天，建议尽快准备投标文件'
  }
])

// 方法
const goBack = () => {
  router.go(-1)
}

const viewPublisher = () => {
  router.push('/resources/enterprises/publisher-id')
}

const refreshMatching = () => {
  console.log('重新分析匹配度')
}

const viewSolution = (solutionId: string) => {
  router.push(`/resources/solutions/${solutionId}`)
}

const contactSales = () => {
  console.log('联系销售团队')
}

const viewCompetitor = (competitorId: string) => {
  router.push(`/resources/enterprises/${competitorId}`)
}

const viewPartner = (partnerName: string) => {
  console.log('查看合作伙伴:', partnerName)
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    active: 'green',
    pending: 'orange',
    closed: 'gray'
  }
  return colorMap[status] || 'default'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    active: '进行中',
    pending: '待开始',
    closed: '已结束'
  }
  return statusMap[status] || status
}

const getScoreColor = (score: number) => {
  if (score >= 90) return 'linear-gradient(135deg, #52c41a, #73d13d)'
  if (score >= 80) return 'linear-gradient(135deg, #faad14, #ffc53d)'
  if (score >= 70) return 'linear-gradient(135deg, #1890ff, #40a9ff)'
  return 'linear-gradient(135deg, #d9d9d9, #f0f0f0)'
}

const getThreatText = (level: string) => {
  const threatMap: Record<string, string> = {
    high: '高威胁',
    medium: '中威胁',
    low: '低威胁'
  }
  return threatMap[level] || level
}
</script>

<style scoped lang="less">
.demand-detail {
  background: var(--light-bg);
  min-height: 100vh;
}

.demand-header {
  background: #fff;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .header-left {
    display: flex;
    align-items: center;
    
    .back-btn {
      margin-right: 16px;
      color: var(--light-primary);
    }
    
    .demand-basic {
      .demand-title {
        font-size: 24px;
        font-weight: bold;
        color: var(--light-text-primary);
        margin: 0 0 8px 0;
      }
      
      .demand-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .meta-item {
          color: var(--light-text-secondary);
          font-size: 14px;
        }
      }
    }
  }
  
  .header-right {
    .demand-stats {
      display: flex;
      gap: 24px;
      
      .stat-item {
        text-align: center;
        
        .stat-value {
          font-size: 18px;
          font-weight: bold;
          color: var(--light-primary);
        }
        
        .stat-label {
          font-size: 12px;
          color: var(--light-text-secondary);
          margin-top: 4px;
        }
      }
    }
  }
}

.detail-content {
  padding: 24px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

// 需求信息样式
.demand-info {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  .info-section {
    margin-bottom: 32px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    h3 {
      color: var(--light-text-primary);
      margin-bottom: 16px;
      font-size: 16px;
      border-bottom: 1px solid #e4e7ed;
      padding-bottom: 8px;
    }
    
    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      .info-item {
        display: flex;
        
        .label {
          width: 90px;
          color: var(--light-text-secondary);
          font-size: 14px;
        }
        
        .value {
          color: var(--light-text-primary);
          font-size: 14px;
          
          &.publisher {
            color: var(--light-primary);
            cursor: pointer;
            
            &:hover {
              text-decoration: underline;
            }
          }
        }
      }
    }
    
    .project-description {
      color: var(--light-text-primary);
      line-height: 1.6;
      font-size: 14px;
    }
    
    .technical-requirements,
    .qualification-requirements {
      ul {
        padding-left: 20px;
        
        li {
          color: var(--light-text-primary);
          line-height: 1.6;
          margin-bottom: 8px;
        }
      }
    }
    
    .demand-tags {
      .ant-tag {
        margin-bottom: 8px;
      }
    }
  }
}

// 智能匹配样式
.smart-matching {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  .matching-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h3 {
      color: var(--light-text-primary);
      margin: 0;
      font-size: 18px;
    }
  }
  
  .matching-section {
    margin-bottom: 32px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    h4 {
      color: var(--light-text-primary);
      margin-bottom: 16px;
      font-size: 16px;
    }
  }
}

// 解决方案推荐样式
.solution-recommendations {
  .solution-item {
    background: #f9f9f9;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--light-primary);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .solution-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      .solution-name {
        color: var(--light-text-primary);
        font-weight: 500;
        font-size: 16px;
      }
      
      .match-score {
        .score-circle {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 12px;
        }
      }
    }
    
    .solution-description {
      color: var(--light-text-secondary);
      margin-bottom: 12px;
      line-height: 1.5;
    }
    
    .match-reasons {
      margin-bottom: 16px;
      
      .reason-title {
        color: var(--light-text-primary);
        font-weight: 500;
        margin-bottom: 8px;
      }
      
      ul {
        padding-left: 16px;
        
        li {
          color: var(--light-text-secondary);
          font-size: 12px;
          line-height: 1.4;
          margin-bottom: 4px;
        }
      }
    }
    
    .solution-footer {
      display: flex;
      gap: 8px;
    }
  }
}

// 竞争对手分析样式
.competitors-analysis {
  .competitor-item {
    background: #f9f9f9;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--light-primary);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .competitor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      .competitor-name {
        color: var(--light-text-primary);
        font-weight: 500;
      }
      
      .threat-level {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        
        &.high {
          background: #fff2f0;
          color: #ff4d4f;
        }
        
        &.medium {
          background: #fff7e6;
          color: #fa8c16;
        }
        
        &.low {
          background: #f6ffed;
          color: #52c41a;
        }
      }
    }
    
    .competitor-info {
      .info-row {
        display: flex;
        margin-bottom: 4px;
        font-size: 14px;
        
        .label {
          width: 80px;
          color: var(--light-text-secondary);
        }
        
        .value {
          color: var(--light-text-primary);
        }
      }
    }
  }
}

// 关系网分析样式
.relationship-network {
  .network-info {
    .publisher-profile {
      background: #f9f9f9;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      
      h5 {
        color: var(--light-text-primary);
        margin-bottom: 12px;
      }
      
      .profile-stats {
        display: flex;
        justify-content: space-between;
        
        .stat {
          text-align: center;
          
          .stat-value {
            display: block;
            font-size: 16px;
            font-weight: bold;
            color: var(--light-primary);
          }
          
          .stat-label {
            font-size: 12px;
            color: var(--light-text-secondary);
          }
        }
      }
    }
    
    .key-relationships,
    .procurement-patterns {
      margin-bottom: 16px;
      
      h6 {
        color: var(--light-text-primary);
        margin-bottom: 8px;
        font-size: 14px;
      }
      
      .partner-list {
        .ant-tag {
          margin-right: 8px;
          margin-bottom: 8px;
        }
      }
      
      ul {
        padding-left: 16px;
        
        li {
          color: var(--light-text-secondary);
          font-size: 12px;
          line-height: 1.4;
          margin-bottom: 4px;
        }
      }
    }
  }
}

// 策略建议样式
.strategy-suggestions {
  .suggestion-item {
    display: flex;
    align-items: flex-start;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
    
    &.strength {
      background: #f6ffed;
      border-left: 4px solid #52c41a;
    }
    
    &.partnership {
      background: #f0f9ff;
      border-left: 4px solid #1890ff;
    }
    
    &.pricing {
      background: #fff7e6;
      border-left: 4px solid #fa8c16;
    }
    
    &.timing {
      background: #fff2f0;
      border-left: 4px solid #ff4d4f;
    }
    
    .suggestion-icon {
      font-size: 20px;
      margin-right: 12px;
      margin-top: 2px;
    }
    
    .suggestion-content {
      .suggestion-title {
        color: var(--light-text-primary);
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .suggestion-description {
        color: var(--light-text-secondary);
        font-size: 12px;
        line-height: 1.4;
      }
    }
  }
}

// 响应式设计
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .demand-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .demand-info .info-section .info-grid {
    grid-template-columns: 1fr;
  }
}
</style> 