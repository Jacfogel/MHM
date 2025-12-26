#!/usr/bin/env python3
# TOOL_TIER: core

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
    parser.add_argument('command', nargs='?')
    
    # Use parse_known_args to separate global args from command args
    if argv is None:
        argv = sys.argv[1:]
    
    known_args, remaining_args = parser.parse_known_args(argv)
    
    project_root = known_args.project_root
    config_path = known_args.config_path
    command_name = known_args.command

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
