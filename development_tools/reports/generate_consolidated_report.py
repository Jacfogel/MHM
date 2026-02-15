#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Consolidated Report Generator

Generates AI_STATUS.md, AI_PRIORITIES.md, and consolidated_report.md
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

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def generate_consolidated_reports(
    project_root: str = None, config_path: str = None
) -> dict:
    """
    Generate all consolidated reports (AI_STATUS.md, AI_PRIORITIES.md, consolidated_report.md).

    Args:
        project_root: Optional project root directory
        config_path: Optional path to config file

    Returns:
        Dictionary with paths to generated files
    """
    service = AIToolsService(project_root=project_root, config_path=config_path)

    # Generate AI Status document
    ai_status = service._generate_ai_status_document()
    ai_status_file = create_output_file("development_tools/AI_STATUS.md", ai_status)

    # Generate AI Priorities document
    ai_priorities = service._generate_ai_priorities_document()
    ai_priorities_file = create_output_file(
        "development_tools/AI_PRIORITIES.md", ai_priorities
    )

    # Generate consolidated report
    consolidated_report = service._generate_consolidated_report()
    consolidated_file = create_output_file(
        "development_tools/consolidated_report.md", consolidated_report
    )

    logger.info(f"Generated consolidated reports:")
    logger.info(f"  - AI_STATUS.md: {ai_status_file}")
    logger.info(f"  - AI_PRIORITIES.md: {ai_priorities_file}")
    logger.info(f"  - consolidated_report.md: {consolidated_file}")

    return {
        "ai_status": str(ai_status_file),
        "ai_priorities": str(ai_priorities_file),
        "consolidated_report": str(consolidated_file),
    }


if __name__ == "__main__":
    """CLI entry point for generating consolidated reports."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate consolidated reports (AI_STATUS.md, AI_PRIORITIES.md, consolidated_report.md)"
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
