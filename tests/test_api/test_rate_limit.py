"""API tests for Redis-backed request rate limiting."""

from fastapi.testclient import TestClient

from app.dependencies import RATE_LIMITS
from app.services.auth_service import AuthService


def _auth_headers(username: str = "johndoe") -> dict[str, str]:
    """Return bearer authorization headers for a test user."""
    token = AuthService().create_access_token(username)
    return {"Authorization": f"Bearer {token}"}


class TestAnonymousRateLimit:
    def test_returns_200_when_anonymous_user_has_not_reached_limit(
        self,
        fastapi_client: TestClient,
    ) -> None:
        limit, _ = RATE_LIMITS["anonymous"]

        responses = [fastapi_client.get("/books/") for _ in range(limit)]

        assert all(response.status_code == 200 for response in responses)

    def test_returns_429_when_anonymous_user_has_reached_limit(
        self,
        fastapi_client: TestClient,
    ) -> None:
        limit, _ = RATE_LIMITS["anonymous"]
        for _ in range(limit):
            fastapi_client.get("/books/")

        response = fastapi_client.get("/books/")

        assert response.status_code == 429


class TestAuthenticatedRateLimit:
    def test_returns_200_when_authenticated_user_has_not_reached_limit(
        self,
        fastapi_client: TestClient,
    ) -> None:
        limit, _ = RATE_LIMITS["authenticated"]
        headers = _auth_headers()

        responses = [fastapi_client.get("/books/", headers=headers) for _ in range(limit)]

        assert all(response.status_code == 200 for response in responses)

    def test_returns_429_when_authenticated_user_has_reached_limit(
        self,
        fastapi_client: TestClient,
    ) -> None:
        limit, _ = RATE_LIMITS["authenticated"]
        headers = _auth_headers()
        for _ in range(limit):
            fastapi_client.get("/books/", headers=headers)

        response = fastapi_client.get("/books/", headers=headers)

        assert response.status_code == 429
