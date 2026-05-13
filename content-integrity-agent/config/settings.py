"""
Configuration management for Content Integrity Agent.
Supports .env files and environment variables.
"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings with sensible defaults."""
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.3
    auto_fix_threshold: float = 0.90
    notify_threshold: float = 0.60
    http_timeout: int = 15
    enable_llm: bool = True
    cache_dir: str = ".cache"
    fixtures_dir: str = "fixtures"
    dry_run: bool = True
    db_path: str = "data/cia.db"
    cors_origin: str = "http://localhost:5173"
    ux_standards_doc_id: str = "1xWKWhvURu7rKmhjhwf1OSvMecBlD0qLpLJmWq2TawwY"
    copy_style_guide_doc_id: str = "1AX-kSNztuAmShEoohe8L3LNLRnSKF7I0qkZGNeoGOok"
    google_service_account_info: str = ""
    compliance_cache_ttl: int = 3600

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            llm_temperature=float(os.environ.get("LLM_TEMPERATURE", "0.3")),
            auto_fix_threshold=float(os.environ.get("AUTO_FIX_THRESHOLD", "0.90")),
            notify_threshold=float(os.environ.get("NOTIFY_THRESHOLD", "0.60")),
            http_timeout=int(os.environ.get("HTTP_TIMEOUT", "15")),
            enable_llm=os.environ.get("ENABLE_LLM", "true").lower() == "true",
            cache_dir=os.environ.get("CACHE_DIR", ".cache"),
            fixtures_dir=os.environ.get("FIXTURES_DIR", "fixtures"),
            dry_run=os.environ.get("DRY_RUN", "true").lower() == "true",
            db_path=os.environ.get("CIA_DB_PATH", "data/cia.db"),
            cors_origin=os.environ.get("CIA_CORS_ORIGIN", "http://localhost:5173"),
            ux_standards_doc_id=os.environ.get(
                "UX_STANDARDS_DOC_ID", "1xWKWhvURu7rKmhjhwf1OSvMecBlD0qLpLJmWq2TawwY"
            ),
            copy_style_guide_doc_id=os.environ.get(
                "COPY_STYLE_GUIDE_DOC_ID", "1AX-kSNztuAmShEoohe8L3LNLRnSKF7I0qkZGNeoGOok"
            ),
            google_service_account_info=os.environ.get("GOOGLE_SERVICE_ACCOUNT_INFO", ""),
            compliance_cache_ttl=int(os.environ.get("COMPLIANCE_CACHE_TTL", "3600")),
        )