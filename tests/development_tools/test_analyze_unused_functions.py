"""Unit tests for development_tools.functions.analyze_unused_functions helpers."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from development_tools.functions.analyze_unused_functions import (
    FunctionDef,
    _decorator_name,
    _is_implicitly_used,
    _is_init_export,
    _normalize_path,
    analyze_unused_functions,
)


@pytest.mark.unit
@pytest.mark.development_tools
def test_decorator_name_extracts_name_attribute_and_call():
    tree = ast.parse(
        "\n".join(
            [
                "@plain",
                "@mod.nested.dec",
                "@app.route('/x')",
                "def f():",
                "    pass",
            ]
        )
    )
    func = tree.body[0]
    assert isinstance(func, ast.FunctionDef)
    assert _decorator_name(func.decorator_list[0]) == "plain"
    assert _decorator_name(func.decorator_list[1]) == "mod.nested.dec"
    assert _decorator_name(func.decorator_list[2]) == "app.route"


@pytest.mark.unit
@pytest.mark.development_tools
def test_is_implicitly_used_by_name_prefix_and_decorator():
    main_tree = ast.parse("def main():\n    pass\n")
    main_fn = main_tree.body[0]
    assert isinstance(main_fn, ast.FunctionDef)
    assert _is_implicitly_used(main_fn) is True

    on_tree = ast.parse("def on_ready():\n    pass\n")
    on_fn = on_tree.body[0]
    assert isinstance(on_fn, ast.FunctionDef)
    assert _is_implicitly_used(on_fn) is True

    decorated = ast.parse(
        "@pytest.fixture\ndef sample():\n    return 1\n"
    )
    decorated_fn = decorated.body[0]
    assert isinstance(decorated_fn, ast.FunctionDef)
    assert _is_implicitly_used(decorated_fn) is True

    plain = ast.parse("def helper_unique_xyz():\n    return 1\n")
    plain_fn = plain.body[0]
    assert isinstance(plain_fn, ast.FunctionDef)
    assert _is_implicitly_used(plain_fn) is False


@pytest.mark.unit
@pytest.mark.development_tools
def test_normalize_path_and_init_export(tmp_path: Path):
    root = tmp_path
    nested = root / "pkg" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("def x():\n    pass\n", encoding="utf-8")
    assert _normalize_path(str(nested), root) == "pkg/mod.py"
    assert _normalize_path("C:/outside/file.py", root).replace("\\", "/").endswith(
        "outside/file.py"
    )

    init_def = FunctionDef(
        name="export_me",
        full_name="export_me",
        file_path="pkg/__init__.py",
        line=1,
        class_name=None,
        is_private=False,
        is_method=False,
    )
    other = FunctionDef(
        name="export_me",
        full_name="export_me",
        file_path="pkg/mod.py",
        line=1,
        class_name=None,
        is_private=False,
        is_method=False,
    )
    assert _is_init_export(init_def) is True
    assert _is_init_export(other) is False


@pytest.mark.unit
@pytest.mark.development_tools
def test_analyze_unused_functions_finds_uncalled_helper(tmp_path: Path, monkeypatch):
    """Mini project: one called helper and one unused private helper."""
    import development_tools.functions.analyze_unused_functions as unused_mod

    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "core" / "mod.py").write_text(
        "\n".join(
            [
                "def used_helper():",
                "    return 1",
                "",
                "def _never_called_unique_zzz():",
                "    return 2",
                "",
                "def entry():",
                "    return used_helper()",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(unused_mod.config, "get_project_root", lambda: str(tmp_path))
    monkeypatch.setattr(unused_mod.config, "get_scan_directories", lambda: ["core"])
    # Temp paths are often excluded by standard_exclusions; force-include for this unit test.
    monkeypatch.setattr(unused_mod, "should_exclude_file", lambda *_a, **_k: False)

    result = analyze_unused_functions(
        include_tests=False,
        include_dev_tools=False,
        include_private_only=True,
        max_results=50,
    )
    assert isinstance(result, dict)
    names = [u["name"] for u in result["details"]["unused_functions"]]
    assert "_never_called_unique_zzz" in names
    assert "used_helper" not in names
