<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1>页面未找到</h1>
      <p>抱歉，您访问的页面不存在或已被移除。</p>
      <div class="actions">
        <a-button type="primary" @click="goHome">
          <template #icon><HomeOutlined /></template>
          返回首页
        </a-button>
        <a-button @click="goBack">
          <template #icon><ArrowLeftOutlined /></template>
          返回上页
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeOutlined, ArrowLeftOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.not-found-content {
  text-align: center;
  padding: 48px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 480px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #1890ff;
  line-height: 1;
  margin-bottom: 24px;
}

h1 {
  font-size: 24px;
  margin-bottom: 16px;
  color: #333;
}

p {
  color: #666;
  margin-bottom: 32px;
  font-size: 16px;
}

.actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style> 