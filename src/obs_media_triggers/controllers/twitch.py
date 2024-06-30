from __future__ import annotations

from asyncio import run
from typing import Tuple, Union
from logging import getLogger
from twitchAPI.helper import first
from twitchAPI.type import AuthScope
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from ..models import TwitchOAuthUserModel
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.eventsub.websocket import EventSubWebsocket
from flask_login import current_user, login_user, logout_user, LoginManager
from twitchAPI.twitch import Twitch, TwitchUser, TwitchAPIException
from .. import __app_host__, __app_port__, __app_id__, __app_secret__

LOG = getLogger(__name__)


class TwitchClient(Twitch):
    API_SCOPES = [
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
        self.db = app.db
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
            self.logout()
            return None
        else:
            login_user(db_user)
            return db_user

    def logout(self: TwitchClient) -> None:
        if self.events is not None:
            if self.events._running:
                run(self.events.unsubscribe_all())
                run(self.events.stop())
        if self.auth._server_running:
            run(self.auth.stop())
        logout_user()

    def sync_api_user_to_db(self: TwitchClient) -> Union[TwitchOAuthUserModel | None]:
        api_user: TwitchUser = self.api_get_user()

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

    def api_get_user(self: TwitchClient) -> object:
        return run(first(self.get_users()))

    def db_get_user(self: TwitchClient) -> Union[TwitchOAuthUserModel | None]:
        return TwitchOAuthUserModel.query.filter_by(id=current_user.id).one_or_none()

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
        return self.auth._is_closed

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
