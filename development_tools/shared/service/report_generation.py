"""
Report generation methods for AIToolsService.

Contains methods for generating AI_STATUS.md, AI_PRIORITIES.md, and CONSOLIDATED_REPORT.md.
These methods are large (~4,300 lines total) and generate comprehensive status reports.
"""

# pyright: reportAttributeAccessIssue=false, reportGeneralTypeIssues=false

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import audit orchestration helper
from .audit_orchestration import _is_audit_in_progress
from .report_generation_linkify import linkify_review_paths_bullet as _linkify_review_paths_bullet


class ReportGenerationMixin:
    """Mixin class providing report generation methods to AIToolsService."""

    def _is_dev_tools_scoped_report(self) -> bool:
        """True when reports are written for DEV_TOOLS_*.md (dev-tools-only audit)."""
        return bool(getattr(self, "dev_tools_only_mode", False))

    def _path_is_under_development_tools_dir(self, path_str: str) -> bool:
        """True if ``path_str`` resolves under ``project_root/development_tools``."""
        if not path_str or not isinstance(path_str, str):
            return False
        try:
            root = self.project_root.resolve()
            anchor = (root / "development_tools").resolve()
            raw = Path(path_str.strip())
            candidate = (raw if raw.is_absolute() else (root / path_str)).resolve()
            return anchor in candidate.parents or candidate == anchor
        except (OSError, ValueError, RuntimeError):
            norm = path_str.replace("\\", "/").strip().lstrip("./")
            return (
                norm.startswith("development_tools/")
                or norm == "development_tools"
            )

    def _filter_duplicate_groups_dev_tools(
        self, groups: list[Any]
    ) -> list[Any]:
        """Keep duplicate groups where every function maps to a file under development_tools/."""
        out: list[Any] = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            funcs = group.get("functions", [])
            if not isinstance(funcs, list) or not funcs:
                continue
            paths: list[str] = []
            for fn in funcs:
                if isinstance(fn, dict):
                    fp = fn.get("file", "")
                    if fp:
                        paths.append(str(fp))
            if not paths:
                continue
            if all(self._path_is_under_development_tools_dir(p) for p in paths):
                out.append(group)
        return out

    def _count_duplicate_affected_files_dev_tools(self, groups: list[Any]) -> int:
        files: set[str] = set()
        for group in groups:
            if not isinstance(group, dict):
                continue
            for fn in group.get("functions", []) or []:
                if isinstance(fn, dict) and fn.get("file"):
                    p = str(fn["file"])
                    if self._path_is_under_development_tools_dir(p):
                        files.add(p.replace("\\", "/"))
        return len(files)

    def _count_duplicate_affected_files(self, groups: list[Any]) -> int:
        """Count unique files represented by duplicate-function groups."""
        files: set[str] = set()
        for group in groups:
            if not isinstance(group, dict):
                continue
            for fn in group.get("functions", []) or []:
                if not isinstance(fn, dict):
                    continue
                path_value = str(fn.get("file", "")).strip()
                if path_value:
                    files.add(path_value.replace("\\", "/"))
        return len(files)

    def _filter_circular_dependencies_dev_tools(self, chains: list[Any]) -> list[Any]:
        """Keep dependency cycles that involve at least one module under ``development_tools/``."""
        out: list[Any] = []
        for chain in chains:
            if not isinstance(chain, list):
                continue
            paths = [p for p in chain if isinstance(p, str) and p.strip()]
            if paths and any(
                self._path_is_under_development_tools_dir(p) for p in paths
            ):
                out.append(chain)
        return out

    def _filter_high_coupling_dev_tools(
        self, items: list[Any]
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict) and self._path_is_under_development_tools_dir(
                str(item.get("file", ""))
            ):
                out.append(item)
        return out

    def _scoped_obvious_unused_import_metrics(
        self, unused_imports_data: dict[str, Any]
    ) -> tuple[int, int, dict[str, int]]:
        """Metrics for obvious/type-hint unused imports limited to ``development_tools/`` files."""
        details = (
            unused_imports_data.get("details", {})
            if isinstance(unused_imports_data, dict)
            else {}
        )
        findings = details.get("findings", {}) if isinstance(details, dict) else {}
        if not isinstance(findings, dict):
            findings = {}
        obvious_list = findings.get("obvious_unused", [])
        if not isinstance(obvious_list, list):
            obvious_list = []
        scoped_obvious = [
            x
            for x in obvious_list
            if isinstance(x, dict)
            and self._path_is_under_development_tools_dir(str(x.get("file", "")))
        ]
        type_list = findings.get("type_hints_only", [])
        if not isinstance(type_list, list):
            type_list = []
        type_scoped = sum(
            1
            for x in type_list
            if isinstance(x, dict)
            and self._path_is_under_development_tools_dir(str(x.get("file", "")))
        )
        per_file: dict[str, int] = {}
        for x in scoped_obvious:
            fp = str(x.get("file", "")).strip()
            if fp:
                per_file[fp] = per_file.get(fp, 0) + 1
        return len(scoped_obvious), type_scoped, per_file

    def _scoped_unused_imports_status_metrics(
        self, unused_imports_data: dict[str, Any]
    ) -> tuple[int, int, dict[str, int]] | None:
        """Per-category counts and totals for unused imports in ``development_tools/`` only."""
        details = (
            unused_imports_data.get("details", {})
            if isinstance(unused_imports_data, dict)
            else {}
        )
        findings = details.get("findings", {}) if isinstance(details, dict) else {}
        if not isinstance(findings, dict) or not findings:
            return None
        by_cat: dict[str, int] = {}
        files_set: set[str] = set()
        for cat, items in findings.items():
            if not isinstance(items, list):
                continue
            for x in items:
                if not isinstance(x, dict):
                    continue
                if not self._path_is_under_development_tools_dir(
                    str(x.get("file", ""))
                ):
                    continue
                by_cat[cat] = by_cat.get(cat, 0) + 1
                fp = str(x.get("file", "")).strip()
                if fp:
                    files_set.add(fp)
        total = sum(by_cat.values())
        if total <= 0:
            return 0, 0, {}
        return total, len(files_set), by_cat

    def _audit_source_cmd_display(self, base_cmd: str) -> str:
        """Append --dev-tools-only to documented source command when scope is restricted."""
        if self._is_dev_tools_scoped_report() and "--dev-tools-only" not in base_cmd:
            return f"{base_cmd} --dev-tools-only"
        return base_cmd

    def _resolve_report_path(self, report_path: str) -> Path:
        """Helper to resolve relative report paths to absolute paths."""
        if isinstance(report_path, str):
            if not Path(report_path).is_absolute():
                return self.project_root / report_path
            else:
                return Path(report_path)
        else:
            return (
                Path(report_path) if not isinstance(report_path, Path) else report_path
            )

    def _markdown_href_from_dev_tools_report(self, target: Path) -> str:
        """Relative URL for links in ``development_tools/*.md`` (repo root is one level up)."""
        base = (self.project_root / "development_tools").resolve()
        dest = Path(target).resolve()
        return Path(os.path.relpath(dest, base)).as_posix()

    def _get_results_file_path(self) -> Path:
        """Get the results file path from config."""
        # Default matches development_tools_config.json
        results_file_path = (self.audit_config or {}).get(
            "results_file", "development_tools/reports/analysis_detailed_results.json"
        )
        from ..audit_storage_scope import (
            STORAGE_SCOPE_DEV_TOOLS,
            STORAGE_SCOPE_FULL,
            scoped_analysis_detailed_path,
        )

        scope = (
            STORAGE_SCOPE_DEV_TOOLS
            if self._is_dev_tools_scoped_report()
            else STORAGE_SCOPE_FULL
        )
        return scoped_analysis_detailed_path(
            self.project_root,
            configured_relative=results_file_path,
            audit_scope=scope,
        )

    def _is_test_directory(self, path: Path) -> bool:
        """Check if path is within a test directory to avoid loading large result files.

        This is critical for preventing memory leaks in parallel test execution.
        """
        try:
            path_str = str(path.resolve()).replace("\\", "/").lower()

            # Check for Windows temp directories (most common case for pytest-xdist)
            # Windows temp dirs are typically: C:\Users\...\AppData\Local\Temp\...
            if "appdata" in path_str and ("temp" in path_str or "tmp" in path_str):
                return True

            # Check for pytest temp directories (pytest-xdist creates these)
            if "pytest" in path_str and ("temp" in path_str or "tmp" in path_str):
                return True

            # Check for common temp directory patterns
            test_indicators = [
                "/tmp",  # nosec B108 — path substring markers for test/temp detection
                "/temp",  # nosec B108
                "/tests/",
                "/test/",  # Test directories
                "tests/data/",
                "tests/fixtures/",
                "tests/temp/",
                "demo_project",  # Demo project used in tests
                "pytest-",
                "pytest_of_",  # pytest temp directories
            ]
            if any(indicator in path_str for indicator in test_indicators):
                return True

            # Additional check: if path contains a tempfile pattern (tmpXXXXXX)
            import re

            return bool(re.search(r"[\\/]tmp[a-z0-9]{6,}[\\/]", path_str))
        except Exception as e:
            # If we can't determine, be conservative and assume it's not a test directory
            # But log it so we can debug
            logger.debug(f"Error checking if path is test directory ({path}): {e}")
            return False

    def _load_results_file_safe(self) -> dict | None:
        """Load analysis_detailed_results.json if it exists and we're not in a test directory.

        Returns None if in test directory or file doesn't exist to prevent loading large files in tests.
        """
        if self._is_test_directory(self.project_root):
            return None
        results_file = self._get_results_file_path()
        if not results_file.exists():
            return None
        try:
            import json

            with open(results_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _get_decision_support_details(self, data: Any) -> dict[str, Any]:
        """Return decision_support details only when data is standard format."""
        if not isinstance(data, dict):
            return {}
        try:
            from ..result_format import normalize_to_standard_format

            normalized = normalize_to_standard_format("decision_support", data)
        except ValueError:
            return {}
        details = normalized.get("details", {})
        return details if isinstance(details, dict) else {}

    def _get_system_signals_details(self, data: Any) -> dict[str, Any]:
        """Return system_signals details only when data is standard format."""
        if not isinstance(data, dict):
            return {}
        try:
            from ..result_format import normalize_to_standard_format

            normalized = normalize_to_standard_format("analyze_system_signals", data)
        except ValueError:
            return {}
        details = normalized.get("details", {})
        return details if isinstance(details, dict) else {}

    def _get_static_analysis_snapshot(self) -> dict[str, dict[str, Any]]:
        """Load normalized summary/details for static analysis tools (ruff, pyright, bandit, pip-audit)."""
        result: dict[str, dict[str, Any]] = {}
        for tool_name in (
            "analyze_ruff",
            "analyze_pyright",
            "analyze_bandit",
            "analyze_pip_audit",
        ):
            tool_data = self._load_tool_data(
                tool_name, "static_checks", log_source=False
            )
            if not isinstance(tool_data, dict):
                result[tool_name] = {
                    "available": False,
                    "summary": {"total_issues": 0, "files_affected": 0, "status": "WARN"},
                    "details": {},
                }
                continue
            summary = tool_data.get("summary", {})
            details = tool_data.get("details", {})
            if not isinstance(summary, dict):
                summary = {}
            if not isinstance(details, dict):
                details = {}
            tool_available = bool(details.get("tool_available", True))
            result[tool_name] = {
                "available": tool_available,
                "summary": {
                    "total_issues": self._coerce_int(summary.get("total_issues"), 0),
                    "files_affected": self._coerce_int(summary.get("files_affected"), 0),
                    "status": str(summary.get("status", "UNKNOWN")),
                },
                "details": details,
            }
        return result

    def _pip_audit_elapsed_suffix(self, details: dict[str, Any]) -> str:
        """Clarify pip-audit timing semantics for consolidated-style static-analysis lines (V5 §4.3)."""
        if not isinstance(details, dict):
            return ""
        state = str(details.get("pip_audit_execution_state") or "").strip()
        if state == "executed_subprocess":
            sub = details.get("pip_audit_subprocess_seconds")
            if sub is not None:
                try:
                    return f" — pip-audit subprocess ~{float(sub):.2f}s"
                except (TypeError, ValueError):
                    return ""
            return ""
        if state == "requirements_lock_cache_hit":
            return " — reused cached pip-audit JSON (requirements unchanged)"
        if state == "skipped_env":
            return " — pip-audit subprocess skipped (MHM_PIP_AUDIT_SKIP)"
        return ""

    def _extract_file_issue_counts(self, tool_data: Any) -> dict[str, int]:
        """Extract per-file issue counts from standardized tool payload."""
        if not isinstance(tool_data, dict):
            return {}
        file_counts: dict[str, int] = {}
        files_section = tool_data.get("files", {})
        if isinstance(files_section, dict):
            for file_path, value in files_section.items():
                try:
                    file_counts[str(file_path)] = int(value)
                except (TypeError, ValueError):
                    continue
        if file_counts:
            return file_counts
        details = tool_data.get("details", {})
        detailed_issues = (
            details.get("detailed_issues", {}) if isinstance(details, dict) else {}
        )
        if isinstance(detailed_issues, dict):
            for file_path, issues in detailed_issues.items():
                if isinstance(issues, list):
                    file_counts[str(file_path)] = len(issues)
                elif isinstance(issues, int):
                    file_counts[str(file_path)] = issues
        return file_counts

    def _coerce_int(self, value: Any, default: int = 0) -> int:
        """Best-effort int coercion for report metrics."""
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    def _normalize_test_node_id(self, node_id: str) -> str:
        """Normalize pytest node IDs for compact display (drop class segment)."""
        text = str(node_id or "").strip()
        if not text:
            return ""
        parts = text.split("::")
        if len(parts) >= 3:
            return f"{parts[0]}::{parts[-1]}"
        return text

    def _get_track_failed_nodes(self, outcome: dict[str, Any]) -> list[str]:
        """Return normalized, de-duplicated failed node IDs for a single track."""
        nodes = outcome.get("failed_node_ids", []) if isinstance(outcome, dict) else []
        if not isinstance(nodes, list):
            return []
        normalized: list[str] = []
        for node in nodes:
            normalized_node = self._normalize_test_node_id(str(node))
            if normalized_node and normalized_node not in normalized:
                normalized.append(normalized_node)
        return normalized

    def _format_track_classification_summary(
        self, label: str, outcome: dict[str, Any]
    ) -> str:
        """Build concise track classification summary for Tier 3 sections."""
        classification = self._track_classification_label(outcome)
        reason = str(outcome.get("classification_reason", "unknown"))
        if reason in {"", "unknown"}:
            reason = classification
        return_hex = outcome.get("return_code_hex")
        log_file = outcome.get("log_file")
        pieces = [f"- **{label} Classification**: {classification} (reason={reason})"]
        if return_hex:
            pieces.append(f"return_hex={return_hex}")
        if classification not in {"passed", "skipped", "unknown"}:
            if isinstance(log_file, str) and log_file.strip():
                pieces.append(f"log={log_file.strip()}")
            context = outcome.get("actionable_context")
            if isinstance(context, str) and context.strip():
                pieces.append(f"hint={context.strip()}")
        return " | ".join(pieces)

    def _track_classification_label(self, outcome: dict[str, Any]) -> str:
        """Return the normalized track classification label."""
        if not isinstance(outcome, dict):
            return "unknown"
        classification = outcome.get("classification")
        if isinstance(classification, str) and classification.strip():
            return classification.strip()
        return "unknown"

    def _tier3_track_skipped_for_audit_scope(self, track: dict[str, Any]) -> bool:
        """True when Tier 3 split (full-repo vs --dev-tools-only) intentionally did not run this track."""
        if not isinstance(track, dict):
            return False
        return track.get("classification_reason") == "not_run_this_audit_scope"

    def _get_code_docstring_metrics(
        self, function_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Return code-docstring metrics from analyze_functions (canonical source)."""
        data = function_data
        if not isinstance(data, dict):
            data = self._load_tool_data(
                "analyze_functions", "functions", log_source=False
            )
        if not isinstance(data, dict):
            return {"total": 0, "undocumented": 0, "documented": 0, "coverage": None}
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        total = self._coerce_int(
            details.get("total_functions", data.get("total_functions", 0))
        )
        undocumented = self._coerce_int(
            details.get("undocumented", data.get("undocumented", 0))
        )
        if total < 0:
            total = 0
        if undocumented < 0:
            undocumented = 0
        if total and undocumented > total:
            undocumented = total
        documented = max(total - undocumented, 0)
        coverage = ((documented / total) * 100) if total > 0 else None
        return {
            "total": total,
            "undocumented": undocumented,
            "documented": documented,
            "coverage": coverage,
        }

    def _get_tier3_test_outcome(self) -> dict[str, Any]:
        """Load Tier 3 test outcome state from in-memory or cached results."""
        in_memory = getattr(self, "tier3_test_outcome", None)
        if isinstance(in_memory, dict) and in_memory.get("state"):
            return in_memory
        coverage_result = self._load_tool_data(
            "analyze_test_coverage", "tests", log_source=False
        )
        if not isinstance(coverage_result, dict):
            return {}
        details = coverage_result.get("details", {})
        if isinstance(details, dict):
            outcome = details.get("tier3_test_outcome", {})
            if isinstance(outcome, dict):
                if not isinstance(outcome.get("development_tools"), dict):
                    dev_tools_result = self._load_tool_data(
                        "generate_dev_tools_coverage", "tests", log_source=False
                    )
                    if isinstance(dev_tools_result, dict):
                        dev_details = dev_tools_result.get("details", {})
                        if isinstance(dev_details, dict):
                            dev_outcome = dev_details.get("dev_tools_test_outcome", {})
                            if isinstance(dev_outcome, dict):
                                outcome = {**outcome, "development_tools": dev_outcome}
                return outcome
        return {}

    def _effective_tier3_state_from_outcome(self, outcome: dict[str, Any]) -> str:
        """Return effective Tier 3 state including development-tools test outcome."""
        state = outcome.get("state", "") if isinstance(outcome, dict) else ""

        if state == "coverage_failed":
            return "coverage_failed"
        if not isinstance(outcome, dict):
            return "unknown"
        parallel = (
            outcome.get("parallel", {})
            if isinstance(outcome.get("parallel"), dict)
            else {}
        )
        no_parallel = (
            outcome.get("no_parallel", {})
            if isinstance(outcome.get("no_parallel"), dict)
            else {}
        )
        dev_tools = (
            outcome.get("development_tools", {})
            if isinstance(outcome.get("development_tools"), dict)
            else {}
        )
        track_labels = (
            self._track_classification_label(parallel),
            self._track_classification_label(no_parallel),
            self._track_classification_label(dev_tools),
        )
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

    def _get_recent_tier3_log_files(
        self,
        include_parallel: bool = False,
        include_no_parallel: bool = False,
        include_dev_tools: bool = False,
    ) -> list[str]:
        """Return latest Tier 3 pytest stdout log files for applicable tracks."""
        logs_dir = self.project_root / "development_tools" / "tests" / "logs"
        if not logs_dir.exists():
            return []

        selections: list[str] = []
        track_patterns = [
            (include_parallel, "pytest_parallel_stdout_*.log"),
            (include_no_parallel, "pytest_no_parallel_stdout_*.log"),
            (include_dev_tools, "pytest_dev_tools_stdout_*.log"),
        ]
        for include_track, pattern in track_patterns:
            if not include_track:
                continue
            matches = sorted(
                logs_dir.glob(pattern),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if not matches:
                continue
            latest = matches[0]
            try:
                rel = latest.relative_to(self.project_root)
                selections.append(str(rel).replace("\\", "/"))
            except ValueError:
                selections.append(str(latest).replace("\\", "/"))

        return selections

    def _append_tier3_test_outcome_lines(
        self, lines: list[str], actionable_only: bool = False
    ) -> None:
        """Append a consistent Tier 3 test outcome summary to report lines."""
        outcome = self._get_tier3_test_outcome()
        if not outcome:
            return
        state = self._effective_tier3_state_from_outcome(outcome)
        actionable_states = {
            "test_failures",
            "coverage_failed",
            "crashed",
            "infra_cleanup_error",
        }
        if actionable_only and state not in actionable_states:
            return
        parallel = (
            outcome.get("parallel", {})
            if isinstance(outcome.get("parallel"), dict)
            else {}
        )
        no_parallel = (
            outcome.get("no_parallel", {})
            if isinstance(outcome.get("no_parallel"), dict)
            else {}
        )
        dev_tools = (
            outcome.get("development_tools", {})
            if isinstance(outcome.get("development_tools"), dict)
            else {}
        )
        failed_nodes = outcome.get("failed_node_ids", [])

        lines.append("## Tier 3 Test Outcome")
        lines.append(f"- **State**: {state}")
        skip_p = self._tier3_track_skipped_for_audit_scope(parallel)
        skip_np = self._tier3_track_skipped_for_audit_scope(no_parallel)
        skip_dt = self._tier3_track_skipped_for_audit_scope(dev_tools)
        if not skip_p:
            lines.append(
                f"- **Parallel Track**: {self._track_classification_label(parallel)} "
                f"(passed={parallel.get('passed_count', 0)}, failed={parallel.get('failed_count', 0)}, "
                f"errors={parallel.get('error_count', 0)}, skipped={parallel.get('skipped_count', 0)}, "
                f"return={parallel.get('return_code')})"
            )
        if not skip_np:
            lines.append(
                f"- **No-Parallel Track**: {self._track_classification_label(no_parallel)} "
                f"(passed={no_parallel.get('passed_count', 0)}, failed={no_parallel.get('failed_count', 0)}, "
                f"errors={no_parallel.get('error_count', 0)}, skipped={no_parallel.get('skipped_count', 0)}, "
                f"return={no_parallel.get('return_code')})"
            )
        if not skip_dt:
            lines.append(
                f"- **Development Tools Track**: {self._track_classification_label(dev_tools)} "
                f"(passed={dev_tools.get('passed_count', 0)}, failed={dev_tools.get('failed_count', 0)}, "
                f"errors={dev_tools.get('error_count', 0)}, skipped={dev_tools.get('skipped_count', 0)}, "
                f"return={dev_tools.get('return_code')})"
            )
        if not skip_p:
            lines.append(self._format_track_classification_summary("Parallel", parallel))
        if not skip_np:
            lines.append(
                self._format_track_classification_summary("No-Parallel", no_parallel)
            )
        if not skip_dt:
            lines.append(
                self._format_track_classification_summary("Development Tools", dev_tools)
            )
        if isinstance(failed_nodes, list) and failed_nodes:
            lines.append(
                f"- **Failed/Error Node IDs**: {self._format_list_for_display(failed_nodes, limit=10)}"
            )
        lines.append("")

    def _lines_for_verify_process_cleanup_status_snapshot(
        self, vpc_data: dict[str, Any] | None
    ) -> list[str]:
        """1-2 lines for AI_STATUS Snapshot: Tier 3 verify_process_cleanup advisory."""
        if not vpc_data or not isinstance(vpc_data, dict):
            return [
                "- **Pytest process cleanup**: No data (run `audit --full` Tier 3 to refresh)"
            ]
        details = vpc_data.get("details", {})
        summary = vpc_data.get("summary", {})
        platform = str(details.get("platform", "") or "")
        if platform != "win32":
            return ["- **Pytest process cleanup**: N/A (Windows-only check)"]
        n = self._coerce_int(summary.get("total_issues"), 0) or 0
        st = str(summary.get("status", "")).upper()
        if n > 0 or st == "WARN":
            return [
                "- **Pytest process cleanup**: "
                f"WARN ({n} candidate python.exe process(es); heuristic — see CONSOLIDATED_REPORT.md)"
            ]
        return ["- **Pytest process cleanup**: PASS (no candidate orphan workers)"]

    def _lines_for_verify_process_cleanup_consolidated_section(
        self, vpc_data: dict[str, Any] | None
    ) -> list[str]:
        """Detailed ## Pytest process cleanup section for CONSOLIDATED_REPORT."""
        out: list[str] = []
        out.append("## Pytest process cleanup (Windows)")
        if not vpc_data or not isinstance(vpc_data, dict):
            out.append(
                "- **Status**: No tool data loaded (run `audit --full` Tier 3 to refresh)."
            )
            out.append("")
            return out
        details = vpc_data.get("details", {})
        summary = vpc_data.get("summary", {})
        platform = str(details.get("platform", "") or "")
        if platform != "win32":
            out.append(
                f"- **Status**: Skipped on this host (`platform={platform or 'unknown'}`); "
                "the check is implemented for Windows."
            )
            out.append("")
            return out
        n = self._coerce_int(summary.get("total_issues"), 0) or 0
        st = str(summary.get("status", "")).upper()
        found = bool(details.get("orphaned_processes_found"))
        offenders = details.get("orphaned_processes") or []
        out.append(
            f"- **Summary**: status={st}, `orphaned_processes_found`={found}, "
            f"candidate count={n} (heuristic on python.exe command lines)."
        )
        out.append(
            "- **Note**: Primary detection uses Windows command-line inspection via CIM; "
            "the fallback path is less informative when command lines are unavailable."
        )
        json_path = (
            self.project_root
            / "development_tools"
            / "tests"
            / "jsons"
            / "verify_process_cleanup_results.json"
        )
        if not json_path.exists():
            scoped = (
                self.project_root
                / "development_tools"
                / "tests"
                / "jsons"
                / "scopes"
                / "full"
                / "verify_process_cleanup_results.json"
            )
            if scoped.exists():
                json_path = scoped
        if json_path.exists():
            href = self._markdown_href_from_dev_tools_report(json_path)
            out.append(
                f"- **Machine-readable**: [verify_process_cleanup_results.json]({href})"
            )
        if isinstance(offenders, list) and offenders:
            out.append("- **Candidates** (PID and flags; command line may be empty):")
            for off in offenders[:20]:
                if isinstance(off, dict):
                    pid = off.get("pid", "?")
                    pytest_flag = off.get("is_pytest", False)
                    out.append(f"    - PID {pid}, pytest_like={pytest_flag}")
            if len(offenders) > 20:
                out.append(f"    - ... +{len(offenders) - 20} more")
        out.append("")
        return out

    def _generate_ai_status_document(self) -> str:
        """Generate AI-optimized status document."""
        # Log data source context
        audit_tier = getattr(self, "current_audit_tier", None)
        status_target = (
            "DEV_TOOLS_STATUS.md"
            if self._is_dev_tools_scoped_report()
            else "AI_STATUS.md"
        )
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating {status_target} using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating {status_target} using cached data (no active audit)"
            )

        # Check if this is a mid-audit write
        instance_flag = hasattr(self, "_audit_in_progress") and self._audit_in_progress
        audit_in_progress = instance_flag or _is_audit_in_progress(self.project_root)
        is_legitimate_end_write = (
            hasattr(self, "current_audit_tier") and self.current_audit_tier is not None
        )

        if audit_in_progress and not is_legitimate_end_write:
            if not instance_flag:
                logger.warning(
                    "_generate_ai_status_document() called from NEW instance during audit! This should only happen at the end."
                )
            else:
                logger.warning(
                    "_generate_ai_status_document() called during audit! This should only happen at the end."
                )
            import traceback

            logger.debug(f"Call stack:\n{''.join(traceback.format_stack())}")

        lines: list[str] = []
        if self._is_dev_tools_scoped_report():
            lines.append("# Development Tools Status - Scoped Snapshot")
            lines.append("")
            lines.append("> **File**: `development_tools/DEV_TOOLS_STATUS.md`")
        else:
            lines.append("# AI Status - Current Codebase State")
            lines.append("")
            lines.append("> **File**: `development_tools/AI_STATUS.md`")
        lines.append(
            "> **Generated**: This file is auto-generated. Do not edit manually."
        )
        lines.append(
            f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if (
            hasattr(self, "_audit_in_progress")
            and self._audit_in_progress
            and self.current_audit_tier is None
        ):
            logger.warning(
                "_generate_ai_status_document() called during audit but current_audit_tier is None!"
            )

        if self.current_audit_tier == 1:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --quick"
            )
            tier_name = "Tier 1 (Quick Audit)"
        elif self.current_audit_tier == 3:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --full"
            )
            tier_name = "Tier 3 (Full Audit)"
        elif self.current_audit_tier == 2:
            source_cmd = "python development_tools/run_development_tools.py audit"
            tier_name = "Tier 2 (Standard Audit)"
        else:
            source_cmd = "python development_tools/run_development_tools.py status"
            tier_name = "Status Check (cached data)"
        lines.append(f"> **Source**: `{self._audit_source_cmd_display(source_cmd)}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        if self._is_dev_tools_scoped_report():
            lines.append(
                "> **Role**: Dev-tools tree health only (`development_tools/` scan); not a full-repo snapshot. Prefer AI_STATUS.md after `audit` without `--dev-tools-only` for product-wide signals."
            )
            lines.append(
                "> **Scope**: Analyzers used `get_scan_directories() -> ['development_tools']` for this audit."
            )
            lines.append(
                "> **Artifact layout**: Reads/writes use scoped paths only (`**/jsons/scopes/dev_tools/`, `reports/scopes/dev_tools/`); pre-scopes flat JSON under `development_tools/**/jsons/*.json` is not loaded."
            )
        else:
            lines.append(
                "> **Role**: Quick operational snapshot for AI contributors (current health signals)."
            )
        lines.append("")

        def strip_doc_header(doc: str, drop_section: str | None = None) -> list[str]:
            doc_lines = doc.splitlines()
            if doc_lines and doc_lines[0].startswith("# "):
                doc_lines = doc_lines[1:]
            if not drop_section:
                return doc_lines

            filtered: list[str] = []
            skip = False
            for line in doc_lines:
                if line.startswith("## "):
                    if line.strip() == drop_section:
                        skip = True
                        continue
                    if skip:
                        skip = False
                if not skip:
                    filtered.append(line)
            return filtered

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                return value if value.strip().endswith("%") else f"{value}%"
            return self._format_percentage(value, decimals)

        def to_int(value: Any) -> int | None:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return int(float(stripped))
                except ValueError:
                    return None
            if isinstance(value, dict):
                count = value.get("count")
                return to_int(count)
            return None

        def to_float(value: Any) -> float | None:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return float(stripped)
                except ValueError:
                    return None
            return None

        metrics = self._get_canonical_metrics()
        if not isinstance(metrics, dict):
            metrics = {}

        # Load all tool data using unified loader
        doc_metrics = self._load_tool_data("analyze_function_registry", "functions")
        error_metrics = self._load_tool_data("analyze_error_handling", "error_handling")
        self._load_tool_data("analyze_functions", "functions")
        analyze_docs_data = self._load_tool_data("analyze_documentation", "docs")
        ascii_data = self._load_tool_data("analyze_ascii_compliance", "docs")
        heading_data = self._load_tool_data("analyze_heading_numbering", "docs")
        missing_addresses_data = self._load_tool_data(
            "analyze_missing_addresses", "docs"
        )
        unconverted_links_data = self._load_tool_data(
            "analyze_unconverted_links", "docs"
        )
        dependency_patterns_data = self._load_tool_data(
            "analyze_dependency_patterns", "imports"
        )
        import_boundary_data = self._load_tool_data(
            "analyze_dev_tools_import_boundaries", "imports"
        )
        backup_health_data = self._load_tool_data(
            "analyze_backup_health", "reports", log_source=False
        )
        static_analysis = self._get_static_analysis_snapshot()
        verify_process_cleanup_status_data = self._load_tool_data(
            "verify_process_cleanup", "tests"
        )

        # Extract overlap analysis data
        details = analyze_docs_data.get("details", {})
        overlap_analysis_ran = (
            "section_overlaps" in analyze_docs_data
            or "consolidation_recommendations" in analyze_docs_data
            or "section_overlaps" in details
            or "consolidation_recommendations" in details
        )
        overlap_data_source = details.get("overlap_data_source", "fresh")
        section_overlaps = (
            (
                analyze_docs_data.get("section_overlaps")
                or details.get("section_overlaps", {})
            )
            if overlap_analysis_ran
            else {}
        )
        consolidation_recs = (
            (
                analyze_docs_data.get("consolidation_recommendations")
                or details.get("consolidation_recommendations", [])
            )
            if overlap_analysis_ran
            else []
        )
        if section_overlaps is None:
            section_overlaps = {}
        if consolidation_recs is None:
            consolidation_recs = []

        doc_metrics_details = (
            doc_metrics.get("details", {}) if isinstance(doc_metrics, dict) else {}
        )
        doc_coverage = doc_metrics_details.get(
            "coverage", metrics.get("doc_coverage", "Unknown")
        )
        missing_docs = doc_metrics_details.get("missing", {})
        missing_files = self._get_missing_doc_files(limit=4)

        _error_metrics: dict[str, Any] = error_metrics or {}

        def _error_field(field_name: str, default: Any = None) -> Any:
            error_details = _error_metrics.get("details", {})
            return error_details.get(field_name, default)

        error_summary = _error_metrics.get("summary", {})
        error_details = _error_metrics.get("details", {})
        missing_error_handlers = to_int(error_summary.get("total_issues"))
        if missing_error_handlers is None:
            missing_error_handlers = (
                to_int(error_details.get("functions_missing_error_handling")) or 0
            )
        details_missing = to_int(error_details.get("functions_missing_error_handling"))
        if (
            details_missing is not None
            and details_missing > 0
            and (missing_error_handlers is None or missing_error_handlers == 0)
        ):
            missing_error_handlers = details_missing

        error_coverage = error_details.get(
            "analyze_error_handling"
        ) or error_details.get("error_handling_coverage")
        error_total = error_details.get("total_functions")
        error_with_handling = error_details.get("functions_with_error_handling")
        canonical_total = metrics.get("total_functions")

        if error_total and error_with_handling:
            calc_coverage = (error_with_handling / error_total) * 100
            if 0 <= calc_coverage <= 100:
                error_coverage = calc_coverage
        elif error_coverage is None and error_total and error_with_handling:
            error_coverage = (error_with_handling / error_total) * 100

        worst_error_modules = error_details.get("worst_modules") or []
        if worst_error_modules is None or not isinstance(
            worst_error_modules, (list, tuple)
        ):
            worst_error_modules = []

        coverage_summary = self._load_coverage_summary() or {}

        if (
            not hasattr(self, "dev_tools_coverage_results")
            or not self.dev_tools_coverage_results
        ):
            self._load_dev_tools_coverage()

        doc_sync_data = self._load_tool_data(
            "analyze_documentation_sync", "docs", log_source=True
        )
        doc_sync_summary = self.docs_sync_summary or doc_sync_data or {}
        if not isinstance(doc_sync_summary, dict):
            doc_sync_summary = {}

        legacy_data = self._load_tool_data("analyze_legacy_references", "legacy")
        legacy_summary = self.legacy_cleanup_summary or legacy_data or {}

        lines.append("## Snapshot")

        total_functions = (
            metrics.get("total_functions", "Unknown") if metrics else "Unknown"
        )
        moderate = metrics.get("moderate", "Unknown") if metrics else "Unknown"
        high = metrics.get("high", "Unknown") if metrics else "Unknown"
        critical = metrics.get("critical", "Unknown") if metrics else "Unknown"

        # Try loading from cache if Unknown (skip in test directories to prevent memory issues)
        if total_functions == "Unknown" or moderate == "Unknown":
            try:
                cached_data = self._load_results_file_safe()
                if cached_data:
                    if (
                        "results" in cached_data
                        and "analyze_functions" in cached_data["results"]
                    ):
                        func_data = cached_data["results"]["analyze_functions"]
                        if "data" in func_data:
                            cached_metrics_raw = func_data["data"]
                            if "details" in cached_metrics_raw and isinstance(
                                cached_metrics_raw.get("details"), dict
                            ):
                                cached_metrics = cached_metrics_raw["details"]
                            else:
                                cached_metrics = cached_metrics_raw
                            if total_functions == "Unknown":
                                total_functions = cached_metrics.get(
                                    "total_functions", "Unknown"
                                )
                            if moderate == "Unknown":
                                moderate = cached_metrics.get(
                                    "moderate_complexity", "Unknown"
                                )
                            if high == "Unknown":
                                high = cached_metrics.get("high_complexity", "Unknown")
                            if critical == "Unknown":
                                critical = cached_metrics.get(
                                    "critical_complexity", "Unknown"
                                )
                    if (
                        total_functions == "Unknown" or moderate == "Unknown"
                    ) and "results" in cached_data:
                        if "decision_support" in cached_data["results"]:
                            ds_data = cached_data["results"]["decision_support"]
                            ds_details = self._get_decision_support_details(
                                ds_data.get("data")
                                if isinstance(ds_data, dict)
                                else None
                            )
                            if ds_details:
                                if total_functions == "Unknown":
                                    total_functions = ds_details.get(
                                        "total_functions", "Unknown"
                                    )
                                if moderate == "Unknown":
                                    moderate = ds_details.get(
                                        "moderate_complexity", "Unknown"
                                    )
                                if high == "Unknown":
                                    high = ds_details.get("high_complexity", "Unknown")
                                if critical == "Unknown":
                                    critical = ds_details.get(
                                        "critical_complexity", "Unknown"
                                    )
            except Exception as e:
                logger.debug(f"Failed to load metrics from cache: {e}")
                pass

        if total_functions == "Unknown":
            lines.append(
                "- **Total Functions**: Run `python development_tools/run_development_tools.py audit` for detailed metrics"
            )
        else:
            lines.append(
                f"- **Total Functions**: {total_functions} (Moderate: {moderate}, High: {high}, Critical: {critical})"
            )

        # Canonical docstring metric source: analyze_functions (code docstrings).
        code_doc_metrics = self._get_code_docstring_metrics()
        code_doc_coverage = code_doc_metrics.get("coverage")
        doc_coverage = (
            f"{code_doc_coverage:.2f}%"
            if isinstance(code_doc_coverage, (int, float))
            else "Unknown"
        )
        functions_without_docstrings = code_doc_metrics.get("undocumented")
        missing_docs = None
        missing_files = []

        # Registry data is used for registry-gaps reporting only.
        registry_data = self._load_tool_data("analyze_function_registry", "functions")
        if not isinstance(registry_data, dict):
            registry_data = self._load_tool_data(
                "analyze_function_registry", "functions"
            )

        # Fallback to cached results
        if (
            doc_coverage == "Unknown" or doc_coverage is None
        ) and functions_without_docstrings is None:
            try:
                cached_data = self._load_results_file_safe()
                if cached_data and (
                    "results" in cached_data
                    and "analyze_functions" in cached_data["results"]
                ):
                    func_data = cached_data["results"]["analyze_functions"]
                    if "data" in func_data:
                        func_metrics_raw = func_data["data"]
                        if "details" in func_metrics_raw and isinstance(
                            func_metrics_raw.get("details"), dict
                        ):
                            func_metrics = func_metrics_raw["details"]
                        else:
                            func_metrics = func_metrics_raw
                        func_total = func_metrics.get("total_functions")
                        func_undocumented = func_metrics.get("undocumented", 0)
                        if func_total is not None and func_total > 0:
                            func_documented = func_total - func_undocumented
                            coverage_pct = (func_documented / func_total) * 100
                            doc_coverage = f"{coverage_pct:.2f}%"
                            functions_without_docstrings = self._coerce_int(
                                func_undocumented, 0
                            )
            except Exception as e:
                logger.debug(f"Failed to load doc_coverage from cache in status: {e}")
                pass

        # Final fallback to results cache
        if (
            (doc_coverage == "Unknown" or doc_coverage is None)
            and functions_without_docstrings is None
            and total_functions is not None
        ):
            func_cache_raw = self.results_cache.get("analyze_functions", {})
            if isinstance(func_cache_raw, dict):
                if "details" in func_cache_raw and isinstance(
                    func_cache_raw.get("details"), dict
                ):
                    func_cache = func_cache_raw["details"]
                else:
                    func_cache = func_cache_raw
                func_undocumented = func_cache.get("undocumented", 0)
                if (
                    isinstance(func_undocumented, (int, float))
                    and isinstance(total_functions, (int, float))
                    and total_functions > 0
                ):
                    func_documented = total_functions - func_undocumented
                    coverage_pct = (func_documented / total_functions) * 100
                    doc_coverage = f"{coverage_pct:.2f}%"
                    functions_without_docstrings = self._coerce_int(
                        func_undocumented, 0
                    )

        # Check registry for missing items (if not already loaded above)
        if not isinstance(registry_data, dict) or missing_docs is None:
            if not isinstance(registry_data, dict):
                registry_data = self._load_tool_data(
                    "analyze_function_registry", "functions"
                )
            missing_docs = None
            missing_files = []

            if isinstance(registry_data, dict):
                registry_details = registry_data.get("details", {})
                missing_docs_raw = registry_details.get("missing", {})
                if isinstance(missing_docs_raw, dict):
                    missing_docs = missing_docs_raw
                    missing_files = missing_docs_raw.get("missing_files", [])
                elif missing_docs_raw:
                    missing_docs = {"count": to_int(missing_docs_raw) or 0}

        # Fallback to cached results
        if not missing_docs:
            try:
                cached_data = self._load_results_file_safe()
                if cached_data and (
                    "results" in cached_data
                    and "analyze_function_registry" in cached_data["results"]
                ):
                    func_reg_data = cached_data["results"][
                        "analyze_function_registry"
                    ]
                    if "data" in func_reg_data:
                        cached_metrics = func_reg_data["data"]
                        cached_details = (
                            cached_metrics.get("details", {})
                            if isinstance(cached_metrics, dict)
                            else {}
                        )
                        missing_docs_raw = cached_details.get("missing", {})
                        if missing_docs_raw:
                            if isinstance(missing_docs_raw, dict):
                                missing_docs = missing_docs_raw
                            else:
                                missing_docs = {
                                    "count": to_int(missing_docs_raw) or 0
                                }
                        if isinstance(missing_docs, dict):
                            missing_files = missing_docs.get("missing_files", [])
            except Exception as e:
                logger.debug(f"Failed to load registry missing data: {e}")
                pass

        missing_docstrings_count = (
            functions_without_docstrings if functions_without_docstrings else 0
        )
        doc_line = f"- **Function Docstring Coverage**: {percent_text(doc_coverage, 2)}"
        if missing_docstrings_count > 0:
            doc_line += f" ({missing_docstrings_count} functions missing docstrings)"
        else:
            doc_line += " (0 functions missing docstrings)"
        lines.append(doc_line)

        missing_count = 0
        if missing_docs:
            if isinstance(missing_docs, dict):
                missing_count = missing_docs.get("count", 0)
            else:
                missing_count = to_int(missing_docs) or 0

        if missing_count > 0:
            lines.append(
                f"- **Registry Gaps**: {missing_count} items missing from registry"
            )
        else:
            lines.append("- **Registry Gaps**: 0 items missing from registry")

        if missing_files:
            lines.append(
                f"- **Missing Documentation Files**: {self._format_list_for_display(missing_files, limit=4)}"
            )

        # Error handling coverage
        error_coverage_from_cache = "Unknown"
        error_total = None
        error_with_handling = None
        if not error_metrics or error_coverage == "Unknown":
            try:
                cached_data = self._load_results_file_safe()
                if (
                    cached_data
                    and "results" in cached_data
                    and "analyze_error_handling" in cached_data["results"]
                ):
                    error_data = cached_data["results"]["analyze_error_handling"]
                    if "data" in error_data:
                        cached_metrics = error_data["data"]
                        error_coverage_from_cache = cached_metrics.get(
                            "analyze_error_handling"
                        ) or cached_metrics.get("error_handling_coverage", "Unknown")
                        if (
                            missing_error_handlers is None
                            or missing_error_handlers == 0
                        ):
                            missing_error_handlers = to_int(
                                cached_metrics.get("functions_missing_error_handling")
                            )
                        error_total = cached_metrics.get("total_functions")
                        error_with_handling = cached_metrics.get(
                            "functions_with_error_handling"
                        )
                        if error_coverage_from_cache != "Unknown":
                            error_coverage = error_coverage_from_cache
            except Exception:
                pass

        if missing_error_handlers is None or missing_error_handlers == 0:
            if error_metrics:
                error_details = error_metrics.get("details", {})
                missing_error_handlers = (
                    to_int(error_details.get("functions_missing_error_handling"))
                    or to_int(error_metrics.get("functions_missing_error_handling"))
                    or 0
                )

        canonical_total = metrics.get("total_functions")
        if (
            error_coverage is not None
            and canonical_total
            and error_total
            and error_with_handling
        ) and error_total != canonical_total:
            recalc_coverage = (error_with_handling / canonical_total) * 100
            if 0 <= recalc_coverage <= 100:
                error_coverage = recalc_coverage

        lines.append(
            f"- **Error Handling Coverage**: {percent_text(error_coverage, 1)}"
            + (
                f" ({missing_error_handlers} functions without handlers)"
                if missing_error_handlers is not None
                else ""
            )
        )

        # Doc sync status
        if doc_sync_summary:

            def get_doc_sync_field(data, field_name, default=None):
                if not data or not isinstance(data, dict):
                    return default
                summary = data.get("summary", {})
                details = data.get("details", {})
                if field_name == "status":
                    return summary.get("status", default)
                if field_name == "total_issues":
                    return summary.get("total_issues", default)
                return details.get(field_name, default)

            sync_status = get_doc_sync_field(doc_sync_summary, "status", "Unknown")
            total_issues = get_doc_sync_field(doc_sync_summary, "total_issues")
            if total_issues is None or total_issues == 0:
                path_drift_issues = get_doc_sync_field(
                    doc_sync_summary, "path_drift_issues", 0
                )
                paired_doc_issues = get_doc_sync_field(
                    doc_sync_summary, "paired_doc_issues", 0
                )
                ascii_issues = get_doc_sync_field(doc_sync_summary, "ascii_issues", 0)
                total_issues = (
                    (path_drift_issues or 0)
                    + (paired_doc_issues or 0)
                    + (ascii_issues or 0)
                )

            sync_line = f"- **Doc Sync**: {sync_status}"
            if total_issues is not None and total_issues > 0:
                sync_line += f" ({total_issues} tracked issues)"
            lines.append(sync_line)
            em_hints = get_doc_sync_field(
                doc_sync_summary, "example_marker_hint_count", 0
            )
            try:
                em_n = int(em_hints or 0)
            except (TypeError, ValueError):
                em_n = 0
            if em_n > 0:
                lines.append(
                    f"- **Example markers (advisory)**: {em_n} hint(s) in paired docs "
                    "(Example sections / path backticks without standard markers)"
                )
            else:
                lines.append(
                    "- **Example markers (advisory)**: no hints (paired-doc Example scan)"
                )
        else:
            lines.append(
                "- **Doc Sync**: Not collected in this run (pending doc-sync refresh)"
            )

        # Test coverage snapshot: dev-tools-only runs skip full-repo refresh; avoid showing
        # stale overall % from coverage.json alongside "not refreshed" in the Test Coverage section.
        skip_main_tracks_snap = bool(
            getattr(self, "_tier3_skipped_main_tracks", False)
        )
        if self._is_dev_tools_scoped_report() and skip_main_tracks_snap:
            dev_snap = self._get_dev_tools_coverage_insights()
            if dev_snap and dev_snap.get("overall_pct") is not None:
                pct = dev_snap["overall_pct"]
                stmts = dev_snap.get("statements")
                covd = dev_snap.get("covered")
                if stmts is not None and covd is not None:
                    lines.append(
                        f"- **Development Tools Package Coverage (this pass)**: "
                        f"{percent_text(pct, 1)} ({covd} of {stmts} statements; "
                        f"`development_tools/` only)"
                    )
                else:
                    lines.append(
                        f"- **Development Tools Package Coverage (this pass)**: "
                        f"{percent_text(pct, 1)} (`development_tools/` only)"
                    )
            else:
                lines.append(
                    "- **Development Tools Package Coverage (this pass)**: "
                    "No `coverage_dev_tools.json` loaded - run `audit --full --dev-tools-only` "
                    "with Tier 3 dev-tools coverage enabled."
                )
        elif coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            primary = coverage_summary.get("primary_overall") or {}
            use_primary = (
                primary
                and primary.get("statements", 0) > 0
                and primary.get("coverage") is not None
                and (overall.get("coverage") or 0) < 25
            )
            cov = primary if use_primary else overall
            if cov.get("coverage") is not None:
                lines.append(
                    f"- **Test Coverage**: {percent_text(cov.get('coverage'), 1)} "
                    f"({cov.get('covered')} of {cov.get('statements')} statements)"
                )

        backup_summary = (
            backup_health_data.get("summary", {})
            if isinstance(backup_health_data, dict)
            else {}
        )
        backup_checks = (
            backup_health_data.get("details", {}).get("checks", [])
            if isinstance(backup_health_data.get("details"), dict)
            else (
                backup_health_data.get("checks", [])
                if isinstance(backup_health_data, dict)
                else []
            )
        )
        if backup_summary:
            backup_status = str(
                backup_summary.get(
                    "status",
                    "PASS" if bool(backup_summary.get("success")) else "FAIL",
                )
            ).upper()
            passed_checks = backup_summary.get("passed_checks")
            total_checks = backup_summary.get("total_checks")
            check_fragment = ""
            if isinstance(passed_checks, int) and isinstance(total_checks, int):
                check_fragment = f" ({passed_checks}/{total_checks} checks)"
            lines.append(f"- **Backup Health**: {backup_status}{check_fragment}")
        else:
            lines.append(
                "- **Backup Health**: Not collected in this run (run `python development_tools/run_development_tools.py backup verify`)"
            )

        ruff_summary = (
            static_analysis.get("analyze_ruff", {}).get("summary", {})
            if isinstance(static_analysis, dict)
            else {}
        )
        pyright_summary = (
            static_analysis.get("analyze_pyright", {}).get("summary", {})
            if isinstance(static_analysis, dict)
            else {}
        )
        bandit_summary = (
            static_analysis.get("analyze_bandit", {}).get("summary", {})
            if isinstance(static_analysis, dict)
            else {}
        )
        pip_audit_summary = (
            static_analysis.get("analyze_pip_audit", {}).get("summary", {})
            if isinstance(static_analysis, dict)
            else {}
        )
        ruff_available = bool(
            static_analysis.get("analyze_ruff", {}).get("available", False)
        ) if isinstance(static_analysis, dict) else False
        pyright_available = bool(
            static_analysis.get("analyze_pyright", {}).get("available", False)
        ) if isinstance(static_analysis, dict) else False
        bandit_available = bool(
            static_analysis.get("analyze_bandit", {}).get("available", False)
        ) if isinstance(static_analysis, dict) else False
        pip_audit_available = bool(
            static_analysis.get("analyze_pip_audit", {}).get("available", False)
        ) if isinstance(static_analysis, dict) else False
        ruff_total = to_int(ruff_summary.get("total_issues")) or 0
        pyright_total = to_int(pyright_summary.get("total_issues")) or 0
        bandit_total = to_int(bandit_summary.get("total_issues")) or 0
        pip_audit_total = to_int(pip_audit_summary.get("total_issues")) or 0
        static_ready = (
            ruff_available
            and pyright_available
            and bandit_available
            and pip_audit_available
        )
        if not static_ready:
            lines.append(
                "- **Static Analysis (ruff/pyright/bandit/pip-audit)**: UNAVAILABLE"
            )
        elif (
            ruff_total > 0
            or pyright_total > 0
            or bandit_total > 0
            or pip_audit_total > 0
        ):
            lines.append(
                f"- **Static Analysis (ruff/pyright/bandit/pip-audit)**: "
                f"{ruff_total + pyright_total + bandit_total + pip_audit_total} issue(s) "
                f"(ruff={ruff_total}, pyright={pyright_total}, bandit={bandit_total}, pip-audit={pip_audit_total})"
            )
        else:
            lines.append(
                "- **Static Analysis (ruff/pyright/bandit/pip-audit)**: CLEAN"
            )

        lines.extend(
            self._lines_for_verify_process_cleanup_status_snapshot(
                verify_process_cleanup_status_data
            )
        )

        lines.append("")
        lines.append("## Documentation Signals")

        # Helper to extract doc sync field (standard format only)
        def get_doc_sync_field(data, field_name, default=None):
            if not data or not isinstance(data, dict):
                return default
            summary = data.get("summary", {})
            details = data.get("details", {})
            if field_name == "status":
                return summary.get("status", default)
            if field_name == "total_issues":
                return summary.get("total_issues", default)
            return details.get(field_name, default)

        # Use aggregated doc sync summary from current run first, then fall back to cache
        doc_sync_summary_for_signals = None
        if (
            hasattr(self, "docs_sync_summary")
            and self.docs_sync_summary
            and isinstance(self.docs_sync_summary, dict)
        ):
            # Use the aggregated summary from _run_doc_sync_check() - use helper to handle both formats
            doc_sync_summary_for_signals = {
                "status": get_doc_sync_field(
                    self.docs_sync_summary, "status", "UNKNOWN"
                ),
                "path_drift_issues": get_doc_sync_field(
                    self.docs_sync_summary, "path_drift_issues", 0
                ),
                "paired_doc_issues": get_doc_sync_field(
                    self.docs_sync_summary, "paired_doc_issues", 0
                ),
                "ascii_issues": get_doc_sync_field(
                    self.docs_sync_summary, "ascii_issues", 0
                ),
                "heading_numbering_issues": get_doc_sync_field(
                    self.docs_sync_summary, "heading_numbering_issues", 0
                ),
                "missing_address_issues": get_doc_sync_field(
                    self.docs_sync_summary, "missing_address_issues", 0
                ),
                "unconverted_link_issues": get_doc_sync_field(
                    self.docs_sync_summary, "unconverted_link_issues", 0
                ),
                "path_drift_files": get_doc_sync_field(
                    self.docs_sync_summary, "path_drift_files", []
                ),
                "example_marker_hint_count": get_doc_sync_field(
                    self.docs_sync_summary, "example_marker_hint_count", 0
                ),
                "example_marker_findings": get_doc_sync_field(
                    self.docs_sync_summary, "example_marker_findings", {}
                ),
            }

        # Fall back to cache if not available in memory
        if not doc_sync_summary_for_signals:
            # Load doc sync data using unified loader (returns standard format)
            doc_sync_result = self._load_tool_data("analyze_documentation_sync", "docs")
            if doc_sync_result:
                doc_sync_summary_for_signals = {
                    "status": get_doc_sync_field(doc_sync_result, "status", "UNKNOWN"),
                    "path_drift_issues": get_doc_sync_field(
                        doc_sync_result, "path_drift_issues", 0
                    ),
                    "paired_doc_issues": get_doc_sync_field(
                        doc_sync_result, "paired_doc_issues", 0
                    ),
                    "ascii_issues": get_doc_sync_field(
                        doc_sync_result, "ascii_issues", 0
                    ),
                    "heading_numbering_issues": get_doc_sync_field(
                        doc_sync_result, "heading_numbering_issues", 0
                    ),
                    "missing_address_issues": get_doc_sync_field(
                        doc_sync_result, "missing_address_issues", 0
                    ),
                    "unconverted_link_issues": get_doc_sync_field(
                        doc_sync_result, "unconverted_link_issues", 0
                    ),
                    "path_drift_files": get_doc_sync_field(
                        doc_sync_result, "path_drift_files", []
                    ),
                    "example_marker_hint_count": get_doc_sync_field(
                        doc_sync_result, "example_marker_hint_count", 0
                    ),
                    "example_marker_findings": get_doc_sync_field(
                        doc_sync_result, "example_marker_findings", {}
                    ),
                }

        # Extract values from doc_sync_summary_for_signals (if available) for use throughout the section
        path_drift = None
        paired = None
        ascii_issues = None
        if doc_sync_summary_for_signals:
            path_drift = get_doc_sync_field(
                doc_sync_summary_for_signals, "path_drift_issues", 0
            )
            if path_drift is None:
                path_drift = 0

            paired = get_doc_sync_field(
                doc_sync_summary_for_signals, "paired_doc_issues", 0
            )
            if paired is None:
                paired = 0

            ascii_issues = get_doc_sync_field(
                doc_sync_summary_for_signals, "ascii_issues", 0
            )
            if ascii_issues is None:
                ascii_issues = 0

        if doc_sync_summary_for_signals:

            # Check for path validation issues first (separate from path_drift - checks if referenced paths exist)
            # Path validation is more critical than path drift
            path_val_issues = None
            path_val_status = None
            if hasattr(self, "path_validation_result") and self.path_validation_result:
                if isinstance(self.path_validation_result, dict):
                    path_val_status = self.path_validation_result.get("status")
                    path_val_issues = self.path_validation_result.get("issues_found", 0)
                    # Also check if issues_found is in the result but status might be different
                    if path_val_issues is None or path_val_issues == 0:
                        # Try to get issues from details if available
                        details = self.path_validation_result.get("details", {})
                        if details and isinstance(details, dict):
                            # Count total issues from details
                            total_issues = sum(
                                len(issues) if isinstance(issues, (list, dict)) else 1
                                for issues in details.values()
                            )
                            if total_issues > 0:
                                path_val_issues = total_issues
                                if path_val_status != "ok":
                                    path_val_status = "fail"

            # Then check path drift (documentation path changes)
            # Path drift checks for documentation path inconsistencies
            # Path validation checks if referenced paths actually exist
            # Get path_drift using helper to handle standard format
            path_drift = get_doc_sync_field(
                doc_sync_summary_for_signals, "path_drift_issues", 0
            )
            if path_drift is None:
                path_drift = 0
            # They can have different issues, but if path validation found issues, we show those under Path Drift
            # to avoid duplication
            if path_drift is not None:
                if path_drift == 0:
                    # Path drift tool found 0 issues
                    if path_val_issues is None:
                        # Path validation didn't run, so trust path drift
                        severity = "CLEAN"
                        lines.append(
                            f"- **Path Drift**: {severity} ({path_drift} issues)"
                        )
                    elif path_val_issues == 0:
                        # Both path drift and path validation found 0 issues
                        severity = "CLEAN"
                        lines.append(
                            f"- **Path Drift**: {severity} ({path_drift} issues)"
                        )
                    else:
                        # Path drift found 0, but path validation found issues - show path validation issues
                        # Don't duplicate by showing both Path Validation and Path Drift
                        severity = "NEEDS ATTENTION"
                        lines.append(
                            f"- **Path Drift**: {severity} ({path_val_issues} referenced paths don't exist)"
                        )
                else:
                    # Path drift found issues - show those
                    severity = "NEEDS ATTENTION"
                    lines.append(f"- **Path Drift**: {severity} ({path_drift} issues)")
            elif path_val_issues is not None and path_val_issues > 0:
                # Path drift didn't run, but path validation found issues
                lines.append(
                    f"- **Path Drift**: NEEDS ATTENTION ({path_val_issues} referenced paths don't exist)"
                )
            else:
                # If neither path_drift nor path_validation ran, show unknown
                lines.append("- **Path Drift**: Unknown (run `audit` to check)")

            if paired is not None:
                status_label = "SYNCHRONIZED" if paired == 0 else "NEEDS ATTENTION"
                lines.append(f"- **Paired Docs**: {status_label} ({paired} issues)")
                # Add details about paired doc issues if available
                if paired > 0 and doc_sync_summary_for_signals:
                    paired_docs_data = doc_sync_summary_for_signals.get(
                        "paired_docs", {}
                    )
                    if isinstance(paired_docs_data, dict):
                        content_sync_issues = paired_docs_data.get("content_sync", [])
                        if content_sync_issues:
                            # Show first 2-3 issues
                            for issue in content_sync_issues[:3]:
                                lines.append(f"  - {issue}")
                            if len(content_sync_issues) > 3:
                                lines.append(
                                    f"  - ...and {len(content_sync_issues) - 3} more issue(s)"
                                )

        # Add ASCII Compliance to Documentation Signals
        # First check doc_sync_summary (aggregated), then check direct tool result
        if ascii_issues is not None and ascii_issues > 0:
            lines.append(
                f"- **ASCII Compliance**: {ascii_issues} files contain non-ASCII characters"
            )
        elif ascii_data and isinstance(ascii_data, dict):
            # Use standard format
            summary = ascii_data.get("summary", {})
            ascii_total = summary.get("total_issues", 0)
            ascii_file_count = summary.get("files_affected", 0)
            if ascii_total > 0 or ascii_file_count > 0:
                lines.append(
                    f"- **ASCII Compliance**: {ascii_total} issues in {ascii_file_count} files"
                )
            else:
                lines.append(
                    "- **ASCII Compliance**: CLEAN (all files are ASCII-compliant)"
                )

        # Add Heading Numbering to Documentation Signals
        if heading_data and isinstance(heading_data, dict):
            # Use standard format
            summary = heading_data.get("summary", {})
            heading_total = summary.get("total_issues", 0)
            heading_file_count = summary.get("files_affected", 0)
            if heading_total > 0 or heading_file_count > 0:
                lines.append(
                    f"- **Heading Numbering**: {heading_total} issues in {heading_file_count} files"
                )
            else:
                lines.append(
                    "- **Heading Numbering**: CLEAN (all headings properly numbered)"
                )

        # Add Missing Addresses to Documentation Signals
        if missing_addresses_data and isinstance(missing_addresses_data, dict):
            # Use standard format
            summary = missing_addresses_data.get("summary", {})
            missing_total = summary.get("total_issues", 0)
            missing_file_count = summary.get("files_affected", 0)
            if missing_total > 0 or missing_file_count > 0:
                lines.append(
                    f"- **Missing Addresses**: {missing_total} issues in {missing_file_count} files"
                )
            else:
                lines.append(
                    "- **Missing Addresses**: CLEAN (all documentation addresses present)"
                )

        # Add Unconverted Links to Documentation Signals
        if unconverted_links_data and isinstance(unconverted_links_data, dict):
            # Use standard format
            summary = unconverted_links_data.get("summary", {})
            links_total = summary.get("total_issues", 0)
            links_file_count = summary.get("files_affected", 0)
            if links_total > 0 or links_file_count > 0:
                lines.append(
                    f"- **Unconverted Links**: {links_total} issues in {links_file_count} files"
                )
            else:
                lines.append(
                    "- **Unconverted Links**: CLEAN (all links properly converted)"
                )

        # Example markers (advisory; from analyze_documentation_sync + --check-example-markers)
        em_hint_n = 0
        if doc_sync_summary_for_signals:
            try:
                em_hint_n = int(
                    doc_sync_summary_for_signals.get("example_marker_hint_count") or 0
                )
            except (TypeError, ValueError):
                em_hint_n = 0
        if em_hint_n > 0:
            lines.append(
                f"- **Example markers (advisory)**: {em_hint_n} hint(s) — path-like lines in "
                "Example sections without a marker within ±5 lines (see AI_DOCUMENTATION_GUIDE §3.6); "
                "details in doc-sync JSON / AI_PRIORITIES when triaging"
            )
        else:
            lines.append(
                "- **Example markers (advisory)**: no hints (paired-doc Example scan is clean)"
            )

        # Add Dependency Docs to Documentation Signals
        dependency_summary = getattr(self, "module_dependency_summary", None) or (
            hasattr(self, "results_cache")
            and self.results_cache.get("analyze_module_dependencies")
        )
        if not dependency_summary:
            # Try loading from tool data
            dependency_data = self._load_tool_data(
                "analyze_module_dependencies", "imports"
            )
            if dependency_data and isinstance(dependency_data, dict):
                dependency_summary = dependency_data

        if dependency_summary:
            missing_deps = dependency_summary.get("missing_dependencies")
            if missing_deps:
                lines.append(
                    f"- **Dependency Docs**: {missing_deps} undocumented references detected"
                )
            else:
                lines.append(
                    "- **Dependency Docs**: CLEAN (no undocumented dependencies)"
                )
        else:
            # Always show Dependency Docs status, even if data not available
            lines.append("- **Dependency Docs**: CLEAN (no undocumented dependencies)")

        if not doc_sync_summary_for_signals:
            lines.append(
                "- Run `python development_tools/run_development_tools.py doc-sync` for drift details"
            )

        # Add config validation status
        config_validation_summary = self._load_config_validation_summary()
        if config_validation_summary:
            config_valid = config_validation_summary.get("config_valid", False)
            config_complete = config_validation_summary.get("config_complete", False)
            total_recommendations = config_validation_summary.get(
                "total_recommendations", 0
            )
            if config_valid and config_complete and total_recommendations == 0:
                lines.append("- **Config Validation**: CLEAN (no issues)")
            elif total_recommendations > 0:
                lines.append(
                    f"- **Config Validation**: {total_recommendations} recommendation(s)"
                )
            else:
                lines.append("- **Config Validation**: Needs attention")

        # Add TODO sync status
        todo_sync_result = getattr(self, "todo_sync_result", None)
        if not todo_sync_result:
            # Try loading from tool data if not in memory
            todo_data = self._load_tool_data("analyze_todo_sync", "docs")
            if todo_data and isinstance(todo_data, dict):
                todo_sync_result = todo_data

        if todo_sync_result and isinstance(todo_sync_result, dict):
            completed_entries = todo_sync_result.get("completed_entries", [])
            if isinstance(completed_entries, list):
                completed_count = len(completed_entries)
            else:
                completed_count = todo_sync_result.get("completed_entries", 0)
            if completed_count > 0:
                lines.append(
                    f"- **TODO Sync**: {completed_count} completed entries need review"
                )
            else:
                lines.append("- **TODO Sync**: CLEAN (no completed entries)")
        else:
            # Always show TODO Sync status, even if data not available
            lines.append("- **TODO Sync**: CLEAN (no completed entries)")

        # Add overlap analysis summary (always show, even if no overlaps found)
        lines.append("")
        lines.append("## Documentation Overlap")
        overlap_count = len(section_overlaps) if section_overlaps else 0
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0

        if overlap_count > 0 or consolidation_count > 0:
            if section_overlaps and overlap_count > 0:
                lines.append(
                    f"- **Section Overlaps**: {overlap_count} sections duplicated across files"
                )
                # Show first few overlaps
                top_overlaps = sorted(
                    section_overlaps.items(), key=lambda x: len(x[1]), reverse=True
                )[:3]
                for section, files in top_overlaps:
                    lines.append(
                        f"  - `{section}` appears in: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}"
                    )
        else:
            if overlap_analysis_ran:
                if overlap_data_source == "cached":
                    lines.append(
                        "- **Status**: No overlaps detected (cached overlap data)"
                    )
                    lines.append(
                        "  - Using cached overlap data (run `audit --full` or `--overlap` flag for latest validation)"
                    )
                else:
                    lines.append(
                        "- **Status**: No overlaps detected (analysis performed)"
                    )
                    lines.append(
                        "  - Overlap analysis ran but found no section overlaps or consolidation opportunities"
                    )
            else:
                lines.append(
                    "- **Status**: Overlap analysis not run (use `audit --full` or `--overlap` flag)"
                )
                lines.append(
                    "  - Standard audits skip overlap analysis by default; run `audit --full` or use `--overlap` flag to include it"
                )

        doc_artifacts = (
            analyze_docs_data.get("artifacts")
            if isinstance(analyze_docs_data, dict)
            else None
        )

        if doc_artifacts:
            primary_artifact = doc_artifacts[0]
            file_name = primary_artifact.get("file")
            line_no = primary_artifact.get("line")
            pattern = primary_artifact.get("pattern")
            lines.append(
                f"- **Content Cleanup**: {file_name} line {line_no} flagged for {pattern.replace('_', ' ')}"
            )
            if len(doc_artifacts) > 1:
                lines.append(
                    f"- Additional documentation artifacts: {len(doc_artifacts) - 1} more findings"
                )

        lines.append("")
        lines.append("## Error Handling")

        if error_metrics:
            # Always show missing error handling count (even if 0)
            if missing_error_handlers is not None:
                lines.append(
                    f"- **Missing Error Handling**: {missing_error_handlers} functions lack protections"
                )
            # Get decorator count from details
            decorated = _error_field("functions_with_decorators")
            if decorated is not None:
                lines.append(
                    f"- **@handle_errors Usage**: {decorated} functions already use the decorator"
                )
            # Show error handling coverage if available
            if error_coverage is not None:
                lines.append(f"- **Error Handling Coverage**: {error_coverage:.1f}%")
            # Show functions with error handling if available
            if error_with_handling is not None:
                lines.append(
                    f"- **Functions with Error Handling**: {error_with_handling}"
                )

            # Phase 1: Candidates for decorator replacement
            # Use helper to access from details or top level
            error_details = error_metrics.get("details", {})
            phase1_total = error_details.get(
                "phase1_total", error_metrics.get("phase1_total", 0)
            )

            if phase1_total > 0:
                phase1_by_priority = (
                    error_details.get(
                        "phase1_by_priority",
                        error_metrics.get("phase1_by_priority", {}),
                    )
                    or {}
                )
                if not isinstance(phase1_by_priority, dict):
                    phase1_by_priority = {}

                priority_counts = []
                if phase1_by_priority.get("high", 0) > 0:
                    priority_counts.append(f"{phase1_by_priority['high']} high")
                if phase1_by_priority.get("medium", 0) > 0:
                    priority_counts.append(f"{phase1_by_priority['medium']} medium")
                if phase1_by_priority.get("low", 0) > 0:
                    priority_counts.append(f"{phase1_by_priority['low']} low")

                priority_text = ", ".join(priority_counts) if priority_counts else "0"
                lines.append(
                    f"- **Phase 1 Candidates**: {phase1_total} functions need decorator replacement ({priority_text} priority)"
                )

            # Phase 2: Generic exception raises
            # Use helper to access from details or top level
            error_details = error_metrics.get("details", {})
            phase2_total = error_details.get(
                "phase2_total", error_metrics.get("phase2_total", 0)
            )

            if phase2_total > 0:
                phase2_by_type = (
                    error_details.get(
                        "phase2_by_type", error_metrics.get("phase2_by_type", {})
                    )
                    or {}
                )
                if not isinstance(phase2_by_type, dict):
                    phase2_by_type = {}

                type_counts = [
                    f"{count} {exc_type}"
                    for exc_type, count in sorted(
                        phase2_by_type.items(), key=lambda x: x[1], reverse=True
                    )[:3]
                ]
                type_text = ", ".join(type_counts) if type_counts else "0"
                if len(phase2_by_type) > 3:
                    type_text += f", ... +{len(phase2_by_type) - 3} more"
                lines.append(
                    f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})"
                )
        else:
            # Try to load cached error handling data
            try:
                cached_data = self._load_results_file_safe()
                if (
                    cached_data
                    and "results" in cached_data
                    and "analyze_error_handling" in cached_data["results"]
                ):
                    error_data = cached_data["results"]["analyze_error_handling"]
                    if "data" in error_data:
                        error_metrics = error_data["data"]
                    else:
                        # Try loading from standardized output storage
                        from ..output_storage import load_tool_result

                        loaded_data = load_tool_result(
                            "analyze_error_handling",
                            "error_handling",
                            project_root=self.project_root,
                        )
                        error_metrics = loaded_data or None

                    if error_metrics:
                        error_details = error_metrics.get("details", {})

                        def get_error_field(field_name, default=None):
                            return error_details.get(field_name, default)

                        coverage = get_error_field(
                            "analyze_error_handling"
                        ) or get_error_field("error_handling_coverage", "Unknown")
                        if coverage != "Unknown":
                            lines.append(
                                f"- **Error Handling Coverage**: {coverage:.1f}%"
                            )
                            lines.append(
                                f"- **Functions with Error Handling**: {get_error_field('functions_with_error_handling', 'Unknown')}"
                            )
                            lines.append(
                                f"- **Functions Missing Error Handling**: {get_error_field('functions_missing_error_handling', 'Unknown')}"
                            )

                            # Add Phase 1 and Phase 2 if available
                            phase1_total = get_error_field("phase1_total", 0)
                            if phase1_total > 0:
                                phase1_by_priority = (
                                    get_error_field("phase1_by_priority", {}) or {}
                                )
                                if not isinstance(phase1_by_priority, dict):
                                    phase1_by_priority = {}
                                priority_counts = []
                                if phase1_by_priority.get("high", 0) > 0:
                                    priority_counts.append(
                                        f"{phase1_by_priority['high']} high"
                                    )
                                if phase1_by_priority.get("medium", 0) > 0:
                                    priority_counts.append(
                                        f"{phase1_by_priority['medium']} medium"
                                    )
                                if phase1_by_priority.get("low", 0) > 0:
                                    priority_counts.append(
                                        f"{phase1_by_priority['low']} low"
                                    )
                                priority_text = (
                                    ", ".join(priority_counts)
                                    if priority_counts
                                    else "0"
                                )
                                lines.append(
                                    f"- **Phase 1 Candidates**: {phase1_total} functions need decorator replacement ({priority_text} priority)"
                                )

                            phase2_total = get_error_field("phase2_total", 0)
                            if phase2_total > 0:
                                phase2_by_type = (
                                    get_error_field("phase2_by_type", {}) or {}
                                )
                                if not isinstance(phase2_by_type, dict):
                                    phase2_by_type = {}
                                type_counts = [
                                    f"{count} {exc_type}"
                                    for exc_type, count in sorted(
                                        phase2_by_type.items(),
                                        key=lambda x: x[1],
                                        reverse=True,
                                    )[:3]
                                ]
                                type_text = (
                                    ", ".join(type_counts) if type_counts else "0"
                                )
                                if len(phase2_by_type) > 3:
                                    type_text += (
                                        f", ... +{len(phase2_by_type) - 3} more"
                                    )
                                lines.append(
                                    f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})"
                                )
                        else:
                            lines.append(
                                "- **Error Handling**: Run `python development_tools/run_development_tools.py audit` for detailed metrics"
                            )
            except Exception:
                pass

        lines.append("")
        lines.append("## Test Coverage")

        dev_tools_insights = self._get_dev_tools_coverage_insights()
        skip_main_tracks = bool(
            getattr(self, "_tier3_skipped_main_tracks", False)
        )
        skip_dev_track = bool(getattr(self, "_tier3_skipped_dev_track", False))

        if skip_main_tracks and self._is_dev_tools_scoped_report():
            lines.append(
                "- **Scope**: Lines below describe **`development_tools` package** coverage from "
                "this dev-tools-only Tier 3 pass only."
            )
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                dev_statements = dev_tools_insights.get("statements")
                dev_covered = dev_tools_insights.get("covered")
                summary_line = (
                    f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                )
                if dev_statements is not None and dev_covered is not None:
                    summary_line += (
                        f" ({dev_covered} of {dev_statements} statements)"
                    )
                lines.append(summary_line)
                gen_json = (
                    self.project_root
                    / "development_tools"
                    / "tests"
                    / "jsons"
                    / "generate_dev_tools_coverage_results.json"
                )
                if gen_json.exists():
                    href = self._markdown_href_from_dev_tools_report(gen_json)
                    lines.append(
                        f"    - **Machine-readable summary**: [generate_dev_tools_coverage_results.json]({href})"
                    )
            else:
                lines.append(
                    "- **Development Tools Coverage**: No parsed coverage insights for this pass."
                )
        elif skip_main_tracks:
            lines.append(
                "- **Overall Coverage**: **Skipped** — this pass used **`audit --full --dev-tools-only`**, "
                "so full-repo pytest/coverage did not run and `development_docs/TEST_COVERAGE_REPORT.md` "
                "was not rebuilt. For updated overall %, run "
                "`python development_tools/run_development_tools.py audit --full` (omit `--dev-tools-only`)."
            )
        elif coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            primary = coverage_summary.get("primary_overall") or {}
            use_primary = (
                primary
                and primary.get("statements", 0) > 0
                and primary.get("coverage") is not None
                and (overall.get("coverage") or 0) < 25
            )
            if use_primary:
                pct = primary.get("coverage")
                covered = primary.get("covered")
                stmts = primary.get("statements")
                domains = ", ".join(primary.get("domains", ["core", "communication", "ai", "user"]))
                lines.append(
                    f"- **Overall Coverage**: {percent_text(pct, 1)} "
                    f"({covered} of {stmts} statements)"
                )
                lines.append(
                    f"    - **Coverage Scope**: Primary domains (`{domains}`); "
                    "`ui`, `tasks`, `notebook` excluded (minimal test coverage). "
                    "`development_tools/` appears with other domains in "
                    "`development_docs/TEST_COVERAGE_REPORT.md` when the full detailed report is refreshed."
                )
            else:
                lines.append(
                    f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} "
                    f"({overall.get('covered')} of {overall.get('statements')} statements)"
                )
            coverage_report_path = (
                self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
            )
            if coverage_report_path.exists():
                href = self._markdown_href_from_dev_tools_report(coverage_report_path)
                lines.append(
                    f"    - **Detailed Report**: [TEST_COVERAGE_REPORT.md]({href})"
                )

            if skip_dev_track:
                lines.append(
                    "- **Development Tools Coverage**: Separate `--dev-tools-only` refresh not run in this "
                    "full-repo Tier 3 pass. The overall coverage line above already includes "
                    "`development_tools`; run "
                    "`python development_tools/run_development_tools.py audit --full --dev-tools-only` "
                    "only when you need refreshed DEV_TOOLS_* artifacts and the dedicated scoped track."
                )
            elif dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                dev_statements = dev_tools_insights.get("statements")
                dev_covered = dev_tools_insights.get("covered")
                summary_line = (
                    f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                )
                if dev_statements is not None and dev_covered is not None:
                    summary_line += f" ({dev_covered} of {dev_statements} statements)"
                lines.append(summary_line)
        else:
            if not skip_main_tracks:
                lines.append(
                    "- Coverage data unavailable; run `audit --full` to regenerate metrics"
                )
            if skip_dev_track:
                lines.append(
                    "- **Development Tools Coverage**: Separate `--dev-tools-only` refresh not run in this "
                    "full-repo Tier 3 pass. The overall coverage line above already includes "
                    "`development_tools`; run "
                    "`python development_tools/run_development_tools.py audit --full --dev-tools-only` "
                    "only when you need refreshed DEV_TOOLS_* artifacts and the dedicated scoped track."
                )
            elif dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                dev_statements = dev_tools_insights.get("statements")
                dev_covered = dev_tools_insights.get("covered")
                summary_line = (
                    f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                )
                if dev_statements is not None and dev_covered is not None:
                    summary_line += f" ({dev_covered} of {dev_statements} statements)"
                lines.append(summary_line)

        # Test markers
        test_markers_data = self._load_tool_data("analyze_test_markers", "tests")
        if test_markers_data and isinstance(test_markers_data, dict):
            if "summary" in test_markers_data:
                summary = test_markers_data.get("summary", {})
                missing_count = summary.get("total_issues", 0)
                details = test_markers_data.get("details", {})
                missing_list = details.get("missing", [])
            else:
                missing_count = test_markers_data.get("missing_count", 0)
                missing_list = test_markers_data.get("missing", [])

            if missing_count > 0 or (missing_list and len(missing_list) > 0):
                lines.append("## Test Markers")
                actual_count = (
                    missing_count
                    if missing_count > 0
                    else len(missing_list) if missing_list else 0
                )
                lines.append(
                    f"- **Missing Category Markers**: {actual_count} tests missing pytest category markers"
                )
            else:
                lines.append("## Test Markers")
                lines.append("- **Status**: CLEAN (all tests have category markers)")

        lines.append("")

        # Unused imports
        unused_imports_data = self._load_tool_data("analyze_unused_imports", "imports")
        if unused_imports_data and isinstance(unused_imports_data, dict):
            summary = unused_imports_data.get("summary", {})
            total_unused = summary.get("total_issues", 0)
            files_with_issues = summary.get("files_affected", 0)
            status = summary.get("status", "GOOD")
            details = unused_imports_data.get("details", {})
            by_category: dict[str, Any] = details.get("by_category") or {}
            perf = details.get("performance") or {}
            if self._is_dev_tools_scoped_report():
                scoped_imp = self._scoped_unused_imports_status_metrics(
                    unused_imports_data
                )
                if scoped_imp is None:
                    scoped_imp = (0, 0, {})
                total_unused, files_with_issues, by_category = scoped_imp
                if total_unused == 0:
                    status = "GOOD"
                elif total_unused < 20:
                    status = "NEEDS ATTENTION"
                else:
                    status = "CRITICAL"

            if total_unused > 0 or files_with_issues > 0:
                lines.append("## Unused Imports")
                if self._is_dev_tools_scoped_report():
                    lines.append(
                        "- **Scope**: Counts below are **development_tools/** files only "
                        "(same audit run may include unused imports elsewhere)."
                    )
                lines.append(
                    f"- **Total Unused**: {total_unused} imports across {files_with_issues} files"
                )
                if status:
                    lines.append(f"- **Status**: {status}")
                if by_category:
                    obvious = by_category.get("obvious_unused", 0)
                    type_only = by_category.get("type_hints_only", 0)
                    if obvious > 0:
                        lines.append(f"    - **Obvious Removals**: {obvious} imports")
                    if type_only > 0:
                        lines.append(
                            f"    - **Type-Only Imports**: {type_only} imports"
                        )
                if isinstance(perf, dict):
                    backend = perf.get("backend")
                    mode = perf.get("scan_mode")
                    files_per_second = perf.get("files_per_second")
                    total_seconds = (
                        perf.get("timings", {}).get("total_seconds")
                        if isinstance(perf.get("timings"), dict)
                        else None
                    )
                    if backend:
                        lines.append(f"    - **Backend**: {backend}")
                    if mode:
                        lines.append(f"    - **Scan Mode**: {mode}")
                    if isinstance(files_per_second, (int, float)):
                        lines.append(
                            f"    - **Throughput**: {float(files_per_second):.2f} files/sec"
                        )
                    if isinstance(total_seconds, (int, float)):
                        lines.append(
                            f"    - **Scan Time**: {float(total_seconds):.2f}s"
                        )
            else:
                lines.append("## Unused Imports")
                lines.append("- **Status**: CLEAN (no unused imports detected)")

            unused_imports_report_path = (
                self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
            )
            if unused_imports_report_path.exists():
                href = self._markdown_href_from_dev_tools_report(
                    unused_imports_report_path
                )
                lines.append(
                    f"- **Detailed Report**: [UNUSED_IMPORTS_REPORT.md]({href})"
                )
        else:
            lines.append("## Unused Imports")
            lines.append(
                "- **Status**: Data unavailable (run `audit --full` for latest scan)"
            )

        lines.append("")
        lines.append("## Static Analysis")
        if isinstance(static_analysis, dict):
            ruff_data = static_analysis.get("analyze_ruff", {})
            pyright_data = static_analysis.get("analyze_pyright", {})
            bandit_data = static_analysis.get("analyze_bandit", {})
            pip_audit_data = static_analysis.get("analyze_pip_audit", {})
            ruff_summary = (
                ruff_data.get("summary", {}) if isinstance(ruff_data, dict) else {}
            )
            pyright_summary = (
                pyright_data.get("summary", {})
                if isinstance(pyright_data, dict)
                else {}
            )
            bandit_summary = (
                bandit_data.get("summary", {})
                if isinstance(bandit_data, dict)
                else {}
            )
            pip_audit_summary = (
                pip_audit_data.get("summary", {})
                if isinstance(pip_audit_data, dict)
                else {}
            )
            ruff_details = (
                ruff_data.get("details", {}) if isinstance(ruff_data, dict) else {}
            )
            pyright_details = (
                pyright_data.get("details", {})
                if isinstance(pyright_data, dict)
                else {}
            )
            bandit_details = (
                bandit_data.get("details", {})
                if isinstance(bandit_data, dict)
                else {}
            )
            pip_audit_details = (
                pip_audit_data.get("details", {})
                if isinstance(pip_audit_data, dict)
                else {}
            )
            ruff_available = bool(ruff_data.get("available", False))
            pyright_available = bool(pyright_data.get("available", False))
            bandit_available = bool(bandit_data.get("available", False))
            pip_audit_available = bool(pip_audit_data.get("available", False))
            lines.append(
                f"- **Ruff**: {ruff_summary.get('status', 'UNKNOWN')} "
                f"({to_int(ruff_summary.get('total_issues')) or 0} issue(s) across "
                f"{to_int(ruff_summary.get('files_affected')) or 0} file(s))"
            )
            pyright_errors = to_int(pyright_details.get("errors")) or 0
            pyright_warnings = to_int(pyright_details.get("warnings")) or 0
            lines.append(
                f"- **Pyright**: {pyright_summary.get('status', 'UNKNOWN')} "
                f"({pyright_errors} error(s), {pyright_warnings} warning(s))"
            )
            lines.append(
                f"- **Bandit**: {bandit_summary.get('status', 'UNKNOWN')} "
                f"({to_int(bandit_summary.get('total_issues')) or 0} MEDIUM/HIGH issue(s) across "
                f"{to_int(bandit_summary.get('files_affected')) or 0} file(s))"
            )
            lines.append(
                f"- **pip-audit**: {pip_audit_summary.get('status', 'UNKNOWN')} "
                f"({to_int(pip_audit_summary.get('total_issues')) or 0} vulnerability finding(s) across "
                f"{to_int(pip_audit_summary.get('files_affected')) or 0} package(s))"
                f"{self._pip_audit_elapsed_suffix(pip_audit_details)}"
            )
            if not ruff_available:
                message = str(ruff_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Ruff unavailable: {message}")
            if not pyright_available:
                message = str(pyright_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Pyright unavailable: {message}")
            if not bandit_available:
                message = str(bandit_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Bandit unavailable: {message}")
            if not pip_audit_available:
                message = str(pip_audit_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - pip-audit unavailable: {message}")
        else:
            lines.append(
                "- Static analysis data unavailable (run `audit --full` for latest diagnostics)"
            )

        lines.append("")
        lines.append("## Dependency Patterns")
        if self._is_dev_tools_scoped_report():
            lines.append(
                "- **Scope note**: Import/coupling metrics below are for the "
                "`development_tools/` scan root only. Product-wide dependency signals "
                "are in `AI_STATUS.md` from a default-scope audit."
            )
        dependency_patterns_details = (
            dependency_patterns_data.get("details", {})
            if isinstance(dependency_patterns_data, dict)
            else {}
        )
        dependency_patterns_payload = (
            dependency_patterns_details.get("data", dependency_patterns_details)
            if isinstance(dependency_patterns_details, dict)
            else {}
        )
        if (
            isinstance(dependency_patterns_payload, dict)
            and not dependency_patterns_payload
            and isinstance(dependency_patterns_data, dict)
        ):
            dependency_patterns_payload = dependency_patterns_data.get(
                "data", dependency_patterns_data
            )

        if isinstance(dependency_patterns_payload, dict):
            circular_dependencies = (
                dependency_patterns_payload.get("circular_dependencies", []) or []
            )
            high_coupling = dependency_patterns_payload.get("high_coupling", []) or []
            circular_count = (
                len(circular_dependencies)
                if isinstance(circular_dependencies, list)
                else 0
            )
            high_coupling_count = (
                len(high_coupling) if isinstance(high_coupling, list) else 0
            )

            if circular_count == 0 and high_coupling_count == 0:
                lines.append(
                    "- **Status**: CLEAN (no circular dependencies or high coupling detected)"
                )
            else:
                lines.append(
                    f"- **Circular Dependencies**: {circular_count} circular dependency chain(s)"
                )
                lines.append(
                    f"- **High Coupling**: {high_coupling_count} high-coupling module(s)"
                )
        else:
            lines.append(
                "- **Status**: Data unavailable (run `audit` or `audit --full` to scan dependency patterns)"
            )

        lines.append("")
        lines.append("## Import Boundary")
        import_boundary_summary = (
            import_boundary_data.get("summary", {})
            if isinstance(import_boundary_data, dict)
            else {}
        )
        import_violations = to_int(import_boundary_summary.get("total_issues"))
        import_files = to_int(import_boundary_summary.get("files_affected"))
        if import_violations is not None and import_violations > 0:
            lines.append(
                f"- **Violations**: {import_violations} non-approved core import(s) across {import_files or 0} file(s)"
            )
            details_obj = import_boundary_data.get("details", {}) or {}
            violations_list = details_obj.get("violations", []) or []
            if violations_list:
                top_files = list({v.get("file", "") for v in violations_list[:5]})
                for f in top_files[:3]:
                    if f:
                        lines.append(f"  - {f}")
            lines.append(
                "- **Action**: Refactor to use only approved imports (`core.logger`); see DEVELOPMENT_TOOLS_GUIDE.md §8.5"
            )
        elif import_violations == 0:
            lines.append("- **Status**: CLEAN (no boundary violations detected)")
        else:
            lines.append(
                "- **Status**: Data unavailable (run `audit` to scan import boundaries)"
            )

        lines.append("")
        lines.append("## Legacy References")

        legacy_summary = legacy_summary or legacy_data or {}
        if (
            legacy_summary
            and "summary" in legacy_summary
            and isinstance(legacy_summary.get("summary"), dict)
        ):
            summary = legacy_summary["summary"]
            legacy_issues = summary.get("files_affected", 0)
            details = legacy_summary.get("details", {})
            report_path = details.get("report_path")

            if legacy_issues == 0:
                lines.append("- **Legacy References**: CLEAN (0 files flagged)")
            else:
                lines.append(
                    f"- **Legacy References**: {legacy_issues} files still reference legacy patterns"
                )

            if report_path:
                report_path_obj = self._resolve_report_path(report_path)
                if report_path_obj.exists():
                    href = self._markdown_href_from_dev_tools_report(report_path_obj)
                    lines.append(
                        f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({href})"
                    )
        else:
            lines.append(
                "- Legacy reference data unavailable (run `audit --full` for latest scan)"
            )

        lines.append("")
        lines.append("## Duplicate Functions")
        if self._is_dev_tools_scoped_report():
            lines.append(
                "- **Scope note**: Duplicate groups are detected within the "
                "`development_tools/` scan only (not a product-wide duplicate audit)."
            )
        duplicate_data = self._load_tool_data(
            "analyze_duplicate_functions", "functions"
        )
        duplicate_summary = (
            duplicate_data.get("summary", {})
            if isinstance(duplicate_data, dict)
            else {}
        )
        duplicate_details_status = (
            duplicate_data.get("details", {})
            if isinstance(duplicate_data, dict)
            else {}
        )
        duplicate_groups = to_int(duplicate_summary.get("total_issues")) or 0
        duplicate_files = to_int(duplicate_summary.get("files_affected")) or 0
        if duplicate_files == 0 and isinstance(duplicate_details_status, dict):
            duplicate_groups_list = duplicate_details_status.get("duplicate_groups", [])
            if isinstance(duplicate_groups_list, list) and duplicate_groups_list:
                duplicate_files = self._count_duplicate_affected_files(
                    duplicate_groups_list
                )
        dup_capped = isinstance(
            duplicate_details_status, dict
        ) and duplicate_details_status.get("groups_capped", False)
        if duplicate_groups > 0:
            groups_label = (
                f"at least {duplicate_groups}" if dup_capped else str(duplicate_groups)
            )
            lines.append(
                f"- **Potential Duplicate Groups**: {groups_label} (files affected: {duplicate_files})"
            )
        else:
            lines.append("- **Potential Duplicate Groups**: 0")

        lines.append("")
        lines.append("## Module Refactor Candidates")
        refactor_data = self._load_tool_data(
            "analyze_module_refactor_candidates", "functions"
        )
        refactor_summary = (
            refactor_data.get("summary", {}) if isinstance(refactor_data, dict) else {}
        )
        refactor_count = to_int(refactor_summary.get("total_issues")) or 0
        prio_ref = (
            "DEV_TOOLS_PRIORITIES"
            if self._is_dev_tools_scoped_report()
            else "AI_PRIORITIES"
        )
        if refactor_count > 0:
            lines.append(
                f"- **Large/High-Complexity Modules**: {refactor_count} candidate(s) "
                f"for refactoring (see {prio_ref})"
            )
        else:
            lines.append("- **Large/High-Complexity Modules**: 0 candidates")

        lines.append("")
        lines.append("## Validation Status")

        validation_output = ""
        if hasattr(self, "validation_results") and self.validation_results:
            validation_output = self.validation_results.get("output", "") or ""

        if not validation_output or not validation_output.strip():
            validation_data = self._load_tool_data(
                "analyze_ai_work", "ai_work", log_source=True
            )
            if validation_data:
                validation_output = validation_data.get("output", "") or ""

        if validation_output and validation_output.strip():
            if "POOR" in validation_output:
                lines.append(
                    "- **AI Work Validation**: POOR — structural gaps likely; confirm with "
                    "`doc-sync`, `TEST_COVERAGE_REPORT.md`, and `error_handling/analyze_error_handling.py` "
                    "rather than relying on this summary alone"
                )
            elif "GOOD" in validation_output:
                lines.append("- **AI Work Validation**: GOOD - keep current standards")
            elif "NEEDS ATTENTION" in validation_output or "FAIR" in validation_output:
                lines.append(
                    "- **AI Work Validation**: NEEDS ATTENTION — use doc-sync, coverage report, "
                    "and domain analyzers for file-level next steps (this tool is structural only)"
                )
            else:
                lines.append(
                    "- **AI Work Validation**: Status available (see consolidated report)"
                )
        else:
            # Check if we're in a tier that doesn't run analyze_ai_work (Tier 1)
            tools_run = getattr(self, "_tools_run_in_current_tier", set())
            if "analyze_ai_work" not in tools_run:
                # Try to load cached validation data
                validation_data = self._load_tool_data(
                    "analyze_ai_work", "ai_work", log_source=False
                )
                if validation_data:
                    cached_output = validation_data.get("output", "") or ""
                    if cached_output and cached_output.strip():
                        if "POOR" in cached_output:
                            lines.append(
                                "- **AI Work Validation**: POOR (cached) — confirm with doc-sync, "
                                "coverage, and error-handling tools for specifics"
                            )
                        elif "GOOD" in cached_output:
                            lines.append(
                                "- **AI Work Validation**: GOOD - keep current standards (cached)"
                            )
                        elif (
                            "NEEDS ATTENTION" in cached_output
                            or "FAIR" in cached_output
                        ):
                            lines.append(
                                "- **AI Work Validation**: NEEDS ATTENTION (cached) — follow up with "
                                "doc-sync and domain analyzers (structural signal only)"
                            )
                        else:
                            lines.append(
                                "- **AI Work Validation**: Status available (cached, see consolidated report)"
                            )
                    else:
                        lines.append(
                            "- **AI Work Validation**: Using cached data (run `audit` or `audit --full` for latest validation)"
                        )
                else:
                    lines.append(
                        "- **AI Work Validation**: Using cached data (run `audit` or `audit --full` for latest validation)"
                    )
            else:
                lines.append(
                    "- Validation results unavailable (run `audit` for latest validation)"
                )

        lines.append("")
        lines.append("## Backup Health")

        if backup_summary:
            backup_status = str(
                backup_summary.get(
                    "status",
                    "PASS" if bool(backup_summary.get("success")) else "FAIL",
                )
            ).upper()
            lines.append(f"- **Status**: {backup_status}")
            passed_checks = backup_summary.get("passed_checks")
            total_checks = backup_summary.get("total_checks")
            if isinstance(passed_checks, int) and isinstance(total_checks, int):
                lines.append(f"- **Checks**: {passed_checks}/{total_checks} passed")
            latest_backup_path = backup_summary.get("latest_backup_path")
            if latest_backup_path:
                lines.append(f"- **Latest Backup Artifact**: `{latest_backup_path}`")
            latest_created_at = backup_summary.get("latest_backup_created_at")
            if latest_created_at:
                lines.append(f"- **Latest Backup Created At**: {latest_created_at}")
            backup_present_status = "UNKNOWN"
            backup_recent_status = "UNKNOWN"
            if isinstance(backup_checks, list):
                for check in backup_checks:
                    if not isinstance(check, dict):
                        continue
                    check_name = str(check.get("name") or "")
                    if check_name in {"backup_present", "weekly_backup_present"}:
                        backup_present_status = (
                            "PASS" if bool(check.get("success")) else "FAIL"
                        )
                    if check_name in {
                        "backups_recent_enough",
                        "weekly_backup_recent_enough",
                    }:
                        backup_recent_status = (
                            "PASS" if bool(check.get("success")) else "FAIL"
                        )
            lines.append(f"- **Weekly Backup Presence**: {backup_present_status}")
            lines.append(f"- **Weekly Backup Recency**: {backup_recent_status}")

            drill_status = "SKIPPED"
            if isinstance(backup_checks, list):
                for check in backup_checks:
                    if isinstance(check, dict) and check.get("name") == "restore_drill":
                        drill_status = "PASS" if bool(check.get("success")) else "FAIL"
                        break
            elif bool(backup_summary.get("drill_executed")):
                drill_status = "UNKNOWN"
            lines.append(f"- **Restore Drill**: {drill_status}")
        else:
            lines.append(
                "- Backup health data unavailable (run `python development_tools/run_development_tools.py backup verify`)"
            )

        lines.append("")
        lines.append("## System Signals")
        lines.append(
            "- **Scope**: Operational health (audit freshness, test coverage pulse, core files, alerts). "
            "Documentation pairing and sync are under **Documentation Signals**, not duplicated here."
        )

        if hasattr(self, "system_signals") and self.system_signals:
            system_signals = self._get_system_signals_details(self.system_signals)
            system_health = system_signals.get("system_health", {})
            overall_status = system_health.get("overall_status", "OK")
            lines.append(f"- **System Health**: {overall_status}")

            # Add audit freshness (consolidated - don't show redundant last_audit)
            audit_freshness = system_health.get("audit_freshness")
            if audit_freshness:
                lines.append(f"  - Audit data: {audit_freshness}")

            # Add test coverage status (doc sync is redundant - already shown in Snapshot and Documentation Signals)
            test_coverage_status = system_health.get("test_coverage_status")
            if test_coverage_status and test_coverage_status != "Unknown":
                lines.append(f"  - Test coverage: {test_coverage_status}")

            # Show actual warnings/critical issues (not just counts)
            severity_levels = system_health.get("severity_levels", {})
            if severity_levels:
                critical_issues = severity_levels.get("CRITICAL", [])
                warnings = severity_levels.get("WARNING", [])
                if critical_issues:
                    for issue in critical_issues[:2]:  # Show first 2 critical issues
                        lines.append(f"  - Critical: {issue}")
                if warnings:
                    for warning in warnings[:2]:  # Show first 2 warnings
                        lines.append(f"  - Warning: {warning}")

            missing_core = [
                name
                for name, state in (system_health.get("core_files") or {}).items()
                if state != "OK"
            ]
            if missing_core:
                lines.append(
                    f"- **Core File Issues**: {self._format_list_for_display(missing_core, limit=3)}"
                )

            recent_activity = system_signals.get("recent_activity", {})
            recent_changes = recent_activity.get("recent_changes") or []
            if recent_changes:
                lines.append(
                    f"- **Recent Changes**: {self._format_list_for_display(recent_changes, limit=3)}"
                )

            critical_alerts = system_signals.get("critical_alerts", [])
            if critical_alerts:
                lines.append(
                    f"- **Critical Alerts**: {len(critical_alerts)} active alert(s)"
                )
                for alert in critical_alerts[:3]:
                    alert_text = (
                        alert
                        if isinstance(alert, str)
                        else alert.get("message", str(alert))
                    )
                    lines.append(f"  - {alert_text}")
        else:
            # Try to load cached system signals
            signals_loaded = False
            try:
                cached_data = self._load_results_file_safe()
                if cached_data:
                    signals_data = None
                    if "results" in cached_data:
                        if "analyze_system_signals" in cached_data["results"]:
                            signals_data = cached_data["results"][
                                "analyze_system_signals"
                            ]

                    if signals_data:
                        if "data" in signals_data:
                            system_signals = self._get_system_signals_details(
                                signals_data["data"]
                            )
                        else:
                            system_signals = self._get_system_signals_details(
                                signals_data
                            )

                        if system_signals:
                            signals_loaded = True
                            system_health = system_signals.get("system_health", {})
                            overall_status = system_health.get("overall_status", "OK")
                            lines.append(f"- **System Health**: {overall_status}")

                            # Add audit freshness (consolidated - don't show redundant last_audit)
                            audit_freshness = system_health.get("audit_freshness")
                            if audit_freshness:
                                lines.append(f"  - Audit data: {audit_freshness}")

                            # Add test coverage status (doc sync is redundant - already shown in Snapshot and Documentation Signals)
                            test_coverage_status = system_health.get(
                                "test_coverage_status"
                            )
                            if (
                                test_coverage_status
                                and test_coverage_status != "Unknown"
                            ):
                                lines.append(
                                    f"  - Test coverage: {test_coverage_status}"
                                )

                            # Show actual warnings/critical issues (not just counts)
                            severity_levels = system_health.get("severity_levels", {})
                            if severity_levels:
                                critical_issues = severity_levels.get("CRITICAL", [])
                                warnings = severity_levels.get("WARNING", [])
                                if critical_issues:
                                    for issue in critical_issues[
                                        :2
                                    ]:  # Show first 2 critical issues
                                        lines.append(f"  - Critical: {issue}")
                                if warnings:
                                    for warning in warnings[
                                        :2
                                    ]:  # Show first 2 warnings
                                        lines.append(f"  - Warning: {warning}")

                            missing_core = [
                                name
                                for name, state in (
                                    system_health.get("core_files") or {}
                                ).items()
                                if state != "OK"
                            ]
                            if missing_core:
                                lines.append(
                                    f"- **Core File Issues**: {self._format_list_for_display(missing_core, limit=3)}"
                                )

                            recent_activity = system_signals.get("recent_activity", {})
                            recent_changes = recent_activity.get("recent_changes") or []
                            if recent_changes:
                                lines.append(
                                    f"- **Recent Changes**: {self._format_list_for_display(recent_changes, limit=3)}"
                                )

                            critical_alerts = system_signals.get("critical_alerts", [])
                            if critical_alerts:
                                lines.append(
                                    f"- **Critical Alerts**: {len(critical_alerts)} active alerts"
                                )
            except Exception as e:
                logger.debug(f"Failed to load system signals from cache: {e}")

            if not signals_loaded:
                lines.append(
                    "- System signals data unavailable (run `system-signals` command)"
                )

        lines.append("")
        self._append_tier3_test_outcome_lines(lines)
        lines.append("## Quick Commands")
        if self._is_dev_tools_scoped_report():
            lines.append(
                "- `python development_tools/run_development_tools.py audit --full` - "
                "Regenerate full-repo `AI_STATUS.md` and refresh `coverage.json` / product metrics"
            )
            lines.append(
                "- `python development_tools/run_development_tools.py audit --full --dev-tools-only` - "
                "Regenerate this file (`DEV_TOOLS_*`) and dev-tools coverage only"
            )
            lines.append(
                "- `python development_tools/run_development_tools.py status` - Read-only; "
                "uses cached aggregate results (full-repo oriented; prefer the commands above for scoped refresh)"
            )
        else:
            lines.append(
                "- `python development_tools/run_development_tools.py status` - Refresh this snapshot"
            )
            lines.append(
                "- `python development_tools/run_development_tools.py audit --full` - Regenerate all metrics"
            )
        lines.append(
            "- `python development_tools/run_development_tools.py doc-sync` - Update documentation pairing data"
        )
        lines.append("")

        return "\n".join(lines)

    def _generate_ai_priorities_document(self) -> str:
        """Generate AI-optimized priorities document with immediate next steps."""
        # Log data source context
        audit_tier = getattr(self, "current_audit_tier", None)
        priorities_target = (
            "DEV_TOOLS_PRIORITIES.md"
            if self._is_dev_tools_scoped_report()
            else "AI_PRIORITIES.md"
        )
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating {priorities_target} using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating {priorities_target} using cached data (no active audit)"
            )

        # Check if this is a mid-audit write
        instance_flag = hasattr(self, "_audit_in_progress") and self._audit_in_progress
        audit_in_progress = instance_flag or _is_audit_in_progress(self.project_root)
        is_legitimate_end_write = (
            hasattr(self, "current_audit_tier") and self.current_audit_tier is not None
        )

        if audit_in_progress and not is_legitimate_end_write:
            if not instance_flag:
                logger.warning(
                    "_generate_ai_priorities_document() called from NEW instance during audit! This should only happen at the end."
                )
            else:
                logger.warning(
                    "_generate_ai_priorities_document() called during audit! This should only happen at the end."
                )
            import traceback

            logger.debug(f"Call stack:\n{''.join(traceback.format_stack())}")

        lines: list[str] = []
        if self._is_dev_tools_scoped_report():
            lines.append("# Development Tools Priorities - Immediate Next Steps")
            lines.append("")
            lines.append("> **File**: `development_tools/DEV_TOOLS_PRIORITIES.md`")
        else:
            lines.append("# AI Priorities - Immediate Next Steps")
            lines.append("")
            lines.append("> **File**: `development_tools/AI_PRIORITIES.md`")
        lines.append(
            "> **Generated**: This file is auto-generated. Do not edit manually."
        )
        lines.append(
            f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if self.current_audit_tier == 1:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --quick"
            )
            tier_name = "Tier 1 (Quick Audit)"
        elif self.current_audit_tier == 3:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --full"
            )
            tier_name = "Tier 3 (Full Audit)"
        elif self.current_audit_tier == 2:
            source_cmd = "python development_tools/run_development_tools.py audit"
            tier_name = "Tier 2 (Standard Audit)"
        else:
            source_cmd = "python development_tools/run_development_tools.py status"
            tier_name = "Status Check (cached data)"
        lines.append(f"> **Source**: `{self._audit_source_cmd_display(source_cmd)}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        if self._is_dev_tools_scoped_report():
            lines.append(
                "> **Role**: Ranked queue for dev-tools work only; domain/product priorities may be stale or absent vs `AI_PRIORITIES.md`."
            )
            lines.append(
                "> **Scope**: Metrics derive from a `development_tools/` scan when `--dev-tools-only` was used."
            )
            lines.append(
                "> **Artifact layout**: Scoped storage only (`**/jsons/scopes/dev_tools/`, `reports/scopes/dev_tools/`); see DEV_TOOLS_STATUS header for detail."
            )
        else:
            lines.append(
                "> **Role**: Ranked action queue for AI work, with guidance sources and detail references per item."
            )
        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed if trimmed.endswith("%") else f"{trimmed}%"
            return self._format_percentage(value, decimals)

        def to_int(value: Any) -> int | None:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return int(float(stripped))
                except ValueError:
                    return None
            if isinstance(value, dict):
                count = value.get("count")
                return to_int(count)
            return None

        def to_float(value: Any) -> float | None:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return float(stripped)
                except ValueError:
                    return None
            return None

        metrics = self._get_canonical_metrics()
        doc_metrics = self._load_tool_data("analyze_function_registry", "functions")
        error_metrics = self._load_tool_data("analyze_error_handling", "error_handling")
        function_metrics = self._load_tool_data("analyze_functions", "functions")
        doc_sync_data = self._load_tool_data(
            "analyze_documentation_sync", "docs", log_source=True
        )
        doc_sync_summary = self.docs_sync_summary or doc_sync_data or {}
        legacy_data = self._load_tool_data("analyze_legacy_references", "legacy")
        legacy_summary = self.legacy_cleanup_summary or legacy_data or {}
        coverage_summary = self._load_coverage_summary()

        if (
            not hasattr(self, "dev_tools_coverage_results")
            or not self.dev_tools_coverage_results
        ):
            self._load_dev_tools_coverage()

        analyze_data = self._load_tool_data("analyze_documentation", "docs")
        ascii_data = self._load_tool_data("analyze_ascii_compliance", "docs")
        heading_data = self._load_tool_data("analyze_heading_numbering", "docs")
        missing_addresses_data = self._load_tool_data(
            "analyze_missing_addresses", "docs"
        )
        unconverted_links_data = self._load_tool_data(
            "analyze_unconverted_links", "docs"
        )
        test_markers_data = self._load_tool_data("analyze_test_markers", "tests")
        verify_process_cleanup_priority_data = self._load_tool_data(
            "verify_process_cleanup", "tests"
        )
        unused_imports_data = self._load_tool_data("analyze_unused_imports", "imports")
        dependency_patterns_data = self._load_tool_data(
            "analyze_dependency_patterns", "imports"
        )
        import_boundary_data = self._load_tool_data(
            "analyze_dev_tools_import_boundaries", "imports"
        )
        duplicate_functions_data = self._load_tool_data(
            "analyze_duplicate_functions", "functions"
        )
        module_refactor_candidates_data = self._load_tool_data(
            "analyze_module_refactor_candidates", "functions"
        )
        backup_health_data = self._load_tool_data(
            "analyze_backup_health", "reports", log_source=False
        )
        static_analysis = self._get_static_analysis_snapshot()

        analyze_details = (
            analyze_data.get("details", {}) if isinstance(analyze_data, dict) else {}
        )
        section_overlaps = analyze_data.get("section_overlaps")
        if section_overlaps is None and isinstance(analyze_details, dict):
            section_overlaps = analyze_details.get("section_overlaps", {})
        consolidation_recs = analyze_data.get("consolidation_recommendations")
        if consolidation_recs is None and isinstance(analyze_details, dict):
            consolidation_recs = analyze_details.get(
                "consolidation_recommendations", []
            )
        if section_overlaps is None:
            section_overlaps = {}
        if consolidation_recs is None:
            consolidation_recs = []

        dependency_details = (
            dependency_patterns_data.get("details", {})
            if isinstance(dependency_patterns_data, dict)
            else {}
        )
        dependency_payload = (
            dependency_details.get("data", dependency_details)
            if isinstance(dependency_details, dict)
            else {}
        )
        if (
            isinstance(dependency_payload, dict)
            and not dependency_payload
            and isinstance(dependency_patterns_data, dict)
        ):
            dependency_payload = dependency_patterns_data.get(
                "data", dependency_patterns_data
            )

        doc_metrics_details = doc_metrics.get("details", {})
        doc_coverage_value = metrics.get("doc_coverage")
        if doc_coverage_value is None or doc_coverage_value == "Unknown":
            doc_coverage_value = doc_metrics_details.get("coverage")

        # Use analyze_functions for missing docstrings (checks code docstrings)
        # NOT analyze_function_registry (checks registry file coverage - different metric)
        function_metrics_for_missing = function_metrics
        func_metrics_details_for_missing = (
            function_metrics_for_missing.get("details", {})
            if isinstance(function_metrics_for_missing, dict)
            else {}
        )
        missing_docstrings_from_functions = (
            func_metrics_details_for_missing.get("undocumented", 0)
            or function_metrics_for_missing.get("undocumented", 0)
            if isinstance(function_metrics_for_missing, dict)
            else 0
        )

        missing_docs_raw = doc_metrics_details.get("missing", {})

        if isinstance(missing_docs_raw, dict):
            missing_docs_count = missing_docs_raw.get("count", 0)
        else:
            missing_docs_count = to_int(missing_docs_raw) or 0

        missing_doc_files = (
            missing_docs_raw.get("missing_files")
            if isinstance(missing_docs_raw, dict)
            else self._get_missing_doc_files(limit=5)
        )
        if not missing_doc_files:
            missing_doc_files = self._get_missing_doc_files(limit=5)

        # Use analyze_functions data for missing docstrings (code docstrings, not registry file)
        # Calculate from function_metrics, not doc_metrics (registry)
        if (
            missing_docstrings_from_functions is not None
            and missing_docstrings_from_functions >= 0
        ):
            missing_docs_count_for_priority = missing_docstrings_from_functions
        else:
            # Fallback: calculate from function_metrics if undocumented count not available
            func_total = (
                func_metrics_details_for_missing.get("total_functions")
                or function_metrics_for_missing.get("total_functions")
                if isinstance(function_metrics_for_missing, dict)
                else None
            )
            if func_total and func_total > 0:
                # Try to get documented count from function_metrics
                func_documented = (
                    func_metrics_details_for_missing.get("documented", 0)
                    or function_metrics_for_missing.get("documented", 0)
                    if isinstance(function_metrics_for_missing, dict)
                    else None
                )
                if func_documented is not None:
                    missing_docs_calculated = func_total - func_documented
                    missing_docs_count_for_priority = missing_docs_calculated
                else:
                    # Last resort: use registry data (but this measures registry file, not code docstrings)
                    total_funcs = metrics.get("total_functions")
                    doc_totals = doc_metrics_details.get("totals") or {}
                    documented_funcs = (
                        doc_totals.get("functions_documented")
                        if isinstance(doc_totals, dict)
                        else None
                    )
                    if total_funcs and documented_funcs is not None:
                        missing_docs_calculated = total_funcs - documented_funcs
                        missing_docs_count_for_priority = (
                            missing_docs_calculated
                            if missing_docs_count is None or missing_docs_count == 0
                            else missing_docs_count
                        )
                    else:
                        missing_docs_count_for_priority = missing_docs_count or 0
            else:
                missing_docs_count_for_priority = missing_docs_count or 0

        error_details = error_metrics.get("details", {})

        def get_error_field(field_name, default=None):
            return error_details.get(field_name, default)

        error_coverage = get_error_field("analyze_error_handling") or get_error_field(
            "error_handling_coverage"
        )
        error_total = get_error_field("total_functions")
        error_with_handling = get_error_field("functions_with_error_handling")
        metrics.get("total_functions")
        missing_error_handlers = to_int(
            get_error_field("functions_missing_error_handling")
        )

        if error_total and error_with_handling:
            calc_coverage = (error_with_handling / error_total) * 100
            if 0 <= calc_coverage <= 100:
                error_coverage = calc_coverage
        elif error_coverage is None and error_total and error_with_handling:
            error_coverage = (error_with_handling / error_total) * 100

        worst_error_modules = get_error_field("worst_modules", []) or []
        if worst_error_modules is None or not isinstance(
            worst_error_modules, (list, tuple)
        ):
            worst_error_modules = []

        def get_doc_sync_field(data, field_name, default=None):
            if not data or not isinstance(data, dict):
                return default
            if "summary" not in data or not isinstance(data.get("summary"), dict):
                return default
            if field_name == "status":
                return data["summary"].get("status", default)
            if field_name == "total_issues":
                return data["summary"].get("total_issues", default)
            return data.get("details", {}).get(field_name, default)

        path_drift_count = (
            to_int(get_doc_sync_field(doc_sync_summary, "path_drift_issues"))
            if doc_sync_summary
            else None
        )
        path_drift_files = (
            get_doc_sync_field(doc_sync_summary, "path_drift_files", [])
            if doc_sync_summary
            else []
        )
        if path_drift_files is None or not isinstance(path_drift_files, list):
            path_drift_files = []
        path_drift_files = [
            f
            for f in path_drift_files
            if f
            and isinstance(f, str)
            and not (
                f.isupper()
                and (
                    "ISSUES" in f
                    or "COMPLIANCE" in f
                    or "DOCUMENTATION" in f
                    or "NUMBERING" in f
                )
            )
        ]
        paired_doc_issues = (
            to_int(get_doc_sync_field(doc_sync_summary, "paired_doc_issues"))
            if doc_sync_summary
            else None
        )
        ascii_issues = (
            to_int(get_doc_sync_field(doc_sync_summary, "ascii_issues"))
            if doc_sync_summary
            else None
        )

        if legacy_summary and isinstance(legacy_summary, dict):
            if "summary" in legacy_summary and isinstance(
                legacy_summary.get("summary"), dict
            ):
                legacy_files = to_int(
                    legacy_summary["summary"].get("files_affected", 0)
                )
                legacy_details = legacy_summary.get("details", {})
                legacy_markers = to_int(legacy_details.get("legacy_markers", 0))
                legacy_report = legacy_details.get("report_path")
            else:
                legacy_files = None
                legacy_markers = None
                legacy_report = None
        else:
            legacy_files = None
            legacy_markers = None
            legacy_report = None

        low_coverage_modules: list[dict[str, Any]] = []
        if coverage_summary:
            module_entries = (coverage_summary or {}).get("modules") or []
            for module in module_entries:
                coverage_value = to_float(module.get("coverage"))
                coverage_float = (
                    to_float(coverage_value) if coverage_value is not None else None
                )
                if coverage_float is not None and coverage_float < 80:
                    low_coverage_modules.append(module)
            low_coverage_modules = low_coverage_modules[:3]

        if (
            hasattr(self, "dev_tools_coverage_results")
            and self.dev_tools_coverage_results
        ):
            _ = self.dev_tools_coverage_results.get("overall", {})
        dev_tools_insights = self._get_dev_tools_coverage_insights()

        analyze_artifacts = analyze_data.get("artifacts") or []
        analyze_duplicates = analyze_data.get("duplicates") or []
        analyze_placeholders = analyze_data.get("placeholders") or []

        function_metrics_details = (
            function_metrics.get("details", {})
            if isinstance(function_metrics, dict)
            else {}
        )
        critical_examples = (
            function_metrics_details.get("critical_complexity_examples")
            or (
                function_metrics.get("critical_complexity_examples")
                if isinstance(function_metrics, dict)
                else []
            )
            or []
        )
        high_examples = (
            function_metrics_details.get("high_complexity_examples")
            or (
                function_metrics.get("high_complexity_examples")
                if isinstance(function_metrics, dict)
                else []
            )
            or []
        )

        # Try loading from multiple sources, prioritizing analyze_functions (global source),
        # then decision_support as fallback.
        if (not critical_examples or len(critical_examples) == 0) or (
            not high_examples or len(high_examples) == 0
        ):
            func_result = self._load_tool_data(
                "analyze_functions", "functions", log_source=False
            )
            if func_result and isinstance(func_result, dict):
                func_details = func_result.get("details", {})
                if not critical_examples or len(critical_examples) == 0:
                    if "critical_complexity_examples" in func_details:
                        critical_examples = func_details.get(
                            "critical_complexity_examples", []
                        )
                        if critical_examples:
                            function_metrics["critical_complexity_examples"] = (
                                critical_examples
                            )
                    elif "critical_complexity_examples" in func_result:
                        critical_examples = func_result.get(
                            "critical_complexity_examples", []
                        )
                        if critical_examples:
                            function_metrics["critical_complexity_examples"] = (
                                critical_examples
                            )
                if not high_examples or len(high_examples) == 0:
                    if "high_complexity_examples" in func_details:
                        high_examples = func_details.get("high_complexity_examples", [])
                        if high_examples:
                            function_metrics["high_complexity_examples"] = high_examples
                    elif "high_complexity_examples" in func_result:
                        high_examples = func_result.get("high_complexity_examples", [])
                        if high_examples:
                            function_metrics["high_complexity_examples"] = high_examples

        decision_metrics = self._get_decision_support_details(
            self.results_cache.get("decision_support")
        )
        if decision_metrics:
            if (
                not critical_examples or len(critical_examples) == 0
            ) and "critical_complexity_examples" in decision_metrics:
                critical_examples = decision_metrics.get(
                    "critical_complexity_examples", []
                )
                if critical_examples:
                    function_metrics["critical_complexity_examples"] = critical_examples
            if (
                not high_examples or len(high_examples) == 0
            ) and "high_complexity_examples" in decision_metrics:
                high_examples = decision_metrics.get("high_complexity_examples", [])
                if high_examples:
                    function_metrics["high_complexity_examples"] = high_examples

        # If still not available, try loading from decision_support tool data (may be cached)
        if (not critical_examples or len(critical_examples) == 0) or (
            not high_examples or len(high_examples) == 0
        ):
            decision_data = self._load_tool_data(
                "decision_support", "functions", log_source=False
            )
            if decision_data and isinstance(decision_data, dict):
                decision_metrics_from_tool = self._get_decision_support_details(
                    decision_data
                )
                if decision_metrics_from_tool:
                    if not decision_metrics:
                        decision_metrics = decision_metrics_from_tool
                    if (
                        (not critical_examples or len(critical_examples) == 0)
                        and "critical_complexity_examples" in decision_metrics_from_tool
                    ):
                        critical_examples = decision_metrics_from_tool.get(
                            "critical_complexity_examples", []
                        )
                        if critical_examples:
                            function_metrics["critical_complexity_examples"] = (
                                critical_examples
                            )
                    if (
                        not high_examples or len(high_examples) == 0
                    ) and "high_complexity_examples" in decision_metrics_from_tool:
                        high_examples = decision_metrics_from_tool.get(
                            "high_complexity_examples", []
                        )
                        if high_examples:
                            function_metrics["high_complexity_examples"] = high_examples

        if self._is_dev_tools_scoped_report():

            def _complexity_example_in_scope(ex: Any) -> bool:
                if not isinstance(ex, dict):
                    return False
                return self._path_is_under_development_tools_dir(str(ex.get("file", "")))

            critical_examples = [
                e for e in (critical_examples or []) if _complexity_example_in_scope(e)
            ]
            high_examples = [
                e for e in (high_examples or []) if _complexity_example_in_scope(e)
            ]

        moderate_complex = to_int(metrics.get("moderate"))
        high_complex = to_int(metrics.get("high"))
        critical_complex = to_int(metrics.get("critical"))

        if moderate_complex is None or high_complex is None or critical_complex is None:
            decision_metrics = self._get_decision_support_details(
                self.results_cache.get("decision_support")
            )
            if decision_metrics:
                if moderate_complex is None:
                    moderate_complex = to_int(
                        decision_metrics.get("moderate_complexity")
                    )
                if high_complex is None:
                    high_complex = to_int(decision_metrics.get("high_complexity"))
                if critical_complex is None:
                    critical_complex = to_int(
                        decision_metrics.get("critical_complexity")
                    )

        if self._is_dev_tools_scoped_report():
            critical_complex = len(critical_examples) if critical_examples else 0
            high_complex = len(high_examples) if high_examples else 0

        priority_items: list[dict[str, Any]] = []
        watch_items: list[dict[str, Any]] = []

        # Fixed tier ordering: tier number * 100 + insertion order within tier
        # This ensures predictable ordering: Tier 1 items (100-199), Tier 2 (200-299), etc.
        tier_insertion_counters = {1: 0, 2: 0, 3: 0, 4: 0}

        def validate_recommendation(
            title: str,
            reason: str,
            data_source: str | None = None,
            count: int | None = None,
            expected_min: int | None = None,
        ) -> bool:
            """
            Validate a recommendation before adding it.

            Args:
                title: Recommendation title
                reason: Recommendation reason text
                data_source: Source of data (e.g., 'analyze_unused_imports')
                count: Actual count/value being recommended
                expected_min: Minimum expected value (warns if count is suspiciously high)

            Returns:
                True if recommendation is valid, False if it should be skipped
            """
            # Check for empty reason
            if not reason or not reason.strip():
                logger.debug(f"Skipping recommendation '{title}': empty reason")
                return False

            # Check for suspicious counts (e.g., recommending 358 imports when only 1 is obvious)
            if count is not None and expected_min is not None:
                if count > expected_min * 10:  # More than 10x expected
                    logger.warning(
                        f"Suspicious recommendation '{title}': count {count} is much higher than expected minimum {expected_min}. "
                        f"Data source: {data_source}"
                    )
                    # Still allow it, but log warning

            # Check if data source is available (basic staleness check)
            if data_source:
                # Try to load data to verify it exists
                try:
                    data = self._load_tool_data(data_source, log_source=False)
                    if not data:
                        logger.debug(
                            f"Skipping recommendation '{title}': data source '{data_source}' not available"
                        )
                        return False
                except Exception:
                    # If we can't check, allow the recommendation
                    pass

            return True

        def add_priority(
            tier: int,
            title: str,
            reason: str,
            bullets: list[str],
            validate: bool = True,
            data_source: str | None = None,
            count: int | None = None,
            expected_min: int | None = None,
        ) -> None:
            nonlocal tier_insertion_counters
            if not reason:
                return
            # Ensure bullets is always a list of strings (guard against int/other types from callers)
            if isinstance(bullets, (list, tuple)):
                bullets = [b if isinstance(b, str) else str(b) for b in bullets]
            else:
                bullets = [] if bullets is None else [str(bullets)]

            # Validate recommendation if requested
            if validate and not validate_recommendation(
                title, reason, data_source, count, expected_min
            ):
                return

            # Normalize tier to valid range (1-4)
            normalized_tier = max(1, min(4, tier))

            guidance_defaults: dict[str, str] = {
                "Stabilize documentation drift": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md (doc-sync), ai_development_docs/AI_DOCUMENTATION_GUIDE.md",
                "Add docstrings to missing functions": "ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Update function registry": "ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Add error handling to missing functions": "ai_development_docs/AI_ERROR_HANDLING_GUIDE.md",
                "Modernize error handling (Phase 1 + Phase 2)": "ai_development_docs/AI_ERROR_HANDLING_GUIDE.md",
                "Raise coverage for domains below target": "ai_development_docs/AI_TESTING_GUIDE.md",
                "Raise development tools coverage": "development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_TESTING_GUIDE.md",
                "Reduce dependency pattern risk": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md (CONSOLIDATED_REPORT), ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Fix development tools import boundary violations": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md (section 8.5)",
                "Remove legacy compatibility code (after full call-site migration)": "ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md",
                "Update tools to use centralized config": "development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md",
                "Add docstrings to handler classes": "ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Add pytest category markers to tests": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md (test markers), ai_development_docs/AI_TESTING_GUIDE.md",
                "Review orphaned pytest worker processes (Windows)": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_TESTING_GUIDE.md",
                "Remove obvious unused imports": "development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md",
                "Investigate possible duplicate functions/methods": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Consider refactoring large or high-complexity modules": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Refactor high-complexity functions": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Investigate and correct test failures/errors": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_TESTING_GUIDE.md",
                "Investigate backup health failures": "ai_development_docs/AI_BACKUP_GUIDE.md",
                "Consolidate documentation files": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Review documentation overlaps": "development_tools/DEVELOPMENT_TOOLS_GUIDE.md, ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md",
                "Triage documentation example-marker hints": "ai_development_docs/AI_DOCUMENTATION_GUIDE.md (section 3.6)",
            }
            details_defaults: dict[str, str] = {
                "Stabilize documentation drift": "development_tools/docs/jsons/analyze_documentation_sync_results.json",
                "Add docstrings to missing functions": "development_tools/functions/jsons/analyze_functions_results.json",
                "Update function registry": "development_docs/FUNCTION_REGISTRY_DETAIL.md",
                "Add error handling to missing functions": "development_tools/error_handling/jsons/analyze_error_handling_results.json",
                "Modernize error handling (Phase 1 + Phase 2)": "development_tools/error_handling/jsons/analyze_error_handling_results.json",
                "Raise coverage for domains below target": "development_docs/TEST_COVERAGE_REPORT.md",
                "Raise development tools coverage": "development_tools/tests/jsons/generate_dev_tools_coverage_results.json",
                "Reduce dependency pattern risk": "development_tools/CONSOLIDATED_REPORT.md",
                "Fix development tools import boundary violations": "development_tools/imports/jsons/analyze_dev_tools_import_boundaries_results.json",
                "Remove legacy compatibility code (after full call-site migration)": "development_docs/LEGACY_REFERENCE_REPORT.md (exact locations)",
                "Update tools to use centralized config": "development_tools/ai_work/jsons/analyze_ai_work_results.json",
                "Add docstrings to handler classes": "development_tools/functions/jsons/analyze_function_patterns_results.json",
                "Add pytest category markers to tests": "development_tools/tests/jsons/analyze_test_markers_results.json",
                "Review orphaned pytest worker processes (Windows)": "development_tools/tests/jsons/verify_process_cleanup_results.json",
                "Remove obvious unused imports": "development_docs/UNUSED_IMPORTS_REPORT.md",
                "Investigate possible duplicate functions/methods": "development_tools/functions/jsons/analyze_duplicate_functions_results.json",
                "Consider refactoring large or high-complexity modules": "development_tools/functions/jsons/analyze_module_refactor_candidates_results.json",
                "Refactor high-complexity functions": "development_tools/functions/jsons/analyze_functions_results.json",
                "Address Ruff findings": "development_tools/CONSOLIDATED_REPORT.md",
                "Address Pyright findings": "development_tools/CONSOLIDATED_REPORT.md",
                "Investigate and correct test failures/errors": "stdout files in development_tools/tests/logs",
                "Investigate backup health failures": "development_tools/reports/jsons/backup_health_report.json",
                "Consolidate documentation files": "development_tools/docs/jsons/analyze_documentation_results.json",
                "Review documentation overlaps": "development_tools/docs/jsons/analyze_documentation_results.json",
                "Triage documentation example-marker hints": "development_tools/docs/jsons/analyze_documentation_sync_results.json (details.example_marker_findings)",
            }

            normalized_bullets: list[str] = []
            for bullet in bullets:
                if not bullet:
                    continue
                normalized = bullet.strip() if isinstance(bullet, str) else str(bullet)
                lower = normalized.lower()
                if lower.startswith("review for guidance:"):
                    suffix = (
                        normalized.split(":", 1)[1].strip() if ":" in normalized else ""
                    )
                    normalized = f"Review for guidance: {suffix}"
                elif lower.startswith("review for details:"):
                    suffix = (
                        normalized.split(":", 1)[1].strip() if ":" in normalized else ""
                    )
                    normalized = f"Review for details: {suffix}"
                normalized_bullets.append(normalized)

            has_guidance = any(
                item.lower().startswith("review for guidance:")
                for item in normalized_bullets
            )
            has_details = any(
                item.lower().startswith("review for details:")
                for item in normalized_bullets
            )
            if not has_guidance:
                guidance = guidance_defaults.get(
                    title, "ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                )
                normalized_bullets.insert(0, f"Review for guidance: {guidance}")
            if not has_details:
                details = details_defaults.get(
                    title, "development_tools/CONSOLIDATED_REPORT.md"
                )
                normalized_bullets.append(f"Review for details: {details}")

            # Get insertion order within this tier
            insertion_order = tier_insertion_counters[normalized_tier]
            tier_insertion_counters[normalized_tier] += 1

            # Calculate order: tier * 100 + insertion order
            # This ensures Tier 1 items come first (100-199), then Tier 2 (200-299), etc.
            order = normalized_tier * 100 + insertion_order

            priority_items.append(
                {
                    "order": order,
                    "title": title,
                    "reason": reason,
                    "bullets": normalized_bullets,
                }
            )

        # Add priorities based on issues found
        # Path drift priority
        if path_drift_count and path_drift_count > 0:
            drift_details: list[str] = []
            if path_drift_files:
                drift_details.append(
                    "Top offenders: "
                    f"{self._format_repo_paths_as_markdown_links(path_drift_files, limit=3)}"
                )
            if paired_doc_issues:
                drift_details.append(
                    f"{paired_doc_issues} paired documentation sets affected alongside drift."
                )
            drift_details.append(
                "Action: Fix broken paths in top offender files, then run `python development_tools/run_development_tools.py doc-sync`"
            )
            drift_details.append(
                "Why this matters: Broken paths in documentation reduce trust and make navigation difficult"
            )
            add_priority(
                tier=1,  # Tier 1: Critical
                title="Stabilize documentation drift",
                reason=f"{path_drift_count} documentation paths are out of sync.",
                bullets=drift_details,
            )

        # Missing docstrings priority
        if missing_docs_count_for_priority and missing_docs_count_for_priority > 0:
            doc_bullets: list[str] = []
            # Try to get examples of undocumented functions (prioritized list)
            function_metrics_details = function_metrics.get("details", {})
            undocumented_examples = (
                function_metrics_details.get("undocumented_examples")
                or function_metrics.get("undocumented_examples")
                or []
            )

            # Also try loading directly from tool data if not in metrics
            if not undocumented_examples or len(undocumented_examples) == 0:
                function_data_for_examples = self._load_tool_data(
                    "analyze_functions", "functions"
                )
                if isinstance(function_data_for_examples, dict):
                    func_details_for_examples = function_data_for_examples.get(
                        "details", {}
                    )
                    undocumented_examples = (
                        func_details_for_examples.get("undocumented_examples")
                        or function_data_for_examples.get("undocumented_examples")
                        or []
                    )

            if (
                undocumented_examples
                and isinstance(undocumented_examples, list)
                and len(undocumented_examples) > 0
            ):
                # Sort by complexity if available (prioritize complex functions), otherwise use order
                sorted_examples = sorted(
                    undocumented_examples,
                    key=lambda x: x.get("complexity", 0) if isinstance(x, dict) else 0,
                    reverse=True,
                )[
                    :5
                ]  # Top 5

                # Format examples with file paths
                example_items = []
                for ex in sorted_examples:
                    if isinstance(ex, dict):
                        func_name = ex.get("name", ex.get("function", "unknown"))
                        file_path = ex.get("file", "")
                        if file_path:
                            file_name = Path(file_path).name
                            example_items.append(f"{func_name} ({file_name})")
                        else:
                            example_items.append(func_name)
                    else:
                        example_items.append(str(ex))
                if example_items:
                    # Add ", ... +N" format if there are more than 5 total
                    total_undocumented = (
                        missing_docs_count_for_priority
                        if missing_docs_count_for_priority
                        else len(undocumented_examples)
                    )
                    if total_undocumented > 5:
                        example_items.append(f"... +{total_undocumented - 5} more")
                    doc_bullets.append(f"Top functions: {', '.join(example_items)}")
            doc_bullets.append("Action: Add docstrings to functions missing them")
            doc_bullets.append(
                "Why this matters: Docstrings help AI collaborators and future developers understand code intent"
            )
            # Calculate total and documented for better context
            # Use analyze_functions data (code docstrings), not registry data
            total_funcs = (
                func_metrics_details_for_missing.get("total_functions")
                or function_metrics_for_missing.get("total_functions")
                if isinstance(function_metrics_for_missing, dict)
                else metrics.get("total_functions")
            )
            if total_funcs and missing_docs_count_for_priority is not None:
                documented_funcs = total_funcs - missing_docs_count_for_priority
                reason_text = f"{missing_docs_count_for_priority} functions are missing docstrings ({total_funcs} total, {documented_funcs} documented)."
            else:
                reason_text = f"{missing_docs_count_for_priority} functions are missing docstrings."
            add_priority(
                tier=1,  # Tier 1: Critical
                title="Add docstrings to missing functions",
                reason=reason_text,
                bullets=doc_bullets,
            )

        # Registry gaps priority (separate from missing docstrings)
        # Get missing_docs_list from doc_metrics (structure: missing_docs.missing_files)
        missing_docs_list = None
        if isinstance(doc_metrics, dict):
            missing_docs_raw_for_list = doc_metrics_details.get("missing", {})
            if isinstance(missing_docs_raw_for_list, dict):
                missing_docs_list = missing_docs_raw_for_list.get("files", {})

        if missing_docs_count and missing_docs_count > 0:
            registry_bullets: list[str] = []

            # Show top missing items if available
            if missing_docs_list and isinstance(missing_docs_list, dict):
                sorted_files = sorted(
                    missing_docs_list.items(),
                    key=lambda x: len(x[1]) if isinstance(x[1], list) else 1,
                    reverse=True,
                )[:5]

                if sorted_files:
                    item_list = []
                    for file_path, funcs in sorted_files:
                        func_count = len(funcs) if isinstance(funcs, list) else 1
                        file_name = Path(file_path).name if file_path else "Unknown"
                        if func_count == 1 and isinstance(funcs, list) and funcs:
                            func_name = funcs[0] if funcs else "Unknown"
                            item_list.append(f"{func_name} ({file_name})")
                        else:
                            item_list.append(f"{file_name} ({func_count} functions)")

                    if len(sorted_files) < len(missing_docs_list):
                        total_files = len(missing_docs_list)
                        item_list.append(f"... +{total_files - len(sorted_files)} more")

                    if item_list:
                        registry_bullets.append(f"Top items: {', '.join(item_list)}")

            registry_bullets.append(
                "Action: Regenerate registry entries via `python development_tools/run_development_tools.py docs`"
            )
            registry_bullets.append(
                "Why this matters: Registry documentation helps track all functions in the codebase and their relationships"
            )

            add_priority(
                tier=2,  # Tier 2: Important but less critical than missing docstrings
                title="Update function registry",
                reason=f"{missing_docs_count} items missing from FUNCTION_REGISTRY_DETAIL.md registry.",
                bullets=registry_bullets,
            )

        # Error handling to missing functions (before Phase 1/2, as it's more critical)
        if missing_error_handlers and missing_error_handlers > 0:
            error_handling_bullets: list[str] = []

            # List modules with function counts
            if worst_error_modules:
                module_list = []
                for module in worst_error_modules[:10]:  # Show up to 10 modules
                    module_name = module.get("module", "Unknown")
                    missing_count = module.get("missing", 0)
                    if missing_count > 0:
                        module_list.append(f"{module_name}: {missing_count} functions")

                if module_list:
                    module_list_str = self._format_list_for_display(
                        module_list, limit=10
                    )
                    error_handling_bullets.append(module_list_str)

            error_handling_bullets.append(
                "Add error handling decorators or try-except blocks to protect these functions."
            )
            # Add specific file paths and line numbers if available
            missing_error_list = get_error_field("missing_error_handling", []) or []
            if missing_error_list and isinstance(missing_error_list, list):
                specific_functions = []
                for func_info in missing_error_list[:3]:
                    if isinstance(func_info, dict):
                        file_path = func_info.get("file", "")
                        func_name = func_info.get("function", "")
                        line_num = func_info.get("line", "")
                        if file_path and func_name:
                            if line_num:
                                specific_functions.append(
                                    f"{file_path}:{line_num} ({func_name})"
                                )
                            else:
                                specific_functions.append(f"{file_path} ({func_name})")
                if specific_functions:
                    error_handling_bullets.append(
                        f"Specific functions: {self._format_list_for_display(specific_functions, limit=3)}"
                    )
            error_handling_bullets.append(
                "Why this matters: Functions without error handling can crash the application on unexpected errors"
            )

            add_priority(
                tier=1,  # Tier 1: Critical
                title="Add error handling to missing functions",
                reason=f"{missing_error_handlers} functions have no error handling.",
                bullets=error_handling_bullets,
            )

        # Error handling modernization (combined Phase 1 + Phase 2)
        phase1_total = to_int(get_error_field("phase1_total", 0))
        phase1_by_priority = get_error_field("phase1_by_priority", {}) or {}
        phase1_high = to_int(phase1_by_priority.get("high", 0))
        phase2_total = to_int(get_error_field("phase2_total", 0))
        _phase2_by_type_raw = get_error_field("phase2_by_type", {}) or {}
        phase2_by_type: dict[str, Any] = (
            dict(_phase2_by_type_raw) if isinstance(_phase2_by_type_raw, dict) else {}
        )

        phase1_candidates_pref = get_error_field("phase1_candidates", []) or []
        if not isinstance(phase1_candidates_pref, list):
            phase1_candidates_pref = []
        phase2_exceptions_pref = get_error_field("phase2_exceptions", []) or []
        if not isinstance(phase2_exceptions_pref, list):
            phase2_exceptions_pref = []

        if self._is_dev_tools_scoped_report():
            phase1_candidates_pref = [
                c
                for c in phase1_candidates_pref
                if isinstance(c, dict)
                and self._path_is_under_development_tools_dir(
                    str(c.get("file_path", ""))
                )
            ]
            phase2_exceptions_pref = [
                e
                for e in phase2_exceptions_pref
                if isinstance(e, dict)
                and self._path_is_under_development_tools_dir(
                    str(e.get("file_path", ""))
                )
            ]
            phase1_total = len(phase1_candidates_pref)
            phase2_total = len(phase2_exceptions_pref)
            phase1_by_priority = {"high": 0, "medium": 0, "low": 0}
            for c in phase1_candidates_pref:
                pr = str(c.get("priority", "")).lower()
                if pr in phase1_by_priority:
                    phase1_by_priority[pr] += 1
            phase1_high = to_int(phase1_by_priority.get("high", 0))
            phase2_by_type = {}
            for e in phase2_exceptions_pref:
                et = str(e.get("exc_type", e.get("type", "Exception")))
                prev = to_int(phase2_by_type.get(et)) or 0
                phase2_by_type[et] = prev + 1

        if (phase1_total and phase1_total > 0) or (phase2_total and phase2_total > 0):
            modernization_bullets: list[str] = []

            if phase1_total and phase1_total > 0:
                modernization_bullets.append(
                    f"Phase 1 (decorator-first): {phase1_total} function(s) should replace basic try-except blocks with `@handle_errors` where possible."
                )

                phase1_candidates = phase1_candidates_pref

                if phase1_candidates:
                    from collections import defaultdict

                    high_by_module = defaultdict(int)
                    medium_by_module = defaultdict(int)

                    for candidate in phase1_candidates:
                        if isinstance(candidate, dict):
                            file_path = candidate.get("file_path", "")
                            priority = candidate.get("priority", "").lower()
                            if file_path:
                                module = file_path.replace("\\", "/")
                                if priority == "high":
                                    high_by_module[module] += 1
                                elif priority == "medium":
                                    medium_by_module[module] += 1

                    if phase1_high and phase1_high > 0:
                        modernization_bullets.append(
                            f"Start with {phase1_high} high-priority decorator migrations (entry points and critical operations)."
                        )
                        if high_by_module:
                            top_modules = sorted(
                                high_by_module.items(), key=lambda x: x[1], reverse=True
                            )[:3]
                            module_list = [
                                f"{Path(m).name} ({count})" for m, count in top_modules
                            ]
                            if module_list:
                                modernization_bullets.append(
                                    f"Phase 1 top modules: {self._format_list_for_display(module_list, limit=3)}"
                                )
                    else:
                        phase1_medium = to_int(phase1_by_priority.get("medium", 0))
                        if phase1_medium and phase1_medium > 0:
                            modernization_bullets.append(
                                f"Process {phase1_medium} medium-priority decorator migrations."
                            )
                            if medium_by_module:
                                top_modules = sorted(
                                    medium_by_module.items(),
                                    key=lambda x: x[1],
                                    reverse=True,
                                )[:3]
                                module_list = [
                                    f"{Path(m).name} ({count})"
                                    for m, count in top_modules
                                ]
                                if module_list:
                                    modernization_bullets.append(
                                        f"Phase 1 top modules: {self._format_list_for_display(module_list, limit=3)}"
                                    )

                phase1_medium = to_int(phase1_by_priority.get("medium", 0))
                if (
                    phase1_medium
                    and phase1_medium > 0
                    and phase1_high
                    and phase1_high > 0
                ):
                    modernization_bullets.append(
                        f"Then process {phase1_medium} medium-priority decorator migrations."
                    )

            if phase2_total and phase2_total > 0:
                modernization_bullets.append(
                    f"Phase 2 (exception typing): {phase2_total} generic exception raise(s) should be categorized into project-specific error classes."
                )
                top_exceptions = sorted(
                    phase2_by_type.items(), key=lambda x: x[1], reverse=True
                )[:3]
                if top_exceptions:
                    exc_details = [
                        f"{count} {exc_type}" for exc_type, count in top_exceptions
                    ]
                    modernization_bullets.append(
                        f"Phase 2 most common: {self._format_list_for_display(exc_details, limit=3)}"
                    )

                phase2_exceptions = phase2_exceptions_pref
                if phase2_exceptions:
                    from collections import defaultdict

                    exceptions_by_module = defaultdict(int)
                    for exc in phase2_exceptions:
                        if isinstance(exc, dict):
                            file_path = exc.get("file_path", "")
                            if file_path:
                                module = file_path.replace("\\", "/")
                                exceptions_by_module[module] += 1

                    if exceptions_by_module:
                        top_modules = sorted(
                            exceptions_by_module.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )[:3]
                        module_list = [
                            f"{Path(m).name} ({count})" for m, count in top_modules
                        ]
                        if module_list:
                            modernization_bullets.append(
                                f"Phase 2 top modules: {self._format_list_for_display(module_list, limit=3)}"
                            )

            modernization_bullets.append(
                "Action order: complete decorator-based handling migration first, then categorize remaining generic exception raises."
            )
            modernization_bullets.append(
                "See `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` for decorator and exception categorization rules."
            )
            modernization_bullets.append(
                "Why this matters: Standardized decorator-driven handling plus specific exceptions improves resilience and debuggability."
            )

            phase1_text = (
                f"{phase1_total}" if phase1_total and phase1_total > 0 else "0"
            )
            phase2_text = (
                f"{phase2_total}" if phase2_total and phase2_total > 0 else "0"
            )
            add_priority(
                tier=2,
                title="Modernize error handling (Phase 1 + Phase 2)",
                reason=(
                    f"{phase1_text} Phase 1 decorator migration candidate(s) and {phase2_text} Phase 2 generic exception raise(s) require action."
                ),
                bullets=modernization_bullets,
            )

        # Coverage priorities: per-domain list from main coverage summary (includes
        # `development_tools` when below target). Omitted in dev-tools-only scope,
        # which uses the dedicated dev-tools coverage priority instead.
        if low_coverage_modules and not self._is_dev_tools_scoped_report():
            coverage_highlights = [
                f"{module.get('module', 'module')} ({percent_text(module.get('coverage'), 1)}, {module.get('missed')} lines missing)"
                for module in low_coverage_modules
            ]
            coverage_bullets = [
                "Review for Guidance: ai_development_docs/AI_TESTING_GUIDE.md",
                f"Top target domains: {self._format_list_for_display(coverage_highlights, limit=3)}",
                "Review for details: development_docs/TEST_COVERAGE_REPORT.md",
                "Action: Add scenario tests for uncovered code paths in target domains",
            ]
            add_priority(
                tier=2,  # Tier 2: High
                title="Raise coverage for domains below target",
                reason=f"{len(low_coverage_modules)} key domains remain below the 80% target.",
                bullets=coverage_bullets,
            )

        # Dev-tools coverage drill-down: only when the report is dev-tools-scoped
        # (`--dev-tools-only`). Full-repo audits include `development_tools` as a normal
        # domain in "Raise coverage for domains below target" (see low_coverage_modules).
        if self._is_dev_tools_scoped_report():
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                low_dev_modules = dev_tools_insights.get("low_modules") or []
                low_dev_modules_below_target = [
                    item
                    for item in low_dev_modules
                    if isinstance(item.get("coverage"), (int, float))
                    and float(item.get("coverage")) < 80
                ]
                if dev_pct < 60 or low_dev_modules_below_target:
                    dev_bullets: list[str] = []
                    dev_bullets.append(
                        "Review for Guidance: development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md and ai_development_docs/AI_TESTING_GUIDE.md"
                    )
                    if low_dev_modules_below_target:
                        highlights = [
                            f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)})"
                            for item in low_dev_modules_below_target
                        ]
                        dev_bullets.append(
                            f"Top target modules: {self._format_list_for_display(highlights, limit=3)}"
                        )
                    dev_bullets.append(
                        "Review for details: development_tools/tests/jsons/generate_dev_tools_coverage_results.json"
                    )
                    if dev_tools_insights.get("html"):
                        dev_bullets.append(
                            f"Review HTML report at {dev_tools_insights['html']}"
                        )
                    dev_bullets.append(
                        "Action: Strengthen tests in `tests/development_tools/` for fragile helpers and low-coverage modules"
                    )
                    if dev_pct < 60:
                        dev_reason = (
                            f"Development tools coverage is {percent_text(dev_pct, 1)} (target 60%+)."
                        )
                    else:
                        dev_reason = (
                            f"{len(low_dev_modules_below_target)} key development-tools module(s) remain below the 80% target."
                        )
                    add_priority(
                        tier=2,  # Tier 2: High
                        title="Raise development tools coverage",
                        reason=dev_reason,
                        bullets=dev_bullets,
                    )

        # Static analysis priority (ruff, pyright, bandit, pip-audit)
        if isinstance(static_analysis, dict):
            ruff_data = static_analysis.get("analyze_ruff", {})
            pyright_data = static_analysis.get("analyze_pyright", {})
            bandit_data = static_analysis.get("analyze_bandit", {})
            pip_audit_data = static_analysis.get("analyze_pip_audit", {})
            ruff_summary = static_analysis.get("analyze_ruff", {}).get("summary", {})
            pyright_summary = static_analysis.get("analyze_pyright", {}).get(
                "summary", {}
            )
            bandit_summary = static_analysis.get("analyze_bandit", {}).get(
                "summary", {}
            )
            pip_audit_summary = static_analysis.get("analyze_pip_audit", {}).get(
                "summary", {}
            )
            pyright_details = static_analysis.get("analyze_pyright", {}).get(
                "details", {}
            )
            bandit_details = static_analysis.get("analyze_bandit", {}).get(
                "details", {}
            )
            pip_audit_details = static_analysis.get("analyze_pip_audit", {}).get(
                "details", {}
            )
            ruff_details = (
                ruff_data.get("details", {}) if isinstance(ruff_data, dict) else {}
            )
            ruff_available = bool(ruff_data.get("available", False))
            pyright_available = bool(pyright_data.get("available", False))
            bandit_available = bool(bandit_data.get("available", False))
            pip_audit_available = bool(pip_audit_data.get("available", False))
            ruff_issues = to_int(ruff_summary.get("total_issues")) or 0
            pyright_issues = to_int(pyright_summary.get("total_issues")) or 0
            bandit_issues = to_int(bandit_summary.get("total_issues")) or 0
            pip_audit_issues = to_int(pip_audit_summary.get("total_issues")) or 0
            pyright_errors = to_int(pyright_details.get("errors")) or 0
            pyright_warnings = to_int(pyright_details.get("warnings")) or 0
            static_tools_ok = (
                ruff_available
                and pyright_available
                and bandit_available
                and pip_audit_available
            )
            if not static_tools_ok:
                unavailable_bullets: list[str] = []
                ruff_msg = str(ruff_details.get("message", "")).strip()
                pyright_msg = str(pyright_details.get("message", "")).strip()
                bandit_msg = str(bandit_details.get("message", "")).strip()
                pip_audit_msg = str(pip_audit_details.get("message", "")).strip()
                if not ruff_available:
                    unavailable_bullets.append(
                        f"Ruff unavailable: {ruff_msg if ruff_msg else 'no details provided'}"
                    )
                if not pyright_available:
                    unavailable_bullets.append(
                        f"Pyright unavailable: {pyright_msg if pyright_msg else 'no details provided'}"
                    )
                if not bandit_available:
                    unavailable_bullets.append(
                        f"Bandit unavailable: {bandit_msg if bandit_msg else 'no details provided'}"
                    )
                if not pip_audit_available:
                    unavailable_bullets.append(
                        f"pip-audit unavailable: {pip_audit_msg if pip_audit_msg else 'no details provided'}"
                    )
                unavailable_bullets.append(
                    "Action: install missing tooling in the audit interpreter (for example `.venv`; "
                    "`pip install bandit pip-audit`) and rerun `python development_tools/run_development_tools.py audit --full`."
                )
                unavailable_bullets.append(
                    "Why this matters: without the full static-analysis stack, security and type/lint signals in reports are incomplete."
                )
                add_priority(
                    tier=2,
                    title="Enable static analysis tooling for audits",
                    reason="One or more static-analysis tools are unavailable in the current audit environment.",
                    bullets=unavailable_bullets,
                )
            else:
                # Ruff: separate priority only when there are findings
                if ruff_issues > 0:
                    ruff_bullets: list[str] = [
                        f"Ruff findings: {ruff_issues} issue(s) across {to_int(ruff_summary.get('files_affected')) or 0} file(s).",
                        "Action: Run `python -m ruff check .` to inspect full diagnostics before fixes.",
                        "Why this matters: Lint regressions reduce reliability and increase defect risk.",
                        "Review for details: development_tools/CONSOLIDATED_REPORT.md",
                    ]
                    ruff_bullets.insert(
                        0, "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                    )
                    add_priority(
                        tier=3,
                        title="Address Ruff findings",
                        reason=(
                            f"Ruff reports {ruff_issues} issue(s) across "
                            f"{to_int(ruff_summary.get('files_affected')) or 0} file(s)."
                        ),
                        bullets=ruff_bullets,
                    )
                # Pyright: separate priority only when there are findings
                if pyright_issues > 0:
                    pyright_bullets: list[str] = [
                        f"Pyright findings: {pyright_errors} error(s), {pyright_warnings} warning(s).",
                        "Action: Run `python -m pyright` to inspect full diagnostics before fixes.",
                        "Why this matters: Type regressions reduce reliability and increase defect risk.",
                        "Review for details: development_tools/CONSOLIDATED_REPORT.md",
                    ]
                    pyright_bullets.insert(
                        0, "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                    )
                    add_priority(
                        tier=3,
                        title="Address Pyright findings",
                        reason=(
                            f"Pyright reports {pyright_errors} error(s), {pyright_warnings} warning(s)."
                        ),
                        bullets=pyright_bullets,
                    )
                if bandit_issues > 0:
                    bandit_bullets: list[str] = [
                        f"Bandit MEDIUM/HIGH findings: {bandit_issues} issue(s) across "
                        f"{to_int(bandit_summary.get('files_affected')) or 0} file(s).",
                        "Action: Run `python -m bandit -r . -f screen` (or `python development_tools/static_checks/analyze_bandit.py`) to review.",
                        "Why this matters: Security regressions in application code increase exploit risk.",
                        "Review for details: development_tools/CONSOLIDATED_REPORT.md",
                    ]
                    bandit_bullets.insert(
                        0, "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                    )
                    add_priority(
                        tier=3,
                        title="Address Bandit security findings",
                        reason=(
                            f"Bandit reports {bandit_issues} MEDIUM/HIGH issue(s) across "
                            f"{to_int(bandit_summary.get('files_affected')) or 0} file(s)."
                        ),
                        bullets=bandit_bullets,
                    )
                if pip_audit_issues > 0:
                    pip_bullets: list[str] = [
                        f"pip-audit reports {pip_audit_issues} vulnerability finding(s) across "
                        f"{to_int(pip_audit_summary.get('files_affected')) or 0} package(s).",
                        "Action: Run `python -m pip_audit --format json` and upgrade pinned dependencies per advisory fix versions.",
                        "Why this matters: Known CVEs in dependencies are a supply-chain risk.",
                        "Review for details: development_tools/CONSOLIDATED_REPORT.md",
                    ]
                    pip_bullets.insert(
                        0, "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                    )
                    add_priority(
                        tier=2,
                        title="Review pip-audit dependency vulnerabilities",
                        reason=(
                            f"pip-audit reports {pip_audit_issues} vulnerability finding(s) across "
                            f"{to_int(pip_audit_summary.get('files_affected')) or 0} package(s)."
                        ),
                        bullets=pip_bullets,
                    )

        # Watch coverage when thresholds are currently met (monitor for regressions).
        if isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall", {})
            overall_pct = None
            if isinstance(overall, dict):
                overall_pct = to_float(overall.get("coverage"))
            if overall_pct is not None and overall_pct >= 80 and not low_coverage_modules:
                watch_items.append(
                    {
                        "title": "Domain coverage stability",
                        "reason": f"Coverage is currently above target ({percent_text(overall_pct, 1)} >= 80%).",
                        "bullets": [
                            "Monitor for downward drift after refactors and feature work.",
                            "Re-run full coverage audits to track trend changes.",
                        ],
                    }
                )

        if self._is_dev_tools_scoped_report():
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct_watch = float(dev_tools_insights["overall_pct"])
                if dev_pct_watch >= 60:
                    watch_items.append(
                        {
                            "title": "Development tools coverage stability",
                            "reason": f"Coverage is currently at/above target ({percent_text(dev_pct_watch, 1)} >= 60%).",
                            "bullets": [
                                "Monitor low modules for regression risk even while overall target is met.",
                                "Use `generate_dev_tools_coverage_results.json` trend checks after major tool edits.",
                            ],
                        }
                    )

        # Dependency patterns priority
        if isinstance(dependency_payload, dict):
            circular_dependencies = dependency_payload.get("circular_dependencies", [])
            high_coupling = dependency_payload.get("high_coupling", [])
            if self._is_dev_tools_scoped_report():
                if isinstance(circular_dependencies, list):
                    circular_dependencies = (
                        self._filter_circular_dependencies_dev_tools(
                            circular_dependencies
                        )
                    )
                if isinstance(high_coupling, list):
                    high_coupling = self._filter_high_coupling_dev_tools(high_coupling)
            circular_count = (
                len(circular_dependencies)
                if isinstance(circular_dependencies, list)
                else 0
            )
            high_coupling_count = (
                len(high_coupling) if isinstance(high_coupling, list) else 0
            )
            if circular_count > 0 or high_coupling_count > 0:
                dep_bullets: list[str] = []
                dep_bullets.append(
                    "Review for Guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                )

                if isinstance(circular_dependencies, list) and circular_dependencies:
                    circular_examples: list[str] = []
                    for chain in circular_dependencies[:3]:
                        if (
                            isinstance(chain, list)
                            and len(chain) >= 2
                            and isinstance(chain[0], str)
                            and isinstance(chain[1], str)
                        ):
                            left = Path(chain[0]).name
                            right = Path(chain[1]).name
                            circular_examples.append(f"{left} <-> {right}")
                    if circular_examples:
                        dep_bullets.append(
                            f"Top circular chains: {self._format_list_for_display(circular_examples, limit=3)}"
                        )

                if isinstance(high_coupling, list) and high_coupling:
                    sorted_coupling = sorted(
                        [item for item in high_coupling if isinstance(item, dict)],
                        key=lambda item: to_int(item.get("import_count")) or 0,
                        reverse=True,
                    )[:3]
                    coupling_examples = []
                    for item in sorted_coupling:
                        file_name = Path(str(item.get("file", "unknown"))).name
                        import_count = to_int(item.get("import_count")) or 0
                        coupling_examples.append(f"{file_name} ({import_count})")
                    if coupling_examples:
                        dep_bullets.append(
                            f"Top high-coupling modules: {self._format_list_for_display(coupling_examples, limit=3)}"
                        )
                dep_bullets.append(
                    "Review for details: development_tools/CONSOLIDATED_REPORT.md"
                )

                dep_bullets.append(
                    "Action: Break circular dependencies and reduce module fan-in/fan-out in top offenders."
                )
                add_priority(
                    tier=3,
                    title="Reduce dependency pattern risk",
                    reason=(
                        f"{circular_count} circular chain(s) and {high_coupling_count} high-coupling module(s) were detected."
                    ),
                    bullets=dep_bullets,
                )

        # Import boundary priority (development_tools portability)
        import_boundary_summary = (
            import_boundary_data.get("summary", {})
            if isinstance(import_boundary_data, dict)
            else {}
        )
        import_violations = to_int(import_boundary_summary.get("total_issues"))
        if import_violations is not None and import_violations > 0:
            import_bullets: list[str] = [
                "Review for policy: development_tools/DEVELOPMENT_TOOLS_GUIDE.md §8.5 Import boundary",
                "Action: Refactor to use only approved imports (core.logger). Replace core.time_utilities with development_tools/shared/time_helpers; core.error_handling with try/except or dev-tools wrapper; core.backup_manager with optional/lazy import.",
                "Verify: Run `python development_tools/imports/analyze_dev_tools_import_boundaries.py` after fixes.",
            ]
            add_priority(
                tier=2,
                title="Fix development tools import boundary violations",
                reason=f"{import_violations} non-approved core import(s) in development_tools/** (portability risk).",
                bullets=import_bullets,
            )

        # Legacy references priority
        if legacy_files and legacy_files > 0:
            legacy_bullets: list[str] = []
            legacy_bullets.append(
                "Review for Guidance: ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md"
            )
            if legacy_markers:
                legacy_bullets.append(
                    f"{legacy_markers} legacy markers still surface during scans."
                )
            if legacy_report:
                legacy_bullets.append(
                    f"Review for details: {legacy_report} (exact locations)"
                )
            legacy_bullets.append(
                "Action: Remove active legacy compatibility behavior by migrating all callers/dependencies to current implementations. Only after migration is verified, remove legacy markers/comments/docs evidence."
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Remove legacy compatibility code (after full call-site migration)",
                reason=f"{legacy_files} files still include legacy compatibility paths requiring migration.",
                bullets=legacy_bullets,
            )

        # Config validation priority
        config_validation_summary = self._load_config_validation_summary()
        if config_validation_summary:
            total_recommendations = config_validation_summary.get(
                "total_recommendations", 0
            )
            recommendations = config_validation_summary.get("recommendations", [])
            if total_recommendations > 0 and recommendations:
                config_bullets: list[str] = []
                # Deduplicate recommendations using a more robust approach
                # Extract (tool_name, issue_type) tuples for deduplication
                seen_tool_issues = set()
                unique_recs = []

                for rec in recommendations:
                    rec_text = (
                        rec if isinstance(rec, str) else rec.get("message", str(rec))
                    )

                    # Extract tool name and issue type for deduplication
                    # Format is typically: "Update {tool_name} to import config module"
                    # or "Replace hardcoded values in {tool_name} with config functions"
                    # or "Fix issues in {tool_name}: {issues}"
                    tool_name = None
                    issue_type = None

                    # Try to extract tool name (usually after "Update", "Replace", "Fix")
                    patterns = [
                        (r"Update\s+([^:]+?)\s+to\s+import\s+config", "import_config"),
                        (
                            r"Replace\s+hardcoded\s+values\s+in\s+([^:]+?)\s+with\s+config",
                            "hardcoded_values",
                        ),
                        (r"Fix\s+issues\s+in\s+([^:]+?):", "issues"),
                    ]

                    for pattern, issue in patterns:
                        match = re.search(pattern, rec_text, re.IGNORECASE)
                        if match:
                            tool_name = match.group(1).strip()
                            issue_type = issue
                            break

                    # If we couldn't extract tool/issue, use the full text for deduplication
                    if tool_name and issue_type:
                        dedup_key = (tool_name.lower(), issue_type)
                    else:
                        # Fallback: use normalized text
                        normalized = rec_text.lower().strip()
                        dedup_key = ("_general", normalized)

                    # Only add if we haven't seen this (tool, issue) combination
                    if dedup_key not in seen_tool_issues:
                        seen_tool_issues.add(dedup_key)
                        unique_recs.append(rec_text)

                    # Limit to top 3 unique recommendations
                    if len(unique_recs) >= 3:
                        break

                # Add unique recommendations to bullets
                for rec_text in unique_recs:
                    config_bullets.append(rec_text)

                # Show count of remaining recommendations if any
                if len(recommendations) > len(unique_recs):
                    config_bullets.append(
                        f"...and {len(recommendations) - len(unique_recs)} more recommendation(s)"
                    )

                # Only add priority if we have unique recommendations
                if unique_recs:
                    config_bullets.append(
                        "Action: Update tools to import and use centralized config module instead of hardcoded values"
                    )
                    config_bullets.append(
                        "Why this matters: Centralized configuration improves maintainability and consistency across tools"
                    )
                    add_priority(
                        tier=4,  # Tier 4: Low
                        title="Update tools to use centralized config",
                        reason=f"{len(unique_recs)} unique config validation recommendation(s) pending review.",
                        bullets=config_bullets,
                    )

        # Handler classes without docs priority
        function_patterns_data = self._load_tool_data(
            "analyze_function_patterns", "functions"
        )
        if function_patterns_data and isinstance(function_patterns_data, dict):
            if "details" in function_patterns_data:
                handlers = function_patterns_data["details"].get("handlers", [])
            else:
                handlers = function_patterns_data.get("handlers", [])

            if handlers:
                handlers_no_doc = [h for h in handlers if not h.get("has_doc", True)]
                if self._is_dev_tools_scoped_report():
                    handlers_no_doc = [
                        h
                        for h in handlers_no_doc
                        if self._path_is_under_development_tools_dir(
                            str(h.get("file", ""))
                        )
                    ]
                if handlers_no_doc:
                    if len(handlers_no_doc) <= 5:
                        if not hasattr(self, "_quick_wins_handlers"):
                            handler_examples = []
                            for h in handlers_no_doc[:3]:
                                class_name = h.get("class", "Unknown")
                                file_path = h.get("file", "")
                                if file_path:
                                    handler_examples.append(
                                        f"{class_name} ({file_path})"
                                    )
                                else:
                                    handler_examples.append(class_name)
                            self._quick_wins_handlers = {
                                "count": len(handlers_no_doc),
                                "examples": handler_examples,
                            }
                    else:
                        # Add as priority item
                        handlers_bullets: list[str] = []
                        top_handlers = sorted(
                            handlers_no_doc,
                            key=lambda x: x.get("methods", 0),
                            reverse=True,
                        )[:5]
                        handler_list = [
                            f"{h.get('class', 'Unknown')} ({Path(h.get('file', '')).name}, {h.get('methods', 0)} methods)"
                            for h in top_handlers
                        ]
                        if len(handlers_no_doc) > 5:
                            handler_list.append(f"... +{len(handlers_no_doc) - 5} more")
                        handlers_bullets.append(
                            f"Top handlers: {', '.join(handler_list)}"
                        )
                        handlers_bullets.append(
                            'Action: Add class-level docstrings to handler classes (e.g., class AccountManagementHandler: """Handler for...""")'
                        )
                        handlers_bullets.append(
                            "Why this matters: Class docstrings improve code documentation and help developers understand handler purpose"
                        )
                        add_priority(
                            tier=1,  # Tier 1: Critical (documentation)
                            title="Add docstrings to handler classes",
                            reason=f"{len(handlers_no_doc)} handler classes missing class docstrings.",
                            bullets=handlers_bullets,
                        )

        # Test markers priority
        if test_markers_data and isinstance(test_markers_data, dict):
            summary = test_markers_data.get("summary", {})
            details = test_markers_data.get("details", {})
            missing_count = summary.get("total_issues", 0)
            missing_list = details.get("missing", [])

            # Use missing_count if available, otherwise count from missing_list
            actual_count = (
                missing_count
                if missing_count > 0
                else (len(missing_list) if missing_list else 0)
            )

            if actual_count > 0:
                test_markers_bullets: list[str] = []

                # Get top files with missing markers if available
                if missing_list and isinstance(missing_list, list):
                    from collections import defaultdict

                    files_with_missing = defaultdict(list)
                    for item in missing_list:
                        if isinstance(item, dict):
                            file_path = item.get("file", "")
                            test_name = item.get("name", "")
                            if file_path:
                                files_with_missing[file_path].append(test_name)

                    if files_with_missing:
                        sorted_files = sorted(
                            files_with_missing.items(),
                            key=lambda x: len(x[1]),
                            reverse=True,
                        )[:5]
                        file_list = []
                        for file_path, tests in sorted_files:
                            test_count = len(tests)
                            file_name = Path(file_path).name if file_path else "Unknown"
                            file_list.append(f"{file_name} ({test_count} tests)")
                        if len(sorted_files) < len(files_with_missing):
                            file_list.append(
                                f"... +{len(files_with_missing) - len(sorted_files)} more files"
                            )
                        test_markers_bullets.append(
                            f"Top files: {self._format_list_for_display(file_list, limit=5)}"
                        )

                test_markers_bullets.append(
                    "Action: Add pytest category markers to tests missing them"
                )
                test_markers_bullets.append(
                    "Why this matters: Category markers help organize tests and enable selective test execution"
                )
                test_markers_bullets.append(
                    "Command: `python development_tools/tests/fix_test_markers.py`"
                )

                add_priority(
                    tier=3,  # Tier 3: Medium priority (test organization)
                    title="Add pytest category markers to tests",
                    reason=f"{actual_count} tests are missing pytest category markers.",
                    bullets=test_markers_bullets,
                )

        # verify_process_cleanup — Windows only; surface in priorities when WARN/issues
        if verify_process_cleanup_priority_data and isinstance(
            verify_process_cleanup_priority_data, dict
        ):
            vpc_pd = verify_process_cleanup_priority_data.get("details", {}) or {}
            vpc_ps = verify_process_cleanup_priority_data.get("summary", {}) or {}
            if str(vpc_pd.get("platform", "") or "") == "win32":
                vpc_n = self._coerce_int(vpc_ps.get("total_issues"), 0) or 0
                vpc_st = str(vpc_ps.get("status", "") or "").upper()
                if vpc_n > 0 or vpc_st == "WARN":
                    vpc_bullets = [
                        "Action: Inspect candidate PIDs in the results JSON; end only processes you have verified are stale pytest-xdist workers.",
                        "Limitation: orphan detection is heuristic until full command lines are available from the OS (see AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md §3.18).",
                    ]
                    add_priority(
                        tier=3,
                        title="Review orphaned pytest worker processes (Windows)",
                        reason=(
                            f"{vpc_n} candidate orphan pytest worker process(es) "
                            "(heuristic; see JSON for PID list)."
                        ),
                        bullets=vpc_bullets,
                        validate=False,
                    )

        # Unused imports priority
        # Only recommend removing "Obvious Unused" imports (not test mocking, Qt testing, etc.)
        if unused_imports_data and isinstance(unused_imports_data, dict):
            summary = unused_imports_data.get("summary", {})
            details = unused_imports_data.get("details", {})
            by_category = details.get("by_category", {})
            if self._is_dev_tools_scoped_report():
                obvious_unused, type_only, files_dict_scoped = (
                    self._scoped_obvious_unused_import_metrics(unused_imports_data)
                )
                files_dict: dict[Any, Any] = files_dict_scoped
            else:
                obvious_unused = (
                    by_category.get("obvious_unused", 0)
                    if isinstance(by_category, dict)
                    else 0
                )
                type_only = (
                    by_category.get("type_hints_only", 0)
                    if isinstance(by_category, dict)
                    else 0
                )
                files_dict = unused_imports_data.get("files", {})

            # Only create recommendation if there are obvious unused imports
            if obvious_unused and obvious_unused > 0:
                unused_bullets: list[str] = []

                # Get top files if available (showing all files, but recommendation is only for obvious)
                if files_dict and isinstance(files_dict, dict):
                    sorted_files = sorted(
                        files_dict.items(),
                        key=lambda x: len(x[1]) if isinstance(x[1], list) else int(x[1]),
                        reverse=True,
                    )[:5]
                    if sorted_files:
                        file_list = []
                        for file_path, imports in sorted_files:
                            import_count = (
                                len(imports) if isinstance(imports, list) else int(imports)
                            )
                            file_name = Path(file_path).name if file_path else "Unknown"
                            file_list.append(f"{file_name} ({import_count} imports)")
                        if len(sorted_files) < len(files_dict):
                            file_list.append(
                                f"... +{len(files_dict) - len(sorted_files)} more files"
                            )
                        unused_bullets.append(
                            f"Top files: {self._format_list_for_display(file_list, limit=5)}"
                        )

                unused_bullets.append(
                    f"{obvious_unused} obvious removals (safe to delete)"
                )
                if type_only and type_only > 0:
                    unused_bullets.append(
                        f"Note: {type_only} type-only imports exist but are not recommended for removal (consider TYPE_CHECKING guard if needed)"
                    )

                unused_bullets.append(
                    "Action: Review and remove obvious unused imports (safe to delete)"
                )
                unused_bullets.append(
                    "Why this matters: Unused imports add noise, slow imports, and can hide real dependencies"
                )

                # Check if there's a detailed report
                unused_imports_report_path = (
                    self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
                )
                if unused_imports_report_path.exists():
                    href = self._markdown_href_from_dev_tools_report(
                        unused_imports_report_path
                    )
                    unused_bullets.append(
                        f"Detailed Report: [UNUSED_IMPORTS_REPORT.md]({href})"
                    )

                # Determine tier based on obvious unused count (not total)
                tier = (
                    1 if obvious_unused > 50 else 2
                )  # Critical if >50 obvious, High otherwise

                add_priority(
                    tier=tier,
                    title="Remove obvious unused imports",
                    reason=f"{obvious_unused} obvious unused import(s) can be safely removed.",
                    bullets=unused_bullets,
                    validate=True,
                    data_source="analyze_unused_imports",
                    count=obvious_unused,
                    expected_min=None,  # No minimum expectation - any number of obvious unused imports is valid
                )

        # Duplicate functions priority
        if duplicate_functions_data and isinstance(duplicate_functions_data, dict):
            summary = duplicate_functions_data.get("summary", {})
            details = duplicate_functions_data.get("details", {})
            groups = (
                details.get("duplicate_groups", []) if isinstance(details, dict) else []
            )
            if self._is_dev_tools_scoped_report() and isinstance(groups, list):
                groups = self._filter_duplicate_groups_dev_tools(groups)
            dup_groups = len(groups) if isinstance(groups, list) and groups else 0
            dup_files = (
                self._count_duplicate_affected_files_dev_tools(groups)
                if self._is_dev_tools_scoped_report()
                and isinstance(groups, list)
                and groups
                else self._count_duplicate_affected_files(groups)
                if isinstance(groups, list) and groups
                else 0
            )
            if dup_groups > 0 and isinstance(groups, list) and groups:

                def group_sort_key(item):
                    funcs = item.get("functions", []) if isinstance(item, dict) else []
                    func_count = len(funcs) if isinstance(funcs, list) else 0
                    similarity_range = (
                        item.get("similarity_range", {})
                        if isinstance(item, dict)
                        else {}
                    )
                    max_score = similarity_range.get("max", 0)
                    return (max_score, func_count)

                sorted_groups = sorted(groups, key=group_sort_key, reverse=True)[:3]
                duplicate_bullets: list[str] = []
                duplicate_bullets.append(
                    "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md"
                )
                duplicate_bullets.append("Top target groups:")
                for idx, group in enumerate(sorted_groups, start=1):
                    funcs = (
                        group.get("functions", []) if isinstance(group, dict) else []
                    )
                    func_count = len(funcs) if isinstance(funcs, list) else 0
                    similarity_range = (
                        group.get("similarity_range", {})
                        if isinstance(group, dict)
                        else {}
                    )
                    max_score = similarity_range.get("max", 0)
                    func_items = []
                    if isinstance(funcs, list):
                        for func in funcs[:3]:
                            if isinstance(func, dict):
                                func_name = func.get("full_name") or func.get(
                                    "name", "unknown"
                                )
                                file_path = func.get("file", "")
                                file_name = (
                                    Path(file_path).name if file_path else "Unknown"
                                )
                                func_items.append(f"{func_name} ({file_name})")
                            else:
                                func_items.append(str(func))
                    if func_count > 3:
                        func_items.append(f"... +{func_count - 3} more")
                    duplicate_bullets.append(
                        f"Group {idx} ({func_count} funcs, max score {max_score}): {', '.join(func_items)}"
                    )
                duplicate_bullets.append(
                    "Review for details: development_tools/functions/jsons/analyze_duplicate_functions_results.json"
                )
                dup_capped_priority = isinstance(details, dict) and details.get(
                    "groups_capped", False
                )
                groups_reason = (
                    f"at least {dup_groups}" if dup_capped_priority else str(dup_groups)
                )
                add_priority(
                    tier=2,
                    title="Investigate possible duplicate functions/methods",
                    reason=f"{groups_reason} potential duplicate groups across {dup_files} files.",
                    bullets=duplicate_bullets,
                    validate=True,
                    data_source="analyze_duplicate_functions",
                    count=dup_groups,
                    expected_min=None,
                )

        # Module refactor candidates (large/high-complexity modules)
        if module_refactor_candidates_data and isinstance(
            module_refactor_candidates_data, dict
        ):
            refactor_details = module_refactor_candidates_data.get("details", {})
            candidates_list = (
                refactor_details.get("refactor_candidates", [])
                if isinstance(refactor_details, dict)
                else []
            )
            if self._is_dev_tools_scoped_report() and isinstance(candidates_list, list):
                candidates_list = [
                    c
                    for c in candidates_list
                    if isinstance(c, dict)
                    and self._path_is_under_development_tools_dir(
                        str(c.get("file", ""))
                    )
                ]
            refactor_count = (
                len(candidates_list) if isinstance(candidates_list, list) else 0
            )
            if (
                refactor_count > 0
                and isinstance(candidates_list, list)
                and candidates_list
            ):
                refactor_bullets = []
                refactor_bullets.append(
                    "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md, ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md"
                )
                refactor_bullets.append("Top candidate modules (consider splitting):")
                for idx, cand in enumerate(candidates_list[:3], start=1):
                    if isinstance(cand, dict):
                        file_key = cand.get("file", "?")
                        line_count = cand.get("lines", 0)
                        funcs = cand.get("function_count", 0)
                        total_comp = cand.get(
                            "total_function_complexity", cand.get("total_complexity", 0)
                        )
                        refactor_bullets.append(
                            f"  {idx}. {file_key} (lines={line_count}, functions={funcs}, total_function_complexity={total_comp})"
                        )
                refactor_bullets.append(
                    "Review for details: development_tools/functions/jsons/analyze_module_refactor_candidates_results.json"
                )
                add_priority(
                    tier=2,
                    title="Consider refactoring large or high-complexity modules",
                    reason=f"{refactor_count} module(s) exceed size/complexity thresholds (candidates for splitting).",
                    bullets=refactor_bullets,
                    validate=True,
                    data_source="analyze_module_refactor_candidates",
                    count=refactor_count,
                    expected_min=None,
                )

        # Complexity refactoring priority
        if critical_complex and critical_complex > 0:
            complexity_bullets: list[str] = []
            # Ensure we have examples - try loading if not available
            if not critical_examples:
                # Try loading from analyze_functions first (global top complexity source).
                func_result = self._load_tool_data(
                    "analyze_functions", "functions", log_source=False
                )
                if func_result and isinstance(func_result, dict):
                    func_details = func_result.get("details", {})
                    if "critical_complexity_examples" in func_details:
                        critical_examples = func_details.get(
                            "critical_complexity_examples", []
                        )
                    elif "critical_complexity_examples" in func_result:
                        critical_examples = func_result.get(
                            "critical_complexity_examples", []
                        )
                    if (
                        (not high_examples or len(high_examples) == 0)
                        and "high_complexity_examples" in func_details
                    ):
                        high_examples = func_details.get("high_complexity_examples", [])
                    elif (
                        (not high_examples or len(high_examples) == 0)
                        and "high_complexity_examples" in func_result
                    ):
                        high_examples = func_result.get("high_complexity_examples", [])

                # If still not available, fall back to decision_support.
                if not critical_examples:
                    decision_metrics = self._get_decision_support_details(
                        self.results_cache.get("decision_support")
                    )
                    if (
                        decision_metrics
                        and "critical_complexity_examples" in decision_metrics
                    ):
                        critical_examples = decision_metrics.get(
                            "critical_complexity_examples", []
                        )
                    if not critical_examples or len(critical_examples) == 0:
                        decision_data = self._load_tool_data(
                            "decision_support", "functions", log_source=False
                        )
                        if decision_data and isinstance(decision_data, dict):
                            decision_metrics_from_tool = (
                                self._get_decision_support_details(decision_data)
                            )
                            if (
                                decision_metrics_from_tool
                                and "critical_complexity_examples"
                                in decision_metrics_from_tool
                            ):
                                critical_examples = decision_metrics_from_tool.get(
                                    "critical_complexity_examples", []
                                )
                            if (
                                (not high_examples or len(high_examples) == 0)
                                and "high_complexity_examples"
                                in decision_metrics_from_tool
                            ):
                                high_examples = decision_metrics_from_tool.get(
                                    "high_complexity_examples", []
                                )

            if critical_examples:
                sorted_examples = sorted(
                    critical_examples[:10],
                    key=lambda x: (
                        x.get("complexity", x.get("nodes", 0))
                        if isinstance(x, dict)
                        else 0
                    ),
                    reverse=True,
                )[:3]
                example_names = []
                for ex in sorted_examples:
                    if isinstance(ex, dict):
                        func_name = ex.get("name", ex.get("function", "unknown"))
                        file_name = ex.get("file", "")
                        if file_name:
                            # Extract just the filename, not full path
                            file_name = Path(file_name).name
                            example_names.append(f"{func_name} ({file_name})")
                        else:
                            example_names.append(func_name)
                    else:
                        example_names.append(str(ex))
                if example_names:
                    complexity_bullets.append(
                        f"Highest complexity: {self._format_list_for_display(example_names, limit=3)}"
                    )
            # Standard order: guidance, top results, details, action
            complexity_bullets.insert(
                0,
                "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md, ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md",
            )
            # Insert details after top results (after index 1 if we have "Highest complexity")
            details_line = "Review for details: development_tools/functions/jsons/analyze_functions_results.json"
            complexity_bullets.insert(1, details_line)
            if len(complexity_bullets) > 2 and not complexity_bullets[2].startswith("Review for details:"):
                # We have "Highest complexity" at index 2; move details to after it
                complexity_bullets.pop(1)
                complexity_bullets.insert(2, details_line)
            if high_complex and high_complex > 0 and critical_complex <= 10:
                complexity_bullets.append(
                    f"Then address {high_complex} high-complexity functions (100-199 nodes)."
                )
            complexity_bullets.append(
                "Action: Break down complex functions into smaller, focused functions with single responsibilities"
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Refactor high-complexity functions",
                reason=f"{critical_complex} critical-complexity functions (>199 nodes) need immediate attention.",
                bullets=complexity_bullets,
            )
        elif high_complex and high_complex > 0:
            high_complexity_bullets: list[str] = []
            if high_examples:
                sorted_examples = sorted(
                    high_examples[:10],
                    key=lambda x: x.get("complexity", 0) if isinstance(x, dict) else 0,
                    reverse=True,
                )[:3]
                example_names = []
                for ex in sorted_examples:
                    if isinstance(ex, dict):
                        func_name = ex.get("name", ex.get("function", "unknown"))
                        file_name = ex.get("file", "")
                        if file_name:
                            example_names.append(f"{func_name} ({file_name})")
                        else:
                            example_names.append(func_name)
                    else:
                        example_names.append(str(ex))
                if example_names:
                    high_complexity_bullets.append(
                        f"Highest complexity: {self._format_list_for_display(example_names, limit=3)}"
                    )
            # Standard order: guidance, top results, details, action
            high_complexity_bullets.insert(
                0,
                "Review for guidance: ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md, ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md",
            )
            details_line_high = "Review for details: development_tools/functions/jsons/analyze_functions_results.json"
            high_complexity_bullets.insert(1, details_line_high)
            if len(high_complexity_bullets) > 2 and not high_complexity_bullets[2].startswith("Review for details:"):
                high_complexity_bullets.pop(1)
                high_complexity_bullets.insert(2, details_line_high)
            high_complexity_bullets.append(
                "Action: Simplify high-complexity functions by extracting helper functions and reducing nesting"
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Refactor high-complexity functions",
                reason=f"{high_complex} high-complexity functions (100-199 nodes) should be simplified.",
                bullets=high_complexity_bullets,
            )

        tier3_outcome = self._get_tier3_test_outcome()
        tier3_state = self._effective_tier3_state_from_outcome(tier3_outcome)
        actionable_tier3_states = {
            "test_failures",
            "coverage_failed",
            "crashed",
            "infra_cleanup_error",
        }
        if tier3_state in actionable_tier3_states:
            tier3_bullets: list[str] = []
            parallel_outcome = (
                tier3_outcome.get("parallel", {})
                if isinstance(tier3_outcome.get("parallel"), dict)
                else {}
            )
            no_parallel_outcome = (
                tier3_outcome.get("no_parallel", {})
                if isinstance(tier3_outcome.get("no_parallel"), dict)
                else {}
            )
            dev_tools_outcome = (
                tier3_outcome.get("development_tools", {})
                if isinstance(tier3_outcome.get("development_tools"), dict)
                else {}
            )
            failed_nodes = tier3_outcome.get("failed_node_ids", [])
            include_parallel_logs = False
            include_no_parallel_logs = False
            include_dev_tools_logs = False
            if tier3_state == "coverage_failed":
                tier3_title = "Investigate and correct test failures/errors"
                tier3_reason = (
                    "Tier 3 coverage orchestration reported a coverage failure outcome."
                )
                cov_parts: list[str] = []
                if not self._tier3_track_skipped_for_audit_scope(parallel_outcome):
                    cov_parts.append(
                        f"Parallel: {self._track_classification_label(parallel_outcome)}"
                    )
                if not self._tier3_track_skipped_for_audit_scope(no_parallel_outcome):
                    cov_parts.append(
                        f"no-parallel: {self._track_classification_label(no_parallel_outcome)}"
                    )
                if not self._tier3_track_skipped_for_audit_scope(dev_tools_outcome):
                    cov_parts.append(
                        f"dev-tools: {self._track_classification_label(dev_tools_outcome)}"
                    )
                if cov_parts:
                    tier3_bullets.append(", ".join(cov_parts) + ".")
            elif tier3_state in {"crashed", "infra_cleanup_error"}:
                tier3_title = "Investigate and correct test failures/errors"
                tier3_reason = f"Tier 3 test pipeline reported `{tier3_state}`."
                for label, track_outcome, track_key in (
                    ("Parallel", parallel_outcome, "parallel"),
                    ("No-parallel", no_parallel_outcome, "no_parallel"),
                    ("Development tools", dev_tools_outcome, "development_tools"),
                ):
                    if self._tier3_track_skipped_for_audit_scope(track_outcome):
                        continue
                    track_state = self._track_classification_label(track_outcome)
                    track_reason = str(
                        track_outcome.get("classification_reason", "unknown")
                    )
                    track_return_hex = track_outcome.get("return_code_hex")
                    track_log_file = track_outcome.get("log_file")
                    if track_state in {"crashed", "infra_cleanup_error"}:
                        summary = f"{label} classification={track_state}, reason={track_reason}"
                        if isinstance(track_return_hex, str) and track_return_hex:
                            summary += f", return={track_return_hex}"
                        if isinstance(track_log_file, str) and track_log_file.strip():
                            summary += f" (log: {track_log_file.strip()})"
                            if track_key == "parallel":
                                include_parallel_logs = True
                            elif track_key == "no_parallel":
                                include_no_parallel_logs = True
                            elif track_key == "development_tools":
                                include_dev_tools_logs = True
                        tier3_bullets.append(summary + ".")
                        track_hint = track_outcome.get("actionable_context")
                        if isinstance(track_hint, str) and track_hint.strip():
                            tier3_bullets.append(f"{label} hint: {track_hint.strip()}")
                if not tier3_bullets:
                    rp = parallel_outcome.get("return_code")
                    rnp = no_parallel_outcome.get("return_code")
                    rdt = dev_tools_outcome.get("return_code")
                    parts_ret: list[str] = []
                    if not self._tier3_track_skipped_for_audit_scope(parallel_outcome):
                        parts_ret.append(f"Parallel return={rp}")
                    if not self._tier3_track_skipped_for_audit_scope(no_parallel_outcome):
                        parts_ret.append(f"no-parallel return={rnp}")
                    if not self._tier3_track_skipped_for_audit_scope(dev_tools_outcome):
                        parts_ret.append(f"dev-tools return={rdt}")
                    if parts_ret:
                        tier3_bullets.append(", ".join(parts_ret) + ".")
            else:
                tier3_title = "Investigate and correct test failures/errors"
                tier3_reason = (
                    "Tier 3 test outcomes include failed and/or errored tracks."
                )
                track_specs = [
                    ("Parallel", parallel_outcome, "parallel"),
                    ("No-parallel", no_parallel_outcome, "no_parallel"),
                    ("Development tools", dev_tools_outcome, "development_tools"),
                ]
                for label, track_outcome, track_key in track_specs:
                    if self._tier3_track_skipped_for_audit_scope(track_outcome):
                        continue
                    track_failed_nodes = self._get_track_failed_nodes(track_outcome)
                    failed = (
                        len(track_failed_nodes)
                        if track_failed_nodes
                        else self._coerce_int(track_outcome.get("failed_count", 0))
                    )
                    errors = self._coerce_int(track_outcome.get("error_count", 0))
                    state = self._track_classification_label(track_outcome)
                    if failed > 0 and track_failed_nodes:
                        tier3_bullets.append(
                            f"{label} tests failed={failed}: {self._format_list_for_display(track_failed_nodes, limit=6)}."
                        )
                    elif failed > 0:
                        tier3_bullets.append(f"{label} tests failed={failed}.")
                    elif errors > 0:
                        tier3_bullets.append(f"{label} tests errors={errors}.")
                    elif state == "failed":
                        tier3_bullets.append(f"{label} classification=failed.")
                    else:
                        continue

                    if failed > 0 or errors > 0 or state == "failed":
                        if track_key == "parallel":
                            include_parallel_logs = True
                        elif track_key == "no_parallel":
                            include_no_parallel_logs = True
                        elif track_key == "development_tools":
                            include_dev_tools_logs = True
                if not (
                    include_parallel_logs
                    or include_no_parallel_logs
                    or include_dev_tools_logs
                ):
                    if not self._tier3_track_skipped_for_audit_scope(parallel_outcome):
                        tier3_bullets.append(
                            f"Parallel failed={parallel_outcome.get('failed_count', 0)}, errors={parallel_outcome.get('error_count', 0)}."
                        )
                        include_parallel_logs = True
                    if not self._tier3_track_skipped_for_audit_scope(no_parallel_outcome):
                        tier3_bullets.append(
                            f"No-parallel failed={no_parallel_outcome.get('failed_count', 0)}, errors={no_parallel_outcome.get('error_count', 0)}."
                        )
                        include_no_parallel_logs = True
                    if not self._tier3_track_skipped_for_audit_scope(dev_tools_outcome):
                        tier3_bullets.append(
                            f"Development tools failed={dev_tools_outcome.get('failed_count', 0)}, errors={dev_tools_outcome.get('error_count', 0)}."
                        )
                        include_dev_tools_logs = True
            if (
                isinstance(failed_nodes, list)
                and failed_nodes
                and tier3_state != "test_failures"
            ):
                failed_nodes = [
                    self._normalize_test_node_id(str(node))
                    for node in dict.fromkeys(
                        str(node).strip() for node in failed_nodes if str(node).strip()
                    )
                ]
                failed_nodes = [node for node in failed_nodes if node]
                tier3_bullets.append(
                    f"Failing/erroring test(s): {self._format_list_for_display(failed_nodes, limit=10)}"
                )
            tier3_bullets.insert(
                0, "Review for guidance: ai_development_docs/AI_TESTING_GUIDE.md"
            )
            tier3_log_files = self._get_recent_tier3_log_files(
                include_parallel=include_parallel_logs,
                include_no_parallel=include_no_parallel_logs,
                include_dev_tools=include_dev_tools_logs,
            )
            if tier3_log_files:
                tier3_bullets.append(
                    f"Review for details: {self._format_list_for_display(tier3_log_files, limit=6)}"
                )
            else:
                tier3_bullets.append(
                    "Review for details: stdout files in development_tools/tests/logs"
                )
            add_priority(
                tier=1,
                title=tier3_title,
                reason=tier3_reason,
                bullets=tier3_bullets,
            )

        backup_summary = (
            backup_health_data.get("summary", {})
            if isinstance(backup_health_data, dict)
            else {}
        )
        backup_checks = (
            backup_health_data.get("details", {}).get("checks", [])
            if isinstance(backup_health_data.get("details"), dict)
            else (
                backup_health_data.get("checks", [])
                if isinstance(backup_health_data, dict)
                else []
            )
        )
        backup_success = (
            bool(backup_summary.get("success")) if backup_summary else False
        )
        if backup_summary and not backup_success:
            backup_bullets: list[str] = []
            backup_bullets.append(
                "Review for guidance: ai_development_docs/AI_BACKUP_GUIDE.md"
            )

            failed_checks: list[str] = []
            if isinstance(backup_checks, list):
                for check in backup_checks:
                    if not isinstance(check, dict):
                        continue
                    if bool(check.get("success")):
                        continue
                    check_name = str(check.get("name") or "unknown_check")
                    details = check.get("details")
                    if isinstance(details, dict) and details.get("error"):
                        failed_checks.append(
                            f"{check_name} (error={details.get('error')})"
                        )
                    else:
                        failed_checks.append(check_name)

            if failed_checks:
                backup_bullets.append(
                    f"Failed checks: {self._format_list_for_display(failed_checks, limit=7)}"
                )
            backup_bullets.append(
                "Action: run `python development_tools/run_development_tools.py backup verify` and resolve failing check(s)"
            )
            backup_bullets.append(
                "Action: run `python development_tools/run_development_tools.py backup drill` to confirm restorability"
            )
            backup_bullets.append(
                "Why this matters: Backup health failures mean recovery confidence is degraded."
            )

            add_priority(
                tier=1,
                title="Investigate backup health failures",
                reason=(
                    f"Backup health is {str(backup_summary.get('status', 'FAIL')).upper()} "
                    f"({backup_summary.get('passed_checks', 0)}/{backup_summary.get('total_checks', 0)} checks passed)."
                ),
                bullets=backup_bullets,
            )

        # Example-marker hints (doc hygiene; surfaced from doc-sync + --check-example-markers)
        doc_sync_em: dict[str, Any] = {}
        if hasattr(self, "docs_sync_summary") and isinstance(
            self.docs_sync_summary, dict
        ):
            doc_sync_em = self.docs_sync_summary
        if not doc_sync_em or not doc_sync_em.get("details"):
            loaded_sync = self._load_tool_data(
                "analyze_documentation_sync", "docs", log_source=False
            )
            if isinstance(loaded_sync, dict):
                doc_sync_em = loaded_sync
        em_details = (
            doc_sync_em.get("details", {})
            if isinstance(doc_sync_em.get("details"), dict)
            else {}
        )
        em_hint_total = 0
        try:
            em_hint_total = int(em_details.get("example_marker_hint_count") or 0)
        except (TypeError, ValueError):
            em_hint_total = 0
        if em_hint_total > 0:
            em_findings_raw = em_details.get("example_marker_findings") or {}
            em_file_count = (
                len(em_findings_raw)
                if isinstance(em_findings_raw, dict)
                else 0
            )
            ranked_em_files: list[tuple[str, int]] = []
            if isinstance(em_findings_raw, dict):
                for rel_path, hint_lines in em_findings_raw.items():
                    n = len(hint_lines) if isinstance(hint_lines, list) else 0
                    if n > 0:
                        ranked_em_files.append(
                            (str(rel_path).replace("\\", "/").strip(), n)
                        )
                ranked_em_files.sort(key=lambda t: (-t[1], t[0].lower()))
            em_file_bullets: list[str] = []
            if ranked_em_files:
                em_file_bullets.append(
                    "Top file(s) by hint line count (up to 3):"
                )
                for idx, (rel_path, n_hints) in enumerate(
                    ranked_em_files[:3], start=1
                ):
                    em_file_bullets.append(
                        f"{idx}. `{rel_path}` — {n_hints} hint line(s)"
                    )
                if em_file_count > 3:
                    em_file_bullets.append(
                        f"({em_file_count - 3} other documentation file(s) with hints; full list in JSON.)"
                    )
            elif em_file_count > 0:
                em_file_bullets.append(
                    f"{em_file_count} documentation file(s) report hints (see JSON for paths)."
                )
            # Order matches other priorities: auto guidance first, content, details, action last.
            em_bullets: list[str] = em_file_bullets + [
                "Review for details: development_tools/docs/jsons/analyze_documentation_sync_results.json (details.example_marker_findings)",
                "Action: Add [OK]/[AVOID]/[GOOD]/[BAD]/[EXAMPLE] next to path references in Example sections where they are intentional examples, or move neutral citations out of Example headings.",
            ]

            add_priority(
                tier=4,
                title="Triage documentation example-marker hints",
                reason=(
                    f"{em_hint_total} line-level hint(s) in documentation Example sections."
                ),
                bullets=em_bullets,
                validate=False,
            )

        lines.append("## Immediate Focus Ranked")
        if priority_items:
            for idx, item in enumerate(
                sorted(priority_items, key=lambda entry: entry["order"]), start=1
            ):
                lines.append(f"{idx}. **{item['title']}**  -  {item['reason']}")
                for bullet in item["bullets"]:
                    bullet = _linkify_review_paths_bullet(bullet)
                    # Further indent top-3 list items (numbered or "Group N")
                    is_sub_bullet = bool(
                        re.match(r"^\d+\.\s", bullet.strip())
                        or bullet.strip().startswith("Group ")
                    )
                    prefix = "     - " if is_sub_bullet else "   - "
                    lines.append(f"{prefix}{bullet}")
        else:
            lines.append(
                "All signals are green. Re-run `python development_tools/run_development_tools.py status` to monitor."
            )
        lines.append("")

        # Store TODO sync for Quick Wins instead of Immediate Focus
        todo_sync_result = getattr(self, "todo_sync_result", None)
        if todo_sync_result and isinstance(todo_sync_result, dict):
            completed_entries = todo_sync_result.get("completed_entries", 0)
            if completed_entries > 0:
                if not hasattr(self, "_quick_wins_todo"):
                    entries = todo_sync_result.get("entries", [])
                    line_numbers = [
                        str(entry.get("line_number", ""))
                        for entry in entries
                        if entry.get("line_number")
                    ]
                    self._quick_wins_todo = {
                        "count": completed_entries,
                        "line_numbers": line_numbers,
                    }

        quick_wins: list[str] = []

        # Add dependency documentation refresh to Quick Wins
        dependency_summary = getattr(self, "module_dependency_summary", None) or (
            hasattr(self, "results_cache")
            and self.results_cache.get("analyze_module_dependencies")
        )
        if dependency_summary and dependency_summary.get("missing_dependencies"):
            missing = dependency_summary["missing_dependencies"]
            files = (
                dependency_summary.get("missing_files")
                or dependency_summary.get("missing_sections")
                or []
            )
            scoped_dt = self._is_dev_tools_scoped_report()
            if scoped_dt and isinstance(files, list):
                files = [
                    f
                    for f in files
                    if self._path_is_under_development_tools_dir(str(f))
                ]
            if missing > 0:
                if scoped_dt and isinstance(files, list) and not files:
                    pass
                else:
                    miss_display = (
                        len(files)
                        if scoped_dt and isinstance(files, list)
                        else missing
                    )
                    files_str = (
                        self._format_list_for_display(files, limit=2)
                        if files
                        else "affected files"
                    )
                    quick_wins.append(
                        f"Refresh dependency documentation: {miss_display} module dependencies are undocumented ({files_str}). Regenerate via `python development_tools/run_development_tools.py docs`."
                    )

        # Add handler classes without docs to Quick Wins (if small count)
        if hasattr(self, "_quick_wins_handlers") and self._quick_wins_handlers:
            handler_info = self._quick_wins_handlers
            count = handler_info.get("count", 0)
            examples = handler_info.get("examples", [])
            if count > 0:
                examples_str = (
                    self._format_list_for_display(examples, limit=2) if examples else ""
                )
                quick_wins.append(
                    f"Add documentation to {count} handler class(es) missing docs{(' (' + examples_str + ')') if examples_str else ''}."
                )

        # Add TODO sync to Quick Wins
        if hasattr(self, "_quick_wins_todo") and self._quick_wins_todo:
            if isinstance(self._quick_wins_todo, dict):
                count = self._quick_wins_todo.get("count", 0)
                line_numbers = self._quick_wins_todo.get("line_numbers", [])
                if line_numbers:
                    lines_str = ", ".join(line_numbers[:5])
                    if len(line_numbers) > 5:
                        lines_str += f", ... +{len(line_numbers) - 5}"
                    quick_wins.append(
                        f"Review {count} completed TODO entry/entries (lines {lines_str}) - if documented in changelogs, remove from TODO.md; otherwise move to CHANGELOG_DETAIL.md and AI_CHANGELOG.md first."
                    )
                else:
                    quick_wins.append(
                        f"Review {count} completed TODO entry/entries - if documented in changelogs, remove from TODO.md; otherwise move to CHANGELOG_DETAIL.md and AI_CHANGELOG.md first."
                    )
            else:
                quick_wins.append(
                    f"Review {self._quick_wins_todo} completed TODO entry/entries - if documented in changelogs, remove from TODO.md; otherwise move to CHANGELOG_DETAIL.md and AI_CHANGELOG.md first."
                )

        if (
            not self._is_dev_tools_scoped_report()
            and paired_doc_issues
            and not (path_drift_count and path_drift_count > 0)
        ):
            if doc_sync_summary:
                paired_docs_data = doc_sync_summary.get("paired_docs", {})
                if isinstance(paired_docs_data, dict):
                    content_sync_issues = paired_docs_data.get("content_sync", [])
                    if content_sync_issues:
                        quick_wins.append(
                            f"Resolve {paired_doc_issues} paired doc sync issue(s). Start with: {content_sync_issues[0]}"
                        )
                        if len(content_sync_issues) > 1:
                            quick_wins.append(
                                f"  - Plus {len(content_sync_issues) - 1} more issue(s) to address"
                            )
                    else:
                        quick_wins.append(
                            f"Resolve {paired_doc_issues} unpaired documentation sets flagged by doc-sync."
                        )
                else:
                    quick_wins.append(
                        f"Resolve {paired_doc_issues} unpaired documentation sets flagged by doc-sync."
                    )
            else:
                quick_wins.append(
                    f"Resolve {paired_doc_issues} unpaired documentation sets flagged by doc-sync."
                )

        if analyze_artifacts:
            artifact = analyze_artifacts[0]
            location = artifact.get("file", "unknown")
            line_number = artifact.get("line")
            if line_number:
                location = f"{location}:{line_number}"
            pattern = artifact.get("pattern", "lint issue")
            quick_wins.append(f"Clean `{pattern}` marker in {location}.")
        if analyze_duplicates:
            quick_wins.append(
                f"Merge {len(analyze_duplicates)} duplicate documentation block(s)."
            )
        if analyze_placeholders:
            quick_wins.append(
                f"Replace {len(analyze_placeholders)} placeholder section(s) flagged by docs scan."
            )

        def add_doc_quick_win(
            label: str, tool_data: dict[str, Any], fix_command: str
        ) -> None:
            if not isinstance(tool_data, dict):
                return
            summary = tool_data.get("summary", {})
            total_issues = to_int(summary.get("total_issues")) or 0
            files_affected = to_int(summary.get("files_affected")) or 0
            file_counts = self._extract_file_issue_counts(tool_data)
            if self._is_dev_tools_scoped_report():
                file_counts = {
                    k: v
                    for k, v in file_counts.items()
                    if self._path_is_under_development_tools_dir(k)
                }
                total_issues = sum(int(v) for v in file_counts.values())
                files_affected = len(file_counts)
            if total_issues <= 0:
                return
            top_files = sorted(
                file_counts.items(), key=lambda item: item[1], reverse=True
            )[:3]
            top_files_text = (
                ", ".join(f"{path} ({count})" for path, count in top_files)
                if top_files
                else "No file-level details available"
            )
            quick_wins.append(
                f"{label}: {total_issues} issue(s) across {files_affected} file(s). "
                f"Top offenders: {top_files_text}. "
                f"Fix: `{fix_command}`. "
                f"Verify: `python development_tools/run_development_tools.py doc-sync`."
            )

        add_doc_quick_win(
            "ASCII compliance",
            ascii_data,
            "python development_tools/run_development_tools.py doc-fix --fix-ascii",
        )
        # Fallback: if final audit summary recorded ASCII issues but the ASCII tool payload
        # was not refreshed in this tier, still surface an actionable quick win.
        if (
            not self._is_dev_tools_scoped_report()
            and (to_int(ascii_issues) or 0) > 0
            and not any(
                isinstance(win, str) and win.startswith("ASCII compliance:")
                for win in quick_wins
            )
        ):
            quick_wins.append(
                "ASCII compliance: non-ASCII characters detected in documentation. "
                "Fix: `python development_tools/run_development_tools.py doc-fix --fix-ascii`. "
                "Verify: `python development_tools/run_development_tools.py doc-sync`."
            )
        add_doc_quick_win(
            "Heading numbering",
            heading_data,
            "python development_tools/run_development_tools.py doc-fix --number-headings",
        )
        add_doc_quick_win(
            "Missing addresses",
            missing_addresses_data,
            "python development_tools/run_development_tools.py doc-fix --add-addresses",
        )
        add_doc_quick_win(
            "Unconverted links",
            unconverted_links_data,
            "python development_tools/run_development_tools.py doc-fix --convert-links",
        )

        # Unused imports (obvious) are surfaced in Immediate Focus Ranked; omit from Quick Wins to avoid duplication.

        lines.append("## Quick Wins")
        if quick_wins:
            quick_wins = list(dict.fromkeys(quick_wins))
            for win in quick_wins:
                lines.append(f"- {win}")
        else:
            lines.append(
                "- No immediate quick wins identified. Re-run doc-sync after tackling focus items."
            )
        lines.append("")

        lines.append("## Watch List")
        if watch_items:
            for item in watch_items:
                lines.append(f"- **{item['title']}**  -  {item['reason']}")
                for bullet in item.get("bullets", []):
                    lines.append(f"  - {bullet}")
        else:
            lines.append("- No active watch-list items. Add threshold-monitor items as key metrics stabilize.")
        lines.append("")

        # Add overlap analysis information only if there are issues to prioritize
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0
        overlap_count = len(section_overlaps) if section_overlaps else 0

        # Add consolidation opportunities as priority items
        if consolidation_recs and consolidation_count > 0:
            # Use tier 4 for consolidation (low priority)
            consolidation_bullets: list[str] = []
            for rec in consolidation_recs[:3]:  # Show top 3
                category = rec.get("category", "Unknown")
                files = rec.get("files", [])
                suggestion = rec.get("suggestion", "")
                if files and len(files) > 1:
                    consolidation_bullets.append(
                        f"{category}: {len(files)} files - {suggestion}"
                    )
                    consolidation_bullets.append(
                        f"  Files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}"
                    )
            add_priority(
                tier=4,  # Tier 4: Low
                title="Consolidate documentation files",
                reason=f"{consolidation_count} file groups could be consolidated to reduce redundancy.",
                bullets=consolidation_bullets,
            )
        elif overlap_count > 0:
            # If only overlaps (no consolidation recs), add as lower priority
            # Use tier 4 for overlap (low priority)
            overlap_bullets = [
                f"{overlap_count} section overlaps detected - review for consolidation opportunities"
            ]
            add_priority(
                tier=4,  # Tier 4: Low
                title="Review documentation overlaps",
                reason=f"{overlap_count} section overlaps detected across documentation files.",
                bullets=overlap_bullets,
            )

        lines.append("")

        lines.append("## Follow-up Commands")
        lines.append(
            "- `python development_tools/run_development_tools.py audit --full`  -  rebuild coverage and hygiene data after fixes."
        )

        return "\n".join(lines)

    def _generate_consolidated_report(self) -> str:
        """Generate comprehensive consolidated report combining all tool outputs."""
        # Log data source context
        audit_tier = getattr(self, "current_audit_tier", None)
        consolidated_target = (
            "DEV_TOOLS_CONSOLIDATED_REPORT.md"
            if self._is_dev_tools_scoped_report()
            else "CONSOLIDATED_REPORT.md"
        )
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating {consolidated_target} using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating {consolidated_target} using cached data (no active audit)"
            )

        # Check if this is a mid-audit write
        instance_flag = hasattr(self, "_audit_in_progress") and self._audit_in_progress
        audit_in_progress = instance_flag or _is_audit_in_progress(self.project_root)
        is_legitimate_end_write = (
            hasattr(self, "current_audit_tier") and self.current_audit_tier is not None
        )

        if audit_in_progress and not is_legitimate_end_write:
            if not instance_flag:
                logger.warning(
                    "_generate_consolidated_report() called from NEW instance during audit! This should only happen at the end."
                )
            else:
                logger.warning(
                    "_generate_consolidated_report() called during audit! This should only happen at the end."
                )
            import traceback

            logger.debug(f"Call stack:\n{''.join(traceback.format_stack())}")

        lines: list[str] = []
        if self._is_dev_tools_scoped_report():
            lines.append("# Development Tools Consolidated Report")
            lines.append("")
            lines.append("> **File**: `development_tools/DEV_TOOLS_CONSOLIDATED_REPORT.md`")
        else:
            lines.append("# Comprehensive AI Development Tools Report")
            lines.append("")
        lines.append(
            "> **Generated**: This file is auto-generated. Do not edit manually."
        )
        lines.append(
            f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if self.current_audit_tier == 1:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --quick"
            )
            tier_name = "Tier 1 (Quick Audit)"
        elif self.current_audit_tier == 3:
            source_cmd = (
                "python development_tools/run_development_tools.py audit --full"
            )
            tier_name = "Tier 3 (Full Audit)"
        elif self.current_audit_tier == 2:
            source_cmd = "python development_tools/run_development_tools.py audit"
            tier_name = "Tier 2 (Standard Audit)"
        else:
            source_cmd = "python development_tools/run_development_tools.py status"
            tier_name = "Status Check (cached data)"
        lines.append(f"> **Source**: `{self._audit_source_cmd_display(source_cmd)}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        if self._is_dev_tools_scoped_report():
            lines.append(
                "> **Role**: Evidence for the `development_tools/` tree from a dev-tools-only audit; product domains may be omitted or under-scanned."
            )
            lines.append(
                "> **Scope**: `get_scan_directories() -> ['development_tools']` for this run. Use `CONSOLIDATED_REPORT.md` without `--dev-tools-only` for full-repo evidence."
            )
            lines.append(
                "> **Artifact layout**: Same as DEV_TOOLS_STATUS — scoped JSON/timings only; legacy flat tool or aggregate files are not read (run `audit --full` with default scope to refresh full-repo caches)."
            )
        else:
            lines.append(
                "> **Role**: Full evidence report with detailed diagnostics, hotspots, and drill-down references."
            )
        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                return value if value.strip().endswith("%") else f"{value}%"
            return self._format_percentage(value, decimals)

        def to_float(value: Any) -> float | None:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return float(stripped)
                except ValueError:
                    return None
            return None

        def to_int(value: Any) -> int | None:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return int(float(stripped))
                except ValueError:
                    return None
            if isinstance(value, dict):
                count = value.get("count")
                return to_int(count)
            return None

        # Load all tool data using unified loader (returns standard format)
        metrics = self._get_canonical_metrics()
        doc_metrics = self._load_tool_data(
            "analyze_function_registry", "functions", log_source=True
        )
        doc_metrics_details = doc_metrics.get("details", {})
        registry_doc_coverage = doc_metrics_details.get(
            "coverage", metrics.get("doc_coverage")
        )
        doc_coverage = registry_doc_coverage

        missing_docs_raw = doc_metrics_details.get("missing", {})

        if isinstance(missing_docs_raw, dict):
            missing_docs_count = missing_docs_raw.get("count", 0)
            missing_docs_list = missing_docs_raw.get("files", {})
        else:
            missing_docs_count = to_int(missing_docs_raw) or 0
            missing_docs_list = {}
        doc_totals = doc_metrics_details.get("totals") or {}
        (
            doc_totals.get("functions_documented")
            if isinstance(doc_totals, dict)
            else None
        )

        doc_sync_data = self._load_tool_data(
            "analyze_documentation_sync", "docs", log_source=True
        )
        doc_sync_summary = (
            getattr(self, "docs_sync_summary", None) or doc_sync_data or {}
        )

        unused_imports_data = self._load_tool_data(
            "analyze_unused_imports", "imports", log_source=True
        )
        analyze_docs_data = self._load_tool_data(
            "analyze_documentation", "docs", log_source=True
        )
        ascii_data = self._load_tool_data(
            "analyze_ascii_compliance", "docs", log_source=True
        )
        heading_data = self._load_tool_data(
            "analyze_heading_numbering", "docs", log_source=True
        )
        missing_addresses_data = self._load_tool_data(
            "analyze_missing_addresses", "docs", log_source=True
        )
        unconverted_links_data = self._load_tool_data(
            "analyze_unconverted_links", "docs", log_source=True
        )

        function_metrics = self._load_tool_data(
            "analyze_functions", "functions", log_source=True
        )
        function_metrics_details = function_metrics.get("details", {})
        code_doc_metrics = self._get_code_docstring_metrics(function_metrics)
        if isinstance(code_doc_metrics.get("coverage"), (int, float)):
            doc_coverage = f"{code_doc_metrics['coverage']:.2f}%"

        (
            analyze_docs_data.get("artifacts")
            if isinstance(analyze_docs_data, dict)
            else None
        )

        # Extract overlap analysis data
        details = analyze_docs_data.get("details", {})
        overlap_analysis_ran = (
            "section_overlaps" in analyze_docs_data
            or "consolidation_recommendations" in analyze_docs_data
            or "section_overlaps" in details
            or "consolidation_recommendations" in details
        )
        overlap_data_source = details.get("overlap_data_source", "fresh")

        section_overlaps = (
            (
                analyze_docs_data.get("section_overlaps")
                or details.get("section_overlaps", {})
            )
            if overlap_analysis_ran
            else {}
        )
        consolidation_recs = (
            (
                analyze_docs_data.get("consolidation_recommendations")
                or details.get("consolidation_recommendations", [])
            )
            if overlap_analysis_ran
            else []
        )
        analyze_docs_data.get("file_purposes") or details.get(
            "file_purposes", {}
        )

        if section_overlaps is None:
            section_overlaps = {}
        if consolidation_recs is None:
            consolidation_recs = []

        error_metrics = self._load_tool_data("analyze_error_handling", "error_handling")
        error_summary = error_metrics.get("summary", {})
        error_details = error_metrics.get("details", {})
        missing_error_handlers = to_int(error_summary.get("total_issues"))
        if missing_error_handlers is None:
            missing_error_handlers = (
                to_int(error_details.get("functions_missing_error_handling")) or 0
            )
        details_missing = to_int(error_details.get("functions_missing_error_handling"))
        if (
            details_missing is not None
            and details_missing > 0
            and (missing_error_handlers is None or missing_error_handlers == 0)
        ):
            missing_error_handlers = details_missing
        error_details.get("recommendations") or []
        worst_error_modules = error_details.get("worst_modules") or []
        if worst_error_modules is None or not isinstance(
            worst_error_modules, (list, tuple)
        ):
            worst_error_modules = []

        coverage_summary = self._load_coverage_summary()

        if (
            not hasattr(self, "dev_tools_coverage_results")
            or not self.dev_tools_coverage_results
        ):
            self._load_dev_tools_coverage()

        legacy_data = self._load_tool_data("analyze_legacy_references", "legacy")
        legacy_summary = (
            getattr(self, "legacy_cleanup_summary", None) or legacy_data or {}
        )
        backup_health_data = self._load_tool_data(
            "analyze_backup_health", "reports", log_source=False
        )
        verify_process_cleanup_data_cr = self._load_tool_data(
            "verify_process_cleanup", "tests", log_source=False
        )
        static_analysis = self._get_static_analysis_snapshot()

        # Get missing docstrings count for consolidated report
        func_undocumented = self._coerce_int(code_doc_metrics.get("undocumented"), 0)

        # Also get handler classes count for consolidated report
        function_patterns_data_for_report = self._load_tool_data(
            "analyze_function_patterns", "functions"
        )
        handler_classes_no_doc = 0
        handler_classes_total = 0
        if function_patterns_data_for_report and isinstance(
            function_patterns_data_for_report, dict
        ):
            handlers = function_patterns_data_for_report.get("details", {}).get(
                "handlers", []
            )
            if handlers:
                handler_classes_total = len(handlers)
                handler_classes_no_doc = len(
                    [h for h in handlers if not h.get("has_doc", True)]
                )

        # Recalculate doc_coverage if Unknown using canonical code metric source.
        if doc_coverage == "Unknown" or doc_coverage is None:
            if isinstance(code_doc_metrics.get("coverage"), (int, float)):
                doc_coverage = f"{code_doc_metrics['coverage']:.2f}%"
            else:
                doc_coverage = "Unknown"

        lines.append("## Executive Summary")

        # Get complexity metrics, trying multiple sources
        total_funcs = metrics.get("total_functions", "Unknown")
        moderate = metrics.get("moderate", "Unknown")
        high = metrics.get("high", "Unknown")
        critical = metrics.get("critical", "Unknown")

        # If still Unknown, try loading from analyze_functions or decision_support cache
        if moderate == "Unknown" or high == "Unknown":
            try:
                cached_data = self._load_results_file_safe()
                if (
                    cached_data
                    and "results" in cached_data
                    and "analyze_functions" in cached_data["results"]
                ):
                    func_data = cached_data["results"]["analyze_functions"]
                    if "data" in func_data:
                        cached_metrics_raw = func_data["data"]
                        if "details" in cached_metrics_raw and isinstance(
                            cached_metrics_raw.get("details"), dict
                        ):
                            cached_metrics = cached_metrics_raw["details"]
                        else:
                            cached_metrics = cached_metrics_raw
                        if moderate == "Unknown":
                            moderate = cached_metrics.get(
                                "moderate_complexity", "Unknown"
                            )
                        if high == "Unknown":
                            high = cached_metrics.get("high_complexity", "Unknown")
                        if critical == "Unknown":
                            critical = cached_metrics.get(
                                "critical_complexity", "Unknown"
                            )
                        if total_funcs == "Unknown":
                            total_funcs = cached_metrics.get(
                                "total_functions", "Unknown"
                            )
                if (
                    (moderate == "Unknown" or high == "Unknown")
                    and cached_data
                    and "results" in cached_data
                    and "decision_support" in cached_data["results"]
                ):
                    ds_data = cached_data["results"]["decision_support"]
                    ds_details = self._get_decision_support_details(
                        ds_data.get("data") if isinstance(ds_data, dict) else None
                    )
                    if ds_details:
                        if moderate == "Unknown":
                            moderate = ds_details.get("moderate_complexity", "Unknown")
                        if high == "Unknown":
                            high = ds_details.get("high_complexity", "Unknown")
                        if critical == "Unknown":
                            critical = ds_details.get("critical_complexity", "Unknown")
                        if total_funcs == "Unknown":
                            total_funcs = ds_details.get("total_functions", "Unknown")
            except Exception as e:
                logger.debug(
                    f"Failed to load complexity from cache in consolidated report: {e}"
                )
                pass

        if total_funcs == "Unknown":
            lines.append(
                "- **Total Functions**: Run `python development_tools/run_development_tools.py audit` for detailed metrics"
            )
        else:
            lines.append(
                f"- **Total Functions**: {total_funcs} (Critical: {critical}, High: {high}, Moderate: {moderate})"
            )

        # Add test markers to executive summary
        test_markers_data = self._load_tool_data("analyze_test_markers", "tests")
        if test_markers_data and isinstance(test_markers_data, dict):
            if "summary" in test_markers_data:
                missing_markers = test_markers_data["summary"].get("total_issues", 0)
            else:
                missing_markers = test_markers_data.get("missing_count", 0)
            if missing_markers > 0:
                lines.append(
                    f"- Test markers: {missing_markers} tests missing category markers"
                )

        if verify_process_cleanup_data_cr and isinstance(
            verify_process_cleanup_data_cr, dict
        ):
            vpc_ex = verify_process_cleanup_data_cr.get("details", {}) or {}
            vpc_sm = verify_process_cleanup_data_cr.get("summary", {}) or {}
            if str(vpc_ex.get("platform", "") or "") == "win32":
                vpc_n_ex = self._coerce_int(vpc_sm.get("total_issues"), 0) or 0
                vpc_st_ex = str(vpc_sm.get("status", "") or "").upper()
                if vpc_n_ex > 0 or vpc_st_ex == "WARN":
                    lines.append(
                        f"- **Pytest process cleanup (Windows)**: WARN — {vpc_n_ex} "
                        "candidate orphan worker process(es); see **Pytest process cleanup (Windows)** below."
                    )

        # Use error_details for consistent metric sourcing (same as AI_STATUS/AI_PRIORITIES)
        error_cov = error_details.get("analyze_error_handling") or error_details.get(
            "error_handling_coverage"
        )
        missing_error_handlers_for_summary = to_int(
            error_details.get("functions_missing_error_handling", 0)
        )
        error_total = error_details.get("total_functions")
        error_with_handling = error_details.get("functions_with_error_handling")

        if error_total and error_with_handling:
            calc_coverage = (error_with_handling / error_total) * 100
            if 0 <= calc_coverage <= 100:
                error_cov = calc_coverage
        elif error_cov is None and error_total and error_with_handling:
            error_cov = (error_with_handling / error_total) * 100

        if error_cov is not None:
            lines.append(
                f"- **Error Handling Coverage**: {percent_text(error_cov, 1)} ({missing_error_handlers_for_summary or 0} functions need protection)"
            )

        dev_tools_insights = self._get_dev_tools_coverage_insights()

        if coverage_summary:
            overall = coverage_summary.get("overall") or {}
            overall_cov = overall.get("coverage")
            lines.append(
                f"- **Overall test coverage**: {percent_text(overall_cov, 1)} across {overall.get('statements', 0)} statements"
            )

            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                summary_line = (
                    f"- **Development tools coverage**: {percent_text(dev_pct, 1)}"
                )
                if (
                    dev_tools_insights.get("covered") is not None
                    and dev_tools_insights.get("statements") is not None
                ):
                    summary_line += f" ({dev_tools_insights['covered']} of {dev_tools_insights['statements']} statements)"
                lines.append(summary_line)
        elif hasattr(self, "coverage_results") and self.coverage_results:
            lines.append(
                "- Coverage regeneration flagged issues; inspect coverage.json for details"
            )
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                summary_line = (
                    f"- **Development tools coverage**: {percent_text(dev_pct, 1)}"
                )
                if (
                    dev_tools_insights.get("covered") is not None
                    and dev_tools_insights.get("statements") is not None
                ):
                    summary_line += f" ({dev_tools_insights['covered']} of {dev_tools_insights['statements']} statements)"
                lines.append(summary_line)
        else:
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                summary_line = (
                    f"- **Development tools coverage**: {percent_text(dev_pct, 1)}"
                )
                if (
                    dev_tools_insights.get("covered") is not None
                    and dev_tools_insights.get("statements") is not None
                ):
                    summary_line += f" ({dev_tools_insights['covered']} of {dev_tools_insights['statements']} statements)"
                lines.append(summary_line)

        # Get path_drift - check standard format first
        path_drift = None
        if doc_sync_summary and isinstance(doc_sync_summary, dict):
            if "summary" in doc_sync_summary and isinstance(
                doc_sync_summary.get("summary"), dict
            ):
                path_drift = doc_sync_summary.get("details", {}).get(
                    "path_drift_issues", 0
                )

        if path_drift is not None:
            lines.append(
                f"- **Documentation path drift**: {path_drift} issues need sync"
            )

        # Get legacy_issues - check standard format first
        legacy_issues = None
        if legacy_summary and isinstance(legacy_summary, dict):
            if "summary" in legacy_summary and isinstance(
                legacy_summary.get("summary"), dict
            ):
                legacy_issues = legacy_summary["summary"].get("files_affected", 0)

        if legacy_issues is not None:
            lines.append(
                f"- **Legacy references**: {legacy_issues} files still reference legacy patterns"
            )

        backup_summary = (
            backup_health_data.get("summary", {})
            if isinstance(backup_health_data, dict)
            else {}
        )
        backup_checks = (
            backup_health_data.get("details", {}).get("checks", [])
            if isinstance(backup_health_data.get("details"), dict)
            else (
                backup_health_data.get("checks", [])
                if isinstance(backup_health_data, dict)
                else []
            )
        )
        if backup_summary:
            backup_status = str(
                backup_summary.get(
                    "status",
                    "PASS" if bool(backup_summary.get("success")) else "FAIL",
                )
            ).upper()
            passed_checks = backup_summary.get("passed_checks")
            total_checks = backup_summary.get("total_checks")
            check_fragment = ""
            if isinstance(passed_checks, int) and isinstance(total_checks, int):
                check_fragment = f" ({passed_checks}/{total_checks} checks)"
            lines.append(f"- **Backup Health**: {backup_status}{check_fragment}")

        lines.append("")

        # Documentation Status section
        lines.append("## Documentation Status")

        # Use aggregated doc sync summary from current run first, then fall back to cache
        doc_sync_summary_for_signals = None
        if (
            hasattr(self, "docs_sync_summary")
            and self.docs_sync_summary
            and isinstance(self.docs_sync_summary, dict)
        ):
            docs_sync_summary = self.docs_sync_summary
            docs_sync_summary_summary = (
                docs_sync_summary.get("summary", {})
                if isinstance(docs_sync_summary.get("summary"), dict)
                else {}
            )
            docs_sync_summary_details = (
                docs_sync_summary.get("details", {})
                if isinstance(docs_sync_summary.get("details"), dict)
                else {}
            )
            doc_sync_summary_for_signals = {
                "status": docs_sync_summary_summary.get("status", "UNKNOWN"),
                "path_drift_issues": docs_sync_summary_details.get(
                    "path_drift_issues", 0
                ),
                "paired_doc_issues": docs_sync_summary_details.get(
                    "paired_doc_issues", 0
                ),
                "ascii_issues": docs_sync_summary_details.get("ascii_issues", 0),
                "heading_numbering_issues": docs_sync_summary_details.get(
                    "heading_numbering_issues", 0
                ),
                "missing_address_issues": docs_sync_summary_details.get(
                    "missing_address_issues", 0
                ),
                "unconverted_link_issues": docs_sync_summary_details.get(
                    "unconverted_link_issues", 0
                ),
                "path_drift_files": docs_sync_summary_details.get(
                    "path_drift_files", []
                ),
                "example_marker_hint_count": docs_sync_summary_details.get(
                    "example_marker_hint_count", 0
                ),
                "example_marker_findings": docs_sync_summary_details.get(
                    "example_marker_findings", {}
                ),
            }

        if not doc_sync_summary_for_signals:
            doc_sync_result = self._load_tool_data("analyze_documentation_sync", "docs")
            if doc_sync_result:
                cached_metrics = (
                    doc_sync_result if isinstance(doc_sync_result, dict) else {}
                )
                summary = (
                    cached_metrics.get("summary", {})
                    if isinstance(cached_metrics, dict)
                    else {}
                )
                details = (
                    cached_metrics.get("details", {})
                    if isinstance(cached_metrics, dict)
                    else {}
                )
                doc_sync_summary_for_signals = {
                    "status": summary.get("status", "UNKNOWN"),
                    "path_drift_issues": details.get("path_drift_issues", 0),
                    "paired_doc_issues": details.get("paired_doc_issues", 0),
                    "ascii_issues": details.get("ascii_issues", 0),
                    "path_drift_files": details.get("path_drift_files", []),
                    "example_marker_hint_count": details.get(
                        "example_marker_hint_count", 0
                    ),
                    "example_marker_findings": details.get(
                        "example_marker_findings", {}
                    ),
                }

        effective_summary = (
            doc_sync_summary if doc_sync_summary else doc_sync_summary_for_signals
        )

        def get_doc_sync_field(data, field_name, default=None):
            if not data or not isinstance(data, dict):
                return default
            if "summary" not in data or not isinstance(data.get("summary"), dict):
                return default
            if field_name == "status":
                return data["summary"].get("status", default)
            if field_name == "total_issues":
                return data["summary"].get("total_issues", default)
            return data.get("details", {}).get(field_name, default)

        def extract_files_with_issue_counts(tool_data):
            """Extract file paths with their issue counts from tool data."""
            if not tool_data or not isinstance(tool_data, dict):
                return {}

            file_counts = {}

            if "files" in tool_data:
                files_dict = tool_data.get("files", {})
                if isinstance(files_dict, dict):
                    for file_path, value in files_dict.items():
                        if isinstance(file_path, str):
                            # CRITICAL: Filter out files that no longer exist
                            try:
                                file_path_obj = self.project_root / file_path
                                if not file_path_obj.exists():
                                    # File doesn't exist, skip it
                                    continue
                            except (OSError, ValueError):
                                # Error checking file, skip it
                                continue

                            if isinstance(value, (int, float)):
                                file_counts[file_path] = int(value)
                            elif isinstance(value, dict):
                                results = value.get("results", [])
                                if isinstance(results, list):
                                    file_counts[file_path] = len(results)
                                else:
                                    file_counts[file_path] = 1

            if not file_counts:
                data_dict = (
                    tool_data.get("data", tool_data)
                    if "data" in tool_data
                    else tool_data
                )
                if isinstance(data_dict, dict):
                    for f, v in data_dict.items():
                        if isinstance(f, str) and isinstance(v, dict):
                            # CRITICAL: Filter out files that no longer exist
                            try:
                                file_path_obj = self.project_root / f
                                if not file_path_obj.exists():
                                    # File doesn't exist, skip it
                                    continue
                            except (OSError, ValueError):
                                # Error checking file, skip it
                                continue

                            results = v.get("results", [])
                            if isinstance(results, list) and len(results) > 0:
                                file_counts[f] = len(results)

            return file_counts

        def get_issue_count(summary_key, tool_data, default=0):
            """Get issue count from summary, or calculate from tool data."""
            count = 0
            if effective_summary:
                if summary_key in effective_summary:
                    count = effective_summary.get(summary_key, 0) or 0
                elif "summary" in effective_summary and isinstance(
                    effective_summary.get("summary"), dict
                ):
                    count = effective_summary.get("details", {}).get(summary_key, 0)

            if count == 0 and tool_data and isinstance(tool_data, dict):
                if "summary" in tool_data and isinstance(
                    tool_data.get("summary"), dict
                ):
                    count = tool_data["summary"].get("total_issues", 0)
                elif "files" in tool_data:
                    files_dict = tool_data.get("files", {})
                    if isinstance(files_dict, dict):
                        count = sum(
                            v if isinstance(v, (int, float)) else 1
                            for v in files_dict.values()
                        )
                else:
                    data_dict = (
                        tool_data.get("data", tool_data)
                        if "data" in tool_data
                        else tool_data
                    )
                    if isinstance(data_dict, dict):
                        total = 0
                        for _f, v in data_dict.items():
                            if isinstance(v, dict):
                                results = v.get("results", [])
                                if isinstance(results, list) and len(results) > 0:
                                    total += len(results)
                        if total > 0:
                            count = total
            return count if count > 0 else default

        if effective_summary:
            # Path Drift
            path_drift = get_doc_sync_field(effective_summary, "path_drift_issues", 0)
            if path_drift is None:
                path_drift = 0
            if path_drift > 0:
                drift_files = get_doc_sync_field(
                    effective_summary, "path_drift_files", []
                )
                if not isinstance(drift_files, list):
                    drift_files = []
                lines.append("**Path Drift** FAIL")
                lines.append(f"  - {path_drift} problem files (total issues)")
                if len(drift_files) <= 4:
                    drift_hotspots = ", ".join(drift_files)
                else:
                    visible = ", ".join(drift_files[:4])
                    remaining = path_drift - 4
                    drift_hotspots = f"{visible}, ... +{remaining}"
                lines.append(f"  - Top files: {drift_hotspots}")
            else:
                lines.append("**Path Drift** CLEAN")
                lines.append("  - 0 problem files")

            # Paired Docs
            paired = get_doc_sync_field(effective_summary, "paired_doc_issues", 0) or 0
            if paired == 0:
                lines.append("**Paired Docs** CLEAN")
                lines.append("  - 0 H2 mismatches")
            else:
                lines.append("**Paired Docs** FAIL")
                lines.append(f"  - {paired} H2 mismatches")

            # ASCII Compliance
            ascii_issues = get_issue_count("ascii_issues", ascii_data)
            if ascii_issues > 0:
                ascii_file_counts = extract_files_with_issue_counts(ascii_data)
                if ascii_data and isinstance(ascii_data, dict):
                    if "summary" in ascii_data:
                        file_count = ascii_data["summary"].get("files_affected", 0)
                    else:
                        file_count = ascii_data.get("file_count", 0)
                else:
                    file_count = len(ascii_file_counts)
                if file_count == 0:
                    file_count = len(ascii_file_counts)
                lines.append("**ASCII Compliance** FAIL")
                lines.append(f"  - {file_count} files with {ascii_issues} total issues")
                if ascii_file_counts:
                    sorted_files = sorted(
                        ascii_file_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    file_list = [
                        f"{file_path} ({count})" for file_path, count in sorted_files
                    ]
                    if len(ascii_file_counts) > 5:
                        file_list.append(f"... +{len(ascii_file_counts) - 5}")
                    lines.append(f"  - Top files: {', '.join(file_list)}")
            else:
                lines.append("**ASCII Compliance** CLEAN")
                lines.append("  - 0 files with issues")

            # Heading Numbering
            heading_issues = get_issue_count("heading_numbering_issues", heading_data)
            if heading_issues > 0:
                heading_file_counts = extract_files_with_issue_counts(heading_data)
                if heading_data and isinstance(heading_data, dict):
                    if "summary" in heading_data:
                        file_count = heading_data["summary"].get("files_affected", 0)
                    else:
                        file_count = heading_data.get("file_count", 0)
                else:
                    file_count = len(heading_file_counts)
                if file_count == 0:
                    file_count = len(heading_file_counts)
                lines.append("**Heading Numbering** FAIL")
                lines.append(
                    f"  - {file_count} files with {heading_issues} total issues"
                )
                if heading_file_counts:
                    sorted_files = sorted(
                        heading_file_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    file_list = [
                        f"{file_path} ({count})" for file_path, count in sorted_files
                    ]
                    if len(heading_file_counts) > 5:
                        file_list.append(f"... +{len(heading_file_counts) - 5}")
                    lines.append(f"  - Top files: {', '.join(file_list)}")
            else:
                lines.append("**Heading Numbering** CLEAN")
                lines.append("  - 0 files with issues")

            # Missing Addresses
            missing_address_issues = get_issue_count(
                "missing_address_issues", missing_addresses_data
            )
            if missing_address_issues > 0:
                missing_file_counts = extract_files_with_issue_counts(
                    missing_addresses_data
                )
                if missing_addresses_data and isinstance(missing_addresses_data, dict):
                    if "summary" in missing_addresses_data:
                        file_count = missing_addresses_data["summary"].get(
                            "files_affected", 0
                        )
                    else:
                        file_count = missing_addresses_data.get("file_count", 0)
                else:
                    file_count = len(missing_file_counts)
                # If file_count is still 0 but we have issues, try to get from file_counts or set to at least 1
                if file_count == 0:
                    file_count = (
                        len(missing_file_counts)
                        if missing_file_counts
                        else (1 if missing_address_issues > 0 else 0)
                    )
                lines.append("**Missing Addresses** FAIL")
                lines.append(
                    f"  - {file_count} files with {missing_address_issues} total documentation missing addresses"
                )
                if missing_file_counts:
                    sorted_files = sorted(
                        missing_file_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    file_list = [
                        f"{file_path} ({count})" for file_path, count in sorted_files
                    ]
                    if len(missing_file_counts) > 5:
                        file_list.append(f"... +{len(missing_file_counts) - 5}")
                    lines.append(f"  - Top files: {', '.join(file_list)}")
            else:
                lines.append("**Missing Addresses** CLEAN")
                lines.append("  - 0 files with missing addresses")

            # Unconverted Links
            unconverted_link_issues = get_issue_count(
                "unconverted_link_issues", unconverted_links_data
            )
            if unconverted_link_issues > 0:
                unconverted_file_counts = extract_files_with_issue_counts(
                    unconverted_links_data
                )
                if unconverted_links_data and isinstance(unconverted_links_data, dict):
                    if "summary" in unconverted_links_data:
                        file_count = unconverted_links_data["summary"].get(
                            "files_affected", 0
                        )
                    else:
                        file_count = unconverted_links_data.get("file_count", 0)
                else:
                    file_count = len(unconverted_file_counts)
                if file_count == 0:
                    file_count = len(unconverted_file_counts)
                lines.append("**Unconverted Links** FAIL")
                lines.append(
                    f"  - {file_count} files with {unconverted_link_issues} total issues"
                )
                if unconverted_file_counts:
                    sorted_files = sorted(
                        unconverted_file_counts.items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:5]
                    file_list = [
                        f"{file_path} ({count})" for file_path, count in sorted_files
                    ]
                    if len(unconverted_file_counts) > 5:
                        file_list.append(f"... +{len(unconverted_file_counts) - 5}")
                    lines.append(f"  - Top files: {', '.join(file_list)}")
            else:
                lines.append("**Unconverted Links** CLEAN")
                lines.append("  - 0 files with unconverted links")

            # Example markers (advisory; audit runs --check-example-markers with doc-sync).
            # effective_summary may be standard {summary,details} or a flat doc_sync_summary_for_signals dict.
            if isinstance(effective_summary, dict) and isinstance(
                effective_summary.get("summary"), dict
            ):
                em_c = get_doc_sync_field(
                    effective_summary, "example_marker_hint_count", 0
                )
                em_cf = get_doc_sync_field(
                    effective_summary, "example_marker_findings", {}
                )
            elif isinstance(effective_summary, dict):
                em_c = effective_summary.get("example_marker_hint_count", 0)
                em_cf = effective_summary.get("example_marker_findings", {})
            else:
                em_c = 0
                em_cf = {}
            try:
                em_cn = int(em_c or 0)
            except (TypeError, ValueError):
                em_cn = 0
            if not isinstance(em_cf, dict):
                em_cf = {}
            if em_cn > 0:
                lines.append("**Example Markers (advisory)** ATTENTION")
                lines.append(
                    f"  - {em_cn} hint(s): path-like lines in Example sections without "
                    "standard [OK]/[AVOID]/[GOOD]/[BAD]/[EXAMPLE] markers"
                )
                top_em = sorted(em_cf.keys())[:5]
                if top_em:
                    lines.append(f"  - Files with hints: {', '.join(top_em)}")
            else:
                lines.append("**Example Markers (advisory)** CLEAN")
                lines.append("  - 0 hints from paired-doc Example scan")

            # Dependency Documentation
            dependency_summary = getattr(self, "module_dependency_summary", None) or (
                hasattr(self, "results_cache")
                and self.results_cache.get("analyze_module_dependencies")
            )
            if not dependency_summary:
                dependency_data = self._load_tool_data(
                    "analyze_module_dependencies", "imports"
                )
                if dependency_data and isinstance(dependency_data, dict):
                    dependency_summary = dependency_data

            missing_deps = (
                dependency_summary.get("missing_dependencies")
                if dependency_summary
                else None
            )
            if missing_deps:
                lines.append("**Dependency Documentation** FAIL")
                missing_files = (
                    dependency_summary.get("missing_files")
                    or dependency_summary.get("missing_sections")
                    or []
                )
                file_count = len(missing_files) if missing_files else missing_deps
                lines.append(
                    f"  - {file_count} files with {missing_deps} total undocumented references detected"
                )
                if missing_files:
                    file_list = []
                    for _i, file_path in enumerate(missing_files[:5]):
                        file_list.append(f"{file_path} (1)")
                    if len(missing_files) > 5:
                        file_list.append(f"... +{len(missing_files) - 5}")
                    lines.append(f"  - Top files: {', '.join(file_list)}")
            else:
                lines.append("**Dependency Documentation** CLEAN")
                lines.append("  - 0 undocumented references")

            # TODO.md Status
            todo_sync_result = getattr(self, "todo_sync_result", None)
            if todo_sync_result and isinstance(todo_sync_result, dict):
                entries = todo_sync_result.get("entries", [])
                completed_entries = todo_sync_result.get("completed_entries", [])

                if (entries and isinstance(entries, list) and len(entries) > 0) or (
                    completed_entries and len(completed_entries) > 0
                ):
                    entry_count = len(entries) if entries else len(completed_entries)
                    lines.append("**TODO.md Status** FAIL")
                    lines.append(f"  - {entry_count} completed entries detected")
                else:
                    lines.append("**TODO.md Status** CLEAN")
                    lines.append("  - 0 completed entries detected")
            else:
                lines.append("**TODO.md Status** CLEAN")
                lines.append("  - 0 completed entries detected")

            # Function Docstring Coverage
            total_funcs_docstatus = self._coerce_int(code_doc_metrics.get("total"), 0)
            undocumented_funcs_docstatus = self._coerce_int(
                code_doc_metrics.get("undocumented"), 0
            )

            if total_funcs_docstatus and total_funcs_docstatus > 0:
                documented_funcs_docstatus = (
                    total_funcs_docstatus - undocumented_funcs_docstatus
                )
                coverage_pct_docstatus = (
                    documented_funcs_docstatus / total_funcs_docstatus
                ) * 100
                if undocumented_funcs_docstatus > 0:
                    lines.append("**Function Docstring Coverage** FAIL")
                    lines.append(
                        f"  - {undocumented_funcs_docstatus} functions missing docstrings ({coverage_pct_docstatus:.2f}% coverage)"
                    )
                else:
                    lines.append("**Function Docstring Coverage** CLEAN")
                    lines.append(
                        f"  - 0 functions missing docstrings ({coverage_pct_docstatus:.2f}% coverage)"
                    )
            else:
                lines.append("**Function Docstring Coverage** UNKNOWN")
                lines.append("  - Function data not available")

        lines.append("")

        # Documentation Overlap
        lines.append("## Documentation Overlap")
        overlap_count = len(section_overlaps) if section_overlaps else 0
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0

        if overlap_count > 0 or consolidation_count > 0:
            if section_overlaps and overlap_count > 0:
                lines.append(
                    f"- **Section Overlaps**: {overlap_count} sections duplicated across files"
                )
                top_overlaps = sorted(
                    section_overlaps.items(), key=lambda x: len(x[1]), reverse=True
                )[:3]
                for section, files in top_overlaps:
                    lines.append(
                        f"  - `{section}` appears in: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}"
                    )
            if consolidation_recs:
                lines.append(
                    f"- **Consolidation Opportunities**: {consolidation_count} file groups identified for potential consolidation"
                )
                for rec in consolidation_recs[:3]:
                    category = rec.get("category", "Unknown")
                    files = rec.get("files", [])
                    suggestion = rec.get("suggestion", "")
                    if files:
                        lines.append(
                            f"  - {category}: {len(files)} files ({', '.join(files[:2])}{'...' if len(files) > 2 else ''}) - {suggestion}"
                        )
        else:
            if overlap_analysis_ran:
                if overlap_data_source == "cached":
                    lines.append(
                        "- **Status**: No overlaps detected (cached overlap data)"
                    )
                    lines.append(
                        "  - Using cached overlap data (run `audit --full` or `--overlap` flag for latest validation)"
                    )
                else:
                    lines.append(
                        "- **Status**: No overlaps detected (analysis performed)"
                    )
                    lines.append(
                        "  - Overlap analysis ran but found no section overlaps or consolidation opportunities"
                    )
            else:
                lines.append(
                    "- **Status**: Overlap analysis not run (use `audit --full` or `--overlap` flag)"
                )
                lines.append(
                    "  - Standard audits skip overlap analysis by default; run `audit --full` or use `--overlap` flag to include it"
                )

        lines.append("")

        # Error Handling
        lines.append("## Error Handling")

        if error_metrics and isinstance(error_metrics, dict):
            error_details = error_metrics.get("details", {})

            def get_error_field(field_name, default=None):
                return error_details.get(field_name, default)

            if missing_error_handlers is None:
                missing_error_handlers = 0
            lines.append(
                f"- **Missing Error Handling**: {missing_error_handlers} functions lack protections"
            )

            if worst_error_modules:
                module_summaries = []
                modules_needing_attention = [
                    m
                    for m in worst_error_modules[:3]
                    if m.get("missing", 0) > 0 and m.get("coverage", 100) < 100
                ]

                for module in modules_needing_attention:
                    module_name = module.get("module", "Unknown")
                    coverage_pct = percent_text(module.get("coverage"), 1)
                    missing = module.get("missing")
                    total = module.get("total")
                    detail = f"{module_name} ({coverage_pct}"
                    if missing is not None and total is not None:
                        detail += f", missing {missing}/{total}"
                    detail += ")"
                    module_summaries.append(detail)

                if module_summaries:
                    lines.append(
                        f"  - Top candidate modules: {', '.join(module_summaries)}"
                    )

            decorated = get_error_field("functions_with_decorators")
            if decorated is not None:
                lines.append(
                    f"- **@handle_errors Usage**: {decorated} functions already use the decorator"
                )

            # Phase 1: Decorator replacement candidates
            phase1_total = get_error_field("phase1_total", 0)

            if phase1_total > 0:
                phase1_by_priority = get_error_field("phase1_by_priority", {}) or {}
                if not isinstance(phase1_by_priority, dict):
                    phase1_by_priority = {}

                priority_breakdown = []
                if phase1_by_priority.get("high", 0) > 0:
                    priority_breakdown.append(f"{phase1_by_priority['high']} high")
                if phase1_by_priority.get("medium", 0) > 0:
                    priority_breakdown.append(f"{phase1_by_priority['medium']} medium")
                if phase1_by_priority.get("low", 0) > 0:
                    priority_breakdown.append(f"{phase1_by_priority['low']} low")

                priority_text = (
                    ", ".join(priority_breakdown) if priority_breakdown else "0"
                )
                lines.append(
                    f"- **Phase 1 Candidates**: {phase1_total} functions with basic try-except blocks need decorator replacement ({priority_text} priority)"
                )

                phase1_candidates = get_error_field("phase1_candidates", []) or []
                if not isinstance(phase1_candidates, list):
                    phase1_candidates = []
                if phase1_candidates:
                    from collections import defaultdict

                    by_module = defaultdict(int)

                    for candidate in phase1_candidates:
                        if isinstance(candidate, dict):
                            file_path = candidate.get("file_path", "")
                            if file_path:
                                module = Path(file_path).name
                                by_module[module] += 1

                    if by_module:
                        top_modules = sorted(
                            by_module.items(), key=lambda x: x[1], reverse=True
                        )[:3]
                        module_list = [
                            f"{module} ({count})" for module, count in top_modules
                        ]
                        if len(by_module) > 3:
                            module_list.append(f"... +{len(by_module) - 3}")
                        lines.append(
                            f"  - Top candidate modules with function counts: {', '.join(module_list)}"
                        )

            # Phase 2: Generic exception categorization
            phase2_total = get_error_field("phase2_total", 0)

            if phase2_total > 0:
                phase2_by_type = get_error_field("phase2_by_type", {}) or {}
                if not isinstance(phase2_by_type, dict):
                    phase2_by_type = {}

                type_breakdown = [
                    f"{count} {exc_type}"
                    for exc_type, count in sorted(
                        phase2_by_type.items(), key=lambda x: x[1], reverse=True
                    )[:3]
                ]
                type_text = ", ".join(type_breakdown) if type_breakdown else "0"

                if len(phase2_by_type) > 3:
                    type_text += f", ... +{len(phase2_by_type) - 3} more"

                lines.append(
                    f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})"
                )

                phase2_exceptions = get_error_field("phase2_exceptions", []) or []
                if not isinstance(phase2_exceptions, list):
                    phase2_exceptions = []
                if phase2_exceptions:
                    from collections import defaultdict

                    by_module = defaultdict(lambda: defaultdict(int))

                    for exc in phase2_exceptions:
                        if isinstance(exc, dict):
                            file_path = exc.get("file_path", "")
                            exc_type = exc.get("exception_type", "Unknown")
                            if file_path:
                                module = Path(file_path).name
                                by_module[module][exc_type] += 1

                    if by_module:
                        module_list = []
                        for module, exc_types in sorted(
                            by_module.items(),
                            key=lambda x: sum(x[1].values()),
                            reverse=True,
                        )[:3]:
                            exc_details = [
                                f"{count} {exc_type}"
                                for exc_type, count in sorted(
                                    exc_types.items(), key=lambda x: x[1], reverse=True
                                )
                            ]
                            module_list.append(f"{module} ({', '.join(exc_details)})")

                        if len(by_module) > 3:
                            module_list.append(f"... +{len(by_module) - 3}")
                        lines.append(
                            f"  - Top candidate modules with function counts and exception types: {', '.join(module_list)}"
                        )
        else:
            lines.append(
                "- **Error Handling**: Run `python development_tools/run_development_tools.py audit` for detailed metrics"
            )

        lines.append("")

        # Test Coverage
        lines.append("## Test Coverage")

        skip_main_tracks_cr = bool(
            getattr(self, "_tier3_skipped_main_tracks", False)
        )
        skip_dev_track_cr = bool(getattr(self, "_tier3_skipped_dev_track", False))

        if skip_main_tracks_cr:
            lines.append(
                "- **Overall Coverage**: **Skipped** - `audit --full --dev-tools-only` does not re-run "
                "full-repo coverage. Run `python development_tools/run_development_tools.py audit --full` "
                "(no `--dev-tools-only`) for updated product coverage and "
                "`development_docs/TEST_COVERAGE_REPORT.md`."
            )
        elif coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            lines.append(
                f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} ({overall.get('covered')} of {overall.get('statements')} statements)"
            )

            # Domains with Lowest Coverage
            domain_gaps = []
            for m in coverage_summary.get("modules") or []:
                coverage_val = m.get("coverage", 100)
                if isinstance(coverage_val, str):
                    coverage_val = to_float(coverage_val) or 100
                elif not isinstance(coverage_val, (int, float)):
                    coverage_val = 100
                if coverage_val < 80:
                    domain_gaps.append(m)

            if domain_gaps:
                domain_descriptions = [
                    f"{m['module']} ({percent_text(m.get('coverage'), 1)}, missing {m.get('missed')} lines)"
                    for m in domain_gaps[:5]
                ]
                lines.append(
                    f"    - **Domains with Lowest Coverage**: {', '.join(domain_descriptions)}"
                )

            worst_files = (coverage_summary or {}).get("worst_files") or []
            if worst_files:
                file_descriptions = [
                    f"{item['path']} ({percent_text(item.get('coverage'), 1)}, missing {item.get('missing', item.get('missed', 0))} lines)"
                    for item in worst_files[:5]
                ]
                lines.append(
                    f"    - **Modules with Lowest Coverage**: {', '.join(file_descriptions)}"
                )
                cov_path = (
                    self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
                )
                if cov_path.exists():
                    href = self._markdown_href_from_dev_tools_report(cov_path)
                    lines.append(
                        f"    - **Detailed Report**: [TEST_COVERAGE_REPORT.md]({href})"
                    )

        if skip_main_tracks_cr or (
            coverage_summary and isinstance(coverage_summary, dict)
        ):
            dev_tools_insights = self._get_dev_tools_coverage_insights()
            if skip_dev_track_cr:
                lines.append(
                    "- **Development Tools Coverage**: Separate `--dev-tools-only` refresh not run in this "
                    "full-repo Tier 3 pass. Overall coverage above already includes "
                    "`development_tools`; run `audit --full --dev-tools-only` only to refresh "
                    "DEV_TOOLS reports and the dedicated scoped track."
                )
            elif dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
                dev_pct = dev_tools_insights["overall_pct"]
                dev_statements = dev_tools_insights.get("statements")
                dev_covered = dev_tools_insights.get("covered")
                summary_line = (
                    f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                )
                if dev_statements is not None and dev_covered is not None:
                    summary_line += f" ({dev_covered} of {dev_statements} statements)"
                lines.append(summary_line)
                low_modules = dev_tools_insights.get("low_modules") or []
                if low_modules:
                    dev_descriptions = [
                        f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)}, missing {item.get('missed')} lines)"
                        for item in low_modules[:5]
                    ]
                    lines.append(
                        f"    - **Modules with Lowest Coverage**: {', '.join(dev_descriptions)}"
                    )

            test_markers_data = self._load_tool_data("analyze_test_markers", "tests")
            if test_markers_data and isinstance(test_markers_data, dict):
                if "summary" in test_markers_data:
                    summary = test_markers_data.get("summary", {})
                    missing_count = summary.get("total_issues", 0)
                    details = test_markers_data.get("details", {})
                    missing_list = details.get("missing", [])
                else:
                    missing_count = test_markers_data.get("missing_count", 0)
                    missing_list = test_markers_data.get("missing", [])

                if missing_count > 0 or (missing_list and len(missing_list) > 0):
                    lines.append("## Test Markers")
                    actual_count = (
                        missing_count
                        if missing_count > 0
                        else len(missing_list) if missing_list else 0
                    )
                    lines.append(
                        f"- **Missing Category Markers**: {actual_count} tests missing pytest category markers"
                    )
                    from collections import defaultdict

                    files_with_missing = defaultdict(list)
                    for item in missing_list:
                        if isinstance(item, dict):
                            file_path = item.get("file", "")
                            test_name = item.get("name", "")
                            if file_path:
                                files_with_missing[file_path].append(test_name)

                    if files_with_missing:
                        sorted_files = sorted(
                            files_with_missing.items(),
                            key=lambda x: len(x[1]),
                            reverse=True,
                        )[:5]
                        file_list = [
                            f"{Path(f).name} ({len(tests)} tests)"
                            for f, tests in sorted_files
                        ]
                        if len(files_with_missing) > 5:
                            file_list.append(
                                f"... +{len(files_with_missing) - 5} files"
                            )
                        lines.append(f"    - **Top files**: {', '.join(file_list)}")
                else:
                    lines.append("## Test Markers")
                    lines.append(
                        "- **Status**: CLEAN (all tests have category markers)"
                    )

        elif hasattr(self, "coverage_results") and self.coverage_results:
            lines.append(
                "- Coverage regeneration completed with issues; inspect coverage.json for gap details"
            )
        else:
            lines.append("- Run `audit --full` to regenerate coverage metrics")

        lines.append("")

        lines.extend(
            self._lines_for_verify_process_cleanup_consolidated_section(
                verify_process_cleanup_data_cr
            )
        )

        # Unused Imports
        lines.append("## Unused Imports")

        if unused_imports_data:
            summary = unused_imports_data.get("summary", {})
            details = unused_imports_data.get("details", {})
            total_unused = summary.get("total_issues", 0)
            files_with_issues = summary.get("files_affected", 0)
            if total_unused > 0 or files_with_issues > 0:
                lines.append(
                    f"- **Total Unused**: {total_unused} imports across {files_with_issues} files"
                )
                by_category = details.get("by_category", {})
                perf = details.get("performance", {})
                obvious = by_category.get("obvious_unused")
                if obvious:
                    lines.append(f"    - **Obvious Removals**: {obvious} imports")
                type_only = by_category.get("type_hints_only")
                if type_only:
                    lines.append(f"    - **Type-Only Imports**: {type_only} imports")
                if isinstance(perf, dict):
                    backend = perf.get("backend")
                    mode = perf.get("scan_mode")
                    files_per_second = perf.get("files_per_second")
                    total_seconds = (
                        perf.get("timings", {}).get("total_seconds")
                        if isinstance(perf.get("timings"), dict)
                        else None
                    )
                    if backend:
                        lines.append(f"    - **Backend**: {backend}")
                    if mode:
                        lines.append(f"    - **Scan Mode**: {mode}")
                    if isinstance(files_per_second, (int, float)):
                        lines.append(
                            f"    - **Throughput**: {float(files_per_second):.2f} files/sec"
                        )
                    if isinstance(total_seconds, (int, float)):
                        lines.append(
                            f"    - **Scan Time**: {float(total_seconds):.2f}s"
                        )

                # Add top files with unused imports
                from collections import defaultdict

                file_counts = defaultdict(int)

                # First, try to get file counts from the tool's JSON output (most current)
                if unused_imports_data and isinstance(unused_imports_data, dict):
                    files_dict = unused_imports_data.get("files", {})
                    if isinstance(files_dict, dict):
                        for file_path_str, count in files_dict.items():
                            if isinstance(file_path_str, str) and isinstance(
                                count, (int, float)
                            ):
                                # CRITICAL: Filter out files that no longer exist
                                try:
                                    file_path = self.project_root / file_path_str
                                    if file_path.exists():
                                        file_counts[file_path_str] = int(count)
                                    # If file doesn't exist, skip it
                                except (OSError, ValueError):
                                    # Error checking file, skip it
                                    pass

                # Fallback to cache file if no data from JSON output
                if not file_counts:
                    try:
                        from ..output_storage import load_tool_cache

                        cache_data = load_tool_cache(
                            "analyze_unused_imports",
                            "imports",
                            project_root=self.project_root,
                        )
                        if cache_data:
                            # CRITICAL: Filter out entries for files that no longer exist
                            for file_path_str, file_data in cache_data.items():
                                if isinstance(file_data, dict):
                                    # Check if file still exists
                                    try:
                                        file_path = self.project_root / file_path_str
                                        if file_path.exists():
                                            # Verify mtime matches (file hasn't been modified)
                                            cached_mtime = file_data.get("mtime")
                                            if cached_mtime is not None:
                                                current_mtime = (
                                                    file_path.stat().st_mtime
                                                )
                                                if current_mtime == cached_mtime:
                                                    results = file_data.get(
                                                        "results", []
                                                    )
                                                    if (
                                                        isinstance(results, list)
                                                        and len(results) > 0
                                                    ):
                                                        file_counts[file_path_str] = (
                                                            len(results)
                                                        )
                                            else:
                                                # No mtime in cache, include it
                                                results = file_data.get("results", [])
                                                if (
                                                    isinstance(results, list)
                                                    and len(results) > 0
                                                ):
                                                    file_counts[file_path_str] = len(
                                                        results
                                                    )
                                        # If file doesn't exist, skip it (don't count deleted files)
                                    except (OSError, ValueError):
                                        # File doesn't exist or error checking, skip it
                                        pass
                    except Exception:
                        pass

                if file_counts:
                    sorted_files = sorted(
                        file_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    file_list = [
                        f"{Path(f).name} ({count})" for f, count in sorted_files
                    ]
                    if unused_imports_data and isinstance(unused_imports_data, dict):
                        summary = unused_imports_data.get("summary", {})
                        total_files_with_issues = summary.get("files_affected", 0)
                    else:
                        total_files_with_issues = len(file_counts)
                    if total_files_with_issues > 5:
                        file_list.append(f"... +{total_files_with_issues - 5}")
                    lines.append(f"    - **Top files**: {', '.join(file_list)}")

                report_path = (
                    self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
                )
                if isinstance(report_path, Path) and report_path.exists():
                    href = self._markdown_href_from_dev_tools_report(report_path)
                    lines.append(
                        f"- **Detailed Report**: [UNUSED_IMPORTS_REPORT.md]({href})"
                    )
            else:
                lines.append("- **Unused Imports**: CLEAN (no unused imports detected)")
        else:
            lines.append(
                "- **Unused Imports**: Data unavailable (run `audit --full` for latest scan)"
            )

        lines.append("")

        # Static Analysis
        lines.append("## Static Analysis")
        if isinstance(static_analysis, dict):
            ruff_data = static_analysis.get("analyze_ruff", {})
            pyright_data = static_analysis.get("analyze_pyright", {})
            bandit_data = static_analysis.get("analyze_bandit", {})
            pip_audit_data = static_analysis.get("analyze_pip_audit", {})
            ruff_summary = (
                ruff_data.get("summary", {}) if isinstance(ruff_data, dict) else {}
            )
            pyright_summary = (
                pyright_data.get("summary", {}) if isinstance(pyright_data, dict) else {}
            )
            bandit_summary = (
                bandit_data.get("summary", {}) if isinstance(bandit_data, dict) else {}
            )
            pip_audit_summary = (
                pip_audit_data.get("summary", {})
                if isinstance(pip_audit_data, dict)
                else {}
            )
            ruff_details = (
                ruff_data.get("details", {}) if isinstance(ruff_data, dict) else {}
            )
            pyright_details = (
                pyright_data.get("details", {}) if isinstance(pyright_data, dict) else {}
            )
            bandit_details = (
                bandit_data.get("details", {}) if isinstance(bandit_data, dict) else {}
            )
            pip_audit_details = (
                pip_audit_data.get("details", {})
                if isinstance(pip_audit_data, dict)
                else {}
            )
            ruff_available = bool(ruff_data.get("available", False))
            pyright_available = bool(pyright_data.get("available", False))
            bandit_available = bool(bandit_data.get("available", False))
            pip_audit_available = bool(pip_audit_data.get("available", False))
            lines.append(
                f"- **Ruff**: {ruff_summary.get('status', 'UNKNOWN')} "
                f"({to_int(ruff_summary.get('total_issues')) or 0} issue(s), "
                f"{to_int(ruff_summary.get('files_affected')) or 0} file(s))"
            )
            lines.append(
                f"- **Pyright**: {pyright_summary.get('status', 'UNKNOWN')} "
                f"({to_int(pyright_details.get('errors')) or 0} error(s), "
                f"{to_int(pyright_details.get('warnings')) or 0} warning(s))"
            )
            lines.append(
                f"- **Bandit**: {bandit_summary.get('status', 'UNKNOWN')} "
                f"({to_int(bandit_summary.get('total_issues')) or 0} MEDIUM/HIGH issue(s), "
                f"{to_int(bandit_summary.get('files_affected')) or 0} file(s))"
            )
            lines.append(
                f"- **pip-audit**: {pip_audit_summary.get('status', 'UNKNOWN')} "
                f"({to_int(pip_audit_summary.get('total_issues')) or 0} vulnerability finding(s), "
                f"{to_int(pip_audit_summary.get('files_affected')) or 0} package(s))"
                f"{self._pip_audit_elapsed_suffix(pip_audit_details)}"
            )
            if not ruff_available:
                message = str(ruff_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Ruff unavailable: {message}")
            elif isinstance(ruff_details.get("top_rules"), list):
                named_rules = []
                for item in (ruff_details.get("top_rules") or [])[:5]:
                    if not isinstance(item, dict):
                        continue
                    code = str(item.get("code", "")).strip()
                    name = str(item.get("name", "")).strip()
                    count = to_int(item.get("count")) or 0
                    if not code:
                        continue
                    if name:
                        named_rules.append(f"{code} {name} ({count})")
                    else:
                        named_rules.append(f"{code} ({count})")
                if named_rules:
                    lines.append(f"  - Top Ruff Rules: {', '.join(named_rules)}")
            elif isinstance(ruff_details.get("violations_by_rule"), dict):
                top_rules = list((ruff_details.get("violations_by_rule") or {}).items())[:5]
                if top_rules:
                    rule_text = ", ".join(f"{rule} ({count})" for rule, count in top_rules)
                    lines.append(f"  - Top Ruff Rules: {rule_text}")
            if not pyright_available:
                message = str(pyright_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Pyright unavailable: {message}")
            if not bandit_available:
                message = str(bandit_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - Bandit unavailable: {message}")
            elif bandit_available and isinstance(bandit_details.get("top_files"), list):
                top_b = (bandit_details.get("top_files") or [])[:5]
                if top_b:
                    file_text = ", ".join(
                        f"{Path(str(item.get('file', 'unknown'))).name} ({to_int(item.get('count')) or 0})"
                        for item in top_b
                        if isinstance(item, dict)
                    )
                    if file_text:
                        lines.append(f"  - Top Bandit Files: {file_text}")
            if not pip_audit_available:
                message = str(pip_audit_details.get("message", "")).strip()
                if message:
                    lines.append(f"  - pip-audit unavailable: {message}")
            elif isinstance(pip_audit_details.get("vulnerable_packages"), list):
                pkgs = (pip_audit_details.get("vulnerable_packages") or [])[:5]
                if pkgs:
                    pkg_text = ", ".join(
                        f"{str(item.get('name', ''))} ({to_int(item.get('vuln_count')) or 0})"
                        for item in pkgs
                        if isinstance(item, dict)
                    )
                    if pkg_text:
                        lines.append(f"  - Top pip-audit packages: {pkg_text}")
            if pyright_available and (
                isinstance(pyright_details.get("top_error_files"), list)
                or isinstance(pyright_details.get("top_warning_files"), list)
            ):
                if (to_int(pyright_details.get("errors")) or 0) > 0:
                    top_error_files = pyright_details.get("top_error_files", [])[:5]
                    if isinstance(top_error_files, list):
                        file_text = ", ".join(
                            f"{Path(str(item.get('file', 'unknown'))).name} ({to_int(item.get('count')) or 0})"
                            for item in top_error_files
                            if isinstance(item, dict)
                        )
                        if file_text:
                            lines.append(f"  - Top Pyright Error Files: {file_text}")
                if (to_int(pyright_details.get("warnings")) or 0) > 0:
                    top_warning_files = pyright_details.get("top_warning_files", [])[:5]
                    if isinstance(top_warning_files, list):
                        file_text = ", ".join(
                            f"{Path(str(item.get('file', 'unknown'))).name} ({to_int(item.get('count')) or 0})"
                            for item in top_warning_files
                            if isinstance(item, dict)
                        )
                        if file_text:
                            lines.append(f"  - Top Pyright Warning Files: {file_text}")
            elif pyright_available and isinstance(pyright_details.get("top_files"), list):
                top_files = pyright_details.get("top_files", [])[:5]
                if top_files:
                    file_text = ", ".join(
                        f"{Path(str(item.get('file', 'unknown'))).name} ({to_int(item.get('count')) or 0})"
                        for item in top_files
                        if isinstance(item, dict)
                    )
                    if file_text:
                        lines.append(f"  - Top Pyright Files: {file_text}")
        else:
            lines.append(
                "- Static analysis data unavailable (run `audit --full` for latest diagnostics)"
            )

        lines.append("")

        # Legacy References
        lines.append("## Legacy References")

        legacy_summary = legacy_summary or legacy_data or {}
        if (
            legacy_summary
            and "summary" in legacy_summary
            and isinstance(legacy_summary.get("summary"), dict)
        ):
            legacy_issues = legacy_summary["summary"].get("files_affected", 0)
            details = legacy_summary.get("details", {})
            legacy_markers = details.get("legacy_markers", 0)
            findings = details.get("findings", {})
            report_path = details.get("report_path")

            if legacy_issues is not None:
                lines.append(f"- **Files with Legacy Markers**: {legacy_issues}")
            else:
                lines.append("- **Files with Legacy Markers**: Unknown")

            if legacy_markers is not None:
                lines.append(f"- **Markers Found**: {legacy_markers}")
            else:
                lines.append("- **Markers Found**: Unknown")

            if findings and isinstance(findings, dict):
                from collections import defaultdict

                file_counts = defaultdict(int)
                for _pattern_type, file_list in findings.items():
                    for file_entry in file_list:
                        if isinstance(file_entry, list) and len(file_entry) >= 3:
                            file_path = file_entry[0]
                            matches = file_entry[2]
                            if isinstance(matches, list):
                                file_counts[file_path] += len(matches)
                            else:
                                file_counts[file_path] += 1

                if file_counts:
                    sorted_files = sorted(
                        file_counts.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    file_list = [
                        f"{Path(f).name} ({count})" for f, count in sorted_files
                    ]
                    if len(file_counts) > 5:
                        file_list.append(f"... +{len(file_counts) - 5}")
                    lines.append(f"    - **Top files**: {', '.join(file_list)}")

            if report_path:
                report_path_obj = self._resolve_report_path(report_path)
                if report_path_obj.exists():
                    href = self._markdown_href_from_dev_tools_report(report_path_obj)
                    lines.append(
                        f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({href})"
                    )
        else:
            lines.append(
                "- **Files with Legacy Markers**: Data unavailable (run `audit --full` for latest scan)"
            )
            lines.append("- **Markers Found**: Data unavailable")
            legacy_report = (
                self.project_root / "development_docs" / "LEGACY_REFERENCE_REPORT.md"
            )
            if legacy_report.exists():
                href = self._markdown_href_from_dev_tools_report(legacy_report)
                lines.append(
                    f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({href})"
                )

        lines.append("")

        # Complexity & Refactoring
        lines.append("## Complexity & Refactoring")

        function_metrics_details = (
            function_metrics.get("details", {})
            if isinstance(function_metrics, dict)
            else {}
        )

        def get_function_field(field_name, default=None):
            return function_metrics_details.get(field_name, default)

        # Try to load complexity from decision_support if analyze_functions doesn't have it
        decision_metrics = self._get_decision_support_details(
            getattr(self, "results_cache", {}).get("decision_support")
        )
        # If not in cache, try loading from decision_support tool data
        if not decision_metrics:
            decision_data = self._load_tool_data(
                "decision_support", "functions", log_source=False
            )
            if decision_data and isinstance(decision_data, dict):
                decision_metrics = self._get_decision_support_details(decision_data)

        high_complexity = get_function_field("high_complexity")
        if high_complexity == "Unknown" or high_complexity is None:
            if decision_metrics:
                high_complexity = decision_metrics.get("high_complexity", "Unknown")
                critical_complexity = decision_metrics.get(
                    "critical_complexity", "Unknown"
                )
                moderate_complexity = decision_metrics.get(
                    "moderate_complexity", "Unknown"
                )
                function_metrics_details["high_complexity"] = high_complexity
                function_metrics_details["critical_complexity"] = critical_complexity
                function_metrics_details["moderate_complexity"] = moderate_complexity

        # If still unknown, try loading from cache
        if high_complexity == "Unknown" or high_complexity is None:
            try:
                cached_data = self._load_results_file_safe()
                if (
                    cached_data
                    and "results" in cached_data
                    and "analyze_functions" in cached_data["results"]
                ):
                    func_data = cached_data["results"]["analyze_functions"]
                    if "data" in func_data:
                        cached_metrics = func_data["data"]
                        function_metrics_details["high_complexity"] = (
                            cached_metrics.get("high_complexity", "Unknown")
                        )
                        function_metrics_details["critical_complexity"] = (
                            cached_metrics.get("critical_complexity", "Unknown")
                        )
                        function_metrics_details["moderate_complexity"] = (
                            cached_metrics.get("moderate_complexity", "Unknown")
                        )
                        if "critical_complexity_examples" in cached_metrics:
                            function_metrics_details["critical_complexity_examples"] = (
                                cached_metrics.get("critical_complexity_examples", [])
                            )
                        if "high_complexity_examples" in cached_metrics:
                            function_metrics_details["high_complexity_examples"] = (
                                cached_metrics.get("high_complexity_examples", [])
                            )
                if (
                    cached_data
                    and function_metrics.get("high_complexity") == "Unknown"
                    and "results" in cached_data
                    and "decision_support" in cached_data["results"]
                ):
                    ds_data = cached_data["results"]["decision_support"]
                    ds_metrics = self._get_decision_support_details(
                        ds_data.get("data") if isinstance(ds_data, dict) else None
                    )
                    if ds_metrics:
                        function_metrics_details["high_complexity"] = ds_metrics.get(
                            "high_complexity", "Unknown"
                        )
                        function_metrics_details["critical_complexity"] = (
                            ds_metrics.get("critical_complexity", "Unknown")
                        )
                        function_metrics_details["moderate_complexity"] = (
                            ds_metrics.get("moderate_complexity", "Unknown")
                        )
                        if "critical_complexity_examples" in ds_metrics:
                            function_metrics_details["critical_complexity_examples"] = (
                                ds_metrics.get("critical_complexity_examples", [])
                            )
                        if "high_complexity_examples" in ds_metrics:
                            function_metrics_details["high_complexity_examples"] = (
                                ds_metrics.get("high_complexity_examples", [])
                            )
            except Exception:
                pass

        lines.append(
            f"- **Critical Complexity Functions**: {get_function_field('critical_complexity', 'Unknown')}"
        )
        lines.append(
            f"- **High Complexity Functions**: {get_function_field('high_complexity', 'Unknown')}"
        )
        lines.append(
            f"- **Moderate Complexity Functions**: {get_function_field('moderate_complexity', 'Unknown')}"
        )

        # Add highest complexity functions list
        critical_examples = get_function_field("critical_complexity_examples", [])
        high_examples = get_function_field("high_complexity_examples", [])

        # Try loading from decision_support (standard format)
        if decision_metrics:
            if (
                not critical_examples
                and "critical_complexity_examples" in decision_metrics
            ):
                critical_examples = decision_metrics.get(
                    "critical_complexity_examples", []
                )
            if not high_examples and "high_complexity_examples" in decision_metrics:
                high_examples = decision_metrics.get("high_complexity_examples", [])

        # If still missing examples, try loading from decision_support tool data (may be cached)
        if not critical_examples or not high_examples:
            decision_data = self._load_tool_data(
                "decision_support", "functions", log_source=False
            )
            if decision_data and isinstance(decision_data, dict):
                decision_metrics_from_tool = self._get_decision_support_details(
                    decision_data
                )
                if decision_metrics_from_tool:
                    decision_metrics = decision_metrics_from_tool
                    if (
                        not critical_examples
                        and "critical_complexity_examples" in decision_metrics_from_tool
                    ):
                        critical_examples = decision_metrics_from_tool.get(
                            "critical_complexity_examples", []
                        )
                    if (
                        not high_examples
                        and "high_complexity_examples" in decision_metrics_from_tool
                    ):
                        high_examples = decision_metrics_from_tool.get(
                            "high_complexity_examples", []
                        )

        if not critical_examples and not high_examples:
            func_result = self._load_tool_data(
                "analyze_functions", "functions", log_source=False
            )
            if func_result and isinstance(func_result, dict):
                func_details = func_result.get("details", {})
                if "critical_complexity_examples" in func_details:
                    critical_examples = func_details.get(
                        "critical_complexity_examples", []
                    )
                elif "critical_complexity_examples" in func_result:
                    critical_examples = func_result.get(
                        "critical_complexity_examples", []
                    )
                if "high_complexity_examples" in func_details:
                    high_examples = func_details.get("high_complexity_examples", [])
                elif "high_complexity_examples" in func_result:
                    high_examples = func_result.get("high_complexity_examples", [])
            # Also try loading from decision_support if available
            if not critical_examples or not high_examples:
                decision_data = self._load_tool_data(
                    "decision_support", "functions", log_source=False
                )
                if decision_data and isinstance(decision_data, dict):
                    decision_metrics_from_tool = self._get_decision_support_details(
                        decision_data
                    )
                    if decision_metrics_from_tool:
                        if (
                            not critical_examples
                            and "critical_complexity_examples"
                            in decision_metrics_from_tool
                        ):
                            critical_examples = decision_metrics_from_tool.get(
                                "critical_complexity_examples", []
                            )
                        if (
                            not high_examples
                            and "high_complexity_examples" in decision_metrics_from_tool
                        ):
                            high_examples = decision_metrics_from_tool.get(
                                "high_complexity_examples", []
                            )

        all_examples = []
        for item in critical_examples[:5]:
            if isinstance(item, dict):
                complexity = item.get("complexity", item.get("nodes", 0))
                all_examples.append(
                    {
                        "function": item.get("function", "Unknown"),
                        "file": item.get("file", "Unknown"),
                        "complexity": complexity,
                        "priority": "critical",
                    }
                )

        for item in high_examples[:3]:
            if isinstance(item, dict):
                complexity = item.get("complexity", item.get("nodes", 0))
                all_examples.append(
                    {
                        "function": item.get("function", "Unknown"),
                        "file": item.get("file", "Unknown"),
                        "complexity": complexity,
                        "priority": "high",
                    }
                )

        if all_examples:
            all_examples.sort(key=lambda x: x.get("complexity", 0), reverse=True)
            top_functions = all_examples[:5]
            function_list = []
            for func_info in top_functions:
                func_name = func_info.get("function", "Unknown")
                file_name = Path(func_info.get("file", "Unknown")).name
                complexity = func_info.get("complexity", 0)
                if complexity > 0:
                    function_list.append(
                        f"{func_name} ({file_name}, {complexity} nodes)"
                    )
                else:
                    function_list.append(f"{func_name} ({file_name})")

            if function_list:
                if len(all_examples) > 5:
                    function_list.append(f"... +{len(all_examples) - 5} more")
                lines.append(f"- **Top functions**: {', '.join(function_list)}")
        else:
            # If no examples found, try one more time to load from analyze_functions directly
            func_result = self._load_tool_data(
                "analyze_functions", "functions", log_source=False
            )
            if func_result and isinstance(func_result, dict):
                func_details = func_result.get("details", {})
                # Try to extract from function analysis results
                if "functions" in func_details:
                    functions_list = func_details.get("functions", [])
                    if isinstance(functions_list, list):
                        # Find highest complexity functions
                        complex_funcs = []
                        for func in functions_list:
                            if isinstance(func, dict):
                                complexity = func.get(
                                    "complexity", func.get("nodes", 0)
                                )
                                if (
                                    complexity and complexity > 199
                                ):  # Critical complexity
                                    complex_funcs.append(
                                        {
                                            "function": func.get("name", "Unknown"),
                                            "file": func.get("file", "Unknown"),
                                            "complexity": complexity,
                                        }
                                    )
                        if complex_funcs:
                            complex_funcs.sort(
                                key=lambda x: x.get("complexity", 0), reverse=True
                            )
                            top_funcs = complex_funcs[:5]
                            function_list = []
                            for func_info in top_funcs:
                                func_name = func_info.get("function", "Unknown")
                                file_name = Path(func_info.get("file", "Unknown")).name
                                complexity = func_info.get("complexity", 0)
                                function_list.append(
                                    f"{func_name} ({file_name}, {complexity} nodes)"
                                )
                            if function_list:
                                lines.append(
                                    f"- **Top functions**: {', '.join(function_list)}"
                                )

        lines.append("")

        # Function Patterns
        lines.append("## Function Patterns")

        # Registry Gaps
        if missing_docs_count > 0:
            lines.append(
                f"- **Registry Gaps**: {missing_docs_count} items missing from registry"
            )
            if missing_docs_list and isinstance(missing_docs_list, dict):
                sorted_files = sorted(
                    missing_docs_list.items(),
                    key=lambda x: len(x[1]) if isinstance(x[1], list) else 1,
                    reverse=True,
                )[:5]
                if sorted_files:
                    item_list = []
                    for file_path, funcs in sorted_files:
                        func_count = len(funcs) if isinstance(funcs, list) else 1
                        file_name = Path(file_path).name if file_path else "Unknown"
                        if func_count == 1 and isinstance(funcs, list) and funcs:
                            func_name = funcs[0] if funcs else "Unknown"
                            item_list.append(f"{func_name} ({file_name})")
                        else:
                            item_list.append(f"{file_name} ({func_count} functions)")
                    if len(sorted_files) < len(missing_docs_list):
                        total_files = len(missing_docs_list)
                        item_list.append(f"... +{total_files - len(sorted_files)} more")
                    if item_list:
                        lines.append(f"    - **Top items**: {', '.join(item_list)}")
        else:
            lines.append("- **Registry Gaps**: 0 items missing from registry")

        # Function Docstring Coverage
        if not func_undocumented and total_funcs and doc_coverage:
            doc_coverage_float: float | None = None
            if isinstance(doc_coverage, str):
                raw = doc_coverage.replace("%", "").strip()
                try:
                    doc_coverage_float = float(raw)
                except ValueError:
                    doc_coverage_float = None
            elif isinstance(doc_coverage, (int, float)):
                doc_coverage_float = float(doc_coverage)
            if (
                doc_coverage_float is not None
                and doc_coverage_float < 100
                and total_funcs
            ):
                func_undocumented = int(total_funcs * (100 - doc_coverage_float) / 100)

        lines.append(
            f"- **Function Docstring Coverage**: {percent_text(doc_coverage, 2)}"
        )
        if func_undocumented and func_undocumented > 0:
            lines.append(
                f"   - **Functions Missing Docstrings**: {func_undocumented} functions need docstrings"
            )
            undocumented_examples = get_function_field("undocumented_examples", [])
            if not undocumented_examples or len(undocumented_examples) == 0:
                function_data_for_consolidated = self._load_tool_data(
                    "analyze_functions", "functions"
                )
                if isinstance(function_data_for_consolidated, dict):
                    func_details_for_consolidated = function_data_for_consolidated.get(
                        "details", {}
                    )
                    undocumented_examples = (
                        func_details_for_consolidated.get("undocumented_examples")
                        or function_data_for_consolidated.get("undocumented_examples")
                        or []
                    )

            if (
                undocumented_examples
                and isinstance(undocumented_examples, list)
                and len(undocumented_examples) > 0
            ):
                sorted_undoc = sorted(
                    undocumented_examples,
                    key=lambda x: x.get("complexity", 0) if isinstance(x, dict) else 0,
                    reverse=True,
                )[:5]
                func_list = []
                for item in sorted_undoc:
                    if isinstance(item, dict):
                        func_name = item.get("function", item.get("name", "unknown"))
                        file_path = item.get("file", "")
                        if file_path:
                            file_name = Path(file_path).name
                            func_list.append(f"{func_name} ({file_name})")
                        else:
                            func_list.append(func_name)
                    else:
                        func_list.append(str(item))
                total_undoc_count = (
                    func_undocumented
                    if func_undocumented
                    else len(undocumented_examples)
                )
                if total_undoc_count > 5:
                    func_list.append(f"... +{total_undoc_count - 5} more")
                if func_list:
                    lines.append(f"   - **Top functions**: {', '.join(func_list)}")
        else:
            lines.append(
                "   - **Functions Missing Docstrings**: 0 functions need docstrings"
            )

        # Handler Classes Docstring Coverage
        if function_patterns_data_for_report and isinstance(
            function_patterns_data_for_report, dict
        ):
            if "details" in function_patterns_data_for_report:
                handlers = function_patterns_data_for_report["details"].get(
                    "handlers", []
                )
            else:
                handlers = function_patterns_data_for_report.get("handlers", [])

            if handlers:
                handlers_no_doc = [h for h in handlers if not h.get("has_doc", True)]
                handler_classes_total = len(handlers)
                handler_classes_no_doc = len(handlers_no_doc)

                if handler_classes_total > 0:
                    handler_coverage_pct = (
                        (handler_classes_total - handler_classes_no_doc)
                        / handler_classes_total
                    ) * 100
                    lines.append(
                        f"- **Handler Classes Docstring Coverage**: {percent_text(handler_coverage_pct, 0)}"
                    )

                    if handlers_no_doc:
                        lines.append(
                            f"   - **Handler Classes Without Class Docstrings**: {handler_classes_no_doc} of {handler_classes_total} handler classes"
                        )
                        top_handlers = sorted(
                            handlers_no_doc,
                            key=lambda x: x.get("methods", 0),
                            reverse=True,
                        )[:5]
                        handler_list = [
                            f"{h.get('class', 'Unknown')} ({Path(h.get('file', '')).name}, {h.get('methods', 0)} methods)"
                            for h in top_handlers
                        ]
                        if len(handlers_no_doc) > 5:
                            handler_list.append(f"... +{len(handlers_no_doc) - 5} more")
                        lines.append(
                            f"    - **Top handlers**: {', '.join(handler_list)}"
                        )
                    else:
                        lines.append(
                            f"   - **Handler Classes Without Class Docstrings**: 0 of {handler_classes_total} handler classes (all have class docstrings)"
                        )

        # Duplicate Functions
        duplicate_data = self._load_tool_data(
            "analyze_duplicate_functions", "functions"
        )
        duplicate_summary = (
            duplicate_data.get("summary", {})
            if isinstance(duplicate_data, dict)
            else {}
        )
        duplicate_details = (
            duplicate_data.get("details", {})
            if isinstance(duplicate_data, dict)
            else {}
        )
        duplicate_groups = to_int(duplicate_summary.get("total_issues")) or 0
        duplicate_files = to_int(duplicate_summary.get("files_affected")) or 0
        if duplicate_files == 0 and isinstance(duplicate_details, dict):
            duplicate_groups_list = duplicate_details.get("duplicate_groups", [])
            if isinstance(duplicate_groups_list, list) and duplicate_groups_list:
                duplicate_files = self._count_duplicate_affected_files(
                    duplicate_groups_list
                )
        dup_capped_cr = isinstance(duplicate_details, dict) and duplicate_details.get(
            "groups_capped", False
        )
        groups_label_cr = (
            f"at least {duplicate_groups}" if dup_capped_cr else str(duplicate_groups)
        )
        lines.append(
            f"- **Duplicate Function Groups**: {groups_label_cr} groups across {duplicate_files} files"
        )
        if isinstance(duplicate_details, dict):
            cache_stats = duplicate_details.get("cache", {})
            if isinstance(cache_stats, dict):
                total_files = cache_stats.get("total_files", 0) or 0
                cache_stats.get("cached_files", 0) or 0
                cache_stats.get("scanned_files", 0) or 0
        if duplicate_groups > 0 and isinstance(duplicate_details, dict):
            groups = duplicate_details.get("duplicate_groups", [])
            if isinstance(groups, list) and groups:

                def group_sort_key(item):
                    funcs = item.get("functions", []) if isinstance(item, dict) else []
                    func_count = len(funcs) if isinstance(funcs, list) else 0
                    similarity_range = (
                        item.get("similarity_range", {})
                        if isinstance(item, dict)
                        else {}
                    )
                    max_score = similarity_range.get("max", 0)
                    return (max_score, func_count)

                sorted_groups = sorted(groups, key=group_sort_key, reverse=True)[:3]
                group_items = []
                for group in sorted_groups:
                    funcs = (
                        group.get("functions", []) if isinstance(group, dict) else []
                    )
                    func_count = len(funcs) if isinstance(funcs, list) else 0
                    similarity_range = (
                        group.get("similarity_range", {})
                        if isinstance(group, dict)
                        else {}
                    )
                    max_score = similarity_range.get("max", 0)
                    func_items = []
                    if isinstance(funcs, list):
                        for func in funcs[:3]:
                            if isinstance(func, dict):
                                func_name = func.get("full_name") or func.get(
                                    "name", "unknown"
                                )
                                file_path = func.get("file", "")
                                file_name = (
                                    Path(file_path).name if file_path else "Unknown"
                                )
                                func_items.append(f"{func_name} ({file_name})")
                            else:
                                func_items.append(str(func))
                    if func_count > 3:
                        func_items.append(f"... +{func_count - 3} more")
                    group_items.append(
                        f"{', '.join(func_items)} (max score {max_score})"
                    )
                if group_items:
                    lines.append(f"   - **Top groups**: {', '.join(group_items)}")
            max_groups = to_int(duplicate_details.get("max_groups")) or 0
            max_pairs = to_int(duplicate_details.get("max_pairs")) or 0
            groups_reported = to_int(duplicate_details.get("groups_reported")) or 0
            top_pairs = duplicate_details.get("top_pairs", [])
            cap_notes = []
            if max_groups or max_pairs:
                limits = []
                if max_groups:
                    limits.append(f"max_groups={max_groups}")
                if max_pairs:
                    limits.append(f"max_pairs={max_pairs}")
                lines.append(f"   - **Configured limits**: {', '.join(limits)}")
            if max_groups and groups_reported >= max_groups:
                cap_notes.append(f"groups capped at {max_groups}")
            if (
                max_pairs
                and isinstance(top_pairs, list)
                and len(top_pairs) >= max_pairs
            ):
                cap_notes.append(f"pairs capped at {max_pairs}")
            if duplicate_details.get("candidate_pair_cap_reached"):
                cap_notes.append("candidate pair cap reached")
            if cap_notes:
                lines.append(
                    f"   - **Output limits**: {', '.join(cap_notes)} (increase config to see more)"
                )
            if duplicate_details.get("consider_body_similarity_used"):
                body_pairs = duplicate_details.get("body_candidate_pairs_considered", 0)
                lines.append(
                    f"   - **Body/structural similarity**: enabled ({body_pairs} body candidate pairs considered)"
                )

        lines.append("")
        # Module Refactor Candidates
        refactor_data_cr = self._load_tool_data(
            "analyze_module_refactor_candidates", "functions"
        )
        refactor_summary_cr = (
            refactor_data_cr.get("summary", {})
            if isinstance(refactor_data_cr, dict)
            else {}
        )
        refactor_details_cr = (
            refactor_data_cr.get("details", {})
            if isinstance(refactor_data_cr, dict)
            else {}
        )
        refactor_cand_count = to_int(refactor_summary_cr.get("total_issues")) or 0
        lines.append(
            f"- **Module Refactor Candidates**: {refactor_cand_count} large/high-complexity module(s)"
        )
        if refactor_cand_count > 0 and isinstance(refactor_details_cr, dict):
            candidates_cr = refactor_details_cr.get("refactor_candidates", [])
            if isinstance(candidates_cr, list) and candidates_cr:
                top_refactor = [
                    f"{c.get('file', '?')} (lines={c.get('lines', 0)}, total_function_complexity={c.get('total_function_complexity', c.get('total_complexity', 0))})"
                    for c in candidates_cr[:3]
                    if isinstance(c, dict)
                ]
                if top_refactor:
                    lines.append(
                        f"   - **Top 3 candidates**: {', '.join(top_refactor)}"
                    )
                lines.append(
                    "   - **Full list**: development_tools/functions/jsons/analyze_module_refactor_candidates_results.json"
                )

        lines.append("")

        # Module Imports
        module_imports_data = self._load_tool_data("analyze_module_imports", "imports")
        if module_imports_data and isinstance(module_imports_data, dict):
            details = module_imports_data.get("details", {})
            import_data = details.get("data", details) if "data" in details else details
            if not import_data or (
                isinstance(import_data, dict) and len(import_data) == 0
            ):
                import_data = module_imports_data.get("data", module_imports_data)

            if isinstance(import_data, dict):
                total_files = len(import_data)
                total_imports = sum(
                    v.get("total_imports", 0) if isinstance(v, dict) else 0
                    for v in import_data.values()
                )
            else:
                total_files = 0
                total_imports = 0

            if total_files > 0:
                lines.append("## Module Imports")
                lines.append(f"- **Files Analyzed**: {total_files} Python files")
                if total_imports > 0:
                    lines.append(
                        f"- **Total Imports**: {total_imports} import statements"
                    )

        lines.append("")

        # Dependency Patterns
        dependency_patterns_data = self._load_tool_data(
            "analyze_dependency_patterns", "imports"
        )
        if dependency_patterns_data and isinstance(dependency_patterns_data, dict):
            details = dependency_patterns_data.get("details", {})
            patterns_data = (
                details.get("data", details) if "data" in details else details
            )
            if not patterns_data or (
                isinstance(patterns_data, dict) and len(patterns_data) == 0
            ):
                patterns_data = dependency_patterns_data.get(
                    "data", dependency_patterns_data
                )

            if isinstance(patterns_data, dict):
                circular_deps = len(patterns_data.get("circular_dependencies", []))
                high_coupling = len(patterns_data.get("high_coupling", []))
            else:
                circular_deps = 0
                high_coupling = 0

            if circular_deps > 0 or high_coupling > 0:
                lines.append("## Dependency Patterns")
                if self._is_dev_tools_scoped_report():
                    lines.append(
                        "- **Scope**: Import/coupling metrics are for the "
                        "`development_tools/` scan root only."
                    )
                if circular_deps > 0:
                    lines.append(
                        f"- **Circular Dependencies**: {circular_deps} circular dependency chains detected"
                    )
                    circular_dependencies = (
                        patterns_data.get("circular_dependencies", [])
                        if isinstance(patterns_data, dict)
                        else []
                    )
                    if isinstance(circular_dependencies, list):
                        top_circular_chains: list[str] = []
                        for chain in circular_dependencies[:3]:
                            if isinstance(chain, list) and chain:
                                module_names = [
                                    Path(str(module)).name
                                    for module in chain[:4]
                                    if isinstance(module, str)
                                ]
                                if module_names:
                                    top_circular_chains.append(
                                        " -> ".join(module_names)
                                    )
                        if top_circular_chains:
                            lines.append(
                                f"- **Top Circular Chains**: {self._format_list_for_display(top_circular_chains, limit=3)}"
                            )
                if high_coupling > 0:
                    lines.append(
                        f"- **High Coupling**: {high_coupling} modules with high coupling"
                    )
                    high_coupling_modules = (
                        patterns_data.get("high_coupling", [])
                        if isinstance(patterns_data, dict)
                        else []
                    )
                    if isinstance(high_coupling_modules, list):
                        coupling_records = sorted(
                            [
                                item
                                for item in high_coupling_modules
                                if isinstance(item, dict)
                            ],
                            key=lambda item: to_int(item.get("import_count")) or 0,
                            reverse=True,
                        )[:3]
                        top_high_coupling_modules = []
                        for module in coupling_records:
                            module_name = Path(str(module.get("file", "unknown"))).name
                            import_count = to_int(module.get("import_count")) or 0
                            top_high_coupling_modules.append(
                                f"{module_name} ({import_count})"
                            )
                        if top_high_coupling_modules:
                            lines.append(
                                f"- **Top High-Coupling Modules**: {self._format_list_for_display(top_high_coupling_modules, limit=3)}"
                            )
            elif circular_deps == 0 and high_coupling == 0 and patterns_data:
                lines.append("## Dependency Patterns")
                if self._is_dev_tools_scoped_report():
                    lines.append(
                        "- **Scope**: Import/coupling metrics are for the "
                        "`development_tools/` scan root only."
                    )
                lines.append(
                    "- **Status**: CLEAN (no circular dependencies or high coupling detected)"
                )

        # Import Boundary (development_tools portability)
        import_boundary_data = self._load_tool_data(
            "analyze_dev_tools_import_boundaries", "imports"
        )
        if import_boundary_data and isinstance(import_boundary_data, dict):
            ib_summary = import_boundary_data.get("summary", {}) or {}
            ib_violations = to_int(ib_summary.get("total_issues"))
            ib_files = to_int(ib_summary.get("files_affected"))
            lines.append("")
            lines.append("## Import Boundary")
            if ib_violations is not None and ib_violations > 0:
                lines.append(
                    f"- **Violations**: {ib_violations} non-approved core import(s) across {ib_files or 0} file(s)"
                )
                ib_details = import_boundary_data.get("details", {}) or {}
                ib_violations_list = ib_details.get("violations", []) or []
                if ib_violations_list:
                    top_violations = ib_violations_list[:5]
                    for v in top_violations[:3]:
                        if isinstance(v, dict) and v.get("file"):
                            lines.append(f"  - {v['file']}: {v.get('module', '')}")
                lines.append(
                    "- **Action**: Refactor to approved imports only (core.logger); see DEVELOPMENT_TOOLS_GUIDE.md §8.5"
                )
            elif ib_violations == 0:
                lines.append("- **Status**: CLEAN (no boundary violations detected)")
            else:
                lines.append("- **Status**: Data unavailable (run `audit` to scan)")

        # Validation Status
        lines.append("## Validation Status")

        validation_output_for_report = ""
        if hasattr(self, "validation_results") and self.validation_results:
            validation_output_for_report = (
                self.validation_results.get("output", "") or ""
            )

        if not validation_output_for_report or not validation_output_for_report.strip():
            validation_data = self._load_tool_data(
                "analyze_ai_work", "ai_work", log_source=True
            )
            if validation_data:
                validation_output_for_report = validation_data.get("output", "") or ""

        if validation_output_for_report and validation_output_for_report.strip():
            if "POOR" in validation_output_for_report:
                lines.append(
                    "- **AI Work Validation**: POOR - documentation or tests missing"
                )
            elif "GOOD" in validation_output_for_report:
                lines.append("- **AI Work Validation**: GOOD - keep current standards")
            elif (
                "NEEDS ATTENTION" in validation_output_for_report
                or "FAIR" in validation_output_for_report
            ):
                lines.append(
                    "- **AI Work Validation**: NEEDS ATTENTION - structural validation issues detected"
                )
            else:
                lines.append(
                    "- **AI Work Validation**: Status available (see validation output)"
                )
        else:
            # Check if we're in a tier that doesn't run analyze_ai_work (Tier 1)
            tools_run = getattr(self, "_tools_run_in_current_tier", set())
            if "analyze_ai_work" not in tools_run:
                # Try to load cached validation data
                validation_data = self._load_tool_data(
                    "analyze_ai_work", "ai_work", log_source=False
                )
                if validation_data:
                    cached_output = validation_data.get("output", "") or ""
                    if cached_output and cached_output.strip():
                        if "POOR" in cached_output:
                            lines.append(
                                "- **AI Work Validation**: POOR - documentation or tests missing (cached)"
                            )
                        elif "GOOD" in cached_output:
                            lines.append(
                                "- **AI Work Validation**: GOOD - keep current standards (cached)"
                            )
                        elif (
                            "NEEDS ATTENTION" in cached_output
                            or "FAIR" in cached_output
                        ):
                            lines.append(
                                "- **AI Work Validation**: NEEDS ATTENTION - structural validation issues detected (cached)"
                            )
                        else:
                            lines.append(
                                "- **AI Work Validation**: Status available (cached, see validation output)"
                            )
                    else:
                        lines.append(
                            "- **AI Work Validation**: Using cached data (run `audit` or `audit --full` for latest validation)"
                        )
                else:
                    lines.append(
                        "- **AI Work Validation**: Using cached data (run `audit` or `audit --full` for latest validation)"
                    )
            else:
                lines.append(
                    "- **AI Work Validation**: Data unavailable (run `audit --full` for validation)"
                )

        # Config Validation
        config_validation_summary = self._load_config_validation_summary()
        if config_validation_summary:
            config_valid = config_validation_summary.get("config_valid", False)
            config_complete = config_validation_summary.get("config_complete", False)
            config_validation_summary.get("recommendations", [])
            tools_using_config = config_validation_summary.get("tools_using_config", 0)
            total_tools = config_validation_summary.get("total_tools", 0)
            tools_analysis = config_validation_summary.get("tools_analysis", {})

            lines.append("- **Configuration Validation**")
            lines.append(f"  - Config valid: {'Yes' if config_valid else 'No'}")
            lines.append(f"  - Config complete: {'Yes' if config_complete else 'No'}")
            if total_tools > 0:
                lines.append(
                    f"  - Tools using config: {tools_using_config}/{total_tools}"
                )

            missing_import_tools = []
            if tools_analysis and isinstance(tools_analysis, dict):
                for tool_name, tool_data in tools_analysis.items():
                    if isinstance(tool_data, dict):
                        if not tool_data.get("imports_config", True):
                            missing_import_tools.append(tool_name)
                        else:
                            issues = tool_data.get("issues", [])
                            if isinstance(issues, list):
                                for issue in issues:
                                    if (
                                        isinstance(issue, str)
                                        and "import config" in issue.lower()
                                    ):
                                        if tool_name not in missing_import_tools:
                                            missing_import_tools.append(tool_name)
                                        break

            if missing_import_tools:
                lines.append(
                    f"  - Tools missing config module import: {', '.join(missing_import_tools)}"
                )

        lines.append("")

        # Backup Health
        lines.append("## Backup Health")
        if backup_summary:
            backup_status = str(
                backup_summary.get(
                    "status",
                    "PASS" if bool(backup_summary.get("success")) else "FAIL",
                )
            ).upper()
            lines.append(f"- **Status**: {backup_status}")
            passed_checks = backup_summary.get("passed_checks")
            total_checks = backup_summary.get("total_checks")
            if isinstance(passed_checks, int) and isinstance(total_checks, int):
                lines.append(f"- **Checks**: {passed_checks}/{total_checks} passed")
            latest_backup_path = backup_summary.get("latest_backup_path")
            if latest_backup_path:
                lines.append(f"- **Latest Backup Artifact**: `{latest_backup_path}`")
            latest_created_at = backup_summary.get("latest_backup_created_at")
            if latest_created_at:
                lines.append(f"- **Latest Backup Created At**: {latest_created_at}")
            backup_present_status = "UNKNOWN"
            backup_recent_status = "UNKNOWN"
            if isinstance(backup_checks, list):
                for check in backup_checks:
                    if not isinstance(check, dict):
                        continue
                    check_name = str(check.get("name") or "")
                    if check_name in {"backup_present", "weekly_backup_present"}:
                        backup_present_status = (
                            "PASS" if bool(check.get("success")) else "FAIL"
                        )
                    if check_name in {
                        "backups_recent_enough",
                        "weekly_backup_recent_enough",
                    }:
                        backup_recent_status = (
                            "PASS" if bool(check.get("success")) else "FAIL"
                        )
            lines.append(f"- **Weekly Backup Presence**: {backup_present_status}")
            lines.append(f"- **Weekly Backup Recency**: {backup_recent_status}")
            drill_status = "SKIPPED"
            if isinstance(backup_checks, list):
                for check in backup_checks:
                    if isinstance(check, dict) and check.get("name") == "restore_drill":
                        drill_status = "PASS" if bool(check.get("success")) else "FAIL"
                        break
            elif bool(backup_summary.get("drill_executed")):
                drill_status = "UNKNOWN"
            lines.append(f"- **Restore Drill**: {drill_status}")
            if isinstance(backup_checks, list) and backup_checks:
                lines.append("- **Check Details**:")
                for check in backup_checks:
                    if not isinstance(check, dict):
                        continue
                    check_name = str(check.get("name") or "unknown_check")
                    check_status = "PASS" if bool(check.get("success")) else "FAIL"
                    detail_text = ""
                    details = check.get("details")
                    if isinstance(details, dict):
                        if check_name == "inventory_generation":
                            inventory_error = details.get("error")
                            if inventory_error:
                                detail_text = f"error={inventory_error}"
                        elif check_name in {
                            "backup_present",
                            "backups_recent_enough",
                            "weekly_backup_present",
                            "weekly_backup_recent_enough",
                        }:
                            weekly_count = details.get("weekly_backup_count")
                            weekly_created = details.get("latest_weekly_created_at")
                            backup_count = details.get("backup_count")
                            backup_created = details.get("latest_backup_created_at")
                            fragments = []
                            if weekly_count is not None:
                                fragments.append(f"count={weekly_count}")
                            if weekly_created:
                                fragments.append(f"latest={weekly_created}")
                            if backup_count is not None:
                                fragments.append(f"count={backup_count}")
                            if backup_created:
                                fragments.append(f"latest={backup_created}")
                            detail_text = ", ".join(fragments)
                        elif check_name == "backups_discoverable":
                            backup_count = details.get("backup_count")
                            if backup_count is not None:
                                detail_text = f"count={backup_count}"
                        elif check_name == "latest_backup_recent_enough":
                            latest_created = details.get("latest_created_at")
                            if latest_created:
                                detail_text = f"latest={latest_created}"
                        elif check_name == "latest_backup_validates":
                            errors = details.get("errors")
                            if isinstance(errors, list):
                                detail_text = f"errors={len(errors)}"
                        elif check_name == "restore_drill":
                            drill_error = details.get("error")
                            if drill_error:
                                detail_text = f"error={drill_error}"
                            else:
                                detail_text = "isolated restore verification completed"
                    if detail_text:
                        lines.append(
                            f"- `{check_status}` `{check_name}` ({detail_text})"
                        )
                    else:
                        lines.append(f"- `{check_status}` `{check_name}`")
            lines.append(
                "- **Command**: `python development_tools/run_development_tools.py backup verify`"
            )
        else:
            lines.append(
                "- Backup health data unavailable (run `python development_tools/run_development_tools.py backup verify`)"
            )

        lines.append("")

        # System Signals
        lines.append("## System Signals")
        lines.append(
            "- **Scope**: Operational health (audit freshness, test coverage pulse, core files, alerts). "
            "Documentation pairing and sync are under **Documentation Signals**, not duplicated here."
        )

        system_signals_data = None
        if hasattr(self, "system_signals") and self.system_signals:
            system_signals_data = self._get_system_signals_details(self.system_signals)
        else:
            try:
                cached_data = self._load_results_file_safe()
                if cached_data:
                    signals_result = None
                    if "results" in cached_data:
                        if "analyze_system_signals" in cached_data["results"]:
                            signals_result = cached_data["results"][
                                "analyze_system_signals"
                            ]

                    if signals_result and "data" in signals_result:
                        system_signals_data = self._get_system_signals_details(
                            signals_result["data"]
                        )
            except Exception as e:
                logger.debug(f"Failed to load system signals from cache: {e}")

        # Extract system health from system_signals_data
        system_health = None
        if system_signals_data and isinstance(system_signals_data, dict):
            system_health = system_signals_data.get("system_health", {})

        if system_health and isinstance(system_health, dict):
            overall_status = system_health.get("overall_status", "OK")
            lines.append(f"- **System Health**: {overall_status}")

            # Add audit freshness (consolidated - single line, not redundant)
            audit_freshness = system_health.get("audit_freshness")
            if audit_freshness:
                lines.append(f"  - Audit data: {audit_freshness}")

            # Add test coverage status if available
            test_coverage_status = system_health.get("test_coverage_status")
            if test_coverage_status and test_coverage_status != "Unknown":
                lines.append(f"  - Test coverage: {test_coverage_status}")

            # Documentation sync status is shown in Documentation Signals section, not here

            # Show actual warnings/critical issues with details (not just counts)
            severity_levels = system_health.get("severity_levels", {})
            if severity_levels:
                critical_issues = severity_levels.get("CRITICAL", [])
                warnings = severity_levels.get("WARNING", [])
                if critical_issues:
                    lines.append(f"  - Critical issues ({len(critical_issues)}):")
                    for issue in critical_issues:
                        lines.append(f"    * {issue}")
                if warnings:
                    lines.append(f"  - Warnings ({len(warnings)}):")
                    for warning in warnings:
                        lines.append(f"    * {warning}")

            # Add recent activity
            recent_activity = (
                system_signals_data.get("recent_activity", {})
                if system_signals_data
                else {}
            )
            recent_changes = (
                recent_activity.get("recent_changes") or []
                if isinstance(recent_activity, dict)
                else []
            )
            if recent_changes and isinstance(recent_changes, list):
                changes_str = self._format_list_for_display(recent_changes, limit=3)
                lines.append(f"- **Recent Changes**: {changes_str}")
        else:
            lines.append("- **System Health**: OK (data unavailable)")
            lines.append(
                "- **Recent Changes**: Data unavailable (run `system-signals` command)"
            )

        lines.append("")
        self._append_tier3_test_outcome_lines(lines)

        # Reference Files
        lines.append("## Reference Files")

        # Get status file paths from config for links
        try:
            from ... import config

            status_config = config.get_status_config()
            status_files_config = status_config.get("status_files", {})
            ai_status_path = status_files_config.get(
                "ai_status", "development_tools/AI_STATUS.md"
            )
            ai_priorities_path = status_files_config.get(
                "ai_priorities", "development_tools/AI_PRIORITIES.md"
            )
        except (ImportError, AttributeError, KeyError):
            ai_status_path = "development_tools/AI_STATUS.md"
            ai_priorities_path = "development_tools/AI_PRIORITIES.md"

        if self._is_dev_tools_scoped_report():
            lines.append(
                f"- Full-repo status (not produced by this run): [AI_STATUS.md]({self._markdown_href_from_dev_tools_report(self.project_root / ai_status_path)})"
            )
            lines.append(
                f"- Scoped priorities from this run: [DEV_TOOLS_PRIORITIES.md]({self._markdown_href_from_dev_tools_report(self.project_root / 'development_tools' / 'DEV_TOOLS_PRIORITIES.md')})"
            )
            lines.append(
                f"- Full-repo priorities: [AI_PRIORITIES.md]({self._markdown_href_from_dev_tools_report(self.project_root / ai_priorities_path)})"
            )
        else:
            lines.append(
                f"- Latest AI status: [AI_STATUS.md]({self._markdown_href_from_dev_tools_report(self.project_root / ai_status_path)})"
            )
            lines.append(
                f"- Current AI priorities: [AI_PRIORITIES.md]({self._markdown_href_from_dev_tools_report(self.project_root / ai_priorities_path)})"
            )
        lines.append(
            f"- Detailed JSON results: [analysis_detailed_results.json]({self._markdown_href_from_dev_tools_report(self._get_results_file_path())})"
        )

        legacy_report = (
            self.project_root / "development_docs" / "LEGACY_REFERENCE_REPORT.md"
        )
        if legacy_report.exists():
            href = self._markdown_href_from_dev_tools_report(legacy_report)
            lines.append(
                f"- Legacy reference report: [LEGACY_REFERENCE_REPORT.md]({href})"
            )

        coverage_report = (
            self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
        )
        if coverage_report.exists():
            href = self._markdown_href_from_dev_tools_report(coverage_report)
            lines.append(
                f"- Test coverage report: [TEST_COVERAGE_REPORT.md]({href})"
            )

        unused_imports_report = (
            self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
        )
        if unused_imports_report.exists():
            href = self._markdown_href_from_dev_tools_report(unused_imports_report)
            lines.append(
                f"- Unused imports detail: [UNUSED_IMPORTS_REPORT.md]({href})"
            )

        archive_dir = self.project_root / "development_tools" / "reports" / "archive"
        if archive_dir.exists():
            lines.append("- Historical audit data: development_tools/reports/archive")

        lines.append("")

        return "\n".join(lines)

    def _identify_critical_issues(self) -> list[str]:
        """Identify critical issues from audit results"""
        issues = []
        if "analyze_functions" in self.results_cache:
            metrics = self.results_cache["analyze_functions"]
            if "coverage" in metrics:
                try:
                    coverage = float(metrics["coverage"].replace("%", ""))
                    if coverage < 90:
                        issues.append(f"Low documentation coverage: {coverage}%")
                except Exception:
                    pass
        if hasattr(self, "_last_failed_audits"):
            for audit in self._last_failed_audits:
                issues.append(f"Failed audit: {audit}")
        return issues

    def _generate_action_items(self) -> list[str]:
        """Generate actionable items from audit results"""
        actions = []
        if "analyze_functions" in self.results_cache:
            metrics = self.results_cache["analyze_functions"]
            if "coverage" in metrics:
                try:
                    coverage = float(metrics["coverage"].replace("%", ""))
                    if coverage < 95:
                        actions.append(
                            f"Improve documentation coverage (currently {coverage}%)"
                        )
                except Exception:
                    pass
        if "decision_support" in self.results_cache:
            insights = self.results_cache["decision_support"]
            if isinstance(insights, list) and insights:
                complexity_warnings = [
                    insight for insight in insights if "complexity" in insight.lower()
                ]
                if complexity_warnings:
                    actions.append(
                        "Refactor high complexity functions for maintainability"
                    )
        actions.append("Review TODO.md for next development priorities")
        actions.append("Run comprehensive testing before major changes")
        actions.append(
            "Update AI_CHANGELOG.md and CHANGELOG_DETAIL.md with recent changes"
        )
        return actions
