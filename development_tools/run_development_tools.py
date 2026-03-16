#!/usr/bin/env python3
# TOOL_TIER: core

"""Command-line interface for AI development tools."""

import argparse
import os
import shutil
import signal
import sys
import time
from pathlib import Path

# Add project root to path FIRST - this allows development_tools to be imported as a package
project_root = Path(__file__).resolve().parent.parent
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Force explicit dev-tools logging mode before importing the logger module.
# This prevents leaked test env vars (e.g., MHM_TESTING=1) from routing
# development-tools logs into test-coverage log directories.
os.environ["MHM_DEV_TOOLS_RUN"] = "1"
os.environ["MHM_TESTING"] = "0"

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
from development_tools.shared.lock_state import cleanup_lock_paths, evaluate_lock_set
from development_tools.shared import audit_signal_state
import contextlib

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
                    with contextlib.suppress(Exception):
                        child.chmod(0o700)
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

    # Use config-driven tests data directory instead of hardcoded tests/data
    try:
        from development_tools import config

        paths_cfg = config.get_paths_config()
        tests_data_rel = paths_cfg.get("tests_data_dir") or "tests/data"
    except Exception:
        tests_data_rel = "tests/data"

    data_dir = project_root / tests_data_rel
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

    protected_test_data_dirs = {
        "tmp",
        "tmp_pytest_runtime",
        "pytest_runner",
    }

    for item in data_dir.iterdir():
        try:
            if item.is_dir():
                if item.name in protected_test_data_dirs:
                    continue
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


def _get_audit_related_lock_paths(project_root: Path) -> list[Path]:
    """Return audit/coverage lock file paths anchored at project root."""
    audit_lock_name = ".audit_in_progress.lock"
    coverage_lock_name = ".coverage_in_progress.lock"
    try:
        from development_tools import config

        audit_lock_name = str(
            config.get_external_value("paths.audit_lock_file", audit_lock_name)
        )
        coverage_lock_name = str(
            config.get_external_value("paths.coverage_lock_file", coverage_lock_name)
        )
    except Exception:
        pass

    coverage_lock_path = project_root / Path(coverage_lock_name)
    return [
        project_root / Path(audit_lock_name),
        coverage_lock_path,
        coverage_lock_path.parent / Path(".coverage_dev_tools_in_progress.lock"),
    ]


def _cleanup_audit_related_locks(project_root: Path) -> int:
    """Best-effort removal of audit/coverage lock files."""
    return cleanup_lock_paths(_get_audit_related_lock_paths(project_root))


def _preflight_handle_stale_audit_locks(project_root: Path) -> tuple[bool, int]:
    """Cleanup stale/malformed audit locks and report active-lock blocking state."""
    lock_states = evaluate_lock_set(_get_audit_related_lock_paths(project_root))
    cleanup_targets = [
        entry["path"]
        for entry in (lock_states["stale"] + lock_states["malformed"])
        if isinstance(entry.get("path"), Path)
    ]
    removed = cleanup_lock_paths(cleanup_targets) if cleanup_targets else 0
    has_active = len(lock_states["active"]) > 0
    if has_active:
        lock_list = ", ".join(
            str(entry["path"])
            for entry in lock_states["active"]
            if isinstance(entry.get("path"), Path)
        )
        logger.error(
            "Audit blocked: active audit/coverage lock file(s) present: "
            f"{lock_list}"
        )
        print(
            "Audit blocked: active audit/coverage lock file(s) present: "
            f"{lock_list}"
        )
    return has_active, removed


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
        "--cache-clear",
        dest="clear_cache",
        action="store_true",
        help="Clear all development tools cache files before running the command (alias: --cache-clear)",
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
    parser.add_argument("--clear-cache", "--cache-clear", dest="clear_cache", action="store_true")
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

    service = None
    try:
        if command_name in {"audit", "full-audit"}:
            has_active_locks, removed = _preflight_handle_stale_audit_locks(
                project_root_path
            )
            if removed > 0:
                logger.warning(
                    f"Removed {removed} stale/malformed audit lock file(s) in preflight"
                )
                print(
                    f"Removed {removed} stale/malformed audit lock file(s) before audit."
                )
            if has_active_locks:
                return 1
        service = AIToolsService(project_root=project_root, config_path=config_path)
        command = commands[command_name]
        # Align with run_tests.py: first SIGINT ignored, second within 2s stops
        if command_name in {"audit", "full-audit"}:
            audit_signal_state.reset_audit_sigint_state()
            if hasattr(signal, "SIGINT"):
                signal.signal(signal.SIGINT, audit_signal_state.handle_audit_sigint)
        exit_code = command.handler(service, remaining_args)
        # If user pressed second Ctrl+C (stop audit), treat as failure even if handler returned 0
        if command_name in {"audit", "full-audit"} and exit_code == 0 and audit_signal_state.audit_sigint_requested():
            logger.warning("Audit completed but user had requested stop (second Ctrl+C); returning failure.")
            return 1
        return exit_code
    except KeyboardInterrupt:
        internal_flag = (
            getattr(service, "_internal_interrupt_detected", False)
            if service is not None
            else False
        )
        internal_interrupt = isinstance(internal_flag, bool) and internal_flag
        if command_name in {"audit", "full-audit"}:
            removed = _cleanup_audit_related_locks(project_root_path)
            if removed > 0:
                logger.warning(
                    f"Interrupted audit; cleaned up {removed} audit/coverage lock file(s)"
                )
                print(
                    f"Interrupted audit; cleaned up {removed} audit/coverage lock file(s)."
                )
        if internal_interrupt or audit_signal_state.audit_sigint_requested():
            if internal_interrupt:
                logger.error(
                    "Execution hit KeyboardInterrupt after internal interrupt signature "
                    "was already detected; returning failure state instead of user-interrupt exit."
                )
                print(
                    "WARNING: Internal interrupt signature was detected earlier in this run. "
                    "Treating this as tool failure (exit code 1), not direct user interrupt."
                )
            return 1
        logger.warning(
            "Execution interrupted by KeyboardInterrupt (SIGINT/console control event). "
            "This is not always a direct user Ctrl+C and can originate from host/terminal signal propagation."
        )
        print(
            "Execution interrupted by KeyboardInterrupt (SIGINT/console control event). "
            "This may come from terminal/host signal propagation, not only direct Ctrl+C."
        )
        return 130
    except Exception as e:
        logger.error(f"Error executing command '{command_name}': {e}", exc_info=True)
        print(f"Error executing command '{command_name}': {e}")
        return 1
    finally:
        _cleanup_transient_runtime_artifacts(project_root_path)


if __name__ == "__main__":
    sys.exit(main())
