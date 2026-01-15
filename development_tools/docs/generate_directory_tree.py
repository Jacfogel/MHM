#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Directory Tree Generator

This script generates directory trees for documentation with placeholders for
certain directories. Configuration is loaded from external config file
(development_tools_config.json) if available, making this tool portable
across different projects.

Usage:
    python docs/generate_directory_tree.py [--output FILE]
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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


class DirectoryTreeGenerator:
    """Generates directory trees for documentation."""

    def __init__(
        self, project_root: Optional[str] = None, config_path: Optional[str] = None
    ):
        """
        Initialize directory tree generator.

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

        # Get paths config for output directories
        paths_config = config.get_paths_config()
        self.docs_dir = paths_config.get("development_docs_dir", "development_docs")

    def generate_directory_tree(self, output_file: Optional[str] = None) -> str:
        """
        Generate a directory tree for documentation with placeholders for certain directories.

        NOTE: This tool should ONLY be run via the 'docs' command, NOT during audits.
        Static documentation (DIRECTORY_TREE, FUNCTION_REGISTRY, MODULE_DEPENDENCIES)
        should not be regenerated during audit runs.

        Args:
            output_file: Optional output file path. If None, uses default from config.

        Returns:
            Path to the generated file
        """
        # Use provided output_file or default from config
        if output_file is None:
            output_file = f"{self.docs_dir}/DIRECTORY_TREE.md"

        # Run tree command
        result = subprocess.run(
            ["tree", "/F", "/A"], capture_output=True, text=True, shell=True
        )

        if result.returncode != 0:
            if logger:
                logger.error("Error running tree command")
            return ""

        lines = result.stdout.split("\n")

        # Import constants from services
        from development_tools.shared.standard_exclusions import DOC_SYNC_PLACEHOLDERS

        placeholders = DOC_SYNC_PLACEHOLDERS

        # Process lines
        processed_lines = []
        skip_until_next_dir = False

        for i, line in enumerate(lines):
            if skip_until_next_dir:
                # Skip ALL content until we hit the next root-level directory
                # Look for lines that start with +--- (root level directories)
                if line.strip() and line.startswith("+---"):
                    # Found next directory at same level, stop skipping
                    skip_until_next_dir = False
                    # Now process this line normally (fall through to the else clause)
                else:
                    # Skip this line completely (don't add it, even if it's a nested placeholder)
                    continue

            # Check if this line contains a directory we want to replace
            should_replace = False
            replacement = None

            for key, placeholder in placeholders.items():
                if key in line and ("+---" in line or "\\---" in line):
                    should_replace = True
                    replacement = placeholder
                    break

            if should_replace:
                # Add the directory line
                processed_lines.append(line)
                # Add the placeholder
                processed_lines.append(replacement)
                skip_until_next_dir = True
            else:
                processed_lines.append(line)

        # Create the final content with standardized metadata
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        header = [
            "# Project Directory Tree",
            "",
            f"> **File**: `{output_file}`",
            "> **Generated**: This file is auto-generated. Do not edit manually.",
            f"> **Last Generated**: {timestamp}",
            f"> **Source**: `python development_tools/docs/generate_directory_tree.py` - Directory Tree Generator",
            "> **Audience**: Human developer and AI collaborators",
            "> **Purpose**: Visual representation of project directory structure",
            "> **Status**: **ACTIVE** - Auto-generated from filesystem tree command",
            "",
        ]

        footer = ["", "---", "", "*Generated by generate_directory_tree.py*"]

        final_content = header + processed_lines + footer

        # Write to file with rotation
        # NOTE: create_output_file() will automatically block writes to DIRECTORY_TREE.md
        # during audits or tests (when writing to real project, not test directories)
        from development_tools.shared.file_rotation import create_output_file

        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            create_output_file(
                str(output_path),
                "\n".join(final_content),
                rotate=True,
                max_versions=7,
                project_root=self.project_root,
            )
        except RuntimeError as e:
            # Handle safeguard blocking (from create_output_file)
            if "Cannot write" in str(e) and "DIRECTORY_TREE.md" in str(e):
                if logger:
                    logger.warning(f"Skipping DIRECTORY_TREE.md generation: {e}")
                return ""
            raise

        if logger:
            logger.info(f"Directory tree generated: {output_path}")
        return str(output_path)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate directory tree for documentation"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: development_docs/DIRECTORY_TREE.md)",
    )

    args = parser.parse_args()

    generator = DirectoryTreeGenerator()
    output_file = generator.generate_directory_tree(args.output)

    if output_file:
        print(f"Directory tree generated: {output_file}")
    else:
        print("Error: Failed to generate directory tree")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
