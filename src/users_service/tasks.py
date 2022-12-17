import os

from asgiref.sync import async_to_sync
from celery import Celery
from fastapi import HTTPException
from sqlalchemy.sql.operators import is_
from sqlmodel import select

from users_service.db import create_session
from users_service.models import User, UserRead, UserUpdate

app = Celery(
    "users_service", backend=os.environ.get("REDIS_URL"), broker=os.environ.get("REDIS_URL")
)


@app.task(name="update_user_task")
def update_user_task(user_id: int, user: dict) -> dict:
    """Celery task to update a user by ID.

    Args:
        user_id: ID of the user to update.
        user: User data to update.

    Returns:
        Updated user data.
    """
    return async_to_sync(_update_user)(user_id, UserUpdate(**user)).dict()


async def _update_user(user_id: int, user: UserUpdate) -> UserRead:
    async with create_session() as session:
        query = select(User).where(User.id == user_id, is_(User.deleted_at, None))
        db_user = (await session.execute(query)).scalars().first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = user.dict(exclude_unset=True)
        for key, value in user_data.items():
            setattr(db_user, key, value)

        session.add(db_user)

        await session.commit()
        await session.refresh(db_user)

        return db_user
