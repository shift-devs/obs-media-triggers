from __future__ import annotations

from logging import getLogger
from dataclasses import dataclass
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.object.api import TwitchUser
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.eventsub.websocket import EventSubWebsocket
from .. import __app_host__, __app_port__, __app_id__, __app_secret__

LOG = getLogger(__name__)
TWITCH_API_SCOPES = [
    AuthScope.USER_READ_SUBSCRIPTIONS,
    AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
    AuthScope.USER_READ_EMAIL,
]


class TwitchClient(Twitch):
    app_id: str = None
    app_secret: str = None

    def __init__(self: TwitchClient, app_id: str, app_secret: str, **kwargs):
        super().__init__(app_id, app_secret, **kwargs)
        self.app_id = app_id
        self.app_secret = app_secret


@dataclass
class TwitchEvent:
    type: str = None
    name: str = None
    allow_anon: bool = False


class TwitchClientManager:
    api: TwitchClient
    auth: UserAuthenticator
    app_url: str
    events: EventSubWebsocket

    def __init__(
        self: TwitchClientManager,
        scheme: str = "http",
        host: str = __app_host__,
        port: int = __app_port__,
    ):
        self.api = None
        self.auth = None
        self.app_url = f"{scheme}://{host}:{port}/twitch/login"

    def start_auth(self: TwitchClientManager):
        self.api = TwitchClient(__app_id__, __app_secret__)
        self.api.auto_refresh_auth = True
        self.auth = UserAuthenticator(
            self.api, TWITCH_API_SCOPES, force_verify=False, url=self.app_url
        )
        return self.auth.return_auth_url()

    async def login(self: TwitchClientManager, user_token: str) -> bool:
        access_token, refresh_token = await self.auth.authenticate(
            user_token=user_token
        )
        await self.api.set_user_authentication(
            access_token,
            refresh_token=refresh_token,
            scope=TWITCH_API_SCOPES,
            validate=True,
        )
        await self.api.authenticate_app(TWITCH_API_SCOPES)
        return self.is_connected()

    async def logout(self: TwitchClientManager) -> None:
        self.stop_es()
        self.auth = None
        self.api = None

    def is_connected(self: TwitchClientManager) -> bool:
        return (self.auth is not None) and (self.auth.state is not None)

    def start_es(self: TwitchClientManager) -> None:
        self.events = EventSubWebsocket(self.api)
        if self.events is not None:
            self.events.start()

    def stop_es(self: TwitchClientManager) -> None:
        if self.events is not None:
            self.events.unsubscribe_all()
            self.events.stop()
        self.events = None
    
    def get_all_event_types():
        raw_func  = EventSubWebsocket.__dict__
        return list(raw_func)

    @property
    async def user_name(self: TwitchClientManager) -> str:
        user: TwitchUser = await first(self.api.get_users())
        return user.display_name

    @property
    async def user_pfp(self: TwitchClientManager) -> str:
        user: TwitchUser = await first(self.api.get_users())
        return user.profile_image_url
