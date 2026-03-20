"""API endpoints for managing library books."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from fastapi_hypermodel import SirenResponse

from dependencies import get_book_service
from models.book import Book, BookStatus, SortField, SortOrder
from schemas.book import BookCollectionResponse, BookCreate, BookResponse
from services.book_service import BookService
from services.exceptions import BookNotFoundError

router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "/",
    response_model=BookCollectionResponse,
    status_code=http_status.HTTP_200_OK,
    response_class=SirenResponse,
)
async def get_books(
    service: Annotated[BookService, Depends(get_book_service)],
    status: BookStatus | None = None,
    author: str | None = None,
    sort_by: SortField | None = None,
    order: SortOrder = SortOrder.ASC,
) -> dict[str, list[Book]]:
    """Return all books, optionally filtered and sorted.

    Args:
        service: Injected BookService.
        status: Optional status filter.
        author: Optional exact author filter.
        sort_by: Field to sort results by.
        order: Sort direction (asc or desc).

    Returns:
        A list of Book objects (serialized via response_model).
    """
    return {
        "items": await service.get_books(
            filter_status=status,
            filter_author=author,
            sort_by=sort_by,
            order=order,
        )
    }


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    status_code=http_status.HTTP_200_OK,
    response_class=SirenResponse,
)
async def get_book(
    book_id: UUID,
    service: Annotated[BookService, Depends(get_book_service)],
) -> Book:
    """Return a single book by its UUID.

    Args:
        book_id: The UUID of the book to retrieve.
        service: Injected BookService.

    Returns:
        The Book (serialized via response_model).

    Raises:
        HTTPException: 404 if the book does not exist.
    """
    try:
        return await service.get_book(book_id)
    except BookNotFoundError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/",
    response_model=BookResponse,
    status_code=http_status.HTTP_201_CREATED,
    response_class=SirenResponse,
)
async def create_book(
    payload: BookCreate,
    service: Annotated[BookService, Depends(get_book_service)],
) -> Book:
    """Create a new book and return it with a generated UUID.

    Args:
        payload: Validated BookCreate request body.
        service: Injected BookService.

    Returns:
        The newly created Book (serialized via response_model) with HTTP 201.
    """
    return await service.create_book(payload)


@router.delete("/{book_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    service: Annotated[BookService, Depends(get_book_service)],
) -> None:
    """Delete a book by UUID.  Idempotent: returns 204 even if the book did not exist.

    Args:
        book_id: The UUID of the book to delete.
        service: Injected BookService.
    """
    await service.delete_book(book_id)
