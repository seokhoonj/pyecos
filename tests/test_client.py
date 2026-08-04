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
    ECOSRateLimitError,
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


def test_fetch_series_maps_vendor_keys_and_parses_value():
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

    rows = ecos.fetch_series("722Y001", start="202401", end="202401")

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

    (row,) = ecos.fetch_series("X", start="202401", end="202401")

    assert row["data_value"] is None


def test_fetch_series_pages_past_the_hundred_row_limit():
    first = [{"STAT_CODE": "X", "TIME": f"2024{i:02d}", "DATA_VALUE": str(i)}
             for i in range(1, 101)]
    second = [{"STAT_CODE": "X", "TIME": "202512", "DATA_VALUE": "101"}]
    paths: list[str] = []
    ecos = _client([_search_page(first, 101), _search_page(second, 101)], paths)

    rows = ecos.fetch_series("X", cycle=Cycle.MONTHLY, start="202401", end="202512")

    assert len(rows) == 101
    assert rows[-1]["data_value"] == pytest.approx(101.0, abs=1e-9)
    assert "/1/100/" in paths[0]
    assert "/101/200/" in paths[1]


def test_fetch_series_builds_the_positional_path_in_order():
    paths: list[str] = []
    ecos = _client([_search_page([], 0)], paths)

    ecos.fetch_series("722Y001", cycle="M", start="202001", end="202412",
                    item_code1="0101000")

    # service/key/format/lang/start_row/end_row/stat/cycle/start/end/item1
    assert paths[0] == (
        "/api/StatisticSearch/TESTKEY/json/kr/1/100"
        "/722Y001/M/202001/202412/0101000"
    )


def test_no_matching_data_returns_empty_list():
    page = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "no data"}}
    ecos = _client([page])

    assert ecos.fetch_series("X", start="202401", end="202401") == []


def test_invalid_key_raises_auth_error():
    page = {"RESULT": {"CODE": "INFO-100", "MESSAGE": "bad key"}}
    ecos = _client([page])

    with pytest.raises(ECOSAuthError):
        ecos.fetch_series("X", start="202401", end="202401")


def test_vendor_error_raises_response_error_with_code():
    page = {"RESULT": {"CODE": "ERROR-300", "MESSAGE": "required argument missing"}}
    ecos = _client([page])

    with pytest.raises(ECOSResponseError) as caught:
        ecos.fetch_series("X")

    assert caught.value.code == "ERROR-300"


def test_transport_failure_raises_network_error(monkeypatch):
    import pyecos._transport as transport
    monkeypatch.setattr(transport, "_RETRY_BACKOFF_SECONDS", 0)  # no real waiting
    attempts = []

    def fail(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        raise httpx.ConnectTimeout("timed out", request=request)

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(fail))

    with pytest.raises(ECOSNetworkError):
        ecos.fetch_series("X", start="202401", end="202401")
    assert len(attempts) == 3  # a transient failure is retried up to the limit


def test_rate_limit_raises_rate_limit_error():
    page = {"RESULT": {"CODE": "ERROR-602", "MESSAGE": "too many calls"}}
    ecos = _client([page])

    with pytest.raises(ECOSRateLimitError) as caught:
        ecos.fetch_series("X")

    assert isinstance(caught.value, ECOSResponseError)  # a subclass, still catchable
    assert caught.value.code == "ERROR-602"


def test_rate_limit_is_not_retried():
    attempts = []

    def handle(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(200, json={"RESULT": {"CODE": "ERROR-602",
                                                    "MESSAGE": "x"}})

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))

    with pytest.raises(ECOSRateLimitError):
        ecos.fetch_series("X")
    assert len(attempts) == 1  # a rate limit is an answer -- raised, not retried


def test_delay_seconds_paces_requests(monkeypatch):
    import pyecos._transport as transport
    monkeypatch.setattr(transport.time, "monotonic", lambda: 1000.0)  # frozen clock
    slept = []
    monkeypatch.setattr(transport.time, "sleep", lambda seconds: slept.append(seconds))
    first = [{"DATA_VALUE": str(i)} for i in range(100)]
    ecos = ECOS("TESTKEY", delay_seconds=0.6,
                transport=_handler([_search_page(first, 101),
                                    _search_page([{"DATA_VALUE": "101"}], 101)], []))

    ecos.fetch_series("X")  # two pages -> the first is free, the second waits one slot

    assert slept == pytest.approx([0.6])  # one slot; frozen clock, so exactly delay


