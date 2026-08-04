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


def test_a_returned_row_does_not_leak_into_the_shared_snapshot():
    row = catalog.table("901Y009")
    assert row is not None
    row["stat_name"] = "MUTATED"                       # caller mutates its copy
    assert catalog.table("901Y009")["stat_name"] != "MUTATED"  # snapshot intact
    assert catalog.search("901Y009")[0]["stat_name"] != "MUTATED"


def test_search_needs_no_api_key(monkeypatch, tmp_path):
    # The offline catalog answers from the bundled file alone -- no key, no client.
    monkeypatch.delenv("ECOS_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # no credentials file
    assert catalog.search("소비자물가")


# -- the generator's table walk --------------------------------------------

import importlib.util  # noqa: E402
from pathlib import Path  # noqa: E402

_GEN = Path(__file__).resolve().parent.parent / "tools" / "gen_catalog.py"
_spec = importlib.util.spec_from_file_location("gen_catalog", _GEN)
assert _spec is not None and _spec.loader is not None
gencat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gencat)


def test_walk_descends_categories_dedups_and_leaves_searchable_tables():
    class _FakeECOS:
        def fetch_tables(self, *, stat_code=None):
            if stat_code is None:
                return [{"stat_code": "P", "searchable": "N"}]  # one category
            if stat_code == "P":
                return [
                    {"stat_code": "P", "searchable": "N"},  # self-reference -> deduped
                    {"stat_code": "L", "searchable": "Y"},  # a searchable leaf
                ]
            return []  # a searchable leaf is never descended, but guard anyway

    found = gencat._walk(_FakeECOS())
    assert set(found) == {"P", "L"}            # terminates, no infinite self-descent
    assert found["L"]["searchable"] == "Y"
