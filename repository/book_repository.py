"""Repository layer responsible for in-memory storage of books."""

from uuid import UUID

from models.book import Book


class BookRepository:
    """Manages a collection of books stored in memory as a list of dicts."""

    def __init__(self) -> None:
        self._books: list[Book] = []

    def get_all(self) -> list[Book]:
        """Return all books currently stored.

        Returns:
            A list of all Book records.
        """
        return list(self._books)

    def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        return next((b for b in self._books if b["id"] == book_id), None)

    def add(self, book: Book) -> Book:
        """Persist a new book and return it.

        Args:
            book: The Book record to store.

        Returns:
            The stored Book record.
        """
        self._books.append(book)
        return book

    def delete(self, book_id: UUID) -> None:
        """Remove a book by ID; does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        self._books = [b for b in self._books if b["id"] != book_id]
