"""FastAPI dependency providers for repository and service instances."""

from typing import Annotated

import motor.motor_asyncio
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db, get_mongo_db
from app.repository.book_repository import BookRepository, MongoBookRepository, SQLBookRepository
from app.services.book_service import BookService


def get_sql_book_repository(db: Annotated[Session, Depends(get_db)]) -> SQLBookRepository:
    """Return a BookRepository initialized with the database session.

    Args:
        db: The SQLAlchemy session to inject.

    Returns:
        A BookRepository instance.
    """
    return SQLBookRepository(db)

def get_mongo_book_repository(get_mongo_db: Annotated[motor.motor_asyncio.AsyncIOMotorDatabase, Depends(get_mongo_db)]) -> MongoBookRepository:
    return MongoBookRepository(get_mongo_db)


def get_book_service(
    repository: Annotated[BookRepository, Depends(get_sql_book_repository)],
) -> BookService:
    """Return a BookService wired to the provided repository.

    Args:
        repository: The BookRepository to inject via FastAPI dependency.

    Returns:
        A BookService instance backed by the provided repository.
    """
    return BookService(repository)
