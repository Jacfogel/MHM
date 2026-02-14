"""
Report generation methods for AIToolsService.

Contains methods for generating AI_STATUS.md, AI_PRIORITIES.md, and consolidated_report.txt.
These methods are large (~4,300 lines total) and generate comprehensive status reports.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import audit orchestration helper
from .audit_orchestration import _is_audit_in_progress


class ReportGenerationMixin:
    """Mixin class providing report generation methods to AIToolsService."""

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

    def _get_results_file_path(self) -> Path:
        """Get the results file path from config."""
        # Default matches development_tools_config.json
        results_file_path = (self.audit_config or {}).get(
            "results_file", "development_tools/reports/analysis_detailed_results.json"
        )
        return self._resolve_report_path(results_file_path)

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
                "/tmp",
                "/temp",  # Unix-style temp
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

            if re.search(r"[\\/]tmp[a-z0-9]{6,}[\\/]", path_str):
                return True

            return False
        except Exception as e:
            # If we can't determine, be conservative and assume it's not a test directory
            # But log it so we can debug
            logger.debug(f"Error checking if path is test directory ({path}): {e}")
            return False

    def _load_results_file_safe(self) -> Optional[Dict]:
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

            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _get_decision_support_details(self, data: Any) -> Dict[str, Any]:
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

    def _get_system_signals_details(self, data: Any) -> Dict[str, Any]:
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

    def _generate_ai_status_document(self) -> str:
        """Generate AI-optimized status document."""
        # Log data source context
        audit_tier = getattr(self, "current_audit_tier", None)
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating AI_STATUS.md using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating AI_STATUS.md using cached data (no active audit)"
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

        lines: List[str] = []
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
        lines.append(f"> **Source**: `{source_cmd}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        lines.append("")

        def strip_doc_header(doc: str, drop_section: Optional[str] = None) -> List[str]:
            doc_lines = doc.splitlines()
            if doc_lines and doc_lines[0].startswith("# "):
                doc_lines = doc_lines[1:]
            if not drop_section:
                return doc_lines

            filtered: List[str] = []
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

        def to_int(value: Any) -> Optional[int]:
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

        def to_float(value: Any) -> Optional[float]:
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
        function_metrics = self._load_tool_data("analyze_functions", "functions")
        analyze_docs_data = self._load_tool_data("analyze_documentation", "docs")
        ascii_data = self._load_tool_data("analyze_ascii_compliance", "docs")
        heading_data = self._load_tool_data("analyze_heading_numbering", "docs")
        missing_addresses_data = self._load_tool_data(
            "analyze_missing_addresses", "docs"
        )
        unconverted_links_data = self._load_tool_data(
            "analyze_unconverted_links", "docs"
        )

        # Extract overlap analysis data
        details = analyze_docs_data.get("details", {})
        overlap_analysis_ran = (
            "section_overlaps" in analyze_docs_data
            or "consolidation_recommendations" in analyze_docs_data
            or "section_overlaps" in details
            or "consolidation_recommendations" in details
        )
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

        def get_error_field(field_name, default=None):
            error_details = error_metrics.get("details", {})
            return error_details.get(field_name, default)

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

        error_coverage = error_details.get("analyze_error_handling") or error_details.get(
            "error_handling_coverage"
        )
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
                                ds_data.get("data") if isinstance(ds_data, dict) else None
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

        # Use registry data for accurate docstring coverage (includes handlers)
        # Registry data is more accurate because it includes all functions, not just non-handlers
        doc_coverage = metrics.get("doc_coverage", "Unknown")
        functions_without_docstrings = None
        missing_docs = None
        missing_files = []

        # First, try to get coverage from registry (most accurate)
        registry_data = self._load_tool_data("analyze_function_registry", "functions")
        if isinstance(registry_data, dict):
            registry_details = registry_data.get("details", {})
            # Check for coverage percentage directly
            registry_coverage = registry_details.get("coverage")
            if registry_coverage is not None:
                doc_coverage = f"{registry_coverage:.2f}%"
                # Calculate undocumented count from registry data
                registry_analysis = registry_details.get("analysis", {})
                undocumented_handlers = registry_analysis.get(
                    "undocumented_handlers_total", 0
                )
                undocumented_other = registry_analysis.get(
                    "undocumented_other_total", 0
                )
                functions_without_docstrings = (
                    undocumented_handlers + undocumented_other
                )

        # Fallback to analyze_functions if registry data not available
        if doc_coverage == "Unknown" or functions_without_docstrings is None:
            function_data = self._load_tool_data("analyze_functions", "functions")
            if isinstance(function_data, dict):
                func_details = function_data.get("details", {})
                func_total = func_details.get("total_functions") or function_data.get(
                    "total_functions"
                )
                func_undocumented = func_details.get(
                    "undocumented", 0
                ) or function_data.get("undocumented", 0)
                if func_total is not None and func_total > 0:
                    func_documented = func_total - func_undocumented
                    coverage_pct = (func_documented / func_total) * 100
                    doc_coverage = f"{coverage_pct:.2f}%"
                    functions_without_docstrings = (
                        int(func_undocumented) if func_undocumented else 0
                    )

        # Fallback to cached results
        if (
            doc_coverage == "Unknown" or doc_coverage is None
        ) and functions_without_docstrings is None:
            try:
                cached_data = self._load_results_file_safe()
                if cached_data:
                    if (
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
                                functions_without_docstrings = func_undocumented
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
                    functions_without_docstrings = int(func_undocumented)

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
                if cached_data:
                    if (
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
            lines.append(f"- **Registry Gaps**: 0 items missing from registry")

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
        ):
            if error_total != canonical_total:
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
        else:
            lines.append(
                "- **Doc Sync**: Not collected in this run (pending doc-sync refresh)"
            )

        # Test coverage
        if coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            if overall.get("coverage") is not None:
                lines.append(
                    f"- **Test Coverage**: {percent_text(overall.get('coverage'), 1)} "
                    f"({overall.get('covered')} of {overall.get('statements')} statements)"
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
                lines.append("- **Status**: No overlaps detected (analysis performed)")
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
            decorated = get_error_field("functions_with_decorators")
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
                        if loaded_data:
                            error_metrics = loaded_data
                        else:
                            error_metrics = None

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

        if coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            lines.append(
                f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} "
                f"({overall.get('covered')} of {overall.get('statements')} statements)"
            )
            lines.append(
                "    - **Coverage Scope**: Main project domains (`core`, `communication`, `ui`, `tasks`, `user`, `ai`) only; `development_tools/` is tracked separately."
            )
            coverage_report_path = (
                self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
            )
            if coverage_report_path.exists():
                lines.append(
                    f"    - **Detailed Report**: [TEST_COVERAGE_REPORT.md](development_docs/TEST_COVERAGE_REPORT.md)"
                )

            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
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
            lines.append(
                "- Coverage data unavailable; run `audit --full` to regenerate metrics"
            )
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
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

            if total_unused > 0 or files_with_issues > 0:
                lines.append("## Unused Imports")
                lines.append(
                    f"- **Total Unused**: {total_unused} imports across {files_with_issues} files"
                )
                if status:
                    lines.append(f"- **Status**: {status}")
                details = unused_imports_data.get("details", {})
                by_category = details.get("by_category") or {}
                if by_category:
                    obvious = by_category.get("obvious_unused", 0)
                    type_only = by_category.get("type_hints_only", 0)
                    if obvious > 0:
                        lines.append(f"    - **Obvious Removals**: {obvious} imports")
                    if type_only > 0:
                        lines.append(
                            f"    - **Type-Only Imports**: {type_only} imports"
                        )
            else:
                lines.append("## Unused Imports")
                lines.append("- **Status**: CLEAN (no unused imports detected)")

            unused_imports_report_path = (
                self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
            )
            if unused_imports_report_path.exists():
                lines.append(
                    f"- **Detailed Report**: [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)"
                )
        else:
            lines.append("## Unused Imports")
            lines.append(
                "- **Status**: Data unavailable (run `audit --full` for latest scan)"
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
                    rel_path = report_path_obj.relative_to(self.project_root)
                    lines.append(
                        f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({rel_path.as_posix()})"
                    )
        else:
            lines.append(
                "- Legacy reference data unavailable (run `audit --full` for latest scan)"
            )

        lines.append("")
        lines.append("## Duplicate Functions")
        duplicate_data = self._load_tool_data(
            "analyze_duplicate_functions", "functions"
        )
        duplicate_summary = (
            duplicate_data.get("summary", {})
            if isinstance(duplicate_data, dict)
            else {}
        )
        duplicate_groups = to_int(duplicate_summary.get("total_issues")) or 0
        duplicate_files = to_int(duplicate_summary.get("files_affected")) or 0
        if duplicate_groups > 0:
            lines.append(
                f"- **Potential Duplicate Groups**: {duplicate_groups} (files affected: {duplicate_files})"
            )
        else:
            lines.append("- **Potential Duplicate Groups**: 0")

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
                    "- **AI Work Validation**: POOR - documentation or tests missing"
                )
            elif "GOOD" in validation_output:
                lines.append("- **AI Work Validation**: GOOD - keep current standards")
            elif "NEEDS ATTENTION" in validation_output or "FAIR" in validation_output:
                lines.append(
                    "- **AI Work Validation**: NEEDS ATTENTION - see consolidated report for details"
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
                                "- **AI Work Validation**: NEEDS ATTENTION - see consolidated report for details (cached)"
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
        lines.append("## System Signals")

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
        lines.append("## Quick Commands")
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
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating AI_PRIORITIES.md using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating AI_PRIORITIES.md using cached data (no active audit)"
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

        lines: List[str] = []
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
        lines.append(f"> **Source**: `{source_cmd}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed if trimmed.endswith("%") else f"{trimmed}%"
            return self._format_percentage(value, decimals)

        def to_int(value: Any) -> Optional[int]:
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

        def to_float(value: Any) -> Optional[float]:
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
        unused_imports_data = self._load_tool_data("analyze_unused_imports", "imports")
        dependency_patterns_data = self._load_tool_data(
            "analyze_dependency_patterns", "imports"
        )
        duplicate_functions_data = self._load_tool_data(
            "analyze_duplicate_functions", "functions"
        )

        section_overlaps = analyze_data.get("section_overlaps", {})
        consolidation_recs = analyze_data.get("consolidation_recommendations", [])

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
        canonical_total = metrics.get("total_functions")
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

        low_coverage_modules: List[Dict[str, Any]] = []
        coverage_overall = None
        worst_coverage_files: List[Dict[str, Any]] = []
        if coverage_summary:
            coverage_overall = (coverage_summary or {}).get("overall")
            module_entries = (coverage_summary or {}).get("modules") or []
            for module in module_entries:
                coverage_value = to_float(module.get("coverage"))
                coverage_float = (
                    to_float(coverage_value) if coverage_value is not None else None
                )
                if coverage_float is not None and coverage_float < 80:
                    low_coverage_modules.append(module)
            low_coverage_modules = low_coverage_modules[:3]
            worst_coverage_files = (coverage_summary or {}).get("worst_files") or []

        dev_tools_coverage_overall = None
        if (
            hasattr(self, "dev_tools_coverage_results")
            and self.dev_tools_coverage_results
        ):
            dev_tools_coverage_overall = self.dev_tools_coverage_results.get(
                "overall", {}
            )
        dev_tools_insights = self._get_dev_tools_coverage_insights()

        analyze_artifacts = analyze_data.get("artifacts") or []
        analyze_duplicates = analyze_data.get("duplicates") or []
        analyze_placeholders = analyze_data.get("placeholders") or []

        critical_examples = function_metrics.get("critical_complexity_examples") or []
        high_examples = function_metrics.get("high_complexity_examples") or []

        # Try loading from multiple sources, prioritizing in-memory cache, then tool data (may be cached)
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

        # If still not available, try loading from analyze_functions tool data (may be cached)
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

        priority_items: List[Dict[str, Any]] = []

        # Fixed tier ordering: tier number * 100 + insertion order within tier
        # This ensures predictable ordering: Tier 1 items (100-199), Tier 2 (200-299), etc.
        tier_insertion_counters = {1: 0, 2: 0, 3: 0, 4: 0}

        def validate_recommendation(
            title: str,
            reason: str,
            data_source: Optional[str] = None,
            count: Optional[int] = None,
            expected_min: Optional[int] = None,
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
            bullets: List[str],
            validate: bool = True,
            data_source: Optional[str] = None,
            count: Optional[int] = None,
            expected_min: Optional[int] = None,
        ) -> None:
            nonlocal tier_insertion_counters
            if not reason:
                return

            # Validate recommendation if requested
            if validate:
                if not validate_recommendation(
                    title, reason, data_source, count, expected_min
                ):
                    return

            # Normalize tier to valid range (1-4)
            normalized_tier = max(1, min(4, tier))

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
                    "bullets": [bullet for bullet in bullets if bullet],
                }
            )

        # Add priorities based on issues found
        # Path drift priority
        if path_drift_count and path_drift_count > 0:
            drift_details: List[str] = []
            if path_drift_files:
                drift_details.append(
                    f"Top offenders: {self._format_list_for_display(path_drift_files, limit=3)}"
                )
            if paired_doc_issues:
                drift_details.append(
                    f"{paired_doc_issues} paired documentation sets affected alongside drift."
                )
            drift_details.append(
                "Action: Fix broken paths in top offender files, then run `python development_tools/run_development_tools.py doc-sync`"
            )
            drift_details.append(
                "Effort: Small (update file paths in documentation, run automated fix tool)"
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
            doc_bullets: List[str] = []
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
                "Effort: Medium (requires understanding each function's purpose and parameters)"
            )
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
            registry_bullets: List[str] = []

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
                "Effort: Small (automated command regenerates FUNCTION_REGISTRY_DETAIL.md)"
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
            error_handling_bullets: List[str] = []

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
                "Effort: Small (add @handle_errors decorator or wrap in try-except)"
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

        # Phase 1: Decorator replacement candidates (after missing error handlers)
        phase1_total = to_int(get_error_field("phase1_total", 0))
        phase1_by_priority = get_error_field("phase1_by_priority", {}) or {}
        phase1_high = to_int(phase1_by_priority.get("high", 0))

        if phase1_total and phase1_total > 0:
            phase1_bullets: List[str] = []
            # Get phase1 candidates to group by module
            phase1_candidates = get_error_field("phase1_candidates", []) or []
            if not isinstance(phase1_candidates, list):
                phase1_candidates = []

            # Group by module (file_path) and priority
            if phase1_candidates:
                from collections import defaultdict

                high_by_module = defaultdict(int)
                medium_by_module = defaultdict(int)

                for candidate in phase1_candidates:
                    if isinstance(candidate, dict):
                        file_path = candidate.get("file_path", "")
                        priority = candidate.get("priority", "").lower()
                        if file_path:
                            # Extract module name (file path without extension)
                            module = file_path.replace("\\", "/")
                            if priority == "high":
                                high_by_module[module] += 1
                            elif priority == "medium":
                                medium_by_module[module] += 1

                # Show top modules with high-priority candidates, or medium if no high
                if phase1_high and phase1_high > 0:
                    phase1_bullets.append(
                        f"Start with {phase1_high} high-priority candidates (entry points and critical operations)."
                    )
                    if high_by_module:
                        # Sort by count and show top 3
                        top_modules = sorted(
                            high_by_module.items(), key=lambda x: x[1], reverse=True
                        )[:3]
                        module_list = [
                            f"{Path(m).name} ({count})" for m, count in top_modules
                        ]
                        if module_list:
                            phase1_bullets.append(
                                f"Top modules: {self._format_list_for_display(module_list, limit=3)}"
                            )
                else:
                    # No high priority, show medium priority modules
                    phase1_medium = to_int(phase1_by_priority.get("medium", 0))
                    if phase1_medium and phase1_medium > 0:
                        phase1_bullets.append(
                            f"Process {phase1_medium} medium-priority functions."
                        )
                        if medium_by_module:
                            top_modules = sorted(
                                medium_by_module.items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )[:3]
                            module_list = [
                                f"{Path(m).name} ({count})" for m, count in top_modules
                            ]
                            if module_list:
                                phase1_bullets.append(
                                    f"Top modules: {self._format_list_for_display(module_list, limit=3)}"
                                )

            phase1_medium = to_int(phase1_by_priority.get("medium", 0))
            if phase1_medium and phase1_medium > 0 and phase1_high and phase1_high > 0:
                phase1_bullets.append(
                    f"Then process {phase1_medium} medium-priority functions."
                )
            phase1_bullets.append(
                "Apply `@handle_errors` decorator to replace basic try-except blocks."
            )
            # Add effort estimate and context
            phase1_bullets.append(
                "Effort: Medium (requires reviewing each function's error handling needs)"
            )
            phase1_bullets.append(
                "Why this matters: Centralized error handling provides consistent logging and recovery patterns"
            )
            add_priority(
                tier=2,  # Tier 2: High
                title="Phase 1: Replace basic try-except with decorators",
                reason=f"{phase1_total} functions have try-except blocks that should use `@handle_errors` decorator.",
                bullets=phase1_bullets,
            )

        # Phase 2: Generic exception categorization (after Phase 1)
        phase2_total = to_int(get_error_field("phase2_total", 0))
        phase2_by_type = get_error_field("phase2_by_type", {}) or {}

        if phase2_total and phase2_total > 0:
            phase2_bullets: List[str] = []
            top_exceptions = sorted(
                phase2_by_type.items(), key=lambda x: x[1], reverse=True
            )[:3]
            if top_exceptions:
                exc_details = [
                    f"{count} {exc_type}" for exc_type, count in top_exceptions
                ]
                phase2_bullets.append(
                    f"Most common: {self._format_list_for_display(exc_details, limit=3)}"
                )

            # Get phase2 exceptions to group by module
            phase2_exceptions = get_error_field("phase2_exceptions", []) or []
            if not isinstance(phase2_exceptions, list):
                phase2_exceptions = []
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
                    # Sort by count and show top 3
                    top_modules = sorted(
                        exceptions_by_module.items(), key=lambda x: x[1], reverse=True
                    )[:3]
                    module_list = [
                        f"{Path(m).name} ({count})" for m, count in top_modules
                    ]
                    if module_list:
                        phase2_bullets.append(
                            f"Top modules: {self._format_list_for_display(module_list, limit=3)}"
                        )

            phase2_bullets.append(
                "Replace generic exceptions (ValueError, Exception, KeyError, TypeError) with specific project error classes."
            )
            phase2_bullets.append(
                "See `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` for categorization rules."
            )
            phase2_bullets.append(
                "Effort: Small (replace exception class names, update imports)"
            )
            phase2_bullets.append(
                "Why this matters: Specific error classes enable targeted error handling and better debugging"
            )
            add_priority(
                tier=2,  # Tier 2: High
                title="Phase 2: Categorize generic exceptions",
                reason=f"{phase2_total} generic exception raises need categorization into project-specific error classes.",
                bullets=phase2_bullets,
            )

        # Coverage priorities
        if low_coverage_modules:
            coverage_highlights = [
                f"{module.get('module', 'module')} ({percent_text(module.get('coverage'), 1)}, {module.get('missed')} lines missing)"
                for module in low_coverage_modules
            ]
            coverage_bullets = [
                f"Target domains: {self._format_list_for_display(coverage_highlights, limit=3)}",
                "Action: Add scenario tests for uncovered code paths in target domains",
                f"Effort: Medium (writing tests for {len(low_coverage_modules)} domains requires understanding business logic)",
                "Why this matters: Higher test coverage reduces bug risk and improves code maintainability",
                "Command: Run `python development_tools/run_development_tools.py audit --full` after adding tests to verify coverage improvement",
            ]
            add_priority(
                tier=2,  # Tier 2: High
                title="Raise coverage for domains below target",
                reason=f"{len(low_coverage_modules)} key domains remain below the 80% target.",
                bullets=coverage_bullets,
            )

        if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
            dev_pct = dev_tools_insights["overall_pct"]
            low_dev_modules = dev_tools_insights.get("low_modules") or []
            if dev_pct < 60 or low_dev_modules:
                dev_bullets: List[str] = []
                if low_dev_modules:
                    highlights = [
                        f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)})"
                        for item in low_dev_modules
                    ]
                    dev_bullets.append(
                        f"Focus on: {self._format_list_for_display(highlights, limit=3)}"
                    )
                if dev_tools_insights.get("html"):
                    dev_bullets.append(
                        f"Review HTML report at {dev_tools_insights['html']}"
                    )
                dev_bullets.append(
                    "Action: Strengthen tests in `tests/development_tools/` for fragile helpers and low-coverage modules"
                )
                dev_bullets.append(
                    f"Effort: Medium (adding tests for {len(low_dev_modules) if low_dev_modules else 'multiple'} modules requires understanding tool behavior)"
                )
                dev_bullets.append(
                    "Why this matters: Development tools need high test coverage to ensure reliability and prevent regressions"
                )
                dev_bullets.append(
                    "Command: Run `python run_tests.py --coverage` to verify coverage improvements"
                )
                add_priority(
                    tier=2,  # Tier 2: High
                    title="Raise development tools coverage",
                    reason=f"Development tools coverage is {percent_text(dev_pct, 1)} (target 60%+).",
                    bullets=dev_bullets,
                )

        # Legacy references priority
        if legacy_files and legacy_files > 0:
            legacy_bullets: List[str] = []
            if legacy_markers:
                legacy_bullets.append(
                    f"{legacy_markers} legacy markers still surface during scans."
                )
            if legacy_report:
                legacy_bullets.append(f"Review {legacy_report} for exact locations.")
            legacy_bullets.append(
                "Action: Remove legacy compatibility code and update references to use new implementations"
            )
            legacy_bullets.append(
                f"Effort: Medium (reviewing {legacy_files} files and updating references requires testing)"
            )
            legacy_bullets.append(
                "Why this matters: Legacy code increases maintenance burden and technical debt"
            )
            legacy_bullets.append(
                "Command: `python development_tools/run_development_tools.py legacy` to scan for legacy references"
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Retire remaining legacy references",
                reason=f"{legacy_files} files still depend on legacy compatibility markers.",
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
                config_bullets: List[str] = []
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
                        f"Effort: Small to Medium (updating {len(unique_recs)} tool(s) requires understanding config structure)"
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
                        handlers_bullets: List[str] = []
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
                            f"Effort: Small (adding docstrings to {len(handlers_no_doc)} handler classes is straightforward)"
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
                test_markers_bullets: List[str] = []

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
                    "Effort: Small (run automated fix tool or add markers manually)"
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

        # Unused imports priority
        # Only recommend removing "Obvious Unused" imports (not test mocking, Qt testing, etc.)
        if unused_imports_data and isinstance(unused_imports_data, dict):
            summary = unused_imports_data.get("summary", {})
            details = unused_imports_data.get("details", {})
            by_category = details.get("by_category", {})
            obvious_unused = (
                by_category.get("obvious_unused", 0)
                if isinstance(by_category, dict)
                else 0
            )

            # Only create recommendation if there are obvious unused imports
            if obvious_unused and obvious_unused > 0:
                unused_bullets: List[str] = []

                # Get files with obvious unused imports
                files_dict = unused_imports_data.get("files", {})
                obvious_files = []
                if files_dict and isinstance(files_dict, dict):
                    # Filter files to only those with obvious unused imports
                    # We need to check the category for each file's imports
                    for file_path, imports in files_dict.items():
                        if isinstance(imports, list):
                            # Check if any import in this file is marked as obvious_unused
                            # The structure may vary, so we'll count files that have obvious unused
                            # For now, we'll show top files from the report
                            pass

                # Get top files if available (showing all files, but recommendation is only for obvious)
                if files_dict and isinstance(files_dict, dict):
                    sorted_files = sorted(
                        files_dict.items(),
                        key=lambda x: len(x[1]) if isinstance(x[1], list) else 1,
                        reverse=True,
                    )[:5]
                    if sorted_files:
                        file_list = []
                        for file_path, imports in sorted_files:
                            import_count = (
                                len(imports) if isinstance(imports, list) else 1
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

                type_only = (
                    by_category.get("type_hints_only", 0)
                    if isinstance(by_category, dict)
                    else 0
                )
                if type_only and type_only > 0:
                    unused_bullets.append(
                        f"Note: {type_only} type-only imports exist but are not recommended for removal (consider TYPE_CHECKING guard if needed)"
                    )

                unused_bullets.append(
                    "Action: Review and remove obvious unused imports (safe to delete)"
                )
                unused_bullets.append(
                    "Effort: Small (remove safe imports identified as obvious unused)"
                )
                unused_bullets.append(
                    "Why this matters: Unused imports add noise, slow imports, and can hide real dependencies"
                )

                # Check if there's a detailed report
                unused_imports_report_path = (
                    self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
                )
                if unused_imports_report_path.exists():
                    unused_bullets.append(
                        f"Detailed Report: [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)"
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
            dup_groups = to_int(summary.get("total_issues")) or 0
            dup_files = to_int(summary.get("files_affected")) or 0
            groups = (
                details.get("duplicate_groups", []) if isinstance(details, dict) else []
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
                    return (func_count, max_score)

                sorted_groups = sorted(groups, key=group_sort_key, reverse=True)[:3]
                duplicate_bullets: List[str] = []
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
                add_priority(
                    tier=2,
                    title="Investigate possible duplicate functions/methods",
                    reason=f"{dup_groups} potential duplicate groups across {dup_files} files.",
                    bullets=duplicate_bullets,
                    validate=True,
                    data_source="analyze_duplicate_functions",
                    count=dup_groups,
                    expected_min=None,
                )

        # Complexity refactoring priority
        if critical_complex and critical_complex > 0:
            complexity_bullets: List[str] = []
            # Ensure we have examples - try loading if not available
            if not critical_examples:
                # Try loading from decision_support (standard format)
                decision_metrics = self._get_decision_support_details(
                    self.results_cache.get("decision_support")
                )
                if decision_metrics and "critical_complexity_examples" in decision_metrics:
                    critical_examples = decision_metrics.get(
                        "critical_complexity_examples", []
                    )
                # If still not available, try loading from analyze_functions (may be cached)
                if not critical_examples:
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
                        # Also check decision_support tool data if available
                        if not critical_examples or len(critical_examples) == 0:
                            decision_data = self._load_tool_data(
                                "decision_support", "functions", log_source=False
                            )
                            if decision_data and isinstance(decision_data, dict):
                                decision_metrics_from_tool = self._get_decision_support_details(
                                    decision_data
                                )
                                if decision_metrics_from_tool and "critical_complexity_examples" in decision_metrics_from_tool:
                                    critical_examples = decision_metrics_from_tool.get(
                                        "critical_complexity_examples", []
                                    )
                                # Also try loading high_examples if not already loaded
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
            if high_complex and high_complex > 0 and critical_complex <= 10:
                complexity_bullets.append(
                    f"Then address {high_complex} high-complexity functions (100-199 nodes)."
                )
            complexity_bullets.append(
                "Action: Break down complex functions into smaller, focused functions with single responsibilities"
            )
            complexity_bullets.append(
                f"Effort: Large (refactoring {critical_complex} critical functions requires careful analysis and testing)"
            )
            complexity_bullets.append(
                "Why this matters: High complexity functions are harder to understand, test, and maintain, increasing bug risk"
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Refactor high-complexity functions",
                reason=f"{critical_complex} critical-complexity functions (>199 nodes) need immediate attention.",
                bullets=complexity_bullets,
            )
        elif high_complex and high_complex > 0:
            high_complexity_bullets: List[str] = []
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
            high_complexity_bullets.append(
                "Action: Simplify high-complexity functions by extracting helper functions and reducing nesting"
            )
            high_complexity_bullets.append(
                f"Effort: Medium (refactoring {high_complex} high-complexity functions requires careful planning)"
            )
            high_complexity_bullets.append(
                "Why this matters: High complexity functions are harder to understand, test, and maintain, increasing bug risk"
            )
            add_priority(
                tier=3,  # Tier 3: Medium
                title="Refactor high-complexity functions",
                reason=f"{high_complex} high-complexity functions (100-199 nodes) should be simplified.",
                bullets=high_complexity_bullets,
            )

        lines.append("## Immediate Focus (Ranked)")
        if priority_items:
            for idx, item in enumerate(
                sorted(priority_items, key=lambda entry: entry["order"]), start=1
            ):
                lines.append(f"{idx}. **{item['title']}**  -  {item['reason']}")
                for bullet in item["bullets"]:
                    lines.append(f"   - {bullet}")
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

        quick_wins: List[str] = []
        if ascii_issues is not None and ascii_issues > 0:
            quick_wins.append(
                f"Normalize {ascii_issues} file(s) with non-ASCII characters via doc-fix."
            )

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
            if missing > 0:
                files_str = (
                    self._format_list_for_display(files, limit=2)
                    if files
                    else "affected files"
                )
                quick_wins.append(
                    f"Refresh dependency documentation: {missing} module dependencies are undocumented ({files_str}). Regenerate via `python development_tools/run_development_tools.py docs`."
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

        if paired_doc_issues and not (path_drift_count and path_drift_count > 0):
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

        # Add documentation analysis quick wins
        if ascii_data and isinstance(ascii_data, dict):
            summary = ascii_data.get("summary", {})
            ascii_total = summary.get("total_issues", 0)
            ascii_file_count = summary.get("files_affected", 0)
            if ascii_total > 0:
                quick_wins.append(
                    f"Fix {ascii_total} ASCII compliance issue(s) in {ascii_file_count} file(s) - run `python development_tools/run_development_tools.py doc-fix --fix-ascii`"
                )

        if heading_data and isinstance(heading_data, dict):
            summary = heading_data.get("summary", {})
            heading_total = summary.get("total_issues", 0)
            heading_file_count = summary.get("files_affected", 0)
            if heading_total > 0:
                quick_wins.append(
                    f"Fix {heading_total} heading numbering issue(s) in {heading_file_count} file(s) - run `python development_tools/run_development_tools.py doc-fix --number-headings`"
                )

        if missing_addresses_data and isinstance(missing_addresses_data, dict):
            summary = missing_addresses_data.get("summary", {})
            missing_total = summary.get("total_issues", 0)
            missing_file_count = summary.get("files_affected", 0)
            if missing_total > 0:
                quick_wins.append(
                    f"Add file address metadata to {missing_file_count} file(s) missing addresses - run `python development_tools/run_development_tools.py doc-fix --add-addresses`"
                )

        if unconverted_links_data and isinstance(unconverted_links_data, dict):
            summary = unconverted_links_data.get("summary", {})
            links_total = summary.get("total_issues", 0)
            links_file_count = summary.get("files_affected", 0)
            if links_total > 0:
                quick_wins.append(
                    f"Convert {links_total} unconverted link(s) in {links_file_count} file(s) - run `python development_tools/run_development_tools.py doc-fix --convert-links`"
                )

        lines.append("## Quick Wins")
        if quick_wins:
            for win in quick_wins:
                lines.append(f"- {win}")
        else:
            lines.append(
                "- No immediate quick wins identified. Re-run doc-sync after tackling focus items."
            )

        # Add overlap analysis information only if there are issues to prioritize
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0
        overlap_count = len(section_overlaps) if section_overlaps else 0

        # Add consolidation opportunities as priority items
        if consolidation_recs and consolidation_count > 0:
            # Use tier 4 for consolidation (low priority)
            consolidation_bullets: List[str] = []
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

        watch_list: List[str] = []
        doc_coverage_float = (
            to_float(doc_coverage_value) if doc_coverage_value is not None else None
        )
        # Get documentation coverage threshold from config (defaults to 80.0 if not found)
        try:
            from ... import config

            validation_config = config.get_validation_config()
            doc_threshold = validation_config.get(
                "documentation_coverage_threshold", 80.0
            )
        except (ImportError, AttributeError):
            doc_threshold = 80.0  # Default fallback
        if doc_coverage_float is not None and doc_coverage_float < doc_threshold:
            watch_list.append(
                f"Documentation coverage sits at {percent_text(doc_coverage_value, 2)} (target {doc_threshold}%)."
            )
        if coverage_overall:
            coverage_pct = coverage_overall.get("coverage", 0)
            target = 80
            watch_list.append(
                f"Overall test coverage is {percent_text(coverage_pct, 1)} (target {target}%) "
                f"({coverage_overall.get('covered')} / {coverage_overall.get('statements')} statements)."
            )
        if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
            dev_pct = dev_tools_insights["overall_pct"]
            detail = f"Development tools coverage is {percent_text(dev_pct, 1)} (target 60%+)."
            watch_list.append(detail)

        registry_doc_coverage_value = (
            doc_metrics_details.get("coverage")
            if isinstance(doc_metrics_details, dict)
            else None
        )
        registry_analysis = (
            doc_metrics_details.get("analysis", {})
            if isinstance(doc_metrics_details, dict)
            else {}
        )
        registry_missing_docstrings = (
            to_int(registry_analysis.get("undocumented_handlers_total", 0)) or 0
        ) + (to_int(registry_analysis.get("undocumented_other_total", 0)) or 0)
        if missing_docs_count_for_priority is not None and registry_doc_coverage_value is not None:
            watch_list.append(
                "Docstring metrics: "
                f"code-docstrings={missing_docs_count_for_priority} missing, "
                f"registry-docstrings={registry_missing_docstrings} missing "
                f"({percent_text(registry_doc_coverage_value, 2)} coverage)."
            )
            if registry_missing_docstrings != missing_docs_count_for_priority:
                watch_list.append(
                    "Docstring count mismatch is expected when registry/handler docs and code docstrings diverge; review both before prioritizing."
                )

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
            dependency_payload = dependency_patterns_data.get("data", dependency_patterns_data)
        if isinstance(dependency_payload, dict):
            circular_dependency_count = len(
                dependency_payload.get("circular_dependencies", []) or []
            )
            high_coupling_count = len(dependency_payload.get("high_coupling", []) or [])
            watch_list.append(
                "Dependency patterns: "
                f"{circular_dependency_count} circular chain(s), "
                f"{high_coupling_count} high-coupling module(s)."
            )

        if high_examples:
            high_focus = [
                f"{entry['function']} ({entry['file']})" for entry in high_examples[:3]
            ]
            if high_focus:
                watch_list.append(
                    f"Monitor high complexity functions: {self._format_list_for_display(high_focus, limit=3)}."
                )

        if legacy_markers and (not legacy_files or legacy_files == 0):
            watch_list.append(
                f"{legacy_markers} legacy markers remain; schedule periodic cleanup post-sprint."
            )

        validation_output = ""
        if hasattr(self, "validation_results") and self.validation_results:
            validation_output = self.validation_results.get("output", "")

        if not validation_output:
            # Try loading from tool data (may be cached)
            validation_data = self._load_tool_data(
                "analyze_ai_work", "ai_work", log_source=True
            )
            if validation_data:
                validation_output = validation_data.get("output", "") or ""
            # Fallback to direct cache file access if tool data loader didn't find it
            if not validation_output:
                try:
                    cached_data = self._load_results_file_safe()
                    if (
                        cached_data
                        and "results" in cached_data
                        and "analyze_ai_work" in cached_data["results"]
                    ):
                        validation_result = cached_data["results"]["analyze_ai_work"]
                        if "data" in validation_result:
                            data = validation_result["data"]
                            validation_output = data.get("output", "") or ""
                except Exception:
                    pass

        if validation_output and (
            "POOR" in validation_output
            or "NEEDS ATTENTION" in validation_output
            or "FAIR" in validation_output
        ):
            watch_list.append(
                "AI Work Validation: Structural validation issues detected (see consolidated report)"
            )

        lines.append("## Watch List")
        if watch_list:
            for item in watch_list:
                lines.append(f"- {item}")
        else:
            lines.append(
                "- No outstanding watch items. Continue regular audits to maintain signal quality."
            )
        lines.append("")

        lines.append("## Follow-up Commands")
        lines.append(
            "- `python development_tools/run_development_tools.py doc-sync`  -  refresh drift, pairing, and ASCII metrics."
        )
        lines.append(
            "- `python development_tools/run_development_tools.py audit --full`  -  rebuild coverage and hygiene data after fixes."
        )
        lines.append(
            "- `python development_tools/run_development_tools.py status`  -  confirm the latest health snapshot."
        )

        return "\n".join(lines)

    def _generate_consolidated_report(self) -> str:
        """Generate comprehensive consolidated report combining all tool outputs."""
        # Log data source context
        audit_tier = getattr(self, "current_audit_tier", None)
        if audit_tier:
            logger.info(
                f"[REPORT GENERATION] Generating consolidated_report.txt using data from Tier {audit_tier} audit"
            )
        else:
            logger.info(
                f"[REPORT GENERATION] Generating consolidated_report.txt using cached data (no active audit)"
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

        lines: List[str] = []
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
        lines.append(f"> **Source**: `{source_cmd}`")
        if self.current_audit_tier:
            lines.append(f"> **Last Audit Tier**: {tier_name}")
        lines.append(
            "> **Generated by**: run_development_tools.py - AI Development Tools Runner"
        )
        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                return value if value.strip().endswith("%") else f"{value}%"
            return self._format_percentage(value, decimals)

        def to_float(value: Any) -> Optional[float]:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip("%")
                try:
                    return float(stripped)
                except ValueError:
                    return None
            return None

        def to_int(value: Any) -> Optional[int]:
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
        doc_coverage = doc_metrics_details.get(
            "coverage", metrics.get("doc_coverage")
        )

        missing_docs_raw = doc_metrics_details.get("missing", {})

        if isinstance(missing_docs_raw, dict):
            missing_docs_count = missing_docs_raw.get("count", 0)
            missing_docs_list = missing_docs_raw.get("files", {})
        else:
            missing_docs_count = to_int(missing_docs_raw) or 0
            missing_docs_list = {}
        doc_totals = doc_metrics_details.get("totals") or {}
        documented_functions = (
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

        doc_artifacts = (
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
        file_purposes = analyze_docs_data.get("file_purposes") or details.get(
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
        error_recommendations = error_details.get("recommendations") or []
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
        legacy_summary = getattr(self, "legacy_cleanup_summary", None) or legacy_data or {}

        # Get missing docstrings count for consolidated report
        func_metrics_details_for_undoc = (
            function_metrics.get("details", {})
            if isinstance(function_metrics, dict)
            else {}
        )
        func_undocumented = func_metrics_details_for_undoc.get("undocumented", 0)

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

        # Recalculate doc_coverage if Unknown
        if doc_coverage == "Unknown" or doc_coverage is None:
            function_data_for_coverage = self._load_tool_data(
                "analyze_functions", "functions"
            )
            if isinstance(function_data_for_coverage, dict):
                func_details_for_coverage = function_data_for_coverage.get(
                    "details", {}
                )
                func_total_for_coverage = func_details_for_coverage.get(
                    "total_functions"
                ) or function_data_for_coverage.get("total_functions")
                func_undocumented_for_coverage = func_details_for_coverage.get(
                    "undocumented", 0
                ) or function_data_for_coverage.get("undocumented", 0)
                if (
                    func_total_for_coverage
                    and isinstance(func_total_for_coverage, (int, float))
                    and func_total_for_coverage > 0
                ):
                    func_documented_for_coverage = (
                        func_total_for_coverage - func_undocumented_for_coverage
                    )
                    coverage_pct = (
                        func_documented_for_coverage / func_total_for_coverage
                    ) * 100
                    if 0 <= coverage_pct <= 100:
                        doc_coverage = f"{coverage_pct:.2f}%"
                    else:
                        doc_coverage = "Unknown"
                else:
                    doc_coverage = "Unknown"
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

        error_cov = error_metrics.get("analyze_error_handling") or error_metrics.get(
            "error_handling_coverage"
        )
        missing_error_handlers_for_summary = to_int(
            error_metrics.get("functions_missing_error_handling", 0)
        )
        error_total = error_metrics.get("total_functions")
        error_with_handling = error_metrics.get("functions_with_error_handling")

        if error_total and error_with_handling:
            calc_coverage = (error_with_handling / error_total) * 100
            if 0 <= calc_coverage <= 100:
                error_cov = calc_coverage
        elif error_cov is None and error_total and error_with_handling:
            error_cov = (error_with_handling / error_total) * 100

        if error_cov is not None:
            lines.append(
                f"- Error handling coverage {percent_text(error_cov, 1)}; {missing_error_handlers_for_summary or 0} functions need protection"
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
            doc_sync_summary_for_signals = {
                "status": self.docs_sync_summary.get("status", "UNKNOWN"),
                "path_drift_issues": self.docs_sync_summary.get("path_drift_issues", 0),
                "paired_doc_issues": self.docs_sync_summary.get("paired_doc_issues", 0),
                "ascii_issues": self.docs_sync_summary.get("ascii_issues", 0),
                "heading_numbering_issues": self.docs_sync_summary.get(
                    "heading_numbering_issues", 0
                ),
                "missing_address_issues": self.docs_sync_summary.get(
                    "missing_address_issues", 0
                ),
                "unconverted_link_issues": self.docs_sync_summary.get(
                    "unconverted_link_issues", 0
                ),
                "path_drift_files": self.docs_sync_summary.get("path_drift_files", []),
            }

        if not doc_sync_summary_for_signals:
            doc_sync_result = self._load_tool_data("analyze_documentation_sync", "docs")
            if doc_sync_result:
                cached_metrics = doc_sync_result if isinstance(doc_sync_result, dict) else {}
                summary = cached_metrics.get("summary", {}) if isinstance(cached_metrics, dict) else {}
                details = cached_metrics.get("details", {}) if isinstance(cached_metrics, dict) else {}
                doc_sync_summary_for_signals = {
                    "status": summary.get("status", "UNKNOWN"),
                    "path_drift_issues": details.get("path_drift_issues", 0),
                    "paired_doc_issues": details.get("paired_doc_issues", 0),
                    "ascii_issues": details.get("ascii_issues", 0),
                    "path_drift_files": details.get("path_drift_files", []),
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
                if "summary" in effective_summary and isinstance(
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
                        for f, v in data_dict.items():
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
                    for i, file_path in enumerate(missing_files[:5]):
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
            # Use function_metrics already loaded at start of function (line 1232)
            func_metrics_details_for_docstatus = (
                function_metrics.get("details", {})
                if isinstance(function_metrics, dict)
                else {}
            )
            total_funcs_docstatus = (
                func_metrics_details_for_docstatus.get("total_functions")
                or function_metrics.get("total_functions")
                if isinstance(function_metrics, dict)
                else None
            )
            undocumented_funcs_docstatus = (
                func_metrics_details_for_docstatus.get("undocumented", 0)
                or function_metrics.get("undocumented", 0)
                if isinstance(function_metrics, dict)
                else 0
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
                lines.append("- **Status**: No overlaps detected (analysis performed)")
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

        if coverage_summary and isinstance(coverage_summary, dict):
            overall = coverage_summary.get("overall") or {}
            lines.append(
                f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} ({overall.get('covered')} of {overall.get('statements')} statements)"
            )
            lines.append(
                "    - **Coverage Scope**: Main project domains (`core`, `communication`, `ui`, `tasks`, `user`, `ai`) only; `development_tools/` is tracked separately."
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
                lines.append(
                    f"    - **Detailed Report**: [TEST_COVERAGE_REPORT.md](development_docs/TEST_COVERAGE_REPORT.md)"
                )

            # Development tools coverage
            dev_tools_insights = self._get_dev_tools_coverage_insights()
            if dev_tools_insights and dev_tools_insights.get("overall_pct") is not None:
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
                obvious = by_category.get("obvious_unused")
                if obvious:
                    lines.append(f"    - **Obvious Removals**: {obvious} imports")
                type_only = by_category.get("type_hints_only")
                if type_only:
                    lines.append(f"    - **Type-Only Imports**: {type_only} imports")

                # Add top files with unused imports
                from collections import defaultdict
                import json

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
                        total_files_with_issues = summary.get(
                            "files_affected", 0
                        )
                    else:
                        total_files_with_issues = len(file_counts)
                    if total_files_with_issues > 5:
                        file_list.append(f"... +{total_files_with_issues - 5}")
                    lines.append(f"    - **Top files**: {', '.join(file_list)}")

                report_path = (
                    self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
                )
                if isinstance(report_path, Path) and report_path.exists():
                    rel_path = report_path.relative_to(self.project_root)
                    lines.append(
                        f"- **Detailed Report**: [UNUSED_IMPORTS_REPORT.md]({rel_path.as_posix()})"
                    )
            else:
                lines.append("- **Unused Imports**: CLEAN (no unused imports detected)")
        else:
            lines.append(
                "- **Unused Imports**: Data unavailable (run `audit --full` for latest scan)"
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
                for pattern_type, file_list in findings.items():
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
                    rel_path = report_path_obj.relative_to(self.project_root)
                    lines.append(
                        f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({rel_path.as_posix()})"
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
                rel_path = legacy_report.relative_to(self.project_root)
                lines.append(
                    f"- **Detailed Report**: [LEGACY_REFERENCE_REPORT.md]({rel_path.as_posix()})"
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
            if not critical_examples and "critical_complexity_examples" in decision_metrics:
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
            lines.append(f"- **Registry Gaps**: 0 items missing from registry")

        # Function Docstring Coverage
        if not func_undocumented and total_funcs and doc_coverage:
            doc_coverage_float = (
                float(doc_coverage.replace("%", ""))
                if isinstance(doc_coverage, str)
                else doc_coverage
            )
            if doc_coverage_float < 100 and total_funcs:
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
                f"   - **Functions Missing Docstrings**: 0 functions need docstrings"
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
        lines.append(
            f"- **Duplicate Function Groups**: {duplicate_groups} groups across {duplicate_files} files"
        )
        if isinstance(duplicate_details, dict):
            cache_stats = duplicate_details.get("cache", {})
            if isinstance(cache_stats, dict):
                total_files = cache_stats.get("total_files", 0) or 0
                cached_files = cache_stats.get("cached_files", 0) or 0
                scanned_files = cache_stats.get("scanned_files", 0) or 0
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
                    return (func_count, max_score)

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
                if circular_deps > 0:
                    lines.append(
                        f"- **Circular Dependencies**: {circular_deps} circular dependency chains detected"
                    )
                if high_coupling > 0:
                    lines.append(
                        f"- **High Coupling**: {high_coupling} modules with high coupling"
                    )
            elif circular_deps == 0 and high_coupling == 0 and patterns_data:
                lines.append("## Dependency Patterns")
                lines.append(
                    "- **Status**: CLEAN (no circular dependencies or high coupling detected)"
                )

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
            recommendations = config_validation_summary.get("recommendations", [])
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

        # System Signals
        lines.append("## System Signals")

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

                    if signals_result:
                        if "data" in signals_result:
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
            results_file_path = (self.audit_config or {}).get(
                "results_file",
                "development_tools/reports/analysis_detailed_results.json",
            )
        except (ImportError, AttributeError, KeyError):
            ai_status_path = "development_tools/AI_STATUS.md"
            ai_priorities_path = "development_tools/AI_PRIORITIES.md"
            results_file_path = "development_tools/reports/analysis_detailed_results.json"

        lines.append(f"- Latest AI status: [AI_STATUS.md]({ai_status_path})")
        lines.append(
            f"- Current AI priorities: [AI_PRIORITIES.md]({ai_priorities_path})"
        )
        lines.append(
            f"- Detailed JSON results: [analysis_detailed_results.json]({results_file_path})"
        )

        legacy_report = (
            self.project_root / "development_docs" / "LEGACY_REFERENCE_REPORT.md"
        )
        if legacy_report.exists():
            rel_path = legacy_report.relative_to(self.project_root)
            lines.append(
                f"- Legacy reference report: [LEGACY_REFERENCE_REPORT.md]({rel_path.as_posix()})"
            )

        coverage_report = (
            self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
        )
        if coverage_report.exists():
            rel_path = coverage_report.relative_to(self.project_root)
            lines.append(
                f"- Test coverage report: [TEST_COVERAGE_REPORT.md]({rel_path.as_posix()})"
            )

        unused_imports_report = (
            self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"
        )
        if unused_imports_report.exists():
            rel_path = unused_imports_report.relative_to(self.project_root)
            lines.append(
                f"- Unused imports detail: [UNUSED_IMPORTS_REPORT.md]({rel_path.as_posix()})"
            )

        archive_dir = self.project_root / "development_tools" / "reports" / "archive"
        if archive_dir.exists():
            lines.append(f"- Historical audit data: development_tools/reports/archive")

        lines.append("")

        return "\n".join(lines)

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues from audit results"""
        issues = []
        if "analyze_functions" in self.results_cache:
            metrics = self.results_cache["analyze_functions"]
            if "coverage" in metrics:
                try:
                    coverage = float(metrics["coverage"].replace("%", ""))
                    if coverage < 90:
                        issues.append(f"Low documentation coverage: {coverage}%")
                except:
                    pass
        if hasattr(self, "_last_failed_audits"):
            for audit in self._last_failed_audits:
                issues.append(f"Failed audit: {audit}")
        return issues

    def _generate_action_items(self) -> List[str]:
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
                except:
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
