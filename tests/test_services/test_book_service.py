"""Unit tests for the BookService class.

Service tests verify that the service correctly delegates to the repository
and performs its own responsibilities (exception raising).
UUID generation is owned by the repository; tests here confirm the behavior end-to-end.
Filtering/sorting logic is fully tested in test_book_repository.py.
"""

from uuid import UUID, uuid4

import pytest

from app.models.book import Book, BookStatus, SortField, SortOrder
from app.repository.book_repository import BookRepository
from app.schemas.book import BookCreate
from app.services.book_service import BookService
from app.services.exceptions import BookNotFoundError
from tests.helpers import make_book


class TestGetBooks:
    async def test_returns_empty_list_when_no_books_exist(self, service: BookService) -> None:
        result = await service.get_books()

        assert result == []

    async def test_returns_all_books_when_no_filters_are_applied(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(make_book(title="Book A"))
        repository.add(make_book(title="Book B"))

        result = await service.get_books()

        assert len(result) == 2

    async def test_delegates_filter_status_to_repository(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result = await service.get_books(filter_status=BookStatus.AVAILABLE)

        assert len(result) == 1
        assert result[0].title == "Available"

    async def test_delegates_sort_params_to_repository(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(make_book(title="Zebra"))
        repository.add(make_book(title="Apple"))

        result = await service.get_books(sort_by=SortField.TITLE, order=SortOrder.ASC)

        assert [b.title for b in result] == ["Apple", "Zebra"]

    async def test_delegates_pagination_params_to_repository(
        self, service: BookService, repository: BookRepository
    ) -> None:
        for i in range(10):
            repository.add(make_book(title=f"Book {i:02d}"))

        result = await service.get_books(limit=3, offset=4, sort_by=SortField.TITLE)

        assert len(result) == 3
        # With offset 4, we expect books starting from the 5th (index 4)
        assert result[0].title == "Book 04"
        assert result[1].title == "Book 05"
        assert result[2].title == "Book 06"

    async def test_returns_book_instances(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(make_book())

        result = await service.get_books()

        assert all(isinstance(b, Book) for b in result)


class TestGetBook:
    async def test_returns_book_when_it_exists(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = make_book(title="Found Book")
        repository.add(book)

        result = await service.get_book(book.id)

        assert isinstance(result, Book)
        assert result.id == book.id

    async def test_raises_book_not_found_error_when_book_does_not_exist(
        self, service: BookService
    ) -> None:
        missing_id = uuid4()

        with pytest.raises(BookNotFoundError) as exc_info:
            await service.get_book(missing_id)

        assert exc_info.value.book_id == missing_id


class TestCreateBook:
    async def test_returns_book_with_generated_uuid(self, service: BookService) -> None:
        payload = BookCreate(
            title="New Book",
            author="Some Author",
            description="A description",
            status=BookStatus.AVAILABLE,
            publication_year=2024,
        )

        result = await service.create_book(payload)

        assert isinstance(result, Book)
        assert isinstance(result.id, UUID)

    async def test_persists_book_so_it_can_be_retrieved_afterwards(
        self, service: BookService, repository: BookRepository
    ) -> None:
        payload = BookCreate(
            title="Persisted",
            author="Author",
            description="",
            status=BookStatus.AVAILABLE,
            publication_year=2020,
        )

        created = await service.create_book(payload)

        assert repository.get_by_id(created.id) is not None

    async def test_each_created_book_receives_a_unique_id(self, service: BookService) -> None:
        payload = BookCreate(
            title="Book",
            author="Author",
            description="",
            status=BookStatus.AVAILABLE,
            publication_year=2020,
        )

        first = await service.create_book(payload)
        second = await service.create_book(payload)

        assert first.id != second.id

    async def test_created_book_has_all_fields_from_payload(self, service: BookService) -> None:
        payload = BookCreate(
            title="Title",
            author="Author Name",
            description="Long description",
            status=BookStatus.ISSUED,
            publication_year=1999,
        )

        result = await service.create_book(payload)

        assert result.title == "Title"
        assert result.author == "Author Name"
        assert result.description == "Long description"
        assert result.status == BookStatus.ISSUED
        assert result.publication_year == 1999


class TestDeleteBook:
    async def test_removes_book_from_storage_when_it_exists(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = make_book()
        repository.add(book)

        await service.delete_book(book.id)

        assert repository.get_by_id(book.id) is None

    async def test_does_not_raise_when_book_does_not_exist(self, service: BookService) -> None:
        await service.delete_book(uuid4())

    async def test_is_idempotent_when_called_multiple_times(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = make_book()
        repository.add(book)

        await service.delete_book(book.id)
        await service.delete_book(book.id)
