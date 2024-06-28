from logging import getLogger

from ..controllers.obs import OBSClientsManager
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template,
)
from flask_login import login_required, current_user
from websocket import WebSocketAddressException

LOG = getLogger(__name__)

view_obs = Blueprint("view_obs", __name__)


@view_obs.route("/", methods=["GET"])
@login_required
def get_root():
    return render_template(
        "obs.html",
    )


@view_obs.route("/add", methods=["GET"])
@login_required
def get_add():
    return render_template(
        "obs-client-form.html",
        new_form="true",
        host="localhost",
        port="4455",
    )


@view_obs.route("/add", methods=["POST"])
@login_required
def post_add():
    d = request.form
    username = current_user.name
    host = d.get("host")
    port = d.get("port")
    password = d.get("password")
    current_app.obs_manager.add_client(username, host, port, password)
    flash(
        f"OBS Client ws://{host}:{port} has been added for {username}!",
        category="success",
    )

    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/edit/<id>", methods=["GET"])
@login_required
def get_edit(id: int):
    obs: OBSClientsManager = current_app.obs_manager
    client = obs.get_client_by_id(id)
    if client is None:
        flash(f"Cannot edit OBS Client #{id}, client not found!", category="danger")
        return redirect(url_for("obs_view.get_root"))
    LOG.debug(f"Found client with ID #{client.id} to edit!")
    return render_template("obs-client-form.html", obs_client=client)


@view_obs.route("/edit/<id>", methods=["POST"])
@login_required
def post_edit(id: int):
    username = current_user.name

    form = request.form
    form_host = form.get("host")
    form_port = form.get("port")
    form_password = form.get("password")

    obs: OBSClientsManager = current_app.obs_manager
    client = obs.get_client_by_id(username, id)

    if client is None:
        flash(f"Cannot edit OBS Client #{id}, client not found!", category="danger")
        return redirect(url_for("obs_view.get_root"))

    LOG.debug(f"Got request to update Client #{client.id}")

    new_values = {}
    if form_host is not None:
        new_values["host"] = form_host
    if form_port is not None:
        new_values["port"] = form_port
    if form_password is not None:
        new_values["password"] = form_password
    obs.update_client(id, new_values)

    flash(
        f"OBS Client #{client.id} has been updated to ws://{client.host}:{client.port}!",
        category="success",
    )
    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/remove/<id>", methods=["POST"])
@login_required
def post_remove(id: int):
    obs: OBSClientsManager = current_app.obs_manager
    obs.delete_client(id)

    if obs.delete_client(id):
        flash(f"OBS Client #{id} has been removed!", category="success")
    else:
        flash(f"OBS Client #{id} was not found!", category="danger")
    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/connect/<id>", methods=["POST"])
@login_required
def post_connect(id: int):
    obs: OBSClientsManager = current_app.obs_manager
    try:
        obs.connect(current_user.name, id)
        flash("Succesfully connected!", category="success")
    except (
        RuntimeError,
        ConnectionRefusedError,
        WebSocketAddressException,
        TimeoutError,
    ) as e:
        LOG.error(e)
        flash(f"Failed to connect: {e}", category="danger")
    finally:
        return redirect(url_for("view_obs.get_root"))


@view_obs.route("/disconnect/<id>", methods=["POST"])
@login_required
def post_disconnect(id: int):
    obs: OBSClientsManager = current_app.obs_manager

    try:
        obs.disconnect_client(id)
        flash(f"Succesfully disconnected from Client #{id}", category="success")
    except RuntimeError as e:
        flash(f"Failed to disconnect from Client #{id}: {e}", category="danger")
    finally:
        return redirect(url_for("view_obs.get_root"))


@view_obs.route("/events", methods=["GET"])
@login_required
def get_events():
    d = request.args

    return render_template(
        "obs-events.html",
        new_form="false",
    )


@view_obs.route("/events/add", methods=["GET"])
@login_required
def get_events_add():
    return render_template(
        "obs-events-form.html",
        new_form="false",
    )


@view_obs.route("/events/add", methods=["POST"])
@login_required
def post_events_add():
    d = request.args
    host = d.get("host")
    port = d.get("port")
    return "Not implemented"
