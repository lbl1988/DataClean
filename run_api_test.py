import requests
import json

BASE = "http://127.0.0.1:8000/v1"
HEADERS = {"X-API-Key": "test_key", "Content-Type": "application/json"}

# 1. 去重
print("=== 1. 批量去重 ===")
r = requests.post(f"{BASE}/dedup", headers=HEADERS, json={
    "records": [
        {"id": 1, "name": "Alice", "email": "Test@Example.com", "phone": "123"},
        {"id": 2, "name": "Alice", "email": "test@example.com", "phone": "123"},
        {"id": 3, "name": "Bob", "email": "bob@test.com", "phone": "456"},
    ],
    "match_fields": ["email", "phone"],
    "match_mode": "fuzzy",
    "standardize_before_match": True,
})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"输入 {d['total_records']} 条 -> 去重后 {d['unique_count']} 条 (重复 {d['duplicate_count']} 条)")
    print(f"耗时: {d['processing_time_ms']}ms")
else:
    print(f"Error: {r.text[:300]}")

# 2. 标准化
print("\n=== 2. 标准化 ===")
r = requests.post(f"{BASE}/standardize", headers=HEADERS, json={
    "records": [
        {"phone": "+86 138-1234-5678", "email": "  ZhangSan@Gmail.com  ", "address": "beijing test"},
    ],
    "fields": ["phone", "email", "address"],
})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"标准化后: {d['standardized_records'][0]}")
    print(f"变更数: {d['changed_count']}")
else:
    print(f"Error: {r.text[:300]}")

# 3. 一键清洗
print("\n=== 3. 一键综合清洗 ===")
r = requests.post(f"{BASE}/clean", headers=HEADERS, json={
    "records": [
        {"id": 1, "name": "Alice", "email": "Test@Example.com", "phone": "123-456-7890", "address": "beijing"},
        {"id": 2, "name": "Alice", "email": "test@example.com", "phone": "1234567890", "address": "beijing"},
        {"id": 3, "name": "invalid", "email": "bad@@email.com", "phone": "999", "address": "shanghai"},
    ],
    "pipeline": ["standardize", "validate", "dedup"],
    "config": {
        "standardize": {"fields": ["phone", "email", "address"]},
        "validate": {"email_check": "format"},
        "dedup": {"match_fields": ["email", "phone"], "mode": "fuzzy", "threshold": 0.7},
    },
})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    s = d["summary"]
    q = d["quality_report"]
    print(f"输入 {s['input_count']} 条 -> 最终 {s['final_count']} 条")
    print(f"质量评分: {q['overall_score']}/100 (完整性:{q['completeness']} 唯一性:{q['uniqueness']} 有效性:{q['validity']})")
    print(f"耗时: {d['processing_time_ms']}ms")
else:
    print(f"Error: {r.text[:300]}")
