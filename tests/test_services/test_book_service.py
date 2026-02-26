"""Unit tests for the BookService class."""

from uuid import UUID, uuid4

import pytest

from models.book import Book, BookStatus, SortField, SortOrder
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse
from services.book_service import BookService
from services.exceptions import BookNotFoundError


def _make_book(
    *,
    book_id: UUID | None = None,
    title: str = "Default Title",
    author: str = "Default Author",
    description: str = "",
    status: BookStatus = BookStatus.AVAILABLE,
    publication_year: int = 2024,
) -> Book:
    """Create a Book dataclass instance with sensible defaults."""
    return Book(
        id=book_id or uuid4(),
        title=title,
        author=author,
        description=description,
        status=status,
        publication_year=publication_year,
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
        result = await service.get_books()

        assert result == []

    async def test_returns_all_books_when_no_filters_are_applied(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="Book A"))
        repository.add(_make_book(title="Book B"))

        result = await service.get_books()

        assert len(result) == 2

    async def test_filters_books_by_available_status(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(_make_book(title="Issued", status=BookStatus.ISSUED))

        result = await service.get_books(filter_status=BookStatus.AVAILABLE)

        assert len(result) == 1
        assert result[0].title == "Available"

    async def test_filters_books_by_issued_status(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(_make_book(title="Issued", status=BookStatus.ISSUED))

        result = await service.get_books(filter_status=BookStatus.ISSUED)

        assert len(result) == 1
        assert result[0].title == "Issued"

    async def test_filters_books_by_exact_author_match(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(author="John Doe"))
        repository.add(_make_book(author="Jane Smith"))

        result = await service.get_books(filter_author="John Doe")

        assert len(result) == 1
        assert result[0].author == "John Doe"

    async def test_does_not_match_partial_author_name(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(author="George R.R. Martin"))
        repository.add(_make_book(author="George Orwell"))

        result = await service.get_books(filter_author="George")

        assert result == []

    async def test_returns_empty_list_when_no_books_match_filter(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(author="John Doe"))

        result = await service.get_books(filter_author="Nonexistent Author")

        assert result == []

    async def test_sorts_books_by_title_ascending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="Zebra"))
        repository.add(_make_book(title="Apple"))
        repository.add(_make_book(title="Mango"))

        result = await service.get_books(sort_by=SortField.TITLE, order=SortOrder.ASC)

        assert [b.title for b in result] == ["Apple", "Mango", "Zebra"]

    async def test_sorts_books_by_title_descending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="Zebra"))
        repository.add(_make_book(title="Apple"))
        repository.add(_make_book(title="Mango"))

        result = await service.get_books(sort_by=SortField.TITLE, order=SortOrder.DESC)

        assert [b.title for b in result] == ["Zebra", "Mango", "Apple"]

    async def test_sorts_books_by_year_ascending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="New", publication_year=2020))
        repository.add(_make_book(title="Old", publication_year=1990))
        repository.add(_make_book(title="Mid", publication_year=2005))

        result = await service.get_books(sort_by=SortField.YEAR, order=SortOrder.ASC)

        assert [b.publication_year for b in result] == [1990, 2005, 2020]

    async def test_sorts_books_by_year_descending(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book(title="New", publication_year=2020))
        repository.add(_make_book(title="Old", publication_year=1990))
        repository.add(_make_book(title="Mid", publication_year=2005))

        result = await service.get_books(sort_by=SortField.YEAR, order=SortOrder.DESC)

        assert [b.publication_year for b in result] == [2020, 2005, 1990]

    async def test_applies_both_status_filter_and_sorting_together(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(
            _make_book(title="C Book", status=BookStatus.AVAILABLE, publication_year=2000)
        )
        repository.add(
            _make_book(title="A Book", status=BookStatus.AVAILABLE, publication_year=2010)
        )
        repository.add(_make_book(title="B Book", status=BookStatus.ISSUED, publication_year=1999))

        result = await service.get_books(
            filter_status=BookStatus.AVAILABLE,
            sort_by=SortField.TITLE,
            order=SortOrder.ASC,
        )

        assert len(result) == 2
        assert [b.title for b in result] == ["A Book", "C Book"]

    async def test_returns_book_response_instances(
        self, service: BookService, repository: BookRepository
    ) -> None:
        repository.add(_make_book())

        result = await service.get_books()

        assert all(isinstance(b, BookResponse) for b in result)


class TestGetBook:
    async def test_returns_book_response_when_book_exists(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = _make_book(title="Found Book")
        repository.add(book)

        result = await service.get_book(book.id)

        assert isinstance(result, BookResponse)
        assert result.id == book.id
        assert result.title == "Found Book"

    async def test_raises_book_not_found_error_when_book_does_not_exist(
        self, service: BookService
    ) -> None:
        missing_id = uuid4()

        with pytest.raises(BookNotFoundError) as exc_info:
            await service.get_book(missing_id)

        assert exc_info.value.book_id == missing_id

    async def test_returned_book_has_all_expected_fields(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = _make_book(
            title="Complete",
            author="Author",
            description="Desc",
            status=BookStatus.ISSUED,
            publication_year=2023,
        )
        repository.add(book)

        result = await service.get_book(book.id)

        assert result.title == "Complete"
        assert result.author == "Author"
        assert result.description == "Desc"
        assert result.status == BookStatus.ISSUED
        assert result.publication_year == 2023


class TestCreateBook:
    async def test_returns_book_response_with_generated_uuid(self, service: BookService) -> None:
        payload = BookCreate(
            title="New Book",
            author="Some Author",
            description="A description",
            status=BookStatus.AVAILABLE,
            publication_year=2024,
        )

        result = await service.create_book(payload)

        assert isinstance(result, BookResponse)
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
        book = _make_book()
        repository.add(book)

        await service.delete_book(book.id)

        assert repository.get_by_id(book.id) is None

    async def test_does_not_raise_when_book_does_not_exist(self, service: BookService) -> None:
        non_existing_id = uuid4()

        await service.delete_book(non_existing_id)

    async def test_is_idempotent_when_called_multiple_times(
        self, service: BookService, repository: BookRepository
    ) -> None:
        book = _make_book()
        repository.add(book)

        await service.delete_book(book.id)
        await service.delete_book(book.id)
