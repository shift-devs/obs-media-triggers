from __future__ import annotations

from typing import Union
from logging import getLogger
from obsws_python import ReqClient
from flask_login import current_user
from ..models import OBSWSClientModel
from flask_sqlalchemy import SQLAlchemy
from obsws_python.error import OBSSDKError
from ..controllers.user import UserManager

LOG = getLogger(__name__)


class OBSActiveClient(ReqClient):
    db_info: OBSWSClientModel
    active_scene_name: str

    def __init__(self: OBSActiveClient, db_info: OBSWSClientModel, timeout: int = 1):
        super().__init__(
            host=db_info.host,
            port=db_info.port,
            password=db_info.password,
            timeout=timeout,
        )
        self.db_info = db_info
        self.active_scene_name = None

    def __eq__(self: OBSActiveClient, other_id: int) -> bool:
        return self.db_info.id == other_id


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
        users: UserManager = self.app.user_manager
        user_id = users.get_id_by_name()
        if db_info is not None and db_info.user_id != user_id:
            raise AssertionError(
                f"User #{user_id} does not have permission to access Client -> {db_info}"
            )

    def __getitem__(self: OBSClientsManager, id: int) -> OBSActiveClient:
        matches = list(filter(lambda x: x == id, self.active_clients))
        if len(matches) == 0:
            raise IndexError(f"Client #{id} was not found among the active clients!")
        return matches[0]

    def is_disconnected(self: OBSClientsManager, id: int) -> bool:
        return len(list(filter(lambda x: x.db_info.id == id, self.active_clients))) == 0

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

    def add_client(
        self: OBSClientsManager, user_id: int, host: str, port: int, password: str
    ):
        new_client = OBSWSClientModel(
            user_id=user_id, host=host, port=port, password=password
        )
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
        users: UserManager = self.app.user_manager
        user_id = users.get_id_by_name()
        return OBSWSClientModel.query.filter_by(user_id=user_id).all()

    def get_db_info_by_id(
        self: OBSClientsManager, id: int
    ) -> Union[OBSWSClientModel | None]:
        db_info = OBSWSClientModel.query.filter_by(id=id).one_or_none()
        self.__validate_permission(db_info)
        return db_info

    def get_all_events(self: OBSClientsManager) -> list[OBSWSClientModel]:
        return OBSWSClientModel.query.all()
