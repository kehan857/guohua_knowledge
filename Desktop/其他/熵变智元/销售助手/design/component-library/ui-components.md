# 销售助手后台UI组件库设计

## 设计系统概述

### 设计原则
- **一致性**: 统一的视觉语言和交互模式
- **效率性**: 符合销售人员工作习惯的高效操作
- **可访问性**: 支持键盘导航和屏幕阅读器
- **响应式**: 适配桌面、平板、手机多端

### 色彩系统
```css
:root {
  /* 主色调 */
  --primary-50: #eff6ff;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;
  
  /* 语义色彩 */
  --success-500: #10b981;
  --warning-500: #f59e0b;
  --error-500: #ef4444;
  --info-500: #06b6d4;
  
  /* 中性色 */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-500: #6b7280;
  --gray-900: #111827;
}
```

## 基础组件

### 1. 按钮组件 (Button)

#### 主要按钮
```html
<!-- 主要操作按钮 -->
<button class="btn btn-primary">
  创建任务
</button>

<!-- 次要操作按钮 -->
<button class="btn btn-secondary">
  取消
</button>

<!-- 危险操作按钮 -->
<button class="btn btn-danger">
  删除
</button>

<!-- 图标按钮 -->
<button class="btn btn-icon">
  <svg class="icon">...</svg>
</button>
```

#### 状态变体
- **默认状态**: 正常可点击
- **悬停状态**: 颜色加深，轻微阴影
- **激活状态**: 按下效果
- **禁用状态**: 灰色，不可点击
- **加载状态**: 显示旋转加载图标

### 2. 状态指示器 (StatusIndicator)

```html
<!-- 在线状态 -->
<div class="status-indicator status-online">
  <span class="status-dot"></span>
  <span class="status-text">在线</span>
</div>

<!-- 离线状态 -->
<div class="status-indicator status-offline">
  <span class="status-dot"></span>
  <span class="status-text">离线</span>
</div>

<!-- 等待状态 -->
<div class="status-indicator status-pending">
  <span class="status-dot"></span>
  <span class="status-text">等待扫码</span>
</div>

<!-- 异常状态 -->
<div class="status-indicator status-error">
  <span class="status-dot"></span>
  <span class="status-text">异常</span>
</div>
```

### 3. 数据卡片 (DataCard)

```html
<div class="data-card">
  <div class="data-card-header">
    <h3 class="data-card-title">在线账号数</h3>
    <svg class="data-card-icon">...</svg>
  </div>
  <div class="data-card-content">
    <div class="data-card-value">8/12</div>
    <div class="data-card-trend positive">
      <svg class="trend-icon">↗</svg>
      <span>+2.3%</span>
    </div>
  </div>
  <div class="data-card-footer">
    <span class="data-card-subtitle">实时状态</span>
  </div>
</div>
```

### 4. 表格组件 (DataTable)

```html
<div class="data-table-container">
  <table class="data-table">
    <thead class="data-table-header">
      <tr>
        <th class="sortable">微信信息</th>
        <th class="sortable">归属员工</th>
        <th>状态</th>
        <th>上线时长</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody class="data-table-body">
      <tr class="data-table-row">
        <td class="data-table-cell">
          <div class="user-info">
            <img src="avatar.jpg" class="user-avatar" alt="头像">
            <div class="user-details">
              <div class="user-name">张经理</div>
              <div class="user-id">zhangjl_001</div>
            </div>
          </div>
        </td>
        <td class="data-table-cell">张三</td>
        <td class="data-table-cell">
          <div class="status-indicator status-online">
            <span class="status-dot"></span>
            <span class="status-text">在线</span>
          </div>
        </td>
        <td class="data-table-cell">2天3小时</td>
        <td class="data-table-cell">
          <div class="action-buttons">
            <button class="btn btn-sm btn-secondary">查看</button>
            <button class="btn btn-sm btn-danger">下线</button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

## 业务组件

### 5. 聊天消息组件 (ChatMessage)

```html
<!-- 接收消息 -->
<div class="chat-message chat-message-received">
  <div class="message-avatar">
    <img src="user-avatar.jpg" alt="用户头像">
  </div>
  <div class="message-content">
    <div class="message-header">
      <span class="message-sender">张三</span>
      <span class="message-time">14:30</span>
    </div>
    <div class="message-body">
      <p>你们这个产品的价格是多少？</p>
    </div>
  </div>
