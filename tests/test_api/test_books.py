"""Integration tests for the /books API endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

VALID_BOOK_PAYLOAD = {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "description": "A novel about the American dream.",
    "status": "available",
    "year": 1925,
}


def _post_book(client: TestClient, overrides: dict[str, object] | None = None) -> dict[str, object]:
    """Helper to create a book via the API and return the response JSON."""
    payload = {**VALID_BOOK_PAYLOAD, **(overrides or {})}
    response = client.post("/books/", json=payload)
    assert response.status_code == 201
    result: dict[str, object] = response.json()
    return result


class TestGetAllBooks:
    def test_returns_200_and_empty_list_when_no_books_exist(self, client: TestClient) -> None:
        # Arrange - client has an empty repository

        # Act
        response = client.get("/books/")

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_200_with_all_books_after_adding_several(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "Book One"})
        _post_book(client, {"title": "Book Two"})

        # Act
        response = client.get("/books/")

        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_filters_by_available_status(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "Available", "status": "available"})
        _post_book(client, {"title": "Issued", "status": "issued"})

        # Act
        response = client.get("/books/", params={"status": "available"})

        # Assert
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == "Available"

    def test_filters_by_issued_status(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "Available", "status": "available"})
        _post_book(client, {"title": "Issued", "status": "issued"})

        # Act
        response = client.get("/books/", params={"status": "issued"})

        # Assert
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == "Issued"

    def test_filters_by_author_case_insensitively(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"author": "John Doe"})
        _post_book(client, {"author": "Jane Smith"})

        # Act
        response = client.get("/books/", params={"author": "john"})

        # Assert
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["author"] == "John Doe"

    def test_sorts_by_title_ascending(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "Zebra Book"})
        _post_book(client, {"title": "Apple Book"})

        # Act
        response = client.get("/books/", params={"sort_by": "title", "order": "asc"})

        # Assert
        assert response.status_code == 200
        titles = [b["title"] for b in response.json()]
        assert titles == ["Apple Book", "Zebra Book"]

    def test_sorts_by_title_descending(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "Zebra Book"})
        _post_book(client, {"title": "Apple Book"})

        # Act
        response = client.get("/books/", params={"sort_by": "title", "order": "desc"})

        # Assert
        assert response.status_code == 200
        titles = [b["title"] for b in response.json()]
        assert titles == ["Zebra Book", "Apple Book"]

    def test_sorts_by_year_ascending(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "New", "year": 2020})
        _post_book(client, {"title": "Old", "year": 1990})

        # Act
        response = client.get("/books/", params={"sort_by": "year", "order": "asc"})

        # Assert
        assert response.status_code == 200
        years = [b["year"] for b in response.json()]
        assert years == [1990, 2020]

    def test_sorts_by_year_descending(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "New", "year": 2020})
        _post_book(client, {"title": "Old", "year": 1990})

        # Act
        response = client.get("/books/", params={"sort_by": "year", "order": "desc"})

        # Assert
        assert response.status_code == 200
        years = [b["year"] for b in response.json()]
        assert years == [2020, 1990]

    def test_returns_422_for_invalid_status_filter(self, client: TestClient) -> None:
        # Arrange - invalid status value

        # Act
        response = client.get("/books/", params={"status": "nonexistent"})

        # Assert
        assert response.status_code == 422

    def test_returns_422_for_invalid_sort_field(self, client: TestClient) -> None:
        # Arrange

        # Act
        response = client.get("/books/", params={"sort_by": "invalid_field"})

        # Assert
        assert response.status_code == 422

    def test_combined_filter_and_sort_returns_correct_subset(self, client: TestClient) -> None:
        # Arrange
        _post_book(client, {"title": "C Book", "status": "available", "year": 2000})
        _post_book(client, {"title": "A Book", "status": "available", "year": 2010})
        _post_book(client, {"title": "B Book", "status": "issued", "year": 1990})

        # Act
        response = client.get(
            "/books/", params={"status": "available", "sort_by": "title", "order": "asc"}
        )

        # Assert
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 2
        assert [b["title"] for b in books] == ["A Book", "C Book"]


class TestGetBookById:
    def test_returns_200_and_book_when_id_exists(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(client)

        # Act
        response = client.get(f"/books/{created['id']}")

        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_returns_404_when_book_id_does_not_exist(self, client: TestClient) -> None:
        # Arrange
        missing_id = str(uuid4())

        # Act
        response = client.get(f"/books/{missing_id}")

        # Assert
        assert response.status_code == 404

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        # Arrange

        # Act
        response = client.get("/books/not-a-valid-uuid")

        # Assert
        assert response.status_code == 422

    def test_returned_book_contains_all_expected_fields(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(
            client,
            {
                "title": "Full Book",
                "author": "Real Author",
                "description": "Some description",
                "status": "issued",
                "year": 2001,
            },
        )

        # Act
        response = client.get(f"/books/{created['id']}")

        # Assert
        body = response.json()
        assert body["title"] == "Full Book"
        assert body["author"] == "Real Author"
        assert body["description"] == "Some description"
        assert body["status"] == "issued"
        assert body["year"] == 2001


class TestCreateBook:
    def test_returns_201_with_created_book(self, client: TestClient) -> None:
        # Arrange

        # Act
        response = client.post("/books/", json=VALID_BOOK_PAYLOAD)

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == VALID_BOOK_PAYLOAD["title"]

    def test_auto_generates_a_uuid_for_the_new_book(self, client: TestClient) -> None:
        # Arrange

        # Act
        response = client.post("/books/", json=VALID_BOOK_PAYLOAD)

        # Assert
        body = response.json()
        assert "id" in body
        assert len(body["id"]) == 36

    def test_two_books_with_same_data_receive_different_ids(self, client: TestClient) -> None:
        # Arrange

        # Act
        first = client.post("/books/", json=VALID_BOOK_PAYLOAD).json()
        second = client.post("/books/", json=VALID_BOOK_PAYLOAD).json()

        # Assert
        assert first["id"] != second["id"]

    def test_returns_422_when_title_is_missing(self, client: TestClient) -> None:
        # Arrange
        payload = {k: v for k, v in VALID_BOOK_PAYLOAD.items() if k != "title"}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 422

    def test_returns_422_when_author_is_missing(self, client: TestClient) -> None:
        # Arrange
        payload = {k: v for k, v in VALID_BOOK_PAYLOAD.items() if k != "author"}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 422

    def test_returns_422_when_status_is_invalid(self, client: TestClient) -> None:
        # Arrange
        payload = {**VALID_BOOK_PAYLOAD, "status": "unknown_status"}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 422

    @pytest.mark.parametrize("year", [999, 2101])
    def test_returns_422_when_year_is_out_of_range(self, client: TestClient, year: int) -> None:
        # Arrange
        payload = {**VALID_BOOK_PAYLOAD, "year": year}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 422

    @pytest.mark.parametrize("year", [1000, 2100])
    def test_accepts_boundary_years(self, client: TestClient, year: int) -> None:
        # Arrange
        payload = {**VALID_BOOK_PAYLOAD, "year": year}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 201

    def test_returns_422_when_title_is_empty_string(self, client: TestClient) -> None:
        # Arrange
        payload = {**VALID_BOOK_PAYLOAD, "title": ""}

        # Act
        response = client.post("/books/", json=payload)

        # Assert
        assert response.status_code == 422

    def test_book_is_retrievable_after_creation(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(client)

        # Act
        response = client.get(f"/books/{created['id']}")

        # Assert
        assert response.status_code == 200


class TestDeleteBook:
    def test_returns_204_when_book_exists(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(client)

        # Act
        response = client.delete(f"/books/{created['id']}")

        # Assert
        assert response.status_code == 204

    def test_returns_204_when_book_does_not_exist(self, client: TestClient) -> None:
        # Arrange
        non_existing_id = str(uuid4())

        # Act
        response = client.delete(f"/books/{non_existing_id}")

        # Assert
        assert response.status_code == 204

    def test_deleted_book_is_no_longer_retrievable(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(client)

        # Act
        client.delete(f"/books/{created['id']}")
        response = client.get(f"/books/{created['id']}")

        # Assert
        assert response.status_code == 404

    def test_is_idempotent_when_called_twice(self, client: TestClient) -> None:
        # Arrange
        created = _post_book(client)

        # Act
        first_response = client.delete(f"/books/{created['id']}")
        second_response = client.delete(f"/books/{created['id']}")

        # Assert
        assert first_response.status_code == 204
        assert second_response.status_code == 204

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        # Arrange

        # Act
        response = client.delete("/books/not-a-uuid")

        # Assert
        assert response.status_code == 422

    def test_does_not_affect_other_books_when_deleting_one(self, client: TestClient) -> None:
        # Arrange
        book_to_delete = _post_book(client, {"title": "Delete Me"})
        book_to_keep = _post_book(client, {"title": "Keep Me"})

        # Act
        client.delete(f"/books/{book_to_delete['id']}")
        all_books = client.get("/books/").json()

        # Assert
        assert len(all_books) == 1
        assert all_books[0]["id"] == book_to_keep["id"]
