"""
CLI interface for development tools.

Contains command handlers and COMMAND_REGISTRY for the command-line interface.
"""

import argparse
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Sequence

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import AIToolsService type for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .service.core import AIToolsService


@dataclass(frozen=True)
class CommandRegistration:
    """Command registration dataclass for CLI interface."""

    name: str
    handler: Callable[["AIToolsService", Sequence[str]], int]
    help: str
    description: str = ""


def _print_command_help(parser: argparse.ArgumentParser) -> None:
    """Print command help."""
    parser.print_help()
    print()


def _audit_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="audit", add_help=False)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run comprehensive audit (Tier 3 - includes coverage and dependencies).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick audit (Tier 1 - core metrics only).",
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis."
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools in analysis.",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include tests and dev tools (equivalent to --include-tests --include-dev-tools).",
    )
    parser.add_argument(
        "--overlap",
        action="store_true",
        help="Include overlap analysis in documentation analysis (section overlaps and consolidation recommendations).",
    )

    if any(arg in ("-h", "--help") for arg in argv):
        _print_command_help(parser)
        return 0

    ns = parser.parse_args(list(argv))

    # Determine audit tier based on flags
    quick_mode = ns.quick
    full_mode = ns.full

    # Set exclusion configuration
    service.set_exclusion_config(
        include_tests=ns.include_tests or ns.include_all,
        include_dev_tools=ns.include_dev_tools or ns.include_all,
    )

    success = service.run_audit(
        quick=quick_mode, full=full_mode, include_overlap=ns.overlap
    )
    return 0 if success else 1


def _docs_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'docs' command does not accept additional arguments.")
            return 2
        print("Usage: docs")
        return 0

    success = service.run_docs()
    return 0 if success else 1


def _validate_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'validate' command does not accept additional arguments.")
            return 2
        print("Usage: validate")
        return 0

    success = service.run_validate()
    return 0 if success else 1


def _config_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'config' command does not accept additional arguments.")
            return 2
        print("Usage: config")
        return 0

    success = service.run_config()
    return 0 if success else 1


def _workflow_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="workflow", add_help=False)
    parser.add_argument("task_type", help="Workflow task to execute")

    if any(arg in ("-h", "--help") for arg in argv):
        _print_command_help(parser)
        return 0

    if not argv:
        print("Usage: workflow <task_type>")
        return 2

    ns = parser.parse_args(list(argv))
    success = service.run_workflow(ns.task_type)
    return 0 if success else 1


def _decision_support_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print(
                "The 'decision-support' command does not accept additional arguments."
            )
            return 2
        print("Usage: decision-support")
        return 0

    result = service.run_decision_support()
    return (
        0
        if (isinstance(result, dict) and result.get("success", False)) or result
        else 1
    )


def _fix_version_sync_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="version-sync", add_help=False)
    parser.add_argument(
        "scope",
        nargs="?",
        default="docs",
        help="Scope to sync (docs, core, ai_docs, all).",
    )

    if any(arg in ("-h", "--help") for arg in argv):
        _print_command_help(parser)
        return 0

    ns = parser.parse_args(list(argv))
    success = service.run_version_sync(ns.scope)
    return 0 if success else 1


def _status_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'status' command does not accept additional arguments.")
            return 2
        print("Usage: status")
        return 0

    # run_status() doesn't return a value, it just generates status files
    # It logs errors but doesn't raise exceptions, so we consider it always successful
    try:
        service.run_status()
        return 0
    except Exception as e:
        logger.error(f"Status command failed: {e}", exc_info=True)
        return 1


