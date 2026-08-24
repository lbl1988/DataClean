import time
from fastapi import APIRouter, Depends

from ..models.schemas import CleanRequest, CleanResponse, CleanSummary, QualityReport
from ..core.standardizer import Standardizer
from ..core.dedup_exact import exact_dedup
from ..core.dedup_fuzzy import fuzzy_dedup
from ..core.validator import EmailValidator
from ..middleware.auth import verify_api_key, hash_api_key
from ..middleware.rate_limit import enforce_rate_limit
from ..billing.credits import deduct_credits
from ..db.queries import log_api_call

router = APIRouter()


@router.post("/clean", response_model=CleanResponse)
async def clean(req: CleanRequest, auth: dict = Depends(verify_api_key)):
    """综合清洗接口（一键全流程）。需要X-API-Key头。

    按pipeline顺序执行：standardize → validate → dedup。
    返回清洗后的数据 + 数据质量报告。
    """
    key_hash = str(auth["user"]["id"])
    await enforce_rate_limit(key_hash, auth["plan"])

    start = time.time()
    records = req.records
    input_count = len(records)

    after_std = input_count
    after_val = input_count
    after_ded = input_count
    invalid_count = 0
    removed_dup = 0

    # 1. 标准化
    if "standardize" in req.pipeline:
        std_config = req.config.get("standardize", {})
        std_fields = std_config.get("fields", ["phone", "email", "address"])
        std_result = Standardizer.standardize_records(records, std_fields)
        records = std_result["standardized_records"]
        after_std = len(records)

    # 2. 验证
    if "validate" in req.pipeline:
        val_config = req.config.get("validate", {})
        email_check = val_config.get("email_check", "format")
        valid_records = []
        for r in records:
            is_valid = True
            email = r.get("email")
            if email and email_check:
                result = EmailValidator.validate(email, email_check)
                if not result["is_valid"]:
                    is_valid = False
            if is_valid:
                valid_records.append(r)
            else:
                invalid_count += 1
        records = valid_records
        after_val = len(records)

    # 3. 去重
    if "dedup" in req.pipeline:
        dedup_config = req.config.get("dedup", {})
        match_fields = dedup_config.get("match_fields", ["email", "phone"])
        mode = dedup_config.get("mode", "fuzzy")
        threshold = dedup_config.get("threshold", 0.85)

        # 去重前标准化匹配字段
        std_fields = [f for f in match_fields if f in ("phone", "email", "address")]
        if std_fields:
            std_result = Standardizer.standardize_records(records, std_fields)
            records = std_result["standardized_records"]

        if mode == "fuzzy":
            result = fuzzy_dedup(records, match_fields, threshold)
        else:
            result = exact_dedup(records, match_fields)
        records = result["deduplicated_records"]
        removed_dup = result["duplicate_count"]
        after_ded = len(records)

    final_count = len(records)
    elapsed_ms = int((time.time() - start) * 1000)

    # 质量报告
    total_fields = sum(len(r) for r in records) if records else 1
    filled_fields = sum(
        1 for r in records for v in r.values() if v is not None and str(v).strip()
    )
    completeness = filled_fields / total_fields if total_fields > 0 else 0
    uniqueness = final_count / input_count if input_count > 0 else 0
    validity = (input_count - invalid_count) / input_count if input_count > 0 else 0
    overall = int((completeness + uniqueness + validity) / 3 * 100)

    summary = CleanSummary(
        input_count=input_count,
        after_standardize=after_std if "standardize" in req.pipeline else None,
        after_validate=after_val if "validate" in req.pipeline else None,
        after_dedup=after_ded if "dedup" in req.pipeline else None,
        final_count=final_count,
        removed_duplicates=removed_dup if "dedup" in req.pipeline else None,
        invalid_records=invalid_count if "validate" in req.pipeline else None,
    )

    quality = QualityReport(
        completeness=round(completeness, 2),
        uniqueness=round(uniqueness, 2),
        validity=round(validity, 2),
        overall_score=overall,
    )

    # 扣减额度 + 记录用量
    await deduct_credits(auth["user"]["id"], input_count)
    await log_api_call(
        auth["user"]["id"], auth["api_key_id"], "/v1/clean",
        input_count, input_count, elapsed_ms, "success",
    )

    return CleanResponse(
        status="success",
        summary=summary,
        cleaned_records=records,
        quality_report=quality,
        credits_used=input_count,
        processing_time_ms=elapsed_ms,
    )
