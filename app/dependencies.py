"""FastAPI dependency providers for repository and service instances."""

from typing import Annotated

import motor.motor_asyncio
from fastapi import Depends, HTTPException
from fastapi import status as http_status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db, get_mongo_db
from app.dtos.users import User
from app.repository.book_repository import BookRepository, MongoBookRepository, SQLBookRepository
from app.services.auth_service import AuthService, TokenKind
from app.services.book_service import BookService
from app.services.exceptions import AuthenticationError

jwt_bearer_scheme = HTTPBearer(auto_error=False)


def get_sql_book_repository(db: Annotated[Session, Depends(get_db)]) -> SQLBookRepository:
    """Return a BookRepository initialized with the database session.

    Args:
        db: The SQLAlchemy session to inject.

    Returns:
        A BookRepository instance.
    """
    return SQLBookRepository(db)

def get_mongo_book_repository(get_mongo_db: Annotated[motor.motor_asyncio.AsyncIOMotorDatabase, Depends(get_mongo_db)]) -> MongoBookRepository:
    return MongoBookRepository(get_mongo_db)


def get_book_service(
    repository: Annotated[BookRepository, Depends(get_sql_book_repository)],
) -> BookService:
    """Return a BookService wired to the provided repository.

    Args:
        repository: The BookRepository to inject via FastAPI dependency.

    Returns:
        A BookService instance backed by the provided repository.
    """
    return BookService(repository)


def get_auth_service() -> AuthService:
    """Return an AuthService for JWT token handling.

    Returns:
        AuthService instance.
    """
    return AuthService()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(jwt_bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Return the user identified by a valid access token.

    Args:
        credentials: Bearer credentials extracted from the Authorization header.
        auth_service: Injected authentication service.

    Returns:
        The authenticated user.

    Raises:
        HTTPException: 401 if token validation fails.
    """
    try:
        if credentials is None:
            raise AuthenticationError
        token_data = auth_service.decode_token(credentials.credentials, expected_kind=TokenKind.ACCESS)
    except AuthenticationError:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(username=token_data.username)
