from flask import Blueprint, render_template
from flask_login import login_required, current_user

views = Blueprint("views", __name__)


@views.route("/")
@login_required
def root():
    return render_template("root.html", user=current_user)


@views.route("/users")
@login_required
def users():
    return render_template("users.html", user=current_user)
