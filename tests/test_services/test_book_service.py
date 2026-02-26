"""Unit tests for the BookService class."""

from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from models.book import Book, BookStatus
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse, SortField, SortOrder
from services.book_service import BookService


def _make_book(
    *,
    book_id: UUID | None = None,
    title: str = "Default Title",
    author: str = "Default Author",
    description: str = "",
    status: BookStatus = BookStatus.AVAILABLE,
    year: int = 2024,
) -> Book:
    """Create a Book TypedDict with sensible defaults."""
    return Book(
        id=book_id or uuid4(),
        title=title,
        author=author,
        description=description,
        status=status,
        year=year,
    )


@pytest.fixture()
def repository() -> BookRepository:
    """Return an empty BookRepository."""
    return BookRepository()


@pytest.fixture()
def service(repository: BookRepository) -> BookService:
    """Return a BookService backed by a fresh repository."""
    return BookService(repository)


class TestGetBooks:
    async def test_returns_empty_list_when_no_books_exist(self, service: BookService) -> None:
        # Arrange - service has an empty repository

        # Act
        result = await service.get_books()

        # Assert
        assert result == []

    async def test_returns_all_books_when_no_filters_are_applied(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="Book A"))
        repository.add(_make_book(title="Book B"))

        # Act
        result = await service.get_books()

        # Assert
        assert len(result) == 2

    async def test_filters_books_by_available_status(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(_make_book(title="Issued", status=BookStatus.ISSUED))

        # Act
        result = await service.get_books(filter_status=BookStatus.AVAILABLE)

        # Assert
        assert len(result) == 1
        assert result[0].title == "Available"

    async def test_filters_books_by_issued_status(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(_make_book(title="Issued", status=BookStatus.ISSUED))

        # Act
        result = await service.get_books(filter_status=BookStatus.ISSUED)

        # Assert
        assert len(result) == 1
        assert result[0].title == "Issued"

    async def test_filters_books_by_author_case_insensitively(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(author="John Doe"))
        repository.add(_make_book(author="Jane Smith"))

        # Act
        result = await service.get_books(filter_author="john")

        # Assert
        assert len(result) == 1
        assert result[0].author == "John Doe"

    async def test_filters_books_by_partial_author_name(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(author="George R.R. Martin"))
        repository.add(_make_book(author="George Orwell"))
        repository.add(_make_book(author="Stephen King"))

        # Act
        result = await service.get_books(filter_author="George")

        # Assert
        assert len(result) == 2

    async def test_returns_empty_list_when_no_books_match_filter(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(author="John Doe"))

        # Act
        result = await service.get_books(filter_author="Nonexistent")

        # Assert
        assert result == []

    async def test_sorts_books_by_title_ascending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="Zebra"))
        repository.add(_make_book(title="Apple"))
        repository.add(_make_book(title="Mango"))

        # Act
        result = await service.get_books(sort_by=SortField.TITLE, order=SortOrder.ASC)

        # Assert
        assert [b.title for b in result] == ["Apple", "Mango", "Zebra"]

    async def test_sorts_books_by_title_descending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="Zebra"))
        repository.add(_make_book(title="Apple"))
        repository.add(_make_book(title="Mango"))

        # Act
        result = await service.get_books(sort_by=SortField.TITLE, order=SortOrder.DESC)

        # Assert
        assert [b.title for b in result] == ["Zebra", "Mango", "Apple"]

    async def test_sorts_books_by_year_ascending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="New", year=2020))
        repository.add(_make_book(title="Old", year=1990))
        repository.add(_make_book(title="Mid", year=2005))

        # Act
        result = await service.get_books(sort_by=SortField.YEAR, order=SortOrder.ASC)

        # Assert
        assert [b.year for b in result] == [1990, 2005, 2020]

    async def test_sorts_books_by_year_descending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="New", year=2020))
        repository.add(_make_book(title="Old", year=1990))
        repository.add(_make_book(title="Mid", year=2005))

        # Act
        result = await service.get_books(sort_by=SortField.YEAR, order=SortOrder.DESC)

        # Assert
        assert [b.year for b in result] == [2020, 2005, 1990]

    async def test_applies_both_status_filter_and_sorting_together(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book(title="C Book", status=BookStatus.AVAILABLE, year=2000))
        repository.add(_make_book(title="A Book", status=BookStatus.AVAILABLE, year=2010))
        repository.add(_make_book(title="B Book", status=BookStatus.ISSUED, year=1999))

        # Act
        result = await service.get_books(
            filter_status=BookStatus.AVAILABLE,
            sort_by=SortField.TITLE,
            order=SortOrder.ASC,
        )

        # Assert
        assert len(result) == 2
        assert [b.title for b in result] == ["A Book", "C Book"]

    async def test_returns_book_response_instances(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book())

        # Act
        result = await service.get_books()

        # Assert
        assert all(isinstance(b, BookResponse) for b in result)


