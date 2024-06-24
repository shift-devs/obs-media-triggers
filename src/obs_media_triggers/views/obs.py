from ..models import DB, OBSWebSocketClient
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

view_obs = Blueprint("view_obs", __name__)


@view_obs.route("/", methods=["GET"])
@login_required
def get_root():
    return render_template("obs.html", user=current_user)


@view_obs.route("/add", methods=["GET"])
@login_required
def get_add():
    return render_template("obs-add.html", user=current_user)


@view_obs.route("/add", methods=["POST"])
@login_required
def post_add():
    d = request.form
    host = d.get("host")
    port = d.get("port")
    password = d.get("password")

    obs_client = OBSWebSocketClient(host=host, port=port, password=password)
    DB.session.add(obs_client)
    DB.session.commit()
    flash("New OBS Client has been added!", category="success")

    return redirect(url_for("view_obs.get_root"))
