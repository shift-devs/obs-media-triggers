from logging import getLogger
from flask_login import login_required, current_user
from flask import Blueprint, render_template, current_app

LOG = getLogger(__name__)

view_twitch = Blueprint("view_twitch", __name__)


@view_twitch.route("/", methods=["GET"])
@login_required
def get_root():
    return render_template(
        "twitch.html",
        user=current_user,
    )


@view_twitch.route("/", methods=["POST"])
@login_required
def get_add():
    current_app.twitch_manager.connect()
    return "Auth Here"
