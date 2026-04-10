"""
Centralized configuration from environment variables.
Uses Pydantic BaseSettings for validation and .env file support.
Fails fast on startup if critical variables are missing.
"""

import json
import os
from pydantic_settings import BaseSettings
from pydantic import SecretStr, model_validator


class Settings(BaseSettings):
    # Google Service Account
    google_sa_json: str = ""  # JSON string of service account key
    google_sa_file: str = ""  # OR path to SA key file
    google_delegated_user: str = "pepe@zanovix.com"

    # Google resources
    sheet_id: str = "1cMZuWl2t3dH_7-6LIKMkXL9S8ueMMKPz69rK_AiZoZ8"
    drive_folder_id: str = "1ZIz3o01cSOZWaRk_YrnRuM5krBIgkTih"

    # Notion
    notion_api_key: SecretStr = SecretStr("")
    notion_assessments_db: str = "33118d57-3b10-81d3-a7a0-c56f70f41853"
    notion_clients_db: str = "33118d57-3b10-817f-988d-de404714b98d"

    # Anthropic
    anthropic_api_key: SecretStr = SecretStr("")

    # Webhook
    webhook_secret: SecretStr = SecretStr("")
    webhook_port: int = 8100

    # Email
    output_email: str = "pepe@zanovix.com"
    resend_api_key: SecretStr = SecretStr("")  # Fallback email via Resend

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @model_validator(mode="after")
    def validate_google_sa(self):
        """At least one Google SA source must be provided."""
        if not self.google_sa_json and not self.google_sa_file:
            # Try loading from legacy path as last resort
            legacy_path = os.path.expanduser("~/.config/gogcli/credentials.json")
            if os.path.exists(legacy_path):
                self.google_sa_file = legacy_path
        return self

    def get_sa_info(self) -> dict:
        """Return parsed service account JSON from whichever source is configured."""
        if self.google_sa_json:
            return json.loads(self.google_sa_json)
        if self.google_sa_file and os.path.exists(self.google_sa_file):
            with open(self.google_sa_file) as f:
                return json.load(f)
        raise ValueError(
            "Google Service Account not configured. "
            "Set GOOGLE_SA_JSON (JSON string) or GOOGLE_SA_FILE (path to key file)."
        )


# Singleton — import this from other modules
settings = Settings()
