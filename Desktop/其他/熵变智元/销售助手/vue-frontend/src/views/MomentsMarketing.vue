<template>
  <div class="moments-marketing">
    <div class="page-header">
      <h2>朋友圈营销</h2>
      <el-button type="primary" @click="createPost">
        <i class="el-icon-plus"></i>
        新建动态
      </el-button>
    </div>
    
    <div class="moments-content">
      <el-row :gutter="20">
        <el-col :span="16">
          <div class="post-editor">
            <h3>动态编辑</h3>
            <el-form :model="postForm" label-width="80px">
              <el-form-item label="内容">
                <el-input
                  v-model="postForm.content"
                  type="textarea"
                  :rows="6"
                  placeholder="输入动态内容..."
                />
              </el-form-item>
              <el-form-item label="图片">
                <el-upload
                  action="#"
                  list-type="picture-card"
                  :auto-upload="false"
                >
                  <i class="el-icon-plus"></i>
                </el-upload>
              </el-form-item>
              <el-form-item label="发布时间">
                <el-date-picker
                  v-model="postForm.scheduleTime"
                  type="datetime"
                  placeholder="选择发布时间"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="savePost">保存</el-button>
                <el-button @click="previewPost">预览</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="post-list">
            <h3>已发布动态</h3>
            <div 
              v-for="post in posts" 
              :key="post.id"
              class="post-item"
            >
              <div class="post-content">{{ post.content }}</div>
              <div class="post-meta">
                <span class="post-time">{{ post.publishedAt }}</span>
                <span class="post-status" :class="post.status">
                  {{ getStatusText(post.status) }}
                </span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'MomentsMarketing',
  setup() {
    const postForm = ref({
      content: '',
      scheduleTime: null
    })
    
    const posts = ref([
      {
        id: 1,
        content: '我们最新的AI销售助手功能上线了！快来体验一下吧！',
        publishedAt: '2024-01-15 10:30',
        status: 'published'
      },
      {
        id: 2,
        content: '感谢各位客户的支持，我们会继续努力提供更好的服务！',
        publishedAt: '2024-01-14 15:20',
        status: 'scheduled'
      }
    ])
    
    const getStatusText = (status) => {
      const texts = {
        published: '已发布',
        scheduled: '已预约',
        draft: '草稿'
      }
      return texts[status] || '未知'
    }
    
    const createPost = () => {
      postForm.value = {
        content: '',
        scheduleTime: null
      }
    }
    
    const savePost = () => {
      // 保存动态逻辑
    }
    
    const previewPost = () => {
      // 预览动态逻辑
    }
    
    return {
      postForm,
      posts,
      getStatusText,
      createPost,
      savePost,
      previewPost
    }
  }
}
</script>

<style lang="scss" scoped>
.moments-marketing {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  h2 {
    margin: 0;
    color: var(--text-color);
  }
}

.moments-content {
  .post-editor,
  .post-list {
    background: var(--card-bg);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    
    h3 {
      margin: 0 0 1rem 0;
      color: var(--text-color);
    }
  }
}

.post-item {
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
}

.post-content {
  margin-bottom: 0.75rem;
  line-height: 1.5;
  color: var(--text-color);
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.post-status {
  &.published {
    color: var(--success-color);
  }
  
  &.scheduled {
    color: var(--warning-color);
  }
  
  &.draft {
    color: var(--text-muted);
  }
}
</style>
