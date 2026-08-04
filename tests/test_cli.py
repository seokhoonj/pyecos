"""CLI behavior, exercised with the client stubbed out (no network, no key)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pyecos import cli
from pyecos.exceptions import ECOSConfigError, ECOSResponseError


def _stub_client(monkeypatch: pytest.MonkeyPatch, *,
                 rows: list[dict[str, Any]] | None = None,
                 error: Exception | None = None) -> dict[str, Any]:
    """Replace ``cli.ECOS`` with a fake whose every service call returns ``rows`` (or
    raises ``error``), and record the kwargs the constructor saw."""
    seen: dict[str, Any] = {}

    class _FakeECOS:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            seen.update(kwargs)

        def __enter__(self) -> _FakeECOS:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def _answer(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            if error is not None:
                raise error
            return rows or []

        fetch_series = fetch_tables = fetch_items = _answer
        fetch_key_statistics = fetch_glossary = fetch_meta = _answer

    monkeypatch.setattr(cli, "ECOS", _FakeECOS)
    return seen


def test_series_text_shows_summary_and_recent_rows(monkeypatch, capsys):
    rows = [{"stat_name": "시장금리", "unit_name": "%", "time": "202401",
             "data_value": 3.5}]
    _stub_client(monkeypatch, rows=rows)

    exit_code = cli.main(["series", "722Y001", "--item", "0101000",
                          "--start", "202401", "--end", "202401"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "722Y001" in out and "1 obs" in out and "3.5" in out


def test_json_flag_emits_the_full_rows(monkeypatch, capsys):
    rows = [{"time": "202401", "data_value": 3.5},
            {"time": "202402", "data_value": 3.5}]
    _stub_client(monkeypatch, rows=rows)

    cli.main(["series", "722Y001", "--json"])

    assert json.loads(capsys.readouterr().out) == rows


def test_lang_flag_reaches_the_client(monkeypatch, capsys):
    seen = _stub_client(monkeypatch, rows=[])

    cli.main(["key-stats", "--lang", "en"])

    assert seen["lang"] == "en"


def test_more_than_four_items_is_rejected(monkeypatch, capsys):
    _stub_client(monkeypatch, rows=[])

    items = sum((["--item", str(i)] for i in range(5)), [])
    exit_code = cli.main(["series", "X", *items])

    assert exit_code == 1
    assert "at most 4" in capsys.readouterr().err


def test_missing_key_is_reported_as_one_line(monkeypatch, capsys):
    _stub_client(monkeypatch, error=ECOSConfigError("no ECOS API key: pass api_key"))

    exit_code = cli.main(["key-stats"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert err.startswith("pyecos: ") and "no ECOS API key" in err


def test_vendor_error_is_reported_as_one_line(monkeypatch, capsys):
    _stub_client(monkeypatch, error=ECOSResponseError("ERROR-300", "argument missing"))

    exit_code = cli.main(["series", "X"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "ERROR-300" in err


def test_empty_series_is_not_an_error(monkeypatch, capsys):
    _stub_client(monkeypatch, rows=[])

    exit_code = cli.main(["series", "X"])

    assert exit_code == 0
    assert "no observations" in capsys.readouterr().out


def test_tables_renders_an_aligned_table_with_a_count(monkeypatch, capsys):
    rows = [{"stat_code": "722Y001", "cycle": "M", "searchable": "Y",
             "stat_name": "시장금리"}]
    _stub_client(monkeypatch, rows=rows)

    cli.main(["tables"])

    out = capsys.readouterr().out
    assert "722Y001" in out and "(1 rows)" in out


# --- each subcommand dispatches to the right client method ------------------

def _recording_client(monkeypatch: pytest.MonkeyPatch,
                      rows: list[dict[str, Any]] | None = None) -> list[tuple]:
    """Replace cli.ECOS with a fake that records (method, args, kwargs) per call."""
    calls: list[tuple] = []

    def _record(name: str):
        def method(self: Any, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
            calls.append((name, args, kwargs))
            return rows or []
        return method

    class _FakeECOS:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> _FakeECOS:
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        fetch_series = _record("fetch_series")
        fetch_tables = _record("fetch_tables")
        fetch_items = _record("fetch_items")
        fetch_key_statistics = _record("fetch_key_statistics")
        fetch_glossary = _record("fetch_glossary")
        fetch_meta = _record("fetch_meta")

    monkeypatch.setattr(cli, "ECOS", _FakeECOS)
    return calls


def test_items_dispatches_to_fetch_items(monkeypatch):
    calls = _recording_client(monkeypatch, rows=[])
    cli.main(["items", "722Y001"])
    assert calls == [("fetch_items", ("722Y001",), {})]


def test_key_stats_dispatches_to_fetch_key_statistics(monkeypatch):
    calls = _recording_client(monkeypatch, rows=[])
    cli.main(["key-stats"])
    assert calls[0][0] == "fetch_key_statistics"


def test_glossary_dispatches_with_word_and_renders_content(monkeypatch, capsys):
    calls = _recording_client(monkeypatch,
                              rows=[{"word": "DSR", "content": "총부채원리금상환비율"}])
    cli.main(["glossary", "DSR"])
    assert calls == [("fetch_glossary", ("DSR",), {})]
    out = capsys.readouterr().out
    assert "DSR" in out and "총부채원리금상환비율" in out


def test_meta_dispatches_with_dataset_name(monkeypatch):
    calls = _recording_client(monkeypatch, rows=[])
    cli.main(["meta", "경제심리지수"])
    assert calls == [("fetch_meta", ("경제심리지수",), {})]


def test_series_dispatch_expands_items_and_maps_cycle(monkeypatch):
    calls = _recording_client(monkeypatch, rows=[])
    cli.main(["series", "X", "--item", "A", "--item", "B", "--cycle", "daily"])
    name, args, kwargs = calls[0]
    assert name == "fetch_series"
    assert args == ("X",)
    assert kwargs["item_code1"] == "A" and kwargs["item_code2"] == "B"
    assert kwargs["item_code3"] is None
    assert str(kwargs["cycle"]) == "D"  # the CLI word "daily" maps to Cycle.DAILY


def test_missing_subcommand_exits_two():
    with pytest.raises(SystemExit) as caught:
        cli.main([])
    assert caught.value.code == 2


def test_series_renders_dash_for_a_missing_value(monkeypatch, capsys):
    _stub_client(monkeypatch, rows=[{"stat_name": "x", "unit_name": "%",
                                     "time": "202401", "data_value": None}])
    cli.main(["series", "X"])
    assert "-" in capsys.readouterr().out


def test_items_renders_the_row_in_a_table(monkeypatch, capsys):
    _stub_client(monkeypatch, rows=[{"item_code": "A", "item_name": "금리"}])
    cli.main(["items", "722Y001"])
    assert "금리" in capsys.readouterr().out
