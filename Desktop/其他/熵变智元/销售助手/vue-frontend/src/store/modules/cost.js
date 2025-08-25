const state = {
  costs: [],
  isLoading: false,
  rankingData: []
}

const mutations = {
  SET_COSTS(state, costs) {
    state.costs = costs
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading
  },
  SET_RANKING_DATA(state, data) {
    state.rankingData = data
  }
}

const actions = {
  async fetchCosts({ commit }) {
    commit('SET_LOADING', true)
    try {
      const costs = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              service: 'GPT-4 API',
              cost: 1250.50,
              usage: '1,250次调用'
            },
            {
              service: 'Claude API',
              cost: 599.80,
              usage: '800次调用'
            }
          ])
        }, 1000)
      })
      commit('SET_COSTS', costs)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async fetchDashboardData({ commit }) {
    commit('SET_LOADING', true)
    try {
      const data = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            totalCost: 1850.30,
            monthlyUsage: 75
          })
        }, 1000)
      })
      // 这里可以设置dashboard相关的数据
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async fetchRankingData({ commit }) {
    try {
      const data = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              name: '张经理',
              cost: 450.50,
              usage: '1,200次调用'
            },
            {
              id: 2,
              name: '李助理',
              cost: 320.80,
              usage: '800次调用'
            }
          ])
        }, 500)
      })
      commit('SET_RANKING_DATA', data)
    } catch (error) {
      console.error('获取排行榜数据失败:', error)
    }
  }
}

const getters = {
  totalCost: state => state.costs.reduce((sum, cost) => sum + cost.cost, 0),
  usagePercentage: () => 75, // 模拟使用百分比
  usageProgress: () => '+12.5%' // 模拟使用进度
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
