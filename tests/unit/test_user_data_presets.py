"""Unit coverage for storage.user_data_presets."""

from __future__ import annotations

import pytest

from storage import user_data_presets as presets


@pytest.mark.unit
@pytest.mark.storage
def test_get_predefined_options_returns_field_values():
    presets._PRESETS_CACHE = None
    options = presets.get_predefined_options("pronouns")

    assert isinstance(options, list)
    assert "they/them" in options


@pytest.mark.unit
@pytest.mark.storage
def test_get_predefined_options_unknown_field_returns_empty_list():
    assert presets.get_predefined_options("not_a_real_field") == []


@pytest.mark.unit
@pytest.mark.storage
def test_load_presets_json_falls_back_when_file_missing(monkeypatch):
    presets._PRESETS_CACHE = None

    def fake_open(*args, **kwargs):
        raise FileNotFoundError("missing presets.json")

    monkeypatch.setattr("builtins.open", fake_open)

    loaded = presets._load_presets_json()

    assert loaded is presets.PREDEFINED_OPTIONS
    presets._PRESETS_CACHE = None


@pytest.mark.unit
@pytest.mark.storage
def test_get_timezone_options_uses_pytz_when_available():
    zones = presets.get_timezone_options()

    assert isinstance(zones, list)
    assert "UTC" in zones


@pytest.mark.unit
@pytest.mark.storage
def test_get_timezone_options_falls_back_without_pytz(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pytz":
            raise ImportError("no pytz")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    zones = presets.get_timezone_options()

    assert zones == presets.TIMEZONE_OPTIONS
