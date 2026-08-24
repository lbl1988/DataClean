import requests
import json
import hmac
import hashlib
import time

BASE = "http://127.0.0.1:8000"
V1 = "http://127.0.0.1:8000/v1"
WEBHOOK_SECRET = "dk_webhook_secret_2024_secure_32chars"

# 1. 健康检查
print("=== 健康检查 ===")
r = requests.get("http://127.0.0.1:8000/health")
print(f"Status: {r.status_code}, Body: {r.json()}")

# 2. 测试Webhook端点（模拟LemonSqueezy webhook）
print("\n=== Webhook端点测试 ===")

# 模拟 order_created 事件
webhook_data = {
    "meta": {
        "event_type": "order_created",
        "event_id": "test_event_001",
    },
    "data": {
        "attributes": {
            "user_email": "test@example.com",
            "variant_id": "2051277",  # Starter plan
            "total": 1900,
        }
    }
}

body = json.dumps(webhook_data).encode()
signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    body,
    hashlib.sha256,
).hexdigest()

r = requests.post(
    f"{BASE}/webhook/lemonsqueezy",
    data=body,
    headers={
        "Content-Type": "application/json",
        "x-signature": signature,
    }
)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

# 3. 测试重复Webhook（幂等性）
print("\n=== 幂等性测试（重复事件）===")
r2 = requests.post(
    f"{BASE}/webhook/lemonsqueezy",
    data=body,
    headers={
        "Content-Type": "application/json",
        "x-signature": signature,
    }
)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.json()}")

# 4. 测试无效签名
print("\n=== 无效签名测试 ===")
r3 = requests.post(
    f"{BASE}/webhook/lemonsqueezy",
    data=body,
    headers={
        "Content-Type": "application/json",
        "x-signature": "invalid_signature",
    }
)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:200]}")

# 5. 测试API接口（限流窗口已重置）
time.sleep(2)
print("\n=== API接口测试 ===")
HEADERS = {"X-API-Key": "test_key", "Content-Type": "application/json"}
r4 = requests.post(f"{V1}/dedup", headers=HEADERS, json={
    "records": [
        {"id": 1, "email": "a@test.com"},
        {"id": 2, "email": "a@test.com"},
    ],
    "match_fields": ["email"],
    "match_mode": "exact",
})
print(f"去重 Status: {r4.status_code}")
if r4.status_code == 200:
    d = r4.json()
    print(f"  输入{d['total_records']}条 -> 去重后{d['unique_count']}条")
