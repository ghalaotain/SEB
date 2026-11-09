import os

from flask import Flask, jsonify

from . import models  # noqa: F401
from .commands import register_commands
from .config import CONFIGS
from .extensions import (
    csrf,
    db,
    limiter,
    login_manager,
    migrate,
)
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    environment = os.getenv(
        "FLASK_ENV",
        "development",
    ).strip().lower()

    config_class = CONFIGS.get(
        environment,
        CONFIGS["development"],
    )

    app.config.from_object(config_class)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        config_class.database_uri()
    )

    if environment == "production":
        config_class.validate()

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is missing. Add it to .env."
        )

    os.makedirs(
        app.instance_path,
        exist_ok=True,
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": (
                        "The requested resource "
                        "was not found."
                    ),
                },
            }
        ), 404

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": (
                        "The uploaded file is too large."
                    ),
                },
            }
        ), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        "Too many requests. "
                        "Please wait and try again."
                    ),
                },
            }
        ), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": (
                        "INTERNAL_SERVER_ERROR"
                    ),
                    "message": (
                        "An unexpected server "
                        "error occurred."
                    ),
                },
            }
        ), 500