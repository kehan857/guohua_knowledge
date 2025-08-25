<template>
  <div class="cost-ranking-list">
    <div class="list-header">
      <h4>成本排行榜</h4>
      <el-button size="small" @click="refreshData">
        <i class="el-icon-refresh"></i>
        刷新
      </el-button>
    </div>
    <div class="list-content">
      <div 
        v-for="(item, index) in rankingData" 
        :key="item.id"
        class="ranking-item"
      >
        <div class="ranking-number" :class="getRankClass(index + 1)">
          {{ index + 1 }}
        </div>
        <div class="item-info">
          <div class="item-name">{{ item.name }}</div>
          <div class="item-desc">{{ item.description }}</div>
        </div>
        <div class="item-cost">
          <div class="cost-amount">¥{{ item.cost.toFixed(2) }}</div>
          <div class="cost-trend" :class="item.trend">
            <i :class="getTrendIcon(item.trend)"></i>
            {{ item.changePercent }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'CostRankingList',
  setup() {
    const rankingData = ref([
      {
        id: 1,
        name: 'GPT-4 API调用',
        description: 'AI对话生成',
        cost: 1250.50,
        trend: 'up',
        changePercent: 12.5
      },
      {
        id: 2,
        name: 'Claude API调用',
        description: '文档分析处理',
        cost: 890.30,
        trend: 'down',
        changePercent: -5.2
      },
      {
        id: 3,
        name: '图片生成',
        description: '营销素材制作',
        cost: 456.80,
        trend: 'up',
        changePercent: 8.7
      }
    ])
    
    const getRankClass = (rank) => {
      if (rank === 1) return 'rank-1'
      if (rank === 2) return 'rank-2'
      if (rank === 3) return 'rank-3'
      return 'rank-other'
    }
    
    const getTrendIcon = (trend) => {
      return trend === 'up' ? 'el-icon-top' : 'el-icon-bottom'
    }
    
    const refreshData = () => {
      // 刷新数据逻辑
    }
    
    return {
      rankingData,
      getRankClass,
      getTrendIcon,
      refreshData
    }
  }
}
</script>

<style lang="scss" scoped>
.cost-ranking-list {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  
  h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
  }
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-color);
  
  &:last-child {
    border-bottom: none;
  }
}

.ranking-number {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 1rem;
  
  &.rank-1 {
    background: #ffd700;
    color: #000;
  }
  
  &.rank-2 {
    background: #c0c0c0;
    color: #000;
  }
  
  &.rank-3 {
    background: #cd7f32;
    color: #fff;
  }
  
  &.rank-other {
    background: var(--bg-hover);
    color: var(--text-secondary);
  }
}

.item-info {
  flex: 1;
  margin-right: 1rem;
}

.item-name {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.item-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.item-cost {
  text-align: right;
}

.cost-amount {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.25rem;
}

.cost-trend {
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  
  &.up {
    color: var(--success-color);
  }
  
  &.down {
    color: var(--danger-color);
  }
}
</style>
