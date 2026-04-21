#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable
from __future__ import annotations

"""
analyze_test_markers.py
Analyze test files for pytest marker usage (read-only analysis).
For fixing operations, use fix_test_markers.py.

**Marker kinds (policy):**

- **Category** (suite layer): ``unit``, ``integration``, ``behavior``, ``ui`` — align with
  ``tests/<subdir>/`` layout and selective runs by suite type.
- **Quality / tier** (optional): e.g. ``critical``, ``smoke``, ``regression`` — not product domains.
- **Domain** (product / source area): the eight areas in ``domain_mapper`` (``core``,
  ``communication``, ``ui``, ``tasks``, ``ai``, ``user``, ``notebook``, ``development_tools``).
  Typical **domain-attribution** pytest names include ``communication``, ``ai``, ``tasks``,
  ``notebook``, ``user_management``, etc. **Categories** are ``unit``, ``integration``,
  ``behavior``, ``ui``; **tier** markers include ``critical``, ``smoke``, ``regression``. Those are
  not the same thing as the eight **product domains** (though ``ui`` doubles as a category label and
  a product area).

**Analyzer config:** ``get_test_markers_config()`` fills ``domain_markers`` from
``domain_marker_union_from_domain_mapper()``, which unions marker strings in
``source_to_test_mapping``’s marker lists. Policy is that those lists contain only
product-domain attribution marks (no category/tier aliases). Exceptions: **directory-only** mappings (empty marker list,
e.g. ``development_tools``) skip domain enforcement. Set
``test_markers.use_domain_mapper_marker_union`` to false and ``domain_markers`` to ``[]`` to
disable domain-marker enforcement.
"""

import sys
import re
import ast
from pathlib import Path
from re import Pattern

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
    from ..shared.common import ProjectPaths
    from ..shared.constants import (
        TEST_CATEGORY_MARKERS,
        TEST_MARKER_AI_PATH_TOKENS,
        TEST_MARKER_DIRECTORY_MAP,
        TEST_MARKER_TRANSIENT_PATH_MARKERS,
    )
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file
    from development_tools.shared.common import ProjectPaths
    from development_tools.shared.constants import (
        TEST_CATEGORY_MARKERS,
        TEST_MARKER_AI_PATH_TOKENS,
        TEST_MARKER_DIRECTORY_MAP,
        TEST_MARKER_TRANSIENT_PATH_MARKERS,
    )

