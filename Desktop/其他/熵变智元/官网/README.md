# 熵变AI 官网

熵变智元(北京)科技有限公司的官方网站，基于 React + Vite + Tailwind CSS 构建。

## 项目特性

- 🚀 基于 Vite 的快速开发体验
- ⚛️ React 18 最新特性
- 🎨 Tailwind CSS 现代化样式
- 📱 响应式设计
- 🌐 中英文双语支持
- 🔐 用户认证系统
- 🔧 完整的开发工具链

## 技术栈

- **前端框架**: React 18
- **构建工具**: Vite
- **样式框架**: Tailwind CSS
- **图标库**: Lucide React
- **部署平台**: GitHub Pages + GitHub Actions
- **多语言**: 自定义 i18n 解决方案

## 核心能力展示

网站展示了熵变智元的五大核心能力：

1. **智能交互与对话系统** - 长程上下文、多模态理解、顾问式话术
2. **知识智能与RAG** - 动态知识库与检索增强生成
3. **客户数据智能与超个性化** - 画像与标签体系、闭环AB实验
4. **生成式AI与多模态创作** - 感知-决策-执行三层架构
5. **企业自动化与工作流编排** - 低代码编排，原生集成企业微信/飞书等生态

## 项目结构

```
官网/
├── src/
│   ├── components/          # React 组件
│   │   ├── Auth/           # 认证相关组件
│   │   ├── Features/       # 能力展示组件
│   │   ├── Footer/         # 页脚组件
│   │   ├── Header/         # 头部组件
│   │   ├── Hero/           # 主视觉组件
│   │   ├── ProductShowcase/# 产品展示组件
│   │   ├── Resources/      # 资源组件
│   │   └── Testimonials/   # 用户评价组件
│   ├── context/            # React Context
│   ├── i18n/               # 多语言配置
│   ├── App.jsx            # 主应用组件
│   ├── main.jsx           # 应用入口
│   └── index.css          # 全局样式
├── .github/workflows/      # GitHub Actions 工作流
├── index.html             # HTML 模板
├── package.json           # 项目配置
├── tailwind.config.js     # Tailwind 配置
├── vite.config.js         # Vite 配置
└── README.md              # 项目文档
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 部署

本项目已配置 GitHub Actions 自动部署到 GitHub Pages：

- 推送到 `main` 分支时自动触发构建和部署
- 访问地址：https://kehan857.github.io/official-website/

## 功能特性

### 多语言支持
- 默认中文显示
- 支持中英文切换
- 所有文案内容都已本地化

### 用户认证
- 本地注册/登录功能
- 会话持久化存储
- 用户状态管理

### 响应式设计
- 移动端友好
- 桌面端优化
- 现代化UI设计

## 许可证

MIT License 