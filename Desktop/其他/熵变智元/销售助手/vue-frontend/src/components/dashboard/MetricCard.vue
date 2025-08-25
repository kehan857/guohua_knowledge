<template>
  <div class="metric-card" @click="handleClick">
    <div class="card-header">
      <h3 class="card-title">{{ metric.title }}</h3>
      <div class="card-icon">{{ metric.icon }}</div>
    </div>

    <div class="card-content">
      <!-- 单一值显示 -->
      <div v-if="typeof metric.value === 'string'" class="card-value">
        {{ metric.value }}
      </div>

      <!-- 复合值显示 -->
      <div v-else-if="typeof metric.value === 'object'" class="card-value">
        <span class="value-primary">{{ metric.value.primary }}</span>
        <span class="value-secondary">{{ metric.value.secondary }}</span>
      </div>

      <!-- 趋势显示 -->
      <div v-if="metric.trend" class="card-trend" :class="trendClass">
        <el-icon class="trend-icon">
          <component :is="trendIcon" />
        </el-icon>
        <span>{{ metric.trend }}</span>
      </div>

      <!-- 进度条显示 -->
      <div v-if="metric.progress" class="card-progress">
        <el-progress
          :percentage="metric.progress.percentage"
          :status="metric.progress.status"
          :show-text="false"
          :stroke-width="8"
        />
      </div>
    </div>

    <div class="card-footer">
      <span class="card-subtitle">{{ metric.subtitle }}</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'

export default {
  name: 'MetricCard',
  components: {
    ArrowUp,
    ArrowDown, 
    Minus
  },
  props: {
    metric: {
      type: Object,
      required: true
    }
  },
  emits: ['click'],

  setup(props, { emit }) {
    // 计算趋势样式
    const trendClass = computed(() => {
      if (!props.metric.trendType) return ''
      return `trend-${props.metric.trendType}`
    })

    // 计算趋势图标
    const trendIcon = computed(() => {
      switch (props.metric.trendType) {
        case 'positive':
          return ArrowUp
        case 'negative':
          return ArrowDown
        case 'neutral':
          return Minus
        default:
          return Minus
      }
    })

    const handleClick = () => {
      emit('click', props.metric)
    }

    return {
      trendClass,
      trendIcon,
      handleClick
    }
  }
}
</script>

<style lang="scss" scoped>
.metric-card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
  cursor: pointer;
  position: relative;
  overflow: hidden;

  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--primary-300);
  }

  &:active {
    transform: translateY(0);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--gray-600);
  margin: 0;
}

.card-icon {
  font-size: var(--text-xl);
  opacity: 0.7;
  transition: opacity var(--transition-fast);
}

.metric-card:hover .card-icon {
  opacity: 1;
}

.card-content {
  margin-bottom: var(--space-3);
}

.card-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-2);
  line-height: 1.2;
}

.value-primary {
  color: var(--primary-600);
  font-weight: 700;
}

.value-secondary {
  color: var(--gray-500);
  font-size: var(--text-lg);
  margin-left: var(--space-2);
  font-weight: 500;
}

.card-trend {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  font-weight: 500;

  &.trend-positive {
    color: var(--success-600);
  }

  &.trend-negative {
    color: var(--error-600);
  }

  &.trend-neutral {
    color: var(--gray-500);
  }

  &.trend-warning {
    color: var(--warning-600);
  }
}

.trend-icon {
  font-size: var(--text-xs);
}

.card-progress {
  margin-top: var(--space-2);
}

.card-footer {
  font-size: var(--text-xs);
  color: var(--gray-500);
}

// 响应式适配
@media (max-width: 768px) {
  .metric-card {
    padding: var(--space-4);
  }

  .card-value {
    font-size: var(--text-xl);
  }

  .value-secondary {
    font-size: var(--text-base);
    display: block;
    margin-left: 0;
    margin-top: var(--space-1);
  }
}

// 加载状态
.metric-card.loading {
  .card-value {
    background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    color: transparent;
    border-radius: var(--radius-md);
  }
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>

