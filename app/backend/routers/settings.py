"""系统设置路由：在网页里配置 DeepSeek API Key（落库，不进 git）。"""
from __future__ import annotations

import httpx
from fastapi import APIRouter

import schemas
from core.config import settings as env_settings
from services import settings_store

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _source() -> str:
    if settings_store._get(settings_store.KEY_DEEPSEEK_API_KEY):
        return "db"
    if env_settings.deepseek_api_key.strip():
        return "env"
    return "none"


@router.get("/llm", response_model=schemas.LLMConfigOut)
def get_llm_config():
    return schemas.LLMConfigOut(
        configured=settings_store.llm_enabled(),
        source=_source(),
        model=settings_store.get_model(),
        base_url=settings_store.get_base_url(),
        masked_key=settings_store.masked_api_key(),
    )


@router.put("/llm", response_model=schemas.LLMConfigOut)
def update_llm_config(payload: schemas.LLMConfigUpdate):
    settings_store.update_llm_config(payload.api_key, payload.model, payload.base_url)
    return get_llm_config()


@router.post("/llm/test", response_model=schemas.LLMTestResult)
def test_llm():
    """用当前配置做一次最小连通性测试。"""
    api_key = settings_store.get_api_key().strip()
    if not api_key:
        return schemas.LLMTestResult(ok=False, message="尚未配置 API Key（当前为 mock 模式）")
    try:
        resp = httpx.post(
            f"{settings_store.get_base_url()}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": settings_store.get_model(),
                "messages": [{"role": "user", "content": "ping，仅回复 ok"}],
                "max_tokens": 5,
                "stream": False,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return schemas.LLMTestResult(ok=True, message=f"连接成功：{settings_store.get_model()}")
        return schemas.LLMTestResult(ok=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:  # noqa: BLE001
        return schemas.LLMTestResult(ok=False, message=f"请求失败：{exc}")
