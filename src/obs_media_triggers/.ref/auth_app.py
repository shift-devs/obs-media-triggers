from __future__ import annotations
from flask import Flask, redirect, request
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch


class AuthApp(Flask):
    __host: str = "localhost"
    __port: int = 17563
    __twitch: Twitch = None
    auth: UserAuthenticator = None

    def __init__(
        self: AuthApp,
        host: str = "0.0.0.0",
        port: int = 17563,
        twitch: Twitch = None,
        auth: UserAuthenticator = None,
    ):
        super().__init__(__name__)
        # Dependency Injections
        self.__host = host
        self.__port = port
        self.__twitch = twitch
        self.auth = auth

        # API Endpoint Rules
        self.add_url_rule("/", view_func=self.home)
        self.add_url_rule("/login", view_func=self.login)
        self.add_url_rule("/login/confirm", view_func=self.login_confirm)

    def start(self: AuthApp, debug: bool = False):
        self.run(host=self.__host, port=self.__port, debug=debug)

    def twitch_is_disconnected(self: AuthApp) -> bool:
        return (self.__twitch is None) or (self.auth is None)

    def home(self: AuthApp):
        if self.twitch_is_disconnected():
            return {"error": "Application was not connected to twitch"}, 500
        return redirect(self.auth.return_auth_url()), 301

    def login(self: AuthApp):
        if self.twitch_is_disconnected():
            return {"error": "Application was not connected to twitch"}, 500
        return redirect(self.auth.return_auth_url())

    async def login_confirm(self: AuthApp):
        if self.twitch_is_disconnected():
            return {"error": "Application was not connected to twitch"}, 500

        state = request.args.get("state")
        code = request.args.get("code")

        if code is None:
            return {"error": "Missing code"}, 400
        try:
            token, refresh = await self.auth.authenticate(user_token=code)
            await self.__twitch.set_user_authentication(token, self.auth.scopes, refresh)
        except TwitchAPIException as e:
            return {"error": "Failed to generate auth token"}, 400
        return {"message": "Sucessfully authenticated!"}, 200
