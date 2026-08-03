"""One request over the wire: build the ECOS path, GET it, surface errors.

ECOS is a path-positional API -- every argument is a slash segment in a fixed
order, up to fifteen of them:

    /api/{service}/{key}/{format}/{lang}/{start_row}/{end_row}/{tail...}

This module is the only place that order is written down. The client passes a
``tail`` of already-ordered segments; nothing above it ever sees a position.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx

from .exceptions import ECOSAuthError, ECOSNetworkError, ECOSResponseError

BASE_URL = "https://ecos.bok.or.kr/api"

# ECOS serves at most this many rows per request; the parser pages past it.
PAGE_SIZE = 100


def request_page(
    client: httpx.Client,
    *,
    service: str,
    api_key: str,
    lang: str,
    start_row: int,
    end_row: int,
    tail: list[str],
) -> dict[str, Any]:
    """Fetch one page and return its ``{list_total_count, row}`` body.

    Raises :class:`ECOSNetworkError` if the request never completed,
    :class:`ECOSAuthError` on a rejected key, and :class:`ECOSResponseError` on
    any other vendor error. A "no data" response (INFO-200) is not an error -- it
    returns as an empty page.
    """
    url = _build_url(service, api_key, lang, start_row, end_row, tail)
    try:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as err:
        raise ECOSNetworkError(str(err)) from err
    except json.JSONDecodeError as err:
        # A 200 whose body is not JSON (a proxy/maintenance HTML page) must still
        # surface through the ECOSError hierarchy, not as a raw decode error.
        raise ECOSResponseError(
            "UNKNOWN", f"non-JSON response from ECOS: {err}") from err
    return _body(payload, service)


def _build_url(
    service: str,
    api_key: str,
    lang: str,
    start_row: int,
    end_row: int,
    tail: list[str],
) -> str:
    segments = [service, api_key, "json", lang, str(start_row), str(end_row), *tail]
    while segments and segments[-1] == "":  # trailing optional args ECOS omits
        segments.pop()
    path = "/".join(quote(segment, safe="") for segment in segments)
    return f"{BASE_URL}/{path}"


def _body(payload: Any, service: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ECOSResponseError("UNKNOWN", f"unexpected ECOS response: {payload!r}")
    if service in payload:
        body: dict[str, Any] = payload[service]
        return body

    result = payload.get("RESULT")
    if not isinstance(result, dict):
        raise ECOSResponseError("UNKNOWN", f"unexpected ECOS response: {payload!r}")

    code = result.get("CODE", "UNKNOWN")
    message = result.get("MESSAGE", "")
    if code == "INFO-200":  # no matching data -- an empty result, not a failure
        return {"list_total_count": "0", "row": []}
    if code == "INFO-100":  # invalid authentication key
        raise ECOSAuthError(message or "invalid ECOS API key")
    raise ECOSResponseError(code, message)
