import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.standardizer import Standardizer


class TestPhoneStandardize:
    def test_removes_dashes(self):
        result = Standardizer.standardize_phone("138-1234-5678")
        assert "13812345678" in result["value"]
        assert result["changed"] is True

    def test_removes_country_code(self):
        result = Standardizer.standardize_phone("+86 138 1234 5678")
        assert "13812345678" in result["value"]
        assert result["changed"] is True

    def test_strips_86_prefix(self):
        result = Standardizer.standardize_phone("8613812345678")
        assert "13812345678" in result["value"]

    def test_no_change_needed(self):
        result = Standardizer.standardize_phone("+86 13812345678")
        assert result["changed"] is False or result["value"].endswith("13812345678")

    def test_empty(self):
        result = Standardizer.standardize_phone("")
        assert result["changed"] is False


class TestEmailStandardize:
    def test_lowercases(self):
        result = Standardizer.standardize_email("Test@Example.COM")
        assert result["value"] == "test@example.com"
        assert result["changed"] is True

    def test_trims_spaces(self):
        result = Standardizer.standardize_email("  test@example.com  ")
        assert result["value"] == "test@example.com"
        assert result["changed"] is True

    def test_gmail_alias_removal(self):
        result = Standardizer.standardize_email("zhangsan+alias@gmail.com")
        assert result["value"] == "zhangsan@gmail.com"

    def test_gmail_dot_removal(self):
        result = Standardizer.standardize_email("zhang.san@gmail.com")
        assert result["value"] == "zhangsan@gmail.com"

    def test_non_gmail_keeps_dots(self):
        result = Standardizer.standardize_email("zhang.san@163.com")
        assert result["value"] == "zhang.san@163.com"


class TestAddressStandardize:
    def test_province_full_to_short(self):
        result = Standardizer.standardize_address("北京市海淀区中关村大街1号")
        assert "北京" in result["value"]
        assert "北京市" not in result["value"]
        assert result["changed"] is True

    def test_removes_spaces(self):
        result = Standardizer.standardize_address("北京 海淀区 中关村")
        assert " " not in result["value"]

    def test_no_change(self):
        result = Standardizer.standardize_address("深圳南山区")
        assert result["changed"] is False


class TestRecordStandardize:
    def test_multi_field(self):
        record = {
            "id": 1,
            "name": "张三",
            "email": "ZhangSan@Gmail.com",
            "phone": "138-1234-5678",
            "address": "北京市海淀区中关村大街1号",
        }
        result = Standardizer.standardize_record(
            record, ["email", "phone", "address"]
        )
        assert result["changed"] is True
        assert "zhangsan@gmail.com" in result["record"]["email"]
        assert "13812345678" in result["record"]["phone"]
        assert "北京" in result["record"]["address"]
