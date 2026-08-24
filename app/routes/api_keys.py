from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from ..db.database import get_db
from ..middleware.auth import generate_api_key, revoke_api_key
from .auth import verify_token

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str = "Default"


class KeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[str]
    created_at: str


class CreateKeyResponse(BaseModel):
    api_key: str
    key_id: str
    key_prefix: str
    name: str
    message: str


@router.post("/keys", response_model=CreateKeyResponse)
async def create_key(req: CreateKeyRequest, token: str = Query(...)):
    user = await verify_token(token)
    if not user:
        raise HTTPException(401, detail={"error": "invalid_token", "message": "Invalid or expired token."})

    raw_key, key_hash, key_prefix = generate_api_key()
    db = get_db()

    response = (
        db.table("api_keys")
        .insert({
            "user_id": user["id"],
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": req.name,
        })
        .execute()
    )

    if not response.data:
        raise HTTPException(500, detail={"error": "insert_failed", "message": "Failed to create API key."})

    record = response.data[0]
    return {
        "api_key": raw_key,
        "key_id": record["id"],
        "key_prefix": key_prefix,
        "name": req.name,
        "message": "Save this API key securely. It won't be shown again.",
    }


@router.get("/keys", response_model=list[KeyResponse])
async def list_keys(token: str = Query(...)):
    user = await verify_token(token)
    if not user:
        raise HTTPException(401, detail={"error": "invalid_token", "message": "Invalid or expired token."})

    db = get_db()
    response = (
        db.table("api_keys")
        .select("id, name, key_prefix, is_active, last_used_at, created_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


@router.delete("/keys/{key_id}")
async def delete_key(key_id: str, token: str = Query(...)):
    user = await verify_token(token)
    if not user:
        raise HTTPException(401, detail={"error": "invalid_token", "message": "Invalid or expired token."})

    success = await revoke_api_key(user["id"], key_id)
    if not success:
        raise HTTPException(404, detail={"error": "key_not_found", "message": "API key not found."})

    return {"status": "revoked", "key_id": key_id}
