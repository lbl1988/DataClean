import hashlib
import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..config import settings
from ..db.database import get_db
from ..billing.credits import PLAN_CREDITS

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    plan: str
    credits_remaining: int
    credits_total: int
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


def hash_password(password: str) -> str:
    salt = "dataclean_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()


@router.post("/auth/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    db = get_db()
    if db is None:
        raise HTTPException(503, detail="Database not configured.")

    existing = db.table("users").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(409, detail={"error": "email_exists", "message": "Email already registered."})

    password_hash = hash_password(req.password)
    new_user = {
        "email": req.email,
        "password_hash": password_hash,
        "name": req.name or req.email.split("@")[0],
        "plan": "free",
        "credits_remaining": PLAN_CREDITS["free"],
        "credits_total": PLAN_CREDITS["free"],
        "is_active": True,
    }

    response = db.table("users").insert(new_user).execute()
    if not response.data:
        raise HTTPException(500, detail={"error": "insert_failed", "message": "Failed to create user."})

    user = response.data[0]
    token = secrets.token_urlsafe(48)
    db.table("users").update({"auth_token": token}).eq("id", user["id"]).execute()

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "plan": "free",
            "credits_remaining": PLAN_CREDITS["free"],
            "credits_total": PLAN_CREDITS["free"],
            "created_at": user.get("created_at", ""),
        },
    }


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    db = get_db()
    if db is None:
        raise HTTPException(503, detail="Database not configured.")

    password_hash = hash_password(req.password)
    response = (
        db.table("users")
        .select("*")
        .eq("email", req.email)
        .eq("password_hash", password_hash)
        .eq("is_active", True)
        .execute()
    )

    if not response.data:
        raise HTTPException(401, detail={"error": "invalid_credentials", "message": "Invalid email or password."})

    user = response.data[0]
    token = secrets.token_urlsafe(48)
    db.table("users").update({"auth_token": token}).eq("id", user["id"]).execute()

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "plan": user.get("plan", "free"),
            "credits_remaining": user.get("credits_remaining", 0),
            "credits_total": user.get("credits_total", 0),
            "created_at": user.get("created_at", ""),
        },
    }


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(token: str):
    db = get_db()
    if db is None:
        raise HTTPException(503, detail="Database not configured.")

    response = db.table("users").select("*").eq("auth_token", token).eq("is_active", True).execute()
    if not response.data:
        raise HTTPException(401, detail={"error": "invalid_token", "message": "Invalid or expired token."})

    user = response.data[0]
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "plan": user.get("plan", "free"),
        "credits_remaining": user.get("credits_remaining", 0),
        "credits_total": user.get("credits_total", 0),
        "created_at": user.get("created_at", ""),
    }


async def verify_token(token: str) -> Optional[dict]:
    db = get_db()
    if db is None:
        return None

    response = db.table("users").select("*").eq("auth_token", token).eq("is_active", True).execute()
    if not response.data:
        return None

    return response.data[0]
