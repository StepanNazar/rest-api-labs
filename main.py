"""FastAPI application entry point for the Library API."""

import uvicorn
from fastapi import FastAPI
from fastapi_hypermodel import SirenHyperModel

from api.books import router as books_router

app = FastAPI(title="Library API", version="0.1.0")
SirenHyperModel.init_app(app)

app.include_router(books_router)


def main() -> None:
    """Start the development server."""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
