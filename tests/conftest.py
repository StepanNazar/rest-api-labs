"""Shared pytest fixtures for the test suite."""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_current_user, get_sql_book_repository, get_book_service
from app.dtos.users import User
from app.main import app
from app.dtos.books import Book, BookStatus, SortField, SortOrder
from app.repository.book_repository import _SORT_ATTR, BookRepository, Cursor, MongoBookRepository, SQLBookRepository
from app.services.book_service import BookService
from app.flask_app.main import create_app as create_flask_app


class FlaskTestClientWrapper:
    def __init__(self, client):
        self.client = client

    def get(self, url, params=None, **kwargs):
        return self._wrap_response(self.client.get(url, query_string=params, **kwargs))

    def post(self, url, json=None, **kwargs):
        return self._wrap_response(self.client.post(url, json=json, **kwargs))

    def delete(self, url, **kwargs):
        return self._wrap_response(self.client.delete(url, **kwargs))

    def _wrap_response(self, response):
        class WrappedResponse:
            def __init__(self, resp):
                self._resp = resp
                self.status_code = resp.status_code

            def json(self):
                return self._resp.get_json()

            def __getattr__(self, name):
                return getattr(self._resp, name)

        return WrappedResponse(response)


class MockBookRepository:
    """Manages a collection of books stored in memory as a dict keyed by UUID."""

    def __init__(self) -> None:
        self._books: dict[UUID, Book] = {}

    async def get_all(
        self,
        *,
        filter_status: BookStatus | None = None,
        filter_author: str | None = None,
        sort_by: SortField | None = None,
        order: SortOrder = SortOrder.ASC,
        limit: int = 10,
        offset: int | None = 0,
        cursor: Cursor | None = None,
    ) -> tuple[list[Book], int] | tuple[list[Book], int, Cursor]:
        """Return books from storage, optionally filtered and sorted.

        Args:
            filter_status: When provided, only books with this status are returned.
            filter_author: When provided, only books whose author exactly matches are returned.
            sort_by: Field to sort results by (title or year).
            order: Sort direction, ascending by default.
            limit: Maximum number of books to return.
            offset: Number of books to skip before starting to return.
            cursor: cursor for cursor based pagination. Ignored if offset is not None.
                    If cursor is None - starts from beginning.

        Returns:
            A tuple of (filtered, sorted, and paginated list of Book records, total count) for offset mode.
            A tuple of (records, total count, next_cursor) for cursor mode.
        """
        books = list(self._books.values())

        if filter_status is not None:
            books = [b for b in books if b.status == filter_status]

        if filter_author is not None:
            books = [b for b in books if b.author == filter_author]

        total_items = len(books)

        if sort_by is not None:
            attr = _SORT_ATTR[sort_by]
            books = sorted(
                books,
                key=lambda b: (getattr(b, attr), b.id),
                reverse=order == SortOrder.DESC,
            )
        else:
            books = sorted(books, key=lambda b: b.id, reverse=order == SortOrder.DESC)

        if offset is None:  # cursor mode
            start_index = 0
            if cursor:
                last_value = cursor["value"]
                last_id = cursor["id"]

                for i, b in enumerate(books):
                    b_value = getattr(b, _SORT_ATTR[sort_by]) if sort_by else b.id
                    if order == SortOrder.ASC:
                        if (b_value, b.id) > (last_value, last_id):
                            start_index = i
                            break
                    else:
                        if (b_value, b.id) < (last_value, last_id):
                            start_index = i
                            break
                else:
                    start_index = len(books)

            items = books[start_index : start_index + limit]
            next_cursor = None
            if items:
                last_item = items[-1]
                last_value = getattr(last_item, _SORT_ATTR[sort_by]) if sort_by else last_item.id
                next_cursor = Cursor(value=last_value, id=last_item.id)
            return items, total_items, next_cursor

        return books[offset : offset + limit], total_items

    async def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        return self._books.get(book_id)

    async def add(self, book: Book) -> Book:
        """Assign a new UUID, persist the book, and return it.

        Args:
            book: The Book record to store. If its id is None, a new UUID will be generated.

        Returns:
            The stored Book record with the generated UUID.
        """
        if book.id is None:
            book.id = uuid4()
        self._books[book.id] = book
        return book

    async def delete(self, book_id: UUID) -> None:
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
def sql_book_repository() -> SQLBookRepository:
    """Create a BookRepository backed by an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine) # noqa: N806
    return SQLBookRepository(Session())


@pytest.fixture()
def mongo_book_repository() -> MongoBookRepository:
    """Create a stub MongoBookRepository."""
    client = AsyncMongoMockClient()
    return MongoBookRepository(client.test_db)


@pytest.fixture(params=["sql", "mongo"])
def book_repository(request, sql_book_repository, mongo_book_repository):
    """Parametrized fixture that returns either a SQL or Mongo repository."""
    if request.param == "sql":
        return sql_book_repository
    if request.param == "mongo":
        return mongo_book_repository


@pytest.fixture()
def service(repository: BookRepository) -> BookService:
    """Return a BookService backed by a fresh, empty repository."""
    return BookService(repository)


@pytest.fixture(params=["fastapi", "flask"])
def client(request, service: BookService) -> Generator[object, None, None]:
    """Return a TestClient with all dependencies overridden to use isolated state."""
    if request.param == "fastapi":
        app.dependency_overrides[get_book_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: User(username="johndoe")
        yield TestClient(app)
        app.dependency_overrides.clear()
    else:
        flask_app = create_flask_app(service)
        with flask_app.test_client() as c:
            yield FlaskTestClientWrapper(c)
