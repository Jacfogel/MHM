"""Unit coverage for storage.user_data_read field filtering helpers."""

from __future__ import annotations

import pytest

from storage.user_data_read import _apply_fields_filter


@pytest.mark.unit
@pytest.mark.storage
class TestApplyFieldsFilter:
    def test_none_fields_returns_data_unchanged(self):
        data = {"timezone": "UTC", "email": "a@b.com"}
        assert _apply_fields_filter(data, "account", None) == data

    def test_string_field_extracts_single_key(self):
        data = {"timezone": "UTC", "email": "a@b.com"}
        assert _apply_fields_filter(data, "account", "timezone") == "UTC"

    def test_list_fields_extracts_subset(self):
        data = {"timezone": "UTC", "email": "a@b.com", "phone": "555"}
        result = _apply_fields_filter(data, "account", ["timezone", "missing"])
        assert result == {"timezone": "UTC"}

    def test_list_fields_returns_none_when_no_matches(self):
        assert _apply_fields_filter({"a": 1}, "account", ["b"]) is None

    def test_dict_fields_scoped_by_data_type(self):
        data = {"channel": {"type": "email"}, "categories": ["health"]}
        fields: dict[str, str | list[str]] = {
            "preferences": "channel",
            "account": "categories",
        }
        assert _apply_fields_filter(data, "preferences", fields) == {
            "type": "email"
        }

    def test_dict_fields_list_under_data_type(self):
        data = {"channel": {"type": "email"}, "categories": ["health"]}
        fields: dict[str, str | list[str]] = {
            "preferences": ["channel", "categories"],
        }
        assert _apply_fields_filter(data, "preferences", fields) == data

    def test_non_dict_data_with_string_field_returns_none(self):
        assert _apply_fields_filter("not-a-dict", "account", "timezone") is None
