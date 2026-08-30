from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Company Orchestrator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./orchestrator.db"
    # For production: postgresql://user:pass@localhost/orchestrator

    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS – comma-separated list, e.g. "http://localhost:3000,https://app.example.com"
    # Empty / unset → allow all ("*") for local dev
    ALLOWED_ORIGINS: Optional[str] = None

    # Budget defaults (USD)
    DEFAULT_AGENT_MONTHLY_BUDGET: float = 50.0
    DEFAULT_COMPANY_MONTHLY_BUDGET: float = 500.0

    # Provider keys (loaded from env)
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Auth – if set, all /api/* routes require header X-API-Key
    # Leave empty for local open access (dev only)
    ORCHESTRATOR_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
