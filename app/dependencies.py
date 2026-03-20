"""FastAPI dependency providers for repository and service instances."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository.book_repository import BookRepository
from app.services.book_service import BookService


def get_book_repository(db: Annotated[Session, Depends(get_db)]) -> BookRepository:
    """Return a BookRepository initialized with the database session.

    Args:
        db: The SQLAlchemy session to inject.

    Returns:
        A BookRepository instance.
    """
    return BookRepository(db)


def get_book_service(
    repository: Annotated[BookRepository, Depends(get_book_repository)],
) -> BookService:
    """Return a BookService wired to the provided repository.

    Args:
        repository: The BookRepository to inject via FastAPI dependency.

    Returns:
        A BookService instance backed by the provided repository.
    """
    return BookService(repository)
