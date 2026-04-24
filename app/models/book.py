"""Book SQLAlchemy model."""

from uuid import UUID, uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so

from app.database import Base
from dtos.books import BookStatus


class BookSQLAlchemy(Base):
    """SQLAlchemy model for a library book."""

    __tablename__ = "books"

    id: so.Mapped[UUID] = so.mapped_column(sa.Uuid, primary_key=True, default=uuid4)
    title: so.Mapped[str] = so.mapped_column(sa.String, nullable=False, index=True)
    author: so.Mapped[str] = so.mapped_column(sa.String, nullable=False)
    description: so.Mapped[str | None] = so.mapped_column(sa.String, nullable=True)
    status: so.Mapped[BookStatus] = so.mapped_column(
        sa.Enum(BookStatus, native_enum=False), nullable=False, default=BookStatus.AVAILABLE
    )
    publication_year: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False, index=True)
