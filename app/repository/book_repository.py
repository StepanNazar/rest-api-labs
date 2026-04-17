"""Repository layer responsible for storage of books in PostgreSQL."""
from typing import TypedDict, Any
from uuid import UUID

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.orm import Session

from app.models.book import Book, BookStatus, SortField, SortOrder

_SORT_ATTR: dict[SortField, str] = {
    SortField.TITLE: "title",
    SortField.YEAR: "publication_year",
}

class Cursor(TypedDict):
    value: Any
    id: UUID

class BookRepository:
    """Manages library books in a PostgreSQL database using SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_all(
        self,
        *,
        filter_status: BookStatus | None = None,
        filter_author: str | None = None,
        sort_by: SortField | None = None,
        order: SortOrder = SortOrder.ASC,
        limit: int = 10,
        offset: int | None = 0,
        cursor: Cursor | None = None,
    ) -> tuple[list[Book], int] | tuple[list[Book], int, Cursor]:
        """Return books from storage, optionally filtered and sorted with pagination.

        Args:
            filter_status: When provided, only books with this status are returned.
            filter_author: When provided, only books whose author exactly matches are returned.
            sort_by: Field to sort results by (title or year).
            order: Sort direction, ascending by default.
            limit: Maximum number of books to return.
            offset: Number of books to skip before starting to return.
            cursor: cursor for cursor based pagination. Ignored if offset is not None.
                    If cursor is None - starts from beginning.

        Returns:
            A tuple of (filtered, sorted, and paginated list of Book records, total count) for offset mode.
            A tuple of (records, total count, next_cursor) for cursor mode.
        """
        stmt = select(Book)
        count_stmt = select(func.count()).select_from(Book)

        if filter_status is not None:
            stmt = stmt.where(Book.status == filter_status)
            count_stmt = count_stmt.where(Book.status == filter_status)

        if filter_author is not None:
            stmt = stmt.where(Book.author == filter_author)
            count_stmt = count_stmt.where(Book.author == filter_author)

        total_items = self._db.scalar(count_stmt) or 0

        if sort_by is not None:
            attr_name = _SORT_ATTR[sort_by]
            sort_column = getattr(Book, attr_name)
        else:
            sort_column = Book.id

        # tie-breaker
        id_column = Book.id

        if order == SortOrder.DESC:
            order_by = [sort_column.desc(), id_column.desc()]
        else:
            order_by = [sort_column.asc(), id_column.asc()]
        stmt = stmt.order_by(*order_by)

        if offset is None: # cursor mode
            if cursor:
                last_value = cursor["value"]
                last_id = cursor["id"]

                if order == SortOrder.ASC:
                    condition = tuple_(sort_column, id_column) > (last_value, last_id)
                else:
                    condition = tuple_(sort_column, id_column) < (last_value, last_id)
                stmt = stmt.where(condition)
            
            stmt = stmt.limit(limit)

            items = list(self._db.scalars(stmt).all())
            next_cursor = None
            if items:
                last_item = items[-1]
                last_value = getattr(last_item, sort_column.key)
                next_cursor = Cursor(value=last_value, id=last_item.id)
            return items, total_items, next_cursor

        stmt = stmt.limit(limit).offset(offset)

        items = list(self._db.scalars(stmt).all())
        return items, total_items

    def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        return self._db.get(Book, book_id)

    def add(self, book: Book) -> Book:
        """Persist the book and return it.

        Args:
            book: The Book record to store.

        Returns:
            The stored Book record.
        """
        self._db.add(book)
        self._db.commit()
        self._db.refresh(book)
        return book

    def delete(self, book_id: UUID) -> None:
        """Remove a book by ID. Does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        stmt = delete(Book).where(Book.id == book_id)
        self._db.execute(stmt)
        self._db.commit()
