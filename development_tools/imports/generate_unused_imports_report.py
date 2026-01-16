#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Unused Imports Report Generator

This script generates markdown reports from unused imports analysis results.
It loads analysis results from analyze_unused_imports_results.json and produces
a formatted report. Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python imports/generate_unused_imports_report.py [--input-file FILE] [--output-file FILE] [--json]

Integration:
    python development_tools/run_development_tools.py unused-imports-report
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger
from core.service_utilities import now_readable_timestamp

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.output_storage import load_tool_result
    from ..shared.file_rotation import create_output_file
except ImportError:
    from development_tools import config
    from development_tools.shared.output_storage import load_tool_result
    from development_tools.shared.file_rotation import create_output_file

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, "load_external_config"):
        config.load_external_config()
except (AttributeError, ImportError):
    pass

logger = get_component_logger("development_tools")


class UnusedImportsReportGenerator:
    """Generates markdown reports from unused imports analysis results."""

    def __init__(self, analysis_data: Dict[str, Any]):
        """
        Initialize report generator with analysis data.

        Args:
            analysis_data: Analysis results dict (from analyze_unused_imports_results.json)
                          Should contain 'findings' and 'stats' keys, or be in standard format
                          with 'details' containing the findings/stats
        """
        # Handle both standard format and legacy format
        if "details" in analysis_data:
            # Standard format - extract from details
            details = analysis_data.get("details", {})
            # First try to get full findings (preferred)
            self.findings = details.get("findings", {})
            self.stats = details.get("stats", {})

            # Check if we have actual findings data (list of items) or just empty dicts
            has_full_findings = (
                self.findings
                and isinstance(self.findings, dict)
                and any(
                    isinstance(items, list) and len(items) > 0
                    for items in self.findings.values()
                )
            )

            if not has_full_findings:
                # Try to reconstruct findings from by_category (fallback - only counts available)
                by_category = details.get("by_category", {})
                self.findings = {
                    cat: []
                    for cat in [
                        "obvious_unused",
                        "type_hints_only",
                        "re_exports",
                        "conditional_imports",
                        "star_imports",
                        "test_mocking",
                        "qt_testing",
                        "test_infrastructure",
                        "production_test_mocking",
                        "ui_imports",
                    ]
                }
                # Note: Only counts available, not full findings
                self.findings_counts = by_category
            else:
                # We have full findings - use them
                self.findings_counts = None
        else:
            # Legacy format - direct access
            self.findings = analysis_data.get("findings", {})
            self.stats = analysis_data.get("stats", {})
            self.findings_counts = None

        # Ensure findings has all categories
        if not self.findings:
            self.findings = {
                "obvious_unused": [],
                "type_hints_only": [],
                "re_exports": [],
                "conditional_imports": [],
                "star_imports": [],
                "test_mocking": [],
                "qt_testing": [],
                "test_infrastructure": [],
                "production_test_mocking": [],
                "ui_imports": [],
            }

    def generate_report(self) -> str:
        """Generate a detailed markdown report."""
        timestamp = now_readable_timestamp()

        lines = []
        lines.append("# Unused Imports Report")
        lines.append("")
        lines.append("> **File**: `development_docs/UNUSED_IMPORTS_REPORT.md`")
        lines.append(
            "> **Generated**: This file is auto-generated. Do not edit manually."
        )
        lines.append(f"> **Last Generated**: {timestamp}")
        lines.append(
            "> **Source**: `python development_tools/run_development_tools.py unused-imports-report` - Unused Imports Report Generator"
        )
        lines.append("")

        # Summary statistics
        lines.append("## Summary Statistics")
        lines.append("")
        files_scanned = self.stats.get("files_scanned", 0)
        files_with_issues = self.stats.get("files_with_issues", 0)
        total_unused = self.stats.get("total_unused", 0)

        lines.append(f"- **Total Files Scanned**: {files_scanned}")
        lines.append(f"- **Files with Unused Imports**: {files_with_issues}")
        lines.append(f"- **Total Unused Imports**: {total_unused}")
        lines.append("")

        # Category breakdown
        lines.append("## Breakdown by Category")
        lines.append("")

        # Use findings_counts if available (from standard format), otherwise use findings
        if self.findings_counts:
            for category, count in self.findings_counts.items():
                category_name = category.replace("_", " ").title()
                lines.append(f"- **{category_name}**: {count} imports")
        else:
            for category, items in self.findings.items():
                category_name = category.replace("_", " ").title()
                lines.append(f"- **{category_name}**: {len(items)} imports")
        lines.append("")

        # Detailed findings by category (only if we have full findings, not just counts)
        if not self.findings_counts and any(self.findings.values()):
            category_order = [
                "obvious_unused",
                "type_hints_only",
                "re_exports",
                "conditional_imports",
                "star_imports",
                "test_mocking",
                "qt_testing",
                "test_infrastructure",
                "production_test_mocking",
                "ui_imports",
            ]

            for category in category_order:
                items = self.findings.get(category, [])
                if not items:
                    continue

                category_name = category.replace("_", " ").title()
                lines.append(f"## {category_name}")
                lines.append("")

                # Add recommendation for each category
                if category == "obvious_unused":
                    lines.append(
                        "**Recommendation**: These imports can likely be safely removed."
                    )
                elif category == "type_hints_only":
                    lines.append(
                        "**Recommendation**: Consider using `TYPE_CHECKING` guard for these imports."
                    )
                elif category == "re_exports":
                    lines.append(
                        "**Recommendation**: Review if these are intentional re-exports in `__init__.py` files."
                    )
                elif category == "conditional_imports":
                    lines.append(
                        "**Recommendation**: Review carefully - these may be for optional dependencies."
                    )
                elif category == "star_imports":
                    lines.append(
                        "**Recommendation**: Star imports can hide unused imports - consider explicit imports."
                    )
                elif category == "test_mocking":
                    lines.append(
                        "**Recommendation**: These imports are required for test mocking with `@patch` decorators and `patch.object()` calls."
                    )
                elif category == "qt_testing":
                    lines.append(
                        "**Recommendation**: These Qt imports are required for UI testing and signal handling."
                    )
                elif category == "test_infrastructure":
                    lines.append(
                        "**Recommendation**: These imports are required for test infrastructure (fixtures, data creation, etc.)."
                    )
                elif category == "production_test_mocking":
                    lines.append(
                        "**Recommendation**: These imports are required in production code for test mocking. Keep them."
                    )
                elif category == "ui_imports":
                    lines.append(
                        "**Recommendation**: These Qt imports are required for UI functionality. Keep them."
                    )
                lines.append("")

                # Group by file
                by_file = defaultdict(list)
                for item in items:
                    by_file[item["file"]].append(item)

                for file_path in sorted(by_file.keys()):
                    file_items = by_file[file_path]
                    lines.append(f"### `{file_path}`")
                    lines.append("")
                    lines.append(f"**Count**: {len(file_items)} unused import(s)")
                    lines.append("")

                    for item in sorted(file_items, key=lambda x: x.get("line", 0)):
                        lines.append(
                            f"- **Line {item.get('line', 0)}**: {item.get('message', '')}"
                        )
                    lines.append("")

        # Recommendations
        lines.append("## Overall Recommendations")
        lines.append("")
        lines.append(
            "1. **Obvious Unused**: Review and remove obvious unused imports to improve code cleanliness"
        )
        lines.append(
            '2. **Type Hints**: For type hint imports, consider using `from __future__ import annotations` and `TYPE_CHECKING` (note: the word "annotations" here refers to the Python `__future__` feature name, not a module to import)'
        )
        lines.append(
            "3. **Re-exports**: Verify `__init__.py` imports are intentional re-exports"
        )
        lines.append(
            "4. **Conditional Imports**: Be cautious with conditional imports - they may be handling optional dependencies"
        )
        lines.append(
            "5. **Star Imports**: Consider replacing star imports with explicit imports for better clarity"
        )
        lines.append(
            "6. **Test Mocking**: Keep imports required for `@patch` decorators and `patch.object()` calls"
        )
        lines.append(
            "7. **Qt Testing**: Keep Qt imports required for UI testing and signal handling"
        )
        lines.append(
            "8. **Test Infrastructure**: Keep imports required for test fixtures and data creation"
        )
        lines.append(
            "9. **Production Test Mocking**: Keep imports in production code that are mocked by tests"
        )
        lines.append(
            "10. **UI Imports**: Keep Qt imports required for UI functionality"
        )
        lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate unused imports report from analysis results"
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="Input JSON file with analysis results (default: load from analyze_unused_imports_results.json)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="development_docs/UNUSED_IMPORTS_REPORT.md",
        help="Output report path (default: development_docs/UNUSED_IMPORTS_REPORT.md)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output JSON data to stdout"
    )
    parser.add_argument(
        "--project-root", type=str, help="Project root directory (default: auto-detect)"
    )
    args = parser.parse_args()

    # Determine project root
    if args.project_root:
        project_root_path = Path(args.project_root).resolve()
    else:
        project_root_path = Path(__file__).parent.parent.parent

    # Load analysis results
    if args.input_file:
        # Load from specified file
        input_path = project_root_path / args.input_file
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1

        with open(input_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)
    else:
        # Load from standardized storage
        analysis_data = load_tool_result(
            "analyze_unused_imports",
            "imports",
            project_root=project_root_path,
            normalize=False,
        )

        if analysis_data is None:
            logger.error(
                "No analysis results found. Run 'python development_tools/run_development_tools.py unused-imports' first."
            )
            return 1

        # Extract data from wrapper
        if "data" in analysis_data:
            analysis_data = analysis_data["data"]

    # Generate report
    generator = UnusedImportsReportGenerator(analysis_data)
    report = generator.generate_report()

    # Output JSON if requested
    if args.json:
        report_data = {
            "report": report,
            "stats": generator.stats,
            "findings_counts": (
                generator.findings_counts
                if hasattr(generator, "findings_counts")
                else None
            ),
        }
        print(json.dumps(report_data, indent=2))

    # Write report to file with rotation
    output_path = project_root_path / args.output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    create_output_file(
        str(output_path),
        report,
        rotate=True,
        max_versions=7,
        project_root=project_root_path,
    )

    # Only print report info if not in JSON mode
    if not args.json:
        print(f"\nReport saved to: {output_path}")
        print(f"Files scanned: {generator.stats.get('files_scanned', 0)}")
        print(f"Files with issues: {generator.stats.get('files_with_issues', 0)}")
        print(f"Total unused imports: {generator.stats.get('total_unused', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
