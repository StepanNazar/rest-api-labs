"""Integration tests for the /books API endpoints.

Only tests HTTP-specific behavior: status codes, input validation, and response structure.
Business logic (filtering, sorting) is tested in lower-layer tests.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

VALID_BOOK_PAYLOAD = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel about the American dream.",
    "status": "available",
    "publication_year": 1925,
}


def _post_book(client: TestClient, overrides: dict[str, object] | None = None) -> dict[str, object]:
    """Helper to create a book via the API and return the response JSON."""
    payload = {**VALID_BOOK_PAYLOAD, **(overrides or {})}
    response = client.post("/books/", json=payload)
    assert response.status_code == 201
    result: dict[str, object] = response.json()["properties"]
    return result


class TestGetAllBooks:
    def test_returns_200_and_empty_list_when_no_books_exist(self, client: TestClient) -> None:
        response = client.get("/books/")

        assert response.status_code == 200
        assert "items" not in response.json()["properties"]

    def test_returns_200_with_all_books(self, client: TestClient) -> None:
        _post_book(client, {"title": "Book One"})
        _post_book(client, {"title": "Book Two"})

        response = client.get("/books/")

        assert response.status_code == 200
        assert len(response.json()["properties"]["items"]) == 2

    def test_returns_paginated_books_with_limit_and_offset(self, client: TestClient) -> None:
        for i in range(10):
            _post_book(client, {"title": f"Book {i:02d}"})

        # We need a stable sort to test offset correctly
        params: dict[str, str | int] = {"limit": 3, "offset": 3, "sort_by": "title", "order": "asc"}
        response = client.get("/books/", params=params)

        assert response.status_code == 200
        items = response.json()["properties"]["items"]
        assert len(items) == 3
        # Offset 3 skips index 0, 1, 2. So starting with 3.
        assert items[0]["properties"]["title"] == "Book 03"
        assert items[1]["properties"]["title"] == "Book 04"
        assert items[2]["properties"]["title"] == "Book 05"

    def test_returns_422_for_invalid_limit_too_small(self, client: TestClient) -> None:
        response = client.get("/books/", params={"limit": 0})

        assert response.status_code == 422

    def test_returns_422_for_invalid_limit_too_large(self, client: TestClient) -> None:
        response = client.get("/books/", params={"limit": 101})

        assert response.status_code == 422

    def test_returns_422_for_invalid_offset_negative(self, client: TestClient) -> None:
        response = client.get("/books/", params={"offset": -1})

        assert response.status_code == 422

    def test_returns_422_for_invalid_status_filter(self, client: TestClient) -> None:
        response = client.get("/books/", params={"status": "nonexistent"})

        assert response.status_code == 422

    def test_returns_422_for_invalid_sort_field(self, client: TestClient) -> None:
        response = client.get("/books/", params={"sort_by": "invalid_field"})

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "params",
        [
            {"status": "available"},
            {"status": "issued"},
            {"author": "F. Scott Fitzgerald"},
            {"sort_by": "title"},
            {"sort_by": "year"},
            {"order": "asc"},
            {"order": "desc"},
            {"sort_by": "title", "order": "desc"},
            {"status": "available", "sort_by": "year", "order": "asc"},
        ],
    )
    def test_returns_200_for_valid_query_params(
        self, client: TestClient, params: dict[str, str]
    ) -> None:
        _post_book(client)

        response = client.get("/books/", params=params)

        assert response.status_code == 200


class TestGetBookById:
    def test_returns_200_and_book_when_id_exists(self, client: TestClient) -> None:
        created = _post_book(client)

        response = client.get(f"/books/{created['id']}")

        assert response.status_code == 200
        assert response.json()["properties"]["id"] == created["id"]

    def test_returns_404_when_book_id_does_not_exist(self, client: TestClient) -> None:
        response = client.get(f"/books/{uuid4()}")

        assert response.status_code == 404

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        response = client.get("/books/not-a-valid-uuid")

        assert response.status_code == 422


class TestCreateBook:
    def test_returns_201_with_book_data(self, client: TestClient) -> None:
        response = client.post("/books/", json=VALID_BOOK_PAYLOAD)

        assert response.status_code == 201
        body = response.json()
        assert body["properties"]["title"] == VALID_BOOK_PAYLOAD["title"]
        assert len(body["properties"]["id"]) == 36

    def test_returns_422_when_required_field_is_missing(self, client: TestClient) -> None:
        payload = {k: v for k, v in VALID_BOOK_PAYLOAD.items() if k != "title"}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422

    def test_returns_422_when_status_is_invalid(self, client: TestClient) -> None:
        payload = {**VALID_BOOK_PAYLOAD, "status": "unknown_status"}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422


class TestDeleteBook:
    def test_returns_204_when_book_exists(self, client: TestClient) -> None:
        created = _post_book(client)

        response = client.delete(f"/books/{created['id']}")

        assert response.status_code == 204

    def test_returns_204_when_book_does_not_exist(self, client: TestClient) -> None:
        response = client.delete(f"/books/{uuid4()}")

        assert response.status_code == 204

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        response = client.delete("/books/not-a-uuid")

        assert response.status_code == 422
