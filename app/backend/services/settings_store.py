"""运行时配置读写。

优先级：数据库 settings 表（网页里填的） > .env 环境变量。
API Key 只存在 data/app.db（已 gitignore），不落到任何会被提交的文件，
从而避免上传 GitHub 时泄露。
"""
from __future__ import annotations

from sqlalchemy import select

from core.config import settings as env_settings
from core.database import SessionLocal
from models import Setting

# 允许通过网页管理的键
KEY_DEEPSEEK_API_KEY = "deepseek_api_key"
KEY_DEEPSEEK_MODEL = "deepseek_model"
KEY_DEEPSEEK_BASE_URL = "deepseek_base_url"


def _get(key: str) -> str | None:
    with SessionLocal() as db:
        row = db.get(Setting, key)
        return row.value if row and row.value else None


def _set(key: str, value: str) -> None:
    with SessionLocal() as db:
        row = db.get(Setting, key)
        if row:
            row.value = value
        else:
            db.add(Setting(key=key, value=value))
        db.commit()


def get_api_key() -> str:
    return _get(KEY_DEEPSEEK_API_KEY) or env_settings.deepseek_api_key


def get_model() -> str:
    return _get(KEY_DEEPSEEK_MODEL) or env_settings.deepseek_model


def get_base_url() -> str:
    return _get(KEY_DEEPSEEK_BASE_URL) or env_settings.deepseek_base_url


def llm_enabled() -> bool:
    return bool(get_api_key().strip())


def masked_api_key() -> str:
    """脱敏后的 key，仅用于回显给前端（绝不返回明文）。"""
    k = get_api_key().strip()
    if not k:
        return ""
    if len(k) <= 8:
        return "*" * len(k)
    return f"{k[:4]}{'*' * (len(k) - 8)}{k[-4:]}"


def update_llm_config(api_key: str | None, model: str | None, base_url: str | None) -> None:
    # api_key 为 None 表示不修改；为空字符串表示清除
    if api_key is not None:
        _set(KEY_DEEPSEEK_API_KEY, api_key.strip())
    if model:
        _set(KEY_DEEPSEEK_MODEL, model.strip())
    if base_url:
        _set(KEY_DEEPSEEK_BASE_URL, base_url.strip())
