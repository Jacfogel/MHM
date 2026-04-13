#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Synchronization Checker

This script checks for paired AI/human documentation consistency.
Other documentation checks have been decomposed into separate tools:
- Path drift: analyze_path_drift.py
- ASCII compliance: analyze_ascii_compliance.py
- Heading numbering: analyze_heading_numbering.py
- Missing addresses: analyze_missing_addresses.py
- Unconverted links: analyze_unconverted_links.py
- Directory trees: generate_directory_tree.py

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/analyze_documentation_sync.py [--check]
"""

import re
import argparse
import sys
from pathlib import Path
from typing import Any
from collections import defaultdict

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
if __name__ != "__main__" and __package__ and "." in __package__:
    from .. import config
    from ..shared.constants import PAIRED_DOCS
else:
    from development_tools import config
    from development_tools.shared.constants import PAIRED_DOCS

logger = get_component_logger("development_tools")


class DocumentationSyncChecker:
    """Checks for paired AI/human documentation consistency."""

    def __init__(
        self, project_root: str | None = None, config_path: str | None = None
    ):
        """
        Initialize documentation sync checker.

        Args:
            project_root: Root directory of the project
            config_path: Optional path to external config file
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

        # Load paired docs from constants (which loads from config)
        self.paired_docs = dict(PAIRED_DOCS)

    def check_paired_documentation(self) -> dict[str, list[str]]:
        """Check for inconsistencies in paired AI/human documentation."""
        issues = defaultdict(list)

        for human_doc, ai_doc in self.paired_docs.items():
            human_path = self.project_root / human_doc
            ai_path = self.project_root / ai_doc

            if not human_path.exists():
                issues["missing_human_docs"].append(human_doc)
            if not ai_path.exists():
                issues["missing_ai_docs"].append(ai_doc)

            if human_path.exists() and ai_path.exists():
                # Check for content synchronization issues
                try:
                    with open(human_path, encoding="utf-8") as f:
                        human_content = f.read()
                    with open(ai_path, encoding="utf-8") as f:
                        ai_content = f.read()

                    # Simple content comparison (could be enhanced)
                    human_sections = set(
                        re.findall(r"^##\s+(.+)$", human_content, re.MULTILINE)
                    )
                    ai_sections = set(
                        re.findall(r"^##\s+(.+)$", ai_content, re.MULTILINE)
                    )

                    missing_in_ai = human_sections - ai_sections
                    missing_in_human = ai_sections - human_sections

                    if missing_in_ai:
                        issues["content_sync"].append(
                            f"{human_doc} has sections missing in {ai_doc}: {missing_in_ai}"
                        )
                    if missing_in_human:
                        issues["content_sync"].append(
                            f"{ai_doc} has sections missing in {human_doc}: {missing_in_human}"
                        )

                except Exception as e:
                    issues["read_errors"].append(
                        f"Error reading {human_doc} or {ai_doc}: {e}"
                    )

        return issues

    def run_checks(self) -> dict[str, Any]:
        """
        Run paired documentation synchronization checks and return results in standard format.

        Note: Other documentation checks (path drift, ASCII compliance, etc.)
        have been decomposed into separate tools. This method only checks
        paired documentation consistency.

        Returns:
            Dictionary with standard format: 'summary', and 'details' keys
        """
        if logger:
            logger.debug("Analyzing documentation synchronization...")

        paired_docs = self.check_paired_documentation()

        total_issues = sum(len(issues) for issues in paired_docs.values())
        status = "PASS" if total_issues == 0 else "FAIL"

        return {
            "summary": {
                "total_issues": total_issues,
                "files_affected": 0,
                "status": status,
            },
            "details": {"paired_doc_issues": total_issues, "paired_docs": paired_docs},
        }

    def print_report(self, results: dict[str, Any]):
        """Print a formatted report of the results."""
        summary = results["summary"]
        details = results["details"]
        paired_docs = details.get("paired_docs", {})
        paired_doc_issues = details.get("paired_doc_issues", 0)
        print("\nSUMMARY:")
        print(f"   Status: {summary['status']}")
        print(f"   Total Issues: {summary['total_issues']}")
        print(f"   Paired Doc Issues: {paired_doc_issues}")

        if paired_docs:
            print("\nPAIRED DOCUMENTATION ISSUES:")
            for issue_type, issues in paired_docs.items():
                if issues:
                    print(f"   {issue_type}:")
                    for issue in issues:
                        # Clean Unicode characters that cause encoding issues
                        clean_issue = issue.encode("ascii", "ignore").decode("ascii")
                        print(f"     - {clean_issue}")

        if summary["total_issues"] == 0:
            print("\nAll paired documentation synchronization checks passed!")
        else:
            print(
                f"\nFound {summary['total_issues']} paired documentation synchronization issues."
            )


def main():
    """Main entry point."""
    import json

    parser = argparse.ArgumentParser(
        description="Check paired documentation synchronization"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON in standard format"
    )
    parser.add_argument(
        "--check-example-markers",
        action="store_true",
        help=(
            "Advisory (V5 §3.0): flag file paths in Example sections that lack "
            "[OK]/[AVOID]/[GOOD]/[BAD]/[EXAMPLE] line markers"
        ),
    )

    args = parser.parse_args()

    checker = DocumentationSyncChecker()

    results = checker.run_checks()

    if args.check_example_markers:
        from development_tools.docs.example_marker_validation import (
            scan_paths_for_example_marker_findings,
        )

        paired_roots: list[str] = []
        for human_doc, ai_doc in checker.paired_docs.items():
            paired_roots.extend([human_doc, ai_doc])
        findings = scan_paths_for_example_marker_findings(
            checker.project_root, sorted(set(paired_roots))
        )
        results["details"]["example_marker_findings"] = findings
        results["summary"]["example_marker_hint_count"] = sum(
            len(v) for v in findings.values()
        )

    if args.json:
        # Output JSON in standard format
        print(json.dumps(results, indent=2))
    else:
        checker.print_report(results)
        if args.check_example_markers:
            ex = results["details"].get("example_marker_findings") or {}
            if ex:
                print("\nEXAMPLE MARKER HINTS (advisory, V5 §3.0):")
                for fn, lines in sorted(ex.items()):
                    print(f"   {fn}:")
                    for line in lines[:20]:
                        print(f"     - {line}")
                    if len(lines) > 20:
                        print(f"     ... +{len(lines) - 20} more")
            else:
                print(
                    "\nExample marker scan: no advisory hints (or no paired files scanned)."
                )


if __name__ == "__main__":
    main()
