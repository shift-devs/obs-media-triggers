from __future__ import annotations

import random, string
from asyncio import run
from flask import Flask
from logging import getLogger
from .models import DB, UserModel
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from .views import view_home, view_auth, view_obs, view_twitch, view_users
from .controllers import OBSClientsManager, TwitchClientManager, UserManager

LOG = getLogger(__name__)
DEFAULT_DB_NAME = "obs-media-triggers.db"


def gen_secret(length: int = 64) -> str:
    return "".join(random.choice(string.printable) for _ in range(length))


class Dashboard(Flask):
    debug: bool = False
    host: str
    port: int
    db: SQLAlchemy
    obs_manager: OBSClientsManager
    twitch_manager: TwitchClientManager
    user_manager: UserManager

    def __init__(
        self: Dashboard,
        host: str = "localhost",
        port: int = 7064,
        debug: bool = False,
        db_uri: str = f"sqlite:///{DEFAULT_DB_NAME}",
        secret_key: str = None,
    ):
        super().__init__(__name__)
        self.debug = debug
        self.db = DB
        self.host = host
        self.port = port

        # Register endpoints
        self.register_blueprint(view_home, url_prefix="/")
        self.register_blueprint(view_auth, url_prefix="/auth/")
        self.register_blueprint(view_obs, url_prefix="/obs/")
        self.register_blueprint(view_twitch, url_prefix="/twitch/")
        self.register_blueprint(view_users, url_prefix="/users/")

        # Setup Controlelrs
        self.obs_manager = OBSClientsManager(self)
        self.twitch_manager = TwitchClientManager()
        self.user_manager = UserManager(self)

        # Configure Flask app
        self.config["SECRET_KEY"] = self.user_manager.password_policy.generate_password() if(secret_key is None) else secret_key
        self.config["SQLALCHEMY_DATABASE_URI"] = db_uri

        # Map callable vars and functions to Jinja environment
        self.jinja_env.globals.update(arun=run)
        self.jinja_env.globals.update(user=current_user)

        # Map controllers to Jinja environment
        self.jinja_env.globals.update(obs_manager=self.obs_manager)
        self.jinja_env.globals.update(twitch_manager=self.twitch_manager)
        self.jinja_env.globals.update(user_manager=self.user_manager)

        # Initialize the database schemas and link to flask
        with self.app_context():
            self.db.init_app(self)
            self.db.create_all()


    def run(self: Dashboard) -> any:
        return super().run(host=self.host, port=self.port, debug=self.debug)
