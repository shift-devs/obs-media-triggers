from logging import getLogger
from flask import Blueprint, render_template
from flask_login import login_required, current_user

LOG = getLogger(__name__)

view_twitch = Blueprint("view_twitch", __name__)

@view_twitch.route('/', methods=["GET"])
@login_required
def get_root():
    return render_template('twitch.html', user=current_user)