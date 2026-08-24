import re
from typing import Any

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


class Standardizer:
    """数据标准化引擎：电话/邮箱/地址/日期。"""

    PROVINCE_MAP = {
        "北京市": "北京", "上海市": "上海", "天津市": "天津",
        "重庆市": "重庆", "广东省": "广东", "江苏省": "江苏",
        "浙江省": "浙江", "四川省": "四川", "湖北省": "湖北",
        "湖南省": "湖南", "福建省": "福建", "山东省": "山东",
        "河南省": "河南", "河北省": "河北", "山西省": "山西",
        "陕西省": "陕西", "辽宁省": "辽宁", "吉林省": "吉林",
        "黑龙江省": "黑龙江", "安徽省": "安徽", "江西省": "江西",
        "广西壮族自治区": "广西", "内蒙古自治区": "内蒙古",
        "宁夏回族自治区": "宁夏", "新疆维吾尔自治区": "新疆",
        "西藏自治区": "西藏", "海南省": "海南", "贵州省": "贵州",
        "云南省": "云南", "甘肃省": "甘肃", "青海省": "青海",
    }

    DISPOSABLE_DOMAINS = {
        "guerrillamail.com", "mailinator.com", "tempmail.com",
        "throwaway.email", "10minutemail.com", "yopmail.com",
        "temp-mail.org", "sharklasers.com", "guerrillamailblock.com",
        "getnada.com", "emailondeck.com",
    }

    @classmethod
    def standardize_phone(
        cls, phone: str, country_code: str = "+86"
    ) -> dict:
        """电话标准化：去特殊字符、补国家码。"""
        if not phone:
            return {"value": phone, "original": phone, "changed": False}

        original = phone
        digits = re.sub(r"\D", "", phone)

        if len(digits) > 11:
            if digits.startswith("86"):
                digits = digits[2:]
            elif digits.startswith("0086"):
                digits = digits[4:]

        result = f"{country_code} {digits}" if len(digits) == 11 else digits
        changed = result != original.strip()
        return {"value": result, "original": original, "changed": changed}

    @classmethod
    def standardize_email(cls, email: str) -> dict:
        """邮箱标准化：去空格、转小写、Gmail去别名。"""
        if not email:
            return {"value": email, "original": email, "changed": False}

        original = email
        email = email.strip().lower()

        # Gmail特性：去除别名和点
        if "@gmail.com" in email:
            local, domain = email.split("@", 1)
            local = local.split("+")[0].replace(".", "")
            email = f"{local}@{domain}"

        changed = email != original
        return {"value": email, "original": original, "changed": changed}

    @classmethod
    def standardize_address(cls, address: str) -> dict:
        """地址标准化：省份全称转简称、去冗余空格。"""
        if not address:
            return {"value": address, "original": address, "changed": False}

        original = address
        result = address

        for full, short in cls.PROVINCE_MAP.items():
            result = result.replace(full, short)

        result = re.sub(r"\s+", "", result)
        changed = result != original
        return {"value": result, "original": original, "changed": changed}

    @classmethod
    def standardize_date(
        cls, date_str: str, target_format: str = "%Y-%m-%d"
    ) -> dict:
        """日期标准化：各种格式统一为ISO 8601。"""
        if not date_str:
            return {"value": date_str, "original": date_str, "changed": False}

        original = date_str
        if date_parser:
            try:
                dt = date_parser.parse(date_str)
                result = dt.strftime(target_format)
                changed = result != original.strip()
                return {"value": result, "original": original, "changed": changed}
            except (ValueError, TypeError):
                pass

        return {"value": date_str, "original": original, "changed": False}

    @classmethod
    def standardize_record(
        cls,
        record: dict[str, Any],
        fields: list[str],
        rules: dict | None = None,
    ) -> dict[str, Any]:
        """对一条记录的多个字段做标准化。"""
        result = dict(record)
        changes = []

        for field in fields:
            if field not in result:
                continue

            original_value = result[field]
            if original_value is None:
                continue

            if field in ("phone", "mobile", "telephone"):
                std = cls.standardize_phone(str(original_value))
            elif field in ("email", "mail", "e-mail"):
                std = cls.standardize_email(str(original_value))
            elif field in ("address", "addr", "location"):
                std = cls.standardize_address(str(original_value))
            elif field in ("date", "created_at", "birthday"):
                std = cls.standardize_date(str(original_value))
            else:
                continue

            if std["changed"]:
                result[field] = std["value"]
                changes.append({
                    "field": field,
                    "original": std["original"],
                    "standardized": std["value"],
                })

        return {
            "record": result,
            "changes": changes,
            "changed": len(changes) > 0,
        }

    @classmethod
    def standardize_records(
        cls,
        records: list[dict[str, Any]],
        fields: list[str],
        rules: dict | None = None,
    ) -> dict:
        """批量标准化。"""
        results = []
        total_changes = 0

        for record in records:
            std = cls.standardize_record(record, fields, rules)
            results.append({
                "record": std["record"],
                "original": record,
                "changed": std["changed"],
                "changes": std["changes"],
            })
            if std["changed"]:
                total_changes += 1

        return {
            "total_records": len(records),
            "changed_count": total_changes,
            "standardized_records": [r["record"] for r in results],
            "details": results,
        }
