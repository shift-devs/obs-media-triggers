from argparse import ArgumentParser, Namespace
from . import __dist_name__, __description__, __version__, __app_host__, __app_port__
from .dashboard import Dashboard
from logging import getLogger, basicConfig, ERROR, INFO, NOTSET

LOG = getLogger(__name__)


def parse_args() -> Namespace:
    """Parse command line parameters

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
        metavar="Log Level",
        action="store_const",
        const=INFO,
        help="Set log level to WARN.",
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="log_level",
        metavar="Log Level",
        action="store_const",
        const=NOTSET,
        help="Set log level to DEBUG.",
    )
    parser.add_argument(
        "-H",
        "--host",
        dest="dashboard_host",
        metavar="Dashboard Host",
        type=str,
        default=__app_host__,
        help="Host for the dashboard web application. (Default: localhost)",
    )
    parser.add_argument(
        "-P",
        "--port",
        dest="dashboard_port",
        metavar="Dashboard Port",
        type=int,
        default=__app_port__,
        help="Port for the dashboard web application. (Default: 7064)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    log_level = ERROR if (args.log_level is None) else args.log_level
    debug = log_level == NOTSET
    basicConfig(level=log_level)

    app = Dashboard(args.dashboard_host, args.dashboard_port, debug=debug)
    app.run()


if __name__ == "__main__":
    main()
