# AGENTS.md — Coding Agent Instructions

This file contains instructions for AI coding agents working on this repository. Read it at the start of every session before making any changes.

---

## Project Overview

A **Library REST API** built with FastAPI. Manages the `Book` entity with in-memory storage.

### Technology Stack

| Tool | Purpose |
|------|---------|
| **Python 3.12+** | Language |
| **FastAPI** | Web framework |
| **Pydantic v2** | Request/response validation and serialization |
| **uv** | Package manager and virtual environment |
| **ruff** | Linter and formatter |
| **mypy** | Static type checker (strict mode) |
| **pytest** | Test framework |
| **pytest-asyncio** | Async test support |

### Project Structure

```
.
├── main.py                          # FastAPI app entry point
├── dependencies.py                  # FastAPI dependency injection providers
├── models/
│   └── book.py                      # Domain model: Book dataclass, BookStatus, SortField, SortOrder
├── schemas/
│   └── book.py                      # Pydantic schemas: BookCreate, BookResponse
├── repository/
│   └── book_repository.py           # In-memory CRUD + filtering/sorting (dict[UUID, Book])
├── services/
│   ├── book_service.py              # Business logic (thin orchestration layer)
│   └── exceptions.py                # Domain exceptions (BookNotFoundError)
├── api/
│   └── books.py                     # HTTP endpoints — catches domain exceptions, maps to HTTP
└── tests/
    ├── conftest.py                  # Shared fixtures (fresh_repository, fresh_service, client)
    ├── test_api/
    │   └── test_books.py            # Integration tests for all endpoints
    ├── test_repository/
    │   └── test_book_repository.py  # Unit tests for BookRepository
    └── test_services/
        └── test_book_service.py     # Unit tests for BookService
```

### Layer Responsibilities

- **models/** — Pure domain types. No framework dependencies. `SortField`/`SortOrder` enums live here because they describe domain query capabilities.
- **schemas/** — Pydantic models for API request validation and JSON serialization only.
- **repository/** — All data access and querying logic (filtering, sorting). No HTTP knowledge.
- **services/** — Thin orchestration layer. Delegates filtering/sorting to repository. Raises domain exceptions (never HTTP exceptions).
- **api/** — HTTP boundary. Catches domain exceptions and converts them to `HTTPException`. Does not contain business logic.

---

## API Endpoints

| Method | Path | Status |
|--------|------|--------|
| `GET` | `/books/` | 200 |
| `GET` | `/books/{id}` | 200 / 404 |
| `POST` | `/books/` | 201 |
| `DELETE` | `/books/{id}` | 204 (idempotent) |

Query params for `GET /books/`: `status`, `author` (exact match), `sort_by` (`title`|`year`), `order` (`asc`|`desc`).

---

## Development Workflow

```bash
# Install dependencies
uv sync --dev

# Run the server
uv run python main.py

# Run tests
uv run pytest tests/ -v

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy . --exclude .venv
```

Always run all three quality checks before committing.

---

## Python Coding Standards

### General

- Use **type hints** on every function signature and variable where the type is not obvious.
- Write **docstrings** on every public function and class using the Google-style format:
  ```python
  def my_function(arg: str) -> int:
      """Short one-line description.

      Args:
          arg: What this argument represents.

      Returns:
          What the function returns.

      Raises:
          SomeError: When and why it is raised.
      """
  ```
- No inline comments unless they answer **why** the code is written this way (not what it does). Readable names make the "what" obvious.
- Prefer **descriptive variable names** over comments: `filtered_books` not `result`.
- Follow all **Clean Code** principles: single responsibility, DRY, small functions, clear names.
- Use `StrEnum` for enumerations that are also used as string values.
- Use **dataclasses** for domain model objects, not `TypedDict` or plain dicts.

### Architecture Rules

- **Service layer must never import from `fastapi`** (no `HTTPException`, no `status`). Raise plain Python domain exceptions instead.
- **API layer translates domain exceptions to HTTP exceptions** using `try/except`.
- **Filtering and sorting logic belongs in the repository layer**, not in services.
- **Author filtering is exact match** (not case-insensitive substring).
- **Do not use `Query()` wrapper** in FastAPI route function signatures unless you need additional validation parameters (e.g., aliases, metadata). Name parameters directly as you want them to appear in the query string.

---

## Test-Driven Development (TDD)

Follow this strict order for every new feature:

### Step 1 — Plan

Before writing any code, define the class/function signatures (stubs) for the new feature. Do not implement them yet.

```python
class BookService:
    async def create_book(self, data: BookCreate) -> BookResponse:
        ...
```

### Step 2 — Write All Tests First

Write **all tests before implementing** the production code. Tests must:

- Have **descriptive names that read as sentences**: `test_returns_404_when_book_id_does_not_exist`
- Be organized in **classes** by the method/endpoint being tested: `class TestGetBook:`
- Be split into exactly **three labelled sections** (no inline comments for these labels — just blank-line separation):

  ```python
  def test_returns_404_when_book_id_does_not_exist(self, service: BookService) -> None:
      missing_id = uuid4()

      with pytest.raises(BookNotFoundError):
          await service.get_book(missing_id)
  ```
  In practice, **do not write `# Arrange`, `# Act`, `# Assert` as comments**. Separate the three sections with blank lines only.

- Use `@pytest.fixture()` for shared setup.
- Use `@pytest.mark.parametrize` to cover boundary values and multiple input variants.
- **Cover all logic combinations**: happy paths, edge cases, boundary values, error cases.

### Step 3 — Implement

Write production code only after all tests exist. Keep implementation clean and free of comments (use names instead).

---

## Common Mistakes to Avoid

- **Do not write `# Arrange`, `# Act`, `# Assert` labels as comments** in tests. Use blank lines to separate sections instead.
- **Do not put filtering/sorting logic in the service layer** — it belongs in the repository.
- **Do not raise `HTTPException` in services** — raise domain exceptions (`BookNotFoundError`) and let the API layer convert them.
- **Do not use `TypedDict` for domain models** — use `@dataclass` for mutable domain objects.
- **Do not use `Query()` wrapper** for simple query params that need no aliases or extra validation.
- **Do not enforce arbitrary range constraints on `publication_year`** unless explicitly required by the spec.
- **Author filter is exact match**, not a case-insensitive substring search.
- When adding a new field to the domain model, update: model, schema (BookCreate + BookResponse), repository `_SORT_ATTR` mapping (if sortable), service, and all affected tests.

---

## When You Are Corrected

If a human corrects a general mistake you made (not a project-specific one), **add a rule to the "Common Mistakes to Avoid" section** above so you never repeat it.
