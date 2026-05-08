"""API endpoints for OAuth2 password authentication with JWT tokens."""

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_auth_service
from app.schemas.auth import AccessToken, RefreshTokenRequest, Token
from app.services.auth_service import AuthService, TokenKind
from app.services.exceptions import AuthenticationError

router = APIRouter(tags=["auth"])


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
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Create bearer access and refresh tokens for the requested username.

    Args:
        form_data: OAuth2 password request form.
        auth_service: Injected authentication service.

    Returns:
        Bearer token response with access and refresh tokens.

    """
    return Token(
        access_token=auth_service.create_access_token(form_data.username),
        refresh_token=auth_service.create_refresh_token(form_data.username),
        token_type="bearer",
    )


@router.post("/refresh", response_model=AccessToken)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccessToken:
    """Exchange a valid refresh token for a new access token.

    Args:
        payload: Request body containing the refresh token.
        auth_service: Injected authentication service.

    Returns:
        New bearer access token.

    Raises:
        HTTPException: 401 if the refresh token is invalid.
    """
    try:
        token_data = auth_service.decode_token(
            payload.refresh_token,
            expected_kind=TokenKind.REFRESH,
        )
    except AuthenticationError:
        raise_token_exception()

    return AccessToken(
        access_token=auth_service.create_access_token(token_data.username),
        token_type="bearer",
    )
