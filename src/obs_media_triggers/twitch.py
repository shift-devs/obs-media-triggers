from __future__ import annotations

from logging import Logger, getLogger

from urllib.parse import ParseResult, urljoin
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.type import AuthScope, TwitchAuthorizationException
from twitchAPI.object.eventsub import ChannelSubscriptionGiftEvent


class TwitchWrapper:
    api: Twitch = None
    bot: TwitchUser = None
    esws: EventSubWebhook = None
    LOG: Logger = getLogger(__name__)

    # TODO: Add back `AuthScope.CHANNEL_READ_SUBSCRIPTIONS`
    @staticmethod
    def scopes() -> [AuthScope]:
        return [AuthScope.USER_READ_SUBSCRIPTIONS]

    @classmethod
    async def build(
        self: TwitchWrapper,
        twt_app_id: str,
        twt_app_secret: str,
        twt_app_url: ParseResult,
        twt_bot_id: str,
        esws_confirm: bool = True,
        esws_timeout: int = 3,
    ) -> bool:
        # Setup Twitch Client
        self.LOG.info(f"Connecting to Twitch API at -> {twt_app_url.geturl()}")
        try:
            # Create and configure Twitch API Client
            self.api = await Twitch(
                twt_app_id,
                twt_app_secret,
                base_url=f"{twt_app_url.geturl()}mock/",
                auth_base_url=f"{twt_app_url.geturl()}auth/",
            )
            self.api.auto_refresh_auth = True

            # Authenticate Twitch Bot
            auth = UserAuthenticationStorageHelper(self.api, [AuthScope.CHANNEL_READ_SUBSCRIPTIONS])
            await auth.bind()
            self.bot: TwitchUser = await first(self.api.get_users())

            # Create and configure the EventSub APi Client
            self.esws: EventSubWebhook = EventSubWebhook(
                "localhost", 17563, api=self.api
            )
            self.esws.wait_for_subscription_confirm = esws_confirm
            self.esws.wait_for_subscription_confirm_timeout = esws_timeout

            return True
        except TwitchAuthorizationException as e:
            self.LOG.error(f"Failed to login: {e}")
            return False

    async def init_eventsub_subscriptions(self: TwitchWrapper):
        # Start the EventSub Websocket Client
        self.esws.start()

        # Unsubscribe and Resubscribe to all the things
        await self.esws.unsubscribe_all()
        await self.esws.listen_channel_subscription_gift(self.bot.id, self.on_subscribe)

    async def on_subscribe(self, data: ChannelSubscriptionGiftEvent) -> None:
        e = data.event  # Truncate the event object
        self.LOG.info(f"{e.user_name} gifted {e.total} {e.total}x {e.tier} subs!")
