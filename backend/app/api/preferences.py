from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_user_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.repositories.preferences import PreferencesRepository
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.services.user import UserService

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get("/me", response_model=PreferencesResponse)
async def get_preferences(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]) -> object:
    preferences = await PreferencesRepository(db).get_for_user(current_user.id)
    if preferences is None:
        preferences = await PreferencesRepository(db).create(user_id=current_user.id)
        await db.commit()
    return preferences


@router.patch("/me", response_model=PreferencesResponse)
async def update_preferences(
    request: PreferencesUpdate,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    preferences = await service.update_preferences(current_user.id, request)
    await db.commit()
    return preferences
