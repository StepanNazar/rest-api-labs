"""Book domain model, status and query enumerations."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


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
    """In-memory representation of a library book."""

    id: UUID
    title: str
    author: str
    description: str
    status: BookStatus
    publication_year: int
