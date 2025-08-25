<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">{{ title }}</h3>

      <!-- 控制按钮组 -->
      <div v-if="controls.length" class="chart-controls">
        <el-button-group>
          <el-button
            v-for="control in controls"
            :key="control.value"
            :type="activeControl === control.value ? 'primary' : 'default'"
            size="small"
            @click="handleControlChange(control.value)"
          >
            {{ control.label }}
          </el-button>
        </el-button-group>
      </div>

      <!-- 操作按钮 -->
      <div v-if="actions.length" class="chart-actions">
        <el-button
          v-for="action in actions"
          :key="action.label"
          :type="action.type || 'text'"
          size="small"
          @click="handleActionClick(action)"
        >
          {{ action.label }}
        </el-button>
      </div>
    </div>

    <div class="chart-content" :class="{ loading: isLoading }">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="chart-loading">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="rect" style="width: 100%; height: 200px;" />
          </template>
        </el-skeleton>
      </div>

      <!-- 图表内容 -->
      <div v-else class="chart-body">
        <slot />
      </div>
    </div>

    <!-- 图例或底部信息 -->
    <div v-if="$slots.footer" class="chart-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ChartCard',
  props: {
    title: {
      type: String,
      required: true
    },
    controls: {
      type: Array,
      default: () => []
    },
    actions: {
      type: Array,
      default: () => []
    },
    defaultControl: {
      type: String,
      default: ''
    },
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['control-change'],

  setup(props, { emit }) {
    const activeControl = ref(props.defaultControl || (props.controls[0]?.value || ''))

    const handleControlChange = (value) => {
      activeControl.value = value
      emit('control-change', value)
    }

    const handleActionClick = (action) => {
      if (action.onClick && typeof action.onClick === 'function') {
        action.onClick()
      }
    }

    return {
      activeControl,
      handleControlChange,
      handleActionClick
    }
  }
}
</script>

<style lang="scss" scoped>
.chart-card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow var(--transition-fast);

  &:hover {
    box-shadow: var(--shadow-md);
  }
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6) var(--space-6) var(--space-4);
  border-bottom: 1px solid var(--gray-100);
  background-color: var(--gray-50);
}

.chart-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: var(--space-2);
}

.chart-actions {
  display: flex;
  gap: var(--space-2);
}

.chart-content {
  position: relative;
  min-height: 200px;
}

.chart-loading {
  padding: var(--space-4) var(--space-6);
}

.chart-body {
  padding: var(--space-4) var(--space-6);
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.chart-footer {
  padding: var(--space-4) var(--space-6);
  background-color: var(--gray-50);
  border-top: 1px solid var(--gray-100);
}

// 响应式适配
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
    padding: var(--space-4);
  }

  .chart-controls,
  .chart-actions {
    width: 100%;
    justify-content: center;
  }

  .chart-body {
    padding: var(--space-3);
    min-height: 160px;
  }

  .chart-footer {
    padding: var(--space-3);
  }
}

// 特殊状态
.chart-content.loading {
  overflow: hidden;
}

// 空状态
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--gray-500);

  .empty-icon {
    font-size: 48px;
    margin-bottom: var(--space-3);
    opacity: 0.5;
  }

  .empty-text {
    font-size: var(--text-sm);
  }
}
</style>