</div>

<!-- 发送消息 -->
<div class="chat-message chat-message-sent">
  <div class="message-content">
    <div class="message-header">
      <span class="message-sender">AI助手</span>
      <span class="message-time">14:31</span>
    </div>
    <div class="message-body">
      <p>感谢您的咨询！我们的产品有多个版本...</p>
    </div>
    <div class="message-status">
      <svg class="icon-sent">✓</svg>
    </div>
  </div>
</div>

<!-- 系统提醒消息 -->
<div class="chat-message chat-message-system">
  <div class="message-content">
    <div class="system-alert">
      ⚠️ AI检测到价格敏感话题，建议人工介入
    </div>
  </div>
</div>
```

### 6. AI控制开关 (AIToggle)

```html
<div class="ai-toggle-container">
  <div class="ai-toggle-header">
    <h4>AI接管状态</h4>
  </div>
  <div class="ai-toggle-control">
    <label class="toggle-switch">
      <input type="checkbox" checked class="toggle-input">
      <span class="toggle-slider">
        <span class="toggle-label active">AI接管中</span>
        <span class="toggle-label inactive">人工模式</span>
      </span>
    </label>
  </div>
  <div class="ai-toggle-info">
    <div class="toggle-status active">
      <svg class="status-icon">🤖</svg>
      <span>智能回复已启用</span>
    </div>
  </div>
</div>
```

### 7. 任务时间线 (TaskTimeline)

```html
<div class="task-timeline">
  <div class="timeline-header">
    <h4>SOP执行流程</h4>
    <button class="btn btn-sm btn-primary">添加步骤</button>
  </div>
  
  <div class="timeline-container">
    <div class="timeline-item">
      <div class="timeline-marker start">
        <svg class="timeline-icon">🚀</svg>
      </div>
      <div class="timeline-content">
        <div class="timeline-title">任务开始</div>
        <div class="timeline-time">立即执行</div>
      </div>
    </div>
    
    <div class="timeline-item">
      <div class="timeline-marker">
        <span class="step-number">1</span>
      </div>
      <div class="timeline-content">
        <div class="timeline-card">
          <div class="card-header">
            <h5>欢迎问候</h5>
            <button class="btn btn-sm btn-ghost">编辑</button>
          </div>
          <div class="card-body">
            <div class="timeline-detail">
              <span class="detail-label">⏰ 时间:</span>
              <span>任务开始后立即执行</span>
            </div>
            <div class="timeline-detail">
              <span class="detail-label">📝 内容:</span>
              <span>"欢迎加入我们的产品讨论群..."</span>
            </div>
            <div class="timeline-detail">
              <span class="detail-label">🎯 条件:</span>
              <span>无前置条件</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="timeline-item">
      <div class="timeline-marker">
        <span class="step-number">2</span>
      </div>
      <div class="timeline-content">
        <div class="timeline-card">
          <div class="card-header">
            <h5>产品介绍</h5>
            <button class="btn btn-sm btn-ghost">编辑</button>
          </div>
          <div class="card-body">
            <div class="timeline-detail">
              <span class="detail-label">⏰ 时间:</span>
              <span>任务开始后1天的09:30执行</span>
            </div>
            <div class="timeline-detail">
              <span class="detail-label">📝 内容:</span>
              <span>"我们的产品特色介绍.pdf"</span>
            </div>
            <div class="timeline-detail">
              <span class="detail-label">🎯 条件:</span>
              <span>如果群内有新成员发言</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 8. 进度条组件 (ProgressBar)

