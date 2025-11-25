#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""Shared helpers for AI development tooling."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence, Tuple, Dict, Any

from development_tools.services.standard_exclusions import (
    get_exclusions,
    should_exclude_file,
)
from development_tools.services.tool_metadata import COMMAND_GROUPS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Command tier grouping for `help`
COMMAND_TIERS = COMMAND_GROUPS


@dataclass(frozen=True)
class ProjectPaths:
    """Convenience accessor for common project directories."""

    root: Path = PROJECT_ROOT
    docs: Path = PROJECT_ROOT / "ai_development_docs"
    dev_docs: Path = PROJECT_ROOT / "development_docs"
    data: Path = PROJECT_ROOT / "data"
    tests: Path = PROJECT_ROOT / "tests"


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


def setup_ai_tools_imports():
    """Setup imports for AI tools - handles both relative and absolute imports cleanly."""
    import sys
    from pathlib import Path
    
    # Add project root to path for core module imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    return project_root


def safe_import(relative_import, absolute_import):
    """Safely import modules, trying relative first, then absolute."""
    try:
        return __import__(relative_import, fromlist=[''])
    except ImportError:
        return __import__(absolute_import, fromlist=[''])


def iter_python_sources(directories: Sequence[Path | str], *, tool_type: str = "analysis", context: str = "development") -> Iterator[Path]:
    """Yield Python source files from the provided directories using standard exclusions."""
    base_exclusions = get_exclusions(tool_type, context)
    for directory in directories:
        base_path = PROJECT_ROOT / directory if isinstance(directory, str) else directory
        if not base_path.exists():
            continue
        for path in base_path.rglob("*.py"):
            if should_exclude_file(str(path), tool_type=tool_type, context=context):
                continue
            yield path


def iter_markdown_files(directories: Sequence[Path | str]) -> Iterator[Path]:
    for directory in directories:
        base_path = PROJECT_ROOT / directory if isinstance(directory, str) else directory
        if not base_path.exists():
            continue
        for path in base_path.rglob("*.md"):
            yield path


def run_cli(execute: Callable[[argparse.Namespace], Tuple[int, str, Dict[str, Any]]], *, description: str, arguments: Sequence[Tuple[Sequence[str], Dict[str, Any]]] | None = None) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    if arguments:
        for args, kwargs in arguments:
            parser.add_argument(*args, **kwargs)
    namespace = parser.parse_args()
    exit_code, text_output, data = execute(namespace)
    if namespace.json:
        print(json.dumps(data or {}, indent=2, sort_keys=True))
    elif text_output:
        print(ensure_ascii(text_output))
    return exit_code



def summary_block(title: str, lines: Iterable[str]) -> str:
    body = '\n'.join(lines)
    underline = '-' * len(title)
    if body:
        return f"{title}\n{underline}\n{body}\n"
    return f"{title}\n{underline}\n"