class TestGetBook:
    async def test_returns_book_response_when_book_exists(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book(title="Found Book")
        repository.add(book)

        # Act
        result = await service.get_book(book["id"])

        # Assert
        assert isinstance(result, BookResponse)
        assert result.id == book["id"]
        assert result.title == "Found Book"

    async def test_raises_http_404_when_book_does_not_exist(self, service: BookService) -> None:
        # Arrange
        missing_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_book(missing_id)

        assert exc_info.value.status_code == 404

    async def test_returned_book_has_all_expected_fields(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book(
            title="Complete",
            author="Author",
            description="Desc",
            status=BookStatus.ISSUED,
            year=2023,
        )
        repository.add(book)

        # Act
        result = await service.get_book(book["id"])

        # Assert
        assert result.title == "Complete"
        assert result.author == "Author"
        assert result.description == "Desc"
        assert result.status == BookStatus.ISSUED
        assert result.year == 2023


class TestCreateBook:
    async def test_returns_book_response_with_generated_uuid(self, service: BookService) -> None:
        # Arrange
        payload = BookCreate(
            title="New Book",
            author="Some Author",
            description="A description",
            status=BookStatus.AVAILABLE,
            year=2024,
        )

        # Act
        result = await service.create_book(payload)

        # Assert
        assert isinstance(result, BookResponse)
        assert isinstance(result.id, UUID)

    async def test_persists_book_so_it_can_be_retrieved_afterwards(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        payload = BookCreate(
            title="Persisted",
            author="Author",
            description="",
            status=BookStatus.AVAILABLE,
            year=2020,
        )

        # Act
        created = await service.create_book(payload)

        # Assert
        assert repository.get_by_id(created.id) is not None

    async def test_each_created_book_receives_a_unique_id(self, service: BookService) -> None:
        # Arrange
        payload = BookCreate(
            title="Book",
            author="Author",
            description="",
            status=BookStatus.AVAILABLE,
            year=2020,
        )

        # Act
        first = await service.create_book(payload)
        second = await service.create_book(payload)

        # Assert
        assert first.id != second.id

    async def test_created_book_has_all_fields_from_payload(self, service: BookService) -> None:
        # Arrange
        payload = BookCreate(
            title="Title",
            author="Author Name",
            description="Long description",
            status=BookStatus.ISSUED,
            year=1999,
        )

        # Act
        result = await service.create_book(payload)

        # Assert
        assert result.title == "Title"
        assert result.author == "Author Name"
        assert result.description == "Long description"
        assert result.status == BookStatus.ISSUED
        assert result.year == 1999


class TestDeleteBook:
    async def test_removes_book_from_storage_when_it_exists(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book()
        repository.add(book)

        # Act
        await service.delete_book(book["id"])

        # Assert
        assert repository.get_by_id(book["id"]) is None

    async def test_does_not_raise_when_book_does_not_exist(self, service: BookService) -> None:
        # Arrange
        non_existing_id = uuid4()

        # Act & Assert - must be idempotent; no exception should be raised
        await service.delete_book(non_existing_id)

    async def test_is_idempotent_when_called_multiple_times(
        self, service: BookService, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book()
        repository.add(book)

        # Act & Assert - both calls must succeed without raising
        await service.delete_book(book["id"])
        await service.delete_book(book["id"])
