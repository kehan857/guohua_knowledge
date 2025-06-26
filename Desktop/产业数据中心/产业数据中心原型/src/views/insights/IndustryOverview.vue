<template>
  <div class="industry-overview standard-page">
    <div class="page-header">
      <h1 class="h1-title">产业链概览</h1>
      <p class="page-subtitle">选择产业链查看详细图谱结构</p>
    </div>

    <div class="industry-grid">
      <div 
        v-for="industry in industries" 
        :key="industry.id"
        class="industry-card glass-card glow-element"
        @click="viewIndustryChain(industry.id)"
      >
        <div class="card-header">
          <div class="industry-icon">
            <!-- 石油化工图标 -->
            <svg v-if="industry.icon === 'petrochemical-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="petro-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#FF6B35"/>
                  <stop offset="100%" style="stop-color:#F7931E"/>
                </linearGradient>
              </defs>
              <rect x="8" y="12" width="6" height="20" fill="url(#petro-gradient)" rx="2"/>
              <rect x="16" y="8" width="8" height="24" fill="url(#petro-gradient)" rx="2"/>
              <rect x="26" y="10" width="6" height="22" fill="url(#petro-gradient)" rx="2"/>
              <circle cx="20" cy="6" r="3" fill="#FFD700"/>
              <path d="M12,34 Q20,30 28,34" stroke="#00E5FF" stroke-width="2" fill="none"/>
            </svg>
            
            <!-- 大数据图标 -->
            <svg v-else-if="industry.icon === 'bigdata-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="data-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#00E5FF"/>
                  <stop offset="100%" style="stop-color:#1976D2"/>
                </linearGradient>
              </defs>
              <rect x="6" y="8" width="28" height="4" fill="url(#data-gradient)" rx="2"/>
              <rect x="6" y="14" width="28" height="4" fill="url(#data-gradient)" rx="2"/>
              <rect x="6" y="20" width="28" height="4" fill="url(#data-gradient)" rx="2"/>
              <rect x="6" y="26" width="28" height="4" fill="url(#data-gradient)" rx="2"/>
              <circle cx="38" cy="10" r="2" fill="#FFD700"/>
              <circle cx="38" cy="16" r="2" fill="#4CAF50"/>
              <circle cx="38" cy="22" r="2" fill="#FF5722"/>
              <circle cx="38" cy="28" r="2" fill="#9C27B0"/>
            </svg>
            
            <!-- 新能源图标 -->
            <svg v-else-if="industry.icon === 'newenergy-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="energy-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#4CAF50"/>
                  <stop offset="100%" style="stop-color:#2E7D32"/>
                </linearGradient>
              </defs>
              <path d="M20,4 L24,12 L32,10 L26,18 L34,22 L24,20 L20,28 L16,20 L6,22 L14,18 L8,10 L16,12 Z" fill="url(#energy-gradient)"/>
              <circle cx="20" cy="16" r="4" fill="#FFD700"/>
              <path d="M20,32 L18,36 L22,36 Z" fill="#00E5FF"/>
            </svg>
            
            <!-- 半导体图标 -->
            <svg v-else-if="industry.icon === 'semiconductor-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="semi-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#9C27B0"/>
                  <stop offset="100%" style="stop-color:#6A1B9A"/>
                </linearGradient>
              </defs>
              <rect x="8" y="8" width="24" height="24" fill="url(#semi-gradient)" rx="4"/>
              <rect x="12" y="12" width="16" height="16" fill="rgba(255,255,255,0.1)" rx="2"/>
              <rect x="16" y="16" width="8" height="8" fill="#FFD700" rx="1"/>
              <line x1="4" y1="12" x2="8" y2="12" stroke="#00E5FF" stroke-width="2"/>
              <line x1="4" y1="20" x2="8" y2="20" stroke="#00E5FF" stroke-width="2"/>
              <line x1="4" y1="28" x2="8" y2="28" stroke="#00E5FF" stroke-width="2"/>
              <line x1="32" y1="12" x2="36" y2="12" stroke="#00E5FF" stroke-width="2"/>
              <line x1="32" y1="20" x2="36" y2="20" stroke="#00E5FF" stroke-width="2"/>
              <line x1="32" y1="28" x2="36" y2="28" stroke="#00E5FF" stroke-width="2"/>
            </svg>
            
            <!-- 生物技术图标 -->
            <svg v-else-if="industry.icon === 'biotech-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="bio-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#E91E63"/>
                  <stop offset="100%" style="stop-color:#AD1457"/>
                </linearGradient>
              </defs>
              <path d="M20,4 Q26,8 28,16 Q26,24 20,28 Q14,24 12,16 Q14,8 20,4 Z" fill="url(#bio-gradient)"/>
              <circle cx="20" cy="12" r="2" fill="#FFD700"/>
              <circle cx="16" cy="18" r="1.5" fill="#4CAF50"/>
              <circle cx="24" cy="18" r="1.5" fill="#4CAF50"/>
              <circle cx="20" cy="22" r="1.5" fill="#00E5FF"/>
              <path d="M20,28 Q18,32 16,36 M20,28 Q22,32 24,36" stroke="#4CAF50" stroke-width="2" fill="none"/>
            </svg>
            
            <!-- 人工智能图标 -->
            <svg v-else-if="industry.icon === 'ai-icon'" width="40" height="40" viewBox="0 0 40 40" fill="none">
              <defs>
                <linearGradient id="ai-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#FF9800"/>
                  <stop offset="100%" style="stop-color:#F57C00"/>
                </linearGradient>
              </defs>
              <circle cx="20" cy="20" r="12" fill="url(#ai-gradient)"/>
              <circle cx="20" cy="20" r="8" fill="rgba(255,255,255,0.1)"/>
              <circle cx="16" cy="16" r="2" fill="#00E5FF"/>
              <circle cx="24" cy="16" r="2" fill="#00E5FF"/>
              <path d="M16,24 Q20,28 24,24" stroke="#4CAF50" stroke-width="2" fill="none"/>
              <circle cx="8" cy="12" r="1" fill="#FFD700"/>
              <circle cx="32" cy="12" r="1" fill="#FFD700"/>
              <circle cx="8" cy="28" r="1" fill="#FFD700"/>
              <circle cx="32" cy="28" r="1" fill="#FFD700"/>
              <line x1="12" y1="8" x2="16" y2="12" stroke="#FFD700" stroke-width="1"/>
              <line x1="28" y1="8" x2="24" y2="12" stroke="#FFD700" stroke-width="1"/>
            </svg>
          </div>
          <h3 class="industry-name">{{ industry.name }}</h3>
        </div>
        
        <div class="industry-stats">
          <div class="stat-item">
            <div class="stat-value">{{ industry.enterprises.toLocaleString() }}</div>
            <div class="stat-label">企业数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ industry.products.toLocaleString() }}</div>
            <div class="stat-label">产品数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ industry.demands.toLocaleString() }}</div>
            <div class="stat-label">需求数量</div>
          </div>
        </div>

        <div class="industry-preview">
          <div class="preview-item" v-for="segment in industry.segments" :key="segment">
            <span class="segment-name">{{ segment }}</span>
          </div>
        </div>

        <div class="card-footer">
          <a-button type="primary" ghost>
            查看图谱
            <template #icon><fund-view-outlined /></template>
          </a-button>
        </div>
      </div>
    </div>

    <!-- 产业分析总览 -->
    <div class="analysis-section">
      <h2 class="section-title">产业分析总览</h2>
      <div class="analysis-grid">
        <div class="analysis-card glass-card">
          <h4>产业分布</h4>
          <div class="chart-container">
            <svg width="100%" height="160" viewBox="0 0 200 160">
              <defs>
                <linearGradient id="barGradient1" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.8" />
                  <stop offset="100%" style="stop-color:#1976D2;stop-opacity:0.8" />
                </linearGradient>
                <linearGradient id="barGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#FFD700;stop-opacity:0.8" />
                  <stop offset="100%" style="stop-color:#FF8F00;stop-opacity:0.8" />
                </linearGradient>
                <linearGradient id="barGradient3" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:0.8" />
                  <stop offset="100%" style="stop-color:#2E7D32;stop-opacity:0.8" />
                </linearGradient>
              </defs>
              
              <!-- 柱状图 -->
              <rect x="30" y="60" width="25" height="80" fill="url(#barGradient1)" rx="2"/>
              <rect x="70" y="40" width="25" height="100" fill="url(#barGradient2)" rx="2"/>
              <rect x="110" y="80" width="25" height="60" fill="url(#barGradient3)" rx="2"/>
              <rect x="150" y="70" width="25" height="70" fill="url(#barGradient1)" rx="2"/>
              
              <!-- 标签 -->
              <text x="42" y="155" text-anchor="middle" fill="#8B949E" font-size="10">石化</text>
              <text x="82" y="155" text-anchor="middle" fill="#8B949E" font-size="10">数据</text>
              <text x="122" y="155" text-anchor="middle" fill="#8B949E" font-size="10">能源</text>
              <text x="162" y="155" text-anchor="middle" fill="#8B949E" font-size="10">半导体</text>
              
              <!-- 数值 -->
              <text x="42" y="50" text-anchor="middle" fill="#00E5FF" font-size="12" font-weight="bold">45%</text>
              <text x="82" y="30" text-anchor="middle" fill="#FFD700" font-size="12" font-weight="bold">30%</text>
              <text x="122" y="70" text-anchor="middle" fill="#4CAF50" font-size="12" font-weight="bold">15%</text>
              <text x="162" y="60" text-anchor="middle" fill="#00E5FF" font-size="12" font-weight="bold">10%</text>
            </svg>
            <p style="color: #8B949E; font-size: 12px; text-align: center; margin-top: 10px;">各产业链企业占比分析</p>
          </div>
        </div>
        
        <div class="analysis-card glass-card">
          <h4>区域集聚</h4>
          <div class="chart-container">
            <svg width="100%" height="160" viewBox="0 0 200 160">
              <!-- 中国地图简化版 -->
              <path d="M50,40 Q80,20 120,35 Q160,25 180,50 Q175,80 160,110 Q140,130 100,135 Q70,140 45,120 Q30,100 35,70 Q40,50 50,40 Z" 
                    fill="rgba(0, 229, 255, 0.1)" stroke="#00E5FF" stroke-width="2"/>
              
              <!-- 热点区域 -->
              <circle cx="120" cy="80" r="8" fill="#FF5722" opacity="0.8"/>
              <circle cx="90" cy="90" r="6" fill="#FFD700" opacity="0.8"/>
              <circle cx="140" cy="70" r="7" fill="#4CAF50" opacity="0.8"/>
              <circle cx="110" cy="110" r="5" fill="#9C27B0" opacity="0.8"/>
              
              <!-- 标签 -->
              <text x="120" y="100" text-anchor="middle" fill="#C9D1D9" font-size="10">山东</text>
              <text x="90" y="110" text-anchor="middle" fill="#C9D1D9" font-size="10">江苏</text>
              <text x="140" y="55" text-anchor="middle" fill="#C9D1D9" font-size="10">河北</text>
              <text x="110" y="130" text-anchor="middle" fill="#C9D1D9" font-size="10">广东</text>
            </svg>
            <p style="color: #8B949E; font-size: 12px; text-align: center; margin-top: 10px;">产业地理分布热力图</p>
          </div>
        </div>
        
        <div class="analysis-card glass-card">
          <h4>发展趋势</h4>
          <div class="chart-container">
            <svg width="100%" height="160" viewBox="0 0 200 160">
              <defs>
                <linearGradient id="trendGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:0.3" />
                  <stop offset="100%" style="stop-color:#4CAF50;stop-opacity:0.05" />
                </linearGradient>
              </defs>
              
              <!-- 网格 -->
              <defs>
                <pattern id="grid2" width="40" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 30" fill="none" stroke="rgba(139, 148, 158, 0.1)" stroke-width="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid2)" />
              
              <!-- 趋势线 -->
              <polyline points="20,120 60,100 100,80 140,60 180,40" 
                        fill="none" stroke="#4CAF50" stroke-width="3" stroke-linecap="round"/>
              
              <!-- 面积 -->
              <polygon points="20,120 60,100 100,80 140,60 180,40 180,140 20,140" 
                       fill="url(#trendGradient2)"/>
              
              <!-- 数据点 -->
              <circle cx="20" cy="120" r="3" fill="#4CAF50"/>
              <circle cx="60" cy="100" r="3" fill="#4CAF50"/>
              <circle cx="100" cy="80" r="3" fill="#4CAF50"/>
              <circle cx="140" cy="60" r="3" fill="#4CAF50"/>
              <circle cx="180" cy="40" r="3" fill="#FFD700"/>
              
              <!-- 增长箭头 -->
              <path d="M165,50 L175,40 L175,50 L185,40 L175,40 L175,30" 
                    stroke="#4CAF50" stroke-width="2" fill="none"/>
            </svg>
            <p style="color: #8B949E; font-size: 12px; text-align: center; margin-top: 10px;">产业增长趋势分析</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { FundViewOutlined } from '@ant-design/icons-vue'

