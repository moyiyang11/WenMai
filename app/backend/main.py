"""FastAPI 应用入口。

启动：
    cd app/backend
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db
from routers import dashboard, novels, settings as settings_router, skills, styles

app = FastAPI(title="AI 小说风格蒸馏与 Skill 导出系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(novels.router)
app.include_router(styles.router)
app.include_router(skills.router)
app.include_router(settings_router.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    from services import settings_store

    return {
        "status": "ok",
        "llm_enabled": settings_store.llm_enabled(),
        "model": settings_store.get_model() if settings_store.llm_enabled() else "mock",
    }
