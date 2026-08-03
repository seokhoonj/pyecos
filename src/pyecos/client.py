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
from ._config import resolve_api_key
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


class ECOS:
    """A client for the Bank of Korea ECOS (Economic Statistics System) API.

    Construct it with an API key, or leave it out to resolve one from the
    ``ECOS_API_KEY`` environment variable or ``~/.config/pyecos/credentials.json``::

        with ECOS() as ecos:
            rows = ecos.get_series("722Y001", cycle="M",
                                   start="202001", end="202412")

    The client owns a pooled HTTP connection, so reuse one instance across calls
    and close it when done -- as a context manager, or via :meth:`close`.

    Every service method raises from the :class:`ECOSError` family:
    :class:`ECOSAuthError` if the key is rejected, :class:`ECOSResponseError` on a
    vendor error, and :class:`ECOSNetworkError` if the request never completes. A
    query that simply matches no data returns an empty list, not an error.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        lang: Language | str = Language.KOREAN,
        timeout: float = _DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = resolve_api_key(api_key)
        self._lang = Language(lang)
        self._client = httpx.Client(timeout=timeout, transport=transport)

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

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

    def get_series(
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

    def get_tables(
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

    def get_items(
        self,
        stat_code: str,
        *,
        lang: Language | str | None = None,
    ) -> list[ItemRow]:
        """List a table's detail items (service StatisticItemList)."""
        rows = self._collect("StatisticItemList", [stat_code], lang)
        return cast("list[ItemRow]", rows)

    def get_key_statistics(
        self,
        *,
        lang: Language | str | None = None,
    ) -> list[KeyStatRow]:
        """Fetch the top-100 headline indicators (service KeyStatisticList)."""
        return cast("list[KeyStatRow]", self._collect("KeyStatisticList", [], lang))

    def get_glossary(
        self,
        word: str,
        *,
        lang: Language | str | None = None,
    ) -> list[WordRow]:
        """Look up a statistical term (service StatisticWord)."""
        return cast("list[WordRow]", self._collect("StatisticWord", [word], lang))

    def get_meta(
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
        return _parse.collect(
            self._client,
            service=service,
            api_key=self._api_key,
            lang=self._resolve_lang(lang),
            tail=tail,
        )

    def _resolve_lang(self, lang: Language | str | None) -> str:
        return self._lang.value if lang is None else Language(lang).value
