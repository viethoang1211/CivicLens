import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    settings.database_url.replace("postgresql+psycopg", "postgresql+psycopg"),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db(clearance_level: int | None = None) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        if clearance_level is not None:
            await session.execute(text(f"SET LOCAL app.clearance_level = '{clearance_level}'"))
        yield session
