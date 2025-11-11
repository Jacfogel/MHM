#!/usr/bin/env python3
"""Command-line interface for AI development tools."""

import argparse
import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add ai_development_tools to path for relative imports when run as script
ai_tools_path = Path(__file__).parent
if str(ai_tools_path) not in sys.path:
    sys.path.insert(0, str(ai_tools_path))

# Handle both relative and absolute imports
try:
    from .services.operations import (
        AIToolsService,
        COMMAND_REGISTRY,
    )
    from .services.common import COMMAND_CATEGORIES
except ImportError:
    # Fallback for when run as script
    from ai_development_tools.services.operations import (
        AIToolsService,
        COMMAND_REGISTRY,
    )
    from ai_development_tools.services.common import COMMAND_CATEGORIES

from core.logger import get_component_logger

logger = get_component_logger("ai_development_tools")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI development tools command-line interface.",
        add_help=True,
    )
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments passed to the command')
    return parser


def _print_available_commands() -> None:
    # User-facing help messages stay as print() for immediate visibility
    print("Available commands:\n")

    for category, commands in COMMAND_CATEGORIES.items():
        print(f"  {category}:")
        for cmd_name in commands:
            if cmd_name in COMMAND_REGISTRY:
                cmd = COMMAND_REGISTRY[cmd_name]
                print(f"    {cmd.name:<16} {cmd.help}")
        print()
    
    print("Use `python ai_development_tools/ai_tools_runner.py <command> --help` for command-specific options.")
    print("Use `python ai_development_tools/ai_tools_runner.py help` for comprehensive help.")



def main(argv=None) -> int:
    parser = _build_parser()
    parsed = parser.parse_args(argv)

    if not parsed.command:
        parser.print_help()
        print()
        _print_available_commands()
        return 1

    command_name = parsed.command
    commands = COMMAND_REGISTRY

    if command_name not in commands:
        logger.error(f"Unknown command: {command_name}")
        # User-facing error messages stay as print() for immediate visibility
        print(f"Unknown command: {command_name}")
        print()
        _print_available_commands()
        return 2

    service = AIToolsService()
    command = commands[command_name]
    exit_code = command.handler(service, parsed.args)
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
