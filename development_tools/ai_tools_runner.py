#!/usr/bin/env python3
# TOOL_TIER: core

"""Command-line interface for AI development tools."""

import argparse
import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add development_tools to path for relative imports when run as script
ai_tools_path = Path(__file__).parent
if str(ai_tools_path) not in sys.path:
    sys.path.insert(0, str(ai_tools_path))

# Handle both relative and absolute imports
try:
    from .shared.operations import (
        AIToolsService,
        COMMAND_REGISTRY,
    )
    from .shared.common import COMMAND_TIERS
except ImportError:
    # Fallback for when run as script
    from development_tools.shared.operations import (
        AIToolsService,
        COMMAND_REGISTRY,
    )
    from development_tools.shared.common import COMMAND_TIERS

from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI development tools command-line interface.",
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
    
    print("Use `python development_tools/ai_tools_runner.py <command> --help` for command-specific options.")
    print("Use `python development_tools/ai_tools_runner.py help` for comprehensive help.")



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
