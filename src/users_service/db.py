import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from users_service.models import *  # noqa


def create_engine() -> AsyncEngine:
    """Create database engine."""
    return create_async_engine(os.environ.get("DATABASE_URL"))


async def create_db_and_tables():
    """Create all tables in the database."""
    async with create_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


def create_session() -> AsyncSession:
    """Create a database session."""
    return sessionmaker(create_engine(), class_=AsyncSession, expire_on_commit=False)()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Wrapper for create_session so we can use it in FastAPI's Depends(...)."""
    async with create_session() as session:
        yield session