def test_non_positive_delay_does_not_pace(monkeypatch):
    import pyecos._transport as transport
    slept = []
    monkeypatch.setattr(transport.time, "sleep", lambda seconds: slept.append(seconds))
    first = [{"DATA_VALUE": str(i)} for i in range(100)]
    ecos = ECOS("TESTKEY", delay_seconds=0.0,  # the default -- no pacing
                transport=_handler([_search_page(first, 101),
                                    _search_page([{"DATA_VALUE": "101"}], 101)], []))

    ecos.fetch_series("X")

    assert slept == []


def test_cycle_accepts_both_enum_and_string():
    paths_enum: list[str] = []
    paths_str: list[str] = []
    _client([_search_page([], 0)], paths_enum).fetch_series("X", cycle=Cycle.DAILY)
    _client([_search_page([], 0)], paths_str).fetch_series("X", cycle="D")

    assert "/X/D" in paths_enum[0]
    assert paths_enum[0] == paths_str[0]


def test_per_call_language_overrides_the_client_default():
    paths: list[str] = []
    empty_key_stats = {"KeyStatisticList": {"list_total_count": "0", "row": []}}
    ecos = ECOS("TESTKEY", lang="kr",
                transport=_handler([empty_key_stats], paths))

    ecos.fetch_key_statistics(lang="en")

    assert "/json/en/" in paths[0]


def test_repr_does_not_leak_the_api_key():
    ecos = _client([])
    assert "TESTKEY" not in repr(ecos)


def test_korean_argument_is_url_encoded():
    paths: list[str] = []
    ecos = _client([{"StatisticWord": {"list_total_count": "0", "row": []}}], paths)

    ecos.fetch_glossary("총부채원리금상환비율")

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
    (lambda e: e.fetch_tables(), "StatisticTableList", "/1/100"),
    (lambda e: e.fetch_tables(stat_code="722Y001"), "StatisticTableList", "/722Y001"),
    (lambda e: e.fetch_items("722Y001"), "StatisticItemList", "/722Y001"),
    (lambda e: e.fetch_key_statistics(), "KeyStatisticList", "/1/100"),
    (lambda e: e.fetch_glossary("DSR"), "StatisticWord", "/DSR"),
    (lambda e: e.fetch_meta("ESI"), "StatisticMeta", "/ESI"),
])
def test_each_service_targets_its_own_endpoint(call, service, tail_segment):
    paths: list[str] = []
    call(_client([_service_page(service, [])], paths))
    assert f"/api/{service}/" in paths[0]
    assert paths[0].endswith(tail_segment)


def test_tables_maps_parent_and_searchable_aliases():
    raw = {"STAT_CODE": "102Y004", "P_STAT_CODE": "0000000620",
           "SRCH_YN": "Y", "STAT_NAME": "본원통화"}
    (row,) = _client([_service_page("StatisticTableList", [raw])]).fetch_tables()
    assert row["parent_stat_code"] == "0000000620"
    assert row["searchable"] == "Y"


def test_items_maps_weight_wgt_variant_and_data_count():
    # StatisticItemList sends the weight as WEIGHT (full word), not WGT.
    raw = {"ITEM_CODE": "0", "P_ITEM_CODE": "ROOT", "WEIGHT": "1000", "DATA_CNT": "5"}
    (row,) = _client([_service_page("StatisticItemList", [raw])]).fetch_items("X")
    assert row["parent_item_code"] == "ROOT"
    assert row["weight"] == "1000"
    assert row["data_count"] == "5"


def test_key_statistics_parses_data_value_to_float():
    raw = {"KEYSTAT_NAME": "한국은행 기준금리", "DATA_VALUE": "2.75", "UNIT_NAME": "%"}
    (row,) = _client([_service_page("KeyStatisticList", [raw])]).fetch_key_statistics()
    assert row["keystat_name"] == "한국은행 기준금리"
    assert row["data_value"] == pytest.approx(2.75, abs=1e-9)


def test_meta_maps_content_hierarchy_aliases():
    raw = {"LVL": "1", "P_CONT_CODE": "R", "CONT_CODE": "A", "CONT_NAME": "명목"}
    (row,) = _client([_service_page("StatisticMeta", [raw])]).fetch_meta("ESI")
    assert row == {"level": "1", "parent_content_code": "R",
                   "content_code": "A", "content_name": "명목"}


