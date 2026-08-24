#!/bin/bash

# DataClean API — curl 示例

API_BASE="https://your-api-domain.com/v1"
API_KEY="dk_live_your_api_key_here"

# 1. 批量去重
echo "=== 批量去重 ==="
curl -s -X POST "$API_BASE/dedup" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": 1, "name": "张三", "email": "ZhangSan@Gmail.com", "phone": "138-1234-5678"},
      {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678"},
      {"id": 3, "name": "李四", "email": "lisi@163.com", "phone": "13900000000"}
    ],
    "match_fields": ["name", "email", "phone"],
    "match_mode": "fuzzy",
    "similarity_threshold": 0.85,
    "standardize_before_match": true
  }' | python -m json.tool

echo ""
echo "=== 标准化 ==="
curl -s -X POST "$API_BASE/standardize" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"phone": "+86 138-1234-5678", "email": "  ZhangSan@Gmail.com  ", "address": "北京市海淀区中关村大街1号"}
    ],
    "fields": ["phone", "email", "address"]
  }' | python -m json.tool

echo ""
echo "=== 一键综合清洗 ==="
curl -s -X POST "$API_BASE/clean" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": 1, "name": "张三", "email": "ZhangSan@Gmail.com", "phone": "138-1234-5678", "address": "北京市海淀区中关村大街1号"},
      {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678", "address": "北京海淀区中关村大街1号"},
      {"id": 3, "name": "invalid", "email": "bad@@email.com", "phone": "13900000000", "address": "上海市浦东新区"}
    ],
    "pipeline": ["standardize", "validate", "dedup"],
    "config": {
      "standardize": {"fields": ["phone", "email", "address"]},
      "validate": {"email_check": "format"},
      "dedup": {"match_fields": ["email", "phone"], "mode": "fuzzy", "threshold": 0.85}
    }
  }' | python -m json.tool
