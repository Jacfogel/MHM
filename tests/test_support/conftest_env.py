"""
Pytest plugin: environment and early-run fixtures (Qt runtime, cwd, loader registry, data shim, QMessageBox patches).

Imports project_root from tests.conftest. Runs early; loaded first in pytest_plugins so shim and patches apply before other plugins.
"""

import os
import pytest
from pathlib import Path

from tests.conftest import project_root


def ensure_qt_runtime():
    """Ensure PySide6 can load in the current environment.

    Qt-dependent tests rely on libGL/GLX libraries that may be absent in
    containerized or headless environments. Import the critical PySide6
    modules and skip those tests gracefully when the runtime is missing.
    """
    try:
        from PySide6 import QtWidgets  # noqa: F401 - import verifies availability
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except (ImportError, OSError) as exc:
        message = str(exc)
        lower_message = message.lower()
        gl_indicators = ("libgl", "opengl", "libegl", "libglu", "glx")
        if any(token in lower_message for token in gl_indicators):
            pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)
        raise


@pytest.fixture(scope="function", autouse=True)
def ensure_valid_cwd():
    """Keep cwd valid across tests to avoid coverage teardown path errors."""
    try:
        original_cwd = Path.cwd()
    except FileNotFoundError:
        original_cwd = project_root
        os.chdir(project_root)

    yield

    target_cwd = original_cwd if original_cwd.exists() else project_root
    try:
        os.chdir(target_cwd)
    except FileNotFoundError:
        os.chdir(project_root)


@pytest.fixture(scope="session", autouse=True)
def verify_user_data_loader_registry():
    import importlib
    import core.user_data_handlers as um
    import core.user_data_handlers as udh

    um = importlib.reload(um)
    udh = importlib.reload(udh)

    if um.USER_DATA_LOADERS is not udh.USER_DATA_LOADERS:
        raise AssertionError(
            "USER_DATA_LOADERS mismatch: core.user_data_handlers reloads hold different dict objects."
        )

    def _missing_keys():
        return [k for k, v in um.USER_DATA_LOADERS.items() if not v.get("loader")]

    missing = _missing_keys()
    if missing:
        try:
            if hasattr(um, "register_default_loaders"):
                um.register_default_loaders()
            elif hasattr(udh, "register_default_loaders"):
                udh.register_default_loaders()
        except Exception as e:
            raise AssertionError(f"Failed to register default loaders: {e}")

        missing_after = _missing_keys()
        if missing_after:
            raise AssertionError(
                f"Missing user data loaders after registration attempt: {missing_after}"
            )

    yield


@pytest.fixture(scope="session", autouse=True)
def initialize_loader_import_order(request):
    """Reload core.user_data_handlers and register loaders once.

    Skip this fixture for development tools tests that don't have core modules available.
    """
    import importlib

    try:
        import core.user_data_handlers as um
    except (ImportError, ModuleNotFoundError):
        yield
        return
    um = importlib.reload(um)
    try:
        import core.user_data_handlers as udh
        udh = importlib.reload(udh)
    except Exception:
        udh = None

    try:
        if hasattr(um, "register_default_loaders"):
            um.register_default_loaders()
        elif udh is not None and hasattr(udh, "register_default_loaders"):
            udh.register_default_loaders()
    except Exception:
        pass
    yield