@pytest.mark.parametrize("call, service", [
    (lambda e: e.fetch_tables(lang="en"), "StatisticTableList"),
    (lambda e: e.fetch_items("X", lang="en"), "StatisticItemList"),
    (lambda e: e.fetch_key_statistics(lang="en"), "KeyStatisticList"),
    (lambda e: e.fetch_glossary("X", lang="en"), "StatisticWord"),
    (lambda e: e.fetch_meta("X", lang="en"), "StatisticMeta"),
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

    rows = ecos.fetch_series("X")

    assert len(rows) == 200
    assert len(paths) == 2  # no wasted third request when the count is exhausted


def test_unexpected_envelope_raises_response_error():
    ecos = _client([{"somethingElse": {"row": []}}])
    with pytest.raises(ECOSResponseError) as caught:
        ecos.fetch_series("X")
    assert caught.value.code == "UNKNOWN"


def test_non_dict_json_body_raises_response_error():
    ecos = _client([["not", "an", "object"]])
    with pytest.raises(ECOSResponseError):
        ecos.fetch_series("X")


def test_non_json_200_body_raises_response_error():
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>maintenance</html>")

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))
    with pytest.raises(ECOSResponseError) as caught:
        ecos.fetch_series("X")
    assert caught.value.code == "UNKNOWN"


def test_garbage_total_count_keeps_paging_and_does_not_truncate():
    # A non-integer total must not truncate a multi-page series; keep paging until
    # an empty batch. The old bug returned only the first page.
    paths: list[str] = []
    ecos = _client(
        [
            {"StatisticSearch": {"list_total_count": "N/A",
                                 "row": [{"DATA_VALUE": str(i)} for i in range(100)]}},
            {"StatisticSearch": {"list_total_count": "N/A",
                                 "row": [{"DATA_VALUE": str(i)} for i in range(50)]}},
            {"StatisticSearch": {"list_total_count": "N/A", "row": []}},
        ],
        paths,
    )
    rows = ecos.fetch_series("X")
    assert len(rows) == 150       # both pages kept, not truncated to the first
    assert len(paths) == 3        # paged past the garbage total to the empty page


# --- opt-in TTL cache -------------------------------------------------------

def _counting_client(*, cache_ttl: float | None = None) -> tuple[ECOS, list[int]]:
    """An ECOS whose mock transport counts requests and always answers one row."""
    calls: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, json=_search_page([{"DATA_VALUE": "1"}], 1))

    ecos = ECOS("TESTKEY", cache_ttl=cache_ttl, transport=httpx.MockTransport(handle))
    return ecos, calls


def test_cache_serves_a_repeat_query_without_a_network_call():
    ecos, calls = _counting_client(cache_ttl=3600)
    first = ecos.fetch_series("X", start="202401", end="202401")
    second = ecos.fetch_series("X", start="202401", end="202401")
    assert first == second
    assert len(calls) == 1  # the second is served from the cache


def test_cache_is_off_by_default_and_refetches():
    ecos, calls = _counting_client()
    ecos.fetch_series("X")
    ecos.fetch_series("X")
    assert len(calls) == 2


def test_cache_keys_on_the_request_so_different_queries_miss():
    ecos, calls = _counting_client(cache_ttl=3600)
    ecos.fetch_series("X")
    ecos.fetch_series("Y")  # a different stat code is a different key
    assert len(calls) == 2


def test_cache_keeps_language_variants_apart():
    ecos, calls = _counting_client(cache_ttl=3600)
    ecos.fetch_series("X", lang="kr")
    ecos.fetch_series("X", lang="en")
    assert len(calls) == 2


def test_cache_entry_expires_after_ttl(monkeypatch):
    import pyecos._cache as cache_mod
    clock = [1000.0]
    monkeypatch.setattr(cache_mod.time, "monotonic", lambda: clock[0])
    ecos, calls = _counting_client(cache_ttl=60)
    ecos.fetch_series("X")
    clock[0] += 61  # past the TTL
    ecos.fetch_series("X")
    assert len(calls) == 2


def test_clear_cache_forces_a_refetch():
    ecos, calls = _counting_client(cache_ttl=3600)
    ecos.fetch_series("X")
    ecos.clear_cache()
    ecos.fetch_series("X")
    assert len(calls) == 2


