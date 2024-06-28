from flask import Blueprint, render_template
from flask_login import login_required

view_home = Blueprint("view_home", __name__)


@view_home.route("/")
@login_required
def get_root():
    return render_template("home.html")
