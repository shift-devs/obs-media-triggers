from __future__ import annotations

from logging import getLogger
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, URL, Boolean, ForeignKey, Sequence

MAX_VARCHAR_LEN = 255

DB = SQLAlchemy()
LOG= getLogger(__name__)

class OBSWSClientModel(DB.Model):
    __tablename__ = "obs_clients"

    id = Column(Integer, Sequence("obs_id", start=0, increment=1), primary_key=True)
    host = Column(String(MAX_VARCHAR_LEN), default="localhost")
    port = Column(Integer, default=4455)
    password = Column(String(MAX_VARCHAR_LEN))

    @property
    def url(self: OBSWSClientModel) -> str:
        return f"ws://{self.host}:{self.port}/"


class EventModel(DB.Model):
    __tablename__ = "events"

    id = Column(Integer, Sequence("event_id", start=0, increment=1), primary_key=True)
    obs_id = Column(Integer, ForeignKey("obs_clients.id"))
    type = Column(String(MAX_VARCHAR_LEN))
    quantity = Column(Integer)
    allow_anon = Column(Boolean)
    src_template = Column(String(MAX_VARCHAR_LEN))


class TwitchOAuthUserModel(DB.Model, UserMixin):
    __tablename__ = "twitch_users"
    
    id = Column(String(255), primary_key=True)
    login_name = Column(String(MAX_VARCHAR_LEN), nullable=False)
    display_name = Column(String(MAX_VARCHAR_LEN), nullable=False)
    pfp_url = Column(String(MAX_VARCHAR_LEN), nullable=False)
    user_token = Column(String(MAX_VARCHAR_LEN), nullable=False)

    def to_dict(self: TwitchOAuthUserModel) -> dict:
        data = {
            'id': self.id,
            'login_name': self.login_name,
            'display_name': self.display_name,
            'pfp_url': self.pfp_url,
            'user_token': self.user_token,
        }
        LOG.debug(f'Converted DB entry to dict: {data}')
        return data
