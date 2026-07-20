from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_token
from app.auth.service import authenticate_user, issue_tokens
from app.database.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.user import UserService
from app.api.dependencies import get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    user = await service.register(request)
    await db.commit()
    tokens = issue_tokens(user)
    return RegisterResponse(user=UserResponse.model_validate(user), **tokens.model_dump())


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    user = await authenticate_user(db, str(request.email), request.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
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
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    try:
        user_id = UUID(decode_token(request.refresh_token, expected_type="refresh")["sub"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    from app.repositories.user import UserRepository

    user = await UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return issue_tokens(user)
