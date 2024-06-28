from __future__ import annotations

from typing import Union
from logging import getLogger
from ..models import UserModel
from flask_sqlalchemy import SQLAlchemy
from password_lib.utils import PasswordUtil
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, logout_user, current_user

LOG = getLogger(__name__)

DEFAULT_PASSWORD_POLICY = {
    "min_length": 9,
    "max_length": 128,
    "requires_lowercase": True,
    "requires_uppercase": True,
    "requires_special_chars": True,
    "requires_digits": True,
}


class UserManager:
    db: SQLAlchemy
    password_policy: PasswordUtil
    login_manager: LoginManager

    def __init__(
        self: UserManager,
        app: object,
        password_policy: dict = DEFAULT_PASSWORD_POLICY,
    ):
        self.db = app.db
        self.password_policy = PasswordUtil()
        for k, v in password_policy.items():
            self.password_policy.configure_strength(k=v)
        
        self.login_manager = LoginManager(app)
        self.login_manager.login_view = "view_auth.get_login"
        self.login_manager.login_message_category = "danger"
        
        @self.login_manager.user_loader
        def load_user(id: int):
            return UserModel.query.filter_by(id=id).one_or_none()

    def signup(self: UserManager, username: str, password: str, password_confirm: str):
        if self.get_user_by_name(username) is not None:
            raise RuntimeError("Username already taken!")
        elif password != password_confirm:
            raise RuntimeError("Passwords do not match!")
        elif not self.password_policy.is_secure(password):
            raise RuntimeError("Password must adhere to policy!")

        password_hash = generate_password_hash(password, method="pbkdf2:sha256:600000")
        new_user = UserModel(name=username, password=password_hash)
        self.db.session.add(new_user)
        self.db.session.commit()
        self.login(username, password_hash, remeber_user=False)

    def login(
        self: UserManager, username: str, password_hash: str, remeber_user: bool = False
    ) -> None:
        db_user: UserModel = UserModel.query.filter_by(name=username).one_or_none()
        if db_user is None:
            raise RuntimeError("username not found")
        elif not check_password_hash(db_user.password, password_hash):
            raise RuntimeError("failed password attempt")
        login_user(db_user, remember=remeber_user)
        LOG.debug(f"User {db_user.name} succesfully logged in!")

    def logout(self: UserManager) -> None:
        logout_user()

    def get_user_by_name(self: UserManager, username: str) -> Union[UserModel | None]:
        return UserModel.query.filter_by(name=username).one_or_none()
