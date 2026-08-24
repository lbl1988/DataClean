# 首发文案 + 部署清单

## 部署清单（上线前逐项检查）

### 功能检查
- [ ] /v1/dedup 接口可用，精确和模糊模式都测试过
- [ ] /v1/standardize 接口可用，电话/邮箱/地址标准化正确
- [ ] /v1/clean 接口可用，pipeline全流程跑通
- [ ] /health 返回200
- [ ] API Key鉴权生效（无Key返回401，错误Key返回403）
- [ ] 限流生效（超QPS返回429）
- [ ] 额度扣减正确（无额度返回402）

### 部署检查
- [ ] 代码推送到GitHub
- [ ] Render部署成功，服务可访问
- [ ] 自定义域名配置完成 + HTTPS
- [ ] CORS配置正确
- [ ] 环境变量全部配置（.env）
- [ ] Supabase数据库表已建（sql/schema.sql执行过）
- [ ] Upstash Redis已配置
- [ ] LemonSqueezy Webhook URL已配置

### 文档检查
- [ ] 文档站可访问
- [ ] 快速开始指南5分钟内能跑通
- [ ] 3个语言示例代码可运行
- [ ] 定价页面可见
- [ ] 错误码说明完整

### 安全检查
- [ ] 所有密钥在环境变量中，无硬编码
- [ ] .env在.gitignore中
- [ ] 错误信息脱敏（不暴露SQL/堆栈）
- [ ] CORS只允许配置的来源

---

## 首发文案

### Hacker News (Show HN)

```
Show HN: DataClean API – Clean and deduplicate any dataset via API

I built an API that cleans messy data — deduplication, standardization, and email validation in a single call.

Use cases: CRM data cleaning, crawled data dedup, lead list validation before outreach.

What it does:
- Exact dedup (MD5 hash) and fuzzy dedup (SimHash + Levenshtein similarity)
- Phone standardization: "+86 138-1234-5678" → "13812345678"
- Email standardization: Gmail alias/dot removal, case normalization
- Address standardization: Chinese province names unified
- Email validation: format + MX record + disposable detection
- One-call pipeline: POST /v1/clean → standardize → validate → dedup → get quality report

Free tier: 1,000 records/month, no credit card needed.

Docs: https://docs.yourdomain.com
Pricing: https://yourdomain.com/pricing

Tech stack: FastAPI + Supabase + Cloudflare + Redis + LemonSqueezy

Feedback welcome!
```

### Reddit (r/SideProject)

```
标题：I built a data cleaning API — dedup + standardize + validate in one call

正文：
Tired of cleaning dirty CRM data manually? I built DataClean API.

It's an API-as-a-service that:
- Deduplicates records (exact + fuzzy matching with SimHash/Levenshtein)
- Standardizes phone numbers, emails, addresses
- Validates emails (format + MX record + disposable detection)
- Gives you a data quality score

One POST request, get clean data back.

Free tier: 1,000 records/month, no signup wall.

Built with: FastAPI, Supabase, Redis, Cloudflare

Demo + Docs: https://yourdomain.com
```

### Product Hunt

```
Tagline: Clean any dataset via API — dedup, standardize, validate in one call

Description:
DataClean API is a data cleaning service for developers and businesses. Send your messy data, get clean data back.

Features:
- 🔍 Deduplication: Exact (MD5) + fuzzy (SimHash + Levenshtein)
- 📏 Standardization: Phone, email, address, date auto-formatting
- ✉️ Email validation: Format + MX record + disposable detection
- 📊 Quality report: Completeness, uniqueness, validity scores
- 🔄 One-call pipeline: Standardize → validate → dedup

Pricing: Free 1,000 records/month. Paid plans from $19/mo.

Built solo with FastAPI + Supabase + Cloudflare.
```

---

## 提交目录站清单

| 目录站 | URL | 状态 |
|--------|-----|------|
| RapidAPI | https://rapidapi.com | [ ] 已提交 |
| PublicAPIs | https://publicapis.org | [ ] 已提交 |
| API List | https://apilist.fun | [ ] 已提交 |
| APIs.io | https://apis.io | [ ] 已提交 |
| Product Hunt | https://producthunt.com | [ ] 已预约 |
| Hacker News | https://news.ycombinator.com | [ ] 已发帖 |
| Reddit | r/SideProject | [ ] 已发帖 |
| Reddit | r/dataengineering | [ ] 已发帖 |
| Reddit | r/webdev | [ ] 已发帖 |
| Dev.to | https://dev.to | [ ] 已发文章 |
| V2EX | https://v2ex.com | [ ] 已发帖 |
