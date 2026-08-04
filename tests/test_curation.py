"""The curated-indicator tree, exercised offline against a mocked ECOS."""

from __future__ import annotations

from datetime import date
from functools import cached_property

import httpx
import pytest

from pyecos import ECOS, Cycle, Indicator, IndicatorSpec
from pyecos.curation._generated import _CurationGroups
from pyecos.curation._indicator import _recent_window


def _group_names() -> list[str]:
    """The 21 top-level group names -- the cached_property accessors on the base."""
    return [
        name
        for name, descriptor in vars(_CurationGroups).items()
        if isinstance(descriptor, cached_property)
    ]


def _recording_client(paths: list[str]) -> ECOS:
    """An ECOS whose every request URL is appended to ``paths``; returns one row."""

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.raw_path.decode("ascii"))
        return httpx.Response(
            200,
            json={
                "StatisticSearch": {
                    "list_total_count": "1",
                    "row": [
                        {"STAT_CODE": "X", "TIME": "202606", "DATA_VALUE": "543.67"}
                    ],
                }
            },
        )

    return ECOS("TESTKEY", transport=httpx.MockTransport(handle))


def _walk(node: object) -> list[Indicator]:
    """Every Indicator reachable under a namespace object."""
    found: list[Indicator] = []
    for value in vars(node).values():
        if isinstance(value, Indicator):
            found.append(value)
        else:
            found.extend(_walk(value))
    return found


# -- structure ------------------------------------------------------------


def test_two_level_path_is_an_indicator_with_its_codes():
    ecos = _recording_client([])
    ind = ecos.rate.base
    assert isinstance(ind, Indicator)
    assert ind.spec.stat_code == "722Y001"
    assert ind.spec.item_code1 == "0101000"
    assert ind.spec.cycle is Cycle.DAILY


def test_deep_nested_path_resolves_to_leaf():
    ecos = _recording_client([])
    ind = ecos.trade.exports.semiconductor.value
    assert ind.spec.stat_code == "403Y001"
    assert ind.spec.item_code1 == "30911AA"
    assert ind.spec.path == "trade.exports.semiconductor.value"


@pytest.mark.parametrize(
    ("path", "stat_code"),
    [
        ("household.apc", "901Y117"),            # renamed from propensity_to_consume
        ("price.producer.logic", "404Y016"),     # 시스템반도체, non-memory
    ],
)
def test_renamed_accessor_still_resolves(path: str, stat_code: str):
    # The count/spec walks stay green through a rename (125 stays 125), so a codegen
    # or TSV rename that dropped or misspelled one would ship untested -- name them.
    ecos = _recording_client([])
    node: object = ecos
    for segment in path.split("."):
        node = getattr(node, segment)
    assert isinstance(node, Indicator)
    assert node.spec.path == path
    assert node.spec.stat_code == stat_code


def test_import_direction_uses_plural_to_dodge_keyword():
    ecos = _recording_client([])
    # `import` is a Python keyword; the branch is named `imports`.
    assert not hasattr(ecos.trade, "import")
    assert ecos.trade.imports.semiconductor.price.spec.stat_code == "401Y015"


def test_three_dimensional_indicator_carries_all_item_codes():
    ecos = _recording_client([])
    ind = ecos.corporate.manufacturing.profit_margin
    codes = (ind.spec.item_code1, ind.spec.item_code2, ind.spec.item_code3)
    assert codes == ("C", "A", "6091")


def test_every_group_hangs_off_the_client():
    ecos = _recording_client([])
    for group in _group_names():
        assert hasattr(ecos, group), group


def test_all_indicators_have_wellformed_specs():
    ecos = _recording_client([])
    indicators = _walk_all(ecos)
    assert indicators
    for ind in indicators:
        assert ind.spec.stat_code
        assert ind.spec.name_ko and ind.spec.name_en
        assert isinstance(ind.spec.cycle, Cycle)


def _walk_all(ecos: ECOS) -> list[Indicator]:
    found: list[Indicator] = []
    for group in _group_names():
        found.extend(_walk(getattr(ecos, group)))
    return found


