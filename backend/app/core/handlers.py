import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status

from app.core.exceptions import AppError, RateLimitError, ServiceUnavailableError
from app.core.logging import log_event

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RateLimitError)
    async def handle_rate_limit(request: Request, exc: RateLimitError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "retry_after": exc.retry_after,
                "code": "rate_limited",
            },
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(ServiceUnavailableError)
    async def handle_service_unavailable(request: Request, exc: ServiceUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "retry_after": exc.retry_after,
                "code": "service_unavailable",
            },
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if isinstance(exc, (RateLimitError, ServiceUnavailableError)):
            # Defensive — specific handlers above should win, but keep shape consistent.
            retry_after = getattr(exc, "retry_after", 60)
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )
        log_event(
            logger,
            logging.WARNING if exc.status_code < 500 else logging.ERROR,
            "Application error",
            event="app_error",
            endpoint=f"{request.method} {request.url.path}",
            error_type=type(exc).__name__,
            extra={"detail": exc.detail},
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database integrity error: %s", exc.orig)
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": "Conflicting database value"})

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error", exc_info=exc)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Database operation failed"})

    @app.exception_handler(OSError)
    async def handle_connection_error(_: Request, exc: OSError) -> JSONResponse:
        logger.exception("Connection error", exc_info=exc)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Database unavailable"})

    @app.exception_handler(ValueError)
    async def handle_value_error(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        log_event(
            logger,
            logging.ERROR,
            "Unhandled exception",
            event="unhandled_exception",
            endpoint=f"{request.method} {request.url.path}",
            error_type=type(exc).__name__,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again."},
        )
