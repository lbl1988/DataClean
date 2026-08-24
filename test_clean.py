import requests
import time

BASE = "http://127.0.0.1:8000/v1"
HEADERS = {"X-API-Key": "test_key", "Content-Type": "application/json"}

# 等待限流窗口重置
time.sleep(2)

print("=== 一键综合清洗（重试） ===")
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
