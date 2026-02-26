"""Pydantic schemas for request validation and response serialization."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from models.book import BookStatus


class SortField(StrEnum):
    """Fields by which books can be sorted."""

    TITLE = "title"
    YEAR = "year"


class SortOrder(StrEnum):
    """Direction of sorting."""

    ASC = "asc"
    DESC = "desc"


class BookCreate(BaseModel):
    """Schema for creating a new book.

    Attributes:
        title: The title of the book.
        author: The author of the book.
        description: A short description of the book.
        status: Current availability status.
        year: Publication year, must be between 1000 and 2100.
    """

    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=0, max_length=2000, default="")
    status: BookStatus
    year: int = Field(ge=1000, le=2100)


class BookResponse(BaseModel):
    """Schema for returning book data in API responses.

    Attributes:
        id: Unique identifier of the book (UUID).
        title: The title of the book.
        author: The author of the book.
        description: A short description of the book.
        status: Current availability status.
        year: Publication year.
    """

    id: UUID
    title: str
    author: str
    description: str
    status: BookStatus
    year: int

    model_config = {"from_attributes": True}
