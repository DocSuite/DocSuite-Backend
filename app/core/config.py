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
    password_reset_token_expire_minutes: int = Field(default=30, validation_alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES")
    admin_email: str = Field(default="admin@docsuite.edu.pe", validation_alias="ADMIN_EMAIL")
    admin_full_name: str = Field(default="Administrador DocSuite", validation_alias="ADMIN_FULL_NAME")
    admin_password: str = Field(default="DocSuite123", validation_alias="ADMIN_PASSWORD")
    mail_host: str = Field(default="smtp.gmail.com", validation_alias="MAIL_HOST")
    mail_port: int = Field(default=587, validation_alias="MAIL_PORT")
    mail_username: str | None = Field(default=None, validation_alias="MAIL_USERNAME")
    mail_password: str | None = Field(default=None, validation_alias="MAIL_PASSWORD")
    mail_from: str | None = Field(default=None, validation_alias="MAIL_FROM")
    frontend_url: str = Field(default="http://localhost:4200", validation_alias="FRONTEND_URL")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o"

    upload_dir: Path = Path("storage/uploads")
    processed_dir: Path = Path("storage/processed")
    temp_dir: Path = Path("storage/temp")
    storage_bin_dir: Path = Path("storage/bin")
    max_upload_file_size_mb: int = Field(default=200, validation_alias="MAX_UPLOAD_FILE_SIZE_MB")

    whisper_model: str = "large-v3"
    whisper_device: str = Field(default="auto", validation_alias="WHISPER_DEVICE")
    whisper_language: str = Field(default="auto", validation_alias="WHISPER_LANGUAGE")
    whisper_chunk_threshold: int = Field(default=1800, validation_alias="WHISPER_CHUNK_THRESHOLD")
    whisper_chunk_size: int = Field(default=600, validation_alias="WHISPER_CHUNK_SIZE")
    max_concurrent_jobs_per_user: int = Field(default=2, validation_alias="MAX_CONCURRENT_JOBS_PER_USER")
    pyannote_model: str = "pyannote/speaker-diarization-community-1"
    pyannote_device: str = Field(default="auto", validation_alias="PYANNOTE_DEVICE")
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    transcription_provider: str = Field(default="local", validation_alias="TRANSCRIPTION_PROVIDER")
    deepgram_api_key: str | None = Field(default=None, validation_alias="DEEPGRAM_API_KEY")
    deepgram_model: str = Field(default="nova-3", validation_alias="DEEPGRAM_MODEL")
    deepgram_language: str = Field(default="es", validation_alias="DEEPGRAM_LANGUAGE")
    deepgram_diarize_model: str = Field(default="latest", validation_alias="DEEPGRAM_DIARIZE_MODEL")
    deepgram_timeout_seconds: int = Field(default=1800, validation_alias="DEEPGRAM_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
