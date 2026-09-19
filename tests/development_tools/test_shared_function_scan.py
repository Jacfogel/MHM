"""Tests for the shared function-analysis parse used by the audit pipeline."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

import pytest

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


def _patch_module_import_analyzer_scan(
    monkeypatch: pytest.MonkeyPatch, scan_impl
) -> None:
    """Patch ``scan_all_python_files`` on every loaded ModuleImportAnalyzer class."""
    for module in list(sys.modules.values()):
        if module is None:
            continue
        cls = getattr(module, "ModuleImportAnalyzer", None)
        if not isinstance(cls, type) or cls.__name__ != "ModuleImportAnalyzer":
            continue
        monkeypatch.setattr(cls, "scan_all_python_files", scan_impl, raising=False)


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

    from development_tools.error_handling.analyze_error_handling import (
        ErrorHandlingAnalyzer,
    )
    from development_tools.functions.analyze_function_registry import (
        collect_project_inventory,
    )
    from development_tools.functions.analyze_package_exports import (
        analyze_imports_for_packages,
        extract_imports_from_file,
    )
    from development_tools.imports.analyze_module_imports import ModuleImportAnalyzer

    ErrorHandlingAnalyzer(str(tmp_path)).analyze_project(
        parsed_modules=scan.modules
    )
    collect_project_inventory([], parsed_modules=scan.modules)
    analyze_imports_for_packages(["core"], parsed_modules=scan.modules)
    for module in scan.modules:
        extract_imports_from_file(
            str(module.path), source=module.source, tree=module.tree
        )
    ModuleImportAnalyzer(project_root=str(tmp_path)).scan_all_python_files(
        parsed_modules=scan.modules
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
    import development_tools.error_handling.analyze_error_handling as error_mod
    import development_tools.functions.analyze_function_registry as registry_mod
    import development_tools.functions.analyze_package_exports as exports_mod

    wrappers_globals = service.run_analyze_module_imports.__func__.__globals__

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
    monkeypatch.setitem(
        wrappers_globals, "save_tool_result", lambda *_a, **_k: None
    )

    class _ErrorAnalyzer:
        def __init__(self, *_args, **_kwargs):
            pass

        def analyze_project(self, **kwargs):
            captured["error"] = kwargs.get("parsed_modules")
            return {"summary": {"total_issues": 0}, "details": {}}

    class _ImportAnalyzer:
        def __init__(self, *_args, **_kwargs):
            pass

        def scan_all_python_files(self, parsed_modules=None):
            captured["imports"] = parsed_modules
            return {}

    monkeypatch.setattr(error_mod, "ErrorHandlingAnalyzer", _ErrorAnalyzer, raising=True)
    monkeypatch.setattr(
        registry_mod,
        "execute",
        lambda *_a, **kwargs: captured.update(
            {"registry": kwargs.get("parsed_modules")}
        )
        or (0, "", {"summary": {"total_issues": 0}, "details": {}}),
        raising=True,
    )
    monkeypatch.setattr(
        exports_mod,
        "analyze_imports_for_packages",
        lambda packages, parsed_modules=None: captured.update(
            {"exports_imports": parsed_modules}
        )
        or {pkg: {} for pkg in packages},
        raising=True,
    )
    monkeypatch.setattr(
        exports_mod,
        "scan_package_modules_for_packages",
        lambda packages, parsed_modules=None: captured.update(
            {"exports_api": parsed_modules}
        )
        or {pkg: {} for pkg in packages},
        raising=True,
    )
    monkeypatch.setattr(
        exports_mod,
        "parse_function_registry_for_packages",
        lambda packages: {pkg: set() for pkg in packages},
        raising=True,
    )
    monkeypatch.setattr(
        exports_mod,
        "generate_audit_report",
        lambda package, *_a, **_k: {
            "package": package,
            "missing_exports": [],
            "potentially_unnecessary": [],
        },
        raising=True,
    )
    monkeypatch.setitem(
        wrappers_globals, "_module_import_analyzer_class", lambda: _ImportAnalyzer
    )
    _patch_module_import_analyzer_scan(
        monkeypatch, _ImportAnalyzer.scan_all_python_files
    )

    assert service.run_analyze_duplicate_functions()["success"] is True
    assert service.run_analyze_unused_functions()["success"] is True
    assert service.run_analyze_facade_shims()["success"] is True
    assert service.run_analyze_module_refactor_candidates()["success"] is True
    assert service.run_analyze_error_handling()["success"] is True
    assert service.run_analyze_function_registry()["success"] is True
    assert service.run_analyze_package_exports()["success"] is True
    imports_result = service.run_analyze_module_imports()
    assert imports_result.get("success") is True, imports_result.get("error")
    assert captured["dup"] is fake_modules
    assert captured["unused"] is fake_modules
    assert captured["facade"] is fake_modules
    assert captured["refactor"] is fake_modules
    assert captured["error"] is fake_modules
    assert captured["registry"] is fake_modules
    assert captured["exports_imports"] is fake_modules
    assert captured["exports_api"] is fake_modules
    assert captured["imports"] is fake_modules


@pytest.mark.unit
def test_module_imports_wrapper_ignores_stale_sys_modules_analyzer(
    temp_project_copy, monkeypatch
):
    """The wrapper must use the bound method's globals, not whichever copy sits in sys.modules."""
    service = AIToolsService(project_root=str(temp_project_copy))
    fake_modules = object()

    class _Scan:
        modules = fake_modules

    service._shared_function_scan = cast(SharedFunctionScan, _Scan())
    captured: dict[str, object] = {}

    class _ImportAnalyzer:
        def __init__(self, *_args, **_kwargs):
            pass

        def scan_all_python_files(self, parsed_modules=None):
            captured["imports"] = parsed_modules
            return {}

    class _HostileAnalyzer:
        def __init__(self, *_args, **_kwargs):
            pass

        def scan_all_python_files(self, parsed_modules=None):
            if parsed_modules is None:
                raise TypeError("'NoneType' object is not iterable")
            for _module in parsed_modules:
                pass
            return {}

    hostile = type(sys)("hostile_analyze_module_imports")
    hostile.ModuleImportAnalyzer = _HostileAnalyzer
    monkeypatch.setitem(
        sys.modules, "development_tools.imports.analyze_module_imports", hostile
    )

    wrappers_globals = service.run_analyze_module_imports.__func__.__globals__
    monkeypatch.setitem(
        wrappers_globals, "_module_import_analyzer_class", lambda: _ImportAnalyzer
    )
    monkeypatch.setitem(wrappers_globals, "save_tool_result", lambda *_a, **_k: None)

    result = service.run_analyze_module_imports()
    assert result.get("success") is True, result.get("error")
    assert captured["imports"] is fake_modules
