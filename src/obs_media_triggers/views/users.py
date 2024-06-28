from flask import Blueprint, render_template
from flask_login import login_required


view_users = Blueprint("view_users", __name__)


@view_users.route("/")
@login_required
def get_root():
    return render_template("users.html")
