from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

MAX_VARCHAR_LEN = 64

DB = SQLAlchemy()

class TwitchOAuthClient(DB.Model):
    username = Column(Integer, ForeignKey("user.name"), primary_key=True)
    access_token = Column(String(256), unique=True)
    refresh_token = Column(String(256), unique=True)
    expiration = Column(DateTime(timezone=True), default=func.now())


class OBSWebSocketClient(DB.Model):
    username = Column(Integer, ForeignKey("user.name"))
    host = Column(String(256), primary_key=True)
    port = Column(Integer, default=4455, primary_key=True)
    password = Column(String(256))

    def get_id(self, host, port) -> str:
        return f"ws://{host}:{port}/"


class User(DB.Model, UserMixin):
    name = Column(String(MAX_VARCHAR_LEN), primary_key=True)
    password = Column(String(MAX_VARCHAR_LEN))
    first_name = Column(String(MAX_VARCHAR_LEN))
    last_name = Column(String(MAX_VARCHAR_LEN))

    def get_id(self) -> str:
        return self.name
