"""
DataClean API — Python 示例

5分钟快速开始：去重 + 标准化 + 一键清洗
"""
import requests

API_BASE = "https://your-api-domain.com/v1"
API_KEY = "dk_live_your_api_key_here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}

# ==================== 1. 批量去重 ====================
print("=== 批量去重 ===")
response = requests.post(
    f"{API_BASE}/dedup",
    headers=headers,
    json={
        "records": [
            {"id": 1, "name": "张三", "email": "ZhangSan@Gmail.com", "phone": "138-1234-5678"},
            {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678"},
            {"id": 3, "name": "李四", "email": "lisi@163.com", "phone": "13900000000"},
        ],
        "match_fields": ["name", "email", "phone"],
        "match_mode": "fuzzy",
        "similarity_threshold": 0.85,
        "standardize_before_match": True,
    },
)
data = response.json()
print(f"输入 {data['total_records']} 条，去重后 {data['unique_count']} 条")
print(f"重复 {data['duplicate_count']} 条，耗时 {data['processing_time_ms']}ms\n")

# ==================== 2. 标准化 ====================
print("=== 标准化 ===")
response = requests.post(
    f"{API_BASE}/standardize",
    headers=headers,
    json={
        "records": [
            {"phone": "+86 138-1234-5678", "email": "  ZhangSan@Gmail.com  ", "address": "北京市海淀区中关村大街1号"},
        ],
        "fields": ["phone", "email", "address"],
    },
)
data = response.json()
print(f"标准化前: {data['standardized_records'][0]}\n")

# ==================== 3. 一键综合清洗 ====================
print("=== 一键综合清洗 ===")
response = requests.post(
    f"{API_BASE}/clean",
    headers=headers,
    json={
        "records": [
            {"id": 1, "name": "张三", "email": "ZhangSan@Gmail.com", "phone": "138-1234-5678", "address": "北京市海淀区中关村大街1号"},
            {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678", "address": "北京海淀区中关村大街1号"},
            {"id": 3, "name": "invalid", "email": "bad@@email.com", "phone": "13900000000", "address": "上海市浦东新区"},
        ],
        "pipeline": ["standardize", "validate", "dedup"],
        "config": {
            "standardize": {"fields": ["phone", "email", "address"]},
            "validate": {"email_check": "format"},
            "dedup": {"match_fields": ["email", "phone"], "mode": "fuzzy", "threshold": 0.85},
        },
    },
)
data = response.json()
print(f"输入 {data['summary']['input_count']} 条 → 最终 {data['summary']['final_count']} 条")
print(f"质量评分: {data['quality_report']['overall_score']}/100")
print(f"完整性: {data['quality_report']['completeness']}")
print(f"唯一性: {data['quality_report']['uniqueness']}")
print(f"有效性: {data['quality_report']['validity']}")
