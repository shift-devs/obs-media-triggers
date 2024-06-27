from __future__ import annotations
from typing import Union
from logging import getLogger
from obsws_python import ReqClient
from obsws_python.error import OBSSDKError


LOG = getLogger(__name__)


class OBSClient(ReqClient):
    host: str
    port: int
    password: str

    def __init__(
        self: OBSClient, host: str, port: int, password: str = None, timeout: int = 1
    ):
        super().__init__(host=host, port=port, password=password, timeout=timeout)
        self.host = host
        self.port = port
        self.password = password

    def __eq__(self: OBSClient, other: tuple) -> bool:
        other_host, other_port = other
        return (self.host == other_host) and (self.port == other_port)

    def set_active_scene(self, scene_name: str):
        self.set_active_scene(scene_name)

    @property
    def url(self: OBSClient) -> str:
        return f"ws://{self.host}:{self.port}/"


class OBSClientsManager:
    clients: list[OBSClient]

    def __init__(self: OBSClientsManager):
        self.clients = []

    def find(self: OBSClientsManager, host: str, port: int) -> Union[OBSClient, None]:
        url = f"ws://{host}:{port}/"
        for c in self.clients:
            if url == c.url:
                return c
        return None

    def is_connected(self: OBSClientsManager, host: str, port: int) -> bool:
        return self.find(host, port) is not None

    def connect(
        self: OBSClientsManager, host: str, port: int, password: str = None
    ) -> None:
        try:
            new_client = OBSClient(host, port, password=password)
            self.clients.append(new_client)
        except OBSSDKError as e:
            raise RuntimeError(e)

    def disconnect(self: OBSClientsManager, host: str, port: int) -> None:
        del_client = self.find(host, port)
        if del_client is not None:
            try:
                del_client.disconnect()
                self.clients.remove(del_client)
                return
            except OBSSDKError as e:
                raise RuntimeError(e)
        raise RuntimeError("The attached client was not found in the manager!")
