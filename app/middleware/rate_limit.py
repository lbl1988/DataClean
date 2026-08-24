from typing import Optional
from fastapi import HTTPException

from ..config import settings

_redis = None


async def get_redis():
    """获取Redis连接（单例）。REDIS_URL未配置时返回None。"""
    global _redis
    if _redis is not None:
        return _redis

    if not settings.redis_url:
        return None

    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    except Exception:
        return None

    return _redis


async def check_rate_limit(
    api_key_hash: str,
    plan: str = "free",
) -> tuple[bool, Optional[str]]:
    """双层限流：QPS限流 + 日配额。

    Args:
        api_key_hash: API Key的SHA256哈希
        plan: 用户套餐 free | hobby | pro | business

    Returns:
        (allowed, error_message)
    """
    redis = await get_redis()
    if redis is None:
        return True, None  # Redis未配置时放行

    qps_limit = (
        settings.rate_limit_qps_paid if plan != "free" else settings.rate_limit_qps_free
    )
    daily_limit = (
        settings.rate_limit_daily_paid if plan != "free" else settings.rate_limit_daily_free
    )

    key_qps = f"rate:qps:{api_key_hash}"
    key_daily = f"rate:daily:{api_key_hash}"

    # QPS限流（滑动窗口）
    try:
        current = await redis.incr(key_qps)
        if current == 1:
            await redis.expire(key_qps, 1)
        if current > qps_limit:
            return False, f"QPS limit exceeded ({qps_limit}/s). Retry in 1 second."
    except Exception:
        pass  # Redis不可用时放行

    # 日配额限流
    try:
        daily_count = await redis.incr(key_daily)
        if daily_count == 1:
            await redis.expire(key_daily, 86400)
        if daily_count > daily_limit:
            return False, f"Daily limit exceeded ({daily_limit}/day). Upgrade your plan."
    except Exception:
        pass

    return True, None


async def enforce_rate_limit(api_key_hash: str, plan: str = "free"):
    """限流中间件：不通过直接抛429。"""
    allowed, message = await check_rate_limit(api_key_hash, plan)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": message,
            },
        )
