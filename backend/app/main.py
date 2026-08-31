from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.auth import APIKeyMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.routers import companies, agents, tasks, budgets, workflows, execution
from app.services.budget import BudgetExceededError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed exclusively by Alembic.
    # Run: alembic upgrade head
    if settings.SECRET_KEY.startswith("change-me"):
        logger.warning(
            "SECRET_KEY is still the insecure default. "
            "Set a strong SECRET_KEY in .env before production use."
        )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

_origins = getattr(settings, "ALLOWED_ORIGINS", None)
if _origins:
    allow_origins = [o.strip() for o in _origins.split(",") if o.strip()]
else:
    allow_origins = ["*"]

app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])


@app.exception_handler(BudgetExceededError)
async def budget_exceeded_handler(request: Request, exc: BudgetExceededError):
    return JSONResponse(
        status_code=409,
        content={
            "detail": str(exc),
            "agent_id": exc.agent_id,
            "remaining": exc.remaining,
            "required": exc.required,
            "error": "budget_exceeded",
        },
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
def root():
    return {
        "message": "AI Company Orchestrator API",
        "docs": "/docs",
        "phase": "2.2 – rate limit + OpenAI + stuck recovery",
    }