def _system_signals_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle system-signals command"""
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'system-signals' command does not accept additional arguments.")
            return 2
        print("Usage: system-signals")
        return 0

    success = service.run_analyze_system_signals()
    return 0 if success else 1


def _doc_sync_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'doc-sync' command does not accept additional arguments.")
            return 2
        print("Usage: doc-sync")
        return 0

    success = service.run_documentation_sync()
    return 0 if success else 1


def _doc_fix_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle doc-fix command with options for different fix types."""
    parser = argparse.ArgumentParser(description="Fix documentation issues")
    parser.add_argument(
        "--add-addresses",
        action="store_true",
        help="Add file addresses to documentation files",
    )
    parser.add_argument(
        "--fix-ascii",
        action="store_true",
        help="Fix non-ASCII characters in documentation",
    )
    parser.add_argument(
        "--number-headings",
        action="store_true",
        help="Number H2 and H3 headings in documentation",
    )
    parser.add_argument(
        "--convert-links",
        action="store_true",
        help="Convert file paths to markdown links",
    )
    parser.add_argument("--all", action="store_true", help="Apply all fix operations")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    # Determine fix type
    fix_types = []
    if args.add_addresses:
        fix_types.append("add-addresses")
    if args.fix_ascii:
        fix_types.append("fix-ascii")
    if args.number_headings:
        fix_types.append("number-headings")
    if args.convert_links:
        fix_types.append("convert-links")

    if args.all:
        fix_type = "all"
    elif len(fix_types) == 1:
        fix_type = fix_types[0]
    elif len(fix_types) > 1:
        print("Error: Can only specify one fix type at a time (or use --all)")
        return 2
    else:
        # Default to all if nothing specified
        fix_type = "all"

    success = service.run_documentation_fix(fix_type=fix_type, dry_run=args.dry_run)
    return 0 if success else 1


def _coverage_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'coverage' command does not accept additional arguments.")
            return 2
        print("Usage: coverage")
        return 0

    success = service.run_coverage_regeneration()
    return 0 if success else 1


def _legacy_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'legacy' command does not accept additional arguments.")
            return 2
        print("Usage: legacy")
        return 0

    success = service.run_legacy_cleanup()
    return 0 if success else 1


