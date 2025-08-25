const state = {
  notifications: [],
  unreadCount: 0
}

const mutations = {
  SET_NOTIFICATIONS(state, notifications) {
    state.notifications = notifications
  },
  ADD_NOTIFICATION(state, notification) {
    state.notifications.unshift(notification)
    if (!notification.read) {
      state.unreadCount++
    }
  },
  MARK_READ(state, id) {
    const notification = state.notifications.find(n => n.id === id)
    if (notification && !notification.read) {
      notification.read = true
      state.unreadCount--
    }
  },
  MARK_ALL_READ(state) {
    state.notifications.forEach(n => n.read = true)
    state.unreadCount = 0
  }
}

const actions = {
  async fetchNotifications({ commit }) {
    const notifications = await new Promise(resolve => {
      setTimeout(() => {
        resolve([
          {
            id: 1,
            title: '系统更新',
            message: '系统将在今晚进行维护更新',
            type: 'info',
            read: false,
            timestamp: new Date()
          }
        ])
      }, 1000)
    })
    commit('SET_NOTIFICATIONS', notifications)
  },
  
  removeNotification({ commit, state }, id) {
    const index = state.notifications.findIndex(n => n.id === id)
    if (index > -1) {
      const notification = state.notifications[index]
      if (!notification.read) {
        commit('MARK_READ', id)
      }
      state.notifications.splice(index, 1)
    }
  },
  
  addNotification({ commit }, notification) {
    const newNotification = {
      id: Date.now(),
      timestamp: new Date(),
      read: false,
      ...notification
    }
    commit('ADD_NOTIFICATION', newNotification)
  },
  
  async handleAlert({ commit }, { alertId, action }) {
    // 模拟处理告警
    await new Promise(resolve => setTimeout(resolve, 500))
    console.log(`处理告警 ${alertId}，动作: ${action}`)
  }
}

const getters = {
  unreadNotifications: state => state.notifications.filter(n => !n.read),
  recentAlerts: state => state.notifications.slice(0, 5) // 返回最近5条通知作为警报
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
