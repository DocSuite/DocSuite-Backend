from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DocSuite API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/docsuite",
        validation_alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o"

    upload_dir: Path = Path("storage/uploads")
    processed_dir: Path = Path("storage/processed")
    temp_dir: Path = Path("storage/temp")
    storage_bin_dir: Path = Path("storage/bin")

    whisper_model: str = "large-v3"
    whisper_device: str = Field(default="auto", validation_alias="WHISPER_DEVICE")
    pyannote_model: str = "pyannote/speaker-diarization-community-1"
    pyannote_device: str = Field(default="auto", validation_alias="PYANNOTE_DEVICE")
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")


@lru_cache
def get_settings() -> Settings:
    return Settings()
