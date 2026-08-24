import re
from typing import Any

try:
    import dns.resolver
except ImportError:
    dns = None

from .standardizer import Standardizer


class EmailValidator:
    """邮箱验证引擎：格式校验 + MX记录检测（第一批不含SMTP探测）。"""

    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )

    ROLE_BASED = {
        "admin", "info", "support", "sales", "contact",
        "help", "team", "office", "noreply", "no-reply",
        "postmaster", "webmaster", "abuse", "security",
    }

    @classmethod
    def validate(cls, email: str, check_level: str = "format") -> dict:
        """验证邮箱。

        Args:
            email: 待验证的邮箱
            check_level: format | mx
                format: 只做格式校验
                mx: 格式 + MX记录检测
                （SMTP探测放第二批实现）
        """
        result = {
            "email": email,
            "is_valid": False,
            "format_valid": False,
            "mx_valid": False,
            "is_disposable": False,
            "is_role_based": False,
            "risk_score": 100,
            "error": None,
        }

        # 标准化
        std = Standardizer.standardize_email(email)
        email = std["value"]

        # 1. 格式校验
        if not cls.EMAIL_REGEX.match(email):
            result["error"] = "invalid_format"
            return result
        result["format_valid"] = True

        domain = email.split("@")[1]
        local = email.split("@")[0]

        # 2. 一次性邮箱检测
        if domain in Standardizer.DISPOSABLE_DOMAINS:
            result["is_disposable"] = True
            result["error"] = "disposable_email"
            result["risk_score"] = 90
            return result

        # 3. 角色邮箱检测
        if local.lower() in cls.ROLE_BASED:
            result["is_role_based"] = True
            result["risk_score"] = 30
        else:
            result["risk_score"] = 5

        if check_level == "format":
            result["is_valid"] = True
            return result

        # 4. MX记录查询
        if dns is None:
            result["error"] = "dns_library_missing"
            result["is_valid"] = True  # 保守判定
            return result

        try:
            mx_records = dns.resolver.resolve(domain, "MX")
            result["mx_valid"] = True
            result["is_valid"] = True
        except dns.resolver.NoAnswer:
            result["error"] = "no_mx_record"
            result["risk_score"] = 80
        except dns.resolver.NXDOMAIN:
            result["error"] = "domain_not_found"
            result["risk_score"] = 100
        except Exception:
            result["error"] = "mx_lookup_failed"
            result["is_valid"] = True  # 网络问题保守判定
            result["risk_score"] = 20

        return result

    @classmethod
    def validate_batch(
        cls, emails: list[str], check_level: str = "format"
    ) -> dict:
        """批量验证。"""
        results = [cls.validate(e, check_level) for e in emails]
        valid_count = sum(1 for r in results if r["is_valid"])
        return {
            "total": len(emails),
            "valid_count": valid_count,
            "invalid_count": len(emails) - valid_count,
            "results": results,
        }
