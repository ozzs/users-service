from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.operators import is_
from sqlmodel import select

from users_service.db import create_db_and_tables, get_session
from users_service.models import User, UserCreate, UserRead, UserUpdate
from users_service.tasks import update_user_task

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    """Prepare application during startup."""
    await create_db_and_tables()


@app.post("/users/", response_model=UserRead)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    """Create a new user.

    Args:
        user: User data to add.
        session: Database session (injected from FastAPI).

    Returns:
        Created user data.
    """
    db_user = User.from_orm(user)

    session.add(db_user)

    await session.commit()
    await session.refresh(db_user)

    return db_user


@app.get("/users/", response_model=list[UserRead])
async def read_users(
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    """Read user by ID.

    Args:
        offset: Position to start reading users from.
        limit: Amount of total users to read (<=100).
        session: Database session (injected from FastAPI).

    Returns:
        List of users.
    """
    query = select(User).where(is_(User.deleted_at, None)).offset(offset).limit(limit)
    return (await session.execute(query)).scalars().all()


@app.get("/users/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Read user by ID.

    Args:
        user_id: ID of the user to read.
        session: Database session (injected from FastAPI).

    Returns:
        User data.
    """
    query = select(User).where(User.id == user_id, is_(User.deleted_at, None))
    user = (await session.execute(query)).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.patch("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate) -> dict:
    """Update user by ID.

    This function will schedule the update with Celery, and then returns
    the task ID. You can query the task status using /tasks/<ID>.

    Args:
        user_id: ID of the user to update.
        user: User data to update.

    Returns:
        Task ID.
    """
    task = update_user_task.delay(user_id=user_id, user=user.dict(exclude_unset=True))
    return {"task_id": task.id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    """Delete user by ID.

    Args:
        user_id: ID of the user to delete.
        session: Database session (injected from FastAPI).

    Returns:
        Whether or not the delete succeeded.
    """
    query = select(User).where(User.id == user_id, is_(User.deleted_at, None))
    db_user = (await session.execute(query)).scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.deleted_at = datetime.now()

    session.add(db_user)
    await session.commit()

    return {"ok": True}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict:
    """Get async task status by ID.

    Args:
        task_id: ID of the task to query.

    Returns:
        The ID of the task, its status (SUCCESS / FAILURE / PENDING), and the result of the
        task in case it succeeded.
    """
    task = update_user_task.AsyncResult(task_id)

    return {
        "id": task.id,
        "status": task.status,
        "result": task.result,
    }
