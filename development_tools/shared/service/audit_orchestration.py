"""
Audit orchestration methods for AIToolsService.

Contains methods for running audits in three tiers (quick, standard, full)
and managing audit state.
"""
# pyright: reportAttributeAccessIssue=false

import contextlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import output storage
from ..output_storage import save_tool_result, get_all_tool_results, load_tool_result
from ..file_rotation import create_output_file
from ..lock_state import cleanup_lock_paths, evaluate_lock_set, write_lock_metadata
from .. import audit_signal_state
from ..audit_tiers import (
    get_tier1_groups,
    get_tier2_groups,
    get_tier3_groups,
    get_expected_tools_for_tier as audit_tiers_get_expected_tools_for_tier,
    get_tier3_tool_names_dev_tools_only,
    get_tier3_tool_names_full_repo,
)
from ..tool_metadata import CACHE_AWARE_TOOLS

# Module-level flag to track if ANY audit is in progress
_AUDIT_IN_PROGRESS_GLOBAL = False

# File-based lock for cross-process protection
_AUDIT_LOCK_FILE = None


class ToolExecutionError(RuntimeError):
    """Raised when a tool execution fails while preserving elapsed timing."""

    def __init__(self, tool_name: str, elapsed_time: float, original_exception: Exception):
        super().__init__(str(original_exception))
        self.tool_name = tool_name
        self.elapsed_time = elapsed_time
        self.original_exception = original_exception


def _get_status_file_mtimes(
    project_root: Path, *, dev_tools_only: bool = False
) -> dict[str, float]:
    """Get modification times for status outputs (full-repo AI_* or dev-tools-only DEV_TOOLS_*)."""
    if dev_tools_only:
        status_files = {
            "DEV_TOOLS_STATUS.md": project_root / "development_tools" / "DEV_TOOLS_STATUS.md",
            "DEV_TOOLS_PRIORITIES.md": project_root
            / "development_tools"
            / "DEV_TOOLS_PRIORITIES.md",
            "DEV_TOOLS_CONSOLIDATED_REPORT.md": project_root
            / "development_tools"
            / "DEV_TOOLS_CONSOLIDATED_REPORT.md",
        }
    else:
        try:
            from ... import config

            status_config = config.get_status_config()
            status_files_config = status_config.get("status_files", {})
            status_files = {
                "AI_STATUS.md": project_root
                / status_files_config.get(
                    "ai_status", "development_tools/AI_STATUS.md"
                ),
                "AI_PRIORITIES.md": project_root
                / status_files_config.get(
                    "ai_priorities", "development_tools/AI_PRIORITIES.md"
                ),
                "CONSOLIDATED_REPORT.md": project_root
                / status_files_config.get(
                    "consolidated_report", "development_tools/CONSOLIDATED_REPORT.md"
                ),
            }
        except (ImportError, AttributeError, KeyError):
            status_files = {
                "AI_STATUS.md": project_root / "development_tools" / "AI_STATUS.md",
                "AI_PRIORITIES.md": project_root
                / "development_tools"
                / "AI_PRIORITIES.md",
                "CONSOLIDATED_REPORT.md": project_root
                / "development_tools"
                / "CONSOLIDATED_REPORT.md",
            }
    mtimes = {}
    for name, path in status_files.items():
        if path.exists():
            mtimes[name] = path.stat().st_mtime
        else:
            mtimes[name] = 0.0
    return mtimes


def _is_audit_in_progress(project_root: Path) -> bool:
    """Check if audit is in progress using in-memory flag + active metadata locks."""
    global _AUDIT_IN_PROGRESS_GLOBAL, _AUDIT_LOCK_FILE
    if _AUDIT_IN_PROGRESS_GLOBAL:
        return True

    try:
        from ... import config

        audit_lock_path = config.get_external_value(
            "paths.audit_lock_file", ".audit_in_progress.lock"
        )
        coverage_lock_path = config.get_external_value(
            "paths.coverage_lock_file", ".coverage_in_progress.lock"
        )
        audit_lock_file = project_root / Path(audit_lock_path)
        coverage_lock_file = project_root / Path(coverage_lock_path)
    except (ImportError, AttributeError):
        audit_lock_file = project_root / ".audit_in_progress.lock"
        coverage_lock_file = project_root / ".coverage_in_progress.lock"
    dev_tools_coverage_lock_file = (
        coverage_lock_file.parent / ".coverage_dev_tools_in_progress.lock"
    )
    lock_states = evaluate_lock_set(
        [audit_lock_file, coverage_lock_file, dev_tools_coverage_lock_file]
    )
    cleanup_targets = [
        entry["path"]
        for entry in (lock_states["stale"] + lock_states["malformed"])
        if isinstance(entry.get("path"), Path)
    ]
    if cleanup_targets:
        removed = cleanup_lock_paths(cleanup_targets)
        logger.warning(
            f"Removed {removed} stale/malformed audit lock file(s) during in-progress check"
        )
    return len(lock_states["active"]) > 0


