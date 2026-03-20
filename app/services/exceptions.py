"""Domain exceptions raised by the service layer."""

from uuid import UUID


class BookNotFoundError(Exception):
    """Raised when a requested book does not exist in the repository.

    Attributes:
        book_id: The UUID that was looked up.
    """

    def __init__(self, book_id: UUID) -> None:
        super().__init__(f"Book with id {book_id} not found")
        self.book_id = book_id
