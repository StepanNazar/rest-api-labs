"""Shared test helper utilities."""

from uuid import UUID, uuid4

from app.models.book import Book, BookStatus


def make_book(
    *,
    book_id: UUID | None = None,
    title: str = "Default Title",
    author: str = "Default Author",
    description: str = "",
    status: BookStatus = BookStatus.AVAILABLE,
    publication_year: int = 2024,
) -> Book:
    """Create a Book dataclass instance with sensible defaults.

    Args:
        book_id: Optional UUID; a random one is generated if not provided.
        title: Book title.
        author: Book author.
        description: Short description.
        status: Availability status.
        publication_year: Year of publication.

    Returns:
        A Book instance.
    """
    return Book(
        id=book_id or uuid4(),
        title=title,
        author=author,
        description=description,
        status=status,
        publication_year=publication_year,
    )
