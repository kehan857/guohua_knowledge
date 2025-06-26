<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">天云聚合产业数据中心</h1>
        <p class="login-subtitle">内部数据门户 - 请登录您的企业账户</p>
      </div>
      
      <a-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        @finish="handleLogin"
        class="login-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="loginForm.username"
            placeholder="请输入工号"
            size="large"
            :prefix="h(UserOutlined)"
          />
        </a-form-item>
        
        <a-form-item name="password">
          <a-input-password
            v-model:value="loginForm.password"
            placeholder="请输入密码"
            size="large"
            :prefix="h(LockOutlined)"
          />
        </a-form-item>
        
        <a-form-item>
          <a-checkbox v-model:checked="loginForm.remember">
            记住我
          </a-checkbox>
        </a-form-item>
        
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
            class="login-button"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="login-footer">
        <p>© 2024 天云聚合产业数据中心 - 内部使用系统</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()

// 表单数据
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { min: 2, max: 20, message: '工号长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ]
}

const loading = ref(false)
const formRef = ref()

// 登录处理
const handleLogin = async () => {
  try {
    loading.value = true
    
    // 模拟登录API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟不同用户权限
    const userRole = loginForm.username === 'admin' ? 'admin' : 'user'
    
    // 保存登录状态和用户信息
    localStorage.setItem('token', 'mock-jwt-token')
    localStorage.setItem('userInfo', JSON.stringify({
      username: loginForm.username,
      role: userRole,
      permissions: userRole === 'admin' ? ['admin', 'user'] : ['user']
    }))
    
    message.success('登录成功')
    
    // 跳转到首页
    router.push('/dashboard')
    
  } catch (error) {
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="less" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.login-header {
  padding: 32px 32px 0;
  text-align: center;
  
  .login-title {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
    margin: 0 0 8px 0;
  }
  
  .login-subtitle {
    font-size: 14px;
    color: #606266;
    margin: 0 0 32px 0;
  }
}

.login-form {
  padding: 0 32px 32px;
  
  .login-button {
    height: 40px;
    font-size: 16px;
    font-weight: 500;
  }
}

.login-footer {
  padding: 20px 32px;
  background: #f7f8fa;
  text-align: center;
  
  p {
    margin: 0;
    font-size: 12px;
    color: #909399;
  }
}

@media (max-width: 480px) {
  .login-card {
    margin: 0 10px;
  }
  
  .login-header {
    padding: 24px 24px 0;
    
    .login-title {
      font-size: 20px;
    }
  }
  
  .login-form {
    padding: 0 24px 24px;
  }
  
  .login-footer {
    padding: 16px 24px;
  }
}
</style> 