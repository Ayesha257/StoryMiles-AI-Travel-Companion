from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_destination_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.schemas.destination import DestinationCreate, DestinationResponse, DestinationUpdate
from app.services.destination import DestinationService

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.get("", response_model=list[DestinationResponse])
async def list_destinations(
    current_user: CurrentUser,
    service: Annotated[DestinationService, Depends(get_destination_service)],
    offset: int = 0,
    limit: int = 100,
) -> object:
    return await service.list(current_user.id, offset=max(offset, 0), limit=min(max(limit, 1), 100))


@router.post("", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_destination(
    request: DestinationCreate,
    current_user: CurrentUser,
    service: Annotated[DestinationService, Depends(get_destination_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    destination = await service.create(current_user.id, request)
    await db.commit()
    return destination


@router.patch("/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: UUID,
    request: DestinationUpdate,
    current_user: CurrentUser,
    service: Annotated[DestinationService, Depends(get_destination_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    destination = await service.update(current_user.id, destination_id, request)
    await db.commit()
    return destination


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(
    destination_id: UUID,
    current_user: CurrentUser,
    service: Annotated[DestinationService, Depends(get_destination_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await service.delete(current_user.id, destination_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
