# DataClean API

数据清洗API — 去重、标准化、验证，一键全流程。

## 快速开始

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url>
cd dataclean-api

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 5. 启动开发服务器
uvicorn app.main:app --reload --port 8000

# 6. 打开文档
# http://localhost:8000/docs
```

### 数据库初始化

在 Supabase SQL Editor 执行 `sql/schema.sql`。

### 运行测试

```bash
pytest tests/ -v
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/v1/dedup` | POST | 批量去重（精确+模糊） |
| `/v1/standardize` | POST | 数据标准化（电话/邮箱/地址/日期） |
| `/v1/clean` | POST | 一键综合清洗（标准化+验证+去重） |
| `/health` | GET | 健康检查 |
| `/webhook/lemonsqueezy` | POST | 支付回调 |

## 鉴权

所有 `/v1/*` 接口需要在Header中传入API Key：

```
X-API-Key: dk_live_your_api_key
```

## 定价

| 套餐 | 月费 | 条数/月 | QPS |
|------|------|--------|-----|
| Free | $0 | 1,000 | 2 |
| Starter | $19 | 10,000 | 10 |
| Pro | $49 | 50,000 | 30 |
| Business | $149 | 200,000 | 100 |

超出部分按 $0.002/条 计费。

## 技术栈

- **API**: FastAPI 0.136
- **数据库**: Supabase (PostgreSQL)
- **缓存/限流**: Upstash Redis
- **部署**: Render / Cloudflare Workers
- **支付**: LemonSqueezy
- **文档**: Mintlify

## 项目结构

```
dataclean-api/
├── app/
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置
│   ├── core/                # 核心算法
│   │   ├── dedup_exact.py   # 精确去重
│   │   ├── dedup_fuzzy.py   # 模糊去重
│   │   ├── standardizer.py  # 标准化引擎
│   │   └── validator.py     # 邮箱验证
│   ├── routes/              # API路由
│   ├── middleware/          # 鉴权+限流
│   ├── db/                  # 数据库操作
│   └── billing/             # 计费+支付
├── tests/                   # 单元测试
├── test_data/               # 测试数据
├── examples/                # 示例代码
├── sql/                     # 建表SQL
├── Dockerfile
├── render.yaml
└── requirements.txt
```

## 部署

### Render部署

1. 推送代码到GitHub
2. 在Render创建Web Service，连接仓库
3. 配置环境变量（见 .env.example）
4. 部署

### 本地Docker

```bash
docker build -t dataclean-api .
docker run -p 8000:8000 --env-file .env dataclean-api
```

## License

MIT
