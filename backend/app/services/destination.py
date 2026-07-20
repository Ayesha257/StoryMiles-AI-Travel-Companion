from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.models.destination import Destination
from app.repositories.destination import DestinationRepository
from app.schemas.destination import DestinationCreate, DestinationUpdate


class DestinationService:
    def __init__(self, repository: DestinationRepository) -> None:
        self.repository = repository

    async def create(self, user_id: UUID, request: DestinationCreate) -> Destination:
        return await self.repository.create(user_id=user_id, **request.model_dump())

    async def list(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[Destination]:
        return await self.repository.list_for_user(user_id, offset=offset, limit=limit)

    async def update(self, user_id: UUID, destination_id: UUID, request: DestinationUpdate) -> Destination:
        destination = await self.repository.get_for_user(destination_id, user_id)
        if destination is None:
            raise NotFoundError("Destination not found")
        return await self.repository.update(destination, **request.model_dump(exclude_unset=True))

    async def delete(self, user_id: UUID, destination_id: UUID) -> None:
        destination = await self.repository.get_for_user(destination_id, user_id)
        if destination is None:
            raise NotFoundError("Destination not found")
        await self.repository.delete(destination)
