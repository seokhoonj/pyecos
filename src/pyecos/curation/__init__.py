"""Curated indicators: named shortcuts to the Bank of Korea's headline series.

Where :meth:`~pyecos.ECOS.fetch_series` takes a raw stat code, the curation tree
takes a name: ``ecos.rate.base.fetch(...)`` instead of remembering
``"722Y001"``. Each leaf is an :class:`Indicator` carrying the table and item
codes for one series; the groups mirror the Bank of Korea's own themes.
"""

from ._indicator import Indicator, IndicatorSpec

__all__ = ["Indicator", "IndicatorSpec"]
