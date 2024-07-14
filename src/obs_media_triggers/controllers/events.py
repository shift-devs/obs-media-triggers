from __future__ import annotations

from asyncio import run
from logging import getLogger
from typing import Awaitable, List
from functools import partial
from flask_sqlalchemy import SQLAlchemy

from ..models import EventSubModel, EventTypes
from .twitch import TwitchClient

LOG = getLogger(__name__)


class EventSubsManager:
    db: SQLAlchemy
    twitch: TwitchClient

    def __init__(
        self: EventSubsManager,
        db: SQLAlchemy,
        twitch: TwitchClient,
    ) -> None:
        self.db = db
        self.twitch = twitch

    def get_all_event_types(self: EventSubsManager) -> List[str]:
        return [e.name.replace("_", " ").title() for e in EventTypes]

    def get_all_events(self: EventSubsManager, obs_id: int = None) -> List[EventSubModel]:
        events = (
            EventSubModel.query.all()
            if obs_id is None
            else EventSubModel.query.filter_by(id=obs_id).all()
        )
        LOG.debug("Found %s events!", len(events))
        return events

    def get_events_by_type(self: EventSubsManager, e_type: EventTypes) -> [EventSubModel]:
        if(not self.db.session.is_active):
            import ipdb; ipdb.set_trace()
        return EventSubModel.query.filter_by(type=e_type).all()


    def twitch_add_chat_message_event(
        self: EventSubsManager,
        obs_id: int,
        scene_name: str,
        source_name: str,
        form_fields: dict,
        callback: Awaitable,
    ) -> None:
        return self.add_event(
            obs_id=obs_id,
            scene_name=scene_name,
            source_name=source_name,
            event_type=EventTypes.CHANNEL_CHAT_MESSAGE,
            form_fields=form_fields,
            twitch_handle=self.twitch.subscribe_to_chat_message,
            callback=callback,
        )

    def twitch_add_gift_sub_event(
        self: EventSubsManager,
        obs_id: int,
        scene_name: str,
        source_name: str,
        form_fields: dict,
        callback: Awaitable,
    ) -> None:
        return self.add_event(
            obs_id=obs_id,
            scene_name=scene_name,
            source_name=source_name,
            event_type=EventTypes.CHANNEL_SUBSCRIPTION_GIFT,
            form_fields=form_fields,
            twitch_handle=self.twitch.subscribe_to_gift_subscription,
            callback=callback,
        )

    def add_event(
        self: EventSubsManager,
        obs_id: int,
        scene_name: str,
        source_name: str,
        event_type: EventTypes,
        form_fields: dict,
        twitch_handle: Awaitable,
        callback: Awaitable,
    ) -> None:
        new_event = EventSubModel(
            obs_id=obs_id,
            scene_name=scene_name,
            source_name=source_name,
            type=event_type,
            fields=form_fields,
        )
        self.db.session.add(new_event)
        self.db.session.commit()
        LOG.debug(f'Added new event in DB: {new_event}')
        return run(twitch_handle(callback))