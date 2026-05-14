"""Unit tests for the AuthService class."""

from datetime import timedelta

import pytest

from app.services.auth_service import AuthService, TokenKind
from app.services.exceptions import AuthenticationError


class TestCreateToken:
    def test_creates_access_token_that_can_be_decoded(self) -> None:
        service = AuthService()

        token = service.create_token(
            subject="johndoe",
            token_kind=TokenKind.ACCESS,
            expires_delta=timedelta(minutes=5),
        )

        token_data = service.decode_token(token, expected_kind=TokenKind.ACCESS)
        assert token_data.username == "johndoe"

    def test_rejects_access_token_when_refresh_token_is_expected(self) -> None:
        service = AuthService()
        token = service.create_token(
            subject="johndoe",
            token_kind=TokenKind.ACCESS,
            expires_delta=timedelta(minutes=5),
        )

        with pytest.raises(AuthenticationError):
            service.decode_token(token, expected_kind=TokenKind.REFRESH)
