"""Unit tests for the BookRepository class."""

from uuid import uuid4

from app.models.book import BookStatus, SortField, SortOrder
from app.repository.book_repository import BookRepository
from tests.helpers import make_book


class TestGetAll:
    def test_returns_empty_list_when_no_books_have_been_added(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        result, count = in_memory_book_repository.get_all()

        assert result == []

    def test_returns_all_books_after_multiple_books_are_added(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book_one = make_book(title="Book One")
        book_two = make_book(title="Book Two")
        in_memory_book_repository.add(book_one)
        in_memory_book_repository.add(book_two)

        result, count = in_memory_book_repository.get_all()

        assert len(result) == 2
        assert book_one in result
        assert book_two in result

    def test_filters_books_by_available_status(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        in_memory_book_repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result, count = in_memory_book_repository.get_all(filter_status=BookStatus.AVAILABLE)

        assert len(result) == 1
        assert result[0].title == "Available"

    def test_filters_books_by_issued_status(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        in_memory_book_repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result, count = in_memory_book_repository.get_all(filter_status=BookStatus.ISSUED)

        assert len(result) == 1
        assert result[0].title == "Issued"

    def test_filters_books_by_exact_author_match(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(author="John Doe"))
        in_memory_book_repository.add(make_book(author="Jane Smith"))

        result, count = in_memory_book_repository.get_all(filter_author="John Doe")

        assert len(result) == 1
        assert result[0].author == "John Doe"

    def test_does_not_return_books_with_partial_author_match(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(author="George R.R. Martin"))
        in_memory_book_repository.add(make_book(author="George Orwell"))

        result, count = in_memory_book_repository.get_all(filter_author="George")

        assert result == []

    def test_returns_empty_list_when_no_books_match_status_filter(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(status=BookStatus.AVAILABLE))

        result, count = in_memory_book_repository.get_all(filter_status=BookStatus.ISSUED)

        assert result == []

    def test_sorts_books_by_title_ascending(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="Zebra"))
        in_memory_book_repository.add(make_book(title="Apple"))
        in_memory_book_repository.add(make_book(title="Mango"))

        result, count = in_memory_book_repository.get_all(
            sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert [b.title for b in result] == ["Apple", "Mango", "Zebra"]

    def test_sorts_books_by_title_descending(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="Zebra"))
        in_memory_book_repository.add(make_book(title="Apple"))
        in_memory_book_repository.add(make_book(title="Mango"))

        result, count = in_memory_book_repository.get_all(
            sort_by=SortField.TITLE, order=SortOrder.DESC
        )

        assert [b.title for b in result] == ["Zebra", "Mango", "Apple"]

    def test_sorts_books_by_year_ascending(self, in_memory_book_repository: BookRepository) -> None:
        in_memory_book_repository.add(make_book(publication_year=2020))
        in_memory_book_repository.add(make_book(publication_year=1990))
        in_memory_book_repository.add(make_book(publication_year=2005))

        result, count = in_memory_book_repository.get_all(
            sort_by=SortField.YEAR, order=SortOrder.ASC
        )

        assert [b.publication_year for b in result] == [1990, 2005, 2020]

    def test_sorts_books_by_year_descending(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(publication_year=2020))
        in_memory_book_repository.add(make_book(publication_year=1990))
        in_memory_book_repository.add(make_book(publication_year=2005))

        result, count = in_memory_book_repository.get_all(
            sort_by=SortField.YEAR, order=SortOrder.DESC
        )

        assert [b.publication_year for b in result] == [2020, 2005, 1990]

    def test_applies_status_filter_and_title_sort_together(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="C Book", status=BookStatus.AVAILABLE))
        in_memory_book_repository.add(make_book(title="A Book", status=BookStatus.AVAILABLE))
        in_memory_book_repository.add(make_book(title="B Book", status=BookStatus.ISSUED))

        result, count = in_memory_book_repository.get_all(
            filter_status=BookStatus.AVAILABLE,
            sort_by=SortField.TITLE,
            order=SortOrder.ASC,
        )

        assert len(result) == 2
        assert [b.title for b in result] == ["A Book", "C Book"]

    def test_limits_returned_books_to_the_given_number(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        for i in range(5):
            in_memory_book_repository.add(make_book(title=f"Book {i}"))

        result, count = in_memory_book_repository.get_all(limit=2)

        assert len(result) == 2

    def test_skips_the_specified_number_of_books_via_offset(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book(title="Book 0"))
        in_memory_book_repository.add(make_book(title="Book 1"))
        in_memory_book_repository.add(make_book(title="Book 2"))

        # We sort by title to have deterministic order for offset
        result, count = in_memory_book_repository.get_all(
            offset=1, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(result) == 2
        assert result[0].title == "Book 1"
        assert result[1].title == "Book 2"

    def test_combines_limit_and_offset_correctly(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        for i in range(5):
            in_memory_book_repository.add(make_book(title=f"Book {i}"))

        result, count = in_memory_book_repository.get_all(
            limit=2, offset=2, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(result) == 2
        assert result[0].title == "Book 2"
        assert result[1].title == "Book 3"


class TestAdd:
    def test_returns_the_same_book_that_was_added(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book = make_book(title="My Book")

        returned = in_memory_book_repository.add(book)

        assert returned == book

    def test_book_is_persisted_and_retrievable_after_adding(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book = make_book()

        in_memory_book_repository.add(book)

        assert book in in_memory_book_repository.get_all()[0]


class TestGetById:
    def test_returns_the_book_when_it_exists(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book = make_book()
        in_memory_book_repository.add(book)

        result = in_memory_book_repository.get_by_id(book.id)

        assert result == book

    def test_returns_none_when_no_book_has_the_given_id(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book())
        missing_id = uuid4()

        result = in_memory_book_repository.get_by_id(missing_id)

        assert result is None

    def test_returns_none_when_repository_is_empty(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        result = in_memory_book_repository.get_by_id(uuid4())

        assert result is None


class TestDelete:
    def test_removes_existing_book_from_storage(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book = make_book()
        in_memory_book_repository.add(book)

        in_memory_book_repository.delete(book.id)

        assert in_memory_book_repository.get_by_id(book.id) is None

    def test_does_nothing_when_book_does_not_exist(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        in_memory_book_repository.add(make_book())
        non_existing_id = uuid4()

        in_memory_book_repository.delete(non_existing_id)

        assert len(in_memory_book_repository.get_all()[0]) == 1

    def test_only_removes_the_targeted_book_leaving_others_intact(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book_to_keep = make_book(title="Keep Me")
        book_to_delete = make_book(title="Delete Me")
        in_memory_book_repository.add(book_to_keep)
        in_memory_book_repository.add(book_to_delete)

        in_memory_book_repository.delete(book_to_delete.id)

        all_books, count = in_memory_book_repository.get_all()
        assert len(all_books) == 1
        assert all_books[0] == book_to_keep

    def test_is_idempotent_when_called_twice_for_the_same_id(
        self, in_memory_book_repository: BookRepository
    ) -> None:
        book = make_book()
        in_memory_book_repository.add(book)

        in_memory_book_repository.delete(book.id)
        in_memory_book_repository.delete(book.id)

        assert in_memory_book_repository.get_all()[0] == []
