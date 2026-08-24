import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.dedup_exact import exact_dedup
from app.core.dedup_fuzzy import fuzzy_dedup


class TestExactDedup:
    def test_no_duplicates(self):
        records = [
            {"id": 1, "name": "Alice", "email": "a@test.com"},
            {"id": 2, "name": "Bob", "email": "b@test.com"},
        ]
        result = exact_dedup(records, ["email"])
        assert result["unique_count"] == 2
        assert result["duplicate_count"] == 0

    def test_exact_duplicates(self):
        records = [
            {"id": 1, "name": "Alice", "email": "a@test.com"},
            {"id": 2, "name": "Alice", "email": "a@test.com"},
        ]
        result = exact_dedup(records, ["email"])
        assert result["unique_count"] == 1
        assert result["duplicate_count"] == 1
        assert 2 in result["removed_ids"]

    def test_case_insensitive(self):
        records = [
            {"id": 1, "name": "Alice", "email": "Test@Example.com"},
            {"id": 2, "name": "Alice", "email": "test@example.com"},
        ]
        result = exact_dedup(records, ["email"])
        assert result["unique_count"] == 1

    def test_multi_field_match(self):
        records = [
            {"id": 1, "name": "Alice", "email": "a@test.com", "phone": "123"},
            {"id": 2, "name": "Alice", "email": "a@test.com", "phone": "456"},
            {"id": 3, "name": "Alice", "email": "a@test.com", "phone": "123"},
        ]
        result = exact_dedup(records, ["email", "phone"])
        assert result["unique_count"] == 2
        assert 3 in result["removed_ids"]

    def test_empty_list(self):
        result = exact_dedup([], ["email"])
        assert result["unique_count"] == 0
        assert result["duplicate_count"] == 0


class TestFuzzyDedup:
    def test_similar_records(self):
        records = [
            {"id": 1, "name": "张三", "email": "zhangsan@gmail.com", "phone": "13812345678"},
            {"id": 2, "name": "张三", "email": "zhangsan@gmail.com", "phone": "138-1234-5678"},
            {"id": 3, "name": "李四", "email": "lisi@163.com", "phone": "13900000000"},
        ]
        result = fuzzy_dedup(records, ["name", "email", "phone"], threshold=0.7)
        assert result["unique_count"] < 3
        assert result["duplicate_count"] >= 1

    def test_no_false_positives(self):
        records = [
            {"id": 1, "name": "Alice", "email": "alice@test.com"},
            {"id": 2, "name": "Bob", "email": "bob@test.com"},
        ]
        result = fuzzy_dedup(records, ["name", "email"], threshold=0.85)
        assert result["unique_count"] == 2
        assert result["duplicate_count"] == 0

    def test_threshold_sensitivity(self):
        records = [
            {"id": 1, "name": "Alice Johnson", "email": "alice@test.com"},
            {"id": 2, "name": "Alice Jonson", "email": "alice@test.com"},
        ]
        # 高阈值可能不匹配
        high = fuzzy_dedup(records, ["name", "email"], threshold=0.95)
        # 低阈值应该匹配
        low = fuzzy_dedup(records, ["name", "email"], threshold=0.70)
        assert low["duplicate_count"] >= high["duplicate_count"]
