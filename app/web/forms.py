from __future__ import annotations

from flask import current_app

from app.models.enums import Channel, Priority, Status
from app.models.ticket import TicketFilter, TicketInput


def _enum_or_none(enum_type, value: str):
    if not value:
        return None
    try:
        return enum_type(value)
    except ValueError:
        return None


def parse_ticket_filter(args) -> TicketFilter:
    page = args.get("page", type=int) or 1
    return TicketFilter(
        status=_enum_or_none(Status, args.get("status", "")),
        priority=_enum_or_none(Priority, args.get("priority", "")),
        channel=_enum_or_none(Channel, args.get("channel", "")),
        query=(args.get("q") or "").strip()[:100],
        page=max(page, 1),
        per_page=current_app.config["TICKETS_PER_PAGE"],
    )


def parse_ticket_input(form) -> TicketInput:
    return TicketInput(
        title=form.get("title", ""),
        description=form.get("description", ""),
        priority=form.get("priority", ""),
        channel=form.get("channel", ""),
    )


def default_ticket_input() -> TicketInput:
    return TicketInput(
        title="",
        description="",
        priority=Priority.MEDIUM.value,
        channel=Channel.FORM.value,
    )
