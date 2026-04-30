# AGENTS.md — Coding Agent Instructions

Read this file at the start of every session. **Keep this file concise** — explain everything in as few words as possible to avoid polluting the context window.

---

## Project Overview

A **Library REST API** built with FastAPI. Manages the `Book` entity with database storage (PostgreSQL or MongoDB).

### Technology Stack

| Tool | Purpose |
|------|---------|
| **Python 3.12+** | Language |
| **FastAPI** | Web framework |
| **Pydantic v2** | Request/response validation and serialization |
| **SQLAlchemy** | Database ORM (PostgreSQL) |
| **Pydantic-Mongo** | MongoDB repository support |
| **FastAPI Hypermodel** | Siren hypermedia support |
| **uv** | Package manager and virtual environment |
| **ruff** | Linter and formatter |
| **mypy** | Static type checker (strict mode) |
| **pytest** | Test framework |
| **pytest-asyncio** | Async test support |

### Project Structure

```
.
├── app/
│   ├── main.py                      # FastAPI app entry point
│   ├── database.py                  # Database configuration (SQLAlchemy/Mongo)
│   ├── dependencies.py              # FastAPI dependency injection providers
│   ├── api/
│   │   └── books.py                 # HTTP endpoints — catches domain exceptions, maps to HTTP
│   ├── dtos/
│   │   └── books.py                 # Pydantic models for domain data & enums
│   ├── models/
│   │   └── book.py                  # SQLAlchemy database models
│   ├── repository/
│   │   └── book_repository.py       # Storage logic (PostgreSQL/SQLAlchemy and MongoDB)
│   ├── schemas/
│   │   └── book.py                  # Hypermedia-aware Pydantic schemas (Siren)
│   └── services/
│       ├── book_service.py          # Business logic (thin orchestration layer)
│       └── exceptions.py            # Domain exceptions (BookNotFoundError)
└── tests/
    ├── conftest.py                  # Shared fixtures: repository, service, client
    ├── helpers.py                   # Shared test utilities (make_book)
    ├── test_api/
    │   └── test_books.py            # HTTP-layer tests (status codes, validation, serialization)
    ├── test_repository/
    │   └── test_book_repository.py  # Unit tests for repositories (filtering, sorting, pagination)
    └── test_services/
        └── test_book_service.py     # Unit tests for BookService (delegation + exception behavior)
```

### Layer Responsibilities

- **dtos/** — Pydantic models representing domain data and enums. These are framework-agnostic data carriers.
- **models/** — Database-specific models (e.g., SQLAlchemy `Base` classes).
- **schemas/** — Hypermedia-aware Pydantic models (Siren) used for API request validation and JSON serialization.
- **repository/** — All data access and querying logic (filtering, sorting, pagination, CRUD). Supports multiple backends.
- **services/** — Thin orchestration layer. Delegates to repository. Raises domain exceptions (never HTTP exceptions).
- **api/** — HTTP boundary. Catches domain exceptions and converts them to `HTTPException`. Handles Hypermedia response mapping.

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
uv run pytest

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
- Use **Pydantic BaseModel** for DTO objects, not `TypedDict`, plain dicts, or dataclasses.

### Architecture Rules

- **Service layer must never import from `fastapi`** (no `HTTPException`, no `status`). Raise plain Python domain exceptions instead.
- **API layer translates domain exceptions to HTTP exceptions** using `try/except`.
- **Service layer returns DTO objects** (`Book`, `list[Book]`), never schema objects. FastAPI's `response_model` handles serialization to Siren hypermedia schemas.
- **Filtering, sorting, and pagination logic belongs in the repository layer**, not in services.
- **ID generation belongs in the repository layer**, not in services.
- **Do not use `Query()` wrapper** in FastAPI route function signatures unless you need additional validation parameters (e.g., aliases, metadata). Name parameters directly as you want them to appear in the query string.

---

## Test-Driven Development (TDD)

Follow this strict order for every new feature:

### Step 1 — Plan

Before writing any code, define the class/function signatures (stubs) for the new feature. Do not implement them yet.

```python
class BookService:
    async def create_book(self, data: BookCreate) -> Book:
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
- **Do not duplicate tests across layers.** Test each concern at exactly one level:
  - **Repository**: all filtering, sorting, pagination, and CRUD edge cases.
  - **Service**: delegation to repository, ID mapping, domain exception raising.
  - **API**: HTTP status codes, input validation (422), Hypermedia links, and domain→HTTP exception mapping.

### Step 3 — Implement

Write production code only after all tests exist. Keep implementation clean and free of comments (use names instead).

---

## Common Mistakes to Avoid

- **Do not write `# Arrange`, `# Act`, `# Assert` labels as comments** in tests. Use blank lines to separate sections instead.
- **Do not put filtering/sorting logic in the service layer** — it belongs in the repository.
- **Do not raise `HTTPException` in services** — raise domain exceptions (`BookNotFoundError`) and let the API layer convert them.
- **Do not use `TypedDict` for domain data** — use Pydantic `BaseModel` for DTOs.
- **Do not return schema objects from the service layer** — return DTO objects and let FastAPI's `response_model` handle serialization.
- **Do not duplicate business logic tests across layers** — test filtering/sorting in repository tests; test delegation in service tests; test HTTP behavior in API tests.
- When adding a new field, update: DTO, SQLAlchemy model, Mongo model, schemas (BookCreate + BookResponse), repository mappings, service, and all affected tests.

---

## When You Are Corrected

If a human corrects a mistake that is not a unique task-specific one that will never be repeated, **add a rule to the "Common Mistakes to Avoid" section** above so you never repeat it.
