import hashlib
import secrets
from typing import Optional
from fastapi import Request, HTTPException

from ..config import settings
from ..db.database import get_db


def generate_api_key() -> tuple[str, str, str]:
    """生成API Key。

    返回: (raw_key, key_hash, key_prefix)
    """
    raw = secrets.token_urlsafe(32)
    api_key = f"dk_live_{raw}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_prefix = api_key[:12]
    return api_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """对API Key做SHA256哈希。"""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(request: Request) -> dict:
    """请求鉴权：从Header提取API Key，查库验证，返回用户信息。"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "missing_api_key",
                "message": "X-API-Key header is required.",
            },
        )

    key_hash = hash_api_key(api_key)
    db = get_db()

    if db is None:
        # 无数据库时的开发模式：用固定测试Key
        if api_key == "test_key":
            return {
                "user": {"id": "dev-user-id", "email": "dev@test.com", "plan": "free", "credits_remaining": 9999},
                "api_key_id": "dev-key-id",
                "plan": "free",
                "credits_remaining": 9999,
            }
        raise HTTPException(
            status_code=503,
            detail={"error": "database_unavailable", "message": "Database not configured."},
        )

    # 查API Key
    response = (
        db.table("api_keys")
        .select("id, user_id, is_active")
        .eq("key_hash", key_hash)
        .eq("is_active", True)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=403,
            detail={"error": "invalid_api_key", "message": "Invalid or revoked API Key."},
        )

    key_record = response.data[0]

    # 查用户
    user_response = (
        db.table("users")
        .select("*")
        .eq("id", key_record["user_id"])
        .execute()
    )

    if not user_response.data:
        raise HTTPException(
            status_code=403,
            detail={"error": "user_not_found", "message": "User account not found."},
        )

    user = user_response.data[0]

    if user.get("credits_remaining", 0) <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "no_credits",
                "message": "No credits remaining. Upgrade your plan.",
                "plan": user.get("plan", "free"),
                "credits_remaining": 0,
            },
        )

    # 更新Key最后使用时间
    db.table("api_keys").update({"last_used_at": "now()"}).eq("id", key_record["id"]).execute()

    return {
        "user": user,
        "api_key_id": key_record["id"],
        "plan": user.get("plan", "free"),
        "credits_remaining": user.get("credits_remaining", 0),
    }


async def create_api_key_for_user(user_id: str, name: str = "Default") -> dict:
    """为用户生成新的API Key。"""
    raw_key, key_hash, key_prefix = generate_api_key()
    db = get_db()
    if db is None:
        return {"error": "database_unavailable"}

    response = (
        db.table("api_keys")
        .insert({
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
        })
        .execute()
    )

    if not response.data:
        return {"error": "insert_failed"}

    record = response.data[0]
    return {
        "api_key": raw_key,
        "key_id": record.get("id"),
        "key_prefix": record.get("key_prefix"),
        "name": record.get("name"),
        "message": "Save this API key securely. It won't be shown again.",
    }


async def revoke_api_key(user_id: str, key_id: str) -> bool:
    """吊销API Key。"""
    db = get_db()
    if db is None:
        return False

    response = (
        db.table("api_keys")
        .update({"is_active": False})
        .eq("id", key_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(response.data or []) > 0
