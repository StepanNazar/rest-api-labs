from marshmallow import Schema, fields, post_dump, validate

from app.dtos.books import BookStatus, SortField, SortOrder

__all__ = ["BookCreateSchema", "BookResponseSchema", "BookCollectionResponseSchema", "BookQueryArgsSchema"]


class BookQueryArgsSchema(Schema):
    """Schema for validating book collection query parameters."""

    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))
    offset = fields.Integer(load_default=None, validate=validate.Range(min=0))
    cursor = fields.String(load_default=None)
    status = fields.Enum(BookStatus, load_default=None, by_value=True)
    author = fields.String(load_default=None)
    sort_by = fields.Enum(SortField, load_default=None, by_value=True)
    order = fields.Enum(SortOrder, load_default=SortOrder.ASC, by_value=True)


class BookCreateSchema(Schema):
    """Schema for creating a new book."""

    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=300),
    )
    author = fields.String(
        required=True,
        validate=validate.Length(min=1, max=200),
    )
    description = fields.String(
        load_default="",
        dump_default="",
        validate=validate.Length(min=0, max=2000),
    )
    status = fields.Enum(BookStatus, required=True, by_value=True)
    publication_year = fields.Integer(required=True)


class BookPropertiesSchema(Schema):
    """Schema for the properties of a book."""

    id = fields.UUID(required=True)
    title = fields.String(required=True)
    author = fields.String(required=True)
    description = fields.String(required=True)
    status = fields.Enum(BookStatus, required=True, by_value=True)
    publication_year = fields.Integer(required=True)


class BookResponseSchema(Schema):
    """Schema for returning book data in API responses."""

    properties = fields.Nested(BookPropertiesSchema, required=True)

    links = fields.List(fields.Dict(), dump_only=True)
    actions = fields.List(fields.Dict(), dump_only=True)

    @post_dump
    def add_siren_fields(self, data: dict, **kwargs) -> dict:
        book_id = str(data["properties"]["id"])

        data["links"] = [
            {
                "rel": ["self"],
                "href": f"/books/{book_id}",
            }
        ]

        data["actions"] = [
            {
                "name": "delete",
                "method": "DELETE",
                "href": f"/books/{book_id}",
            }
        ]

        return data

class BookCollectionPropertiesSchema(Schema):
    """Schema for the properties of a book collection response, including pagination metadata."""

    items = fields.List(fields.Nested(BookResponseSchema), required=True)

    limit = fields.Integer(required=True)
    offset = fields.Integer(allow_none=True, required=True)
    total = fields.Integer(required=True)
    count = fields.Integer(required=True)

    next_offset = fields.Integer(allow_none=True, required=True)
    prev_offset = fields.Integer(allow_none=True, required=True)
    next_cursor = fields.String(allow_none=True, required=True)


class BookCollectionResponseSchema(Schema):
    """Schema for returning a collection of books with pagination metadata."""

    properties = fields.Nested(BookCollectionPropertiesSchema, required=True)

    links = fields.List(fields.Dict())
    actions = fields.List(fields.Dict())

    @post_dump
    def add_siren_fields(self, data: dict, **kwargs) -> dict:
        props = data.get("properties", {})
        if "items" in props and not props["items"]:
            del props["items"]

        if not data.get("links"):
            links = [
                {
                    "rel": ["self"],
                    "href": "/books",
                }
            ]

            has_next_offset = (
                props.get("offset") is not None
                and props["offset"] + props["limit"] < props["total"]
            )
            has_next_cursor = props.get("next_cursor") is not None

            if has_next_offset or has_next_cursor:
                links.append(
                    {
                        "rel": ["next"],
                        "href": "/books",
                    }
                )

            if props.get("offset") is not None and props["offset"] > 0:
                links.append(
                    {
                        "rel": ["prev"],
                        "href": "/books",
                    }
                )

            data["links"] = links

        data["actions"] = [
            {
                "name": "find",
                "method": "GET",
                "href": "/books/{book_id}",
                "templated": True,
            },
            {
                "name": "delete",
                "method": "DELETE",
                "href": "/books/{book_id}",
                "templated": True,
            },
            {
                "name": "create",
                "method": "POST",
                "href": "/books",
                "type": "application/json",
                "fields": [
                    {"name": "title", "type": "text", "value": "None"},
                    {"name": "author", "type": "text", "value": "None"},
                    {"name": "description", "type": "text"},
                    {"name": "status", "type": "text", "value": "None"},
                    {"name": "publication_year", "type": "number", "value": "None"},
                ],
            },
        ]

        return data