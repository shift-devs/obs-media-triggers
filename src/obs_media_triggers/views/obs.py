from logging import getLogger

from websocket import WebSocketAddressException
from flask_login import login_required, current_user
from ..controllers import OBSClientsManager, TwitchClient
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template,
)

LOG = getLogger(__name__)

view_obs = Blueprint("view_obs", __name__)


@view_obs.route("/", methods=["GET"])
@login_required
def get_root():
    return render_template("obs.html")


@view_obs.route("/add", methods=["GET"])
@login_required
def get_add():
    return render_template(
        "obs-client-form.html", banner="New", host="localhost", port="4455"
    )


@view_obs.route("/add", methods=["POST"])
@login_required
def post_add():
    obs: OBSClientsManager = current_app.obs

    d = request.form
    host = d.get("host")
    port = d.get("port")
    password = d.get("password")
    obs.add_client(host, port, password)
    flash(
        f"OBS Client ws://{host}:{port} has been added!",
        category="success",
    )

    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/edit/<int:id>", methods=["GET"])
@login_required
def get_edit(id: int):
    obs: OBSClientsManager = current_app.obs
    client = obs.get_db_info_by_id(id)
    if client is None:
        flash(f"Cannot edit OBS Client #{id}, client not found!", category="danger")
        return redirect(url_for("obs_view.get_root"))
    LOG.debug(f"Found client with ID #{client.id} to edit!")
    return render_template(
        "obs-client-form.html",
        banner="Update",
        host=client.host,
        port=client.port,
        password=client.password,
    )


@view_obs.route("/edit/<int:id>", methods=["POST"])
@login_required
def post_edit(id: int):
    form = request.form
    form_host = form.get("host")
    form_port = form.get("port")
    form_password = form.get("password")

    obs: OBSClientsManager = current_app.obs
    client = obs.get_db_info_by_id(id)

    if client is None:
        flash(f"Cannot edit OBS Client #{id}, client not found!", category="danger")
        return redirect(url_for("obs_view.get_root"))

    LOG.debug(f"Got request to update Client #{client.id}")

    new_values = {"host": form_host, "port": form_port, "password": form_password}
    obs.update_client(id, new_values)
    flash(
        f"OBS Client #{client.id} has been updated to ws://{client.host}:{client.port}!",
        category="success",
    )
    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/remove/<int:id>", methods=["GET"])
@login_required
def get_remove(id: int):
    obs: OBSClientsManager = current_app.obs

    try:
        obs.delete_client(id)
        flash(f"OBS Client #{id} has been removed!", category="success")
    except RuntimeError as e:
        msg = f"OBS Client #{id} deletion failed with reason: {e}"
        LOG.error(msg)
        flash(msg, category="danger")
    return redirect(url_for("view_obs.get_root"))


@view_obs.route("/connect/<int:id>", methods=["GET"])
@login_required
def get_connect(id: int):
    obs: OBSClientsManager = current_app.obs
    LOG.debug(f"Attempting connection to OBS Client #{id}")
    try:
        obs.connect_client(id)
        msg = f"OBS Client #{id} succesfully connected!"
        LOG.info(msg)
        flash(id, category="success")
    except (
        RuntimeError,
        ConnectionRefusedError,
        WebSocketAddressException,
        TimeoutError,
    ) as e:
        msg = f"OBS Client #{id} connection faild: {e}"
        LOG.error(msg)
        flash(msg, category="danger")
    finally:
        return redirect(url_for("view_obs.get_root"))


@view_obs.route("/disconnect/<int:id>", methods=["GET"])
@login_required
def get_disconnect(id: int):
    obs: OBSClientsManager = current_app.obs

    obs.disconnect_client(id)
    try:
        flash(f"OBS Client #{id} succesfully disconnected!", category="success")
    except RuntimeError as e:
        flash(f"OBS Client #{id} disconnection failed: {e}", category="danger")
    finally:
        return redirect(url_for("view_obs.get_root"))


@view_obs.route("/events/<int:id>", methods=["GET"])
@login_required
def get_events(id: int):
    try:
        obs: OBSClientsManager = current_app.obs
        twitch: TwitchClient = current_app.twitch
        if not twitch.is_logged_in():
            flash("Must log into Twitch before editing events!", category="danger")
            return redirect(url_for("view_obs.get_root"))

        client = obs[id]
        return render_template("obs-events.html", obs_client=client)
    except RuntimeError as e:
        msg = f"OBS Client #{id} failed to fetch with reason: {e}"
        LOG.error(msg)
        flash(e, category="danger")
        return redirect(url_for("view_obs.get_root"))


@view_obs.route("/events/<int:id>/scene", methods=["POST"])
@login_required
def post_active_scene(id: int):
    form = request.form
    form_active_scene = form.get("active_scene")
    obs: OBSClientsManager = current_app.obs
    client = obs[id]
    client.active_scene = form_active_scene
    LOG.debug(f'Setting active scene to {form_active_scene} for {client}')

    return redirect(url_for("view_obs.get_events", id=id))


@view_obs.route("/events/<int:id>/add", methods=["GET"])
@login_required
def get_events_add(id: int):
    obs: OBSClientsManager = current_app.obs
    client = obs[id]
    return render_template("obs-events-form.html", obs_client=client)


@view_obs.route("/events/<int:id>/add", methods=["POST"])
@login_required
def post_events_add(id: int):
    obs: OBSClientsManager = current_app.obs
    client = obs[id]
    form = request.form

    form_type = form.get("event_type")
    form_qt = form.get("event_qt")
    form_allow_anon = form.get("event_allow_anon") is not None
    fomr_src_template = form.get('event_src_template')

    client.add_event(id, form_type, form_qt, form_allow_anon, src_template=fomr_src_template)

    LOG.debug(f"Got new event type")

    return "Not implemented"
