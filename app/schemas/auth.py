"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel


class Token(BaseModel):
    """Bearer token response containing the access token."""

    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """Request body for creating JWT tokens."""

    username: str
    password: str


class AccessToken(BaseModel):
    """Bearer access token response returned by the refresh endpoint."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Decoded JWT payload data needed by the application."""

    username: str
