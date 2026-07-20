from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.schemas.user import ProfileResponse, ProfileUpdate, UserResponse
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> object:
    return current_user


@router.patch("/me/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdate,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    profile = await service.update_profile(current_user.id, request)
    await db.commit()
    return profile
