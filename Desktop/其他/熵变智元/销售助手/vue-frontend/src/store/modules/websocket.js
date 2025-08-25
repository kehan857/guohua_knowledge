const state = {
  connected: false,
  socketId: null,
  messages: [],
  manager: null
}

const mutations = {
  SET_CONNECTED(state, connected) {
    state.connected = connected
  },
  SET_SOCKET_ID(state, id) {
    state.socketId = id
  },
  ADD_MESSAGE(state, message) {
    state.messages.push(message)
  },
  SET_MANAGER(state, manager) {
    state.manager = manager
  }
}

const actions = {
  connect({ commit }) {
    commit('SET_CONNECTED', true)
  },
  
  disconnect({ commit }) {
    commit('SET_CONNECTED', false)
  },
  
  receiveMessage({ commit }, message) {
    commit('ADD_MESSAGE', message)
  }
}

const getters = {
  isConnected: state => state.connected
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
