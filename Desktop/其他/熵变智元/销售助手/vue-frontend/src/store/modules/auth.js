const state = {
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: false
}

const mutations = {
  SET_USER(state, user) {
    state.user = user
    state.isAuthenticated = !!user
  },
  SET_TOKEN(state, token) {
    state.token = token
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  },
  LOGOUT(state) {
    state.user = null
    state.token = null
    state.isAuthenticated = false
    localStorage.removeItem('token')
  }
}

const actions = {
  async login({ commit }, credentials) {
    try {
      // 模拟API调用
      const response = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            user: {
              id: 1,
              username: credentials.username,
              name: '管理员',
              email: 'admin@example.com',
              role: 'admin'
            },
            token: 'mock-jwt-token'
          })
        }, 1000)
      })
      
      commit('SET_USER', response.user)
      commit('SET_TOKEN', response.token)
      return response
    } catch (error) {
      throw error
    }
  },
  
  async logout({ commit }) {
    commit('LOGOUT')
  },
  
  async checkAuth({ commit }) {
    const token = localStorage.getItem('token')
    if (token) {
      // 验证token有效性
      try {
        // 模拟API调用
        const user = await new Promise(resolve => {
          setTimeout(() => {
            resolve({
              id: 1,
              username: 'admin',
              name: '管理员',
              email: 'admin@example.com',
              role: 'admin'
            })
          }, 500)
        })
        
        commit('SET_USER', user)
        commit('SET_TOKEN', token)
      } catch (error) {
        commit('LOGOUT')
      }
    }
  },
  
  async verifyToken({ commit }) {
    const token = localStorage.getItem('token')
    if (!token) {
      throw new Error('No token found')
    }
    
    try {
      // 模拟token验证API调用
      const user = await new Promise((resolve, reject) => {
        setTimeout(() => {
          // 简单的token验证逻辑
          if (token === 'mock-jwt-token') {
            resolve({
              id: 1,
              username: 'admin',
              name: '管理员',
              email: 'admin@example.com',
              role: 'admin'
            })
          } else {
            reject(new Error('Invalid token'))
          }
        }, 500)
      })
      
      commit('SET_USER', user)
      commit('SET_TOKEN', token)
      return user
    } catch (error) {
      commit('LOGOUT')
      throw error
    }
  }
}

const getters = {
  isAuthenticated: state => state.isAuthenticated,
  currentUser: state => state.user,
  userRole: state => state.user?.role
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
