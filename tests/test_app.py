from http import HTTPStatus

from httpx import AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool

from users_service.app import app, get_session


@pytest_asyncio.fixture(name="session")
async def session_fixture():
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(name="client")
async def client_fixture(session: AsyncSession):
    def get_session_override() -> AsyncSession:
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user_sanity(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data["name"] == "Harry Potter"
    assert data["email"] == "harry@potter.com"
    assert data["age"] == 53
    assert data["gender"] == "male"
    assert data["house"] == "gryffindor"
    assert data["blood_status"] == "pure_blood"

    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_user_age_optional(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data["name"] == "Harry Potter"
    assert data["email"] == "harry@potter.com"
    assert data["age"] is None
    assert data["gender"] == "male"
    assert data["house"] == "gryffindor"
    assert data["blood_status"] == "pure_blood"

    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_user_invalid_gender(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "maleasdfasdfljasdflkjasdf",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_user_invalid_house(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor2",
            "blood_status": "pure_blood",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_user_invalid_blood_status(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood123",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_user_missing_required_parameter(client: AsyncClient):
    response = await client.post(
        "/users/",
        json={
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):

    # Add a few users
    for _ in range(100):
        await client.post(
            "/users/",
            json={
                "name": "Harry Potter",
                "email": "harry@potter.com",
                "age": 53,
                "gender": "male",
                "house": "gryffindor",
                "blood_status": "pure_blood",
            },
        )

    # Get all users
    response = await client.get("/users/")

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(data) == 100


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient):

    # Add a few users
    for _ in range(100):
        await client.post(
            "/users/",
            json={
                "name": "Harry Potter",
                "email": "harry@potter.com",
                "age": 53,
                "gender": "male",
                "house": "gryffindor",
                "blood_status": "pure_blood",
            },
        )

    # Get all users
    response = await client.get("/users/?limit=5&offset=5")

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(data) == 5


@pytest.mark.asyncio
async def test_read_user(client: AsyncClient):
    # Add a user
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    data_created = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data_created["id"] is not None

    # Read the created user
    response = await client.get(f"/users/{data_created['id']}")

    assert response.status_code == HTTPStatus.OK
    data_read = response.json()

    assert data_read == data_created


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    # Add a user
    response = await client.post(
        "/users/",
        json={
            "name": "Harry Potter",
            "email": "harry@potter.com",
            "age": 53,
            "gender": "male",
            "house": "gryffindor",
            "blood_status": "pure_blood",
        },
    )

    data_created = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data_created["id"] is not None

    # Delete the created user
    response = await client.delete(f"/users/{data_created['id']}")
    assert response.status_code == HTTPStatus.OK

    # Make sure the user doesn't appear when reading all users
    response = await client.get("/users/")
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(data) == 0

    # Make sure the user doesn't appear when reading it specifically
    response = await client.get(f"/users/{data_created['id']}")
    data = response.json()

    assert response.status_code == HTTPStatus.NOT_FOUND
