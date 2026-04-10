"""
Centralized configuration from environment variables.
Uses Pydantic BaseSettings for validation and .env file support.
"""

from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    # Anthropic (LLM)
    anthropic_api_key: SecretStr = SecretStr("")

    # Webhook
    webhook_secret: SecretStr = SecretStr("")
    webhook_port: int = 8100

    # CORS
    cors_origins: str = "https://assess.zanovix.com,http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton — import this from other modules
settings = Settings()
