"""
Tool wrapper methods for AIToolsService.

Contains methods for running analysis, generation, and fix tools.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import output storage
from ..output_storage import save_tool_result

# Script registry - maps tool names to their file paths
SCRIPT_REGISTRY = {
    "analyze_documentation": "docs/analyze_documentation.py",
    "analyze_function_registry": "functions/analyze_function_registry.py",
    "analyze_module_dependencies": "imports/analyze_module_dependencies.py",
    "analyze_config": "config/analyze_config.py",
    "decision_support": "reports/decision_support.py",
    "analyze_documentation_sync": "docs/analyze_documentation_sync.py",
    "analyze_path_drift": "docs/analyze_path_drift.py",
    "analyze_missing_addresses": "docs/analyze_missing_addresses.py",
    "analyze_ascii_compliance": "docs/analyze_ascii_compliance.py",
    "analyze_heading_numbering": "docs/analyze_heading_numbering.py",
    "analyze_unconverted_links": "docs/analyze_unconverted_links.py",
    "generate_directory_tree": "docs/generate_directory_tree.py",
    "analyze_error_handling": "error_handling/analyze_error_handling.py",
    "generate_error_handling_report": "error_handling/generate_error_handling_report.py",
    "analyze_functions": "functions/analyze_functions.py",
    "analyze_duplicate_functions": "functions/analyze_duplicate_functions.py",
    "analyze_function_patterns": "functions/analyze_function_patterns.py",
    "analyze_package_exports": "functions/analyze_package_exports.py",
    "generate_function_registry": "functions/generate_function_registry.py",
    "generate_module_dependencies": "imports/generate_module_dependencies.py",
    "analyze_module_imports": "imports/analyze_module_imports.py",
    "analyze_dependency_patterns": "imports/analyze_dependency_patterns.py",
    "fix_legacy_references": "legacy/fix_legacy_references.py",
    "analyze_legacy_references": "legacy/analyze_legacy_references.py",
    "generate_legacy_reference_report": "legacy/generate_legacy_reference_report.py",
    "quick_status": "reports/quick_status.py",
    "run_test_coverage": "tests/run_test_coverage.py",
    "analyze_test_coverage": "tests/analyze_test_coverage.py",
    "generate_test_coverage_report": "tests/generate_test_coverage_report.py",
    "analyze_test_markers": "tests/analyze_test_markers.py",
    "analyze_unused_imports": "imports/analyze_unused_imports.py",
    "generate_unused_imports_report": "imports/generate_unused_imports_report.py",
    "analyze_ai_work": "ai_work/analyze_ai_work.py",
    "fix_version_sync": "docs/fix_version_sync.py",
    "fix_documentation": "docs/fix_documentation.py",
    "analyze_system_signals": "reports/analyze_system_signals.py",
    "cleanup_project": "shared/fix_project_cleanup.py",
}


class ToolWrappersMixin:
    """Mixin class providing tool execution methods to AIToolsService."""

    exclusion_config: Dict[str, bool]
    project_root: Path

    def run_script(self, script_name: str, *args, timeout: Optional[int] = 300) -> Dict:
        """Run a registered helper script from development_tools."""
        script_rel_path = SCRIPT_REGISTRY.get(script_name)
        if not script_rel_path:
            return {
                "success": False,
                "output": "",
                "error": f"Script '{script_name}' is not registered",
            }
        script_path = Path(__file__).resolve().parent.parent.parent / script_rel_path
        if not script_path.exists():
            return {
                "success": False,
                "output": "",
                "error": f"Registered script '{script_name}' not found at {script_rel_path}",
            }
        cmd = [sys.executable, str(script_path)] + list(args)
        env = os.environ.copy()
        env["MHM_DEV_TOOLS_RUN"] = "1"
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=timeout,
                env=env,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Script '{script_name}' timed out after {timeout // 60 if timeout else 'N/A'} minutes",
                "returncode": None,
            }

    def run_analyze_documentation(self, include_overlap: bool = False) -> Dict:
        """Run analyze_documentation with structured JSON handling."""
        logger.info("Analyzing documentation...")
        args = ["--json"]
        if include_overlap:
            args.append("--overlap")

        # Before running, check if we have cached overlap data to preserve
        cached_overlap_data = None
        cached_overlap_in_details = False
        cached_has_section_overlaps = False
        cached_has_consolidation = False
        if not include_overlap:
            try:
                from ..output_storage import load_tool_result

                cached_data = load_tool_result(
                    "analyze_documentation",
                    "docs",
                    project_root=self.project_root,
                    normalize=False,
                )
                if cached_data and isinstance(cached_data, dict):
                    cached_data_dict = cached_data.get("data", cached_data)
                    details = cached_data_dict.get("details", {})
                    has_section_overlaps = (
                        "section_overlaps" in cached_data_dict
                        or "section_overlaps" in details
                    )
                    has_consolidation = (
                        "consolidation_recommendations" in cached_data_dict
                        or "consolidation_recommendations" in details
                    )
                    if has_section_overlaps or has_consolidation:
                        cached_has_section_overlaps = has_section_overlaps
                        cached_has_consolidation = has_consolidation
                        cached_overlap_in_details = (
                            "section_overlaps" in details
                            or "consolidation_recommendations" in details
                        )
                        cached_overlap_data = {
                            "section_overlaps": (
                                details.get("section_overlaps")
                                if cached_overlap_in_details
                                else cached_data_dict.get("section_overlaps")
                            ),
                            "consolidation_recommendations": (
                                details.get("consolidation_recommendations")
                                if cached_overlap_in_details
                                else cached_data_dict.get(
                                    "consolidation_recommendations"
                                )
                            ),
                        }
            except Exception as e:
                logger.debug(f"Failed to load cached overlap data: {e}")

        result = self.run_script("analyze_documentation", *args)
        output = result.get("output", "")
        data = None
        if output:
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                data = None
        if data is not None:
            # If we have cached overlap data and new data doesn't include it, merge it in
            if cached_overlap_data and not include_overlap:
                details = data.get("details", {})
                has_overlap = (
                    "section_overlaps" in data
                    or "consolidation_recommendations" in data
                    or "section_overlaps" in details
                    or "consolidation_recommendations" in details
                )
                if not has_overlap:
                    if cached_overlap_in_details:
                        if "details" not in data:
                            data["details"] = {}
                        if cached_has_section_overlaps:
                            data["details"]["section_overlaps"] = cached_overlap_data.get(
                                "section_overlaps", {}
                            )
                        if cached_has_consolidation:
                            data["details"]["consolidation_recommendations"] = (
                                cached_overlap_data.get("consolidation_recommendations", [])
                            )
                        data["details"]["overlap_data_source"] = "cached"
                    else:
                        if cached_has_section_overlaps:
                            data["section_overlaps"] = cached_overlap_data.get(
                                "section_overlaps", {}
                            )
                        if cached_has_consolidation:
                            data["consolidation_recommendations"] = cached_overlap_data.get(
                                "consolidation_recommendations", []
                            )
                        if "details" not in data:
                            data["details"] = {}
                        data["details"]["overlap_data_source"] = "cached"
                    logger.debug(
                        "Preserved cached overlap analysis data in new results"
                    )
            result["data"] = data
            self.results_cache["analyze_documentation"] = data
            try:
                save_tool_result(
                    "analyze_documentation",
                    "docs",
                    data,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_documentation result: {e}")
            result["issues_found"] = bool(
                data.get("duplicates")
                or data.get("placeholders")
                or data.get("missing")
            )
            result["success"] = True
            result["error"] = ""
        else:
            lowered = output.lower() if isinstance(output, str) else ""
            if not result.get("success") and (
                "verbatim duplicate" in lowered or "placeholder" in lowered
            ):
                result["issues_found"] = True
                result["success"] = True
                result["error"] = ""
        return result

    def run_analyze_function_registry(self) -> Dict:
        """Run analyze_function_registry with structured JSON handling."""
        logger.info("Analyzing function registry...")
        result = self.run_script("analyze_function_registry", "--json")
        stderr_output = result.get("error", "")
        if stderr_output:
            logger.info(f"analyze_function_registry stderr output: {stderr_output}")
            if "Traceback" in stderr_output or 'File "' in stderr_output:
                logger.error(
                    f"analyze_function_registry traceback found in stderr:\n{stderr_output}"
                )
            if not result.get("success"):
                original_error = result.get("error", "")
                result["error"] = (
                    f"{original_error}\nStderr: {stderr_output}"
                    if original_error != stderr_output
                    else stderr_output
                )
        output = result.get("output", "")
        data = None
        if output:
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                data = None
        if data is not None:
            result["data"] = data
            try:
                save_tool_result(
                    "analyze_function_registry",
                    "functions",
                    data,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_function_registry result: {e}")
            missing = (
                data.get("missing", {})
                if isinstance(data.get("missing"), dict)
                else data.get("missing")
            )
            extra = (
                data.get("extra", {})
                if isinstance(data.get("extra"), dict)
                else data.get("extra")
            )
            errors = data.get("errors") or []
            missing_count = (
                missing.get("count") if isinstance(missing, dict) else missing
            )
            extra_count = extra.get("count") if isinstance(extra, dict) else extra
            result["issues_found"] = bool(missing_count or extra_count or errors)
            result["success"] = True
            result["error"] = ""
        else:
            lowered = output.lower() if isinstance(output, str) else ""
            if (
                "missing from registry" in lowered
                or "missing items" in lowered
                or "extra functions" in lowered
            ):
                result["issues_found"] = True
                result["success"] = True
                result["error"] = ""
        return result

    def run_analyze_module_dependencies(self) -> Dict:
        """Run analyze_module_dependencies and capture dependency drift summary."""
        logger.info("Analyzing module dependencies...")
        result = self.run_script("analyze_module_dependencies")
        output = result.get("output", "")
        summary = self._parse_module_dependency_report(output)
        if summary:
            missing_dependencies = summary.get("missing_dependencies", 0)
            missing_sections = summary.get("missing_sections", [])
            total_issues = (
                missing_dependencies + len(missing_sections)
                if isinstance(missing_sections, list)
                else missing_dependencies
            )
            standard_format = {
                "summary": {"total_issues": total_issues, "files_affected": 0},
                "details": summary,
            }
            result["data"] = standard_format
            try:
                save_tool_result(
                    "analyze_module_dependencies",
                    "imports",
                    standard_format,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to save analyze_module_dependencies result: {e}"
                )
            issues = summary.get("missing_dependencies", 0)
            issues = issues or len(summary.get("missing_sections") or [])
            result["issues_found"] = bool(issues)
            if "success" not in result:
                result["success"] = True
            self.module_dependency_summary = summary
            self.results_cache["analyze_module_dependencies"] = summary
        return result

    def run_analyze_functions(self) -> Dict:
        """Run analyze_functions with structured JSON handling."""
        logger.info("Analyzing functions...")
        args = ["--json"]
        if self.exclusion_config.get("include_tests", False):
            args.append("--include-tests")
        if self.exclusion_config.get("include_dev_tools", False):
            args.append("--include-dev-tools")
        result = self.run_script("analyze_functions", *args)
        if result.get("success") and result.get("output"):
            try:
                json_data = json.loads(result["output"])
                result["data"] = json_data
                if "analyze_functions" in self.results_cache:
                    extracted_metrics_raw = self.results_cache["analyze_functions"]
                    if "details" in extracted_metrics_raw and isinstance(
                        extracted_metrics_raw.get("details"), dict
                    ):
                        extracted_metrics = extracted_metrics_raw["details"]
                    else:
                        extracted_metrics = extracted_metrics_raw
                    if "critical_complexity_examples" in extracted_metrics:
                        json_data["details"]["critical_complexity_examples"] = (
                            extracted_metrics["critical_complexity_examples"]
                        )
                    if "high_complexity_examples" in extracted_metrics:
                        json_data["details"]["high_complexity_examples"] = (
                            extracted_metrics["high_complexity_examples"]
                        )
                    if "undocumented_examples" in extracted_metrics:
                        json_data["details"]["undocumented_examples"] = (
                            extracted_metrics["undocumented_examples"]
                        )
                try:
                    save_tool_result(
                        "analyze_functions",
                        "functions",
                        json_data,
                        project_root=self.project_root,
                    )
                    self.results_cache["analyze_functions"] = json_data
                except Exception as e:
                    logger.warning(f"Failed to save analyze_functions result: {e}")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse analyze_functions JSON output: {e}")
        return result

    def run_analyze_duplicate_functions(
        self, min_overall: Optional[float] = None, min_name: Optional[float] = None
    ) -> Dict:
        """Run analyze_duplicate_functions with structured JSON handling."""
        logger.info("Analyzing duplicate functions...")
        args = ["--json"]
        if self.exclusion_config.get("include_tests", False):
            args.append("--include-tests")
        if self.exclusion_config.get("include_dev_tools", False):
            args.append("--include-dev-tools")
        if min_overall is not None:
            args.extend(["--min-overall", str(min_overall)])
        if min_name is not None:
            args.extend(["--min-name", str(min_name)])
        result = self.run_script("analyze_duplicate_functions", *args)
        output = result.get("output", "")
        data = None
        if output:
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                data = None
        if data is not None:
            result["data"] = data
            try:
                save_tool_result(
                    "analyze_duplicate_functions",
                    "functions",
                    data,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to save analyze_duplicate_functions result: {e}"
                )
            summary = data.get("summary", {}) if isinstance(data, dict) else {}
            result["issues_found"] = bool(summary.get("total_issues", 0))
            result["success"] = True
            result["error"] = ""
        return result

    def run_decision_support(self) -> Dict:
        """Run decision_support with structured JSON handling."""
        logger.info("Running decision_support...")
        args = []
        if self.exclusion_config.get("include_tests", False):
            args.append("--include-tests")
        if self.exclusion_config.get("include_dev_tools", False):
            args.append("--include-dev-tools")
        result = self.run_script("decision_support", *args)
        self._extract_decision_insights(result)
        try:
            data = None
            if "decision_support" in self.results_cache:
                data = self.results_cache["decision_support"]
            elif result.get("data"):
                data = result.get("data")
            elif result.get("output"):
                try:
                    data = json.loads(result.get("output", ""))
                except (json.JSONDecodeError, TypeError):
                    data = None
            if data is not None:
                try:
                    from ..result_format import normalize_to_standard_format

                    data = normalize_to_standard_format("decision_support", data)
                    save_tool_result(
                        "decision_support",
                        "reports",
                        data,
                        project_root=self.project_root,
                    )
                except ValueError as e:
                    logger.error(f"Invalid decision_support result format: {e}")
                    error_result = self._create_standard_format_result(
                        0, 0, None, {"error": str(e)}
                    )
                    save_tool_result(
                        "decision_support",
                        "reports",
                        error_result,
                        project_root=self.project_root,
                    )
            else:
                error_result = self._create_standard_format_result(
                    0, 0, None, {"error": "decision_support produced no JSON output"}
                )
                save_tool_result(
                    "decision_support",
                    "reports",
                    error_result,
                    project_root=self.project_root,
                )
        except Exception as save_error:
            logger.error(
                f"Failed to save decision_support results: {save_error}", exc_info=True
            )
        return result

    def run_analyze_function_patterns(self) -> Dict:
        """Run analyze_function_patterns and save results."""
        logger.info("Analyzing function patterns...")
        try:
            from development_tools.functions.analyze_function_patterns import (
                analyze_function_patterns,
            )
            from development_tools.functions.analyze_functions import (
                scan_all_python_files,
            )

            actual_functions = scan_all_python_files()
            patterns = analyze_function_patterns(actual_functions)
            standard_format = {
                "summary": {"total_issues": 0, "files_affected": 0},
                "details": patterns,
            }
            save_tool_result(
                "analyze_function_patterns",
                "functions",
                standard_format,
                project_root=self.project_root,
            )
            return {
                "success": True,
                "data": standard_format,  # Return standard_format to match what was saved
            }
        except Exception as e:
            logger.warning(f"Failed to run analyze_function_patterns: {e}")
            return {"success": False, "error": str(e)}

    def run_analyze_module_imports(self) -> Dict:
        """Run analyze_module_imports and save results."""
        logger.info("Analyzing module imports...")
        try:
            from development_tools.imports.analyze_module_imports import (
                ModuleImportAnalyzer,
            )

            analyzer = ModuleImportAnalyzer(project_root=str(self.project_root))
            import_data = analyzer.scan_all_python_files()
            standard_format = {
                "summary": {"total_issues": 0, "files_affected": 0},
                "details": import_data,
            }
            save_tool_result(
                "analyze_module_imports",
                "imports",
                standard_format,
                project_root=self.project_root,
            )
            # Cache for downstream tools in the same audit run (e.g., dependency patterns).
            self.results_cache["analyze_module_imports"] = standard_format
            return {"success": True, "data": standard_format}
        except Exception as e:
            logger.warning(f"Failed to run analyze_module_imports: {e}")
            return {"success": False, "error": str(e)}

    def run_analyze_dependency_patterns(self) -> Dict:
        """Run analyze_dependency_patterns and save results."""
        logger.info("Analyzing dependency patterns...")
        try:
            from development_tools.imports.analyze_module_imports import (
                ModuleImportAnalyzer,
            )
            from development_tools.imports.analyze_dependency_patterns import (
                DependencyPatternAnalyzer,
            )
            actual_imports = None
            cached_module_imports = self.results_cache.get("analyze_module_imports")
            if isinstance(cached_module_imports, dict):
                details = cached_module_imports.get("details")
                if isinstance(details, dict):
                    actual_imports = details
                elif cached_module_imports:
                    actual_imports = cached_module_imports
            if not actual_imports:
                import_analyzer = ModuleImportAnalyzer(project_root=str(self.project_root))
                actual_imports = import_analyzer.scan_all_python_files()
            pattern_analyzer = DependencyPatternAnalyzer()
            patterns = pattern_analyzer.analyze_dependency_patterns(actual_imports)
            standard_format = {
                "summary": {"total_issues": 0, "files_affected": 0},
                "details": patterns,
            }
            save_tool_result(
                "analyze_dependency_patterns",
                "imports",
                standard_format,
                project_root=self.project_root,
            )
            return {"success": True, "data": standard_format}
        except Exception as e:
            logger.warning(f"Failed to run analyze_dependency_patterns: {e}")
            return {"success": False, "error": str(e)}

    def run_analyze_package_exports(self) -> Dict:
        """Run analyze_package_exports and save results."""
        logger.info("Analyzing package exports...")
        try:
            from development_tools.functions.analyze_package_exports import (
                generate_audit_report,
                analyze_imports_for_packages,
                parse_function_registry_for_packages,
                scan_package_modules_for_packages,
            )
            from concurrent.futures import ThreadPoolExecutor, as_completed

            packages = ["core", "communication", "ui", "tasks", "ai", "user"]
            all_reports = {}
            max_workers = min(6, len(packages))
            import_usage_index = analyze_imports_for_packages(packages)
            package_api_index = scan_package_modules_for_packages(packages)
            registry_index = parse_function_registry_for_packages(packages)
            logger.info(
                f"Analyzing package exports with parallel package scanning ({len(packages)} packages, {max_workers} workers)..."
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_package = {
                    executor.submit(
                        generate_audit_report,
                        package,
                        False,
                        import_usage_index,
                        package_api_index,
                        registry_index,
                    ): package
                    for package in packages
                }
                for future in as_completed(future_to_package):
                    package = future_to_package[future]
                    try:
                        report = future.result()
                        if isinstance(report, dict):
                            for key, value in report.items():
                                if isinstance(value, set):
                                    report[key] = sorted(value)
                                elif isinstance(value, dict):
                                    for nested_key, nested_value in value.items():
                                        if isinstance(nested_value, set):
                                            value[nested_key] = sorted(nested_value)
                        all_reports[package] = report
                        if isinstance(report, dict):
                            logger.info(
                                f"Package export audit complete: {package} "
                                f"(missing={len(report.get('missing_exports', []))}, "
                                f"unnecessary={len(report.get('potentially_unnecessary', []))})"
                            )
                    except Exception as e:
                        logger.warning(f"Failed to audit package {package}: {e}")
                        all_reports[package] = {
                            "package": package,
                            "error": str(e),
                            "missing_exports": [],
                            "potentially_unnecessary": [],
                        }
            total_missing = sum(
                len(r.get("missing_exports", [])) for r in all_reports.values()
            )
            total_unnecessary = sum(
                len(r.get("potentially_unnecessary", [])) for r in all_reports.values()
            )
            packages_with_missing = sum(
                1 for r in all_reports.values() if r.get("missing_exports")
            )
            total_issues = total_missing + total_unnecessary
            result_data = {
                "summary": {
                    "total_issues": total_issues,
                    "files_affected": packages_with_missing,
                },
                "details": {
                    "total_missing_exports": total_missing,
                    "total_unnecessary_exports": total_unnecessary,
                    "packages_with_missing": packages_with_missing,
                    "packages": all_reports,
                },
            }
            self.results_cache["analyze_package_exports"] = result_data
            save_tool_result(
                "analyze_package_exports",
                "functions",
                result_data,
                project_root=self.project_root,
            )
            return {"success": True, "data": result_data}
        except Exception as e:
            logger.warning(f"Failed to run analyze_package_exports: {e}")
            return {"success": False, "error": str(e)}

    def run_analyze_error_handling(self) -> Dict:
        """Run analyze_error_handling with structured JSON handling."""
        args = ["--json"]
        if self.exclusion_config.get("include_tests", False):
            args.append("--include-tests")
        if self.exclusion_config.get("include_dev_tools", False):
            args.append("--include-dev-tools")
        result = self.run_script("analyze_error_handling", *args)
        output = result.get("output", "")
        stderr_output = result.get("error", "")
        # Log errors for debugging
        if stderr_output and not result.get("success", False):
            logger.warning(
                f"analyze_error_handling stderr: {stderr_output[:500]}"
            )  # Log first 500 chars
            if "Traceback" in stderr_output or "Error" in stderr_output:
                logger.error(f"analyze_error_handling error details:\n{stderr_output}")
        data = None
        if output:
            try:
                lines = output.split("\n")
                json_start = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("{"):
                        json_start = i
                        break
                if json_start >= 0:
                    json_output = "\n".join(lines[json_start:])
                    data = json.loads(json_output)
                else:
                    data = json.loads(output)
            except json.JSONDecodeError:
                data = None
        # If JSON parsing failed, try loading from standardized output storage
        # BUT: Only use cached data if the script actually succeeded (returncode == 0)
        # If the script failed, don't perpetuate stale cached data by saving it back
        script_succeeded = (
            result.get("success", False) and result.get("returncode") == 0
        )
        if data is None and script_succeeded:
            try:
                from ..output_storage import load_tool_result

                data = load_tool_result(
                    "analyze_error_handling",
                    "error_handling",
                    project_root=self.project_root,
                )
            except (OSError, json.JSONDecodeError):
                data = None
        if data is not None:
            result["data"] = data
            # Only save if we got data from the script output (script succeeded)
            # Don't save cached data back when script failed - that perpetuates stale data
            if script_succeeded:
                try:
                    save_tool_result(
                        "analyze_error_handling",
                        "error_handling",
                        data,
                        project_root=self.project_root,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save analyze_error_handling result: {e}")
            coverage = data.get("analyze_error_handling") or data.get(
                "error_handling_coverage", 0
            )
            missing_count = data.get("functions_missing_error_handling", 0)
            result["issues_found"] = coverage < 80 or missing_count > 0
            # Only mark as successful if script actually succeeded
            # If we're using cached data from a failed run, keep success=False
            if script_succeeded:
                result["success"] = True
                result["error"] = ""
        else:
            lowered = output.lower() if isinstance(output, str) else ""
            if "missing error handling" in lowered or "coverage" in lowered:
                result["issues_found"] = True
                result["success"] = True
                result["error"] = ""
        return result

    def run_analyze_documentation_sync(self) -> Dict:
        """Run analyze_documentation_sync with structured data handling."""
        try:
            if self._run_doc_sync_check():
                summary_payload = self.docs_sync_summary or {}
                summary = (
                    summary_payload.get("summary", {})
                    if isinstance(summary_payload, dict)
                    else {}
                )
                details = (
                    summary_payload.get("details", {})
                    if isinstance(summary_payload, dict)
                    else {}
                )
                all_results = getattr(self, "docs_sync_results", {}).get(
                    "all_results", {}
                )
                path_drift_files = details.get("path_drift_files", [])
                data = {
                    "summary": {
                        "total_issues": summary.get("total_issues", 0),
                        "files_affected": (
                            len(path_drift_files)
                            if isinstance(path_drift_files, list)
                            else 0
                        ),
                        "status": summary.get("status", "UNKNOWN"),
                    },
                    "details": {
                        "paired_doc_issues": details.get("paired_doc_issues", 0),
                        "path_drift_issues": details.get("path_drift_issues", 0),
                        "ascii_compliance_issues": details.get("ascii_issues", 0),
                        "heading_numbering_issues": details.get(
                            "heading_numbering_issues", 0
                        ),
                        "missing_address_issues": details.get(
                            "missing_address_issues", 0
                        ),
                        "unconverted_link_issues": details.get(
                            "unconverted_link_issues", 0
                        ),
                        "path_drift_files": path_drift_files,
                        "paired_docs": all_results.get("paired_docs", {}),
                        "path_drift": all_results.get("path_drift", {}),
                        "ascii_compliance": all_results.get("ascii_compliance", {}),
                        "heading_numbering": all_results.get("heading_numbering", {}),
                        "missing_addresses": all_results.get("missing_addresses", {}),
                        "unconverted_links": all_results.get("unconverted_links", {}),
                    },
                }
                import io
                import sys

                output_buffer = io.StringIO()
                original_stdout = sys.stdout
                sys.stdout = output_buffer
                try:
                    from development_tools.docs.analyze_documentation_sync import (
                        DocumentationSyncChecker,
                    )

                    checker = DocumentationSyncChecker()
                    report_results = {
                        "summary": data["summary"],
                        "details": {
                            "paired_doc_issues": data["details"].get(
                                "paired_doc_issues", 0
                            ),
                            "paired_docs": data["details"].get("paired_docs", {}),
                        },
                    }
                    checker.print_report(report_results)
                    output = output_buffer.getvalue()
                finally:
                    sys.stdout = original_stdout
                try:
                    save_tool_result(
                        "analyze_documentation_sync",
                        "docs",
                        data,
                        project_root=self.project_root,
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to save analyze_documentation_sync result: {e}"
                    )
                return {
                    "success": True,
                    "output": output,
                    "error": "",
                    "returncode": 0,
                    "data": data,
                }
            else:
                return {
                    "success": False,
                    "error": "Documentation sync check failed",
                    "output": "",
                    "returncode": 1,
                }
        except Exception as e:
            logger.error(f"Error running documentation sync: {e}", exc_info=True)
            return {"success": False, "error": str(e), "output": "", "returncode": 1}

    def run_analyze_path_drift(self) -> Dict:
        """Run analyze_path_drift with structured data handling."""
        try:
            from development_tools.docs.analyze_path_drift import PathDriftAnalyzer

            analyzer = PathDriftAnalyzer()
            structured_results = analyzer.run_analysis()
            # run_analysis() always returns standard format with 'summary', 'files', and 'details' keys
            summary = structured_results.get("summary", {})
            files = (
                structured_results.get("files", {})
                if isinstance(structured_results, dict)
                else {}
            )
            total_issues = summary.get("total_issues", 0)
            details = (
                structured_results.get("details", {})
                if isinstance(structured_results, dict)
                else {}
            )
            data = self._create_standard_format_result(
                total_issues,
                len(files) if isinstance(files, dict) else 0,
                files if isinstance(files, dict) else {},
                details,
            )
            import io
            import sys

            output_buffer = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = output_buffer
            try:
                if total_issues > 0:
                    print(f"\nPath Drift Issues:")
                    print(f"   Total files with issues: {len(files)}")
                    print(f"   Total issues found: {total_issues}")
                    print(f"   Top files with most issues:")
                    sorted_files = sorted(
                        files.items(), key=lambda x: x[1], reverse=True
                    )
                    for doc_file, issue_count in sorted_files[:5]:
                        print(f"     {doc_file}: {issue_count} issues")
                else:
                    print("\nNo path drift issues found!")
                output = output_buffer.getvalue()
            finally:
                sys.stdout = original_stdout
            try:
                save_tool_result(
                    "analyze_path_drift", "docs", data, project_root=self.project_root
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_path_drift result: {e}")
            return {
                "success": True,
                "output": output,
                "error": "",
                "returncode": 0,
                "data": data,
            }
        except Exception as e:
            logger.error(f"Error running path drift analyzer: {e}", exc_info=True)
            result = self.run_script("analyze_path_drift", "--json")
            try:

                def path_drift_converter(file_data: Dict[str, Any]) -> Dict[str, Any]:
                    files_with_issues = {}
                    detailed_issues = {}
                    total_issues = 0
                    for file_path, file_info in file_data.items():
                        if isinstance(file_info, dict):
                            results = file_info.get("results", [])
                            if results:
                                files_with_issues[file_path] = len(results)
                                detailed_issues[file_path] = results
                                total_issues += len(results)
                    return {
                        "files": files_with_issues,
                        "total_issues": total_issues,
                        "detailed_issues": detailed_issues,
                    }

                data = self._load_mtime_cached_tool_results(
                    "analyze_path_drift",
                    "docs",
                    result,
                    self._parse_path_drift_output,
                    path_drift_converter,
                )
                if data:
                    result["data"] = data
                    result["success"] = True
                    result["error"] = ""
                else:
                    result["success"] = False
                    result["error"] = f"Failed to load path drift results: {e}"
            except Exception as helper_error:
                logger.debug(
                    f"Failed to use unified helper for path drift fallback: {helper_error}"
                )
                output = result.get("output", "")
                data = None
                if output:
                    try:
                        data = json.loads(output)
                    except json.JSONDecodeError:
                        data = self._parse_path_drift_output(output)
                if data:
                    try:
                        save_tool_result(
                            "analyze_path_drift",
                            "docs",
                            data,
                            project_root=self.project_root,
                        )
                    except Exception as save_error:
                        logger.warning(
                            f"Failed to save analyze_path_drift result: {save_error}"
                        )
                    result["data"] = data
                    result["success"] = True
                    result["error"] = ""
                else:
                    result["success"] = False
                    result["error"] = f"Failed to parse path drift output: {e}"
            return result

    def run_generate_legacy_reference_report(self) -> Dict:
        """Run generate_legacy_reference_report to create LEGACY_REFERENCE_REPORT.md."""
        logger.info("Generating legacy reference report...")
        # First, ensure we have legacy reference analysis results
        legacy_data = None
        if hasattr(self, "legacy_cleanup_summary") and self.legacy_cleanup_summary:
            legacy_data = self.legacy_cleanup_summary
        else:
            # Try to load from cache
            try:
                legacy_result = self._load_tool_data(
                    "analyze_legacy_references", "legacy", log_source=False
                )
                if legacy_result and isinstance(legacy_result, dict):
                    legacy_data = legacy_result
            except Exception as e:
                logger.debug(f"Failed to load legacy data for report generation: {e}")

        if not legacy_data:
            return {
                "success": False,
                "output": "",
                "error": "No legacy reference analysis data available. Run analyze_legacy_references first.",
                "returncode": 1,
            }

        # Prepare findings file
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            findings_file = f.name
            details = (
                legacy_data.get("details", {}) if isinstance(legacy_data, dict) else {}
            )
            findings = details.get("findings")
            if findings is None:
                return {
                    "success": False,
                    "output": "",
                    "error": "Legacy reference results missing details.findings.",
                    "returncode": 1,
                }
            json.dump(findings, f, indent=2)

        try:
            script_path = (
                Path(__file__).resolve().parent.parent.parent
                / "legacy"
                / "generate_legacy_reference_report.py"
            )
            output_file = "development_docs/LEGACY_REFERENCE_REPORT.md"
            cmd = [
                sys.executable,
                str(script_path),
                "--findings-file",
                findings_file,
                "--output-file",
                output_file,
            ]
            env = os.environ.copy()
            env["MHM_DEV_TOOLS_RUN"] = "1"
            result_proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300,
                env=env,
            )
            # Clean up temp file
            try:
                Path(findings_file).unlink()
            except Exception:
                pass

            return {
                "success": result_proc.returncode == 0,
                "output": result_proc.stdout,
                "error": result_proc.stderr,
                "returncode": result_proc.returncode,
            }
        except subprocess.TimeoutExpired:
            try:
                Path(findings_file).unlink()
            except Exception:
                pass
            return {
                "success": False,
                "output": "",
                "error": "generate_legacy_reference_report timed out after 5 minutes",
                "returncode": None,
            }
        except Exception as e:
            try:
                Path(findings_file).unlink()
            except Exception:
                pass
            return {
                "success": False,
                "output": "",
                "error": f"generate_legacy_reference_report failed: {e}",
                "returncode": None,
            }

    def run_generate_test_coverage_report(self) -> Dict:
        """Run generate_test_coverage_report to generate TEST_COVERAGE_REPORT.md from existing coverage data.

        This tool generates TEST_COVERAGE_REPORT.md, HTML, and JSON reports from existing coverage.json.
        It should be run after run_test_coverage has executed tests and collected coverage data.
        """
        logger.info("Generating test coverage report from existing coverage data...")

        # Check if coverage.json exists
        coverage_json = (
            self.project_root
            / "development_tools"
            / "tests"
            / "jsons"
            / "coverage.json"
        )
        if not coverage_json.exists():
            error_msg = "coverage.json not found. Run run_test_coverage first to generate coverage data."
            logger.warning(f"Test coverage data not found: {error_msg}")
            return {"success": False, "output": "", "error": error_msg, "returncode": 1}

        # Run the report generator with --update-plan to generate TEST_COVERAGE_REPORT.md
        try:
            result = self.run_script(
                "generate_test_coverage_report", "--update-plan", timeout=300
            )
            if result.get("success"):
                test_coverage_report = (
                    self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
                )
                if test_coverage_report.exists():
                    logger.info(
                        f"Test coverage report generated: {test_coverage_report.relative_to(self.project_root)}"
                    )
                    return {
                        "success": True,
                        "output": f"TEST_COVERAGE_REPORT.md generated successfully",
                        "error": "",
                        "returncode": 0,
                    }
                else:
                    logger.warning(
                        "Report generation completed but TEST_COVERAGE_REPORT.md not found"
                    )
                    return result
            else:
                # Log the actual error for debugging
                error_msg = result.get("error", "Unknown error")
                output_msg = result.get("output", "")
                logger.warning(f"generate_test_coverage_report failed: {error_msg}")
                if output_msg:
                    logger.debug(f"Script output: {output_msg[:500]}")
                return result
        except Exception as e:
            logger.error(f"Failed to generate test coverage report: {e}", exc_info=True)
            return {
                "success": False,
                "output": "",
                "error": f"generate_test_coverage_report failed: {e}",
                "returncode": None,
            }

    def run_analyze_legacy_references(self) -> Dict:
        """Run analyze_legacy_references with structured data handling."""
        try:
            from development_tools.legacy.analyze_legacy_references import (
                LegacyReferenceAnalyzer,
            )

            analyzer = LegacyReferenceAnalyzer(project_root=str(self.project_root))
            findings = analyzer.scan_for_legacy_references()
            total_files = sum(len(files) for files in findings.values())
            total_markers = sum(
                len(matches) for files in findings.values() for _, _, matches in files
            )
            cache_stats = getattr(analyzer, "cache_stats", {}) or {}
            cache_hits = int(cache_stats.get("hits", 0) or 0)
            cache_misses = int(cache_stats.get("misses", 0) or 0)
            total_cache_checks = cache_hits + cache_misses
            if total_cache_checks == 0:
                cache_mode = "unknown"
            elif cache_hits > 0 and cache_misses == 0:
                cache_mode = "cache_only"
            elif cache_hits > 0 and cache_misses > 0:
                cache_mode = "partial_cache"
            else:
                cache_mode = "cold_scan"
            serializable_findings = {}
            for pattern_type, file_list in findings.items():
                serializable_findings[pattern_type] = [
                    [file_path, content, matches]
                    for file_path, content, matches in file_list
                ]
            standard_format = {
                "summary": {
                    "total_issues": total_markers,
                    "files_affected": total_files,
                },
                "details": {
                    "findings": serializable_findings,
                    "files_with_issues": total_files,
                    "legacy_markers": total_markers,
                    "report_path": "development_docs/LEGACY_REFERENCE_REPORT.md",
                    "cache": {
                        "cache_mode": cache_mode,
                        "hits": cache_hits,
                        "misses": cache_misses,
                        "total_cache_checks": total_cache_checks,
                        "hit_rate": round((cache_hits / total_cache_checks) * 100, 1)
                        if total_cache_checks
                        else 0.0,
                    },
                },
            }
            try:
                save_tool_result(
                    "analyze_legacy_references",
                    "legacy",
                    standard_format,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_legacy_references result: {e}")
            # Store in legacy_cleanup_summary for report generation
            self.legacy_cleanup_summary = standard_format
            # Also store in results_cache
            if not hasattr(self, "results_cache"):
                self.results_cache = {}
            self.results_cache["analyze_legacy_references"] = standard_format
            if not hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata["analyze_legacy_references"] = (
                standard_format.get("details", {}).get("cache", {})
            )

            return {
                "success": True,
                "output": f"Found {total_markers} legacy markers in {total_files} files",
                "error": "",
                "returncode": 0,
                "data": standard_format,
            }
        except Exception as e:
            logger.error(
                f"Error running legacy references analyzer: {e}", exc_info=True
            )
            return {"success": False, "error": str(e), "output": "", "returncode": 1}

    def run_analyze_unused_imports(self) -> Dict:
        """Run analyze_unused_imports with structured JSON handling (analysis only)."""
        script_path = (
            Path(__file__).resolve().parent.parent.parent
            / "imports"
            / "analyze_unused_imports.py"
        )
        # Run with --json flag only (report generation is now separate)
        cmd = [sys.executable, str(script_path), "--json"]
        env = os.environ.copy()
        env["MHM_DEV_TOOLS_RUN"] = "1"
        try:
            result_proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=1200,
                env=env,
            )
            result = {
                "success": result_proc.returncode == 0,
                "output": result_proc.stdout,
                "error": result_proc.stderr,
                "returncode": result_proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Unused imports checker timed out after 20 minutes",
                "returncode": None,
                "issues_found": False,
            }
        output = result.get("output", "")
        data = None
        if output:
            # Try to find JSON in output (may be mixed with other text)
            # JSON is printed first, so look for the first complete JSON object
            output_lines = output.strip().split("\n")
            json_start = None

            # Find the start of JSON (first line with '{')
            for i, line in enumerate(output_lines):
                stripped = line.strip()
                if stripped.startswith("{"):
                    json_start = i
                    logger.debug(f"Found JSON start at line {i}: {stripped[:50]}...")
                    break

            if json_start is not None:
                # Find the matching closing brace by counting braces
                # Start with 1 because we found the opening brace
                brace_count = 1
                json_end = None
                for i in range(json_start + 1, len(output_lines)):
                    line = output_lines[i]
                    brace_count += line.count("{") - line.count("}")
                    if brace_count == 0:
                        json_end = i + 1
                        logger.debug(
                            f"Found JSON end at line {i+1}, total lines: {json_end - json_start}"
                        )
                        break

                if json_end is not None:
                    json_output = "\n".join(output_lines[json_start:json_end])
                    try:
                        data = json.loads(json_output)
                        logger.info(
                            f"Successfully parsed JSON output from analyze_unused_imports ({len(str(data))} chars, {len(json_output)} chars raw)"
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to parse JSON output from analyze_unused_imports: {e}"
                        )
                        logger.debug(
                            f"JSON section preview (first 500 chars): {json_output[:500]}"
                        )
                        data = None
                else:
                    logger.warning(
                        f"analyze_unused_imports: Found JSON start at line {json_start} but couldn't find matching closing brace (searched {len(output_lines) - json_start} lines, brace_count ended at {brace_count})"
                    )
            else:
                # Try parsing entire output as JSON (fallback)
                try:
                    data = json.loads(output)
                    logger.debug(
                        f"Successfully parsed JSON output from analyze_unused_imports ({len(str(data))} chars)"
                    )
                except json.JSONDecodeError as e:
                    logger.warning(
                        f"Failed to parse JSON output from analyze_unused_imports: {e}"
                    )
                    logger.debug(f"Output preview (first 500 chars): {output[:500]}")
                    data = None
        else:
            logger.warning(
                f"analyze_unused_imports returned empty output (returncode: {result.get('returncode')})"
            )
        if data is not None:
            details = data.get("details", {}) if isinstance(data, dict) else {}
            stats = details.get("stats", {}) if isinstance(details, dict) else {}
            cache_hits = int(stats.get("cache_hits", 0) or 0)
            cache_misses = int(stats.get("cache_misses", 0) or 0)
            files_scanned = int(stats.get("files_scanned", 0) or 0)
            # Some analyzer modes report cache_misses as 0; derive misses from files_scanned when possible.
            if files_scanned > 0 and cache_misses == 0 and files_scanned >= cache_hits:
                cache_misses = files_scanned - cache_hits
            total_cache_checks = cache_hits + cache_misses
            if total_cache_checks == 0:
                cache_mode = "unknown"
            elif cache_hits > 0 and cache_misses == 0:
                cache_mode = "cache_only"
            elif cache_hits > 0 and cache_misses > 0:
                cache_mode = "partial_cache"
            else:
                cache_mode = "cold_scan"
            cache_metadata = {
                "cache_mode": cache_mode,
                "hits": cache_hits,
                "misses": cache_misses,
                "total_cache_checks": total_cache_checks,
                "hit_rate": round((cache_hits / total_cache_checks) * 100, 1)
                if total_cache_checks
                else 0.0,
            }
            if isinstance(details, dict):
                details["_cache_metadata"] = cache_metadata
            if isinstance(data, dict):
                data["_cache_metadata"] = cache_metadata
            result["data"] = data
            self.results_cache["analyze_unused_imports"] = data
            if not hasattr(self, "_tool_cache_metadata"):
                self._tool_cache_metadata = {}
            self._tool_cache_metadata["analyze_unused_imports"] = cache_metadata
            # Extract total_unused from standard format (summary.total_issues)
            total_unused = (
                data.get("summary", {}).get("total_issues", 0)
                if isinstance(data, dict) and "summary" in data
                else data.get("total_unused", 0)
            )
            result["issues_found"] = total_unused > 0
            result["success"] = True
            result["error"] = ""
            try:
                save_tool_result(
                    "analyze_unused_imports",
                    "imports",
                    data,
                    project_root=self.project_root,
                )
            except Exception as e:
                logger.warning(f"Failed to save analyze_unused_imports result: {e}")
                import traceback

                logger.debug(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning(
                f"analyze_unused_imports: No data extracted, skipping save_tool_result()"
            )
            if not result.get("error"):
                result["error"] = "No parseable JSON output from analyze_unused_imports"
            result["success"] = False
        return result

    def run_generate_unused_imports_report(self) -> Dict:
        """Run generate_unused_imports_report to generate markdown report from analysis results."""
        logger.info("Generating unused imports report...")
        tools_run = getattr(self, "_tools_run_in_current_tier", None)
        if tools_run is None:
            tools_run = set()
            setattr(self, "_tools_run_in_current_tier", tools_run)
        if "analyze_unused_imports" not in tools_run:
            logger.info("Running unused imports analysis before generating the report.")
            analysis_result = self.run_unused_imports()
            if not analysis_result.get("success", False):
                logger.warning(
                    "Unused imports analysis failed; the report will use cached data (if available)."
                )
        script_path = (
            Path(__file__).resolve().parent.parent.parent
            / "imports"
            / "generate_unused_imports_report.py"
        )
        cmd = [
            sys.executable,
            str(script_path),
            "--project-root",
            str(self.project_root),
        ]

        env = os.environ.copy()
        env["MHM_DEV_TOOLS_RUN"] = "1"
        try:
            result_proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60,
                env=env,
            )
            result = {
                "success": result_proc.returncode == 0,
                "output": result_proc.stdout,
                "error": result_proc.stderr,
                "returncode": result_proc.returncode,
            }
            if result["success"]:
                logger.info("Unused imports report generated successfully")
            else:
                logger.warning(
                    f"Unused imports report generation completed with issues: {result.get('error', 'Unknown error')}"
                )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Unused imports report generation timed out after 1 minute",
                "returncode": None,
            }
        except Exception as e:
            logger.error(f"Error generating unused imports report: {e}", exc_info=True)
            return {"success": False, "error": str(e), "output": "", "returncode": 1}
        return result
