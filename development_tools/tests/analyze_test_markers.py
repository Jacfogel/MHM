#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
analyze_test_markers.py
Analyze test files for pytest marker usage (read-only analysis).
For fixing operations, use fix_test_markers.py.
"""

import sys
import re
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
except ImportError:
    from development_tools import config

from core.logger import get_component_logger

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")

CATEGORY_MARKERS = {"unit", "integration", "behavior", "ui"}


class TestMarkerAnalyzer:
    """Analyze and manage pytest category markers in test files."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(config.get_project_root())
        self.test_dir = self.project_root / "tests"

    def find_test_files(self, exclude_ai: bool = True) -> List[Path]:
        """Find all test files in the tests directory."""
        test_files = []
        if not self.test_dir.exists():
            return test_files

        for test_file in self.test_dir.rglob("test_*.py"):
            if test_file.is_file():
                # Skip AI test files if requested
                if exclude_ai and (
                    "ai/test_ai" in str(test_file) or "test_ai" in test_file.name
                ):
                    continue

                # Skip temporary test files in tests/data/ (pytest temporary directories)
                file_str = str(test_file).replace("\\", "/")
                if "/tests/data/" in file_str or file_str.startswith("tests/data/"):
                    # Exclude pytest temporary directories
                    if "pytest-tmp-" in file_str or "pytest-of-" in file_str:
                        continue

                test_files.append(test_file)

        return sorted(test_files)

    def has_category_marker(self, content: str) -> bool:
        """Check if content has any category marker."""
        patterns = [
            r"@pytest\.mark\.unit\b",
            r"@pytest\.mark\.integration\b",
            r"@pytest\.mark\.behavior\b",
            r"@pytest\.mark\.ui\b",
        ]
        return any(re.search(pattern, content) for pattern in patterns)

    def get_expected_marker(self, file_path: Path) -> Optional[str]:
        """Determine expected marker based on directory structure."""
        f_str = str(file_path).replace("\\", "/")
        if "/tests/unit/" in f_str or f_str.startswith("tests/unit/"):
            return "unit"
        elif "/tests/integration/" in f_str or f_str.startswith("tests/integration/"):
            return "integration"
        elif "/tests/behavior/" in f_str or f_str.startswith("tests/behavior/"):
            return "behavior"
        elif "/tests/ui/" in f_str or f_str.startswith("tests/ui/"):
            return "ui"
        return None

    def analyze_markers(self) -> Dict:
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

    def find_missing_markers_ast(self) -> List[Tuple[str, int, str, str]]:
        """Find missing markers using AST analysis (more accurate)."""
        finder = MissingMarkerFinder()
        test_files = self.find_test_files()

        for file_path in test_files:
            finder.analyze_file(file_path)

        return finder.missing

    def add_markers(self, dry_run: bool = False) -> Dict:
        """
        Add missing markers to test files based on directory structure.

        Note: This method is kept here for backward compatibility but the fixing
        logic should be used via fix_test_markers.py module.
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

    def __init__(self):
        self.missing = []

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
            elif isinstance(target, ast.Name):
                if target.id == "fixture":
                    return True
        return False

    def has_category_marker(self, decorators):
        for dec in decorators:
            target = dec
            if isinstance(dec, ast.Call):
                target = dec.func
            if isinstance(target, ast.Attribute):
                if target.attr in CATEGORY_MARKERS:
                    value = target.value
                    if isinstance(value, ast.Attribute) and value.attr == "mark":
                        return True
                    if isinstance(value, ast.Name) and value.id == "mark":
                        # handles 'from pytest import mark'
                        return True
            elif isinstance(target, ast.Name):
                if target.id in CATEGORY_MARKERS:
                    return True
        return False

    def process_function(self, node, file_path, inherited_category=False):
        if not node.name.startswith("test_"):
            return
        if self._is_pytest_fixture(node.decorator_list):
            return
        if inherited_category or self.has_category_marker(node.decorator_list):
            return
        self.missing.append((str(file_path), node.lineno, node.name, "function"))

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

    def process_class(self, node, file_path, inherited_category=False):
        if self._class_marked_not_test(node):
            return
        if not node.name.startswith("Test") and not inherited_category:
            return
        class_has = inherited_category or self.has_category_marker(node.decorator_list)
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.process_function(stmt, file_path, inherited_category=class_has)
            elif isinstance(stmt, ast.AsyncFunctionDef):
                self.process_function(stmt, file_path, inherited_category=class_has)
            elif isinstance(stmt, ast.ClassDef):
                self.process_class(stmt, file_path, inherited_category=class_has)

    def analyze_file(self, file_path):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            logger.warning(f"Skipping {file_path} due to syntax error: {exc}")
            return
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.process_function(node, file_path)
            elif isinstance(node, ast.AsyncFunctionDef):
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

            print(json.dumps(result, indent=2))
        else:
            print(f"Total test files: {result['total_files']}")
            print(f"Files needing category markers: {result['files_needing_markers']}")
            print(f"\nFiles by directory:")
            for dir_name, count in result["files_by_dir"].items():
                print(f"  {dir_name}: {count}")
            if result["missing_markers"]:
                print(f"\nFiles needing markers (first 30):")
                for f, expected in result["missing_markers"][:30]:
                    print(f"  {expected or 'unknown'}: {f}")

    else:  # args.check (default)
        missing = analyzer.find_missing_markers_ast()
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "missing_count": len(missing),
                        "missing": [
                            {"file": f, "line": l, "name": n, "type": t}
                            for f, l, n, t in missing
                        ],
                    },
                    indent=2,
                )
            )
        else:
            if not missing:
                print("All tests have category markers. Great job!")
                return 0

            print("Tests missing category markers (unit/integration/behavior/ui):")
            for file_path, lineno, name, node_type in missing:
                print(f"  - {file_path}:{lineno} ({node_type} {name})")

            print(f"\nTotal missing markers: {len(missing)}")
            return 1 if missing else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
