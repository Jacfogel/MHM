#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
Development-tools import boundary checker.

Ensures modules under development_tools/** only import approved core/business modules.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config  # type: ignore
    from development_tools.shared.standard_exclusions import (  # type: ignore
        should_exclude_file,
    )


logger = get_component_logger("development_tools")


APPROVED_CORE_IMPORT_PREFIXES: tuple[str, ...] = (
    "core.logger",
)


class DevToolsImportBoundaryChecker:
    """Analyze imports inside development_tools for boundary violations."""

    def __init__(self, project_root_path: str | None = None) -> None:
        if project_root_path:
            self.project_root = Path(project_root_path).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()

        self.dev_tools_root = self.project_root / "development_tools"

    def _iter_dev_tools_files(self) -> List[Path]:
        """Yield Python files under development_tools respecting exclusions."""
        if not self.dev_tools_root.exists():
            return []

        results: List[Path] = []
        for py_file in self.dev_tools_root.rglob("*.py"):
            rel = py_file.relative_to(self.project_root)
            rel_str = str(rel).replace("\\", "/")
            if should_exclude_file(rel_str, tool_type="analysis", context="development"):
                continue
            results.append(py_file)
        return results

    def _extract_import_modules(self, file_path: Path) -> List[str]:
        """Return fully qualified modules imported in file."""
        modules: List[str] = []
        try:
            text = file_path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(file_path))
        except Exception as exc:
            logger.debug(f"Skipping {file_path} due to parse error: {exc}")
            return modules

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name:
                        modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.append(node.module)
        return modules

    def _is_approved_core_import(self, module_name: str) -> bool:
        """True if module_name is in the approved core import allowlist."""
        if not module_name:
            return False
        return module_name.startswith(APPROVED_CORE_IMPORT_PREFIXES)

    def _is_dev_tools_file(self, rel_path: str) -> bool:
        return rel_path.startswith("development_tools/")

    def analyze(self) -> Dict[str, Any]:
        """Return standard-format result with import-boundary violations."""
        violations: List[Dict[str, str]] = []

        files = self._iter_dev_tools_files()
        for file_path in files:
            rel = file_path.relative_to(self.project_root)
            rel_str = str(rel).replace("\\", "/")

            imported_modules = self._extract_import_modules(file_path)
            for module_name in imported_modules:
                # Only care about imports that cross into core.* or other business modules
                if module_name.startswith("core.") and not self._is_approved_core_import(
                    module_name
                ):
                    violations.append(
                        {
                            "file": rel_str,
                            "module": module_name,
                            "reason": "Non-approved core import inside development_tools",
                        }
                    )

        summary = {
            "total_violations": len(violations),
            "files_with_violations": len({v["file"] for v in violations}),
        }

        result: Dict[str, Any] = {
            "summary": {
                "total_issues": summary["total_violations"],
                "files_affected": summary["files_with_violations"],
            },
            "details": {
                "violations": violations,
                "summary": summary,
            },
        }
        return result


def main() -> int:
    """CLI entry point."""
    checker = DevToolsImportBoundaryChecker()
    result = checker.analyze()

    total = result["summary"]["total_issues"]
    files = result["summary"]["files_affected"]

    logger.debug(
        f"Development-tools import boundary check: {total} violation(s) across {files} file(s)"
    )

    for violation in result["details"]["violations"]:
        logger.warning(
            f"[IMPORT-BOUNDARY] {violation['file']} imports {violation['module']}: {violation['reason']}"
        )

    # Print JSON to stdout for audit orchestration if needed
    import json as _json

    print(_json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

