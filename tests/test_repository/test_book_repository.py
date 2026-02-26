"""Unit tests for the BookRepository class."""

from uuid import UUID, uuid4

import pytest

from models.book import Book, BookStatus
from repository.book_repository import BookRepository


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
    """Return a fresh, empty BookRepository."""
    return BookRepository()


class TestGetAll:
    def test_returns_empty_list_when_no_books_have_been_added(
        self, repository: BookRepository
    ) -> None:
        # Arrange - repository is already empty

        # Act
        result = repository.get_all()

        # Assert
        assert result == []

    def test_returns_all_books_after_multiple_books_are_added(
        self, repository: BookRepository
    ) -> None:
        # Arrange
        book_one = _make_book(title="Book One")
        book_two = _make_book(title="Book Two")
        repository.add(book_one)
        repository.add(book_two)

        # Act
        result = repository.get_all()

        # Assert
        assert len(result) == 2
        assert book_one in result
        assert book_two in result

    def test_returns_a_copy_so_external_mutation_does_not_affect_storage(
        self, repository: BookRepository
    ) -> None:
        # Arrange
        repository.add(_make_book())

        # Act
        result = repository.get_all()
        result.clear()

        # Assert
        assert len(repository.get_all()) == 1


class TestAdd:
    def test_returns_the_same_book_that_was_added(self, repository: BookRepository) -> None:
        # Arrange
        book = _make_book(title="My Book")

        # Act
        returned = repository.add(book)

        # Assert
        assert returned == book

    def test_book_is_persisted_and_retrievable_after_adding(
        self, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book()

        # Act
        repository.add(book)

        # Assert
        assert book in repository.get_all()


class TestGetById:
    def test_returns_the_book_when_it_exists(self, repository: BookRepository) -> None:
        # Arrange
        book = _make_book()
        repository.add(book)

        # Act
        result = repository.get_by_id(book["id"])

        # Assert
        assert result == book

    def test_returns_none_when_no_book_has_the_given_id(self, repository: BookRepository) -> None:
        # Arrange
        repository.add(_make_book())
        missing_id = uuid4()

        # Act
        result = repository.get_by_id(missing_id)

        # Assert
        assert result is None

    def test_returns_none_when_repository_is_empty(self, repository: BookRepository) -> None:
        # Arrange - repository is empty

        # Act
        result = repository.get_by_id(uuid4())

        # Assert
        assert result is None


class TestDelete:
    def test_removes_existing_book_from_storage(self, repository: BookRepository) -> None:
        # Arrange
        book = _make_book()
        repository.add(book)

        # Act
        repository.delete(book["id"])

        # Assert
        assert repository.get_by_id(book["id"]) is None

    def test_does_nothing_when_book_does_not_exist(self, repository: BookRepository) -> None:
        # Arrange
        repository.add(_make_book())
        non_existing_id = uuid4()

        # Act & Assert - no exception should be raised
        repository.delete(non_existing_id)
        assert len(repository.get_all()) == 1

    def test_only_removes_the_targeted_book_leaving_others_intact(
        self, repository: BookRepository
    ) -> None:
        # Arrange
        book_to_keep = _make_book(title="Keep Me")
        book_to_delete = _make_book(title="Delete Me")
        repository.add(book_to_keep)
        repository.add(book_to_delete)

        # Act
        repository.delete(book_to_delete["id"])

        # Assert
        all_books = repository.get_all()
        assert len(all_books) == 1
        assert all_books[0] == book_to_keep

    def test_is_idempotent_when_called_twice_for_the_same_id(
        self, repository: BookRepository
    ) -> None:
        # Arrange
        book = _make_book()
        repository.add(book)

        # Act & Assert - second delete should not raise
        repository.delete(book["id"])
        repository.delete(book["id"])
        assert repository.get_all() == []
