"""Resolve the ECOS API key from the caller, the environment, or the config file.

The key is looked up in a fixed order, so an explicit value always wins and a set
environment variable beats a file on disk:

1. the ``api_key`` passed to ``ECOS(...)``
2. the ``ECOS_API_KEY`` environment variable
3. ``"ECOS_API_KEY"`` in ``$XDG_CONFIG_HOME/pyecos/credentials.json``
   (``$XDG_CONFIG_HOME`` defaults to ``~/.config``)

The resolution, the whitespace trimming, the permission handling (a group/other-readable
file is warned about, not refused), and the storage backend are delegated to credbox.
The store binding is not hardcoded: ``Credentials.for_app("pyecos")`` lets a host
embedding pyecos redirect it via ``PYECOS_STORE_APP`` / ``PYECOS_NAMESPACE``; standalone
it is exactly the flat ``~/.config/pyecos/credentials.json`` pyecos has always read. A
file that is present but unreadable, not JSON, or not a JSON object is still an error
rather than a silent skip.

Once a key is found, any character outside printable ASCII is rejected here. An
ECOS key is plain ASCII, so a control char, a non-ASCII char, or a lone surrogate (from
corrupt environment bytes) can only be a broken key -- and a lone surrogate additionally
makes ``urllib.parse.quote`` raise a whole-key ``UnicodeEncodeError`` while encoding the
key into its path segment, echoing it. That check is pyecos's own concern, not something
the credential store knows about.
"""

from __future__ import annotations

from functools import lru_cache

from credbox import CredBoxError, Credentials

from .exceptions import ECOSConfigError

_ENV_VAR = "ECOS_API_KEY"
_STORE_APP = "pyecos"


def resolve_api_key(explicit: str | None) -> str:
    """Return the first key found across the three sources, or raise if none exists."""
    try:
        found = _get_credentials().secret(_ENV_VAR, override=explicit)
    except CredBoxError as err:
        # credbox's message already names the store path + fault; don't prepend a static
        # path (wrong under a PYECOS_STORE_APP redirect); credbox detaches the
        # secret-bearing context, so `from err` keeps the key out of any traceback.
        raise ECOSConfigError(f"could not read the credential store: {err}") from err
    if found is None:
        # Binding validated cleanly above (None, not error), so store_location() is safe
        # and gives the real store (the host's under a redirect).
        raise ECOSConfigError(
            f"no ECOS API key: pass api_key=, set the {_ENV_VAR} environment "
            f"variable, or put it in {_get_credentials().store_location()}"
        )
    key = found.reveal()
    if any(not (0x20 <= ord(ch) < 0x7F) for ch in key):
        # An ECOS key is plain ASCII, so any character outside printable ASCII -- a
        # control char, a non-ASCII char, or a lone surrogate from corrupt environment
        # bytes -- can only be a broken key. A lone surrogate additionally makes
        # ``urllib.parse.quote`` raise a whole-key ``UnicodeEncodeError`` while encoding
        # it into the path segment, echoing the key -- so reject it here, before it
        # becomes a request, and never echo it.
        raise ECOSConfigError(
            "the ECOS API key must be printable ASCII (a stray newline, tab, or "
            "non-ASCII character is a broken key)"
        )
    return key


@lru_cache(maxsize=1)
def _get_credentials() -> Credentials:
    """pyecos's credbox credential store, built on first use and cached.

    Built via ``for_app`` (not the bare ``Credentials(...)``) so a host embedding pyecos
    can redirect the binding with ``PYECOS_STORE_APP`` / ``PYECOS_NAMESPACE`` before the
    first lookup. credbox re-resolves the store *path* per call (honouring a later
    ``XDG_CONFIG_HOME``); the binding is read from the environment once, when the
    facade is built. A malformed binding surfaces as ``ECOSConfigError`` on the
    first lookup that reaches the store -- an explicit arg or ``ECOS_API_KEY``
    resolves first, so a bad binding with the env var set never raises.
    """
    return Credentials.for_app(_STORE_APP)
