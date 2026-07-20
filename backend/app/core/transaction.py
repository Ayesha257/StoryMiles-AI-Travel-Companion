from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


class Transaction:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> AsyncSession:
        if not self.session.in_transaction():
            self._transaction = await self.session.begin()
        else:
            self._transaction = await self.session.begin_nested()
        return self.session

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if exc_type is None:
            await self._transaction.commit()
        else:
            await self._transaction.rollback()
        return False


async def transactional(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    async with Transaction(session) as transaction_session:
        yield transaction_session
