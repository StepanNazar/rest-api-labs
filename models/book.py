"""Book domain model, status and query enumerations."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class BookStatus(StrEnum):
    """Represents the availability status of a book in the library."""

    AVAILABLE = "available"
    ISSUED = "issued"


class SortField(StrEnum):
    """Fields by which books can be sorted."""

    TITLE = "title"
    YEAR = "year"


class SortOrder(StrEnum):
    """Direction of sorting."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class Book:
    """In-memory representation of a library book.

    The `id` field is assigned by `BookRepository.add()`, which overwrites
    any value set at construction time. The default_factory exists only to
    allow creating a Book without an id before it is persisted.
    """

    title: str
    author: str
    description: str
    status: BookStatus
    publication_year: int
    id: UUID = field(default_factory=uuid4)
