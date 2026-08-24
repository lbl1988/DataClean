import time
import hashlib
from fastapi import APIRouter, Depends, HTTPException

from ..models.schemas import DedupRequest, DedupResponse
from ..core.dedup_exact import exact_dedup
from ..core.dedup_fuzzy import fuzzy_dedup
from ..core.standardizer import Standardizer
from ..middleware.auth import verify_api_key, hash_api_key
from ..middleware.rate_limit import enforce_rate_limit
from ..billing.credits import deduct_credits
from ..db.queries import log_api_call

router = APIRouter()


@router.post("/dedup", response_model=DedupResponse)
async def dedup(req: DedupRequest, auth: dict = Depends(verify_api_key)):
    """批量去重接口。

    支持精确去重（MD5哈希）和模糊去重（SimHash + Levenshtein）。
    可选匹配前标准化（电话/邮箱/地址统一格式）。
    需要X-API-Key头。
    """
    # 限流
    key_hash = str(auth["user"]["id"])
    await enforce_rate_limit(key_hash, auth["plan"])

    start = time.time()
    records = req.records

    if req.standardize_before_match:
        std_fields = [f for f in req.match_fields if f in ("phone", "email", "address")]
        if std_fields:
            std_result = Standardizer.standardize_records(records, std_fields)
            records = std_result["standardized_records"]

    if req.match_mode == "fuzzy":
        result = fuzzy_dedup(records, req.match_fields, req.similarity_threshold)
    elif req.match_mode == "exact":
        result = exact_dedup(records, req.match_fields)
    else:
        raise HTTPException(400, f"Invalid match_mode: {req.match_mode}. Use 'exact' or 'fuzzy'.")

    elapsed_ms = int((time.time() - start) * 1000)
    credits = result["total_records"]

    # 扣减额度
    await deduct_credits(auth["user"]["id"], credits)
    # 记录用量
    await log_api_call(
        auth["user"]["id"], auth["api_key_id"], "/v1/dedup",
        result["total_records"], credits, elapsed_ms, "success",
    )

    return DedupResponse(
        status="success",
        total_records=result["total_records"],
        unique_count=result["unique_count"],
        duplicate_count=result["duplicate_count"],
        duplicate_groups=result["duplicate_groups"],
        deduplicated_records=result["deduplicated_records"],
        removed_ids=result["removed_ids"],
        credits_used=credits,
        processing_time_ms=elapsed_ms,
    )
