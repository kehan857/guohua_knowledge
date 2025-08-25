import axios from 'axios'
import store from '@/store'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()

    // 显示加载状态
    if (config.showLoading !== false) {
      store.commit('app/SET_LOADING', true)
    }

    return config
  },
  (error) => {
    store.commit('app/SET_LOADING', false)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 隐藏加载状态
    store.commit('app/SET_LOADING', false)

    // 处理业务错误码
    if (response.data.code && response.data.code !== 200) {
      const error = new Error(response.data.message || '请求失败')
      error.code = response.data.code
      throw error
    }

    return response.data
  },
  (error) => {
    store.commit('app/SET_LOADING', false)

    // 处理HTTP错误
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权，清除token并跳转登录
          localStorage.removeItem('token')
          store.dispatch('auth/logout')
          router.push('/login')
          break

        case 403:
          // 权限不足
          store.dispatch('notifications/addNotification', {
            type: 'error',
            title: '权限不足',
            message: '您没有权限执行此操作'
          })
          break

        case 404:
          // 资源不存在
          store.dispatch('notifications/addNotification', {
            type: 'error',
            title: '资源不存在',
            message: '请求的资源不存在'
          })
          break

        case 429:
          // 请求频率限制
          store.dispatch('notifications/addNotification', {
            type: 'warning',
            title: '请求过于频繁',
            message: '请稍后再试'
          })
          break

        case 500:
          // 服务器错误
          store.dispatch('notifications/addNotification', {
            type: 'error',
            title: '服务器错误',
            message: '服务器内部错误，请稍后重试'
          })
          break

        default:
          // 其他错误
          store.dispatch('notifications/addNotification', {
            type: 'error',
            title: '请求失败',
            message: data?.message || error.message || '网络错误'
          })
      }
    } else if (error.request) {
      // 网络错误
      store.dispatch('notifications/addNotification', {
        type: 'error',
        title: '网络错误',
        message: '无法连接到服务器，请检查网络连接'
      })
    } else {
      // 其他错误
      store.dispatch('notifications/addNotification', {
        type: 'error',
        title: '请求失败',
        message: error.message || '发生未知错误'
      })
    }

    return Promise.reject(error)
  }
)

// 生成请求ID
function generateRequestId() {
  return Math.random().toString(36).substr(2, 9) + Date.now().toString(36)
}

// API方法封装
export const authAPI = {
  // 登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 验证token
  verifyToken: () => api.get('/auth/verify'),
  
  // 刷新token
  refreshToken: () => api.post('/auth/refresh'),
  
  // 退出登录
  logout: () => api.post('/auth/logout')
}

export const devicesAPI = {
  // 获取设备列表
  getDevices: (params) => api.get('/devices', { params }),
  
  // 获取设备详情
  getDevice: (id) => api.get(`/devices/${id}`),
  
  // 添加设备
  addDevice: (data) => api.post('/devices', data),
  
  // 更新设备
  updateDevice: (id, data) => api.put(`/devices/${id}`, data),
  
  // 删除设备
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  
  // 获取登录二维码
  getQRCode: (appId) => api.post('/devices/qrcode', { appId }),
  
  // 强制下线
  forceOffline: (id) => api.post(`/devices/${id}/offline`),
  
  // 获取登录日志
  getLoginLogs: (id, params) => api.get(`/devices/${id}/logs`, { params })
}

export const chatAPI = {
  // 获取会话列表
  getConversations: (params) => api.get('/chat/conversations', { params }),
  
  // 获取聊天记录
  getMessages: (conversationId, params) => api.get(`/chat/conversations/${conversationId}/messages`, { params }),
  
  // 发送消息
  sendMessage: (data) => api.post('/chat/messages', data),
  
  // 切换AI接管状态
  toggleAI: (conversationId, enabled) => api.put(`/chat/conversations/${conversationId}/ai`, { enabled }),
  
  // 获取今日统计
  getTodayStats: () => api.get('/chat/stats/today'),
  
  // 获取趋势数据
  getTrendData: (params) => api.get('/chat/stats/trend', { params })
}

export const sopAPI = {
  // 获取SOP任务列表
  getTasks: (params) => api.get('/sop/tasks', { params }),
  
  // 获取任务详情
  getTask: (id) => api.get(`/sop/tasks/${id}`),
  
  // 创建任务
  createTask: (data) => api.post('/sop/tasks', data),
  
  // 更新任务
  updateTask: (id, data) => api.put(`/sop/tasks/${id}`, data),
  
  // 删除任务
  deleteTask: (id) => api.delete(`/sop/tasks/${id}`),
  
  // 启动/暂停任务
  toggleTask: (id, action) => api.post(`/sop/tasks/${id}/${action}`),
  
  // 获取执行日志
  getTaskLogs: (id, params) => api.get(`/sop/tasks/${id}/logs`, { params })
}

export const momentsAPI = {
  // 获取朋友圈任务列表
  getTasks: (params) => api.get('/moments/tasks', { params }),
  
  // 创建朋友圈任务
  createTask: (data) => api.post('/moments/tasks', data),
  
  // 立即发布
  publishNow: (id) => api.post(`/moments/tasks/${id}/publish`),
  
  // 获取AI互动配置
  getAIConfig: () => api.get('/moments/ai-config'),
  
  // 更新AI互动配置
  updateAIConfig: (data) => api.put('/moments/ai-config', data),
  
  // 获取互动日志
  getInteractionLogs: (params) => api.get('/moments/interactions', { params }),
  
  // 获取数据分析
  getAnalytics: (params) => api.get('/moments/analytics', { params })
}

export const costAPI = {
  // 获取Dashboard数据
  getDashboardData: () => api.get('/cost/dashboard'),
  
  // 获取用户配额列表
  getUserQuotas: (params) => api.get('/cost/quotas', { params }),
  
  // 更新用户配额
  updateUserQuota: (userId, data) => api.put(`/cost/quotas/${userId}`, data),
  
  // 获取成本明细
  getCostDetails: (params) => api.get('/cost/details', { params }),
  
  // 获取模型价格
  getModelPrices: () => api.get('/cost/models'),
  
  // 更新模型价格
  updateModelPrice: (modelId, data) => api.put(`/cost/models/${modelId}`, data),
  
  // 生成成本报告
  generateReport: (params) => api.post('/cost/reports', params)
}

export const materialsAPI = {
  // 获取物料列表
  getMaterials: (params) => api.get('/materials', { params }),
  
  // 添加物料
  addMaterial: (data) => api.post('/materials', data),
  
  // 更新物料
  updateMaterial: (id, data) => api.put(`/materials/${id}`, data),
  
  // 删除物料
  deleteMaterial: (id) => api.delete(`/materials/${id}`),
  
  // 上传文件
  uploadFile: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/materials/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    })
  }
}

export default api

