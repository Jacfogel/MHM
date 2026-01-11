"""
Data loading and parsing methods for AIToolsService.

Contains methods for loading tool results, parsing output, and aggregating data.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import utilities for helper functions
# Note: Uses self._create_standard_format_result method instead of imported function


class DataLoadingMixin:
    """Mixin class providing data loading and parsing methods to AIToolsService."""
    
    def _load_tool_data(self, tool_name: str, domain: Optional[str] = None, log_source: bool = True) -> Dict[str, Any]:
        """
        Unified data loading helper with consistent fallback chain.
        
        Loads tool data from multiple sources in order of preference:
        1. results_cache (in-memory, current audit run)
        2. load_tool_result() (standardized storage, recent run)
        3. Central aggregation file (analysis_detailed_results.json, cached)
        
        All data is normalized to standard format before returning.
        
        Args:
            tool_name: Name of the tool (e.g., 'analyze_functions')
            domain: Domain directory (e.g., 'functions'). If None, inferred from tool_name
            log_source: If True, log the data source at INFO level for report generation
            
        Returns:
            Dict containing tool data in standard format, or empty dict if not found
        """
        # Determine if we're in an active audit (should have current data)
        is_active_audit = hasattr(self, 'current_audit_tier') and self.current_audit_tier is not None
        audit_tier = getattr(self, 'current_audit_tier', None)
        
        # Check if this tool was actually run in the current audit tier
        tools_run_in_tier = getattr(self, '_tools_run_in_current_tier', set())
        tool_was_run = tool_name in tools_run_in_tier
        
        # Step 1: Check results_cache (in-memory, current audit run)
        # CRITICAL: Only use cache if tool was actually run in current tier to avoid stale data
        if tool_was_run and hasattr(self, 'results_cache') and self.results_cache:
            cached_data = self.results_cache.get(tool_name)
            if cached_data and isinstance(cached_data, dict):
                if log_source:
                    logger.debug(f"[DATA SOURCE] {tool_name}: loaded from current audit run (Tier {audit_tier})")
                # Normalize before returning
                from ..result_format import normalize_to_standard_format
                normalized = normalize_to_standard_format(tool_name, cached_data)
                return normalized
        
        # Step 2: Fallback to standardized storage (recent run)
        # CRITICAL: Do NOT store in results_cache - this is cached data, not current audit run data
        # Storing it would cause future calls to incorrectly log "current audit run"
        try:
            from ..output_storage import load_tool_result
            stored_data = load_tool_result(tool_name, domain, project_root=self.project_root, normalize=True)
            if stored_data and isinstance(stored_data, dict):
                if log_source:
                    logger.debug(f"[DATA SOURCE] {tool_name}: loaded from standardized storage (cached)")
                # Do NOT store in results_cache - this is cached data, not from current audit run
                return stored_data
        except Exception as e:
            logger.debug(f"Failed to load {tool_name} from standardized storage: {e}")
        
        # Step 3: Fallback to central aggregation file (cached)
        # CRITICAL: Do NOT store in results_cache - this is cached data, not current audit run data
        # Skip in test directories to prevent loading large files
        try:
            # Check if we're in a test directory (use method from AuditOrchestrationMixin if available)
            is_test_dir = False
            if hasattr(self, '_is_test_directory'):
                is_test_dir = self._is_test_directory(self.project_root)
            
            if is_test_dir:
                return {}
            
            results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                if 'results' in cached_data and tool_name in cached_data['results']:
                    tool_data = cached_data['results'][tool_name]
                    # Handle nested data structure: results.tool_name.data
                    if 'data' in tool_data:
                        data = tool_data['data']
                        if log_source:
                            logger.debug(f"[DATA SOURCE] {tool_name}: loaded from central aggregation file (cached)")
                        # Normalize before returning
                        from ..result_format import normalize_to_standard_format
                        normalized = normalize_to_standard_format(tool_name, data)
                        # Do NOT store in results_cache - this is cached data, not from current audit run
                        return normalized
                    else:
                        # Some tools store data directly without 'data' wrapper
                        if log_source:
                            logger.debug(f"[DATA SOURCE] {tool_name}: loaded from central aggregation file (cached, direct)")
                        # Normalize before returning
                        from ..result_format import normalize_to_standard_format
                        normalized = normalize_to_standard_format(tool_name, tool_data)
                        # Do NOT store in results_cache - this is cached data, not from current audit run
                        return normalized
        except Exception as e:
            logger.debug(f"Failed to load {tool_name} from central aggregation file: {e}")
        
        # No data found in any source
        if log_source:
            logger.warning(f"[DATA SOURCE] {tool_name}: no data found in any source (using empty fallback)")
        return {}
    
    def _get_canonical_metrics(self) -> Dict[str, Any]:
        """Provide consistent totals across downstream documents."""
        results_cache = self.results_cache or {}
        fd_metrics_raw = results_cache.get('analyze_functions', {}) or {}
        
        # Handle standard format - extract details if present
        if 'details' in fd_metrics_raw and isinstance(fd_metrics_raw.get('details'), dict):
            fd_metrics = fd_metrics_raw['details']
        else:
            fd_metrics = fd_metrics_raw

        ds_metrics = results_cache.get('decision_support_metrics', {}) or {}

        audit_data = results_cache.get('analyze_function_registry', {}) or {}
        
        # Handle standard format for audit_data
        if 'details' in audit_data and isinstance(audit_data.get('details'), dict):
            audit_data_details = audit_data['details']
            audit_totals = audit_data_details.get('totals') if isinstance(audit_data_details, dict) else {}
        else:
            audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}
        if audit_totals is None or not isinstance(audit_totals, dict):
            audit_totals = {}

        # PRIORITY: Always use analyze_functions as single source of truth (most accurate and consistent)
        # decision_support now uses the same categorization logic, so metrics should match
        # But we prioritize analyze_functions to ensure consistency
        total_functions = None

        # First priority: analyze_functions (single source of truth)
        # Check if fd_metrics is not empty (could be empty dict which is falsy)
        if fd_metrics and isinstance(fd_metrics, dict):
            total_functions = fd_metrics.get('total_functions')

        # Second priority: decision_support (should match analyze_functions now, but kept as fallback)
        # Note: decision_support now uses categorize_functions() from analyze_functions, so metrics should be consistent
        if total_functions is None:
            total_functions = ds_metrics.get('total_functions')

        # Last resort: analyze_function_registry (but only if it's reasonable)
        if total_functions is None and isinstance(audit_data, dict):
            # Check both standard format and legacy format
            if 'details' in audit_data:
                audit_total = audit_data['details'].get('totals', {}).get('functions_found')
            else:
                audit_total = audit_data.get('total_functions')
            if audit_total is not None and isinstance(audit_total, int) and audit_total > 100:
                total_functions = audit_total

        # Final fallback: audit_totals (but validate it's reasonable)
        if total_functions is None and isinstance(audit_totals, dict):
            registry_total = audit_totals.get('functions_found')
            if registry_total is not None and isinstance(registry_total, int) and registry_total > 100:
                total_functions = registry_total

        # Complexity metrics: prioritize analyze_functions (single source of truth)
        moderate = fd_metrics.get('moderate_complexity')
        if moderate is None:
            moderate = ds_metrics.get('moderate_complexity')

        high = fd_metrics.get('high_complexity')
        if high is None:
            high = ds_metrics.get('high_complexity')

        critical = fd_metrics.get('critical_complexity')
        if critical is None:
            critical = ds_metrics.get('critical_complexity')
        
        # If still missing, try loading from cache (skip in test directories to prevent memory issues)
        if total_functions is None or moderate is None or high is None or critical is None:
            try:
                # Skip in test directories to prevent loading large files
                # BUT: If we have data in results_cache, we should still return what we have
                is_test_dir = False
                if hasattr(self, '_is_test_directory'):
                    is_test_dir = self._is_test_directory(self.project_root)
                
                if is_test_dir:
                    # In test directories, return what we have from results_cache (don't load from disk)
                    # Don't return empty dict - return what we found so far, even if incomplete
                    # This allows tests to work with mocked data in results_cache
                    pass  # Continue to return statement at end of function
                
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            cached_metrics_raw = func_data['data']
                            # Handle standard format
                            if 'details' in cached_metrics_raw and isinstance(cached_metrics_raw.get('details'), dict):
                                cached_metrics = cached_metrics_raw['details']
                            else:
                                cached_metrics = cached_metrics_raw
                            if total_functions is None:
                                total_functions = cached_metrics.get('total_functions')
                            if moderate is None:
                                moderate = cached_metrics.get('moderate_complexity')
                            if high is None:
                                high = cached_metrics.get('high_complexity')
                            if critical is None:
                                critical = cached_metrics.get('critical_complexity')
                    
                    # Fallback to decision_support
                    if (total_functions is None or moderate is None or high is None or critical is None) and 'results' in cached_data:
                        if 'decision_support' in cached_data['results']:
                            ds_data = cached_data['results']['decision_support']
                            if 'data' in ds_data and 'decision_support_metrics' in ds_data['data']:
                                cached_ds_metrics = ds_data['data']['decision_support_metrics']
                                if total_functions is None:
                                    total_functions = cached_ds_metrics.get('total_functions')
                                if moderate is None:
                                    moderate = cached_ds_metrics.get('moderate_complexity')
                                if high is None:
                                    high = cached_ds_metrics.get('high_complexity')
                                if critical is None:
                                    critical = cached_ds_metrics.get('critical_complexity')
                    
                    # Fallback to analyze_function_registry - parse high_complexity array
                    if (high is None or critical is None) and 'results' in cached_data:
                        if 'analyze_function_registry' in cached_data['results']:
                            afr_data = cached_data['results']['analyze_function_registry']
                            if 'data' in afr_data and 'analysis' in afr_data['data']:
                                analysis = afr_data['data']['analysis']
                                high_complexity_array = analysis.get('high_complexity', [])
                                if isinstance(high_complexity_array, list):
                                    # Count by thresholds: MODERATE=50, HIGH=100, CRITICAL=200
                                    critical_count = sum(1 for f in high_complexity_array 
                                                        if isinstance(f, dict) and f.get('complexity', 0) >= 200)
                                    high_count = sum(1 for f in high_complexity_array 
                                                   if isinstance(f, dict) and 100 <= f.get('complexity', 0) < 200)
                                    if critical is None:
                                        critical = critical_count
                                    if high is None:
                                        high = high_count
                                    # For moderate, we'd need all functions, but we can estimate if we have total
                                    if moderate is None and total_functions is not None and isinstance(total_functions, int):
                                        moderate = max(0, total_functions - high_count - critical_count)
            except Exception as e:
                logger.debug(f"Failed to load metrics from cache in _get_canonical_metrics: {e}")
                pass

        doc_coverage = audit_data.get('doc_coverage') if isinstance(audit_data, dict) else None

        # Use analyze_functions for docstring coverage (consistent source)
        if doc_coverage is None:
            fd_metrics_raw = self.results_cache.get('analyze_functions', {}) or {}
            # Handle standard format
            if 'details' in fd_metrics_raw and isinstance(fd_metrics_raw.get('details'), dict):
                fd_metrics = fd_metrics_raw['details']
            else:
                fd_metrics = fd_metrics_raw
            func_total = fd_metrics.get('total_functions')
            func_undocumented = fd_metrics.get('undocumented', 0)
            
            if func_total is not None and func_total > 0:
                func_documented = func_total - func_undocumented
                coverage_pct = (func_documented / func_total) * 100
                if 0 <= coverage_pct <= 100:
                    doc_coverage = f"{coverage_pct:.2f}%"
                else:
                    doc_coverage = 'Unknown'
            else:
                doc_coverage = 'Unknown'

        # Validate any existing doc_coverage value and reject invalid ones
        if isinstance(doc_coverage, str):
            if '12690' in doc_coverage or 'Unknown' not in doc_coverage:
                try:
                    val_str = doc_coverage.strip('%').replace(',', '')
                    if val_str.replace('.', '').isdigit():
                        val = float(val_str)
                        if val > 100:
                            fd_metrics_raw = self.results_cache.get('analyze_functions', {}) or {}
                            if 'details' in fd_metrics_raw and isinstance(fd_metrics_raw.get('details'), dict):
                                fd_metrics = fd_metrics_raw['details']
                            else:
                                fd_metrics = fd_metrics_raw
                            func_total = fd_metrics.get('total_functions')
                            func_undocumented = fd_metrics.get('undocumented', 0)
                            if func_total is not None and func_total > 0:
                                func_documented = func_total - func_undocumented
                                coverage_pct = (func_documented / func_total) * 100
                                if 0 <= coverage_pct <= 100:
                                    doc_coverage = f"{coverage_pct:.2f}%"
                                else:
                                    doc_coverage = 'Unknown'
                            else:
                                doc_coverage = 'Unknown'
                except (ValueError, TypeError):
                    if '12690' in doc_coverage:
                        doc_coverage = 'Unknown'
        
        if doc_coverage is None or (isinstance(doc_coverage, str) and '12690' in doc_coverage):
            doc_coverage = 'Unknown'
        
        # Return metrics dict with all values
        return {
            'total_functions': total_functions if total_functions is not None else 'Unknown',
            'moderate': moderate if moderate is not None else 'Unknown',
            'high': high if high is not None else 'Unknown',
            'critical': critical if critical is not None else 'Unknown',
            'doc_coverage': doc_coverage
        }
    
    def _get_missing_doc_files(self, limit: int = 5) -> List[str]:
        """Return the top documentation files missing from the registry."""
        metrics = self.results_cache.get('analyze_function_registry', {})
        missing_files = []
        if isinstance(metrics, dict):
            missing_files = metrics.get('missing_files') or []
        if not isinstance(missing_files, list):
            return []
        return missing_files[:limit]
    
    def _get_system_status(self) -> str:
        """Get current system status"""
        status_lines = []
        status_lines.append("SYSTEM STATUS")
        status_lines.append("=" * 30)
        
        # Check key files (configurable for portability)
        for file_path in self.key_files:
            if Path(file_path).exists():
                status_lines.append(f"[OK] {file_path}")
            else:
                status_lines.append(f"[MISSING] {file_path}")
        
        # Check recent audit results
        results_file_name = (self.audit_config or {}).get('results_file', 'development_tools/reports/analysis_detailed_results.json')
        for prefix in ('ai_tools/', 'development_tools/'):
            if results_file_name.startswith(prefix):
                results_file_name = results_file_name[len(prefix):]
                break
        results_file = self.project_root / results_file_name
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                    timestamp = data.get('timestamp', 'Unknown')
                    status_lines.append(f"[AUDIT] Last audit: {timestamp}")
            except:
                status_lines.append("[AUDIT] Last audit: Unknown")
        else:
            status_lines.append("[AUDIT] No recent audit found")
        return '\n'.join(status_lines)
    
    def _load_coverage_summary(self) -> Optional[Dict[str, Any]]:
        """Load overall and per-module coverage metrics from coverage.json."""
        # Check development_tools/tests/jsons first (new location), then fall back to old location (legacy)
        coverage_path = self.project_root / "development_tools" / "tests" / "jsons" / "coverage.json"
        if not coverage_path.exists():
            # Fallback to old location (development_tools/tests/coverage.json) for backward compatibility
            coverage_path = self.project_root / "development_tools" / "tests" / "coverage.json"
        
        # If main file doesn't exist, check archive for most recent coverage.json (may have been rotated)
        if not coverage_path.exists():
            archive_dir = self.project_root / "development_tools" / "tests" / "jsons" / "archive"
            if archive_dir.exists():
                archived_files = sorted(
                    archive_dir.glob("coverage_*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                if archived_files:
                    coverage_path = archived_files[0]
                    logger.debug(f"[DATA SOURCE] coverage_summary: using archived file {coverage_path.name} (main file was rotated)")
        
        # Note: Removed project root fallback - coverage.json is always in development_tools/tests/jsons/
        # If not found there, it doesn't exist (coverage hasn't been run yet)
        
        # Log data source
        audit_tier = getattr(self, 'current_audit_tier', None)
        if coverage_path.exists():
            if audit_tier == 3:
                logger.debug(f"[DATA SOURCE] coverage_summary: loaded from {coverage_path.name} (current Tier 3 audit)")
            else:
                logger.debug(f"[DATA SOURCE] coverage_summary: loaded from {coverage_path.name} (cached)")
        else:
            # This is expected if coverage hasn't been run yet - use DEBUG instead of WARNING
            logger.debug(f"[DATA SOURCE] coverage_summary: not found at {coverage_path.relative_to(self.project_root)} (coverage not yet generated, using empty fallback)")
            return None
        try:
            with coverage_path.open('r', encoding='utf-8') as handle:
                coverage_data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        files = coverage_data.get('files')
        if not isinstance(files, dict) or not files:
            return None
        total_statements = 0
        total_covered = 0
        module_stats = defaultdict(lambda: {'statements': 0, 'covered': 0, 'missed': 0})
        worst_files: List[Dict[str, Any]] = []
        for path, info in files.items():
            summary = info.get('summary') or {}
            statements = summary.get('num_statements') or 0
            covered = summary.get('covered_lines') or 0
            missed = summary.get('missing_lines')
            if missed is None:
                missed = max(statements - covered, 0)
            total_statements += statements
            total_covered += covered
            parts = path.replace('/', '\\').split('\\')
            module_name = parts[0] if parts and parts[0] else 'root'
            module_entry = module_stats[module_name]
            module_entry['statements'] += statements
            module_entry['covered'] += covered
            module_entry['missed'] += missed
            if statements > 0:
                coverage_pct = round((covered / statements) * 100, 1)
            else:
                coverage_pct = 0.0
            worst_files.append({
                'path': path.replace('\\', '/'),
                'coverage': coverage_pct,
                'missing': missed
            })
        if total_statements == 0:
            overall_coverage = 0.0
        else:
            overall_coverage = round((total_covered / total_statements) * 100, 1)
        module_list: List[Dict[str, Any]] = []
        for module_name, stats in module_stats.items():
            statements = stats['statements']
            if statements == 0:
                coverage_pct = 0.0
            else:
                coverage_pct = round((stats['covered'] / statements) * 100, 1)
            module_list.append({
                'module': module_name.replace('\\', '/'),
                'coverage': coverage_pct,
                'missed': stats['missed']
            })
        module_list.sort(key=lambda item: item['coverage'])
        worst_files.sort(key=lambda item: item['coverage'])
        meta = coverage_data.get('meta', {})
        timestamp = meta.get('timestamp')
        return {
            'overall': {
                'coverage': overall_coverage,
                'statements': total_statements,
                'covered': total_covered,
                'missed': max(total_statements - total_covered, 0),
                'generated': timestamp
            },
            'modules': module_list,
            'worst_files': worst_files[:5]
        }
    
    def _load_config_validation_summary(self) -> Optional[Dict[str, Any]]:
        """Load config validation summary from JSON file."""
        try:
            config_file = self.project_root / "development_tools" / "config" / "jsons" / "analyze_config_results.json"
            if config_file.exists():
                audit_tier = getattr(self, 'current_audit_tier', None)
                if audit_tier == 2 or audit_tier == 3:
                    logger.debug(f"[DATA SOURCE] config_validation_summary: loaded from {config_file.name} (current Tier {audit_tier} audit)")
                else:
                    logger.debug(f"[DATA SOURCE] config_validation_summary: loaded from {config_file.name} (cached)")
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle standard format (summary/details) and legacy formats
                    if 'summary' in data and 'details' in data:
                        top_summary = data['summary']
                        details = data['details']
                        nested_summary = details.get('summary', {})
                        summary = {**top_summary, **nested_summary}
                        summary['recommendations'] = details.get('recommendations', [])
                        summary['tools_analysis'] = details.get('tools_analysis', {})
                        summary['config_valid'] = nested_summary.get('config_valid', summary.get('config_valid', False))
                        summary['config_complete'] = nested_summary.get('config_complete', summary.get('config_complete', False))
                        if 'validation' in details and summary.get('config_valid') is False:
                            validation = details['validation']
                            summary['config_valid'] = validation.get('config_structure_valid', False)
                        if 'completeness' in details and summary.get('config_complete') is False:
                            completeness = details['completeness']
                            summary['config_complete'] = completeness.get('sections_complete', False)
                        return summary
                    elif 'data' in data:
                        config_data = data['data']
                        if 'summary' in config_data and 'details' in config_data:
                            top_summary = config_data['summary']
                            details = config_data['details']
                            nested_summary = details.get('summary', {})
                            summary = {**top_summary, **nested_summary}
                            summary['recommendations'] = details.get('recommendations', [])
                            summary['tools_analysis'] = details.get('tools_analysis', {})
                            summary['config_valid'] = nested_summary.get('config_valid', summary.get('config_valid', False))
                            summary['config_complete'] = nested_summary.get('config_complete', summary.get('config_complete', False))
                            if 'validation' in details and summary.get('config_valid') is False:
                                validation = details['validation']
                                summary['config_valid'] = validation.get('config_structure_valid', False)
                            if 'completeness' in details and summary.get('config_complete') is False:
                                completeness = details['completeness']
                                summary['config_complete'] = completeness.get('sections_complete', False)
                            return summary
                        else:
                            summary = config_data.get('summary', {})
                            summary['recommendations'] = config_data.get('recommendations', [])
                            summary['tools_analysis'] = config_data.get('tools_analysis', {})
                            if 'config_validation' in config_data and summary.get('config_valid') is None:
                                config_validation = config_data['config_validation']
                                summary['config_valid'] = config_validation.get('config_structure_valid', False)
                            if 'completeness' in config_data and summary.get('config_complete') is None:
                                completeness = config_data['completeness']
                                summary['config_complete'] = completeness.get('sections_complete', False)
                            return summary
                    elif 'validation_results' in data:
                        validation_results = data.get('validation_results', {})
                        summary = validation_results.get('summary', {})
                        summary['recommendations'] = validation_results.get('recommendations', [])
                        summary['tools_analysis'] = validation_results.get('tools_analysis', {})
                        return summary
            else:
                logger.warning(f"[DATA SOURCE] config_validation_summary: not found at {config_file} (using empty fallback)")
        except Exception as e:
            logger.warning(f"[DATA SOURCE] config_validation_summary: failed to load - {e} (using empty fallback)")
        return None
    
    def _load_dev_tools_coverage(self) -> None:
        """Load dev tools coverage from JSON file if it exists."""
        # Check development_tools/tests/jsons first (new location), then fall back to old location (legacy)
        coverage_path = self.project_root / "development_tools" / "tests" / "jsons" / "coverage_dev_tools.json"
        if not coverage_path.exists():
            coverage_path = self.project_root / "development_tools" / "tests" / "coverage_dev_tools.json"
        if not coverage_path.exists():
            return
        try:
            with coverage_path.open('r', encoding='utf-8') as handle:
                coverage_data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        files = coverage_data.get('files')
        if not isinstance(files, dict) or not files:
            return
        total_statements = 0
        total_missed = 0
        for path, info in files.items():
            summary = info.get('summary') or {}
            statements = summary.get('num_statements') or 0
            missed = summary.get('missing_lines') or 0
            total_statements += statements
            total_missed += missed
        if total_statements == 0:
            overall_coverage = 0.0
        else:
            overall_coverage = round((total_statements - total_missed) / total_statements * 100, 1)
        module_data = self._load_coverage_json(coverage_path)
        self.dev_tools_coverage_results = {
            'overall': {
                'overall_coverage': overall_coverage,
                'total_statements': total_statements,
                'total_missed': total_missed
            },
            'modules': module_data,
            'coverage_collected': True,
            'output_file': str(coverage_path),
            'html_dir': None
        }
    
    def _load_coverage_json(self, json_path: Path) -> Dict[str, Dict[str, Any]]:
        """Load module metrics from coverage JSON output."""
        try:
            with json_path.open('r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except (OSError, json.JSONDecodeError):
            return {}
        files = data.get('files', {})
        coverage_data: Dict[str, Dict[str, Any]] = {}
        for module_name, file_data in files.items():
            summary = file_data.get('summary', {})
            statements = int(summary.get('num_statements', 0))
            covered = int(summary.get('covered_lines', statements - summary.get('missing_lines', 0)))
            missed = int(summary.get('missing_lines', statements - covered))
            percent = summary.get('percent_covered')
            if isinstance(percent, float):
                percent_value = int(round(percent))
            else:
                try:
                    percent_value = int(percent)
                except (TypeError, ValueError):
                    percent_value = 0
            missing_lines = file_data.get('missing_lines', [])
            missing_line_strings = [str(line) for line in missing_lines]
            coverage_data[module_name] = {
                'statements': statements,
                'missed': missed,
                'coverage': percent_value,
                'missing_lines': missing_line_strings,
                'covered': covered
            }
        return coverage_data
    
    def _get_dev_tools_coverage_insights(self) -> Optional[Dict[str, Any]]:
        """Return summarized dev tools coverage insights."""
        results = getattr(self, 'dev_tools_coverage_results', None)
        if not results:
            return None
        modules = results.get('modules')
        if (not modules) and results.get('output_file'):
            try:
                modules = self._load_coverage_json(Path(results['output_file']))
            except Exception:
                modules = {}
        if not isinstance(modules, dict):
            modules = {}
        overall = results.get('overall') or {}
        overall_pct = overall.get('overall_coverage') or overall.get('coverage')
        total_statements = overall.get('total_statements')
        total_missed = overall.get('total_missed')
        if (total_statements is None or total_missed is None) and modules:
            total_statements = sum((data.get('statements') or 0) for data in modules.values())
            total_missed = sum((data.get('missed') or 0) for data in modules.values())
        covered = None
        if total_statements is not None and total_missed is not None:
            covered = max(total_statements - total_missed, 0)
        low_modules: List[Dict[str, Any]] = []
        if modules:
            sorted_modules = sorted(modules.items(), key=lambda kv: kv[1].get('coverage', 101))
            for name, data in sorted_modules:
                coverage_value = data.get('coverage')
                if coverage_value is None:
                    continue
                low_modules.append({
                    'path': name,
                    'coverage': coverage_value,
                    'missed': data.get('missed'),
                    'statements': data.get('statements')
                })
                if len(low_modules) == 3:
                    break
        return {
            'overall_pct': overall_pct,
            'statements': total_statements,
            'covered': covered,
            'html': results.get('html_dir'),
            'low_modules': low_modules,
            'module_count': len(modules),
        }
    
    def _parse_module_dependency_report(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract summary statistics from analyze_module_dependencies output."""
        if not output:
            return None
        summary: Dict[str, Any] = {}
        patterns = {
            'files_scanned': r"Files scanned:\s+(\d+)",
            'total_imports': r"Total imports found:\s+(\d+)",
            'documented_dependencies': r"Dependencies documented:\s+(\d+)",
            'standard_library': r"Standard library imports:\s+(\d+)",
            'third_party': r"Third-party imports:\s+(\d+)",
            'local_imports': r"Local imports:\s+(\d+)",
            'missing_dependencies': r"Total missing dependencies:\s+(\d+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                try:
                    summary[key] = int(match.group(1))
                except ValueError:
                    summary[key] = None
        missing_files = re.findall(r"\[FILE\]\s+([^:]+):", output)
        missing_sections = re.findall(r"\[DIR\]\s+(.+?) - ENTIRE FILE MISSING", output)
        if not summary and not missing_files and not missing_sections:
            return None
        summary['missing_files'] = missing_files
        summary['missing_sections'] = missing_sections
        return summary
    
    def _parse_test_results_from_output(self, output: str) -> Dict[str, Any]:
        """Parse test results from pytest output."""
        results = {
            'random_seed': None,
            'test_summary': None,
            'failed_tests': [],
            'passed_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'warnings_count': 0
        }
        if not output:
            return results
        # Extract random seed if pytest-randomly is used
        seed_pattern = r'--randomly-seed=(\d+)'
        seed_match = re.search(seed_pattern, output)
        if seed_match:
            results['random_seed'] = seed_match.group(1)
        # Extract test summary
        summary_pattern = r'(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+(\d+)\s+skipped[,\s]+(\d+)\s+warnings'
        summary_match = re.search(summary_pattern, output)
        if summary_match:
            results['failed_count'] = int(summary_match.group(1))
            results['passed_count'] = int(summary_match.group(2))
            results['skipped_count'] = int(summary_match.group(3))
            results['warnings_count'] = int(summary_match.group(4))
            results['test_summary'] = f"{results['failed_count']} failed, {results['passed_count']} passed, {results['skipped_count']} skipped, {results['warnings_count']} warnings"
        # Extract failed test names
        short_summary_pattern = r'short test summary info[^\n]*\n(.*?)(?=\n===|$)'
        short_summary_match = re.search(short_summary_pattern, output, re.DOTALL)
        if short_summary_match:
            summary_lines = short_summary_match.group(1).strip().split('\n')
            for line in summary_lines:
                if line.strip().startswith('FAILED'):
                    test_match = re.search(r'FAILED\s+(.+)', line)
                    if test_match:
                        results['failed_tests'].append(test_match.group(1).strip())
        return results
    
    def _parse_doc_sync_output(self, output: str) -> Dict[str, Any]:
        """Derive structured metrics from documentation sync output."""
        summary: Dict[str, Any] = {
            'status': None,
            'total_issues': None,
            'paired_doc_issues': None,
            'path_drift_issues': None,
            'ascii_issues': None,
            'path_drift_files': []
        }
        if not isinstance(output, str) or not output.strip():
            return summary
        lines_iter = output.splitlines()
        path_section = False
        for raw_line in lines_iter:
            line = raw_line.strip()
            if not line:
                if path_section:
                    path_section = False
                continue
            if line.startswith('Status:'):
                summary['status'] = line.split(':', 1)[1].strip() or None
                continue
            if line.startswith('Total Issues:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['total_issues'] = value
                continue
            if line.startswith('Paired Doc Issues:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['paired_doc_issues'] = value
                continue
            if line.startswith('Path Drift Issues:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['path_drift_issues'] = value
                continue
            if line.startswith('ASCII Compliance Issues:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['ascii_issues'] = value
                path_section = False
                continue
            if line.startswith('Heading Numbering Issues:'):
                path_section = False
                continue
            if line.startswith('Top files with most issues:'):
                path_section = True
                continue
            if (line.isupper() and ('ISSUES' in line or 'COMPLIANCE' in line or 'DOCUMENTATION' in line)) or \
               line.startswith('HEADING NUMBERING') or \
               line.startswith('ASCII COMPLIANCE') or \
               line.startswith('PAIRED DOCUMENTATION'):
                path_section = False
                continue
            if path_section:
                cleaned = line.lstrip('-*').strip()
                if not cleaned:
                    continue
                if ':' in cleaned:
                    file_part = cleaned.split(':', 1)[0].strip()
                else:
                    file_part = cleaned
                if file_part and file_part.isupper() and ('ISSUES' in file_part or 'COMPLIANCE' in file_part):
                    path_section = False
                    continue
                if file_part and file_part not in summary['path_drift_files']:
                    summary['path_drift_files'].append(file_part)
        return summary
    
    def _parse_documentation_sync_output(self, output: str) -> Dict[str, Any]:
        """Parse paired documentation sync output."""
        issues = {}
        if not isinstance(output, str) or not output.strip():
            return issues
        lines = output.splitlines()
        current_section = None
        for line in lines:
            line = line.strip()
            if 'PAIRED DOCUMENTATION ISSUES:' in line:
                current_section = 'paired_docs'
                continue
            if current_section == 'paired_docs' and line.startswith('   '):
                if ':' in line:
                    issue_type = line.split(':')[0].strip()
                    if issue_type not in issues:
                        issues[issue_type] = []
                elif line.startswith('     - '):
                    if current_section:
                        last_type = list(issues.keys())[-1] if issues else None
                        if last_type:
                            issues[last_type].append(line[7:])
        return issues
    
    def _parse_path_drift_output(self, output: str) -> Dict[str, Any]:
        """Parse path drift analysis output."""
        # Try to parse as JSON first
        if output.strip().startswith('{'):
            try:
                parsed = json.loads(output)
                from ..result_format import normalize_to_standard_format
                normalized = normalize_to_standard_format('analyze_path_drift', parsed)
                # Format conversion: Convert standard format to simplified format expected by aggregation code
                # The aggregation code in _aggregate_documentation_sync_results() expects:
                # {'files': {file: count}, 'total_issues': int}
                # TODO: Consider refactoring aggregation code to use standard format directly
                if 'summary' in normalized:
                    logger.debug("_parse_path_drift_output: Converting standard format to simplified format for aggregation")
                    return {
                        'files': normalized.get('files', {}),
                        'total_issues': normalized.get('summary', {}).get('total_issues', 0),
                        'detailed_issues': normalized.get('details', {}).get('detailed_issues', {})
                    }
                return normalized
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to text parsing if JSON parsing failed
        result = {'files': {}, 'total_issues': 0}
        if not isinstance(output, str) or not output.strip():
            return result
        lines = output.splitlines()
        in_files_section = False
        for line in lines:
            line = line.strip()
            if 'Total issues found:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['total_issues'] = value
            elif 'Top files with most issues:' in line:
                in_files_section = True
                continue
            elif in_files_section and ':' in line and line.endswith('issues'):
                parts = line.split(':')
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    issue_count = self._extract_first_int(parts[1])
                    if issue_count is not None:
                        result['files'][file_path] = issue_count
        return result
    
    def _parse_ascii_compliance_output(self, output: str) -> Dict[str, Any]:
        """Parse ASCII compliance check output. Returns standard format."""
        # Try to parse as JSON first
        if output.strip().startswith('{'):
            try:
                parsed = json.loads(output)
                from ..result_format import normalize_to_standard_format
                return normalize_to_standard_format("analyze_ascii_compliance", parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to text parsing if JSON parsing failed
        files = {}
        total_issues = 0
        file_count = 0
        if not isinstance(output, str) or not output.strip():
            return self._create_standard_format_result(total_issues, file_count, files)
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files with non-ASCII characters:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    file_count = value
            elif 'Total issues found:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    total_issues = value
            elif ':' in line and ('issues' in line.lower() or 'characters' in line.lower()):
                parts = line.split(':')
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    issue_text = parts[1].strip()
                    issue_count = self._extract_first_int(issue_text)
                    if issue_count is not None:
                        files[file_path] = issue_count
        return self._create_standard_format_result(total_issues, file_count, files)
    
    def _parse_heading_numbering_output(self, output: str) -> Dict[str, Any]:
        """Parse heading numbering check output. Returns standard format."""
        # Try to parse as JSON first
        if output.strip().startswith('{'):
            try:
                parsed = json.loads(output)
                from ..result_format import normalize_to_standard_format
                return normalize_to_standard_format(parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to text parsing if JSON parsing failed
        files = {}
        total_issues = 0
        file_count = 0
        if not isinstance(output, str) or not output.strip():
            return self._create_standard_format_result(total_issues, file_count, files)
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files with numbering issues:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    file_count = value
            elif 'Total issues found:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    total_issues = value
            elif ':' in line and 'issues' in line.lower():
                parts = line.split(':')
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    issue_count = self._extract_first_int(parts[1])
                    if issue_count is not None:
                        files[file_path] = issue_count
        return self._create_standard_format_result(total_issues, file_count, files)
    
    def _parse_missing_addresses_output(self, output: str) -> Dict[str, Any]:
        """Parse missing addresses check output."""
        # Try to parse as JSON first
        if output.strip().startswith('{'):
            try:
                parsed = json.loads(output)
                from ..result_format import normalize_to_standard_format
                return normalize_to_standard_format("analyze_missing_addresses", parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to text parsing if JSON parsing failed
        result = {'files': [], 'total_issues': 0}
        if not isinstance(output, str) or not output.strip():
            return result
        if 'All documentation files have file addresses!' in output:
            return result
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files missing addresses:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['total_issues'] = value
            elif line.startswith('- ') or line.startswith('  - '):
                file_path = line.lstrip('- ').strip()
                if file_path:
                    result['files'].append(file_path)
        return result
    
    def _parse_unconverted_links_output(self, output: str) -> Dict[str, Any]:
        """Parse unconverted links check output."""
        # Try to parse as JSON first
        if output.strip().startswith('{'):
            try:
                parsed = json.loads(output)
                from ..result_format import normalize_to_standard_format
                return normalize_to_standard_format("analyze_unconverted_links", parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        # Fall back to text parsing if JSON parsing failed
        result = {'files': {}, 'total_issues': 0}
        if not isinstance(output, str) or not output.strip():
            return result
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files with unconverted links:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['file_count'] = value
            elif 'Total issues found:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['total_issues'] = value
            elif ':' in line and 'issues' in line.lower():
                parts = line.split(':')
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    issue_count = self._extract_first_int(parts[1])
                    if issue_count is not None:
                        result['files'][file_path] = issue_count
        return result
    
    def _aggregate_doc_sync_results(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all documentation sync tools into unified summary."""
        summary: Dict[str, Any] = {
            'status': 'PASS',
            'total_issues': 0,
            'paired_doc_issues': 0,
            'path_drift_issues': 0,
            'ascii_issues': 0,
            'heading_numbering_issues': 0,
            'missing_address_issues': 0,
            'unconverted_link_issues': 0,
            'path_drift_files': []
        }
        # Aggregate paired docs
        paired_docs = all_results.get('paired_docs', {})
        if isinstance(paired_docs, dict):
            for issue_type, issues in paired_docs.items():
                if isinstance(issues, list):
                    summary['paired_doc_issues'] += len(issues)
                    summary['total_issues'] += len(issues)
        # Aggregate path drift
        path_drift = all_results.get('path_drift', {})
        if isinstance(path_drift, dict):
            summary['path_drift_issues'] = path_drift.get('total_issues', 0)
            summary['total_issues'] += summary['path_drift_issues']
            files = path_drift.get('files', {})
            if isinstance(files, dict):
                summary['path_drift_files'] = list(files.keys())[:10]
        # Aggregate ASCII compliance
        ascii_compliance = all_results.get('ascii_compliance', {})
        if isinstance(ascii_compliance, dict):
            summary['ascii_issues'] = ascii_compliance.get('total_issues', 0)
            summary['total_issues'] += summary['ascii_issues']
        # Aggregate heading numbering
        heading_numbering = all_results.get('heading_numbering', {})
        if isinstance(heading_numbering, dict):
            summary['heading_numbering_issues'] = heading_numbering.get('total_issues', 0)
            summary['total_issues'] += summary['heading_numbering_issues']
        # Aggregate missing addresses
        missing_addresses = all_results.get('missing_addresses', {})
        if isinstance(missing_addresses, dict):
            summary['missing_address_issues'] = missing_addresses.get('total_issues', 0)
            summary['total_issues'] += summary['missing_address_issues']
        # Aggregate unconverted links
        unconverted_links = all_results.get('unconverted_links', {})
        if isinstance(unconverted_links, dict):
            summary['unconverted_link_issues'] = unconverted_links.get('total_issues', 0)
            summary['total_issues'] += summary['unconverted_link_issues']
        # Determine overall status
        if summary['total_issues'] > 0:
            summary['status'] = 'FAIL'
        else:
            summary['status'] = 'PASS'
        return summary
    
    def _parse_legacy_output(self, output: str) -> Dict[str, Any]:
        """Extract headline metrics from the legacy cleanup output."""
        summary: Dict[str, Any] = {
            'files_with_issues': None,
            'legacy_markers': None,
            'report_path': None
        }
        if not isinstance(output, str) or not output.strip():
            return summary
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('Files with issues:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['files_with_issues'] = value
                continue
            if line.startswith('legacy_compatibility_markers:'):
                value = self._extract_first_int(line)
                if value is not None:
                    summary['legacy_markers'] = value
                continue
            if 'report saved to:' in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    summary['report_path'] = parts[1].strip()
        return summary
    
    def _load_mtime_cached_tool_results(
        self, 
        tool_name: str, 
        domain: str, 
        result: Dict,
        parse_output_func: Optional[Callable[[str], Dict[str, Any]]] = None,
        cache_converter_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Unified helper for loading results from mtime-cached tools.
        
        After tool execution, this method:
        1. Loads from cache FIRST (fresh data after tool execution)
        2. Converts cache format to results format (using converter or default)
        3. Saves to results JSON
        4. Returns results dict
        5. Falls back to parsing output if cache fails
        """
        from ..output_storage import save_tool_result, load_tool_cache
        
        # Step 1: Load from cache FIRST using standardized storage
        cache_data = None
        try:
            cache_data = load_tool_cache(tool_name, domain, project_root=self.project_root)
            if cache_data:
                logger.debug(f"Loaded {tool_name} from cache (fresh data after execution)")
        except Exception as cache_error:
            logger.debug(f"Failed to load {tool_name} from cache: {cache_error}")
        
        # Step 2: Convert cache format to results format
        if cache_data and isinstance(cache_data, dict):
            # Handle both formats: wrapped {'data': {...}} and direct {file_path: {...}}
            if 'data' in cache_data:
                file_data = cache_data.get('data', {})
            else:
                # Direct format - cache_data IS the file data
                file_data = cache_data
            if file_data and isinstance(file_data, dict):
                # CRITICAL: Filter out entries for files that no longer exist
                # The cache may contain entries for deleted files, which would cause stale data
                filtered_file_data = {}
                for file_path_str, file_info in file_data.items():
                    if isinstance(file_info, dict):
                        # Check if file still exists
                        try:
                            file_path = self.project_root / file_path_str
                            if file_path.exists():
                                # Verify mtime matches (file hasn't been modified)
                                cached_mtime = file_info.get('mtime')
                                if cached_mtime is not None:
                                    current_mtime = file_path.stat().st_mtime
                                    if current_mtime == cached_mtime:
                                        filtered_file_data[file_path_str] = file_info
                                    else:
                                        logger.debug(f"Skipping {file_path_str} - mtime mismatch (file modified)")
                                else:
                                    # No mtime in cache, include it but it will be re-scanned
                                    filtered_file_data[file_path_str] = file_info
                            else:
                                logger.debug(f"Skipping {file_path_str} - file no longer exists")
                        except (OSError, ValueError) as e:
                            logger.debug(f"Skipping {file_path_str} - error checking file: {e}")
                    else:
                        # Invalid format, skip
                        logger.debug(f"Skipping {file_path_str} - invalid cache entry format")
                
                # Use filtered data
                file_data = filtered_file_data
                # Use custom converter if provided, otherwise use default
                if cache_converter_func:
                    tool_result = cache_converter_func(file_data)
                else:
                    # Default converter
                    files_with_issues = {}
                    total_issues = 0
                    for file_path, file_info in file_data.items():
                        if isinstance(file_info, dict):
                            results = file_info.get('results', [])
                            if results:
                                files_with_issues[file_path] = len(results)
                                total_issues += len(results)
                    tool_result = {
                        'files': files_with_issues,
                        'file_count': len(files_with_issues),
                        'total_issues': total_issues
                    }
                
                # Step 3: Save to results JSON and populate in-memory cache
                try:
                    save_tool_result(tool_name, domain, tool_result, project_root=self.project_root)
                    logger.debug(f"Regenerated {tool_name}_results.json from fresh cache")
                    # Populate in-memory cache for current audit run
                    if not hasattr(self, 'results_cache'):
                        self.results_cache = {}
                    self.results_cache[tool_name] = tool_result
                except Exception as save_error:
                    logger.debug(f"Failed to save {tool_name} results: {save_error}")
                
                return tool_result
        
        # Step 4: Fallback to parsing output if cache failed
        if result.get('output') or result.get('success'):
            if parse_output_func:
                tool_result = parse_output_func(result.get('output', ''))
                try:
                    save_tool_result(tool_name, domain, tool_result, project_root=self.project_root)
                    logger.debug(f"Saved {tool_name} results from parsed output")
                    # Populate in-memory cache for current audit run
                    if not hasattr(self, 'results_cache'):
                        self.results_cache = {}
                    self.results_cache[tool_name] = tool_result
                except Exception as save_error:
                    logger.debug(f"Failed to save {tool_name} results: {save_error}")
                return tool_result
            else:
                logger.warning(f"No parser function provided for {tool_name}, cannot parse output")
        else:
            logger.warning(f"{tool_name} failed: {result.get('error', 'Unknown error')}")
        
        # Return empty result if all else fails
        return {
            'files': {},
            'file_count': 0,
            'total_issues': 0
        }
