from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routes import dedup, standardize, clean, health, auth, api_keys, billing, afdian
from .billing import webhook
from .routes import afdian_webhook

static_dir = Path(__file__).parent.parent / "static"
assets_dir = Path(__file__).parent.parent / "assets"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="数据清洗API — 去重、标准化、验证，一键全流程。",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if static_dir.exists():
    app.mount("/css", StaticFiles(directory=static_dir / "css"), name="css")
    app.mount("/js", StaticFiles(directory=static_dir / "js"), name="js")

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

prefix = settings.api_prefix

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=prefix, tags=["auth"])
app.include_router(api_keys.router, prefix=prefix, tags=["api_keys"])
app.include_router(dedup.router, prefix=prefix, tags=["dedup"])
app.include_router(standardize.router, prefix=prefix, tags=["standardize"])
app.include_router(clean.router, prefix=prefix, tags=["clean"])
app.include_router(webhook.router, tags=["webhook"])
app.include_router(billing.router, tags=["billing"])
app.include_router(afdian.router, tags=["afdian"])
app.include_router(afdian_webhook.router, tags=["afdian_webhook"])


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(static_dir / "index.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return FileResponse(static_dir / "dashboard.html")


@app.get("/api-info")
async def api_info():
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
