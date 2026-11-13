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
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.standard_exclusions import should_exclude_file
from development_tools.shared.logging import get_dev_tools_logger
from development_tools.shared.time_helpers import now_timestamp_full

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


def _get_line_indent(line: str) -> int | None:
    """
    Return the character index where the "+---" or "\\---" marker appears.
    """
    for marker in ("+---", "\\---"):
        idx = line.find(marker)
        if idx >= 0:
            return idx
    return None


def _build_dir_path(line: str, indent: int, stack: list[str]) -> str | None:
    """
    Update the current path stack and return the joined path for the current directory.
    """
    segment = line[indent:]
    for marker in ("+---", "\\---"):
        if segment.startswith(marker):
            dir_name = segment[len(marker) :].strip()
            level = indent // 4
            stack[:] = stack[:level]
            stack.append(dir_name)
            return "/".join(stack)
    return None


def _get_tree_file_name(line: str) -> str | None:
    """Return a filename from a ``tree /F /A`` output line, if present."""
    if _get_line_indent(line) is not None:
        return None

    if "|" in line:
        file_name = line.rsplit("|", 1)[-1].strip()
    elif line.startswith("    "):
        file_name = line.strip()
    else:
        return None

    if not file_name or file_name.startswith("("):
        return None
    return file_name


def _is_sensitive_runtime_path(relative_path: str) -> bool:
    """Return whether a path must never be included in generated documentation."""
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized:
        return False

    parts = tuple(part for part in normalized.split("/") if part)
    name = parts[-1].lower()
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    if name.endswith((".flag", ".log", ".pid")):
        return True
    runtime_directories = {
        ".cache",
        ".pytest_cache",
        ".pytest_runtime",
        ".wrangler",
        "__pycache__",
        "data",
        "logs",
    }
    return any(part.lower() in runtime_directories for part in parts)


class DirectoryTreeGenerator:
    """Generates directory trees for documentation."""

    def __init__(
        self, project_root: str | None = None, config_path: str | None = None
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

    def _get_git_visible_paths(self) -> tuple[set[str], set[str]] | None:
        """Return Git-visible files and their parent directories.

        Tracked files and untracked, non-ignored files are included. ``None`` is
        returned outside a Git checkout. If Git cannot provide the manifest for
        a checkout, an empty allowlist is returned so generation fails closed.
        """
        if not (self.project_root / ".git").exists():
            return None

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.project_root),
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                    "-z",
                ],
                capture_output=True,
                text=True,
                shell=False,
                cwd=self.project_root,
            )
        except OSError as exc:
            if logger:
                logger.error("Git manifest unavailable for directory tree: %s", exc)
            return set(), set()

        if result.returncode != 0:
            if logger:
                logger.error("Git manifest unavailable for directory tree")
            return set(), set()

        files: set[str] = set()
        directories: set[str] = set()
        for raw_path in result.stdout.split("\0"):
            normalized = raw_path.strip().replace("\\", "/").strip("/")
            if not normalized or _is_sensitive_runtime_path(normalized):
                continue
            files.add(normalized)
            parent = Path(normalized).parent
            while str(parent) not in {"", "."}:
                directories.add(parent.as_posix())
                parent = parent.parent

        return files, directories

    def generate_directory_tree(self, output_file: str | None = None) -> str:
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

        git_visible_paths = self._get_git_visible_paths()
        visible_files: set[str] | None = None
        visible_directories: set[str] | None = None
        if git_visible_paths is not None:
            visible_files, visible_directories = git_visible_paths

        # Run tree command (Windows: tree.com; avoid shell=True — Bandit B602)
        tree_exe = "tree.com" if os.name == "nt" else "tree"
        result = subprocess.run(
            [tree_exe, "/F", "/A"],
            capture_output=True,
            text=True,
            shell=False,
            cwd=self.project_root,
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
        placeholder_skip_indent: int | None = None
        skip_exclusion_indent: int | None = None
        path_stack: list[str] = []

        for line in lines:
            line = line.rstrip()
            indent = _get_line_indent(line)

            if skip_exclusion_indent is not None:
                if indent is not None and indent <= skip_exclusion_indent:
                    skip_exclusion_indent = None
                else:
                    continue

            if placeholder_skip_indent is not None:
                if indent is not None and indent <= placeholder_skip_indent:
                    placeholder_skip_indent = None
                else:
                    continue

            dir_path = None
            if indent is not None:
                dir_path = _build_dir_path(line, indent, path_stack)

            if dir_path:
                if (
                    _is_sensitive_runtime_path(dir_path)
                    or should_exclude_file(Path(dir_path), context="development")
                    or (
                        visible_directories is not None
                        and dir_path not in visible_directories
                    )
                ):
                    skip_exclusion_indent = indent if indent is not None else 0
                    continue
            else:
                file_name = _get_tree_file_name(line)
                if file_name:
                    relative_path = "/".join([*path_stack, file_name])
                    if (
                        _is_sensitive_runtime_path(relative_path)
                        or should_exclude_file(
                            Path(relative_path), context="development"
                        )
                        or (
                            visible_files is not None
                            and relative_path not in visible_files
                        )
                    ):
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
                placeholder_skip_indent = indent if indent is not None else 0
            else:
                processed_lines.append(line)

        # Create the final content with standardized metadata
        timestamp = now_timestamp_full()

        header = [
            "# Project Directory Tree",
            "",
            f"> **File**: `{output_file}`",
            "> **Generated**: This file is auto-generated. Do not edit manually.",
            f"> **Last Generated**: {timestamp}",
            "> **Source**: `python development_tools/docs/generate_directory_tree.py` - Directory Tree Generator",
            "> **Audience**: Human developer and AI collaborators",
            "> **Purpose**: Visual representation of project directory structure",
            "> **Status**: **ACTIVE** - Auto-generated from Git-visible project files",
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
        logger.info(f"Directory tree generated: {output_file}")
    else:
        logger.error("Failed to generate directory tree")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
