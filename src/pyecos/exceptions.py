"""Exception hierarchy for pyecos.

Every *operational* error raised by this package derives from ``ECOSError``, so a
caller can catch all of them with one ``except ECOSError``. The subclasses separate
the failure modes a caller handles differently: a misconfiguration caught before any
request, a rejected API key, a vendor-reported error inside a well-formed response,
and a transport failure that never reached ECOS. An *invalid argument* -- an unknown
``cycle`` or ``lang`` value -- raises the standard ``ValueError`` instead, the usual
signal for a caller mistake rather than a runtime failure.
"""

from __future__ import annotations


class ECOSError(Exception):
    """Base class for every error raised by pyecos."""


class ECOSConfigError(ECOSError):
    """The client is misconfigured; raised before any request goes out.

    The usual cause is a missing API key -- neither passed to ``ECOS(...)`` nor
    present in the ``ECOS_API_KEY`` environment variable.
    """


class ECOSAuthError(ECOSError):
    """ECOS rejected the API key (vendor code INFO-100)."""


class ECOSResponseError(ECOSError):
    """ECOS returned a well-formed response carrying an error code.

    ``code`` and ``message`` are the vendor's own, so a caller can branch on the
    code without parsing the message text.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class ECOSRateLimitError(ECOSResponseError):
    """ECOS is rate-limiting the caller (vendor code ERROR-602).

    ECOS restricts a key that exceeds roughly 300 calls in three minutes and then
    locks it out for about thirty minutes. It subclasses :class:`ECOSResponseError`,
    so ``except ECOSResponseError`` still catches it, but a caller can catch this
    distinctly to back off instead of treating it as a generic error.
    """


class ECOSNetworkError(ECOSError):
    """The request failed at the transport or HTTP layer.

    A timeout, DNS failure, connection reset, or a non-success HTTP status that ECOS
    never turned into a RESULT body. The underlying exception is chained as
    ``__cause__``.
    """
