from asyncio import run
from logging import getLogger
from flask_login import login_required
from flask import Blueprint, current_app, request, redirect, url_for, flash

LOG = getLogger(__name__)

view_twitch = Blueprint("view_twitch", __name__)


@view_twitch.route("/", methods=["GET"])
@login_required
def get_root():
    return redirect(current_app.twitch_manager.start_auth())


@view_twitch.route("/login", methods=["GET"])
@login_required
def get_login():
    twitch = current_app.twitch_manager
    auth = twitch.auth

    args = request.args
    state = args.get("state")
    user_token = args.get("code")

    if state != auth.state:
        return {"err": "Bad state!"}, 401

    if user_token is None:
        return {"err": "Missing token!"}, 400

    LOG.info(f"Got {state} request with user token: {user_token}")
    if run(twitch.login(user_token)):
        flash(f"Logged into Twitch as {run(twitch.user_name)}", category='success')
    else:
        flash("Failed to log into twitch!", category="danger")
    return redirect(url_for("view_home.get_root"))