from core.logger import get_component_logger

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class TestMarkerAnalyzer:
    """Analyze and manage pytest category markers in test files."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = (project_root or Path(config.get_project_root())).resolve()

        paths = ProjectPaths(root=self.project_root)
        self.test_dir = paths.tests
        self.tests_data_dir = paths.tests_data
        self.tests_dir_rel = self._normalize_rel_path(
            str(config.get_external_value("paths.tests_dir", "tests"))
        )
        self.tests_data_dir_rel = self._normalize_rel_path(
            str(
                config.get_external_value(
                    "paths.tests_data_dir", f"{self.tests_dir_rel}/data"
                )
            )
        )
        test_markers_config = (
            config.get_test_markers_config()
            if hasattr(config, "get_test_markers_config")
            else {}
        )

        configured_categories = test_markers_config.get(
            "categories", list(TEST_CATEGORY_MARKERS)
        )
        if not isinstance(configured_categories, list) or not configured_categories:
            configured_categories = list(TEST_CATEGORY_MARKERS)
        self.category_markers: tuple[str, ...] = tuple(
            str(marker).strip() for marker in configured_categories if str(marker).strip()
        )
        if not self.category_markers:
            self.category_markers = TEST_CATEGORY_MARKERS

        self.category_marker_patterns: list[Pattern[str]] = [
            re.compile(rf"@pytest\.mark\.{re.escape(marker)}\b")
            for marker in self.category_markers
        ]

        configured_dir_map = test_markers_config.get(
            "directory_to_marker", TEST_MARKER_DIRECTORY_MAP
        )
        if not isinstance(configured_dir_map, dict) or not configured_dir_map:
            configured_dir_map = TEST_MARKER_DIRECTORY_MAP
        self.directory_to_marker: dict[str, str] = {
            str(directory).strip("/\\"): str(marker).strip()
            for directory, marker in configured_dir_map.items()
            if str(directory).strip("/\\") and str(marker).strip()
        }
        if not self.directory_to_marker:
            self.directory_to_marker = dict(TEST_MARKER_DIRECTORY_MAP)

        configured_transient_markers = test_markers_config.get(
            "transient_data_path_markers",
            list(TEST_MARKER_TRANSIENT_PATH_MARKERS),
        )
        if not isinstance(configured_transient_markers, list):
            configured_transient_markers = list(TEST_MARKER_TRANSIENT_PATH_MARKERS)
        self.transient_data_path_markers: tuple[str, ...] = tuple(
            str(marker).replace("\\", "/")
            for marker in configured_transient_markers
            if str(marker).strip()
        ) or TEST_MARKER_TRANSIENT_PATH_MARKERS

        configured_ai_tokens = test_markers_config.get(
            "ai_path_tokens",
            list(TEST_MARKER_AI_PATH_TOKENS),
        )
        if not isinstance(configured_ai_tokens, list):
            configured_ai_tokens = list(TEST_MARKER_AI_PATH_TOKENS)
        self.ai_path_tokens: tuple[str, ...] = tuple(
            str(token).replace("\\", "/")
            for token in configured_ai_tokens
            if str(token).strip()
        ) or TEST_MARKER_AI_PATH_TOKENS

        dm = test_markers_config.get("domain_markers", [])
        if isinstance(dm, list) and dm:
            self.domain_markers: tuple[str, ...] = tuple(
                str(x).strip() for x in dm if str(x).strip()
            )
        else:
            self.domain_markers = ()

        self._last_marker_finder: MissingMarkerFinder | None = None

    def _directory_only_domain_exempt_prefixes(self) -> tuple[str, ...]:
        """Repo-relative path prefixes where domain_mapper has test dirs but no pytest markers."""
        raw = config.get_domain_mapper_config()
        stm = raw.get("source_to_test_mapping") or {}
        out: list[str] = []
        for _name, val in stm.items():
            if not isinstance(val, (list, tuple)) or len(val) < 2:
                continue
            test_dirs, markers = val[0], val[1]
            mlist = list(markers) if isinstance(markers, (list, tuple)) else []
            if mlist:
                continue
            for td in test_dirs or []:
                t = str(td).strip().replace("\\", "/").strip("/")
                if t:
                    out.append(f"{t}/")
        return tuple(sorted(set(out)))

    @staticmethod
    def _normalize_rel_path(path_value: str) -> str:
        """Normalize relative path strings for cross-platform substring matching."""
        return path_value.replace("\\", "/").strip("/")

    def _is_under_tests_data_dir(self, normalized_file_path: str) -> bool:
        """Return True if file path points to configured tests data directory."""
        marker = f"/{self.tests_data_dir_rel}/"
        return marker in normalized_file_path or normalized_file_path.startswith(
            f"{self.tests_data_dir_rel}/"
        )

    def find_test_files(self, exclude_ai: bool = True) -> list[Path]:
        """Find all test files in the tests directory."""
        test_files = []
        if not self.test_dir.exists():
            return test_files

        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.is_file():
                file_str = str(test_file).replace("\\", "/")
                relative_path = str(test_file.relative_to(self.project_root)).replace(
                    "\\", "/"
                )

                # Apply shared exclusions so tests/data, scripts, caches, etc.
                # stay consistent with other analyzer tools.
                if should_exclude_file(
                    relative_path, tool_type="analysis", context="development"
                ):
                    continue

                # Skip AI test files if requested
                if exclude_ai and any(token in file_str for token in self.ai_path_tokens):
                    continue

                # Skip temporary test files in tests/data/ (pytest temporary directories)
                if self._is_under_tests_data_dir(file_str) and any(
                    marker in file_str
                    for marker in self.transient_data_path_markers
                ):
                    continue

                test_files.append(test_file)

        return sorted(test_files)

    def has_category_marker(self, content: str) -> bool:
        """Check if content has any category marker."""
        return any(pattern.search(content) for pattern in self.category_marker_patterns)

    def get_expected_marker(self, file_path: Path) -> str | None:
        """Determine expected marker based on directory structure."""
        f_str = str(file_path).replace("\\", "/")

        for directory, marker in self.directory_to_marker.items():
            normalized_directory = self._normalize_rel_path(directory)
            expected_prefix = f"{self.tests_dir_rel}/{normalized_directory}/"
            if f"/{expected_prefix}" in f_str or f_str.startswith(expected_prefix):
                return marker
        return None

    def analyze_markers(self) -> dict:
        """Analyze all test files for marker usage."""
        test_files = self.find_test_files()
        files_needing_markers = []
        files_by_dir = {
            "unit": [],
            "integration": [],
            "behavior": [],
            "ui": [],
            "other": [],
        }

        for test_file in test_files:
            try:
                content = test_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to read {test_file}: {e}")
                continue

            expected = self.get_expected_marker(test_file)
            if expected:
                files_by_dir[expected].append(str(test_file))
            else:
                files_by_dir["other"].append(str(test_file))

            if not self.has_category_marker(content):
                files_needing_markers.append((str(test_file), expected))

        return {
            "total_files": len(test_files),
            "files_needing_markers": len(files_needing_markers),
            "files_by_dir": {k: len(v) for k, v in files_by_dir.items()},
            "missing_markers": files_needing_markers,
        }

    def find_missing_markers_ast(self) -> list[tuple[str, int, str, str]]:
        """Find missing markers using AST analysis (more accurate)."""
        finder = MissingMarkerFinder(
            category_markers=self.category_markers,
            domain_markers=self.domain_markers,
            project_root=self.project_root,
            exempt_rel_prefixes=self._directory_only_domain_exempt_prefixes(),
        )
        test_files = self.find_test_files()

        for file_path in test_files:
            finder.analyze_file(file_path)

        self._last_marker_finder = finder
        return finder.missing

    def get_last_domain_marker_gaps(self) -> list[tuple[str, int, str, str]]:
        """Advisory: tests with a category marker but no configured domain marker (V5 §5.7)."""
        if self._last_marker_finder is None:
            return []
        return self._last_marker_finder.missing_domain

    def add_markers(self, dry_run: bool = False) -> dict:
        """
        Add missing markers to test files based on directory structure.
        """
        test_files = self.find_test_files()
        files_updated = []
        files_skipped = []

        for test_file in test_files:
            try:
                content = test_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to read {test_file}: {e}")
                continue

            # Check if already has category marker
            if self.has_category_marker(content):
                files_skipped.append(str(test_file))
                continue

            # Determine expected category from directory
            marker = self.get_expected_marker(test_file)
            if not marker:
                files_skipped.append(str(test_file))
                continue

            # Find all test classes
            class_pattern = r"^class\s+(Test\w+):"
            matches = list(re.finditer(class_pattern, content, re.MULTILINE))

            if not matches:
                files_skipped.append(str(test_file))
                continue

            # Add marker before first test class
            first_match = matches[0]
            insert_pos = first_match.start()

            # Check if pytest is already imported
            needs_pytest_import = (
                "import pytest" not in content and "from pytest" not in content
            )

            # Build the marker line
            marker_line = f"@pytest.mark.{marker}\n"

            # If we need to add pytest import, add it near the top
            if needs_pytest_import:
                # Find a good place to add import (after other imports)
                import_pattern = r"^(import\s+\w+|from\s+\w+.*import)"
                import_matches = list(
                    re.finditer(import_pattern, content, re.MULTILINE)
                )
                if import_matches:
                    last_import = import_matches[-1]
                    import_end = last_import.end()
                    # Add import after last import, before blank line if present
                    next_line_start = content.find("\n", import_end) + 1
                    if (
                        next_line_start > 0
                        and next_line_start < len(content)
                        and content[next_line_start : next_line_start + 1] == "\n"
                    ):
                        # Already a blank line, add before it
                        content = (
                            content[:next_line_start]
                            + "import pytest\n"
                            + content[next_line_start:]
                        )
                    else:
                        # Add import and blank line
                        content = (
                            content[:next_line_start]
                            + "import pytest\n\n"
                            + content[next_line_start:]
                        )
                else:
                    # No imports found, add at top after docstring
                    docstring_end = content.find('"""', content.find('"""') + 3) + 3
                    if docstring_end > 2:
                        next_line = content.find("\n", docstring_end) + 1
                        content = (
                            content[:next_line]
                            + "import pytest\n\n"
                            + content[next_line:]
                        )
                    else:
                        # No docstring, add at very top
                        content = "import pytest\n\n" + content

            # Add marker before first class
            # Find the line start for the class
            line_start = content.rfind("\n", 0, insert_pos) + 1
            # Check if there's already a marker on the previous line
            prev_line_start = (
                content.rfind("\n", 0, line_start - 1) + 1 if line_start > 0 else 0
            )
            prev_line = (
                content[prev_line_start : line_start - 1].strip()
                if line_start > 0
                else ""
            )

            if prev_line.startswith("@pytest.mark."):
                # Already has a marker, skip
                files_skipped.append(str(test_file))
                continue

            # Insert marker before class
            content = content[:line_start] + marker_line + content[line_start:]

            # Add marker to remaining classes in the file
            for match in matches[1:]:
                class_line_start = content.rfind("\n", 0, match.start()) + 1
                prev_class_line_start = (
                    content.rfind("\n", 0, class_line_start - 1) + 1
                    if class_line_start > 0
                    else 0
                )
                prev_class_line = (
                    content[prev_class_line_start : class_line_start - 1].strip()
                    if class_line_start > 0
                    else ""
                )

                if not prev_class_line.startswith("@pytest.mark."):
                    content = (
                        content[:class_line_start]
                        + marker_line
                        + content[class_line_start:]
                    )

            # Write updated content
            if not dry_run:
                test_file.write_text(content, encoding="utf-8")
            files_updated.append((str(test_file), marker))

        return {"updated": files_updated, "skipped": files_skipped, "dry_run": dry_run}


class MissingMarkerFinder:
    """AST-based finder for missing markers (more accurate than regex)."""

    def __init__(
        self,
        category_markers: tuple[str, ...] | None = None,
        domain_markers: tuple[str, ...] | None = None,
        project_root: Path | None = None,
        exempt_rel_prefixes: tuple[str, ...] | None = None,
    ):
        self.missing = []
        self.missing_domain: list[tuple[str, int, str, str]] = []
        self.category_markers = set(category_markers or TEST_CATEGORY_MARKERS)
        self.domain_markers = set(domain_markers or ())
        self.project_root = Path(project_root).resolve() if project_root else None
        self.exempt_rel_prefixes = tuple(
            str(p).strip().replace("\\", "/").strip("/") + "/"
            for p in (exempt_rel_prefixes or ())
            if str(p).strip()
        )

    def _rel_under_exempt_prefix(self, file_path: Path) -> bool:
        if not self.exempt_rel_prefixes or not self.project_root:
            return False
        try:
            rel = str(file_path.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            rel = str(file_path).replace("\\", "/")
        return any(rel.startswith(pref) for pref in self.exempt_rel_prefixes)

    def _is_pytest_fixture(self, decorators):
        for dec in decorators:
            target = dec
            if isinstance(dec, ast.Call):
                target = dec.func
            if isinstance(target, ast.Attribute):
                if target.attr == "fixture":
                    value = target.value
                    if isinstance(value, ast.Name) and value.id == "pytest":
                        return True
                    if isinstance(value, ast.Attribute) and value.attr == "fixture":
                        return True
            elif isinstance(target, ast.Name) and target.id == "fixture":
                return True
        return False

    def has_category_marker(self, decorators):
        for dec in decorators:
            target = dec
            if isinstance(dec, ast.Call):
                target = dec.func
            if isinstance(target, ast.Attribute):
                if target.attr in self.category_markers:
                    value = target.value
                    if isinstance(value, ast.Attribute) and value.attr == "mark":
                        return True
                    if isinstance(value, ast.Name) and value.id == "mark":
                        # handles 'from pytest import mark'
                        return True
            elif isinstance(target, ast.Name):
                if target.id in self.category_markers:
                    return True
        return False

    def has_domain_marker(self, decorators):
        if not self.domain_markers:
            return False
        for dec in decorators:
            target = dec
            if isinstance(dec, ast.Call):
                target = dec.func
            if isinstance(target, ast.Attribute):
                if target.attr in self.domain_markers:
                    value = target.value
                    if isinstance(value, ast.Attribute) and value.attr == "mark":
                        return True
                    if isinstance(value, ast.Name) and value.id == "mark":
                        return True
            elif isinstance(target, ast.Name):
                if target.id in self.domain_markers:
                    return True
        return False

    def process_function(
        self, node, file_path, inherited_category=False, inherited_domain=False
    ):
        if not node.name.startswith("test_"):
            return
        if self._is_pytest_fixture(node.decorator_list):
            return
        has_cat = inherited_category or self.has_category_marker(node.decorator_list)
        has_dom = inherited_domain or self.has_domain_marker(node.decorator_list)
        if not has_cat:
            self.missing.append((str(file_path), node.lineno, node.name, "function"))
            return
        if (
            self.domain_markers
            and not has_dom
            and not self._rel_under_exempt_prefix(file_path)
        ):
            self.missing_domain.append((str(file_path), node.lineno, node.name, "function"))

    def _class_marked_not_test(self, node):
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "__test__":
                        if (
                            isinstance(stmt.value, ast.Constant)
                            and stmt.value.value is False
                        ):
                            return True
        return False

    def process_class(self, node, file_path, inherited_category=False, inherited_domain=False):
        if self._class_marked_not_test(node):
            return
        if not node.name.startswith("Test") and not inherited_category:
            return
        class_has_cat = inherited_category or self.has_category_marker(node.decorator_list)
        class_has_dom = inherited_domain or self.has_domain_marker(node.decorator_list)
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.process_function(
                    stmt,
                    file_path,
                    inherited_category=class_has_cat,
                    inherited_domain=class_has_dom,
                )
            elif isinstance(stmt, ast.ClassDef):
                self.process_class(
                    stmt,
                    file_path,
                    inherited_category=class_has_cat,
                    inherited_domain=class_has_dom,
                )

    def analyze_file(self, file_path):
        try:
            # Use utf-8-sig so BOM-prefixed files do not trigger SyntaxError.
            tree = ast.parse(file_path.read_text(encoding="utf-8-sig"))
        except SyntaxError as exc:
            logger.warning(f"Skipping {file_path} due to syntax error: {exc}")
            return
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.process_function(node, file_path)
            elif isinstance(node, ast.ClassDef):
                self.process_class(node, file_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze and manage pytest test markers"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check for missing markers (default)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze marker usage and provide detailed report",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Default to check if no action specified
    if not (args.check or args.analyze):
        args.check = True

    analyzer = TestMarkerAnalyzer()

    if args.analyze:
        result = analyzer.analyze_markers()
        if args.json:
            import json
            missing_markers = result.get("missing_markers", [])
            files_affected = len({item[0] for item in missing_markers if item})
            total_issues = result.get("files_needing_markers", files_affected)
            standard_result = {
                "summary": {
                    "total_issues": total_issues,
                    "files_affected": files_affected,
                },
                "details": result,
            }
            print(json.dumps(standard_result, indent=2))
        else:
            print(f"Total test files: {result['total_files']}")
            print(f"Files needing category markers: {result['files_needing_markers']}")
            print("\nFiles by directory:")
            for dir_name, count in result["files_by_dir"].items():
                print(f"  {dir_name}: {count}")
            if result["missing_markers"]:
                print("\nFiles needing markers (first 30):")
                for f, expected in result["missing_markers"][:30]:
                    print(f"  {expected or 'unknown'}: {f}")

    else:  # args.check (default)
        missing = analyzer.find_missing_markers_ast()
        domain_gaps = analyzer.get_last_domain_marker_gaps()
        if args.json:
            import json

            missing_list = [
                {"file": f, "line": line_number, "name": n, "type": t}
                for f, line_number, n, t in missing
            ]
            missing_domain_list = [
                {"file": f, "line": line_number, "name": n, "type": t}
                for f, line_number, n, t in domain_gaps
            ]
            file_keys = {item["file"] for item in missing_list if item.get("file")}
            file_keys.update(
                item["file"] for item in missing_domain_list if item.get("file")
            )
            total_issues = len(missing_list) + len(missing_domain_list)
            standard_result = {
                "summary": {
                    "total_issues": total_issues,
                    "files_affected": len(file_keys),
                },
                "details": {
                    "missing_count": len(missing_list),
                    "missing": missing_list,
                    "missing_domain_count": len(missing_domain_list),
                    "missing_domain": missing_domain_list,
                    "domain_markers_configured": list(analyzer.domain_markers),
                },
            }
            print(json.dumps(standard_result, indent=2))
            return 1 if total_issues else 0
        if not missing and not domain_gaps:
            print(
                "All tests have required category markers and domain markers. Great job!"
            )
            return 0

        if missing:
            print("Tests missing category markers (unit/integration/behavior/ui):")
            for file_path, lineno, name, node_type in missing:
                print(f"  - {file_path}:{lineno} ({node_type} {name})")
            print(f"\nTotal missing category markers: {len(missing)}")
        if domain_gaps:
            print(
                "\nTests missing domain markers (see test_markers.domain_markers / domain_mapper):"
            )
            for file_path, lineno, name, node_type in domain_gaps:
                print(f"  - {file_path}:{lineno} ({node_type} {name})")
            print(f"\nTotal missing domain markers: {len(domain_gaps)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
