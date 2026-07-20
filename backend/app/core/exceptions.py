from fastapi import HTTPException, status


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Application error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource conflict"


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication failed"


class VerificationError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Email verification failed"


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Please wait before trying again"


class EmailDeliveryError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Verification email could not be sent"


class AIServiceError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "AI provider request failed"


def as_http_exception(error: AppError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)
