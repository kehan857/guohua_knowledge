const state = {
  posts: [],
  isLoading: false
}

const mutations = {
  SET_POSTS(state, posts) {
    state.posts = posts
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading
  }
}

const actions = {
  async fetchPosts({ commit }) {
    commit('SET_LOADING', true)
    try {
      const posts = await new Promise(resolve => {
        setTimeout(() => {
          resolve([
            {
              id: 1,
              content: '我们最新的AI销售助手功能上线了！',
              status: 'published',
              publishedAt: '2024-01-15 10:30'
            },
            {
              id: 2,
              content: '感谢各位客户的支持！',
              status: 'scheduled',
              publishedAt: '2024-01-14 15:20'
            }
          ])
        }, 1000)
      })
      commit('SET_POSTS', posts)
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

const getters = {
  publishedPosts: state => state.posts.filter(p => p.status === 'published')
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
