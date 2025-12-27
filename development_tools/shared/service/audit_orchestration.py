"""
Audit orchestration methods for AIToolsService.

Contains methods for running audits in three tiers (quick, standard, full)
and managing audit state.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import output storage
from ..output_storage import save_tool_result, get_all_tool_results
from ..file_rotation import create_output_file

# Module-level flag to track if ANY audit is in progress
_AUDIT_IN_PROGRESS_GLOBAL = False

# File-based lock for cross-process protection
_AUDIT_LOCK_FILE = None


def _get_status_file_mtimes(project_root: Path) -> Dict[str, float]:
    """Get modification times for all status files."""
    # Get status file paths from config
    try:
        from .. import config
        status_config = config.get_status_config()
        status_files_config = status_config.get('status_files', {})
        # Use default from STATUS config if status_files_config is empty (matches default config)
        if not status_files_config:
            from ..config.config import STATUS
            status_files_config = STATUS.get('status_files', {})
        status_files = {
            'AI_STATUS.md': project_root / status_files_config.get('ai_status', 'development_tools/AI_STATUS.md'),
            'AI_PRIORITIES.md': project_root / status_files_config.get('ai_priorities', 'development_tools/AI_PRIORITIES.md'),
            'consolidated_report.txt': project_root / status_files_config.get('consolidated_report', 'development_tools/consolidated_report.txt')
        }
    except (ImportError, AttributeError, KeyError):
        # Fallback to default STATUS config values for backward compatibility
        try:
            from ..config.config import STATUS
            status_files_default = STATUS.get('status_files', {})
            status_files = {
                'AI_STATUS.md': project_root / status_files_default.get('ai_status', 'development_tools/AI_STATUS.md'),
                'AI_PRIORITIES.md': project_root / status_files_default.get('ai_priorities', 'development_tools/AI_PRIORITIES.md'),
                'consolidated_report.txt': project_root / status_files_default.get('consolidated_report', 'development_tools/consolidated_report.txt')
            }
        except (ImportError, AttributeError):
            # Last resort fallback
            status_files = {
                'AI_STATUS.md': project_root / 'development_tools' / 'AI_STATUS.md',
                'AI_PRIORITIES.md': project_root / 'development_tools' / 'AI_PRIORITIES.md',
                'consolidated_report.txt': project_root / 'development_tools' / 'consolidated_report.txt'
            }
    mtimes = {}
    for name, path in status_files.items():
        if path.exists():
            mtimes[name] = path.stat().st_mtime
        else:
            mtimes[name] = 0.0
    return mtimes


def _is_audit_in_progress(project_root: Path) -> bool:
    """Check if audit is in progress using both in-memory flag and file-based lock."""
    global _AUDIT_IN_PROGRESS_GLOBAL, _AUDIT_LOCK_FILE
    if _AUDIT_IN_PROGRESS_GLOBAL:
        return True
    if _AUDIT_LOCK_FILE is None:
        # Use generic path relative to project root (no development_tools/ assumption)
        try:
            from .. import config
            lock_file_path = config.get_external_value('paths.audit_lock_file', '.audit_in_progress.lock')
            _AUDIT_LOCK_FILE = project_root / lock_file_path
        except (ImportError, AttributeError):
            _AUDIT_LOCK_FILE = project_root / '.audit_in_progress.lock'
    audit_lock_exists = _AUDIT_LOCK_FILE.exists()
    # Use generic path relative to project root (no development_tools/ assumption)
    try:
        from .. import config
        coverage_lock_path = config.get_external_value('paths.coverage_lock_file', '.coverage_in_progress.lock')
        coverage_lock_file = project_root / coverage_lock_path
    except (ImportError, AttributeError):
        coverage_lock_file = project_root / '.coverage_in_progress.lock'
    coverage_lock_exists = coverage_lock_file.exists()
    lock_exists = audit_lock_exists or coverage_lock_exists
    if lock_exists:
        logger.debug(f"Audit/coverage lock file check: audit={audit_lock_exists}, coverage={coverage_lock_exists}")
    return lock_exists


class AuditOrchestrationMixin:
    """Mixin class providing audit orchestration methods to AIToolsService."""
    
    def _get_audit_lock_file_path(self) -> Path:
        """Get audit lock file path (configurable via config, defaults to .audit_in_progress.lock relative to project root)."""
        try:
            from .. import config
            # Default to generic path relative to project root (no development_tools/ assumption)
            lock_file_path = config.get_external_value('paths.audit_lock_file', '.audit_in_progress.lock')
            return self.project_root / lock_file_path
        except (ImportError, AttributeError):
            return self.project_root / 'development_tools' / '.audit_in_progress.lock'
    
    def _get_coverage_lock_file_path(self) -> Path:
        """Get coverage lock file path (configurable via config, defaults to .coverage_in_progress.lock relative to project root)."""
        try:
            from .. import config
            # Default to generic path relative to project root (no development_tools/ assumption)
            lock_file_path = config.get_external_value('paths.coverage_lock_file', '.coverage_in_progress.lock')
            return self.project_root / lock_file_path
        except (ImportError, AttributeError):
            return self.project_root / 'development_tools' / '.coverage_in_progress.lock'
    
    def run_audit(self, quick: bool = False, full: bool = False, include_overlap: bool = False):
        """Run audit workflow with three-tier structure."""
        global _AUDIT_IN_PROGRESS_GLOBAL, _AUDIT_LOCK_FILE
        
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
        # Track which tools were actually run in this audit tier
        self._tools_run_in_current_tier = set()
        # Track timing for each tool
        self._tool_timings = {}
        
        # Create file-based lock
        if _AUDIT_LOCK_FILE is None:
            _AUDIT_LOCK_FILE = self._get_audit_lock_file_path()
        try:
            _AUDIT_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
            _AUDIT_LOCK_FILE.touch()
        except Exception as e:
            logger.warning(f"Failed to create audit lock file: {e}")
        
        initial_mtimes = _get_status_file_mtimes(self.project_root)
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
                print("Running Tier 2 tools (standard audit)...")
                logger.info("Running Tier 2 tools (standard audit)...")
                tier2_success = self._run_standard_audit_tools()
                if not tier2_success:
                    success = False
            
            # Tier 3: Full audit tools
            if tier >= 3:
                print("Running Tier 3 tools (full audit)...")
                logger.info("Running Tier 3 tools (full audit)...")
                tier3_success = self._run_full_audit_tools()
                if not tier3_success:
                    success = False
        except Exception as e:
            print(f"ERROR: Error during audit execution: {e}")
            logger.error(f"Error during audit execution: {e}", exc_info=True)
            success = False
        
        # Save all tool results
        try:
            self._save_audit_results_aggregated(tier)
        except Exception as e:
            logger.warning(f"Failed to save aggregated audit results: {e}")
        
        # Reload cache data
        self._reload_all_cache_data()
        
        # Sync TODO.md with changelog
        self._sync_todo_with_changelog()
        
        # Validate referenced paths
        try:
            self._validate_referenced_paths()
        except Exception as e:
            logger.warning(f"Path validation failed (non-blocking): {e}")
        
        # Generate status files
        if self.current_audit_tier is None:
            logger.warning(f"current_audit_tier is None at end of audit! Setting to tier {tier}")
        
        try:
            pre_final_mtimes = _get_status_file_mtimes(self.project_root)
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
                    from .. import config
                    status_config = config.get_status_config()
                    status_files_config = status_config.get('status_files', {})
                    # Use default from STATUS config if status_files_config is empty (matches default config)
                    if not status_files_config:
                        # Fallback to default STATUS config values for backward compatibility
                        from ..config.config import STATUS
                        status_files_config = STATUS.get('status_files', {})
                    ai_status_path = status_files_config.get('ai_status', 'development_tools/AI_STATUS.md')
                    ai_priorities_path = status_files_config.get('ai_priorities', 'development_tools/AI_PRIORITIES.md')
                    consolidated_report_path = status_files_config.get('consolidated_report', 'development_tools/consolidated_report.txt')
                except (ImportError, AttributeError, KeyError):
                    # Fallback to default STATUS config values for backward compatibility
                    try:
                        from ..config.config import STATUS
                        status_files_default = STATUS.get('status_files', {})
                        ai_status_path = status_files_default.get('ai_status', 'development_tools/AI_STATUS.md')
                        ai_priorities_path = status_files_default.get('ai_priorities', 'development_tools/AI_PRIORITIES.md')
                        consolidated_report_path = status_files_default.get('consolidated_report', 'development_tools/consolidated_report.txt')
                    except (ImportError, AttributeError):
                        # Last resort fallback
                        ai_status_path = 'development_tools/AI_STATUS.md'
                        ai_priorities_path = 'development_tools/AI_PRIORITIES.md'
                        consolidated_report_path = 'development_tools/consolidated_report.txt'
                
                try:
                    ai_status = self._generate_ai_status_document()
                except Exception as e:
                    logger.warning(f"Error generating AI_STATUS document: {e}")
                    ai_status = "# AI Status\n\nError generating status document."
                ai_status_file = create_output_file(ai_status_path, ai_status, project_root=self.project_root)
                
                try:
                    ai_priorities = self._generate_ai_priorities_document()
                except Exception as e:
                    logger.warning(f"Error generating AI_PRIORITIES document: {e}")
                    ai_priorities = "# AI Priorities\n\nError generating priorities document."
                ai_priorities_file = create_output_file(ai_priorities_path, ai_priorities, project_root=self.project_root)
                
                try:
                    consolidated_report = self._generate_consolidated_report()
                except Exception as e:
                    logger.warning(f"Error generating consolidated report: {e}")
                    consolidated_report = "Error generating consolidated report."
                consolidated_file = create_output_file(consolidated_report_path, consolidated_report, project_root=self.project_root)
                
                post_final_mtimes = _get_status_file_mtimes(self.project_root)
                for file_name, mtime in post_final_mtimes.items():
                    if mtime <= pre_final_mtimes.get(file_name, 0):
                        logger.warning(f"Status file {file_name} mtime did not change during final write!")
            finally:
                _AUDIT_IN_PROGRESS_GLOBAL = was_audit_in_progress
            
            # Additional checks
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
            
            print("=" * 50)
            logger.info("=" * 50)
            if success:
                print(f"Completed {operation_name} successfully!")
                logger.info(f"Completed {operation_name} successfully!")
                # Log timing summary
                if self._tool_timings:
                    total_time = sum(self._tool_timings.values())
                    timing_msg = f"Total tool execution time: {total_time:.2f}s"
                    print(f"  {timing_msg}")
                    logger.info(timing_msg)
                    # Log slowest tools
                    sorted_timings = sorted(self._tool_timings.items(), key=lambda x: x[1], reverse=True)
                    if len(sorted_timings) > 0:
                        slowest_msg = f"Slowest tools: {', '.join(f'{name} ({time:.2f}s)' for name, time in sorted_timings[:5])}"
                        print(f"  {slowest_msg}")
                        logger.info(slowest_msg)
                print(f"  * AI Status: {ai_status_file}")
                print(f"  * AI Priorities: {ai_priorities_file}")
                print(f"  * Consolidated Report: {consolidated_file}")
                logger.info(f"* AI Status: {ai_status_file}")
                logger.info(f"* AI Priorities: {ai_priorities_file}")
                logger.info(f"* Consolidated Report: {consolidated_file}")
            else:
                print(f"Completed {operation_name} with some errors")
                logger.warning(f"Completed {operation_name} with some errors")
        except Exception as e:
            print(f"ERROR: Error generating status files: {e}")
            logger.error(f"Error generating status files: {e}", exc_info=True)
            success = False
        finally:
            # Clear flags and remove lock file
            self._audit_in_progress = False
            self.current_audit_tier = None
            self._tools_run_in_current_tier = set()  # Clear tracking when audit completes
            # Clear results_cache to prevent stale data from being used in next audit
            if hasattr(self, 'results_cache'):
                self.results_cache = {}
            # Save timing data for analysis
            if hasattr(self, '_tool_timings') and self._tool_timings:
                self._save_timing_data(tier)
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
        """Run Tier 1 tools: Quick audit (core metrics only, ≤2s per tool).
        
        Note: Tools moved here based on execution time (≤2s) while respecting dependencies.
        """
        successful = []
        failed = []
        
        # Core Tier 1 tools (≤2s)
        tier1_core_tools = [
            ('analyze_system_signals', self.run_analyze_system_signals),  # 1.07s
        ]
        
        # Independent tools (≤2s)
        tier1_independent_tools = [
            ('analyze_documentation', lambda: self.run_analyze_documentation(include_overlap=getattr(self, '_include_overlap', False))),  # 0.21s
            ('analyze_config', lambda: self.run_script('analyze_config')),  # 0.93s
            ('analyze_ai_work', self.run_validate),  # 0.95s
        ]
        
        # Dependent groups (all tools ≤2s)
        tier1_dependent_groups = [
            # Function patterns group: depends on analyze_functions (runs in Tier 2)
            [
                ('analyze_function_patterns', self.run_analyze_function_patterns),  # 1.79s
            ],
            # Decision support group: depends on analyze_functions (runs in Tier 2)
            [
                ('decision_support', self.run_decision_support),  # 1.96s
            ],
        ]
        
        tier1_tools = tier1_core_tools
        
        # Run core tools first (analyze_functions must run before dependent tools)
        for tool_name, tool_func in tier1_core_tools:
            try:
                # Time tool execution
                start_time = time.time()
                # Note: Tools log their own execution, so no need to log here
                result = tool_func()
                elapsed_time = time.time() - start_time
                self._tool_timings[tool_name] = elapsed_time
                logger.debug(f"  - {tool_name} completed in {elapsed_time:.2f}s")
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                    # Note: Tools save their own results, so no need to save here
                    # Removed duplicate save_tool_result call to prevent duplicate logging
                else:
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
            except Exception as exc:
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
                    group_results[tool_name] = ({'success': False, 'error': str(exc)}, 0.0)
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
                    
                    if success:
                        successful.append(tool_name)
                        self._tools_run_in_current_tier.add(tool_name)
                    else:
                        failed.append(tool_name)
                        logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        # Run quick_status at the end of Tier 1 (after other tools have run and potentially created results)
        # This allows it to use fresh data from the current audit run, but it still works gracefully if data is missing
        try:
            # Time quick_status execution
            start_time = time.time()
            # Note: quick_status logs its own execution ("Generating JSON status output")
            quick_status_result = self.run_script('quick_status', 'json')
            elapsed_time = time.time() - start_time
            self._tool_timings['quick_status'] = elapsed_time
            logger.debug(f"  - quick_status completed in {elapsed_time:.2f}s")
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
                        successful.append('quick_status')
                        self._tools_run_in_current_tier.add('quick_status')
                    except json.JSONDecodeError:
                        logger.warning("  - quick_status output could not be parsed as JSON")
                        failed.append('quick_status')
                else:
                    failed.append('quick_status')
            else:
                failed.append('quick_status')
        except Exception as exc:
            failed.append('quick_status')
            logger.error(f"  - quick_status failed: {exc}")
        
        if failed:
            logger.warning(f"Tier 1 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 1 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_standard_audit_tools(self) -> bool:
        """Run Tier 2 tools: Standard audit (quality checks, >2s but ≤10s per tool).
        
        Note: Tools moved here based on execution time (>2s but ≤10s) while respecting dependencies.
        """
        successful = []
        failed = []
        
        # Independent tools (>2s but ≤10s)
        tier2_independent_tools = [
            ('analyze_functions', self.run_analyze_functions),  # 3.41s
            ('analyze_error_handling', self.run_analyze_error_handling),  # 3.06s
            ('analyze_package_exports', self.run_analyze_package_exports),  # 9.06s
        ]
        
        # Dependent groups (>2s but ≤10s)
        tier2_dependent_groups = [
            # Module imports group: analyze_module_imports → analyze_dependency_patterns, analyze_module_dependencies
            [
                ('analyze_module_imports', self.run_analyze_module_imports),  # 2.18s
                ('analyze_dependency_patterns', self.run_analyze_dependency_patterns),  # 2.03s
                ('analyze_module_dependencies', self.run_analyze_module_dependencies),  # 5.94s
            ],
            # Function registry group: analyze_function_registry validates generate_function_registry output
            [
                ('analyze_function_registry', self.run_analyze_function_registry),  # 2.12s
            ],
            # Documentation sync group: includes multiple sub-tools
            [
                ('analyze_documentation_sync', self.run_analyze_documentation_sync),  # 7.70s
            ],
            # Unused imports group: moved from Tier 3 (both ≤10s)
            [
                ('analyze_unused_imports', self.run_unused_imports),  # 7.82s
                ('generate_unused_imports_report', self.run_generate_unused_imports_report),  # 0.98s
            ],
        ]
        
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
                    group_results[tool_name] = ({'success': False, 'error': str(exc)}, 0.0)
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
            
            if success:
                successful.append(tool_name)
                self._tools_run_in_current_tier.add(tool_name)
            else:
                failed.append(tool_name)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        if failed:
            logger.warning(f"Tier 2 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 2 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_tool_with_timing(self, tool_name: str, tool_func) -> tuple:
        """Run a tool and return (result, elapsed_time) tuple."""
        start_time = time.time()
        try:
            result = tool_func()
            elapsed_time = time.time() - start_time
            return result, elapsed_time
        except Exception as e:
            elapsed_time = time.time() - start_time
            raise
    
    def _run_full_audit_tools(self) -> bool:
        """Run Tier 3 tools: Full audit (comprehensive analysis, >10s per tool or groups with >10s tools).
        
        Note: Tools moved here based on execution time (>10s) while respecting dependencies:
        - Coverage group: run_test_coverage (365.45s) and generate_dev_tools_coverage (94.23s) are >10s, so entire group stays in Tier 3
        - Legacy group: analyze_legacy_references (62.11s) is >10s, so entire group stays in Tier 3
        """
        successful = []
        failed = []
        
        # Coverage tool group - must run together (dependencies)
        # run_test_coverage (365.45s) and generate_dev_tools_coverage (94.23s) are >10s, so entire group stays in Tier 3
        tier3_coverage_group = [
            ('run_test_coverage', self.run_coverage_regeneration),  # 365.45s
            ('generate_dev_tools_coverage', self.run_dev_tools_coverage),  # 94.23s
            ('analyze_test_markers', lambda: self.run_test_markers('check')),  # 1.57s
            ('generate_test_coverage_report', self.run_generate_test_coverage_report),  # ~5s
        ]
        
        # Legacy group - analyze_legacy_references (62.11s) is >10s, so entire group stays in Tier 3
        tier3_legacy_group = [
            ('analyze_legacy_references', self.run_analyze_legacy_references),  # 62.11s
            ('generate_legacy_reference_report', self.run_generate_legacy_reference_report),  # 0.96s
        ]
        
        # Independent groups that can run in parallel with each other
        tier3_parallel_groups = [
            tier3_legacy_group,
        ]
        
        # Run coverage group sequentially (they depend on each other)
        logger.debug("Running coverage tool group (sequential)...")
        for tool_name, tool_func in tier3_coverage_group:
            try:
                start_time = time.time()
                result = tool_func()
                elapsed_time = time.time() - start_time
                self._tool_timings[tool_name] = elapsed_time
                logger.debug(f"  - {tool_name} completed in {elapsed_time:.2f}s")
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                else:
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
            except Exception as exc:
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        # Run independent tool groups in parallel (each group runs its tools sequentially)
        if tier3_parallel_groups:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            logger.debug(f"Running {len(tier3_parallel_groups)} independent tool groups in parallel...")
            
            def run_tool_group(group_tools):
                """Run a group of tools sequentially and return results."""
                group_results = {}
                for tool_name, tool_func in group_tools:
                    try:
                        result, elapsed_time = self._run_tool_with_timing(tool_name, tool_func)
                        group_results[tool_name] = (result, elapsed_time)
                    except Exception as exc:
                        logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                        group_results[tool_name] = ({'success': False, 'error': str(exc)}, 0.0)
                return group_results
            
            with ThreadPoolExecutor(max_workers=len(tier3_parallel_groups)) as executor:
                future_to_group = {
                    executor.submit(run_tool_group, group): i
                    for i, group in enumerate(tier3_parallel_groups)
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
                        if success:
                            successful.append(tool_name)
                            self._tools_run_in_current_tier.add(tool_name)
                        else:
                            failed.append(tool_name)
                            logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        if failed:
            logger.warning(f"Tier 3 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 3 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _save_additional_tool_results(self):
        """Save results from additional tools to the cached file."""
        try:
            results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
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
                # Store with new key
                cached_data['results']['analyze_system_signals'] = {
                    'success': True,
                    'data': self.system_signals,
                    'timestamp': datetime.now().isoformat()
                }
                # LEGACY COMPATIBILITY: Also store with old key for backward compatibility
                # Removal plan: Remove 'system_signals' key storage after 2025-03-01 if no references found
                # Detection pattern: "system_signals" in cached_data['results']
                cached_data['results']['system_signals'] = {
                    'success': True,
                    'data': self.system_signals,
                    'timestamp': datetime.now().isoformat()
                }
            
            decision_metrics = self.results_cache.get('decision_support_metrics', {})
            if decision_metrics:
                cached_data['results']['decision_support'] = {
                    'success': True,
                    'data': {'decision_support_metrics': decision_metrics},
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
        """Reload all cache data from disk."""
        try:
            all_results = get_all_tool_results(project_root=self.project_root)
            if all_results:
                for tool_name, result_data in all_results.items():
                    if isinstance(result_data, dict):
                        tool_data = result_data.get('data', result_data)
                        self.results_cache[tool_name] = tool_data
                        if tool_name == 'analyze_documentation_sync' and isinstance(tool_data, dict):
                            self.docs_sync_summary = tool_data
                        if tool_name == 'analyze_legacy_references' and isinstance(tool_data, dict):
                            self.legacy_cleanup_summary = tool_data
            
            results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                if 'results' in cached_data:
                    for tool_name, tool_data in cached_data['results'].items():
                        if tool_name not in self.results_cache and 'data' in tool_data:
                            self.results_cache[tool_name] = tool_data['data']
                    if 'decision_support' in cached_data['results']:
                        ds_data = cached_data['results']['decision_support']
                        if 'data' in ds_data and 'decision_support_metrics' in ds_data['data']:
                            self.results_cache['decision_support_metrics'] = ds_data['data']['decision_support_metrics']
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
    
    def _save_audit_results_aggregated(self, tier: int):
        """Save aggregated audit results from all tool result files."""
        all_results = get_all_tool_results(project_root=self.project_root)
        enhanced_results = {}
        successful = []
        failed = []
        
        for tool_name, result_data in all_results.items():
            if isinstance(result_data, dict):
                tool_data = result_data.get('data', result_data)
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
        
        for tool_name, data in self.results_cache.items():
            if tool_name not in enhanced_results:
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
        
        results_file_path = self.audit_config.get('results_file', 'development_tools/reports/analysis_detailed_results.json')
        results_file = (self.project_root / results_file_path).resolve()
        if isinstance(results_file, str):
            results_file = Path(results_file)
        
        create_output_file(str(results_file), json.dumps(audit_data, indent=2), project_root=self.project_root)
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report."""
        # This method can be implemented if needed
        # For now, audit reports are generated via the status document methods
        pass
    
    def _check_and_trim_changelog_entries(self) -> None:
        """Check and trim AI_CHANGELOG entries to prevent bloat."""
        try:
            from ai_development_docs import changelog_manager
        except Exception:
            changelog_manager = None
        if changelog_manager and hasattr(changelog_manager, 'trim_change_log'):
            try:
                result = changelog_manager.trim_change_log()
                if isinstance(result, dict):
                    trimmed = result.get('trimmed_entries')
                    archive_created = result.get('archive_created')
                    if trimmed:
                        logger.info(f"   Trimmed {trimmed} old changelog entries")
                    if archive_created:
                        logger.info("   Created archive: development_tools/reports/archive/AI_CHANGELOG_ARCHIVE.md")
            except Exception as exc:
                logger.warning(f"   Changelog check/trim failed: {exc}")
        else:
            logger.warning("   Changelog check: Tooling unavailable (skipping trim)")
    
    def _validate_referenced_paths(self) -> None:
        """Validate that all referenced paths in documentation exist."""
        try:
            from development_tools.docs.fix_version_sync import validate_referenced_paths
            result = validate_referenced_paths()
            status = result.get('status') if isinstance(result, dict) else None
            message = result.get('message') if isinstance(result, dict) else None
            if isinstance(result, dict):
                self.path_validation_result = result
            if status == 'ok':
                logger.info(f"   Path validation: {message}")
            elif status == 'fail':
                issues = result.get('issues_found', 'unknown') if isinstance(result, dict) else 'unknown'
                logger.info(f"   Path validation: {message}")
                logger.info(f"   Found {issues} path issues")
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
                    logger.info("   Documentation quality: No verbatim duplicates found")
                if placeholders:
                    logger.warning(f"   Documentation quality: Found {len(placeholders)} files with placeholders")
                else:
                    logger.info("   Documentation quality: No placeholder content found")
        except Exception as exc:
            logger.warning(f"   Documentation quality check failed: {exc}")
    
    def _check_ascii_compliance(self) -> None:
        """Check for non-ASCII characters in documentation files."""
        try:
            from development_tools.docs.analyze_ascii_compliance import ASCIIComplianceAnalyzer
            analyzer = ASCIIComplianceAnalyzer()
            results = analyzer.check_ascii_compliance()
            total_issues = sum(len(issues) for issues in results.values())
            files_with_issues = len(results)
            if total_issues == 0:
                logger.info("   ASCII compliance: All documentation files use ASCII-only characters")
                if not hasattr(self, 'docs_sync_summary') or not self.docs_sync_summary:
                    self.docs_sync_summary = {}
                self.docs_sync_summary['ascii_issues'] = 0
            else:
                logger.info(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {files_with_issues} files")
                if not hasattr(self, 'docs_sync_summary') or not self.docs_sync_summary:
                    self.docs_sync_summary = {}
                self.docs_sync_summary['ascii_issues'] = files_with_issues
        except Exception as exc:
            logger.warning(f"   ASCII compliance check failed: {exc}")
    
    def _save_timing_data(self, tier: int) -> None:
        """Save timing data to a JSON file for analysis."""
        try:
            timing_file = self.project_root / 'development_tools' / 'reports' / 'tool_timings.json'
            timing_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing timing data
            existing_data = {}
            if timing_file.exists():
                try:
                    with open(timing_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    existing_data = {}
            
            # Add new timing entry
            timestamp = datetime.now().isoformat()
            tier_name = {1: 'quick', 2: 'standard', 3: 'full'}.get(tier, 'unknown')
            
            if 'runs' not in existing_data:
                existing_data['runs'] = []
            
            existing_data['runs'].append({
                'timestamp': timestamp,
                'tier': tier_name,
                'tier_number': tier,
                'tool_timings': self._tool_timings.copy(),
                'total_time': sum(self._tool_timings.values())
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
        """Sync TODO.md with AI_CHANGELOG.md to move completed entries."""
        try:
            from development_tools.docs.fix_version_sync import sync_todo_with_changelog
            result = sync_todo_with_changelog()
            if isinstance(result, dict):
                self.todo_sync_result = result
                status = result.get('status')
                if status == 'ok':
                    moved = result.get('moved_entries', 0)
                    if moved > 0:
                        logger.info(f"   TODO sync: Moved {moved} completed entries to changelog")
                    else:
                        logger.info("   TODO sync: No completed entries to move")
                else:
                    message = result.get('message', 'Unknown error')
                    logger.warning(f"   TODO sync: {message}")
        except Exception as exc:
            logger.warning(f"   TODO sync failed: {exc}")
