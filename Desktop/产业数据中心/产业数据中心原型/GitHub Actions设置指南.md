# GitHub Actions 和 Pages 设置指南

## 一、GitHub Pages 设置

### 1. 进入仓库设置
1. 打开您的GitHub仓库：https://github.com/kehan857/Industrial-Data-Center
2. 点击仓库页面右上角的 **Settings** 标签

### 2. 配置 Pages 设置
1. 在左侧菜单中找到并点击 **Pages**
2. 在 **Source** 部分：
   - 选择 **Deploy from a branch**
   - **Branch** 选择 `gh-pages`
   - **Folder** 选择 `/ (root)`
3. 点击 **Save** 保存设置

### 3. 等待部署
- 设置保存后，GitHub会自动创建 `gh-pages` 分支
- 首次部署可能需要几分钟时间

## 二、GitHub Actions 设置

### 1. 启用 Actions
1. 在仓库页面点击 **Actions** 标签
2. 如果Actions被禁用，点击 **I understand my workflows, go ahead and enable them**

### 2. 检查工作流权限
1. 进入 **Settings** → **Actions** → **General**
2. 在 **Workflow permissions** 部分：
   - 选择 **Read and write permissions**
   - 勾选 **Allow GitHub Actions to create and approve pull requests**
3. 点击 **Save** 保存

### 3. 检查 GITHUB_TOKEN 权限
1. 确保在 **Actions permissions** 中：
   - **Allow all actions and reusable workflows** 被选中
   - 或者至少允许 **Allow actions created by GitHub** 和 **Allow actions by Marketplace verified creators**

## 三、触发部署

### 方法一：推送代码触发
```bash
# 任何推送到main分支的代码都会触发自动部署
git add .
git commit -m "触发GitHub Pages部署"
git push origin main
```

### 方法二：手动触发
1. 进入 **Actions** 标签
2. 选择 **Deploy to GitHub Pages** 工作流
3. 点击 **Run workflow** 按钮
4. 选择 `main` 分支
5. 点击 **Run workflow**

## 四、验证部署状态

### 1. 检查 Actions 执行状态
1. 进入 **Actions** 标签
2. 查看最新的工作流运行状态
3. 如果有错误，点击失败的工作流查看详细日志

### 2. 访问部署的网站
- 部署成功后，网站将在以下地址可用：
- **https://kehan857.github.io/Industrial-Data-Center/**

## 五、常见问题排查

### 问题1：Actions 页面显示 404
**解决方案：**
1. 确保仓库是公开的（Public）
2. 或者如果是私有仓库，确保您有 GitHub Pro/Team/Enterprise 账户

### 问题2：工作流权限不足
**错误信息：** `Permission denied` 或 `GITHUB_TOKEN` 相关错误
**解决方案：**
1. 进入 Settings → Actions → General
2. 设置 Workflow permissions 为 "Read and write permissions"

### 问题3：gh-pages 分支不存在
**解决方案：**
1. 工作流会自动创建 gh-pages 分支
2. 如果没有创建，检查 Actions 执行日志
3. 确保 peaceiris/actions-gh-pages@v3 action 有正确的权限

### 问题4：构建失败
**常见原因：**
- Node.js 版本不兼容
- 依赖安装失败
- TypeScript 编译错误
- 环境变量配置问题

**解决方案：**
1. 检查 package.json 中的 engines 配置
2. 确保所有依赖都在 package.json 中正确声明
3. 修复任何 TypeScript 或 ESLint 错误

## 六、当前项目状态

✅ **已完成的配置：**
- [x] GitHub Actions 工作流文件 (`.github/workflows/deploy.yml`)
- [x] Vite 配置支持 GitHub Pages (`base: '/Industrial-Data-Center/'`)
- [x] package.json 构建脚本 (`build:gh-pages`, `deploy`)
- [x] 编译错误修复
- [x] 本地构建测试通过

🔄 **需要手动完成的设置：**
- [ ] GitHub Pages 源设置为 gh-pages 分支
- [ ] GitHub Actions 权限配置
- [ ] 首次工作流触发

## 七、部署验证清单

部署完成后，请验证以下功能：

### 页面功能验证
- [ ] 首页正常加载
- [ ] 路由跳转正常
- [ ] 深色/浅色主题切换
- [ ] 产业链图谱交互功能
- [ ] 产业地图可视化
- [ ] 企业资源管理页面
- [ ] 需求库搜索和筛选
- [ ] 响应式设计适配

### 性能验证
- [ ] 页面加载速度 < 3秒
- [ ] 图表渲染正常
- [ ] 移动端适配良好
- [ ] 无控制台错误

如果遇到任何问题，请检查：
1. GitHub Actions 执行日志
2. 浏览器开发者工具控制台
3. 网络请求状态

---

**项目在线地址：** https://kehan857.github.io/Industrial-Data-Center/
**GitHub仓库：** https://github.com/kehan857/Industrial-Data-Center 