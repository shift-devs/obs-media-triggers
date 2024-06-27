from __future__ import annotations
import random, string
from flask import Flask
from logging import getLogger
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .models import DB, User, OBSWebSocketClient
from .controllers import OBSClientsManager, TwitchClientManager
from .views import view_home, view_auth, view_obs, view_twitch, view_user, PSUT

LOG = getLogger(__name__)
DEFAULT_DB_NAME = "obs-media-triggers.db"


def gen_secret(length: int = 64) -> str:
    return "".join(random.choice(string.printable) for _ in range(length))


class Dashboard(Flask):
    debug: bool = False
    host: str
    port: int
    db: SQLAlchemy
    login_manager: LoginManager
    obs_manager: OBSClientsManager
    twitch_manager: TwitchClientManager

    def __init__(
        self: Dashboard,
        host: str = "localhost",
        port: int = 7064,
        debug: bool = False,
        db_uri: str = f"sqlite:///{DEFAULT_DB_NAME}",
        secret_key: str = gen_secret(),
    ):
        super().__init__(__name__)
        self.debug = debug
        self.db = DB
        self.host = host
        self.port = port

        # Configure Flask app
        self.config["SECRET_KEY"] = secret_key
        self.config["SQLALCHEMY_DATABASE_URI"] = db_uri

        # Register endpoints
        self.register_blueprint(view_home, url_prefix="/")
        self.register_blueprint(view_auth, url_prefix="/auth/")
        self.register_blueprint(view_obs, url_prefix="/obs/")
        self.register_blueprint(view_twitch, url_prefix="/twitch/")
        self.register_blueprint(view_user, url_prefix="/user/")

        # Setup Controlelrs
        self.obs_manager = OBSClientsManager()
        self.twitch_manager = TwitchClientManager()

        # Setup login manager
        self.login_manager = LoginManager(self)
        self.login_manager.login_view = "view_auth.get_login"

        @self.login_manager.user_loader
        def load_user(username: str):
            return User.query.filter_by(name=username).one_or_none()

        # Map callable functions to Jinja environment
        self.jinja_env.globals.update(password_strength_reqs=PSUT)
        self.jinja_env.globals.update(get_all_users=self.get_all_users)
        self.jinja_env.globals.update(get_all_obs_clients=self.get_all_obs_clients)

        # Map controllers to Jinja environment
        self.jinja_env.globals.update(obs_manager=self.obs_manager)
        self.jinja_env.globals.update(twitch_manager=self.twitch_manager)

        # Initialize the database schemas and link to flask
        with self.app_context():
            self.db.init_app(self)
            self.db.create_all()

    def get_all_users(self: Dashboard) -> list[User]:
        res = self.db.session.query(User).all()
        return self.db.session.query(User).all()

    def get_all_obs_clients(self: Dashboard) -> list[User]:
        res = self.db.session.query(OBSWebSocketClient).all()
        LOG.debug(f"Found {len(res)} OBS clients in the db!")
        return res

    def run(self: Dashboard) -> any:
        return super().run(host=self.host, port=self.port, debug=self.debug)
