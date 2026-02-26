"""Repository layer responsible for in-memory storage of books."""

from uuid import UUID

from models.book import Book, BookStatus, SortField, SortOrder

_SORT_ATTR: dict[SortField, str] = {
    SortField.TITLE: "title",
    SortField.YEAR: "publication_year",
}


class BookRepository:
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
    ) -> list[Book]:
        """Return books from storage, optionally filtered and sorted.

        Args:
            filter_status: When provided, only books with this status are returned.
            filter_author: When provided, only books whose author exactly matches are returned.
            sort_by: Field to sort results by (title or year).
            order: Sort direction, ascending by default.

        Returns:
            A filtered and sorted list of Book records.
        """
        books = list(self._books.values())

        if filter_status is not None:
            books = [b for b in books if b.status == filter_status]

        if filter_author is not None:
            books = [b for b in books if b.author == filter_author]

        if sort_by is not None:
            attr = _SORT_ATTR[sort_by]
            books = sorted(books, key=lambda b: getattr(b, attr), reverse=order == SortOrder.DESC)

        return books

    def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        return self._books.get(book_id)

    def add(self, book: Book) -> Book:
        """Persist a new book and return it.

        Args:
            book: The Book record to store.

        Returns:
            The stored Book record.
        """
        self._books[book.id] = book
        return book

    def delete(self, book_id: UUID) -> None:
        """Remove a book by ID; does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        self._books.pop(book_id, None)
