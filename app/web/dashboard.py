from __future__ import annotations

from flask import Blueprint, g, render_template

from app.models.enums import Priority, Role, Status
from app.web.security import role_required

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@role_required(Role.TECHNICIAN)
def index():
    stats = g.services.dashboard.stats(g.user)
    return render_template(
        "dashboard/index.html",
        stats=stats,
        statuses=list(Status),
        priorities=list(Priority),
    )
