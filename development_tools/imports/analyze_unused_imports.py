#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Unused Imports Detection

This script identifies unused imports throughout the codebase.
It categorizes findings and generates detailed reports for cleanup planning.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.

Usage:
    python imports/analyze_unused_imports.py [--output REPORT_PATH]

Integration:
    python development_tools/run_development_tools.py unused-imports
"""

import sys
import subprocess
import argparse
import json
import importlib.util
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

# Handle both relative and absolute imports
try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
    from core.logger import get_component_logger
except ImportError:
    # Fallback for when run as script
    # Add project root to path for core module imports
    project_root = Path(__file__).parent.parent.parent  # Corrected path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file
    from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Load config at module level
UNUSED_IMPORTS_CONFIG = config.get_unused_imports_config()


def _run_subprocess_with_timeout(
    cmd: list[str],
    timeout_seconds: float,
    cwd: str,
) -> subprocess.CompletedProcess[str]:
    """
    Run a subprocess with timeout, using temp files for stdout/stderr.

    Avoids Windows pipe deadlock where subprocess.run() can block indefinitely
    after killing a timed-out child (see e.g. Python issue 88693).
    """
    out_path = None
    err_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".out", encoding="utf-8"
        ) as out_f:
            out_path = out_f.name
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".err", encoding="utf-8"
        ) as err_f:
            err_path = err_f.name
        with open(out_path, "w", encoding="utf-8") as out_f:
            with open(err_path, "w", encoding="utf-8") as err_f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=out_f,
                    stderr=err_f,
                    text=True,
                    cwd=cwd,
                )
        try:
            proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise
        with open(out_path, "r", encoding="utf-8") as f:
            stdout = f.read()
        with open(err_path, "r", encoding="utf-8") as f:
            stderr = f.read()
        return subprocess.CompletedProcess(proc.args, proc.returncode, stdout, stderr)
    finally:
        for p in (out_path, err_path):
            if p:
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:
                    pass


class UnusedImportsChecker:
    """Detects and categorizes unused imports in Python files."""

    def __init__(
        self,
        project_root: str = ".",
        max_workers: int | None = None,
        use_cache: bool = True,
        verbose: bool = False,
        config_path: str | None = None,
    ):
        self.project_root = Path(project_root).resolve()

        # Load config if config_path provided
        global UNUSED_IMPORTS_CONFIG
        if config_path:
            config.load_external_config(config_path)
            UNUSED_IMPORTS_CONFIG = config.get_unused_imports_config()
        # Reload config to ensure it's up to date (project_root is handled via config file)
        UNUSED_IMPORTS_CONFIG = config.get_unused_imports_config()

        # Legacy argument retained for compatibility (not used for primary scan path).
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.verbose = verbose

        # Caching - use shared utility
        from development_tools.shared.mtime_cache import MtimeFileCache

        self.cache = MtimeFileCache(
            project_root=self.project_root,
            use_cache=use_cache,
            tool_name="analyze_unused_imports",
            domain="imports",
            tool_paths=[Path(__file__)],
        )

        # Get config values
        self.preferred_backend = UNUSED_IMPORTS_CONFIG.get(
            "preferred_backend", "ruff"
        ).lower()
        self.ruff_command = UNUSED_IMPORTS_CONFIG.get(
            "ruff_command", [sys.executable, "-m", "ruff"]
        )
        self.pylint_command = UNUSED_IMPORTS_CONFIG.get(
            "pylint_command", [sys.executable, "-m", "pylint"]
        )
        self.batch_size = max(1, int(UNUSED_IMPORTS_CONFIG.get("batch_size", 200)))
        self.pylint_batch_size = max(
            1, int(UNUSED_IMPORTS_CONFIG.get("pylint_batch_size", 25))
        )
        self.timeout_seconds = UNUSED_IMPORTS_CONFIG.get("timeout_seconds", 30)
        self.max_total_scan_seconds = max(
            60,
            int(UNUSED_IMPORTS_CONFIG.get("max_total_scan_seconds", 900)),
        )
        self.ignore_patterns = UNUSED_IMPORTS_CONFIG.get("ignore_patterns", [])
        self.type_stub_locations = UNUSED_IMPORTS_CONFIG.get("type_stub_locations", [])

        # Files to skip entirely
        # Import constants from services
        from development_tools.shared.standard_exclusions import (
            BASE_EXCLUSION_SHORTLIST,
        )

        self.skip_patterns = set(BASE_EXCLUSION_SHORTLIST)

        # Results storage
        self.findings = {
            "obvious_unused": [],
            "type_hints_only": [],
            "re_exports": [],
            "conditional_imports": [],
            "star_imports": [],
            "test_mocking": [],
            "qt_testing": [],
            "test_infrastructure": [],
            "production_test_mocking": [],
            "ui_imports": [],
        }

        self.stats = {
            "files_scanned": 0,
            "files_with_issues": 0,
            "total_unused": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "changed_files": 0,
            "cache_mode": "unknown",
            "backend": "unknown",
        }
        self.performance = {
            "backend": "unknown",
            "scan_mode": "unknown",
            "timings": {
                "discovery_seconds": 0.0,
                "detection_seconds": 0.0,
                "categorization_seconds": 0.0,
                "total_seconds": 0.0,
            },
            "files_per_second": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "changed_files": 0,
            "batch_size": self.batch_size,
            "fallback_used": False,
            "fallback_reason": "",
        }
        self._file_context_cache: dict[Path, tuple[list[str], str]] = {}
        self._scan_start: float = 0.0

    def _check_scan_deadline(self) -> None:
        """Raise TimeoutError if total scan time exceeds max_total_scan_seconds."""
        if self._scan_start <= 0:
            return
        elapsed = time.perf_counter() - self._scan_start
        if elapsed > self.max_total_scan_seconds:
            raise TimeoutError(
                f"analyze_unused_imports exceeded max total scan time "
                f"({self.max_total_scan_seconds}s) after {elapsed:.0f}s. "
                "Increase unused_imports.max_total_scan_seconds in config or run with cache warm."
            )

    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        # Convert to relative path
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path).replace("\\", "/")
        except ValueError:
            return False

        # Skip patterns
        for pattern in self.skip_patterns:
            if pattern in rel_path_str:
                return False

        # Use standard exclusions (development context, no tool type)
        if should_exclude_file(rel_path_str, tool_type=None, context="development"):
            return False

        # Must be Python file
        if file_path.suffix != ".py":
            return False

        # Must exist and be readable
        return not (not file_path.exists() or not file_path.is_file())

    def find_python_files(self) -> list[Path]:
        """Find all Python files to scan."""
        python_files = []

        # Full scan
        for file_path in self.project_root.rglob("*.py"):
            if self.should_scan_file(file_path):
                python_files.append(file_path)

        return sorted(python_files)

    def _command_exists(self, command: list[str]) -> bool:
        """Return True when the command executable is available."""
        if not command:
            return False
        resolved = self._resolve_python_command(command)
        if len(resolved) >= 3 and resolved[1] == "-m":
            module_name = resolved[2]
            # Fast in-process check first.
            if importlib.util.find_spec(module_name) is None:
                return False
            # Verify the exact command/interpreter pair can execute.
            try:
                probe = resolved + ["--version"]
                result = _run_subprocess_with_timeout(
                    probe,
                    timeout_seconds=5,
                    cwd=str(self.project_root),
                )
                return result.returncode == 0
            except Exception:
                return False
        first = resolved[0]
        if Path(first).exists():
            return True
        return shutil.which(first) is not None

    def _resolve_python_command(self, command: list[str]) -> list[str]:
        """Normalize Python launcher commands to the current interpreter."""
        if not command:
            return command
        first = str(command[0]).lower()
        if first in {"python", "python3", "py"}:
            return [sys.executable] + command[1:]
        return command

    def _detect_backend(self) -> str:
        """Pick backend, preferring ruff and falling back to pylint."""
        if self.preferred_backend == "pylint":
            return "pylint"
        if self._command_exists(self.ruff_command):
            return "ruff"
        return "pylint"

    def _chunk_files(self, files: list[Path], chunk_size: int | None = None) -> list[list[Path]]:
        """Split files into stable chunks for batched backend calls."""
        size = chunk_size or self.batch_size
        return [files[i : i + size] for i in range(0, len(files), size)]

    def _normalize_pylint_issue(self, issue: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize pylint issue to unused-import issue payload."""
        message_id = issue.get("message-id")
        if message_id != "W0611":
            return None
        return {
            "message-id": "W0611",
            "message": issue.get("message", ""),
            "line": issue.get("line", 0),
            "column": issue.get("column", 0),
            "symbol": issue.get("symbol", "unused-import"),
        }

    def _normalize_ruff_issue(self, issue: dict[str, Any]) -> tuple[Path, dict[str, Any]] | None:
        """Normalize ruff issue to per-file unused-import payload."""
        if not isinstance(issue, dict):
            return None
        if issue.get("code") != "F401":
            return None
        filename = issue.get("filename")
        if not filename:
            return None
        issue_path = Path(filename)
        if not issue_path.is_absolute():
            issue_path = (self.project_root / issue_path).resolve()
        location = issue.get("location", {}) if isinstance(issue.get("location"), dict) else {}
        normalized = {
            "message-id": "W0611",
            "message": issue.get("message", ""),
            "line": int(location.get("row", 0) or 0),
            "column": int(location.get("column", 0) or 0),
            "symbol": "unused-import",
        }
        return (issue_path, normalized)

    def _run_batched_ruff(self, files: list[Path]) -> dict[Path, list[dict[str, Any]]]:
        """Run ruff in file batches and return issues keyed by file path."""
        issues_by_file: dict[Path, list[dict[str, Any]]] = {fp: [] for fp in files}
        chunks = self._chunk_files(files, chunk_size=self.batch_size)
        for batch_idx, batch in enumerate(chunks):
            self._check_scan_deadline()
            if logger:
                logger.debug(
                    f"analyze_unused_imports: ruff batch {batch_idx + 1}/{len(chunks)} "
                    f"({len(batch)} files)"
                )
            cmd = self._resolve_python_command(self.ruff_command) + [
                "check",
                "--select",
                "F401",
                "--output-format",
                "json",
            ] + [str(fp) for fp in batch]

            result = _run_subprocess_with_timeout(
                cmd,
                timeout_seconds=self.timeout_seconds,
                cwd=str(self.project_root),
            )
            if result.returncode not in (0, 1):
                raise RuntimeError(
                    f"ruff execution failed (rc={result.returncode}): {result.stderr.strip()}"
                )
            stdout = result.stdout.strip() if result.stdout else ""
            if not stdout and result.returncode == 0:
                continue
            if not stdout and result.returncode != 0:
                raise RuntimeError(
                    f"ruff produced no JSON output (rc={result.returncode}): {result.stderr.strip()}"
                )
            parsed = json.loads(stdout)
            if not isinstance(parsed, list):
                raise RuntimeError("ruff output JSON is not a list")
            for raw_issue in parsed:
                normalized = self._normalize_ruff_issue(raw_issue)
                if not normalized:
                    continue
                issue_path, issue_payload = normalized
                if issue_path not in issues_by_file:
                    continue
                issues_by_file[issue_path].append(issue_payload)
        return issues_by_file

    def _run_batched_pylint(self, files: list[Path]) -> dict[Path, list[dict[str, Any]]]:
        """Run pylint in file batches and return issues keyed by file path."""
        issues_by_file: dict[Path, list[dict[str, Any]]] = {fp: [] for fp in files}
        chunks = self._chunk_files(files, chunk_size=self.pylint_batch_size)
        for batch_idx, batch in enumerate(chunks):
            self._check_scan_deadline()
            if logger:
                logger.debug(
                    f"analyze_unused_imports: pylint batch {batch_idx + 1}/{len(chunks)} "
                    f"({len(batch)} files)"
                )
            cmd = self._resolve_python_command(self.pylint_command) + [
                "--disable=all",
                "--enable=unused-import",
                "--output-format=json",
            ] + [str(fp) for fp in batch]
            # Pylint cost grows with batch size; avoid false timeouts on fallback path.
            timeout_seconds = max(
                self.timeout_seconds,
                int(self.timeout_seconds * max(1.0, len(batch) / 8.0)),
            )

            result = _run_subprocess_with_timeout(
                cmd,
                timeout_seconds=timeout_seconds,
                cwd=str(self.project_root),
            )

            stdout = (result.stdout or "").strip()
            if not stdout and result.returncode == 0:
                continue
            if not stdout and result.returncode != 0:
                raise RuntimeError(
                    f"pylint produced no JSON output (rc={result.returncode}): {(result.stderr or '').strip()}"
                )
            parsed = json.loads(stdout)
            if not isinstance(parsed, list):
                raise RuntimeError("pylint output JSON is not a list")
            for raw_issue in parsed:
                if not isinstance(raw_issue, dict):
                    continue
                issue_file = raw_issue.get("path")
                if not issue_file:
                    continue
                issue_path = Path(issue_file)
                if not issue_path.is_absolute():
                    issue_path = (self.project_root / issue_path).resolve()
                if issue_path not in issues_by_file:
                    continue
                normalized = self._normalize_pylint_issue(raw_issue)
                if normalized:
                    issues_by_file[issue_path].append(normalized)
        return issues_by_file

    def _run_detection_backend(
        self, files: list[Path]
    ) -> tuple[str, dict[Path, list[dict[str, Any]]], bool, str]:
        """Run detection backend with ruff-first fallback semantics."""
        backend = self._detect_backend()
        fallback_used = False
        fallback_reason = ""
        if not files:
            return backend, {}, False, ""
        if backend == "ruff":
            try:
                return "ruff", self._run_batched_ruff(files), False, ""
            except Exception as exc:
                fallback_used = True
                fallback_reason = f"ruff failed: {exc}"
                if logger:
                    logger.warning(
                        f"Ruff backend failed ({exc}); falling back to pylint batched scan."
                    )
                try:
                    return (
                        "pylint",
                        self._run_batched_pylint(files),
                        fallback_used,
                        fallback_reason,
                    )
                except Exception as pylint_exc:
                    raise RuntimeError(
                        f"unused-import detection backend failed: {fallback_reason}; "
                        f"pylint failed: {pylint_exc}"
                    ) from pylint_exc
        try:
            return "pylint", self._run_batched_pylint(files), fallback_used, fallback_reason
        except Exception as exc:
            raise RuntimeError(f"unused-import detection backend failed: pylint failed: {exc}") from exc

    def run_pylint_on_file(self, file_path: Path) -> list[dict] | None:
        """Run pylint on a single file to detect unused imports."""
        # Check cache first
        cached = self.cache.get_cached(file_path)
        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached  # cached is already a list (possibly empty)

        self.stats["cache_misses"] += 1

        try:
            # Run pylint with only unused-import enabled, JSON output
            cmd = self.pylint_command + [
                "--disable=all",
                "--enable=unused-import",
                "--output-format=json",
                str(file_path),
            ]

            result = _run_subprocess_with_timeout(
                cmd,
                timeout_seconds=self.timeout_seconds,
                cwd=str(self.project_root),
            )

            # Pylint returns non-zero if it finds issues, which is what we want
            issues = None
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                except json.JSONDecodeError:
                    if logger:
                        logger.warning(f"Could not parse pylint output for {file_path}")
                    return None
            else:
                issues = []

            # Cache results
            self.cache.cache_results(file_path, issues if issues else [])
            return issues

        except subprocess.TimeoutExpired:
            if logger:
                logger.warning(f"Pylint timeout on {file_path}")
            return None
        except Exception as e:
            if logger:
                logger.error(f"Error running pylint on {file_path}: {e}")
            return None

    def categorize_unused_import(self, file_path: Path, issue: dict) -> str:
        """Categorize an unused import based on context."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            str(rel_path).replace("\\", "/")
        except ValueError:
            str(file_path)

        # Extract import name from the message
        message = issue.get("message", "")
        import_name = self._extract_import_name_from_message(message)

        # Check if it's in an __init__.py file
        if file_path.name == "__init__.py":
            return "re_exports"

        # Read the file to get context (cached per file for this run)
        try:
            lines, file_content = self._get_file_context(file_path)

            line_num = issue.get("line", 1) - 1  # Convert to 0-based
            if line_num < 0 or line_num >= len(lines):
                return "obvious_unused"

            # Get the import line and surrounding context
            import_line = lines[line_num].strip()

            # Check for test mocking requirements
            if self._is_test_mocking_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(
                        f"Test mocking import detected: {import_name} in {file_path}"
                    )
                return "test_mocking"

            # Check for Qt testing requirements
            if self._is_qt_testing_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(
                        f"Qt testing import detected: {import_name} in {file_path}"
                    )
                return "qt_testing"

            # Check for pytest fixture imports
            if self._is_pytest_fixture_import(
                file_path, import_name, import_line, file_content
            ):
                if logger:
                    logger.debug(
                        f"Pytest fixture import detected: {import_name} in {file_path}"
                    )
                return "test_infrastructure"

            # Check for test infrastructure imports
            if self._is_test_infrastructure_import(
                file_path, import_name, file_content
            ):
                if logger:
                    logger.debug(
                        f"Test infrastructure import detected: {import_name} in {file_path}"
                    )
                return "test_infrastructure"

            # Check for production code test mocking requirements
            if self._is_production_test_mocking_import(
                file_path, import_name, file_content
            ):
                if logger:
                    logger.debug(
                        f"Production test mocking import detected: {import_name} in {file_path}"
                    )
                return "production_test_mocking"

            # Check for UI imports
            if self._is_ui_import(file_path, import_name, file_content):
                if logger:
                    logger.debug(f"UI import detected: {import_name} in {file_path}")
                return "ui_imports"

            # Check for conditional import (in try/except or if block)
            # Look backwards for try/except or if statements
            indent_level = len(lines[line_num]) - len(lines[line_num].lstrip())
            for i in range(max(0, line_num - 10), line_num):
                prev_line = lines[i].strip()
                prev_indent = len(lines[i]) - len(lines[i].lstrip())
                if prev_indent < indent_level and (
                    prev_line.startswith("try:")
                    or prev_line.startswith("if ")
                    or prev_line.startswith("except")
                ):
                    return "conditional_imports"

            # Check for star imports
            if "import *" in import_line:
                return "star_imports"

            # Check if used only in type hints
            # Look for TYPE_CHECKING or if the import appears in comments/strings
            if "TYPE_CHECKING" in file_content and import_name:
                # Check if import is only used in type hint context
                # This is a heuristic - look for the name in type annotations
                type_hint_patterns = [
                    f": {import_name}",
                    f"-> {import_name}",
                    f"List[{import_name}",
                    f"Dict[{import_name}",
                    f"Optional[{import_name}",
                    f"Union[{import_name}",
                ]
                if any(pattern in file_content for pattern in type_hint_patterns):
                    return "type_hints_only"

            # Check for type hint imports that are commonly unused
            type_hint_imports = [
                "Optional",
                "List",
                "Dict",
                "Any",
                "Tuple",
                "Set",
                "Union",
                "Callable",
            ]
            if import_name in type_hint_imports:
                # Check if used in type annotations
                type_annotation_patterns = [
                    f": {import_name}",
                    f"-> {import_name}",
                    f"List[{import_name}",
                    f"Dict[{import_name}",
                    f"Optional[{import_name}",
                    f"Union[{import_name}",
                    f"Tuple[{import_name}",
                    f"Set[{import_name}",
                    f"Callable[{import_name}",
                ]
                if any(pattern in file_content for pattern in type_annotation_patterns):
                    return "type_hints_only"

            return "obvious_unused"

        except Exception as e:
            if logger:
                logger.warning(f"Error categorizing import in {file_path}: {e}")
            return "obvious_unused"

    def _get_file_context(self, file_path: Path) -> tuple[list[str], str]:
        """Load and cache file lines/content for categorization phase."""
        cached = self._file_context_cache.get(file_path)
        if cached is not None:
            return cached
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
        content = "".join(lines)
        payload = (lines, content)
        self._file_context_cache[file_path] = payload
        return payload

    def _extract_import_name_from_message(self, message: str) -> str:
        """Extract the import symbol from pylint/ruff unused-import messages."""
        # Examples:
        # "Unused import os" -> "os"
        # "Unused Optional imported from typing" -> "Optional"
        # "Unused List imported from typing" -> "List"
        # "Unused datetime imported from datetime" -> "datetime"
        # "`typing.Optional` imported but unused" -> "Optional"
        # "`unittest.mock.Mock` imported but unused" -> "Mock"
        # "`.audit_orchestration._AUDIT_LOCK_FILE` imported but unused" -> "_AUDIT_LOCK_FILE"

        if not message:
            return ""

        # Ruff F401 format: backtick-wrapped import path.
        backtick_match = re.search(r"`([^`]+)`\s+imported but unused", message)
        if backtick_match:
            raw_name = backtick_match.group(1).strip()
            if raw_name.startswith("."):
                raw_name = raw_name[1:]
            if not raw_name:
                return ""
            return raw_name.split(".")[-1]

        if not message.startswith("Unused "):
            return ""

        # Remove "Unused " prefix
        remaining = message[7:]  # len("Unused ") = 7

        # Handle "import X" pattern
        if remaining.startswith("import "):
            return remaining[7:]  # len("import ") = 7

        # Handle "X imported from Y" pattern
        if " imported from " in remaining:
            return remaining.split(" imported from ")[0]

        return remaining

    def _is_test_mocking_import(
        self, file_path: Path, import_name: str, file_content: str
    ) -> bool:
        """Check if import is required for test mocking."""
        # Check if it's a test file
        file_path_str = str(file_path)
        if not ("test" in file_path_str or "tests/" in file_path_str):
            return False

        # Check for unittest.mock imports
        mock_imports = ["Mock", "MagicMock", "patch", "mock_open"]
        if import_name in mock_imports:
            # Check if used in @patch decorators or patch.object calls
            if (
                "@patch" in file_content
                or "patch.object" in file_content
                or "with patch" in file_content
            ):
                if self.verbose:
                    print(
                        f"DEBUG: Test mocking pattern found for {import_name} in {file_path_str}"
                    )
                return True

            # For test files, assume mock imports are needed even without explicit usage
            # as they might be used in ways not easily detected by static analysis
            if self.verbose:
                print(
                    f"DEBUG: Test mocking import assumed needed for {import_name} in {file_path_str}"
                )
            return True

        # Check for production functions that are commonly mocked in tests
        production_mock_functions = [
            "get_user_data",
            "save_user_data",
            "get_user_categories",
            "create_user_files",
            "get_user_file_path",
            "is_valid_email",
            "is_valid_phone",
            "update_user_account",
            "update_user_schedules",
            "update_channel_preferences",
            "get_schedule_time_periods",
            "set_schedule_periods",
            "set_schedule_days",
            "create_new_user",
            "ensure_user_directory",
            "load_default_messages",
            "update_user_context",
            "get_user_id_by_identifier",
            "_create_next_recurring_task_instance",
            "determine_file_path",
            "get_available_channels",
            "get_channel_class_mapping",
            "validate_schedule_periods__validate_time_format",
            "ProjectError",
            "DataError",
            "FileOperationError",  # Add error handling imports (example - customize for your project)
        ]

        if import_name in production_mock_functions:
            # Check if there are @patch decorators that might mock this function
            patch_patterns = [
                "@patch(",
                "patch.object(",
                "with patch(",
                "patch(",
            ]
            if any(pattern in file_content for pattern in patch_patterns):
                if self.verbose:
                    print(
                        f"DEBUG: Production function mocking pattern found for {import_name} in {file_path_str}"
                    )
                return True

            # For test files, assume production functions are needed for mocking
            # even without explicit @patch decorators
            if self.verbose:
                print(
                    f"DEBUG: Production function mocking assumed needed for {import_name} in {file_path_str}"
                )
            return True

        return False

    def _is_qt_testing_import(
        self, file_path: Path, import_name: str, file_content: str
    ) -> bool:
        """Check if import is required for Qt testing."""
        # Check if it's a test file
        file_path_str = str(file_path)
        if not ("test" in file_path_str or "tests/" in file_path_str):
            return False

        # Check for Qt imports
        qt_imports = [
            "QWidget",
            "QMessageBox",
            "QDialog",
            "Qt",
            "QTimer",
            "QTest",
            "QApplication",
            "QLineEdit",
            "QScrollArea",
            "Signal",
            "QFont",
            "QColor",
            "QPalette",
            "QPainter",
            "QPen",
            "QBrush",
            "QVBoxLayout",
            "QHBoxLayout",
            "QLabel",
            "QTextEdit",
            "QPushButton",
            "QComboBox",
            "QTabWidget",
            "QFrame",
            "QThread",
            "QListWidgetItem",
            "QInputDialog",
            "QTableWidgetItem",
        ]

        if import_name in qt_imports:
            # Check if used in Qt testing patterns
            qt_test_patterns = [
                "QTest.",
                "QApplication.",
                "QApplication.processEvents",
                "QTest.keyClicks",
                "QTest.mouseClick",
                "Signal(",
                "QWidget(",
                "QMessageBox(",
                "QDialog(",
                "QTimer(",
                "QApplication(",
            ]
            if any(pattern in file_content for pattern in qt_test_patterns):
                if self.verbose:
                    print(
                        f"DEBUG: Qt testing pattern found for {import_name} in {file_path_str}"
                    )
                return True

        return False

    def _is_ui_import(
        self, file_path: Path, import_name: str, file_content: str
    ) -> bool:
        """Check if import is required for UI files (not test files)."""
        # Normalize path separators to forward slashes for consistent checking
        try:
            rel_path = file_path.relative_to(self.project_root)
            file_path_str = str(rel_path).replace("\\", "/")
        except ValueError:
            # If not relative to project root, use absolute path
            file_path_str = str(file_path).replace("\\", "/")

        # Check if it's a UI file (not test file)
        if "test" in file_path_str.lower() or "tests/" in file_path_str.lower():
            return False

        # Check if it's in ui/ directory (normalized path separator)
        if "ui/" not in file_path_str.lower():
            return False

        # Check for Qt imports
        qt_imports = [
            "QWidget",
            "QMessageBox",
            "QDialog",
            "Qt",
            "QTimer",
            "QApplication",
            "QLineEdit",
            "QScrollArea",
            "Signal",
            "QFont",
            "QColor",
            "QPalette",
            "QPainter",
            "QPen",
            "QBrush",
            "QVBoxLayout",
            "QHBoxLayout",
            "QLabel",
            "QTextEdit",
            "QPushButton",
            "QComboBox",
            "QTabWidget",
            "QFrame",
            "QThread",
            "QListWidgetItem",
            "QInputDialog",
            "QTableWidgetItem",
        ]

        if import_name in qt_imports:
            # For UI files, assume Qt imports are needed even if not explicitly used
            # as they might be used in ways not easily detected by static analysis
            if logger:
                logger.debug(f"UI import detected: {import_name} in {file_path_str}")
            return True

        return False

    def _is_pytest_fixture_import(
        self, file_path: Path, import_name: str, import_line: str, file_content: str
    ) -> bool:
        """Check if import is a pytest fixture imported from conftest."""
        # Check if it's a test file
        file_path_str = str(file_path)
        if not ("test" in file_path_str or "tests/" in file_path_str):
            return False

        # Check if import is from conftest
        if "conftest" not in import_line:
            return False

        # Common pytest fixture names (can be extended)
        common_fixture_names = [
            "demo_project_root",
            "test_config_path",
            "temp_project_copy",
            "load_development_tools_module",
            "test_user",
            "test_user_id",
            "test_data_dir",
            "temp_dir",
            "mock_bot",
            "mock_channel",
            "isolation_manager",
            "test_factory",
            "test_data_factory",
            "test_user_factory",
            "test_user_data_factory",
        ]

        # Check if it's a known fixture name
        if import_name in common_fixture_names:
            # Check if used as function parameter (pytest fixture pattern)
            # Look for function definitions with this name as a parameter
            # Pattern: def test_something(self, fixture_name, ...) or def test_something(fixture_name, ...)
            fixture_param_pattern = re.compile(
                r"def\s+\w+\([^)]*\b" + re.escape(import_name) + r"\b[^)]*\)",
                re.MULTILINE,
            )
            if fixture_param_pattern.search(file_content):
                if self.verbose:
                    print(
                        f"DEBUG: Pytest fixture pattern found for {import_name} in {file_path_str}"
                    )
                return True

        # Also check if the import line explicitly imports from conftest
        # and the name is used as a parameter anywhere in the file
        if "conftest" in import_line:
            # Look for any function parameter usage
            # More flexible pattern: any function with this as a parameter
            any_param_pattern = re.compile(
                r"def\s+\w+\([^)]*\b" + re.escape(import_name) + r"\b[^)]*\)",
                re.MULTILINE,
            )
            if any_param_pattern.search(file_content):
                if self.verbose:
                    print(
                        f"DEBUG: Conftest import used as parameter for {import_name} in {file_path_str}"
                    )
                return True

        return False

    def _is_test_infrastructure_import(
        self, file_path: Path, import_name: str, file_content: str
    ) -> bool:
        """Check if import is required for test infrastructure."""
        # Check if it's a test file
        if not ("test" in str(file_path) or "tests/" in str(file_path)):
            return False

        # Check for test infrastructure imports
        test_infrastructure_imports = [
            "pytest",
            "tempfile",
            "shutil",
            "json",
            "datetime",
            "time",
            "threading",
            "os",
            "Path",
        ]

        if import_name in test_infrastructure_imports:
            # Check if used in test patterns
            test_patterns = [
                "@pytest.",
                "pytest.",
                "tempfile.",
                "shutil.",
                "json.",
                "datetime.",
                "time.",
                "threading.",
                "os.",
                "TestUserFactory",
                "TestDataFactory",
                "TestUserDataFactory",
                "IsolationManager",
            ]
            if any(pattern in file_content for pattern in test_patterns):
                if self.verbose:
                    print(
                        f"DEBUG: Test infrastructure pattern found for {import_name} in {file_path}"
                    )
                return True

        # Check for test factory imports
        test_factory_patterns = [
            "TestDataFactory",
            "TestUserDataFactory",
            "TestUserFactory",
        ]
        if import_name in test_factory_patterns:
            if self.verbose:
                print(
                    f"DEBUG: Test factory pattern found for {import_name} in {file_path}"
                )
            return True

        # Check for UI widget imports in test files
        ui_widget_patterns = [
            "CategorySelectionWidget",
            "ChannelSelectionWidget",
            "TaskSettingsWidget",
            "CheckinSettingsWidget",
            "TaskEditDialog",
            "TaskCrudDialog",
            "TaskCompletionDialog",
            "open_schedule_editor",
        ]
        if import_name in ui_widget_patterns:
            if self.verbose:
                print(
                    f"DEBUG: UI widget pattern found for {import_name} in {file_path}"
                )
            return True

        return False

    def _is_production_test_mocking_import(
        self, file_path: Path, import_name: str, file_content: str
    ) -> bool:
        """Check if import is required for production code test mocking."""
        # Check if it's production code (not in tests/)
        if "tests/" in str(file_path) or "test" in str(file_path):
            return False

        # Check for imports that are commonly mocked in tests
        production_mock_imports = [
            "determine_file_path",
            "get_available_channels",
            "get_channel_class_mapping",
            "get_user_data",
            "save_user_data",
            "create_user_files",
            "get_user_file_path",
            "is_valid_email",
            "is_valid_phone",
            "validate_schedule_periods__validate_time_format",
            "update_user_account",
            "update_user_schedules",
            "update_channel_preferences",
            "get_schedule_time_periods",
            "set_schedule_periods",
            "set_schedule_days",
            "create_new_user",
            "ensure_user_directory",
            "load_default_messages",
            "get_user_categories",
            "update_user_context",
            "get_user_id_by_identifier",
            "_create_next_recurring_task_instance",
            "os",  # Add os to the list
        ]

        if import_name in production_mock_imports:
            # Check if there are comments indicating test mocking requirements
            if (
                "test mocking" in file_content.lower()
                or "needed for test" in file_content.lower()
            ):
                if self.verbose:
                    print(
                        f"DEBUG: Production test mocking comment found for {import_name} in {file_path}"
                    )
                return True

            # Check if there are test files that might mock this function
            # This is a heuristic - if the function name suggests it's commonly mocked
            if any(
                keyword in import_name.lower()
                for keyword in ["get_", "save_", "create_", "update_", "validate_"]
            ):
                if self.verbose:
                    print(
                        f"DEBUG: Production test mocking heuristic found for {import_name} in {file_path}"
                    )
                return True

            # Special case for 'os' - check if there's a comment about test mocking
            if import_name == "os" and (
                "test mocking" in file_content.lower()
                or "needed for test" in file_content.lower()
            ):
                if self.verbose:
                    print(
                        f"DEBUG: Production test mocking os comment found in {file_path}"
                    )
                return True

        return False

    def scan_codebase(self) -> dict:
        """Scan the entire codebase for unused imports."""
        self._file_context_cache = {}
        start_total = time.perf_counter()
        if logger:
            logger.debug(
                f"Starting unused imports scan (cache: {self.use_cache}, preferred backend: {self.preferred_backend})..."
            )

        self._scan_start = time.perf_counter()
        start_discovery = time.perf_counter()
        python_files = self.find_python_files()
        discovery_seconds = time.perf_counter() - start_discovery

        self.stats["files_scanned"] = len(python_files)
        total_files = len(python_files)

        print(f"Scanning {total_files} Python files for unused imports...")
        print(f"Using cache: {self.use_cache}, preferred backend: {self.preferred_backend}")
        print("")

        files_to_scan: list[Path] = []
        issues_by_file: dict[Path, list[dict[str, Any]]] = {}
        for file_path in python_files:
            cached = self.cache.get_cached(file_path)
            if cached is not None:
                self.stats["cache_hits"] += 1
                issues_by_file[file_path] = cached if isinstance(cached, list) else []
            else:
                self.stats["cache_misses"] += 1
                files_to_scan.append(file_path)

        self.stats["changed_files"] = len(files_to_scan)
        if not self.use_cache:
            self.stats["cache_mode"] = "disabled"
        elif self.stats["cache_hits"] > 0 and self.stats["cache_misses"] == 0:
            self.stats["cache_mode"] = "cache_only"
        elif self.stats["cache_hits"] > 0 and self.stats["cache_misses"] > 0:
            self.stats["cache_mode"] = "partial_cache"
        else:
            self.stats["cache_mode"] = "cold_scan"

        start_detection = time.perf_counter()
        backend_used = self._detect_backend()
        fallback_used = False
        fallback_reason = ""
        if files_to_scan:
            print(
                f"Processing {len(files_to_scan)} changed file(s) (cached: {self.stats['cache_hits']})..."
            )
            try:
                backend_used, detected, fallback_used, fallback_reason = self._run_detection_backend(
                    files_to_scan
                )
            except Exception as exc:
                self.cache.mark_run_result(success=False, error=str(exc))
                self.cache.save_cache()
                raise
            for file_path in files_to_scan:
                file_issues = detected.get(file_path, [])
                issues_by_file[file_path] = file_issues
                self.cache.cache_results(file_path, file_issues)
        detection_seconds = time.perf_counter() - start_detection

        start_categorization = time.perf_counter()
        for file_path in python_files:
            if not file_path.exists():
                continue
            issues = issues_by_file.get(file_path) or []
            if not issues:
                continue

            try:
                rel_path = file_path.relative_to(self.project_root)
                rel_path_str = str(rel_path).replace("\\", "/")
            except ValueError:
                rel_path_str = str(file_path)

            file_issue_count = 0
            for issue in issues:
                if issue.get("message-id") != "W0611":
                    continue
                category = self.categorize_unused_import(file_path, issue)
                self.findings[category].append(
                    {
                        "file": rel_path_str,
                        "line": issue.get("line", 0),
                        "column": issue.get("column", 0),
                        "message": issue.get("message", ""),
                        "symbol": issue.get("symbol", ""),
                    }
                )
                self.stats["total_unused"] += 1
                file_issue_count += 1

            if file_issue_count > 0:
                self.stats["files_with_issues"] += 1
        categorization_seconds = time.perf_counter() - start_categorization

        if files_to_scan:
            self.cache.mark_run_result(success=True)
        self.cache.save_cache()

        total_seconds = time.perf_counter() - start_total
        files_per_second = (
            round(total_files / total_seconds, 2) if total_seconds > 0 else 0.0
        )
        self.stats["backend"] = backend_used

        self.performance = {
            "backend": backend_used,
            "scan_mode": self.stats["cache_mode"],
            "timings": {
                "discovery_seconds": round(discovery_seconds, 4),
                "detection_seconds": round(detection_seconds, 4),
                "categorization_seconds": round(categorization_seconds, 4),
                "total_seconds": round(total_seconds, 4),
            },
            "files_per_second": files_per_second,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "changed_files": self.stats["changed_files"],
            "batch_size": self.batch_size,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }

        print("")
        if logger:
            logger.debug(
                f"Scan complete. Found {self.stats['total_unused']} unused imports in "
                f"{self.stats['files_with_issues']} files "
                f"(backend={backend_used}, mode={self.stats['cache_mode']}, files/sec={files_per_second})."
            )

        return {"findings": self.findings, "stats": self.stats, "performance": self.performance}

    def get_summary_data(self) -> dict:
        """Get summary data for integration with AI tools."""
        return {
            "files_scanned": self.stats["files_scanned"],
            "files_with_issues": self.stats["files_with_issues"],
            "total_unused": self.stats["total_unused"],
            "backend": self.stats.get("backend", "unknown"),
            "cache_mode": self.stats.get("cache_mode", "unknown"),
            "by_category": {
                category: len(items) for category, items in self.findings.items()
            },
            "status": self._determine_status(),
        }

    def _determine_status(self) -> str:
        """Determine overall status based on findings."""
        if self.stats["total_unused"] == 0:
            return "GOOD"
        elif self.stats["total_unused"] < 20:
            return "NEEDS ATTENTION"
        else:
            return "CRITICAL"

    def run_analysis(self) -> dict[str, Any]:
        """
        Run unused imports analysis and return results in standard format.

        Returns:
            Dictionary with standard format: 'summary', 'files', and 'details' keys
        """
        # Ensure scan has been run
        if self.stats.get("files_scanned", 0) == 0:
            self.scan_codebase()

        # Build files dict from findings
        files = {}
        for _category, items in self.findings.items():
            for item in items:
                file_path = item.get("file", "")
                if file_path:
                    if file_path not in files:
                        files[file_path] = 0
                    files[file_path] += 1

        # Return standard format with full findings for report generation
        return {
            "summary": {
                "total_issues": self.stats["total_unused"],
                "files_affected": self.stats["files_with_issues"],
                "status": self._determine_status(),
            },
            "files": files,
            "details": {
                "findings": self.findings,  # Full findings for detailed reports
                "stats": self.stats,  # Full stats for report generation
                "performance": self.performance,
                "by_category": {
                    category: len(items) for category, items in self.findings.items()
                },
                "files_scanned": self.stats["files_scanned"],
            },
        }


def execute(
    project_root: str | None = None, config_path: str | None = None, **kwargs
) -> dict:
    """Execute unused imports check (for use by run_development_tools)."""
    if project_root:
        root_path = Path(project_root).resolve()
    else:
        # Script is at: development_tools/imports/analyze_unused_imports.py
        # So we need to go up 2 levels to get to project root
        root_path = Path(__file__).parent.parent.parent

    checker = UnusedImportsChecker(
        str(root_path), config_path=config_path, verbose=kwargs.get("verbose", False)
    )
    results = checker.scan_codebase()

    # Return analysis results only (report generation is now separate)
    return {"results": results, "stats": checker.stats}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect unused imports in codebase")
    parser.add_argument(
        "--json", action="store_true", help="Output JSON data to stdout"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show DEBUG messages during scanning",
    )
    args = parser.parse_args()

    # Determine project root
    project_root = Path(__file__).parent.parent.parent

    # Run the check
    checker = UnusedImportsChecker(str(project_root), verbose=args.verbose)
    checker.scan_codebase()

    # Output JSON if --json flag is provided
    if args.json:
        # Output JSON in standard format for integration
        standard_results = checker.run_analysis()
        print(json.dumps(standard_results, indent=2))
    else:
        # Print summary if not in JSON mode
        print(f"\nFiles scanned: {checker.stats['files_scanned']}")
        print(f"Files with issues: {checker.stats['files_with_issues']}")
        print(f"Total unused imports: {checker.stats['total_unused']}")
        print("\nNote: To generate a detailed report, run:")
        print(
            "  python development_tools/run_development_tools.py unused-imports-report"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
