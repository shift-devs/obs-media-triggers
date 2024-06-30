from asyncio import run
from logging import getLogger
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template,
)
from ..controllers import TwitchClient
from flask_sqlalchemy import SQLAlchemy
from twitchAPI.twitch import TwitchUser
from ..models import TwitchOAuthUserModel
from sqlalchemy.exc import IntegrityError
from twitchAPI.oauth import UserAuthenticator
from flask_login import login_user, logout_user, login_required

LOG = getLogger(__name__)

view_twitch = Blueprint("view_twitch", __name__)


@view_twitch.route("/", methods=["GET"])
def get_root():
    return render_template("twitch-login.html")


@view_twitch.route("/login/redirect", methods=["GET"])
def get_login_redirect():
    return redirect(current_app.twitch.get_user_auth_url())


@view_twitch.route("/login", methods=["GET"])
def get_login():
    db: SQLAlchemy = current_app.db
    twitch: TwitchClient = current_app.twitch
    auth: UserAuthenticator = twitch.auth

    args = request.args
    state = args.get("state")
    user_token = args.get("code")

    if state != auth.state:
        return {"err": "Bad state!"}, 401
    if user_token is None:
        return {"err": "Missing token!"}, 400

    try:
        db_user: TwitchOAuthUserModel = twitch.login(user_token)
        msg = f"Logged into Twitch as {db_user.display_name}"
        LOG.debug(msg)
        flash(msg, category="success")
        return redirect(url_for("view_obs.get_root"))
    except (RuntimeError, AttributeError) as e:
        msg = f"Failed to log into twitch with reason: {e}"
        LOG.error(msg)
        flash(msg, category="danger")
        return redirect(url_for("view_twitch.get_root"))


@view_twitch.route("/logout", methods=["GET"])
@login_required
def get_logout():
    current_app.twitch.logout()
    return redirect(url_for("view_twitch.get_root"))
