"""One request over the wire: build the ECOS path, GET it, surface errors.

ECOS is a path-positional API -- every argument is a slash segment in a fixed
order, up to fifteen of them:

    /api/{service}/{key}/{format}/{lang}/{start_row}/{end_row}/{tail...}

This module is the only place that order is written down. ``_Transport`` holds the
HTTP client and the pacing clock: it spaces consecutive requests (``delay_seconds``)
and retries a transient failure (timeout, connection reset, 5xx) with backoff, but a
rate limit (ERROR-602) is an answer to respect, raised straight through.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import quote

import httpx

from .exceptions import (
    ECOSAuthError,
    ECOSNetworkError,
    ECOSRateLimitError,
    ECOSResponseError,
)

BASE_URL = "https://ecos.bok.or.kr/api"

# ECOS serves at most this many rows per request; the parser pages past it.
PAGE_SIZE = 100

# A transient failure (timeout, reset, 5xx) is a glitch worth retrying; a rate
# limit is not (see _Transport.request_page).
_TRANSIENT_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 1.0
_RETRY_BACKOFF_FACTOR = 2  # each retry waits this many times the last


class _Transport:
    """The HTTP client plus its pacing clock -- one per :class:`ECOS`.

    ``delay_seconds`` spaces consecutive requests so a burst (a long paginated
    series, or many indicators in a loop) stays under the ECOS rate cap of ~300
    calls in three minutes; the default is 0 because a handful of calls never
    reaches it, and pacing every page would only slow the common case. A bulk
    caller sets it (0.6s keeps one client under the cap indefinitely).
    """

    def __init__(
        self,
        client: httpx.Client,
        *,
        delay_seconds: float = 0.0,
        retries: int = _TRANSIENT_RETRIES,
    ) -> None:
        self._client = client
        self._delay_seconds = delay_seconds
        self._retries = retries
        self._next_request_at = 0.0

    def request_page(
        self,
        *,
        service: str,
        api_key: str,
        lang: str,
        start_row: int,
        end_row: int,
        tail: list[str],
    ) -> dict[str, Any]:
        """Fetch one page and return its ``{list_total_count, row}`` body.

        Retries a transient transport failure (timeout, connection reset, 5xx) with
        backoff. Raises :class:`ECOSNetworkError` if it never completes,
        :class:`ECOSRateLimitError` on a rate limit (ERROR-602, not retried),
        :class:`ECOSAuthError` on a rejected key, and :class:`ECOSResponseError` on
        any other vendor error. A "no data" response (INFO-200) returns as empty.
        """
        url = _build_url(service, api_key, lang, start_row, end_row, tail)
        last_error: Exception | None = None
        for attempt in range(self._retries):
            self._wait_for_next_slot()
            try:
                response = self._client.get(url)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as err:
                status = err.response.status_code
                if status == 429:  # an HTTP-level rate limit, should ECOS send one
                    raise ECOSRateLimitError("ERROR-602", str(err)) from err
                if status < 500:  # any other 4xx is the server's answer
                    raise ECOSNetworkError(str(err)) from err
                last_error = ECOSNetworkError(str(err))  # 5xx -- retry
            except httpx.HTTPError as err:  # timeout, connection reset, ...
                last_error = ECOSNetworkError(str(err))
            except json.JSONDecodeError as err:
                # A 200 whose body is not JSON (a proxy/maintenance HTML page) must
                # surface through the ECOSError hierarchy, not as a raw decode error.
                raise ECOSResponseError(
                    "UNKNOWN", f"non-JSON response from ECOS: {err}") from err
            else:
                return _body(payload, service)
            if attempt + 1 < self._retries:
                time.sleep(_RETRY_BACKOFF_SECONDS * _RETRY_BACKOFF_FACTOR**attempt)
        raise last_error if last_error else ECOSNetworkError("request failed")

    def _wait_for_next_slot(self) -> None:
        if self._delay_seconds <= 0:
            return
        now = time.monotonic()
        if now < self._next_request_at:
            time.sleep(self._next_request_at - now)
        self._next_request_at = time.monotonic() + self._delay_seconds


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
    if code == "ERROR-602":  # too many calls -- rate limited, back off
        raise ECOSRateLimitError(code, message)
    raise ECOSResponseError(code, message)
