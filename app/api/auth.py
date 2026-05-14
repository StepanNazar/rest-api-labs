"""API endpoints for JWT authentication."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi import status as http_status

from app.dependencies import get_auth_service
from app.schemas.auth import AccessToken, LoginRequest, Token
from app.services.auth_service import REFRESH_TOKEN_EXPIRE_DAYS, AuthService, TokenKind
from app.services.exceptions import AuthenticationError

router = APIRouter(tags=["auth"])
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/refresh"
REFRESH_TOKEN_COOKIE_MAX_AGE_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def raise_token_exception() -> NoReturn:
    """Raise the standard HTTP error for invalid refresh tokens.

    Raises:
        HTTPException: Always raised with HTTP 401.
    """
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/token", response_model=Token)
async def login_for_tokens(
    payload: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Create bearer tokens for the requested username.

    Args:
        payload: Request body containing user credentials.
        response: HTTP response used to set the refresh token cookie.
        auth_service: Injected authentication service.

    Returns:
        Bearer token response with the access token.

    """
    refresh_token = auth_service.create_refresh_token(payload.username)
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_TOKEN_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="strict",
        path=REFRESH_TOKEN_COOKIE_PATH,
    )

    return Token(
        access_token=auth_service.create_access_token(payload.username),
        token_type="bearer",
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh_access_token(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AccessToken:
    """Exchange a valid refresh token for a new access token.

    Args:
        auth_service: Injected authentication service.
        refresh_token: Refresh token read from the scoped HTTP-only cookie.

    Returns:
        New bearer access token.

    Raises:
        HTTPException: 401 if the refresh token is invalid.
    """
    try:
        if refresh_token is None:
            raise AuthenticationError
        token_data = auth_service.decode_token(
            refresh_token,
            expected_kind=TokenKind.REFRESH,
        )
    except AuthenticationError:
        raise_token_exception()

    return AccessToken(
        access_token=auth_service.create_access_token(token_data.username),
        token_type="bearer",
    )
