"""应用配置。使用 pydantic-settings 从环境变量 / .env 读取。"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # DeepSeek / LLM
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 数据库
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"

    # 蒸馏采样（单次 API 调用最大字符数；中文约 1 char≈1 token，留余量给 schema/system prompt）
    distill_sample_chars: int = 80000

    @property
    def llm_enabled(self) -> bool:
        """是否配置了真实 API key。未配置时走 mock。"""
        return bool(self.deepseek_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# 确保数据目录存在
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "exports").mkdir(parents=True, exist_ok=True)
