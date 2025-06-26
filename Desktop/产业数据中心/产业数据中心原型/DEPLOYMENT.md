# 产业数据中心 - 部署说明

## 🚀 GitHub Pages 自动部署

本项目已配置 GitHub Actions 自动部署流程，每次推送到 `main` 分支时会自动构建并部署到 GitHub Pages。

### 🔧 部署配置

1. **GitHub Actions 工作流**: `.github/workflows/deploy.yml`
2. **构建输出目录**: `dist/`
3. **GitHub Pages URL**: `https://kehan857.github.io/Industrial-Data-Center/`

### 📋 部署步骤

#### 自动部署（推荐）
```bash
# 1. 提交代码到main分支
git add .
git commit -m "feat: 新功能更新"
git push origin main

# 2. GitHub Actions 会自动执行以下步骤：
# - 安装依赖 (npm ci)
# - 构建项目 (npm run build)
# - 部署到 GitHub Pages
```

#### 手动部署
```bash
# 1. 本地构建
npm run build

# 2. 预览构建结果
npm run preview

# 3. 推送到仓库触发自动部署
git push origin main
```

### ⚙️ 配置要求

#### GitHub 仓库设置
1. 进入仓库的 Settings > Pages
2. Source 选择 "GitHub Actions"
3. 确保启用 Actions 权限

#### 环境变量
- `NODE_ENV=production`: 生产环境构建
- `BASE_URL=/Industrial-Data-Center/`: GitHub Pages 子路径

### 🌐 访问地址

- **生产环境**: https://kehan857.github.io/Industrial-Data-Center/
- **开发环境**: http://localhost:3000/

### 📁 项目结构

```
产业数据中心原型/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions 部署配置
├── public/
│   └── 404.html               # GitHub Pages 404页面
├── src/
│   ├── views/                 # 页面组件
│   ├── router/                # 路由配置
│   └── ...
├── dist/                      # 构建输出目录
├── vite.config.ts            # Vite 配置（包含GitHub Pages路径）
└── package.json              # 项目依赖和脚本
```

### 🔍 故障排除

#### 常见问题

1. **404 错误**
   - 检查 `vite.config.ts` 中的 `base` 配置
   - 确保路由使用正确的基础路径

2. **资源加载失败**
   - 验证静态资源路径是否正确
   - 检查 `index.html` 中的资源引用

3. **构建失败**
   - 查看 GitHub Actions 日志
   - 本地执行 `npm run build` 验证

#### 调试命令

```bash
# 检查构建状态
npm run build

# 本地预览生产版本
npm run preview

# 类型检查
npm run type-check
```

### 📊 监控和日志

- **GitHub Actions**: 查看仓库的 Actions 标签页
- **部署状态**: Settings > Pages 查看部署状态
- **访问统计**: GitHub Insights 查看访问数据

### 🔄 更新流程

1. **功能开发**: 在本地开发新功能
2. **测试验证**: `npm run dev` 本地测试
3. **构建检查**: `npm run build` 确保构建成功
4. **提交代码**: 推送到 main 分支
5. **自动部署**: GitHub Actions 自动部署
6. **验证上线**: 访问生产地址验证功能

### 📞 支持联系

如有部署问题，请：
1. 查看 GitHub Actions 构建日志
2. 检查本文档的故障排除部分
3. 提交 Issue 到项目仓库 