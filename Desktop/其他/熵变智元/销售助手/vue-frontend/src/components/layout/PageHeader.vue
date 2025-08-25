<template>
  <header class="page-header">
    <div class="header-content">
      <!-- 左侧标题 -->
      <div class="header-left">
        <h1 class="page-title">{{ title }}</h1>
        <div v-if="subtitle" class="page-subtitle">{{ subtitle }}</div>
      </div>

      <!-- 右侧操作 -->
      <div class="header-right">
        <div class="header-actions">
          <el-button
            v-for="action in actions"
            :key="action.label"
            :type="action.type || 'default'"
            :size="action.size || 'default'"
            :icon="action.icon"
            @click="handleActionClick(action)"
          >
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'PageHeader',
  props: {
    title: {
      type: String,
      required: true
    },
    subtitle: {
      type: String,
      default: ''
    },
    actions: {
      type: Array,
      default: () => []
    }
  },

  setup(props) {
    const handleActionClick = (action) => {
      if (action.onClick && typeof action.onClick === 'function') {
        action.onClick()
      }
    }

    return {
      handleActionClick
    }
  }
}
</script>

<style lang="scss" scoped>
.page-header {
  margin-bottom: var(--space-8);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) 0;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
  margin-bottom: var(--space-1);
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--gray-600);
}

.header-right {
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-3);
}

// 响应式适配
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-4);
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .page-title {
    font-size: var(--text-2xl);
  }
}

@media (max-width: 480px) {
  .header-actions {
    flex-direction: column;
    gap: var(--space-2);
  }
}
</style>

