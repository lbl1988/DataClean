from datetime import datetime
from fastapi import APIRouter
from typing import Optional

from ..models.schemas import HealthResponse
from ..config import settings
from ..db.database import get_db, get_last_error

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口（Render/部署平台需要）。"""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/debug")
async def debug():
    """临时调试端点，检查配置状态。"""
    supabase_url_set = bool(settings.supabase_url)
    supabase_key_set = bool(settings.supabase_service_key)
    redis_url_set = bool(settings.redis_url)
    db = get_db()
    db_ok = db is not None
    import os
    raw_envs = {k: v[:30] for k, v in os.environ.items() if 'SUPABASE' in k or 'REDIS' in k or 'LEMON' in k or k == 'ENV'}
    return {
        'raw_envs': raw_envs,
        "env": settings.env,
        "supabase_url_set": supabase_url_set,
        "supabase_url_prefix": settings.supabase_url[:30] if settings.supabase_url else "",
        "supabase_key_set": supabase_key_set,
        "supabase_key_prefix": settings.supabase_service_key[:10] if settings.supabase_service_key else "",
        "redis_url_set": redis_url_set,
        "db_connected": db_ok,
        "db_type": str(type(db)) if db else "None",
        "db_error": get_last_error(),
    }


@router.get("/test-db")
async def test_db():
    """测试数据库表访问。"""
    db = get_db()
    if db is None:
        return {"error": "Database not connected", "detail": get_last_error()}

    results = {}
    for table in ["users", "api_keys", "api_usage", "payments", "jobs"]:
        try:
            resp = db.table(table).select("*").limit(1).execute()
            results[table] = {"ok": True, "rows": len(resp.data), "data": resp.data[:1]}
        except Exception as e:
            results[table] = {"ok": False, "error": str(e)}

    # Try a raw insert into users
    try:
        import hashlib, secrets
        test_email = f"probe_{secrets.token_hex(4)}@test.dev"
        password_hash = hashlib.sha256(("test" + "dataclean_salt_2024").encode()).hexdigest()
        resp = db.table("users").insert({
            "email": test_email,
            "password_hash": password_hash,
            "name": "Probe",
            "plan": "free",
            "credits_remaining": 1000,
            "credits_total": 1000,
            "is_active": True,
        }).execute()
        results["insert_test"] = {"ok": True, "data": resp.data[:1]} if resp.data else {"ok": False, "error": "No data returned"}
        # Clean up
        if resp.data:
            db.table("users").delete().eq("id", resp.data[0]["id"]).execute()
            results["insert_test"]["cleanup"] = "done"
    except Exception as e:
        results["insert_test"] = {"ok": False, "error": str(e)}

    return results

