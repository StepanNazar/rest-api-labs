"""Integration tests for authentication endpoints."""

from fastapi.testclient import TestClient

from app.main import app


class TestLogin:
    def test_returns_access_and_refresh_tokens_for_any_credentials(self) -> None:
        client = TestClient(app)

        response = client.post(
            "/token",
            data={"username": "johndoe", "password": "secret"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)
        assert isinstance(body["refresh_token"], str)
        assert body["access_token"] != body["refresh_token"]

class TestRefreshToken:
    def test_returns_new_access_token_for_valid_refresh_token(self) -> None:
        client = TestClient(app)
        login_response = client.post(
            "/token",
            data={"username": "johndoe", "password": "secret"},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post("/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)

    def test_returns_401_when_refresh_token_is_invalid(self) -> None:
        client = TestClient(app)

        response = client.post("/refresh", json={"refresh_token": "not-a-token"})

        assert response.status_code == 401


class TestProtectedBooks:
    def test_returns_401_without_access_token(self) -> None:
        client = TestClient(app)

        response = client.get("/books/")

        assert response.status_code == 401