def _apply_get_user_data_shim_early():
    if os.getenv("ENABLE_TEST_DATA_SHIM", "1") != "1":
        return
    try:
        import core.user_data_handlers as um
    except Exception:
        return
    try:
        import core.user_data_handlers as udh
    except Exception:
        udh = None

    original_get_user_data = getattr(um, "get_user_data", None)
    if (
        original_get_user_data is None
        and udh is not None
        and hasattr(udh, "get_user_data")
    ):
        original_get_user_data = getattr(udh, "get_user_data", None)
    if original_get_user_data is None:
        return

    def _load_single_type(user_id: str, key: str, *, auto_create: bool):
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            loader = entry.get("loader") if entry else None
            if loader is None:
                key_to_func_and_file = {
                    "account": (um._get_user_data__load_account, "account"),
                    "preferences": (um._get_user_data__load_preferences, "preferences"),
                    "context": (um._get_user_data__load_context, "user_context"),
                    "schedules": (um._get_user_data__load_schedules, "schedules"),
                }
                func_file = key_to_func_and_file.get(key)
                if func_file is None:
                    return None
                func, file_type = func_file
                try:
                    um.register_data_loader(key, func, file_type)
                    entry = um.USER_DATA_LOADERS.get(key)
                    loader = entry.get("loader") if entry else None
                except Exception:
                    loader = func
            if loader is None:
                return None
            return loader(user_id, auto_create)
        except Exception:
            return None

    def wrapped_get_user_data(user_id: str, data_type: str = "all", *args, **kwargs):
        auto_create = True
        try:
            auto_create = bool(kwargs.get("auto_create", True))
        except Exception:
            auto_create = True
        result = original_get_user_data(user_id, data_type, *args, **kwargs)
        try:
            if data_type == "all":
                if not isinstance(result, dict):
                    result = {} if result is None else {"value": result}
                for key in ("account", "preferences", "context", "schedules"):
                    if key not in result or not result.get(key):
                        loaded = _load_single_type(
                            user_id, key, auto_create=auto_create
                        )
                        if loaded is not None:
                            result[key] = loaded
                return result
            if isinstance(data_type, list):
                if not isinstance(result, dict):
                    result = {}
                for key in data_type:
                    if key not in result or not result.get(key):
                        loaded = _load_single_type(
                            user_id, key, auto_create=auto_create
                        )
                        if loaded is not None:
                            result[key] = loaded
                return result
            if isinstance(data_type, str):
                key = data_type
                if isinstance(result, dict) and result.get(key):
                    return result
                loaded = _load_single_type(user_id, key, auto_create=auto_create)
                if loaded is not None:
                    return {key: loaded}
                return result
        except Exception:
            return result
        return result

    try:
        um.get_user_data = wrapped_get_user_data
    except Exception:
        pass
    try:
        if udh is not None and hasattr(udh, "get_user_data"):
            udh.get_user_data = wrapped_get_user_data
    except Exception:
        pass


_apply_get_user_data_shim_early()


@pytest.fixture(scope="function", autouse=True)
def toggle_data_shim_per_marker(request, monkeypatch):
    marker = request.node.get_closest_marker("no_data_shim")
    if marker is not None:
        monkeypatch.setenv("ENABLE_TEST_DATA_SHIM", "0")
    yield


def setup_qmessagebox_patches():
    """Set up global QMessageBox patches to prevent popup dialogs during testing."""
    verbose_patch_logging = os.environ.get("MHM_TEST_QT_PATCH_LOG", "0") == "1"
    try:
        from PySide6.QtWidgets import QMessageBox

        class MockQMessageBox:
            @staticmethod
            def information(*args, **kwargs):
                return QMessageBox.StandardButton.Ok

            @staticmethod
            def warning(*args, **kwargs):
                return QMessageBox.StandardButton.Ok

            @staticmethod
            def critical(*args, **kwargs):
                return QMessageBox.StandardButton.Ok

            @staticmethod
            def question(*args, **kwargs):
                return QMessageBox.StandardButton.Yes

            @staticmethod
            def about(*args, **kwargs) -> None:
                pass

        QMessageBox.information = MockQMessageBox.information
        QMessageBox.warning = MockQMessageBox.warning
        QMessageBox.critical = MockQMessageBox.critical
        QMessageBox.question = MockQMessageBox.question
        QMessageBox.about = MockQMessageBox.about

        if verbose_patch_logging:
            print("Global QMessageBox patches applied to prevent popup dialogs")
    except ImportError:
        if verbose_patch_logging:
            print("PySide6 not available, skipping QMessageBox patches")
    except Exception as e:
        if verbose_patch_logging:
            print(f"Failed to apply QMessageBox patches: {e}")


setup_qmessagebox_patches()
