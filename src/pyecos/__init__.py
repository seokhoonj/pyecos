"""pyecos -- a Python client for the Bank of Korea ECOS Open API."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from . import catalog
from .client import ECOS
from .curation import Indicator, IndicatorSpec
from .exceptions import (
    ECOSAuthError,
    ECOSConfigError,
    ECOSError,
    ECOSNetworkError,
    ECOSRateLimitError,
    ECOSResponseError,
)
from .types import (
    CatalogRow,
    Cycle,
    ItemRow,
    KeyStatRow,
    Language,
    MetaRow,
    StatRow,
    TableRow,
    WordRow,
)

try:
    __version__ = version("pyecos")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0"

__all__ = [
    "ECOS",
    "catalog",
    "Indicator",
    "IndicatorSpec",
    "Cycle",
    "Language",
    "StatRow",
    "CatalogRow",
    "TableRow",
    "ItemRow",
    "KeyStatRow",
    "WordRow",
    "MetaRow",
    "ECOSError",
    "ECOSConfigError",
    "ECOSAuthError",
    "ECOSResponseError",
    "ECOSRateLimitError",
    "ECOSNetworkError",
    "__version__",
]
