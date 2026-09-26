import json
from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Вычисление путей:
# __file__ = backend/app/core/config.py
# parents[0] = backend/app/core
# parents[1] = backend/app
# parents[2] = backend
# parents[3] = PROJECT_ROOT
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "VSM Conductor Simulator"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    POLZA_API_KEY: str = "your_polza_api_key_here"
    POLZA_BASE_URL: str = "https://polza.ai/api/v1"
    POLZA_CHAT_MODEL: str = "google/gemini-2.5-flash"
    POLZA_STT_MODEL: str = "openai/whisper-large-v3-turbo"

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    return json.loads(v_stripped)
                except Exception:
                    pass
            return [item.strip() for item in v_stripped.split(",") if item.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]
        return ["*"]


settings = Settings()
