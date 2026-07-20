from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token
from app.auth.service import authenticate_user, issue_tokens
from app.database.session import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    ForgotPasswordRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.email_verification import EmailVerificationService
from app.services.user import UserService
from app.api.dependencies import get_email_verification_service, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    verification: Annotated[EmailVerificationService, Depends(get_email_verification_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    user = await service.register(request)
    await verification.send_code(user)
    await db.commit()
    return RegisterResponse(
        email=user.email,
        message="We sent a 6-digit verification code to your email",
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: VerifyEmailRequest,
    verification: Annotated[EmailVerificationService, Depends(get_email_verification_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await verification.verify(str(request.email).lower(), request.code)
    await db.commit()
    return MessageResponse(message="Email verified. You can now sign in")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    verification: Annotated[EmailVerificationService, Depends(get_email_verification_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await verification.resend(str(request.email).lower())
    await db.commit()
    return MessageResponse(message="If the account is awaiting verification, a new code has been sent")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    verification: Annotated[EmailVerificationService, Depends(get_email_verification_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await verification.request_password_reset(str(request.email).lower())
    await db.commit()
    return MessageResponse(
        message="If a verified account exists for that email, a password reset code has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    verification: Annotated[EmailVerificationService, Depends(get_email_verification_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await verification.reset_password(
        str(request.email).lower(),
        request.code,
        request.new_password,
    )
    await db.commit()
    return MessageResponse(message="Password updated. You can now sign in")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    user = await authenticate_user(db, str(request.email), request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email before signing in",
        )
    return issue_tokens(user)


@router.post("/token", response_model=TokenResponse, summary="OAuth2 token (Swagger Authorize)")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Use your email address as the username. Used by Swagger UI's Authorize button."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verify your email before signing in",
        )
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    try:
        user_id = UUID(decode_token(request.refresh_token, expected_type="refresh")["sub"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    from app.repositories.user import UserRepository

    user = await UserRepository(db).get(user_id)
    if user is None or not user.is_active or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return issue_tokens(user)
