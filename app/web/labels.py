from __future__ import annotations

from flask import Flask, request, url_for

from app.labels import (
    channel_label,
    format_datetime,
    format_hours,
    priority_label,
    role_label,
    status_label,
)


def _page_url(page: int) -> str:
    args = request.args.to_dict(flat=True)
    args["page"] = page
    return url_for("tickets.list_tickets", **args)


def _export_url() -> str:
    args = request.args.to_dict(flat=True)
    args.pop("page", None)
    return url_for("tickets.export_csv", **args)


def register_template_helpers(app: Flask) -> None:
    app.jinja_env.filters["status_label"] = status_label
    app.jinja_env.filters["priority_label"] = priority_label
    app.jinja_env.filters["channel_label"] = channel_label
    app.jinja_env.filters["role_label"] = role_label
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["format_hours"] = format_hours
    app.jinja_env.globals["page_url"] = _page_url
    app.jinja_env.globals["export_url"] = _export_url
