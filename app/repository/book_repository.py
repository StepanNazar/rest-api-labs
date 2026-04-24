"""Repository layer responsible for storage of books in PostgreSQL."""
import abc
from typing import TypedDict, Any
from uuid import UUID

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.orm import Session
from bson import ObjectId
from pydantic import BaseModel
from pydantic_mongo import AsyncAbstractRepository, PydanticObjectId

from app.models.book import BookSQLAlchemy
from app.dtos.books import Book, BookStatus, SortField, SortOrder

_SORT_ATTR: dict[SortField, str] = {
    SortField.TITLE: "title",
    SortField.YEAR: "publication_year",
}


def _map_to_dto(model: BookSQLAlchemy) -> Book:
    """Map SQLAlchemy model to Book DTO."""
    return Book(
        id=model.id,
        title=model.title,
        author=model.author,
        description=model.description,
        status=model.status,
        publication_year=model.publication_year,
    )


class Cursor(TypedDict):
    value: Any
    id: UUID

class BookRepository(abc.ABC):
    async def get_all(self,
        *,
        filter_status: BookStatus | None = None,
        filter_author: str | None = None,
        sort_by: SortField | None = None,
        order: SortOrder = SortOrder.ASC,
        limit: int = 10,
        offset: int | None = 0,
        cursor: Cursor | None = None,
    ) -> tuple[list[Book], int] | tuple[list[Book], int, Cursor]:
        pass

    async def get_by_id(self, book_id: UUID) -> Book | None:
        pass

    async def add(self, book: Book) -> Book:
        pass

    async def delete(self, book_id: UUID) -> None:
        pass


class SQLBookRepository:
    """Manages library books in a PostgreSQL database using SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    async def get_all(
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
        stmt = select(BookSQLAlchemy)
        count_stmt = select(func.count()).select_from(BookSQLAlchemy)

        if filter_status is not None:
            stmt = stmt.where(BookSQLAlchemy.status == filter_status)
            count_stmt = count_stmt.where(BookSQLAlchemy.status == filter_status)

        if filter_author is not None:
            stmt = stmt.where(BookSQLAlchemy.author == filter_author)
            count_stmt = count_stmt.where(BookSQLAlchemy.author == filter_author)

        total_items = self._db.scalar(count_stmt) or 0

        if sort_by is not None:
            attr_name = _SORT_ATTR[sort_by]
            sort_column = getattr(BookSQLAlchemy, attr_name)
        else:
            sort_column = BookSQLAlchemy.id

        # tie-breaker
        id_column = BookSQLAlchemy.id

        if order == SortOrder.DESC:
            order_by = [sort_column.desc(), id_column.desc()]
        else:
            order_by = [sort_column.asc(), id_column.asc()]
        stmt = stmt.order_by(*order_by)

        if offset is None:  # cursor mode
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
            return [_map_to_dto(item) for item in items], total_items, next_cursor

        stmt = stmt.limit(limit).offset(offset)

        items = list(self._db.scalars(stmt).all())
        return [_map_to_dto(item) for item in items], total_items

    async def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        model = self._db.get(BookSQLAlchemy, book_id)
        return _map_to_dto(model) if model else None

    async def add(self, book: Book) -> Book:
        """Persist the book and return it.

        Args:
            book: The Book DTO to store.

        Returns:
            The stored Book DTO.
        """
        model = BookSQLAlchemy(
            title=book.title,
            author=book.author,
            description=book.description,
            status=book.status,
            publication_year=book.publication_year,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return _map_to_dto(model)

    async def delete(self, book_id: UUID) -> None:
        """Remove a book by ID. Does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        stmt = delete(BookSQLAlchemy).where(BookSQLAlchemy.id == book_id)
        self._db.execute(stmt)
        self._db.commit()


class MongoBook(BaseModel):
    id: PydanticObjectId | None = None
    title: str
    author: str
    description: str | None
    status: BookStatus
    publication_year: int


def _map_mongo_to_dto(model: MongoBook) -> Book:
    """Map MongoBook model to Book DTO."""
    json = model.model_dump()
    if json.get("id"):
        json["id"] = UUID(str(json["id"]) + "0" * 8)
    return Book(**json)


class _MongoBookRepository(AsyncAbstractRepository[MongoBook]):
    class Meta:
        collection_name = "books"


class MongoBookRepository:
    def __init__(self, database):
        self._repo = _MongoBookRepository(database)

    async def get_all(
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
        query = {}
        if filter_status:
            query["status"] = filter_status
        if filter_author:
            query["author"] = filter_author

        total_count = await self._repo.get_collection().count_documents(query)

        mongo_order = 1 if order == SortOrder.ASC else -1
        if sort_by:
            sort_field = _SORT_ATTR[sort_by]
        else:
            sort_field = "_id"

        sort = [(sort_field, mongo_order), ("_id", mongo_order)]

        if offset is not None:
            models = await self._repo.find_by(query, skip=offset, limit=limit, sort=sort)
            return [_map_mongo_to_dto(m) for m in models], total_count

        # Cursor mode
        if cursor:
            last_value = cursor["value"]
            last_id = ObjectId(str(cursor["id"])[:-8].replace("-", ""))

            op = "$gt" if order == SortOrder.ASC else "$lt"
            if sort_field == "_id":
                query["_id"] = {op: last_id}
            else:
                query["$or"] = [
                    {sort_field: {op: last_value}},
                    {sort_field: last_value, "_id": {op: last_id}},
                ]

        models = list(await self._repo.find_by(query, limit=limit, sort=sort))

        next_cursor = None
        if models:
            last_model = models[-1]
            last_dto = _map_mongo_to_dto(last_model)
            cursor_value = (
                getattr(last_model, sort_field) if sort_field != "_id" else last_dto.id
            )
            next_cursor = Cursor(value=cursor_value, id=last_dto.id)

        return [_map_mongo_to_dto(m) for m in models], total_count, next_cursor

    async def get_by_id(self, book_id: UUID) -> Book | None:
        """Find a book by its unique identifier.

        Args:
            book_id: The UUID of the book to retrieve.

        Returns:
            The matching Book if found, otherwise None.
        """
        model = await self._repo.find_one_by_id(
            ObjectId(str(book_id)[:-8].replace("-", ""))
        )
        return _map_mongo_to_dto(model) if model else None

    async def add(self, book: Book) -> Book:
        """Persist the book and return it.

        Args:
            book: The Book record to store.

        Returns:
            The stored Book record.
        """
        mongo_book = MongoBook(**book.model_dump())
        await self._repo.save(mongo_book)
        return _map_mongo_to_dto(mongo_book)

    async def delete(self, book_id: UUID) -> None:
        """Remove a book by ID. Does nothing if the book does not exist.

        Args:
            book_id: The UUID of the book to remove.
        """
        await self._repo.delete_by_id(ObjectId(str(book_id)[:-8].replace("-", "")))

