#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Documentation Fix Tool (Dispatcher)

Orchestrates all documentation fix operations by calling specialized fixers:
- fix_documentation_addresses.py - Adds file addresses
- fix_documentation_ascii.py - Fixes non-ASCII characters
- fix_documentation_headings.py - Numbers headings
- fix_documentation_links.py - Converts paths to links

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python docs/fix_documentation.py [--add-addresses] [--fix-ascii] [--number-headings] [--convert-links] [--all] [--dry-run]
"""

import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .fix_documentation_addresses import DocumentationAddressFixer
    from .fix_documentation_ascii import DocumentationASCIIFixer
    from .fix_documentation_headings import DocumentationHeadingFixer
    from .fix_documentation_links import DocumentationLinkFixer
except ImportError:
    from development_tools.docs.fix_documentation_addresses import (
        DocumentationAddressFixer,
    )
    from development_tools.docs.fix_documentation_ascii import DocumentationASCIIFixer
    from development_tools.docs.fix_documentation_headings import (
        DocumentationHeadingFixer,
    )
    from development_tools.docs.fix_documentation_links import DocumentationLinkFixer

logger = get_component_logger("development_tools")


def main():
    """Main entry point - dispatches to specialized fixers."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix documentation issues")
    parser.add_argument(
        "--add-addresses",
        action="store_true",
        help="Add file addresses to documentation files",
    )
    parser.add_argument(
        "--fix-ascii",
        action="store_true",
        help="Fix non-ASCII characters in documentation",
    )
    parser.add_argument(
        "--number-headings",
        action="store_true",
        help="Number H2 and H3 headings in documentation",
    )
    parser.add_argument(
        "--convert-links",
        action="store_true",
        help="Convert file paths to markdown links",
    )
    parser.add_argument("--all", action="store_true", help="Apply all fix operations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()

    results = {}
    total_errors = 0

    if args.add_addresses or args.all:
        fixer = DocumentationAddressFixer()
        result = fixer.fix_add_addresses(dry_run=args.dry_run)
        results["add_addresses"] = result
        total_errors += result.get("errors", 0)
        print(
            f"\nAdd Addresses: Updated {result['updated']}, Skipped {result['skipped']}, Errors {result['errors']}"
        )

    if args.fix_ascii or args.all:
        fixer = DocumentationASCIIFixer()
        result = fixer.fix_ascii(dry_run=args.dry_run)
        results["fix_ascii"] = result
        total_errors += result.get("errors", 0)
        print(
            f"\nFix ASCII: Updated {result['files_updated']} files, Made {result['replacements_made']} replacements, Errors {result['errors']}"
        )

    if args.number_headings or args.all:
        fixer = DocumentationHeadingFixer()
        result = fixer.fix_number_headings(dry_run=args.dry_run)
        results["number_headings"] = result
        total_errors += result.get("errors", 0)
        print(
            f"\nNumber Headings: Updated {result['files_updated']} files, Fixed {result['issues_fixed']} issues, Errors {result['errors']}"
        )

    if args.convert_links or args.all:
        fixer = DocumentationLinkFixer()
        result = fixer.fix_convert_links(dry_run=args.dry_run)
        results["convert_links"] = result
        total_errors += result.get("errors", 0)
        print(
            f"\nConvert Links: Updated {result['files_updated']} files, Made {result['changes_made']} changes, Errors {result['errors']}"
        )

    if not (
        args.add_addresses
        or args.fix_ascii
        or args.number_headings
        or args.convert_links
        or args.all
    ):
        parser.print_help()
        return 1

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
