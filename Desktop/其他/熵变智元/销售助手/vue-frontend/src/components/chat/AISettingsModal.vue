<template>
  <el-dialog
    title="AI设置"
    :visible.sync="visible"
    width="500px"
    @close="$emit('close')"
  >
    <div class="ai-settings-modal">
      <el-form :model="settings" label-width="100px">
        <el-form-item label="AI模型">
          <el-select v-model="settings.model" placeholder="选择AI模型">
            <el-option label="GPT-4" value="gpt-4" />
            <el-option label="GPT-3.5" value="gpt-3.5" />
            <el-option label="Claude" value="claude" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="温度">
          <el-slider
            v-model="settings.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="最大长度">
          <el-input-number
            v-model="settings.maxLength"
            :min="100"
            :max="4000"
            :step="100"
          />
        </el-form-item>
        
        <el-form-item label="系统提示">
          <el-input
            v-model="settings.systemPrompt"
            type="textarea"
            :rows="4"
            placeholder="输入系统提示词..."
          />
        </el-form-item>
        
        <el-form-item label="自动回复">
          <el-switch v-model="settings.autoReply" />
        </el-form-item>
        
        <el-form-item label="回复延迟">
          <el-input-number
            v-model="settings.replyDelay"
            :min="0"
            :max="60"
            :step="1"
          />
          <span class="unit">秒</span>
        </el-form-item>
      </el-form>
    </div>
    
    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" @click="saveSettings">保存</el-button>
    </template>
  </el-dialog>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'AISettingsModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    currentSettings: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'save-settings'],
  setup(props, { emit }) {
    const settings = ref({
      model: 'gpt-4',
      temperature: 0.7,
      maxLength: 1000,
      systemPrompt: '你是一个专业的销售助手，请帮助用户解答问题。',
      autoReply: true,
      replyDelay: 3,
      ...props.currentSettings
    })
    
    const saveSettings = () => {
      emit('save-settings', settings.value)
      emit('close')
    }
    
    return {
      settings,
      saveSettings
    }
  }
}
</script>

<style lang="scss" scoped>
.ai-settings-modal {
  .unit {
    margin-left: 0.5rem;
    color: var(--text-secondary);
  }
}
</style>
