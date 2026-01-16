#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Unconverted Link Analyzer

This script checks for file path references that should be converted to markdown links.
Uses the same logic as the fixer to ensure consistency. Only reports links that would
actually be converted. Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable across
different projects.

Usage:
    python docs/analyze_unconverted_links.py
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != "__main__" and __package__ and "." in __package__:
    from .. import config
else:
    from development_tools import config

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, "load_external_config"):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")


class UnconvertedLinkAnalyzer:
    """Analyzes documentation files for unconverted file path links."""

    def __init__(
        self,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Initialize unconverted link analyzer.

        Args:
            project_root: Root directory of the project
            config_path: Optional path to external config file
            use_cache: Whether to use mtime-based caching for file analysis
        """
        # Load external config if provided
        if config_path:
            config.load_external_config(config_path)
        else:
            config.load_external_config()

        # Use provided project_root or get from config
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()

        # Caching - use standardized storage
        from development_tools.shared.mtime_cache import MtimeFileCache

        self.cache = MtimeFileCache(
            project_root=self.project_root,
            use_cache=use_cache,
            tool_name="analyze_unconverted_links",
            domain="docs",
        )

    def _should_skip_generated_file(self, file_path: Path) -> bool:
        """
        Skip generated files using BOTH:
        - Authoritative list (ALL_GENERATED_FILES)
        - Heuristic/header/pattern detection (is_generated_file)
        """
        from development_tools.shared.exclusion_utilities import is_generated_file
        from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES

        # Fast path: authoritative list (relative to project root)
        try:
            rel_path_str = str(file_path.relative_to(self.project_root)).replace(
                "\\", "/"
            )
            if rel_path_str in ALL_GENERATED_FILES:
                return True
        except ValueError:
            # If file isn't under project root, fall back to heuristic detection only
            pass

        # Heuristic detection (header markers, /generated/, suffix patterns, _pyqt.py)
        return is_generated_file(str(file_path))

    def _is_in_code_block(self, lines: List[str], line_num: int) -> bool:
        """Check if a line is inside a code block."""
        in_code = False
        for i in range(line_num + 1):
            if i < len(lines) and lines[i].strip().startswith("```"):
                in_code = not in_code
        return in_code

    def _is_in_example_context(
        self, line: str, lines: List[str], line_num: int
    ) -> bool:
        """
        Check if a line is in an example context based on documentation standards.

        Examples must be marked using one of these standards:
        1. Example markers: [OK], [AVOID], [GOOD], [BAD], [EXAMPLE] at start of section
        2. Example headings: "Examples:", "Example Usage:", "Example Code:" headings
        3. Code blocks: Automatically excluded (handled separately)
        4. Archive references: Lines containing "archive" or "archived" (for archived file references)
        5. Example phrases: "for example", "for instance", "e.g.", etc.

        This method implements the example marking standards defined in DOCUMENTATION_GUIDE.md section 2.6.
        Uses the same logic as fix_documentation.py for consistency.
        """
        line_stripped = line.strip()
        line_lower = line.lower()

        # Standard 4: Check if line contains "archive" or "archived" (for archived file references)
        if "archive" in line_lower or "archived" in line_lower:
            return True

        # Standard 5: Check for example phrases in the current line
        example_phrases = [
            "for example",
            "for instance",
            "e.g.,",
            "e.g.",
            "example:",
            "examples:",
        ]
        for phrase in example_phrases:
            if phrase in line_lower:
                return True

        # Standard 1: Check for example markers at the start of the line
        # These are the official markers per documentation standards
        example_markers = [
            r"^\[OK\]",
            r"^\[AVOID\]",
            r"^\[GOOD\]",
            r"^\[BAD\]",
            r"^\[EXAMPLE\]",
        ]
        for marker in example_markers:
            if re.match(marker, line_stripped, re.IGNORECASE):
                return True

        # Standard 1 & 5 (continued): Check previous lines (up to 5 lines back) for example markers and phrases
        # This catches cases where [AVOID] or [OK] is on a previous line (per standard)
        for i in range(max(0, line_num - 5), line_num):
            prev_line = lines[i].strip()
            prev_line_lower = prev_line.lower()
            # Check for archive references in previous lines too
            if "archive" in prev_line_lower or "archived" in prev_line_lower:
                if line_num - i <= 3:  # Within 3 lines of archive reference
                    return True
            # Check for example phrases in previous lines
            for phrase in example_phrases:
                if phrase in prev_line_lower:
                    if line_num - i <= 3:  # Within 3 lines of example phrase
                        return True
            # Check for example markers in previous lines
            for marker in example_markers:
                if re.match(marker, prev_line, re.IGNORECASE):
                    # If we found a marker, check if current line is part of the example
                    # (list item, continuation, or within same section)
                    if (
                        line_stripped.startswith(("-", "*", "1.", "2.", "3.", "  "))
                        or line_num - i <= 3
                    ):  # Within 3 lines of the marker
                        return True

        # Standard 2: Check if we're in an "Examples" section by looking backwards for section headers
        # Look back up to 20 lines for section headers (per standard)
        for i in range(max(0, line_num - 20), line_num):
            prev_line = lines[i].strip()
            # Check for "Examples:" or "Example Usage:" or "Example Code:" headings (per standard)
            if re.match(
                r"^#+\s+(Examples?|Example\s+Usage|Example\s+Code)",
                prev_line,
                re.IGNORECASE,
            ):
                return True
            # Check for bold "Examples:" or "Example Usage:" text
            if re.match(
                r"^\*\*(Examples?|Example\s+Usage)\*\*", prev_line, re.IGNORECASE
            ):
                return True

        # Note: Code blocks are handled separately in scan_documentation_paths() by checking in_code_block
        # This is Standard 3 and doesn't need to be checked here

        return False

    def _is_already_link(self, line: str, path: str) -> bool:
        """Check if the path is already in a markdown link."""
        link_pattern = rf"\[[^\]]*\]\(({re.escape(path)})\)"
        return bool(re.search(link_pattern, line))

    def _is_file_metadata_line(self, line: str) -> bool:
        """Check if line is the specific 'File' metadata line."""
        return bool(re.match(r"^\s*>\s*\*\*File\*\*", line))

    def _is_valid_file_path_for_link(self, path: str, source_file: Path) -> bool:
        """Validate that a file path exists and is valid for link conversion."""
        from development_tools.shared.constants import (
            STANDARD_LIBRARY_MODULES,
            THIRD_PARTY_LIBRARIES,
            COMMON_FUNCTION_NAMES,
            COMMON_CLASS_NAMES,
            COMMON_VARIABLE_NAMES,
            COMMON_CODE_PATTERNS,
            IGNORED_PATH_PATTERNS,
            COMMAND_PATTERNS,
            TEMPLATE_PATTERNS,
        )

        if path.startswith(("*", "http", "#", "mailto", "python ", "pip ", "git ")):
            return False
        if "{" in path and "}" in path:
            return False
        if path in STANDARD_LIBRARY_MODULES or path in THIRD_PARTY_LIBRARIES:
            return False
        if (
            path in COMMON_FUNCTION_NAMES
            or path in COMMON_CLASS_NAMES
            or path in COMMON_VARIABLE_NAMES
        ):
            return False
        if path in COMMON_CODE_PATTERNS or path in IGNORED_PATH_PATTERNS:
            return False
        if any(path.startswith(cmd) for cmd in COMMAND_PATTERNS):
            return False
        if any(pattern in path for pattern in TEMPLATE_PATTERNS):
            return False
        if path.startswith("../") or path.startswith("./"):
            return False
        if "/" not in path and "\\" not in path:
            if path.endswith(".md"):
                file_path = self.project_root / path
                if file_path.exists() and file_path.is_file():
                    return True
            return False
        file_path = self.project_root / path
        if file_path.exists() and file_path.is_file():
            return True
        if path.endswith(".md"):
            mdc_path = path[:-2] + "c"
            mdc_file = self.project_root / mdc_path
            if mdc_file.exists() and mdc_file.is_file():
                return True
        return False

    def _is_metadata_section(self, lines: List[str], line_num: int) -> bool:
        """Check if a line is in the metadata section (H1 + lines starting with >)."""
        current_line = lines[line_num].strip()
        if current_line.startswith("#") or current_line.startswith(">"):
            return True
        h1_found = False
        metadata_block_start = None
        for i in range(line_num, -1, -1):
            if i < len(lines):
                line = lines[i].strip()
                if line.startswith("#"):
                    h1_found = True
                    break
                if line.startswith(">"):
                    if metadata_block_start is None:
                        metadata_block_start = i
                elif line and metadata_block_start is not None:
                    break
        if h1_found:
            for i in range(line_num + 1):
                if i < len(lines):
                    stripped = lines[i].strip()
                    if stripped.startswith(">"):
                        if i == line_num:
                            return True
                    elif (
                        stripped
                        and not stripped.startswith("#")
                        and not stripped.startswith(">")
                    ):
                        if i < line_num:
                            return False
        if metadata_block_start is not None:
            for i in range(metadata_block_start, line_num + 1):
                if i < len(lines):
                    stripped = lines[i].strip()
                    if (
                        stripped
                        and not stripped.startswith(">")
                        and not stripped.startswith("#")
                    ):
                        if i < line_num:
                            return False
                    if i == line_num and (stripped.startswith(">") or not stripped):
                        return True
        return False

    def _should_convert_path_to_link(
        self, path: str, line: str, line_num: int, lines: List[str], source_file: Path
    ) -> bool:
        """
        Determine if a path should be converted to a link.

        Returns False if:
        - Already in a markdown link
        - In the specific 'File' metadata line (> **File**:)
        - In code block (excluded for safety)
        - In example context (e.g., "for example", "[OK]", etc.)
        - Path matches the current document (don't link to self)
        """
        if self._is_already_link(line, path):
            return False
        if self._is_file_metadata_line(line):
            return False
        if self._is_in_code_block(lines, line_num):
            return False
        if self._is_in_example_context(line, lines, line_num):
            return False

        # Don't convert links to the current document
        source_name = source_file.name
        if path == source_name:
            return False

        # Also check if it's a full path that matches the current file
        try:
            source_relative = str(source_file.relative_to(self.project_root))
            if path == source_relative:
                return False
        except ValueError:
            pass

        return True

    def check_unconverted_links(self) -> Dict[str, List[str]]:
        """
        Check for file path references that should be converted to markdown links.

        Uses the same logic as the fixer to ensure consistency. Only reports
        links that would actually be converted.

        Returns:
            Dictionary mapping file paths to lists of issues
        """
        unconverted_links = defaultdict(list)

        from development_tools.shared.constants import DEFAULT_DOCS
        from development_tools.shared.standard_exclusions import (
            HISTORICAL_PRESERVE_FILES,
        )

        for file_path_str in DEFAULT_DOCS:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                continue

            # Skip generated files
            if self._should_skip_generated_file(file_path):
                continue

            # Skip historical preserve files
            if file_path_str in HISTORICAL_PRESERVE_FILES:
                continue
            # Check cache first
            cached_issues = self.cache.get_cached(file_path)
            if cached_issues is not None:
                if cached_issues:
                    unconverted_links[file_path_str] = cached_issues
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                metadata_linked_files = (
                    set()
                )  # Track paths already linked in metadata section

                # First pass: Find all paths that are already links in metadata section
                for line_num, line in enumerate(lines):
                    is_metadata_section = self._is_metadata_section(lines, line_num)
                    if is_metadata_section:
                        # Check for existing links in metadata
                        link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
                        for match in re.finditer(link_pattern, line):
                            linked_path = match.group(2).replace("\\", "/")
                            metadata_linked_files.add(linked_path)

                # Second pass: Check for unconverted paths
                for line_num, line in enumerate(lines):
                    is_metadata_section = self._is_metadata_section(lines, line_num)

                    if self._is_in_code_block(lines, line_num):
                        continue
                    if self._is_in_example_context(line, lines, line_num):
                        continue
                    if self._is_file_metadata_line(line):
                        continue

                    # Find file paths in backticks
                    pattern = r"`([a-zA-Z_][a-zA-Z0-9_/\\]*\.md)`"
                    for match in re.finditer(pattern, line):
                        path = match.group(1).replace("\\", "/")

                        # Use same checks as fixer
                        if self._is_already_link(line, path):
                            continue
                        if path == file_path.name:
                            continue

                        # Check if target is generated (don't suggest linking to generated files)
                        target_path = self.project_root / path
                        if target_path.exists() and self._should_skip_generated_file(
                            target_path
                        ):
                            continue

                        if not self._is_valid_file_path_for_link(path, file_path):
                            continue

                        # Check should_convert logic (same as fixer)
                        if not self._should_convert_path_to_link(
                            path, line, line_num, lines, file_path
                        ):
                            continue

                        # In metadata section, skip if this path is already linked anywhere in metadata
                        if is_metadata_section:
                            if path in metadata_linked_files:
                                continue  # Skip - already linked in metadata section
                            metadata_linked_files.add(
                                path
                            )  # Track that we're reporting this one

                        unconverted_links[file_path_str].append(
                            f"Line {line_num + 1}: Path `{path}` should be converted to markdown link"
                        )
            except Exception as e:
                file_issues = [f"Error reading file: {e}"]
                self.cache.cache_results(file_path, file_issues)
                unconverted_links[file_path_str] = file_issues
            else:
                # Cache results for this file
                file_issues = unconverted_links.get(file_path_str, [])
                self.cache.cache_results(file_path, file_issues)

        # Save cache
        self.cache.save_cache()

        return unconverted_links

    def run_analysis(self) -> Dict[str, Any]:
        """
        Run unconverted links analysis and return results in standard format.

        Returns:
            Dictionary with standard format structure:
            {
                "summary": {
                    "total_issues": int,
                    "files_affected": int,
                    "status": str
                },
                "files": {
                    "file_path": issue_count
                },
                "details": {
                    "detailed_issues": Dict[str, List[str]]
                }
            }
        """
        unconverted_links = self.check_unconverted_links()

        # Convert to standard format
        files = {}
        total_issues = 0
        for file_path, issues in unconverted_links.items():
            issue_count = len(issues)
            files[file_path] = issue_count
            total_issues += issue_count

        # Determine status
        if total_issues == 0:
            status = "CLEAN"
        elif total_issues < 10:
            status = "NEEDS_ATTENTION"
        else:
            status = "CRITICAL"

        return {
            "summary": {
                "total_issues": total_issues,
                "files_affected": len(files),
                "status": status,
            },
            "files": files,
            "details": {"detailed_issues": dict(unconverted_links)},
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for unconverted file path links in documentation"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON in standard format"
    )

    args = parser.parse_args()

    analyzer = UnconvertedLinkAnalyzer()

    # Use run_analysis() to get standard format
    if args.json:
        import json

        results = analyzer.run_analysis()
        print(json.dumps(results, indent=2))
        return 0

    # Otherwise use check_unconverted_links() for human-readable output
    results = analyzer.check_unconverted_links()

    # Print results
    if results:
        print(f"\nUnconverted Link Issues:")
        print(f"   Total files with unconverted links: {len(results)}")
        print(
            f"   Total issues found: {sum(len(issues) for issues in results.values())}"
        )
        print(f"   Files with unconverted links:")
        for doc_file, issues in results.items():
            print(f"     {doc_file}: {len(issues)} issues")
            for issue in issues[:5]:
                clean_issue = issue.encode("ascii", "ignore").decode("ascii")
                print(f"       - {clean_issue}")
            if len(issues) > 5:
                print(f"       ... and {len(issues) - 5} more issues")
    else:
        print("\nAll file paths are properly converted to markdown links!")

    return 0 if not results else 1


if __name__ == "__main__":
    sys.exit(main())