class AuditOrchestrationMixin:
    """Mixin class providing audit orchestration methods to AIToolsService."""

    def run_analyze_duplicate_functions(self, *args, **kwargs):
        """Stub for mixin typing; implemented in ToolWrappersMixin."""
        raise NotImplementedError

    def _run_analyze_duplicate_functions_for_audit(self):
        """Run duplicate-functions with body-for-near-miss when this is a full audit and config enables it."""
        try:
            from ... import config as devtools_config
            cfg = devtools_config.get_analyze_duplicate_functions_config()
        except Exception:
            cfg = {}
        body_for_near_miss = (
            getattr(self, "current_audit_tier", 2) >= 3
            and cfg.get("run_body_similarity_on_full_audit", True)
        )
        return self.run_analyze_duplicate_functions(body_for_near_miss_only=body_for_near_miss)

    def _effective_tier3_state(self) -> str:
        """Return Tier 3 state including development-tools track impact."""
        outcome = (
            self.tier3_test_outcome
            if isinstance(getattr(self, "tier3_test_outcome", None), dict)
            else {}
        )
        state = outcome.get("state", "") or ""
        parallel = outcome.get("parallel", {}) if isinstance(outcome.get("parallel"), dict) else {}
        no_parallel = outcome.get("no_parallel", {}) if isinstance(outcome.get("no_parallel"), dict) else {}
        dev_tools = (
            outcome.get("development_tools", {})
            if isinstance(outcome.get("development_tools"), dict)
            else {}
        )

        def _track_label(track: dict[str, Any]) -> str:
            classification = track.get("classification")
            if isinstance(classification, str) and classification.strip():
                return classification.strip()
            return "unknown"

        track_labels = (
            _track_label(parallel),
            _track_label(no_parallel),
            _track_label(dev_tools),
        )

        if state == "coverage_failed":
            return "coverage_failed"
        if "infra_cleanup_error" in track_labels:
            return "infra_cleanup_error"
        if "crashed" in track_labels:
            return "crashed"
        if "failed" in track_labels:
            return "test_failures"
        if any(label in {"passed", "skipped"} for label in track_labels):
            return "clean"
        if any(label == "unknown" for label in track_labels):
            return "coverage_failed"
        return "unknown"

    def _finalize_tier3_audit_scope(self) -> None:
        """Align tier3_test_outcome and coverage scope flags with full vs dev-tools-only Tier 3 runs (V5 §1.9)."""
        dev_only = bool(getattr(self, "dev_tools_only_mode", False))
        outcome: dict[str, Any] = (
            dict(self.tier3_test_outcome)
            if isinstance(getattr(self, "tier3_test_outcome", None), dict)
            else {}
        )

        skipped_scope_parallel = {
            "state": "skipped",
            "classification": "skipped",
            "classification_reason": "not_run_this_audit_scope",
            "actionable_context": (
                "Main parallel/no-parallel pytest tracks were not run; this pass used "
                "`audit --full --dev-tools-only`. "
                "Run `python development_tools/run_development_tools.py audit --full` "
                "(without `--dev-tools-only`) to refresh full-repo coverage and Tier 3 main tracks."
            ),
            "log_file": None,
            "return_code_hex": None,
            "return_code": None,
            "passed_count": 0,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "failed_node_ids": [],
        }
        skipped_scope_dev = {
            "state": "skipped",
            "classification": "skipped",
            "classification_reason": "not_run_this_audit_scope",
            "actionable_context": (
                "Development-tools coverage was not run; this pass used full-repo Tier 3 scope "
                "(main `run_test_coverage` only). "
                "Run `python development_tools/run_development_tools.py audit --full --dev-tools-only` "
                "to refresh dev-tools coverage and the development-tools Tier 3 track."
            ),
            "log_file": None,
            "return_code_hex": None,
            "return_code": None,
            "passed_count": 0,
            "failed_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "failed_node_ids": [],
        }

        if dev_only:
            self._tier3_skipped_main_tracks = True
            self._tier3_skipped_dev_track = False
            outcome["parallel"] = skipped_scope_parallel
            outcome["no_parallel"] = skipped_scope_parallel
            dev_track = outcome.get("development_tools")
            if isinstance(dev_track, dict) and dev_track.get("state"):
                outcome["state"] = dev_track.get("state")
            elif not outcome.get("state"):
                outcome["state"] = "clean"
        else:
            self._tier3_skipped_main_tracks = False
            dev_existing = outcome.get("development_tools")
            keep_unified_dev = False
            if isinstance(dev_existing, dict):
                cls = dev_existing.get("classification")
                creason = dev_existing.get("classification_reason")
                st = dev_existing.get("state")
                if creason == "cache_only_precheck":
                    keep_unified_dev = False
                elif (
                    cls in ("passed", "failed", "crashed", "infra_cleanup_error")
                    or creason
                    in (
                        "no_dev_tools_failures_unified_run",
                        "pytest_failed_or_errored",
                    )
                    or st in ("passed", "failed", "crashed")
                ):
                    keep_unified_dev = True
            if keep_unified_dev:
                self._tier3_skipped_dev_track = False
            else:
                self._tier3_skipped_dev_track = True
                outcome["development_tools"] = skipped_scope_dev

        self.tier3_test_outcome = outcome

    def _get_audit_lock_file_path(self) -> Path:
        """Get audit lock file path (configurable via config, defaults to .audit_in_progress.lock relative to project root)."""
        try:
            from ... import config
            # Default to generic path relative to project root (no development_tools/ assumption)
            lock_file_path = config.get_external_value('paths.audit_lock_file', '.audit_in_progress.lock')
            return self.project_root / lock_file_path
        except (ImportError, AttributeError):
            return self.project_root / 'development_tools' / '.audit_in_progress.lock'
    
    def _get_coverage_lock_file_path(self) -> Path:
        """Get coverage lock file path (configurable via config, defaults to .coverage_in_progress.lock relative to project root)."""
        try:
            from ... import config
            # Default to generic path relative to project root (no development_tools/ assumption)
            lock_file_path = config.get_external_value('paths.coverage_lock_file', '.coverage_in_progress.lock')
            return self.project_root / lock_file_path
        except (ImportError, AttributeError):
            return self.project_root / 'development_tools' / '.coverage_in_progress.lock'
    
    def run_audit(
        self,
        quick: bool = False,
        full: bool = False,
        include_overlap: bool = False,
        strict: bool = False,
    ):
        """Run audit workflow with three-tier structure."""
        global _AUDIT_IN_PROGRESS_GLOBAL, _AUDIT_LOCK_FILE

        lock_states = evaluate_lock_set(self._get_audit_related_lock_paths())
        cleanup_targets = [
            entry["path"]
            for entry in (lock_states["stale"] + lock_states["malformed"])
            if isinstance(entry.get("path"), Path)
        ]
        if cleanup_targets:
            removed = cleanup_lock_paths(cleanup_targets)
            logger.warning(
                f"Removed {removed} stale/malformed audit lock file(s) before starting audit"
            )
        if lock_states["active"]:
            lock_list = ", ".join(
                str(entry["path"])
                for entry in lock_states["active"]
                if isinstance(entry.get("path"), Path)
            )
            print(
                "Audit blocked: active audit/coverage lock file(s) present: "
                f"{lock_list}"
            )
            logger.error(
                "Audit blocked: active audit/coverage lock file(s) present: "
                f"{lock_list}"
            )
            return False
        
        # Determine audit tier
        if quick:
            tier = 1
            operation_name = "audit --quick (Tier 1)"
        elif full:
            tier = 3
            operation_name = "audit --full (Tier 3)"
        else:
            tier = 2
            operation_name = "audit (Tier 2 - standard)"
        
        # Print to console for user visibility (regardless of log level)
        print(f"Starting {operation_name}...")
        print("=" * 50)
        logger.info(f"Starting {operation_name}...")
        logger.info("=" * 50)
        
        self.current_audit_tier = tier
        self._audit_in_progress = True
        _AUDIT_IN_PROGRESS_GLOBAL = True
        # Dev-tools-only mode: restrict scan to development_tools
        dev_tools_only = getattr(self, 'dev_tools_only_mode', False)
        _audit_storage_token = None
        if dev_tools_only:
            from ..audit_storage_scope import (
                STORAGE_SCOPE_DEV_TOOLS,
                set_audit_storage_scope,
            )

            _audit_storage_token = set_audit_storage_scope(STORAGE_SCOPE_DEV_TOOLS)
            operation_name = f"{operation_name} (dev-tools-only)"
            try:
                from ... import config as dt_config
                self._original_get_scan_directories = dt_config.get_scan_directories
                dt_config.get_scan_directories = lambda: ["development_tools"]
            except (ImportError, AttributeError):
                pass
        # Track which tools were actually run in this audit tier
        self._tools_run_in_current_tier = set()
        # Track timing for each tool
        self._tool_timings = {}
        # Track execution status for each tool (success/failed)
        self._tool_execution_status = {}
        # Track cache metadata per tool for timing diagnostics
        self._tool_cache_metadata = {}
        self.tier3_test_outcome = {}
        self._tier3_skipped_main_tracks = False
        self._tier3_skipped_dev_track = False
        self._internal_interrupt_detected = False
        # Track wall-clock runtime (accurate total audit duration with parallel execution)
        self._audit_wall_clock_start = time.perf_counter()
        
        # Create file-based lock
        if _AUDIT_LOCK_FILE is None:
            _AUDIT_LOCK_FILE = self._get_audit_lock_file_path()
        try:
            if not write_lock_metadata(_AUDIT_LOCK_FILE, lock_type="audit"):
                raise RuntimeError("write_lock_metadata returned False for audit lock")
        except Exception as e:
            logger.warning(f"Failed to create audit lock file: {e}")
        
        initial_mtimes = _get_status_file_mtimes(
            self.project_root, dev_tools_only=dev_tools_only
        )
        self._audit_start_mtimes = initial_mtimes
        
        self._include_overlap = include_overlap
        if full and not include_overlap:
            include_overlap = True
            self._include_overlap = True
        
        success = True
        try:
            # Tier 1: Quick audit tools
            print("Running Tier 1 tools (quick audit)...")
            logger.info("Running Tier 1 tools (quick audit)...")
            tier1_success = self._run_quick_audit_tools()
            if not tier1_success:
                success = False
            
            # Tier 2: Standard audit tools
            if tier >= 2:
                print("=" * 50)
                logger.info("=" * 50)
                print("Running Tier 2 tools (standard audit)...")
                logger.info("Running Tier 2 tools (standard audit)...")
                tier2_success = self._run_standard_audit_tools()
                if not tier2_success:
                    success = False
            
            # Tier 3: Full audit tools
            if tier >= 3:
                print("=" * 50)
                logger.info("=" * 50)
                print("Running Tier 3 tools (full audit)...")
                logger.info("Running Tier 3 tools (full audit)...")
                tier3_success = self._run_full_audit_tools()
                if not tier3_success:
                    success = False
        except KeyboardInterrupt:
            if bool(getattr(self, "_internal_interrupt_detected", False)):
                print(
                    "WARNING: Internal interrupt signature detected during Tier 3 coverage "
                    "(SIGINT/control event propagated from subprocess). "
                    "Treating audit as failed without user-interrupt exit."
                )
                logger.error(
                    "Internal interrupt signature detected during Tier 3 coverage; "
                    "continuing audit finalization with failure state."
                )
                success = False
            else:
                raise
        except Exception as e:
            print(f"ERROR: Error during audit execution: {e}")
            logger.error(f"Error during audit execution: {e}", exc_info=True)
            success = False
        
        # Save all tool results
        try:
            self._save_audit_results_aggregated(tier)
        except Exception as e:
            logger.warning(f"Failed to save aggregated audit results: {e}", exc_info=True)
        
        # Reload cache data
        try:
            self._reload_all_cache_data()
        except KeyboardInterrupt:
            self._internal_interrupt_detected = True
            success = False
            logger.error(
                "KeyboardInterrupt during audit finalization (_reload_all_cache_data); "
                "treating as internal failure state."
            )
        
        # Sync TODO.md with changelog
        try:
            self._sync_todo_with_changelog()
        except KeyboardInterrupt:
            self._internal_interrupt_detected = True
            success = False
            logger.error(
                "KeyboardInterrupt during audit finalization (_sync_todo_with_changelog); "
                "treating as internal failure state."
            )
        
        # Validate referenced paths
        try:
            self._validate_referenced_paths()
        except Exception as e:
            logger.warning(f"Path validation failed (non-blocking): {e}")
        
        # Final quality checks (must run before report generation so findings appear in reports)
        try:
            self._check_and_trim_changelog_entries()
        except Exception as e:
            logger.warning(f"Changelog trim check failed (non-blocking): {e}")

        try:
            self._check_documentation_quality()
        except Exception as e:
            logger.warning(f"Documentation quality check failed (non-blocking): {e}")

        try:
            self._check_ascii_compliance()
        except Exception as e:
            logger.warning(f"ASCII compliance check failed (non-blocking): {e}")

        # Generate status files
        if self.current_audit_tier is None:
            logger.warning(f"current_audit_tier is None at end of audit! Setting to tier {tier}")
        
        try:
            pre_final_mtimes = _get_status_file_mtimes(
                self.project_root, dev_tools_only=dev_tools_only
            )
            if hasattr(self, '_audit_start_mtimes'):
                for file_name, mtime in pre_final_mtimes.items():
                    if mtime > self._audit_start_mtimes.get(file_name, 0):
                        logger.warning(f"Status file {file_name} was modified during audit!")
            
            was_audit_in_progress = _AUDIT_IN_PROGRESS_GLOBAL
            _AUDIT_IN_PROGRESS_GLOBAL = False
            
            if _AUDIT_LOCK_FILE and _AUDIT_LOCK_FILE.exists():
                try:
                    _AUDIT_LOCK_FILE.unlink()
                except Exception as e:
                    logger.warning(f"Failed to temporarily remove audit lock file: {e}")
            
            try:
                # Generate status documents
                # Get status file paths from config
                try:
                    from ... import config
                    status_config = config.get_status_config()
                    status_files_config = status_config.get('status_files', {})
                    if getattr(self, 'dev_tools_only_mode', False):
                        ai_status_path = 'development_tools/DEV_TOOLS_STATUS.md'
                        ai_priorities_path = 'development_tools/DEV_TOOLS_PRIORITIES.md'
                        consolidated_report_path = 'development_tools/DEV_TOOLS_CONSOLIDATED_REPORT.md'
                    else:
                        ai_status_path = status_files_config.get('ai_status', 'development_tools/AI_STATUS.md')
                        ai_priorities_path = status_files_config.get('ai_priorities', 'development_tools/AI_PRIORITIES.md')
                        consolidated_report_path = status_files_config.get('consolidated_report', 'development_tools/CONSOLIDATED_REPORT.md')
                except (ImportError, AttributeError, KeyError):
                    if getattr(self, 'dev_tools_only_mode', False):
                        ai_status_path = 'development_tools/DEV_TOOLS_STATUS.md'
                        ai_priorities_path = 'development_tools/DEV_TOOLS_PRIORITIES.md'
                        consolidated_report_path = 'development_tools/DEV_TOOLS_CONSOLIDATED_REPORT.md'
                    else:
                        ai_status_path = 'development_tools/AI_STATUS.md'
                        ai_priorities_path = 'development_tools/AI_PRIORITIES.md'
                        consolidated_report_path = 'development_tools/CONSOLIDATED_REPORT.md'
                
                try:
                    ai_status = self._generate_ai_status_document()
                except Exception as e:
                    logger.warning(f"Error generating AI_STATUS document: {e}")
                    ai_status = "# AI Status\n\nError generating status document."
                ai_status_file = create_output_file(ai_status_path, ai_status, project_root=self.project_root)
                
                try:
                    ai_priorities = self._generate_ai_priorities_document()
                except Exception as e:
                    import traceback
                    logger.warning(f"Error generating AI_PRIORITIES document: {e}")
                    logger.debug(f"AI_PRIORITIES traceback:\n{traceback.format_exc()}")
                    ai_priorities = "# AI Priorities\n\nError generating priorities document."
                ai_priorities_file = create_output_file(ai_priorities_path, ai_priorities, project_root=self.project_root)
                
                try:
                    consolidated_report = self._generate_consolidated_report()
                except Exception as e:
                    logger.warning(f"Error generating consolidated report: {e}")
                    consolidated_report = "Error generating consolidated report."
                consolidated_file = create_output_file(consolidated_report_path, consolidated_report, project_root=self.project_root)
                
                post_final_mtimes = _get_status_file_mtimes(
                    self.project_root, dev_tools_only=dev_tools_only
                )
                for file_name, mtime in post_final_mtimes.items():
                    if mtime <= pre_final_mtimes.get(file_name, 0):
                        logger.warning(f"Status file {file_name} mtime did not change during final write!")
            finally:
                _AUDIT_IN_PROGRESS_GLOBAL = was_audit_in_progress
            
            print("=" * 50)
            logger.info("=" * 50)
            tier3_state = ""
            if tier >= 3:
                tier3_state = self._effective_tier3_state()
            if strict and tier >= 3 and tier3_state in {"test_failures", "crashed", "infra_cleanup_error"}:
                success = False
                logger.warning(
                    f"Strict mode forcing non-zero exit for Tier 3 outcome: {tier3_state}"
                )

            if success:
                if tier >= 3 and tier3_state == "test_failures":
                    print(f"Completed {operation_name} with test failures")
                    logger.warning(f"Completed {operation_name} with test failures")
                elif tier >= 3 and tier3_state in {"crashed", "infra_cleanup_error"}:
                    print(f"Completed {operation_name} with crashes/infrastructure issues")
                    logger.warning(
                        f"Completed {operation_name} with crashes/infrastructure issues"
                    )
                else:
                    print(f"Completed {operation_name} successfully!")
                    logger.info(f"Completed {operation_name} successfully!")
                # Log timing summary (logging only; avoid stdout noise per 2.2/2.9)
                if self._tool_timings:
                    total_time = sum(self._tool_timings.values())
                    timing_msg = f"Total tool execution time: {total_time:.2f}s"
                    logger.info(timing_msg)
                    if hasattr(self, '_audit_wall_clock_start'):
                        wall_clock_total = time.perf_counter() - self._audit_wall_clock_start
                        wall_clock_msg = f"Total audit wall-clock time: {wall_clock_total:.2f}s"
                        logger.info(wall_clock_msg)
                    # Log slowest tools
                    sorted_timings = sorted(self._tool_timings.items(), key=lambda x: x[1], reverse=True)
                    if len(sorted_timings) > 0:
                        slowest_msg = f"Slowest tools: {', '.join(f'{name} ({time:.2f}s)' for name, time in sorted_timings[:5])}"
                        logger.info(slowest_msg)
                    coverage_summary = self._format_coverage_mode_summary()
                    if coverage_summary:
                        coverage_msg = f"Coverage mode summary: {coverage_summary}"
                        logger.info(coverage_msg)
                    cache_summary = self._format_cache_mode_summary(
                        ['analyze_unused_imports', 'analyze_legacy_references', 'analyze_documentation_sync']
                    )
                    if cache_summary:
                        cache_msg = f"Cache mode summary: {cache_summary}"
                        logger.info(cache_msg)
                if getattr(self, "dev_tools_only_mode", False):
                    print(f"  * Dev Tools Status: {ai_status_file}")
                    print(f"  * Dev Tools Priorities: {ai_priorities_file}")
                    print(f"  * Dev Tools Consolidated Report: {consolidated_file}")
                    logger.info(f"* Dev Tools Status: {ai_status_file}")
                    logger.info(f"* Dev Tools Priorities: {ai_priorities_file}")
                    logger.info(f"* Dev Tools Consolidated Report: {consolidated_file}")
                else:
                    print(f"  * AI Status: {ai_status_file}")
                    print(f"  * AI Priorities: {ai_priorities_file}")
                    print(f"  * Consolidated Report: {consolidated_file}")
                    logger.info(f"* AI Status: {ai_status_file}")
                    logger.info(f"* AI Priorities: {ai_priorities_file}")
                    logger.info(f"* Consolidated Report: {consolidated_file}")
            else:
                if strict and tier >= 3 and tier3_state in {"test_failures", "crashed", "infra_cleanup_error"}:
                    print(f"Completed {operation_name} with strict-mode test failures/crashes/infra errors")
                    logger.warning(
                        f"Completed {operation_name} with strict-mode test failures/crashes/infra errors"
                    )
                else:
                    print(f"Completed {operation_name} with tool failures")
                    logger.warning(f"Completed {operation_name} with tool failures")
        except KeyboardInterrupt:
            self._internal_interrupt_detected = True
            success = False
            print(
                "WARNING: KeyboardInterrupt occurred during audit finalization/report generation. "
                "Treating as internal failure state, not direct user interrupt."
            )
            logger.error(
                "KeyboardInterrupt during audit finalization/report generation; "
                "treating as internal failure state."
            )
        except Exception as e:
            print(f"ERROR: Error generating status files: {e}")
            logger.error(f"Error generating status files: {e}", exc_info=True)
            success = False
        finally:
            # Restore get_scan_directories if we patched it for dev-tools-only mode
            if getattr(self, 'dev_tools_only_mode', False) and hasattr(self, '_original_get_scan_directories'):
                try:
                    from ... import config as dt_config
                    dt_config.get_scan_directories = self._original_get_scan_directories
                except (ImportError, AttributeError):
                    pass
            # Clear flags and remove lock file
            self._audit_in_progress = False
            self.current_audit_tier = None
            self._tools_run_in_current_tier = set()  # Clear tracking when audit completes
            # Clear results_cache to prevent stale data from being used in next audit
            if hasattr(self, 'results_cache'):
                self.results_cache = {}
            # Save timing data for analysis
            if hasattr(self, '_tool_timings') and self._tool_timings:
                self._save_timing_data(tier=tier, audit_success=success)
            if _audit_storage_token is not None:
                from ..audit_storage_scope import reset_audit_storage_scope

                reset_audit_storage_scope(_audit_storage_token)
            _AUDIT_IN_PROGRESS_GLOBAL = False
            if _AUDIT_LOCK_FILE and _AUDIT_LOCK_FILE.exists():
                try:
                    _AUDIT_LOCK_FILE.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove audit lock file: {e}")
        
        return success
    
    def run_quick_audit(self) -> bool:
        """Run quick audit (Tier 1 only)."""
        return self.run_audit(quick=True)
    
    def _run_quick_audit_tools(self) -> bool:
        """Run Tier 1 tools: Quick audit (core metrics only, <=2s per tool).
        
        Note: Tools moved here based on execution time (<=2s) while respecting dependencies.
        """
        successful = []
        failed = []
        
        # Tier 1 tools from canonical audit_tiers (single source of truth)
        tier1_core_tools, tier1_independent_tools, tier1_dependent_groups = get_tier1_groups(self)
        
        # Run core tools first (analyze_functions must run before dependent tools)
        for tool_name, tool_func in tier1_core_tools:
            try:
                result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                self._tool_timings[tool_name] = elapsed_time
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    self._tool_execution_status[tool_name] = 'success'
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                    # Note: Tools save their own results, so no need to save here
                    # Removed duplicate save_tool_result call to prevent duplicate logging
                else:
                    self._tool_execution_status[tool_name] = 'failed'
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
                    if isinstance(result, dict) and result.get("error"):
                        _err = (result.get("error") or "").strip()[:800]
                        if _err:
                            logger.warning(f"  {tool_name} error detail: {_err}")
            except Exception as exc:
                elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                self._tool_timings[tool_name] = elapsed_time
                self._tool_execution_status[tool_name] = 'failed'
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        # Run independent tools and dependent groups in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def run_tool_group(group_tools):
            """Run a group of tools sequentially and return results."""
            group_results = {}
            for tool_name, tool_func in group_tools:
                try:
                    result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                    group_results[tool_name] = (result, elapsed_time)
                except Exception as exc:
                    logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                    elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                    group_results[tool_name] = ({'success': False, 'error': str(exc)}, elapsed_time)
            return group_results
        
        # Combine independent tools (as single-tool groups) and dependent groups
        all_groups = [[(name, func)] for name, func in tier1_independent_tools] + tier1_dependent_groups
        max_workers = min(4, len(all_groups))
        
        logger.debug(f"Running Tier 1 additional tools: {len(tier1_independent_tools)} independent + {len(tier1_dependent_groups)} groups with {max_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(run_tool_group, group): i
                for i, group in enumerate(all_groups)
            }
            
            for future in as_completed(future_to_group):
                group_results = future.result()
                for tool_name, (result, elapsed_time) in group_results.items():
                    self._tool_timings[tool_name] = elapsed_time
                    logger.debug(f"  - {tool_name} completed in {elapsed_time:.2f}s")
                    if isinstance(result, dict):
                        success = result.get('success', False)
                        if 'data' in result:
                            self._extract_key_info(tool_name, result)
                    else:
                        success = bool(result)
                    self._record_tool_cache_metadata(tool_name, result)
                    
                    if success:
                        self._tool_execution_status[tool_name] = 'success'
                        successful.append(tool_name)
                        self._tools_run_in_current_tier.add(tool_name)
                    else:
                        self._tool_execution_status[tool_name] = 'failed'
                        failed.append(tool_name)
                        logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        # quick_status is only part of explicit Tier 1 (--quick) runs.
        if self.current_audit_tier == 1:
            try:
                quick_status_result, elapsed_time = self._run_tool_with_timing(
                    'quick_status',
                    lambda: self.run_script('quick_status', 'json')
                )
                self._tool_timings['quick_status'] = elapsed_time
                if quick_status_result.get('success'):
                    self.status_results = quick_status_result
                    output = quick_status_result.get('output', '')
                    if output:
                        try:
                            parsed = json.loads(output)
                            self.status_summary = parsed
                            quick_status_result['data'] = parsed
                            try:
                                save_tool_result('quick_status', 'reports', parsed, project_root=self.project_root)
                            except Exception as e:
                                logger.debug(f"Failed to save quick_status result: {e}")
                            self._tool_execution_status['quick_status'] = 'success'
                            successful.append('quick_status')
                            self._tools_run_in_current_tier.add('quick_status')
                        except json.JSONDecodeError:
                            self._tool_execution_status['quick_status'] = 'failed'
                            logger.warning("  - quick_status output could not be parsed as JSON")
                            failed.append('quick_status')
                    else:
                        self._tool_execution_status['quick_status'] = 'failed'
                        failed.append('quick_status')
                else:
                    self._tool_execution_status['quick_status'] = 'failed'
                    failed.append('quick_status')
            except Exception as exc:
                elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                self._tool_timings['quick_status'] = elapsed_time
                self._tool_execution_status['quick_status'] = 'failed'
                failed.append('quick_status')
                logger.error(f"  - quick_status failed: {exc}")
        
        if failed:
            logger.warning(f"Tier 1 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 1 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_standard_audit_tools(self) -> bool:
        """Run Tier 2 tools: Standard audit (quality checks, >2s but <=10s per tool).
        
        Note: Tools moved here based on execution time (>2s but <=10s) while respecting dependencies.
        """
        successful = []
        failed = []
        
        # Tier 2 tools from canonical audit_tiers (single source of truth)
        tier2_independent_tools, tier2_dependent_groups = get_tier2_groups(self)
        
        # Run independent tools and dependent groups in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def run_tool_group(group_tools):
            """Run a group of tools sequentially and return results."""
            group_results = {}
            for tool_name, tool_func in group_tools:
                try:
                    result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                    group_results[tool_name] = (result, elapsed_time)
                except Exception as exc:
                    logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                    elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                    group_results[tool_name] = ({'success': False, 'error': str(exc)}, elapsed_time)
            return group_results
        
        # Combine independent tools (as single-tool groups) and dependent groups
        all_groups = [[(name, func)] for name, func in tier2_independent_tools] + tier2_dependent_groups
        max_workers = min(4, len(all_groups))
        
        logger.debug(f"Running Tier 2 tools: {len(tier2_independent_tools)} independent + {len(tier2_dependent_groups)} groups with {max_workers} parallel workers...")
        
        all_results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(run_tool_group, group): i
                for i, group in enumerate(all_groups)
            }
            
            for future in as_completed(future_to_group):
                group_results = future.result()
                for tool_name, (result, elapsed_time) in group_results.items():
                    all_results[tool_name] = result
                    self._tool_timings[tool_name] = elapsed_time
                    logger.debug(f"  - {tool_name} completed in {elapsed_time:.2f}s")
        
        # Process results
        for tool_name, result in all_results.items():
            if isinstance(result, dict):
                success = result.get('success', False)
                if 'data' in result:
                    self._extract_key_info(tool_name, result)
            else:
                success = bool(result)
            self._record_tool_cache_metadata(tool_name, result)
            
            if success:
                self._tool_execution_status[tool_name] = 'success'
                successful.append(tool_name)
                self._tools_run_in_current_tier.add(tool_name)
            else:
                self._tool_execution_status[tool_name] = 'failed'
                failed.append(tool_name)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
                if isinstance(result, dict) and result.get("error"):
                    _err = (result.get("error") or "").strip()[:800]
                    if _err:
                        logger.warning(f"  {tool_name} error detail: {_err}")
        
        if failed:
            logger.warning(f"Tier 2 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 2 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_tool_with_timing(self, tool_name: str, tool_func) -> tuple:
        """Run a tool and return (result, elapsed_time) tuple."""
        self._log_tool_start(tool_name)
        start_time = time.time()
        try:
            result = tool_func()
            elapsed_time = time.time() - start_time
            self._record_tool_cache_metadata(tool_name, result)
            self._log_tool_completion(tool_name, result, elapsed_time)
            return result, elapsed_time
        except Exception as exc:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Completed {tool_name}: FAIL (exception) elapsed={elapsed_time:.2f}s",
                exc_info=True,
            )
            raise ToolExecutionError(tool_name=tool_name, elapsed_time=elapsed_time, original_exception=exc) from exc

    def _normalize_cache_state(self, raw_mode: str | None) -> str | None:
        """Normalize internal cache mode labels for operator-facing logs."""
        if not isinstance(raw_mode, str) or not raw_mode.strip():
            return None
        normalized = raw_mode.strip().lower()
        mapping = {
            "cache_only": "utilized",
            "partial_cache": "partially_utilized",
            "cold_scan": "invalidated",
            "cache_hit": "utilized",
            "skipped_env": "skipped",
            "unknown": "none_found",
        }
        return mapping.get(normalized, "none_found")

    def _tool_cache_state_for_log(
        self, tool_name: str, allow_default_none_found: bool
    ) -> str | None:
        """Return normalized cache state for log lines."""
        if tool_name not in CACHE_AWARE_TOOLS:
            return None
        metadata = getattr(self, "_tool_cache_metadata", {})
        if isinstance(metadata, dict):
            tool_meta = metadata.get(tool_name, {})
            if isinstance(tool_meta, dict):
                state = self._normalize_cache_state(tool_meta.get("cache_mode"))
                if state:
                    return state
        if allow_default_none_found:
            return "none_found"
        return None

    def _log_tool_start(self, tool_name: str) -> None:
        """Log standardized tool start line (cache only when known at start)."""
        cache_state = self._tool_cache_state_for_log(
            tool_name, allow_default_none_found=False
        )
        if cache_state:
            logger.info(f"Starting {tool_name} (cache={cache_state})")
        else:
            logger.info(f"Starting {tool_name}")

    def _extract_issue_count(self, tool_name: str, result: Any) -> int | None:
        """Extract normalized issue count from tool result payload when available."""
        if tool_name in {"run_test_coverage", "generate_dev_tools_coverage"}:
            return None
        if not isinstance(result, dict):
            return None
        data = result.get("data")
        if isinstance(data, dict):
            summary = data.get("summary", {})
            if isinstance(summary, dict):
                value = summary.get("total_issues")
                if isinstance(value, bool):
                    return int(value)
                if isinstance(value, int):
                    return value
                if isinstance(value, float):
                    return int(value)
                if isinstance(value, str):
                    try:
                        return int(value)
                    except ValueError:
                        pass
        issues_found = result.get("issues_found")
        if isinstance(issues_found, bool):
            return 1 if issues_found else 0
        return None

    def _log_tool_completion(self, tool_name: str, result: Any, elapsed_time: float) -> None:
        """Log standardized tool completion line with status, issues, and cache mode."""
        success = bool(result)
        if isinstance(result, dict):
            success = bool(result.get("success", False))
        status = "PASS" if success else "FAIL"
        issue_count = self._extract_issue_count(tool_name, result)

        issue_fragment = (
            f" issues={issue_count}"
            if isinstance(issue_count, int)
            else ""
        )
        cache_state = self._tool_cache_state_for_log(
            tool_name, allow_default_none_found=True
        )
        if success and cache_state == "invalidated":
            cache_state = "created"
        cache_fragment = f" cache={cache_state}" if cache_state else ""
        detail_fragment = ""
        if tool_name == "generate_unused_imports_report" and success:
            detail_fragment = " detailed_report=development_docs/UNUSED_IMPORTS_REPORT.md"
        elif tool_name == "generate_test_coverage_report" and success:
            detail_fragment = " detailed_report=development_docs/TEST_COVERAGE_REPORT.md"
        elif tool_name == "generate_legacy_reference_report" and success:
            detail_fragment = " detailed_report=development_docs/LEGACY_REFERENCE_REPORT.md"
        pip_audit_fragment = ""
        if tool_name == "analyze_pip_audit" and isinstance(result, dict):
            pdata = result.get("data")
            if isinstance(pdata, dict):
                det = pdata.get("details", {})
                if isinstance(det, dict):
                    pstate = str(det.get("pip_audit_execution_state") or "").strip()
                    psub = det.get("pip_audit_subprocess_seconds")
                    if pstate == "requirements_lock_cache_hit":
                        pip_audit_fragment = " pip_audit=cache_hit(no_subprocess)"
                    elif pstate == "skipped_env":
                        pip_audit_fragment = " pip_audit=skipped_env"
                    elif pstate == "executed_subprocess" and isinstance(
                        psub, (int, float)
                    ):
                        pip_audit_fragment = f" pip_audit=subprocess={float(psub):.2f}s"
                    elif pstate == "error":
                        pip_audit_fragment = " pip_audit=error"
        message = (
            f"Completed {tool_name}: {status}{issue_fragment}"
            f"{cache_fragment} elapsed={elapsed_time:.2f}s{pip_audit_fragment}{detail_fragment}"
        )
        if success:
            logger.info(message)
        else:
            logger.warning(message)

    def _infer_cache_mode_from_hits_misses(self, hits: int, misses: int) -> str:
        """Infer cache mode from cache hit/miss counters."""
        total = hits + misses
        if total <= 0:
            return 'unknown'
        if hits > 0 and misses == 0:
            return 'cache_only'
        if hits > 0 and misses > 0:
            return 'partial_cache'
        return 'cold_scan'

    def _extract_coverage_cache_metadata(self, tool_name: str) -> dict[str, str]:
        """Extract cache mode metadata for coverage tools from coverage JSON metadata."""
        if tool_name == 'run_test_coverage':
            coverage_file = self.project_root / 'development_tools' / 'tests' / 'jsons' / 'coverage.json'
        elif tool_name == 'generate_dev_tools_coverage':
            coverage_file = self.project_root / 'development_tools' / 'tests' / 'jsons' / 'coverage_dev_tools.json'
        else:
            return {}
        if not coverage_file.exists():
            return {}
        try:
            with open(coverage_file, encoding='utf-8') as f:
                coverage_data = json.load(f)
            metadata = coverage_data.get('_metadata', {}) if isinstance(coverage_data, dict) else {}
            generated_by = str(metadata.get('generated_by', ''))
            generated_by_lower = generated_by.lower()
            if 'cache (no test execution)' in generated_by_lower:
                cache_mode = 'cache_only'
            elif 'cache merge' in generated_by_lower:
                cache_mode = 'partial_cache'
            elif 'pytest-cov' in generated_by_lower:
                cache_mode = 'cold_scan'
            else:
                cache_mode = 'unknown'
            return {
                'cache_mode': cache_mode,
                'source': 'coverage_json_metadata',
                'generated_by': generated_by,
            }
        except (OSError, json.JSONDecodeError):
            return {}

    def _record_tool_cache_metadata(self, tool_name: str, result=None) -> None:
        """Capture cache-mode metadata for selected tools and store in timing payload."""
        metadata = {}
        runtime_metadata = getattr(self, '_tool_cache_metadata', {})
        if isinstance(runtime_metadata, dict):
            existing = runtime_metadata.get(tool_name)
            if isinstance(existing, dict):
                metadata.update(existing)

        if isinstance(result, dict):
            direct_metadata = result.get('cache_metadata')
            if isinstance(direct_metadata, dict):
                metadata.update(direct_metadata)
            data = result.get('data')
            if isinstance(data, dict):
                cache_metadata = data.get('_cache_metadata') or data.get('cache_metadata')
                if isinstance(cache_metadata, dict):
                    metadata.update(cache_metadata)

                if tool_name == 'analyze_unused_imports':
                    details = data.get('details', {})
                    stats = details.get('stats', {}) if isinstance(details, dict) else {}
                    if isinstance(stats, dict):
                        hits = int(stats.get('cache_hits', 0) or 0)
                        misses = int(stats.get('cache_misses', 0) or 0)
                        files_scanned = int(stats.get('files_scanned', 0) or 0)
                        if files_scanned > 0 and misses == 0 and files_scanned >= hits:
                            misses = files_scanned - hits
                        metadata.setdefault('hits', hits)
                        metadata.setdefault('misses', misses)
                        metadata.setdefault('total_cache_checks', hits + misses)
                        metadata.setdefault('cache_mode', self._infer_cache_mode_from_hits_misses(hits, misses))

                if tool_name == 'analyze_legacy_references':
                    details = data.get('details', {})
                    cache_data = details.get('cache', {}) if isinstance(details, dict) else {}
                    if isinstance(cache_data, dict):
                        metadata.update(cache_data)

                if tool_name == 'analyze_pip_audit':
                    details = data.get('details', {})
                    if isinstance(details, dict):
                        state = details.get('pip_audit_execution_state')
                        if state:
                            metadata['pip_audit_execution_state'] = state
                        sub = details.get('pip_audit_subprocess_seconds')
                        if sub is not None:
                            with contextlib.suppress(TypeError, ValueError):
                                metadata['pip_audit_subprocess_seconds'] = float(sub)
                        if state == 'requirements_lock_cache_hit':
                            metadata.setdefault('cache_mode', 'cache_hit')
                        elif state == 'executed_subprocess':
                            metadata.setdefault('cache_mode', 'cold_scan')
                        elif state == 'skipped_env':
                            metadata.setdefault('cache_mode', 'skipped_env')

        if tool_name in {'run_test_coverage', 'generate_dev_tools_coverage'}:
            coverage_metadata = self._extract_coverage_cache_metadata(tool_name)
            if coverage_metadata:
                existing_mode = metadata.get('cache_mode')
                extracted_mode = coverage_metadata.get('cache_mode')
                if (
                    existing_mode
                    and existing_mode != 'unknown'
                    and extracted_mode == 'unknown'
                ):
                    coverage_metadata = {
                        key: value
                        for key, value in coverage_metadata.items()
                        if key != 'cache_mode'
                    }
                metadata.update(coverage_metadata)

        if tool_name == 'analyze_unused_imports' and not metadata:
            try:
                cached_unused = load_tool_result(
                    'analyze_unused_imports',
                    'imports',
                    project_root=self.project_root,
                )
                if isinstance(cached_unused, dict):
                    details = cached_unused.get('details', {})
                    stats = details.get('stats', {}) if isinstance(details, dict) else {}
                    if isinstance(stats, dict):
                        hits = int(stats.get('cache_hits', 0) or 0)
                        misses = int(stats.get('cache_misses', 0) or 0)
                        files_scanned = int(stats.get('files_scanned', 0) or 0)
                        if files_scanned > 0 and misses == 0 and files_scanned >= hits:
                            misses = files_scanned - hits
                        metadata = {
                            'cache_mode': self._infer_cache_mode_from_hits_misses(hits, misses),
                            'hits': hits,
                            'misses': misses,
                            'total_cache_checks': hits + misses,
                            'source': 'cached_tool_result',
                        }
            except Exception:
                pass

        if metadata:
            self._tool_cache_metadata[tool_name] = metadata

    def _format_coverage_mode_summary(self) -> str:
        """Build concise coverage mode summary for final audit logs."""
        entries = []
        metadata = getattr(self, '_tool_cache_metadata', {})
        if not isinstance(metadata, dict):
            return ""
        for tool_name in ('run_test_coverage', 'generate_dev_tools_coverage'):
            tool_meta = metadata.get(tool_name, {})
            if not isinstance(tool_meta, dict) or not tool_meta:
                continue
            cache_mode = tool_meta.get('cache_mode', 'unknown')
            reason = tool_meta.get('invalidation_reason', 'unknown')
            entries.append(f"{tool_name}={cache_mode} ({reason})")
        return "; ".join(entries)

    def _format_cache_mode_summary(self, tool_names: list[str]) -> str:
        """Build concise cache mode summary for selected tools."""
        metadata = getattr(self, '_tool_cache_metadata', {})
        if not isinstance(metadata, dict):
            return ""
        parts = []
        for tool_name in tool_names:
            tool_meta = metadata.get(tool_name, {})
            if not isinstance(tool_meta, dict):
                continue
            cache_mode = tool_meta.get('cache_mode')
            if not cache_mode:
                continue
            details = []
            if 'hits' in tool_meta and 'misses' in tool_meta:
                details.append(f"hits={tool_meta.get('hits', 0)}")
                details.append(f"misses={tool_meta.get('misses', 0)}")
            elif 'cache_hits' in tool_meta and 'cache_misses' in tool_meta:
                details.append(f"hits={tool_meta.get('cache_hits', 0)}")
                details.append(f"misses={tool_meta.get('cache_misses', 0)}")
            detail_suffix = f" [{', '.join(details)}]" if details else ""
            parts.append(f"{tool_name}={cache_mode}{detail_suffix}")
        return "; ".join(parts)
    
    def _run_full_audit_tools(self) -> bool:
        """Run Tier 3 tools: Full audit (comprehensive analysis, >10s per tool or groups with >10s tools).

        Note: Tools moved here based on execution time (>10s) while respecting dependencies:
        - Coverage: exactly one scope per audit — main ``run_test_coverage`` *or* ``generate_dev_tools_coverage``
          (see V5 §1.9); they are never both scheduled in the same pass.
        - Coverage-dependent tools run after that coverage step; ``generate_test_coverage_report`` runs only
          after main coverage (it reads repo ``coverage.json``).
        - Legacy group: analyze_legacy_references (62.11s) is >10s, so entire group stays in Tier 3
        - Static analysis group: ruff and pyright run in parallel with coverage/legacy groups
        """
        successful = []
        failed = []
        
        # Tier 3 tool groups from canonical audit_tiers (single source of truth).
        # Coverage groups run heavy pytest workloads; we run them concurrently for throughput
        # and apply worker caps in command handlers to avoid CPU oversubscription.
        (
            tier3_coverage_main_group,
            tier3_coverage_dev_tools_group,
            tier3_coverage_dependent_group,
            tier3_legacy_group,
            tier3_static_analysis_group,
        ) = get_tier3_groups(self)

        coverage_run_groups: list[list[tuple[str, Any]]] = []
        if tier3_coverage_main_group:
            coverage_run_groups.append(tier3_coverage_main_group)
        if tier3_coverage_dev_tools_group:
            coverage_run_groups.append(tier3_coverage_dev_tools_group)
        if not coverage_run_groups:
            logger.error("Tier 3 has no coverage group for this audit scope; aborting Tier 3.")
            return False

        # Independent groups that can run in parallel with each other.
        if os.name == "nt":
            # Windows guardrail: when both coverage arms existed historically, they ran in one sequential batch.
            # With scope split (V5 §1.9) there is at most one coverage arm; still merge for a single worker slot.
            merged_coverage: list[tuple[str, Any]] = []
            for grp in coverage_run_groups:
                merged_coverage.extend(grp)
            logger.info(
                "Windows Tier 3 coverage: running coverage tool group sequentially within one worker slot."
            )
            tier3_parallel_groups = [
                merged_coverage,
                tier3_legacy_group,
                tier3_static_analysis_group,
            ]
        else:
            tier3_parallel_groups = coverage_run_groups + [
                tier3_legacy_group,
                tier3_static_analysis_group,
            ]
        
        # Run coverage and legacy groups in parallel (each group runs its tools sequentially)
        if tier3_parallel_groups:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import time
            
            logger.debug(f"Running {len(tier3_parallel_groups)} independent tool groups in parallel...")
            
            # Track parallel execution start time for accurate wall-clock measurement
            parallel_start_time = time.time()
            
            def run_tool_group(group_tools):
                """Run a group of tools sequentially and return results."""
                group_results = {}
                for tool_name, tool_func in group_tools:
                    if audit_signal_state.audit_sigint_requested():
                        raise KeyboardInterrupt()
                    try:
                        result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                        group_results[tool_name] = (result, elapsed_time)
                    except KeyboardInterrupt:
                        # Double-tap: first SIGINT/propagation ignored, second within 2s stops (align with run_tests.py)
                        if audit_signal_state.record_audit_keyboard_interrupt():
                            self._internal_interrupt_detected = True
                            logger.error(
                                f"  - {tool_name} raised KeyboardInterrupt during Tier 3 group execution; "
                                "recording tool failure and continuing audit finalization."
                            )
                        else:
                            logger.warning(
                                "SIGINT received - ignoring. Press Ctrl+C again within 2s to stop the audit."
                            )
                        group_results[tool_name] = (
                            {
                                "success": False,
                                "error": (
                                    "Tool interrupted by KeyboardInterrupt "
                                    "(SIGINT/control event propagated from subprocess)"
                                ),
                                "returncode": 130,
                                "interrupted": True,
                            },
                            0.0,
                        )
                    except Exception as exc:
                        logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                        elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                        group_results[tool_name] = ({'success': False, 'error': str(exc)}, elapsed_time)
                return group_results
            
            def _apply_group_results(
                group_results: dict[str, Any],
                group_wall_clock: float,
                successful_tools: list[str],
                failed_tools: list[str],
                parallel_times: dict[str, float],
            ) -> None:
                """Apply completed group results into orchestration state."""
                for tool_name, (result, elapsed_time) in group_results.items():
                    self._tool_timings[tool_name] = elapsed_time
                    parallel_times[tool_name] = group_wall_clock
                    logger.debug(
                        f"  - {tool_name} completed in {elapsed_time:.2f}s "
                        f"(wall-clock: {group_wall_clock:.2f}s)"
                    )
                    if isinstance(result, dict):
                        success = result.get('success', False)
                        if 'data' in result:
                            self._extract_key_info(tool_name, result)
                    else:
                        success = bool(result)
                    self._record_tool_cache_metadata(tool_name, result)
                    if success:
                        self._tool_execution_status[tool_name] = 'success'
                        successful_tools.append(tool_name)
                        self._tools_run_in_current_tier.add(tool_name)
                    else:
                        self._tool_execution_status[tool_name] = 'failed'
                        failed_tools.append(tool_name)
                        logger.warning(
                            f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data"
                        )
                        if isinstance(result, dict) and result.get("error"):
                            _err = (result.get("error") or "").strip()
                            if _err:
                                logger.warning(f"  {tool_name} error detail: {_err[:800]}")

            self._tier3_coverage_concurrent = True
            self._tier3_coverage_serialized = os.name == "nt"
            executor = ThreadPoolExecutor(max_workers=len(tier3_parallel_groups))
            try:
                future_to_group = {
                    executor.submit(run_tool_group, group): i
                    for i, group in enumerate(tier3_parallel_groups)
                }

                # Track when all parallel groups complete for accurate timing
                parallel_group_times = {}
                processed_futures = set()
                try:
                    for future in as_completed(future_to_group):
                        try:
                            group_results = future.result()
                        except KeyboardInterrupt:
                            if audit_signal_state.record_audit_keyboard_interrupt():
                                self._internal_interrupt_detected = True
                                if "tier3_parallel_execution" not in failed:
                                    failed.append("tier3_parallel_execution")
                                logger.error(
                                    "Tier 3 worker group future raised KeyboardInterrupt; "
                                    "continuing with failure state."
                                )
                            else:
                                logger.warning(
                                    "SIGINT received - ignoring. Press Ctrl+C again within 2s to stop the audit."
                                )
                            if audit_signal_state.audit_sigint_requested():
                                self._internal_interrupt_detected = True
                                if "tier3_parallel_execution" not in failed:
                                    failed.append("tier3_parallel_execution")
                                break
                            continue
                        processed_futures.add(future)
                        group_end_time = time.time()
                        group_wall_clock = group_end_time - parallel_start_time
                        _apply_group_results(
                            group_results=group_results,
                            group_wall_clock=group_wall_clock,
                            successful_tools=successful,
                            failed_tools=failed,
                            parallel_times=parallel_group_times,
                        )
                        if audit_signal_state.audit_sigint_requested():
                            self._internal_interrupt_detected = True
                            if "tier3_parallel_execution" not in failed:
                                failed.append("tier3_parallel_execution")
                            break
                except KeyboardInterrupt:
                    def _is_done(fut) -> bool:
                        try:
                            return bool(fut.done())
                        except Exception:
                            return False

                    all_done = all(_is_done(fut) for fut in future_to_group)
                    if all_done:
                        # Drain any completed futures not yet applied so tool timings remain complete.
                        for fut in future_to_group:
                            if fut in processed_futures or not _is_done(fut):
                                continue
                            try:
                                drained_results = fut.result()
                            except Exception:
                                continue
                            _apply_group_results(
                                group_results=drained_results,
                                group_wall_clock=time.time() - parallel_start_time,
                                successful_tools=successful,
                                failed_tools=failed,
                                parallel_times=parallel_group_times,
                            )
                            processed_futures.add(fut)
                        logger.info(
                            "Tier 3 parallel completion loop received KeyboardInterrupt "
                            "after all futures completed; treated as non-blocking signal noise."
                        )
                    else:
                        if audit_signal_state.record_audit_keyboard_interrupt():
                            self._internal_interrupt_detected = True
                            logger.error(
                                "Tier 3 parallel completion loop interrupted by KeyboardInterrupt; "
                                "marking Tier 3 as failed and continuing finalization."
                            )
                            if "tier3_parallel_execution" not in failed:
                                failed.append("tier3_parallel_execution")
                        else:
                            logger.warning(
                                "SIGINT received - ignoring. Press Ctrl+C again within 2s to stop the audit."
                            )
            finally:
                self._tier3_coverage_concurrent = False
                self._tier3_coverage_serialized = False
                # Avoid blocking on worker join when exiting due to interrupt (prevents "Exception ignored on threading shutdown")
                executor.shutdown(wait=not getattr(self, "_internal_interrupt_detected", False))
            
            # Log parallel execution summary
            if parallel_group_times:
                max_parallel_time = max(parallel_group_times.values())
                sum_individual_times = sum(self._tool_timings.get(name, 0) for name in parallel_group_times)
                time_saved = sum_individual_times - max_parallel_time
                if time_saved > 1.0:  # Only log if significant time saved
                    logger.info(f"Parallel execution saved ~{time_saved:.1f}s (wall-clock: {max_parallel_time:.1f}s vs sequential: {sum_individual_times:.1f}s)")
        
        # Run coverage-dependent tools sequentially (after the coverage step for this audit scope).
        logger.debug("Running coverage-dependent tools (sequential, after coverage completion)...")
        for tool_name, tool_func in tier3_coverage_dependent_group:
            if audit_signal_state.audit_sigint_requested():
                self._internal_interrupt_detected = True
                failed.append(tool_name)
                break
            try:
                result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                self._tool_timings[tool_name] = elapsed_time
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    self._tool_execution_status[tool_name] = 'success'
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                else:
                    self._tool_execution_status[tool_name] = 'failed'
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
                    if isinstance(result, dict) and result.get("error"):
                        _err = (result.get("error") or "").strip()[:800]
                        if _err:
                            logger.warning(f"  {tool_name} error detail: {_err}")
            except KeyboardInterrupt:
                self._internal_interrupt_detected = True
                elapsed_time = 0.0
                self._tool_timings[tool_name] = elapsed_time
                self._tool_execution_status[tool_name] = 'failed'
                failed.append(tool_name)
                logger.error(
                    f"  - {tool_name} raised KeyboardInterrupt during Tier 3 dependent execution; "
                    "recording failure and continuing."
                )
                logger.warning(
                    f"[TOOL FAILURE] {tool_name} interrupted by control event - reports may use cached/fallback data"
                )
            except Exception as exc:
                elapsed_time = exc.elapsed_time if isinstance(exc, ToolExecutionError) else 0.0
                self._tool_timings[tool_name] = elapsed_time
                self._tool_execution_status[tool_name] = 'failed'
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")

        if not failed:
            self._finalize_tier3_audit_scope()

        if failed:
            logger.warning(f"Tier 3 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            tier3_state = self._effective_tier3_state()
            if tier3_state == "test_failures":
                logger.warning(
                    f"Tier 3 completed with test failures ({len(successful)} tools)"
                )
            elif tier3_state in {"crashed", "infra_cleanup_error"}:
                logger.warning(
                    f"Tier 3 completed with crashes/infrastructure issues ({len(successful)} tools)"
                )
            else:
                logger.info(f"Tier 3 completed successfully ({len(successful)} tools)")

        return len(failed) == 0
    
    def _save_additional_tool_results(self):
        """Save results from additional tools to the cached file."""
        try:
            from ..audit_storage_scope import scoped_analysis_detailed_path

            audit_cfg = getattr(self, "audit_config", None) or {}
            configured = audit_cfg.get(
                "results_file", "development_tools/reports/analysis_detailed_results.json"
            )
            results_file = scoped_analysis_detailed_path(
                self.project_root, configured_relative=configured
            )
            if results_file.exists():
                with open(results_file, encoding='utf-8') as f:
                    cached_data = json.load(f)
            else:
                cached_data = {'results': {}}
            
            if hasattr(self, 'legacy_cleanup_summary') and self.legacy_cleanup_summary:
                cached_data['results']['fix_legacy_references'] = {
                    'success': True,
                    'data': self.legacy_cleanup_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            if hasattr(self, 'validation_results') and self.validation_results:
                cached_data['results']['analyze_ai_work'] = {
                    'success': True,
                    'data': self.validation_results,
                    'timestamp': datetime.now().isoformat()
                }
            
            if hasattr(self, 'system_signals') and self.system_signals:
                cached_data['results']['analyze_system_signals'] = {
                    'success': True,
                    'data': self.system_signals,
                    'timestamp': datetime.now().isoformat()
                }
            
            if hasattr(self, 'docs_sync_summary') and self.docs_sync_summary:
                cached_data['results']['analyze_documentation_sync'] = {
                    'success': True,
                    'data': self.docs_sync_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            if 'analyze_documentation' in self.results_cache:
                analyze_docs_data = self.results_cache['analyze_documentation']
                cached_data['results']['analyze_documentation'] = {
                    'success': True,
                    'data': analyze_docs_data,
                    'timestamp': datetime.now().isoformat()
                }
            
            create_output_file(str(results_file), json.dumps(cached_data, indent=2), project_root=self.project_root)
        except Exception as e:
            logger.warning(f"Failed to save additional tool results: {e}")
    
    def _reload_all_cache_data(self):
        """Reload cache data from disk, merging with in-memory results from current audit run.

        We merge (update from disk) instead of clear-then-replace so that tools which ran
        this audit but did not write a file (e.g. parse failed, or no summary) keep their
        in-memory results for report generation. Prevents [DATA SOURCE] warnings for
        analyze_module_dependencies and others when disk is missing a result file.
        """
        try:
            if not hasattr(self, 'results_cache') or self.results_cache is None:
                self.results_cache = {}
            
            # Skip loading all results in test directories to prevent memory issues
            # Tests use temp_project_copy which should have minimal/no results files
            # Loading all results is expensive and unnecessary for tests
            project_root_str = str(self.project_root.resolve())
            is_test_dir = self._is_test_directory(self.project_root)
            
            # Enhanced logging for memory leak investigation (DEBUG level to reduce verbosity in production)
            if is_test_dir:
                logger.debug(
                    f"[MEMORY-LEAK-PREVENTION] Skipping _reload_all_cache_data() in test directory\n"
                    f"  project_root: {project_root_str}\n"
                    f"  is_test_directory check: True"
                )
                return
            else:
                logger.debug(
                    f"[MEMORY-LEAK-PREVENTION] NOT a test directory, proceeding with _reload_all_cache_data()\n"
                    f"  project_root: {project_root_str}\n"
                    f"  is_test_directory check: False"
                )
            
            all_results = get_all_tool_results(project_root=self.project_root)
            if all_results:
                logger.debug(
                    f"[MEMORY-LEAK-PREVENTION] Loading {len(all_results)} tool results from disk\n"
                    f"  project_root: {project_root_str}\n"
                    f"  tools: {list(all_results.keys())[:5]}{'...' if len(all_results) > 5 else ''}"
                )
                for tool_name, result_data in all_results.items():
                    if isinstance(result_data, dict):
                        tool_data = result_data.get('data', result_data)
                        self.results_cache[tool_name] = tool_data
                        if tool_name == 'analyze_documentation_sync' and isinstance(tool_data, dict):
                            self.docs_sync_summary = tool_data
                        if tool_name == 'analyze_legacy_references' and isinstance(tool_data, dict):
                            self.legacy_cleanup_summary = tool_data
            else:
                logger.debug(f"[MEMORY-LEAK-PREVENTION] No tool results found (project_root: {project_root_str})")
            
            # CRITICAL: Also skip loading analysis_detailed_results.json in test directories
            # This file can be very large and causes memory leaks in parallel test execution
            from ..audit_storage_scope import scoped_analysis_detailed_path

            audit_cfg = getattr(self, "audit_config", None) or {}
            configured = audit_cfg.get(
                "results_file", "development_tools/reports/analysis_detailed_results.json"
            )
            results_file = scoped_analysis_detailed_path(
                self.project_root, configured_relative=configured
            )
            is_test_dir_check = self._is_test_directory(self.project_root)
            if results_file.exists() and not is_test_dir_check:
                file_size_mb = results_file.stat().st_size / (1024 * 1024)
                logger.debug(
                    f"[MEMORY-LEAK-PREVENTION] Loading analysis_detailed_results.json\n"
                    f"  file: {results_file}\n"
                    f"  size: {file_size_mb:.2f} MB\n"
                    f"  project_root: {project_root_str}"
                )
                with open(results_file, encoding='utf-8') as f:
                    cached_data = json.load(f)
                if 'results' in cached_data:
                    for tool_name, tool_data in cached_data['results'].items():
                        if tool_name not in self.results_cache and 'data' in tool_data:
                            self.results_cache[tool_name] = tool_data['data']
                if not self.docs_sync_summary and 'analyze_documentation_sync' in cached_data.get('results', {}):
                    doc_sync_data = cached_data['results']['analyze_documentation_sync']
                    if 'data' in doc_sync_data:
                        self.docs_sync_summary = doc_sync_data['data']
                if not hasattr(self, 'legacy_cleanup_summary') or not self.legacy_cleanup_summary:
                    if 'analyze_legacy_references' in cached_data.get('results', {}):
                        legacy_data = cached_data['results']['analyze_legacy_references']
                        if 'data' in legacy_data:
                            self.legacy_cleanup_summary = legacy_data['data']
                if not hasattr(self, 'dev_tools_coverage_results') or not self.dev_tools_coverage_results:
                    self._load_dev_tools_coverage()
                if 'analyze_module_dependencies' in cached_data.get('results', {}):
                    dep_data = cached_data['results']['analyze_module_dependencies']
                    if 'data' in dep_data:
                        self.module_dependency_summary = dep_data['data']
        except Exception as e:
            logger.debug(f"Failed to reload cache data: {e}")
    
    def _is_test_directory(self, path: Path) -> bool:
        """Check if path is within a test directory to avoid loading large result files.
        
        This is critical for preventing memory leaks in parallel test execution.
        """
        try:
            path_str = str(path.resolve()).replace('\\', '/').lower()
            
            # Check for Windows temp directories (most common case for pytest-xdist)
            # Windows temp dirs are typically: C:\Users\...\AppData\Local\Temp\...
            if 'appdata' in path_str and ('temp' in path_str or 'tmp' in path_str):
                return True
            
            # Check for pytest temp directories (pytest-xdist creates these)
            if 'pytest' in path_str and ('temp' in path_str or 'tmp' in path_str):
                return True
            
            # Check for common temp directory patterns
            test_indicators = [
                "/tmp",  # nosec B108 — path substring markers for test/temp detection
                "/temp",  # nosec B108
                '/tests/', '/test/',  # Test directories
                'tests/data/', 'tests/fixtures/', 'tests/temp/',
                'demo_project',  # Demo project used in tests
                'pytest-', 'pytest_of_',  # pytest temp directories
            ]
            if any(indicator in path_str for indicator in test_indicators):
                return True
            
            # Additional check: if path contains a tempfile pattern (tmpXXXXXX)
            import re
            return bool(re.search(r'[\\/]tmp[a-z0-9]{6,}[\\/]', path_str))
        except Exception as e:
            # If we can't determine, be conservative and assume it's not a test directory
            # But log it so we can debug
            logger.debug(f"Error checking if path is test directory ({path}): {e}")
            return False
    
    def _save_audit_results_aggregated(self, tier: int):
        """Save aggregated audit results from all tool result files."""
        # In test directories, create minimal file without loading all results from disk
        # This prevents memory issues while still creating the file tests expect
        is_test_dir = self._is_test_directory(self.project_root)
        
        if is_test_dir:
            logger.debug(f"Creating minimal analysis_detailed_results.json in test directory (project_root: {self.project_root})")
            # Use only results_cache data (from mocked tools) - don't load from disk
            enhanced_results = {}
            successful = []
            failed = []
            
            for tool_name, data in self.results_cache.items():
                enhanced_results[tool_name] = {
                    'success': True,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
                successful.append(tool_name)
        else:
            # Real project: Load all results from disk (normal behavior)
            # Retry logic to handle race conditions where files may not be written yet
            # This is especially important in test scenarios where file system operations
            # may not be immediately synchronized
            import time
            all_results = {}
            max_retries = 3
            initial_delay = 0.05
            
            for attempt in range(max_retries):
                all_results = get_all_tool_results(project_root=self.project_root)
                # If we found results or this is the last attempt, proceed
                if all_results or attempt == max_retries - 1:
                    break
                # Small delay before retry to allow file system to sync
                time.sleep(initial_delay * (attempt + 1))
            
            # Log warning if no results found (but don't fail - some tools may not produce results)
            if not all_results:
                logger.debug("No tool results found during aggregation (this may be normal if no tools ran)")
            
            enhanced_results = {}
            successful = []
            failed = []
            
            for tool_name, result_data in all_results.items():
                if isinstance(result_data, dict):
                    tool_data = result_data.get('data', result_data)
                    # Enforce standard result format in the aggregation cache.
                    try:
                        from ..result_format import normalize_to_standard_format

                        tool_data = normalize_to_standard_format(tool_name, tool_data)
                    except ValueError as e:
                        enhanced_results[tool_name] = {
                            'success': False,
                            'data': {},
                            'error': str(e),
                        }
                        failed.append(tool_name)
                        continue
                    enhanced_results[tool_name] = {
                        'success': True,
                        'data': tool_data,
                        'timestamp': result_data.get('timestamp', datetime.now().isoformat())
                    }
                    successful.append(tool_name)
                else:
                    enhanced_results[tool_name] = {
                        'success': False,
                        'data': {},
                        'error': 'Invalid result format'
                    }
                    failed.append(tool_name)
            
            # Also include results_cache data (from current audit run)
            for tool_name, data in self.results_cache.items():
                if tool_name not in enhanced_results:
                    try:
                        from ..result_format import normalize_to_standard_format

                        data = normalize_to_standard_format(tool_name, data)
                    except ValueError:
                        continue
                    enhanced_results[tool_name] = {
                        'success': True,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
                    if tool_name not in successful:
                        successful.append(tool_name)
        
        if tier == 1:
            source_cmd = 'python development_tools/run_development_tools.py audit --quick'
        elif tier == 3:
            source_cmd = 'python development_tools/run_development_tools.py audit --full'
        else:
            source_cmd = 'python development_tools/run_development_tools.py audit'
        
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamp_iso = datetime.now().isoformat()
        audit_data = {
            'generated_by': 'run_development_tools.py - AI Development Tools Runner',
            'last_generated': timestamp_str,
            'source': source_cmd,
            'audit_tier': tier,
            'note': 'This file is auto-generated. Do not edit manually.',
            'timestamp': timestamp_iso,
            'successful': successful,
            'failed': failed,
            'results': enhanced_results
        }
        
        audit_cfg = getattr(self, "audit_config", None) or {}
        from ..audit_storage_scope import scoped_analysis_detailed_path

        configured = audit_cfg.get(
            "results_file", "development_tools/reports/analysis_detailed_results.json"
        )
        scoped_results = scoped_analysis_detailed_path(
            self.project_root, configured_relative=configured
        )
        try:
            results_file_path = str(
                scoped_results.relative_to(self.project_root.resolve())
            )
        except ValueError:
            results_file_path = str(scoped_results)
        # Use relative path for create_output_file to ensure proper path resolution
        # create_output_file handles project_root resolution internally
        try:
            # Always create the file, even if results are empty (for test scenarios with mocked tools)
            json_content = json.dumps(audit_data, indent=2)
            created_file = create_output_file(results_file_path, json_content, project_root=self.project_root)
            # Ensure file is flushed to disk and verify it exists
            if created_file:
                # Wait a moment for file system to sync (especially important on Windows)
                import time
                time.sleep(0.05)
                if created_file.exists() and created_file.stat().st_size > 0:
                    logger.debug(f"Saved aggregated audit results to {created_file}")
                else:
                    logger.warning(f"File {created_file} was created but doesn't exist or is empty. Path: {created_file.absolute()}")
            else:
                logger.error(f"create_output_file returned None for {results_file_path}")
        except Exception as e:
            logger.error(f"Failed to create analysis_detailed_results.json: {e}", exc_info=True)
            # Don't raise - allow audit to complete even if results file can't be saved
            # This prevents test failures when file system operations fail
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report."""
        # This method can be implemented if needed
        # For now, audit reports are generated via the status document methods
        pass
    
    def _check_and_trim_changelog_entries(self) -> None:
        """Check and trim AI_CHANGELOG entries to prevent bloat."""
        try:
            from development_tools.docs.fix_version_sync import (
                check_changelog_entry_count,
                trim_ai_changelog_entries,
            )
        except Exception as exc:
            logger.warning(f"   Changelog check: Tooling unavailable (skipping trim): {exc}")
            return

        try:
            check_result = check_changelog_entry_count(max_entries=15)
        except Exception as exc:
            logger.warning(f"   Changelog check failed: {exc}")
            return

        if not isinstance(check_result, dict):
            logger.warning("   Changelog check failed: unexpected result shape")
            return

        status = str(check_result.get("status", "unknown")).lower()
        message = check_result.get("message")
        if message:
            logger.debug(f"   Changelog check: {message}")

        if status in {"ok", "pass"}:
            return
        if status not in {"fail", "warning"}:
            logger.warning(f"   Changelog check failed: status={status}")
            return

        try:
            trim_result = trim_ai_changelog_entries(days_to_keep=30, max_entries=15)
        except Exception as exc:
            logger.warning(f"   Changelog trim failed: {exc}")
            return

        if not isinstance(trim_result, dict):
            logger.warning("   Changelog trim failed: unexpected result shape")
            return

        if trim_result.get("error"):
            logger.warning(f"   Changelog trim failed: {trim_result['error']}")
            return

        trimmed = int(trim_result.get("trimmed_entries", 0) or 0)
        kept = int(trim_result.get("kept_entries", 0) or 0)
        archive_created = bool(trim_result.get("archive_created", False))

        if trimmed > 0:
            logger.info(f"   Trimmed {trimmed} old changelog entries")
        else:
            logger.info("   Changelog trim: no old entries needed trimming")

        logger.info(f"   Changelog entries kept: {kept}")
        if archive_created:
            logger.info("   Created archive: archive/AI_CHANGELOG_ARCHIVE.md")
    
    def _validate_referenced_paths(self) -> None:
        """Validate that all referenced paths in documentation exist."""
        try:
            from development_tools.docs.fix_version_sync import validate_referenced_paths
            result = validate_referenced_paths(project_root=str(self.project_root))
            status = result.get('status') if isinstance(result, dict) else None
            message = result.get('message') if isinstance(result, dict) else None
            if isinstance(result, dict):
                self.path_validation_result = result
            if status == 'ok':
                logger.debug(f"   Path validation: {message}")
            elif status == 'fail':
                issues = result.get('issues_found', 'unknown') if isinstance(result, dict) else 'unknown'
                logger.debug(f"   Path validation: {message}")
                logger.debug(f"   Found {issues} path issues")
        except Exception as exc:
            logger.warning(f"   Path validation failed: {exc}")
            self.path_validation_result = None
    
    def _check_documentation_quality(self) -> None:
        """Check for documentation duplicates and placeholder content."""
        try:
            data = self.results_cache.get('analyze_documentation')
            if not isinstance(data, dict):
                result = self.run_analyze_documentation()
                data = result.get('data') if isinstance(result, dict) else None
                if isinstance(data, dict):
                    self.results_cache['analyze_documentation'] = data
            if isinstance(data, dict):
                duplicates = data.get('duplicates') or []
                placeholders = data.get('placeholders') or []
                if duplicates:
                    logger.warning(f"   Documentation quality: Found {len(duplicates)} verbatim duplicates")
                else:
                    logger.debug("   Documentation quality: No verbatim duplicates found")
                if placeholders:
                    logger.warning(f"   Documentation quality: Found {len(placeholders)} files with placeholders")
                else:
                    logger.debug("   Documentation quality: No placeholder content found")
        except Exception as exc:
            logger.warning(f"   Documentation quality check failed: {exc}")
    
    def _check_ascii_compliance(self) -> None:
        """Check for non-ASCII characters using standardized tool output."""
        try:
            result = self.run_script("analyze_ascii_compliance", "--json")
            parsed = self._parse_ascii_compliance_output(result.get("output", ""))
            if (
                not isinstance(parsed, dict)
                or not isinstance(parsed.get("summary"), dict)
                or not isinstance(parsed.get("details"), dict)
            ):
                logger.warning("   ASCII compliance check returned non-standard data")
                return

            # Keep cache/storage in sync with the final quality check.
            try:
                save_tool_result(
                    "analyze_ascii_compliance",
                    "docs",
                    parsed,
                    project_root=self.project_root,
                )
            except Exception as exc:
                logger.debug(f"Failed to persist ascii compliance result: {exc}")

            if hasattr(self, "results_cache") and isinstance(self.results_cache, dict):
                self.results_cache["analyze_ascii_compliance"] = parsed

            summary = parsed.get("summary", {})
            total_issues = int(summary.get("total_issues", 0) or 0)
            files_with_issues = int(summary.get("files_affected", 0) or 0)
            current_doc_sync = (
                self.docs_sync_summary
                if isinstance(getattr(self, "docs_sync_summary", None), dict)
                else {}
            )
            doc_sync_summary = (
                current_doc_sync.get("summary", {})
                if isinstance(current_doc_sync.get("summary"), dict)
                else {}
            )
            doc_sync_details = (
                current_doc_sync.get("details", {})
                if isinstance(current_doc_sync.get("details"), dict)
                else {}
            )
            if total_issues == 0:
                logger.debug("   ASCII compliance: All documentation files use ASCII-only characters")
                doc_sync_details["ascii_issues"] = 0
            else:
                logger.debug(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {files_with_issues} files")
                doc_sync_details["ascii_issues"] = files_with_issues
            recalculated_total = (
                int(doc_sync_details.get("paired_doc_issues", 0) or 0)
                + int(doc_sync_details.get("path_drift_issues", 0) or 0)
                + int(doc_sync_details.get("ascii_issues", 0) or 0)
                + int(doc_sync_details.get("heading_numbering_issues", 0) or 0)
                + int(doc_sync_details.get("missing_address_issues", 0) or 0)
                + int(doc_sync_details.get("unconverted_link_issues", 0) or 0)
            )
            doc_sync_summary["total_issues"] = recalculated_total
            doc_sync_summary["status"] = "FAIL" if recalculated_total > 0 else "PASS"
            doc_sync_summary["files_affected"] = int(
                doc_sync_summary.get("files_affected", 0) or 0
            )
            self.docs_sync_summary = {
                "summary": doc_sync_summary,
                "details": doc_sync_details,
            }
        except Exception as exc:
            logger.warning(f"   ASCII compliance check failed: {exc}")
    
    def _get_expected_tools_for_tier(self, tier: int) -> list[str]:
        """Return expected tool names for a given audit tier (from canonical audit_tiers)."""
        dev_only = bool(getattr(self, "dev_tools_only_mode", False))
        if tier != 3:
            return audit_tiers_get_expected_tools_for_tier(tier, dev_tools_only=dev_only)
        base = audit_tiers_get_expected_tools_for_tier(2, dev_tools_only=dev_only)
        if dev_only:
            return base + get_tier3_tool_names_dev_tools_only()
        return base + get_tier3_tool_names_full_repo()

    def _save_timing_data(self, tier: int, audit_success: bool) -> None:
        """Save timing data to a JSON file for analysis."""
        try:
            from ..audit_storage_scope import scoped_tool_timings_path

            timing_file = scoped_tool_timings_path(self.project_root)
            timing_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing timing data (scoped path only; see V5 §7.16)
            existing_data: dict[str, Any] = {}
            if timing_file.exists():
                try:
                    with open(timing_file, encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    existing_data = {}
            
            def _to_human_timestamp(raw_value: object) -> str:
                """Normalize timestamps to human-readable format."""
                if isinstance(raw_value, str) and raw_value.strip():
                    candidate = raw_value.strip()
                    for parser in (
                        lambda v: datetime.strptime(v, "%Y-%m-%d %H:%M:%S"),
                        lambda v: datetime.fromisoformat(v.replace("Z", "")),
                    ):
                        try:
                            return parser(candidate).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            continue
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Normalize any pre-existing run timestamps.
            for existing_run in existing_data.get("runs", []) if isinstance(existing_data.get("runs"), list) else []:
                if isinstance(existing_run, dict):
                    existing_run["timestamp"] = _to_human_timestamp(
                        existing_run.get("timestamp")
                    )

            # Add new timing entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tier_name = {1: 'quick', 2: 'standard', 3: 'full'}.get(tier, 'unknown')
            tool_timings = self._tool_timings.copy()
            expected_tools = self._get_expected_tools_for_tier(tier)
            observed_tools = sorted(tool_timings.keys())
            missing_expected_tools = sorted(set(expected_tools) - set(observed_tools))
            failed_tools = sorted(
                tool_name
                for tool_name, status in getattr(self, '_tool_execution_status', {}).items()
                if status == 'failed'
            )
            wall_clock_total = None
            if hasattr(self, '_audit_wall_clock_start'):
                wall_clock_total = time.perf_counter() - self._audit_wall_clock_start
            sum_tool_times = sum(tool_timings.values())
            
            if 'runs' not in existing_data:
                existing_data['runs'] = []
            
            existing_data['runs'].append({
                'timestamp': timestamp,
                'tier': tier_name,
                'tier_number': tier,
                'audit_success': audit_success,
                'tool_timings': tool_timings,
                # Keep aggregate duration for quick dashboard/trend views.
                'total_time': sum_tool_times,
                'sum_tool_durations_seconds': sum_tool_times,
                'wall_clock_total_seconds': wall_clock_total,
                'parallelism_gain_seconds': (sum_tool_times - wall_clock_total) if wall_clock_total is not None else None,
                'expected_tools': expected_tools,
                'observed_tools': observed_tools,
                'missing_expected_tools': missing_expected_tools,
                'failed_tools': failed_tools,
                'tool_execution_status': getattr(self, '_tool_execution_status', {}).copy(),
                'tool_cache_metadata': getattr(self, '_tool_cache_metadata', {}).copy(),
            })
            
            # Keep only last 50 runs
            if len(existing_data['runs']) > 50:
                existing_data['runs'] = existing_data['runs'][-50:]
            
            # Save updated timing data
            with open(timing_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save timing data: {e}")
    
    def _sync_todo_with_changelog(self) -> None:
        """Analyze TODO.md for completed entries and report dry-run cleanup data."""
        try:
            from development_tools.docs.fix_version_sync import sync_todo_with_changelog
            result = sync_todo_with_changelog()
            if isinstance(result, dict):
                self.todo_sync_result = result
                status = result.get('status')
                if status == 'ok':
                    completed_count = result.get('completed_entries', 0) or 0
                    summary = result.get('summary', {}) if isinstance(result.get('summary'), dict) else {}
                    auto_count = summary.get('auto_cleanable_count', 0)
                    manual_count = summary.get('manual_review_count', 0)
                    if completed_count > 0:
                        logger.debug(
                            f"   TODO sync: {completed_count} completed entries detected "
                            f"({auto_count} auto-cleanable, {manual_count} manual review)"
                        )
                        dry_run_report = result.get('dry_run_report')
                        if isinstance(dry_run_report, str) and dry_run_report.strip():
                            logger.debug(f"   {dry_run_report}")
                    else:
                        logger.debug("   TODO sync: No completed entries detected")
                else:
                    message = result.get('message', 'Unknown error')
                    logger.warning(f"   TODO sync: {message}")
        except Exception as exc:
            logger.warning(f"   TODO sync failed: {exc}")

    def _get_audit_related_lock_paths(self) -> list[Path]:
        """Return lock paths used by audit/coverage operations."""
        audit_lock = self._get_audit_lock_file_path()
        coverage_lock = self._get_coverage_lock_file_path()
        dev_tools_coverage_lock = (
            coverage_lock.parent / ".coverage_dev_tools_in_progress.lock"
        )
        return [audit_lock, coverage_lock, dev_tools_coverage_lock]
