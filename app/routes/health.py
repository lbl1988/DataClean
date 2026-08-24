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
