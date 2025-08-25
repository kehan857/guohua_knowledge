<template>
  <div class="shortcut-panel">
    <div class="panel-header">
      <h4>快捷操作</h4>
    </div>
    <div class="shortcut-grid">
      <div 
        v-for="shortcut in shortcuts" 
        :key="shortcut.id"
        class="shortcut-item"
        @click="executeShortcut(shortcut)"
      >
        <div class="shortcut-icon">
          <i :class="shortcut.icon"></i>
        </div>
        <div class="shortcut-label">{{ shortcut.label }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'ShortcutPanel',
  props: {
    shortcuts: {
      type: Array,
      default: () => []
    }
  },
  emits: ['shortcut-click'],
  setup(props, { emit }) {
    const executeShortcut = (shortcut) => {
      if (shortcut.onClick) {
        shortcut.onClick()
      }
      emit('shortcut-click', shortcut)
    }
    
    return {
      executeShortcut
    }
  }
}
</script>

<style lang="scss" scoped>
.shortcut-panel {
  background: var(--card-bg);
  border-radius: var(--border-radius);
  padding: 1rem;
  box-shadow: var(--shadow);
}

.panel-header {
  margin-bottom: 1rem;
  
  h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
  }
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.shortcut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: var(--border-radius);
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: var(--primary-color);
    background: var(--bg-hover);
    transform: translateY(-2px);
  }
}

.shortcut-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  
  i {
    font-size: 1.5rem;
    color: white;
  }
}

.shortcut-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color);
  text-align: center;
}

@media (max-width: 768px) {
  .shortcut-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