```html
<!-- 基础进度条 -->
<div class="progress-bar">
  <div class="progress-track">
    <div class="progress-fill" style="width: 68%"></div>
  </div>
  <div class="progress-text">68%</div>
</div>

<!-- 带状态的进度条 -->
<div class="progress-bar progress-success">
  <div class="progress-track">
    <div class="progress-fill" style="width: 85%"></div>
  </div>
  <div class="progress-text">85% 正常</div>
</div>

<!-- 预算使用进度条 -->
<div class="budget-progress">
  <div class="budget-header">
    <span class="budget-label">本月算力使用</span>
    <span class="budget-value">$125.67 / $200.00</span>
  </div>
  <div class="progress-bar progress-warning">
    <div class="progress-track">
      <div class="progress-fill" style="width: 62.8%"></div>
    </div>
    <div class="progress-text">62.8%</div>
  </div>
  <div class="budget-footer">
    <span class="budget-remaining">剩余: $74.33</span>
    <span class="budget-days">距月底: 10天</span>
  </div>
</div>
```

## 表单组件

### 9. 输入框组件 (Input)

```html
<!-- 基础输入框 -->
<div class="form-group">
  <label class="form-label">任务名称 *</label>
  <input type="text" class="form-input" placeholder="请输入任务名称">
  <div class="form-help">建议使用有意义的描述性名称</div>
</div>

<!-- 带图标输入框 -->
<div class="form-group">
  <label class="form-label">搜索</label>
  <div class="input-group">
    <div class="input-icon">
      <svg class="icon-search">🔍</svg>
    </div>
    <input type="text" class="form-input" placeholder="搜索账号/昵称...">
  </div>
</div>

<!-- 错误状态输入框 -->
<div class="form-group has-error">
  <label class="form-label">配额金额 *</label>
  <input type="number" class="form-input" value="abc">
  <div class="form-error">请输入有效的数字</div>
</div>
```

### 10. 选择器组件 (Select)

```html
<div class="form-group">
  <label class="form-label">执行账号 *</label>
  <div class="select-wrapper">
    <select class="form-select">
      <option value="">请选择执行账号</option>
      <option value="account1">张经理微信 (zhangjl_001)</option>
      <option value="account2">李销售微信 (lixs_002)</option>
    </select>
    <div class="select-arrow">
      <svg class="icon-chevron-down">▼</svg>
    </div>
  </div>
</div>
```

## 导航组件

### 11. 标签页组件 (Tabs)

```html
<div class="tabs-container">
  <div class="tabs-header">
    <button class="tab-button active" data-tab="moments">📅 定时发朋友圈</button>
    <button class="tab-button" data-tab="ai-interaction">🤖 AI智能互动</button>
    <button class="tab-button" data-tab="analytics">📊 数据分析</button>
  </div>
  
  <div class="tabs-content">
    <div class="tab-panel active" id="moments">
      <!-- 定时发朋友圈内容 -->
    </div>
    <div class="tab-panel" id="ai-interaction">
      <!-- AI智能互动内容 -->
    </div>
    <div class="tab-panel" id="analytics">
      <!-- 数据分析内容 -->
    </div>
  </div>
</div>
```

### 12. 面包屑导航 (Breadcrumb)

```html
<nav class="breadcrumb">
  <ol class="breadcrumb-list">
    <li class="breadcrumb-item">
      <a href="/dashboard" class="breadcrumb-link">首页</a>
    </li>
    <li class="breadcrumb-separator">/</li>
    <li class="breadcrumb-item">
      <a href="/ai-sales" class="breadcrumb-link">AI销售</a>
    </li>
    <li class="breadcrumb-separator">/</li>
    <li class="breadcrumb-item active">
      <span class="breadcrumb-current">SOP任务管理</span>
    </li>
  </ol>
</nav>
```

## 反馈组件

### 13. 模态框组件 (Modal)

```html
<div class="modal-overlay">
  <div class="modal-container">
    <div class="modal-header">
      <h3 class="modal-title">创建SOP任务</h3>
      <button class="modal-close" aria-label="关闭">
        <svg class="icon-close">✕</svg>
      </button>
    </div>
    
    <div class="modal-body">
      <!-- 模态框内容 -->
    </div>
    
    <div class="modal-footer">
      <button class="btn btn-secondary">取消</button>
      <button class="btn btn-primary">确认</button>
    </div>
  </div>
</div>
```

