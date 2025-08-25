const state = {
  conversations: [],
  currentConversation: null,
  messages: [],
  isAIEnabled: false,
  isLoading: false,
  todayStats: {
    received: 0,
    sent: 0
  },
  trendData: [],
  conversationsLoading: false,
  messagesLoading: false,
  aiSettings: {
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 1000
  }
}

const mutations = {
  SET_CONVERSATIONS(state, conversations) {
    state.conversations = conversations
  },
  SET_CURRENT_CONVERSATION(state, conversation) {
    state.currentConversation = conversation
  },
  SET_MESSAGES(state, messages) {
    state.messages = messages
  },
  ADD_MESSAGE(state, message) {
    state.messages.push(message)
  },
  SET_AI_ENABLED(state, enabled) {
    state.isAIEnabled = enabled
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading
  },
  SET_TODAY_STATS(state, stats) {
    state.todayStats = stats
  },
  SET_TREND_DATA(state, data) {
    state.trendData = data
  },
  SET_CONVERSATIONS_LOADING(state, loading) {
    state.conversationsLoading = loading
  },
  SET_MESSAGES_LOADING(state, loading) {
    state.messagesLoading = loading
  },
  SET_AI_SETTINGS(state, settings) {
    state.aiSettings = { ...state.aiSettings, ...settings }
  }
}

const actions = {
  async fetchConversations({ commit }) {
    commit('SET_LOADING', true)
    try {
      // 模拟API调用
      const conversations = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              title: '客户咨询',
              lastMessage: '您好，我想了解一下产品',
              timestamp: new Date(),
              unreadCount: 2,
              status: 'online'
            },
            {
              id: 2,
              title: '技术支持',
              lastMessage: '系统运行正常',
              timestamp: new Date(Date.now() - 1000 * 60 * 30),
              unreadCount: 0,
              status: 'offline'
            }
          ])
        }, 1000)
      })
      
      commit('SET_CONVERSATIONS', conversations)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async fetchMessages({ commit }, conversationId) {
    commit('SET_LOADING', true)
    try {
      // 模拟API调用
      const messages = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              content: '您好，我想了解一下产品',
              sender: '客户',
              type: 'user',
              timestamp: new Date(Date.now() - 1000 * 60 * 5),
              avatar: '/images/avatar1.jpg'
            },
            {
              id: 2,
              content: '您好！很高兴为您服务，请问您想了解哪方面的产品呢？',
              sender: 'AI助手',
              type: 'assistant',
              timestamp: new Date(Date.now() - 1000 * 60 * 4),
              avatar: '/images/ai-avatar.jpg'
            }
          ])
        }, 500)
      })
      
      commit('SET_MESSAGES', messages)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  async fetchTodayStats({ commit }) {
    try {
      // 模拟API调用获取今日统计数据
      const stats = await new Promise(resolve => {
        setTimeout(() => {
          resolve({
            received: 156,
            sent: 142
          })
        }, 500)
      })
      
      commit('SET_TODAY_STATS', stats)
    } catch (error) {
      console.error('获取今日统计数据失败:', error)
    }
  },
  
  async fetchTrendData({ commit }, { period }) {
    try {
      // 模拟API调用获取趋势数据
      const data = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            { date: '2024-01-01', received: 120, sent: 110 },
            { date: '2024-01-02', received: 135, sent: 125 },
            { date: '2024-01-03', received: 142, sent: 130 },
            { date: '2024-01-04', received: 156, sent: 142 },
            { date: '2024-01-05', received: 168, sent: 155 },
            { date: '2024-01-06', received: 145, sent: 135 },
            { date: '2024-01-07', received: 132, sent: 120 }
          ])
        }, 500)
      })
      
      commit('SET_TREND_DATA', data)
    } catch (error) {
      console.error('获取趋势数据失败:', error)
    }
  },
  
  enableEmergencyMode({ commit }) {
    // 模拟启用紧急模式
    console.log('启用紧急模式')
    commit('SET_AI_ENABLED', true)
  },
  
  async sendMessage({ commit }, { content, conversationId }) {
    const message = {
      id: Date.now(),
      content,
      sender: '用户',
      type: 'user',
      timestamp: new Date(),
      avatar: '/images/user-avatar.jpg'
    }
    
    commit('ADD_MESSAGE', message)
    
    // 模拟AI回复
    setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        content: '感谢您的消息，我正在为您处理...',
        sender: 'AI助手',
        type: 'assistant',
        timestamp: new Date(),
        avatar: '/images/ai-avatar.jpg'
      }
      commit('ADD_MESSAGE', aiMessage)
    }, 1000)
  },
  

  
  async setCurrentConversation({ commit }, conversationId) {
    commit('SET_CURRENT_CONVERSATION', conversationId)
  },
  
  async loadMessages({ commit }, { conversationId }) {
    commit('SET_MESSAGES_LOADING', true)
    try {
      await store.dispatch('chat/fetchMessages', conversationId)
    } finally {
      commit('SET_MESSAGES_LOADING', false)
    }
  },
  
  updateAISettings({ commit }, settings) {
    commit('SET_AI_SETTINGS', settings)
  },
  
  async markAsRead({ commit }, conversationId) {
    // 模拟标记为已读
    console.log('标记会话为已读:', conversationId)
  },
  
  async toggleAI({ commit }, { conversationId, enabled }) {
    commit('SET_AI_ENABLED', enabled)
  },
  
  async updateContactTags({ commit }, { conversationId, tags }) {
    // 模拟更新联系人标签
    console.log('更新联系人标签:', conversationId, tags)
  },
  
  async loadConversations({ commit }) {
    commit('SET_CONVERSATIONS_LOADING', true)
    try {
      await store.dispatch('chat/fetchConversations')
    } finally {
      commit('SET_CONVERSATIONS_LOADING', false)
    }
  },
  
  async loadAISettings({ commit }) {
    // 模拟加载AI设置
    console.log('加载AI设置')
  },
  
  async handleNewMessage({ commit }, data) {
    // 处理新消息
    console.log('处理新消息:', data)
  },
  
  async updateAIStatus({ commit }, data) {
    // 更新AI状态
    commit('SET_AI_ENABLED', data.enabled)
  },
  
  async updateTypingStatus({ commit }, data) {
    // 更新输入状态
    console.log('更新输入状态:', data)
  }
}

const getters = {
  currentMessages: state => state.messages,
  currentConversation: state => state.currentConversation,
  isAIEnabled: state => state.isAIEnabled,
  isLoading: state => state.isLoading,
  unreadCount: state => state.conversations.reduce((total, conv) => total + conv.unreadCount, 0),
  filteredConversations: (state) => (query, filter) => {
    let filtered = state.conversations
    
    if (query) {
      filtered = filtered.filter(conv => 
        conv.title.toLowerCase().includes(query.toLowerCase()) ||
        conv.lastMessage.toLowerCase().includes(query.toLowerCase())
      )
    }
    
    if (filter && filter !== 'all') {
      filtered = filtered.filter(conv => conv.status === filter)
    }
    
    return filtered
  },
  currentContactInfo: state => {
    if (!state.currentConversation) return null
    return {
      name: state.currentConversation.title || '未知联系人',
      avatar: '/images/default-avatar.jpg',
      status: state.currentConversation.status || 'offline'
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
