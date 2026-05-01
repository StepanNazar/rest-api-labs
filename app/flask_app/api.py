from uuid import UUID

from flask import g, request
from flask_apispec import use_kwargs, marshal_with, MethodResource
from flask_restful import abort
from marshmallow import fields
from pydantic import ValidationError

from api.books import decode_cursor, encode_cursor
from app.flask_app.schemas import (
    BookResponseSchema,
    BookCollectionResponseSchema,
    BookQueryArgsSchema,
    BookCreateSchema,
)
from app.dtos.books import Book
from app.services.exceptions import BookNotFoundError
from app.flask_app.async_bridge import bridge


class BookListResource(MethodResource):
    @use_kwargs(BookQueryArgsSchema, location="query")
    @marshal_with(BookCollectionResponseSchema)
    def get(self, **kwargs):
        service = g.book_service

        limit = kwargs["limit"]
        offset = kwargs["offset"]
        cursor = kwargs["cursor"]
        status = kwargs["status"]
        author = kwargs["author"]
        sort_by = kwargs["sort_by"]
        order = kwargs["order"]

        decoded_cursor = None
        if cursor is not None:
            try:
                decoded_cursor = decode_cursor(cursor)
            except Exception:
                abort(422, message="Invalid cursor value")

        result = bridge.run(
            service.get_books(
                filter_status=status,
                filter_author=author,
                sort_by=sort_by,
                order=order,
                limit=limit,
                offset=offset,
                cursor=decoded_cursor,
            )
        )

        next_cursor = None
        if offset is None:
            items, total, next_cursor_obj = result
            next_cursor = encode_cursor(next_cursor_obj)
        else:
            items, total = result

        response_properties = {
            "items": [{"properties": item.model_dump()} for item in items],
            "limit": limit,
            "offset": offset,
            "total": total,
            "count": len(items),
            "next_offset": None,
            "prev_offset": None,
            "next_cursor": next_cursor,
        }

        from urllib.parse import urlencode

        params = dict(request.args)
        next_params = None
        prev_params = None

        if offset is not None:
            next_offset = offset + limit
            if next_offset < total:
                response_properties["next_offset"] = next_offset
                next_params = params.copy()
                next_params["offset"] = str(next_offset)
            if offset > 0:
                prev_offset = max(offset - limit, 0)
                response_properties["prev_offset"] = prev_offset
                prev_params = params.copy()
                prev_params["offset"] = str(prev_offset)
        elif next_cursor:
            next_params = params.copy()
            next_params["cursor"] = next_cursor

        base_url = request.url.split("?")[0]
        links = [
            {
                "rel": ["self"],
                "href": f"{base_url}?{urlencode(params, doseq=True)}"
                if params
                else base_url,
            }
        ]
        if next_params is not None:
            links.append(
                {
                    "rel": ["next"],
                    "href": f"{base_url}?{urlencode(next_params, doseq=True)}",
                }
            )
        if prev_params is not None:
            links.append(
                {
                    "rel": ["prev"],
                    "href": f"{base_url}?{urlencode(prev_params, doseq=True)}",
                }
            )

        return {"properties": response_properties, "links": links}

    @use_kwargs(BookCreateSchema)
    @marshal_with(BookResponseSchema, code=201)
    def post(self, **kwargs):
        service = g.book_service
        try:
            dto = Book(**kwargs)
            book = bridge.run(service.create_book(dto))
            return {"properties": book.model_dump()}, 201
        except ValidationError:
            abort(422, message="Validation error")


class BookResource(MethodResource):
    @use_kwargs({"book_id": fields.UUID()}, location="view_args")
    @marshal_with(BookResponseSchema)
    def get(self, book_id, **kwargs):
        service = g.book_service
        try:
            book = bridge.run(service.get_book(book_id))
            return {"properties": book.model_dump()}
        except BookNotFoundError as exc:
            abort(404, message=str(exc))

    @use_kwargs({"book_id": fields.UUID()}, location="view_args")
    def delete(self, book_id, **kwargs):
        service = g.book_service
        bridge.run(service.delete_book(book_id))
        return "", 204
