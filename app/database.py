"""Database configuration and session management."""

import os
from collections.abc import AsyncGenerator, Generator

import motor.motor_asyncio
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]
MONGO_DATABASE_URL = os.environ.get("MONGO_DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Provide a database session to dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DATABASE_URL)
mongo_db = mongo_client["books"]


async def get_mongo_db() -> AsyncGenerator[motor.motor_asyncio.AsyncIOMotorDatabase, None]:
    """Provide a MongoDB database instance to dependency injection."""
    yield mongo_db


