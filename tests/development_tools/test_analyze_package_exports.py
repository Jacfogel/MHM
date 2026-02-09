"""Tests for analyze_package_exports supporting tool."""

import shutil
import uuid
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.fixture
def exports_module():
    """Load analyze_package_exports module with dev tools loader."""
    return load_development_tools_module("functions.analyze_package_exports")


@pytest.mark.unit
def test_extract_imports_from_file_collects_imports_and_module_items(exports_module):
    """extract_imports_from_file should capture imports and public module items."""
    temp_root = Path(__file__).parent.parent / "data" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = temp_root / f"tmp_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        sample = temp_path / "sample.py"
        sample.write_text(
            "import os\n"
            "from core.config import Config\n"
            "\n"
            "def public_func():\n"
            "    return 1\n"
            "\n"
            "class PublicClass:\n"
            "    def method(self):\n"
            "        return 2\n"
            "\n"
            "class _Private:\n"
            "    pass\n",
            encoding="utf-8",
        )

        imports = exports_module.extract_imports_from_file(str(sample))
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)

    assert any(imp["module"] == "os" for imp in imports["direct_imports"])
    assert any(imp["module"] == "core.config" for imp in imports["from_imports"])
    assert {"name": "public_func", "type": "function"} in imports["module_items"]
    assert {"name": "PublicClass", "type": "class"} in imports["module_items"]
    assert all(item["name"] != "_Private" for item in imports["module_items"])


@pytest.mark.unit
def test_check_current_exports_reads_dunder_all_and_reexports(
    exports_module, monkeypatch
):
    """check_current_exports should include __all__ and re-exported symbols."""
    temp_root = Path(__file__).parent.parent / "data" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = temp_root / f"tmp_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        package_dir = temp_path / "alpha"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text(
            "__all__ = ['Foo']\nfrom alpha.module import Bar as Baz\n",
            encoding="utf-8",
        )
        (package_dir / "module.py").write_text(
            "class Bar:\n    pass\n", encoding="utf-8"
        )

        monkeypatch.setattr(exports_module, "project_root", temp_path, raising=False)

        exports = exports_module.check_current_exports("alpha")
        assert "Foo" in exports
        assert "Baz" in exports
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.mark.unit
def test_generate_audit_report_finds_missing_exports(
    exports_module, monkeypatch
):
    """generate_audit_report should flag public API missing from __all__."""
    temp_root = Path(__file__).parent.parent / "data" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp_path = temp_root / f"tmp_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True, exist_ok=True)
    try:
        package_dir = temp_path / "alpha"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
        (package_dir / "module.py").write_text(
            "def public_func():\n    return 1\n",
            encoding="utf-8",
        )

        # File that imports the public function to simulate usage
        (temp_path / "consumer.py").write_text(
            "from alpha.module import public_func\n",
            encoding="utf-8",
        )

        docs_dir = temp_path / "development_docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "FUNCTION_REGISTRY_DETAIL.md").write_text(
            "#### `alpha/module.py`\n"
            "**Functions:**\n"
            "- [OK] `public_func()` - Example\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(exports_module, "project_root", temp_path, raising=False)
        monkeypatch.setattr(
            exports_module,
            "should_exclude_file",
            lambda *args, **kwargs: False,
            raising=False,
        )

        report = exports_module.generate_audit_report("alpha")

        assert "public_func" in report["missing_exports"]
        assert report["should_export_count"] >= 1
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)
