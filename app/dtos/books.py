"""Book DTO and enumerations."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


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


class Book(BaseModel):
    """DB-agnostic representation of a library book."""

    title: str
    author: str
    description: str | None
    status: BookStatus
    publication_year: int
    id: UUID | None = None
