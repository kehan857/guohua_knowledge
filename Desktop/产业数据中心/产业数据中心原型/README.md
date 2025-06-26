# 🧠 产业数据中心 (Industrial Data Center)

[![Deploy to GitHub Pages](https://github.com/kehan857/Industrial-Data-Center/actions/workflows/deploy.yml/badge.svg)](https://github.com/kehan857/Industrial-Data-Center/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vue 3](https://img.shields.io/badge/Vue-3.4-4FC08D?logo=vue.js)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript)](https://www.typescriptlang.org/)

天云聚合产业数据中心 - 构建智慧产业生态，赋能数字经济发展

## 🌟 在线预览

🔗 **[Live Demo](https://kehan857.github.io/Industrial-Data-Center/)**

## ✨ 功能特点

- 🎯 **产业链分析**: 交互式产业链图谱，可视化产业结构和关系
- 🗺️ **产业地图**: 地理分布热力图和区域产业分析
- 🏢 **企业资源**: 企业信息管理、产品展示、专家库
- 📊 **数据洞察**: 多维度数据分析和智能报告
- 💼 **需求匹配**: 需求发布、解决方案库、智能匹配
- 🎨 **现代化UI**: 响应式设计，支持深色/浅色主题切换
- 🔐 **权限管理**: 用户角色管理和权限控制

## 🛠️ 技术栈

### 核心技术
- **前端框架**: Vue 3.4 + Composition API
- **类型系统**: TypeScript 5.3
- **UI组件库**: Ant Design Vue 4.1
- **路由管理**: Vue Router 4.2
- **状态管理**: Pinia 2.1

### 数据可视化
- **图表库**: ECharts 5.4
- **Vue集成**: Vue-ECharts 6.6
- **数据处理**: D3.js 7.8

### 开发工具
- **构建工具**: Vite 5.0
- **样式预处理**: Less 4.2
- **HTTP客户端**: Axios 1.6

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

### GitHub Pages部署

```bash
npm run deploy
```

## 📁 项目结构

```
产业数据中心原型/
├── src/
│   ├── components/          # 公共组件
│   ├── views/              # 页面组件
│   │   ├── auth/           # 🔐 认证相关
│   │   ├── insights/       # 📊 数据洞察
│   │   │   ├── IndustryChain.vue    # 产业链图谱
│   │   │   ├── IndustryMap.vue      # 产业地图
│   │   │   └── EnterpriseMap.vue    # 企业地图
│   │   ├── resources/      # 📋 资源管理
│   │   │   ├── EnterpriseList.vue   # 企业库
│   │   │   ├── ProductList.vue      # 产品库
│   │   │   ├── ExpertList.vue       # 专家库
│   │   │   ├── DemandList.vue       # 需求库
│   │   │   └── SolutionList.vue     # 解决方案库
│   │   ├── opportunities/  # 🎯 商机发现
│   │   └── admin/          # ⚙️ 系统管理
│   ├── router/             # 路由配置
│   ├── styles/             # 样式文件
│   │   ├── themes/         # 主题配置
│   │   │   ├── light.less  # 浅色主题
│   │   │   └── dark.less   # 深色主题
│   │   └── global.less     # 全局样式
│   ├── layouts/            # 布局组件
│   └── main.ts            # 应用入口
├── .github/workflows/      # GitHub Actions
├── public/                 # 静态资源
└── dist/                  # 构建输出
```

## 🎯 功能模块

### 📊 数据洞察
- **产业概览**: 整体产业发展状况和趋势分析
- **产业链图谱**: 交互式产业链可视化，支持节点详情查看
- **产业地图**: 全国产业分布热力图和区域对比
- **企业地图**: 企业空间分布和集群分析

### 📋 资源管理
- **企业库**: 企业信息管理，支持搜索、筛选、详情查看
- **产品库**: 产品信息展示，分类管理
- **专家库**: 专家资源管理，专业领域分类
- **需求库**: 需求信息发布、搜索、匹配
- **解决方案库**: 解决方案展示和推荐

### 🎯 商机发现
- **供需地图**: 供需关系可视化分析
- **智能匹配**: 基于算法的需求解决方案匹配

### ⚙️ 系统管理
- **用户管理**: 用户信息管理和权限控制
- **角色管理**: 角色权限配置和分配

## 🎨 设计特色

### 主题系统
- 🌞 **浅色主题**: 清新明亮的视觉体验
- 🌙 **深色主题**: 护眼的深色模式
- 🎛️ **一键切换**: 实时主题切换，无需刷新

### 响应式设计
- 📱 **移动端优化**: 完美适配手机和平板
- 💻 **桌面端体验**: 充分利用大屏幕空间
- 🔄 **自适应布局**: 智能响应不同屏幕尺寸

### 交互体验
- ✨ **流畅动画**: 精心设计的过渡效果
- 🎯 **直观操作**: 符合用户习惯的交互设计
- 📊 **数据可视化**: 丰富的图表和可视化组件

## 🚀 部署说明

### GitHub Pages自动部署

项目配置了GitHub Actions，当代码推送到main分支时会自动构建和部署到GitHub Pages。

### 手动部署

1. 构建项目：
```bash
npm run build:gh-pages
```

2. 部署到GitHub Pages：
```bash
npm run deploy
```

## 🤝 贡献指南

### 开发规范
- 使用 TypeScript 进行类型检查
- 遵循 Vue 3 Composition API 最佳实践
- 统一的代码格式化和 ESLint 规则
- 组件命名采用 PascalCase
- 文件命名采用 kebab-case

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建或辅助工具变动

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下开源项目：
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Ant Design Vue](https://antdv.com/) - 企业级UI组件库
- [ECharts](https://echarts.apache.org/) - 强大的数据可视化库
- [Vite](https://vitejs.dev/) - 下一代前端构建工具

---

⭐ 如果这个项目对你有帮助，请给它一个Star！

## 项目特性

- 🎯 产业链图谱交互式可视化
- 🗺️ 产业地图地理分布展示  
- 🏢 企业资源管理(企业库、产品库、专家库、需求库、解决方案库)
- 💼 需求匹配和智能推荐
- 🎨 深色/浅色主题切换
- 📱 响应式设计适配各种设备
- 🔐 用户角色权限管理

## 技术栈

- Vue 3.4 + Composition API + TypeScript 5.3
- Ant Design Vue 4.1 + Vue Router 4.2 + Pinia 2.1
- ECharts 5.4 + D3.js 7.8 + Vite 5.0 + Less 4.2

## 部署状态

- **GitHub Pages**: https://kehan857.github.io/Industrial-Data-Center/
- **自动部署**: 推送到main分支自动触发构建和部署
- **更新时间**: 2025年1月26日

最新更新：添加了workflow_dispatch触发器，支持手动部署。 