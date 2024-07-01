from logging import getLogger
from flask_login import login_required
from ..controllers import EventSubsManager, OBSClientsManager, OBSActiveClient
from flask import (
    flash,
    url_for,
    request,
    redirect,
    Blueprint,
    current_app,
    render_template,
)

LOG = getLogger(__name__)

view_events = Blueprint("view_events", __name__)


@view_events.route("/<int:id>", methods=["GET"])
@login_required
def get_root_id(id: int):
    try:
        obs: OBSClientsManager = current_app.obs
        obs_client = obs[id]
        events: EventSubsManager = obs_client.events
        return render_template("events.html", events=events, obs=obs_client)
    except RuntimeError as e:
        msg = f"OBS Client #{id} failed to fetch with reason: {e}"
        LOG.error(msg)
        flash(e, category="danger")
        return redirect(url_for("view_obs.get_root"))


@view_events.route("/<int:id>/scene", methods=["POST"])
@login_required
def post_id_scene(id: int):
    form = request.form
    form_active_scene = form.get("active_scene")
    obs: OBSClientsManager = current_app.obs
    client: OBSActiveClient = obs[id]

    if (
        form_active_scene is not None
        and form_active_scene != OBSActiveClient.DEFAULT_ACTIVE_SCENE
    ):
        client.active_scene = form_active_scene
        msg = f"Set active scene to {form_active_scene} for {client}"
        LOG.debug(msg)
        flash(msg, category="success")
    else:
        flash(
            f"Cannot set OBS Default active scene to: {form_active_scene}",
            category="danger",
        )

    return redirect(url_for("view_events.get_root_id", id=id))


@view_events.route("/<int:id>/add", methods=["GET"])
@login_required
def get_id_add(id: int):
    obs: OBSClientsManager = current_app.obs
    obs_client = obs[id]
    events: EventSubsManager = obs_client.events
    return render_template("events-form.html", events=events, obs=obs_client)


@view_events.route("/<int:id>/add", methods=["POST"])
@login_required
def post_id_add(id: int):
    obs: OBSActiveClient = current_app.obs[id]
    form = request.form

    fomr_src_template = form.get("event_src_template")
    form_type = form.get("event_type")

    form_qt = form.get("event_qt")
    form_allow_anon = form.get("event_allow_anon") is not None

    obs.subscribe_to_event(form)

    msg = f"Created events with form: {form}"
    LOG.debug(msg)
    flash(msg, category="success")
    return redirect(url_for("view_events.get_root_id", id=id))
    # try:
    # except RuntimeError as e:
    #     msg = f"Failed to create event with reason: {e}"
    #     LOG.error(msg)
    #     flash(msg, category="danger")
    #     redirect(url_for("view_events.get_root_id", id=id))
