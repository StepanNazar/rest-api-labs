"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 bearer token response containing access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str


class AccessToken(BaseModel):
    """Bearer access token response returned by the refresh endpoint."""

    access_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    """Request body for exchanging a refresh token for a new access token."""

    refresh_token: str


class TokenData(BaseModel):
    """Decoded JWT payload data needed by the application."""

    username: str
