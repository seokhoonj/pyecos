"""An opt-in, TTL-bounded store of prior fetch results, keyed by the logical query.

Off unless :class:`ECOS` is given a ``cache_ttl``. When on, a repeated query returns
the stored rows without a network round trip -- cutting calls so a burst stays under
the ECOS rate cap (~300 in three minutes), and repeating work for free.

The store holds *complete* results (a whole paginated, mapped series), never a single
page: a page is a partial intermediate, and caching answers rather than ingredients is
what keeps a cache honest. Entries expire after ``ttl`` seconds, so the staleness a
caller accepts is exactly the bound they chose -- a series whose latest observation has
since updated is re-fetched once its entry expires. Least-recently-used entries are
evicted past ``maxsize`` so the store cannot grow without bound.

Not thread-safe: the entries are mutable instance state with no lock, like the client
that owns it -- use one client per thread.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

# (service, resolved language, request tail) -- the logical query, minus the paging
# window and the API key, so kr and en cache apart and two clients never collide.
Key = tuple[str, str, tuple[str, ...]]

Rows = list[dict[str, Any]]

_DEFAULT_MAXSIZE = 256


class _Cache:
    """A TTL + LRU store mapping a query key to its rows."""

    def __init__(self, *, ttl: float, maxsize: int = _DEFAULT_MAXSIZE) -> None:
        self._ttl = ttl
        self._maxsize = maxsize
        self._entries: OrderedDict[Key, tuple[float, Rows]] = OrderedDict()

    def get(self, key: Key) -> Rows | None:
        """The cached rows for ``key`` if present and unexpired, else ``None``.

        Returns a shallow copy so a caller mutating the list cannot corrupt the
        entry; the row dicts are shared, so treat them as read-only.
        """
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, rows = entry
        if time.monotonic() >= expires_at:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)  # mark most-recently-used
        return list(rows)

    def set(self, key: Key, rows: Rows) -> None:
        """Store a shallow copy of ``rows`` under ``key``, evicting LRU past maxsize."""
        self._entries[key] = (time.monotonic() + self._ttl, list(rows))
        self._entries.move_to_end(key)
        while len(self._entries) > self._maxsize:
            self._entries.popitem(last=False)  # drop the least-recently-used

    def clear(self) -> None:
        """Drop every entry."""
        self._entries.clear()
