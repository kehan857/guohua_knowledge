# 熵变智元AI销售助手 - 后续开发规划和准备工作

## 🎯 当前完成状态

✅ **前端Vue.js应用** - 完整的组件化开发已完成  
✅ **UI/UX设计** - 现代化界面和交互体验  
✅ **技术架构** - 完整的前端技术栈和工程化配置  

## 📋 接下来的开发工作

### 阶段一：后端核心服务开发 (4-6周)

#### 1. 后端API服务开发 🚀
**技术栈**: Python + FastAPI + SQLAlchemy

```python
# 主要开发任务
├── 用户认证服务 (auth/)
│   ├── JWT token管理
│   ├── 用户注册/登录
│   └── 权限控制middleware
├── 设备管理服务 (devices/)
│   ├── 微信账号CRUD
│   ├── 设备状态同步
│   └── GeWe API集成
├── 聊天服务 (chat/)
│   ├── 消息收发管理
│   ├── 会话状态管理
│   └── AI接管控制
├── SOP任务服务 (sop/)
│   ├── 任务创建和管理
│   ├── 定时任务调度
│   └── 执行状态跟踪
└── 算力管理服务 (cost/)
    ├── 成本计算和统计
    ├── 用户配额管理
    └── 预算预警系统
```

#### 2. 数据库设计和实现 🗄️
**技术栈**: PostgreSQL + Elasticsearch + Redis

**核心数据表设计**:
```sql
-- 用户和组织
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 微信账号管理
CREATE TABLE wechat_accounts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    wxid VARCHAR(100) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    avatar TEXT,
    gewe_token_id VARCHAR(100),
    gewe_app_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'OFFLINE',
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SOP任务管理
CREATE TABLE sop_tasks (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    target_type VARCHAR(20), -- 'friend', 'group', 'tag'
    target_ids JSONB,
    workflow_config JSONB,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 算力成本管理
CREATE TABLE cost_ledgers (
    id UUID PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE,
    user_id UUID REFERENCES users(id),
    wechat_account_id UUID REFERENCES wechat_accounts(id),
    model_name VARCHAR(50),
    input_tokens INTEGER,
    output_tokens INTEGER,
    calculated_cost DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. WebSocket实时通信服务 🔌
**技术栈**: Socket.IO + Redis Adapter

```python
# 主要功能实现
├── WebSocket连接管理
├── 用户认证和房间管理
├── 实时消息推送
├── 设备状态变化通知
├── 任务执行状态更新
└── 系统告警推送
```

### 阶段二：外部服务集成 (2-3周)

#### 1. GeWe平台集成 🤖
```python
# GeWe API集成服务
class GeWeService:
    async def send_message(self, wxid: str, content: str)
    async def get_device_status(self, app_id: str)
    async def get_qr_code(self, app_id: str)
    async def handle_callback(self, data: dict)
    async def batch_operations(self, operations: list)
```

#### 2. FastGPT AI服务集成 🧠
```python
# AI服务集成
class AIService:
    async def process_message(self, message: str, context: dict)
    async def calculate_cost(self, tokens: dict, model: str)
    async def manage_workflows(self, workflow_id: str)
    async def batch_process(self, messages: list)
```

### 阶段三：基础设施和部署 (2-3周)

#### 1. 容器化部署 🐳
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./vue-frontend
    ports: ["80:80"]
  
  backend:
    build: ./fastapi-backend
    ports: ["8000:8000"]
    
  postgres:
    image: postgres:15
    
  redis:
    image: redis:7
    
  elasticsearch:
    image: elasticsearch:8.8.0
```

#### 2. CI/CD流水线 ⚙️
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Test Frontend
      - name: Test Backend  
      - name: Build Images
      - name: Deploy to Server
```

## 🛠️ 外部准备工作清单

### 1. 服务器和基础设施 🖥️

#### 推荐配置:
```bash
# 生产环境服务器配置
主服务器:
  - CPU: 8核心
  - 内存: 32GB
  - 存储: 500GB SSD
  - 带宽: 100Mbps
  - 操作系统: Ubuntu 22.04 LTS

数据库服务器:
  - CPU: 4核心
  - 内存: 16GB  
  - 存储: 1TB SSD
  - 数据库: PostgreSQL 15 + Redis 7 + Elasticsearch 8

# 开发/测试环境
开发服务器:
  - CPU: 4核心
  - 内存: 16GB
  - 存储: 200GB SSD
```

#### 云服务提供商选择:
- **阿里云**: ECS + RDS + Redis + OSS
- **腾讯云**: CVM + TencentDB + TcaplusDB  
- **华为云**: ECS + RDS + DCS + OBS
- **AWS**: EC2 + RDS + ElastiCache + S3

### 2. 域名和SSL证书 🌐

```bash
# 需要准备的域名
主域名: your-company.com
API子域名: api.your-company.com  
管理后台: admin.your-company.com
WebSocket: ws.your-company.com

