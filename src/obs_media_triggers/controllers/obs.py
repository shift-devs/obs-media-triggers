from __future__ import annotations

from logging import getLogger
from time import sleep
from typing import Union

from flask_sqlalchemy import SQLAlchemy
from obsws_python import ReqClient
from obsws_python.error import OBSSDKError
from twitchAPI.object.eventsub import (
    ChannelChatMessageData,
    ChannelChatMessageEvent,
    ChannelSubscriptionGiftData,
    ChannelSubscriptionGiftEvent,
)

from functools import partial
from ..models import OBSWSClientModel, EventTypes, EventSubModel
from .events import EventSubsManager
from .twitch import TwitchClient

LOG = getLogger(__name__)


class OBSActiveClient(ReqClient):
    DEFAULT_ACTIVE_SCENE = "NO_ACTIVE_SCENE"

    db: SQLAlchemy
    db_info: OBSWSClientModel
    obs_id: int
    host: str
    port: int
    password: str
    active_scene: str
    events: EventSubsManager

    def __init__(
        self: OBSActiveClient,
        db: SQLAlchemy,
        db_info: OBSWSClientModel,
        twitch: TwitchClient,
        timeout: int = 1,
    ):
        super().__init__(
            host=db_info.host,
            port=db_info.port,
            password=db_info.password,
            timeout=timeout,
        )
        self.db = db
        self.id = db_info.id
        self.host = db_info.host
        self.port = db_info.port
        self.password = db_info.password
        self.active_scene = OBSActiveClient.DEFAULT_ACTIVE_SCENE
        self.events = EventSubsManager(db, twitch)

    def __eq__(self: OBSActiveClient, other_id: int) -> bool:
        return self.id == other_id

    def is_active_scene(self: OBSActiveClient, scene_name: str = None) -> bool:
        scene_name = OBSActiveClient.DEFAULT_ACTIVE_SCENE if scene_name is None else scene_name
        return self.active_scene.lower() == scene_name.lower()

    def get_all_sources(self: OBSActiveClient, scene_name: str = None):
        scene_name = self.active_scene if scene_name is None else scene_name

        if scene_name == OBSActiveClient.DEFAULT_ACTIVE_SCENE:
            LOG.debug("No active scene has been set! Skipping DB query!")
            return []
        LOG.debug("Looking for sources in active scene: %s", scene_name)
        items = self.get_scene_item_list(scene_name).scene_items
        return list(map(lambda x: x["sourceName"], items))

    def duplicate_source(self: OBSActiveClient, scene_name: str, source_name: str) -> object:
        source_id = self.get_scene_item_id(
            scene_name=scene_name, source_name=source_name
        ).scene_item_id
        return self.duplicate_scene_item(
            scene_name=scene_name,
            item_id=source_id,
            dest_scene_name=scene_name,
        )

    def show_duplicate_source(
        self: OBSActiveClient, scene_name: str, source_name: str, duration: int
    ) -> None:
        dupe_id = self.duplicate_source(scene_name=scene_name, source_name=source_name)
        self.set_scene_item_enabled(scene_name=scene_name, item_id=dupe_id, enabled=True)
        sleep(duration)
        self.set_scene_item_enabled(scene_name=scene_name, item_id=dupe_id, enabled=False)
        self.remove_scene_item(scene_name=scene_name, item_id=dupe_id)

    def add_twitch_chat_message_event(self: OBSActiveClient, form_fields: dict) -> None:
        LOG.debug("Subscribing to event with payload: %s", form_fields)
        scene_name = form_fields["e_scene_name"]
        source_name = form_fields["e_source_name"]
        self.events.twitch_add_chat_message_event(
            obs_id=self.id,
            scene_name=scene_name,
            source_name=source_name,
            form_fields=form_fields,
            callback=self.handle_chat_message,
        )

    def add_twitch_gift_sub_event(self: OBSActiveClient, form_fields: dict) -> None:
        LOG.debug("Subscribing to event with payload: %s", form_fields)
        scene_name = form_fields["e_scene_name"]
        source_name = form_fields["e_source_name"]
        self.events.twitch_add_gift_sub_event(
            obs_id=self.id,
            scene_name=scene_name,
            source_name=source_name,
            form_fields=form_fields,
            callback=self.handle_chat_message,
        )

    @staticmethod
    def __req_fields_are_present(fields: list[str], fields_dict: dict) -> bool:
        for name in fields:
            try:
                assert fields_dict.get(name) is not None
            except AssertionError as e:
                LOG.error("Expected %s in %s but was not found!", name, fields_dict)
                return False
        return True

    async def handle_gift_subscription(self: OBSActiveClient, event: ChannelSubscriptionGiftEvent):
        gift: ChannelSubscriptionGiftData = event.event
        conditions: List[EventSubModel] = self.events.get_events_by_type(
            EventTypes.CHANNEL_SUBSCRIPTION_GIFT
        )
        LOG.debug("Checking %s conditions for %sx Gift-Sub event!", len(conditions), gift.total)
        for cnd in conditions:
            cnd: EventSubModel

            if not OBSActiveClient.__req_fields_are_present(
                ["e_quantity", "e_allow_anon", cnd.fields]
            ):
                continue

            req_sub_quantity = int(cnd.fields["e_quantity"])
            allow_anon = bool(cnd.fields["e_allow_anon"])

            condition_is_met = not (not allow_anon and gift.is_anonymous()) and (
                gift.total >= req_sub_quantity
            )

            if condition_is_met:
                self.show_duplicate_source(
                    scene_name=cnd.scene_name, source_name=cnd.source_name, duration=4
                )

    async def handle_chat_message(self: OBSActiveClient, event: ChannelChatMessageEvent):
        chat: ChannelChatMessageData = event.event
        conditions: List[EventSubModel] = self.events.get_events_by_type(
            EventTypes.CHANNEL_SUBSCRIPTION_GIFT
        )
        LOG.debug(
            "Checking %s conditions for Chat-Message event from %s!",
            len(conditions),
            chat.chatter_user_name,
        )
        for cnd in conditions:
            cnd: EventSubModel
            if not OBSActiveClient.__req_fields_are_present(["e_msg_contains", cnd.fields]):
                continue
            msg_contains = cnd.fields["e_msg_contains"]
            condition_is_met = ()
            if condition_is_met:
                self.show_duplicate_source(
                    scene_name=scene_name, source_name=source_name, duration=4
                )


