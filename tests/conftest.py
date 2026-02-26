"""Shared pytest fixtures for the test suite."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from dependencies import get_book_repository, get_book_service
from main import app
from repository.book_repository import BookRepository
from services.book_service import BookService


@pytest.fixture()
def fresh_repository() -> BookRepository:
    """Return an empty, isolated BookRepository for each test."""
    return BookRepository()


@pytest.fixture()
def fresh_service(fresh_repository: BookRepository) -> BookService:
    """Return a BookService backed by a fresh, empty repository."""
    return BookService(fresh_repository)


@pytest.fixture()
def client(fresh_service: BookService) -> Generator[TestClient, None, None]:
    """Return a TestClient with all dependencies overridden to use isolated state."""
    app.dependency_overrides[get_book_service] = lambda: fresh_service
    app.dependency_overrides[get_book_repository] = lambda: fresh_service._repository
    yield TestClient(app)
    app.dependency_overrides.clear()
