from uuid import UUID

from app.auth.security import hash_password
from app.core.exceptions import ConflictError
from app.models.user import User
from app.repositories.preferences import PreferencesRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.preferences import PreferencesUpdate
from app.schemas.user import ProfileUpdate


class UserService:
    def __init__(self, users: UserRepository, preferences: PreferencesRepository) -> None:
        self.users = users
        self.preferences = preferences

    async def register(self, request: RegisterRequest) -> User:
        if await self.users.get_by_email(str(request.email)):
            raise ConflictError("An account with this email already exists")
        user = await self.users.create(
            email=str(request.email).lower(),
            password_hash=hash_password(request.password),
            is_verified=False,
        )
        await self.users.create_profile(user.id, first_name=request.first_name, last_name=request.last_name)
        await self.preferences.create(user_id=user.id)
        created = await self.users.get_with_relations(user.id)
        if created is None:
            raise RuntimeError("Registered user could not be loaded")
        return created

    async def update_profile(self, user_id: UUID, request: ProfileUpdate) -> object:
        user = await self.users.get_with_relations(user_id)
        if user is None:
            raise ValueError("User not found")
        values = request.persisted_values()
        if user.profile is None:
            return await self.users.create_profile(user_id, **values)
        return await self.users.update(user.profile, **values)

    async def update_preferences(self, user_id: UUID, request: PreferencesUpdate) -> object:
        preferences = await self.preferences.get_for_user(user_id)
        values = request.persisted_values()
        if preferences is None:
            return await self.preferences.create(user_id=user_id, **values)
        merged_min = values.get("min_trip_days", preferences.min_trip_days)
        merged_max = values.get("max_trip_days", preferences.max_trip_days)
        if merged_min > merged_max:
            raise ValueError("min_trip_days cannot exceed max_trip_days")
        return await self.preferences.update(preferences, **values)
