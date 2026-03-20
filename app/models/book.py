"""Book domain model, status and query enumerations."""

from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so

from app.database import Base


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


class Book(Base):
    """SQLAlchemy model for a library book."""

    __tablename__ = "books"

    id: so.Mapped[UUID] = so.mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    title: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    author: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    description: so.Mapped[str | None] = so.mapped_column(sa.String, nullable=True)
    status: so.Mapped[BookStatus] = so.mapped_column(
        sa.Enum(BookStatus, native_enum=False), nullable=False, default=BookStatus.AVAILABLE
    )
    publication_year: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
