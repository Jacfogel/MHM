#!/usr/bin/env python3
# TOOL_TIER: core

"""Shared helpers for AI development tooling."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence, Tuple, Dict, Any, Optional

from development_tools.shared.standard_exclusions import should_exclude_file
from development_tools.shared.tool_metadata import COMMAND_GROUPS

# Import config for project root and paths
try:
    from .. import config
except ImportError:
    # Fallback for when run as standalone script
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from development_tools import config

# Load external config on module import (if not already loaded)
try:
    if hasattr(config, "load_external_config"):
        config.load_external_config()
except (AttributeError, ImportError):
    pass


# Get project root from config (config-driven, portable)
def _get_project_root() -> Path:
    """Get project root from config.

    Always returns a fully-resolved absolute path so callers can safely use
    Path.relative_to() comparisons against other resolved paths.
    """
    try:
        return Path(config.get_project_root()).expanduser().resolve()
    except (AttributeError, ImportError, TypeError):
        # Fallback to path calculation if config not available
        return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _get_project_root()

# Command tier grouping for `help`
COMMAND_TIERS = COMMAND_GROUPS


class ProjectPaths:
    """Convenience accessor for common project directories.

    Paths are loaded from config for portability. Falls back to defaults if config not available.
    """

    def __init__(self, root: Optional[Path] = None):
        """Initialize ProjectPaths with config-driven paths.

        Args:
            root: Optional project root path. If None, uses config.get_project_root()
        """
        # Get project root
        if root is not None:
            project_root = Path(root)
        else:
            try:
                project_root = Path(config.get_project_root()).expanduser().resolve()
            except (AttributeError, ImportError, TypeError):
                # Fallback to path calculation if config not available
                project_root = Path(__file__).resolve().parents[2]

        # Get paths from config
        try:
            paths_config = config.get_paths_config()
            self.root = project_root
            self.docs = project_root / paths_config.get(
                "ai_docs_dir", "ai_development_docs"
            )
            self.dev_docs = project_root / paths_config.get(
                "development_docs_dir", "development_docs"
            )
            self.data = project_root / paths_config.get("data_dir", "data")
            # Note: tests_dir not in paths_config, use default
            self.tests = project_root / "tests"
        except (AttributeError, ImportError, TypeError, KeyError):
            # Fallback to defaults if config not available
            self.root = project_root
            self.docs = project_root / "ai_development_docs"
            self.dev_docs = project_root / "development_docs"
            self.data = project_root / "data"
            self.tests = project_root / "tests"


def ensure_ascii(text: str) -> str:
    """Return text restricted to ASCII, replacing unsupported characters."""
    if not text:
        return ""
    return text.encode("ascii", "replace").decode("ascii")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_python_sources(
    directories: Sequence[Path | str],
    *,
    tool_type: str = "analysis",
    context: str = "development",
    project_root: Optional[Path] = None,
) -> Iterator[Path]:
    """Yield Python source files from the provided directories using standard exclusions.

    Args:
        directories: Directories to search (Path objects or strings relative to project_root)
        tool_type: Type of tool for exclusion filtering
        context: Context for exclusion filtering
        project_root: Optional project root path. If None, uses config.get_project_root()
    """
    # Get project root from config if not provided
    if project_root is None:
        project_root = PROJECT_ROOT

    for directory in directories:
        base_path = (
            project_root / directory if isinstance(directory, str) else directory
        )
        if not base_path.exists():
            continue
        for path in base_path.rglob("*.py"):
            if should_exclude_file(str(path), tool_type=tool_type, context=context):
                continue
            yield path


def run_cli(
    execute: Callable[[argparse.Namespace], Tuple[int, str, Dict[str, Any]]],
    *,
    description: str,
    arguments: Sequence[Tuple[Sequence[str], Dict[str, Any]]] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON"
    )
    if arguments:
        for args, kwargs in arguments:
            parser.add_argument(*args, **kwargs)
    namespace = parser.parse_args()
    try:
        exit_code, text_output, data = execute(namespace)
    except Exception as e:
        print(f"ERROR in execute: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        raise
    if namespace.json:
        try:
            print(json.dumps(data or {}, indent=2, sort_keys=True))
        except Exception as e:
            print(f"ERROR in json.dumps: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            raise
    elif text_output:
        print(ensure_ascii(text_output))
    return exit_code


def summary_block(title: str, lines: Iterable[str]) -> str:
    body = "\n".join(lines)
    underline = "-" * len(title)
    if body:
        return f"{title}\n{underline}\n{body}\n"
    return f"{title}\n{underline}\n"