const router = useRouter()

// 产业链数据
const industries = ref([
  {
    id: 'petrochemical',
    name: '石油化工',
    icon: 'petrochemical-icon',
    enterprises: 12580,
    products: 8965,
    demands: 3245,
    segments: ['上游开采', '中游炼化', '下游化工', '终端应用']
  },
  {
    id: 'bigdata',
    name: '大数据',
    icon: 'bigdata-icon',
    enterprises: 8934,
    products: 12456,
    demands: 5678,
    segments: ['数据采集', '数据处理', '数据分析', '数据应用']
  },
  {
    id: 'newenergy',
    name: '新能源',
    icon: 'newenergy-icon',
    enterprises: 9876,
    products: 6543,
    demands: 4321,
    segments: ['发电设备', '储能技术', '电力传输', '终端消费']
  },
  {
    id: 'semiconductor',
    name: '半导体',
    icon: 'semiconductor-icon',
    enterprises: 5432,
    products: 9876,
    demands: 3456,
    segments: ['设计研发', '制造封测', '材料设备', '应用市场']
  },
  {
    id: 'biotech',
    name: '生物技术',
    icon: 'biotech-icon',
    enterprises: 4567,
    products: 5432,
    demands: 2345,
    segments: ['基础研究', '药物开发', '临床试验', '产业化']
  },
  {
    id: 'ai',
    name: '人工智能',
    icon: 'ai-icon',
    enterprises: 7890,
    products: 11234,
    demands: 4567,
    segments: ['算法框架', '计算芯片', '数据平台', '行业应用']
  }
])

