from flask import Flask, g
from flask_restful import Api
from flask_apispec.extension import FlaskApiSpec
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

from app.database import mongo_db
from app.repository.book_repository import MongoBookRepository
from app.services.book_service import BookService
from app.flask_app.api import BookListResource, BookResource

def create_app(service=None):
    app = Flask(__name__)
    
    if service is None:
        repo = MongoBookRepository(mongo_db)
        service = BookService(repo)
    
    app.config.update({
        'APISPEC_SPEC': APISpec(
            title='Library API',
            version='v1',
            plugins=[MarshmallowPlugin()],
            openapi_version="2.0"
        ),
        'APISPEC_SWAGGER_URL': '/swagger/',
        'APISPEC_SWAGGER_UI_URL': '/docs/'
    })
    
    api = Api(app)

    @app.before_request
    def inject_service():
        if service:
            g.book_service = service

    api.add_resource(BookListResource, "/books/")
    api.add_resource(BookResource, "/books/<string:book_id>")

    docs = FlaskApiSpec(app)
    docs.register(BookListResource)
    docs.register(BookResource)

    return app

if __name__ == "__main__":
    create_app().run(debug=True)