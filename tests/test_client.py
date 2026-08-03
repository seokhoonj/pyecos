"""Client behavior against a mocked ECOS, exercised without a network."""

from __future__ import annotations

import httpx
import pytest

from pyecos import (
    ECOS,
    Cycle,
    ECOSAuthError,
    ECOSConfigError,
    ECOSNetworkError,
    ECOSResponseError,
)


def _handler(responses: list[dict], recorded_paths: list[str]):
    """Return a MockTransport handler that replays ``responses`` in order."""
    remaining = list(responses)

    def handle(request: httpx.Request) -> httpx.Response:
        recorded_paths.append(request.url.raw_path.decode("ascii"))
        return httpx.Response(200, json=remaining.pop(0))

    return httpx.MockTransport(handle)


def _client(responses: list[dict], recorded_paths: list[str] | None = None) -> ECOS:
    recorded_paths = [] if recorded_paths is None else recorded_paths
    return ECOS("TESTKEY", transport=_handler(responses, recorded_paths))


def _search_page(rows: list[dict], total: int) -> dict:
    return {"StatisticSearch": {"list_total_count": str(total), "row": rows}}


def test_missing_api_key_raises_config_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ECOS_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # empty -- no credentials file
    with pytest.raises(ECOSConfigError):
        ECOS()


def test_api_key_read_from_environment(monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "FROMENV")
    ecos = ECOS(transport=_handler([_search_page([], 0)], []))
    assert ecos._api_key == "FROMENV"


def test_get_series_maps_vendor_keys_and_parses_value():
    raw = {
        "STAT_CODE": "722Y001",
        "STAT_NAME": "1.3.1. 시장금리",
        "ITEM_CODE1": "0101000",
        "ITEM_NAME1": "한국은행 기준금리",
        "UNIT_NAME": "%",
        "WGT": "",
        "TIME": "202401",
        "DATA_VALUE": "3.5",
    }
    ecos = _client([_search_page([raw], 1)])

    rows = ecos.get_series("722Y001", start="202401", end="202401")

    assert rows == [{
        "stat_code": "722Y001",
        "stat_name": "1.3.1. 시장금리",
        "item_code1": "0101000",
        "item_name1": "한국은행 기준금리",
        "unit_name": "%",
        "weight": "",
        "time": "202401",
        "data_value": 3.5,
    }]


def test_blank_data_value_becomes_none():
    raw = {"STAT_CODE": "X", "TIME": "202401", "DATA_VALUE": ""}
    ecos = _client([_search_page([raw], 1)])

    (row,) = ecos.get_series("X", start="202401", end="202401")

    assert row["data_value"] is None


def test_get_series_pages_past_the_hundred_row_limit():
    first = [{"STAT_CODE": "X", "TIME": f"2024{i:02d}", "DATA_VALUE": str(i)}
             for i in range(1, 101)]
    second = [{"STAT_CODE": "X", "TIME": "202512", "DATA_VALUE": "101"}]
    paths: list[str] = []
    ecos = _client([_search_page(first, 101), _search_page(second, 101)], paths)

    rows = ecos.get_series("X", cycle=Cycle.MONTHLY, start="202401", end="202512")

    assert len(rows) == 101
    assert rows[-1]["data_value"] == 101.0
    assert "/1/100/" in paths[0]
    assert "/101/200/" in paths[1]


def test_get_series_builds_the_positional_path_in_order():
    paths: list[str] = []
    ecos = _client([_search_page([], 0)], paths)

    ecos.get_series("722Y001", cycle="M", start="202001", end="202412",
                    item_code1="0101000")

    # service/key/format/lang/start_row/end_row/stat/cycle/start/end/item1
    assert paths[0] == (
        "/api/StatisticSearch/TESTKEY/json/kr/1/100"
        "/722Y001/M/202001/202412/0101000"
    )


def test_no_matching_data_returns_empty_list():
    page = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "no data"}}
    ecos = _client([page])

    assert ecos.get_series("X", start="202401", end="202401") == []


def test_invalid_key_raises_auth_error():
    page = {"RESULT": {"CODE": "INFO-100", "MESSAGE": "bad key"}}
    ecos = _client([page])

    with pytest.raises(ECOSAuthError):
        ecos.get_series("X", start="202401", end="202401")


def test_vendor_error_raises_response_error_with_code():
    page = {"RESULT": {"CODE": "ERROR-300", "MESSAGE": "required argument missing"}}
    ecos = _client([page])

    with pytest.raises(ECOSResponseError) as caught:
        ecos.get_series("X")

    assert caught.value.code == "ERROR-300"


def test_transport_failure_raises_network_error():
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(fail))

    with pytest.raises(ECOSNetworkError):
        ecos.get_series("X", start="202401", end="202401")


def test_cycle_accepts_both_enum_and_string():
    paths_enum: list[str] = []
    paths_str: list[str] = []
    _client([_search_page([], 0)], paths_enum).get_series("X", cycle=Cycle.DAILY)
    _client([_search_page([], 0)], paths_str).get_series("X", cycle="D")

    assert "/X/D" in paths_enum[0]
    assert paths_enum[0] == paths_str[0]


def test_per_call_language_overrides_the_client_default():
    paths: list[str] = []
    empty_key_stats = {"KeyStatisticList": {"list_total_count": "0", "row": []}}
    ecos = ECOS("TESTKEY", lang="kr",
                transport=_handler([empty_key_stats], paths))

    ecos.get_key_statistics(lang="en")

    assert "/json/en/" in paths[0]


def test_repr_does_not_leak_the_api_key():
    ecos = _client([])
    assert "TESTKEY" not in repr(ecos)


