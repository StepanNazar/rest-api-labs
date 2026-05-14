"""Business logic for JWT token handling."""

import os
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError

from app.schemas.auth import TokenData
from app.services.exceptions import AuthenticationError

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenKind(StrEnum):
    """JWT token purposes supported by the application."""

    ACCESS = "access"
    REFRESH = "refresh"


class AuthService:
    """Create and validate JWT tokens."""

    def create_token(
        self,
        *,
        subject: str,
        token_kind: TokenKind,
        expires_delta: timedelta,
    ) -> str:
        """Create a signed JWT token for the supplied subject.

        Args:
            subject: Unique user identifier for the JWT ``sub`` claim.
            token_kind: Token purpose stored in the JWT payload.
            expires_delta: How long the token remains valid.

        Returns:
            Encoded JWT token string.
        """
        expire = datetime.now(UTC) + expires_delta
        payload: dict[str, Any] = {"sub": subject, "type": token_kind.value, "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_access_token(self, username: str) -> str:
        """Create a short-lived access token.

        Args:
            username: User identifier stored in the JWT subject.

        Returns:
            Encoded access token.
        """
        return self.create_token(
            subject=username,
            token_kind=TokenKind.ACCESS,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, username: str) -> str:
        """Create a long-lived refresh token.

        Args:
            username: User identifier stored in the JWT subject.

        Returns:
            Encoded refresh token.
        """
        return self.create_token(
            subject=username,
            token_kind=TokenKind.REFRESH,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )

    def decode_token(self, token: str, *, expected_kind: TokenKind) -> TokenData:
        """Decode and validate a JWT token.

        Args:
            token: Encoded JWT token string.
            expected_kind: Required token purpose.

        Returns:
            Decoded token data.

        Raises:
            AuthenticationError: If the token is invalid, expired, or has the wrong purpose.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except InvalidTokenError as exc:
            raise AuthenticationError from exc

        username = payload.get("sub")
        token_kind = payload.get("type")
        if not isinstance(username, str) or token_kind != expected_kind.value:
            raise AuthenticationError

        return TokenData(username=username)
