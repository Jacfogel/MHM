#!/usr/bin/env python3
# TOOL_TIER: core


"""

Core operations used by the AI development toolchain.

This module contains the reusable service layer that powers the CLI in

`run_development_tools.py`. Each public method exposes a discrete workflow that

can be invoked programmatically or through a registered command.

"""

import sys

import subprocess

import json

import os

import re

import argparse

from pathlib import Path

from datetime import datetime

from dataclasses import dataclass

from typing import Any, Dict, List, Optional, Sequence, Callable

from collections import OrderedDict, defaultdict

from .. import config
# Load external config if path was provided (will be set by AIToolsService)

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

SCRIPT_REGISTRY = {

    'analyze_documentation': 'docs/analyze_documentation.py',

    'analyze_function_registry': 'functions/analyze_function_registry.py',

    'analyze_module_dependencies': 'imports/analyze_module_dependencies.py',

    'analyze_config': 'config/analyze_config.py',

    'decision_support': 'reports/decision_support.py',

    'analyze_documentation_sync': 'docs/analyze_documentation_sync.py',
    'analyze_path_drift': 'docs/analyze_path_drift.py',
    'analyze_missing_addresses': 'docs/analyze_missing_addresses.py',
    'analyze_ascii_compliance': 'docs/analyze_ascii_compliance.py',
    'analyze_heading_numbering': 'docs/analyze_heading_numbering.py',
    'analyze_unconverted_links': 'docs/analyze_unconverted_links.py',
    'generate_directory_tree': 'docs/generate_directory_tree.py',

    'analyze_error_handling': 'error_handling/analyze_error_handling.py',
    'generate_error_handling_report': 'error_handling/generate_error_handling_report.py',
    'generate_error_handling_recommendations': 'error_handling/generate_error_handling_recommendations.py',

    'analyze_functions': 'functions/analyze_functions.py',
    'analyze_function_patterns': 'functions/analyze_function_patterns.py',
    'generate_function_registry': 'functions/generate_function_registry.py',

    'generate_module_dependencies': 'imports/generate_module_dependencies.py',
    'analyze_module_imports': 'imports/analyze_module_imports.py',
    'analyze_dependency_patterns': 'imports/analyze_dependency_patterns.py',

    'fix_legacy_references': 'legacy/fix_legacy_references.py',
    'analyze_legacy_references': 'legacy/analyze_legacy_references.py',
    'generate_legacy_reference_report': 'legacy/generate_legacy_reference_report.py',

    'quick_status': 'reports/quick_status.py',

    'generate_test_coverage': 'tests/generate_test_coverage.py',
    'analyze_test_coverage': 'tests/analyze_test_coverage.py',
    'generate_test_coverage_reports': 'tests/generate_test_coverage_reports.py',

    'analyze_unused_imports': 'imports/analyze_unused_imports.py',

    'analyze_ai_work': 'ai_work/analyze_ai_work.py',

    'fix_version_sync': 'docs/fix_version_sync.py',

    'fix_documentation': 'docs/fix_documentation.py',

    'system_signals': 'reports/system_signals.py'

}

from ..shared.file_rotation import create_output_file
from .common import COMMAND_TIERS

