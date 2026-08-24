import hashlib
from typing import Any


def exact_dedup(records: list[dict[str, Any]], match_fields: list[str]) -> dict:
    """精确去重：对指定字段组合做MD5哈希，完全一致即重复。

    适用于：内容完全一致的记录去重，对格式差异敏感（空格/大小写不同视为不同）。
    如果需要模糊匹配，先用标准化处理再调用本函数，或使用 fuzzy_dedup。
    """
    seen: dict[str, int] = {}
    duplicates: list[dict] = []
    unique_records: list[dict] = []

    for record in records:
        key_parts = [str(record.get(f, "")).strip().lower() for f in match_fields]
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode("utf-8")).hexdigest()

        if key_hash in seen:
            duplicates.append({
                "duplicate_id": record.get("id"),
                "master_id": seen[key_hash],
                "match_reason": "exact_hash_match",
                "matched_fields": match_fields,
            })
        else:
            seen[key_hash] = record.get("id")
            unique_records.append(record)

    return {
        "total_records": len(records),
        "unique_count": len(unique_records),
        "duplicate_count": len(duplicates),
        "duplicate_groups": _group_duplicates(duplicates),
        "deduplicated_records": unique_records,
        "removed_ids": [d["duplicate_id"] for d in duplicates],
    }


def _group_duplicates(duplicates: list[dict]) -> list[dict]:
    """把重复对按master_id分组。"""
    groups: dict[Any, list] = {}
    for d in duplicates:
        master = d["master_id"]
        if master not in groups:
            groups[master] = {
                "group_id": len(groups) + 1,
                "master_id": master,
                "duplicate_ids": [],
                "match_reason": d["match_reason"],
            }
        groups[master]["duplicate_ids"].append(d["duplicate_id"])

    return list(groups.values())
