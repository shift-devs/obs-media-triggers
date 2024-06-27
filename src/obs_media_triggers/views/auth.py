from ..models import DB, User
from logging import getLogger
from password_lib.utils import PasswordUtil
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

LOG = getLogger(__name__)
PSUT = PasswordUtil()
PSUT.configure_strength(
    min_length=9,
    max_length=128,
    requires_lowercase=True,
    requires_uppercase=True,
    requires_special_chars=True,
    requires_digits=True,
)

view_auth = Blueprint("view_auth", __name__)


@view_auth.route("/login", methods=["GET"])
def get_login():
    return render_template("login.html", user=current_user)


@view_auth.route("/login", methods=["POST"])
def post_login():
    d = request.form
    username = d.get("username")
    password = d.get("password")

    account: User = DB.session.query(User).where(User.name == username).one_or_none()
    LOG.debug(f"Matching {username} to db account: {account}")
    if account is not None and check_password_hash(account.password, password):
        flash("Login successful!", category="success")
        login_user(account, remember=True)
        return redirect(url_for("view_home.get_root"))
    else:
        flash("Invalid username or password!", category="danger")
        return redirect(url_for("view_auth.get_login"))


@view_auth.route("/logout", methods=["GET"])
@login_required
def get_logout():
    logout_user()
    return redirect(url_for('view_home.get_root'))


@view_auth.route("/signup", methods=["GET"])
def get_signup():
    return render_template("signup.html", user=current_user)


@view_auth.route("/signup", methods=["POST"])
def post_signup():
    d = request.form
    first_name = d.get('first_name')
    last_name = d.get('last_name')
    username = d.get("username")
    password = d.get("password")
    password_confirm = d.get("password_confirm")
    LOG.info(f"Got sign-up request for {first_name} {last_name} <{username}>")
    username_exists = DB.session.query(User).filter_by(name=username).first() is not None

    if password != password_confirm:
        flash("Passwords do not match!", category="danger")
        return redirect(url_for("view_auth.get_signup"))
    elif username_exists:
        flash("Username already taken!", category="danger")
        return redirect(url_for("view_auth.get_signup"))
    elif not PSUT.is_secure(password):
        flash("Password does not meet the minimim requirements!", category="danger")
        return redirect(url_for("view_auth.get_signup"))

    hash_password = generate_password_hash(password=password)
    new_user = User(name=username, password=hash_password, first_name=first_name, last_name=last_name)
    DB.session.add(new_user)
    DB.session.commit()
    flash("Account has been created!", category="success")
    login_user(new_user, remember=True)
    return redirect(url_for("view_home.get_root"))