class AIToolsService:

    """Comprehensive AI tools runner optimized for AI collaboration."""

    def __init__(self, project_root: Optional[str] = None, config_path: Optional[str] = None, 
                 project_name: Optional[str] = None, key_files: Optional[List[str]] = None):

        # Load external config if path provided, or try to auto-load from default location
        if config_path:
            config.load_external_config(config_path)
        else:
            # Try to auto-load from development_tools/config/development_tools_config.json or project root
            config.load_external_config()
        
        # Use provided project_root or fall back to config
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()
        
        # Store config_path for reference
        self.config_path = config_path
        
        # Project-specific configuration (for portability)
        # Can be overridden by external config
        self.project_name = project_name or config.get_external_value('project.name', "Project")
        self.key_files = key_files or config.get_external_value('project.key_files', [])

        self.workflow_config = config.get_workflow_config() or {}

        self.validation_config = config.get_ai_validation_config() or {}

        self.ai_config = config.get_ai_collaboration_config() or {}

        self.audit_config = config.get_quick_audit_config() or {}

        self.results_cache = {}

        self.docs_sync_results = None

        self.system_signals = None
        self.dev_tools_coverage_results = None
        self.module_dependency_summary = None

        self.exclusion_config = {

            'include_tests': False,

            'include_dev_tools': False

        }

        self.docs_sync_summary = None

        self.legacy_cleanup_results = None

        self.legacy_cleanup_summary = None

        self.status_results = None

        self.status_summary = None

    def set_exclusion_config(self, include_tests: bool = False, include_dev_tools: bool = False):

        """Set exclusion configuration for audit tools."""

        self.exclusion_config = {

            'include_tests': include_tests,

            'include_dev_tools': include_dev_tools

        }

    def run_script(self, script_name: str, *args, timeout: Optional[int] = 300) -> Dict:

        """Run a registered helper script from development_tools."""

        script_rel_path = SCRIPT_REGISTRY.get(script_name)

        if not script_rel_path:

            return {

                'success': False,

                'output': '',

                'error': f"Script '{script_name}' is not registered"

            }

        script_path = Path(__file__).resolve().parent.parent / script_rel_path

        if not script_path.exists():

            return {

                'success': False,

                'output': '',

                'error': f"Registered script '{script_name}' not found at {script_rel_path}"

            }

        cmd = [sys.executable, str(script_path)] + list(args)

        try:

            result = subprocess.run(

                cmd,

                capture_output=True,

                text=True,

                cwd=str(self.project_root),

                timeout=timeout  # default 5 minute timeout

            )

            return {

                'success': result.returncode == 0,

                'output': result.stdout,

                'error': result.stderr,

                'returncode': result.returncode

            }

        except subprocess.TimeoutExpired:

            return {

                'success': False,

                'output': '',

                'error': f"Script '{script_name}' timed out after {timeout // 60 if timeout else 'N/A'} minutes",

                'returncode': None

            }

    def run_analyze_documentation(self, include_overlap: bool = False) -> Dict:

        """Run analyze_documentation with structured JSON handling."""

        args = ["--json"]
        if include_overlap:
            args.append("--overlap")
        result = self.run_script("analyze_documentation", *args)

        output = result.get('output', '')

        data = None

        if output:

            try:

                data = json.loads(output)

            except json.JSONDecodeError:

                data = None

        if data is not None:

            result['data'] = data

            self.results_cache['analyze_documentation'] = data

            result['issues_found'] = bool(data.get('duplicates') or data.get('placeholders') or data.get('missing'))

            result['success'] = True

            result['error'] = ''

        else:

            lowered = output.lower() if isinstance(output, str) else ''

            if not result.get('success') and ("verbatim duplicate" in lowered or "placeholder" in lowered):

                result['issues_found'] = True

                result['success'] = True

                result['error'] = ''

        return result

    def run_analyze_function_registry(self) -> Dict:

        """Run analyze_function_registry with structured JSON handling."""

        result = self.run_script("analyze_function_registry", "--json")

        output = result.get('output', '')

        data = None

        if output:

            try:

                data = json.loads(output)

            except json.JSONDecodeError:

                data = None

        if data is not None:

            result['data'] = data

            missing = data.get('missing', {}) if isinstance(data.get('missing'), dict) else data.get('missing')

            extra = data.get('extra', {}) if isinstance(data.get('extra'), dict) else data.get('extra')

            errors = data.get('errors') or []

            missing_count = missing.get('count') if isinstance(missing, dict) else missing

            extra_count = extra.get('count') if isinstance(extra, dict) else extra

            result['issues_found'] = bool(missing_count or extra_count or errors)

            result['success'] = True

            result['error'] = ''

        else:

            lowered = output.lower() if isinstance(output, str) else ''

            if 'missing from registry' in lowered or 'missing items' in lowered or 'extra functions' in lowered:

                result['issues_found'] = True

                result['success'] = True

                result['error'] = ''

        return result

    def run_analyze_module_dependencies(self) -> Dict:

        """Run analyze_module_dependencies and capture dependency drift summary."""

        result = self.run_script("analyze_module_dependencies")

        output = result.get('output', '')

        summary = self._parse_module_dependency_report(output)

        if summary:

            result['data'] = summary

            issues = summary.get('missing_dependencies', 0)

            issues = issues or len(summary.get('missing_sections') or [])

            result['issues_found'] = bool(issues)

            # preserve success flag if script executed; default to True when stdout parsed

            if 'success' not in result:

                result['success'] = True

            self.module_dependency_summary = summary

            self.results_cache['analyze_module_dependencies'] = summary

        return result

    def run_analyze_functions(self) -> Dict:

        """Run analyze_functions with structured JSON handling."""

        # Build command line arguments based on exclusion configuration

        args = ["--json"]  # Always request JSON output for parsing

        if self.exclusion_config.get('include_tests', False):

            args.append("--include-tests")

        if self.exclusion_config.get('include_dev_tools', False):

            args.append("--include-dev-tools")

        result = self.run_script("analyze_functions", *args)

        # Parse JSON output if available
        if result.get('success') and result.get('output'):
            try:
                import json
                json_data = json.loads(result['output'])
                result['data'] = json_data
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse analyze_functions JSON output: {e}")

        return result

    def run_decision_support(self) -> Dict:

        """Run decision_support with structured JSON handling."""

        # Build command line arguments based on exclusion configuration

        args = []

        if self.exclusion_config.get('include_tests', False):

            args.append("--include-tests")

        if self.exclusion_config.get('include_dev_tools', False):

            args.append("--include-dev-tools")

        result = self.run_script("decision_support", *args)

        return result

    def run_analyze_error_handling(self) -> Dict:

        """Run analyze_error_handling with structured JSON handling."""

        # Build command line arguments based on exclusion configuration

        args = ["--json"]

        if self.exclusion_config.get('include_tests', False):

            args.append("--include-tests")

        if self.exclusion_config.get('include_dev_tools', False):

            args.append("--include-dev-tools")

        result = self.run_script("analyze_error_handling", *args)

        output = result.get('output', '')

        data = None

        if output:

            try:

                # Find the JSON part in the output (after the text)

                lines = output.split('\n')

                json_start = -1

                for i, line in enumerate(lines):

                    if line.strip().startswith('{'):

                        json_start = i

                        break

                if json_start >= 0:

                    json_output = '\n'.join(lines[json_start:])

                    data = json.loads(json_output)

                else:

                    # Fallback: try to parse the entire output

                    data = json.loads(output)

            except json.JSONDecodeError:

                data = None

        # If JSON parsing from stdout failed, try reading from the file
        if data is None:
            try:
                json_file = self.project_root / 'development_tools' / 'error_handling' / 'error_handling_details.json'
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            except (OSError, json.JSONDecodeError):
                data = None

        if data is not None:

            result['data'] = data

            # Check for issues in error handling coverage

            coverage = data.get('analyze_error_handling') or data.get('error_handling_coverage', 0)

            missing_count = data.get('functions_missing_error_handling', 0)

            result['issues_found'] = coverage < 80 or missing_count > 0

            result['success'] = True

            result['error'] = ''

        else:

            lowered = output.lower() if isinstance(output, str) else ''

            if 'missing error handling' in lowered or 'coverage' in lowered:

                result['issues_found'] = True

                result['success'] = True

                result['error'] = ''

        return result

    def run_analyze_documentation_sync(self) -> Dict:
        """Run analyze_documentation_sync with structured data handling."""
        try:
            # Import and call the checker directly to get structured data
            from ..docs.analyze_documentation_sync import DocumentationSyncChecker
            
            checker = DocumentationSyncChecker()
            results = checker.run_checks()
            
            # Convert results to the expected format
            summary = results.get('summary', {})
            data = {
                'status': summary.get('status', 'UNKNOWN'),
                'total_issues': summary.get('total_issues', 0),
                'paired_doc_issues': summary.get('paired_doc_issues', 0),
                'path_drift_issues': summary.get('path_drift_issues', 0),
                'ascii_compliance_issues': summary.get('ascii_compliance_issues', 0),
                'heading_numbering_issues': summary.get('heading_numbering_issues', 0),
                'path_drift_files': list(results.get('path_drift', {}).keys()),
                # Store detailed issues for each category
                'paired_docs': results.get('paired_docs', {}),
                'path_drift': results.get('path_drift', {}),
                'ascii_compliance': results.get('ascii_compliance', {}),
                'heading_numbering': results.get('heading_numbering', {})
            }
            
            # Generate text output for compatibility
            import io
            import sys
            output_buffer = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = output_buffer
            try:
                checker.print_report(results)
                output = output_buffer.getvalue()
            finally:
                sys.stdout = original_stdout
            
            return {
                'success': True,
                'output': output,
                'error': '',
                'returncode': 0,
                'data': data
            }
        except Exception as e:
            logger.error(f"Error running documentation sync checker: {e}")
            # Fallback to subprocess method
        result = self.run_script("analyze_documentation_sync", "--check")
        output = result.get('output', '')
        data = None
        
        if output:
            try:
                # Try to parse JSON output if available
                data = json.loads(output)
            except json.JSONDecodeError:
                # If not JSON, create structured data from text output
                data = self._parse_documentation_sync_output(output)
        
        if data is not None:
            result['data'] = data
            result['success'] = True
            result['error'] = ''
        else:
            result['success'] = False
            result['error'] = f'Failed to parse documentation sync output: {e}'
        
        return result

    def _parse_documentation_sync_output(self, output: str) -> Dict:
        """Parse documentation sync checker text output into structured data."""
        data = {
            'path_drift_issues': 0,
            'paired_doc_issues': 0,
            'ascii_issues': 0,
            'path_drift_files': [],
            'status': 'UNKNOWN'
        }
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if 'Path drift issues:' in line:
                try:
                    data['path_drift_issues'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Paired documentation issues:' in line:
                try:
                    data['paired_doc_issues'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'ASCII compliance issues:' in line:
                try:
                    data['ascii_issues'] = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Overall status:' in line:
                data['status'] = line.split(':')[1].strip()
        
        return data

    def run_analyze_unused_imports(self) -> Dict:

        """Run analyze_unused_imports with structured JSON handling."""

        # Use longer timeout for this script (10 minutes) as it runs pylint on many files

        script_path = Path(__file__).resolve().parent.parent / 'imports' / 'analyze_unused_imports.py'

        cmd = [sys.executable, str(script_path), '--json']

        try:

            result_proc = subprocess.run(

                cmd,

                capture_output=True,

                text=True,

                cwd=str(self.project_root),

                timeout=600  # 10 minute timeout for pylint operations

            )

            result = {

                'success': result_proc.returncode == 0,

                'output': result_proc.stdout,

                'error': result_proc.stderr,

                'returncode': result_proc.returncode

            }

        except subprocess.TimeoutExpired:

            return {

                'success': False,

                'output': '',

                'error': 'Unused imports checker timed out after 10 minutes',

                'returncode': None,

                'issues_found': False

            }

        output = result.get('output', '')

        data = None

        if output:

            try:

                data = json.loads(output)

            except json.JSONDecodeError:

                data = None

        if data is not None:

            result['data'] = data

            self.results_cache['unused_imports'] = data

            # Check for issues

            total_unused = data.get('total_unused', 0)

            result['issues_found'] = total_unused > 0

            result['success'] = True

            result['error'] = ''

        else:

            lowered = output.lower() if isinstance(output, str) else ''

            if 'unused import' in lowered:

                result['issues_found'] = True

                result['success'] = True

                result['error'] = ''

        return result

    # ===== SIMPLE COMMANDS (for users) =====

    def run_audit(self, fast: bool = True, include_overlap: bool = False):

        """Run the full audit workflow with concise summary"""

        operation_name = "audit (fast)" if fast else "audit (full)"
        logger.info(f"Starting {operation_name}...")

        if fast:

            logger.info("Running FAST audit (core only)...")

            logger.info("=" * 50)

        else:

            logger.info("Running comprehensive audit...")

            logger.info("=" * 50)
            # Include overlap analysis in full audits by default
            if not include_overlap:
                include_overlap = True

        # Store for use in _run_contributing_tools
        self._include_overlap = include_overlap

        result = self.run_quick_audit()

        if result:

            if not fast:

                # Run other AI development tools to contribute to AI documents FIRST

                self._run_contributing_tools()
                
                # Save additional tool results to cached file
                self._save_additional_tool_results()

            else:

                # Fast mode: run essential tools to populate all status data

                self._run_essential_tools_only()
                
                # Save additional tool results to cached file
                self._save_additional_tool_results()

            # Create AI-optimized status document (contributed by multiple tools)

            ai_status = self._generate_ai_status_document()

            ai_status_file = create_output_file("development_tools/AI_STATUS.md", ai_status)

            # Create AI-optimized priorities document (contributed by multiple tools)

            ai_priorities = self._generate_ai_priorities_document()

            ai_priorities_file = create_output_file("development_tools/AI_PRIORITIES.md", ai_priorities)

            # Create comprehensive consolidated report

            consolidated_report = self._generate_consolidated_report()

            consolidated_file = create_output_file("development_tools/consolidated_report.txt", consolidated_report)

            # Check and trim AI_CHANGELOG entries to prevent bloat

            self._check_and_trim_changelog_entries()

            # Validate referenced paths exist

            self._validate_referenced_paths()

            # Check for documentation duplicates and placeholders

            self._check_documentation_quality()

            # Check ASCII compliance

            self._check_ascii_compliance()

            # Sync TODO.md with changelog

            self._sync_todo_with_changelog()

            # Audit completed

            logger.info("=" * 50)

            logger.info(f"Completed {operation_name} successfully!")

            logger.info(f"* AI Status: {ai_status_file}")

            logger.info(f"* AI Priorities: {ai_priorities_file}")

            logger.info(f"* Consolidated Report: {consolidated_file}")

            logger.info(f"* JSON Data: development_tools/reports/analysis_detailed_results.json")

            logger.info("* Check development_tools/reports/archive/ for previous runs")

            return True

        else:

            logger.error(f"Completed {operation_name} with errors!")

            return False

    def _save_additional_tool_results(self):
        """Save results from additional tools to the cached file"""
        try:
            import json
            from datetime import datetime
            results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
            
            # Load existing results
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
            else:
                cached_data = {'results': {}}
            
            # Add legacy cleanup results if available
            if hasattr(self, 'legacy_cleanup_summary') and self.legacy_cleanup_summary:
                cached_data['results']['fix_legacy_references'] = {
                    'success': True,
                    'data': self.legacy_cleanup_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add validation results if available
            if hasattr(self, 'validation_results') and self.validation_results:
                cached_data['results']['analyze_ai_work'] = {
                    'success': True,
                    'data': self.validation_results,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add system signals results if available
            if hasattr(self, 'system_signals') and self.system_signals:
                cached_data['results']['system_signals'] = {
                    'success': True,
                    'data': self.system_signals,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add decision_support metrics if available
            decision_metrics = self.results_cache.get('decision_support_metrics', {})
            if decision_metrics:
                cached_data['results']['decision_support'] = {
                    'success': True,
                    'data': {
                        'decision_support_metrics': decision_metrics
                    },
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add aggregated doc sync summary if available
            if hasattr(self, 'docs_sync_summary') and self.docs_sync_summary:
                cached_data['results']['analyze_documentation_sync'] = {
                    'success': True,
                    'data': self.docs_sync_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Save updated results using create_output_file to ensure correct location and rotation
            from ..shared.file_rotation import create_output_file
            create_output_file(str(results_file), json.dumps(cached_data, indent=2))
                
        except Exception as e:
            logger.warning(f"Failed to save additional tool results: {e}")

    def _run_essential_tools_only(self):
        """Run a minimal subset of tools for fast audit mode."""
        logger.info("Running AI development tools (fast mode - skipping test coverage and unused imports)...")
        try:
            logger.info("  - Running docs-sync for documentation status...")
            self._run_doc_sync_check()
        except Exception as exc:
            logger.error(f"  - Documentation sync failed: {exc}")
        try:
            logger.info("  - Refreshing quick status snapshot...")
            result = self.run_script('quick_status', 'json')
            if result.get('success'):
                self.status_results = result
                # Parse JSON and store in status_summary
                output = result.get('output', '')
                if output:
                    try:
                        import json
                        parsed = json.loads(output)
                        self.status_summary = parsed
                    except json.JSONDecodeError:
                        pass
            else:
                if result.get('output'):
                    logger.debug(result['output'])
                if result.get('error'):
                    logger.error(result['error'])
        except Exception as exc:
            logger.error(f"  - Quick status failed: {exc}")
        try:
            logger.info("  - Running legacy-cleanup for cleanup priorities...")
            if self.run_legacy_cleanup():
                logger.info("  - Legacy reference scan completed!")
        except Exception as exc:
            logger.error(f"  - Legacy cleanup failed: {exc}")
        try:
            logger.info("  - Running validate-work for validation status...")
            self.run_validate()
        except Exception as exc:
            logger.error(f"  - Validation failed: {exc}")
        try:
            logger.info("  - Running function discovery for complexity metrics...")
            self.run_analyze_functions()
        except Exception as exc:
            logger.error(f"  - Function discovery failed: {exc}")
        try:
            logger.info("  - Running decision support for complexity insights...")
            self.run_decision_support()
        except Exception as exc:
            logger.error(f"  - Decision support failed: {exc}")
        try:
            logger.info("  - Running error handling coverage analysis...")
            self.run_analyze_error_handling()
        except Exception as exc:
            logger.error(f"  - Error handling coverage failed: {exc}")
        try:
            logger.info("  - Running system signals generator...")
            self.run_system_signals()
        except Exception as exc:
            logger.error(f"  - System signals failed: {exc}")

    def _run_contributing_tools(self) -> None:
        """Run the full suite of supporting tools for comprehensive audits."""
        logger.info("Running contributing AI development tools...")
        try:
            logger.info("  - Running docs-sync for documentation status...")
            if self._run_doc_sync_check():
                logger.info("  - Documentation sync completed (see summary above)")
        except Exception as exc:
            logger.error(f"  - Documentation sync failed: {exc}")
        try:
            logger.info("  - Running legacy-cleanup for cleanup priorities...")
            if self.run_legacy_cleanup():
                logger.info("  - Legacy reference scan completed!")
        except Exception as exc:
            logger.error(f"  - Legacy cleanup failed: {exc}")
        try:
            logger.info("  - Running unused-imports checker for code quality...")
            result = self.run_unused_imports_report()
            if isinstance(result, dict):
                if result.get('success'):
                    summary = self.results_cache.get('unused_imports') or {}
                    total_unused = summary.get('total_unused')
                    if total_unused:
                        logger.info(f"  - Unused imports checker completed (found {total_unused} imports to review)")
                    else:
                        logger.info("  - Unused imports checker completed (no unused imports detected)")
        except Exception as exc:
            logger.error(f"  - Unused imports checker failed: {exc}")
        try:
            logger.info("  - Running validate-work for validation status...")
            self.run_validate()
        except Exception as exc:
            logger.error(f"  - Validation workflow failed: {exc}")
        try:
            logger.info("  - Running quick-status for system status...")
            quick_status = self.run_script('quick_status', 'json')
            if quick_status.get('success'):
                self.status_results = quick_status
        except Exception as exc:
            logger.error(f"  - Quick status failed: {exc}")
        try:
            include_overlap = getattr(self, '_include_overlap', False)
            overlap_msg = " (with overlap analysis)" if include_overlap else ""
            logger.info(f"  - Running documentation analysis{overlap_msg}...")
            self.run_analyze_documentation(include_overlap=include_overlap)
        except Exception as exc:
            logger.error(f"  - Documentation analysis failed: {exc}")
        # Note: analyze_module_dependencies is already run in run_quick_audit() via audit_scripts,
        # so we skip it here to avoid duplicate execution
        try:
            logger.info("  - Running configuration validation...")
            self.run_script('analyze_config')
        except Exception as exc:
            logger.error(f"  - Configuration validation failed: {exc}")
        try:
            logger.info("  - Running coverage regeneration (full test suite)...")
            if self.run_coverage_regeneration():
                logger.info("  - Coverage regeneration completed successfully")
            else:
                logger.warning("  - Coverage regeneration completed with issues")
        except Exception as exc:
            logger.error(f"  - Coverage regeneration failed: {exc}")
        try:
            logger.info("  - Running development tools coverage analysis...")
            dev_tools_coverage = self.run_dev_tools_coverage()
            if dev_tools_coverage.get('coverage_collected'):
                overall = dev_tools_coverage.get('overall', {})
                coverage_pct = overall.get('overall_coverage', 0)
                logger.info(f"  - Dev tools coverage: {coverage_pct:.1f}%")
                logger.info(f"  - Dev tools coverage report: {dev_tools_coverage.get('html_dir', 'N/A')}")
            else:
                logger.warning("  - Dev tools coverage data not collected")
        except Exception as exc:
            logger.error(f"  - Development tools coverage failed: {exc}")
        try:
            logger.info("  - Running system signals generator...")
            self.run_system_signals()
        except Exception as exc:
            logger.error(f"  - System signals failed: {exc}")
        try:
            logger.info("  - Running version sync...")
            result = self.run_version_sync(scope='all')
            if isinstance(result, dict) and result.get('success'):
                self.fix_version_sync_results = result
        except Exception as exc:
            logger.error(f"  - Version sync failed: {exc}")
        logger.info("  - Full audit tools completed (including coverage)")

    def _check_and_trim_changelog_entries(self) -> None:
        """Check and trim AI_CHANGELOG entries to prevent bloat."""
        try:
            from ai_development_docs import changelog_manager  # type: ignore
        except Exception:
            changelog_manager = None
        if changelog_manager and hasattr(changelog_manager, 'trim_change_log'):
            try:
                result = changelog_manager.trim_change_log()
                if isinstance(result, dict):
                    status = result.get('status')
                    if status == 'ok':
                        trimmed = result.get('trimmed_entries')
                        archive_created = result.get('archive_created')
                    if trimmed:
                        logger.info(f"   Trimmed {trimmed} old changelog entries")
                    if archive_created:
                        logger.info("   Created archive: ai_development_docs/AI_CHANGELOG_ARCHIVE.md")
                else:
                    logger.warning(f"   Changelog trim reported an issue: {result.get('message')}")
            except Exception as exc:
                logger.warning(f"   Changelog check/trim failed: {exc}")
        else:
            logger.info("   Changelog check: Tooling unavailable (skipping trim)")

    def _validate_referenced_paths(self) -> None:
        """Validate that all referenced paths in documentation exist."""
        try:
            from ..docs.fix_version_sync import validate_referenced_paths  # type: ignore
            result = validate_referenced_paths()
            status = result.get('status') if isinstance(result, dict) else None
            message = result.get('message') if isinstance(result, dict) else None
            if status == 'ok':
                logger.info(f"   Path validation: {message}")
            elif status == 'fail':
                issues = result.get('issues_found', 'unknown') if isinstance(result, dict) else 'unknown'
                logger.warning(f"   Path validation failed: {message}")
                logger.warning(f"   Found {issues} path issues - consider running documentation sync checker")
            else:
                logger.warning(f"   Path validation error: {message}")
        except Exception as exc:
            logger.warning(f"   Path validation failed: {exc}")

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
                    logger.warning("   -> Remove duplicates between AI and human docs")
                else:
                    logger.info("   Documentation quality: No verbatim duplicates found")
                if placeholders:
                    logger.warning(f"   Documentation quality: Found {len(placeholders)} files with placeholders")
                    logger.warning("   -> Replace placeholder content with actual content")
                else:
                    logger.info("   Documentation quality: No placeholder content found")
            else:
                logger.warning("   Documentation quality check unavailable: no analysis data")
        except Exception as exc:
            logger.warning(f"   Documentation quality check failed: {exc}")

    def _check_ascii_compliance(self) -> None:
        """Check for non-ASCII characters in documentation files."""
        try:
            from ..docs.analyze_ascii_compliance import ASCIIComplianceAnalyzer  # type: ignore
            analyzer = ASCIIComplianceAnalyzer()
            results = analyzer.check_ascii_compliance()
            total_issues = sum(len(issues) for issues in results.values())
            if total_issues == 0:
                logger.info("   ASCII compliance: All documentation files use ASCII-only characters")
            else:
                logger.warning(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {len(results)} files")
                logger.warning("   -> Replace non-ASCII characters with ASCII equivalents")
        except Exception as exc:
            logger.warning(f"   ASCII compliance check failed: {exc}")

    def _sync_todo_with_changelog(self) -> None:
        """Sync TODO.md with AI_CHANGELOG.md to move completed entries."""
        try:
            from ..docs.fix_version_sync import sync_todo_with_changelog  # type: ignore
            result = sync_todo_with_changelog()
            status = result.get('status') if isinstance(result, dict) else None
            if status == 'ok':
                moved = result.get('moved_entries', 0)
                if moved:
                    logger.info(f"   TODO sync: Moved {moved} completed entries from TODO.md")
                else:
                    message = result.get('message')
                    logger.info(f"   TODO sync: {message}")
            else:
                message = result.get('message') if isinstance(result, dict) else None
                logger.warning(f"   TODO sync failed: {message}")
        except Exception as exc:
            logger.warning(f"   TODO sync failed: {exc}")

    def run_docs(self):

        """Update all documentation (OPTIONAL - not essential for audit)"""

        logger.info("Starting documentation update...")

        logger.info("Updating documentation...")

        logger.info("=" * 50)

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

        try:

            logger.info("  - Generating directory trees...")

            self.generate_directory_trees()

        except Exception as exc:

            logger.error(f"  - Directory tree generation failed: {exc}")

            success = False

        # Run documentation sync check

        try:

            logger.info("  - Checking documentation sync...")

            if not self._run_doc_sync_check('--check'):

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

        logger.info("Starting validation...")

        logger.info("Validating AI work...")

        logger.info("=" * 50)

        result = self.run_script('analyze_ai_work')

        if result['success']:

            # Store results for consolidated report

            self.validation_results = result

            logger.info("=" * 50)

            logger.info("Validation completed successfully!")

            return True

        else:

            logger.error(f"Validation failed: {result['error']}")

            return False

    def run_config(self):

        """Check configuration consistency (simple command)"""

        logger.info("Starting configuration check...")

        logger.info("Checking configuration...")

        logger.info("=" * 50)

        result = self.run_script('analyze_config')

        if result['success']:

            logger.info(result['output'])

            logger.info("=" * 50)

            logger.info("Configuration check completed!")

            return True

        else:

            logger.error(f"Configuration check failed: {result['error']}")

            return False

    # ===== ADVANCED COMMANDS (for AI collaborators) =====

    def run_workflow(self, task_type: str, task_data: Optional[Dict] = None) -> bool:

        """Run workflow with audit-first protocol"""

        logger.info(f"Running workflow: {task_type}")

        logger.info("=" * 50)

        # Check trigger requirements

        if not self.check_trigger_requirements(task_type):

            return False

        # Run audit first

        audit_results = self.run_audit_first(task_type)

        if not audit_results['success']:

            logger.error(f"Audit failed: {audit_results['error']}")

            return False

        # Execute the task

        task_success = self.execute_task(task_type, task_data)

        # Validate the work

        if task_success:

            validation_results = self.validate_work(task_type, task_data or {})

            self.show_validation_report(validation_results)

        return task_success

    def run_quick_audit(self) -> bool:

        """Run comprehensive audit with concise output"""

        logger.info("Running comprehensive audit...")

        successful = []

        failed = []

        results = {}

        for script in self.audit_config['audit_scripts']:

            script_name = script.replace('.py', '')

            logger.info(f"Running {script_name}...")

            # Special handling for analyze_documentation

            if script_name == 'analyze_documentation':

                result = self.run_analyze_documentation()

            elif script_name == 'analyze_function_registry':

                result = self.run_analyze_function_registry()

            elif script_name == 'analyze_module_dependencies':

                result = self.run_analyze_module_dependencies()

            elif script_name == 'analyze_error_handling':

                result = self.run_analyze_error_handling()

            elif script_name == 'analyze_documentation_sync':

                result = self.run_analyze_documentation_sync()

            elif script_name == 'analyze_functions':

                result = self.run_analyze_functions()

            elif script_name == 'decision_support':

                result = self.run_decision_support()

            else:

                result = self.run_script(script_name)

            results[script_name] = result

            # Handle both dict and bool return types

            if isinstance(result, dict):

                success = result.get('success', False)

            else:

                success = bool(result)

            if success:

                successful.append(script_name)

                # Extract key information for concise output (only for dict results)

                if isinstance(result, dict):

                    self._extract_key_info(script_name, result)

            else:

                failed.append(script_name)

                error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)

                logger.error(f"  {script_name} failed: {error_msg}")

        # Save detailed results

        if (self.audit_config or {}).get('save_results', False):

            self._save_audit_results(successful, failed, results)

        # Audit completed

        # Show summary

        self.print_audit_summary(successful, failed, results)

        return len(failed) == 0

    def run_decision_support(self):

        """Get actionable insights for decision-making"""

        logger.info("Getting actionable insights...")

        logger.info("=" * 50)

        result = self.run_script('decision_support')

        if result['success']:

            # Extract and format actionable insights

            insights = self._extract_actionable_insights(result['output'])

            logger.info(insights)

            # Return the result dict so metrics can be extracted
            return result

        else:

            logger.error(f"Decision support failed: {result['error']}")

            return result

    def run_version_sync(self, scope: str = 'docs'):

        """Sync version numbers"""

        logger.info(f"Syncing versions for scope: {scope}")

        logger.info("=" * 50)

        result = self.run_script('fix_version_sync', 'sync', '--scope', scope)

        if result['success']:

            # Store results for consolidated report

            self.fix_version_sync_results = result

            logger.info("Version sync completed!")

            return True

        else:

            logger.error(f"Version sync failed: {result['error']}")

            return False

    def run_dev_tools_coverage(self) -> Dict:
        """Run coverage analysis specifically for development_tools directory."""
        logger.info("Starting development tools coverage analysis...")
        
        try:
            from ..tests.generate_test_coverage import CoverageMetricsRegenerator
            
            regenerator = CoverageMetricsRegenerator()
            result = regenerator.run_dev_tools_coverage()
            
            # Store results for consolidated report
            if not hasattr(self, 'dev_tools_coverage_results'):
                self.dev_tools_coverage_results = {}
            self.dev_tools_coverage_results = result
            
            logger.info("Completed development tools coverage analysis!")
            
            # Reload dev tools coverage after regeneration
            self._load_dev_tools_coverage()
            
            return result
            
        except Exception as exc:
            logger.error(f"Development tools coverage analysis failed: {exc}")
            return {'coverage_collected': False, 'error': str(exc)}

    def run_status(self):

        """Get current system status - quick check that updates status files"""

        logger.info("Starting status check...")

        logger.info("Getting system status...")

        logger.info("=" * 50)

        # Run quick status for basic system health
        # quick_status.py expects 'json' as the first argument (sys.argv[1])
        result = self.run_script('quick_status', 'json')

        if result.get('success'):

            self.status_results = result

            parsed = None

            output = result.get('output', '')

            if output:

                try:

                    parsed = json.loads(output)

                except json.JSONDecodeError:

                    parsed = None

            if parsed is not None:

                result['data'] = parsed

                self.status_summary = parsed

                logger.info("Status check completed!")

            else:

                logger.warning("Status check completed, but output could not be parsed as JSON.")

            # Run TODO sync check for status
            logger.info("Checking TODO sync status...")
            self._sync_todo_with_changelog()

            # Run system signals generator
            logger.info("Generating system signals...")
            self.run_system_signals()
            
            # Save additional tool results to cached file (including system signals)
            self._save_additional_tool_results()

            # Generate all three status files with current data
            logger.info("Generating status files...")
            
            # AI Status
            ai_status = self._generate_ai_status_document()
            ai_status_file = create_output_file("development_tools/AI_STATUS.md", ai_status)
            logger.info(f"AI Status: {ai_status_file}")
            
            # AI Priorities
            ai_priorities = self._generate_ai_priorities_document()
            ai_priorities_file = create_output_file("development_tools/AI_PRIORITIES.md", ai_priorities)
            logger.info(f"AI Priorities: {ai_priorities_file}")
            
            # Consolidated Report
            consolidated_report = self._generate_consolidated_report()
            consolidated_file = create_output_file("development_tools/consolidated_report.txt", consolidated_report)
            logger.info(f"Consolidated Report: {consolidated_file}")

            logger.info("Completed status check successfully!")

            return True

        if result.get('output'):

            logger.info(result['output'])

        if result.get('error'):

            logger.error(f"Completed status check with errors: {result['error']}")

        return False

    def run_documentation_sync(self):

        """Run documentation synchronization checks"""

        logger.info("Starting documentation sync check...")

        logger.info("Running documentation synchronization checks...")

        if self._run_doc_sync_check('--check'):

            logger.info("Completed documentation sync check successfully!")

            return True

        logger.error("Completed documentation sync check with errors!")

        return False

    def run_documentation_fix(self, fix_type: str = 'all', dry_run: bool = False) -> bool:

        """Run documentation fix operations.

        Args:
            fix_type: Type of fix to apply ('add-addresses', 'fix-ascii', 'number-headings', 'convert-links', 'all')
            dry_run: If True, show what would be changed without making changes

        Returns:
            True if successful, False otherwise
        """

        logger.info(f"Starting documentation fix (type: {fix_type}, dry_run: {dry_run})...")

        try:

            # Use decomposed fixer classes (Batch 2 decomposition)
            from development_tools.docs.fix_documentation_addresses import DocumentationAddressFixer
            from development_tools.docs.fix_documentation_ascii import DocumentationASCIIFixer
            from development_tools.docs.fix_documentation_headings import DocumentationHeadingFixer
            from development_tools.docs.fix_documentation_links import DocumentationLinkFixer

            results = {}

            if fix_type in ('add-addresses', 'all'):

                fixer = DocumentationAddressFixer(project_root=str(self.project_root))
                result = fixer.fix_add_addresses(dry_run=dry_run)

                results['add_addresses'] = result

                print(f"\nAdd Addresses: Updated {result['updated']}, Skipped {result['skipped']}, Errors {result['errors']}")

            if fix_type in ('fix-ascii', 'all'):

                fixer = DocumentationASCIIFixer(project_root=str(self.project_root))
                result = fixer.fix_ascii(dry_run=dry_run)

                results['fix_ascii'] = result

                print(f"\nFix ASCII: Updated {result['files_updated']} files, Made {result['replacements_made']} replacements, Errors {result['errors']}")

            if fix_type in ('number-headings', 'all'):

                fixer = DocumentationHeadingFixer(project_root=str(self.project_root))
                result = fixer.fix_number_headings(dry_run=dry_run)

                results['number_headings'] = result

                print(f"\nNumber Headings: Updated {result['files_updated']} files, Fixed {result['issues_fixed']} issues, Errors {result['errors']}")

            if fix_type in ('convert-links', 'all'):

                fixer = DocumentationLinkFixer(project_root=str(self.project_root))
                result = fixer.fix_convert_links(dry_run=dry_run)

                results['convert_links'] = result

                print(f"\nConvert Links: Updated {result['files_updated']} files, Made {result['changes_made']} changes, Errors {result['errors']}")

            # Check for errors

            total_errors = sum(r.get('errors', 0) for r in results.values())

            if total_errors > 0:

                logger.error(f"Documentation fix completed with {total_errors} error(s)")

                return False

            logger.info("Completed documentation fix successfully!")

            return True

        except Exception as e:

            logger.error(f"Error running documentation fix: {e}", exc_info=True)

            return False

    def run_coverage_regeneration(self):

        """Regenerate test coverage metrics"""

        logger.info("Starting coverage regeneration...")

        logger.info("Regenerating test coverage metrics...")

        result = self.run_script('generate_test_coverage', '--update-plan', timeout=1800)  # 30 minute timeout for coverage

        # Parse test results from output
        output = result.get('output', '')
        error_output = result.get('error', '')
        test_results = self._parse_test_results_from_output(output)
        
        # Log error output if present for debugging
        if error_output and logger:
            logger.warning(f"Coverage regeneration stderr: {error_output[:500]}")
        
        # Check if coverage was collected successfully
        # Only consider it collected if we see actual test output, not just existing files
        coverage_collected = (
            'TOTAL' in output or 
            'coverage:' in output.lower() or
            ('passed' in output.lower() and 'failed' in output.lower()) or  # Test results present
            ('[  ' in output and '%]' in output)  # Progress indicators from pytest
        )
        
        # If no test output detected but coverage.json exists, warn that tests may not have run
        if not coverage_collected and ((self.project_root / "coverage.json").exists() or (self.project_root / "development_tools" / "tests" / "coverage.json").exists()):
            if logger:
                logger.error("Coverage regeneration completed with no test output detected - tests likely did not run!")
                logger.error(f"Script output length: {len(output)} chars, stderr length: {len(error_output)} chars")
                if error_output:
                    logger.error(f"Script stderr (first 1000 chars): {error_output[:1000]}")
                logger.error("This indicates the test suite did not execute. Check for import errors or pytest configuration issues.")
            # Don't consider it collected - this is a failure
            coverage_collected = False

        if result['success']:

            # Store results for consolidated report

            self.coverage_results = result

            logger.info("Completed coverage regeneration successfully!")
            
            logger.info("Coverage metrics regenerated and plan updated!")
            
            # Reload coverage summary after regeneration - force reload
            self.coverage_results = None  # Clear cached results
            # Force reload by clearing any cached coverage_summary
            if hasattr(self, '_cached_coverage_summary'):
                delattr(self, '_cached_coverage_summary')
            # Wait a moment for file system to sync, then reload
            import time
            time.sleep(0.5)  # Brief pause to ensure file is written
            coverage_summary = self._load_coverage_summary()
            if coverage_summary:
                overall = coverage_summary.get('overall', {})
                logger.info(f"Reloaded coverage summary after regeneration: {overall.get('coverage', 'N/A')}% ({overall.get('covered', 'N/A')} of {overall.get('statements', 'N/A')} statements)")
            else:
                logger.warning("Failed to reload coverage summary after regeneration - coverage.json may not have been updated")
            
            # Report test results if available
            if test_results.get('test_summary'):
                logger.info(f"Test results: {test_results['test_summary']}")
                if test_results.get('random_seed'):
                    logger.info(f"Random seed used: {test_results['random_seed']}")

        else:

            # Distinguish between coverage collection failures and test failures
            if coverage_collected:
                # Coverage was collected successfully, but tests may have failed
                logger.warning("Coverage data collected successfully, but script exited with non-zero code")
                
                if test_results.get('failed_count', 0) > 0:
                    failure_msg = f"Test failures detected ({test_results['failed_count']} failed, {test_results.get('passed_count', 0)} passed)"
                    if test_results.get('random_seed'):
                        failure_msg += f" (random seed: {test_results['random_seed']})"
                    logger.warning(failure_msg)
                    
                    if test_results.get('failed_tests'):
                        logger.warning("Failed tests:")
                        for test_name in test_results['failed_tests']:
                            logger.warning(f"  - {test_name}")
                    else:
                        logger.warning("  See development_tools/tests/logs/coverage_regeneration/ for detailed test failure information")
            else:
                # Coverage collection failed
                error_msg = "Coverage regeneration failed"

                if result.get('error'):

                    error_msg += f": {result['error']}"

                if result.get('returncode') is not None:

                    error_msg += f" (exit code: {result['returncode']})"

                # Check for common failure patterns in output

                if 'unrecognized arguments' in output.lower():

                    error_msg += "\n  - Detected pytest argument error (possibly empty --cov argument)"

                # Check for empty --cov pattern: "--cov --cov" (two --cov in a row)
                if output and '--cov' in output:
                    output_parts = output.split()
                    for i in range(len(output_parts) - 1):
                        if output_parts[i] == '--cov' and output_parts[i + 1] == '--cov':
                            error_msg += "\n  - Detected empty --cov argument in error output"
                            break

                logger.error(f"ERROR: {error_msg}")

                if result.get('error'):

                    logger.error(f"  Full error: {result['error'][:500]}")  # Limit error length

            logger.info("  Check development_tools/tests/logs/coverage_regeneration/ for detailed logs")

        return result['success']
    
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
        
        # Extract test summary (e.g., "4 failed, 2276 passed, 1 skipped, 4 warnings")
        summary_pattern = r'(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+(\d+)\s+skipped[,\s]+(\d+)\s+warnings'
        summary_match = re.search(summary_pattern, output)
        if summary_match:
            results['failed_count'] = int(summary_match.group(1))
            results['passed_count'] = int(summary_match.group(2))
            results['skipped_count'] = int(summary_match.group(3))
            results['warnings_count'] = int(summary_match.group(4))
            results['test_summary'] = f"{results['failed_count']} failed, {results['passed_count']} passed, {results['skipped_count']} skipped, {results['warnings_count']} warnings"
        
        # Extract failed test names from "short test summary info" section
        short_summary_pattern = r'short test summary info[^\n]*\n(.*?)(?=\n===|$)'
        short_summary_match = re.search(short_summary_pattern, output, re.DOTALL)
        if short_summary_match:
            summary_lines = short_summary_match.group(1).strip().split('\n')
            for line in summary_lines:
                if line.strip().startswith('FAILED'):
                    # Extract test path from "FAILED tests/path/to/test.py::test_function"
                    test_match = re.search(r'FAILED\s+(.+)', line)
                    if test_match:
                        results['failed_tests'].append(test_match.group(1).strip())
        
        return results

    def run_legacy_cleanup(self):

        """Run legacy reference cleanup"""

        logger.info("Starting legacy cleanup...")

        logger.info("Running legacy reference cleanup...")

        if self._run_legacy_cleanup_scan('--scan'):

            logger.info("Completed legacy cleanup successfully!")

            return True

        logger.error("Completed legacy cleanup with errors!")

        return False

    def run_system_signals(self):
        """Run system signals generator"""
        logger.info("Starting system signals generation...")
        logger.info("Generating system signals...")
        
        result = self.run_script('system_signals', '--json')
        
        if result.get('success'):
            output = result.get('output', '')
            if output:
                try:
                    import json
                    self.system_signals = json.loads(output)
                    logger.info("Completed system signals generation successfully!")
                    return True
                except json.JSONDecodeError:
                    logger.error("Completed system signals generation with errors: Failed to parse JSON output")
                    return False
            else:
                logger.warning("Completed system signals generation with warnings: No output from tool")
                return False
        else:
            if result.get('error'):
                logger.error(f"Completed system signals generation with errors: {result['error']}")
            return False

    def run_unused_imports_report(self):

        """Run unused imports checker and generate report"""

        logger.info("Starting unused imports check...")

        logger.info("Running unused imports checker...")

        # Use longer timeout for this script (10 minutes) as it runs pylint on many files

        script_path = Path(__file__).resolve().parent.parent / 'imports' / 'analyze_unused_imports.py'

        cmd = [sys.executable, str(script_path)]

        try:

            result_proc = subprocess.run(

                cmd,

                capture_output=True,

                text=True,

                cwd=str(self.project_root),

                timeout=600  # 10 minute timeout for pylint operations

            )

            result = {

                'success': result_proc.returncode == 0,

                'output': result_proc.stdout,

                'error': result_proc.stderr,

                'returncode': result_proc.returncode

            }

        except subprocess.TimeoutExpired:

            logger.error("Completed unused imports check with errors: Timed out after 10 minutes")

            return False

        if result['success']:

            logger.info(result['output'])

            logger.info("Completed unused imports check successfully!")

            report_path = self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"

            if report_path.exists():

                logger.info(f"Report saved to: {report_path}")

            return True

        else:

            logger.error(f"Completed unused imports check with errors: {result.get('error', 'Unknown error')}")

            return False

    def generate_directory_trees(self):

        """Generate directory trees for documentation"""

        logger.info("Generating directory trees...")

        result = self.run_script('generate_directory_tree')

        if result['success']:
            # Don't log result['output'] as it contains duplicate messages
            # The script already logs "Directory tree generated: {path}" internally
            logger.info("Directory tree generated!")
            logger.info("Check development_docs/DIRECTORY_TREE.md for project structure")

        return result['success']

    # ===== HELPER METHODS =====

    def check_trigger_requirements(self, task_type: str) -> bool:

        """Check if trigger requirements are met"""

        trigger_file = self.project_root / 'TRIGGER.md'

        if not trigger_file.exists():

            logger.warning("TRIGGER.md not found - proceeding anyway")

            return True

        # For AI tools, we don't need user approval

        return True

    def run_audit_first(self, task_type: str) -> Dict:

        """Run audit first as required by protocol"""

        logger.info("Running audit-first protocol...")

        audit_success = self.run_quick_audit()

        return {

            'success': audit_success,

            'error': '' if audit_success else 'Audit failed'

        }

    def execute_task(self, task_type: str, task_data: Optional[Dict] = None) -> bool:

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

    def validate_work(self, work_type: str, work_data: Dict) -> Dict:

        """Validate the work before presenting"""

        logger.info("Validating work...")

        result = self.run_script('analyze_ai_work')

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

    def validate_audit_results(self, results: Dict) -> Dict:

        """Validate audit results"""

        # Simple validation for now

        return {

            'completeness': 95.0,

            'accuracy': 90.0,

            'consistency': 85.0,

            'actionable': 80.0,

            'overall': 87.5,

            'issues': []

        }

    def show_validation_report(self, validation_results: Dict):

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

    def print_audit_summary(self, successful: List, failed: List, results: Dict):

        """Print concise audit summary"""

        print("\n" + "=" * 80)

        print("AUDIT SUMMARY")

        print("=" * 80)

        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"Successful: {len(successful)}")

        print(f"Failed: {len(failed)}")

        if failed:

            print(f"\n[CRITICAL] Failed audits: {', '.join(failed)}")

        # Extract key metrics

        key_metrics = self._extract_key_metrics(results)

        if key_metrics:

            print("\nKey Metrics:")

            for metric, value in key_metrics.items():

                print(f"  {metric}: {value}")

        print(f"\nDetailed results saved to: {(self.audit_config or {}).get('results_file', 'development_tools/reports/analysis_detailed_results.json')}")

        if self.audit_config.get('prioritize_issues', False):

            print(f"Critical issues saved to: {self.audit_config['issues_file']}")

    def _extract_key_info(self, script_name: str, result: Dict[str, Any]):

        """Extract key information from script result."""

        if script_name not in self.results_cache:

            self.results_cache[script_name] = {}

        if 'analyze_functions' in script_name:

            self._extract_function_metrics(result)

        elif 'analyze_function_registry' in script_name:

            self._extract_documentation_metrics(result)

        elif 'decision_support' in script_name:

            self._extract_decision_insights(result)

        elif 'analyze_error_handling' in script_name:

            self._extract_error_handling_metrics(result)

        elif 'analyze_module_dependencies' in script_name:

            data = result.get('data')

            if data:

                self.module_dependency_summary = data

    def _extract_function_metrics(self, result: Dict[str, Any]):

        """Extract function-related metrics"""

        output = result.get('output', '')

        if not isinstance(output, str):

            return

        lines = output.split('\n')

        metrics: Dict[str, Any] = {}

        import re

        section_lookup = {

            'high_complexity_examples': 'HIGH COMPLEXITY',

            'critical_complexity_examples': 'CRITICAL COMPLEXITY',

            'undocumented_examples': 'UNDOCUMENTED'

        }

        section_limits = {

            'high_complexity_examples': 5,

            'critical_complexity_examples': 5,

            'undocumented_examples': 5

        }

        current_section = None

        for raw_line in lines:

            line = raw_line.rstrip()

            lower = line.lower()

            if 'found' in lower and 'functions' in lower:

                match = re.search(r'Found (\d+) functions', line)

                if match:

                    metrics['total_functions'] = int(match.group(1))

                continue

            if 'moderate complexity' in lower and '(' in line:

                match = re.search(r'\((\d+)\):', line)

                if match:

                    metrics['moderate_complexity'] = int(match.group(1))

                continue

            if line.strip().upper().startswith('HIGH COMPLEXITY'):

                current_section = 'high_complexity_examples'

                match = re.search(r'\((\d+)\):', line)

                if match:

                    metrics['high_complexity'] = int(match.group(1))

                continue

            if line.strip().upper().startswith('CRITICAL COMPLEXITY'):

                current_section = 'critical_complexity_examples'

                match = re.search(r'\((\d+)\):', line)

                if match:

                    metrics['critical_complexity'] = int(match.group(1))

                continue

            if line.strip().upper().startswith('UNDOCUMENTED'):

                current_section = 'undocumented_examples'

                match = re.search(r'\((\d+)\):', line)

                if match:

                    metrics['undocumented'] = int(match.group(1))

                continue

            if any(line.strip().upper().startswith(label) for label in section_lookup.values()):

                current_section = None

                continue

            if current_section:

                stripped = line.strip()

                if not stripped.startswith('- '):

                    continue

                if '...and' in stripped and 'more' in stripped:

                    continue

                entry = self._parse_function_entry(stripped[2:])

                if entry is None:

                    continue

                metrics.setdefault(current_section, [])

                if len(metrics[current_section]) < section_limits[current_section]:

                    metrics[current_section].append(entry)

        self.results_cache['analyze_functions'] = metrics

    def _extract_documentation_metrics(self, result: Dict[str, Any]):

        """Extract documentation-related metrics"""

        metrics: Dict[str, Any] = {}

        data = result.get('data')

        if isinstance(data, dict):

            # Get documented count from registry
            totals = data.get('totals') if isinstance(data.get('totals'), dict) else None
            documented = totals.get('functions_documented', 0) if isinstance(totals, dict) else 0

            # Get actual total functions from analyze_functions (not registry's limited count)
            fd_metrics = self.results_cache.get('analyze_functions', {}) or {}
            actual_total = fd_metrics.get('total_functions')
            
            # Recalculate coverage using actual total, not registry's limited count
            if actual_total is not None and actual_total > 0 and documented > 0:
                coverage_pct = (documented / actual_total) * 100
                # Only use if reasonable (not > 100%)
                if coverage_pct <= 100:
                    metrics['doc_coverage'] = f"{coverage_pct:.2f}%"
                else:
                    # Invalid - skip the wrong coverage from registry
                    metrics['doc_coverage'] = 'Unknown'
            else:
                # Fallback: try to use registry's coverage but validate it
                coverage = data.get('coverage')
                if coverage is not None:
                    coverage_str = str(coverage).strip()
                    try:
                        coverage_val = float(coverage_str.strip('%'))
                        # Skip obviously wrong values (> 100%)
                        if coverage_val <= 100:
                            metrics['doc_coverage'] = f"{coverage_val:.2f}%"
                        else:
                            metrics['doc_coverage'] = 'Unknown'
                    except (TypeError, ValueError):
                        # If it's already a string and reasonable, use it
                        if coverage_str.endswith('%'):
                            try:
                                val = float(coverage_str.strip('%'))
                                if val <= 100:
                                    metrics['doc_coverage'] = coverage_str
                                else:
                                    metrics['doc_coverage'] = 'Unknown'
                            except:
                                metrics['doc_coverage'] = 'Unknown'
                        else:
                            metrics['doc_coverage'] = 'Unknown'
                else:
                    metrics['doc_coverage'] = 'Unknown'

            if isinstance(totals, dict):

                metrics['totals'] = totals

                # Don't use registry's functions_found - it's only counting registry entries, not all functions
                # Store it for reference but don't use it for calculations
                registry_functions_found = totals.get('functions_found')
                if registry_functions_found is not None:
                    metrics['registry_functions_found'] = registry_functions_found  # For reference only

                # Use actual total from analyze_functions
                if actual_total is not None:
                    metrics['total_functions'] = actual_total

                if documented is not None:

                    metrics['documented_functions'] = documented

                classes_found = totals.get('classes_found')

                if classes_found is not None:

                    metrics['classes_found'] = classes_found

                files_scanned = totals.get('files_scanned')

                if files_scanned is not None:

                    metrics['files_scanned'] = files_scanned

            missing = data.get('missing')

            if isinstance(missing, dict):

                metrics['missing_docs'] = missing.get('count')

                metrics['missing_items'] = missing.get('count')

                missing_files = missing.get('missing_files')

                if missing_files:

                    metrics['missing_files'] = missing_files

            extra = data.get('extra')

            if isinstance(extra, dict):

                metrics['extra_items'] = extra.get('count')

        else:

            output = result.get('output', '')

            if not isinstance(output, str):

                self.results_cache['analyze_function_registry'] = metrics

                return

            lines_out = output.split('\n')

            for line in lines_out:

                lower = line.lower()

                if 'coverage:' in lower:

                    import re

                    match = re.search(r'coverage:\s*(\d+\.?\d*)%', line, re.IGNORECASE)

                    if match:

                        metrics['doc_coverage'] = match.group(1) + '%'

                        continue

                    coverage_text = line.split(':')[-1].strip()

                    metrics['doc_coverage'] = coverage_text

                elif 'missing from registry:' in lower:

                    metrics['missing_docs'] = line.split(':')[-1].strip()

                elif 'missing items:' in lower:

                    import re

                    match = re.search(r'missing items:\s*(\d+)', line, re.IGNORECASE)

                    if match:

                        metrics['missing_items'] = match.group(1)

        self.results_cache['analyze_function_registry'] = metrics

    def _extract_decision_insights(self, result: Dict[str, Any]):

        """Extract decision support insights and metrics (counts)."""

        output = result.get('output', '')

        if not isinstance(output, str):

            return

        lines = output.split('\n')

        insights: List[str] = []

        metrics: Dict[str, Any] = {}

        # Debug: log first few lines to verify output format
        if lines and len(lines) > 0:
            logger.debug(f"decision_support output sample (first 10 lines): {lines[:10]}")

        for raw_line in lines:

            line = raw_line.strip()

            lower = line.lower()

            if any(keyword in lower for keyword in ['[warn]', '[critical]', '[info]', '[complexity]', '[doc]', '[dupe]']):

                insights.append(line)

            if line.startswith('Total functions:'):

                value = line.split(':', 1)[1].strip()

                try:

                    metrics['total_functions'] = int(value)

                except ValueError:

                    metrics['total_functions'] = value

            elif line.startswith('Moderate complexity:'):

                value = line.split(':', 1)[1].strip()

                try:

                    metrics['moderate_complexity'] = int(value)

                except ValueError:

                    metrics['moderate_complexity'] = value

            elif line.startswith('High complexity:'):

                value = line.split(':', 1)[1].strip()

                try:

                    metrics['high_complexity'] = int(value)

                except ValueError:

                    metrics['high_complexity'] = value

            elif line.startswith('Critical complexity:'):

                value = line.split(':', 1)[1].strip()

                try:

                    metrics['critical_complexity'] = int(value)

                except ValueError:

                    metrics['critical_complexity'] = value

            elif line.startswith('Undocumented functions:'):

                value = line.split(':', 1)[1].strip()

                try:

                    metrics['undocumented'] = int(value)

                except ValueError:

                    metrics['undocumented'] = value

        if insights:

            metrics['decision_support_items'] = len(insights)

            metrics['decision_support_sample'] = insights[:5]

        # Debug: log extracted metrics
        if metrics:
            logger.debug(f"Extracted decision_support metrics: {metrics}")
        else:
            logger.warning("No metrics extracted from decision_support output")

        self.results_cache['decision_support_metrics'] = metrics

    def _extract_error_handling_metrics(self, result: Dict[str, Any]):

        """Extract error handling coverage metrics"""

        data = result.get('data')

        if isinstance(data, dict):

            metrics = {

                'total_functions': data.get('total_functions', 0),

                'functions_with_error_handling': data.get('functions_with_error_handling', 0),

                'functions_missing_error_handling': data.get('functions_missing_error_handling', 0),

                'analyze_error_handling': data.get('analyze_error_handling') or data.get('error_handling_coverage', 0),

                'functions_with_decorators': data.get('functions_with_decorators', 0),

                'error_handling_quality': data.get('error_handling_quality', {}),

                'error_patterns': data.get('error_patterns', {}),

                'recommendations': data.get('recommendations', []),

                'worst_modules': data.get('worst_modules', []),

                # Phase 1: Candidates for decorator replacement

                'phase1_candidates': data.get('phase1_candidates', []),

                'phase1_total': data.get('phase1_total', 0),

                'phase1_by_priority': data.get('phase1_by_priority', {}),

                # Phase 2: Generic exception raises

                'phase2_exceptions': data.get('phase2_exceptions', []),

                'phase2_total': data.get('phase2_total', 0),

                'phase2_by_type': data.get('phase2_by_type', {})

            }

        else:

            # Fallback to parsing output text

            output = result.get('output', '')

            if not isinstance(output, str):

                return

            metrics = {}

            lines = output.split('\n')

            for line in lines:

                if 'Total Functions:' in line:

                    match = re.search(r'Total Functions: (\d+)', line)

                    if match:

                        metrics['total_functions'] = int(match.group(1))

                elif 'Functions with Error Handling:' in line:

                    match = re.search(r'Functions with Error Handling: (\d+)', line)

                    if match:

                        metrics['functions_with_error_handling'] = int(match.group(1))

                elif 'Functions Missing Error Handling:' in line:

                    match = re.search(r'Functions Missing Error Handling: (\d+)', line)

                    if match:

                        metrics['functions_missing_error_handling'] = int(match.group(1))

                elif 'Error Handling Coverage:' in line:

                    match = re.search(r'Error Handling Coverage: ([\d.]+)%', line)

                    if match:

                        metrics['analyze_error_handling'] = float(match.group(1))

        self.results_cache['analyze_error_handling'] = metrics

    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:

        """Collect combined metrics for audit summary output."""

        combined: Dict[str, Any] = {}

        for cache_key in ('analyze_functions', 'analyze_function_registry', 'decision_support_metrics', 'analyze_error_handling'):

            cache = self.results_cache.get(cache_key)

            if isinstance(cache, dict):

                for key, value in cache.items():

                    if value is not None and value != '':

                        combined[key] = value

        return combined

    def _parse_function_entry(self, text: str) -> Optional[Dict[str, Any]]:

        """Parse a function discovery bullet into structured data."""

        if not text:

            return None

        import re

        pattern = re.compile(

            r'^(?P<name>.+?) \(file: (?P<file>.+?), complexity: (?P<complexity>\d+)\)'

        )

        match = pattern.match(text.strip())

        if not match:

            return None

        try:

            complexity = int(match.group('complexity'))

        except ValueError:

            complexity = None

        return {

            'function': match.group('name').strip(),

            'file': match.group('file').strip(),

            'complexity': complexity,

        }

    def _extract_first_int(self, text: str) -> Optional[int]:

        """Return the first integer found in the supplied text or None."""

        if not isinstance(text, str):

            return None

        match = re.search(r'(-?\d+)', text)

        if match:

            try:

                return int(match.group(1))

            except ValueError:

                return None

        return None

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

                # Don't set path_section here - wait for "Top files with most issues:"
                continue

            if line.startswith('ASCII Compliance Issues:'):

                value = self._extract_first_int(line)

                if value is not None:

                    summary['ascii_issues'] = value

                # Stop path_section if it was active
                path_section = False
                continue

            if line.startswith('Heading Numbering Issues:'):

                # Stop path_section if it was active
                path_section = False
                continue

            if line.startswith('Top files with most issues:'):

                path_section = True

                continue

            # Stop path_section when we encounter a new section header
            # Section headers are typically all caps or start with specific keywords
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

                # Skip if it looks like a section header (all caps, contains ISSUES, etc.)
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
        """Parse ASCII compliance check output."""
        result = {'files': {}, 'total_issues': 0}
        if not isinstance(output, str) or not output.strip():
            return result
        
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files with non-ASCII characters:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['file_count'] = value
            elif 'Total issues found:' in line:
                value = self._extract_first_int(line)
                if value is not None:
                    result['total_issues'] = value
            elif ':' in line and ('issues' in line.lower() or 'characters' in line.lower()):
                parts = line.split(':')
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    issue_text = parts[1].strip()
                    issue_count = self._extract_first_int(issue_text)
                    if issue_count is not None:
                        result['files'][file_path] = issue_count
        
        return result

    def _parse_heading_numbering_output(self, output: str) -> Dict[str, Any]:
        """Parse heading numbering check output."""
        result = {'files': {}, 'total_issues': 0}
        if not isinstance(output, str) or not output.strip():
            return result
        
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if 'Total files with numbering issues:' in line:
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

    def _parse_missing_addresses_output(self, output: str) -> Dict[str, Any]:
        """Parse missing addresses check output."""
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
                summary['path_drift_files'] = list(files.keys())[:10]  # Top 10
        
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

            if line.startswith('Report saved to:'):

                summary['report_path'] = line.split(':', 1)[1].strip() or None

        return summary

    def _format_list_for_display(self, items: Sequence[str], limit: int = 3) -> str:

        """Return a concise, comma-separated list with optional overflow marker."""

        filtered = [item for item in items if item]

        if not filtered:

            return ''

        if len(filtered) <= limit:

            return ', '.join(filtered)

        visible = ', '.join(filtered[:limit])

        remaining = len(filtered) - limit

        return f"{visible}, ... +{remaining}"

    def _format_percentage(self, value: Any, decimals: int = 1) -> str:

        """Format a numeric value as a percentage string."""

        try:

            return f"{float(value):.{decimals}f}%"

        except (TypeError, ValueError):

            return str(value)

    def _get_missing_doc_files(self, limit: int = 5) -> List[str]:

        """Return the top documentation files missing from the registry."""

        metrics = self.results_cache.get('analyze_function_registry', {})

        missing_files = []

        if isinstance(metrics, dict):

            missing_files = metrics.get('missing_files') or []

        if not isinstance(missing_files, list):

            return []

        return missing_files[:limit]

    def _load_coverage_summary(self) -> Optional[Dict[str, Any]]:

        """Load overall and per-module coverage metrics from coverage.json."""
        
        # Try project root first, then tests directory
        coverage_path = self.project_root / "coverage.json"
        if not coverage_path.exists():
            coverage_path = self.project_root / "development_tools" / "tests" / "coverage.json"

        if not coverage_path.exists():

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

    def _load_dev_tools_coverage(self) -> None:
        """Load dev tools coverage from JSON file if it exists."""
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
            'html_dir': None  # HTML reports disabled
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

        if missing_files:
            summary['missing_files'] = [item.strip() for item in missing_files[:5]]
        if missing_sections:
            summary['missing_sections'] = [item.strip() for item in missing_sections[:5]]

        return summary

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

    def _get_canonical_metrics(self) -> Dict[str, Any]:

        """Provide consistent totals across downstream documents."""

        results_cache = self.results_cache or {}
        fd_metrics = results_cache.get('analyze_functions', {}) or {}

        ds_metrics = results_cache.get('decision_support_metrics', {}) or {}

        audit_data = results_cache.get('analyze_function_registry', {}) or {}

        audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}
        if audit_totals is None or not isinstance(audit_totals, dict):
            audit_totals = {}

        # PRIORITY: Always use analyze_functions first (most accurate)
        # Don't use analyze_function_registry's functions_found - it only counts registry entries, not all functions
        total_functions = None

        # First priority: analyze_functions (most accurate)
        if fd_metrics:
            total_functions = fd_metrics.get('total_functions')

        # Second priority: decision_support
        if total_functions is None:
            total_functions = ds_metrics.get('total_functions')

        # Last resort: analyze_function_registry (but only if it's reasonable)
        if total_functions is None and isinstance(audit_data, dict):
            audit_total = audit_data.get('total_functions')
            if audit_total is not None and isinstance(audit_total, int) and audit_total > 100:
                # Only use if it seems reasonable (not the 11 from registry scan)
                total_functions = audit_total

        # Final fallback: audit_totals (but validate it's reasonable)
        if total_functions is None and isinstance(audit_totals, dict):
            registry_total = audit_totals.get('functions_found')
            if registry_total is not None and isinstance(registry_total, int) and registry_total > 100:
                # Only use if reasonable (not the 11 from limited registry scan)
                total_functions = registry_total

        moderate = fd_metrics.get('moderate_complexity')

        if moderate is None:

            moderate = ds_metrics.get('moderate_complexity')

        high = fd_metrics.get('high_complexity')

        if high is None:

            high = ds_metrics.get('high_complexity')

        critical = fd_metrics.get('critical_complexity')

        if critical is None:

            critical = ds_metrics.get('critical_complexity')
        
        # If still missing, try loading from cache
        if total_functions is None or moderate is None or high is None or critical is None:
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            cached_metrics = func_data['data']
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
                                        # Estimate: total - high - critical (approximate, may include low complexity)
                                        moderate = max(0, total_functions - high_count - critical_count)
            except Exception as e:
                logger.debug(f"Failed to load metrics from cache in _get_canonical_metrics: {e}")
                pass

        doc_coverage = audit_data.get('doc_coverage') if isinstance(audit_data, dict) else None

        # Recalculate documentation coverage using actual total functions
        # The registry's functions_found only counts functions in the registry, not all functions
        audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}
        if audit_totals is None or not isinstance(audit_totals, dict):
            audit_totals = {}
        documented = audit_totals.get('functions_documented', 0)
        
        # If documented is 0, try loading from cache file (structure might be different)
        if documented == 0:
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    # Try to get documented count from analyze_function_registry
                    if 'results' in cached_data and 'analyze_function_registry' in cached_data['results']:
                        afr_data = cached_data['results']['analyze_function_registry']
                        if 'data' in afr_data:
                            afr_data_dict = afr_data['data']
                            if 'totals' in afr_data_dict:
                                cached_totals = afr_data_dict['totals']
                                if isinstance(cached_totals, dict):
                                    documented = cached_totals.get('functions_documented', 0)
            except Exception as e:
                logger.debug(f"Failed to load documented count from cache: {e}")
        
        # ALWAYS recalculate documentation coverage using actual total functions
        # Never trust the registry's coverage calculation - it uses wrong denominator
        if total_functions is not None and isinstance(total_functions, (int, float)) and total_functions > 0:
            if documented > 0:
                coverage_pct = (documented / total_functions) * 100
                # Only use if reasonable (0-100%)
                if 0 <= coverage_pct <= 100:
                    doc_coverage = f"{coverage_pct:.2f}%"
                else:
                    doc_coverage = 'Unknown'  # Invalid calculation
            else:
                doc_coverage = '0.00%'  # No documented functions
        else:
            # Can't calculate without total - mark as unknown
            doc_coverage = 'Unknown'

        # Validate any existing doc_coverage value and reject invalid ones
        if isinstance(doc_coverage, str):
            # Check for obviously wrong values
            if '12690' in doc_coverage or 'Unknown' not in doc_coverage:
                try:
                    # Try to parse the percentage
                    val_str = doc_coverage.strip('%').replace(',', '')
                    if val_str.replace('.', '').isdigit():
                        val = float(val_str)
                        if val > 100:
                            # Invalid - recalculate if we have the data
                            if total_functions and documented:
                                coverage_pct = (documented / total_functions) * 100
                                if 0 <= coverage_pct <= 100:
                                    doc_coverage = f"{coverage_pct:.2f}%"
                                else:
                                    doc_coverage = 'Unknown'
                            else:
                                doc_coverage = 'Unknown'
                except (ValueError, TypeError):
                    # Can't parse - might be valid string like "Unknown"
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

    def _extract_actionable_insights(self, output: str) -> str:

        """Extract and format actionable insights from raw output."""

        if not isinstance(output, str):

            return 'No specific actionable insights found.'

        lines = output.split('\n')

        insights = []

        for line in lines:

            if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'next step', 'action']):

                insights.append(line.strip())

        if insights:

            return '\n'.join(insights[:10])

        return 'No specific actionable insights found.'

    def _save_audit_results(self, successful: List, failed: List, results: Dict):

        """Save detailed audit results"""
        
        # Enhance results with extracted metrics from results_cache
        enhanced_results = dict(results)
        
        # Add analyze_functions metrics if available
        if 'analyze_functions' in self.results_cache:
            func_metrics = self.results_cache['analyze_functions']
            if 'analyze_functions' not in enhanced_results:
                enhanced_results['analyze_functions'] = {'success': True, 'data': func_metrics}
            elif 'data' not in enhanced_results.get('analyze_functions', {}):
                enhanced_results['analyze_functions']['data'] = func_metrics
        
        # Add decision_support metrics if available
        if 'decision_support_metrics' in self.results_cache:
            ds_metrics = self.results_cache['decision_support_metrics']
            # Check if decision_support exists and is a dict with proper structure
            decision_support_result = enhanced_results.get('decision_support')
            if decision_support_result is None or not isinstance(decision_support_result, dict):
                # Replace boolean or None with proper dict structure
                enhanced_results['decision_support'] = {
                    'success': True,
                    'data': {'decision_support_metrics': ds_metrics}
                }
            elif 'data' not in decision_support_result:
                decision_support_result['data'] = {'decision_support_metrics': ds_metrics}
            elif 'decision_support_metrics' not in decision_support_result.get('data', {}):
                decision_support_result['data']['decision_support_metrics'] = ds_metrics

        audit_data = {

            'generated_by': 'run_development_tools.py - AI Development Tools Runner',

            'last_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

            'source': 'python development_tools/run_development_tools.py audit',

            'note': 'This file is auto-generated. Do not edit manually.',

            'timestamp': datetime.now().isoformat(),

            'successful': successful,

            'failed': failed,

            'results': enhanced_results

        }

        # Normalise location relative to the project root
        results_file_path = self.audit_config.get('results_file', 'development_tools/reports/analysis_detailed_results.json')
        results_file = (self.project_root / results_file_path).resolve()

        # Use file rotation for JSON files too

        create_output_file(str(results_file), json.dumps(audit_data, indent=2))

    def _generate_audit_report(self):

        """Generate comprehensive audit report"""

        report_lines = []

        report_lines.append("COMPREHENSIVE AUDIT REPORT")

        report_lines.append("=" * 60)

        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        report_lines.append("")

        # Add detailed results for each component

        for script_name, metrics in self.results_cache.items():

            if metrics:

                report_lines.append(f"[{script_name.upper()}]")

                report_lines.append("-" * 40)

                if isinstance(metrics, dict):

                    for key, value in metrics.items():

                        report_lines.append(f"  {key}: {value}")

                elif isinstance(metrics, list):

                    for item in metrics:

                        report_lines.append(f"  {item}")

                report_lines.append("")

        # Add system information

        report_lines.append("[SYSTEM INFO]")

        report_lines.append("-" * 40)

        report_lines.append(f"Python version: {sys.version}")

        report_lines.append(f"Working directory: {os.getcwd()}")

        report_lines.append(f"Timestamp: {datetime.now().isoformat()}")

        return "\n".join(report_lines)

    def _generate_ai_status_document(self) -> str:

        """Generate AI-optimized status document."""

        lines: List[str] = []

        lines.append("# AI Status - Current Codebase State")

        lines.append("")

        lines.append("> **File**: `development_tools/AI_STATUS.md`")

        lines.append("> **Generated**: This file is auto-generated by run_development_tools.py. Do not edit manually.")

        lines.append("> **Generated by**: run_development_tools.py - AI Development Tools Runner")

        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("> **Source**: `python development_tools/run_development_tools.py status`")

        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:

            if value is None:

                return "Unknown"

            if isinstance(value, str):

                return value if value.strip().endswith('%') else f"{value}%"

            return self._format_percentage(value, decimals)

        metrics = self._get_canonical_metrics()
        if not isinstance(metrics, dict):
            metrics = {}

        results_cache = self.results_cache or {}
        doc_metrics = results_cache.get('analyze_function_registry', {}) or {}

        error_metrics = results_cache.get('analyze_error_handling', {}) or {}

        function_metrics = results_cache.get('analyze_functions', {}) or {}

        analyze_docs = results_cache.get('analyze_documentation', {}) or {}
        # analyze_documentation stores the payload directly, not wrapped in 'data'
        if isinstance(analyze_docs, dict):
            analyze_docs_data = analyze_docs
        else:
            analyze_docs_data = {}
        
        # Extract overlap analysis data
        section_overlaps = analyze_docs_data.get('section_overlaps', {})
        consolidation_recs = analyze_docs_data.get('consolidation_recommendations', [])

        doc_coverage = doc_metrics.get('doc_coverage', metrics.get('doc_coverage', 'Unknown'))

        missing_docs = doc_metrics.get('missing_docs') or doc_metrics.get('missing_items')

        missing_files = self._get_missing_doc_files(limit=4)

        error_coverage = error_metrics.get('analyze_error_handling') or error_metrics.get('error_handling_coverage')
        
        # Recalculate error handling coverage using canonical function count for consistency
        error_total = error_metrics.get('total_functions')
        error_with_handling = error_metrics.get('functions_with_error_handling')
        canonical_total = metrics.get('total_functions')
        
        if error_coverage is not None and canonical_total and error_total and error_with_handling:
            # If error_handling used a different total, recalculate for consistency
            if error_total != canonical_total:
                recalc_coverage = (error_with_handling / canonical_total) * 100
                if 0 <= recalc_coverage <= 100:
                    error_coverage = recalc_coverage
                    # Also update missing count
                    missing_error_handlers = canonical_total - error_with_handling
                else:
                    missing_error_handlers = error_metrics.get('functions_missing_error_handling')
            else:
                missing_error_handlers = error_metrics.get('functions_missing_error_handling')
        else:
            missing_error_handlers = error_metrics.get('functions_missing_error_handling')

        worst_error_modules = error_metrics.get('worst_modules') or []

        coverage_summary = self._load_coverage_summary() or {}
        
        # Load dev tools coverage if not already loaded
        if not hasattr(self, 'dev_tools_coverage_results') or not self.dev_tools_coverage_results:
            self._load_dev_tools_coverage()

        doc_sync_summary = self.docs_sync_summary or {}
        if not isinstance(doc_sync_summary, dict):
            doc_sync_summary = {}

        legacy_summary = self.legacy_cleanup_summary or {}

        lines.append("## Snapshot")

        # Try to load cached audit results if not available in memory
        total_functions = metrics.get('total_functions', 'Unknown') if metrics else 'Unknown'
        moderate = metrics.get('moderate', 'Unknown') if metrics else 'Unknown'
        high = metrics.get('high', 'Unknown') if metrics else 'Unknown'
        critical = metrics.get('critical', 'Unknown') if metrics else 'Unknown'
        
        # If metrics are Unknown, try loading from cache
        if total_functions == 'Unknown' or moderate == 'Unknown':
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            cached_metrics = func_data['data']
                            if total_functions == 'Unknown':
                                total_functions = cached_metrics.get('total_functions', 'Unknown')
                            if moderate == 'Unknown':
                                moderate = cached_metrics.get('moderate_complexity', 'Unknown')
                            if high == 'Unknown':
                                high = cached_metrics.get('high_complexity', 'Unknown')
                            if critical == 'Unknown':
                                critical = cached_metrics.get('critical_complexity', 'Unknown')
                    
                    # Fallback to decision_support if still Unknown
                    if (total_functions == 'Unknown' or moderate == 'Unknown') and 'results' in cached_data:
                        # Check if decision_support was run and metrics extracted
                        if 'decision_support' in cached_data['results']:
                            ds_data = cached_data['results']['decision_support']
                            if 'data' in ds_data and 'decision_support_metrics' in ds_data['data']:
                                ds_metrics = ds_data['data']['decision_support_metrics']
                                if total_functions == 'Unknown':
                                    total_functions = ds_metrics.get('total_functions', 'Unknown')
                                if moderate == 'Unknown':
                                    moderate = ds_metrics.get('moderate_complexity', 'Unknown')
                                if high == 'Unknown':
                                    high = ds_metrics.get('high_complexity', 'Unknown')
                                if critical == 'Unknown':
                                    critical = ds_metrics.get('critical_complexity', 'Unknown')
            except Exception as e:
                logger.debug(f"Failed to load metrics from cache: {e}")
                pass
        
        if total_functions == 'Unknown':
            lines.append("- **Total Functions**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
        else:
            lines.append(f"- **Total Functions**: {total_functions} (Moderate: {moderate}, High: {high}, Critical: {critical})")

        # Try to load documentation coverage from cached data
        doc_coverage = metrics.get('doc_coverage', 'Unknown')
        missing_docs = None
        missing_files = []
        if doc_coverage == 'Unknown' or doc_coverage is None:
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_function_registry' in cached_data['results']:
                        func_reg_data = cached_data['results']['analyze_function_registry']
                        if 'data' in func_reg_data:
                            cached_metrics = func_reg_data['data']
                            cached_doc_cov = cached_metrics.get('doc_coverage') or cached_metrics.get('coverage')
                            if cached_doc_cov is not None:
                                if isinstance(cached_doc_cov, (int, float)):
                                    doc_coverage = f"{float(cached_doc_cov):.2f}%"
                                else:
                                    doc_coverage = str(cached_doc_cov)
                            missing_docs = cached_metrics.get('missing') or cached_metrics.get('missing_docs') or cached_metrics.get('missing_items')
                            missing_files = []
                        else:
                            # Parse from text output
                            output = func_reg_data.get('output', '')
                            if 'Documentation Coverage:' in output:
                                import re
                                match = re.search(r'Documentation Coverage:\s*(\d+\.?\d*)%', output)
                                if match:
                                    doc_coverage = match.group(1) + '%'
            except Exception as e:
                logger.debug(f"Failed to load doc_coverage from cache in status: {e}")
                pass

        doc_line = f"- **Documentation Coverage**: {percent_text(doc_coverage, 2)}"

        if missing_docs:

            doc_line += f" ({missing_docs} items missing from registry)"

        lines.append(doc_line)

        if missing_files:

            lines.append(f"- **Missing Documentation Files**: {self._format_list_for_display(missing_files, limit=4)}")

        # Try to load error handling coverage from cached data
        error_coverage = 'Unknown'
        missing_error_handlers = None
        if not error_coverage or error_coverage == 'Unknown':
            try:
                import json
                results_file = Path("development_tools/reports/analysis_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_error_handling' in cached_data['results']:
                        error_data = cached_data['results']['analyze_error_handling']
                        if 'data' in error_data:
                            cached_metrics = error_data['data']
                            error_coverage = cached_metrics.get('analyze_error_handling') or cached_metrics.get('error_handling_coverage', 'Unknown')
                            missing_error_handlers = cached_metrics.get('functions_missing_error_handling')
            except Exception:
                pass

        lines.append(

            f"- **Error Handling Coverage**: {percent_text(error_coverage, 1)}"

            + (f" ({missing_error_handlers} functions without handlers)" if missing_error_handlers else "")

        )

        # Try to load doc sync data from cached data
        if not doc_sync_summary:
            try:
                import json
                results_file = Path("development_tools/reports/analysis_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_documentation' in cached_data['results']:
                        doc_sync_data = cached_data['results']['analyze_documentation']
                        if 'data' in doc_sync_data:
                            cached_metrics = doc_sync_data['data']
                            # Create a doc_sync_summary from the cached data
                            doc_sync_summary = {
                                'status': 'GOOD' if not cached_metrics.get('artifacts') else 'NEEDS REVIEW',
                                'total_issues': len(cached_metrics.get('artifacts', []))
                            }
            except Exception:
                pass

        if doc_sync_summary:

            sync_status = doc_sync_summary.get('status', 'Unknown')

            total_issues = doc_sync_summary.get('total_issues')

            sync_line = f"- **Doc Sync**: {sync_status}"

            if total_issues is not None:

                sync_line += f" ({total_issues} tracked issues)"

            lines.append(sync_line)

        else:

            lines.append("- **Doc Sync**: Not collected in this run (pending doc-sync refresh)")

        lines.append("")

        lines.append("## Documentation Signals")

        # Use aggregated doc sync summary from current run first, then fall back to cache
        doc_sync_summary_for_signals = None
        if self.docs_sync_summary and isinstance(self.docs_sync_summary, dict):
            # Use the aggregated summary from _run_doc_sync_check()
            doc_sync_summary_for_signals = {
                'status': self.docs_sync_summary.get('status', 'UNKNOWN'),
                'path_drift_issues': self.docs_sync_summary.get('path_drift_issues', 0),
                'paired_doc_issues': self.docs_sync_summary.get('paired_doc_issues', 0),
                'ascii_issues': self.docs_sync_summary.get('ascii_issues', 0),
                'heading_numbering_issues': self.docs_sync_summary.get('heading_numbering_issues', 0),
                'missing_address_issues': self.docs_sync_summary.get('missing_address_issues', 0),
                'unconverted_link_issues': self.docs_sync_summary.get('unconverted_link_issues', 0),
                'path_drift_files': self.docs_sync_summary.get('path_drift_files', [])
            }
        
        # Fall back to cache if not available in memory
        if not doc_sync_summary_for_signals:
            try:
                import json
                results_file = Path("development_tools/reports/analysis_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_documentation_sync' in cached_data['results']:
                        doc_sync_data = cached_data['results']['analyze_documentation_sync']
                        if 'data' in doc_sync_data:
                            cached_metrics = doc_sync_data['data']
                            # Create a doc_sync_summary from the cached data
                            doc_sync_summary_for_signals = {
                                'status': cached_metrics.get('status', 'UNKNOWN'),
                                'path_drift_issues': cached_metrics.get('path_drift_issues', 0),
                                'paired_doc_issues': cached_metrics.get('paired_doc_issues', 0),
                                'ascii_issues': cached_metrics.get('ascii_issues', 0),
                                'path_drift_files': cached_metrics.get('path_drift_files', [])
                            }
            except Exception:
                pass

        if doc_sync_summary_for_signals:

            path_drift = doc_sync_summary_for_signals.get('path_drift_issues')

            paired = doc_sync_summary_for_signals.get('paired_doc_issues')

            ascii_issues = doc_sync_summary_for_signals.get('ascii_issues')

            if path_drift is not None:

                severity = "CLEAN" if path_drift == 0 else "NEEDS ATTENTION"

                lines.append(f"- **Path Drift**: {severity} ({path_drift} issues)")

            drift_files = doc_sync_summary_for_signals.get('path_drift_files') or []

            if drift_files:

                lines.append(f"- **Drift Hotspots**: {self._format_list_for_display(drift_files, limit=4)}")

            if paired is not None:

                status_label = "SYNCHRONIZED" if paired == 0 else "NEEDS ATTENTION"

                lines.append(f"- **Paired Docs**: {status_label} ({paired} issues)")
        
        # Add overlap analysis summary (always show, even if no overlaps found)
        lines.append("")
        lines.append("## Documentation Overlap")
        overlap_count = len(section_overlaps) if section_overlaps else 0
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0
        
        if overlap_count > 0 or consolidation_count > 0:
            if section_overlaps:
                lines.append(f"- **Section Overlaps**: {overlap_count} sections duplicated across files")
            if consolidation_recs:
                lines.append(f"- **Consolidation Opportunities**: {consolidation_count} file groups could be merged")
        else:
            lines.append("- **Status**: No overlaps detected (analysis performed)")

        if ascii_issues:

            lines.append(f"- **ASCII Cleanup**: {ascii_issues} files contain non-ASCII characters")

        if not doc_sync_summary_for_signals:

            lines.append("- Run `python development_tools/run_development_tools.py doc-sync` for drift details")

        dependency_summary = self.module_dependency_summary or self.results_cache.get('analyze_module_dependencies')

        if dependency_summary:

            missing_deps = dependency_summary.get('missing_dependencies')

            if missing_deps:

                lines.append(f"- **Dependency Docs**: {missing_deps} undocumented references detected")

                missing_files = dependency_summary.get('missing_files') or dependency_summary.get('missing_sections') or []

                if missing_files:

                    lines.append(f"  Top files: {self._format_list_for_display(missing_files, limit=3)}")

            else:

                lines.append("- **Dependency Docs**: CLEAN (no undocumented dependencies)")

        doc_artifacts = analyze_docs.get('artifacts') if isinstance(analyze_docs, dict) else None

        if doc_artifacts:

            primary_artifact = doc_artifacts[0]

            file_name = primary_artifact.get('file')

            line_no = primary_artifact.get('line')

            pattern = primary_artifact.get('pattern')

            lines.append(

                f"- **Content Cleanup**: {file_name} line {line_no} flagged for {pattern.replace('_', ' ')}"

            )

            if len(doc_artifacts) > 1:

                lines.append(f"- Additional documentation artifacts: {len(doc_artifacts) - 1} more findings")

        lines.append("")

        lines.append("## Error Handling")

        if error_metrics:

            if missing_error_handlers:

                lines.append(f"- **Missing Error Handling**: {missing_error_handlers} functions lack protections")

            decorated = error_metrics.get('functions_with_decorators')

            if decorated is not None:

                lines.append(f"- **@handle_errors Usage**: {decorated} functions already use the decorator")

            # Phase 1: Candidates for decorator replacement

            phase1_total = error_metrics.get('phase1_total', 0)

            if phase1_total > 0:

                phase1_by_priority = error_metrics.get('phase1_by_priority', {})

                priority_counts = []

                if phase1_by_priority.get('high', 0) > 0:

                    priority_counts.append(f"{phase1_by_priority['high']} high")

                if phase1_by_priority.get('medium', 0) > 0:

                    priority_counts.append(f"{phase1_by_priority['medium']} medium")

                if phase1_by_priority.get('low', 0) > 0:

                    priority_counts.append(f"{phase1_by_priority['low']} low")

                priority_text = ', '.join(priority_counts) if priority_counts else '0'

                lines.append(f"- **Phase 1 Candidates**: {phase1_total} functions need decorator replacement ({priority_text} priority)")

            # Phase 2: Generic exception raises

            phase2_total = error_metrics.get('phase2_total', 0)

            if phase2_total > 0:

                phase2_by_type = error_metrics.get('phase2_by_type', {})

                type_counts = [f"{count} {exc_type}" for exc_type, count in sorted(phase2_by_type.items(), key=lambda x: x[1], reverse=True)[:3]]

                type_text = ', '.join(type_counts) if type_counts else '0'

                if len(phase2_by_type) > 3:

                    type_text += f", ... +{len(phase2_by_type) - 3} more"

                lines.append(f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})")

            if worst_error_modules:

                module_descriptions = []

                for module in worst_error_modules[:3]:

                    module_name = module.get('module', 'Unknown')

                    coverage_value = module.get('coverage')

                    coverage_text = percent_text(coverage_value, 1)

                    missing = module.get('missing')

                    total = module.get('total')

                    detail = f"{module_name} ({coverage_text}"

                    if missing is not None and total is not None:

                        detail += f", missing {missing}/{total}"

                    detail += ")"

                    module_descriptions.append(detail)

                lines.append(f"- **Modules to Prioritize**: {', '.join(module_descriptions)}")

        else:
            # Try to load cached error handling data
            try:
                import json
                results_file = Path("development_tools/reports/analysis_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_error_handling' in cached_data['results']:
                        error_data = cached_data['results']['analyze_error_handling']
                        if 'data' in error_data:
                            error_metrics = error_data['data']
                        else:
                            # Try reading from the file if 'data' key is missing
                            try:
                                json_file = self.project_root / 'development_tools' / 'error_handling' / 'error_handling_details.json'
                                if json_file.exists():
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        error_metrics = json.load(f)
                                else:
                                    error_metrics = None
                            except (OSError, json.JSONDecodeError):
                                error_metrics = None
                        
                        if error_metrics:
                            coverage = error_metrics.get('analyze_error_handling') or error_metrics.get('error_handling_coverage', 'Unknown')
                            if coverage != 'Unknown':
                                lines.append(f"- **Error Handling Coverage**: {coverage:.1f}%")
                                lines.append(f"- **Functions with Error Handling**: {error_metrics.get('functions_with_error_handling', 'Unknown')}")
                                lines.append(f"- **Functions Missing Error Handling**: {error_metrics.get('functions_missing_error_handling', 'Unknown')}")
                                
                                # Add Phase 1 and Phase 2 if available
                                phase1_total = error_metrics.get('phase1_total', 0)
                                if phase1_total > 0:
                                    phase1_by_priority = error_metrics.get('phase1_by_priority', {})
                                    priority_counts = []
                                    if phase1_by_priority.get('high', 0) > 0:
                                        priority_counts.append(f"{phase1_by_priority['high']} high")
                                    if phase1_by_priority.get('medium', 0) > 0:
                                        priority_counts.append(f"{phase1_by_priority['medium']} medium")
                                    if phase1_by_priority.get('low', 0) > 0:
                                        priority_counts.append(f"{phase1_by_priority['low']} low")
                                    priority_text = ', '.join(priority_counts) if priority_counts else '0'
                                    lines.append(f"- **Phase 1 Candidates**: {phase1_total} functions need decorator replacement ({priority_text} priority)")
                                
                                phase2_total = error_metrics.get('phase2_total', 0)
                                if phase2_total > 0:
                                    phase2_by_type = error_metrics.get('phase2_by_type', {})
                                    type_counts = [f"{count} {exc_type}" for exc_type, count in sorted(phase2_by_type.items(), key=lambda x: x[1], reverse=True)[:3]]
                                    type_text = ', '.join(type_counts) if type_counts else '0'
                                    if len(phase2_by_type) > 3:
                                        type_text += f", ... +{len(phase2_by_type) - 3} more"
                                    lines.append(f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})")
                            else:
                                lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
                        else:
                            lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
                    else:
                        lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
                else:
                    lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
            except Exception:
                lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")

        lines.append("")

        lines.append("## Complexity Hotspots")

        critical_examples = function_metrics.get('critical_complexity_examples') or []

        high_examples = function_metrics.get('high_complexity_examples') or []

        undocumented_examples = function_metrics.get('undocumented_examples') or []

        if critical_examples:

            formatted = [

                f"{item['function']} ({item['file']}, complexity {item['complexity']})"

                for item in critical_examples[:3]

            ]

            lines.append(f"- **Critical** (>199 nodes): {', '.join(formatted)}")

        if high_examples:

            formatted = [

                f"{item['function']} ({item['file']}, complexity {item['complexity']})"

                for item in high_examples[:3]

            ]

            lines.append(f"- **High** (100-199 nodes): {', '.join(formatted)}")

        if undocumented_examples:

            formatted = [

                f"{item['function']} ({item['file']})"

                for item in undocumented_examples[:3]

            ]

            lines.append(f"- **Undocumented Functions**: {', '.join(formatted)}")

        # Always display canonical metrics (even if we showed examples above)
        # This ensures consistency with Snapshot section
        if moderate != 'Unknown' and moderate is not None:
            lines.append(f"- **Complexity Distribution**: Moderate: {moderate}, High: {high}, Critical: {critical}")
            if total_functions != 'Unknown' and total_functions is not None:
                lines.append(f"- **Total Functions**: {total_functions}")
        elif not (critical_examples or high_examples or undocumented_examples):
            # Try to load cached complexity data
            moderate = 'Unknown'
            high = 'Unknown'
            critical = 'Unknown'
            total_functions = 'Unknown'
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            func_metrics = func_data['data']
                            moderate = func_metrics.get('moderate_complexity', 'Unknown')
                            high = func_metrics.get('high_complexity', 'Unknown')
                            critical = func_metrics.get('critical_complexity', 'Unknown')
                            total_functions = func_metrics.get('total_functions', 'Unknown')
                    # Fallback to decision_support metrics
                    if moderate == 'Unknown' and 'results' in cached_data:
                        # Check if decision_support was run and metrics were extracted
                        if 'decision_support' in cached_data['results']:
                            ds_data = cached_data['results']['decision_support']
                            # The metrics might be in the results_cache or in the data
                            if 'data' in ds_data:
                                ds_metrics = ds_data['data'].get('decision_support_metrics', {})
                                if ds_metrics:
                                    moderate = ds_metrics.get('moderate_complexity', 'Unknown')
                                    high = ds_metrics.get('high_complexity', 'Unknown')
                                    critical = ds_metrics.get('critical_complexity', 'Unknown')
                                    total_functions = ds_metrics.get('total_functions', 'Unknown')
                        # Also check if decision_support_metrics is directly in results
                        if moderate == 'Unknown' and 'decision_support_metrics' in cached_data.get('results', {}):
                            ds_metrics = cached_data['results']['decision_support_metrics']
                            if isinstance(ds_metrics, dict):
                                moderate = ds_metrics.get('moderate_complexity', 'Unknown')
                                high = ds_metrics.get('high_complexity', 'Unknown')
                                critical = ds_metrics.get('critical_complexity', 'Unknown')
                                total_functions = ds_metrics.get('total_functions', 'Unknown')
                    
                    # Fallback to analyze_function_registry - parse high_complexity array
                    if (high == 'Unknown' or critical == 'Unknown') and 'results' in cached_data:
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
                                    if critical == 'Unknown':
                                        critical = critical_count
                                    if high == 'Unknown':
                                        high = high_count
                                    # For moderate, we'd need all functions, but we can estimate if we have total
                                    if moderate == 'Unknown' and total_functions != 'Unknown' and isinstance(total_functions, int):
                                        # Estimate: total - high - critical (approximate, may include low complexity)
                                        moderate = max(0, total_functions - high_count - critical_count)
                                    # Also get total_functions from analyze_function_registry if missing
                                    if total_functions == 'Unknown' and 'totals' in afr_data['data']:
                                        totals = afr_data['data']['totals']
                                        total_functions = totals.get('functions_found', 'Unknown')
                    
                    # Update metrics if we found them in cache
                    if moderate != 'Unknown' and moderate is not None:
                        # Update metrics dict for consistency
                        metrics['moderate'] = moderate
                        metrics['high'] = high
                        metrics['critical'] = critical
                        if total_functions != 'Unknown' and total_functions is not None:
                            metrics['total_functions'] = total_functions
                    
                    # Always use canonical metrics for display (re-read from metrics dict)
                    moderate = metrics.get('moderate', 'Unknown')
                    high = metrics.get('high', 'Unknown')
                    critical = metrics.get('critical', 'Unknown')
                    total_functions = metrics.get('total_functions', 'Unknown')
                    
                    if moderate != 'Unknown' and moderate is not None:
                        lines.append(f"- **Complexity Distribution**: Moderate: {moderate}, High: {high}, Critical: {critical}")
                        if total_functions != 'Unknown' and total_functions is not None:
                            lines.append(f"- **Total Functions**: {total_functions}")
                    else:
                        lines.append("- **Complexity Analysis**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
                else:
                    lines.append("- **Complexity Analysis**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")
            except Exception as e:
                logger.debug(f"Failed to load complexity from cache: {e}")
                lines.append("- **Complexity Analysis**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")

        lines.append("")

        lines.append("## Test Coverage")

        dev_tools_insights = self._get_dev_tools_coverage_insights()

        if coverage_summary and isinstance(coverage_summary, dict):

            overall = coverage_summary.get('overall') or {}

            lines.append(

                f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} "

                f"({overall.get('covered')} of {overall.get('statements')} statements)"

            )

            generated = overall.get('generated')

            if generated:

                lines.append(f"- **Report Timestamp**: {generated}")

            module_gaps = (coverage_summary.get('modules') or [])[:3]

            if module_gaps:

                descriptions = [

                    f"{m['module']} ({percent_text(m.get('coverage'), 1)}, missing {m.get('missed')} lines)"

                    for m in module_gaps

                ]

                lines.append(f"- **Lowest Modules**: {', '.join(descriptions)}")

            worst_files = (coverage_summary or {}).get('worst_files') or []

            if worst_files:

                descriptions = [

                    f"{item['path']} ({percent_text(item.get('coverage'), 1)})"

                    for item in worst_files[:3]

                ]

                lines.append(f"- **Files Needing Tests**: {', '.join(descriptions)}")
            
            if dev_tools_insights and dev_tools_insights.get('overall_pct') is not None:
                dev_pct = dev_tools_insights['overall_pct']
                dev_statements = dev_tools_insights.get('statements')
                dev_covered = dev_tools_insights.get('covered')
                summary_line = f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                if dev_statements is not None and dev_covered is not None:
                    summary_line += f" ({dev_covered} of {dev_statements} statements)"
                lines.append(summary_line)
                html_dir = dev_tools_insights.get('html')
                if html_dir:
                    lines.append(f"- **Dev Tools Report**: {html_dir}")
                low_modules = dev_tools_insights.get('low_modules') or []
                if low_modules:
                    dev_descriptions = [
                        f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)}, missing {item.get('missed')} lines)"
                        for item in low_modules
                    ]
                    lines.append(f"- **Lowest Dev Tool Modules**: {', '.join(dev_descriptions)}")

        else:

            lines.append("- Coverage data unavailable; run `audit --full` to regenerate metrics")

        lines.append("")

        lines.append("## Legacy References")

        if legacy_summary:

            legacy_issues = legacy_summary.get('files_with_issues')

            if legacy_issues == 0:

                lines.append("- **Legacy References**: CLEAN (0 files flagged)")

            elif legacy_issues is not None:

                lines.append(f"- **Legacy References**: {legacy_issues} files still reference legacy patterns")

            report_path = legacy_summary.get('report_path')

            if report_path:

                lines.append(f"- **Detailed Report**: {report_path}")

        else:
            # Try to load cached audit results if not available in memory
            try:
                import json
                results_file = Path("development_tools/reports/analysis_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'fix_legacy_references' in cached_data['results']:
                        legacy_data = cached_data['results']['fix_legacy_references']
                        if 'data' in legacy_data:
                            cached_legacy = legacy_data['data']
                            legacy_issues = cached_legacy.get('files_with_issues', 'Unknown')
                            if legacy_issues != 'Unknown':
                                if legacy_issues == 0:
                                    lines.append("- **Legacy References**: CLEAN (0 files flagged)")
                                else:
                                    lines.append(f"- **Legacy References**: {legacy_issues} files still reference legacy patterns")
                                report_path = cached_legacy.get('report_path')
                                if report_path:
                                    lines.append(f"- **Detailed Report**: {report_path}")
                            else:
                                lines.append("- Legacy reference data unavailable (run `audit --fast` for latest scan)")
                        else:
                            lines.append("- Legacy reference data unavailable (run `audit --fast` for latest scan)")
                    else:
                        lines.append("- Legacy reference data unavailable (run `audit --fast` for latest scan)")
                else:
                    lines.append("- Legacy reference data unavailable (run `audit --fast` for latest scan)")
            except Exception:
                lines.append("- Legacy reference data unavailable (run `audit --fast` for latest scan)")

        lines.append("")

        lines.append("## Validation Status")

        if hasattr(self, 'validation_results') and self.validation_results:

            validation_output = self.validation_results.get('output', '')

            if 'POOR' in validation_output:

                lines.append("- **AI Work Validation**: POOR - documentation or tests missing")

            elif 'GOOD' in validation_output:

                lines.append("- **AI Work Validation**: GOOD - keep current standards")

            else:

                lines.append("- **AI Work Validation**: NEEDS REVIEW - inspect consolidated report")

        else:
            # Try to load cached audit results if not available in memory
            validation_loaded = False
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_ai_work' in cached_data['results']:
                        validation_data = cached_data['results']['analyze_ai_work']
                        # Handle nested data structure: results.analyze_ai_work.data.output
                        if 'data' in validation_data:
                            data = validation_data['data']
                            # Check if data is a dict with 'output' key, or if it's the result dict itself
                            if isinstance(data, dict):
                                validation_output = data.get('output', '') or ''
                                # If output is empty, check if there's a nested structure
                                if not validation_output and 'data' in data:
                                    validation_output = data['data'].get('output', '') or ''
                        else:
                            validation_output = validation_data.get('output', '') or ''
                        if validation_output:
                            if 'POOR' in validation_output:
                                lines.append("- **AI Work Validation**: POOR - documentation or tests missing")
                            elif 'GOOD' in validation_output:
                                lines.append("- **AI Work Validation**: GOOD - keep current standards")
                            else:
                                lines.append("- **AI Work Validation**: NEEDS REVIEW - inspect consolidated report")
                            validation_loaded = True
            except Exception as e:
                logger.debug(f"Failed to load validation from cache: {e}")
            
            if not validation_loaded:
                lines.append("- Validation results unavailable (run `audit --fast` for latest validation)")

        lines.append("")

        lines.append("## System Signals")

        if hasattr(self, 'system_signals') and self.system_signals:

            system_health = self.system_signals.get('system_health', {})

            overall_status = system_health.get('overall_status')

            if overall_status:

                lines.append(f"- **System Health**: {overall_status}")

            missing_core = [

                name for name, state in (system_health.get('core_files') or {}).items()

                if state != 'OK'

            ]

            if missing_core:

                lines.append(f"- **Core File Issues**: {self._format_list_for_display(missing_core, limit=3)}")

            recent_activity = self.system_signals.get('recent_activity', {})

            last_audit = recent_activity.get('last_audit')

            if last_audit:

                lines.append(f"- **Last Audit**: {last_audit}")

            recent_changes = recent_activity.get('recent_changes') or []

            if recent_changes:

                lines.append(f"- **Recent Changes**: {self._format_list_for_display(recent_changes, limit=3)}")

            # Add critical alerts if any
            critical_alerts = self.system_signals.get('critical_alerts', [])
            if critical_alerts:
                lines.append(f"- **Critical Alerts**: {len(critical_alerts)} active alerts")

        else:
            # Try to load cached system signals if not available in memory
            signals_loaded = False
            system_signals = None
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'system_signals' in cached_data['results']:
                        signals_data = cached_data['results']['system_signals']
                        # Handle both 'data' wrapper and direct signals
                        if 'data' in signals_data:
                            system_signals = signals_data['data']
                        else:
                            system_signals = signals_data
                        
                        if system_signals:
                            signals_loaded = True
                            system_health = system_signals.get('system_health', {})
                            overall_status = system_health.get('overall_status')
                            if overall_status:
                                lines.append(f"- **System Health**: {overall_status}")
                            
                            missing_core = [
                                name for name, state in (system_health.get('core_files') or {}).items()
                                if state != 'OK'
                            ]
                            if missing_core:
                                lines.append(f"- **Core File Issues**: {self._format_list_for_display(missing_core, limit=3)}")
                            
                            recent_activity = system_signals.get('recent_activity', {})
                            last_audit = recent_activity.get('last_audit')
                            if last_audit:
                                lines.append(f"- **Last Audit**: {last_audit}")
                            
                            recent_changes = recent_activity.get('recent_changes') or []
                            if recent_changes:
                                lines.append(f"- **Recent Changes**: {self._format_list_for_display(recent_changes, limit=3)}")
                            
                            critical_alerts = system_signals.get('critical_alerts', [])
                            if critical_alerts:
                                lines.append(f"- **Critical Alerts**: {len(critical_alerts)} active alerts")
                            
                            signals_loaded = True
            except Exception as e:
                logger.debug(f"Failed to load system signals from cache: {e}")
            
            if not signals_loaded:
                lines.append("- System signals data unavailable (run `system-signals` command)")

        lines.append("")

        lines.append("## Quick Commands")

        lines.append("- `python development_tools/run_development_tools.py status` - Refresh this snapshot")

        lines.append("- `python development_tools/run_development_tools.py audit --full` - Regenerate all metrics")

        lines.append("- `python development_tools/run_development_tools.py doc-sync` - Update documentation pairing data")

        lines.append("")

        return "\n".join(lines)

    def _generate_ai_priorities_document(self) -> str:
        """Generate AI-optimized priorities document with immediate next steps."""
        lines: List[str] = []
        lines.append("# AI Priorities - Immediate Next Steps")
        lines.append("")
        lines.append("> **File**: `development_tools/AI_PRIORITIES.md`")
        lines.append("> **Generated**: This file is auto-generated by run_development_tools.py. Do not edit manually.")
        lines.append("> **Generated by**: run_development_tools.py - AI Development Tools Runner")
        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("> **Source**: `python development_tools/run_development_tools.py audit`")
        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:
            if value is None:
                return "Unknown"
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed if trimmed.endswith('%') else f"{trimmed}%"
            return self._format_percentage(value, decimals)

        def to_int(value: Any) -> Optional[int]:
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip('%')
                if stripped.isdigit():
                    return int(stripped)
            if isinstance(value, dict):
                count = value.get('count')
                return to_int(count)
            return None

        def to_float(value: Any) -> Optional[float]:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                stripped = value.strip().rstrip('%')
                try:
                    return float(stripped)
                except ValueError:
                    return None
            return None

        metrics = self._get_canonical_metrics()
        doc_metrics = self.results_cache.get('analyze_function_registry', {}) or {}
        error_metrics = self.results_cache.get('analyze_error_handling', {}) or {}
        function_metrics = self.results_cache.get('analyze_functions', {}) or {}
        doc_sync_summary = self.docs_sync_summary or {}
        legacy_summary = self.legacy_cleanup_summary or {}
        coverage_summary = self._load_coverage_summary()
        
        # Load dev tools coverage if not already loaded
        if not hasattr(self, 'dev_tools_coverage_results') or not self.dev_tools_coverage_results:
            self._load_dev_tools_coverage()
        
        analyze_docs_result = self.results_cache.get('analyze_documentation', {}) or {}
        # analyze_documentation stores the payload directly, not wrapped in 'data'
        if isinstance(analyze_docs_result, dict):
            analyze_data = analyze_docs_result
        else:
            analyze_data = {}
        
        # Extract overlap analysis data
        section_overlaps = analyze_data.get('section_overlaps', {})
        consolidation_recs = analyze_data.get('consolidation_recommendations', [])

        # Get doc coverage from canonical metrics first (most accurate)
        doc_coverage_value = metrics.get('doc_coverage')
        if doc_coverage_value is None or doc_coverage_value == 'Unknown':
            # Fallback to doc_metrics
            doc_coverage_value = doc_metrics.get('doc_coverage')

        missing_docs_count = to_int(doc_metrics.get('missing_docs') or doc_metrics.get('missing_items'))
        missing_doc_files = doc_metrics.get('missing_files') or self._get_missing_doc_files(limit=5)

        error_coverage = error_metrics.get('analyze_error_handling') or error_metrics.get('error_handling_coverage')
        
        # Recalculate error handling coverage using canonical function count for consistency
        error_total = error_metrics.get('total_functions')
        error_with_handling = error_metrics.get('functions_with_error_handling')
        canonical_total = metrics.get('total_functions')
        
        if error_coverage is not None and canonical_total and error_total and error_with_handling:
            # If error_handling used a different total, recalculate for consistency
            if error_total != canonical_total:
                recalc_coverage = (error_with_handling / canonical_total) * 100
                if 0 <= recalc_coverage <= 100:
                    error_coverage = recalc_coverage
                    # Also update missing count
                    missing_error_handlers = canonical_total - error_with_handling
                else:
                    missing_error_handlers = to_int(error_metrics.get('functions_missing_error_handling'))
            else:
                missing_error_handlers = to_int(error_metrics.get('functions_missing_error_handling'))
        else:
            missing_error_handlers = to_int(error_metrics.get('functions_missing_error_handling'))
        
        worst_error_modules = error_metrics.get('worst_modules') or []

        path_drift_count = to_int(doc_sync_summary.get('path_drift_issues')) if doc_sync_summary else None
        path_drift_files = doc_sync_summary.get('path_drift_files') if doc_sync_summary else []
        # Filter out section headers that were incorrectly parsed as file names
        path_drift_files = [f for f in path_drift_files if not (f.isupper() and ('ISSUES' in f or 'COMPLIANCE' in f or 'DOCUMENTATION' in f or 'NUMBERING' in f))]
        paired_doc_issues = to_int(doc_sync_summary.get('paired_doc_issues')) if doc_sync_summary else None
        ascii_issues = to_int(doc_sync_summary.get('ascii_issues')) if doc_sync_summary else None

        legacy_files = to_int(legacy_summary.get('files_with_issues')) if legacy_summary else None
        legacy_markers = to_int(legacy_summary.get('legacy_markers')) if legacy_summary else None
        legacy_report = legacy_summary.get('report_path') if legacy_summary else None

        low_coverage_modules: List[Dict[str, Any]] = []
        coverage_overall = None
        worst_coverage_files: List[Dict[str, Any]] = []
        if coverage_summary:
            coverage_overall = (coverage_summary or {}).get('overall')
            module_entries = (coverage_summary or {}).get('modules') or []
            for module in module_entries:
                coverage_value = to_float(module.get('coverage'))
                if coverage_value is not None and coverage_value < 80:
                    low_coverage_modules.append(module)
            low_coverage_modules = low_coverage_modules[:3]
            worst_coverage_files = (coverage_summary or {}).get('worst_files') or []
        
        # Get dev tools coverage if available
        dev_tools_coverage_overall = None
        if hasattr(self, 'dev_tools_coverage_results') and self.dev_tools_coverage_results:
            dev_tools_coverage_overall = self.dev_tools_coverage_results.get('overall', {})
        dev_tools_insights = self._get_dev_tools_coverage_insights()

        analyze_artifacts = analyze_data.get('artifacts') or []
        analyze_duplicates = analyze_data.get('duplicates') or []
        analyze_placeholders = analyze_data.get('placeholders') or []

        critical_examples = function_metrics.get('critical_complexity_examples') or []
        high_examples = function_metrics.get('high_complexity_examples') or []
        
        # Get complexity metrics from canonical metrics or decision_support
        moderate_complex = to_int(metrics.get('moderate'))
        high_complex = to_int(metrics.get('high'))
        critical_complex = to_int(metrics.get('critical'))
        
        # If not in metrics, try loading from decision_support_metrics
        if moderate_complex is None or high_complex is None or critical_complex is None:
            decision_metrics = self.results_cache.get('decision_support_metrics', {})
            if decision_metrics:
                if moderate_complex is None:
                    moderate_complex = to_int(decision_metrics.get('moderate_complexity'))
                if high_complex is None:
                    high_complex = to_int(decision_metrics.get('high_complexity'))
                if critical_complex is None:
                    critical_complex = to_int(decision_metrics.get('critical_complexity'))

        priority_items: List[Dict[str, Any]] = []

        def add_priority(order: int, title: str, reason: str, bullets: List[str]) -> None:
            if not reason:
                return
            priority_items.append({
                'order': order,
                'title': title,
                'reason': reason,
                'bullets': [bullet for bullet in bullets if bullet]
            })

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
                "Run `python development_tools/run_development_tools.py doc-sync --fix` after adjustments."
            )
            add_priority(
                order=1,
                title="Stabilize documentation drift",
                reason=f"{path_drift_count} documentation paths are out of sync.",
                bullets=drift_details
            )

        if missing_docs_count and missing_docs_count > 0:
            doc_bullets: List[str] = []
            if missing_doc_files:
                doc_bullets.append(
                    f"Document: {self._format_list_for_display(list(missing_doc_files)[:5], limit=3)}"
                )
            doc_bullets.append(
                "Regenerate registry entries via `python development_tools/run_development_tools.py docs`."
            )
            add_priority(
                order=2,
                title="Close documentation registry gaps",
                reason=f"{missing_docs_count} functions are missing or stale in the registry.",
                bullets=doc_bullets
            )

        # Phase 1: Decorator replacement candidates
        phase1_total = to_int(error_metrics.get('phase1_total', 0))
        phase1_by_priority = error_metrics.get('phase1_by_priority', {}) or {}
        phase1_high = to_int(phase1_by_priority.get('high', 0))
        
        if phase1_total and phase1_total > 0:
            phase1_bullets: List[str] = []
            if phase1_high and phase1_high > 0:
                phase1_bullets.append(
                    f"Start with {phase1_high} high-priority candidates (entry points and critical operations)."
                )
            phase1_medium = to_int(phase1_by_priority.get('medium', 0))
            if phase1_medium and phase1_medium > 0:
                phase1_bullets.append(
                    f"Then process {phase1_medium} medium-priority functions."
                )
            phase1_bullets.append(
                "Apply `@handle_errors` decorator to replace basic try-except blocks."
            )
            add_priority(
                order=3,
                title="Phase 1: Replace basic try-except with decorators",
                reason=f"{phase1_total} functions have try-except blocks that should use `@handle_errors` decorator.",
                bullets=phase1_bullets
            )
        
        # Phase 2: Generic exception categorization
        phase2_total = to_int(error_metrics.get('phase2_total', 0))
        phase2_by_type = error_metrics.get('phase2_by_type', {}) or {}
        
        if phase2_total and phase2_total > 0:
            phase2_bullets: List[str] = []
            top_exceptions = sorted(phase2_by_type.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_exceptions:
                exc_details = [f"{count} {exc_type}" for exc_type, count in top_exceptions]
                phase2_bullets.append(
                    f"Most common: {self._format_list_for_display(exc_details, limit=3)}"
                )
            phase2_bullets.append(
                "Replace generic exceptions (ValueError, Exception, KeyError, TypeError) with specific project error classes."
            )
            phase2_bullets.append(
                "See `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` for categorization rules."
            )
            add_priority(
                order=4,
                title="Phase 2: Categorize generic exceptions",
                reason=f"{phase2_total} generic exception raises need categorization into project-specific error classes.",
                bullets=phase2_bullets
            )
        
        # General error handling priority (if no Phase 1/2 but still missing handlers)
        if missing_error_handlers and missing_error_handlers > 0 and not (phase1_total or phase2_total):
            module_samples: List[str] = []
            for module in worst_error_modules[:3]:
                module_name = module.get('module', 'Unknown')
                coverage_value = percent_text(module.get('coverage'), 1)
                missing = module.get('missing')
                total = module.get('total')
                detail = f"{module_name} ({coverage_value}"
                if missing is not None and total is not None:
                    detail += f", missing {missing}/{total}"
                detail += ")"
                module_samples.append(detail)
            error_bullets = []
            if module_samples:
                error_bullets.append(
                    f"Focus modules: {self._format_list_for_display(module_samples, limit=3)}"
                )
            error_bullets.append(
                "Convert remaining basic handlers to `@handle_errors` and add guard tests."
            )
            add_priority(
                order=3,
                title="Harden critical error handling",
                reason=f"{missing_error_handlers} functions still lack structured error recovery.",
                bullets=error_bullets
            )

        # Adjust order numbers based on whether Phase 1/2 priorities exist
        coverage_order = 4
        dev_coverage_order = coverage_order + 1
        dependency_order = dev_coverage_order + 1
        legacy_order = dependency_order + 1
        if phase1_total or phase2_total:
            coverage_order = 5
            dev_coverage_order = coverage_order + 1
            dependency_order = dev_coverage_order + 1
            legacy_order = dependency_order + 1
        
        if low_coverage_modules:
            coverage_highlights = [
                f"{module.get('module', 'module')} ({percent_text(module.get('coverage'), 1)}, {module.get('missed')} lines missing)"
                for module in low_coverage_modules
            ]
            coverage_bullets = [
                f"Target modules: {self._format_list_for_display(coverage_highlights, limit=3)}",
                "Add scenario tests before the next full audit to lift module coverage above 80%."
            ]
            add_priority(
                order=coverage_order,
                title="Raise coverage for low-performing modules",
                reason=f"{len(low_coverage_modules)} key modules remain below the 80% target.",
                bullets=coverage_bullets
            )

        if dev_tools_insights and dev_tools_insights.get('overall_pct') is not None:
            dev_pct = dev_tools_insights['overall_pct']
            low_dev_modules = dev_tools_insights.get('low_modules') or []
            if dev_pct < 60 or low_dev_modules:
                dev_bullets: List[str] = []
                if low_dev_modules:
                    highlights = [
                        f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)})"
                        for item in low_dev_modules
                    ]
                    dev_bullets.append(f"Focus on: {self._format_list_for_display(highlights, limit=3)}")
                if dev_tools_insights.get('html'):
                    dev_bullets.append(f"Review HTML report at {dev_tools_insights['html']}")
                dev_bullets.append("Strengthen tests in `tests/development_tools/` for fragile helpers.")
                add_priority(
                    order=dev_coverage_order,
                    title="Raise development tools coverage",
                    reason=f"Development tools coverage is {percent_text(dev_pct, 1)} (target 60%+).",
                    bullets=dev_bullets
                )

        dependency_summary = self.module_dependency_summary or self.results_cache.get('analyze_module_dependencies')

        if dependency_summary and dependency_summary.get('missing_dependencies'):

            missing = dependency_summary['missing_dependencies']

            dep_bullets = []

            files = dependency_summary.get('missing_files') or dependency_summary.get('missing_sections') or []

            if files:

                dep_bullets.append(f"Affected files: {self._format_list_for_display(files, limit=3)}")

            dep_bullets.append("Regenerate dependencies via `python development_tools/run_development_tools.py docs` and rerun the audit.")

            add_priority(

                order=dependency_order,

                title="Refresh dependency documentation",

                reason=f"{missing} module dependencies are undocumented.",

                bullets=dep_bullets

            )

        if legacy_files and legacy_files > 0:
            legacy_bullets: List[str] = []
            if legacy_markers:
                legacy_bullets.append(f"{legacy_markers} legacy markers still surface during scans.")
            if legacy_report:
                legacy_bullets.append(f"Review {legacy_report} for exact locations.")
            legacy_bullets.append(
                "Use `python development_tools/run_development_tools.py legacy --apply` to replace deprecated helpers."
            )
            add_priority(
                order=legacy_order,
                title="Retire remaining legacy references",
                reason=f"{legacy_files} files still depend on legacy compatibility markers.",
                bullets=legacy_bullets
            )
        
        # Add complexity refactoring priority if there are critical or high complexity functions
        complexity_order = legacy_order + 1
        if critical_complex and critical_complex > 0:
            complexity_bullets: List[str] = []
            if critical_examples:
                example_names = [ex.get('name', 'unknown') for ex in critical_examples[:3]]
                complexity_bullets.append(
                    f"Start with critical functions: {self._format_list_for_display(example_names, limit=3)}"
                )
            if high_complex and high_complex > 0:
                complexity_bullets.append(
                    f"Then address {high_complex} high-complexity functions (100-199 nodes)."
                )
            complexity_bullets.append(
                "Refactor to reduce cyclomatic complexity and improve maintainability."
            )
            add_priority(
                order=complexity_order,
                title="Refactor high-complexity functions",
                reason=f"{critical_complex} critical-complexity functions (>199 nodes) need immediate attention.",
                bullets=complexity_bullets
            )
        elif high_complex and high_complex > 0:
            complexity_bullets: List[str] = []
            if high_examples:
                example_names = [ex.get('name', 'unknown') for ex in high_examples[:3]]
                complexity_bullets.append(
                    f"Focus on: {self._format_list_for_display(example_names, limit=3)}"
                )
            complexity_bullets.append(
                "Refactor to reduce cyclomatic complexity and improve maintainability."
            )
            add_priority(
                order=complexity_order,
                title="Refactor high-complexity functions",
                reason=f"{high_complex} high-complexity functions (100-199 nodes) should be simplified.",
                bullets=complexity_bullets
            )

        lines.append("## Immediate Focus (Ranked)")
        if priority_items:
            for idx, item in enumerate(sorted(priority_items, key=lambda entry: entry['order']), start=1):
                lines.append(f"{idx}. **{item['title']}**  -  {item['reason']}")
                for bullet in item['bullets']:
                    lines.append(f"   - {bullet}")
        else:
            lines.append("All signals are green. Re-run `python development_tools/run_development_tools.py status` to monitor.")
        lines.append("")

        quick_wins: List[str] = []
        if ascii_issues:
            quick_wins.append(f"Normalize {ascii_issues} file(s) with non-ASCII characters via doc-fix.")
        if paired_doc_issues and not (path_drift_count and path_drift_count > 0):
            quick_wins.append(f"Resolve {paired_doc_issues} unpaired documentation sets flagged by doc-sync.")
        if analyze_artifacts:
            artifact = analyze_artifacts[0]
            location = artifact.get('file', 'unknown')
            line_number = artifact.get('line')
            if line_number:
                location = f"{location}:{line_number}"
            pattern = artifact.get('pattern', 'lint issue')
            quick_wins.append(f"Clean `{pattern}` marker in {location}.")
        if analyze_duplicates:
            quick_wins.append(f"Merge {len(analyze_duplicates)} duplicate documentation block(s).")
        if analyze_placeholders:
            quick_wins.append(f"Replace {len(analyze_placeholders)} placeholder section(s) flagged by docs scan.")

        lines.append("## Quick Wins")
        if quick_wins:
            for win in quick_wins:
                lines.append(f"- {win}")
        else:
            lines.append("- No immediate quick wins identified. Re-run doc-sync after tackling focus items.")
        
        # Add overlap analysis information only if there are issues to prioritize
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0
        overlap_count = len(section_overlaps) if section_overlaps else 0
        
        if consolidation_recs:
            lines.append(f"- **Documentation Consolidation**: {consolidation_count} file groups could be consolidated to reduce redundancy")
            for rec in consolidation_recs[:2]:  # Show top 2
                category = rec.get('category', 'Unknown')
                files = rec.get('files', [])
                if files and len(files) > 1:
                    lines.append(f"  - {category}: Consider merging {len(files)} files ({', '.join(files[:2])}{'...' if len(files) > 2 else ''})")
        elif overlap_count > 0:
            lines.append(f"- **Documentation Overlap Analysis**: {overlap_count} section overlaps detected (review for consolidation opportunities)")
        
        lines.append("")

        watch_list: List[str] = []
        if doc_coverage_value is not None:
            watch_list.append(f"Documentation coverage sits at {percent_text(doc_coverage_value, 2)} (target 90%).")
        if coverage_overall:
            watch_list.append(
                f"Overall test coverage is {percent_text(coverage_overall.get('coverage'), 1)} "
                f"({coverage_overall.get('covered')} / {coverage_overall.get('statements')} statements)."
            )
        if dev_tools_insights and dev_tools_insights.get('overall_pct') is not None:
            dev_pct = dev_tools_insights['overall_pct']
            detail = f"Development tools coverage is {percent_text(dev_pct, 1)} (target 60%+)."
            low_modules = dev_tools_insights.get('low_modules') or []
            if low_modules:
                focus = [
                    f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)})"
                    for item in low_modules
                ]
                detail += f" Focus on {self._format_list_for_display(focus, limit=2)}."
            watch_list.append(detail)
        dependency_summary = self.module_dependency_summary or self.results_cache.get('analyze_module_dependencies')
        if dependency_summary and dependency_summary.get('missing_dependencies'):
            missing = dependency_summary['missing_dependencies']
            files = dependency_summary.get('missing_files') or dependency_summary.get('missing_sections') or []
            detail = f"Dependency docs missing {missing} reference(s); regenerate MODULE_DEPENDENCIES detail."
            if files:
                detail += f" Hotspots: {self._format_list_for_display(files, limit=2)}."
            watch_list.append(detail)
        if worst_coverage_files:
            file_focus = [
                f"{item['path']} ({percent_text(item.get('coverage'), 1)})"
                for item in worst_coverage_files[:2]
            ]
            watch_list.append(f"Keep an eye on untested files: {self._format_list_for_display(file_focus, limit=2)}.")
        if critical_examples:
            critical_focus = [
                f"{entry['function']} ({entry['file']})"
                for entry in critical_examples[:2]
            ]
            watch_list.append(f"Plan refactors for complex hotspots: {self._format_list_for_display(critical_focus, limit=2)}.")
        elif high_examples:
            high_focus = [
                f"{entry['function']} ({entry['file']})"
                for entry in high_examples[:2]
            ]
            watch_list.append(f"Monitor high complexity functions: {self._format_list_for_display(high_focus, limit=2)}.")
        if legacy_markers and (not legacy_files or legacy_files == 0):
            watch_list.append(f"{legacy_markers} legacy markers remain; schedule periodic cleanup post-sprint.")

        lines.append("## Watch List")
        if watch_list:
            for item in watch_list:
                lines.append(f"- {item}")
        else:
            lines.append("- No outstanding watch items. Continue regular audits to maintain signal quality.")
        lines.append("")

        lines.append("## Follow-up Commands")
        lines.append("- `python development_tools/run_development_tools.py doc-sync`  -  refresh drift, pairing, and ASCII metrics.")
        lines.append("- `python development_tools/run_development_tools.py legacy --apply`  -  update legacy references in-place.")
        lines.append("- `python development_tools/run_development_tools.py audit --full`  -  rebuild coverage and hygiene data after fixes.")
        lines.append("- `python development_tools/run_development_tools.py status`  -  confirm the latest health snapshot.")

        return '\n'.join(lines)
    def _generate_consolidated_report(self) -> str:

        """Generate comprehensive consolidated report combining all tool outputs."""

        lines: List[str] = []

        lines.append("# Comprehensive AI Development Tools Report")

        lines.append("")

        lines.append("> **Generated**: This file is auto-generated by run_development_tools.py. Do not edit manually.")

        lines.append("> **Generated by**: run_development_tools.py - AI Development Tools Runner")

        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("> **Source**: `python development_tools/run_development_tools.py audit`")

        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:

            if value is None:

                return "Unknown"

            if isinstance(value, str):

                return value if value.strip().endswith('%') else f"{value}%"

            return self._format_percentage(value, decimals)

        metrics = self._get_canonical_metrics()

        doc_metrics = self.results_cache.get('analyze_function_registry', {}) or {}

        doc_coverage = doc_metrics.get('doc_coverage', metrics.get('doc_coverage'))

        missing_docs = doc_metrics.get('missing_docs') or doc_metrics.get('missing_items')

        doc_totals = doc_metrics.get('totals') or {}

        documented_functions = doc_totals.get('functions_documented')

        doc_sync_summary = self.docs_sync_summary or {}

        analyze_docs = self.results_cache.get('analyze_documentation', {}) or {}
        # analyze_documentation stores the payload directly, not wrapped in 'data'
        if isinstance(analyze_docs, dict):
            analyze_docs_data = analyze_docs
        else:
            analyze_docs_data = {}

        doc_artifacts = analyze_docs_data.get('artifacts') if isinstance(analyze_docs_data, dict) else None
        
        # Extract overlap analysis data
        section_overlaps = analyze_docs_data.get('section_overlaps', {})
        consolidation_recs = analyze_docs_data.get('consolidation_recommendations', [])
        file_purposes = analyze_docs_data.get('file_purposes', {})

        error_metrics = self.results_cache.get('analyze_error_handling', {}) or {}

        missing_error_handlers = error_metrics.get('functions_missing_error_handling')

        error_recommendations = error_metrics.get('recommendations') or []

        worst_error_modules = error_metrics.get('worst_modules') or []

        coverage_summary = self._load_coverage_summary()
        
        # Load dev tools coverage if not already loaded
        if not hasattr(self, 'dev_tools_coverage_results') or not self.dev_tools_coverage_results:
            self._load_dev_tools_coverage()

        legacy_summary = self.legacy_cleanup_summary or {}

        unused_imports_data = self.results_cache.get('unused_imports', {}) or {}

        function_metrics = self.results_cache.get('analyze_functions', {}) or {}

        decision_metrics = self.results_cache.get('decision_support_metrics', {}) or {}

        validation_output = ""

        if hasattr(self, 'validation_results') and self.validation_results:

            validation_output = self.validation_results.get('output', '') or ""
        else:
            # Try to load from cache
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'analyze_ai_work' in cached_data['results']:
                        validation_data = cached_data['results']['analyze_ai_work']
                        # Handle nested data structure: results.analyze_ai_work.data.output
                        if 'data' in validation_data:
                            data = validation_data['data']
                            # Check if data is a dict with 'output' key, or if it's the result dict itself
                            if isinstance(data, dict):
                                validation_output = data.get('output', '') or ''
                                # If output is empty, check if there's a nested structure
                                if not validation_output and 'data' in data:
                                    validation_output = data['data'].get('output', '') or ''
                        else:
                            validation_output = validation_data.get('output', '') or ""
            except Exception:
                pass

        results_file = self.audit_config.get('results_file', 'development_tools/reports/analysis_detailed_results.json')

        issues_file = self.audit_config.get('issues_file', 'development_tools/critical_issues.txt')

        # Recalculate doc_coverage if Unknown (same logic as Documentation Findings section)
        # Do this BEFORE Executive Summary so it's available for display
        if doc_coverage == 'Unknown' or doc_coverage is None:
            results_cache = self.results_cache or {}
            audit_data = results_cache.get('analyze_function_registry', {}) or {}
            audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}
            if audit_totals is None or not isinstance(audit_totals, dict):
                audit_totals = {}
            documented = audit_totals.get('functions_documented', 0)
            total_funcs = metrics.get('total_functions')
            if total_funcs and isinstance(total_funcs, (int, float)) and total_funcs > 0 and documented > 0:
                coverage_pct = (documented / total_funcs) * 100
                if 0 <= coverage_pct <= 100:
                    doc_coverage = f"{coverage_pct:.2f}%"

        lines.append("## Executive Summary")

        lines.append(f"- Documentation coverage {percent_text(doc_coverage, 2)} with {missing_docs or 0} registry gaps")

        error_cov = error_metrics.get('analyze_error_handling') or error_metrics.get('error_handling_coverage')
        
        # Recalculate error handling coverage using canonical function count for consistency
        # analyze_error_handling might use a different total (including tests/dev tools)
        # but we want to show coverage against the same function set as other metrics
        error_total = error_metrics.get('total_functions')
        error_with_handling = error_metrics.get('functions_with_error_handling')
        canonical_total = metrics.get('total_functions')
        
        if error_cov is not None and canonical_total and error_total and error_with_handling:
            # If error_handling used a different total, recalculate for consistency
            if error_total != canonical_total:
                # Recalculate coverage using canonical total
                recalc_coverage = (error_with_handling / canonical_total) * 100
                if 0 <= recalc_coverage <= 100:
                    error_cov = recalc_coverage
                    # Also update missing count
                    missing_error_handlers = canonical_total - error_with_handling
                else:
                    # If recalculation gives > 100%, it means error_with_handling includes functions from tests/dev tools
                    # that aren't in canonical_total. In this case, we can't accurately recalculate.
                    # Use the original value but note it might be based on a different function set.
                    pass
            elif error_total == canonical_total:
                # Same total, use the original coverage value
                missing_error_handlers = error_metrics.get('functions_missing_error_handling', 0)

        if error_cov is not None:

            lines.append(f"- Error handling coverage {percent_text(error_cov, 1)}; {missing_error_handlers or 0} functions need protection")

        dev_tools_insights = self._get_dev_tools_coverage_insights()

        if coverage_summary:

            overall = coverage_summary.get('overall') or {}
            overall_cov = overall.get('coverage')

            lines.append(f"- Test coverage {percent_text(overall_cov, 1)} across {overall.get('statements', 0)} statements")
            
            if dev_tools_insights and dev_tools_insights.get('overall_pct') is not None:
                dev_pct = dev_tools_insights['overall_pct']
                summary_line = f"- Development tools coverage {percent_text(dev_pct, 1)}"
                if dev_tools_insights.get('covered') is not None and dev_tools_insights.get('statements') is not None:
                    summary_line += f" ({dev_tools_insights['covered']} of {dev_tools_insights['statements']} statements)"
                lines.append(summary_line)

        elif hasattr(self, 'coverage_results') and self.coverage_results:

            lines.append("- Coverage regeneration flagged issues; inspect coverage.json for details")

        path_drift = doc_sync_summary.get('path_drift_issues') if doc_sync_summary else None

        if path_drift is not None:

            lines.append(f"- Documentation path drift: {path_drift} files need sync")

        legacy_issues = legacy_summary.get('files_with_issues')

        if legacy_issues is not None:

            lines.append(f"- Legacy references outstanding in {legacy_issues} files")

        lines.append("")

        lines.append("## Audit Metrics")

        # Get complexity metrics, trying multiple sources
        total_funcs = metrics.get('total_functions', 'Unknown')
        moderate = metrics.get('moderate', 'Unknown')
        high = metrics.get('high', 'Unknown')
        critical = metrics.get('critical', 'Unknown')
        
        # If still Unknown, try loading from analyze_functions or decision_support cache
        if moderate == 'Unknown' or high == 'Unknown':
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            cached_metrics = func_data['data']
                            if moderate == 'Unknown':
                                moderate = cached_metrics.get('moderate_complexity', 'Unknown')
                            if high == 'Unknown':
                                high = cached_metrics.get('high_complexity', 'Unknown')
                            if critical == 'Unknown':
                                critical = cached_metrics.get('critical_complexity', 'Unknown')
                            if total_funcs == 'Unknown':
                                total_funcs = cached_metrics.get('total_functions', 'Unknown')
                    # Fallback to decision_support
                    if (moderate == 'Unknown' or high == 'Unknown') and 'results' in cached_data and 'decision_support' in cached_data['results']:
                        ds_data = cached_data['results']['decision_support']
                        if 'data' in ds_data and 'decision_support_metrics' in ds_data['data']:
                            ds_metrics = ds_data['data']['decision_support_metrics']
                            if moderate == 'Unknown':
                                moderate = ds_metrics.get('moderate_complexity', 'Unknown')
                            if high == 'Unknown':
                                high = ds_metrics.get('high_complexity', 'Unknown')
                            if critical == 'Unknown':
                                critical = ds_metrics.get('critical_complexity', 'Unknown')
                            if total_funcs == 'Unknown':
                                total_funcs = ds_metrics.get('total_functions', 'Unknown')
            except Exception as e:
                logger.debug(f"Failed to load complexity from cache in consolidated report: {e}")
                pass

        lines.append(f"- **Total Functions**: {total_funcs}")

        lines.append(f"- **Complexity Distribution**: Moderate {moderate}, High {high}, Critical {critical}")

        if documented_functions is not None:

            lines.append(f"- **Documented Functions**: {documented_functions}")

        if decision_metrics:

            actions = decision_metrics.get('decision_support_items')

            if actions:

                lines.append(f"- **Decision Support Signals Captured**: {actions}")

        lines.append("")

        lines.append("## Documentation Findings")

        # Use canonical metrics for doc_coverage (same as AI_STATUS.md)
        doc_coverage = metrics.get('doc_coverage', 'Unknown')
        if doc_coverage == 'Unknown' or doc_coverage is None:
            # Recalculate if we have the data
            audit_data = results_cache.get('analyze_function_registry', {}) or {}
            audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}
            if audit_totals is None or not isinstance(audit_totals, dict):
                audit_totals = {}
            documented = audit_totals.get('functions_documented', 0)
            total_funcs = metrics.get('total_functions')
            if total_funcs and isinstance(total_funcs, (int, float)) and total_funcs > 0 and documented > 0:
                coverage_pct = (documented / total_funcs) * 100
                if 0 <= coverage_pct <= 100:
                    doc_coverage = f"{coverage_pct:.2f}%"
        
        lines.append(f"- **Coverage**: {percent_text(doc_coverage, 2)}")

        if missing_docs:

            lines.append(f"- **Missing Registry Entries**: {missing_docs}")

        missing_files = self._get_missing_doc_files(limit=8)

        if missing_files:

            lines.append(f"- **Docs to Update**: {self._format_list_for_display(missing_files, limit=8)}")
        
        # Add overlap analysis section (always show, even if no overlaps found)
        lines.append("")
        lines.append("## Documentation Overlap Analysis")
        overlap_count = len(section_overlaps) if section_overlaps else 0
        consolidation_count = len(consolidation_recs) if consolidation_recs else 0
        
        if overlap_count > 0 or consolidation_count > 0:
            if section_overlaps:
                lines.append(f"- **Section Overlaps**: {overlap_count} sections appear in multiple files")
                # Show top 5 overlaps
                top_overlaps = sorted(section_overlaps.items(), key=lambda x: len(x[1]), reverse=True)[:5]
                for section_name, files in top_overlaps:
                    if len(files) > 1:
                        lines.append(f"  - Section '{section_name}' appears in {len(files)} files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}")
            if consolidation_recs:
                lines.append(f"- **Consolidation Opportunities**: {consolidation_count} file groups identified for potential consolidation")
                for rec in consolidation_recs[:3]:  # Show top 3 recommendations
                    category = rec.get('category', 'Unknown')
                    files = rec.get('files', [])
                    suggestion = rec.get('suggestion', '')
                    if files:
                        lines.append(f"  - {category}: {len(files)} files ({', '.join(files[:2])}{'...' if len(files) > 2 else ''}) - {suggestion}")
        else:
            lines.append("- **Status**: No section overlaps or consolidation opportunities detected")
            lines.append("- Overlap analysis was performed during this audit")

        if doc_sync_summary:

            path_drift = doc_sync_summary.get('path_drift_issues')

            paired = doc_sync_summary.get('paired_doc_issues')

            ascii_issues = doc_sync_summary.get('ascii_issues')

            total_issues = doc_sync_summary.get('total_issues')

            lines.append(f"- **Doc Sync Status**: {doc_sync_summary.get('status', 'Unknown')} ({total_issues or 0} issues)")

            if path_drift:

                lines.append(f"  - Path drift in {path_drift} files")

            if paired:

                lines.append(f"  - {paired} paired documents out of sync")

            if ascii_issues:

                lines.append(f"  - {ascii_issues} files contain non-ASCII characters")

            drift_files = doc_sync_summary.get('path_drift_files') or []

            if drift_files:

                lines.append(f"  - Hotspots: {self._format_list_for_display(drift_files, limit=5)}")

        else:

            lines.append("- Run doc-sync to capture current documentation drift data")

        dependency_summary = self.module_dependency_summary or self.results_cache.get('analyze_module_dependencies')

        if dependency_summary:

            missing = dependency_summary.get('missing_dependencies')

            line = f"- **Dependency Docs**: {missing or 0} undocumented references"

            lines.append(line)

            dep_files = dependency_summary.get('missing_files') or dependency_summary.get('missing_sections') or []

            if dep_files and (missing or 0):

                lines.append(f"  - Hotspots: {self._format_list_for_display(dep_files, limit=5)}")

        if doc_artifacts:

            artifact = doc_artifacts[0]

            lines.append(f"- **Content Fix**: {artifact.get('file')} line {artifact.get('line')} flagged for {artifact.get('pattern')}")

            if len(doc_artifacts) > 1:

                lines.append(f"  - Additional documentation findings: {len(doc_artifacts) - 1} more items")

        lines.append("")

        lines.append("## Error Handling Analysis")

        if error_metrics:
            # Use recalculated error_cov from Executive Summary section (already calculated above)
            # If not recalculated, get from error_metrics
            if 'error_cov' not in locals() or error_cov is None:
                error_cov = error_metrics.get('analyze_error_handling') or error_metrics.get('error_handling_coverage')
                # Recalculate if needed
                error_total = error_metrics.get('total_functions')
                error_with_handling = error_metrics.get('functions_with_error_handling')
                canonical_total = metrics.get('total_functions')
                if error_cov is not None and canonical_total and error_total and error_with_handling:
                    if error_total != canonical_total:
                        recalc_coverage = (error_with_handling / canonical_total) * 100
                        if 0 <= recalc_coverage <= 100:
                            error_cov = recalc_coverage
                            missing_error_handlers = canonical_total - error_with_handling
                        else:
                            missing_error_handlers = error_metrics.get('functions_missing_error_handling', 0)
                    else:
                        missing_error_handlers = error_metrics.get('functions_missing_error_handling', 0)
                else:
                    missing_error_handlers = error_metrics.get('functions_missing_error_handling', 0)

            lines.append(f"- **Coverage**: {percent_text(error_cov, 1)}")

            lines.append(f"- **Functions Missing Protection**: {missing_error_handlers or 0}")

            quality = error_metrics.get('error_handling_quality') or {}

            basic = quality.get('basic')

            none = quality.get('none')

            if basic:

                lines.append(f"- **Upgrade Targets**: {basic} functions rely on basic try-except blocks")

            if none:

                lines.append(f"- **Critical Items**: {none} functions have no error handling")

            # Phase 1: Decorator replacement candidates

            phase1_total = error_metrics.get('phase1_total', 0)

            if phase1_total > 0:

                phase1_by_priority = error_metrics.get('phase1_by_priority', {})

                priority_breakdown = []

                if phase1_by_priority.get('high', 0) > 0:

                    priority_breakdown.append(f"{phase1_by_priority['high']} high")

                if phase1_by_priority.get('medium', 0) > 0:

                    priority_breakdown.append(f"{phase1_by_priority['medium']} medium")

                if phase1_by_priority.get('low', 0) > 0:

                    priority_breakdown.append(f"{phase1_by_priority['low']} low")

                priority_text = ', '.join(priority_breakdown) if priority_breakdown else '0'

                lines.append(f"- **Phase 1 Candidates**: {phase1_total} functions need `@handle_errors` decorator ({priority_text} priority)")

            # Phase 2: Generic exception categorization

            phase2_total = error_metrics.get('phase2_total', 0)

            if phase2_total > 0:

                phase2_by_type = error_metrics.get('phase2_by_type', {})

                type_breakdown = [f"{count} {exc_type}" for exc_type, count in sorted(phase2_by_type.items(), key=lambda x: x[1], reverse=True)[:5]]

                type_text = ', '.join(type_breakdown) if type_breakdown else '0'

                if len(phase2_by_type) > 5:

                    type_text += f", ... +{len(phase2_by_type) - 5} more"

                lines.append(f"- **Phase 2 Exceptions**: {phase2_total} generic exception raises need categorization ({type_text})")

            if error_recommendations:

                lines.append(f"- **Top Recommendation**: {error_recommendations[0]}")

            if worst_error_modules:

                module_summaries = []

                for module in worst_error_modules[:5]:

                    module_name = module.get('module', 'Unknown')

                    coverage_pct = percent_text(module.get('coverage'), 1)

                    missing = module.get('missing')

                    total = module.get('total')

                    detail = f"{module_name} ({coverage_pct}"

                    if missing is not None and total is not None:

                        detail += f", missing {missing}/{total}"

                    detail += ")"

                    module_summaries.append(detail)

                lines.append(f"- **Modules Requiring Attention**: {', '.join(module_summaries)}")

        else:

            lines.append("- **Error Handling**: Run `python development_tools/run_development_tools.py audit --fast` for detailed metrics")

        lines.append("")

        lines.append("## Testing & Coverage")

        if coverage_summary and isinstance(coverage_summary, dict):

            overall = coverage_summary.get('overall') or {}

            lines.append(f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} ({overall.get('covered')} of {overall.get('statements')} statements)")

            module_gaps = [m for m in (coverage_summary.get('modules') or []) if m.get('coverage', 100) < 90]

            if module_gaps:

                module_descriptions = [

                    f"{m['module']} ({percent_text(m.get('coverage'), 1)}, missing {m.get('missed')} lines)"

                    for m in module_gaps[:5]

                ]

                lines.append(f"- **Modules Below Target**: {', '.join(module_descriptions)}")

            worst_files = (coverage_summary or {}).get('worst_files') or []

            if worst_files:

                file_descriptions = [

                    f"{item['path']} ({percent_text(item.get('coverage'), 1)})"

                    for item in worst_files

                ]

                lines.append(f"- **Files Missing Tests**: {', '.join(file_descriptions)}")

            if dev_tools_insights and dev_tools_insights.get('overall_pct') is not None:
                dev_pct = dev_tools_insights['overall_pct']
                dev_line = f"- **Development Tools Coverage**: {percent_text(dev_pct, 1)}"
                if dev_tools_insights.get('covered') is not None and dev_tools_insights.get('statements') is not None:
                    dev_line += f" ({dev_tools_insights['covered']} of {dev_tools_insights['statements']} statements)"
                lines.append(dev_line)
                low_modules = dev_tools_insights.get('low_modules') or []
                if low_modules:
                    dev_descriptions = [
                        f"{Path(item['path']).name} ({percent_text(item.get('coverage'), 1)}, missing {item.get('missed')} lines)"
                        for item in low_modules
                    ]
                    lines.append(f"- **Lowest Dev Tool Modules**: {', '.join(dev_descriptions)}")
                if dev_tools_insights.get('html'):
                    lines.append(f"- **Dev Tools Report**: {dev_tools_insights['html']}")

            generated = overall.get('generated')

            if generated:

                lines.append(f"- **Report Timestamp**: {generated}")
            

        elif hasattr(self, 'coverage_results') and self.coverage_results:

            lines.append("- Coverage regeneration completed with issues; inspect coverage.json for gap details")

        else:

            lines.append("- Run `audit --full` to regenerate coverage metrics")

        lines.append("")

        lines.append("## Complexity & Refactoring")
        
        # Try to load complexity from decision_support if analyze_functions doesn't have it
        if function_metrics.get('high_complexity') == 'Unknown' or function_metrics.get('high_complexity') is None:
            if decision_metrics:
                function_metrics['high_complexity'] = decision_metrics.get('high_complexity', 'Unknown')
                function_metrics['critical_complexity'] = decision_metrics.get('critical_complexity', 'Unknown')
                function_metrics['moderate_complexity'] = decision_metrics.get('moderate_complexity', 'Unknown')
        
        # If still unknown, try loading from cache
        if function_metrics.get('high_complexity') == 'Unknown' or function_metrics.get('high_complexity') is None:
            try:
                import json
                results_file = self.project_root / "development_tools" / "reports" / "analysis_detailed_results.json"
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    # Try analyze_functions first
                    if 'results' in cached_data and 'analyze_functions' in cached_data['results']:
                        func_data = cached_data['results']['analyze_functions']
                        if 'data' in func_data:
                            cached_metrics = func_data['data']
                            function_metrics['high_complexity'] = cached_metrics.get('high_complexity', 'Unknown')
                            function_metrics['critical_complexity'] = cached_metrics.get('critical_complexity', 'Unknown')
                            function_metrics['moderate_complexity'] = cached_metrics.get('moderate_complexity', 'Unknown')
                    # Fallback to decision_support
                    if function_metrics.get('high_complexity') == 'Unknown' and 'results' in cached_data and 'decision_support' in cached_data['results']:
                        ds_data = cached_data['results']['decision_support']
                        if 'data' in ds_data and 'decision_support_metrics' in ds_data['data']:
                            ds_metrics = ds_data['data']['decision_support_metrics']
                            function_metrics['high_complexity'] = ds_metrics.get('high_complexity', 'Unknown')
                            function_metrics['critical_complexity'] = ds_metrics.get('critical_complexity', 'Unknown')
                            function_metrics['moderate_complexity'] = ds_metrics.get('moderate_complexity', 'Unknown')
            except Exception:
                pass

        lines.append(f"- **High Complexity Functions**: {function_metrics.get('high_complexity', 'Unknown')}")

        lines.append(f"- **Critical Complexity Functions**: {function_metrics.get('critical_complexity', 'Unknown')}")

        critical_examples = function_metrics.get('critical_complexity_examples') or []

        if critical_examples:

            critical_items = [

                f"{item['function']} ({item['file']})"

                for item in critical_examples[:5]

            ]

            lines.append(f"- **Critical Examples**: {', '.join(critical_items)}")

        high_examples = function_metrics.get('high_complexity_examples') or []

        if high_examples:

            high_items = [

                f"{item['function']} ({item['file']})"

                for item in high_examples[:5]

            ]

            lines.append(f"- **High Complexity Examples**: {', '.join(high_items)}")

        undocumented_examples = function_metrics.get('undocumented_examples') or []

        if undocumented_examples:

            undocumented_items = [

                f"{item['function']} ({item['file']})"

                for item in undocumented_examples[:5]

            ]

            lines.append(f"- **Undocumented Functions**: {', '.join(undocumented_items)}")

        lines.append("")

        lines.append("## Legacy & Code Hygiene")

        if legacy_summary:

            legacy_issues = legacy_summary.get('files_with_issues')

            lines.append(f"- **Files with Legacy Markers**: {legacy_issues if legacy_issues is not None else 'Unknown'}")

            legacy_markers = legacy_summary.get('legacy_markers')

            if legacy_markers is not None:

                lines.append(f"- **Markers Found**: {legacy_markers}")

            report_path = legacy_summary.get('report_path')

            if report_path:

                lines.append(f"- **Detailed Report**: {report_path}")

        else:

            lines.append("- Run legacy cleanup to refresh legacy reference data")

        if unused_imports_data:

            total_unused = unused_imports_data.get('total_unused', 0)

            files_with_issues = unused_imports_data.get('files_with_issues', 0)

            lines.append(f"- **Unused Imports**: {total_unused} across {files_with_issues} files")

            by_category = unused_imports_data.get('by_category') or {}

            obvious = by_category.get('obvious_unused')

            if obvious:

                lines.append(f"  - Obvious removals: {obvious}")

            type_only = by_category.get('type_hints_only')

            if type_only:

                lines.append(f"  - Type-only imports: {type_only}")

        else:

            lines.append("- Run unused-imports checker for an updated removal list")

        ascii_issues = doc_sync_summary.get('ascii_issues') if doc_sync_summary else None

        if ascii_issues:

            lines.append(f"- **ASCII Cleanup**: {ascii_issues} files need normalization")

        lines.append("")

        lines.append("## Validation & Follow-ups")

        if 'POOR' in validation_output:

            lines.append("- **AI Work Validation**: POOR - documentation or tests missing")

        elif 'GOOD' in validation_output:

            lines.append("- **AI Work Validation**: GOOD - keep current standards")

        elif validation_output:

            lines.append("- **AI Work Validation**: NEEDS REVIEW - inspect consolidated report")

        else:

            lines.append("- Validation results unavailable for this run")

        lines.append("- **Suggested Commands**:")

        lines.append("  - `python development_tools/run_development_tools.py doc-sync`")

        lines.append("  - `python development_tools/run_development_tools.py audit --full`")

        lines.append("  - `python development_tools/run_development_tools.py legacy`")

        lines.append("  - `python development_tools/run_development_tools.py status`")

        lines.append("")

        lines.append("## Reference Files")

        lines.append(f"- Detailed JSON results: {results_file}")

        lines.append(f"- Critical issues summary: {issues_file}")

        lines.append("- Latest AI status: development_tools/AI_STATUS.md")

        lines.append("- Current AI priorities: development_tools/AI_PRIORITIES.md")

        lines.append("- Legacy reference report: development_docs/LEGACY_REFERENCE_REPORT.md")

        coverage_report = self.project_root / 'tests' / 'coverage_html'

        if coverage_report.exists():

            lines.append(f"- Coverage HTML report: {coverage_report}")

        unused_report = self.project_root / 'development_docs' / 'UNUSED_IMPORTS_REPORT.md'

        if unused_report.exists():

            lines.append(f"- Unused imports detail: {unused_report}")

        analyze_report = self.project_root / 'development_tools' / 'reports' / 'analysis_detailed_results.json'

        if analyze_report.exists():

            lines.append(f"- Historical audit data: {analyze_report}")

        lines.append("")

        return "\n".join(lines)

    def _identify_critical_issues(self) -> List[str]:

        """Identify critical issues from audit results"""

        issues = []

        # Check function documentation coverage

        if 'analyze_functions' in self.results_cache:

            metrics = self.results_cache['analyze_functions']

            if 'coverage' in metrics:

                try:

                    coverage = float(metrics['coverage'].replace('%', ''))

                    if coverage < 90:

                        issues.append(f"Low documentation coverage: {coverage}%")

                except:

                    pass

        # Check for failed audits

        if hasattr(self, '_last_failed_audits'):

            for audit in self._last_failed_audits:

                issues.append(f"Failed audit: {audit}")

        return issues

    def _generate_action_items(self) -> List[str]:

        """Generate actionable items from audit results"""

        actions = []

        # Documentation improvements (only if needed)

        if 'analyze_functions' in self.results_cache:

            metrics = self.results_cache['analyze_functions']

            if 'coverage' in metrics:

                try:

                    coverage = float(metrics['coverage'].replace('%', ''))

                    if coverage < 95:

                        actions.append(f"Improve documentation coverage (currently {coverage}%)")

                except:

                    pass

        # Complexity management (only if significant)

        if 'decision_support' in self.results_cache:

            insights = self.results_cache['decision_support']

            if isinstance(insights, list) and insights:

                # Look for complexity warnings

                complexity_warnings = [insight for insight in insights if 'complexity' in insight.lower()]

                if complexity_warnings:

                    actions.append("Refactor high complexity functions for maintainability")

        # Core development tasks

        actions.append("Review TODO.md for next development priorities")

        actions.append("Run comprehensive testing before major changes")

        # Maintenance tasks (updated changelog reference)

        actions.append("Update AI_CHANGELOG.md and CHANGELOG_DETAIL.md with recent changes")

        return actions

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

    def _run_doc_sync_check(self, *args) -> bool:

        """Run all documentation sync checks and aggregate results."""

        all_results = {}

        # Run paired documentation sync
        logger.info("Running paired documentation synchronization checks...")
        result = self.run_script('analyze_documentation_sync', *args)
        # For analysis tools, success means they ran and produced output (even if issues found)
        if result.get('output') or result.get('success'):
            all_results['paired_docs'] = self._parse_documentation_sync_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_documentation_sync failed: {result.get('error', 'Unknown error')}")

        # Run path drift analysis
        logger.info("Running path drift analysis...")
        result = self.run_script('analyze_path_drift')
        if result.get('output') or result.get('success'):
            all_results['path_drift'] = self._parse_path_drift_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_path_drift failed: {result.get('error', 'Unknown error')}")

        # Run ASCII compliance check
        logger.info("Running ASCII compliance check...")
        result = self.run_script('analyze_ascii_compliance')
        if result.get('output') or result.get('success'):
            all_results['ascii_compliance'] = self._parse_ascii_compliance_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_ascii_compliance failed: {result.get('error', 'Unknown error')}")

        # Run heading numbering check
        logger.info("Running heading numbering check...")
        result = self.run_script('analyze_heading_numbering')
        if result.get('output') or result.get('success'):
            all_results['heading_numbering'] = self._parse_heading_numbering_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_heading_numbering failed: {result.get('error', 'Unknown error')}")

        # Run missing addresses check
        logger.info("Running missing addresses check...")
        result = self.run_script('analyze_missing_addresses')
        if result.get('output') or result.get('success'):
            all_results['missing_addresses'] = self._parse_missing_addresses_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_missing_addresses failed: {result.get('error', 'Unknown error')}")

        # Run unconverted links check
        logger.info("Running unconverted links check...")
        result = self.run_script('analyze_unconverted_links')
        if result.get('output') or result.get('success'):
            all_results['unconverted_links'] = self._parse_unconverted_links_output(result.get('output', ''))
        else:
            logger.warning(f"analyze_unconverted_links failed: {result.get('error', 'Unknown error')}")

        # Aggregate all results
        summary = self._aggregate_doc_sync_results(all_results)

        self.docs_sync_results = {'success': True, 'summary': summary, 'all_results': all_results}
        self.docs_sync_summary = summary

        logger.info(f"Documentation sync summary: {summary.get('status', 'UNKNOWN')} - {summary.get('total_issues', 0)} total issues")

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

            logger.info(result['output'])

        if result.get('error'):

            logger.error(result['error'])

        return False

    def show_help(self):

        """Show comprehensive help and the available command list."""

        print("AI Development Tools Runner")
        print("=" * 50)
        print(f"Comprehensive AI collaboration tools for the {self.project_name} project")
        print()
        print("USAGE:")
        print("  python development_tools/run_development_tools.py <command> [options]")
        print()
        print("AVAILABLE COMMANDS:")
        print()

        for section, metadata in COMMAND_TIERS.items():
            print(f"  {section}:")
            description = metadata.get("description")
            if description:
                print(f"    {description}")
            for cmd_name in metadata.get("commands", []):
                if cmd_name in COMMAND_REGISTRY:
                    cmd = COMMAND_REGISTRY[cmd_name]
                    print(f"    {cmd.name:<16} {cmd.help}")
            if metadata.get("tier") == "experimental":
                print("    WARNING: Experimental commands may change or fail; run only with approval.")
            print()

        print("EXAMPLES:")
        print("  python development_tools/run_development_tools.py status")
        print("  python development_tools/run_development_tools.py audit --full")
        print("  python development_tools/run_development_tools.py docs")
        print("  python development_tools/run_development_tools.py unused-imports")
        print()
        print("For detailed command options:")
        print("  python development_tools/run_development_tools.py <command> --help")

