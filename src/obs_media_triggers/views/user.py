from flask import Blueprint, render_template
from flask_login import login_required, current_user


view_user = Blueprint("view_user", __name__)


@view_user.route("/")
@login_required
def get_root():
    return render_template("users.html", user=current_user)
