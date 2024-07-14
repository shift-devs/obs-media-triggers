from logging import getLogger

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..models import EventTypes
from ..controllers import EventSubsManager, OBSActiveClient, OBSClientsManager

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

    if form_active_scene is not None and form_active_scene != OBSActiveClient.DEFAULT_ACTIVE_SCENE:
        client.active_scene = form_active_scene
        msg = f"Set active scene to {form_active_scene} for {client}"
        LOG.debug(msg)
        flash(msg, category="success")
    else:
        flash(
            f"Cannot set OBS Default active scene to: {form_active_scene}",
            category="danger",
        )

    return redirect(url_for("view_events.get_id_add", id=id))


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

    form = form.to_dict()
    form['e_scene_name'] = obs.active_scene

    form_event_type = form['e_type'].replace(' ', '_').upper()
    event_type = EventTypes[form_event_type]
    add_event_handle = {
        EventTypes.CHANNEL_CHAT_MESSAGE: obs.add_twitch_chat_message_event,
        EventTypes.CHANNEL_SUBSCRIPTION_GIFT: obs.add_twitch_gift_sub_event,
    }[event_type]

    add_event_handle(form)
    msg = f"Created a {event_type} event!"
    LOG.debug(msg)
    flash(msg, category="success")
    
    return redirect(url_for("view_events.get_root_id", id=id))
    # try:
    # except RuntimeError as e:
    #     msg = f"Failed to create event with reason: {e}"
    #     LOG.error(msg)
    #     flash(msg, category="danger")
    #     redirect(url_for("view_events.get_root_id", id=id))
