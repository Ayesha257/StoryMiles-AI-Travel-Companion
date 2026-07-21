from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.circuit_breaker import ai_circuit_breaker
from app.core.handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.sentry import init_sentry
from app.database.database import dispose_database
from app.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.ml.model_loader import get_model_health, load_recommendation_artifacts


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging("DEBUG" if settings.debug else "INFO", json_logs=settings.log_json)
    init_sentry()
    Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
    load_recommendation_artifacts()
    yield
    await dispose_database()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    # AnyHttpUrl serializes with a trailing slash; browsers send Origin without one.
    allow_origins=[str(origin).rstrip("/") for origin in settings.cors_origins],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
# StaticFiles requires the directory to exist at import time (before lifespan runs).
Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_directory), name="uploads")
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "recommendation_model": get_model_health(),
        "circuits": {
            "groq": ai_circuit_breaker.status("groq"),
            "gemini": ai_circuit_breaker.status("gemini"),
        },
    }
