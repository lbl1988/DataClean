from datetime import datetime
from fastapi import APIRouter

from ..models.schemas import HealthResponse
from ..config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口（Render/部署平台需要）。"""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
    )
