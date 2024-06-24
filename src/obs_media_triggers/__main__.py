"""
References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import logging
import sys
from obs_media_triggers import __dist_name__, __description__, __version__
from argparse import ArgumentParser, Namespace

LOG = logging.getLogger(__name__)


def parse_args() -> Namespace:
    """Parse command line parameters

    Args:
      args (list[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = ArgumentParser(prog=__dist_name__, description=__description__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__dist_name__} {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="log_level",
        help="set log_level to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="log_level",
        help="set log_level to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args()


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


def main():
    args = parse_args()


if __name__ == "__main__":
    main()
