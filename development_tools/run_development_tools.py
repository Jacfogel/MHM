#!/usr/bin/env python3
# TOOL_TIER: core

# NOTE: This file was modified to test domain-aware coverage cache merging.

"""Command-line interface for AI development tools."""

import argparse
import sys
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


def _clear_all_caches(project_root: Path) -> int:
    """
    Clear all development tools cache files.

    Includes:
    - Standardized storage cache files: development_tools/{domain}/jsons/.{tool}_cache.json
    - Test-file-based coverage cache: development_tools/tests/jsons/test_file_coverage_cache.json
    - Dev tools coverage cache: development_tools/tests/jsons/dev_tools_coverage_cache.json

    Args:
        project_root: Project root directory

    Returns:
        Number of cache files cleared
    """
    cache_files_cleared = 0
    dev_tools_dir = project_root / "development_tools"

    # Find all cache files in standardized storage: development_tools/{domain}/jsons/.{tool}_cache.json
    if dev_tools_dir.exists():
        for domain_dir in dev_tools_dir.iterdir():
            if domain_dir.is_dir():
                jsons_dir = domain_dir / "jsons"
                if jsons_dir.exists():
                    for cache_file in jsons_dir.glob(".*_cache.json"):
                        try:
                            cache_file.unlink()
                            cache_files_cleared += 1
                            logger.debug(f"Cleared cache file: {cache_file}")
                        except Exception as e:
                            logger.warning(f"Failed to clear cache file {cache_file}: {e}")

    # Clear test-file-based coverage cache (now in jsons/ directory)
    jsons_dir = dev_tools_dir / "tests" / "jsons"
    if jsons_dir.exists():
        # New test-file-based cache
        test_file_cache_file = jsons_dir / "test_file_coverage_cache.json"
        if test_file_cache_file.exists():
            try:
                test_file_cache_file.unlink()
                cache_files_cleared += 1
                logger.debug(f"Cleared test-file-based coverage cache: {test_file_cache_file}")
            except Exception as e:
                logger.warning(f"Failed to clear test-file-based coverage cache {test_file_cache_file}: {e}")

        # Dev tools coverage cache
        dev_tools_cache_file = jsons_dir / "dev_tools_coverage_cache.json"
        if dev_tools_cache_file.exists():
            try:
                dev_tools_cache_file.unlink()
                cache_files_cleared += 1
                logger.debug(f"Cleared dev tools coverage cache: {dev_tools_cache_file}")
            except Exception as e:
                logger.warning(f"Failed to clear dev tools coverage cache {dev_tools_cache_file}: {e}")

    return cache_files_cleared


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Development tools command-line interface. Shorthand: use run_dev_tools.py instead of run_development_tools.py",
        add_help=True,
    )
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments passed to the command')
    parser.add_argument(
        '--project-root',
        type=str,
        default=None,
        help='Project root directory (default: auto-detect from script location)'
    )
    parser.add_argument(
        '--config-path',
        type=str,
        default=None,
        help='Path to config file (default: use built-in config)'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear all development tools cache files before running the command'
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
            print("    WARNING: Experimental commands may change or fail; run only with approval.")
        print()
    
    print("Use `python development_tools/run_development_tools.py <command> --help` for command-specific options.")
    print("Use `python development_tools/run_development_tools.py help` for comprehensive help.")
    print()
    print("Note: You can use the shorter alias `run_dev_tools.py` instead of `run_development_tools.py`")



def main(argv=None) -> int:
    # Parse known args first to extract global flags
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--project-root', type=str, default=None)
    parser.add_argument('--config-path', type=str, default=None)
    parser.add_argument('--clear-cache', action='store_true')
    parser.add_argument('command', nargs='?')
    
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


if __name__ == '__main__':
    sys.exit(main())
