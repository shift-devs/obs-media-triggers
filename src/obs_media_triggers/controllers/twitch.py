from __future__ import annotations
from twitchAPI.twitch import Twitch
from logging import getLogger
from .. import __app_host__, __app_port__

LOG = getLogger(__name__)


class TwitchClient(Twitch):
    app_id: str = None
    app_secret: str = None

    def __init__(
        self: TwitchClient,
        app_id: str,
        app_secret: str,
        scheme: str = "https",
        host: str = __app_host__,
        port: int = __app_port__,
    ):
        super().__init__(app_id, app_secret, base_url=f"{scheme}://{host}:{port}/")
        self.app_id = app_id
        self.app_secret = app_secret


class TwitchClientManager:
    clients: list[TwitchClient]

    def __init__(self: TwitchClientManager):
        self.clients = []

    def is_connected(self: TwitchClientManager) -> bool:
        return True

    def connect(self: TwitchClientManager):
        new_client = TwitchClient()
        self.clients.append(new_client)
