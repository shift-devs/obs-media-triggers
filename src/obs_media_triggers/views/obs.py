from logging import getLogger
from ..models import DB, OBSWebSocketClient
from ..controllers import OBSClientsManager, OBS_MANAGER
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from websocket import WebSocketAddressException

LOG = getLogger(__name__)

view_obs = Blueprint("view_obs", __name__)


@view_obs.route("/", methods=["GET"])
@login_required
def get_root():

    return render_template("obs.html", user=current_user, obs_manager=OBS_MANAGER)


@view_obs.route("/add", methods=["GET"])
@login_required
def get_add():
    return render_template(
        "obs-client-form.html",
        new_form="true",
        host="localhost",
        port="4455",
        user=current_user,
    )


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
    flash(f"OBS Client ws://{host}:{port} has been added!", category="success")

    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/edit", methods=["GET"])
@login_required
def get_edit():
    d = request.args
    host = d.get("host")
    port = d.get("port")

    return render_template(
        "obs-client-form.html",
        new_form="false",
        host=host,
        port=port,
        user=current_user,
    )


@view_obs.route("/edit", methods=["POST"])
@login_required
def post_edit():
    d = request.form
    original_host = d.get("original_host")
    original_port = d.get("original_port")
    host = d.get("host")
    port = d.get("port")
    password = d.get("password")

    LOG.debug(f'Looking for row in the db matching ws://{original_host}:{original_port}/')
    obs_client: OBSWebSocketClient = OBSWebSocketClient.query.filter_by(
        host=original_host, port=original_port
    ).one_or_none()
    if obs_client is None:
        flash(f"OBS Client ws://{original_host}:{original_port} was not found!", category="danger")
        return redirect(url_for("view_obs.get_root"))

    LOG.debug(f"Got request to update {obs_client}")
    obs_client.host = host
    obs_client.port = port
    if password is not None:
        obs_client.password = password
    DB.session.commit()
    flash(f"OBS Client ws://{original_host}:{original_port} has been updated to ws://{host}:{port}!", category="success")

    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/remove", methods=["POST"])
@login_required
def post_remove():
    d = request.form
    host = d.get("host")
    port = d.get("port")

    obs_client = OBSWebSocketClient.query.filter_by(host=host, port=port).one_or_none()
    if obs_client is None:
        flash(f"OBS Client ws://{host}:{port} was not found!", category="danger")
        return redirect(url_for("view_obs.get_root"))

    LOG.debug(f"Got request to delete {obs_client}")
    DB.session.delete(obs_client)
    DB.session.commit()
    flash(f"OBS Client ws://{host}:{port} has been removed!", category="success")

    return redirect(url_for("view_obs.get_root"))

@view_obs.route("/connect", methods=["POST"])
@login_required
def post_connect():
    d = request.form
    host = d.get("host")
    port = d.get("port")
    url = f'ws://{host}:{port}/'

    obs_client = OBSWebSocketClient.query.filter_by(host=host, port=port).one_or_none()
    if obs_client is None:
        flash(f"Cannot connect to {url} since its config was not found!", category="danger")
        return redirect(url_for("view_obs.get_root"))

    LOG.debug(f"Got request to connect to {url} with password: {obs_client.password}")
    try:
        OBS_MANAGER.connect(obs_client.host, obs_client.port, obs_client.password)
    except (RuntimeError, ConnectionRefusedError, WebSocketAddressException) as e:
        flash(f'Failed to connect to {url}: {e}', category='danger')
        return redirect(url_for("view_obs.get_root"))
    flash(f"Succesfully connected to {url}", category="success")

    return redirect(url_for("view_obs.get_root"))

@view_obs.route("/disconnect", methods=["POST"])
@login_required
def post_disconnect():
    d = request.form
    host = d.get("host")
    port = d.get("port")
    url = f'ws://{host}:{port}/'

    obs_client = OBSWebSocketClient.query.filter_by(host=host, port=port).one_or_none()
    if obs_client is None:
        flash(f"OBS Client {url} was not found!", category="danger")
        return redirect(url_for("view_obs.get_root"))

    LOG.debug(f"Got request to disconnect from {url}")
    try:
        OBS_MANAGER.disconnect(host, port)
        flash(f"Succesfully disconnected from {url}", category="success")
        return redirect(url_for("view_obs.get_root"))
    except RuntimeError as e:
        flash(f'Failed to disconnect from {url}: {e}', category='danger')
        return redirect(url_for("view_obs.get_root"))
    
@view_obs.route("/stream", methods=["GET"])
@login_required
def get_stream():
    d = request.args
    host = d.get("host")
    port = d.get("port")
    obs_client = OBS_MANAGER.find(host, port)

    return render_template(
        "obs-stream.html",
        new_form="false",
        obs_client=obs_client,
        user=current_user,
    )
