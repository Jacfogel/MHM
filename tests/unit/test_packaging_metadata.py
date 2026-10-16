"""Checks for the installable runtime contract declared in pyproject.toml."""

from pathlib import Path
import tomllib

import pytest

import core.resource_paths as resource_paths
from core.error_handling import error_handler
from core.resource_paths import (
    shipped_resource_path,
    shipped_style_path,
    shipped_website_path,
)


pytestmark = [pytest.mark.unit, pytest.mark.core]

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_project_metadata_declares_runtime_and_supported_python() -> None:
    metadata = tomllib.loads(
        (_PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    project = metadata["project"]
    assert project["requires-python"] == ">=3.11"
    assert project["dependencies"]
    assert {"dev", "ui"} <= set(project["optional-dependencies"])
    assert metadata["tool"]["pyright"]["pythonVersion"] == "3.11"


def test_shipped_runtime_assets_resolve_from_package_paths() -> None:
    assert shipped_resource_path("default_tags.json").is_file()
    assert shipped_resource_path("prompts", "assistant_system_prompt.txt").is_file()
    assert shipped_resource_path("default_messages", "motivational.json").is_file()
    assert (shipped_website_path() / "index.html").is_file()
    assert (shipped_website_path() / "fonts" / "inter-latin.woff2").is_file()
    assert shipped_style_path("admin_theme.qss").is_file()


@pytest.mark.parametrize(
    ("helper", "args", "operation"),
    [
        (
            shipped_resource_path,
            ("default_tags.json",),
            "resolving shipped resource path",
        ),
        (shipped_website_path, (), "resolving shipped website path"),
        (shipped_style_path, ("admin_theme.qss",), "resolving shipped style path"),
    ],
)
def test_shipped_path_helpers_report_and_reraise_unexpected_errors(
    monkeypatch: pytest.MonkeyPatch,
    helper,
    args: tuple[str, ...],
    operation: str,
) -> None:
    class BrokenPackageRoot:
        def joinpath(self, *parts: str) -> Path:
            raise RuntimeError("path resolution failed")

        def __truediv__(self, part: str) -> Path:
            raise RuntimeError("path resolution failed")

    handled: list[tuple[Exception, dict[str, object], str, bool]] = []

    def record_error(
        error: Exception,
        context: dict[str, object],
        operation_name: str,
        user_friendly: bool,
    ) -> bool:
        handled.append((error, context, operation_name, user_friendly))
        return False

    monkeypatch.setattr(resource_paths, "_PROJECT_PACKAGE_ROOT", BrokenPackageRoot())
    monkeypatch.setattr(error_handler, "handle_error", record_error)

    with pytest.raises(RuntimeError, match="path resolution failed"):
        helper(*args)

    assert len(handled) == 1
    error, context, operation_name, user_friendly = handled[0]
    assert isinstance(error, RuntimeError)
    assert context == {"function": helper.__name__}
    assert operation_name == operation
    assert user_friendly is False
