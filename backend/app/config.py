from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    database_url: str | None = None
    frontend_origin: str = "http://127.0.0.1:3000"
    max_upload_bytes: int = 5_000_000
    retrieval_mode: Literal["auto","file","postgresql"] = "auto"
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

settings = Settings()
