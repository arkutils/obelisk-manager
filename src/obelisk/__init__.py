from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version('obelisk-manager')  # must match [project].name in pyproject.toml
except PackageNotFoundError:
    __version__ = '0.0.0-dev'  # fallback for local dev
