# 熵变智元AI销售助手 - 前端应用

基于Vue.js 3构建的现代化销售助手管理后台，提供完整的AI销售流程管理功能。

## 🚀 项目特性

### 核心功能模块
- **📊 主控面板** - 实时数据监控与快捷操作
- **💬 AI客服** - 聚合聊天管理与智能接管
- **🤖 AI销售** - SOP任务创建与自动化执行
- **🌟 朋友圈营销** - 定时发布与AI智能互动
- **📱 设备管理** - 微信账号状态监控与管理
- **💰 算力管理** - AI成本控制与配额管理

### 技术特色
- **Vue 3 + Composition API** - 现代化开发体验
- **Vuex 4** - 状态管理与数据流控制
- **Vue Router 4** - 路由管理与导航守卫
- **Element Plus** - 企业级UI组件库
- **WebSocket** - 实时数据推送
- **Chart.js** - 数据可视化图表
- **响应式设计** - 支持桌面、平板、手机多端

## 📁 项目结构

```
vue-frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口封装
│   │   └── index.js       # 统一API管理
│   ├── components/        # 可复用组件
│   │   ├── common/        # 通用组件
│   │   ├── layout/        # 布局组件
│   │   └── dashboard/     # 业务组件
│   ├── router/            # 路由配置
│   │   └── index.js       # 路由定义与守卫
│   ├── store/             # Vuex状态管理
│   │   ├── index.js       # 主store
│   │   └── modules/       # 分模块状态
│   ├── styles/            # 样式文件
│   │   ├── main.scss      # 主样式文件
│   │   └── variables.scss # 设计变量
│   ├── utils/             # 工具函数
│   │   └── websocket.js   # WebSocket管理
│   ├── views/             # 页面组件
│   │   ├── Dashboard.vue  # 主控面板
│   │   ├── ChatAggregation.vue # 聚合聊天
│   │   └── ...           # 其他页面
│   ├── App.vue           # 根组件
│   └── main.js           # 应用入口
├── package.json          # 项目配置
└── README.md            # 说明文档
```

## 🛠️ 开发环境搭建

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0
- Vue CLI >= 5.0.0

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd vue-frontend
```

2. **安装依赖**
```bash
npm install
```

3. **环境配置**
```bash
# 复制环境配置文件
cp .env.example .env.local

# 编辑配置文件
vim .env.local
```

4. **启动开发服务器**
```bash
npm run serve
```

5. **访问应用**
打开浏览器访问 `http://localhost:8080`

## 🔧 环境变量配置

在 `.env.local` 文件中配置以下变量：

```bash
# API基础URL
VUE_APP_API_BASE_URL=http://localhost:3000/api

# WebSocket服务URL
VUE_APP_WS_URL=ws://localhost:3000

# 应用标题
VUE_APP_TITLE=熵变智元AI销售助手

# 调试模式
VUE_APP_DEBUG=true
```

## 📊 状态管理架构

### Vuex模块划分

```javascript
store/
├── index.js              # 主store配置
└── modules/
    ├── app.js            # 应用全局状态
    ├── auth.js           # 用户认证状态
    ├── chat.js           # 聊天会话状态
    ├── devices.js        # 设备管理状态
    ├── sop.js            # SOP任务状态
    ├── moments.js        # 朋友圈营销状态
    ├── cost.js           # 算力成本状态
    ├── notifications.js  # 通知消息状态
    └── websocket.js      # WebSocket连接状态
```

### 状态使用示例

```vue
<template>
  <div>
    <div>在线设备: {{ onlineDevicesCount }}</div>
    <div>未读消息: {{ unreadMessagesCount }}</div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'

export default {
  setup() {
    const store = useStore()
    
    const onlineDevicesCount = computed(() => 
      store.getters['devices/onlineCount']
    )
    
    const unreadMessagesCount = computed(() => 
      store.getters.unreadMessagesCount
    )
    
    return {
      onlineDevicesCount,
      unreadMessagesCount
    }
  }
}
</script>
```

## 🌐 API接口使用

### 接口调用示例