def test_curation_covers_every_worksheet_indicator():
    ecos = _recording_client([])
    assert len(_walk_all(ecos)) == 125


# -- fetch behavior -------------------------------------------------------


def test_fetch_forwards_stat_and_item_codes_to_the_request():
    paths: list[str] = []
    ecos = _recording_client(paths)
    ecos.trade.exports.semiconductor.value.fetch(start="202601", end="202612")
    (url,) = paths
    # positional tail: .../<stat>/<cycle>/<start>/<end>/<item1>...
    assert "/StatisticSearch/" in url
    assert "/403Y001/" in url
    assert "/202601/202612/" in url
    assert url.endswith("/30911AA")  # trailing empty item2..4 are trimmed


def test_fetch_forwards_all_item_codes_for_a_3d_indicator():
    paths: list[str] = []
    ecos = _recording_client(paths)
    # A three-dimensional table: item1=industry, item2=size class, item3=metric.
    ecos.corporate.manufacturing.profit_margin.fetch(start="2021", end="2026")
    (url,) = paths
    assert url.endswith("/C/A/6091")  # item_code1 / item_code2 / item_code3, in order


def test_fetch_maps_rows_and_returns_typed_dicts():
    ecos = _recording_client([])
    rows = ecos.rate.base.fetch(start="202401", end="202412")
    assert rows[0]["data_value"] == pytest.approx(
        543.67, abs=1e-9
    )  # exact decimal parse


def test_latest_returns_the_greatest_time_regardless_of_row_order():
    def handle(request: httpx.Request) -> httpx.Response:
        rows = [
            {"STAT_CODE": "X", "TIME": t, "DATA_VALUE": "1"}
            for t in ("202604", "202606", "202605")  # deliberately not sorted
        ]
        return httpx.Response(
            200, json={"StatisticSearch": {"list_total_count": "3", "row": rows}}
        )

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))
    latest = ecos.rate.base.latest(today=date(2026, 8, 4))
    assert latest is not None
    assert latest["time"] == "202606"  # max, not rows[-1]


def test_latest_forwards_the_current_recent_window_to_fetch():
    paths: list[str] = []
    ecos = _recording_client(paths)
    ecos.rate.base.latest(today=date(2026, 8, 4))  # DAILY -> 400-day window
    (url,) = paths
    assert "/20250630/20260804/" in url


def test_latest_is_none_for_an_empty_series():
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "no data"}}
        )

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))
    assert ecos.rate.base.latest(today=date(2026, 8, 4)) is None


def test_repr_names_the_path_not_the_key():
    ecos = _recording_client([])
    text = repr(ecos.rate.base)
    assert "rate.base" in text
    assert "722Y001" not in text  # repr shows the name, not the raw code


# -- recent window --------------------------------------------------------


@pytest.mark.parametrize(
    ("cycle", "expected"),
    [
        (Cycle.ANNUAL, ("2023", "2026")),
        (Cycle.QUARTERLY, ("2024Q1", "2026Q4")),
        (Cycle.MONTHLY, ("202401", "202612")),
        (Cycle.SEMIANNUAL, ("2023S1", "2026S2")),
        (Cycle.SEMIMONTHLY, ("202501S1", "202612S2")),
        (Cycle.DAILY, ("20250630", "20260804")),
    ],
)
def test_recent_window_is_cycle_formatted(cycle, expected):
    assert _recent_window(cycle, date(2026, 8, 4)) == expected


def test_indicator_spec_is_frozen():
    spec = IndicatorSpec(
        path="p", name_ko="a", name_en="b", stat_code="X", cycle=Cycle.MONTHLY
    )
    with pytest.raises((AttributeError, TypeError)):
        spec.stat_code = "Y"  # type: ignore[misc]


def test_wildcard_item_code_is_percent_encoded_in_the_request():
    # trade.exports.value uses item_code1="*AA"; ECOS decodes %2AAA back to *AA.
    paths: list[str] = []
    ecos = _recording_client(paths)
    ecos.trade.exports.value.fetch(start="202601", end="202612")
    assert "%2AAA" in paths[0]
