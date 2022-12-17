from datetime import datetime
from enum import Enum

from sqlmodel import Column, DateTime, Field, func, SQLModel, String


class House(str, Enum):
    """Hogwarts house of a user."""

    GRYFFINDOR = "gryffindor"
    RAVENCLAW = "ravenclaw"
    SLYTHERIN = "slytherin"
    HUFFLEPUFF = "hufflepuff"


class BloodStatus(str, Enum):
    """Blood status of a user."""

    PURE_BLOOD = "pure_blood"
    MUGGLE_BORN = "muggle_born"
    HALF_BLOOD = "half_blood"
    SQUIB = "squib"


class Gender(str, Enum):
    """User gender."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class UserBase(SQLModel):
    """Base class to represents common user fields."""

    name: str
    email: str
    age: int | None = None
    gender: Gender = Field(sa_column=Column(String), nullable=False)
    house: House = Field(sa_column=Column(String), nullable=False)
    blood_status: BloodStatus = Field(sa_column=Column(String), nullable=False)


class User(UserBase, table=True):
    """User table in the DB."""

    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime | None = Field(sa_column=Column(DateTime(), server_default=func.now()))

    updated_at: datetime | None = Field(sa_column=Column(DateTime(), onupdate=func.now()))

    deleted_at: datetime | None


class UserCreate(UserBase):
    """User creation data."""

    pass


class UserRead(UserBase):
    """User read data."""

    id: int


class UserUpdate(UserBase):
    """User update data."""

    name: str | None = None
    email: str | None = None
    age: int | None = None
    gender: Gender | None = None
    house: House | None = None
    blood_status: BloodStatus | None = None