```javascript
import { devicesAPI } from '@/api'

// 获取设备列表
const devices = await devicesAPI.getDevices({
  page: 1,
  size: 10,
  status: 'ONLINE'
})

// 添加设备
const newDevice = await devicesAPI.addDevice({
  name: '张经理微信',
  userId: 'user123'
})
```

### 错误处理

所有API调用都经过统一的错误处理，会自动：
- 显示错误通知
- 处理认证失败
- 重试网络错误
- 记录错误日志

## 📱 WebSocket实时通信

### 连接管理

```javascript
import wsManager from '@/utils/websocket'

// 连接WebSocket
await wsManager.connect()

// 发送消息
wsManager.emit('send_message', {
  conversationId: 'conv123',
  content: '你好'
})

// 监听事件
wsManager.on('new_message', (data) => {
  console.log('收到新消息:', data)
})
```

### 支持的事件

- `new_message` - 新消息到达
- `device_status_change` - 设备状态变化
- `ai_toggle` - AI接管状态切换
- `task_status_update` - 任务状态更新
- `cost_update` - 算力使用更新
- `system_alert` - 系统告警
- `manual_intervention_required` - 人工介入请求

## 🎨 样式开发指南

### 设计系统

项目采用统一的设计系统，基于CSS变量定义：

```scss
:root {
  // 主色调
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  
  // 语义色彩
  --success-500: #10b981;
  --warning-500: #f59e0b;
  --error-500: #ef4444;
  
  // 字体大小
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  
  // 间距
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
}
```

### 组件样式约定

```vue
<style lang="scss" scoped>
.component-name {
  // 组件根样式
  
  &__element {
    // BEM元素样式
  }
  
  &--modifier {
    // BEM修饰符样式
  }
  
  // 响应式适配
  @media (max-width: 768px) {
    // 移动端样式
  }
}
</style>
```

## 🔍 开发调试

### Chrome DevTools

推荐安装Vue开发者工具：
- [Vue.js devtools](https://chrome.google.com/webstore/detail/vuejs-devtools)

### 调试技巧

```javascript
// 开发环境下的调试输出
if (process.env.NODE_ENV === 'development') {
  console.log('调试信息:', data)
}

// 使用Vue DevTools调试状态
this.$store.state // 查看状态
this.$store.getters // 查看计算属性
```

## 📦 构建与部署

### 构建命令

```bash
# 开发环境构建
npm run serve

# 生产环境构建
npm run build

# 代码检查
npm run lint

# 代码格式化
npm run lint --fix
```

### 部署配置

```bash
# 构建生产版本
npm run build

# 生成的文件在dist目录
# 可以直接部署到静态服务器
```

### 环境变量

```bash
# 生产环境配置
VUE_APP_API_BASE_URL=https://api.example.com
VUE_APP_WS_URL=wss://ws.example.com
```

## 🧪 测试

### 单元测试

```bash
# 运行测试
npm run test:unit

# 测试覆盖率
npm run test:coverage
```

### E2E测试

```bash
# 运行端到端测试
npm run test:e2e
```

## 📈 性能优化

### 代码分割

```javascript
// 路由懒加载
const Dashboard = () => import('@/views/Dashboard.vue')

// 组件懒加载
const HeavyComponent = defineAsyncComponent(() =>
  import('@/components/HeavyComponent.vue')
)
```

### 构建优化

```javascript
// webpack配置优化
module.exports = {
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all'
      }
    }
  }
}
```

## 🤝 贡献指南

### 代码规范

- 使用ESLint进行代码检查
- 遵循Vue官方风格指南
- 组件命名使用PascalCase
- 文件命名使用kebab-case

### 提交规范

```bash
# 功能开发
git commit -m "feat: 添加设备管理功能"

# 问题修复
git commit -m "fix: 修复聊天消息显示问题"

# 文档更新
git commit -m "docs: 更新API文档"
```

## 📞 技术支持

如有问题，请联系：
- 邮箱: support@entropy-ai.com
- 技术群: 微信群二维码
- 文档: https://docs.entropy-ai.com

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

