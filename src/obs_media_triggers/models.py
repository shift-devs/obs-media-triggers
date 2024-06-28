from __future__ import annotations
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Sequence

MAX_VARCHAR_LEN = 64

DB = SQLAlchemy()


class OBSWSClientModel(DB.Model):
    id = Column(Integer, Sequence("obs_id", start=0, increment=1), primary_key=True)
    user_id = Column(Integer, ForeignKey("user_model.id"))
    host = Column(String(256))
    port = Column(Integer, default=4455)
    password = Column(String(256))

    @property
    def url(self: OBSWSClientModel) -> str:
        return f'ws://{self.host}:{self.port}/'

class EventModel(DB.Model):
    id = Column(Integer, Sequence('event_id', start=0, increment=1), primary_key=True)
    obs_id = Column(Integer, ForeignKey('obsws_client_model.id'))
    type = Column(String(MAX_VARCHAR_LEN))
    quantity = Column(Integer)
    allow_anon = Column(Boolean)
    src_template = Column(String(MAX_VARCHAR_LEN))


class UserModel(DB.Model, UserMixin):
    id = Column(Integer, Sequence("user_id"), primary_key=True)
    name = Column(String(MAX_VARCHAR_LEN), unique=True)
    password = Column(String(MAX_VARCHAR_LEN))
