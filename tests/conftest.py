"""Shared pytest fixtures for the test suite."""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_book_repository, get_book_service
from app.main import app
from app.models.book import Book, BookStatus, SortField, SortOrder
from app.repository.book_repository import _SORT_ATTR, BookRepository
from app.services.book_service import BookService


class MockBookRepository:
    """Manages a collection of books stored in memory as a dict keyed by UUID."""

    def __init__(self) -> None:
        self._books: dict[UUID, Book] = {}

    def get_all(
        self,
        *,
        filter_status: BookStatus | None = None,
        filter_author: str | None = None,
        sort_by: SortField | None = None,
        order: SortOrder = SortOrder.ASC,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Book], int]:
        """Return books from storage, optionally filtered and sorted.

        Args:
            filter_status: When provided, only books with this status are returned.
            filter_author: When provided, only books whose author exactly matches are returned.
            sort_by: Field to sort results by (title or year).
            order: Sort direction, ascending by default.
            limit: Maximum number of books to return.
            offset: Number of books to skip before starting to return.

        Returns:
            A tuple of (filtered, sorted, and paginated list of Book records, total count).
        """
        books = list(self._books.values())

        if filter_status is not None:
            books = [b for b in books if b.status == filter_status]

        if filter_author is not None:
            books = [b for b in books if b.author == filter_author]

        if sort_by is not None:
            attr = _SORT_ATTR[sort_by]
            books = sorted(books, key=lambda b: getattr(b, attr), reverse=order == SortOrder.DESC)

        return books[offset : offset + limit], len(self._books)

    def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        return self._books.get(book_id)

    def add(self, book: Book) -> Book:
        """Assign a new UUID, persist the book, and return it.

        Args:
            book: The Book record to store. Its id will be overwritten with a new UUID.

        Returns:
            The stored Book record with the generated UUID.
        """
        book.id = uuid4()
        self._books[book.id] = book
        return book

    def delete(self, book_id: UUID) -> None:
        """Remove a book by ID; does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        self._books.pop(book_id, None)


@pytest.fixture()
def repository() -> MockBookRepository:
    """Return an empty, isolated MockBookRepository for each test."""
    return MockBookRepository()


@pytest.fixture()
def in_memory_book_repository() -> BookRepository:
    """Create a BookRepository backed by an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine) # noqa: N806
    return BookRepository(Session())


@pytest.fixture()
def service(repository: BookRepository) -> BookService:
    """Return a BookService backed by a fresh, empty repository."""
    return BookService(repository)


@pytest.fixture()
def client(service: BookService) -> Generator[TestClient, None, None]:
    """Return a TestClient with all dependencies overridden to use isolated state."""
    app.dependency_overrides[get_book_service] = lambda: service
    app.dependency_overrides[get_book_repository] = lambda: service._repository
    yield TestClient(app)
    app.dependency_overrides.clear()
