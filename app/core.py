"""Compatibility facade for the app runtime.

Routers import from this module while the legacy runtime is being split into
smaller services.
"""

from .services.runtime import *  # noqa: F403
from .services.runtime import (
    _fetch_source,
    _fmp_ws_tasks,
    _news_cache,
    _quote_latest_by_key,
    _quote_ws_clients,
    _quotes_cache,
)
