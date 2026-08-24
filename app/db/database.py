from typing import Optional
from ..config import settings

_client = None
_last_error = None


def get_db():
    """获取Supabase客户端（单例）。

    使用supabase-py SDK，直接用SUPABASE_URL和SERVICE_KEY连接。
    """
    global _client, _last_error
    if _client is not None:
        return _client

    if not settings.supabase_url or not settings.supabase_service_key:
        _last_error = "SUPABASE_URL or SUPABASE_SERVICE_KEY not set"
        return None

    try:
        from supabase import create_client
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
        _last_error = None
    except Exception as e:
        import logging
        logging.error(f"Supabase init failed: {e}")
        print(f"Supabase init failed: {e}")
        _last_error = str(e)
        _client = None

    return _client


def get_last_error():
    global _last_error
    return _last_error


def close_db():
    """关闭数据库连接。"""
    global _client
    if _client is not None:
        _client = None