def test_cached_rows_are_isolated_from_caller_mutation():
    ecos, calls = _counting_client(cache_ttl=3600)
    first = ecos.fetch_series("X")
    first.append({"tampered": "row"})  # list-level mutation
    first[0]["data_value"] = 999.0     # dict-level mutation of a row
    second = ecos.fetch_series("X")    # served from the cache
    assert len(second) == 1            # the list is isolated
    assert second[0]["data_value"] == 1.0  # and each row dict is isolated too


def test_cache_evicts_least_recently_used_past_maxsize():
    from pyecos._cache import _Cache
    cache = _Cache(ttl=3600, maxsize=2)
    cache.set(("s", "kr", ("a",)), [{"v": "1"}])
    cache.set(("s", "kr", ("b",)), [{"v": "2"}])
    assert cache.get(("s", "kr", ("a",))) is not None  # touches "a" -> "b" is LRU
    cache.set(("s", "kr", ("c",)), [{"v": "3"}])  # over maxsize -> evict "b"
    assert cache.get(("s", "kr", ("b",))) is None
    assert cache.get(("s", "kr", ("a",))) is not None


def test_cache_stores_the_whole_paginated_result_and_a_hit_skips_all_pages():
    first = [{"DATA_VALUE": str(i)} for i in range(100)]
    calls: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        page = _search_page(first, 101) if len(calls) == 1 \
            else _search_page([{"DATA_VALUE": "100"}], 101)
        return httpx.Response(200, json=page)

    ecos = ECOS("TESTKEY", cache_ttl=3600, transport=httpx.MockTransport(handle))
    first = ecos.fetch_series("X")
    second = ecos.fetch_series("X")  # repeat -> whole 101-row result from cache

    assert len(first) == len(second) == 101
    assert len(calls) == 2  # two pages once; the repeat made no request


def test_transient_failure_is_retried_and_the_later_success_is_returned(monkeypatch):
    import pyecos._transport as transport
    monkeypatch.setattr(transport, "_RETRY_BACKOFF_SECONDS", 0)  # no real waiting
    attempts: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            raise httpx.ConnectTimeout("blip", request=request)
        return httpx.Response(200, json=_search_page([{"DATA_VALUE": "1"}], 1))

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))

    (row,) = ecos.fetch_series("X")
    assert row["data_value"] == 1.0
    assert len(attempts) == 2  # failed once, then the retry succeeded


def test_non_positive_cache_ttl_is_rejected():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            ECOS("TESTKEY", cache_ttl=bad, transport=httpx.MockTransport(lambda r: r))


def test_http_429_maps_to_rate_limit_error():
    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(
        lambda request: httpx.Response(429, json={})))

    with pytest.raises(ECOSRateLimitError) as caught:
        ecos.fetch_series("X")
    assert caught.value.code == "ERROR-602"


def test_http_4xx_maps_to_network_error_without_retry():
    attempts: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(404, text="not found")

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))

    with pytest.raises(ECOSNetworkError):
        ecos.fetch_series("X")
    assert len(attempts) == 1  # a 4xx is the server's answer, not retried


def test_http_5xx_is_retried_then_succeeds(monkeypatch):
    import pyecos._transport as transport
    monkeypatch.setattr(transport, "_RETRY_BACKOFF_SECONDS", 0)
    attempts: list[int] = []

    def handle(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            return httpx.Response(500, text="oops")
        return httpx.Response(200, json=_search_page([{"DATA_VALUE": "1"}], 1))

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(handle))

    (row,) = ecos.fetch_series("X")
    assert row["data_value"] == pytest.approx(1.0, abs=1e-9)
    assert len(attempts) == 2  # one 5xx, then the retry succeeded


def test_retry_exhaustion_chains_the_underlying_cause(monkeypatch):
    import pyecos._transport as transport
    monkeypatch.setattr(transport, "_RETRY_BACKOFF_SECONDS", 0)

    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("blip", request=request)

    ecos = ECOS("TESTKEY", transport=httpx.MockTransport(fail))

    with pytest.raises(ECOSNetworkError) as caught:
        ecos.fetch_series("X")
    assert isinstance(caught.value.__cause__, httpx.HTTPError)  # cause is preserved


def test_unknown_lang_raises_value_error():
    with pytest.raises(ValueError):
        ECOS("TESTKEY", lang="xx",
             transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))


def test_unknown_cycle_raises_value_error():
    ecos = _client([_search_page([], 0)])
    with pytest.raises(ValueError):
        ecos.fetch_series("X", cycle="Z")
