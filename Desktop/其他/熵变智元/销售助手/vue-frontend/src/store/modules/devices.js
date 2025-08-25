const state = {
  devices: [],
  isLoading: false
}

const mutations = {
  SET_DEVICES(state, devices) {
    state.devices = devices
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading
  }
}

const actions = {
  async fetchDevices({ commit }) {
    commit('SET_LOADING', true)
    try {
      const devices = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              name: '张经理微信',
              status: 'online',
              uptime: '2小时30分',
              messageCount: 156
            },
            {
              id: 2,
              name: '李助理微信',
              status: 'offline',
              uptime: '0小时0分',
              messageCount: 89
            }
          ])
        }, 1000)
      })
      commit('SET_DEVICES', devices)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  showQRCodeModal({ commit }) {
    // 模拟显示二维码模态框
    console.log('显示二维码模态框')
  }
}

const getters = {
  onlineDevices: state => state.devices.filter(d => d.status === 'online'),
  onlineCount: state => state.devices.filter(d => d.status === 'online').length,
  totalCount: state => state.devices.length
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
