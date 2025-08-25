<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>熵变智元AI销售助手</h1>
        <p>智能销售管理平台</p>
      </div>
      
      <div class="login-form">
        <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef">
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              prefix-icon="el-icon-user"
              size="large"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              prefix-icon="el-icon-lock"
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
            <a href="#" class="forgot-password">忘记密码？</a>
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
              style="width: 100%"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <div class="login-footer">
        <p>© 2024 熵变智元科技有限公司. 保留所有权利.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const store = useStore()
    const loginFormRef = ref(null)
    const loading = ref(false)
    
    const loginForm = reactive({
      username: '',
      password: '',
      remember: false
    })
    
    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      try {
        await loginFormRef.value.validate()
        loading.value = true
        
        // 调用Vuex登录action
        try {
          await store.dispatch('auth/login', {
            username: loginForm.username,
            password: loginForm.password
          })
          
          // 登录成功后跳转
          const redirect = router.currentRoute.value.query.redirect || '/dashboard'
          router.push(redirect)
        } catch (error) {
          console.error('登录失败:', error)
          // 这里可以显示错误提示
        } finally {
          loading.value = false
        }
      } catch (error) {
        console.error('登录验证失败:', error)
        loading.value = false
      }
    }
    
    return {
      loginFormRef,
      loginForm,
      loginRules,
      loading,
      handleLogin
    }
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 3rem;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
  
  h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-color);
  }
  
  p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
}

.login-form {
  margin-bottom: 2rem;
}

.forgot-password {
  float: right;
  color: var(--primary-color);
  text-decoration: none;
  font-size: 0.875rem;
  
  &:hover {
    text-decoration: underline;
  }
}

.login-footer {
  text-align: center;
  
  p {
    margin: 0;
    font-size: 0.75rem;
    color: var(--text-muted);
  }
}
</style>
