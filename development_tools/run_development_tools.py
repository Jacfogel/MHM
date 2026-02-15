#!/usr/bin/env python3
# TOOL_TIER: core

# NOTE: This file was modified to test domain-aware coverage cache merging.

"""Command-line interface for AI development tools."""

import argparse
import shutil
import sys
import time
from pathlib import Path

# Add project root to path FIRST - this allows development_tools to be imported as a package
project_root = Path(__file__).resolve().parent.parent
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Now we can import development_tools as a package
try:
    from development_tools.shared.service import AIToolsService
    from development_tools.shared.cli_interface import COMMAND_REGISTRY
    from development_tools.shared.common import COMMAND_TIERS
except ImportError as e:
    # Provide helpful error message
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Current working directory:", Path.cwd())
    print("Project root:", project_root)
    print("Python path:", sys.path[:3])  # Show first 3 entries
    raise

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def _remove_path_with_retries(path: Path, retries: int = 10, delay_seconds: float = 0.2) -> None:
    """Best-effort Windows-friendly path removal."""
    if not path.exists():
        return

    for _ in range(retries):
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            else:
                path.unlink(missing_ok=True)
            return
        except Exception:
            try:
                for child in path.rglob("*"):
                    try:
                        child.chmod(0o700)
                    except Exception:
                        pass
                path.chmod(0o700)
            except Exception:
                pass
            time.sleep(delay_seconds)

    # Final best-effort
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    except Exception:
        pass


def _cleanup_transient_runtime_artifacts(project_root: Path) -> None:
    """Best-effort cleanup of transient artifacts created by audit/test subprocesses."""
    root_dirs = [
        ".pytest_cache",
        ".pytest_tmp_cache",
        ".tmp_devtools_pyfiles",
        ".tmp_pytest",
        ".tmp_pytest_runner",
        "htmlcov",
    ]

    for rel in root_dirs:
        target = project_root / rel
        _remove_path_with_retries(target)

    data_dir = project_root / "tests" / "data"
    if not data_dir.exists():
        return

    dir_prefixes = (
        "logs_",
        "mhm_pytest_tmp_main_",
        "pytest-of-",
        "tmp_",
    )
    file_prefixes = (
        "conversation_states_",
        "welcome_tracking_",
    )

    for item in data_dir.iterdir():
        try:
            if item.is_dir():
                if (
                    item.name in {"flags", "requests", "tag-tests"}
                    or item.name.startswith(dir_prefixes)
                    or (item.name.startswith("tmp") and item.name != "tmp")
                ):
                    _remove_path_with_retries(item)
            elif item.is_file():
                if item.suffix == ".json" and item.name.startswith(file_prefixes):
                    item.unlink(missing_ok=True)
        except Exception:
            pass


def _clear_all_caches(project_root: Path) -> int:
    """
    Clear all development tools cache files.

    Includes development-tools cache artifacts only (tool json caches/results
    used for cache reuse and freshness checks). It intentionally does NOT clean:
    - Python interpreter caches (__pycache__)
    - pytest runtime caches (.pytest_cache)
    - unrelated non-tool cache directories

    Args:
        project_root: Project root directory

    Returns:
        Number of cache files cleared
    """
    cache_files_cleared = 0
    try:
        from development_tools.shared.fix_project_cleanup import ProjectCleanup

        cleanup = ProjectCleanup(project_root=project_root)
        # --clear-cache for audit should be scoped to development-tools caches only.
        removed, failed = cleanup.cleanup_tool_cache_artifacts(dry_run=False)
        cache_files_cleared += removed
        if failed:
            logger.warning(f"Failed to clear {failed} development-tools cache artifact(s)")
    except Exception as e:
        logger.warning(f"Fallback cache clear path activated due to error: {e}")
        # Fail-safe: clear core standardized cache files.
        dev_tools_dir = project_root / "development_tools"
        if dev_tools_dir.exists():
            for cache_file in dev_tools_dir.glob("**/jsons/.*_cache.json"):
                try:
                    cache_file.unlink()
                    cache_files_cleared += 1
                except Exception:
                    pass
            for cache_file in dev_tools_dir.glob("**/jsons/*_cache.json"):
                try:
                    cache_file.unlink()
                    cache_files_cleared += 1
                except Exception:
                    pass

    return cache_files_cleared


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Development tools command-line interface. Shorthand: use run_dev_tools.py instead of run_development_tools.py",
        add_help=True,
    )
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments passed to the command"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: auto-detect from script location)",
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default=None,
        help="Path to config file (default: use built-in config)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all development tools cache files before running the command",
    )
    return parser


def _print_available_commands() -> None:
    # User-facing help messages stay as print() for immediate visibility
    print("Available commands (grouped by tier):\n")

    for section, metadata in COMMAND_TIERS.items():
        print(f"  {section}:")
        description = metadata.get("description")
        if description:
            print(f"    {description}")
        for cmd_name in metadata.get("commands", []):
            if cmd_name in COMMAND_REGISTRY:
                cmd = COMMAND_REGISTRY[cmd_name]
                print(f"    {cmd.name:<16} {cmd.help}")
        if metadata.get("tier") == "experimental":
            print(
                "    WARNING: Experimental commands may change or fail; run only with approval."
            )
        print()

    print(
        "Use `python development_tools/run_development_tools.py <command> --help` for command-specific options."
    )
    print(
        "Use `python development_tools/run_development_tools.py help` for comprehensive help."
    )
    print()
    print(
        "Note: You can use the shorter alias `run_dev_tools.py` instead of `run_development_tools.py`"
    )


def main(argv=None) -> int:
    # Parse known args first to extract global flags
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--project-root", type=str, default=None)
    parser.add_argument("--config-path", type=str, default=None)
    parser.add_argument("--clear-cache", action="store_true")
    parser.add_argument("command", nargs="?")

    # Use parse_known_args to separate global args from command args
    if argv is None:
        argv = sys.argv[1:]

    known_args, remaining_args = parser.parse_known_args(argv)

    project_root = known_args.project_root
    config_path = known_args.config_path
    clear_cache = known_args.clear_cache
    command_name = known_args.command

    # Determine project root for cache clearing (before service initialization)
    if project_root:
        project_root_path = Path(project_root).resolve()
    else:
        # Use the same logic as service initialization
        project_root_path = Path(__file__).resolve().parent.parent

    # Clear caches if requested
    if clear_cache:
        cache_count = _clear_all_caches(project_root_path)
        if cache_count > 0:
            print(f"Cleared {cache_count} cache file(s).")
            logger.info(f"Cleared {cache_count} cache file(s) before running command")
        else:
            print("No cache files found to clear.")
            logger.debug("No cache files found to clear")

    if not command_name:
        # Build full parser for help output
        full_parser = _build_parser()
        full_parser.print_help()
        print()
        _print_available_commands()
        return 1

    commands = COMMAND_REGISTRY

    if command_name not in commands:
        logger.error(f"Unknown command: {command_name}")
        # User-facing error messages stay as print() for immediate visibility
        print(f"Unknown command: {command_name}")
        print()
        _print_available_commands()
        return 2

    try:
        service = AIToolsService(project_root=project_root, config_path=config_path)
        command = commands[command_name]
        exit_code = command.handler(service, remaining_args)
        return exit_code
    except Exception as e:
        logger.error(f"Error executing command '{command_name}': {e}", exc_info=True)
        print(f"Error executing command '{command_name}': {e}")
        return 1
    finally:
        _cleanup_transient_runtime_artifacts(project_root_path)


if __name__ == "__main__":
    sys.exit(main())
