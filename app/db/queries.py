from typing import Optional, Any
from datetime import datetime


async def log_api_call(
    user_id: str,
    api_key_id: str,
    endpoint: str,
    records_processed: int,
    credits_used: int,
    processing_time_ms: int,
    status: str = "success",
    error_message: Optional[str] = None,
):
    """记录API调用日志。"""
    from .database import get_db
    db = get_db()
    if db is None:
        return

    db.table("api_usage").insert({
        "user_id": user_id,
        "api_key_id": api_key_id,
        "endpoint": endpoint,
        "records_processed": records_processed,
        "credits_used": credits_used,
        "processing_time_ms": processing_time_ms,
        "status": status,
        "error_message": error_message,
    }).execute()


async def get_usage_summary(user_id: str, days: int = 30) -> dict:
    """获取用户用量摘要。"""
    from .database import get_db
    db = get_db()
    if db is None:
        return {"total_calls": 0, "total_records": 0, "by_endpoint": {}}

    response = (
        db.table("api_usage")
        .select("endpoint, records_processed, credits_used")
        .eq("user_id", user_id)
        .gte("created_at", datetime.utcnow().isoformat())
        .execute()
    )

    rows = response.data or []
    by_endpoint: dict[str, dict] = {}
    total_calls = 0
    total_records = 0

    for r in rows:
        ep = r.get("endpoint", "unknown")
        if ep not in by_endpoint:
            by_endpoint[ep] = {"calls": 0, "records": 0, "credits": 0}
        by_endpoint[ep]["calls"] += 1
        by_endpoint[ep]["records"] += r.get("records_processed", 0) or 0
        by_endpoint[ep]["credits"] += r.get("credits_used", 0) or 0
        total_calls += 1
        total_records += r.get("records_processed", 0) or 0

    return {
        "total_calls": total_calls,
        "total_records": total_records,
        "by_endpoint": by_endpoint,
    }


async def create_job(
    user_id: str,
    job_type: str,
    input_size: int,
) -> str:
    """创建异步任务。"""
    from .database import get_db
    db = get_db()
    if db is None:
        return ""

    response = db.table("jobs").insert({
        "user_id": user_id,
        "job_type": job_type,
        "input_size": input_size,
        "status": "pending",
    }).execute()

    if response.data:
        return str(response.data[0].get("id", ""))
    return ""


async def update_job_status(
    job_id: str,
    status: str,
    output_size: Optional[int] = None,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """更新异步任务状态。"""
    from .database import get_db
    db = get_db()
    if db is None:
        return

    update_data: dict[str, Any] = {"status": status}
    if output_size is not None:
        update_data["output_size"] = output_size
    if result_url is not None:
        update_data["result_url"] = result_url
    if error_message is not None:
        update_data["error_message"] = error_message
    if status in ("completed", "failed"):
        update_data["completed_at"] = datetime.utcnow().isoformat()

    db.table("jobs").update(update_data).eq("id", job_id).execute()
