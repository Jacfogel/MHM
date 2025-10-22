#!/usr/bin/env python3
"""Command-line interface for AI development tools."""

import argparse
import sys

from .services.operations import (
    AIToolsService,
    COMMAND_REGISTRY,
    list_commands,
)


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
    for entry in list_commands():
        print(f"  {entry.name:<14} {entry.help}")
    print("\nUse `python ai_development_tools/ai_tools_runner.py <command> --help` for command-specific options.")



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
