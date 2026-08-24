from typing import Any

try:
    from simhash import Simhash
except ImportError:
    Simhash = None

try:
    import Levenshtein
except ImportError:
    Levenshtein = None


def fuzzy_dedup(
    records: list[dict[str, Any]],
    match_fields: list[str],
    threshold: float = 0.85,
) -> dict:
    """模糊去重：SimHash快速初筛 + Levenshtein精确确认。

    第一步：用SimHash计算每条记录的指纹，海明距离<=3的可能是相似。
    第二步：对候选对用Levenshtein做精确相似度计算，超过阈值则判定为重复。

    Args:
        records: 待去重的记录列表
        match_fields: 参与匹配的字段名列表
        threshold: 相似度阈值，0-1之间，默认0.85
    """
    if Simhash is None or Levenshtein is None:
        return _fallback_fuzzy_dedup(records, match_fields, threshold)

    # 构建SimHash索引
    simhash_index: list[tuple] = []
    for record in records:
        text = " ".join(str(record.get(f, "")) for f in match_fields)
        sh = Simhash(text)
        simhash_index.append((record.get("id"), sh, text))

    duplicates: list[dict] = []
    processed: set = set()

    for i, (id_a, sh_a, text_a) in enumerate(simhash_index):
        if id_a in processed:
            continue

        best_match = None
        best_score = 0.0

        for j in range(i + 1, len(simhash_index)):
            id_b, sh_b, text_b = simhash_index[j]
            if id_b in processed:
                continue

            # SimHash海明距离初筛
            distance = sh_a.distance(sh_b)
            if distance <= 3:
                # Levenshtein精确确认
                ratio = Levenshtein.ratio(text_a, text_b)
                if ratio >= threshold and ratio > best_score:
                    best_match = id_b
                    best_score = ratio

        if best_match is not None:
            duplicates.append({
                "master_id": id_a,
                "duplicate_id": best_match,
                "similarity_score": round(best_score, 4),
                "match_reason": f"fuzzy_match_{best_score:.2f}",
            })
            processed.add(best_match)

    unique_ids = {
        r.get("id") for r in records
    } - {d["duplicate_id"] for d in duplicates}
    unique_records = [r for r in records if r.get("id") in unique_ids]

    return {
        "total_records": len(records),
        "unique_count": len(unique_records),
        "duplicate_count": len(duplicates),
        "duplicate_groups": _group_duplicates(duplicates),
        "deduplicated_records": unique_records,
        "removed_ids": [d["duplicate_id"] for d in duplicates],
    }


def _fallback_fuzzy_dedup(
    records: list[dict[str, Any]],
    match_fields: list[str],
    threshold: float,
) -> dict:
    """无第三方库时的降级方案：用difflib做相似度计算。"""
    import difflib

    duplicates: list[dict] = []
    processed: set = set()

    for i, record_a in enumerate(records):
        if record_a.get("id") in processed:
            continue
        text_a = " ".join(str(record_a.get(f, "")) for f in match_fields)

        best_match = None
        best_score = 0.0

        for j in range(i + 1, len(records)):
            record_b = records[j]
            if record_b.get("id") in processed:
                continue
            text_b = " ".join(str(record_b.get(f, "")) for f in match_fields)
            ratio = difflib.SequenceMatcher(None, text_a, text_b).ratio()
            if ratio >= threshold and ratio > best_score:
                best_match = record_b.get("id")
                best_score = ratio

        if best_match is not None:
            duplicates.append({
                "master_id": record_a.get("id"),
                "duplicate_id": best_match,
                "similarity_score": round(best_score, 4),
                "match_reason": f"fuzzy_match_{best_score:.2f}",
            })
            processed.add(best_match)

    unique_ids = {r.get("id") for r in records} - {d["duplicate_id"] for d in duplicates}
    unique_records = [r for r in records if r.get("id") in unique_ids]

    return {
        "total_records": len(records),
        "unique_count": len(unique_records),
        "duplicate_count": len(duplicates),
        "duplicate_groups": _group_duplicates(duplicates),
        "deduplicated_records": unique_records,
        "removed_ids": [d["duplicate_id"] for d in duplicates],
    }


def _group_duplicates(duplicates: list[dict]) -> list[dict]:
    groups: dict[Any, dict] = {}
    for d in duplicates:
        master = d["master_id"]
        if master not in groups:
            groups[master] = {
                "group_id": len(groups) + 1,
                "master_id": master,
                "duplicate_ids": [],
                "similarity_score": d["similarity_score"],
                "match_reason": d["match_reason"],
            }
        groups[master]["duplicate_ids"].append(d["duplicate_id"])

    return list(groups.values())
