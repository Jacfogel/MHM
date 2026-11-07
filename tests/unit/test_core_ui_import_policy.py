"""Keep core independent from the admin UI without importing either package."""

import pytest

from tests.test_helpers.source_policy import core_ui_violations, product_sources

pytestmark = [pytest.mark.unit, pytest.mark.user]


def test_core_does_not_import_ui():
    violations = [
        v
        for path, source in product_sources()
        if path.startswith("core/")
        for v in core_ui_violations(source, path)
    ]
    assert not violations, "\n".join(violations)


@pytest.mark.parametrize(
    "source",
    [
        "import ui",
        "import ui.widgets as widgets",
        "from ui.dialogs import Dialog",
        "from ui import dialogs",
        "if TYPE_CHECKING:\n    from ui import Dialog",
        "def launch():\n    import ui.dialogs",
        "import importlib as loader\nloader.import_module('ui.dialogs')",
        "from importlib import import_module as load\nload('ui')",
        "__import__('ui.dialogs')",
    ],
)
def test_ui_import_forms_are_rejected(source):
    assert core_ui_violations(source, "core/example.py")


@pytest.mark.parametrize(
    "source",
    [
        "from . import utilities",
        "from .ui_helpers import helper",
        "from core.ui_helpers import helper",
        "text = 'import ui' # import ui.widgets",
    ],
)
def test_unrelated_imports_comments_and_strings_are_allowed(source):
    assert not core_ui_violations(source, "core/example.py")


def test_ui_can_import_ui_outside_core():
    assert not core_ui_violations("import ui.widgets", "ui/example.py")
