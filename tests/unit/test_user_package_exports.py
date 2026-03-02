"""Unit tests for lazy exports in user package __init__."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.unit
@pytest.mark.user_management
class TestUserPackageExports:
    def test_lazy_export_user_context_manager_and_singleton(self):
        user_pkg = importlib.import_module("user")
        from user.context_manager import UserContextManager, user_context_manager

        assert user_pkg.UserContextManager is UserContextManager
        assert user_pkg.user_context_manager is user_context_manager

    def test_lazy_export_user_context(self):
        user_pkg = importlib.import_module("user")
        from user.user_context import UserContext

        assert user_pkg.UserContext is UserContext

    def test_lazy_export_user_preferences(self):
        user_pkg = importlib.import_module("user")
        from user.user_preferences import UserPreferences

        assert user_pkg.UserPreferences is UserPreferences

    def test_unknown_attribute_raises_attribute_error(self):
        user_pkg = importlib.import_module("user")
        with pytest.raises(AttributeError, match="has no attribute"):
            _ = user_pkg.NotARealExport
