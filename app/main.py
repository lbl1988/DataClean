from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, get_cors_origins
from .routes import dedup, standardize, clean, health, auth, api_keys
from .billing import webhook

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="数据清洗API — 去重、标准化、验证，一键全流程。",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_prefix

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=prefix, tags=["auth"])
app.include_router(api_keys.router, prefix=prefix, tags=["api_keys"])
app.include_router(dedup.router, prefix=prefix, tags=["dedup"])
app.include_router(standardize.router, prefix=prefix, tags=["standardize"])
app.include_router(clean.router, prefix=prefix, tags=["clean"])
app.include_router(webhook.router, tags=["webhook"])


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "register": f"{prefix}/auth/register",
            "login": f"{prefix}/auth/login",
            "me": f"{prefix}/auth/me",
            "create_key": f"{prefix}/keys",
            "dedup": f"{prefix}/dedup",
            "standardize": f"{prefix}/standardize",
            "clean": f"{prefix}/clean",
            "health": "/health",
        },
    }