class OBSClientsManager:
    active_clients: list[OBSActiveClient]
    db: SQLAlchemy
    twitch: TwitchClient

    def __init__(self: OBSClientsManager, db: SQLAlchemy, twitch: TwitchClient):
        self.active_clients = []
        self.db = db
        self.twitch = twitch

    def __validate_permission(self: OBSClientsManager, db_info: OBSWSClientModel) -> None:
        LOG.debug("Validating request for db entry: %s", db_info)
        return True

    def __getitem__(self: OBSClientsManager, uid: int) -> OBSActiveClient:
        matches = list(filter(lambda x: x == uid, self.active_clients))
        if len(matches) == 0:
            raise IndexError(f"Client #{uid} was not found among the active clients!")
        return matches[0]

    def is_disconnected(self: OBSClientsManager, uid: int) -> bool:
        return len(list(filter(lambda x: x.id == uid, self.active_clients))) == 0

    def connect_client(self: OBSClientsManager, uid: int) -> None:
        try:
            db_info: OBSWSClientModel = self.get_db_info_by_id(uid)
            if db_info is None:
                raise RuntimeError(f"Client #{uid} was not found in the DB!")
            new_client = OBSActiveClient(self.db, db_info, self.twitch)
            self.active_clients.append(new_client)
            LOG.debug("Active client count: %s", len(self.active_clients))
        except OBSSDKError as e:
            LOG.error(e)
            raise e
    
    def connect_all_db_clients(self: OBSClientsManager) -> None:
        clients = self.get_active_user_clients()
        for c in clients:
            if(self.is_disconnected(c.id)):
                self.connect_client(c.id)

    def disconnect_client(self: OBSClientsManager, uid: int) -> None:
        client = self[uid]
        try:
            client.disconnect()
            self.active_clients.remove(client)
            LOG.debug("Active client count: %s", len(self.active_clients))
        except OBSSDKError as e:
            LOG.error(e)
            raise e

    def add_client(self: OBSClientsManager, host: str, port: int, password: str):
        new_client = OBSWSClientModel(host=host, port=port, password=password)
        self.db.session.add(new_client)
        self.db.session.commit()

    def update_client(self: OBSClientsManager, uid: int, values: dict):
        db_info = OBSWSClientModel.query.filter_by(id=uid).one_or_none()
        if db_info is None:
            raise RuntimeError("client not found")
        self.__validate_permission(db_info)
        OBSWSClientModel.query.filter_by(id=uid).update(values)
        self.db.session.commit()

    def delete_client(self: OBSClientsManager, uid: int):
        db_info = OBSWSClientModel.query.filter_by(id=uid).one_or_none()
        if db_info is None:
            raise RuntimeError("client not found")
        self.__validate_permission(db_info)
        self.db.session.delete(db_info)
        self.db.session.commit()

    def get_active_user_clients(self: OBSClientsManager) -> List[OBSWSClientModel]:
        return OBSWSClientModel.query.all()

    def get_db_info_by_id(self: OBSClientsManager, uid: int) -> Union[OBSWSClientModel | None]:
        db_info = OBSWSClientModel.query.filter_by(id=uid).one_or_none()
        self.__validate_permission(db_info)
        return db_info
