"""API endpoints for managing library books."""
import base64
import json
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status
from fastapi_hypermodel import SirenResponse, UrlType

from app.dependencies import get_book_service
from app.dtos.books import BookStatus, SortField, SortOrder, Book
from app.schemas.book import BookCollectionResponse, BookCreate, BookResponse
from app.services.book_service import BookService
from app.services.exceptions import BookNotFoundError
from app.repository.book_repository import Cursor

router = APIRouter(prefix="/books", tags=["books"])

def encode_cursor(data: Cursor | None) -> str | None:
    if data is None:
        return None
    data_dict = data.copy()
    for key, value in data_dict.items():
        if isinstance(value, UUID):
            data_dict[key] = str(value)
    return base64.urlsafe_b64encode(json.dumps(data_dict).encode()).decode()

def decode_cursor(cursor: str) -> Cursor:
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    for key, value in data.items():
        try:
            data[key] = UUID(value)
        except Exception:
            pass
    return data

@router.get(
    "/",
    response_model=BookCollectionResponse,
    status_code=http_status.HTTP_200_OK,
    response_class=SirenResponse,
)
async def get_books(
    request: Request,
    service: Annotated[BookService, Depends(get_book_service)],
    status: BookStatus | None = None,
    author: str | None = None,
    sort_by: SortField | None = None,
    order: SortOrder = SortOrder.ASC,
    limit: int = Query(10, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    cursor: str | None = None,
) -> BookCollectionResponse:
    """Return books, optionally filtered, sorted and paginated.

    Args:
        request: FastAPI Request object for accessing query parameters.
        service: Injected BookService.
        status: Optional status filter.
        author: Optional exact author filter.
        sort_by: Field to sort results by.
        order: Sort direction (asc or desc).
        limit: Maximum number of books to return.
        offset: Number of books to skip.
        cursor: cursor for cursor based pagination. Ignored if offset is not None.
                If cursor is None - starts from beginning.

    Returns:
        A collection of Book objects with pagination metadata.
    """
    if cursor is not None:
        try:
            cursor = decode_cursor(cursor)
        except Exception:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid cursor value",
            )
    result = await service.get_books(
        filter_status=status,
        filter_author=author,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
        cursor=cursor,
    )
    next_cursor = None
    if offset is None:
        items, total, next_cursor = result
        next_cursor = encode_cursor(next_cursor)
    else:
        items, total = result
    result = BookCollectionResponse(
        **{
            "items": items,
            "limit": limit,
            "offset": offset,
            "total": total,
            "count": len(items),
            "next_offset": None,
            "prev_offset": None,
            "next_cursor": next_cursor,
        }
    )
    params = dict(request.query_params)
    next_params = None
    prev_params = None
    if offset is not None:
        next_offset = offset + limit
        if next_offset < total:
            result.next_offset = next_offset
            next_params = params.copy()
            next_params["offset"] = str(next_offset)
        if offset > 0:
            prev_offset = max(offset - limit, 0)
            result.prev_offset = prev_offset
            prev_params = params.copy()
            prev_params["offset"] = str(prev_offset)
    elif next_cursor:
        next_params = params.copy()
        next_params["cursor"] = next_cursor

    for link in result.links:
        if "self" in link.rel:
            query_str = urlencode(params, doseq=True)
            link.href = UrlType(request.url.replace(query=query_str))
        if "next" in link.rel and next_params is not None:
            query_str = urlencode(next_params, doseq=True)
            link.href = UrlType(request.url.replace(query=query_str))
        if "prev" in link.rel and prev_params is not None:
            query_str = urlencode(prev_params, doseq=True)
            link.href = UrlType(request.url.replace(query=query_str))
    result.items = result.entities # noqa
    return result


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