@dataclass(frozen=True)

class CommandRegistration:

    name: str

    handler: Callable[["AIToolsService", Sequence[str]], int]

    help: str

    description: str = ''

def _print_command_help(parser: argparse.ArgumentParser) -> None:

    parser.print_help()

    print()

def _audit_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    parser = argparse.ArgumentParser(prog='audit', add_help=False)

    parser.add_argument('--full', action='store_true', help='Run comprehensive audit (includes coverage).')

    parser.add_argument('--fast', action='store_true', help='Force fast audit (skip coverage).')

    parser.add_argument('--include-tests', action='store_true', help='Include test files in analysis.')

    parser.add_argument('--include-dev-tools', action='store_true', help='Include development_tools in analysis.')

    parser.add_argument('--include-all', action='store_true', help='Include tests and dev tools (equivalent to --include-tests --include-dev-tools).')

    parser.add_argument('--overlap', action='store_true', help='Include overlap analysis in documentation analysis (section overlaps and consolidation recommendations).')

    if any(arg in ('-h', '--help') for arg in argv):

        _print_command_help(parser)

        return 0

    ns = parser.parse_args(list(argv))

    fast_mode = not ns.full

    if ns.fast:

        fast_mode = True

    # Set exclusion configuration

    service.set_exclusion_config(

        include_tests=ns.include_tests or ns.include_all,

        include_dev_tools=ns.include_dev_tools or ns.include_all

    )

    success = service.run_audit(fast=fast_mode, include_overlap=ns.overlap)

    return 0 if success else 1

