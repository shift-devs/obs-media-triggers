from __future__ import annotations
import random, string
from .auth import auth, PSUT
from flask import Flask
from .views import views
from .models import DB, User
from logging import getLogger
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

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
        self.host = host
        self.port = port

        # Configure Flask app
        self.config["SECRET_KEY"] = secret_key
        self.config["SQLALCHEMY_DATABASE_URI"] = db_uri

        # Register endpoints
        self.register_blueprint(views, url_prefix="/")
        self.register_blueprint(auth, url_prefix="/auth/")

        # Setup login manager
        self.login_manager = LoginManager(self)
        self.login_manager.login_view = "auth.get_login"

        @self.login_manager.user_loader
        def load_user(username: str):
            return User.query.filter_by(name=username).one_or_none()

        # Map callable functions
        self.jinja_env.globals.update(get_all_users=self.get_all_users)
        self.jinja_env.globals.update(password_strength_reqs=PSUT)

        with self.app_context():
            DB.init_app(self)
            DB.create_all()

    def get_all_users(self: Dashboard) -> list[User]:
        res = DB.session.query(User).all()
        LOG.info(res)
        return res

    def run(self: Dashboard) -> any:
        return super().run(host=self.host, port=self.port, debug=self.debug)
