"""Domain marker advisory gaps (V5 §5.7) when test_markers.domain_markers is configured."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.tests.analyze_test_markers import MissingMarkerFinder


@pytest.mark.unit
def test_domain_gap_when_domain_markers_configured(tmp_path: Path) -> None:
    p = tmp_path / "test_sample.py"
    p.write_text(
        "import pytest\n\n@pytest.mark.unit\ndef test_foo():\n    assert True\n",
        encoding="utf-8",
    )
    finder = MissingMarkerFinder(
        category_markers=("unit", "integration", "behavior", "ui"),
        domain_markers=("core",),
    )
    finder.analyze_file(p)
    assert finder.missing == []
    assert len(finder.missing_domain) == 1
    assert finder.missing_domain[0][2] == "test_foo"


@pytest.mark.unit
def test_no_domain_gap_when_core_present(tmp_path: Path) -> None:
    p = tmp_path / "test_sample.py"
    p.write_text(
        "import pytest\n\n@pytest.mark.unit\n@pytest.mark.core\ndef test_foo():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    finder = MissingMarkerFinder(
        category_markers=("unit", "integration", "behavior", "ui"),
        domain_markers=("core",),
    )
    finder.analyze_file(p)
    assert finder.missing == []
    assert finder.missing_domain == []
