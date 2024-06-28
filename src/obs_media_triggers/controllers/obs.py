from __future__ import annotations
from typing import Union
from logging import getLogger
from obsws_python import ReqClient
from obsws_python.error import OBSSDKError
from ..models import OBSWSClientModel
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user

LOG = getLogger(__name__)


class OBSClient(ReqClient):
    db_info: OBSWSClientModel
    active_scene_name: str

    def __init__(self: OBSClient, db_info: OBSWSClientModel, timeout: int = 1):
        super().__init__(
            host=db_info.host,
            port=db_info.port,
            password=db_info.password,
            timeout=timeout,
        )
        self.db_info = db_info
        self.active_scene_name = None

    def __eq__(self: OBSClient, other_id: int) -> bool:
        return self.db_info.id == other_id


class OBSClientsManager:
    active_clients: list[OBSClient]
    db: SQLAlchemy

    def __init__(self: OBSClientsManager, app: object):
        self.active_clients = []
        self.db = app.db

    def __validate_permission(self: OBSClientsManager, db_info: OBSWSClientModel) -> None:
        user_id = current_user.name
        if db_info is not None and db_info.user_id != user_id:
            raise AssertionError(
                f"User #{user_id} does not have permission to access Client -> {db_info}"
            )

    def __getitem__(self: OBSClientsManager, id: int) -> OBSClient:
        matches = list(filter(lambda x: x == id, self.active_clients))
        if len(matches) == 0:
            raise IndexError(f"Client #{id} was not found among the active clients")
        return matches[0]

    def is_connected(self: OBSClientsManager, host: str, port: int) -> bool:
        return self.find(host, port) is not None

    def connect_client(self: OBSClientsManager, user_id: int, id: int) -> None:
        try:
            db_info: OBSWSClientModel = self.get_client_by_id(user_id, id)
            new_client = OBSClient(
                db_info.host, db_info.port, password=db_info.password
            )
            self.active_clients.append(new_client)
        except OBSSDKError as e:
            raise RuntimeError(e)

    def disconnect_client(self: OBSClientsManager, user_id: int, id: int) -> None:
        matches = list(filter(lambda x: x.matches(user_id, id)))
        if len(matches) == 0:
            raise RuntimeError("The attached client was not found in the manager!")
        client = matches[0]
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
        OBSWSClientModel.query.filter_by(id=id).update(values=values)
        self.db.session.commit()

    def delete_client(self: OBSClientsManager, id: int):
        OBSWSClientModel.query.filter_by(id=id).delete()

    def get_all_clients(self: OBSClientsManager) -> list[OBSClient]:
        return OBSWSClientModel.query.all()

    def get_client_by_id(
        self: OBSClientsManager, id: int
    ) -> Union[OBSWSClientModel | None]:
        db_info = OBSWSClientModel.query.filter_by(id=id).one_or_none()
        self.__validate_permission(db_info)
        return db_info

    def get_all_events(self: OBSClientsManager) -> list[OBSWSClientModel]:
        return OBSWSClientModel.query.all()
