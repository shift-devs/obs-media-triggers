"""
References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import os
import sys
import time
import logging
import asyncio
import argparse
import threading
from pathlib import Path
from urllib.parse import ParseResult, urlparse
from obsws_python import ReqClient
from obsws_python.error import OBSSDKRequestError

from . import __version__
from .twitch import TwitchWrapper

LOG = logging.getLogger(__name__)


def assert_env_var(env_name: str) -> any:
    env_value = os.getenv(env_name)
    if env_value is None:
        raise RuntimeError(
            f"Expected environment variable `{env_name}` but was undefined!"
        )
    return env_value


def parse_args():
    """Parse command line parameters

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Environment Variable Args
    app_id = assert_env_var("OMT_CLIENT_ID")
    app_secret = assert_env_var("OMT_CLIENT_SECRET")
    app_url = assert_env_var("OMT_APP_URL")

    # Command Line Args
    parser = argparse.ArgumentParser(description="Twitch Event Listener")
    parser.add_argument(
        "--version",
        action="version",
        version=f"obs-media-triggers {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log_level",
        metavar="Log Level",
        help="set log level to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="log_level",
        metavar="Log Level",
        help="set log level to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "-H",
        "--obs-ws-host",
        dest="obs_ws_host",
        metavar="OBS Websocket Host",
        type=str,
        default="localhost",
    )
    parser.add_argument(
        "-P",
        "--obs-ws-port",
        dest="obs_ws_port",
        metavar="OBS Websocket Port",
        type=int,
        default=4455,
    )
    parser.add_argument(
        "--obs-ws-passwd",
        dest="obs_ws_passwd",
        metavar="OBS WebSocket Password",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--twitch-app-id",
        dest="twt_app_id",
        metavar="Twitch Bot App ID",
        type=str,
        default=app_id,
    )
    parser.add_argument(
        "--twitch-app-secret",
        dest="twt_app_secret",
        metavar="Twitch Bot App Secret",
        type=str,
        default=app_secret,
    )
    parser.add_argument(
        "--twitch-app-url",
        dest="twt_app_url",
        metavar="Twitch Bot App URL",
        type=str,
        default=app_url,
    )
    args: argparse.Namespace = parser.parse_args()
    args.twt_app_url = urlparse(args.twt_app_url)
    return args


def add_thanos(
    obs: ReqClient, source_id: int, media_path: Path = Path("~/Downloads/thanos.mp4")
) -> None:
    try:
        scene_name = "Scene"
        iname = f"thanos_funny_{source_id}"
        settings = {
            "is_local_file": True,
            "looping": False,
            "local_file": media_path.absolute(),
        }
        md_src = obs.create_input("Scene", iname, "ffmpeg_source", settings, True)
        item_id = obs.get_scene_item_id(scene_name, iname)
        md_filter = obs.create_source_filter(
            iname, "chroma", "chroma_key_filter_v2", {}
        )
        time.sleep(10)
        obs.remove_input(iname)
    except OBSSDKRequestError as e:
        LOG.error(e)


def setup_logging(log_level):
    """Setup basic logging

    Args:
      log_level (int): minimum log_level for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def main():
    args = parse_args()
    setup_logging(args.log_level)
    bot_username = "53100947"

    # Setup Twitch Connection
    twitch = TwitchWrapper()
    success: bool = await twitch.build(
        args.twt_app_id, args.twt_app_secret, args.twt_app_url, bot_username
    )
    if not success:
        LOG.warn(
            "Could not create the Twitch Bot... The Bot will gracefully exit now..."
        )
        return

    # Setup OBS WS connection
    obs_client: ReqClient = ReqClient(
        host=args.obs_ws_host,
        port=args.obs_ws_port,
        password=args.obs_ws_passwd,
        timeout=1,
    )

    input_types: [str] = obs_client.get_input_kind_list(True)
    LOG.debug(f"Got types of input: {input_types}")

    input_settings: dict = {
        "Local File": True,
    }

    for i in range(100):
        threading.Thread(target=add_thanos, args=(obs_client, i), daemon=False).start()
        time.sleep(0.5)

    # import ipdb; ipdb.set_trace()


if __name__ == "__main__":
    asyncio.run(main())
