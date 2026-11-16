#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Consolidated Report Generator

Generates STATUS_BRIEF.md, PRIORITIES_BRIEF.md, and CONSOLIDATED_REPORT.md
in the development_tools root directory.

This module provides a simple interface to generate all consolidated reports
that are used by AI collaborators and human developers.
"""

import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from ..shared.service import AIToolsService
    from ..shared.file_rotation import create_output_file
except ImportError:
    from development_tools.shared.service import AIToolsService
    from development_tools.shared.file_rotation import create_output_file

from development_tools.shared.logging import get_dev_tools_logger

logger = get_dev_tools_logger("development_tools")


def generate_consolidated_reports(
    project_root: str | None = None, config_path: str | None = None
) -> dict:
    """
    Generate all consolidated reports (STATUS_BRIEF.md, PRIORITIES_BRIEF.md, CONSOLIDATED_REPORT.md).

    Args:
        project_root: Optional project root directory
        config_path: Optional path to config file

    Returns:
        Dictionary with paths to generated files
    """
    service = AIToolsService(project_root=project_root, config_path=config_path)
    output_project_root = Path(project_root) if project_root is not None else None

    def write_report(path: str, content: str) -> Path:
        if output_project_root is None:
            return create_output_file(path, content)
        try:
            return create_output_file(path, content, project_root=output_project_root)
        except TypeError as exc:
            # Some focused tests patch create_output_file with the historical
            # two-argument signature.
            if "project_root" not in str(exc):
                raise
            return create_output_file(path, content)

    # Generate Status Brief document
    status_brief = service._generate_status_brief_document()
    status_brief_file = write_report("development_tools/STATUS_BRIEF.md", status_brief)

    # Generate Priorities Brief document
    priorities_brief = service._generate_priorities_brief_document()
    priorities_brief_file = write_report("development_tools/PRIORITIES_BRIEF.md", priorities_brief)

    # Generate consolidated report
    consolidated_report = service._generate_consolidated_report()
    consolidated_file = write_report(
        "development_tools/CONSOLIDATED_REPORT.md",
        consolidated_report,
    )

    logger.info("Generated consolidated reports:")
    logger.info(f"  - STATUS_BRIEF.md: {status_brief_file}")
    logger.info(f"  - PRIORITIES_BRIEF.md: {priorities_brief_file}")
    logger.info(f"  - CONSOLIDATED_REPORT.md: {consolidated_file}")

    return {
        "status_brief": str(status_brief_file),
        "priorities_brief": str(priorities_brief_file),
        "consolidated_report": str(consolidated_file),
    }


if __name__ == "__main__":
    """CLI entry point for generating consolidated reports."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate consolidated reports (STATUS_BRIEF.md, PRIORITIES_BRIEF.md, CONSOLIDATED_REPORT.md)"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default=None,
        help="Path to config file (default: use built-in config)",
    )

    args = parser.parse_args()

    try:
        results = generate_consolidated_reports(
            project_root=args.project_root, config_path=args.config_path
        )
        print("Successfully generated consolidated reports:")
        for key, path in results.items():
            print(f"  {key}: {path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error generating consolidated reports: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)
