# DataClean API

数据清洗 API 服务 — 去重、标准化、验证，一键全流程。支持精确去重、模糊匹配、电话/邮箱/地址标准化，按量付费。

**在线体验：** https://dataclean-x4jc.onrender.com

## 功能

### 数据清洗
- **精确去重** — MD5 哈希比对，指定字段组合匹配，毫秒级处理
- **模糊去重** — SimHash + Levenshtein 算法，识别相似记录
- **数据标准化** — 电话格式化（E.164）、邮箱小写化、地址规范化、日期统一
- **邮箱验证** — 语法检查 + 域名 MX 记录查询
- **一键全流程** — 标准化 + 去重 + 验证一条龙

### 用户系统
- 邮箱注册/登录（SHA256 密码哈希）
- Auth Token 认证（48 位安全随机 Token）
- API Key 管理（创建/查看/吊销，`dk_live_` 前缀）
- 额度系统（免费 1,000 次，付费最高 200,000 次/月）
- LemonSqueezy 支付集成

### 前端控制台
- SaaS 风格落地页（功能展示、代码示例、定价表）
- 用户仪表板（概览统计、API Key 管理、交互式 Playground、计费管理）
- 深色主题，响应式布局

## 技术栈

| 组件 | 技术 |
|------|------|
| API 框架 | FastAPI |
| 数据库 | Supabase (PostgreSQL) |
| 缓存/限流 | Upstash Redis |
| 支付 | LemonSqueezy |
| 部署 | Render (Docker) |
| 前端 | HTML + CSS + 原生 JS |

## 快速开始

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/lbl1988/DataClean.git
cd DataClean

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 Supabase、Redis、LemonSqueezy 配置

# 5. 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 6. 打开浏览器
# 首页:     http://localhost:8000
# 控制台:   http://localhost:8000/dashboard
# API文档:  http://localhost:8000/docs
```

### 数据库初始化

在 Supabase SQL Editor 中执行：
1. `sql/schema.sql` — 基础表结构
2. `sql/schema_v2.sql` — 用户系统扩展表
3. 补全字段（如已有旧表）：

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;
NOTIFY pgrst, 'reload schema';
```

## API 接口

### 认证（无需 API Key）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/auth/register` | POST | 用户注册（email, password, name） |
| `/v1/auth/login` | POST | 用户登录，返回 auth token |
| `/v1/auth/me` | GET | 获取当前用户信息（?token=xxx） |

### API Key 管理（需要 Auth Token）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/keys` | GET | 列出所有 API Key |
| `/v1/keys` | POST | 创建新 API Key |
| `/v1/keys/{id}` | DELETE | 吊销 API Key |

### 计费管理（需要 Auth Token）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/billing/checkout` | GET | 创建 LemonSqueezy 结账并返回支付链接（`?plan=starter\|pro\|business&token=xxx`） |
| `/v1/billing/balance` | GET | 查询当前用户额度与套餐（`?token=xxx`） |

### 数据清洗（需要 API Key）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/dedup` | POST | 去重（exact / fuzzy） |
| `/v1/standardize` | POST | 数据标准化 |
| `/v1/clean` | POST | 一键全流程清洗 |

### 其他

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api-info` | GET | 服务信息与端点目录 |
| `/debug` | GET | 调试信息（环境/数据库状态） |
| `/webhook/lemonsqueezy` | POST | LemonSqueezy 支付回调 |

## 鉴权

### Auth Token（用户操作）

通过 query 参数传递：
```
GET /v1/auth/me?token=your_auth_token
POST /v1/keys?token=your_auth_token
```

### API Key（数据清洗）

通过 Header 传递：
```bash
curl -X POST https://dataclean-x4jc.onrender.com/v1/dedup \
  -H "X-API-Key: dk_live_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"records": [...], "match_fields": ["email"], "match_mode": "exact"}'
```

## 使用示例

### Python

```python
import requests

API_KEY = "dk_live_your_api_key"
BASE = "https://dataclean-x4jc.onrender.com"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# 去重
data = {
    "records": [
        {"id": 1, "email": "A@Test.com ", "phone": "13800138000"},
        {"id": 2, "email": "a@test.com", "phone": "13800138000"},
        {"id": 3, "email": "b@test.com", "phone": "13900139000"},
    ],
    "match_fields": ["email", "phone"],
    "match_mode": "exact"
}
resp = requests.post(f"{BASE}/v1/dedup", json=data, headers=HEADERS)
print(resp.json())
# {'total_records': 3, 'unique_count': 2, 'duplicates_removed': 1, ...}

# 标准化
data = {
    "records": [{"email": " John.Doe@Test.com ", "phone": "138 0013 8000"}],
    "fields": ["email", "phone"]
}
resp = requests.post(f"{BASE}/v1/standardize", json=data, headers=HEADERS)
print(resp.json())
# email: john.doe@test.com, phone: +8613800138000

