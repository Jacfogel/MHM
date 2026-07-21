"""
Report generation helpers for AIToolsService.

Document builders live in dedicated mixins (V6 B-015):
``report_generation_ai_status``, ``report_generation_ai_priorities``,
``report_generation_consolidated``. This module keeps shared helpers and composes
those mixins.
"""

# pyright: reportAttributeAccessIssue=false, reportGeneralTypeIssues=false

import os
from pathlib import Path
from typing import Any

from development_tools.shared.logging import get_dev_tools_logger

logger = get_dev_tools_logger("development_tools")

from .report_generation_tier3_helpers import (
    coerce_int as _tier3_coerce_int,
    effective_tier3_state_from_outcome as _tier3_effective_state,
    normalize_test_node_id as _tier3_normalize_test_node_id,
    tier3_outcome_has_run_evidence as _tier3_outcome_has_run_evidence_fn,
    tier3_track_skipped_for_audit_scope as _tier3_track_skipped_fn,
    track_classification_label as _tier3_track_classification_label,
)
from .report_generation_ai_status import AIStatusDocumentMixin
from .report_generation_ai_priorities import AIPrioritiesDocumentMixin
from .report_generation_consolidated import ConsolidatedReportDocumentMixin


class ReportGenerationMixin(
    AIStatusDocumentMixin,
    AIPrioritiesDocumentMixin,
    ConsolidatedReportDocumentMixin,
):
    """Shared report helpers plus AI_STATUS / AI_PRIORITIES / CONSOLIDATED builders."""

    def _is_dev_tools_scoped_report(self) -> bool:
        """True when reports are written for DEV_TOOLS_*.md (dev-tools-only audit)."""
        return bool(getattr(self, "dev_tools_only_mode", False))

    def _scoped_tool_result_path(self, domain: str, tool_name: str) -> str:
        """Return the repo-relative scoped JSON result path used by tool storage."""
        scope = "dev_tools" if self._is_dev_tools_scoped_report() else "full"
        return (
            f"development_tools/{domain}/jsons/scopes/{scope}/"
            f"{tool_name}_results.json"
        )

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
            return norm.startswith("development_tools/") or norm == "development_tools"

    def _filter_duplicate_groups_dev_tools(self, groups: list[Any]) -> list[Any]:
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

    def _filter_high_coupling_dev_tools(self, items: list[Any]) -> list[dict[str, Any]]:
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
                    "summary": {
                        "total_issues": 0,
                        "files_affected": 0,
                        "status": "WARN",
                    },
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
                    "files_affected": self._coerce_int(
                        summary.get("files_affected"), 0
                    ),
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
            return " — pip-audit subprocess skipped (DEV_TOOLS_PIP_AUDIT_SKIP)"
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
        return _tier3_coerce_int(value, default)

    def _test_marker_gap_metrics(
        self, test_markers_data: dict[str, Any] | None
    ) -> tuple[int, int, list[Any], list[Any]]:
        """Counts and issue lists from ``analyze_test_markers`` JSON.

        Category gaps = missing suite markers (``tests/`` subdirs: unit, integration, behavior, ui).
        Domain gaps = missing product-area markers per ``domain_mapper`` (not the same as category
        or tier markers such as critical; see analyzer docstring).
        """
        if not test_markers_data or not isinstance(test_markers_data, dict):
            return 0, 0, [], []
        details = test_markers_data.get("details")
        if isinstance(details, dict):
            cat = self._coerce_int(details.get("missing_count"), 0) or 0
            dom = self._coerce_int(details.get("missing_domain_count"), 0) or 0
            mlist = details.get("missing")
            dlist = details.get("missing_domain")
            if not isinstance(mlist, list):
                mlist = []
            if not isinstance(dlist, list):
                dlist = []
            return cat, dom, mlist, dlist
        cat = self._coerce_int(test_markers_data.get("missing_count"), 0) or 0
        dom = self._coerce_int(test_markers_data.get("missing_domain_count"), 0) or 0
        mlist = test_markers_data.get("missing")
        if not isinstance(mlist, list):
            mlist = []
        if cat or dom:
            return cat, dom, mlist, []
        summary = test_markers_data.get("summary") or {}
        total = self._coerce_int(summary.get("total_issues"), 0) or 0
        if total:
            return total, 0, mlist, []
        return 0, 0, [], []

    def _top_test_marker_files_bullet(
        self,
        issue_list: list[Any],
        *,
        limit: int = 5,
    ) -> str | None:
        """Single bullet line listing top files by issue count (dict items with file/name)."""
        if not issue_list:
            return None
        from collections import defaultdict

        files_with_missing: dict[str, list[str]] = defaultdict(list)
        for item in issue_list:
            if not isinstance(item, dict):
                continue
            file_path = item.get("file", "")
            test_name = item.get("name", "")
            if file_path:
                files_with_missing[str(file_path)].append(str(test_name))

        if not files_with_missing:
            return None
        sorted_files = sorted(
            files_with_missing.items(),
            key=lambda x: len(x[1]),
            reverse=True,
        )[:limit]
        file_list = []
        for file_path, tests in sorted_files:
            file_name = Path(file_path).name if file_path else "Unknown"
            file_list.append(f"{file_name} ({len(tests)} tests)")
        if len(files_with_missing) > len(sorted_files):
            file_list.append(
                f"... +{len(files_with_missing) - len(sorted_files)} more files"
            )
        return f"Top files: {self._format_list_for_display(file_list, limit=limit)}"

    def _normalize_test_node_id(self, node_id: str) -> str:
        """Normalize pytest node IDs for compact display (drop class segment)."""
        return _tier3_normalize_test_node_id(node_id)

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
        return _tier3_track_classification_label(outcome)

    def _tier3_track_skipped_for_audit_scope(self, track: dict[str, Any]) -> bool:
        """True when Tier 3 split (full-repo vs --dev-tools-only) intentionally did not run this track."""
        return _tier3_track_skipped_fn(track)

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

    def _tier3_outcome_has_run_evidence(self, outcome: dict[str, Any]) -> bool:
        """True when outcome reflects a Tier 3 test run (not empty/stale coverage-only cache)."""
        return _tier3_outcome_has_run_evidence_fn(outcome)

    def _tier3_test_outcome_is_cached_for_report(self) -> bool:
        """True when tier-3 test outcome comes from cache, not from the current Tier 3 audit run."""
        if getattr(self, "current_audit_tier", None) != 3:
            return True
        in_memory = getattr(self, "tier3_test_outcome", None)
        return not (isinstance(in_memory, dict) and in_memory.get("state"))

    def _get_tier3_test_outcome(self) -> dict[str, Any]:
        """Load Tier 3 test outcome state from in-memory or cached results."""
        in_memory = getattr(self, "tier3_test_outcome", None)
        if isinstance(in_memory, dict) and (
            in_memory.get("state")
            or isinstance(in_memory.get("parallel"), dict)
            or isinstance(in_memory.get("no_parallel"), dict)
            or isinstance(in_memory.get("development_tools"), dict)
        ):
            return in_memory

        suite_result = self._load_tool_data(
            "run_test_suite", "tests", log_source=False
        )
        coverage_result = self._load_tool_data(
            "analyze_test_coverage", "tests", log_source=False
        )
        for result in (suite_result, coverage_result):
            if not isinstance(result, dict):
                continue
            details = result.get("details", {})
            if isinstance(details, dict):
                outcome = details.get("tier3_test_outcome", {})
                if isinstance(outcome, dict) and outcome:
                    if not isinstance(outcome.get("development_tools"), dict):
                        dev_tools_result = self._load_tool_data(
                            "generate_dev_tools_coverage", "tests", log_source=False
                        )
                        if isinstance(dev_tools_result, dict):
                            dev_details = dev_tools_result.get("details", {})
                            if isinstance(dev_details, dict):
                                dev_outcome = dev_details.get("dev_tools_test_outcome", {})
                                if isinstance(dev_outcome, dict) and dev_outcome:
                                    outcome = {**outcome, "development_tools": dev_outcome}
                    return outcome
        return {}

    def _effective_tier3_state_from_outcome(self, outcome: dict[str, Any]) -> str:
        """Return effective Tier 3 state including development-tools test outcome."""
        return _tier3_effective_state(outcome)

    def _normalize_tier3_log_file_ref(self, log_file: Any) -> str | None:
        """Return a repo-relative forward-slash path for a track log_file, or None."""
        if not isinstance(log_file, str):
            return None
        raw = log_file.strip()
        if not raw:
            return None
        path = Path(raw)
        if not path.is_absolute():
            path = self.project_root / path
        try:
            rel = path.resolve().relative_to(self.project_root.resolve())
            return str(rel).replace("\\", "/")
        except ValueError:
            return raw.replace("\\", "/")

    def _get_tier3_detail_log_files(
        self,
        outcome: dict[str, Any],
        *,
        include_parallel: bool = False,
        include_no_parallel: bool = False,
        include_dev_tools: bool = False,
    ) -> list[str]:
        """Prefer each track's log_file from tier3_test_outcome; fall back to latest stdout logs."""
        if not isinstance(outcome, dict):
            outcome = {}

        track_specs: list[tuple[bool, str]] = [
            (include_parallel, "parallel"),
            (include_no_parallel, "no_parallel"),
            (include_dev_tools, "development_tools"),
        ]
        selections: list[str] = []
        seen: set[str] = set()
        fallback_parallel = False
        fallback_no_parallel = False
        fallback_dev_tools = False

        for include_track, outcome_key in track_specs:
            if not include_track:
                continue
            track = outcome.get(outcome_key)
            if not isinstance(track, dict):
                track = {}
            normalized = self._normalize_tier3_log_file_ref(track.get("log_file"))
            if normalized:
                if normalized not in seen:
                    selections.append(normalized)
                    seen.add(normalized)
            elif outcome_key == "parallel":
                fallback_parallel = True
            elif outcome_key == "no_parallel":
                fallback_no_parallel = True
            else:
                fallback_dev_tools = True

        if fallback_parallel or fallback_no_parallel or fallback_dev_tools:
            for path in self._get_recent_tier3_log_files(
                include_parallel=fallback_parallel,
                include_no_parallel=fallback_no_parallel,
                include_dev_tools=fallback_dev_tools,
            ):
                if path not in seen:
                    selections.append(path)
                    seen.add(path)
        return selections

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
        if self._tier3_test_outcome_is_cached_for_report():
            lines.append(
                "- **Source**: Cached from last Tier 3 (`audit --full`) run "
                "(this audit did not re-run tests)"
            )
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
            lines.append(
                self._format_track_classification_summary("Parallel", parallel)
            )
        if not skip_np:
            lines.append(
                self._format_track_classification_summary("No-Parallel", no_parallel)
            )
        if not skip_dt:
            lines.append(
                self._format_track_classification_summary(
                    "Development Tools", dev_tools
                )
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
        json_candidates = [
            self.project_root
            / "development_tools"
            / "tests"
            / "jsons"
            / "scopes"
            / ("dev_tools" if self._is_dev_tools_scoped_report() else "full")
            / "verify_process_cleanup_results.json",
            self.project_root
            / "development_tools"
            / "tests"
            / "jsons"
            / "verify_process_cleanup_results.json",
        ]
        json_path = next((p for p in json_candidates if p.exists()), json_candidates[0])
        scope = "dev_tools" if self._is_dev_tools_scoped_report() else "full"
        default_rel = (
            f"development_tools/tests/jsons/scopes/{scope}/verify_process_cleanup_results.json"
        )
        if json_path.exists():
            rel_from_root = json_path.relative_to(self.project_root).as_posix()
        else:
            rel_from_root = default_rel
        # Audit JSON under development_tools/**/jsons/ is gitignored; avoid markdown
        # links to ephemeral targets (doc-sync flags them as missing).
        if "/jsons/" in rel_from_root.replace("\\", "/"):
            out.append(
                f"- **Machine-readable**: `{rel_from_root}` "
                "(audit output; regenerated each Tier 3 run)"
            )
        else:
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
