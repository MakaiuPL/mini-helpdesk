from __future__ import annotations

from logging.config import dictConfig
from pathlib import Path

from flask import Flask, g, redirect, render_template, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from app.cli import register_cli
from app.config import Config
from app.db import close_db
from app.errors import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.web.labels import register_template_helpers
from app.web.security import init_request_context

csrf = CSRFProtect()


def _configure_logging(app: Flask) -> None:
    level = app.config["LOG_LEVEL"]
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"
                }
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": level, "handlers": ["stdout"]},
        }
    )
    app.logger.setLevel(level)


def _register_blueprints(app: Flask) -> None:
    from app.web.auth import bp as auth_bp
    from app.web.dashboard import bp as dashboard_bp
    from app.web.tickets import bp as tickets_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(dashboard_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AuthorizationError)
    def handle_authorization(error: AuthorizationError):
        app.logger.warning("Odmowa dostępu: %s", error)
        return render_template("errors/403.html"), 403

    @app.errorhandler(NotFoundError)
    def handle_not_found(error: NotFoundError):
        return render_template("errors/404.html"), 404

    @app.errorhandler(ValidationError)
    def handle_validation(error: ValidationError):
        return (
            render_template("errors/400.html", message=error.message),
            400,
        )

    @app.errorhandler(CSRFError)
    def handle_csrf(error: CSRFError):
        return (
            render_template(
                "errors/400.html",
                message=(
                    "Sesja formularza wygasła lub token jest nieprawidłowy. "
                    "Odśwież stronę i spróbuj ponownie."
                ),
            ),
            400,
        )

    @app.errorhandler(403)
    def handle_403(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def handle_404(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def handle_500(error):
        return render_template("errors/500.html"), 500


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    _configure_logging(app)
    if app.config["SECRET_KEY"] == "dev-only-change-me" and not app.config.get(
        "TESTING"
    ):
        app.logger.warning(
            "Używany jest domyślny SECRET_KEY. Ustaw zmienną SECRET_KEY."
        )

    csrf.init_app(app)
    app.teardown_appcontext(close_db)
    app.before_request(init_request_context)

    _register_blueprints(app)
    _register_error_handlers(app)
    register_template_helpers(app)
    register_cli(app)

    @app.get("/")
    def index():
        if g.user is None:
            return redirect(url_for("auth.login"))
        return redirect(url_for("tickets.list_tickets"))

    return app
