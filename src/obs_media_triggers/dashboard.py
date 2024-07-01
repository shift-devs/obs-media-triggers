from __future__ import annotations

import random, string
from .models import DB
from flask import Flask
from logging import getLogger
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, LoginManager
from .views import view_events, view_obs, view_twitch
from .controllers import OBSClientsManager, TwitchClient

LOG = getLogger(__name__)
DEFAULT_DB_NAME = "obs-media-triggers.db"


def gen_secret(length: int = 64) -> str:
    return "".join(random.choice(string.printable) for _ in range(length))


class Dashboard(Flask):
    debug: bool = False
    host: str
    port: int
    db: SQLAlchemy
    obs: OBSClientsManager
    twitch: TwitchClient
    login_manager: LoginManager

    def __init__(
        self: Dashboard,
        host: str = "localhost",
        port: int = 7064,
        debug: bool = False,
        db_uri: str = f"sqlite:///{DEFAULT_DB_NAME}",
        secret_key: str = "Something Random",
    ):
        super().__init__(__name__)
        self.debug = debug
        self.db = DB
        self.host = host
        self.port = port

        # Register endpoints
        self.register_blueprint(view_obs, url_prefix="/")
        self.register_blueprint(view_twitch, url_prefix="/twitch/")
        self.register_blueprint(view_events, url_prefix="/event/")

        # Setup Controlelrs
        self.twitch = TwitchClient(self, db=self.db, host=host, port=port)
        self.obs = OBSClientsManager(db=self.db, twitch=self.twitch)
        self.login_manager = self.twitch.get_login()

        # Configure Flask app
        self.config["SECRET_KEY"] = secret_key
        self.config["SQLALCHEMY_DATABASE_URI"] = db_uri

        # Map variables to Jinja environment
        self.jinja_env.globals.update(user=current_user)
        self.jinja_env.globals.update(obs=self.obs)
        self.jinja_env.globals.update(twitch=self.twitch)

        # Initialize the database schemas and link to flask
        with self.app_context():
            self.db.init_app(self)
            self.db.create_all()

    def run(self: Dashboard) -> any:
        return super().run(host=self.host, port=self.port, debug=self.debug)
