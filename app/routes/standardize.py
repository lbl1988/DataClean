import time
from fastapi import APIRouter, Depends

from ..models.schemas import StandardizeRequest, StandardizeResponse
from ..core.standardizer import Standardizer
from ..middleware.auth import verify_api_key, hash_api_key
from ..middleware.rate_limit import enforce_rate_limit
from ..billing.credits import deduct_credits
from ..db.queries import log_api_call

router = APIRouter()


@router.post("/standardize", response_model=StandardizeResponse)
async def standardize(req: StandardizeRequest, auth: dict = Depends(verify_api_key)):
    """数据标准化接口。需要X-API-Key头。"""
    key_hash = str(auth["user"]["id"])
    await enforce_rate_limit(key_hash, auth["plan"])

    start = time.time()
    result = Standardizer.standardize_records(req.records, req.fields, req.rules)
    elapsed_ms = int((time.time() - start) * 1000)
    credits = result["total_records"]

    await deduct_credits(auth["user"]["id"], credits)
    await log_api_call(
        auth["user"]["id"], auth["api_key_id"], "/v1/standardize",
        result["total_records"], credits, elapsed_ms, "success",
    )

    return StandardizeResponse(
        status="success",
        total_records=result["total_records"],
        changed_count=result["changed_count"],
        standardized_records=result["standardized_records"],
        credits_used=credits,
        processing_time_ms=elapsed_ms,
    )
