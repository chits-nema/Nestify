from __future__ import annotations

from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings.

    By default values are read from environment variables, but the app can
    also set them programmatically via :func:`set_use_mock`.
    """

    HEATMAP_USE_MOCK: bool = False


# module-level singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def set_use_mock(value: bool) -> None:
    """Programmatically override the mock mode at runtime.

    Call this from your application startup code to force live calls without
    relying on environment variables.
    """
    s = get_settings()
    # pydantic BaseSettings is immutable by default, but we can set attribute
    # on the instance for runtime override.
    setattr(s, "HEATMAP_USE_MOCK", bool(value))
