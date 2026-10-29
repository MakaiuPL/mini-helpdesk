from __future__ import annotations

from datetime import UTC, datetime

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from app.errors import ConflictError, ValidationError
from app.models.enums import Channel, Priority, Role, Status
from app.services.ticket_service import allowed_transitions
from app.web.forms import (
    default_ticket_input,
    parse_ticket_filter,
    parse_ticket_input,
)
from app.web.security import login_required, role_required

bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@bp.get("")
@login_required
def list_tickets():
    filters = parse_ticket_filter(request.args)
    page = g.services.tickets.list(g.user, filters)
    return render_template(
        "tickets/list.html",
        page=page,
        filters=filters,
        statuses=list(Status),
        priorities=list(Priority),
        channels=list(Channel),
    )


@bp.get("/new")
@role_required(Role.USER)
def new_ticket():
    return render_template(
        "tickets/new.html",
        form=default_ticket_input(),
        errors={},
        priorities=list(Priority),
        channels=list(Channel),
    )


@bp.post("")
@role_required(Role.USER)
def create_ticket():
    data = parse_ticket_input(request.form)
    try:
        ticket = g.services.tickets.create(g.user, data)
    except ValidationError as error:
        return (
            render_template(
                "tickets/new.html",
                form=data,
                errors=error.errors,
                priorities=list(Priority),
                channels=list(Channel),
            ),
            400,
        )

    flash("Zgłoszenie zostało utworzone.", "success")
    return redirect(url_for("tickets.detail", ticket_id=ticket.id))


@bp.get("/<int:ticket_id>")
@login_required
def detail(ticket_id: int):
    details = g.services.tickets.get_details(g.user, ticket_id)
    return render_template(
        "tickets/detail.html",
        details=details,
        next_statuses=allowed_transitions(details.ticket.status),
    )


@bp.post("/<int:ticket_id>/status")
@role_required(Role.TECHNICIAN)
def change_status(ticket_id: int):
    try:
        g.services.tickets.change_status(
            g.user,
            ticket_id,
            request.form.get("status", ""),
        )
    except ConflictError as error:
        flash(str(error), "error")
    except ValidationError as error:
        flash(error.message, "error")
    else:
        flash("Status został zmieniony.", "success")
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))


@bp.post("/<int:ticket_id>/assign")
@role_required(Role.TECHNICIAN)
def assign_to_self(ticket_id: int):
    try:
        g.services.tickets.assign_to_self(g.user, ticket_id)
    except ConflictError as error:
        flash(str(error), "error")
    else:
        flash("Zgłoszenie zostało przypisane do Ciebie.", "success")
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))


@bp.post("/<int:ticket_id>/comments")
@role_required(Role.TECHNICIAN)
def add_comment(ticket_id: int):
    try:
        g.services.comments.add(
            g.user,
            ticket_id,
            request.form.get("body", ""),
        )
    except ValidationError as error:
        flash(error.message, "error")
    else:
        flash("Komentarz został dodany.", "success")
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))


@bp.get("/export.csv")
@role_required(Role.TECHNICIAN)
def export_csv():
    filters = parse_ticket_filter(request.args)
    content = g.services.export.export_csv(g.user, filters)
    filename = f"zgloszenia-{datetime.now(UTC):%Y%m%d-%H%M}.csv"
    return Response(
        content,
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
