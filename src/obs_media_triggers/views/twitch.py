from logging import getLogger

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required
from twitchAPI.oauth import UserAuthenticator

from ..controllers import TwitchClient
from ..models import TwitchOAuthUserModel

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
