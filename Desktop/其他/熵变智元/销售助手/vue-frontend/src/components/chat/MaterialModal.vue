<template>
  <el-dialog
    title="选择素材"
    :visible.sync="visible"
    width="600px"
    @close="$emit('close')"
  >
    <div class="material-modal">
      <div class="material-tabs">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="文本素材" name="text">
            <div class="material-list">
              <div 
                v-for="material in textMaterials" 
                :key="material.id"
                class="material-item"
                @click="selectMaterial(material)"
              >
                <div class="material-title">{{ material.title }}</div>
                <div class="material-content">{{ material.content }}</div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="图片素材" name="image">
            <div class="material-list">
              <div 
                v-for="material in imageMaterials" 
                :key="material.id"
                class="material-item"
                @click="selectMaterial(material)"
              >
                <img :src="material.url" :alt="material.title" />
                <div class="material-title">{{ material.title }}</div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </el-dialog>
</template>

<script>
export default {
  name: 'MaterialModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'select-material'],
  setup(props, { emit }) {
    const activeTab = ref('text')
    
    const textMaterials = ref([
      {
        id: 1,
        title: '产品介绍',
        content: '我们公司专注于提供高质量的AI销售解决方案...',
        type: 'text'
      },
      {
        id: 2,
        title: '价格说明',
        content: '我们的产品采用灵活的定价模式，根据您的需求定制...',
        type: 'text'
      }
    ])
    
    const imageMaterials = ref([
      {
        id: 3,
        title: '产品截图',
        url: '/images/product-screenshot.png',
        type: 'image'
      }
    ])
    
    const selectMaterial = (material) => {
      emit('select-material', material)
      emit('close')
    }
    
    return {
      activeTab,
      textMaterials,
      imageMaterials,
      selectMaterial
    }
  }
}
</script>

<style lang="scss" scoped>
.material-modal {
  .material-list {
    max-height: 400px;
    overflow-y: auto;
  }
  
  .material-item {
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    margin-bottom: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: var(--primary-color);
      background: var(--bg-hover);
    }
  }
  
  .material-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-color);
  }
  
  .material-content {
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }
  
  img {
    width: 100%;
    height: 120px;
    object-fit: cover;
    border-radius: var(--border-radius);
    margin-bottom: 0.5rem;
  }
}
</style>
