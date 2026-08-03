"""Turn ECOS's paged, upper-cased rows into a full list of snake_cased dicts.

Two jobs live here, both above a single wire request (``_transport``):

* **paginate** -- ECOS caps a response at :data:`PAGE_SIZE` rows, so walk the
  ``start_row``/``end_row`` window until ``list_total_count`` is exhausted and
  return every row, never a first page silently mistaken for the whole answer.
* **map** -- rename the vendor's ``UPPER_CASE`` keys to the snake_case fields the
  ``TypedDict``s document, and parse the one genuinely numeric field
  (``DATA_VALUE``) to ``float``. Every key the vendor sends is kept; an
  unrecognized one simply lowercases and passes through.
"""

from __future__ import annotations

from typing import Any

import httpx

from ._transport import PAGE_SIZE, request_page

# Vendor keys whose snake_case is not a plain lowercase of the original.
_FIELD_BY_VENDOR_KEY = {
    "P_STAT_CODE":  "parent_stat_code",
    "P_ITEM_CODE":  "parent_item_code",
    "P_ITEM_NAME":  "parent_item_name",
    "GRP_CODE":     "group_code",
    "GRP_NAME":     "group_name",
    "ORG_NAME":     "org_name",
    "SRCH_YN":      "searchable",
    "WGT":          "weight",
    "DATA_CNT":     "data_count",
    "DATA_VALUE":   "data_value",
    "KEYSTAT_NAME": "keystat_name",
    "CLASS_NAME":   "class_name",
    "LVL":          "level",
    "P_CONT_CODE":  "parent_content_code",
    "CONT_CODE":    "content_code",
    "CONT_NAME":    "content_name",
}


def collect(
    client: httpx.Client,
    *,
    service: str,
    api_key: str,
    lang: str,
    tail: list[str],
) -> list[dict[str, Any]]:
    """Fetch every page of a service call and return the mapped rows."""
    return [_map_row(row) for row in _paginate(
        client, service=service, api_key=api_key, lang=lang, tail=tail,
    )]


def _paginate(
    client: httpx.Client,
    *,
    service: str,
    api_key: str,
    lang: str,
    tail: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start_row = 1
    while True:
        page = request_page(
            client,
            service=service,
            api_key=api_key,
            lang=lang,
            start_row=start_row,
            end_row=start_row + PAGE_SIZE - 1,
            tail=tail,
        )
        batch = page.get("row") or []
        rows.extend(batch)
        try:
            total = int(page.get("list_total_count") or 0)
        except (TypeError, ValueError):
            # A garbage total must not crash the loop; the empty-batch guard ends it.
            total = len(rows)
        if not batch or len(rows) >= total:
            return rows
        start_row += PAGE_SIZE


def _map_row(raw: dict[str, Any]) -> dict[str, Any]:
    row = {_FIELD_BY_VENDOR_KEY.get(key, key.lower()): value
           for key, value in raw.items()}
    if "data_value" in row:
        row["data_value"] = _to_float(row["data_value"])
    return row


def _to_float(text: Any) -> float | None:
    # ECOS marks a missing observation with an empty string or a lone dash.
    if text in (None, "", "-"):
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None
