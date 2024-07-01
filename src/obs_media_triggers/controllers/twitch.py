from __future__ import annotations

from asyncio import run
from typing import Awaitable, Union
from flask import current_app
from logging import getLogger
from twitchAPI.helper import first
from twitchAPI.type import AuthScope
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch, TwitchUser
from ..models import TwitchOAuthUserModel, EventSubModel
from twitchAPI.eventsub.websocket import EventSubWebsocket
from .. import __app_host__, __app_port__, __app_id__, __app_secret__
from flask_login import current_user, login_user, logout_user, LoginManager

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
        host: str = __app_host__,
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

    def login(
        self: TwitchClient, user_token: str
    ) -> Union[TwitchOAuthUserModel | None]:
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
        db_user = self.sync_api_user_to_db()
        if db_user is None:
            raise RuntimeError(f"Failed to create local sync of user: {db_user}!")
        login_user(db_user)
        LOG.debug(f"User logged in with info: {db_user}")
        return db_user

    def logout(self: TwitchClient) -> None:
        if self.events is not None:
            if self.events._running:
                run(self.events.unsubscribe_all())
                run(self.events.stop())
        if self.auth._server_running:
            self.set_user_authentication(None, TwitchClient.API_SCOPES, None)
            run(self.auth.stop())

        LOG.debug(f"User logged out!")
        logout_user()

    def sync_api_user_to_db(self: TwitchClient) -> Union[TwitchOAuthUserModel | None]:
        api_user: TwitchUser = run(self.api_get_user())

        db_user = TwitchOAuthUserModel(
            id=api_user.id,
            login_name=api_user.login,
            display_name=api_user.display_name,
            pfp_url=api_user.profile_image_url,
            user_token=run(self.get_refreshed_user_auth_token()),
        )
        user_exists = (
            TwitchOAuthUserModel.query.filter_by(id=db_user.id).one_or_none()
            is not None
        )

        try:
            if user_exists:
                TwitchOAuthUserModel.query.update(db_user.to_dict())
            else:
                self.db.session.add(db_user)
            self.db.session.commit()
            return db_user
        except IntegrityError as e:
            LOG.error(f"Failed to add sync user {db_user} to DB with reason: {e}")

    async def api_get_user(self: TwitchClient) -> object:
        return await first(self.get_users())

    def db_get_user(self: TwitchClient) -> Union[TwitchOAuthUserModel | None]:
        return TwitchOAuthUserModel.query.filter_by(id=current_user.id).one_or_none()

    async def subscribe_to_chat_message_event(
        self: TwitchClient, callback: Awaitable
    ) -> None:
        try:
            self.events.start()
        except RuntimeError as e:
            LOG.warn("Twitch ES server is already running!")
        user: TwitchUser = current_user
        res = await self.events.listen_channel_chat_message(user.id, user.id, callback)
        LOG.info(f"Registered subscription with Twitch: {res}")

    @property
    def is_logged_in(self: TwitchClient) -> bool:
        # if self.auth._is_closed:
        #     db_user = self.get_db_user()
        #     try:
        #         self.login(db_user.user_token)
        #         login_user(db_user)
        #     except TwitchAPIException as e:
        #         LOG.error(f'Failed to auto-log-into Twitch with reason: {e}')
        #         logout_user()
        #         return False
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
