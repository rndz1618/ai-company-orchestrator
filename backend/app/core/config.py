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

    # Rate limiting (requests per window per client key/IP)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    # Stricter limit for execution endpoints
    RATE_LIMIT_EXECUTION_REQUESTS: int = 10
    RATE_LIMIT_EXECUTION_WINDOW_SECONDS: int = 60

    # Stuck RUNNING recovery: mark FAILED after this many minutes
    STUCK_RUNNING_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
