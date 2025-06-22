"""
Application configuration
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./travel2.sqlite"
    
    # API Keys
    tavily_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Customer Support Bot"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    verbose_logging: bool = False  # Set to True for detailed tool/agent logging
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with environment variables
        if os.getenv("VERBOSE_LOGGING", "").lower() == "true":
            self.verbose_logging = True
        if os.getenv("LOG_LEVEL"):
            self.log_level = os.getenv("LOG_LEVEL")
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
