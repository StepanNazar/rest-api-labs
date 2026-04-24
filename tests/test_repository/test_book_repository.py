"""Unit tests for the BookRepository class."""

from uuid import uuid4

from app.dtos.books import BookStatus, SortField, SortOrder
from app.repository.book_repository import BookRepository
from tests.helpers import make_book


class TestGetAll:
    async def test_returns_empty_list_when_no_books_have_been_added(
        self, book_repository: BookRepository
    ) -> None:
        result, count = await book_repository.get_all()

        assert result == []

    async def test_returns_all_books_after_multiple_books_are_added(
        self, book_repository: BookRepository
    ) -> None:
        book_one = await book_repository.add(make_book(title="Book One"))
        book_two = await book_repository.add(make_book(title="Book Two"))

        result, count = await book_repository.get_all()

        assert len(result) == 2
        assert book_one in result
        assert book_two in result

    async def test_filters_books_by_available_status(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        await book_repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result, count = await book_repository.get_all(filter_status=BookStatus.AVAILABLE)

        assert len(result) == 1
        assert result[0].title == "Available"

    async def test_filters_books_by_issued_status(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="Available", status=BookStatus.AVAILABLE))
        await book_repository.add(make_book(title="Issued", status=BookStatus.ISSUED))

        result, count = await book_repository.get_all(filter_status=BookStatus.ISSUED)

        assert len(result) == 1
        assert result[0].title == "Issued"

    async def test_filters_books_by_exact_author_match(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(author="John Doe"))
        await book_repository.add(make_book(author="Jane Smith"))

        result, count = await book_repository.get_all(filter_author="John Doe")

        assert len(result) == 1
        assert result[0].author == "John Doe"

    async def test_does_not_return_books_with_partial_author_match(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(author="George R.R. Martin"))
        await book_repository.add(make_book(author="George Orwell"))

        result, count = await book_repository.get_all(filter_author="George")

        assert result == []

    async def test_returns_empty_list_when_no_books_match_status_filter(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(status=BookStatus.AVAILABLE))

        result, count = await book_repository.get_all(filter_status=BookStatus.ISSUED)

        assert result == []

    async def test_sorts_books_by_title_ascending(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="Zebra"))
        await book_repository.add(make_book(title="Apple"))
        await book_repository.add(make_book(title="Mango"))

        result, count = await book_repository.get_all(
            sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert [b.title for b in result] == ["Apple", "Mango", "Zebra"]

    async def test_sorts_books_by_title_descending(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="Zebra"))
        await book_repository.add(make_book(title="Apple"))
        await book_repository.add(make_book(title="Mango"))

        result, count = await book_repository.get_all(
            sort_by=SortField.TITLE, order=SortOrder.DESC
        )

        assert [b.title for b in result] == ["Zebra", "Mango", "Apple"]

    async def test_sorts_books_by_year_ascending(self, book_repository: BookRepository) -> None:
        await book_repository.add(make_book(publication_year=2020))
        await book_repository.add(make_book(publication_year=1990))
        await book_repository.add(make_book(publication_year=2005))

        result, count = await book_repository.get_all(
            sort_by=SortField.YEAR, order=SortOrder.ASC
        )

        assert [b.publication_year for b in result] == [1990, 2005, 2020]

    async def test_sorts_books_by_year_descending(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(publication_year=2020))
        await book_repository.add(make_book(publication_year=1990))
        await book_repository.add(make_book(publication_year=2005))

        result, count = await book_repository.get_all(
            sort_by=SortField.YEAR, order=SortOrder.DESC
        )

        assert [b.publication_year for b in result] == [2020, 2005, 1990]

    async def test_applies_status_filter_and_title_sort_together(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="C Book", status=BookStatus.AVAILABLE))
        await book_repository.add(make_book(title="A Book", status=BookStatus.AVAILABLE))
        await book_repository.add(make_book(title="B Book", status=BookStatus.ISSUED))

        result, count = await book_repository.get_all(
            filter_status=BookStatus.AVAILABLE,
            sort_by=SortField.TITLE,
            order=SortOrder.ASC,
        )

        assert len(result) == 2
        assert [b.title for b in result] == ["A Book", "C Book"]

    async def test_limits_returned_books_to_the_given_number(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(5):
            await book_repository.add(make_book(title=f"Book {i}"))

        result, count = await book_repository.get_all(limit=2)

        assert len(result) == 2

    async def test_skips_the_specified_number_of_books_via_offset(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="Book 0"))
        await book_repository.add(make_book(title="Book 1"))
        await book_repository.add(make_book(title="Book 2"))

        # We sort by title to have deterministic order for offset
        result, count = await book_repository.get_all(
            offset=1, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(result) == 2
        assert result[0].title == "Book 1"
        assert result[1].title == "Book 2"

    async def test_combines_limit_and_offset_correctly(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(5):
            await book_repository.add(make_book(title=f"Book {i}"))

        result, count = await book_repository.get_all(
            limit=2, offset=2, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(result) == 2
        assert result[0].title == "Book 2"
        assert result[1].title == "Book 3"

    async def test_returns_next_cursor_on_first_page_in_cursor_mode(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(5):
            await book_repository.add(make_book(title=f"Book {i:02d}"))

        items, total, cursor = await book_repository.get_all(
            limit=2, offset=None, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(items) == 2
        assert items[0].title == "Book 00"
        assert items[1].title == "Book 01"
        assert cursor is not None
        assert cursor["value"] == "Book 01"
        assert cursor["id"] == items[1].id

    async def test_fetches_subsequent_page_using_cursor(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(5):
            await book_repository.add(make_book(title=f"Book {i:02d}"))

        _, _, first_cursor = await book_repository.get_all(
            limit=2, offset=None, sort_by=SortField.TITLE, order=SortOrder.ASC
        )
        items, total, second_cursor = await book_repository.get_all(
            limit=2, offset=None, cursor=first_cursor, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(items) == 2
        assert items[0].title == "Book 02"
        assert items[1].title == "Book 03"
        assert second_cursor is not None
        assert second_cursor["value"] == "Book 03"

    async def test_returns_none_cursor_on_last_page(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(3):
            await book_repository.add(make_book(title=f"Book {i:02d}"))

        items, total, cursor = await book_repository.get_all(
            limit=5, offset=None, sort_by=SortField.TITLE, order=SortOrder.ASC
        )

        assert len(items) == 3
        assert cursor is not None # It returns the cursor of the last item found
        
        # To actually get None, we need to request after the last item
        items, total, next_cursor = await book_repository.get_all(
            limit=5, offset=None, cursor=cursor, sort_by=SortField.TITLE, order=SortOrder.ASC
        )
        
        assert items == []
        assert next_cursor is None

    async def test_cursor_pagination_with_descending_order(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(5):
            await book_repository.add(make_book(title=f"Book {i:02d}"))

        items, total, cursor = await book_repository.get_all(
            limit=2, offset=None, sort_by=SortField.TITLE, order=SortOrder.DESC
        )

        assert items[0].title == "Book 04"
        assert items[1].title == "Book 03"
        
        items2, total2, cursor2 = await book_repository.get_all(
            limit=2, offset=None, cursor=cursor, sort_by=SortField.TITLE, order=SortOrder.DESC
        )
        
        assert items2[0].title == "Book 02"
        assert items2[1].title == "Book 01"

    async def test_cursor_pagination_with_year_sort(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book(title="B1", publication_year=2000))
        await book_repository.add(make_book(title="B2", publication_year=2000))
        await book_repository.add(make_book(title="B3", publication_year=2001))

        # Sort by year, B1 and B2 have same year, so ID tie-breaker is used
        items, total, cursor = await book_repository.get_all(
            limit=1, offset=None, sort_by=SortField.YEAR, order=SortOrder.ASC
        )
        
        assert len(items) == 1
        first_book = items[0]
        
        items2, total2, cursor2 = await book_repository.get_all(
            limit=1, offset=None, cursor=cursor, sort_by=SortField.YEAR, order=SortOrder.ASC
        )
        
        assert len(items2) == 1
        assert items2[0].id != first_book.id
        assert items2[0].publication_year >= first_book.publication_year

    async def test_cursor_pagination_with_filters(
        self, book_repository: BookRepository
    ) -> None:
        for i in range(10):
            status = BookStatus.AVAILABLE if i % 2 == 0 else BookStatus.ISSUED
            await book_repository.add(make_book(title=f"Book {i:02d}", status=status))

        items, total, cursor = await book_repository.get_all(
            limit=2, offset=None, filter_status=BookStatus.AVAILABLE, sort_by=SortField.TITLE
        )

        assert len(items) == 2
        assert items[0].title == "Book 00"
        assert items[1].title == "Book 02"
        
        items2, total2, cursor2 = await book_repository.get_all(
            limit=2, offset=None, cursor=cursor, filter_status=BookStatus.AVAILABLE, sort_by=SortField.TITLE
        )
        
        assert items2[0].title == "Book 04"
        assert items2[1].title == "Book 06"


class TestAdd:
    async def test_returns_the_same_book_that_was_added(
        self, book_repository: BookRepository
    ) -> None:
        book = make_book(title="My Book")

        returned = await book_repository.add(book)

        book.id = returned.id
        assert returned == book

    async def test_book_is_persisted_and_retrievable_after_adding(
        self, book_repository: BookRepository
    ) -> None:
        book = await book_repository.add(make_book())

        assert book in (await book_repository.get_all())[0]


class TestGetById:
    async def test_returns_the_book_when_it_exists(
        self, book_repository: BookRepository
    ) -> None:
        book = await book_repository.add(make_book())

        result = await book_repository.get_by_id(book.id)

        assert result == book

    async def test_returns_none_when_no_book_has_the_given_id(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book())
        missing_id = uuid4()

        result = await book_repository.get_by_id(missing_id)

        assert result is None

    async def test_returns_none_when_repository_is_empty(
        self, book_repository: BookRepository
    ) -> None:
        result = await book_repository.get_by_id(uuid4())

        assert result is None


class TestDelete:
    async def test_removes_existing_book_from_storage(
        self, book_repository: BookRepository
    ) -> None:
        book = await book_repository.add(make_book())

        await book_repository.delete(book.id)

        assert await book_repository.get_by_id(book.id) is None

    async def test_does_nothing_when_book_does_not_exist(
        self, book_repository: BookRepository
    ) -> None:
        await book_repository.add(make_book())
        non_existing_id = uuid4()

        await book_repository.delete(non_existing_id)

        assert len((await book_repository.get_all())[0]) == 1

    async def test_only_removes_the_targeted_book_leaving_others_intact(
        self, book_repository: BookRepository
    ) -> None:
        book_to_keep = await book_repository.add(make_book(title="Keep Me"))
        book_to_delete = await book_repository.add(make_book(title="Delete Me"))

        await book_repository.delete(book_to_delete.id)

        all_books, count = await book_repository.get_all()
        assert len(all_books) == 1
        assert all_books[0] == book_to_keep

    async def test_is_idempotent_when_called_twice_for_the_same_id(
        self, book_repository: BookRepository
    ) -> None:
        book = await book_repository.add(make_book())

        await book_repository.delete(book.id)
        await book_repository.delete(book.id)

        assert (await book_repository.get_all())[0] == []
