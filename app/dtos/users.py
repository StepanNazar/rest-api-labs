"""User DTOs used by the authentication layer."""

from pydantic import BaseModel


class User(BaseModel):
    """DB-agnostic representation of an authenticated user."""

    username: str
    email: str | None = None
    full_name: str | None = None
