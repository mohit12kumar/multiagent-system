"""
backend/core/config.py

Centralised application configuration using Pydantic Settings.

All configuration is loaded from environment variables and/or a .env file.
No scattered os.getenv() calls. Import `settings` anywhere in the codebase
and access typed, validated configuration properties.

Usage:
    from backend.core.config import settings
    engine = create_engine(settings.database_url, pool_size=settings.database_pool_size)
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings.
    All values can be overridden by environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # Silently ignore unknown env vars
    )

    # ── Application ────────────────────────────────────────────────────────────
    env:         str = "development"
    api_port:    int = 8000
    log_level:   str = "INFO"
    app_version: str = "2.1.0"

    # ── Security ───────────────────────────────────────────────────────────────
    jwt_secret_key:                str         # Required — no default (must be in .env)
    jwt_algorithm:                 str = "HS256"
    access_token_expire_minutes:   int = 1440  # 24 hours
    refresh_token_expire_days:     int = 7

    # ── Database ───────────────────────────────────────────────────────────────
    mysql_host:     str = "localhost"
    mysql_port:     int = 3306
    mysql_user:     str = "root"
    mysql_password: str = ""
    mysql_database: str = "clinical_multiagent"

    # Connection pool — tuned for clinical intranet (< 50 concurrent users)
    database_pool_size:     int = 10
    database_max_overflow:  int = 20
    database_pool_timeout:  int = 30
    database_pool_recycle:  int = 3600   # Recycle connections every 1 hour

    # ── External APIs ──────────────────────────────────────────────────────────
    groq_api_key:           str = ""
    langchain_tracing_v2:   bool = False
    langchain_api_key:      str = ""
    langchain_project:      str = "multiagent-ner"

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_host:    str = "localhost"
    chroma_port:    int = 8001

    # ── Pipeline timeouts (seconds) ────────────────────────────────────────────
    pipeline_timeout_seconds:   int = 120
    llm_timeout_seconds:        int = 30
    ocr_timeout_seconds:        int = 60
    agent_timeout_seconds:      int = 30

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allowed_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:3000"
    )

    # ── Rate limiting ──────────────────────────────────────────────────────────
    rate_limit_requests: int = 100
    rate_limit_window:   int = 60

    # ── Feature flags ─────────────────────────────────────────────────────────
    # Enable/disable major pipeline components without redeploying.
    enable_ocr:              bool = True
    enable_fhir:             bool = True
    enable_risk_engine:      bool = True
    enable_llm:              bool = True
    enable_phi_redaction:    bool = True
    enable_knowledge_graph:  bool = False   # Experimental

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def database_url(self) -> str:
        """Full MySQL connection URL."""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def server_url(self) -> str:
        """MySQL server URL without database (for CREATE DATABASE IF NOT EXISTS)."""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.env.lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.
    lru_cache(maxsize=1) ensures the .env file is read exactly once at startup.
    """
    return Settings()


# Module-level singleton — import this directly for convenience:
#   from backend.core.config import settings
settings = get_settings()
