#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
fix_project_cleanup.py
Project cleanup tool to remove cache files, temporary directories, and unnecessary artifacts.

Follows the fix_* naming convention for cleanup/repair operations.

This tool removes:
- Python cache directories (__pycache__)
- pytest cache (.pytest_cache)
- Coverage files (.coverage)
- Old coverage regeneration logs
- Temporary test directories
- Test user data directories
- Other generated/cache files

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import os
import shutil
import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from .. import config
except ImportError:
    from development_tools import config

from core.logger import get_component_logger

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class ProjectCleanup:
    """Clean up project cache files, temporary directories, and artifacts."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(config.get_project_root())

    def find_directories(self, pattern: str) -> list[Path]:
        """Find all directories matching a pattern."""
        directories = []
        for root, dirs, _files in os.walk(self.project_root):
            # Skip certain directories from being searched
            dirs[:] = [
                d for d in dirs if d not in [".git", "venv", ".venv", "node_modules"]
            ]

            for dir_name in dirs:
                if pattern in dir_name:
                    dir_path = Path(root) / dir_name
                    directories.append(dir_path)

        return directories

    def find_files(self, pattern: str) -> list[Path]:
        """Find all files matching a pattern."""
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            # Skip certain directories from being searched
            dirs[:] = [
                d for d in dirs if d not in [".git", "venv", ".venv", "node_modules"]
            ]

            for filename in filenames:
                if pattern in filename:
                    file_path = Path(root) / filename
                    files.append(file_path)

        return files

    def get_size(self, path: Path) -> str:
        """Get human-readable size of file or directory."""
        try:
            if path.is_file():
                size = path.stat().st_size
            elif path.is_dir():
                size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            else:
                return "0 B"

            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except Exception:
            return "unknown size"

    def remove_path(self, path: Path, dry_run: bool = False) -> tuple[bool, str]:
        """Remove a file or directory."""
        try:
            if not path.exists():
                return False, f"Does not exist: {path}"

            if dry_run:
                size = self.get_size(path)
                return True, f"Would remove: {path} ({size})"

            if path.is_file():
                path.unlink()
                return True, f"Removed file: {path}"
            elif path.is_dir():
                shutil.rmtree(path)
                return True, f"Removed directory: {path}"
            else:
                return False, f"Unknown type: {path}"
        except PermissionError as e:
            return False, f"Permission denied: {path} - {e}"
        except Exception as e:
            return False, f"Error removing {path}: {e}"

    def cleanup_cache_directories(
        self, dry_run: bool = False, include_tool_caches: bool = False
    ) -> tuple[int, int]:
        """
        Remove __pycache__ directories.

        Args:
            dry_run: If True, show what would be removed without actually removing
            include_tool_caches: If True, also clean standardized storage cache files
        """
        directories = self.find_directories("__pycache__")
        removed = 0
        failed = 0

        for dir_path in directories:
            success, message = self.remove_path(dir_path, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        # Only clean standardized/tool cache files if explicitly requested.
        if include_tool_caches:
            tool_removed, tool_failed = self.cleanup_tool_cache_artifacts(dry_run=dry_run)
            removed += tool_removed
            failed += tool_failed

        return removed, failed

    def cleanup_tool_cache_artifacts(
        self, dry_run: bool = False, cache_scope: str | None = None
    ) -> tuple[int, int]:
        """Remove development-tools cache/result artifacts used for audit cache reuse.

        ``cache_scope``:
            - ``None`` (default): remove **all** known tool cache layouts (full + dev_tools
              scopes, archives, legacy aggregates, coverage JSON, dot caches). Used by
              interactive ``cleanup`` / tests expecting a full reset.
            - ``full``: only full-repo audit artifacts (``scopes/full``, main
              ``coverage.json``, archives, legacy paths, flat dot caches) - leaves
              ``scopes/dev_tools`` and ``coverage_dev_tools.json`` intact.
            - ``dev_tools``: only dev-tools-scoped audit artifacts - leaves full-repo
              scope caches intact.

        Includes flat and scoped layouts per scope; see ``audit_storage_scope`` module.
        """
        removed = 0
        failed = 0
        for cache_file in self._iter_tool_cache_artifacts(cache_scope=cache_scope):
            success, message = self.remove_path(cache_file, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")
        return removed, failed

    def _iter_tool_cache_artifacts(
        self, cache_scope: str | None = None
    ) -> list[Path]:
        """Return cache/artifact files used for cache-style reuse."""
        if cache_scope == "dev_tools":
            return self._iter_dev_tools_only_tool_cache_artifacts()
        if cache_scope == "full":
            return self._iter_full_repo_only_tool_cache_artifacts()
        return self._iter_all_tool_cache_artifacts()

    def _dedupe_artifact_paths(self, artifacts: list[Path]) -> list[Path]:
        unique: list[Path] = []
        seen: set[str] = set()
        for artifact in artifacts:
            if not artifact.is_file():
                continue
            normalized = str(artifact.resolve()).lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(artifact)
        return unique

    def _iter_dev_tools_only_tool_cache_artifacts(self) -> list[Path]:
        """Scoped cache files for ``audit --full --dev-tools-only`` reuse only."""
        artifacts: list[Path] = []
        dev_tools_dir = self.project_root / "development_tools"
        if not dev_tools_dir.exists():
            return artifacts
        for cache_file in dev_tools_dir.glob("**/jsons/scopes/dev_tools/**/*"):
            if cache_file.is_file():
                artifacts.append(cache_file)
        reports_scoped_dev = dev_tools_dir / "reports" / "scopes" / "dev_tools"
        if reports_scoped_dev.is_dir():
            for scoped_report in reports_scoped_dev.rglob("*"):
                if scoped_report.is_file():
                    artifacts.append(scoped_report)
        tests_jsons = dev_tools_dir / "tests" / "jsons"
        if tests_jsons.exists():
            for name in (
                "coverage_dev_tools.json",
                "generate_dev_tools_coverage_results.json",
            ):
                p = tests_jsons / name
                if p.is_file():
                    artifacts.append(p)
        return self._dedupe_artifact_paths(artifacts)

    def _iter_full_repo_only_tool_cache_artifacts(self) -> list[Path]:
        """Scoped cache files for default full-repo audits (not dev_tools scope tree)."""
        all_paths = self._iter_all_tool_cache_artifacts()
        dev_only = {
            str(p.resolve()).lower()
            for p in self._iter_dev_tools_only_tool_cache_artifacts()
        }
        return [
            p
            for p in all_paths
            if str(p.resolve()).lower() not in dev_only
        ]

    def _iter_all_tool_cache_artifacts(self) -> list[Path]:
        """Return every known tool cache file (full + dev_tools + shared)."""
        artifacts: list[Path] = []
        dev_tools_dir = self.project_root / "development_tools"
        if not dev_tools_dir.exists():
            return artifacts
        # Canonical tool list: derive cache and result files from central metadata.
        try:
            from development_tools.shared.tool_metadata import iter_tools

            for tool_info in iter_tools():
                path_parts = tool_info.path.replace("\\", "/").split("/")
                # Expected form: development_tools/<domain>/<tool>.py
                if len(path_parts) < 3 or path_parts[0] != "development_tools":
                    continue
                domain = path_parts[1]
                jsons_dir = dev_tools_dir / domain / "jsons"
                if not jsons_dir.exists():
                    continue
                artifacts.append(jsons_dir / f".{tool_info.name}_cache.json")

                # Result payloads are also used as freshness inputs for some domains.
                if domain in {"docs", "tests"}:
                    artifacts.append(jsons_dir / f"{tool_info.name}_results.json")
        except Exception:
            # Fall back to generic globbing if metadata is unavailable.
            pass

        # Generic discovery catches current and future cache files (including unregistered tools).
        for cache_file in dev_tools_dir.glob("**/jsons/.*_cache.json"):
            if cache_file.is_file():
                artifacts.append(cache_file)
        for cache_file in dev_tools_dir.glob("**/jsons/*_cache.json"):
            if cache_file.is_file():
                artifacts.append(cache_file)

        # Dev-tools-only audit scope (per-tool results/caches under .../jsons/scopes/dev_tools/).
        for cache_file in dev_tools_dir.glob("**/jsons/scopes/dev_tools/**/*"):
            if cache_file.is_file():
                artifacts.append(cache_file)
        reports_scoped_dev = dev_tools_dir / "reports" / "scopes" / "dev_tools"
        if reports_scoped_dev.is_dir():
            for scoped_report in reports_scoped_dev.rglob("*"):
                if scoped_report.is_file():
                    artifacts.append(scoped_report)

        # Full-repo audit scope (default Tier 2/3 layout): per-domain .../jsons/scopes/full/** and
        # aggregated JSON under development_tools/reports/scopes/full/** (see audit_storage_scope).
        for cache_file in dev_tools_dir.glob("**/jsons/scopes/full/**/*"):
            if cache_file.is_file():
                artifacts.append(cache_file)
        reports_scoped_full = dev_tools_dir / "reports" / "scopes" / "full"
        if reports_scoped_full.is_dir():
            for scoped_report in reports_scoped_full.rglob("*"):
                if scoped_report.is_file():
                    artifacts.append(scoped_report)

        # Rotated markdown snapshots (AI_STATUS / AI_PRIORITIES / CONSOLIDATED) from prior runs.
        reports_archive = dev_tools_dir / "reports" / "archive"
        if reports_archive.is_dir():
            for archived in reports_archive.rglob("*"):
                if archived.is_file():
                    artifacts.append(archived)

        # Orphan pre-scopes aggregates (safe to delete if present; loaders use reports/scopes/**).
        legacy_analysis = dev_tools_dir / "reports" / "analysis_detailed_results.json"
        if legacy_analysis.is_file():
            artifacts.append(legacy_analysis)
        legacy_timings = dev_tools_dir / "reports" / "jsons" / "tool_timings.json"
        if legacy_timings.is_file():
            artifacts.append(legacy_timings)

        # Coverage JSON artifacts used as warm-run inputs.
        tests_jsons = dev_tools_dir / "tests" / "jsons"
        if tests_jsons.exists():
            for file_path in tests_jsons.glob("coverage*.json"):
                if file_path.is_file():
                    artifacts.append(file_path)
            for file_path in tests_jsons.glob("run_test_coverage*_results.json"):
                if file_path.is_file():
                    artifacts.append(file_path)

        return self._dedupe_artifact_paths(artifacts)

    def cleanup_pytest_cache(self, dry_run: bool = False) -> tuple[int, int]:
        """Remove .pytest_cache directories."""
        directories = self.find_directories(".pytest_cache")
        removed = 0
        failed = 0

        for dir_path in directories:
            success, message = self.remove_path(dir_path, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        return removed, failed

    def cleanup_coverage_files(self, dry_run: bool = False) -> tuple[int, int]:
        """Remove .coverage files and coverage cache files."""
        files = self.find_files(".coverage")
        removed = 0
        failed = 0

        for file_path in files:
            success, message = self.remove_path(file_path, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        # Clean up test-file-based coverage cache (now in jsons/ directory)
        jsons_dir = self.project_root / "development_tools" / "tests" / "jsons"
        if jsons_dir.exists():
            # New test-file-based cache
            test_file_cache_file = jsons_dir / "test_file_coverage_cache.json"
            if test_file_cache_file.exists():
                success, message = self.remove_path(test_file_cache_file, dry_run)
                if success:
                    removed += 1
                    if not dry_run:
                        logger.info(f"  {message}")
                else:
                    failed += 1
                    if not dry_run:
                        logger.warning(f"  {message}")

            # Dev tools coverage cache
            dev_tools_cache_file = jsons_dir / "dev_tools_coverage_cache.json"
            if dev_tools_cache_file.exists():
                success, message = self.remove_path(dev_tools_cache_file, dry_run)
                if success:
                    removed += 1
                    if not dry_run:
                        logger.info(f"  {message}")
                else:
                    failed += 1
                    if not dry_run:
                        logger.warning(f"  {message}")

        return removed, failed

    def cleanup_coverage_logs(self, dry_run: bool = False) -> tuple[int, int]:
        """Remove old coverage regeneration log files, keeping only the 2 most recent per type."""
        coverage_logs_dir = (
            self.project_root / "development_tools" / "logs" / "coverage_regeneration"
        )
        removed = 0
        failed = 0

        if not coverage_logs_dir.exists():
            return removed, failed

        # Get all log files (excluding .latest.log files which should always be kept)
        log_files = [
            f
            for f in coverage_logs_dir.glob("*.log")
            if not f.name.endswith(".latest.log")
        ]

        # Group by base name (e.g., pytest_stdout, coverage_html)
        log_groups = {}
        for log_file in log_files:
            base_name = log_file.stem
            # Remove timestamp patterns - try multiple formats
            if "_" in base_name:
                parts = base_name.rsplit("_", 2)
                # Check if last parts look like timestamps
                if len(parts) >= 2:
                    # Pattern might be: name_20251103_010734
                    if len(parts[-1]) == 6 and len(parts[-2]) == 8:
                        base_name = "_".join(parts[:-2])
                    elif "-" in parts[-1]:
                        # Pattern: name_20251103-010734
                        base_name = "_".join(parts[:-1])
            if "-" in base_name:
                # Pattern: name-20251103-010734
                parts = base_name.rsplit("-", 2)
                if len(parts) >= 2 and len(parts[-1]) == 6 and len(parts[-2]) == 8:
                    base_name = parts[0]

            if base_name not in log_groups:
                log_groups[base_name] = []
            log_groups[base_name].append(log_file)

        for _base_name, files in log_groups.items():
            if len(files) <= 2:
                continue  # Keep all if we have 2 or fewer

            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            # Keep only the 2 most recent, remove the rest
            files_to_remove = files[2:]

            for file_path in files_to_remove:
                success, message = self.remove_path(file_path, dry_run)
                if success:
                    removed += 1
                    if not dry_run:
                        logger.info(f"  {message}")
                else:
                    failed += 1
                    if not dry_run:
                        logger.warning(f"  {message}")

        return removed, failed

    def cleanup_test_temp_dirs(self, dry_run: bool = False) -> tuple[int, int]:
        """Remove temporary test directories."""
        try:
            from development_tools import config as _config

            paths_cfg = _config.get_paths_config()
            tests_data_rel = paths_cfg.get("tests_data_dir") or "tests/data"
        except Exception:
            tests_data_rel = "tests/data"

        test_data_dir = self.project_root / tests_data_rel
        removed = 0
        failed = 0

        if not test_data_dir.exists():
            return removed, failed

        # Remove pytest-of-* directories (created by pytest's tmpdir plugin)
        pytest_of_dirs = list(test_data_dir.glob("pytest-of-*"))
        for dir_path in pytest_of_dirs:
            success, message = self._remove_test_temp_dir(dir_path, dry_run)
            if success is True:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            elif success is False:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        # Remove pytest-tmp-* directories (created during parallel test execution)
        pytest_tmp_dirs = list(test_data_dir.glob("pytest-tmp-*"))
        for dir_path in pytest_tmp_dirs:
            success, message = self._remove_test_temp_dir(dir_path, dry_run)
            if success is True:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            elif success is False:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        # Remove tmp subdirectories (but keep the tmp directory itself)
        tmp_dir = test_data_dir / "tmp"
        if tmp_dir.exists():
            for item in tmp_dir.iterdir():
                if item.is_dir():
                    success, message = self._remove_test_temp_dir(item, dry_run)
                    if success is True:
                        removed += 1
                        if not dry_run:
                            logger.info(f"  {message}")
                    elif success is False:
                        failed += 1
                        if not dry_run:
                            logger.warning(f"  {message}")

        # Remove conversation_states.json
        conversation_states = test_data_dir / "conversation_states.json"
        if conversation_states.exists():
            success, message = self.remove_path(conversation_states, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        # Clean up flags, requests, backups directories (contents only)
        for subdir_name in ["flags", "requests", "backups"]:
            subdir = test_data_dir / subdir_name
            if subdir.exists():
                for item in subdir.iterdir():
                    success, message = self._remove_test_temp_dir(item, dry_run)
                    if success is True:
                        removed += 1
                        if not dry_run:
                            logger.info(f"  {message}")
                    elif success is False:
                        failed += 1
                        if not dry_run:
                            logger.warning(f"  {message}")

        return removed, failed

    def _remove_test_temp_dir(
        self, path: Path, dry_run: bool = False
    ) -> tuple[bool | None, str]:
        """Remove test temp directory with permission-safe handling.

        Returns:
            (True, message) if removed
            (False, message) if failed
            (None, message) if skipped due to permissions
        """
        if dry_run:
            return self.remove_path(path, dry_run)
        try:
            if not path.exists():
                return False, f"Does not exist: {path}"
            if path.is_file():
                path.unlink()
                return True, f"Removed file: {path}"
            shutil.rmtree(path)
            return True, f"Removed directory: {path}"
        except PermissionError as exc:
            return None, f"Permission denied: {path} - {exc}"
        except Exception as exc:
            return False, f"Error removing {path}: {exc}"

    def cleanup_test_user_data(self, dry_run: bool = False) -> tuple[int, int]:
        """Remove test user data directories."""
        users_dir = self.project_root / "data" / "users"
        removed = 0
        failed = 0

        if not users_dir.exists():
            return removed, failed

        # Remove test_* user directories
        test_user_dirs = [
            d for d in users_dir.iterdir() if d.is_dir() and d.name.startswith("test_")
        ]

        for dir_path in test_user_dirs:
            success, message = self.remove_path(dir_path, dry_run)
            if success:
                removed += 1
                if not dry_run:
                    logger.info(f"  {message}")
            else:
                failed += 1
                if not dry_run:
                    logger.warning(f"  {message}")

        return removed, failed

    def cleanup_all(
        self,
        dry_run: bool = False,
        cache: bool = True,
        test_data: bool = True,
        coverage: bool = True,
        keep_vscode: bool = False,
        keep_cursor: bool = False,
        include_tool_caches: bool = False,
    ) -> dict:
        """
        Run all cleanup operations.

        Args:
            dry_run: If True, show what would be removed without actually removing
            cache: Clean cache directories (__pycache__, .pytest_cache)
            test_data: Clean test data directories
            coverage: Clean coverage files, logs, and test-file-based coverage cache
            keep_vscode: Keep VSCode cache directories (not implemented)
            keep_cursor: Keep Cursor cache directories (not implemented)
            include_tool_caches: If True, also clean standardized storage/tool cache artifacts

        Returns:
            Dictionary with cleanup results for each category
        """
        results = {
            "cache": {"removed": 0, "failed": 0},
            "pytest_cache": {"removed": 0, "failed": 0},
            "coverage": {"removed": 0, "failed": 0},
            "coverage_logs": {"removed": 0, "failed": 0},
            "test_data": {"removed": 0, "failed": 0},
            "test_user_data": {"removed": 0, "failed": 0},
            "total_removed": 0,
            "total_failed": 0,
        }

        if cache:
            removed, failed = self.cleanup_cache_directories(
                dry_run, include_tool_caches=include_tool_caches
            )
            results["cache"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

            removed, failed = self.cleanup_pytest_cache(dry_run)
            results["pytest_cache"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

        if coverage:
            removed, failed = self.cleanup_coverage_files(dry_run)
            results["coverage"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

            removed, failed = self.cleanup_coverage_logs(dry_run)
            results["coverage_logs"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

        if test_data:
            removed, failed = self.cleanup_test_temp_dirs(dry_run)
            results["test_data"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

            removed, failed = self.cleanup_test_user_data(dry_run)
            results["test_user_data"] = {"removed": removed, "failed": failed}
            results["total_removed"] += removed
            results["total_failed"] += failed

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up project cache and temporary files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Clean cache directories (__pycache__, .pytest_cache)",
    )
    parser.add_argument(
        "--test-data", action="store_true", help="Clean test data directories"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Clean coverage files and logs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all categories (default if no specific category specified)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # If no specific category is specified, default to --all
    if not (args.cache or args.test_data or args.coverage):
        args.all = True

    cleanup = ProjectCleanup()

    if args.all:
        results = cleanup.cleanup_all(
            dry_run=args.dry_run, cache=True, test_data=True, coverage=True
        )
    else:
        results = cleanup.cleanup_all(
            dry_run=args.dry_run,
            cache=args.cache,
            test_data=args.test_data,
            coverage=args.coverage,
        )

    if args.json:
        import json

        print(json.dumps(results, indent=2))
    else:
        if args.dry_run:
            logger.info("DRY RUN MODE - No files were actually removed")
        logger.info(
            f"Summary: {results['total_removed']} items removed, {results['total_failed']} failed"
        )

    return 0 if results["total_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
