from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.errors import AuthenticationError, ValidationError

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("tickets.list_tickets"))

    errors: dict[str, str] = {}
    username = ""

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            user = g.services.auth.authenticate(username, password)
        except ValidationError as error:
            errors = error.errors
        except AuthenticationError as error:
            errors = {"_": str(error)}
            current_app.logger.warning(
                "Nieudane logowanie username=%r",
                username.strip()[:50],
            )
        else:
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            current_app.logger.info("Zalogowano user_id=%s", user.id)
            return redirect(url_for("tickets.list_tickets"))

    return render_template("auth/login.html", errors=errors, username=username)


@bp.post("/logout")
def logout():
    if g.user is None:
        return redirect(url_for("auth.login"))
    user_id = g.user.id
    session.clear()
    current_app.logger.info("Wylogowano user_id=%s", user_id)
    flash("Zostałeś wylogowany.", "success")
    return redirect(url_for("auth.login"))
