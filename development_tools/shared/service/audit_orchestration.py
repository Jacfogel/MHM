"""
Audit orchestration methods for AIToolsService.

Contains methods for running audits in three tiers (quick, standard, full)
and managing audit state.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Import output storage
from ..output_storage import save_tool_result, get_all_tool_results, _get_domain_from_tool_name
from ..file_rotation import create_output_file

# Module-level flag to track if ANY audit is in progress
_AUDIT_IN_PROGRESS_GLOBAL = False

# File-based lock for cross-process protection
_AUDIT_LOCK_FILE = None


def _get_status_file_mtimes(project_root: Path) -> Dict[str, float]:
    """Get modification times for all status files."""
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
        _AUDIT_LOCK_FILE = project_root / 'development_tools' / '.audit_in_progress.lock'
    audit_lock_exists = _AUDIT_LOCK_FILE.exists()
    coverage_lock_file = project_root / 'development_tools' / '.coverage_in_progress.lock'
    coverage_lock_exists = coverage_lock_file.exists()
    lock_exists = audit_lock_exists or coverage_lock_exists
    if lock_exists:
        logger.debug(f"Audit/coverage lock file check: audit={audit_lock_exists}, coverage={coverage_lock_exists}")
    return lock_exists


class AuditOrchestrationMixin:
    """Mixin class providing audit orchestration methods to AIToolsService."""
    
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
        
        logger.info(f"Starting {operation_name}...")
        logger.info("=" * 50)
        
        self.current_audit_tier = tier
        self._audit_in_progress = True
        _AUDIT_IN_PROGRESS_GLOBAL = True
        # Track which tools were actually run in this audit tier
        self._tools_run_in_current_tier = set()
        
        # Create file-based lock
        if _AUDIT_LOCK_FILE is None:
            _AUDIT_LOCK_FILE = self.project_root / 'development_tools' / '.audit_in_progress.lock'
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
            logger.info("Running Tier 1 tools (quick audit)...")
            tier1_success = self._run_quick_audit_tools()
            if not tier1_success:
                success = False
            
            # Tier 2: Standard audit tools
            if tier >= 2:
                logger.info("Running Tier 2 tools (standard audit)...")
                tier2_success = self._run_standard_audit_tools()
                if not tier2_success:
                    success = False
            
            # Tier 3: Full audit tools
            if tier >= 3:
                logger.info("Running Tier 3 tools (full audit)...")
                tier3_success = self._run_full_audit_tools()
                if not tier3_success:
                    success = False
        except Exception as e:
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
                try:
                    ai_status = self._generate_ai_status_document()
                except Exception as e:
                    logger.warning(f"Error generating AI_STATUS document: {e}")
                    ai_status = "# AI Status\n\nError generating status document."
                ai_status_file = create_output_file("development_tools/AI_STATUS.md", ai_status, project_root=self.project_root)
                
                try:
                    ai_priorities = self._generate_ai_priorities_document()
                except Exception as e:
                    logger.warning(f"Error generating AI_PRIORITIES document: {e}")
                    ai_priorities = "# AI Priorities\n\nError generating priorities document."
                ai_priorities_file = create_output_file("development_tools/AI_PRIORITIES.md", ai_priorities, project_root=self.project_root)
                
                try:
                    consolidated_report = self._generate_consolidated_report()
                except Exception as e:
                    logger.warning(f"Error generating consolidated report: {e}")
                    consolidated_report = "Error generating consolidated report."
                consolidated_file = create_output_file("development_tools/consolidated_report.txt", consolidated_report, project_root=self.project_root)
                
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
            
            logger.info("=" * 50)
            if success:
                logger.info(f"Completed {operation_name} successfully!")
                logger.info(f"* AI Status: {ai_status_file}")
                logger.info(f"* AI Priorities: {ai_priorities_file}")
                logger.info(f"* Consolidated Report: {consolidated_file}")
            else:
                logger.warning(f"Completed {operation_name} with some errors")
        except Exception as e:
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
        """Run Tier 1 tools: Quick audit (core metrics only)."""
        successful = []
        failed = []
        
        tier1_tools = [
            ('analyze_functions', self.run_analyze_functions),
            ('analyze_documentation_sync', self.run_analyze_documentation_sync),
            ('system_signals', self.run_system_signals),
        ]
        
        # Handle quick_status separately
        try:
            logger.info("  - Running quick_status...")
            quick_status_result = self.run_script('quick_status', 'json')
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
        
        for tool_name, tool_func in tier1_tools:
            try:
                logger.info(f"  - Running {tool_name}...")
                result = tool_func()
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                    if isinstance(result, dict) and 'data' in result:
                        try:
                            domain = _get_domain_from_tool_name(tool_name, self.project_root)
                            save_tool_result(tool_name, domain, result['data'], project_root=self.project_root)
                        except Exception as e:
                            logger.debug(f"Failed to save {tool_name} result: {e}")
                else:
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
            except Exception as exc:
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        if failed:
            logger.warning(f"Tier 1 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 1 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_standard_audit_tools(self) -> bool:
        """Run Tier 2 tools: Standard audit (quality checks)."""
        successful = []
        failed = []
        
        tier2_tools = [
            ('analyze_documentation', lambda: self.run_analyze_documentation(include_overlap=getattr(self, '_include_overlap', False))),
            ('analyze_error_handling', self.run_analyze_error_handling),
            ('decision_support', self.run_decision_support),
            ('analyze_config', lambda: self.run_script('analyze_config')),
            ('analyze_ai_work', self.run_validate),
            ('analyze_function_registry', self.run_analyze_function_registry),
            ('analyze_module_dependencies', self.run_analyze_module_dependencies),
            ('analyze_module_imports', self.run_analyze_module_imports),
            ('analyze_dependency_patterns', self.run_analyze_dependency_patterns),
            ('analyze_function_patterns', self.run_analyze_function_patterns),
            ('analyze_package_exports', self.run_analyze_package_exports),
        ]
        
        for tool_name, tool_func in tier2_tools:
            try:
                logger.info(f"  - Running {tool_name}...")
                result = tool_func()
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                    if isinstance(result, dict):
                        data = result.get('data')
                        if not data and result.get('output'):
                            try:
                                data = json.loads(result.get('output', ''))
                            except (json.JSONDecodeError, TypeError):
                                pass
                        if data:
                            try:
                                domain = _get_domain_from_tool_name(tool_name, self.project_root)
                                save_tool_result(tool_name, domain, data, project_root=self.project_root)
                            except Exception as e:
                                logger.debug(f"Failed to save {tool_name} result: {e}")
                else:
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
            except Exception as exc:
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        if failed:
            logger.warning(f"Tier 2 completed with {len(failed)} failure(s): {', '.join(failed)}")
        else:
            logger.info(f"Tier 2 completed successfully ({len(successful)} tools)")
        
        return len(failed) == 0
    
    def _run_full_audit_tools(self) -> bool:
        """Run Tier 3 tools: Full audit (comprehensive analysis)."""
        successful = []
        failed = []
        
        tier3_analyze_tools = [
            ('generate_test_coverage', self.run_coverage_regeneration),
            ('generate_dev_tools_coverage', self.run_dev_tools_coverage),
            ('analyze_test_markers', lambda: self.run_test_markers('check')),
            ('analyze_unused_imports', self.run_unused_imports_report),
            ('analyze_legacy_references', self.run_analyze_legacy_references),
        ]
        
        tier3_report_tools = [
            ('generate_legacy_reference_report', self.run_generate_legacy_reference_report),
            ('generate_test_coverage_reports', self.run_generate_test_coverage_reports),
        ]
        
        for tool_name, tool_func in tier3_analyze_tools:
            try:
                logger.info(f"  - Running {tool_name}...")
                result = tool_func()
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if 'data' in result:
                        self._extract_key_info(tool_name, result)
                else:
                    success = bool(result)
                if success:
                    successful.append(tool_name)
                    self._tools_run_in_current_tier.add(tool_name)
                    if isinstance(result, dict):
                        data = result.get('data')
                        if not data and result.get('output'):
                            try:
                                data = json.loads(result.get('output', ''))
                                logger.debug(f"Extracted data from {tool_name} output via JSON parsing")
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.debug(f"Failed to parse {tool_name} output as JSON: {e}")
                                pass
                        if data:
                            try:
                                domain = _get_domain_from_tool_name(tool_name, self.project_root)
                                save_tool_result(tool_name, domain, data, project_root=self.project_root)
                                logger.debug(f"Saved {tool_name} result via audit orchestration (domain: {domain})")
                            except Exception as e:
                                logger.warning(f"Failed to save {tool_name} result via audit orchestration: {e}")
                        else:
                            logger.debug(f"{tool_name} completed successfully but no data extracted (result.get('data')={result.get('data')}, has_output={bool(result.get('output'))})")
                else:
                    failed.append(tool_name)
                    logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
            except Exception as exc:
                failed.append(tool_name)
                logger.error(f"  - {tool_name} failed: {exc}", exc_info=True)
                logger.warning(f"[TOOL FAILURE] {tool_name} execution failed - reports may use cached/fallback data")
        
        for tool_name, tool_func in tier3_report_tools:
            try:
                logger.info(f"  - Running {tool_name}...")
                result = tool_func()
                if isinstance(result, dict):
                    success = result.get('success', False)
                    error_msg = result.get('error', '')
                    returncode = result.get('returncode')
                    if not success:
                        if error_msg:
                            logger.error(f"  - {tool_name} failed: {error_msg}")
                        elif returncode is not None:
                            logger.error(f"  - {tool_name} failed with return code {returncode}")
                        else:
                            logger.error(f"  - {tool_name} failed: Unknown error")
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
            logger.info("   Changelog check: Tooling unavailable (skipping trim)")
    
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
                logger.warning(f"   Path validation failed: {message}")
                logger.warning(f"   Found {issues} path issues")
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
                logger.warning(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {files_with_issues} files")
                if not hasattr(self, 'docs_sync_summary') or not self.docs_sync_summary:
                    self.docs_sync_summary = {}
                self.docs_sync_summary['ascii_issues'] = files_with_issues
        except Exception as exc:
            logger.warning(f"   ASCII compliance check failed: {exc}")
    
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
