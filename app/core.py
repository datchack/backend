"""Compatibility facade for the app runtime.

Routers import from this module while the legacy runtime is being split into
smaller services.
"""

from .services.context import *  # noqa: F403
from .services.profiles import *  # noqa: F403
from .services.calendar import *  # noqa: F403
from .services.news import *  # noqa: F403
from .services.quotes import *  # noqa: F403
from .services.accounts import *  # noqa: F403
from .services.billing import *  # noqa: F403
from .preferences import validate_preferences_payload
from .schemas import *  # noqa: F403
from .services.news import (
    _fetch_source,
    _news_cache,
)
from .services.quotes import (
    _fmp_ws_tasks,
    _quote_latest_by_key,
    _quote_ws_clients,
    _quotes_cache,
)
from .services.billing import stripe
