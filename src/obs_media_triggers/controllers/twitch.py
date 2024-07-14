from __future__ import annotations

from time import sleep
from asyncio import run
from logging import getLogger
from typing import Awaitable, Union

from flask_login import LoginManager, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.type import AuthScope

from .. import __app_id__, __app_port__, __app_secret__
from ..models import TwitchOAuthUserModel

LOG = getLogger(__name__)


class TwitchClient(Twitch):
    API_SCOPES = [
        AuthScope.USER_READ_CHAT,
        AuthScope.USER_READ_EMAIL,
        AuthScope.USER_READ_SUBSCRIPTIONS,
        AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
    ]

    db: SQLAlchemy
    callback_url: str
    auth: UserAuthenticator
    events: EventSubWebsocket
    login_manager: LoginManager

    def __init__(
        self: TwitchClient,
        app: object,
        db: SQLAlchemy,
        scheme: str = "http",
        host: str = "localhost",
        port: int = __app_port__,
        app_id: str = __app_id__,
        app_secret: str = __app_secret__,
        **kwargs,
    ):
        super().__init__(app_id, app_secret, **kwargs)

        # Twitch Client Options
        self.auto_refresh_auth = True
        self.callback_url = f"{scheme}://{host}:{port}/twitch/login"

        # Setup Twitch peripheral managers
        self.db = db
        self.auth = UserAuthenticator(
            self,
            TwitchClient.API_SCOPES,
            force_verify=False,
            url=self.callback_url,
        )
        self.events = EventSubWebsocket(self)

        # Setup login manager
        self.login_manager = LoginManager(app)
        self.login_manager.login_view = "view_twitch.get_root"
        self.login_manager.login_message_category = "danger"

        @self.login_manager.user_loader
        def load_user(id: str):
            return TwitchOAuthUserModel.query.filter_by(id=id).one_or_none()

    def get_login(self: TwitchClient) -> LoginManager:
        return self.login_manager

    def get_user_auth_url(self: TwitchClient):
        return self.auth.return_auth_url()

    def login(self: TwitchClient, user_token: str) -> Union[TwitchOAuthUserModel | None]:
        access_token, refresh_token = run(self.auth.authenticate(user_token=user_token))
        run(
            self.set_user_authentication(
                access_token,
                refresh_token=refresh_token,
                scope=TwitchClient.API_SCOPES,
                validate=True,
            )
        )
        run(self.authenticate_app(TwitchClient.API_SCOPES))
        db_user = self.sync_api_user_to_db(user_token)
        if db_user is None:
            raise RuntimeError(f"Failed to create local sync for {db_user.login_name}!")
        login_user(db_user)
        LOG.debug(f"Logged into Twitch as {db_user.login_name}!")
        self.__safe_start_events()
        return db_user

    def logout(self: TwitchClient) -> None:
        if self.events is not None and self.events._ready:
            run(self.events.unsubscribe_all())
            run(self.events.stop())
        if self.auth._server_running:
            self.set_user_authentication(None, TwitchClient.API_SCOPES, None)
            run(self.auth.stop())
        logout_user()
        LOG.debug("User logged out from Twitch!")

        # try:
        # except RuntimeError as e:
        #     LOG.error(e)

    def sync_api_user_to_db(self: TwitchClient, user_token: str) -> Union[TwitchOAuthUserModel | None]:
        api_user: TwitchUser = run(self.api_get_user())

        db_user = TwitchOAuthUserModel(
            id=api_user.id,
            login_name=api_user.login,
            display_name=api_user.display_name,
            pfp_url=api_user.profile_image_url,
            user_token=user_token,
        )
        user_exists = TwitchOAuthUserModel.query.filter_by(id=db_user.id).one_or_none() is not None

        try:
            if user_exists:
                TwitchOAuthUserModel.query.update(db_user.to_dict())
            else:
                self.db.session.add(db_user)
            self.db.session.commit()
            return db_user
        except IntegrityError as e:
            LOG.error("Failed to add sync user %s to DB with reason: %s", db_user, e)

    async def api_get_user(self: TwitchClient) -> object:
        return await first(self.get_users())

    def db_get_user(self: TwitchClient) -> Union[TwitchOAuthUserModel | None]:
        return TwitchOAuthUserModel.query.filter_by(id=current_user.id).one_or_none()

    def __safe_start_events(self: TwitchClient) -> None:
        try:
            self.events.start()
        except RuntimeError:
            LOG.warn("Twitch ES server is already running!")

    async def subscribe_to_chat_message(self: TwitchClient, callback: Awaitable) -> None:
        user: TwitchUser = current_user
        await self.__subscribe_to_event(
            self.events.listen_channel_chat_message, user.id, user.id, callback
        )

    async def subscribe_to_gift_subscription(self: TwitchClient, callback: Awaitable):
        user: TwitchUser = current_user
        await self.__subscribe_to_event(
            self.events.listen_channel_subscription_gift, user.id, callback
        )

    async def __subscribe_to_event(self: TwitchClient, event_sub: Awaitable, *args) -> None:
        user: TwitchUser = current_user
        self.__safe_start_events()
        res = await event_sub(*args)
        LOG.debug("Registered subscription @Twitch-API %s with args: %s", res, args)

    @property
    def is_logged_in(self: TwitchClient) -> bool:
        return self.get_user_auth_token() is not None

    @property
    def username(self: TwitchClient) -> str:
        user: TwitchOAuthUserModel = self.db_get_user()
        if user is None:
            return None
        return user.display_name

    @property
    def pfp_url(self: TwitchClient) -> str:
        user: TwitchOAuthUserModel = self.db_get_user()
        if user is None:
            return None
        return user.pfp_url
