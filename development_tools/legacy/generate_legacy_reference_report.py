#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Legacy Reference Report Generator (Portable)

This script generates markdown reports from legacy reference analysis results.
It takes analysis results from analyze_legacy_references.py and produces a
formatted report. Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python legacy/generate_legacy_reference_report.py [--findings-file FILE] [--output-file FILE]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

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


class LegacyReferenceReportGenerator:
    """Generates markdown reports from legacy reference analysis results."""

    def __init__(self, project_root: str = "."):
        """
        Initialize legacy reference report generator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()

    def _should_exclude_report_path(self, file_path: str) -> bool:
        """Apply shared exclusion rules before rendering file-level findings."""
        from development_tools.shared.standard_exclusions import should_exclude_file

        normalized = str(file_path).replace("\\", "/")
        if normalized.endswith("run_tests.py"):
            return False
        if self._is_historical_context_path(normalized):
            return True
        return should_exclude_file(
            normalized, tool_type="analysis", context="development"
        )

    def _is_historical_context_path(self, normalized_path: str) -> bool:
        """Treat historical/planning docs as out of scope for legacy cleanup reporting."""
        lowered = normalized_path.lower().strip("/")
        base_name = Path(lowered).name

        if "/archive/" in f"/{lowered}/" or "/archived/" in f"/{lowered}/":
            return True
        if lowered.startswith("archive/") or lowered.startswith("archived/"):
            return True

        changelog_files = {
            "ai_changelog.md",
            "changelog_detail.md",
            "ai_changelog_archive.md",
        }
        if base_name in changelog_files:
            return True

        if "changelog_history/" in lowered:
            return True

        planning_files = {
            "todo.md",
            "plans.md",
        }
        if base_name in planning_files:
            return True

        if base_name.endswith("_plan.md") or base_name.startswith("plan_"):
            return True

        return False

    def generate_cleanup_report(
        self, findings: dict[str, list[tuple[str, str, list[dict[str, Any]]]]]
    ) -> str:
        """
        Generate a report of all legacy references found.

        Args:
            findings: Analysis results from LegacyReferenceAnalyzer.scan_for_legacy_references()

        Returns:
            Markdown report string
        """
        report_lines = []

        generated_at = now_timestamp_full()
        report_lines.append("# Legacy Reference Cleanup Report")
        report_lines.append("")
        report_lines.append("> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`")
        report_lines.append(
            "> **Generated**: This file is auto-generated. Do not edit manually."
        )
        report_lines.append(f"> **Last Generated**: {generated_at}")
        report_lines.append(
            "> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator"
        )

        filtered_findings: dict[str, list[tuple[str, str, list[dict[str, Any]]]]] = {}
        for pattern_type, files in findings.items():
            kept = [
                item
                for item in files
                if not self._should_exclude_report_path(item[0])
            ]
            if kept:
                filtered_findings[pattern_type] = kept

        affected_files = {
            file_path
            for files in filtered_findings.values()
            for file_path, _, _ in files
        }
        report_lines.append(f"**Total Files with Issues**: {len(affected_files)}")

        total_markers = sum(
            len(matches)
            for files in filtered_findings.values()
            for _, _, matches in files
        )
        report_lines.append(
            f"**Legacy Compatibility Markers Detected**: {total_markers}"
        )
        report_lines.append("")

        # Always include Summary section
        report_lines.append("## Summary")
        if affected_files:
            report_lines.append("- Scan mode only: no automated fixes were applied.")
            report_lines.append(
                "- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report."
            )

            legacy_entries = filtered_findings.get("legacy_compatibility_markers", [])
            if legacy_entries:
                legacy_marker_count = sum(
                    len(matches) for _, _, matches in legacy_entries
                )
                report_lines.append(
                    f"- Legacy compatibility markers remain in {len(legacy_entries)} file(s) ({legacy_marker_count} total markers)."
                )
                other_file_count = len(affected_files) - len(legacy_entries)
                other_marker_count = total_markers - legacy_marker_count
                if other_file_count > 0 and other_marker_count > 0:
                    report_lines.append(
                        f"- Remaining counts come from legacy inventory tracking categories ({other_file_count} file(s), {other_marker_count} marker(s))."
                    )
                enabled_fields_files = {
                    file_path
                    for file_path, _, matches in legacy_entries
                    if any(
                        "enabled_fields" in (match.get("line_content", "") or "")
                        for match in matches
                    )
                }
                if enabled_fields_files:
                    report_lines.append(
                        f"- {len(enabled_fields_files)} file(s) still reference `enabled_fields`; confirm any clients still produce that payload."
                    )
                preference_files = {
                    file_path
                    for file_path, _, matches in legacy_entries
                    if any(
                        "Preference" in (match.get("line_content", "") or "")
                        for match in matches
                    )
                }
                if preference_files:
                    report_lines.append(
                        f"- {len(preference_files)} file(s) rely on legacy preference delegation paths; decide whether to modernise or retire them."
                    )
            report_lines.append("")

        report_lines.append("## Recommended Follow-Up")
        report_lines.append(
            "- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)"
        )
        report_lines.append(
            "1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers."
        )
        report_lines.append(
            "2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance."
        )
        report_lines.append(
            "3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues."
        )
        report_lines.append("")

        for pattern_type in sorted(filtered_findings.keys()):
            files = filtered_findings[pattern_type]
            if not files:
                continue

            report_lines.append(f"## {pattern_type.replace('_', ' ').title()}")
            report_lines.append(f"**Files Affected**: {len(files)}")
            report_lines.append("")

            for file_path, _content, matches in sorted(files, key=lambda item: item[0]):
                report_lines.append(f"### {file_path}")
                report_lines.append(f"**Issues Found**: {len(matches)}")
                report_lines.append("")

                for match in sorted(matches, key=lambda m: m.get("line", 0)):
                    line_num = match.get("line", 0)
                    match_text = match.get("match", "")
                    line_content = match.get("line_content", "")
                    report_lines.append(f"- **Line {line_num}**: `{match_text}`")
                    report_lines.append("  ```")
                    report_lines.append(f"  {line_content}")
                    report_lines.append("  ```")
                    report_lines.append("")

        return "\n".join(report_lines)

    def save_report(self, report: str, output_file: Path | None = None) -> Path:
        """
        Save the report to a file.

        Args:
            report: The markdown report string
            output_file: Optional output file path. If None, uses default location.

        Returns:
            Path to the saved report file
        """
        if output_file is None:
            output_file = (
                self.project_root / "development_docs" / "LEGACY_REFERENCE_REPORT.md"
            )
        else:
            output_file = Path(output_file)

        # Ensure parent directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Use rotation system for archiving
        from development_tools.shared.file_rotation import create_output_file

        create_output_file(
            str(output_file),
            report,
            rotate=True,
            max_versions=7,
            project_root=self.project_root,
        )

        if logger:
            logger.debug(f"Legacy reference report saved: {output_file}")

        return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate legacy reference report from analysis results"
    )
    parser.add_argument(
        "--findings-file",
        type=str,
        metavar="FILE",
        help="JSON file containing analysis findings (optional, can read from stdin)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        metavar="FILE",
        help="Output file path (default: development_docs/LEGACY_REFERENCE_REPORT.md)",
    )

    args = parser.parse_args()

    generator = LegacyReferenceReportGenerator()

    # Load findings
    if args.findings_file:
        with open(args.findings_file, encoding="utf-8") as f:
            findings = json.load(f)
    else:
        # Try to read from stdin (for piping from analyzer)
        import sys

        if not sys.stdin.isatty():
            findings = json.load(sys.stdin)
        else:
            logger.error(
                "No findings provided. Use --findings-file or pipe JSON to stdin."
            )
            return 1

    # Generate report
    report = generator.generate_cleanup_report(findings)

    # Save report
    output_file = Path(args.output_file) if args.output_file else None
    saved_path = generator.save_report(report, output_file)

    logger.info("Legacy Reference Report Generated")
    logger.info("Report saved to: %s" % saved_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
