"""Application configuration using Pydantic Settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration, populated from environment variables."""

    session_timeout_seconds: int = 7200
    max_sessions: int = 100
    cors_origins: list[str] = ["*"]
    data_dir: str = Field(default="data/mixtures", description="Path to bundled mixture data files")

    model_config = {"env_prefix": "PP_"}
