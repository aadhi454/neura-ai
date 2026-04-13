"""Compatibility entrypoint for running the backend directly."""

try:
    from .app.main import app
except ImportError:  # pragma: no cover
    from app.main import app

