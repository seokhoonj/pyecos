"""Row shapes and enumerations for the ECOS Open API.

Rows come back as plain dicts (``TypedDict``) so a caller can turn them into a
DataFrame in one line -- ``pd.DataFrame(rows)`` -- without this package ever
importing pandas. Each ``TypedDict`` documents the fields ECOS is known to
return; it is ``total=False`` because ECOS omits fields that do not apply to a
given statistic, and the response parser passes through *every* key the vendor
sends, so a field new to the API still arrives in the dict even before it is
declared here.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class Cycle(StrEnum):
    """Observation frequency of a statistic -- the ECOS ``cycle`` code.

    The value is the code ECOS expects in a request; the member name is its
    English meaning. A bare string (``"M"``) is accepted anywhere a ``Cycle`` is,
    because ``StrEnum`` members compare equal to their value.

    The ``time`` field of a returned row is formatted to match the cycle:
    ``"2024"`` for annual, ``"2024S1"`` semiannual, ``"2024Q1"`` quarterly,
    ``"202401"`` monthly, ``"202401S1"`` semimonthly, ``"20240115"`` daily.
    """

    ANNUAL      = "A"
    SEMIANNUAL  = "S"
    QUARTERLY   = "Q"
    MONTHLY     = "M"
    SEMIMONTHLY = "SM"
    DAILY       = "D"


class Language(StrEnum):
    """Response language for the names and labels ECOS returns."""

    KOREAN  = "kr"
    ENGLISH = "en"


class StatRow(TypedDict, total=False):
    """One observation from :meth:`ECOS.get_series` (service StatisticSearch)."""

    stat_code: str
    stat_name: str
    item_code1: str
    item_name1: str
    item_code2: str
    item_name2: str
    item_code3: str
    item_name3: str
    item_code4: str
    item_name4: str
    unit_name: str
    weight: str               # vendor WGT
    time: str                 # cycle-formatted, e.g. "202401" for monthly
    data_value: float | None  # vendor DATA_VALUE, None when the vendor sent it blank


class TableRow(TypedDict, total=False):
    """One statistical table from :meth:`ECOS.get_tables` (StatisticTableList)."""

    stat_code: str
    stat_name: str
    group_code: str
    group_name: str
    parent_stat_code: str  # vendor P_STAT_CODE
    cycle: str
    searchable: str        # vendor SRCH_YN -- "Y" if the table serves observations
    org_name: str


class ItemRow(TypedDict, total=False):
    """One detail item from :meth:`ECOS.get_items` (StatisticItemList)."""

    stat_code: str
    stat_name: str
    group_code: str
    group_name: str
    item_code: str
    item_name: str
    parent_item_code: str  # vendor P_ITEM_CODE
    parent_item_name: str
    cycle: str
    start_time: str
    end_time: str
    data_count: str        # vendor DATA_CNT
    unit_name: str
    weight: str


class KeyStatRow(TypedDict, total=False):
    """One of the top-100 indicators from :meth:`ECOS.get_key_statistics`."""

    class_name: str
    keystat_name: str
    data_value: float | None  # vendor DATA_VALUE
    cycle: str
    unit_name: str


class WordRow(TypedDict, total=False):
    """One glossary entry from :meth:`ECOS.get_glossary` (StatisticWord)."""

    word: str
    content: str


class MetaRow(TypedDict, total=False):
    """One meta-DB row from :meth:`ECOS.get_meta` (StatisticMeta)."""

    level: str             # vendor LVL
    parent_content_code: str
    content_code: str
    content_name: str
