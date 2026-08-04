"""The curated-indicator objects: a static spec plus a client-bound accessor.

An :class:`IndicatorSpec` is the frozen description of one Bank of Korea series
-- which table, which item codes, which frequency. An :class:`Indicator` pairs
that spec with a live client, so ``.fetch()`` returns observations. The specs
are generated from the curation worksheet into ``_generated.py``; the two
classes here are hand-written and shared by every generated namespace.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol, assert_never

from ..types import Cycle, Language, StatRow


class _SeriesClient(Protocol):
    """The single client capability an :class:`Indicator` needs.

    Kept minimal so the curation tree depends on a behavior, not on the concrete
    :class:`~pyecos.ECOS` class -- which would be a circular import, since ``ECOS``
    exposes the tree.
    """

    def fetch_series(
        self,
        stat_code: str,
        *,
        cycle: Cycle | str = ...,
        start: str | None = ...,
        end: str | None = ...,
        item_code1: str | None = ...,
        item_code2: str | None = ...,
        item_code3: str | None = ...,
        item_code4: str | None = ...,
        lang: Language | str | None = ...,
    ) -> list[StatRow]: ...


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    """Static definition of one curated indicator -- no client, no I/O.

    ``path`` is the dotted accessor under the client
    (``"trade.exports.semiconductor.value"``); ``stat_code`` and the ``item_code``
    slots identify the series inside ECOS. Most indicators use only ``item_code1``;
    two- and three-dimensional tables (a metric within an industry within a size
    class) fill ``item_code2`` and ``item_code3`` as well. No curated series needs
    a fourth item code, so the spec deliberately stops at three.
    """

    path: str
    name_ko: str
    name_en: str
    stat_code: str
    cycle: Cycle
    item_code1: str | None = None
    item_code2: str | None = None
    item_code3: str | None = None


class Indicator:
    """A curated indicator bound to a client; call :meth:`fetch` for its series.

    Reached by walking the curation tree on a client -- ``ecos.rate.base`` or
    ``ecos.trade.exports.semiconductor.value``. The :class:`IndicatorSpec` it
    carries names the table and item codes; :meth:`fetch` forwards them to
    :meth:`~pyecos.ECOS.fetch_series`, so the caller never handles a stat code.
    """

    __slots__ = ("_client", "spec")

    _client: _SeriesClient
    spec: IndicatorSpec

    def __init__(self, client: _SeriesClient, spec: IndicatorSpec) -> None:
        self._client = client
        self.spec = spec

    def fetch(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        lang: Language | str | None = None,
    ) -> list[StatRow]:
        """Fetch this indicator's observations over ``[start, end]``.

        ``start`` and ``end`` are cycle-formatted period bounds (``"202401"`` for
        a monthly series, ``"2024"`` for annual -- see :class:`Cycle`). Leaving
        them out fetches the series' entire available range.
        """
        spec = self.spec
        return self._client.fetch_series(
            spec.stat_code,
            cycle=spec.cycle,
            start=start,
            end=end,
            item_code1=spec.item_code1,
            item_code2=spec.item_code2,
            item_code3=spec.item_code3,
            lang=lang,
        )

    def latest(
        self,
        *,
        today: date | None = None,
        lang: Language | str | None = None,
    ) -> StatRow | None:
        """Return the most recent observation in a recent window, or ``None``.

        Fetches a window sized to the indicator's frequency (roughly the last few
        years, ending at ``today`` -- the current date unless one is given) and
        returns the observation with the greatest ``time``, so a one-liner never
        pulls the whole history and never relies on the vendor's row order. A
        series with no observation in that window -- including a discontinued one
        whose last point predates it -- yields ``None``; that is distinct from an
        empty overall series only in how far back the window reaches, so widen the
        frequency window (or call :meth:`fetch`) if a very stale series matters.
        """
        start, end = _recent_window(self.spec.cycle, today or date.today())
        fetched = self.fetch(start=start, end=end, lang=lang)
        rows = [row for row in fetched if row.get("time")]
        if not rows:
            return None
        return max(rows, key=lambda row: row["time"])

    def __repr__(self) -> str:
        return f"Indicator(path={self.spec.path!r}, name={self.spec.name_en!r})"


def _recent_window(cycle: Cycle, today: date) -> tuple[str, str]:
    """A cycle-formatted ``(start, end)`` covering roughly the last few years."""
    year = today.year
    match cycle:
        case Cycle.ANNUAL:
            return str(year - 3), str(year)
        case Cycle.SEMIANNUAL:
            return f"{year - 3}S1", f"{year}S2"
        case Cycle.QUARTERLY:
            return f"{year - 2}Q1", f"{year}Q4"
        case Cycle.MONTHLY:
            return f"{year - 2}01", f"{year}12"
        case Cycle.SEMIMONTHLY:
            return f"{year - 1}01S1", f"{year}12S2"
        case Cycle.DAILY:
            # Wide enough to clear weekends, holidays, and any short publication
            # gap so the last observation is always inside the window.
            start = today - timedelta(days=400)
            return start.strftime("%Y%m%d"), today.strftime("%Y%m%d")
    assert_never(cycle)
