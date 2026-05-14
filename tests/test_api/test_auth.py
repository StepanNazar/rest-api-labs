"""Integration tests for authentication endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestLogin:
    def test_returns_access_token_and_sets_refresh_token_cookie_for_any_credentials(
        self,
    ) -> None:
        client = TestClient(app)

        response = client.post(
            "/token",
            json={"username": "johndoe", "password": "secret"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)
        assert "refresh_token" not in body
        assert "refresh_token=" in response.headers["set-cookie"]
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "Path=/refresh" in response.headers["set-cookie"]


class TestRefreshToken:
    def test_returns_new_access_token_when_refresh_token_cookie_is_valid(self) -> None:
        client = TestClient(app)

        client.post(
            "/token",
            json={"username": "johndoe", "password": "secret"},
        )

        response = client.post("/refresh")

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)

    def test_returns_401_when_refresh_token_cookie_is_invalid(self) -> None:
        client = TestClient(app)
        client.cookies.set("refresh_token", "not-a-token", path="/refresh")

        response = client.post("/refresh")

        assert response.status_code == 401

    def test_returns_401_when_refresh_token_cookie_is_missing(self) -> None:
        client = TestClient(app)

        response = client.post("/refresh")

        assert response.status_code == 401


class TestProtectedBooks:
    def test_returns_401_without_access_token(self) -> None:
        client = TestClient(app)

        response = client.get("/books/")

        assert response.status_code == 401