# SSL证书
Let's Encrypt免费证书 或 付费证书
```

### 3. GeWe平台接入准备 🔗

#### 需要从GeWe获取:
```json
{
  "api_endpoint": "https://gewe.cn/api/v1",
  "token_id": "你的GeWe Token ID",
  "callback_url": "https://api.your-company.com/callbacks/gewe",
  "rate_limits": {
    "messages_per_minute": 40,
    "api_calls_per_hour": 1000
  }
}
```

#### GeWe接入流程:
1. **注册GeWe账号** - 在gewe.cn注册企业账号
2. **实名认证** - 完成企业实名认证
3. **购买服务** - 根据需要的微信账号数量购买套餐
4. **获取Token** - 获取API调用的Token ID
5. **配置回调** - 设置消息回调的URL地址
6. **测试连接** - 使用测试账号验证API连接

### 4. FastGPT AI服务准备 🤖

#### 需要配置的信息:
```json
{
  "fastgpt_endpoint": "https://your-fastgpt-instance.com/api/v1",
  "api_key": "your-fastgpt-api-key",
  "default_model": "doubao-pro-32k",
  "workflows": {
    "sales_assistant": "workflow-id-1",
    "customer_service": "workflow-id-2"
  },
  "pricing": {
    "doubao-pro-32k": {
      "input_price_per_1k": 0.008,
      "output_price_per_1k": 0.024
    }
  }
}
```

#### FastGPT接入流程:
1. **部署FastGPT实例** - 自建或使用云服务
2. **创建知识库** - 导入产品文档和FAQ
3. **设计工作流** - 配置AI对话流程
4. **获取API密钥** - 用于后端调用
5. **测试工作流** - 验证AI回复质量

### 5. 数据库初始化脚本 📊

```sql
-- 数据库初始化
-- 1. 创建数据库
CREATE DATABASE entropy_ai_sales;

-- 2. 创建用户和权限
CREATE USER entropy_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE entropy_ai_sales TO entropy_user;

-- 3. 安装扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 4. 执行表结构创建脚本
\i create_tables.sql

-- 5. 插入初始数据
\i insert_initial_data.sql
```

### 6. 环境变量配置 ⚙️

```bash
# .env.production
# 数据库配置
DATABASE_URL=postgresql://entropy_user:password@localhost:5432/entropy_ai_sales
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200

# GeWe配置
GEWE_API_ENDPOINT=https://gewe.cn/api/v1
GEWE_TOKEN_ID=your_token_id
GEWE_CALLBACK_SECRET=your_callback_secret

# FastGPT配置  
FASTGPT_API_ENDPOINT=https://your-fastgpt.com/api/v1
FASTGPT_API_KEY=your_api_key

# JWT配置
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# 文件存储
UPLOAD_PATH=/var/uploads
MAX_FILE_SIZE=10485760

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@your-company.com
SMTP_PASSWORD=your_email_password
```

### 7. 监控和日志系统 📈

#### 推荐工具:
```yaml
# 监控栈
监控工具:
  - Prometheus + Grafana (系统监控)
  - Sentry (错误监控)
  - ELK Stack (日志分析)

# 日志配置
日志等级: INFO
日志格式: JSON
日志轮转: 按天
保留时间: 30天

# 告警规则
- CPU使用率 > 80%
- 内存使用率 > 85%  
- 磁盘使用率 > 90%
- API响应时间 > 5秒
- 错误率 > 5%
```

## 📅 开发时间表

### 第1-2周: 环境准备和基础搭建
- [ ] 服务器采购和配置
- [ ] 域名注册和SSL证书申请
- [ ] GeWe和FastGPT账号申请
- [ ] 数据库设计和创建
- [ ] 基础后端项目架构搭建

### 第3-4周: 核心API开发
- [ ] 用户认证服务开发
- [ ] 设备管理API开发
- [ ] GeWe集成开发
- [ ] 基础WebSocket服务

### 第5-6周: 业务功能开发
- [ ] 聊天服务API开发
- [ ] SOP任务管理开发
- [ ] FastGPT集成开发
- [ ] 算力管理API开发

### 第7-8周: 集成测试和优化
- [ ] 前后端联调测试
- [ ] 性能优化和压力测试
- [ ] 安全加固和漏洞修复
- [ ] 监控和日志系统部署

### 第9-10周: 部署上线
- [ ] 生产环境部署
- [ ] 数据迁移和备份
- [ ] 用户培训和文档
- [ ] 正式上线运营

## 🚨 关键依赖和风险点

### 1. GeWe平台稳定性 ⚠️
**风险**: GeWe服务可能不稳定，影响微信账号管理
**缓解措施**:
- 实现完整的错误处理和重试机制
- 建立多重备份和故障转移方案
- 与GeWe保持密切沟通，获取技术支持

### 2. 微信风控政策 ⚠️
**风险**: 微信可能加强对自动化行为的检测
**缓解措施**:
- 严格按照GeWe的使用建议配置参数
- 实现智能化的频率控制和行为模拟
- 建立风控预警和应对机制

### 3. AI成本控制 💰
**风险**: AI API调用成本可能超出预算
**缓解措施**:
- 实现精细化的成本监控和预警
- 设置用户配额和调用限制
- 优化AI工作流，减少不必要的调用

## 🎯 成功交付标准

### 功能完整性 ✅
- [ ] 所有前端功能正常工作
- [ ] 后端API完整实现
- [ ] GeWe和FastGPT正常集成
- [ ] 实时通信稳定运行

### 性能指标 📊
- [ ] API响应时间 < 2秒
- [ ] 页面加载时间 < 3秒
- [ ] 系统可用性 > 99%
- [ ] 并发用户数 > 100

### 安全标准 🔒
- [ ] 通过安全扫描测试
- [ ] 数据加密传输和存储
- [ ] 用户权限控制完善
- [ ] 审计日志完整

## 🚀 立即开始

1. **确认技术方案** - 审阅本文档并确认技术选型
2. **采购服务器** - 根据配置建议采购云服务器
3. **申请服务账号** - 注册GeWe和FastGPT账号
4. **准备开发团队** - 组建后端开发团队
5. **启动项目** - 按照时间表开始开发工作

**下一步**: 我将开始后端API服务的架构设计和核心代码实现！🎉

