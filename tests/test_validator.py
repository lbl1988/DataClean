import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.validator import EmailValidator


class TestEmailFormat:
    def test_valid_email(self):
        result = EmailValidator.validate("test@example.com", "format")
        assert result["is_valid"] is True
        assert result["format_valid"] is True

    def test_uppercase_email(self):
        result = EmailValidator.validate("Test@Example.COM", "format")
        assert result["is_valid"] is True

    def test_invalid_format_double_at(self):
        result = EmailValidator.validate("test@@example.com", "format")
        assert result["is_valid"] is False
        assert result["error"] == "invalid_format"

    def test_invalid_format_no_at(self):
        result = EmailValidator.validate("testexample.com", "format")
        assert result["is_valid"] is False
        assert result["error"] == "invalid_format"

    def test_invalid_empty(self):
        result = EmailValidator.validate("", "format")
        assert result["is_valid"] is False

    def test_disposable_email(self):
        result = EmailValidator.validate("test@mailinator.com", "format")
        assert result["is_disposable"] is True
        assert result["error"] == "disposable_email"

    def test_role_based_email(self):
        result = EmailValidator.validate("admin@example.com", "format")
        assert result["is_role_based"] is True
        assert result["risk_score"] > 5

    def test_normal_email_low_risk(self):
        result = EmailValidator.validate("zhangsan@gmail.com", "format")
        assert result["is_valid"] is True
        assert result["risk_score"] == 5
        assert result["is_role_based"] is False


class TestEmailBatch:
    def test_batch_mixed(self):
        emails = [
            "valid@example.com",
            "invalid@@test.com",
            "admin@example.com",
        ]
        result = EmailValidator.validate_batch(emails, "format")
        assert result["total"] == 3
        assert result["valid_count"] == 2
        assert result["invalid_count"] == 1
