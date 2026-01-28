"""
Configuration settings using environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres%40123@localhost:5432/hrms_vector_db"
    
    # LLM Configuration
    ollama_model: str = "qwen2:0.5b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 30
    
    # Vector Database
    vector_persist_dir: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # RAG + Hybrid Search Configuration
    gemini_api_key: str = "AIzaSyDpBuzaSqef2cL9UbXCvIIKLYkkGszs-no"
    use_hybrid_search: str = "true"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()