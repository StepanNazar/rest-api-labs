"""Integration tests for the /books API endpoints."""

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
    result: dict[str, object] = response.json()
    return result


class TestGetAllBooks:
    def test_returns_200_and_empty_list_when_no_books_exist(self, client: TestClient) -> None:
        response = client.get("/books/")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_200_with_all_books_after_adding_several(self, client: TestClient) -> None:
        _post_book(client, {"title": "Book One"})
        _post_book(client, {"title": "Book Two"})

        response = client.get("/books/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_filters_by_available_status(self, client: TestClient) -> None:
        _post_book(client, {"title": "Available", "status": "available"})
        _post_book(client, {"title": "Issued", "status": "issued"})

        response = client.get("/books/", params={"status": "available"})

        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == "Available"

    def test_filters_by_issued_status(self, client: TestClient) -> None:
        _post_book(client, {"title": "Available", "status": "available"})
        _post_book(client, {"title": "Issued", "status": "issued"})

        response = client.get("/books/", params={"status": "issued"})

        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == "Issued"

    def test_filters_by_exact_author_match(self, client: TestClient) -> None:
        _post_book(client, {"author": "John Doe"})
        _post_book(client, {"author": "Jane Smith"})

        response = client.get("/books/", params={"author": "John Doe"})

        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["author"] == "John Doe"

    def test_does_not_match_partial_author_name(self, client: TestClient) -> None:
        _post_book(client, {"author": "George R.R. Martin"})
        _post_book(client, {"author": "George Orwell"})

        response = client.get("/books/", params={"author": "George"})

        assert response.status_code == 200
        assert response.json() == []

    def test_sorts_by_title_ascending(self, client: TestClient) -> None:
        _post_book(client, {"title": "Zebra Book"})
        _post_book(client, {"title": "Apple Book"})

        response = client.get("/books/", params={"sort_by": "title", "order": "asc"})

        assert response.status_code == 200
        titles = [b["title"] for b in response.json()]
        assert titles == ["Apple Book", "Zebra Book"]

    def test_sorts_by_title_descending(self, client: TestClient) -> None:
        _post_book(client, {"title": "Zebra Book"})
        _post_book(client, {"title": "Apple Book"})

        response = client.get("/books/", params={"sort_by": "title", "order": "desc"})

        assert response.status_code == 200
        titles = [b["title"] for b in response.json()]
        assert titles == ["Zebra Book", "Apple Book"]

    def test_sorts_by_year_ascending(self, client: TestClient) -> None:
        _post_book(client, {"title": "New", "publication_year": 2020})
        _post_book(client, {"title": "Old", "publication_year": 1990})

        response = client.get("/books/", params={"sort_by": "year", "order": "asc"})

        assert response.status_code == 200
        years = [b["publication_year"] for b in response.json()]
        assert years == [1990, 2020]

    def test_sorts_by_year_descending(self, client: TestClient) -> None:
        _post_book(client, {"title": "New", "publication_year": 2020})
        _post_book(client, {"title": "Old", "publication_year": 1990})

        response = client.get("/books/", params={"sort_by": "year", "order": "desc"})

        assert response.status_code == 200
        years = [b["publication_year"] for b in response.json()]
        assert years == [2020, 1990]

    def test_returns_422_for_invalid_status_filter(self, client: TestClient) -> None:
        response = client.get("/books/", params={"status": "nonexistent"})

        assert response.status_code == 422

    def test_returns_422_for_invalid_sort_field(self, client: TestClient) -> None:
        response = client.get("/books/", params={"sort_by": "invalid_field"})

        assert response.status_code == 422

    def test_combined_filter_and_sort_returns_correct_subset(self, client: TestClient) -> None:
        _post_book(client, {"title": "C Book", "status": "available", "publication_year": 2000})
        _post_book(client, {"title": "A Book", "status": "available", "publication_year": 2010})
        _post_book(client, {"title": "B Book", "status": "issued", "publication_year": 1990})

        response = client.get(
            "/books/", params={"status": "available", "sort_by": "title", "order": "asc"}
        )

        assert response.status_code == 200
        books = response.json()
        assert len(books) == 2
        assert [b["title"] for b in books] == ["A Book", "C Book"]


class TestGetBookById:
    def test_returns_200_and_book_when_id_exists(self, client: TestClient) -> None:
        created = _post_book(client)

        response = client.get(f"/books/{created['id']}")

        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_returns_404_when_book_id_does_not_exist(self, client: TestClient) -> None:
        missing_id = str(uuid4())

        response = client.get(f"/books/{missing_id}")

        assert response.status_code == 404

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        response = client.get("/books/not-a-valid-uuid")

        assert response.status_code == 422

    def test_returned_book_contains_all_expected_fields(self, client: TestClient) -> None:
        created = _post_book(
            client,
            {
                "title": "Full Book",
                "author": "Real Author",
                "description": "Some description",
                "status": "issued",
                "publication_year": 2001,
            },
        )

        response = client.get(f"/books/{created['id']}")

        body = response.json()
        assert body["title"] == "Full Book"
        assert body["author"] == "Real Author"
        assert body["description"] == "Some description"
        assert body["status"] == "issued"
        assert body["publication_year"] == 2001


class TestCreateBook:
    def test_returns_201_with_created_book(self, client: TestClient) -> None:
        response = client.post("/books/", json=VALID_BOOK_PAYLOAD)

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == VALID_BOOK_PAYLOAD["title"]

    def test_auto_generates_a_uuid_for_the_new_book(self, client: TestClient) -> None:
        response = client.post("/books/", json=VALID_BOOK_PAYLOAD)

        body = response.json()
        assert "id" in body
        assert len(body["id"]) == 36

    def test_two_books_with_same_data_receive_different_ids(self, client: TestClient) -> None:
        first = client.post("/books/", json=VALID_BOOK_PAYLOAD).json()
        second = client.post("/books/", json=VALID_BOOK_PAYLOAD).json()

        assert first["id"] != second["id"]

    def test_returns_422_when_title_is_missing(self, client: TestClient) -> None:
        payload = {k: v for k, v in VALID_BOOK_PAYLOAD.items() if k != "title"}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422

    def test_returns_422_when_author_is_missing(self, client: TestClient) -> None:
        payload = {k: v for k, v in VALID_BOOK_PAYLOAD.items() if k != "author"}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422

    def test_returns_422_when_status_is_invalid(self, client: TestClient) -> None:
        payload = {**VALID_BOOK_PAYLOAD, "status": "unknown_status"}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422

    def test_returns_422_when_title_is_empty_string(self, client: TestClient) -> None:
        payload = {**VALID_BOOK_PAYLOAD, "title": ""}

        response = client.post("/books/", json=payload)

        assert response.status_code == 422

    def test_book_is_retrievable_after_creation(self, client: TestClient) -> None:
        created = _post_book(client)

        response = client.get(f"/books/{created['id']}")

        assert response.status_code == 200

    @pytest.mark.parametrize("publication_year", [-9999, 0, 9999])
    def test_accepts_any_integer_for_publication_year(
        self, client: TestClient, publication_year: int
    ) -> None:
        payload = {**VALID_BOOK_PAYLOAD, "publication_year": publication_year}

        response = client.post("/books/", json=payload)

        assert response.status_code == 201


class TestDeleteBook:
    def test_returns_204_when_book_exists(self, client: TestClient) -> None:
        created = _post_book(client)

        response = client.delete(f"/books/{created['id']}")

        assert response.status_code == 204

    def test_returns_204_when_book_does_not_exist(self, client: TestClient) -> None:
        non_existing_id = str(uuid4())

        response = client.delete(f"/books/{non_existing_id}")

        assert response.status_code == 204

    def test_deleted_book_is_no_longer_retrievable(self, client: TestClient) -> None:
        created = _post_book(client)

        client.delete(f"/books/{created['id']}")
        response = client.get(f"/books/{created['id']}")

        assert response.status_code == 404

    def test_is_idempotent_when_called_twice(self, client: TestClient) -> None:
        created = _post_book(client)

        first_response = client.delete(f"/books/{created['id']}")
        second_response = client.delete(f"/books/{created['id']}")

        assert first_response.status_code == 204
        assert second_response.status_code == 204

    def test_returns_422_for_non_uuid_id(self, client: TestClient) -> None:
        response = client.delete("/books/not-a-uuid")

        assert response.status_code == 422

    def test_does_not_affect_other_books_when_deleting_one(self, client: TestClient) -> None:
        book_to_delete = _post_book(client, {"title": "Delete Me"})
        book_to_keep = _post_book(client, {"title": "Keep Me"})

        client.delete(f"/books/{book_to_delete['id']}")
        all_books = client.get("/books/").json()

        assert len(all_books) == 1
        assert all_books[0]["id"] == book_to_keep["id"]
