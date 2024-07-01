from __future__ import annotations

from time import sleep
from typing import Union
from logging import getLogger
from .twitch import TwitchClient
from obsws_python import ReqClient
from .events import EventSubsManager
from ..models import OBSWSClientModel
from flask_sqlalchemy import SQLAlchemy
from obsws_python.error import OBSSDKError
from twitchAPI.object.eventsub import ChannelChatMessageEvent, ChannelChatMessageData

LOG = getLogger(__name__)


class OBSActiveClient(ReqClient):
    DEFAULT_ACTIVE_SCENE = "NO_ACTIVE_SCENE"

    db: SQLAlchemy
    db_info: OBSWSClientModel
    id: int
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

    def get_all_sources(self: OBSActiveClient):
        LOG.debug(f"Looking for sources in active scene: {self.active_scene}")
        items = self.get_scene_item_list(self.active_scene).scene_items
        return list(map(lambda x: x["sourceName"], items))

    def subscribe_to_event(self: OBSActiveClient, form: dict) -> None:
        LOG.debug(f'Subscribing to event with payload: {form}')
        self.events.add_event_sub(self.handle_chat_message)

    # def toggle_media(self: OBSActiveClient, src_name: str) -> None:
    #     scene_name = self.active_scene
    #     item_id = self.get_scene_item_id(scene_name, src_name)
    #     self.set_scene_item_enabled(scene_name, item_id, True)
    #     sleep(3)
    #     self.set_scene_item_enabled(scene_name, item_id, False)

    async def handle_chat_message(self: OBSActiveClient, event: ChannelChatMessageEvent):
        data: ChannelChatMessageData = event.event
        cmd = data.message.text.title()
        srcs = self.get_all_sources()

        if(cmd in srcs):
            LOG.debug(f"Enabling Source by command: {cmd}")
            item_id = self.get_scene_item_id(self.active_scene, cmd).scene_item_id

            if(item_id is None):
                LOG.error(f'A source for cmd: {cmd} was not found!')
                return

            self.set_scene_item_enabled(self.active_scene, item_id, True)
            sleep(3)
            LOG.debug(f"Disabling {cmd}#{item_id}")
            self.set_scene_item_enabled(self.active_scene, item_id, False)


class OBSClientsManager:
    active_clients: list[OBSActiveClient]
    db: SQLAlchemy
    twitch: TwitchClient

    def __init__(self: OBSClientsManager, db: SQLAlchemy, twitch: TwitchClient):
        self.active_clients = []
        self.db = db
        self.twitch = twitch

    def __validate_permission(
        self: OBSClientsManager, db_info: OBSWSClientModel
    ) -> None:
        return True

    def __getitem__(self: OBSClientsManager, id: int) -> OBSActiveClient:
        matches = list(filter(lambda x: x == id, self.active_clients))
        if len(matches) == 0:
            raise IndexError(f"Client #{id} was not found among the active clients!")
        return matches[0]

    def is_disconnected(self: OBSClientsManager, id: int) -> bool:
        return len(list(filter(lambda x: x.id == id, self.active_clients))) == 0

    def connect_client(self: OBSClientsManager, id: int) -> None:
        try:
            db_info: OBSWSClientModel = self.get_db_info_by_id(id)
            if db_info is None:
                raise RuntimeError(f"Client #{id} was not found in the DB!")
            new_client = OBSActiveClient(self.db, db_info, self.twitch)
            self.active_clients.append(new_client)
            LOG.debug(f"Active client count: {len(self.active_clients)}")
        except OBSSDKError as e:
            raise RuntimeError(e)

    def disconnect_client(self: OBSClientsManager, id: int) -> None:
        client = self[id]
        try:
            client.disconnect()
            self.active_clients.remove(client)
            LOG.debug(f"Active client count: {len(self.active_clients)}")
        except OBSSDKError as e:
            raise RuntimeError(e)

    def add_client(self: OBSClientsManager, host: str, port: int, password: str):
        new_client = OBSWSClientModel(host=host, port=port, password=password)
        self.db.session.add(new_client)
        self.db.session.commit()

    def update_client(self: OBSClientsManager, id: int, values: dict):
        db_info = OBSWSClientModel.query.filter_by(id=id).one_or_none()
        if db_info is None:
            raise RuntimeError("client not found")
        self.__validate_permission(db_info)
        OBSWSClientModel.query.filter_by(id=id).update(values)
        self.db.session.commit()

    def delete_client(self: OBSClientsManager, id: int):
        db_info = OBSWSClientModel.query.filter_by(id=id).one_or_none()
        if db_info is None:
            raise RuntimeError("client not found")
        self.__validate_permission(db_info)
        self.db.session.delete(db_info)
        self.db.session.commit()

    def get_active_user_clients(self: OBSClientsManager) -> list[OBSActiveClient]:
        return OBSWSClientModel.query.filter_by().all()

    def get_db_info_by_id(
        self: OBSClientsManager, id: int
    ) -> Union[OBSWSClientModel | None]:
        db_info = OBSWSClientModel.query.filter_by(id=id).one_or_none()
        self.__validate_permission(db_info)
        return db_info
