"""The ``ECOS`` client -- the one public handle to the Bank of Korea Open API.

One object holds the API key, the response language, and a pooled HTTP
connection; its six methods mirror the six ECOS services one-to-one. Every
method takes named arguments and returns a list of dict rows -- the vendor's
fifteen-segment path order lives entirely in ``_transport`` and never surfaces
here.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, cast

import httpx

from . import _parse
from ._cache import _Cache
from ._config import resolve_api_key
from ._transport import _Transport
from .curation._generated import _CurationGroups
from .types import (
    Cycle,
    ItemRow,
    KeyStatRow,
    Language,
    MetaRow,
    StatRow,
    TableRow,
    WordRow,
)

_DEFAULT_TIMEOUT = 30.0


class ECOS(_CurationGroups):
    """A client for the Bank of Korea ECOS (Economic Statistics System) API.

    Construct it with an API key, or leave it out to resolve one from the
    ``ECOS_API_KEY`` environment variable or ``~/.config/pyecos/credentials.json``::

        with ECOS() as ecos:
            rows = ecos.fetch_series("722Y001", cycle="M",
                                   start="202001", end="202412")

    For the Bank's headline series you need not remember a stat code: the client
    carries a tree of curated indicators grouped by theme, so the call above is
    also ``ecos.rate.base.fetch(start="202001", end="202412")``, and a
    two-dimensional series reads ``ecos.trade.exports.semiconductor.value.fetch()``.

    The client owns a pooled HTTP connection, so reuse one instance across calls
    and close it when done -- as a context manager, or via :meth:`close`. Set
    ``delay_seconds`` to space out requests when fetching in bulk, so a burst stays
    under the ECOS rate cap (~300 calls in three minutes); 0.6s keeps one client
    under it indefinitely. ``cache_ttl`` (off by default) turns on an in-memory cache:
    a repeated query returns the stored rows for that many seconds without a network
    call -- the staleness a caller accepts is exactly the bound they set.

    Construction raises :class:`ECOSConfigError` if no API key can be resolved, and
    ``ValueError`` for an unknown ``lang`` or a non-positive ``cache_ttl``. Every
    service method then raises from the :class:`ECOSError` family:
    :class:`ECOSAuthError` if the key is rejected, :class:`ECOSRateLimitError` if
    ECOS is rate-limiting the key, :class:`ECOSResponseError` on any other vendor
    error, and :class:`ECOSNetworkError` if the request never completes (a transient
    timeout or 5xx is retried with backoff first). A query that simply matches no
    data returns an empty list, not an error.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        lang: Language | str = Language.KOREAN,
        timeout: float = _DEFAULT_TIMEOUT,
        delay_seconds: float = 0.0,
        cache_ttl: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if cache_ttl is not None and cache_ttl <= 0:
            raise ValueError(f"cache_ttl must be positive seconds, got {cache_ttl}")
        self._api_key = resolve_api_key(api_key)
        self._lang = Language(lang)
        self._client = httpx.Client(timeout=timeout, transport=transport)
        self._transport = _Transport(self._client, delay_seconds=delay_seconds)
        self._cache = _Cache(ttl=cache_ttl) if cache_ttl is not None else None
        self._series_client = self  # groups build lazily off this (see _CurationGroups)

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def clear_cache(self) -> None:
        """Drop any cached results, forcing the next query to refetch.

        Rarely needed -- the cache expires and evicts itself (see ``cache_ttl``); this
        is the escape hatch for forcing fresh data before an entry's TTL is up. A
        no-op when caching is off.
        """
        if self._cache is not None:
            self._cache.clear()

    def __enter__(self) -> ECOS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        # Deliberately never shows the API key.
        return f"ECOS(lang={self._lang.value!r})"

    # -- services ----------------------------------------------------------

    def fetch_series(
        self,
        stat_code: str,
        *,
        cycle: Cycle | str = Cycle.MONTHLY,
        start: str | None = None,
        end: str | None = None,
        item_code1: str | None = None,
        item_code2: str | None = None,
        item_code3: str | None = None,
        item_code4: str | None = None,
        lang: Language | str | None = None,
    ) -> list[StatRow]:
        """Fetch a statistic's observations (service StatisticSearch).

        ``start`` and ``end`` are cycle-formatted period bounds (``"202401"``
        for a monthly series, ``"2024"`` for annual -- see :class:`Cycle`). The
        four ``item_code`` slots select a series within the table; most tables
        use only ``item_code1``. Every matching observation is returned, paging
        past the vendor's per-request limit transparently.
        """
        tail = [
            stat_code,
            str(Cycle(cycle)),
            start or "",
            end or "",
            item_code1 or "",
            item_code2 or "",
            item_code3 or "",
            item_code4 or "",
        ]
        return cast("list[StatRow]", self._collect("StatisticSearch", tail, lang))

    def fetch_tables(
        self,
        *,
        stat_code: str | None = None,
        lang: Language | str | None = None,
    ) -> list[TableRow]:
        """List statistical tables (service StatisticTableList).

        With no ``stat_code``, returns the top-level tables; with one, returns
        that table's children.
        """
        tail = [stat_code] if stat_code else []
        return cast("list[TableRow]", self._collect("StatisticTableList", tail, lang))

    def fetch_items(
        self,
        stat_code: str,
        *,
        lang: Language | str | None = None,
    ) -> list[ItemRow]:
        """List a table's detail items (service StatisticItemList)."""
        rows = self._collect("StatisticItemList", [stat_code], lang)
        return cast("list[ItemRow]", rows)

    def fetch_key_statistics(
        self,
        *,
        lang: Language | str | None = None,
    ) -> list[KeyStatRow]:
        """Fetch the top-100 headline indicators (service KeyStatisticList)."""
        return cast("list[KeyStatRow]", self._collect("KeyStatisticList", [], lang))

    def fetch_glossary(
        self,
        word: str,
        *,
        lang: Language | str | None = None,
    ) -> list[WordRow]:
        """Look up a statistical term (service StatisticWord)."""
        return cast("list[WordRow]", self._collect("StatisticWord", [word], lang))

    def fetch_meta(
        self,
        dataset_name: str,
        *,
        lang: Language | str | None = None,
    ) -> list[MetaRow]:
        """Fetch a meta-DB dataset by name (service StatisticMeta)."""
        rows = self._collect("StatisticMeta", [dataset_name], lang)
        return cast("list[MetaRow]", rows)

    # -- internals ---------------------------------------------------------

    def _collect(
        self,
        service: str,
        tail: list[str],
        lang: Language | str | None,
    ) -> list[dict[str, Any]]:
        resolved_lang = self._resolve_lang(lang)
        key = (service, resolved_lang, tuple(tail))
        if self._cache is not None:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
        rows = _parse.collect(
            self._transport,
            service=service,
            api_key=self._api_key,
            lang=resolved_lang,
            tail=tail,
        )
        if self._cache is not None:
            self._cache.set(key, rows)
        return rows

    def _resolve_lang(self, lang: Language | str | None) -> str:
        return self._lang.value if lang is None else Language(lang).value
