import asyncio

from sqlalchemy import select

from app.auth.security import hash_password
from app.database.database import AsyncSessionLocal, dispose_database
from app.models.destination import Destination
from app.models.enums import BudgetLevel, TravelStyle
from app.models.preferences import UserPreferences
from app.models.user import User, UserProfile


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == "demo@storymiles.app"))
        if user is None:
            user = User(email="demo@storymiles.app", password_hash=hash_password("StoryMilesDemo2026!"), is_verified=True)
            session.add(user)
            await session.flush()
            session.add(UserProfile(user_id=user.id, first_name="Demo", last_name="Traveler", bio="Exploring the world one itinerary at a time.", country="Pakistan", city="Karachi"))
            session.add(UserPreferences(user_id=user.id, travel_styles=[TravelStyle.CULTURAL, TravelStyle.FOOD, TravelStyle.NATURE], budget_level=BudgetLevel.MEDIUM, preferred_currencies=["USD", "PKR"], preferred_languages=["en"], min_trip_days=3, max_trip_days=10))
            session.add_all([
                Destination(user_id=user.id, name="Istanbul", country="Türkiye", city="Istanbul", description="A vibrant crossroads of history, food, and the Bosphorus.", tags=["history", "food", "culture"], is_favorite=True),
                Destination(user_id=user.id, name="Hunza Valley", country="Pakistan", city="Gilgit-Baltistan", description="High mountain scenery, forts, and welcoming villages.", tags=["nature", "mountains", "culture"], is_favorite=True),
            ])
            await session.commit()


async def _main() -> None:
    try:
        await seed()
    finally:
        # Dispose inside the same event loop; a second asyncio.run() would
        # try to close asyncpg connections on a dead loop and crash.
        await dispose_database()


if __name__ == "__main__":
    asyncio.run(_main())
