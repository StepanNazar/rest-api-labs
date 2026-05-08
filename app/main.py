"""FastAPI application entry point for the Library API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi_hypermodel import SirenHyperModel

from app.api.auth import router as auth_router
from app.api import router as books_router
from app.database import Base, engine
from app.dependencies import get_sql_book_repository, get_mongo_book_repository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_sql_book_repository] = get_mongo_book_repository
    yield


app = FastAPI(title="Library API", version="0.1.0", lifespan=lifespan)
SirenHyperModel.init_app(app)

app.include_router(books_router)
app.include_router(auth_router)


def main() -> None:
    """Start the development server."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
