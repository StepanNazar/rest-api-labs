"""FastAPI dependency providers for repository, service, and request limits."""

import os
import time
from typing import Annotated

import motor.motor_asyncio
import redis.asyncio as redis
from fastapi import Depends, HTTPException, Request
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
RATE_LIMITS = {
    "anonymous": (2, 60),
    "authenticated": (10, 60),
}
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://book-cache:6379"), decode_responses=True)


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


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(jwt_bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """Return the authenticated user when bearer credentials are present.

    Args:
        credentials: Optional bearer credentials extracted from the Authorization header.
        auth_service: Injected authentication service.

    Returns:
        The authenticated user, or None for an anonymous request.

    Raises:
        HTTPException: 401 if provided token validation fails.
    """
    if credentials is None:
        return None

    try:
        token_data = auth_service.decode_token(credentials.credentials, expected_kind=TokenKind.ACCESS)
    except AuthenticationError:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(username=token_data.username)


def get_redis_client() -> redis.Redis:
    """Return the Redis client used by request rate limiting.

    Returns:
        Redis client instance.
    """
    return redis_client


async def rate_limit(
    request: Request,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    redis_connection: Annotated[redis.Redis, Depends(get_redis_client)],
) -> None:
    """Limit requests with a Redis-backed sliding time window.

    Args:
        request: The incoming HTTP request.
        current_user: Optional authenticated user resolved from bearer credentials.
        redis_connection: Redis client used to store request timestamps.

    Raises:
        HTTPException: 429 when the identity has reached its configured limit.
    """
    identity = current_user.username if current_user else request.client.host
    limit_type = "authenticated" if current_user else "anonymous"
    limit, period = RATE_LIMITS[limit_type]
    key = f"rate_limit_{identity}"
    now = int(time.time())
    window_start = now - period

    await redis_connection.zremrangebyscore(key, min=0, max=window_start)
    request_count = await redis_connection.zcard(key)
    if request_count >= limit:
        raise HTTPException(
            status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    await redis_connection.zadd(key, {str(time.time_ns()): now})
    await redis_connection.expire(key, period)