def _unused_imports_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle unused-imports command (analysis only)."""
    if argv:
        if "-h" in argv or "--help" in argv:
            print("Usage: unused-imports")
            return 0

        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'unused-imports' command does not accept additional arguments.")
            print("Usage: unused-imports")
            return 2

    result = service.run_unused_imports()
    success = result.get("success", False) if isinstance(result, dict) else bool(result)
    return 0 if success else 1


def _unused_imports_report_command(
    service: "AIToolsService", argv: Sequence[str]
) -> int:
    """Handle unused-imports-report command (report generation)."""
    if argv:
        if "-h" in argv or "--help" in argv:
            print("Usage: unused-imports-report")
            return 0

        if any(arg not in ("-h", "--help") for arg in argv):
            print(
                "The 'unused-imports-report' command does not accept additional arguments."
            )
            print("Usage: unused-imports-report")
            return 2

    result = service.run_unused_imports_report()
    success = result.get("success", False) if isinstance(result, dict) else bool(result)
    return 0 if success else 1


def _cleanup_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle cleanup command."""
    parser = argparse.ArgumentParser(prog="cleanup", add_help=False)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Clean everything including tool caches (default: only __pycache__ and temp test files)",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Clean cache directories (__pycache__, .pytest_cache) and standardized storage cache files",
    )
    parser.add_argument(
        "--test-data", action="store_true", help="Clean test data directories"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Clean coverage files, logs, and test-file-based coverage cache",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )

    if "-h" in argv or "--help" in argv:
        print(
            "Usage: cleanup [--full] [--cache] [--test-data] [--coverage] [--dry-run]"
        )
        print(
            "  --full       Clean everything including tool caches (default: only __pycache__ and temp test files)"
        )
        print(
            "  --cache      Clean cache directories (__pycache__, .pytest_cache) and standardized storage cache files"
        )
        print("  --test-data  Clean test data directories")
        print(
            "  --coverage   Clean coverage files, logs, and test-file-based coverage cache"
        )
        print("  --dry-run    Show what would be removed without making changes")
        print()
        print(
            "Default behavior (no flags): Clean __pycache__ directories and temp test files only"
        )
        print("Use --full to clean everything including tool caches")
        return 0

    try:
        args, unknown = parser.parse_known_args(argv)
        if unknown:
            print(f"Unknown arguments: {unknown}")
            print(
                "Usage: cleanup [--full] [--cache] [--test-data] [--coverage] [--dry-run]"
            )
            return 2
    except SystemExit:
        return 2

    # If --full is specified, clean everything
    if args.full:
        cache = True
        test_data = True
        coverage = True
    else:
        # Default: only clean __pycache__ and temp test files (light cleanup)
        # If no flags specified, default to minimal cleanup (cache + test_data only)
        if not any([args.cache, args.test_data, args.coverage]):
            cache = True  # Clean __pycache__ directories
            test_data = True  # Clean temp test files
            coverage = False  # Don't clean coverage or tool caches by default
        else:
            # Use explicit flags if provided
            cache = args.cache
            test_data = args.test_data
            coverage = args.coverage

    result = service.run_cleanup(
        cache=cache,
        test_data=test_data,
        reports=False,
        all=False,  # Don't use --all flag, we handle it via --full
        coverage=coverage,
        full=args.full,
        dry_run=args.dry_run,
    )

    if result.get("success"):
        data = result.get("data", {})
        total_removed = data.get("total_removed", 0)
        total_failed = data.get("total_failed", 0)
        if args.dry_run:
            logger.info(f"DRY RUN: Would remove {total_removed} items")
        else:
            logger.info(
                f"Cleanup completed: {total_removed} items removed, {total_failed} failed"
            )
        return 0 if total_failed == 0 else 1
    else:
        logger.error(f"Cleanup failed: {result.get('error', 'Unknown error')}")
        return 1


def _export_code_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """
    Export Python files into a single Markdown snapshot.

    Note: this command does not require AIToolsService; we accept it to conform
    to the CommandRegistration signature.
    """
    # Delegate parsing + behavior to the tool module
    from development_tools.shared.export_code_snapshot import main

    # main() expects argv excluding the command name (same as we receive here)
    return int(main(list(argv)))


def _trees_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    if argv:
        if any(arg not in ("-h", "--help") for arg in argv):
            print("The 'trees' command does not accept additional arguments.")
            return 2
        print("Usage: trees")
        return 0

    success = service.generate_directory_trees()
    return 0 if success else 1


def _show_help_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    service.show_help()
    return 0


COMMAND_REGISTRY = OrderedDict(
    [
        (
            "audit",
            CommandRegistration(
                "audit",
                _audit_command,
                "Run audit (Tier 2 - standard). Use --quick for Tier 1, --full for Tier 3.",
            ),
        ),
        (
            "docs",
            CommandRegistration(
                "docs", _docs_command, "Regenerate documentation artifacts."
            ),
        ),
        (
            "validate",
            CommandRegistration(
                "validate", _validate_command, "Validate AI-generated work."
            ),
        ),
        (
            "config",
            CommandRegistration(
                "config", _config_command, "Check configuration consistency."
            ),
        ),
        (
            "workflow",
            CommandRegistration(
                "workflow", _workflow_command, "Execute an audit-first workflow task."
            ),
        ),
        (
            "decision-support",
            CommandRegistration(
                "decision-support",
                _decision_support_command,
                "Generate decision support insights.",
            ),
        ),
        (
            "version-sync",
            CommandRegistration(
                "version-sync",
                _fix_version_sync_command,
                "Synchronize version metadata.",
            ),
        ),
        (
            "status",
            CommandRegistration(
                "status", _status_command, "Print quick system status."
            ),
        ),
        (
            "system-signals",
            CommandRegistration(
                "system-signals",
                _system_signals_command,
                "Generate system health and status signals.",
            ),
        ),
        (
            "doc-sync",
            CommandRegistration(
                "doc-sync", _doc_sync_command, "Check documentation synchronisation."
            ),
        ),
        (
            "doc-fix",
            CommandRegistration(
                "doc-fix",
                _doc_fix_command,
                "Fix documentation issues (addresses, ASCII, headings, links).",
            ),
        ),
        (
            "coverage",
            CommandRegistration(
                "coverage", _coverage_command, "Regenerate coverage metrics."
            ),
        ),
        (
            "legacy",
            CommandRegistration(
                "legacy", _legacy_command, "Scan for legacy references."
            ),
        ),
        (
            "unused-imports",
            CommandRegistration(
                "unused-imports",
                _unused_imports_command,
                "Detect unused imports in codebase (analysis only).",
            ),
        ),
        (
            "unused-imports-report",
            CommandRegistration(
                "unused-imports-report",
                _unused_imports_report_command,
                "Generate unused imports report from analysis results.",
            ),
        ),
        (
            "cleanup",
            CommandRegistration(
                "cleanup",
                _cleanup_command,
                "Clean up project cache and temporary files.",
            ),
        ),
        (
            "export-code",
            CommandRegistration(
                "export-code",
                _export_code_command,
                "Export Python files into a single Markdown snapshot (LLM-friendly).",
            ),
        ),
        (
            "trees",
            CommandRegistration(
                "trees", _trees_command, "Generate directory tree reports."
            ),
        ),
        (
            "help",
            CommandRegistration(
                "help", _show_help_command, "Show detailed help information."
            ),
        ),
    ]
)


def list_commands() -> Sequence[CommandRegistration]:
    """List all registered commands."""
    return tuple(COMMAND_REGISTRY.values())