# 一键全流程
data = {
    "records": [...],
    "dedup_fields": ["email", "phone"],
    "dedup_mode": "exact",
    "standardize_fields": ["email", "phone"]
}
resp = requests.post(f"{BASE}/v1/clean", json=data, headers=HEADERS)
```

更多示例见 `examples/` 目录。

## 定价

| 套餐 | 价格 | 调用量 | QPS |
|------|------|--------|-----|
| Free | ¥0 | 1,000 次 | 2/s |
| Starter | ¥19 | 5,000 次 | 10/s |
| Pro | ¥49 | 10,000 次 | 30/s |
| Business | ¥149 | 50,000 次 | 50/s |

注册即送 1,000 次免费调用，无需信用卡。

## 项目结构

```
DataClean/
├── app/
│   ├── main.py                # FastAPI 入口 + 静态文件服务 + /api-info
│   ├── config.py              # 环境变量配置
│   ├── core/                  # 核心算法
│   │   ├── dedup_exact.py     # 精确去重（MD5）
│   │   ├── dedup_fuzzy.py     # 模糊去重（SimHash + Levenshtein）
│   │   ├── standardizer.py    # 标准化引擎
│   │   └── validator.py       # 邮箱验证（MX 查询）
│   ├── routes/                # API 路由
│   │   ├── auth.py            # 注册/登录/me
│   │   ├── api_keys.py        # API Key 管理
│   │   ├── billing.py         # 计费（结账/额度查询）
│   │   ├── dedup.py           # 去重
│   │   ├── standardize.py     # 标准化
│   │   ├── clean.py           # 全流程清洗
│   │   └── health.py          # 健康检查 + 调试 + test-db
│   ├── middleware/            # 中间件
│   │   ├── auth.py            # API Key 鉴权
│   │   └── rate_limit.py      # Redis 限流
│   ├── models/
│   │   └── schemas.py         # Pydantic 模型
│   ├── db/
│   │   ├── database.py        # Supabase 客户端
│   │   └── queries.py         # 数据库查询
│   └── billing/
│       ├── credits.py         # 额度管理（add_credits / update_plan）
│       └── webhook.py         # LemonSqueezy 回调
├── static/                    # 前端
│   ├── index.html             # 落地页
│   ├── dashboard.html         # 控制台
│   ├── css/style.css          # 样式
│   └── js/api.js              # API 客户端
├── docs/                      # 文档（Mintlify）
│   ├── introduction.mdx
│   ├── quickstart.mdx
│   └── mint.json
├── sql/                       # 数据库
│   ├── schema.sql             # 基础表
│   └── schema_v2.sql          # 用户系统表
├── examples/                  # 示例代码
│   ├── python_example.py
│   ├── javascript_example.js
│   └── curl_example.sh
├── test_data/                 # 测试数据
│   └── dirty_data.json
├── tests/                     # 单元/集成测试
│   ├── test_dedup.py
│   ├── test_standardizer.py
│   ├── test_validator.py
│   └── test_e2e.py
├── Dockerfile
├── docker-entrypoint.sh
├── render.yaml
├── requirements.txt
├── runtime.txt                # Render Python 版本
├── LAUNCH.md                  # 上线清单
├── run_api_test.py            # API 自测脚本
├── test_clean.py              # 清洗流程测试
├── test_user_system.py        # 用户系统测试
└── test_webhook.py            # Webhook 测试
```

## 部署

### Render 部署

1. Fork 仓库到 GitHub
2. 在 Render 创建 Web Service，连接仓库
3. 配置环境变量：

| 变量 | 说明 |
|------|------|
| `SUPABASE_URL` | Supabase 项目 URL（不含区域前缀） |
| `SUPABASE_SERVICE_KEY` | Supabase service_role 密钥 |
| `REDIS_URL` | Upstash Redis 连接 URL |
| `LEMONSQUEEZY_API_KEY` | LemonSqueezy API Key |
| `LEMONSQUEEZY_WEBHOOK_SECRET` | Webhook 签名密钥 |
| `LEMONSQUEEZY_STORE_ID` | LemonSqueezy Store ID |

4. 部署，访问 `https://your-app.onrender.com`

### 本地 Docker

```bash
docker build -t dataclean-api .
docker run -p 8000:8000 --env-file .env dataclean-api
```

## 环境依赖

- Python 3.11+
- Supabase 项目（PostgreSQL）
- Upstash Redis（限流）
- LemonSqueezy 账号（支付，可选）

## 支持项目

如果本项目对您有帮助，欢迎您的支持！
[支持与赞助 (微信/支付宝)](./SUPPORT.md)

## License

MIT