### 14. 通知组件 (Notification)

```html
<!-- 成功通知 -->
<div class="notification notification-success">
  <div class="notification-icon">
    <svg class="icon-check">✓</svg>
  </div>
  <div class="notification-content">
    <div class="notification-title">任务创建成功</div>
    <div class="notification-message">SOP任务已开始执行</div>
  </div>
  <button class="notification-close">
    <svg class="icon-close">✕</svg>
  </button>
</div>

<!-- 错误通知 -->
<div class="notification notification-error">
  <div class="notification-icon">
    <svg class="icon-error">!</svg>
  </div>
  <div class="notification-content">
    <div class="notification-title">连接失败</div>
    <div class="notification-message">无法连接到微信账号，请检查网络</div>
  </div>
  <button class="notification-close">
    <svg class="icon-close">✕</svg>
  </button>
</div>
```

### 15. 加载状态组件 (Loading)

```html
<!-- 页面加载 -->
<div class="loading-overlay">
  <div class="loading-spinner">
    <div class="spinner-ring"></div>
  </div>
  <div class="loading-text">正在加载...</div>
</div>

<!-- 按钮加载 -->
<button class="btn btn-primary loading">
  <div class="btn-spinner"></div>
  <span>处理中...</span>
</button>

<!-- 表格加载 -->
<div class="table-loading">
  <div class="skeleton-rows">
    <div class="skeleton-row">
      <div class="skeleton-cell"></div>
      <div class="skeleton-cell"></div>
      <div class="skeleton-cell"></div>
    </div>
  </div>
</div>
```

## 图表组件

### 16. 简单图表组件 (SimpleChart)

```html
<!-- 趋势图容器 -->
<div class="chart-container">
  <div class="chart-header">
    <h4 class="chart-title">消息量趋势</h4>
    <div class="chart-controls">
      <button class="btn btn-sm btn-ghost active">7天</button>
      <button class="btn btn-sm btn-ghost">30天</button>
    </div>
  </div>
  <div class="chart-content">
    <canvas id="messageChart" class="chart-canvas"></canvas>
  </div>
  <div class="chart-legend">
    <div class="legend-item">
      <span class="legend-color" style="background: #3b82f6"></span>
      <span class="legend-label">发送消息</span>
    </div>
    <div class="legend-item">
      <span class="legend-color" style="background: #10b981"></span>
      <span class="legend-label">接收消息</span>
    </div>
  </div>
</div>
```

## 工具提示组件

### 17. 提示框组件 (Tooltip)

```html
<button class="btn btn-icon" data-tooltip="获取登录二维码">
  <svg class="icon-qr">📱</svg>
</button>

<div class="tooltip">
  <div class="tooltip-content">
    获取登录二维码
  </div>
  <div class="tooltip-arrow"></div>
</div>
```

## 响应式断点

```css
/* 移动端 */
@media (max-width: 768px) {
  .data-table {
    display: block;
    overflow-x: auto;
  }
  
  .modal-container {
    margin: 1rem;
    width: calc(100% - 2rem);
  }
}

/* 平板端 */
@media (min-width: 769px) and (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: 280px 1fr;
  }
}

/* 桌面端 */
@media (min-width: 1025px) {
  .chat-layout {
    grid-template-columns: 320px 1fr 280px;
  }
}
```

## 组件使用指南

### 命名规范
- 使用BEM命名法：`block__element--modifier`
- 组件名使用PascalCase：`DataTable`
- CSS类名使用kebab-case：`data-table`

### 状态管理
- 使用CSS类切换状态：`.active`, `.disabled`, `.loading`
- 通过data属性传递配置：`data-tooltip`, `data-tab`

### 可访问性
- 所有交互元素支持键盘导航
- 提供aria-label和role属性
- 确保色彩对比度符合WCAG标准

