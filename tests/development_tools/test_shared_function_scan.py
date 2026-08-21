"""Tests for the shared function-analysis parse used by the audit pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from typing import cast

from development_tools.functions.analyze_functions import (
    scan_all_functions,
    scan_all_python_files,
)
from development_tools.functions.analyze_unused_functions import analyze_unused_functions
from development_tools.functions.shared_function_scan import (
    SharedFunctionScan,
    build_shared_function_scan,
    collect_python_files,
)
from development_tools.shared.service import AIToolsService


@pytest.mark.unit
def test_shared_scan_parses_each_file_once(tmp_path: Path, monkeypatch):
    pkg = tmp_path / "core"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (pkg / "mod.py").write_text("def work():\n    helper()\n", encoding="utf-8")
    (tmp_path / "run_mhm.py").write_text("def main():\n    return 0\n", encoding="utf-8")

    reads = {"n": 0}
    original_read = Path.read_text
    root = tmp_path.resolve()

    def _counting_read(self, *args, **kwargs):
        if self.suffix == ".py":
            resolved = self.resolve()
            if root in resolved.parents or resolved.parent == root:
                reads["n"] += 1
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _counting_read)

    scan = build_shared_function_scan(
        tmp_path,
        include_tests=False,
        include_dev_tools=False,
        scan_directories=["core"],
        apply_exclusions=False,
    )
    first_reads = reads["n"]
    assert first_reads == len(scan.modules)
    assert first_reads >= 2

    functions = scan_all_functions(parsed_modules=scan.modules)
    files_index = scan_all_python_files(parsed_modules=scan.modules)
    unused = analyze_unused_functions(
        project_root=tmp_path,
        apply_exclusions=False,
        parsed_modules=scan.modules,
    )

    assert reads["n"] == first_reads
    assert any(func["name"] == "helper" for func in functions)
    assert any(key.endswith("mod.py") for key in files_index)
    assert unused["summary"]["total_definitions_scanned"] >= 2


@pytest.mark.unit
def test_collect_python_files_respects_include_flags(tmp_path: Path):
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "a.py").write_text("def a():\n    pass\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    (tmp_path / "development_tools").mkdir()
    (tmp_path / "development_tools" / "tool.py").write_text("def tool():\n    pass\n", encoding="utf-8")

    production = collect_python_files(
        tmp_path, scan_directories=["core"], apply_exclusions=False
    )
    with_tests = collect_python_files(
        tmp_path,
        include_tests=True,
        scan_directories=["core"],
        apply_exclusions=False,
    )
    with_dev = collect_python_files(
        tmp_path,
        include_dev_tools=True,
        scan_directories=["core"],
        apply_exclusions=False,
    )

    assert any(path.name == "a.py" for path in production)
    assert not any(path.name == "test_a.py" for path in production)
    assert any(path.name == "test_a.py" for path in with_tests)
    assert any(path.name == "tool.py" for path in with_dev)


@pytest.mark.unit
def test_wrapper_consumers_reuse_shared_scan_modules(temp_project_copy, monkeypatch):
    service = AIToolsService(project_root=str(temp_project_copy))
    fake_modules = object()

    class _Scan:
        modules = fake_modules

    service._shared_function_scan = cast(SharedFunctionScan, _Scan())
    captured: dict[str, object] = {}

    import development_tools.functions.analyze_duplicate_functions as dup_mod
    import development_tools.functions.analyze_unused_functions as unused_mod
    import development_tools.functions.analyze_facade_shims as facade_mod
    import development_tools.functions.analyze_module_refactor_candidates as refactor_mod

    monkeypatch.setattr(dup_mod, "_get_analysis_config", lambda: {}, raising=True)
    monkeypatch.setattr(
        dup_mod,
        "_gather_function_records",
        lambda **kwargs: captured.update({"dup": kwargs.get("parsed_modules")}) or ([], {}),
        raising=True,
    )
    monkeypatch.setattr(
        dup_mod,
        "_analyze_duplicates",
        lambda *_a, **_k: {"summary": {"total_issues": 0}, "details": {}},
        raising=True,
    )
    monkeypatch.setattr(
        unused_mod,
        "analyze_unused_functions",
        lambda **kwargs: captured.update({"unused": kwargs.get("parsed_modules")})
        or {"summary": {"total_issues": 0}, "details": {}},
        raising=True,
    )
    monkeypatch.setattr(
        facade_mod,
        "analyze_project",
        lambda **kwargs: captured.update({"facade": kwargs.get("parsed_modules")})
        or {"summary": {"total_issues": 0}, "details": {}},
        raising=True,
    )
    monkeypatch.setattr(
        refactor_mod,
        "_scan_and_evaluate",
        lambda **kwargs: captured.update({"refactor": kwargs.get("parsed_modules")})
        or {"summary": {"total_issues": 0}, "details": {}},
        raising=True,
    )
    import development_tools.shared.service.tool_wrappers as wrappers_mod

    monkeypatch.setattr(wrappers_mod, "save_tool_result", lambda *_a, **_k: None)

    assert service.run_analyze_duplicate_functions()["success"] is True
    assert service.run_analyze_unused_functions()["success"] is True
    assert service.run_analyze_facade_shims()["success"] is True
    assert service.run_analyze_module_refactor_candidates()["success"] is True
    assert captured["dup"] is fake_modules
    assert captured["unused"] is fake_modules
    assert captured["facade"] is fake_modules
    assert captured["refactor"] is fake_modules
