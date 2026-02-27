"""Unit tests for the BookRepository class."""

from uuid import uuid4

from models.book import BookStatus, SortField, SortOrder
from repository.book_repository import BookRepository
from tests.helpers import make_book


class TestGetAll:
    def test_returns_empty_list_when_no_books_have_been_added(
        self, repository: BookRepository
    ) -> None:
        result = repository.get_all()

        assert result == []

    def test_returns_all_books_after_multiple_books_are_added(
        self, repository: BookRepository
    ) -> None:
        book_one = make_book(title="Book One")
        book_two = make_book(title="Book Two")
        repository.add(book_one)
        repository.add(book_two)

        result = repository.get_all()

        assert len(result) == 2
        assert book_one in result
        assert book_two in result

    def test_filters_books_by_available_status(self, repository: BookRepository) -> None:
        repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result = repository.get_all(filter_status=BookStatus.AVAILABLE)

        assert len(result) == 1
        assert result[0].title == "Available"

    def test_filters_books_by_issued_status(self, repository: BookRepository) -> None:
        repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result = repository.get_all(filter_status=BookStatus.ISSUED)

        assert len(result) == 1
        assert result[0].title == "Issued"

    def test_filters_books_by_exact_author_match(self, repository: BookRepository) -> None:
        repository.add(make_book(author="John Doe"))
        repository.add(make_book(author="Jane Smith"))

        result = repository.get_all(filter_author="John Doe")

        assert len(result) == 1
        assert result[0].author == "John Doe"

    def test_does_not_return_books_with_partial_author_match(
        self, repository: BookRepository
    ) -> None:
        repository.add(make_book(author="George R.R. Martin"))
        repository.add(make_book(author="George Orwell"))

        result = repository.get_all(filter_author="George")

        assert result == []

    def test_returns_empty_list_when_no_books_match_status_filter(
        self, repository: BookRepository
    ) -> None:
        repository.add(make_book(status=BookStatus.AVAILABLE))

        result = repository.get_all(filter_status=BookStatus.ISSUED)

        assert result == []

    def test_sorts_books_by_title_ascending(self, repository: BookRepository) -> None:
        repository.add(make_book(title="Zebra"))
        repository.add(make_book(title="Apple"))
        repository.add(make_book(title="Mango"))

        result = repository.get_all(sort_by=SortField.TITLE, order=SortOrder.ASC)

        assert [b.title for b in result] == ["Apple", "Mango", "Zebra"]

    def test_sorts_books_by_title_descending(self, repository: BookRepository) -> None:
        repository.add(make_book(title="Zebra"))
        repository.add(make_book(title="Apple"))
        repository.add(make_book(title="Mango"))

        result = repository.get_all(sort_by=SortField.TITLE, order=SortOrder.DESC)

        assert [b.title for b in result] == ["Zebra", "Mango", "Apple"]

    def test_sorts_books_by_year_ascending(self, repository: BookRepository) -> None:
        repository.add(make_book(publication_year=2020))
        repository.add(make_book(publication_year=1990))
        repository.add(make_book(publication_year=2005))

        result = repository.get_all(sort_by=SortField.YEAR, order=SortOrder.ASC)

        assert [b.publication_year for b in result] == [1990, 2005, 2020]

    def test_sorts_books_by_year_descending(self, repository: BookRepository) -> None:
        repository.add(make_book(publication_year=2020))
        repository.add(make_book(publication_year=1990))
        repository.add(make_book(publication_year=2005))

        result = repository.get_all(sort_by=SortField.YEAR, order=SortOrder.DESC)

        assert [b.publication_year for b in result] == [2020, 2005, 1990]

    def test_applies_status_filter_and_title_sort_together(
        self, repository: BookRepository
    ) -> None:
        repository.add(make_book(title="C Book", status=BookStatus.AVAILABLE))
        repository.add(make_book(title="A Book", status=BookStatus.AVAILABLE))
        repository.add(make_book(title="B Book", status=BookStatus.ISSUED))

        result = repository.get_all(
            filter_status=BookStatus.AVAILABLE,
            sort_by=SortField.TITLE,
            order=SortOrder.ASC,
        )

        assert len(result) == 2
        assert [b.title for b in result] == ["A Book", "C Book"]


class TestAdd:
    def test_returns_the_same_book_that_was_added(self, repository: BookRepository) -> None:
        book = make_book(title="My Book")

        returned = repository.add(book)

        assert returned == book

    def test_book_is_persisted_and_retrievable_after_adding(
        self, repository: BookRepository
    ) -> None:
        book = make_book()

        repository.add(book)

        assert book in repository.get_all()


class TestGetById:
    def test_returns_the_book_when_it_exists(self, repository: BookRepository) -> None:
        book = make_book()
        repository.add(book)

        result = repository.get_by_id(book.id)

        assert result == book

    def test_returns_none_when_no_book_has_the_given_id(self, repository: BookRepository) -> None:
        repository.add(make_book())
        missing_id = uuid4()

        result = repository.get_by_id(missing_id)

        assert result is None

    def test_returns_none_when_repository_is_empty(self, repository: BookRepository) -> None:
        result = repository.get_by_id(uuid4())

        assert result is None


class TestDelete:
    def test_removes_existing_book_from_storage(self, repository: BookRepository) -> None:
        book = make_book()
        repository.add(book)

        repository.delete(book.id)

        assert repository.get_by_id(book.id) is None

    def test_does_nothing_when_book_does_not_exist(self, repository: BookRepository) -> None:
        repository.add(make_book())
        non_existing_id = uuid4()

        repository.delete(non_existing_id)

        assert len(repository.get_all()) == 1

    def test_only_removes_the_targeted_book_leaving_others_intact(
        self, repository: BookRepository
    ) -> None:
        book_to_keep = make_book(title="Keep Me")
        book_to_delete = make_book(title="Delete Me")
        repository.add(book_to_keep)
        repository.add(book_to_delete)

        repository.delete(book_to_delete.id)

        all_books = repository.get_all()
        assert len(all_books) == 1
        assert all_books[0] == book_to_keep

    def test_is_idempotent_when_called_twice_for_the_same_id(
        self, repository: BookRepository
    ) -> None:
        book = make_book()
        repository.add(book)

        repository.delete(book.id)
        repository.delete(book.id)

        assert repository.get_all() == []
