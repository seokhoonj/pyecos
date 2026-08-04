"""Refresh the bundled table catalog at src/pyecos/data/catalog.tsv.gz.

Walks the ECOS table hierarchy (StatisticTableList) once -- descending into every
category and recording every table -- and writes a gzipped snapshot the package
ships so ``pyecos.catalog`` can search offline. Needs a valid ECOS API key and a
network; paced to stay under the rate cap.

Run:  uv run python tools/gen_catalog.py
"""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

from pyecos import ECOS

_ROOT = Path(__file__).resolve().parent.parent
_OUT = _ROOT / "src" / "pyecos" / "data" / "catalog.tsv.gz"
_COLUMNS = ("stat_code", "stat_name", "cycle", "searchable")


def _walk(ecos: ECOS) -> dict[str, dict[str, str]]:
    """Every table in the hierarchy, keyed by stat_code (categories descended into)."""
    found: dict[str, dict[str, str]] = {}
    pending: list[str | None] = [None]  # None = the top level
    while pending:
        parent = pending.pop()
        rows = ecos.fetch_tables(stat_code=parent) if parent else ecos.fetch_tables()
        for row in rows:
            code = row.get("stat_code", "")
            if not code or code in found:
                continue
            searchable = row.get("searchable", "")
            found[code] = {
                "stat_code": code,
                "stat_name": row.get("stat_name", ""),
                "cycle": row.get("cycle", ""),
                "searchable": searchable,
            }
            if searchable != "Y":  # a category -- descend for its children
                pending.append(code)
    return found


def main() -> None:
    with ECOS(delay_seconds=0.4) as ecos:  # pace under the ECOS rate cap
        tables = _walk(ecos)
    ordered = sorted(tables.values(), key=lambda row: row["stat_code"])
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(_OUT, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerows(ordered)
    searchable = sum(1 for row in ordered if row["searchable"] == "Y")
    print(f"wrote {_OUT.name} -- {len(ordered)} tables ({searchable} searchable)")


if __name__ == "__main__":
    main()
