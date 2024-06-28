from asyncio import run
from logging import getLogger
from ..controllers import UserManager
from flask_login import login_required
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template,
)

LOG = getLogger(__name__)


view_auth = Blueprint("view_auth", __name__)


@view_auth.route("/login", methods=["GET"])
def get_login():
    return render_template("login.html")


@view_auth.route("/login", methods=["POST"])
def post_login():
    users: UserManager = current_app.user_manager

    form = request.form
    form_username = form.get("username")
    form_password = form.get("password")
    form_remeber_me = form.get("remember_me") is not None

    try:
        users.login(form_username, form_password, remeber_user=form_remeber_me)
        flash("Login successful!", category="success")
        return redirect(url_for("view_home.get_root"))
    except RuntimeError as e:
        LOG.error(f"Login attempt for {form_username} failed with reason: {e}")
        flash("Invalid username or password!", category="danger")
        return redirect(url_for("view_auth.get_login"))


@view_auth.route("/logout", methods=["GET"])
@login_required
def get_logout():
    run(current_app.twitch_manager.logout())
    current_app.user_manager.logout()
    return redirect(url_for("view_home.get_root"))


@view_auth.route("/signup", methods=["GET"])
def get_signup():
    users: UserManager = current_app.user_manager
    return render_template("signup.html", policy=users.password_policy)


@view_auth.route("/signup", methods=["POST"])
def post_signup():
    users: UserManager = current_app.user_manager

    form = request.form
    form_username = form.get("username")
    form_password = form.get("password")
    form_password_confirm = form.get("password_confirm")

    try:
        users.signup(form_username, form_password, form_password_confirm)
        LOG.info(f"Account {form_username} has been created!")
        flash("Account has been created!", category="success")
        return redirect(url_for("view_home.get_root"))
    except RuntimeError as e:
        LOG.error(
            f"Signup for requested username {form_username} failed with reason: {e}"
        )
        flash(f"Sign-up failed: {e}", category="danger")
        return redirect(url_for("view_auth.get_signup"))
