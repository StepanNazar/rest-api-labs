"""Pydantic schemas for request validation and response serialization."""

from collections.abc import Sequence
from uuid import UUID

from fastapi_hypermodel import SirenActionFor, SirenHyperModel, SirenLinkFor
from pydantic import BaseModel, Field

from models.book import BookStatus, SortField, SortOrder

__all__ = ["BookCreate", "BookResponse", "SortField", "SortOrder"]


class BookCreate(BaseModel):
    """Schema for creating a new book.

    Attributes:
        title: The title of the book.
        author: The author of the book.
        description: A short description of the book.
        status: Current availability status.
        publication_year: Year the book was published.
    """

    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=0, max_length=2000, default="")
    status: BookStatus
    publication_year: int


class BookResponse(SirenHyperModel):
    """Schema for returning book data in API responses.

    Attributes:
        id: Unique identifier of the book (UUID).
        title: The title of the book.
        author: The author of the book.
        description: A short description of the book.
        status: Current availability status.
        publication_year: Year the book was published.
    """

    id: UUID
    title: str
    author: str
    description: str
    status: BookStatus
    publication_year: int

    links: Sequence[SirenLinkFor] = (SirenLinkFor("get_book", {"book_id": "<id>"}, rel=["self"]),)
    actions: Sequence[SirenActionFor] = (
        SirenActionFor("delete_book", {"book_id": "<id>"}, name="delete"),
    )

    model_config = {"from_attributes": True}


class BookCollectionResponse(SirenHyperModel):
    items: Sequence[BookResponse]

    links: Sequence[SirenLinkFor] = (SirenLinkFor("get_books", rel=["self"]),)
    actions: Sequence[SirenActionFor] = (
        SirenActionFor("get_book", templated=True, name="find"),
        SirenActionFor("delete_book", templated=True, name="delete"),
        SirenActionFor("create_book", name="create"),
    )
