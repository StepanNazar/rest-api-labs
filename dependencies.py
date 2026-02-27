"""FastAPI dependency providers for repository and service instances."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from repository.book_repository import BookRepository
from services.book_service import BookService


@lru_cache(maxsize=1)
def get_book_repository() -> BookRepository:
    """Return the application-wide singleton BookRepository.

    Returns:
        The shared BookRepository instance.
    """
    return BookRepository()


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
