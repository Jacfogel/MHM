#!/usr/bin/env python3
"""Command-line interface for AI development tools."""

import argparse
import sys

from .services.operations import (
    AIToolsService,
    COMMAND_REGISTRY,
)
from .services.common import COMMAND_CATEGORIES


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI development tools command-line interface.",
        add_help=True,
    )
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments passed to the command')
    return parser


def _print_available_commands() -> None:
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
