import { createStore } from 'vuex'

// 导入所有模块
import app from './modules/app'
import auth from './modules/auth'
import chat from './modules/chat'
import devices from './modules/devices'
import sop from './modules/sop'
import moments from './modules/moments'
import cost from './modules/cost'
import notifications from './modules/notifications'
import websocket from './modules/websocket'

export default createStore({
  modules: {
    app,
    auth,
    chat,
    devices,
    sop,
    moments,
    cost,
    notifications,
    websocket
  },
  
  // 严格模式
  strict: process.env.NODE_ENV !== 'production',
  
  // 全局状态
  state: {
    version: '1.0.0'
  },
  
  // 全局getters
  getters: {
    // 获取应用版本
    appVersion: (state) => state.version,
    
    // 获取当前用户
    currentUser: (state) => state.auth.user,
    
    // 获取在线设备数量
    onlineDevicesCount: (state) => {
      return state.devices.list.filter(device => device.status === 'ONLINE').length
    },
    
    // 获取未读消息总数
    unreadMessagesCount: (state) => {
      return state.chat.conversations.reduce((total, conversation) => {
        return total + (conversation.unreadCount || 0)
      }, 0)
    }
  },
  
  // 全局mutations
  mutations: {
    // 重置所有状态
    RESET_ALL_STATE(state) {
      // 重置除了app模块外的所有状态
      Object.keys(state).forEach(key => {
        if (key !== 'app' && key !== 'version') {
          state[key] = {}
        }
      })
    }
  },
  
  // 全局actions
  actions: {
    // 初始化应用数据
    async initAppData({ dispatch, commit }) {
      try {
        commit('app/SET_LOADING', true)
        
        // 并行加载基础数据
        await Promise.all([
          dispatch('devices/fetchDevices'),
          dispatch('chat/fetchConversations'),
          dispatch('cost/fetchDashboardData')
        ])
        
        commit('app/SET_LOADING', false)
      } catch (error) {
        commit('app/SET_LOADING', false)
        throw error
      }
    },
    
    // 清除所有数据
    clearAllData({ commit }) {
      commit('RESET_ALL_STATE')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})

