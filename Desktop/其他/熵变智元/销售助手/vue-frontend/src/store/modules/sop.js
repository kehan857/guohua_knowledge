const state = {
  sops: [],
  isLoading: false
}

const mutations = {
  SET_SOPS(state, sops) {
    state.sops = sops
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading
  }
}

const actions = {
  async fetchSOPs({ commit }) {
    commit('SET_LOADING', true)
    try {
      const sops = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              name: '客户咨询处理流程',
              status: 'active',
              createdAt: '2024-01-15'
            },
            {
              id: 2,
              name: '产品介绍SOP',
              status: 'draft',
              createdAt: '2024-01-10'
            }
          ])
        }, 1000)
      })
      commit('SET_SOPS', sops)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async fetchActiveTasks({ commit }) {
    commit('SET_LOADING', true)
    try {
      const tasks = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              name: '客户咨询处理流程',
              status: 'active',
              progress: 75
            },
            {
              id: 2,
              name: '产品介绍SOP',
              status: 'active',
              progress: 30
            }
          ])
        }, 1000)
      })
      commit('SET_SOPS', tasks)
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

const getters = {
  activeSOPs: state => state.sops.filter(s => s.status === 'active'),
  activeTasksCount: state => state.sops.filter(s => s.status === 'active').length
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
