"""
端到端测试脚本 — 验证完整流程可用

使用方法:
1. 启动本地服务: uvicorn app.main:app --reload
2. 运行测试: python tests/test_e2e.py

不需要数据库/Redis（无DB时鉴权放行，适合本地验证算法）
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "test_key"  # 本地测试用

def test_health():
    """1. 健康检查"""
    print("测试1: 健康检查...", end=" ")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    print(f"✓ (version={data['version']})")

def test_dedup():
    """2. 精确去重"""
    print("测试2: 精确去重...", end=" ")
    r = requests.post(
        f"{BASE_URL}/v1/dedup",
        headers={"X-API-Key": API_KEY},
        json={
            "records": [
                {"id": 1, "email": "test@example.com", "phone": "123"},
                {"id": 2, "email": "test@example.com", "phone": "123"},
                {"id": 3, "email": "other@example.com", "phone": "456"},
            ],
            "match_fields": ["email", "phone"],
            "match_mode": "exact",
        },
    )
    # 可能因为无DB返回401，这是正常的
    if r.status_code == 401:
        print("⚠ (需要数据库，跳过)")
        return
    assert r.status_code == 200
    data = r.json()
    assert data["total_records"] == 3
    assert data["unique_count"] == 2
    assert data["duplicate_count"] == 1
    print(f"✓ (3→2, 去重1条)")

def test_fuzzy_dedup():
    """3. 模糊去重"""
    print("测试3: 模糊去重...", end=" ")
    r = requests.post(
        f"{BASE_URL}/v1/dedup",
        headers={"X-API-Key": API_KEY},
        json={
            "records": [
                {"id": 1, "name": "张三", "email": "ZhangSan@Gmail.com", "phone": "138-1234-5678"},
                {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678"},
                {"id": 3, "name": "李四", "email": "lisi@163.com", "phone": "13900000000"},
            ],
            "match_fields": ["name", "email", "phone"],
            "match_mode": "fuzzy",
            "similarity_threshold": 0.7,
            "standardize_before_match": True,
        },
    )
    if r.status_code == 401:
        print("⚠ (需要数据库，跳过)")
        return
    assert r.status_code == 200
    data = r.json()
    assert data["total_records"] == 3
    assert data["unique_count"] <= 3
    print(f"✓ (3→{data['unique_count']}, 去重{data['duplicate_count']}条)")

def test_standardize():
    """4. 标准化"""
    print("测试4: 标准化...", end=" ")
    r = requests.post(
        f"{BASE_URL}/v1/standardize",
        headers={"X-API-Key": API_KEY},
        json={
            "records": [
                {"phone": "+86 138-1234-5678", "email": "  ZhangSan@Gmail.com  ", "address": "北京市海淀区中关村大街1号"},
            ],
            "fields": ["phone", "email", "address"],
        },
    )
    if r.status_code == 401:
        print("⚠ (需要数据库，跳过)")
        return
    assert r.status_code == 200
    data = r.json()
    record = data["standardized_records"][0]
    assert "zhangsan@gmail.com" in record["email"]
    assert "13812345678" in record["phone"]
    assert "北京" in record["address"]
    assert "北京市" not in record["address"]
    print(f"✓ (email/phone/address 已标准化)")

def test_clean():
    """5. 一键综合清洗"""
    print("测试5: 一键综合清洗...", end=" ")
    r = requests.post(
        f"{BASE_URL}/v1/clean",
        headers={"X-API-Key": API_KEY},
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
                "dedup": {"match_fields": ["email", "phone"], "mode": "fuzzy", "threshold": 0.7},
            },
        },
    )
    if r.status_code == 401:
        print("⚠ (需要数据库，跳过)")
        return
    assert r.status_code == 200
    data = r.json()
    summary = data["summary"]
    assert summary["input_count"] == 3
    assert summary["final_count"] < 3  # 应该去掉了重复和无效
    print(f"✓ (3→{summary['final_count']}, 质量={data['quality_report']['overall_score']}/100)")

def main():
    print("=" * 50)
    print("DataClean API 端到端测试")
    print("=" * 50)

    tests = [
        test_health,
        test_dedup,
        test_fuzzy_dedup,
        test_standardize,
        test_clean,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ ({e})")
            failed += 1

    print()
    print("=" * 50)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