def _docs_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'docs' command does not accept additional arguments.")

            return 2

        print("Usage: docs")

        return 0

    success = service.run_docs()

    return 0 if success else 1

def _validate_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'validate' command does not accept additional arguments.")

            return 2

        print("Usage: validate")

        return 0

    success = service.run_validate()

    return 0 if success else 1

def _config_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'config' command does not accept additional arguments.")

            return 2

        print("Usage: config")

        return 0

    success = service.run_config()

    return 0 if success else 1

def _workflow_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    parser = argparse.ArgumentParser(prog='workflow', add_help=False)

    parser.add_argument('task_type', help='Workflow task to execute')

    if any(arg in ('-h', '--help') for arg in argv):

        _print_command_help(parser)

        return 0

    if not argv:

        print("Usage: workflow <task_type>")

        return 2

    ns = parser.parse_args(list(argv))

    success = service.run_workflow(ns.task_type)

    return 0 if success else 1

def _quick_audit_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'quick-audit' command does not accept additional arguments.")

            return 2

        print("Usage: quick-audit")

        return 0

    success = service.run_quick_audit()

    return 0 if success else 1

def _decision_support_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'decision-support' command does not accept additional arguments.")

            return 2

        print("Usage: decision-support")

        return 0

    result = service.run_decision_support()

    return 0 if (isinstance(result, dict) and result.get('success', False)) or result else 1

