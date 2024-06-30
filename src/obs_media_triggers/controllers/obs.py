from __future__ import annotations

from typing import Union
from logging import getLogger
from obsws_python import ReqClient
from ..models import OBSWSClientModel, EventModel
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from obsws_python.error import OBSSDKError

LOG = getLogger(__name__)


class OBSActiveClient(ReqClient):
    db: SQLAlchemy
    db_info: OBSWSClientModel
    id: int
    host: str
    port: int
    password: str
    active_scene: str
    active_events: list[EventModel]

    def __init__(self: OBSActiveClient, db_info: OBSWSClientModel, timeout: int = 1):
        super().__init__(
            host=db_info.host,
            port=db_info.port,
            password=db_info.password,
            timeout=timeout,
        )
        self.db = current_app.db
        self.id = db_info.id
        self.host = db_info.host
        self.port = db_info.port
        self.password = db_info.password
        self.active_scene = "default"
        self.active_events = []

    def __eq__(self: OBSActiveClient, other_id: int) -> bool:
        return self.id == other_id

    def add_event(
        self: OBSActiveClient,
        obs_id: int,
        type: str,
        quantity: int,
        allow_anon: bool,
        src_template: str,
    ):
        new_event = EventModel(
            obs_id=obs_id,
            type=type,
            quantity=quantity,
            allow_anon=allow_anon,
            src_template=src_template,
        )
        self.db.session.add(new_event)
        self.db.session.commit()
        self.active_events.append(new_event)

    def get_all_sources(self: OBSActiveClient):
        LOG.debug(f"Looking for sources in active scene: {self.active_scene}")
        items = self.get_scene_item_list(self.active_scene).scene_items
        return list(map(lambda x: x["sourceName"], items))

    def get_all_events(self: OBSActiveClient) -> list[EventModel]:
        return EventModel.query.all()


class OBSClientsManager:
    active_clients: list[OBSActiveClient]
    db: SQLAlchemy
    app: object

    def __init__(self: OBSClientsManager, app: object):
        self.active_clients = []
        self.db = app.db
        self.app = app

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
            new_client = OBSActiveClient(db_info)
            LOG.debug(f"Active clinets: {new_client}")
            self.active_clients.append(new_client)
        except OBSSDKError as e:
            raise RuntimeError(e)

    def disconnect_client(self: OBSClientsManager, id: int) -> None:
        client = self[id]
        try:
            client.disconnect()
            self.active_clients.remove(client)
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
