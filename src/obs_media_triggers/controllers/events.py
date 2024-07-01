from __future__ import annotations

from asyncio import run
from typing import Awaitable, List
from logging import getLogger
from .twitch import TwitchClient
from flask_sqlalchemy import SQLAlchemy
from ..models import EventTypes, EventSubModel

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

    def get_all_event_sub_types(self: EventSubsManager) -> List[str]:
        return [e.name.replace("_", " ").title() for e in EventTypes]

    def get_all_event_subs(
        self: EventSubsManager, id: int = None
    ) -> List[EventSubModel]:
        if id is None:
            return EventSubModel.query.all()
        else:
            return EventSubModel.query.filter_by(id=id).all()

    def add_event_sub(self: EventSubsManager, callback: Awaitable) -> None:
        run(self.twitch.subscribe_to_chat_message_event(callback))
