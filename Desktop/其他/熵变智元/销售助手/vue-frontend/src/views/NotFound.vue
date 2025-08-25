<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1>页面未找到</h1>
      <p>抱歉，您访问的页面不存在或已被移除。</p>
      <div class="actions">
        <el-button type="primary" @click="goHome">
          <i class="el-icon-house"></i>
          返回首页
        </el-button>
        <el-button @click="goBack">
          <i class="el-icon-back"></i>
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'NotFound',
  setup() {
    const router = useRouter()
    
    const goHome = () => {
      router.push('/dashboard')
    }
    
    const goBack = () => {
      router.go(-1)
    }
    
    return {
      goHome,
      goBack
    }
  }
}
</script>

<style lang="scss" scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  padding: 2rem;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.error-code {
  font-size: 8rem;
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
  margin-bottom: 1rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

h1 {
  font-size: 2rem;
  color: var(--text-color);
  margin: 0 0 1rem 0;
}

p {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin: 0 0 2rem 0;
  line-height: 1.5;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