def test_korean_argument_is_url_encoded():
    paths: list[str] = []
    ecos = _client([{"StatisticWord": {"list_total_count": "0", "row": []}}], paths)

    ecos.get_glossary("총부채원리금상환비율")

    # The Korean term is percent-encoded, not passed raw into the path.
    assert "총부채" not in paths[0]
    assert "%" in paths[0]


def test_context_manager_closes_the_connection():
    ecos = _client([])
    with ecos as handle:
        assert handle is ecos
    assert ecos._client.is_closed


# --- the five non-series services -------------------------------------------

def _service_page(service: str, rows: list[dict], total: int | None = None) -> dict:
    return {service: {"list_total_count": str(len(rows) if total is None else total),
                      "row": rows}}


@pytest.mark.parametrize("call, service, tail_segment", [
    (lambda e: e.get_tables(), "StatisticTableList", "/1/100"),
    (lambda e: e.get_tables(stat_code="722Y001"), "StatisticTableList", "/722Y001"),
    (lambda e: e.get_items("722Y001"), "StatisticItemList", "/722Y001"),
    (lambda e: e.get_key_statistics(), "KeyStatisticList", "/1/100"),
    (lambda e: e.get_glossary("DSR"), "StatisticWord", "/DSR"),
    (lambda e: e.get_meta("ESI"), "StatisticMeta", "/ESI"),
])
def test_each_service_targets_its_own_endpoint(call, service, tail_segment):
    paths: list[str] = []
    call(_client([_service_page(service, [])], paths))
    assert f"/api/{service}/" in paths[0]
    assert paths[0].endswith(tail_segment)


def test_tables_maps_parent_and_searchable_aliases():
    raw = {"STAT_CODE": "102Y004", "P_STAT_CODE": "0000000620",
           "SRCH_YN": "Y", "STAT_NAME": "본원통화"}
    (row,) = _client([_service_page("StatisticTableList", [raw])]).get_tables()
    assert row["parent_stat_code"] == "0000000620"
    assert row["searchable"] == "Y"


def test_items_maps_weight_wgt_variant_and_data_count():
    # StatisticItemList sends the weight as WEIGHT (full word), not WGT.
    raw = {"ITEM_CODE": "0", "P_ITEM_CODE": "ROOT", "WEIGHT": "1000", "DATA_CNT": "5"}
    (row,) = _client([_service_page("StatisticItemList", [raw])]).get_items("X")
    assert row["parent_item_code"] == "ROOT"
    assert row["weight"] == "1000"
    assert row["data_count"] == "5"


def test_key_statistics_parses_data_value_to_float():
    raw = {"KEYSTAT_NAME": "한국은행 기준금리", "DATA_VALUE": "2.75", "UNIT_NAME": "%"}
    (row,) = _client([_service_page("KeyStatisticList", [raw])]).get_key_statistics()
    assert row["keystat_name"] == "한국은행 기준금리"
    assert row["data_value"] == 2.75


def test_meta_maps_content_hierarchy_aliases():
    raw = {"LVL": "1", "P_CONT_CODE": "R", "CONT_CODE": "A", "CONT_NAME": "명목"}
    (row,) = _client([_service_page("StatisticMeta", [raw])]).get_meta("ESI")
    assert row == {"level": "1", "parent_content_code": "R",
                   "content_code": "A", "content_name": "명목"}


@pytest.mark.parametrize("call, service", [
    (lambda e: e.get_tables(lang="en"), "StatisticTableList"),
    (lambda e: e.get_items("X", lang="en"), "StatisticItemList"),
    (lambda e: e.get_key_statistics(lang="en"), "KeyStatisticList"),
    (lambda e: e.get_glossary("X", lang="en"), "StatisticWord"),
    (lambda e: e.get_meta("X", lang="en"), "StatisticMeta"),
])
def test_per_call_language_override_reaches_every_service(call, service):
    paths: list[str] = []
    ecos = ECOS("TESTKEY", lang="kr",
                transport=_handler([_service_page(service, [])], paths))
    call(ecos)
    assert "/json/en/" in paths[0]


# --- pagination and malformed-response edges --------------------------------

def test_pagination_stops_after_two_full_pages_equal_to_total():
    first = [{"DATA_VALUE": str(i)} for i in range(100)]
    second = [{"DATA_VALUE": str(i)} for i in range(100, 200)]
    paths: list[str] = []
    ecos = _client([_search_page(first, 200), _search_page(second, 200)], paths)

    rows = ecos.get_series("X")

    assert len(rows) == 200
    assert len(paths) == 2  # no wasted third request when the count is exhausted


def test_unexpected_envelope_raises_response_error():
    ecos = _client([{"somethingElse": {"row": []}}])
    with pytest.raises(ECOSResponseError) as caught:
        ecos.get_series("X")
    assert caught.value.code == "UNKNOWN"


def test_non_dict_json_body_raises_response_error():
    ecos = _client([["not", "an", "object"]])
    with pytest.raises(ECOSResponseError):
        ecos.get_series("X")


def test_non_json_200_body_raises_response_error():
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>maintenance</html>")

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))
    with pytest.raises(ECOSResponseError) as caught:
        ecos.get_series("X")
    assert caught.value.code == "UNKNOWN"


def test_garbage_total_count_does_not_loop_forever():
    page = {"StatisticSearch": {"list_total_count": "N/A",
                                "row": [{"DATA_VALUE": "1"}]}}
    (row,) = _client([page]).get_series("X")  # terminates on the empty next batch
    assert row["data_value"] == 1.0
