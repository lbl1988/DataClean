import requests

BASE = "http://127.0.0.1:8000"
prefix = "/v1"

print("=== 0. 健康检查 ===")
r = requests.get(f"{BASE}/health", timeout=10)
print(f"Status: {r.status_code} | {r.json()}")

print("\n=== 1. 用户注册 ===")
r = requests.post(f"{BASE}{prefix}/auth/register", json={
    "email": "testuser@DataClean.com",
    "password": "test123456",
    "name": "Test User"
}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    token = data["token"]
    user = data["user"]
    print(f"User ID: {user['id']}")
    print(f"Email: {user['email']}")
    print(f"Plan: {user['plan']}")
    print(f"Credits: {user['credits_remaining']}")
    print(f"Token: {token[:20]}...")
else:
    print(f"Error: {r.text[:300]}")
    raise SystemExit(1)

print("\n=== 2. 重复注册（应失败409）===")
r = requests.post(f"{BASE}{prefix}/auth/register", json={
    "email": "testuser@DataClean.com",
    "password": "test123456",
}, timeout=10)
print(f"Status: {r.status_code} (expect 409)")
print(f"Body: {r.text[:200]}")

print("\n=== 3. 用户登录 ===")
r = requests.post(f"{BASE}{prefix}/auth/login", json={
    "email": "testuser@DataClean.com",
    "password": "test123456",
}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    login_data = r.json()
    login_token = login_data["token"]
    print(f"Token: {login_token[:20]}...")
    print(f"Plan: {login_data['user']['plan']}")
else:
    print(f"Error: {r.text[:300]}")

print("\n=== 4. 错误密码登录（应失败401）===")
r = requests.post(f"{BASE}{prefix}/auth/login", json={
    "email": "testuser@DataClean.com",
    "password": "wrongpassword",
}, timeout=10)
print(f"Status: {r.status_code} (expect 401)")

print("\n=== 5. 查看个人信息 ===")
r = requests.get(f"{BASE}{prefix}/auth/me?token={token}", timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    me = r.json()
    print(f"Email: {me['email']}")
    print(f"Plan: {me['plan']}")
    print(f"Credits: {me['credits_remaining']}/{me['credits_total']}")
else:
    print(f"Error: {r.text[:300]}")

print("\n=== 6. 创建API Key ===")
r = requests.post(f"{BASE}{prefix}/keys?token={token}", json={"name": "Production Key"}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    key_data = r.json()
    api_key = key_data["api_key"]
    print(f"API Key: {api_key[:16]}...")
    print(f"Key ID: {key_data['key_id']}")
    print(f"Prefix: {key_data['key_prefix']}")
    print(f"Message: {key_data['message']}")
else:
    print(f"Error: {r.text[:300]}")

print("\n=== 7. 列出API Keys ===")
r = requests.get(f"{BASE}{prefix}/keys?token={token}", timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    keys = r.json()
    print(f"Total keys: {len(keys)}")
    for k in keys:
        print(f"  - {k['name']} | {k['key_prefix']}... | active={k['is_active']}")
else:
    print(f"Error: {r.text[:300]}")

print("\n=== 8. 用新API Key调用去重接口 ===")
r = requests.post(f"{BASE}{prefix}/dedup", headers={
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}, json={
    "records": [
        {"id": 1, "email": "Test@Example.com"},
        {"id": 2, "email": "test@example.com"},
    ],
    "match_fields": ["email"],
    "match_mode": "exact",
    "standardize_before_match": True,
}, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"输入 {d['total_records']} 条 -> 去重后 {d['unique_count']} 条")
else:
    print(f"Error: {r.text[:300]}")

print("\n=== 9. 用旧test_key调用（应失败）===")
r = requests.post(f"{BASE}{prefix}/dedup", headers={
    "X-API-Key": "test_key",
    "Content-Type": "application/json"
}, json={
    "records": [{"id": 1, "email": "a@b.com"}],
    "match_fields": ["email"],
    "match_mode": "exact",
}, timeout=10)
print(f"Status: {r.status_code} (expect 403)")

print("\n=== 10. 吊销API Key ===")
if r.status_code == 200 or True:
    key_id = key_data["key_id"]
    r = requests.delete(f"{BASE}{prefix}/keys/{key_id}?token={token}", timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.json()}")

print("\n=== 11. 用已吊销的API Key调用（应失败403）===")
r = requests.post(f"{BASE}{prefix}/dedup", headers={
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}, json={
    "records": [{"id": 1, "email": "a@b.com"}],
    "match_fields": ["email"],
    "match_mode": "exact",
}, timeout=10)
print(f"Status: {r.status_code} (expect 403)")

print("\n=== 用户系统测试完成 ===")
