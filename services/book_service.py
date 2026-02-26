"""Business logic layer for managing library books."""

from uuid import UUID, uuid4

from models.book import Book, BookStatus, SortField, SortOrder
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse
from services.exceptions import BookNotFoundError


class BookService:
    """Orchestrates book operations between the API layer and the repository."""

    def __init__(self, repository: BookRepository) -> None:
        self._repository = repository

    async def get_books(
        self,
        *,
        filter_status: BookStatus | None = None,
        filter_author: str | None = None,
        sort_by: SortField | None = None,
        order: SortOrder = SortOrder.ASC,
    ) -> list[BookResponse]:
        """Retrieve all books with optional filtering and sorting.

        Args:
            filter_status: When provided, only books with this status are returned.
            filter_author: When provided, only books whose author exactly matches are returned.
            sort_by: Field to sort results by (title or year).
            order: Sort direction, ascending by default.

        Returns:
            A list of BookResponse objects matching the given criteria.
        """
        books = self._repository.get_all(
            filter_status=filter_status,
            filter_author=filter_author,
            sort_by=sort_by,
            order=order,
        )
        return [BookResponse.model_validate(b) for b in books]

    async def get_book(self, book_id: UUID) -> BookResponse:
        """Retrieve a single book by its ID.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The BookResponse for the requested book.

        Raises:
            BookNotFoundError: If no book with the given ID exists.
        """
        book = self._repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError(book_id)
        return BookResponse.model_validate(book)

    async def create_book(self, data: BookCreate) -> BookResponse:
        """Create and persist a new book with an auto-generated UUID.

        Args:
            data: Validated BookCreate payload from the request body.

        Returns:
            The BookResponse of the newly created book.
        """
        book = Book(
            id=uuid4(),
            title=data.title,
            author=data.author,
            description=data.description,
            status=data.status,
            publication_year=data.publication_year,
        )
        saved = self._repository.add(book)
        return BookResponse.model_validate(saved)

    async def delete_book(self, book_id: UUID) -> None:
        """Delete a book by ID; silently succeeds if the book does not exist.

        Args:
            book_id: The UUID of the book to delete.
        """
        self._repository.delete(book_id)
