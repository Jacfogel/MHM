"""Domain marker policy when test_markers.domain_markers is configured."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools import config
from development_tools.tests.analyze_test_markers import MissingMarkerFinder, TestMarkerAnalyzer


@pytest.mark.unit
def test_domain_marker_union_matches_domain_mapper_markers() -> None:
    """Default union is the sorted set of markers from domain_mapper.source_to_test_mapping."""
    config.load_external_config()
    union = set(config.domain_marker_union_from_domain_mapper())
    assert "core" in union
    assert "communication" in union
    assert "ui" in union
    assert "tasks" in union
    assert "unit" not in union
    assert "integration" not in union
    assert "critical" not in union
    tm = config.get_test_markers_config()
    assert tm.get("use_domain_mapper_marker_union") is True
    assert set(tm.get("domain_markers") or []) == union


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
def test_directory_only_exempt_skips_domain_marker_requirement(tmp_path: Path) -> None:
    """tests/development_tools/ has no domain markers in mapper — exempt from pytest domain marks."""
    p = tmp_path / "tests" / "development_tools" / "test_x.py"
    p.parent.mkdir(parents=True)
    p.write_text(
        "import pytest\n\n@pytest.mark.unit\ndef test_foo():\n    assert True\n",
        encoding="utf-8",
    )
    finder = MissingMarkerFinder(
        category_markers=("unit", "integration", "behavior", "ui"),
        domain_markers=("communication", "ui"),
        project_root=tmp_path,
        exempt_rel_prefixes=("tests/development_tools/",),
    )
    finder.analyze_file(p)
    assert finder.missing == []
    assert finder.missing_domain == []


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
    summary = finder.domain_attribution_summary()
    assert summary["domain_enforced_test_functions"] == 1
    assert summary["domain_marked_test_functions"] == 1
    assert summary["domain_unmarked_test_functions"] == 0


@pytest.mark.unit
def test_domain_attribution_summary_via_analyzer_ast_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """JSON consumers can read domain_attribution_summary after AST scan (TEST_PLAN §4.4)."""
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    fa = tests_dir / "test_a.py"
    fb = tests_dir / "test_b.py"
    fa.write_text(
        "import pytest\n\n@pytest.mark.unit\n@pytest.mark.core\ndef test_one():\n    assert True\n",
        encoding="utf-8",
    )
    fb.write_text(
        "import pytest\n\n@pytest.mark.unit\ndef test_two():\n    assert True\n",
        encoding="utf-8",
    )

    def _fixed_find(self: TestMarkerAnalyzer, exclude_ai: bool = True) -> list[Path]:
        return sorted([fa, fb])

    monkeypatch.setattr(TestMarkerAnalyzer, "find_test_files", _fixed_find)
    analyzer = TestMarkerAnalyzer(project_root=tmp_path)
    analyzer.find_missing_markers_ast()
    summary = analyzer.get_domain_attribution_summary()
    assert summary["domain_enforced_test_functions"] == 2
    assert summary["domain_marked_test_functions"] == 1
    assert summary["domain_unmarked_test_functions"] == 1
