#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Legacy Reference Analyzer (Portable)

This script analyzes codebases for legacy references. It identifies legacy patterns
but does not generate reports or perform fixes. Configuration is loaded from external
config file (development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python legacy/analyze_legacy_references.py [--find ITEM] [--verify ITEM]
"""

import re
import argparse
import sys
import json
from pathlib import Path
from typing import Any
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.logging import get_dev_tools_logger
from development_tools.shared.exclusion_utilities import parse_devtools_markers

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

logger = get_dev_tools_logger("development_tools")


class LegacyReferenceAnalyzer:
    """Analyzes codebase for legacy references (portable across projects)."""

    def __init__(
        self,
        project_root: str = ".",
        legacy_tokens: dict[str, list[str]] | None = None,
        use_cache: bool = True,
    ):
        """
        Initialize legacy reference analyzer.

        Args:
            project_root: Root directory of the project
            legacy_tokens: Optional dict of legacy pattern categories and their regex patterns.
                          If None, loads from config or uses generic defaults.
            use_cache: Whether to use mtime-based caching for file scans (default: True)
        """
        self.project_root = Path(project_root).resolve()
        self.use_cache = use_cache

        # Load legacy configuration from external config
        legacy_config = config.get_external_value("legacy_cleanup", {})

        # Deprecation inventory first: canonical legacy_scan_patterns + active entry terms
        self.deprecation_inventory_path = self._resolve_deprecation_inventory_path(
            legacy_config
        )
        (
            self.deprecation_inventory_data,
            self.deprecation_inventory_summary,
        ) = self._load_deprecation_inventory(self.deprecation_inventory_path)

        # Legacy regex categories: DEPRECATION_INVENTORY.json legacy_scan_patterns,
        # optional override per category via legacy_cleanup.legacy_patterns in config.
        if legacy_tokens is not None:
            self.legacy_patterns = legacy_tokens
        else:
            inv_patterns_raw = self.deprecation_inventory_data.get(
                "legacy_scan_patterns"
            )
            inv_patterns = inv_patterns_raw if isinstance(inv_patterns_raw, dict) else {}
            cfg_patterns_raw = legacy_config.get("legacy_patterns")
            cfg_patterns = cfg_patterns_raw if isinstance(cfg_patterns_raw, dict) else {}
            merged: dict[str, list[str]] = {}
            for category in sorted(
                set(inv_patterns.keys()) | set(cfg_patterns.keys()),
                key=str,
            ):
                cfg_vals = cfg_patterns.get(category)
                inv_vals = inv_patterns.get(category)
                if isinstance(cfg_vals, list) and len(cfg_vals) > 0:
                    merged[category] = [
                        p if isinstance(p, str) else str(p) for p in cfg_vals
                    ]
                elif isinstance(inv_vals, list) and len(inv_vals) > 0:
                    merged[category] = [
                        p if isinstance(p, str) else str(p) for p in inv_vals
                    ]
            if merged:
                self.legacy_patterns = merged
            else:
                self.legacy_patterns = {
                    "legacy_compatibility_markers": [
                        r"# LEGACY COMPATIBILITY:",
                        r"# LEGACY:",
                    ],
                }
        inventory_patterns = self._build_inventory_search_patterns(
            self.deprecation_inventory_data
        )
        if inventory_patterns:
            existing = self.legacy_patterns.get("deprecation_inventory_terms", [])
            merged_patterns = list(dict.fromkeys([*existing, *inventory_patterns]))
            self.legacy_patterns["deprecation_inventory_terms"] = merged_patterns
            self.deprecation_inventory_summary["injected_pattern_count"] = len(
                merged_patterns
            )
        else:
            self.deprecation_inventory_summary["injected_pattern_count"] = 0

        # Files that should be preserved (historical context)
        from development_tools.shared.standard_exclusions import (
            HISTORICAL_PRESERVE_FILES,
        )

        self.preserve_files = set(HISTORICAL_PRESERVE_FILES)

        # File extensions to skip entirely
        skip_exts = legacy_config.get(
            "skip_extensions", [".md", ".txt", ".json", ".log"]
        )
        self.skip_extensions = (
            set(skip_exts) if isinstance(skip_exts, list) else skip_exts
        )

        # Initialize caching
        if self.use_cache:
            try:
                from development_tools.shared.mtime_cache import MtimeFileCache

                self.cache = MtimeFileCache(
                    project_root=self.project_root,
                    use_cache=True,
                    tool_name="analyze_legacy_references",
                    domain="legacy",
                    tool_paths=[
                        Path(__file__),
                        self.deprecation_inventory_path,
                    ],
                )
            except ImportError:
                logger.warning("MtimeFileCache not available, caching disabled")
                self.use_cache = False
                self.cache = None
        else:
            self.cache = None
        self.cache_stats: dict[str, int] = {"hits": 0, "misses": 0}

    def _resolve_deprecation_inventory_path(
        self, legacy_config: dict[str, Any]
    ) -> Path:
        """Resolve deprecation inventory path from config or default."""
        configured = legacy_config.get(
            "deprecation_inventory_file",
            "development_tools/config/jsons/DEPRECATION_INVENTORY.json",
        )
        inventory_path = Path(configured)
        if not inventory_path.is_absolute():
            inventory_path = self.project_root / inventory_path
        return inventory_path

    def _load_deprecation_inventory(
        self, inventory_path: Path
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load deprecation inventory JSON and return data + summary metadata."""
        summary: dict[str, Any] = {
            "inventory_path": str(
                inventory_path.relative_to(self.project_root)
                if inventory_path.is_absolute()
                and str(inventory_path).startswith(str(self.project_root))
                else inventory_path
            ).replace("\\", "/"),
            "exists": inventory_path.exists(),
            "loaded": False,
            "error": None,
            "active_or_candidate_entries": 0,
            "removed_entries": 0,
            "active_search_terms": 0,
        }
        if not inventory_path.exists():
            summary["error"] = "inventory_file_missing"
            return {}, summary

        try:
            with open(inventory_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary["error"] = f"inventory_load_failed: {exc}"
            return {}, summary

        if not isinstance(data, dict):
            summary["error"] = "inventory_invalid_shape"
            return {}, summary

        active_entries = data.get("active_or_candidate_inventory", [])
        removed_entries = data.get("removed_inventory", [])
        if not isinstance(active_entries, list):
            active_entries = []
        if not isinstance(removed_entries, list):
            removed_entries = []

        active_terms = 0
        for entry in active_entries:
            if isinstance(entry, dict):
                terms = entry.get("search_terms", [])
                if isinstance(terms, list):
                    active_terms += len([term for term in terms if isinstance(term, str)])

        summary.update(
            {
                "loaded": True,
                "active_or_candidate_entries": len(active_entries),
                "removed_entries": len(removed_entries),
                "active_search_terms": active_terms,
            }
        )
        return data, summary

    def _build_inventory_search_patterns(self, inventory_data: dict[str, Any]) -> list[str]:
        """Build regex-safe scan patterns from active/candidate inventory terms."""
        if not isinstance(inventory_data, dict):
            return []

        active_entries = inventory_data.get("active_or_candidate_inventory", [])
        if not isinstance(active_entries, list):
            return []

        allowed_statuses = {"active_bridge", "deprecated_in_use", "retire_candidate"}
        patterns: list[str] = []
        for entry in active_entries:
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", "")).strip().lower()
            if status and status not in allowed_statuses:
                continue
            terms = entry.get("search_terms", [])
            if not isinstance(terms, list):
                continue
            for term in terms:
                if not isinstance(term, str):
                    continue
                cleaned = term.strip()
                if len(cleaned) < 3:
                    continue
                patterns.append(re.escape(cleaned))

        # Deduplicate while preserving insertion order.
        return list(dict.fromkeys(patterns))

    def get_deprecation_inventory_summary(self) -> dict[str, Any]:
        """Expose inventory metadata for wrappers/reporting."""
        return dict(self.deprecation_inventory_summary)

    def _relative_path_str(self, file_path: Path) -> str:
        """Return a repo-relative path string, or the original path if outside the root."""
        try:
            return str(file_path.relative_to(self.project_root)).replace("\\", "/")
        except ValueError:
            return str(file_path).replace("\\", "/")

    def _is_main_project_root(self) -> bool:
        """Return True when this analyzer is scanning the live repo, not a demo/temp tree."""
        try:
            return str(self.project_root.resolve()) == str(Path(".").resolve())
        except (OSError, ValueError):
            return False

    def _path_should_skip(self, file_path: Path, rel_path_str: str) -> bool:
        """Return True when path/exclusion rules skip *file_path* without reading it."""
        if rel_path_str.endswith("run_tests.py"):
            return False

        from development_tools.shared.standard_exclusions import should_exclude_file

        if should_exclude_file(
            rel_path_str, tool_type="analysis", context="development"
        ):
            return True

        if "analyze_legacy_references.py" in rel_path_str:
            return True

        if self._is_main_project_root() and (
            "tests/fixtures/" in rel_path_str or "tests\\fixtures\\" in rel_path_str
        ):
            return True

        from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES

        if rel_path_str in ALL_GENERATED_FILES:
            return True

        from development_tools.shared.standard_exclusions import (
            BASE_EXCLUSION_SHORTLIST,
        )

        skip_dirs = [
            pattern.rstrip("/")
            for pattern in BASE_EXCLUSION_SHORTLIST
            if not pattern.startswith("*")
        ]
        for skip_dir in skip_dirs:
            path_parts = rel_path_str.split("/")
            skip_parts = skip_dir.split("/")
            if len(path_parts) >= len(skip_parts):
                if path_parts[: len(skip_parts)] == skip_parts:
                    return True

        for preserve_pattern in self.preserve_files:
            if preserve_pattern.endswith("/"):
                if (
                    preserve_pattern in rel_path_str
                    or f"/{preserve_pattern}" in rel_path_str
                ):
                    return True
            elif preserve_pattern == ".cursor/plans":
                if ".cursor/plans" in rel_path_str or ".cursor\\plans" in rel_path_str:
                    return True
            elif preserve_pattern.startswith("_") or preserve_pattern.endswith("_"):
                if preserve_pattern in file_path.name:
                    return True
            elif preserve_pattern in rel_path_str:
                return True

        return file_path.suffix.lower() in self.skip_extensions

    def _has_intentional_legacy_skip(self, file_path: Path, rel_path_str: str) -> bool:
        """Read the first 10 lines to honor INTENTIONAL LEGACY markers on test files."""
        if not self._is_main_project_root():
            return False
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as handle:
                first_lines = "".join(handle.readlines()[:10])
        except (OSError, UnicodeDecodeError):
            return False
        if (
            "INTENTIONAL LEGACY" not in first_lines
            and "# INTENTIONAL LEGACY:" not in first_lines
        ):
            return False
        return (
            "tests/fixtures/" in rel_path_str
            or "tests\\fixtures\\" in rel_path_str
            or "test_" in file_path.name
            or rel_path_str.startswith("tests/")
        )

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped from scanning."""
        rel_path_str = self._relative_path_str(file_path)
        if rel_path_str.endswith("run_tests.py"):
            return False
        if self._path_should_skip(file_path, rel_path_str):
            return True
        return self._has_intentional_legacy_skip(file_path, rel_path_str)

    def analyze_file_content(
        self, file_path: Path, content: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Analyze file content for legacy patterns."""
        findings = defaultdict(list)
        ignored_lines = {
            marker.line
            for marker in parse_devtools_markers(
                content,
                "legacy-references",
                include_legacy_aliases=False,
            )
            if marker.action == "ignore"
        }

        for pattern_type, patterns in self.legacy_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    if line_num in ignored_lines or (line_num - 1) in ignored_lines:
                        continue
                    line_content = content.split("\n")[line_num - 1].strip()

                    findings[pattern_type].append(
                        {
                            "pattern": pattern,
                            "match": match.group(0),
                            "line": line_num,
                            "line_content": line_content,
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        return findings

    def _record_cached_findings(
        self,
        file_path: Path,
        cached_result: dict[str, list[dict[str, Any]]],
        findings: dict[str, list[tuple[str, str, list[dict[str, Any]]]]],
    ) -> None:
        """Apply cached matches without re-reading file contents."""
        rel_path_str = self._relative_path_str(file_path)
        for pattern_type, matches in cached_result.items():
            if pattern_type in self.legacy_patterns and matches:
                findings[pattern_type].append((rel_path_str, "", matches))

    def _scan_files_for_legacy(
        self,
        glob_pattern: str,
        findings: dict[str, list[tuple[str, str, list[dict[str, Any]]]]],
        cache_stats: dict[str, int],
    ) -> None:
        """Scan files matching *glob_pattern*, using mtime cache to skip unchanged I/O."""
        for file_path in self.project_root.rglob(glob_pattern):
            rel_path_str = self._relative_path_str(file_path)
            if (
                not rel_path_str.endswith("run_tests.py")
                and self._path_should_skip(file_path, rel_path_str)
            ):
                continue

            cached_result = None
            if self.use_cache and self.cache:
                cached_result = self.cache.get_cached(file_path)
            if isinstance(cached_result, dict):
                cache_stats["hits"] += 1
                self._record_cached_findings(file_path, cached_result, findings)
                continue

            if self._has_intentional_legacy_skip(file_path, rel_path_str):
                continue

            cache_stats["misses"] += 1
            try:
                with open(file_path, encoding="utf-8") as handle:
                    content = handle.read()
            except Exception as exc:
                if logger:
                    logger.warning(f"Error reading {file_path}: {exc}")
                continue

            file_findings = self.analyze_file_content(file_path, content)
            if self.use_cache and self.cache:
                self.cache.cache_results(file_path, file_findings)
            for pattern_type, matches in file_findings.items():
                if matches:
                    findings[pattern_type].append((rel_path_str, content, matches))

    def scan_for_legacy_references(
        self,
    ) -> dict[str, list[tuple[str, str, list[dict[str, Any]]]]]:
        """Scan the codebase for legacy references."""
        if logger:
            logger.debug("Analyzing legacy references...")

        findings: dict[str, list[tuple[str, str, list[dict[str, Any]]]]] = defaultdict(
            list
        )
        cache_stats = {"hits": 0, "misses": 0}

        self._scan_files_for_legacy("*.py", findings, cache_stats)
        self._scan_files_for_legacy("*.md", findings, cache_stats)

        if self.use_cache and self.cache:
            self.cache.save_cache()
            if logger and (cache_stats["hits"] > 0 or cache_stats["misses"] > 0):
                total = cache_stats["hits"] + cache_stats["misses"]
                hit_rate = (cache_stats["hits"] / total * 100) if total > 0 else 0
                logger.debug(
                    f"Legacy reference cache: {cache_stats['hits']}/{total} hits ({hit_rate:.1f}% hit rate)"
                )

        self.cache_stats = cache_stats
        return findings

    def find_all_references(self, item_name: str) -> dict[str, list[dict[str, Any]]]:
        """
        Find all references to a specific legacy item (function, class, module, etc.).

        Args:
            item_name: Name of the legacy item to search for

        Returns:
            Dictionary mapping file paths to lists of reference details
        """
        if logger:
            logger.info(f"Searching for all references to '{item_name}'...")

        references = defaultdict(list)

        # Patterns to search for
        search_patterns = [
            # Direct imports
            rf"from\s+[\w.]+?\s+import\s+{re.escape(item_name)}\b",
            rf"import\s+{re.escape(item_name)}\b",
            # Class and function definitions
            rf"\bclass\s+{re.escape(item_name)}\b",
            rf"\bdef\s+{re.escape(item_name)}\s*\(",
            # Usage patterns
            rf"\b{re.escape(item_name)}\s*\(",
            rf"\b{re.escape(item_name)}\s*\.",
            rf"\.{re.escape(item_name)}\b",
            # String references (in comments, docstrings, etc.)
            rf'["\']{re.escape(item_name)}["\']',
            rf"`{re.escape(item_name)}`",
        ]

        # Scan Python files
        for py_file in self.project_root.rglob("*.py"):
            if self.should_skip_file(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    "".join(lines)

                file_refs = []
                # Collect all matches first, then deduplicate overlapping ones
                all_matches = []
                for line_num, line in enumerate(lines, 1):
                    for pattern in search_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            all_matches.append(
                                {
                                    "line": line_num,
                                    "line_content": line.strip(),
                                    "match": match.group(0),
                                    "pattern": pattern,
                                    "start": match.start(),
                                    "end": match.end(),
                                    "context": self._get_context(lines, line_num),
                                }
                            )

                # Deduplicate: remove matches that overlap on the same line
                seen_lines = {}
                for match in all_matches:
                    line_num = match["line"]
                    start = match["start"]
                    end = match["end"]

                    if line_num not in seen_lines:
                        seen_lines[line_num] = []

                    should_add = True
                    to_remove = []
                    for i, existing in enumerate(seen_lines[line_num]):
                        if start == existing["start"] and end == existing["end"]:
                            should_add = False
                            break
                        elif not (end <= existing["start"] or start >= existing["end"]):
                            new_length = end - start
                            existing_length = existing["end"] - existing["start"]
                            if new_length > existing_length:
                                to_remove.append(i)
                            else:
                                should_add = False
                                break

                    for i in reversed(to_remove):
                        seen_lines[line_num].pop(i)

                    if should_add:
                        seen_lines[line_num].append(match)

                # Flatten results and remove internal keys
                for line_matches in seen_lines.values():
                    for match in line_matches:
                        match.pop("start", None)
                        match.pop("end", None)
                        file_refs.append(match)

                if file_refs:
                    references[str(py_file.relative_to(self.project_root))] = file_refs

            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {py_file}: {e}")

        # Scan Markdown files
        for md_file in self.project_root.rglob("*.md"):
            if self.should_skip_file(md_file):
                continue

            try:
                with open(md_file, encoding="utf-8") as f:
                    lines = f.readlines()

                file_refs = []
                for line_num, line in enumerate(lines, 1):
                    if item_name.lower() in line.lower():
                        file_refs.append(
                            {
                                "line": line_num,
                                "line_content": line.strip(),
                                "match": item_name,
                                "pattern": "text_search",
                                "context": self._get_context(lines, line_num),
                            }
                        )

                if file_refs:
                    references[str(md_file.relative_to(self.project_root))] = file_refs

            except Exception as e:
                if logger:
                    logger.warning(f"Error reading {md_file}: {e}")

        return dict(references)

    def _get_context(
        self, lines: list[str], line_num: int, context_lines: int = 2
    ) -> str:
        """Get context around a line for better reference understanding."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        context = lines[start:end]
        return "".join(context)

    def verify_removal_readiness(self, item_name: str) -> dict[str, Any]:
        """
        Verify that a legacy item is ready for removal.

        Checks:
        - No active code references
        - No test dependencies (or tests updated)
        - Documentation references identified
        - Configuration references checked

        Args:
            item_name: Name of the legacy item to verify

        Returns:
            Dictionary with verification results and recommendations
        """
        if logger:
            logger.info(f"Verifying removal readiness for '{item_name}'...")

        references = self.find_all_references(item_name)

        # Categorize references
        active_code = []
        test_files = []
        documentation = []
        config_files = []
        archive_files = []

        for file_path, refs in references.items():
            file_path_lower = file_path.lower()

            if "archive" in file_path_lower:
                archive_files.append((file_path, refs))
            elif file_path_lower.endswith(".md"):
                documentation.append((file_path, refs))
            elif "test" in file_path_lower or file_path.startswith("tests/"):
                test_files.append((file_path, refs))
            elif "config" in file_path_lower or file_path.endswith(
                (".json", ".yaml", ".yml", ".ini", ".toml")
            ):
                config_files.append((file_path, refs))
            else:
                active_code.append((file_path, refs))

        # Determine readiness
        ready_for_removal = len(active_code) == 0 and len(config_files) == 0

        # Generate recommendations
        recommendations = []
        if active_code:
            recommendations.append(
                f"[ERROR] {len(active_code)} active code file(s) still reference '{item_name}' - must update before removal"
            )
        if test_files:
            recommendations.append(
                f"[WARNING] {len(test_files)} test file(s) reference '{item_name}' - update tests or remove if testing legacy behavior"
            )
        if config_files:
            recommendations.append(
                f"[ERROR] {len(config_files)} configuration file(s) reference '{item_name}' - must update before removal"
            )
        if documentation:
            recommendations.append(
                f"[INFO] {len(documentation)} documentation file(s) reference '{item_name}' - update for clarity (except archive)"
            )
        if archive_files:
            recommendations.append(
                f"[INFO] {len(archive_files)} archive file(s) reference '{item_name}' - can leave for historical context"
            )

        if ready_for_removal:
            recommendations.append(
                "[OK] Ready for removal - no active code or configuration references found"
            )

        return {
            "item_name": item_name,
            "ready_for_removal": ready_for_removal,
            "references": references,
            "categorized": {
                "active_code": active_code,
                "test_files": test_files,
                "documentation": documentation,
                "config_files": config_files,
                "archive_files": archive_files,
            },
            "counts": {
                "total_files": len(references),
                "active_code": len(active_code),
                "test_files": len(test_files),
                "documentation": len(documentation),
                "config_files": len(config_files),
                "archive_files": len(archive_files),
            },
            "recommendations": recommendations,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze codebase for legacy references"
    )
    parser.add_argument(
        "--find",
        type=str,
        metavar="ITEM",
        help="Find all references to a specific legacy item (function, class, module, etc.)",
    )
    parser.add_argument(
        "--verify",
        type=str,
        metavar="ITEM",
        help="Verify that a legacy item is ready for removal",
    )

    args = parser.parse_args()

    analyzer = LegacyReferenceAnalyzer()

    # Handle --find command
    if args.find:
        references = analyzer.find_all_references(args.find)

        print(f"\nReferences to '{args.find}':")
        print(f"   Total files: {len(references)}")

        if references:
            for file_path, refs in sorted(references.items()):
                print(f"\n   {file_path} ({len(refs)} reference(s)):")
                for ref in refs[:5]:  # Show first 5 references per file
                    print(f"      Line {ref['line']}: {ref['line_content'][:80]}")
                if len(refs) > 5:
                    print(f"      ... and {len(refs) - 5} more")
        else:
            print("   No references found - item may be safe to remove")

        return

    # Handle --verify command
    if args.verify:
        verification = analyzer.verify_removal_readiness(args.verify)

        print(f"\nRemoval Readiness Verification for '{args.verify}':")
        print(
            f"   Status: {'READY' if verification['ready_for_removal'] else 'NOT READY'}"
        )
        print("\n   Reference Summary:")
        print(f"      Total files: {verification['counts']['total_files']}")
        print(f"      Active code: {verification['counts']['active_code']}")
        print(f"      Test files: {verification['counts']['test_files']}")
        print(f"      Documentation: {verification['counts']['documentation']}")
        print(f"      Config files: {verification['counts']['config_files']}")
        print(f"      Archive files: {verification['counts']['archive_files']}")

        print("\n   Recommendations:")
        for rec in verification["recommendations"]:
            rec_clean = (
                rec.replace("❌", "[ERROR]")
                .replace("⚠️", "[WARNING]")
                .replace("ℹ️", "[INFO]")
                .replace("✅", "[OK]")
            )
            print(f"      {rec_clean}")

        if verification["counts"]["active_code"] > 0:
            print("\n   Active Code Files (must update):")
            for file_path, refs in verification["categorized"]["active_code"]:
                print(f"      - {file_path} ({len(refs)} reference(s))")

        if verification["counts"]["test_files"] > 0:
            print("\n   Test Files (update or remove):")
            for file_path, refs in verification["categorized"]["test_files"]:
                print(f"      - {file_path} ({len(refs)} reference(s))")

        return

    # Default: scan for legacy references
    findings = analyzer.scan_for_legacy_references()

    # Print summary
    total_issues = sum(len(files) for files in findings.values())
    print("\nLegacy Reference Analysis Complete")
    print(f"   Files with issues: {total_issues}")

    if total_issues > 0:
        for pattern_type, files in findings.items():
            if files:
                print(f"   {pattern_type}: {len(files)} files")


if __name__ == "__main__":
    main()
