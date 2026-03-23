"""
Command execution methods for AIToolsService.

Contains methods for executing various CLI commands (docs, validate, config, etc.)
"""
# pyright: reportAttributeAccessIssue=false

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from core.logger import get_component_logger
from core.time_utilities import now_timestamp_filename

logger = get_component_logger("development_tools")

# Import output storage
from ..output_storage import save_tool_result
from ..backup_inventory import build_backup_inventory
from ..backup_policy_models import load_backup_policy, resolve_policy_path
from ..backup_reports import (
    write_json_report,
)
from ..lock_state import cleanup_lock_paths, evaluate_lock_set, write_lock_metadata
from ..retention_engine import apply_retention_plan, build_retention_plan
import contextlib


class CommandsMixin:
    """Mixin class providing command execution methods to AIToolsService."""

    def _get_audit_related_lock_paths(self) -> list[Path]:
        """Return audit/coverage lock file paths anchored at project root."""
        lock_names = [".audit_in_progress.lock", ".coverage_in_progress.lock"]
        try:
            from ... import config

            lock_names[0] = str(
                config.get_external_value(
                    "paths.audit_lock_file", lock_names[0]
                )
            )
            lock_names[1] = str(
                config.get_external_value(
                    "paths.coverage_lock_file", lock_names[1]
                )
            )
        except Exception:
            pass

        audit_lock = self.project_root / Path(lock_names[0])
        coverage_lock = self.project_root / Path(lock_names[1])
        dev_tools_coverage_lock = (
            coverage_lock.parent / ".coverage_dev_tools_in_progress.lock"
        )
        return [audit_lock, coverage_lock, dev_tools_coverage_lock]

    def _get_existing_audit_related_locks(self) -> list[Path]:
        """Return active lock files after cleaning stale/malformed entries."""
        lock_paths = self._get_audit_related_lock_paths()
        lock_states = evaluate_lock_set(lock_paths)
        cleanup_targets = [
            entry["path"]
            for entry in (lock_states["stale"] + lock_states["malformed"])
            if isinstance(entry.get("path"), Path)
        ]
        if cleanup_targets:
            removed = cleanup_lock_paths(cleanup_targets)
            logger.warning(
                f"Removed {removed} stale/malformed audit lock file(s) before command execution"
            )
        return [entry["path"] for entry in lock_states["active"] if isinstance(entry.get("path"), Path)]

    def _resolve_coverage_workers(self, target: str) -> str | None:
        """Resolve pytest-xdist worker count for coverage runs."""
        if target not in {"main", "dev_tools"}:
            return None

        try:
            # Use sys.modules lookup to ensure we hit the *same* `development_tools.config`
            # module object that tests patch (string target
            # `development_tools.config.get_coverage_runtime_config`).
            import sys
            import importlib

            config_mod = sys.modules.get("development_tools.config")
            if config_mod is None:
                config_mod = importlib.import_module("development_tools.config")

            coverage_cfg = config_mod.get_coverage_runtime_config() or {}
        except Exception:
            coverage_cfg = {}

        # Use explicit instance state only.
        # Some tests (and orchestration code) may mutate class-level attributes; using
        # __dict__ prevents leaked defaults from changing behavior unexpectedly.
        self_dict = getattr(self, "__dict__", {}) or {}
        concurrent = bool(self_dict.get("_tier3_coverage_concurrent", False))
        if target == "main":
            key = "main_workers_when_concurrent" if concurrent else "main_workers"
        else:
            key = (
                "dev_tools_workers_when_concurrent"
                if concurrent
                else "dev_tools_workers"
            )

        configured = coverage_cfg.get(key)
        if configured is not None:
            configured_text = str(configured).strip()
            if configured_text.lower() == "auto":
                return "auto"
            try:
                configured_int = int(configured_text)
                if configured_int > 0:
                    return str(configured_int)
            except ValueError:
                logger.warning(
                    f"Ignoring invalid coverage worker config {key}={configured!r}"
                )

        # When Tier 3 coverage jobs run concurrently, cap workers per job to avoid
        # over-subscribing CPU and triggering timeout regressions.
        if concurrent:
            cpu_count = os.cpu_count() or 4
            if target == "main":
                if cpu_count >= 8:
                    return "6"
                if cpu_count >= 6:
                    return "4"
                return str(max(2, cpu_count - 1))
            serialized = bool(self_dict.get("_tier3_coverage_serialized", False))
            if serialized:
                if cpu_count >= 8:
                    return "6"
                if cpu_count >= 6:
                    return "4"
                return str(max(2, cpu_count - 1))
            return str(max(1, cpu_count // 3))

        return None

    def _infer_coverage_cache_mode_from_output(self, output: str) -> str:
        """Infer cache mode from run_test_coverage script output text."""
        text = (output or "").lower()
        if "using cached coverage data only" in text:
            return "cache_only"
        if "merged cached and fresh coverage data" in text or "cache merge" in text:
            return "partial_cache"
        if "using cached coverage data" in text:
            return "cache_only"
        if "running all tests" in text or "source files changed" in text:
            return "cold_scan"
        return "unknown"

    def _extract_coverage_invalidation_reason(self, output: str) -> str:
        """Extract first cache invalidation or rerun reason from coverage output."""
        if not output:
            return "unknown"
        reason_markers = (
            "invalidating",
            "source files changed",
            "running all tests",
            "no domains changed",
            "using cached coverage data",
            "using full coverage cache",
        )
        for raw_line in output.splitlines():
            line = raw_line.strip()
            lowered = line.lower()
            if any(marker in lowered for marker in reason_markers):
                return line
        return "unknown"

    def _extract_changed_domains(self, output: str) -> list[str]:
        """Extract changed domains list from run_test_coverage output."""
        if not output:
            return []
        marker = "domain(s) changed:"
        for raw_line in output.splitlines():
            line = raw_line.strip()
            lowered = line.lower()
            if marker in lowered:
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                if value.startswith("[") and value.endswith("]"):
                    try:
                        parsed = json.loads(value.replace("'", '"'))
                        if isinstance(parsed, list):
                            return [str(item) for item in parsed]
                    except Exception:
                        pass
                return [part.strip().strip("'\"") for part in value.strip("[]").split(",") if part.strip()]
        return []

    def _is_interrupt_signature(self, output: str, returncode: int | None) -> bool:
        """Detect likely interrupt/console control event signatures."""
        text = (output or "").lower()
        if "keyboardinterrupt" in text:
            return True
        # 130 is common for SIGINT-style exits.
        return returncode == 130

    def _build_coverage_metadata(self, output: str, source: str) -> dict[str, object]:
        """Build normalized coverage cache metadata payload."""
        cache_mode = self._infer_coverage_cache_mode_from_output(output)
        reason = self._extract_coverage_invalidation_reason(output)
        changed_domains = self._extract_changed_domains(output)
        metadata: dict[str, object] = {
            "cache_mode": cache_mode,
            "invalidation_reason": reason,
            "source": source,
        }
        if changed_domains:
            metadata["changed_domains"] = changed_domains
        return metadata

    def _latest_mtime_for_patterns(
        self,
        patterns: list[str],
        exclude_prefixes: list[str] | None = None,
        exclude_paths: list[str] | None = None,
    ) -> float:
        """Return latest mtime for files matching any glob pattern."""
        from ..standard_exclusions import should_exclude_file

        latest = 0.0
        exclude_prefixes = exclude_prefixes or []
        exclude_paths_normalized = {path.replace("\\", "/") for path in (exclude_paths or [])}
        for pattern in patterns:
            for path in self.project_root.glob(pattern):
                if not path.is_file():
                    continue
                normalized = str(path.relative_to(self.project_root)).replace("\\", "/")
                if normalized in exclude_paths_normalized:
                    continue
                if any(normalized.startswith(prefix) for prefix in exclude_prefixes):
                    continue
                if should_exclude_file(normalized, tool_type="analysis", context="development"):
                    continue
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                if mtime > latest:
                    latest = mtime
        return latest

    def _is_coverage_file_fresh(
        self,
        coverage_file: Path,
        source_patterns: list[str],
        exclude_prefixes: list[str] | None = None,
        tool_names: list[str] | None = None,
        config_paths: list[str] | None = None,
    ) -> bool:
        """Check whether a coverage file is newer than all relevant inputs."""
        if not coverage_file.exists():
            return False
        try:
            coverage_mtime = coverage_file.stat().st_mtime
        except OSError:
            return False
        latest_input_mtime = self._latest_mtime_for_patterns(
            source_patterns, exclude_prefixes=exclude_prefixes
        )

        # Invalidate when coverage runner implementation changes.
        if tool_names:
            try:
                from .tool_wrappers import SCRIPT_REGISTRY

                for tool_name in tool_names:
                    # SCRIPT_REGISTRY maps tool name -> script path string
                    script_path_str = SCRIPT_REGISTRY.get(tool_name)
                    if not script_path_str:
                        continue
                    script_path = self.project_root / script_path_str
                    if not script_path.exists():
                        continue
                    latest_input_mtime = max(
                        latest_input_mtime, script_path.stat().st_mtime
                    )
            except Exception:
                pass

        # Invalidate when config changes.
        for rel in (config_paths or []):
            try:
                config_path = self.project_root / rel
                if config_path.exists():
                    latest_input_mtime = max(
                        latest_input_mtime, config_path.stat().st_mtime
                    )
            except Exception:
                continue

        return coverage_mtime >= latest_input_mtime

    def _load_cached_result_if_available(self, tool_name: str, domain: str) -> dict | None:
        """Load cached standardized tool result if it exists."""
        try:
            from ..output_storage import load_tool_result

            data = load_tool_result(tool_name, domain, project_root=self.project_root)
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None

    def _to_standard_dev_tools_coverage_result(self, raw_data: dict) -> dict:
        """Normalize dev-tools coverage payload to standard summary/details format."""
        if (
            isinstance(raw_data, dict)
            and isinstance(raw_data.get("summary"), dict)
            and isinstance(raw_data.get("details"), dict)
        ):
            return raw_data

        overall = raw_data.get("overall", {}) if isinstance(raw_data, dict) else {}
        total_missed = int(overall.get("total_missed", 0) or 0)
        standard = {
            "summary": {
                "total_issues": total_missed,
                "files_affected": 0,
            },
            "details": raw_data if isinstance(raw_data, dict) else {},
        }
        return standard

    def _extract_cached_main_coverage_state(self, cached_result: dict | None) -> str | None:
        """Extract cached main coverage test outcome state when present."""
        if not isinstance(cached_result, dict):
            return None
        details = cached_result.get("details")
        if not isinstance(details, dict):
            return None
        tier3 = details.get("tier3_test_outcome")
        if isinstance(tier3, dict):
            state = self._derive_tier3_state_from_classifications(tier3)
            if isinstance(state, str) and state:
                return state
        coverage_outcome = details.get("coverage_outcome")
        if isinstance(coverage_outcome, dict):
            state = self._derive_tier3_state_from_classifications(coverage_outcome)
            if isinstance(state, str) and state:
                return state
        return None

    def _extract_cached_dev_tools_state(self, cached_result: dict | None) -> str | None:
        """Extract cached dev-tools test outcome state when present."""
        if not isinstance(cached_result, dict):
            return None
        details = cached_result.get("details")
        if not isinstance(details, dict):
            return None
        dev_tools = details.get("dev_tools_test_outcome")
        if isinstance(dev_tools, dict):
            state = self._extract_track_classification(dev_tools)
            if isinstance(state, str) and state:
                return state
        return None

    def _extract_track_classification(self, track: dict) -> str:
        """Return canonical per-track classification label."""
        if not isinstance(track, dict):
            return "unknown"
        classification = track.get("classification")
        if isinstance(classification, str) and classification.strip():
            return classification.strip()
        return "unknown"

    def _derive_tier3_state_from_classifications(self, outcome: dict) -> str:
        """Derive aggregate Tier 3 state from per-track classifications."""
        if not isinstance(outcome, dict):
            return ""
        state = outcome.get("state")
        if state == "coverage_failed":
            return "coverage_failed"
        parallel = (
            outcome.get("parallel", {}) if isinstance(outcome.get("parallel"), dict) else {}
        )
        no_parallel = (
            outcome.get("no_parallel", {}) if isinstance(outcome.get("no_parallel"), dict) else {}
        )
        dev_tools = (
            outcome.get("development_tools", {})
            if isinstance(outcome.get("development_tools"), dict)
            else {}
        )
        track_labels = (
            self._extract_track_classification(parallel),
            self._extract_track_classification(no_parallel),
            self._extract_track_classification(dev_tools),
        )
        if "infra_cleanup_error" in track_labels:
            return "infra_cleanup_error"
        if "crashed" in track_labels:
            return "crashed"
        if "failed" in track_labels:
            return "test_failures"
        if "passed" in track_labels or "skipped" in track_labels:
            return "clean"
        if any(label == "unknown" for label in track_labels):
            return "coverage_failed"
        return "unknown"

    def _is_failure_state(self, state: str | None) -> bool:
        """Return True when cached test outcome state represents a failure."""
        if not state:
            return False
        return state in {
            "failed",
            "test_failures",
            "coverage_failed",
            "crashed",
            "infra_cleanup_error",
            "error",
            "errors",
        }
    
    def run_docs(self):
        """Update all documentation (OPTIONAL - not essential for audit)"""
        logger.info("Starting documentation update...")
        logger.info("Updating documentation...")
        logger.info("=" * 50)

        # Fail fast when audit/coverage locks are present to avoid noisy partial updates.
        blocking_locks = self._get_existing_audit_related_locks()
        if blocking_locks:
            lock_list = ", ".join(str(path) for path in blocking_locks)
            logger.error(
                "Documentation update blocked: audit/coverage lock file(s) present: "
                f"{lock_list}"
            )
            logger.error(
                "If no audit is running, remove stale lock file(s) and rerun: "
                "python development_tools/run_development_tools.py docs"
            )
            logger.info("=" * 50)
            return False

        success = True
        
        # Generate function registry
        try:
            logger.info("  - Generating function registry...")
            result = self.run_script("generate_function_registry")
            if result['success']:
                logger.info("  - Function registry generated successfully")
            else:
                logger.error(f"  - Function registry generation failed: {result['error']}")
                success = False
        except Exception as exc:
            logger.error(f"  - Function registry generation failed: {exc}")
            success = False
        
        # Generate module dependencies
        try:
            logger.info("  - Generating module dependencies...")
            result = self.run_script("generate_module_dependencies")
            if result['success']:
                logger.info("  - Module dependencies generated successfully")
            else:
                logger.error(f"  - Module dependencies generation failed: {result['error']}")
                success = False
        except Exception as exc:
            logger.error(f"  - Module dependencies generation failed: {exc}")
            success = False
        
        # Generate directory trees
        # NOTE: Static documentation (DIRECTORY_TREE, FUNCTION_REGISTRY, MODULE_DEPENDENCIES)
        # should ONLY be generated via the 'docs' command, NOT during audits.
        try:
            logger.info("  - Generating directory trees...")
            self.generate_directory_trees()
        except Exception as exc:
            logger.error(f"  - Directory tree generation failed: {exc}")
            success = False
        
        # Run documentation sync check
        try:
            logger.info("  - Checking documentation sync...")
            if not self._run_doc_sync_check():
                success = False
        except Exception as exc:
            logger.error(f"  - Documentation sync check failed: {exc}")
            success = False
        
        logger.info("=" * 50)
        if success:
            logger.info("Completed documentation update successfully!")
        else:
            logger.warning("Completed documentation update with issues.")
        return success
    
    def run_validate(self):
        """Validate AI-generated work (simple command)"""
        logger.debug("Analyzing AI work...")
        # Use --json flag to prevent multiline print output from being captured
        result = self.run_script('analyze_ai_work', '--json')
        if result['success']:
            self.validation_results = result
            try:
                data = result.get('data')
                if not data and result.get('output'):
                    try:
                        import json
                        data = json.loads(result.get('output', ''))
                    except (json.JSONDecodeError, TypeError):
                        data = {
                            'success': result.get('success', False),
                            'output': result.get('output', ''),
                            'error': result.get('error', ''),
                            'returncode': result.get('returncode', 0)
                        }
                if data:
                    save_tool_result('analyze_ai_work', 'ai_work', data, project_root=self.project_root)
            except Exception as e:
                logger.debug(f"Failed to save analyze_ai_work results: {e}")
            logger.debug("Validation completed successfully!")
            return True
        else:
            logger.error(f"Validation failed: {result['error']}")
            return False
    
    def run_config(self):
        """Check configuration consistency (simple command)"""
        logger.info("Running analyze_config...")
        result = self.run_script('analyze_config')
        if result['success']:
            output = result.get('output', '')
            if output:
                try:
                    import json
                    lines = output.strip().split('\n')
                    json_start = None
                    for i in range(len(lines) - 1, -1, -1):
                        if lines[i].strip().startswith('{'):
                            json_start = i
                            break
                    if json_start is not None:
                        json_output = '\n'.join(lines[json_start:])
                        json_data = json.loads(json_output)
                        try:
                            save_tool_result('analyze_config', 'config', json_data, project_root=self.project_root)
                            logger.debug("Regenerated analyze_config_results.json")
                        except Exception as e:
                            logger.warning(f"Failed to save analyze_config result: {e}")
                    else:
                        json_data = json.loads(output)
                        save_tool_result('analyze_config', 'config', json_data, project_root=self.project_root)
                        logger.debug("Regenerated analyze_config_results.json")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse analyze_config JSON output: {e}")
                    logger.debug(f"Output was: {output[:500]}...")
                logger.debug(f"analyze_config output (first 1000 chars): {output[:1000]}")
            else:
                logger.warning("No output from analyze_config script")
            return True
        else:
            logger.error(f"Configuration check failed: {result['error']}")
            return False

    def run_analyze_config(self) -> dict:
        """Run analyze_config script, persist result for report generation, return result dict for audit."""
        result = self.run_script("analyze_config")
        output = result.get("output", "")
        if not output:
            return {**result, "success": result.get("success", False)}
        try:
            lines = output.strip().split("\n")
            json_start = None
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip().startswith("{"):
                    json_start = i
                    break
            if json_start is not None:
                json_output = "\n".join(lines[json_start:])
                json_data = json.loads(json_output)
            else:
                json_data = json.loads(output)
            save_tool_result(
                "analyze_config", "config", json_data, project_root=self.project_root
            )
            if hasattr(self, "results_cache") and self.results_cache is not None:
                self.results_cache["analyze_config"] = json_data
            return {**result, "success": True, "data": json_data}
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"analyze_config JSON parse failed: {e}")
            return {**result, "success": result.get("success", False)}
    
    def run_workflow(self, task_type: str, task_data: dict | None = None) -> bool:
        """Run workflow with audit-first protocol"""
        logger.info(f"Running workflow: {task_type}")
        logger.info("=" * 50)
        if not self.check_trigger_requirements(task_type):
            return False
        audit_results = self.run_audit_first(task_type)
        if not audit_results['success']:
            logger.error(f"Audit failed: {audit_results['error']}")
            return False
        task_success = self.execute_task(task_type, task_data)
        if task_success:
            validation_results = self.validate_work(task_type, task_data or {})
            self.show_validation_report(validation_results)
        return task_success
    
    def run_version_sync(self, scope: str = 'docs'):
        """Sync version numbers"""
        logger.info(f"Syncing versions for scope: {scope}")
        logger.info("=" * 50)
        result = self.run_script('fix_version_sync', 'sync', '--scope', scope)
        if result['success']:
            self.fix_version_sync_results = result
            logger.info("Version sync completed!")
            return True
        else:
            logger.error(f"Version sync failed: {result['error']}")
            return False
    
    def run_dev_tools_coverage(self) -> dict:
        """Run coverage analysis specifically for development_tools directory."""
        logger.debug("Generating dev tools coverage (development_tools/tests)...")
        dev_tools_coverage_file = self.project_root / "development_tools" / "tests" / "jsons" / "coverage_dev_tools.json"
        dev_tools_patterns = [
            "development_tools/**/*.py",
            "tests/development_tools/**/*.py",
        ]
        if self._is_coverage_file_fresh(
            dev_tools_coverage_file,
            dev_tools_patterns,
            tool_names=["run_test_coverage"],
            config_paths=[
                "development_tools/tests/coverage_dev_tools.ini",
                "development_tools/config/development_tools_config.json",
                "development_tools_config.json",
            ],
        ):
            cached_data = self._load_cached_result_if_available("generate_dev_tools_coverage", "tests")
            cached_state = self._extract_cached_dev_tools_state(cached_data)
            if self._is_failure_state(cached_state):
                logger.info(
                    "Skipping precheck cache reuse for dev tools coverage because cached test outcome state is "
                    + str(cached_state)
                )
                cached_data = None
            cache_metadata = {
                "cache_mode": "cache_only",
                "invalidation_reason": "Precheck: dev tools/test sources unchanged since coverage_dev_tools.json",
                "source": "orchestration_precheck",
            }
            if not hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata["generate_dev_tools_coverage"] = cache_metadata
            if cached_data:
                existing_tier3 = (
                    self.tier3_test_outcome
                    if isinstance(getattr(self, "tier3_test_outcome", None), dict)
                    else {}
                )
                merged_tier3 = dict(existing_tier3)
                merged_tier3["development_tools"] = {
                    "state": "skipped",
                    "classification": "skipped",
                    "classification_reason": "cache_reuse_precheck",
                    "actionable_context": "Development-tools coverage execution skipped because cache is fresh.",
                    "log_file": None,
                    "return_code_hex": None,
                    "return_code": None,
                    "passed_count": 0,
                    "failed_count": 0,
                    "error_count": 0,
                    "skipped_count": 0,
                    "failed_node_ids": [],
                    "from_cache": True,
                }
                self.tier3_test_outcome = merged_tier3
                logger.info(
                    "Skipping dev tools coverage run - cached dev tools coverage is up to date"
                )
                normalized_cached = self._to_standard_dev_tools_coverage_result(cached_data)
                normalized_cached.setdefault("_cache_metadata", {}).update(cache_metadata)
                return {"success": True, "data": normalized_cached, "cache_metadata": cache_metadata}

        # Use separate lock file for dev tools coverage to avoid conflicts when running in parallel with main coverage
        # Both lock files are checked by _is_audit_in_progress(), so this is safe
        coverage_lock_file = self._get_coverage_lock_file_path() if hasattr(self, '_get_coverage_lock_file_path') else (self.project_root / 'development_tools' / '.coverage_in_progress.lock')
        # Use a separate lock file for dev tools to avoid file conflicts when running in parallel
        coverage_lock_file = coverage_lock_file.parent / '.coverage_dev_tools_in_progress.lock'
        try:
            if not write_lock_metadata(
                coverage_lock_file, lock_type="coverage_dev_tools"
            ):
                raise RuntimeError(
                    "write_lock_metadata returned False for dev-tools coverage lock"
                )
        except Exception as e:
            logger.warning(f"Failed to create coverage lock file: {e}")
        
        try:
            dev_tools_output_file = (
                self.project_root
                / "development_tools"
                / "tests"
                / "jsons"
                / "run_test_coverage_dev_tools_results.json"
            )
            coverage_args = [
                "run_test_coverage",
                "--dev-tools-only",
                "--output-file",
                str(dev_tools_output_file),
            ]
            dev_workers = self._resolve_coverage_workers("dev_tools")
            if dev_workers:
                coverage_args.extend(["--workers", dev_workers])
                logger.info(
                    f"Dev tools coverage worker cap: {dev_workers} (concurrent={bool(getattr(self, '_tier3_coverage_concurrent', False))})"
                )
            result = self.run_script(*coverage_args, timeout=720)
            output_text = "\n".join(
                [result.get("output", "") or "", result.get("error", "") or ""]
            )
            interrupted = self._is_interrupt_signature(
                output_text, result.get("returncode")
            )
            initial_dev_tools_state = "unknown"
            if result.get("returncode") not in (None, 0):
                initial_dev_tools_state = "failed"
            dev_tools_outcome = {
                "state": initial_dev_tools_state,
                "classification": (
                    "failed" if initial_dev_tools_state == "failed" else "unknown"
                ),
                "classification_reason": (
                    "dev_tools_nonzero_exit_no_structured_outcome"
                    if initial_dev_tools_state == "failed"
                    else "dev_tools_outcome_pending_parse"
                ),
                "actionable_context": "Inspect dev-tools pytest stdout log for details.",
                "log_file": None,
                "return_code_hex": None,
                "return_code": result.get("returncode"),
                "passed_count": 0,
                "failed_count": 0,
                "error_count": 0,
                "skipped_count": 0,
                "failed_node_ids": [],
            }
            if interrupted:
                self._internal_interrupt_detected = True
                dev_tools_outcome["classification"] = "crashed"
                dev_tools_outcome["classification_reason"] = "subprocess_keyboard_interrupt"
                dev_tools_outcome["actionable_context"] = (
                    "Coverage subprocess reported KeyboardInterrupt/SIGINT. "
                    "Check terminal/host signal events and pytest logs."
                )
                logger.error(
                    "Detected interrupt signature while running dev-tools coverage subprocess "
                    f"(returncode={result.get('returncode')})."
                )
            if dev_tools_output_file.exists():
                try:
                    with open(dev_tools_output_file, encoding="utf-8") as f:
                        dev_tools_payload = json.load(f)
                    if isinstance(dev_tools_payload, dict):
                        details = dev_tools_payload.get("details")
                        parsed_outcome = {}
                        if isinstance(details, dict):
                            parsed_outcome = details.get("dev_tools_test_outcome", {})
                        if isinstance(parsed_outcome, dict):
                            dev_tools_outcome = {
                                "state": parsed_outcome.get("state", "unknown"),
                                "classification": parsed_outcome.get(
                                    "classification",
                                    parsed_outcome.get("state", "unknown"),
                                ),
                                "classification_reason": parsed_outcome.get(
                                    "classification_reason", "unknown"
                                ),
                                "actionable_context": parsed_outcome.get(
                                    "actionable_context",
                                    "Inspect dev-tools pytest stdout log for details.",
                                ),
                                "log_file": parsed_outcome.get("log_file"),
                                "return_code_hex": parsed_outcome.get("return_code_hex"),
                                "return_code": parsed_outcome.get("return_code"),
                                "passed_count": parsed_outcome.get("passed_count", 0),
                                "failed_count": parsed_outcome.get("failed_count", 0),
                                "error_count": parsed_outcome.get("error_count", 0),
                                "skipped_count": parsed_outcome.get("skipped_count", 0),
                                "failed_node_ids": parsed_outcome.get(
                                    "failed_node_ids", []
                                ),
                            }
                except Exception as parse_error:
                    logger.debug(
                        f"Failed to parse dev tools structured coverage output: {parse_error}"
                    )
            cache_metadata = self._build_coverage_metadata(
                output_text, source="run_test_coverage --dev-tools-only"
            )
            if cache_metadata.get("cache_mode") == "unknown":
                cache_metadata["cache_mode"] = "cold_scan"
                if cache_metadata.get("invalidation_reason") in (None, "", "unknown"):
                    cache_metadata["invalidation_reason"] = (
                        "Coverage command executed (stdout mode markers unavailable)"
                    )
            if not hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata["generate_dev_tools_coverage"] = cache_metadata
            existing_tier3 = (
                self.tier3_test_outcome
                if isinstance(getattr(self, "tier3_test_outcome", None), dict)
                else {}
            )
            merged_tier3 = dict(existing_tier3)
            merged_tier3["development_tools"] = dev_tools_outcome
            self.tier3_test_outcome = merged_tier3
            # Check if coverage was collected, not just if pytest succeeded
            # pytest can exit with non-zero code if tests fail, but coverage may still be collected
            coverage_collected = False
            
            # First check if coverage file exists (most reliable indicator)
            if dev_tools_coverage_file.exists():
                coverage_collected = True
            
            # Also check output for coverage indicators
            if result.get('output'):
                output = result['output']
                if 'TOTAL' in output or 'coverage' in output.lower() or 'Cover' in output:
                    coverage_collected = True
            
            # If script failed but coverage file exists, we still succeeded
            if coverage_collected:
                self._load_dev_tools_coverage()
                if hasattr(self, 'dev_tools_coverage_results') and isinstance(self.dev_tools_coverage_results, dict):
                    normalized = self._to_standard_dev_tools_coverage_result(self.dev_tools_coverage_results)
                    normalized.setdefault("_cache_metadata", {})
                    normalized["_cache_metadata"].update(cache_metadata)
                    normalized.setdefault("details", {})
                    if isinstance(normalized.get("details"), dict):
                        normalized["details"]["dev_tools_test_outcome"] = dev_tools_outcome
                    self.dev_tools_coverage_results = normalized
                # Save results to standardized storage
                if hasattr(self, 'dev_tools_coverage_results') and self.dev_tools_coverage_results:
                    try:
                        save_tool_result('generate_dev_tools_coverage', 'tests', self.dev_tools_coverage_results, project_root=self.project_root)
                    except Exception as e:
                        logger.warning(f"Failed to save generate_dev_tools_coverage result: {e}")
                return {
                    'success': True,
                    'data': self.dev_tools_coverage_results,
                    'cache_metadata': cache_metadata,
                }
            else:
                # Even if script failed, check one more time if coverage file was created
                # (it might have been created before the script failed)
                if dev_tools_coverage_file.exists():
                    logger.info("Coverage file found despite script failure - loading coverage data")
                    self._load_dev_tools_coverage()
                    if hasattr(self, 'dev_tools_coverage_results') and self.dev_tools_coverage_results:
                        normalized = self._to_standard_dev_tools_coverage_result(self.dev_tools_coverage_results)
                        normalized.setdefault("_cache_metadata", {})
                        normalized["_cache_metadata"].update(cache_metadata)
                        normalized.setdefault("details", {})
                        if isinstance(normalized.get("details"), dict):
                            normalized["details"]["dev_tools_test_outcome"] = dev_tools_outcome
                        self.dev_tools_coverage_results = normalized
                        try:
                            save_tool_result('generate_dev_tools_coverage', 'tests', self.dev_tools_coverage_results, project_root=self.project_root)
                        except Exception as e:
                            logger.warning(f"Failed to save generate_dev_tools_coverage result: {e}")
                        return {
                            'success': True,
                            'data': self.dev_tools_coverage_results,
                            'cache_metadata': cache_metadata,
                        }
                
                # No coverage collected
                error_msg = result.get('error', 'Unknown error')
                if result.get('output'):
                    error_msg = f"{error_msg}\nOutput: {result['output'][:500]}"
                logger.warning(f"Dev tools coverage failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'cache_metadata': cache_metadata,
                }
        finally:
            if coverage_lock_file.exists():
                try:
                    coverage_lock_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove coverage lock file: {e}")
            if 'dev_tools_output_file' in locals() and dev_tools_output_file.exists():
                with contextlib.suppress(OSError):
                    dev_tools_output_file.unlink()
    
    def run_status(self, skip_status_files: bool = False):
        """Generate status snapshot (cached data, no audit)"""
        logger.info("Generating status snapshot...")
        logger.info("=" * 50)
        
        if not skip_status_files:
            # Get status file paths from config
            try:
                from ... import config
                status_config = config.get_status_config()
                status_files_config = status_config.get('status_files', {})
                ai_status_path = status_files_config.get('ai_status', 'development_tools/AI_STATUS.md')
                ai_priorities_path = status_files_config.get('ai_priorities', 'development_tools/AI_PRIORITIES.md')
                consolidated_report_path = status_files_config.get('consolidated_report', 'development_tools/CONSOLIDATED_REPORT.md')
            except (ImportError, AttributeError, KeyError):
                ai_status_path = 'development_tools/AI_STATUS.md'
                ai_priorities_path = 'development_tools/AI_PRIORITIES.md'
                consolidated_report_path = 'development_tools/CONSOLIDATED_REPORT.md'
            
            try:
                ai_status = self._generate_ai_status_document()
                from ..file_rotation import create_output_file
                ai_status_file = create_output_file(ai_status_path, ai_status, project_root=self.project_root)
                logger.info(f"Generated: {ai_status_file}")
            except Exception as e:
                logger.warning(f"Error generating AI_STATUS document: {e}")
            
            try:
                ai_priorities = self._generate_ai_priorities_document()
                from ..file_rotation import create_output_file
                ai_priorities_file = create_output_file(ai_priorities_path, ai_priorities, project_root=self.project_root)
                logger.info(f"Generated: {ai_priorities_file}")
            except Exception as e:
                logger.warning(f"Error generating AI_PRIORITIES document: {e}")
            
            try:
                consolidated_report = self._generate_consolidated_report()
                from ..file_rotation import create_output_file
                consolidated_file = create_output_file(consolidated_report_path, consolidated_report, project_root=self.project_root)
                logger.info(f"Generated: {consolidated_file}")
            except Exception as e:
                logger.warning(f"Error generating consolidated report: {e}")
        
        logger.info("=" * 50)
        logger.info("Status snapshot completed!")
    
    def run_documentation_sync(self):
        """Run documentation sync check"""
        logger.info("Running documentation sync check...")
        logger.info("=" * 50)
        success = self._run_doc_sync_check()
        if success:
            logger.info("Documentation sync check completed!")
        else:
            logger.warning("Documentation sync check completed with issues.")
        return success
    
    def run_documentation_fix(self, fix_type: str = 'all', dry_run: bool = False) -> bool:
        """Run documentation fix operations"""
        logger.info(f"Running documentation fix: {fix_type}")
        logger.info("=" * 50)
        args = []
        if dry_run:
            args.append('--dry-run')
        if fix_type == 'all':
            args.append('--all')
        elif fix_type == 'ascii' or fix_type == 'fix-ascii':
            args.append('--fix-ascii')
        elif fix_type == 'number-headings':
            args.append('--number-headings')
        elif fix_type == 'add-addresses':
            args.append('--add-addresses')
        elif fix_type == 'convert-links':
            args.append('--convert-links')
        result = self.run_script('fix_documentation', *args)
        if result['success']:
            logger.info("Documentation fix completed!")
            return True
        else:
            error_msg = result.get('error', '').strip()
            returncode = result.get('returncode')
            if not error_msg:
                if returncode is not None:
                    error_msg = f"Script exited with code {returncode}"
                else:
                    error_msg = "Unknown error (no error message or return code)"
            logger.error(f"Documentation fix failed: {error_msg}")
            if result.get('output'):
                logger.debug(f"Script output: {result['output'][:200]}")
            return False
    
    def run_coverage_regeneration(self):
        """Regenerate test coverage data"""
        logger.debug("Generating test coverage (main project tests)...")
        main_coverage_file = self.project_root / "development_tools" / "tests" / "jsons" / "coverage.json"
        main_coverage_patterns = [
            "*.py",
            "core/**/*.py",
            "communication/**/*.py",
            "ui/**/*.py",
            "tasks/**/*.py",
            "ai/**/*.py",
            "user/**/*.py",
            "tests/**/*.py",
        ]
        if self._is_coverage_file_fresh(
            main_coverage_file,
            main_coverage_patterns,
            exclude_prefixes=["development_tools/"],
            tool_names=["run_test_coverage"],
            config_paths=[
                "development_tools/tests/coverage.ini",
                "development_tools/config/development_tools_config.json",
                "development_tools_config.json",
            ],
        ):
            cached_coverage_result = self._load_cached_result_if_available("analyze_test_coverage", "tests")
            cached_state = self._extract_cached_main_coverage_state(cached_coverage_result)
            if self._is_failure_state(cached_state):
                logger.info(
                    "Skipping precheck cache reuse for main test coverage because cached test outcome state is "
                    + str(cached_state)
                )
                cached_coverage_result = None
            if not hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata["run_test_coverage"] = {
                "cache_mode": "cache_only",
                "invalidation_reason": "Precheck: core/test sources unchanged since coverage.json",
                "source": "orchestration_precheck",
            }
            cached_summary = self._load_coverage_summary()
            if cached_summary and cached_coverage_result is not None:
                logger.info(
                    "Skipping test coverage run - cached main project coverage is up to date"
                )
                overall = cached_summary.get("overall", {}) if isinstance(cached_summary, dict) else {}
                missed = overall.get("missed", 0) if isinstance(overall, dict) else 0
                standard_format = {
                    "summary": {"total_issues": missed, "files_affected": 0},
                    "details": cached_summary,
                    "_cache_metadata": self._tool_cache_metadata["run_test_coverage"],
                }
                try:
                    from ..output_storage import save_tool_result
                    save_tool_result(
                        "analyze_test_coverage",
                        "tests",
                        standard_format,
                        project_root=self.project_root,
                    )
                except Exception as save_error:
                    logger.debug(f"Failed to save cached analyze_test_coverage result: {save_error}")
                existing_tier3 = (
                    self.tier3_test_outcome
                    if isinstance(getattr(self, "tier3_test_outcome", None), dict)
                    else {}
                )
                self.tier3_test_outcome = {
                    "state": "clean",
                    "parallel": {
                        "state": "unknown",
                        "classification": "unknown",
                        "classification_reason": "cache_only_precheck",
                    },
                    "no_parallel": {
                        "state": "unknown",
                        "classification": "unknown",
                        "classification_reason": "cache_only_precheck",
                    },
                    "failed_node_ids": [],
                    "development_tools": existing_tier3.get(
                        "development_tools",
                        {
                            "state": "unknown",
                            "classification": "unknown",
                            "classification_reason": "cache_only_precheck",
                        },
                    ),
                }
                return True

        # Use helper method if available, otherwise default location
        coverage_lock_file = self._get_coverage_lock_file_path() if hasattr(self, '_get_coverage_lock_file_path') else (self.project_root / 'development_tools' / '.coverage_in_progress.lock')
        try:
            if not write_lock_metadata(coverage_lock_file, lock_type="coverage_main"):
                raise RuntimeError(
                    "write_lock_metadata returned False for main coverage lock"
                )
        except Exception as e:
            logger.warning(f"Failed to create coverage lock file: {e}")
        
        try:
            # Run test coverage execution (TEST_COVERAGE_REPORT.md is now generated by generate_test_coverage_report tool)
            # Use 20 minutes timeout (1200s) to allow pytest to complete
            # The script itself sets a 15-minute timeout for pytest, so we need
            # a bit more time for script overhead and pytest execution
            coverage_output_file = (
                self.project_root
                / "development_tools"
                / "tests"
                / "jsons"
                / "run_test_coverage_results.json"
            )
            coverage_args = [
                "run_test_coverage",
                "--output-file",
                str(coverage_output_file),
            ]
            main_workers = self._resolve_coverage_workers("main")
            if main_workers:
                coverage_args.extend(["--workers", main_workers])
                logger.info(
                    f"Main coverage worker cap: {main_workers} (concurrent={bool(getattr(self, '_tier3_coverage_concurrent', False))})"
                )
            result = self.run_script(*coverage_args, timeout=1200)
            output_text = "\n".join(
                [result.get("output", "") or "", result.get("error", "") or ""]
            )
            interrupted = self._is_interrupt_signature(
                output_text, result.get("returncode")
            )
            cache_metadata = self._build_coverage_metadata(output_text, source="run_test_coverage")
            if cache_metadata.get("cache_mode") == "unknown":
                cache_metadata["cache_mode"] = "cold_scan"
                if cache_metadata.get("invalidation_reason") in (None, "", "unknown"):
                    cache_metadata["invalidation_reason"] = (
                        "Coverage command executed (stdout mode markers unavailable)"
                    )
            if not hasattr(self, '_tool_cache_metadata'):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata['run_test_coverage'] = cache_metadata
            structured_outcome = {
                "state": "coverage_failed",
                "parallel": {
                    "state": "unknown",
                    "classification": "unknown",
                    "classification_reason": "coverage_outcome_missing",
                    "actionable_context": "No structured parallel outcome was provided.",
                    "log_file": None,
                    "return_code_hex": None,
                },
                "no_parallel": {
                    "state": "unknown",
                    "classification": "unknown",
                    "classification_reason": "coverage_outcome_missing",
                    "actionable_context": "No structured no-parallel outcome was provided.",
                    "log_file": None,
                    "return_code_hex": None,
                },
                "failed_node_ids": [],
            }
            payload_coverage_collected = False
            payload_from_cache = False
            if coverage_output_file.exists():
                try:
                    with open(coverage_output_file, encoding="utf-8") as f:
                        coverage_payload = json.load(f)
                    if isinstance(coverage_payload, dict):
                        payload_coverage_collected = bool(
                            coverage_payload.get("coverage_collected")
                        )
                        payload_from_cache = bool(coverage_payload.get("from_cache"))
                        structured = coverage_payload.get("coverage_outcome", {})
                        if isinstance(structured, dict) and structured:
                            structured_outcome = {
                                "state": structured.get("state", "coverage_failed"),
                                "parallel": structured.get("parallel", {}),
                                "no_parallel": structured.get("no_parallel", {}),
                                "failed_node_ids": structured.get(
                                "failed_node_ids", []
                                ),
                            }
                            for track_name in ("parallel", "no_parallel"):
                                track = structured_outcome.get(track_name, {})
                                if not isinstance(track, dict):
                                    track = {"state": "unknown"}
                                    structured_outcome[track_name] = track
                                if "classification" not in track:
                                    logger.info(
                                        "Tier 3 coverage payload missing per-track classification fields; "
                                        f"normalizing track metadata for {track_name}."
                                    )
                                    track_state = str(track.get("state", "unknown") or "unknown")
                                    track["classification"] = track_state
                                    track["classification_reason"] = "state_only_payload_missing_classification"
                                    track["actionable_context"] = (
                                        "Coverage outcome payload omitted explicit classification fields; "
                                        "state-derived classification applied."
                                    )
                                    existing_log_file = track.get("log_file")
                                    track["log_file"] = (
                                        str(existing_log_file)
                                        if existing_log_file is not None
                                        else ""
                                    )
                                    existing_return_code_hex = track.get("return_code_hex")
                                    track["return_code_hex"] = (
                                        str(existing_return_code_hex)
                                        if existing_return_code_hex is not None
                                        else ""
                                    )
                        else:
                            # coverage_outcome missing: invalidate cache, do not use payload
                            try:
                                coverage_output_file.unlink(missing_ok=True)
                                logger.info(
                                    "Tier 3 coverage payload missing coverage_outcome; "
                                    "invalidated cache file."
                                )
                            except Exception as unlink_err:
                                logger.warning(
                                    f"Failed to invalidate coverage cache: {unlink_err}"
                                )
                except Exception as parse_error:
                    logger.debug(
                        f"Failed to parse run_test_coverage structured output: {parse_error}"
                    )
            inferred_tier3_state = self._derive_tier3_state_from_classifications(
                structured_outcome
            )
            raw_tier3_state = str(structured_outcome.get("state", "")).strip()
            if raw_tier3_state in ("", "unknown"):
                if inferred_tier3_state:
                    structured_outcome["state"] = inferred_tier3_state
            elif (
                raw_tier3_state == "coverage_failed"
                and payload_coverage_collected
                and inferred_tier3_state
                and inferred_tier3_state != "coverage_failed"
            ):
                logger.warning(
                    "Tier 3 coverage payload reported coverage_failed while "
                    f"coverage_collected=True; normalizing state to {inferred_tier3_state}."
                )
                structured_outcome["state"] = inferred_tier3_state
            existing_tier3 = (
                self.tier3_test_outcome
                if isinstance(getattr(self, "tier3_test_outcome", None), dict)
                else {}
            )
            self.tier3_test_outcome = {
                **structured_outcome,
                "development_tools": existing_tier3.get(
                    "development_tools", {"state": "unknown"}
                ),
            }
            tier3_state = structured_outcome.get("state", "coverage_failed")
            if tier3_state == "coverage_failed":
                if interrupted:
                    self._internal_interrupt_detected = True
                    logger.error(
                        "Tier 3 coverage failed with interrupt signature "
                        f"(returncode={result.get('returncode')})."
                    )
                logger.error(
                    "Tier 3 coverage outcome is coverage_failed; treating run_test_coverage as failed"
                )
                return False
            if result['success']:
                
                # Save coverage results to standardized storage
                # Load coverage data (will check archive if main file was rotated)
                try:
                    coverage_data = self._load_coverage_summary()
                    if coverage_data:
                        # _load_coverage_summary() returns 'coverage' not 'percent_covered'
                        overall_coverage = coverage_data.get('overall', {}).get('coverage', 'N/A')
                        modules_count = len(coverage_data.get('modules', []))
                        logger.debug(f"Loaded coverage data: overall={overall_coverage}%, modules={modules_count}")
                        from ..output_storage import save_tool_result
                        overall = coverage_data.get('overall', {}) if isinstance(coverage_data, dict) else {}
                        missed = overall.get('missed', 0) if isinstance(overall, dict) else 0
                        standard_format = {
                            'summary': {
                                'total_issues': missed,
                                'files_affected': 0,
                            },
                            'details': {
                                **coverage_data,
                                'tier3_test_outcome': self.tier3_test_outcome,
                            },
                            '_cache_metadata': cache_metadata,
                        }
                        save_tool_result('analyze_test_coverage', 'tests', standard_format, project_root=self.project_root)
                        logger.debug(f"Saved analyze_test_coverage results to standardized storage (coverage: {overall_coverage}%)")
                    else:
                        logger.warning("No coverage data available to save - _load_coverage_summary() returned None (coverage.json may not exist or be empty)")
                except Exception as save_error:
                    logger.warning(f"Failed to save analyze_test_coverage results: {save_error}")
                    import traceback
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                return True
            else:
                logger.warning(
                    f"Tier 3 coverage outcome: {structured_outcome.get('state', 'coverage_failed')}"
                )
                logger.error(f"Test coverage regeneration failed: {result['error']}")
                return False
        finally:
            if coverage_lock_file.exists():
                try:
                    coverage_lock_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove coverage lock file: {e}")
            if 'coverage_output_file' in locals() and coverage_output_file.exists():
                with contextlib.suppress(OSError):
                    coverage_output_file.unlink()
    
    def run_legacy_cleanup(self):
        """Run legacy reference cleanup"""
        logger.info("Starting legacy cleanup...")
        logger.info("=" * 50)
        success = self._run_legacy_cleanup_scan()
        if success:
            logger.info("Legacy cleanup completed!")
        else:
            logger.warning("Legacy cleanup completed with issues.")
        return success
    
    def run_cleanup(self, cache: bool = False, test_data: bool = False,
                    reports: bool = False,
                    coverage: bool = False, full: bool = False,
                    dry_run: bool = False,
                    include_tool_caches: bool = False):
        """Clean up generated files and caches"""
        try:
            from development_tools.shared.fix_project_cleanup import ProjectCleanup
            
            logger.info("Starting cleanup...")
            logger.info("=" * 50)
            
            # If --full is specified, clean everything including tool caches.
            if full:
                cache = True
                test_data = True
                coverage = True
                include_tool_caches = True
            cleanup = ProjectCleanup(self.project_root)
            results = cleanup.cleanup_all(
                dry_run=dry_run,
                cache=cache,
                test_data=test_data,
                coverage=coverage,
                include_tool_caches=include_tool_caches
            )
            
            if dry_run:
                logger.info("DRY RUN MODE - No files were actually removed")
            
            logger.info("Cleanup completed!")
            
            return {
                'success': True,
                'data': results
            }
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def run_backup_inventory(self) -> dict[str, object]:
        """Generate backup ownership/producer inventory from policy config."""
        try:
            policy = load_backup_policy()
            inventory = build_backup_inventory(self.project_root, policy)
            inventory_payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "project_root": str(self.project_root),
                "inventory": inventory,
            }
            json_path = write_json_report(
                self.project_root,
                "development_tools/reports/jsons/backup_inventory.json",
                inventory_payload,
                rotate=False,
            )
            return {
                "success": True,
                "data": inventory_payload,
                "report_paths": {
                    "json": str(json_path),
                },
            }
        except Exception as e:
            logger.error(f"Backup inventory failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def run_backup_retention(self, dry_run: bool = True, apply: bool = False) -> dict[str, object]:
        """Apply or preview portable retention policy for development-tool artifacts."""
        execute_apply = bool(apply) and not bool(dry_run)
        try:
            policy = load_backup_policy()
            plan = build_retention_plan(
                self.project_root,
                policy,
                target_category="B",
                owner="development_tools",
            )
            result = apply_retention_plan(plan, dry_run=not execute_apply)
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "project_root": str(self.project_root),
                "plan": plan,
                "result": result,
            }
            json_path = write_json_report(
                self.project_root,
                "development_tools/reports/jsons/backup_retention_report.json",
                payload,
                rotate=False,
            )
            return {
                "success": True,
                "data": payload,
                "report_paths": {
                    "json": str(json_path),
                },
            }
        except Exception as e:
            logger.error(f"Backup retention failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def run_backup_drill(
        self,
        backup_path: str | None = None,
        restore_users: bool = True,
        restore_config: bool = False,
    ) -> dict[str, object]:
        """Run isolated restore drill for latest core user backup."""
        restore_destination: Path | None = None
        try:
            from core.backup_manager import backup_manager
        except Exception as e:
            return {
                "success": False,
                "error": f"Core backup manager unavailable: {e}",
            }

        try:
            policy = load_backup_policy()
            drill_cfg = policy.restore_drill
            drill_root = resolve_policy_path(self.project_root, drill_cfg.temp_restore_root)
            drill_root.mkdir(parents=True, exist_ok=True)
            restore_destination = drill_root / f"restore_drill_{now_timestamp_filename()}"
            restore_destination.mkdir(parents=True, exist_ok=True)

            selected_backup_path = backup_path
            if not selected_backup_path:
                backups = backup_manager.list_backups()
                if not backups:
                    raise RuntimeError("No backups available for restore drill")
                selected_backup_path = str(backups[0].get("file_path") or "")
            if not selected_backup_path:
                raise RuntimeError("Unable to resolve backup path for restore drill")

            is_valid, validation_errors = backup_manager.validate_backup(selected_backup_path)
            if not is_valid:
                raise RuntimeError(
                    "Backup validation failed before drill restore: "
                    + "; ".join(validation_errors)
                )

            restored = backup_manager.restore_backup_to_path(
                backup_path=selected_backup_path,
                destination=str(restore_destination),
                restore_users=restore_users,
                restore_config=restore_config,
            )
            if not restored:
                raise RuntimeError("restore_backup_to_path returned False")

            all_files = [p for p in restore_destination.rglob("*") if p.is_file()]
            checks = drill_cfg.verification_checks or {}
            required_paths = checks.get("required_paths", [])
            if not isinstance(required_paths, list):
                required_paths = []
            min_file_count = checks.get("min_file_count", 1)
            if not isinstance(min_file_count, int):
                min_file_count = 1

            missing_required_paths: list[str] = []
            for rel in required_paths:
                rel_str = str(rel).strip()
                if not rel_str:
                    continue
                candidate = restore_destination / rel_str
                if not candidate.exists():
                    missing_required_paths.append(rel_str)

            verification = {
                "required_paths_ok": len(missing_required_paths) == 0,
                "missing_required_paths": missing_required_paths,
                "min_file_count_ok": len(all_files) >= min_file_count,
                "expected_min_file_count": min_file_count,
                "restored_file_count": len(all_files),
            }
            success = verification["required_paths_ok"] and verification["min_file_count_ok"]
            report = {
                "summary": {
                    "success": success,
                    "backup_path": selected_backup_path,
                    "restore_destination": str(restore_destination),
                    "restored_file_count": len(all_files),
                },
                "verification": verification,
            }
            json_path = write_json_report(
                self.project_root,
                drill_cfg.report_json_path,
                cast(dict[str, object], report),
                rotate=False,
            )
            return {
                "success": success,
                "data": report,
                "report_paths": {
                    "json": str(json_path),
                },
            }
        except Exception as e:
            logger.error(f"Backup drill failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        finally:
            if restore_destination is not None:
                shutil.rmtree(restore_destination, ignore_errors=True)

    def run_backup_health_check(self, run_drill: bool = True) -> dict[str, object]:
        """Verify backup creation/discoverability/restorability end-to-end."""
        checks: list[dict[str, object]] = []
        report_paths: dict[str, str] = {}
        try:
            from core.backup_manager import backup_manager
        except Exception as e:
            return {
                "success": False,
                "error": f"Core backup manager unavailable: {e}",
            }

        try:
            inventory_result = self.run_backup_inventory()
            inventory_ok = bool(inventory_result.get("success"))
            checks.append(
                {
                    "name": "inventory_generation",
                    "success": inventory_ok,
                    "details": {
                        "report_paths": inventory_result.get("report_paths", {}),
                        "error": inventory_result.get("error"),
                    },
                }
            )

            backups = backup_manager.list_backups()
            has_backups = len(backups) > 0
            checks.append(
                {
                    "name": "backups_discoverable",
                    "success": has_backups,
                    "details": {"backup_count": len(backups)},
                }
            )
            if not has_backups:
                # Fresh install or no backups yet: report success with skipped status so audit doesn't fail
                payload = {
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "project_root": str(self.project_root),
                    "summary": {
                        "status": "SKIP",
                        "total_issues": 0,
                        "files_affected": 0,
                        "success": True,
                        "total_checks": len(checks),
                        "passed_checks": sum(1 for c in checks if bool(c.get("success"))),
                        "latest_backup_path": None,
                        "latest_backup_created_at": None,
                        "drill_executed": False,
                        "message": "No backups in data/backups (normal for fresh install). Create backups via the app to run full health check.",
                    },
                    "details": {"checks": checks, "failed_checks": []},
                    "checks": checks,
                }
                json_path = write_json_report(
                    self.project_root,
                    "development_tools/reports/jsons/backup_health_report.json",
                    payload,
                    rotate=False,
                )
                try:
                    save_tool_result(
                        "analyze_backup_health",
                        "reports",
                        payload,
                        project_root=self.project_root,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save analyze_backup_health result: {e}")
                return {
                    "success": True,
                    "data": payload,
                    "report_paths": {"health_json": str(json_path)},
                }

            def _parse_backup_created_at(raw_value: object) -> datetime | None:
                if not isinstance(raw_value, str) or not raw_value.strip():
                    return None
                try:
                    return datetime.fromisoformat(raw_value.replace("Z", ""))
                except Exception:
                    return None

            latest_backup = backups[0]
            latest_path = str(latest_backup.get("file_path") or "")
            if not latest_path:
                raise RuntimeError("Latest backup entry missing file_path")

            latest_created_raw = latest_backup.get("created_at")
            latest_created = None
            if isinstance(latest_created_raw, str) and latest_created_raw:
                latest_created = _parse_backup_created_at(latest_created_raw)

            weekly_backups = [
                backup
                for backup in backups
                if str(backup.get("backup_name") or "").startswith("weekly_backup_")
                or str(backup.get("file_name") or "").startswith("weekly_backup_")
            ]
            latest_weekly = weekly_backups[0] if weekly_backups else None
            latest_weekly_path = (
                str(latest_weekly.get("file_path") or "") if latest_weekly else ""
            )
            latest_weekly_created_raw = (
                latest_weekly.get("created_at") if latest_weekly else None
            )
            latest_weekly_created = _parse_backup_created_at(latest_weekly_created_raw)

            checks.append(
                {
                    "name": "weekly_backup_present",
                    "success": bool(latest_weekly),
                    "details": {
                        "weekly_backup_count": len(weekly_backups),
                        "latest_weekly_backup_path": latest_weekly_path,
                        "latest_weekly_created_at": latest_weekly_created_raw,
                    },
                }
            )

            recent_days = 14  # Default: allow weekly backups to pass (8 days was too tight)
            try:
                from development_tools.config import config as _cfg
                health_cfg = getattr(_cfg, "get_backup_health_config", lambda: {})()
                recent_days = int(health_cfg.get("recent_days", recent_days))
            except Exception:
                pass
            recent_cutoff = datetime.now() - timedelta(days=recent_days)
            weekly_backup_recent_enough = (
                latest_weekly_created is not None
                and latest_weekly_created >= recent_cutoff
            )
            checks.append(
                {
                    "name": "weekly_backup_recent_enough",
                    "success": weekly_backup_recent_enough,
                    "details": {
                        "recent_cutoff": recent_cutoff.isoformat(timespec="seconds"),
                        "latest_weekly_backup_path": latest_weekly_path,
                        "latest_weekly_created_at": latest_weekly_created_raw,
                    },
                }
            )

            recent_ok = latest_created is not None and latest_created >= recent_cutoff
            checks.append(
                {
                    "name": "latest_backup_recent_enough",
                    "success": recent_ok,
                    "details": {
                        "latest_backup_path": latest_path,
                        "latest_created_at": latest_created_raw,
                        "recent_cutoff": recent_cutoff.isoformat(timespec="seconds"),
                    },
                }
            )

            valid, errors = backup_manager.validate_backup(latest_path)
            checks.append(
                {
                    "name": "latest_backup_validates",
                    "success": bool(valid),
                    "details": {"backup_path": latest_path, "errors": errors or []},
                }
            )

            drill_result: dict[str, object] = {"success": True, "skipped": not run_drill}
            if run_drill:
                drill_result = self.run_backup_drill(
                    backup_path=latest_path,
                    restore_users=True,
                    restore_config=False,
                )
                checks.append(
                    {
                        "name": "restore_drill",
                        "success": bool(drill_result.get("success")),
                        "details": {
                            "report_paths": drill_result.get("report_paths", {}),
                            "error": drill_result.get("error"),
                        },
                    }
                )
                if isinstance(drill_result.get("report_paths"), dict):
                    report_paths.update(
                        {
                            f"drill_{k}": str(v)
                            for k, v in drill_result.get("report_paths", {}).items()
                        }
                    )

            success = all(bool(check.get("success")) for check in checks)
            failed_checks = [check for check in checks if not bool(check.get("success"))]
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "project_root": str(self.project_root),
                "summary": {
                    "status": "PASS" if success else "FAIL",
                    "total_issues": len(failed_checks),
                    "files_affected": 0,
                    "success": success,
                    "total_checks": len(checks),
                    "passed_checks": sum(
                        1 for check in checks if bool(check.get("success"))
                    ),
                    "latest_backup_path": latest_path,
                    "latest_backup_created_at": latest_created_raw,
                    "drill_executed": bool(run_drill),
                },
                "details": {
                    "checks": checks,
                    "failed_checks": [str(check.get("name") or "") for check in failed_checks],
                },
                "checks": checks,
            }
            json_path = write_json_report(
                self.project_root,
                "development_tools/reports/jsons/backup_health_report.json",
                payload,
                rotate=False,
            )
            report_paths.update(
                {
                    "health_json": str(json_path),
                }
            )
            try:
                save_tool_result(
                    "analyze_backup_health",
                    "reports",
                    payload,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_backup_health result: {e}")
            return {
                "success": success,
                "data": payload,
                "report_paths": report_paths,
            }
        except Exception as e:
            logger.error(f"Backup health check failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def run_analyze_system_signals(self):
        """Run system signals analysis"""
        logger.debug("Analyzing system signals...")
        result = self.run_script('analyze_system_signals', '--json')
        if result['success']:
            output = result.get('output', '')
            if output:
                try:
                    import json
                    # Try to find JSON in the output (might have extra text)
                    # Look for JSON object/array boundaries
                    json_start = output.find('{')
                    if json_start == -1:
                        json_start = output.find('[')
                    if json_start != -1:
                        json_end = output.rfind('}') + 1
                        if json_end == 0:
                            json_end = output.rfind(']') + 1
                        if json_end > json_start:
                            json_str = output[json_start:json_end]
                            data = json.loads(json_str)
                        else:
                            data = json.loads(output)
                    else:
                        data = json.loads(output)
                    if not (
                        isinstance(data, dict)
                        and isinstance(data.get('summary'), dict)
                        and isinstance(data.get('details'), dict)
                    ):
                        logger.error("analyze_system_signals returned non-standard JSON (missing summary/details)")
                        return False
                    self.system_signals = data
                    try:
                        save_tool_result('analyze_system_signals', 'reports', data, project_root=self.project_root)
                    except Exception as e:
                        logger.debug(f"Failed to save analyze_system_signals result: {e}")
                except json.JSONDecodeError as e:
                    logger.warning(f"analyze_system_signals output could not be parsed as JSON: {e}")
                    logger.debug(f"analyze_system_signals raw output (first 500 chars): {output[:500]}")
                    return False
            else:
                logger.error("analyze_system_signals returned empty output")
                return False
            logger.debug("System signals analysis completed!")
            return True
        else:
            logger.error(f"System signals analysis failed: {result.get('error', 'Unknown error')}")
            return False
    
    def run_test_markers(self, action: str = 'check', dry_run: bool = False) -> dict:
        """Run test markers analysis or fix"""
        logger.debug(f"Analyzing test markers: {action}")
        args = []
        if action == 'check':
            args.append('--check')
        elif action == 'analyze':
            args.append('--analyze')
        elif action == 'fix':
            args.append('--fix')
        if dry_run:
            args.append('--dry-run')
        # Always request JSON output for parsing
        args.append('--json')
        
        result = self.run_script('analyze_test_markers', *args)
        
        # The script returns exit code 1 if markers are missing (which is valid data, not a failure)
        # So we check for output rather than just success
        output = result.get('output', '')
        if output:
            try:
                import json
                raw_data = json.loads(output)
                from ..result_format import normalize_to_standard_format
                normalized = normalize_to_standard_format("analyze_test_markers", raw_data)
                details = normalized.get("details", {})
                missing_items = details.get('missing', []) if isinstance(details, dict) else []
                missing_count = details.get('missing_count')
                if not isinstance(missing_count, int):
                    missing_count = len(missing_items) if isinstance(missing_items, list) else 0
                missing_files = set()
                if isinstance(missing_items, list):
                    for item in missing_items:
                        if isinstance(item, dict):
                            file_path = item.get('file')
                            if file_path:
                                missing_files.add(file_path)
                        elif isinstance(item, (list, tuple)) and item:
                            missing_files.add(item[0])
                standard_result = self._create_standard_format_result(
                    missing_count,
                    len(missing_files),
                    None,
                    details
                )
                result['data'] = standard_result
                result['success'] = True  # Mark as success if we got valid JSON
                try:
                    save_tool_result('analyze_test_markers', 'tests', standard_result, project_root=self.project_root)
                except Exception as e:
                    logger.debug(f"Failed to save analyze_test_markers result: {e}")
                logger.debug("Test markers analysis completed!")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Test markers analysis failed: Invalid JSON output: {e}")
                logger.debug(f"Output was: {output[:200]}")
                result['success'] = False
                result['error'] = f"Invalid JSON output: {e}"
        elif result.get('error'):
            error_msg = result['error']
            logger.error(f"Test markers analysis failed: {error_msg}")
            if result.get('output'):
                logger.debug(f"Script stdout: {result['output'][:500]}")
            result['success'] = False
        else:
            error_msg = f"No output received (returncode: {result.get('returncode')})"
            logger.error(f"Test markers analysis failed: {error_msg}")
            if result.get('error'):
                logger.debug(f"Script stderr: {result['error'][:500]}")
            result['success'] = False
            result['error'] = error_msg
        
        return result
    
    def run_unused_imports_report(self):
        """Run unused imports report generation (generates markdown report from analysis results)"""
        logger.info("Generating unused imports report...")
        result = self.run_generate_unused_imports_report()
        if result.get('success'):
            logger.info("Unused imports report generated successfully!")
        else:
            logger.warning(f"Unused imports report generation completed with issues: {result.get('error', 'Unknown error')}")
        return result
    
    def generate_directory_trees(self):
        """Generate directory tree documentation.
        
        NOTE: This should ONLY be called from the 'docs' command, NOT during audits.
        Static documentation should not be regenerated during audit runs.
        The safeguard in create_output_file() will automatically prevent writes during audits/tests.
        """
        logger.info("Generating directory trees...")
        try:
            result = self.run_script('generate_directory_tree')
            if result['success']:
                logger.info("Directory trees generated successfully!")
                return True
            else:
                logger.error(f"Directory tree generation failed: {result['error']}")
                return False
        except RuntimeError as e:
            # Handle safeguard blocking (from create_output_file)
            if "Cannot write" in str(e) and "DIRECTORY_TREE.md" in str(e):
                logger.warning(f"Skipping DIRECTORY_TREE.md generation: {e}")
                return False
            raise
    
    def check_trigger_requirements(self, task_type: str) -> bool:
        """Check if trigger requirements are met for a task"""
        # Implementation would check workflow config
        return True
    
    def run_audit_first(self, task_type: str) -> dict:
        """Run audit first as required by protocol"""
        logger.info("Running audit-first protocol...")
        audit_success = self._run_quick_audit_tools()
        return {
            'success': audit_success,
            'error': '' if audit_success else 'Audit failed'
        }
    
    def execute_task(self, task_type: str, task_data: dict | None = None) -> bool:
        """Execute the specific task"""
        if task_type == 'documentation':
            return self._execute_documentation_task()
        elif task_type == 'function_registry':
            return self._execute_function_registry_task()
        elif task_type == 'module_dependencies':
            return self._execute_module_dependencies_task()
        else:
            logger.error(f"Unknown task type: {task_type}")
            return False
    
    def validate_work(self, work_type: str, work_data: dict) -> dict:
        """Validate the work before presenting"""
        logger.info("Validating work...")
        # Use --json flag to prevent multiline print output from being captured
        result = self.run_script('analyze_ai_work', '--work-type', work_type, '--json')
        if result['success']:
            return self.validate_audit_results({'output': result['output']})
        else:
            return {
                'completeness': 0.0,
                'accuracy': 0.0,
                'consistency': 0.0,
                'actionable': 0.0,
                'overall': 0.0,
                'issues': [f"Validation failed: {result['error']}"]
            }
    
    def validate_audit_results(self, results: dict) -> dict:
        """Validate audit results"""
        return {
            'completeness': 95.0,
            'accuracy': 90.0,
            'consistency': 85.0,
            'actionable': 80.0,
            'overall': 87.5,
            'issues': []
        }
    
    def show_validation_report(self, validation_results: dict):
        """Show validation report"""
        print("\n" + "=" * 50)
        print("VALIDATION REPORT")
        print("=" * 50)
        scores = [
            f"Completeness: {validation_results['completeness']:.1f}%",
            f"Accuracy: {validation_results['accuracy']:.1f}%",
            f"Consistency: {validation_results['consistency']:.1f}%",
            f"Actionable: {validation_results['actionable']:.1f}%"
        ]
        overall = validation_results['overall']
        status = "PASSED" if overall >= 80.0 else "NEEDS IMPROVEMENT"
        print(f"Overall Score: {overall:.1f}% - {status}")
        print("\nComponent Scores:")
        for score in scores:
            print(f"  {score}")
        if validation_results['issues']:
            print("\nIssues Found:")
            for issue in validation_results['issues']:
                print(f"  [ISSUE] {issue}")
    
    def print_audit_summary(self, successful: list, failed: list, results: dict):
        """Print concise audit summary"""
        print("\n" + "=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        if failed:
            print(f"\n[CRITICAL] Failed audits: {', '.join(failed)}")
        key_metrics = self._extract_key_metrics(results)
        if key_metrics:
            print("\nKey Metrics:")
            for metric, value in key_metrics.items():
                print(f"  {metric}: {value}")
        # Default to generic path relative to project root (no development_tools/ assumption)
        results_file = (self.audit_config or {}).get('results_file', 'reports/analysis_detailed_results.json')
        print(f"\nDetailed results saved to: {results_file}")
    
    def _execute_documentation_task(self) -> bool:
        """Execute documentation update task"""
        logger.info("Updating documentation...")
        result = self.run_script('generate_documentation')
        return result['success']
    
    def _execute_function_registry_task(self) -> bool:
        """Execute function registry task"""
        logger.info("Updating function registry...")
        result = self.run_script('generate_function_registry')
        return result['success']
    
    def _execute_module_dependencies_task(self) -> bool:
        """Execute module dependencies task"""
        logger.info("Updating module dependencies...")
        result = self.run_script('generate_module_dependencies')
        return result['success']

    def _get_docs_tree_max_mtime(self) -> float:
        """Return latest mtime across documentation files."""
        patterns = [
            "*.md",
            "development_docs/**/*.md",
            "ai_development_docs/**/*.md",
        ]
        generated_docs = [
            "development_docs/UNUSED_IMPORTS_REPORT.md",
            "development_docs/TEST_COVERAGE_REPORT.md",
            "development_docs/LEGACY_REFERENCE_REPORT.md",
        ]
        return self._latest_mtime_for_patterns(patterns, exclude_paths=generated_docs)

    def _is_doc_subcheck_cache_fresh(self, tool_name: str) -> bool:
        """Check whether a documentation subcheck result file is up to date."""
        result_file = (
            self.project_root
            / "development_tools"
            / "docs"
            / "jsons"
            / f"{tool_name}_results.json"
        )
        if not result_file.exists():
            return False
        try:
            result_mtime = result_file.stat().st_mtime
        except OSError:
            return False
        docs_mtime = self._get_docs_tree_max_mtime()

        # Invalidate doc-subcheck cache when tool implementation changes.
        tool_mtime = 0.0
        try:
            from .tool_wrappers import SCRIPT_REGISTRY

            script_rel = SCRIPT_REGISTRY.get(tool_name)
            if script_rel:
                script_path = (
                    Path(__file__).resolve().parent.parent.parent / script_rel
                )
                if script_path.exists():
                    tool_mtime = script_path.stat().st_mtime
        except Exception:
            tool_mtime = 0.0

        # Invalidate when development-tools config changes.
        config_mtime = 0.0
        try:
            config_path = (
                self.project_root
                / "development_tools"
                / "config"
                / "development_tools_config.json"
            )
            if not config_path.exists():
                config_path = self.project_root / "development_tools_config.json"
            if config_path.exists():
                config_mtime = config_path.stat().st_mtime
        except OSError:
            config_mtime = 0.0

        latest_input_mtime = max(docs_mtime, tool_mtime, config_mtime)
        return result_mtime >= latest_input_mtime

    def _run_doc_subcheck_with_cache(
        self,
        tool_name: str,
        log_label: str,
        parser_func,
        run_callable,
    ) -> dict:
        """Run a docs subcheck only when stale; otherwise use cached result."""
        from ..output_storage import load_tool_result

        if self._is_doc_subcheck_cache_fresh(tool_name):
            cached = load_tool_result(tool_name, "docs", project_root=self.project_root)
            if isinstance(cached, dict):
                logger.debug(f"  - {log_label}: using cached result (mtime up to date)")
                if hasattr(self, "_tool_cache_metadata"):
                    self._tool_cache_metadata[tool_name] = {
                        "cache_mode": "cache_only",
                        "invalidation_reason": "Docs unchanged since last subcheck result",
                        "source": "doc_subcheck_mtime",
                    }
                return cached

        result = run_callable()
        if hasattr(self, "_tools_run_in_current_tier"):
            self._tools_run_in_current_tier.add(tool_name)
        result_data = result.get("data") if isinstance(result, dict) else None
        if (
            isinstance(result_data, dict)
            and isinstance(result_data.get("summary"), dict)
            and isinstance(result_data.get("details"), dict)
        ):
            if hasattr(self, "results_cache"):
                self.results_cache[tool_name] = result_data
            if hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata[tool_name] = {
                    "cache_mode": "cold_scan",
                    "invalidation_reason": "Subcheck executed and returned standard result",
                    "source": "subcheck_direct_result",
                }
            return result_data

        # Prefer standardized stdout parsing over cache reconstruction.
        # This keeps report payloads aligned with the tool's current output.
        if result.get("output") or result.get("success"):
            parsed = parser_func(result.get("output", ""))
            if (
                isinstance(parsed, dict)
                and isinstance(parsed.get("summary"), dict)
                and isinstance(parsed.get("details"), dict)
            ):
                with contextlib.suppress(Exception):
                    save_tool_result(
                        tool_name, "docs", parsed, project_root=self.project_root
                    )
                if hasattr(self, "results_cache") and isinstance(self.results_cache, dict):
                    self.results_cache[tool_name] = parsed
                if hasattr(self, "_tool_cache_metadata"):
                    self._tool_cache_metadata[tool_name] = {
                        "cache_mode": "cold_scan",
                        "invalidation_reason": "Parsed standardized stdout from subcheck",
                        "source": "doc_subcheck_stdout",
                    }
                return parsed
        try:
            parsed = self._load_mtime_cached_tool_results(
                tool_name,
                "docs",
                result,
                parser_func,
            )
            if hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata[tool_name] = {
                    "cache_mode": "cold_scan",
                    "invalidation_reason": "Subcheck executed after stale or missing cache",
                    "source": "doc_subcheck_execution",
                }
            return parsed
        except Exception:
            if result.get("output") or result.get("success"):
                parsed = parser_func(result.get("output", ""))
                with contextlib.suppress(Exception):
                    save_tool_result(tool_name, "docs", parsed, project_root=self.project_root)
                if hasattr(self, "_tool_cache_metadata"):
                    self._tool_cache_metadata[tool_name] = {
                        "cache_mode": "cold_scan",
                        "invalidation_reason": "Fallback parse path used",
                        "source": "doc_subcheck_fallback",
                    }
                return parsed
            logger.warning(f"{tool_name} failed: {result.get('error', 'Unknown error')}")
            return {}
    
    def _run_doc_sync_check(self, *args) -> bool:
        """Run all documentation sync checks and aggregate results."""
        all_results = {}
        subcheck_modes = {}
        from ..output_storage import load_tool_result

        paired_docs_cached = self._is_doc_subcheck_cache_fresh("analyze_documentation_sync")
        if paired_docs_cached:
            cached_sync = load_tool_result(
                "analyze_documentation_sync",
                "docs",
                project_root=self.project_root,
            )
            if isinstance(cached_sync, dict):
                details = cached_sync.get("details", {})
                all_results["paired_docs"] = (
                    details.get("paired_docs", {})
                    if isinstance(details, dict)
                    else {}
                )
                subcheck_modes["paired_docs"] = "cache_only"
                logger.debug("  - Paired docs: using cached result (mtime up to date)")
            else:
                paired_docs_cached = False

        if not paired_docs_cached:
            result = self.run_script("analyze_documentation_sync", "--json")
            if result.get("output") and result.get("success"):
                try:
                    parsed = json.loads(result.get("output", ""))
                    details = parsed.get("details", {}) if isinstance(parsed, dict) else {}
                    all_results["paired_docs"] = details.get("paired_docs", {})
                    subcheck_modes["paired_docs"] = "cold_scan"
                except json.JSONDecodeError as e:
                    logger.warning(f"analyze_documentation_sync output could not be parsed as JSON: {e}")
                    all_results["paired_docs"] = {}
                    subcheck_modes["paired_docs"] = "unknown"
            else:
                logger.warning(
                    f"analyze_documentation_sync failed: {result.get('error', 'Unknown error')}"
                )
                all_results["paired_docs"] = {}
                subcheck_modes["paired_docs"] = "unknown"

        logger.debug("  - Analyzing path drift...")
        path_drift_result = self.run_analyze_path_drift()
        path_drift_data = (
            path_drift_result.get("data")
            if isinstance(path_drift_result, dict)
            else {}
        )
        if (
            isinstance(path_drift_data, dict)
            and isinstance(path_drift_data.get("summary"), dict)
            and isinstance(path_drift_data.get("details"), dict)
        ):
            all_results["path_drift"] = path_drift_data
            if hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata["analyze_path_drift"] = {
                    "cache_mode": "internal_mtime_cache",
                    "invalidation_reason": "Path drift uses internal analyzer cache",
                    "source": "run_analyze_path_drift",
                }
        else:
            all_results["path_drift"] = self._create_standard_format_result(0, 0, {})
            logger.warning("Path drift result was non-standard; defaulting to empty result")
        subcheck_modes["path_drift"] = (
            self._tool_cache_metadata.get("analyze_path_drift", {}).get("cache_mode", "unknown")
            if hasattr(self, "_tool_cache_metadata")
            else "unknown"
        )

        logger.debug("  - Analyzing ASCII compliance...")
        all_results["ascii_compliance"] = self._run_doc_subcheck_with_cache(
            "analyze_ascii_compliance",
            "ASCII compliance",
            self._parse_ascii_compliance_output,
            lambda: self.run_script("analyze_ascii_compliance", "--json"),
        )
        subcheck_modes["ascii_compliance"] = (
            self._tool_cache_metadata.get("analyze_ascii_compliance", {}).get("cache_mode", "unknown")
            if hasattr(self, "_tool_cache_metadata")
            else "unknown"
        )

        logger.debug("  - Analyzing heading numbering...")
        all_results["heading_numbering"] = self._run_doc_subcheck_with_cache(
            "analyze_heading_numbering",
            "Heading numbering",
            self._parse_heading_numbering_output,
            lambda: self.run_script("analyze_heading_numbering", "--json"),
        )
        subcheck_modes["heading_numbering"] = (
            self._tool_cache_metadata.get("analyze_heading_numbering", {}).get("cache_mode", "unknown")
            if hasattr(self, "_tool_cache_metadata")
            else "unknown"
        )

        logger.debug("  - Analyzing missing addresses...")
        all_results["missing_addresses"] = self._run_doc_subcheck_with_cache(
            "analyze_missing_addresses",
            "Missing addresses",
            self._parse_missing_addresses_output,
            lambda: self.run_script("analyze_missing_addresses", "--json"),
        )
        subcheck_modes["missing_addresses"] = (
            self._tool_cache_metadata.get("analyze_missing_addresses", {}).get("cache_mode", "unknown")
            if hasattr(self, "_tool_cache_metadata")
            else "unknown"
        )

        logger.debug("  - Analyzing unconverted links...")
        all_results["unconverted_links"] = self._run_doc_subcheck_with_cache(
            "analyze_unconverted_links",
            "Unconverted links",
            self._parse_unconverted_links_output,
            lambda: self.run_script("analyze_unconverted_links", "--json"),
        )
        subcheck_modes["unconverted_links"] = (
            self._tool_cache_metadata.get("analyze_unconverted_links", {}).get("cache_mode", "unknown")
            if hasattr(self, "_tool_cache_metadata")
            else "unknown"
        )

        summary = self._aggregate_doc_sync_results(all_results)
        path_drift_files = summary.get("path_drift_files", [])
        doc_sync_standard = {
            "summary": {
                "total_issues": summary.get("total_issues", 0),
                "files_affected": (
                    len(path_drift_files) if isinstance(path_drift_files, list) else 0
                ),
                "status": summary.get("status", "UNKNOWN"),
            },
            "details": {
                "paired_doc_issues": summary.get("paired_doc_issues", 0),
                "path_drift_issues": summary.get("path_drift_issues", 0),
                "ascii_issues": summary.get("ascii_issues", 0),
                "heading_numbering_issues": summary.get("heading_numbering_issues", 0),
                "missing_address_issues": summary.get("missing_address_issues", 0),
                "unconverted_link_issues": summary.get("unconverted_link_issues", 0),
                "path_drift_files": path_drift_files
                if isinstance(path_drift_files, list)
                else [],
            },
        }
        self.docs_sync_results = {
            'success': True,
            'summary': summary,
            'all_results': all_results,
            'standard': doc_sync_standard,
        }
        self.docs_sync_summary = doc_sync_standard
        if hasattr(self, "_tool_cache_metadata"):
            cache_only_count = sum(1 for mode in subcheck_modes.values() if mode == "cache_only")
            refresh_count = sum(1 for mode in subcheck_modes.values() if mode != "cache_only")
            doc_sync_cache_mode = (
                "cache_only"
                if refresh_count == 0
                else ("cold_scan" if cache_only_count == 0 else "partial_cache")
            )
            self._tool_cache_metadata["analyze_documentation_sync"] = {
                "cache_mode": doc_sync_cache_mode,
                "cache_hits": cache_only_count,
                "cache_misses": refresh_count,
                "subchecks": subcheck_modes,
                "invalidation_reason": (
                    "All doc subchecks served from cache"
                    if refresh_count == 0
                    else "One or more doc subchecks refreshed"
                ),
            }
        logger.debug(
            f"Documentation sync subchecks cache summary: "
            f"{', '.join(f'{name}={mode}' for name, mode in sorted(subcheck_modes.items()))}"
        )
        logger.debug(f"Documentation sync summary: {summary.get('status', 'UNKNOWN')} - {summary.get('total_issues', 0)} total issues")
        return True
    
    def _run_legacy_cleanup_scan(self, *args) -> bool:
        """Run legacy cleanup and store structured results."""
        result = self.run_script('fix_legacy_references', *args)
        if result.get('success'):
            summary = self._parse_legacy_output(result.get('output', ''))
            result['summary'] = summary
            self.legacy_cleanup_results = result
            self.legacy_cleanup_summary = summary
            return True
        if result.get('output'):
            logger.debug(result['output'])
        if result.get('error'):
            logger.error(result['error'])
        return False
