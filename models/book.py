"""Book domain model and status enumeration."""

from enum import StrEnum
from typing import TypedDict
from uuid import UUID


class BookStatus(StrEnum):
    """Represents the availability status of a book in the library."""

    AVAILABLE = "available"
    ISSUED = "issued"


class Book(TypedDict):
    """In-memory representation of a library book."""

    id: UUID
    title: str
    author: str
    description: str
    status: BookStatus
    year: int
