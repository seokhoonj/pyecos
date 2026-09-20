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
    ECOSError,
    ECOSNetworkError,
    ECOSRateLimitError,
    ECOSResponseError,
)

BASE_URL = "https://ecos.bok.or.kr/api"

# ECOS serves at most this many rows per request; the parser pages past it.
PAGE_SIZE = 100

# The vendor's rate-limit code -- in the RESULT body, and mirrored for an HTTP 429.
_RATE_LIMIT_CODE = "ERROR-602"

# A transient failure (timeout, reset, 5xx) is a glitch worth retrying; a rate
# limit is not (see _Transport.request_page). This counts total attempts, not
# retries -- 3 is one try plus two retries.
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 1.0
_RETRY_BACKOFF_FACTOR = 2  # each retry waits this many times the last


class _Transport:
    """The HTTP client plus its pacing clock -- one per :class:`ECOS`.

    ``delay_seconds`` spaces consecutive requests so a burst (a long paginated
    series, or many indicators in a loop) stays under the ECOS rate cap of ~300
    calls in three minutes; the default is 0 because a handful of calls never
    reaches it, and pacing every page would only slow the common case. A bulk
    caller sets it (0.6s keeps one client under the cap indefinitely).

    Not thread-safe: the pacing clock (``_next_request_at``) is shared mutable
    state, so use one client -- hence one transport -- per thread.
    """

    def __init__(
        self,
        client: httpx.Client,
        *,
        delay_seconds: float = 0.0,
        max_attempts: int = _MAX_ATTEMPTS,
    ) -> None:
        self._client = client
        self._delay_seconds = delay_seconds
        self._max_attempts = max_attempts
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
        last_error: ECOSError | None = None
        for attempt in range(self._max_attempts):
            self._wait_for_next_slot()
            # The key rides in `url` as a path segment. Every failure error is BUILT
            # inside the except block but RAISED after it (`from None`), so the
            # key-bearing httpx error -- whose str()/repr() re-emit the URL and whose
            # `.request` holds it -- is never attached as __context__ or __cause__. This
            # is the load-bearing secret-safety invariant.
            failure: ECOSError | None = None
            retry = False
            try:
                response = self._client.get(url)
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as err:
                # httpx builds str(err) from response.url, so it embeds the whole key.
                # Build the message from the status code alone; never from str(err).
                status = err.response.status_code
                detail = f"ECOS returned HTTP {status}"
                if status == 429:  # an HTTP-level rate limit, should ECOS send one
                    failure = ECOSRateLimitError(_RATE_LIMIT_CODE, detail)
                elif status < 500:  # any other 4xx is the server's answer
                    failure = ECOSNetworkError(detail)
                else:  # 5xx -- retry
                    failure, retry = ECOSNetworkError(detail), True
            except httpx.HTTPError as err:  # timeout, connection reset, ...
                # Name the failure type only. The httpx error's str() is key-free today,
                # but the error object carries the request (with the key-bearing URL) as
                # `.request`, so it is not chained -- a structured logger walking the
                # cause chain must not be able to reach the key. `retry` with no cause.
                failure, retry = (
                    ECOSNetworkError(f"request to ECOS failed: {type(err).__name__}"),
                    True,
                )
            except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as err:
                # A 200 whose body is not JSON, not UTF-8, or nested too deep (a
                # proxy/maintenance page, invalid bytes, or a hostile payload) must
                # surface through the ECOSError hierarchy, not a raw error. httpx's
                # .json() does json.loads(bytes), which raises UnicodeDecodeError --
                # NOT a JSONDecodeError -- on a non-UTF-8 body, and RecursionError on
                # a deeply nested one. The page can echo the requested URL, so redact
                # the key; the error is not chained (its .object/args hold the body,
                # which can echo the key).
                failure = ECOSResponseError(
                    "UNKNOWN",
                    f"non-JSON response from ECOS: {_redact_key(str(err), api_key)}",
                )
            else:
                return _extract_body(payload, service, api_key)
            if not retry:
                raise failure from None  # raised outside the except: no __context__
            last_error = failure
            if attempt + 1 < self._max_attempts:
                time.sleep(_RETRY_BACKOFF_SECONDS * _RETRY_BACKOFF_FACTOR**attempt)
        if last_error is not None:
            raise last_error from None  # raised outside the except: no __context__
        raise ECOSNetworkError("request failed")

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
    if "" in segments:
        # A remaining empty is an interior positional gap (end without start, or
        # item_code2 without item_code1); it would shift every later argument.
        raise ValueError(
            "cannot build a request with a gap between positional arguments"
        )
    path = "/".join(quote(segment, safe="") for segment in segments)
    return f"{BASE_URL}/{path}"


def _redact_key(text: str, api_key: str) -> str:
    """Blank the API key out of any text derived from the request URL.

    ECOS carries the key as a URL path segment, and httpx's ``HTTPStatusError`` message
    is built from ``response.url``, so an error string can embed the key -- in its raw
    form and, since the URL is url-encoded, in its ``quote``d form. Replace both. (An
    empty key would splice ``<key>`` between every character, so guard it.)
    """
    if not api_key:
        return text
    return text.replace(api_key, "<key>").replace(quote(api_key, safe=""), "<key>")


def _extract_body(payload: Any, service: str, api_key: str) -> dict[str, Any]:
    # `payload` is the server's response body; a misbehaving proxy could echo the
    # key-bearing request URL in it, and the vendor MESSAGE is arbitrary server text, so
    # every value derived from either is redacted before it reaches an error message.
    def unexpected() -> ECOSResponseError:
        return ECOSResponseError(
            "UNKNOWN",
            f"unexpected ECOS response: {_redact_key(repr(payload), api_key)}",
        )

    if not isinstance(payload, dict):
        raise unexpected()
    if service in payload:
        body = payload[service]
        if not isinstance(body, dict):  # a non-object under the service key is bad
            raise unexpected()
        if "row" not in body and "list_total_count" not in body:
            # A dict under the service key that carries no page fields (e.g. a
            # nested RESULT error) must surface, not read as an empty series.
            raise unexpected()
        return body

    result = payload.get("RESULT")
    if not isinstance(result, dict):
        raise unexpected()

    # CODE and MESSAGE are both server-authored, so both are redacted; str() also
    # hardens a non-string CODE/MESSAGE value.
    code = _redact_key(str(result.get("CODE", "UNKNOWN")), api_key)
    message = _redact_key(str(result.get("MESSAGE", "")), api_key)
    if code == "INFO-200":  # no matching data -- an empty result, not a failure
        return {"list_total_count": "0", "row": []}
    if code == "INFO-100":  # invalid authentication key
        raise ECOSAuthError(message or "invalid ECOS API key")
    if code == _RATE_LIMIT_CODE:  # too many calls -- rate limited, back off
        raise ECOSRateLimitError(code, message)
    raise ECOSResponseError(code, message)
