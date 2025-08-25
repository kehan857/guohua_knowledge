const state = {
  loading: false,
  loadingText: '加载中...',
  sidebarCollapsed: false,
  theme: 'light',
  currentRoute: '/',
  config: {
    appName: '熵变智元AI销售助手',
    version: '1.0.0',
    copyright: '© 2024 熵变智元科技有限公司',
    autoRefreshInterval: 30000 // 30秒自动刷新
  }
}

const mutations = {
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_LOADING_TEXT(state, text) {
    state.loadingText = text
  },
  SET_SIDEBAR_COLLAPSED(state, collapsed) {
    state.sidebarCollapsed = collapsed
  },
  SET_THEME(state, theme) {
    state.theme = theme
  },
  SET_CONFIG(state, config) {
    state.config = { ...state.config, ...config }
  },
  SET_CURRENT_ROUTE(state, route) {
    state.currentRoute = route
  }
}

const actions = {
  async loadConfig({ commit }) {
    // 模拟配置加载
    try {
      const config = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            appName: '熵变智元AI销售助手',
            version: '1.0.0',
            copyright: '© 2024 熵变智元科技有限公司',
            features: {
              aiChat: true,
              deviceManagement: true,
              sopManagement: true,
              momentsMarketing: true,
              costManagement: true
            }
          })
        }, 500)
      })
      commit('SET_CONFIG', config)
    } catch (error) {
      console.error('配置加载失败:', error)
    }
  },
  
  toggleSidebar({ commit, state }) {
    commit('SET_SIDEBAR_COLLAPSED', !state.sidebarCollapsed)
  },
  
  setTheme({ commit }, theme) {
    commit('SET_THEME', theme)
    // 保存到本地存储
    localStorage.setItem('theme', theme)
  },
  
  showLoading({ commit }, text = '加载中...') {
    commit('SET_LOADING_TEXT', text)
    commit('SET_LOADING', true)
  },
  
  hideLoading({ commit }) {
    commit('SET_LOADING', false)
  }
}

const getters = {
  isLoading: state => state.loading,
  loadingText: state => state.loadingText,
  sidebarCollapsed: state => state.sidebarCollapsed,
  currentTheme: state => state.theme,
  appConfig: state => state.config,
  websocketUrl: () => process.env.VUE_APP_WS_URL || 'ws://localhost:3000'
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}