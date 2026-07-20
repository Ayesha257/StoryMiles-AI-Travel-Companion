from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_itinerary_generator
from app.auth.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.itinerary import Itinerary
from app.repositories.itinerary import ItineraryRepository
from app.schemas.itinerary import ItineraryCreate, ItineraryGenerateRequest, ItineraryResponse, ItineraryUpdate
from app.services.itinerary import ItineraryGenerator

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


@router.post("/generate", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def generate_itinerary(
    request: ItineraryGenerateRequest,
    current_user: CurrentUser,
    generator: Annotated[ItineraryGenerator, Depends(get_itinerary_generator)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ItineraryResponse:
    itinerary = await generator.generate(current_user.id, request)
    await db.commit()
    return itinerary


@router.get("", response_model=list[ItineraryResponse])
async def list_itineraries(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = 0,
    limit: int = 100,
) -> object:
    return await ItineraryRepository(db).list_for_user(current_user.id, offset=max(offset, 0), limit=min(max(limit, 1), 100))


@router.post("", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def save_itinerary(
    request: ItineraryCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Itinerary:
    itinerary = await ItineraryRepository(db).create(user_id=current_user.id, **request.model_dump())
    await db.commit()
    return itinerary


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Itinerary:
    itinerary = await ItineraryRepository(db).get_for_user(itinerary_id, current_user.id)
    if itinerary is None:
        raise NotFoundError("Itinerary not found")
    return itinerary


@router.patch("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: UUID,
    request: ItineraryUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Itinerary:
    repository = ItineraryRepository(db)
    itinerary = await repository.get_for_user(itinerary_id, current_user.id)
    if itinerary is None:
        raise NotFoundError("Itinerary not found")
    result = await repository.update(itinerary, **request.model_dump(exclude_unset=True))
    await db.commit()
    return result


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    repository = ItineraryRepository(db)
    itinerary = await repository.get_for_user(itinerary_id, current_user.id)
    if itinerary is None:
        raise NotFoundError("Itinerary not found")
    await repository.delete(itinerary)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
