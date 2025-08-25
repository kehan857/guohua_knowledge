import { io } from 'socket.io-client'
import store from '@/store'

class WebSocketManager {
  constructor() {
    this.socket = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.isConnecting = false
    this.heartbeatTimer = null
    this.heartbeatInterval = 30000 // 30秒心跳
  }

  // 连接WebSocket
  connect() {
    // 暂时禁用WebSocket连接以避免错误
    console.log('WebSocket connection disabled for demo purposes')
    return Promise.resolve()
    
    if (this.socket?.connected || this.isConnecting) {
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      this.isConnecting = true

      const token = localStorage.getItem('token')
      if (!token) {
        this.isConnecting = false
        reject(new Error('No authentication token'))
        return
      }

      // 创建socket连接
      this.socket = io(store.getters['app/websocketUrl'], {
        auth: {
          token
        },
        transports: ['websocket'],
        timeout: 10000,
        reconnection: false // 手动控制重连
      })

      // 连接成功
      this.socket.on('connect', () => {
        console.log('WebSocket connected:', this.socket.id)
        this.isConnecting = false
        this.reconnectAttempts = 0
        
        // 更新连接状态
        store.commit('websocket/SET_CONNECTED', true)
        store.commit('websocket/SET_SOCKET_ID', this.socket.id)
        
        // 开始心跳
        this.startHeartbeat()
        
        // 订阅用户相关事件
        this.subscribeToEvents()
        
        resolve()
      })

      // 连接失败
      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error)
        this.isConnecting = false
        
        if (error.message.includes('authentication')) {
          // 认证失败，可能token过期
          store.dispatch('auth/logout')
          reject(error)
        } else {
          // 网络错误，尝试重连
          this.handleReconnect()
          reject(error)
        }
      })

      // 连接断开
      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason)
        store.commit('websocket/SET_CONNECTED', false)
        this.stopHeartbeat()

        if (reason === 'io server disconnect') {
          // 服务器主动断开，可能是维护
          store.dispatch('notifications/addNotification', {
            type: 'warning',
            title: '连接断开',
            message: '服务器连接已断开，正在尝试重连...'
          })
        }

        // 自动重连
        this.handleReconnect()
      })

      // 处理错误
      this.socket.on('error', (error) => {
        console.error('WebSocket error:', error)
        store.dispatch('notifications/addNotification', {
          type: 'error',
          title: '连接错误',
          message: error.message || 'WebSocket连接发生错误'
        })
      })
    })
  }

  // 订阅事件
  subscribeToEvents() {
    if (!this.socket) return

    // 新消息事件
    this.socket.on('new_message', (data) => {
      store.dispatch('chat/handleNewMessage', data)
    })

    // 设备状态变化
    this.socket.on('device_status_change', (data) => {
      store.dispatch('devices/updateDeviceStatus', data)
    })

    // AI接管状态变化
    this.socket.on('ai_toggle', (data) => {
      store.dispatch('chat/updateAIStatus', data)
    })

    // 任务状态更新
    this.socket.on('task_status_update', (data) => {
      store.dispatch('sop/updateTaskStatus', data)
    })

    // 算力使用更新
    this.socket.on('cost_update', (data) => {
      store.dispatch('cost/updateUsage', data)
    })

    // 系统告警
    this.socket.on('system_alert', (data) => {
      store.dispatch('notifications/handleSystemAlert', data)
    })

    // 人工介入请求
    this.socket.on('manual_intervention_required', (data) => {
      store.dispatch('chat/handleInterventionRequest', data)
    })

    // 朋友圈互动结果
    this.socket.on('moments_interaction_result', (data) => {
      store.dispatch('moments/updateInteractionResult', data)
    })

    // 心跳响应
    this.socket.on('pong', () => {
      // 收到服务器心跳响应
      console.log('Received heartbeat pong')
    })
  }

  // 断开连接
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    
    this.stopHeartbeat()
    store.commit('websocket/SET_CONNECTED', false)
    store.commit('websocket/SET_SOCKET_ID', null)
  }

  // 发送消息
  emit(event, data) {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
      return true
    } else {
      console.warn('WebSocket not connected, cannot emit:', event)
      return false
    }
  }

  // 处理重连
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      store.dispatch('notifications/addNotification', {
        type: 'error',
        title: '连接失败',
        message: '无法连接到服务器，请检查网络连接或刷新页面重试'
      })
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // 指数退避

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)

    setTimeout(() => {
      if (!this.socket?.connected) {
        this.connect().catch(console.error)
      }
    }, delay)
  }

  // 开始心跳
  startHeartbeat() {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping')
      }
    }, this.heartbeatInterval)
  }

  // 停止心跳
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // 获取连接状态
  get isConnected() {
    return this.socket?.connected || false
  }

  // 监听特定事件
  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback)
    }
  }

  // 取消监听事件
  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback)
    }
  }
}

// 创建单例实例
const wsManager = new WebSocketManager()

export default wsManager

