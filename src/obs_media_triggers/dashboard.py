"""Main Flask Application"""

from __future__ import annotations

import random
import string
from logging import getLogger

from flask import Flask
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy

from .controllers import OBSClientsManager, TwitchClient
from .models import DB
from .views import view_events, view_obs, view_twitch

LOG = getLogger(__name__)
DEFAULT_DB_NAME = "obs-media-triggers.db"


def gen_secret(length: int = 64) -> str:
    """_summary_

    :param length: Generate a random string, defaults to 64
    :type length: int, optional
    :return: Fixed-length string of random ASCII characters
    :rtype: str
    """
    return "".join(random.choice(string.printable) for _ in range(length))


class Dashboard(Flask):
    """Primary flask application for OBS Media Triggers Dashboard"""

    DATA_DIR = "./"

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
        secret_key: str = "Something Random",
    ):
        """Dashboard constructor
        :param host: Host to bind application to, defaults to "localhost"
        :type host: str, optional
        :param port: Port to bind application to, defaults to 7064
        :type port: int, optional
        :param debug: Toggles debug mode, defaults to False
        :type debug: bool, optional
        :param secret_key: Secret string for SSL entcryption, defaults to "Something Random"
        :type secret_key: str, optional
        """
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
        self.twitch = TwitchClient(self, db=self.db, port=port)
        self.obs = OBSClientsManager(db=self.db, twitch=self.twitch)
        self.login_manager = self.twitch.get_login()

        # Configure Flask app
        self.config["SECRET_KEY"] = secret_key
        self.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Dashboard.DATA_DIR}/{DEFAULT_DB_NAME}"
        LOG.debug("Initializing Database at -> %s", self.config["SQLALCHEMY_DATABASE_URI"])

        # Map variables to Jinja environment
        self.jinja_env.globals.update(user=current_user)
        self.jinja_env.globals.update(obs=self.obs)
        self.jinja_env.globals.update(twitch=self.twitch)

        # Initialize the database schemas and link to flask
        with self.app_context():
            self.db.init_app(self)
            self.db.create_all()
            self.obs.connect_all_db_clients()
            # self.twitch.login_with_db_user()

    def run(self: Dashboard, *args) -> any:
        return super().run(host=self.host, port=self.port, debug=self.debug, *args)
