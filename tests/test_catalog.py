"""The bundled offline table catalog -- searched without a key or a network."""

from __future__ import annotations

from pyecos import catalog


def test_search_finds_a_table_by_name():
    codes = {hit["stat_code"] for hit in catalog.search("소비자물가")}
    assert "901Y009" in codes


def test_search_matches_a_stat_code():
    assert any(hit["stat_code"] == "901Y009" for hit in catalog.search("901Y009"))


def test_search_is_case_insensitive():
    assert catalog.search("gdp") == catalog.search("GDP")


def test_search_keeps_only_searchable_tables_by_default():
    assert catalog.search("물가")  # non-empty
    assert all(hit["searchable"] for hit in catalog.search("물가"))


def test_search_can_include_category_headers():
    with_categories = catalog.search("통화", searchable_only=False)
    assert any(not hit["searchable"] for hit in with_categories)  # a category header
    assert len(with_categories) >= len(catalog.search("통화"))


def test_table_returns_the_row_or_none():
    row = catalog.table("901Y009")
    assert row is not None
    assert row["searchable"] is True
    assert row["cycle"] == "M"
    assert catalog.table("NO-SUCH-CODE") is None


def test_tables_returns_the_whole_snapshot_typed():
    tables = catalog.tables()
    assert len(tables) > 500
    assert all(isinstance(row["searchable"], bool) for row in tables)
    searchable = sum(1 for row in tables if row["searchable"])
    assert searchable < len(tables)  # the snapshot keeps category headers too
