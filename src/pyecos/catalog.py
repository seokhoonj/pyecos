"""Offline search over a bundled snapshot of the ECOS table catalog.

The hard part of using ECOS is finding the stat code you need -- and
:meth:`~pyecos.ECOS.fetch_tables` costs a network call every time. This module
ships a snapshot of the table hierarchy inside the package, so you can search it
by name or code with **no key and no network**::

    from pyecos import catalog

    for table in catalog.search("소비자물가"):
        print(table["stat_code"], table["stat_name"])   # 901Y009 소비자물가지수

    catalog.table("901Y009")   # one table's row, or None

The snapshot is a point-in-time copy (refresh it with ``tools/gen_catalog.py``);
for the live hierarchy, or a table's detail items, use ``ECOS.fetch_tables`` /
``ECOS.fetch_items``.
"""

from __future__ import annotations

import csv
import gzip
import io
from functools import cache
from importlib.resources import files

from .types import CatalogRow

_DATA = files("pyecos").joinpath("data", "catalog.tsv.gz")


@cache
def _tables() -> tuple[CatalogRow, ...]:
    text = gzip.decompress(_DATA.read_bytes()).decode("utf-8")
    return tuple(
        CatalogRow(
            stat_code=row["stat_code"],
            stat_name=row["stat_name"],
            cycle=row["cycle"],
            searchable=row["searchable"] == "Y",
        )
        for row in csv.DictReader(io.StringIO(text), delimiter="\t")
    )


def tables() -> list[CatalogRow]:
    """Every table in the bundled catalog snapshot."""
    return list(_tables())


def table(stat_code: str) -> CatalogRow | None:
    """The catalog row for ``stat_code``, or ``None`` if the snapshot lacks it."""
    return next((row for row in _tables() if row["stat_code"] == stat_code), None)


def search(query: str, *, searchable_only: bool = True) -> list[CatalogRow]:
    """Tables whose code or name contains ``query``, case-insensitively, offline.

    ``searchable_only`` (the default) keeps only tables you can actually query
    with :meth:`~pyecos.ECOS.fetch_series`, dropping the category headers that
    organize the hierarchy; pass ``False`` to search those too.
    """
    needle = query.strip().lower()
    hits = [
        row
        for row in _tables()
        if needle in row["stat_code"].lower() or needle in row["stat_name"].lower()
    ]
    if searchable_only:
        hits = [row for row in hits if row["searchable"]]
    return hits
