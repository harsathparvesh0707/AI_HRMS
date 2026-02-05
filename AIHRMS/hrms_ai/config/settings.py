"""
Configuration settings using environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # --------------------
    # Database
    # --------------------
    database_url: str

    # --------------------
    # Redis
    # --------------------
    redis_host: str
    redis_port: int

    # --------------------
    # Ollama
    # --------------------
    ollama_model: str
    ollama_base_url: str
    ollama_timeout: int = 30

    # --------------------
    # Vector DB
    # --------------------
    vector_persist_dir: str
    embedding_model: str

    # --------------------
    # RAG
    # --------------------
    gemini_api_key: str
    use_hybrid_search: str = "true"

    # --------------------
    # API
    # --------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # --------------------
    # CORS
    # --------------------
    allowed_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
