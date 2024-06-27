import sys

__dist_name__ = "obs-media-triggers"
__description__ = "A web app for controlling local media in OBS."
__author__ = "Ivo Robotnic"
__copyright__ = __author__
__license__ = "MIT"

__app_host__ = 'localhost'
__app_port__ = 7064

if sys.version_info[:2] >= (3, 8):
    from importlib.metadata import PackageNotFoundError, version
else:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version(__dist_name__)
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError