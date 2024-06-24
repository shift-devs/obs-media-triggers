import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    __dist_name__ = "obs-media-triggers"
    __description__ = 'A webapp for controlling custom media locally in OBS.'
    __version__ = version(__dist_name__)
    __author__ = "the-ivo-robotnic"
    __copyright__ = "the-ivo-robotnic"
    __license__ = "MIT"
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError