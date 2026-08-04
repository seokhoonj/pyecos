"""API-key resolution across the caller, the environment, and the config file."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyecos._config import credentials_path, resolve_api_key
from pyecos.exceptions import ECOSConfigError


@pytest.fixture(autouse=True)
def _isolated_config(monkeypatch, tmp_path):
    """Point key resolution at an empty temp config home and clear the env var, so a
    real ~/.config/pyecos or a set ECOS_API_KEY on the dev machine cannot leak in."""
    monkeypatch.delenv("ECOS_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))


def _write_credentials(contents: str) -> Path:
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    return path


def test_explicit_key_wins_over_everything(monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "FROMENV")
    _write_credentials('{"ECOS_API_KEY": "FROMFILE"}')

    assert resolve_api_key("EXPLICIT") == "EXPLICIT"


def test_environment_used_when_no_explicit_key(monkeypatch):
    monkeypatch.setenv("ECOS_API_KEY", "FROMENV")
    _write_credentials('{"ECOS_API_KEY": "FROMFILE"}')

    assert resolve_api_key(None) == "FROMENV"


def test_file_used_when_no_explicit_or_environment_key():
    _write_credentials('{"ECOS_API_KEY": "FROMFILE"}')

    assert resolve_api_key(None) == "FROMFILE"


def test_no_key_anywhere_raises_config_error_naming_the_path():
    with pytest.raises(ECOSConfigError) as caught:
        resolve_api_key(None)

    assert str(credentials_path()) in str(caught.value)


def test_absent_file_is_not_an_error_it_just_means_no_key():
    # No file written; with no env either this is the "nothing anywhere" case.
    with pytest.raises(ECOSConfigError):
        resolve_api_key(None)


def test_malformed_json_file_raises_config_error():
    _write_credentials("{not json")

    with pytest.raises(ECOSConfigError, match="valid JSON"):
        resolve_api_key(None)


def test_non_object_json_file_raises_config_error():
    _write_credentials('["not", "an", "object"]')

    with pytest.raises(ECOSConfigError, match="JSON object"):
        resolve_api_key(None)


def test_file_present_but_key_blank_falls_through():
    _write_credentials('{"ECOS_API_KEY": ""}')

    with pytest.raises(ECOSConfigError):  # blank is treated as absent
        resolve_api_key(None)


def test_credentials_path_honors_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert credentials_path() == tmp_path / "pyecos" / "credentials.json"


def test_blank_environment_key_falls_through_to_file(monkeypatch):
    # An exported-but-empty ECOS_API_KEY is treated as absent, not as a blank key.
    monkeypatch.setenv("ECOS_API_KEY", "")
    _write_credentials('{"ECOS_API_KEY": "FROMFILE"}')

    assert resolve_api_key(None) == "FROMFILE"


def test_unreadable_credentials_file_raises_config_error():
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()  # a directory where the file should be -> OSError on read
    with pytest.raises(ECOSConfigError, match="could not read"):
        resolve_api_key(None)


def test_non_string_key_value_is_treated_as_absent():
    _write_credentials('{"ECOS_API_KEY": 123}')
    with pytest.raises(ECOSConfigError):
        resolve_api_key(None)