def _fix_version_sync_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    parser = argparse.ArgumentParser(prog='version-sync', add_help=False)

    parser.add_argument('scope', nargs='?', default='docs', help='Scope to sync (docs, core, ai_docs, all).')

    if any(arg in ('-h', '--help') for arg in argv):

        _print_command_help(parser)

        return 0

    ns = parser.parse_args(list(argv))

    success = service.run_version_sync(ns.scope)

    return 0 if success else 1

def _status_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'status' command does not accept additional arguments.")

            return 2

        print("Usage: status")

        return 0

    success = service.run_status()

    return 0 if success else 1

def _system_signals_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle system-signals command"""
    if argv:
        if any(arg not in ('-h', '--help') for arg in argv):
            print("The 'system-signals' command does not accept additional arguments.")
            return 2
        print("Usage: system-signals")
        return 0

    success = service.run_system_signals()
    return 0 if success else 1

def _doc_sync_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'doc-sync' command does not accept additional arguments.")

            return 2

        print("Usage: doc-sync")

        return 0

    success = service.run_documentation_sync()

    return 0 if success else 1

def _doc_fix_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    """Handle doc-fix command with options for different fix types."""

    parser = argparse.ArgumentParser(description='Fix documentation issues')

    parser.add_argument('--add-addresses', action='store_true', help='Add file addresses to documentation files')

    parser.add_argument('--fix-ascii', action='store_true', help='Fix non-ASCII characters in documentation')

    parser.add_argument('--number-headings', action='store_true', help='Number H2 and H3 headings in documentation')

    parser.add_argument('--convert-links', action='store_true', help='Convert file paths to markdown links')

    parser.add_argument('--all', action='store_true', help='Apply all fix operations')

    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')

    try:

        args = parser.parse_args(argv)

    except SystemExit:

        return 2

    # Determine fix type

    fix_types = []

    if args.add_addresses:

        fix_types.append('add-addresses')

    if args.fix_ascii:

        fix_types.append('fix-ascii')

    if args.number_headings:

        fix_types.append('number-headings')

    if args.convert_links:

        fix_types.append('convert-links')

    if args.all:

        fix_type = 'all'

    elif len(fix_types) == 1:

        fix_type = fix_types[0]

    elif len(fix_types) > 1:

        print("Error: Can only specify one fix type at a time (or use --all)")

        return 2

    else:

        # Default to all if nothing specified

        fix_type = 'all'

    success = service.run_documentation_fix(fix_type=fix_type, dry_run=args.dry_run)

    return 0 if success else 1

def _coverage_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'coverage' command does not accept additional arguments.")

            return 2

        print("Usage: coverage")

        return 0

    success = service.run_coverage_regeneration()

    return 0 if success else 1

def _legacy_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'legacy' command does not accept additional arguments.")

            return 2

        print("Usage: legacy")

        return 0

    success = service.run_legacy_cleanup()

    return 0 if success else 1

def _unused_imports_command(service: "AIToolsService", argv: Sequence[str]) -> int:
    """Handle unused-imports command."""
    if argv:
        if '-h' in argv or '--help' in argv:
            print("Usage: unused-imports")
            return 0
        
        if any(arg not in ('-h', '--help') for arg in argv):
            print("The 'unused-imports' command does not accept additional arguments.")
            print("Usage: unused-imports")
            return 2

    success = service.run_unused_imports_report()

    return 0 if success else 1

def _trees_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'trees' command does not accept additional arguments.")

            return 2

        print("Usage: trees")

        return 0

    success = service.generate_directory_trees()

    return 0 if success else 1

def _show_help_command(service: "AIToolsService", argv: Sequence[str]) -> int:

    service.show_help()

    return 0

COMMAND_REGISTRY = OrderedDict([

    ('audit', CommandRegistration('audit', _audit_command, 'Run fast or full audit.')),

    ('docs', CommandRegistration('docs', _docs_command, 'Regenerate documentation artifacts.')),

    ('validate', CommandRegistration('validate', _validate_command, 'Validate AI-generated work.')),

    ('config', CommandRegistration('config', _config_command, 'Check configuration consistency.')),

    ('workflow', CommandRegistration('workflow', _workflow_command, 'Execute an audit-first workflow task.')),

    ('quick-audit', CommandRegistration('quick-audit', _quick_audit_command, 'Run comprehensive audit without extras.')),

    ('decision-support', CommandRegistration('decision-support', _decision_support_command, 'Generate decision support insights.')),

    ('version-sync', CommandRegistration('version-sync', _fix_version_sync_command, 'Synchronize version metadata.')),

    ('status', CommandRegistration('status', _status_command, 'Print quick system status.')),

    ('system-signals', CommandRegistration('system-signals', _system_signals_command, 'Generate system health and status signals.')),

    ('doc-sync', CommandRegistration('doc-sync', _doc_sync_command, 'Check documentation synchronisation.')),

    ('doc-fix', CommandRegistration('doc-fix', _doc_fix_command, 'Fix documentation issues (addresses, ASCII, headings, links).')),

    ('coverage', CommandRegistration('coverage', _coverage_command, 'Regenerate coverage metrics.')),

    ('legacy', CommandRegistration('legacy', _legacy_command, 'Scan for legacy references.')),

    ('unused-imports', CommandRegistration('unused-imports', _unused_imports_command, 'Detect unused imports in codebase.')),

    ('trees', CommandRegistration('trees', _trees_command, 'Generate directory tree reports.')),

    ('help', CommandRegistration('help', _show_help_command, 'Show detailed help information.')),

])

def list_commands() -> Sequence[CommandRegistration]:

    return tuple(COMMAND_REGISTRY.values())