// 查看产业链图谱
const viewIndustryChain = (industryId: string) => {
  router.push(`/insights/industry-chain/${industryId}`)
}
</script>

<style scoped lang="less">
// 产业概览特定样式
.industry-overview {
  .page-header {
    text-align: center;
    margin-bottom: 48px;
    
    .page-subtitle {
      font-size: 16px;
      color: var(--text-secondary);
      margin-top: 8px;
    }
  }
}

.industry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 32px;
  margin-bottom: 64px;
}

.industry-card {
  background: rgba(26, 32, 68, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 16px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
    transition: left 0.8s ease;
  }

  &:hover {
    transform: translateY(-8px);
    border-color: var(--primary-color);
    box-shadow: 0 16px 64px rgba(0, 229, 255, 0.2);

    &::before {
      left: 100%;
    }
  }
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  
  .industry-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;
    font-size: 24px;
    color: white;
  }
  
  .industry-name {
    font-size: 24px;
    font-weight: bold;
    color: var(--text-primary);
  }
}

.industry-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  
  .stat-item {
    text-align: center;
    
    .stat-value {
      font-size: 20px;
      font-weight: bold;
      color: var(--primary-color);
      text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    
    .stat-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 4px;
    }
  }
}

.industry-preview {
  margin-bottom: 24px;
  
  .preview-item {
    display: inline-block;
    margin: 4px 8px 4px 0;
    
    .segment-name {
      background: rgba(0, 229, 255, 0.1);
      color: var(--primary-color);
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      border: 1px solid rgba(0, 229, 255, 0.3);
    }
  }
}

.card-footer {
  text-align: center;
  
  .ant-btn {
    border-color: var(--primary-color);
    color: var(--primary-color);
    
    &:hover {
      background: var(--primary-color);
      color: var(--primary-bg);
    }
  }
}

.analysis-section {
  .section-title {
    font-size: 24px;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 32px;
    text-align: center;
  }
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.analysis-card {
  background: rgba(26, 32, 68, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 12px;
  padding: 24px;
  
  h4 {
    color: var(--text-primary);
    margin-bottom: 16px;
    font-size: 18px;
  }
  
  .chart-container {
    text-align: center;
    padding: 40px 20px;
    
    svg {
      width: 100%;
      height: 160px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .industry-overview {
    padding: 16px;
  }
  
  .industry-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .industry-card {
    padding: 24px;
  }
  
  .industry-stats {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style> 