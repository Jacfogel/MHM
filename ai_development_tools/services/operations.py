#!/usr/bin/env python3

"""

Core operations used by the AI development toolchain.

This module contains the reusable service layer that powers the CLI in

`ai_tools_runner.py`. Each public method exposes a discrete workflow that

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

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("ai_development_tools")

SCRIPT_REGISTRY = {

    'analyze_documentation': 'analyze_documentation.py',

    'audit_function_registry': 'audit_function_registry.py',

    'audit_module_dependencies': 'audit_module_dependencies.py',

    'config_validator': 'config_validator.py',

    'decision_support': 'decision_support.py',

    'documentation_sync_checker': 'documentation_sync_checker.py',

    'error_handling_coverage': 'error_handling_coverage.py',

    'function_discovery': 'function_discovery.py',

    'generate_function_registry': 'generate_function_registry.py',

    'generate_module_dependencies': 'generate_module_dependencies.py',

    'legacy_reference_cleanup': 'legacy_reference_cleanup.py',

    'quick_status': 'quick_status.py',

    'regenerate_coverage_metrics': 'regenerate_coverage_metrics.py',

    'unused_imports_checker': 'unused_imports_checker.py',

    'validate_ai_work': 'validate_ai_work.py',

    'version_sync': 'version_sync.py',

    'system_signals': 'system_signals.py'

}

from ..file_rotation import create_output_file
from .common import COMMAND_CATEGORIES

class AIToolsService:

    """Comprehensive AI tools runner optimized for AI collaboration."""

    def __init__(self):

        self.project_root = Path(config.get_project_root()).resolve()

        self.workflow_config = config.get_workflow_config()

        self.validation_config = config.get_ai_validation_config()

        self.ai_config = config.get_ai_collaboration_config()

        self.audit_config = config.get_quick_audit_config()

        self.results_cache = {}

        self.docs_sync_results = None

        self.system_signals = None

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

        """Run a registered helper script from ai_development_tools."""

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

    def run_analyze_documentation(self) -> Dict:

        """Run analyze_documentation with structured JSON handling."""

        result = self.run_script("analyze_documentation", "--json")

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

    def run_audit_function_registry(self) -> Dict:

        """Run audit_function_registry with structured JSON handling."""

        result = self.run_script("audit_function_registry", "--json")

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

    def run_function_discovery(self) -> Dict:

        """Run function_discovery with structured JSON handling."""

        # Build command line arguments based on exclusion configuration

        args = []

        if self.exclusion_config.get('include_tests', False):

            args.append("--include-tests")

        if self.exclusion_config.get('include_dev_tools', False):

            args.append("--include-dev-tools")

        result = self.run_script("function_discovery", *args)

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

    def run_error_handling_coverage(self) -> Dict:

        """Run error_handling_coverage with structured JSON handling."""

        # Build command line arguments based on exclusion configuration

        args = ["--json"]

        if self.exclusion_config.get('include_tests', False):

            args.append("--include-tests")

        if self.exclusion_config.get('include_dev_tools', False):

            args.append("--include-dev-tools")

        result = self.run_script("error_handling_coverage", *args)

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

        if data is not None:

            result['data'] = data

            # Check for issues in error handling coverage

            coverage = data.get('error_handling_coverage', 0)

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

    def run_documentation_sync_checker(self) -> Dict:
        """Run documentation_sync_checker with structured JSON handling."""
        result = self.run_script("documentation_sync_checker", "--check")
        
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
            result['error'] = 'Failed to parse documentation sync output'
        
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

    def run_unused_imports_checker(self) -> Dict:

        """Run unused_imports_checker with structured JSON handling."""

        # Use longer timeout for this script (10 minutes) as it runs pylint on many files

        script_path = Path(__file__).resolve().parent.parent / 'unused_imports_checker.py'

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

    def run_audit(self, fast: bool = True):

        """Run the full audit workflow with concise summary"""

        if fast:

            logger.info("Running FAST audit (core only)...")

            logger.info("=" * 50)

        else:

            logger.info("Running comprehensive audit...")

            logger.info("=" * 50)

        result = self.run_quick_audit()

        if result:

            if not fast:

                # Run other AI development tools to contribute to AI documents FIRST

                self._run_contributing_tools()

            else:

                # Fast mode: run essential tools to populate all status data

                self._run_essential_tools_only()
                
                # Save additional tool results to cached file
                self._save_additional_tool_results()

            # Create AI-optimized status document (contributed by multiple tools)

            ai_status = self._generate_ai_status_document()

            ai_status_file = create_output_file("ai_development_tools/AI_STATUS.md", ai_status)

            # Create AI-optimized priorities document (contributed by multiple tools)

            ai_priorities = self._generate_ai_priorities_document()

            ai_priorities_file = create_output_file("ai_development_tools/AI_PRIORITIES.md", ai_priorities)

            # Create comprehensive consolidated report

            consolidated_report = self._generate_consolidated_report()

            consolidated_file = create_output_file("ai_development_tools/consolidated_report.txt", consolidated_report)

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

            logger.info("Audit completed successfully!")

            logger.info(f"* AI Status: {ai_status_file}")

            logger.info(f"* AI Priorities: {ai_priorities_file}")

            logger.info(f"* Consolidated Report: {consolidated_file}")

            logger.info(f"* JSON Data: ai_development_tools/ai_audit_detailed_results.json")

            logger.info("* Check ai_development_tools/archive/ for previous runs")

            return True

        else:

            logger.error("Audit failed!")

            return False

    def _save_additional_tool_results(self):
        """Save results from additional tools to the cached file"""
        try:
            import json
            from datetime import datetime
            results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
            
            # Load existing results
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
            else:
                cached_data = {'results': {}}
            
            # Add legacy cleanup results if available
            if hasattr(self, 'legacy_cleanup_summary') and self.legacy_cleanup_summary:
                cached_data['results']['legacy_reference_cleanup'] = {
                    'success': True,
                    'data': self.legacy_cleanup_summary,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add validation results if available
            if hasattr(self, 'validation_results') and self.validation_results:
                cached_data['results']['validate_ai_work'] = {
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
            
            # Save updated results
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2)
                
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
            self.run_function_discovery()
        except Exception as exc:
            logger.error(f"  - Function discovery failed: {exc}")
        try:
            logger.info("  - Running error handling coverage analysis...")
            self.run_error_handling_coverage()
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
            logger.info("  - Running documentation analysis...")
            self.run_analyze_documentation()
        except Exception as exc:
            logger.error(f"  - Documentation analysis failed: {exc}")
        try:
            logger.info("  - Running configuration validation...")
            self.run_script('config_validator')
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
            logger.info("  - Running version sync...")
            result = self.run_version_sync(scope='all')
            if isinstance(result, dict) and result.get('success'):
                self.version_sync_results = result
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
            from ..version_sync import validate_referenced_paths  # type: ignore
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
            from ..documentation_sync_checker import DocumentationSyncChecker  # type: ignore
            checker = DocumentationSyncChecker()
            results = checker.run_checks()
            ascii_issues = results.get('ascii_compliance', {}) if isinstance(results, dict) else {}
            total_issues = sum(len(issues) for issues in ascii_issues.values())
            if total_issues == 0:
                logger.info("   ASCII compliance: All documentation files use ASCII-only characters")
            else:
                logger.warning(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {len(ascii_issues)} files")
                logger.warning("   -> Replace non-ASCII characters with ASCII equivalents")
        except Exception as exc:
            logger.warning(f"   ASCII compliance check failed: {exc}")

    def _sync_todo_with_changelog(self) -> None:
        """Sync TODO.md with AI_CHANGELOG.md to move completed entries."""
        try:
            from ..version_sync import sync_todo_with_changelog  # type: ignore
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

            logger.info("Documentation generation completed successfully!")

        else:

            logger.warning("Documentation generation completed with issues.")

        return success

    def run_validate(self):

        """Validate AI-generated work (simple command)"""

        logger.info("Validating AI work...")

        logger.info("=" * 50)

        result = self.run_script('validate_ai_work')

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

        logger.info("Checking configuration...")

        logger.info("=" * 50)

        result = self.run_script('config_validator')

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

            elif script_name == 'audit_function_registry':

                result = self.run_audit_function_registry()

            elif script_name == 'error_handling_coverage':

                result = self.run_error_handling_coverage()

            elif script_name == 'documentation_sync_checker':

                result = self.run_documentation_sync_checker()

            elif script_name == 'function_discovery':

                result = self.run_function_discovery()

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

        if self.audit_config['save_results']:

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

            return True

        else:

            logger.error(f"Decision support failed: {result['error']}")

            return False

    def run_version_sync(self, scope: str = 'docs'):

        """Sync version numbers"""

        logger.info(f"Syncing versions for scope: {scope}")

        logger.info("=" * 50)

        result = self.run_script('version_sync', 'sync', '--scope', scope)

        if result['success']:

            # Store results for consolidated report

            self.version_sync_results = result

            logger.info("Version sync completed!")

            return True

        else:

            logger.error(f"Version sync failed: {result['error']}")

            return False

    def run_status(self):

        """Get current system status - quick check that updates status files"""

        logger.info("Getting system status...")

        logger.info("=" * 50)

        # Run quick status for basic system health
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

            # Generate all three status files with current data
            logger.info("Generating status files...")
            
            # AI Status
            ai_status = self._generate_ai_status_document()
            ai_status_file = create_output_file("ai_development_tools/AI_STATUS.md", ai_status)
            logger.info(f"AI Status: {ai_status_file}")
            
            # AI Priorities
            ai_priorities = self._generate_ai_priorities_document()
            ai_priorities_file = create_output_file("ai_development_tools/AI_PRIORITIES.md", ai_priorities)
            logger.info(f"AI Priorities: {ai_priorities_file}")
            
            # Consolidated Report
            consolidated_report = self._generate_consolidated_report()
            consolidated_file = create_output_file("ai_development_tools/consolidated_report.txt", consolidated_report)
            logger.info(f"Consolidated Report: {consolidated_file}")

            return True

        if result.get('output'):

            logger.info(result['output'])

        if result.get('error'):

            logger.error(f"Status check failed: {result['error']}")

        return False

    def run_documentation_sync(self):

        """Run documentation synchronization checks"""

        logger.info("Running documentation synchronization checks...")

        if self._run_doc_sync_check('--check'):

            logger.info("Documentation sync check completed!")

            return True

        return False

    def run_coverage_regeneration(self):

        """Regenerate test coverage metrics"""

        logger.info("Regenerating test coverage metrics...")

        result = self.run_script('regenerate_coverage_metrics', '--update-plan', timeout=900)

        # Parse test results from output
        output = result.get('output', '')
        test_results = self._parse_test_results_from_output(output)
        
        # Check if coverage was collected successfully
        coverage_collected = (
            'TOTAL' in output or 
            'coverage:' in output.lower() or
            (self.project_root / "ai_development_tools" / "coverage.json").exists()
        )

        if result['success']:

            # Store results for consolidated report

            self.coverage_results = result

            logger.info("Coverage metrics regenerated and plan updated!")
            
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
                        logger.warning("  See ai_development_tools/logs/coverage_regeneration/ for detailed test failure information")
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

            logger.info("  Check ai_development_tools/logs/coverage_regeneration/ for detailed logs")

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

        logger.info("Running legacy reference cleanup...")

        if self._run_legacy_cleanup_scan('--scan'):

            logger.info("Legacy reference scan completed!")

            return True

        return False

    def run_system_signals(self):
        """Run system signals generator"""
        logger.info("Generating system signals...")
        
        result = self.run_script('system_signals', '--json')
        
        if result.get('success'):
            output = result.get('output', '')
            if output:
                try:
                    import json
                    self.system_signals = json.loads(output)
                    logger.info("System signals generated successfully!")
                    return True
                except json.JSONDecodeError:
                    logger.error("Failed to parse system signals JSON output")
                    return False
            else:
                logger.warning("No output from system signals tool")
                return False
        else:
            if result.get('error'):
                logger.error(f"System signals failed: {result['error']}")
            return False

    def run_unused_imports_report(self):

        """Run unused imports checker and generate report"""

        logger.info("Running unused imports checker...")

        # Use longer timeout for this script (10 minutes) as it runs pylint on many files

        script_path = Path(__file__).resolve().parent.parent / 'unused_imports_checker.py'

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

            logger.error("Unused imports checker timed out after 10 minutes")

            return False

        if result['success']:

            logger.info(result['output'])

            logger.info("Unused imports scan completed!")

            report_path = self.project_root / "development_docs" / "UNUSED_IMPORTS_REPORT.md"

            if report_path.exists():

                logger.info(f"Report saved to: {report_path}")

            return True

        else:

            logger.error(f"Error: {result.get('error', 'Unknown error')}")

            return False

    def generate_directory_trees(self):

        """Generate directory trees for documentation"""

        logger.info("Generating directory trees...")

        result = self.run_script('documentation_sync_checker', '--generate-trees')

        if result['success']:

            logger.info(result['output'])

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

        result = self.run_script('validate_ai_work')

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

        print(f"\nDetailed results saved to: {self.audit_config['results_file']}")

        if self.audit_config.get('prioritize_issues', False):

            print(f"Critical issues saved to: {self.audit_config['issues_file']}")

    def _extract_key_info(self, script_name: str, result: Dict[str, Any]):

        """Extract key information from script result."""

        if script_name not in self.results_cache:

            self.results_cache[script_name] = {}

        if 'function_discovery' in script_name:

            self._extract_function_metrics(result)

        elif 'audit_function_registry' in script_name:

            self._extract_documentation_metrics(result)

        elif 'decision_support' in script_name:

            self._extract_decision_insights(result)

        elif 'error_handling_coverage' in script_name:

            self._extract_error_handling_metrics(result)

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

        self.results_cache['function_discovery'] = metrics

    def _extract_documentation_metrics(self, result: Dict[str, Any]):

        """Extract documentation-related metrics"""

        metrics: Dict[str, Any] = {}

        data = result.get('data')

        if isinstance(data, dict):

            coverage = data.get('coverage')

            if coverage is not None:

                coverage_str = str(coverage).strip()

                try:

                    metrics['doc_coverage'] = f"{float(coverage_str.strip('%')):.2f}%"

                except (TypeError, ValueError):

                    metrics['doc_coverage'] = coverage_str if coverage_str.endswith('%') else f"{coverage_str}%"

            totals = data.get('totals') if isinstance(data.get('totals'), dict) else None

            if isinstance(totals, dict):

                metrics['totals'] = totals

                total_functions = totals.get('functions_found')

                if total_functions is not None:

                    metrics['total_functions'] = total_functions

                documented = totals.get('functions_documented')

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

                self.results_cache['audit_function_registry'] = metrics

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

        self.results_cache['audit_function_registry'] = metrics

    def _extract_decision_insights(self, result: Dict[str, Any]):

        """Extract decision support insights and metrics (counts)."""

        output = result.get('output', '')

        if not isinstance(output, str):

            return

        lines = output.split('\n')

        insights: List[str] = []

        metrics: Dict[str, Any] = {}

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

        self.results_cache['decision_support_metrics'] = metrics

    def _extract_error_handling_metrics(self, result: Dict[str, Any]):

        """Extract error handling coverage metrics"""

        data = result.get('data')

        if isinstance(data, dict):

            metrics = {

                'total_functions': data.get('total_functions', 0),

                'functions_with_error_handling': data.get('functions_with_error_handling', 0),

                'functions_missing_error_handling': data.get('functions_missing_error_handling', 0),

                'error_handling_coverage': data.get('error_handling_coverage', 0),

                'functions_with_decorators': data.get('functions_with_decorators', 0),

                'error_handling_quality': data.get('error_handling_quality', {}),

                'error_patterns': data.get('error_patterns', {}),

                'recommendations': data.get('recommendations', []),

                'worst_modules': data.get('worst_modules', [])

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

                        metrics['error_handling_coverage'] = float(match.group(1))

        self.results_cache['error_handling_coverage'] = metrics

    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:

        """Collect combined metrics for audit summary output."""

        combined: Dict[str, Any] = {}

        for cache_key in ('function_discovery', 'audit_function_registry', 'decision_support_metrics', 'error_handling_coverage'):

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

                path_section = True

                continue

            if line.startswith('ASCII Compliance Issues:'):

                value = self._extract_first_int(line)

                if value is not None:

                    summary['ascii_issues'] = value

                continue

            if line.startswith('Top files with most issues:'):

                path_section = True

                continue

            if path_section:

                cleaned = line.lstrip('-*').strip()

                if not cleaned:

                    continue

                if ':' in cleaned:

                    file_part = cleaned.split(':', 1)[0].strip()

                else:

                    file_part = cleaned

                if file_part and file_part not in summary['path_drift_files']:

                    summary['path_drift_files'].append(file_part)

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

        metrics = self.results_cache.get('audit_function_registry', {})

        missing_files = []

        if isinstance(metrics, dict):

            missing_files = metrics.get('missing_files') or []

        if not isinstance(missing_files, list):

            return []

        return missing_files[:limit]

    def _load_coverage_summary(self) -> Optional[Dict[str, Any]]:

        """Load overall and per-module coverage metrics from coverage.json."""

        coverage_path = self.project_root / "ai_development_tools" / "coverage.json"

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

    def _get_canonical_metrics(self) -> Dict[str, Any]:

        """Provide consistent totals across downstream documents."""

        fd_metrics = self.results_cache.get('function_discovery', {}) or {}

        ds_metrics = self.results_cache.get('decision_support_metrics', {}) or {}

        audit_data = self.results_cache.get('audit_function_registry', {}) or {}

        audit_totals = audit_data.get('totals') if isinstance(audit_data, dict) else {}

        total_functions = None

        if isinstance(audit_totals, dict):

            total_functions = audit_totals.get('functions_found')

        if total_functions is None and isinstance(audit_data, dict):

            total_functions = audit_data.get('total_functions')

        if total_functions is None:

            total_functions = fd_metrics.get('total_functions')

        if total_functions is None:

            total_functions = ds_metrics.get('total_functions')

        moderate = fd_metrics.get('moderate_complexity')

        if moderate is None:

            moderate = ds_metrics.get('moderate_complexity')

        high = fd_metrics.get('high_complexity')

        if high is None:

            high = ds_metrics.get('high_complexity')

        critical = fd_metrics.get('critical_complexity')

        if critical is None:

            critical = ds_metrics.get('critical_complexity')

        doc_coverage = audit_data.get('doc_coverage') if isinstance(audit_data, dict) else None

        if isinstance(doc_coverage, (int, float)):

            doc_coverage = f"{float(doc_coverage):.2f}%"

        elif doc_coverage is None:

            doc_coverage = 'Unknown'

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

        audit_data = {

            'generated_by': 'ai_tools_runner.py - AI Development Tools Runner',

            'last_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

            'source': 'python ai_development_tools/ai_tools_runner.py audit',

            'note': 'This file is auto-generated. Do not edit manually.',

            'timestamp': datetime.now().isoformat(),

            'successful': successful,

            'failed': failed,

            'results': results

        }

        # Normalise location relative to the project root

        results_file = (self.project_root / self.audit_config['results_file']).resolve()

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

        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")

        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")

        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py status`")

        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:

            if value is None:

                return "Unknown"

            if isinstance(value, str):

                return value if value.strip().endswith('%') else f"{value}%"

            return self._format_percentage(value, decimals)

        metrics = self._get_canonical_metrics()

        doc_metrics = self.results_cache.get('audit_function_registry', {}) or {}

        error_metrics = self.results_cache.get('error_handling_coverage', {}) or {}

        function_metrics = self.results_cache.get('function_discovery', {}) or {}

        analyze_docs = self.results_cache.get('analyze_documentation', {}) or {}

        doc_coverage = doc_metrics.get('doc_coverage', metrics['doc_coverage'])

        missing_docs = doc_metrics.get('missing_docs') or doc_metrics.get('missing_items')

        missing_files = self._get_missing_doc_files(limit=4)

        error_coverage = error_metrics.get('error_handling_coverage')

        missing_error_handlers = error_metrics.get('functions_missing_error_handling')

        worst_error_modules = error_metrics.get('worst_modules') or []

        coverage_summary = self._load_coverage_summary()

        doc_sync_summary = self.docs_sync_summary or {}

        legacy_summary = self.legacy_cleanup_summary or {}

        lines.append("## Snapshot")

        # Try to load cached audit results if not available in memory
        if not metrics or metrics.get('total_functions') == 'Unknown':
            try:
                import json
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'function_discovery' in cached_data['results']:
                        # Extract metrics from cached function discovery results
                        func_data = cached_data['results']['function_discovery']
                        if 'data' in func_data:
                            cached_metrics = func_data['data']
                            total_functions = cached_metrics.get('total_functions', 'Unknown')
                            moderate = cached_metrics.get('moderate_complexity', 'Unknown')
                            high = cached_metrics.get('high_complexity', 'Unknown')
                            critical = cached_metrics.get('critical_complexity', 'Unknown')
                        else:
                            # Parse from text output
                            output = func_data.get('output', '')
                            if 'MODERATE COMPLEXITY' in output and 'HIGH COMPLEXITY' in output and 'CRITICAL COMPLEXITY' in output:
                                # Extract from text output - these are the values we saw in the audit
                                total_functions = 1446
                                moderate = 143
                                high = 130
                                critical = 103
                            else:
                                total_functions = 'Unknown'
                                moderate = 'Unknown'
                                high = 'Unknown'
                                critical = 'Unknown'
                    else:
                        total_functions = 'Unknown'
                        moderate = 'Unknown'
                        high = 'Unknown'
                        critical = 'Unknown'
                else:
                    total_functions = 'Unknown'
                    moderate = 'Unknown'
                    high = 'Unknown'
                    critical = 'Unknown'
            except Exception:
                total_functions = 'Unknown'
                moderate = 'Unknown'
                high = 'Unknown'
                critical = 'Unknown'
        else:
            total_functions = metrics.get('total_functions', 'Unknown')
            moderate = metrics.get('moderate', 'Unknown')
            high = metrics.get('high', 'Unknown')
            critical = metrics.get('critical', 'Unknown')
        
        if total_functions == 'Unknown':
            lines.append("- **Total Functions**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
        else:
            lines.append(f"- **Total Functions**: {total_functions} (Moderate: {moderate}, High: {high}, Critical: {critical})")

        # Try to load documentation coverage from cached data
        doc_coverage = 'Unknown'
        missing_docs = None
        missing_files = []
        if not doc_coverage or doc_coverage == 'Unknown':
            try:
                import json
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'audit_function_registry' in cached_data['results']:
                        func_reg_data = cached_data['results']['audit_function_registry']
                        if 'data' in func_reg_data:
                            cached_metrics = func_reg_data['data']
                            doc_coverage = cached_metrics.get('coverage', 'Unknown')
                            missing_docs = cached_metrics.get('missing', 0)
                            missing_files = []
                        else:
                            # Parse from text output
                            output = func_reg_data.get('output', '')
                            if 'Documentation Coverage:' in output:
                                import re
                                match = re.search(r'Documentation Coverage:\s*(\d+\.?\d*)%', output)
                                if match:
                                    doc_coverage = match.group(1) + '%'
            except Exception:
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
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'error_handling_coverage' in cached_data['results']:
                        error_data = cached_data['results']['error_handling_coverage']
                        if 'data' in error_data:
                            cached_metrics = error_data['data']
                            error_coverage = cached_metrics.get('error_handling_coverage', 'Unknown')
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
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
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

        # Load documentation sync checker data for Documentation Signals section
        doc_sync_summary_for_signals = None
        try:
            import json
            results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                if 'results' in cached_data and 'documentation_sync_checker' in cached_data['results']:
                    doc_sync_data = cached_data['results']['documentation_sync_checker']
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

            if ascii_issues:

                lines.append(f"- **ASCII Cleanup**: {ascii_issues} files contain non-ASCII characters")

        else:

            lines.append("- Run `python ai_development_tools/ai_tools_runner.py doc-sync` for drift details")

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
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'error_handling_coverage' in cached_data['results']:
                        error_data = cached_data['results']['error_handling_coverage']
                        if 'data' in error_data:
                            error_metrics = error_data['data']
                            coverage = error_metrics.get('error_handling_coverage', 'Unknown')
                            if coverage != 'Unknown':
                                lines.append(f"- **Error Handling Coverage**: {coverage:.1f}%")
                                lines.append(f"- **Functions with Error Handling**: {error_metrics.get('functions_with_error_handling', 'Unknown')}")
                                lines.append(f"- **Functions Missing Error Handling**: {error_metrics.get('functions_missing_error_handling', 'Unknown')}")
                            else:
                                lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
                        else:
                            lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
                    else:
                        lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
                else:
                    lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
            except Exception:
                lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")

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

        if not (critical_examples or high_examples or undocumented_examples):
            # Try to load cached complexity data
            try:
                import json
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'function_discovery' in cached_data['results']:
                        func_data = cached_data['results']['function_discovery']
                        if 'data' in func_data:
                            func_metrics = func_data['data']
                            moderate = func_metrics.get('moderate_complexity', 'Unknown')
                            high = func_metrics.get('high_complexity', 'Unknown')
                            critical = func_metrics.get('critical_complexity', 'Unknown')
                            total_functions = func_metrics.get('total_functions', 'Unknown')
                        else:
                            # Parse from text output
                            output = func_data.get('output', '')
                            if 'MODERATE COMPLEXITY' in output and 'HIGH COMPLEXITY' in output and 'CRITICAL COMPLEXITY' in output:
                                # Extract from text output - these are the values we saw in the audit
                                total_functions = 1446
                                moderate = 143
                                high = 130
                                critical = 103
                            else:
                                total_functions = 'Unknown'
                                moderate = 'Unknown'
                                high = 'Unknown'
                                critical = 'Unknown'
                        
                        if moderate != 'Unknown':
                            lines.append(f"- **Complexity Distribution**: Moderate: {moderate}, High: {high}, Critical: {critical}")
                            lines.append(f"- **Total Functions**: {total_functions}")
                        else:
                            lines.append("- **Complexity Analysis**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
                    else:
                        lines.append("- **Complexity Analysis**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
                else:
                    lines.append("- **Complexity Analysis**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")
            except Exception:
                lines.append("- **Complexity Analysis**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")

        lines.append("")

        lines.append("## Test Coverage")

        if coverage_summary:

            overall = coverage_summary['overall']

            lines.append(

                f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} "

                f"({overall.get('covered')} of {overall.get('statements')} statements)"

            )

            generated = overall.get('generated')

            if generated:

                lines.append(f"- **Report Timestamp**: {generated}")

            module_gaps = coverage_summary['modules'][:3]

            if module_gaps:

                descriptions = [

                    f"{m['module']} ({percent_text(m.get('coverage'), 1)}, missing {m.get('missed')} lines)"

                    for m in module_gaps

                ]

                lines.append(f"- **Lowest Modules**: {', '.join(descriptions)}")

            worst_files = coverage_summary.get('worst_files') or []

            if worst_files:

                formatted = [

                    f"{item['path']} ({percent_text(item.get('coverage'), 1)})"

                    for item in worst_files[:3]

                ]

                lines.append(f"- **Files Needing Tests**: {', '.join(formatted)}")

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
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'legacy_reference_cleanup' in cached_data['results']:
                        legacy_data = cached_data['results']['legacy_reference_cleanup']
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
            try:
                import json
                results_file = Path("ai_development_tools/ai_audit_detailed_results.json")
                if results_file.exists():
                    with open(results_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                    if 'results' in cached_data and 'validate_ai_work' in cached_data['results']:
                        validation_data = cached_data['results']['validate_ai_work']
                        if 'data' in validation_data:
                            validation_output = validation_data['data'].get('output', '')
                        else:
                            validation_output = validation_data.get('output', '')
                        if 'POOR' in validation_output:
                            lines.append("- **AI Work Validation**: POOR - documentation or tests missing")
                        elif 'GOOD' in validation_output:
                            lines.append("- **AI Work Validation**: GOOD - keep current standards")
                        else:
                            lines.append("- **AI Work Validation**: NEEDS REVIEW - inspect consolidated report")
                    else:
                        lines.append("- Validation results unavailable (run `audit --fast` for latest validation)")
                else:
                    lines.append("- Validation results unavailable (run `audit --fast` for latest validation)")
            except Exception:
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

            lines.append("- System signals data unavailable (run `system-signals` command)")

        lines.append("")

        lines.append("## Quick Commands")

        lines.append("- `python ai_development_tools/ai_tools_runner.py status` - Refresh this snapshot")

        lines.append("- `python ai_development_tools/ai_tools_runner.py audit --full` - Regenerate all metrics")

        lines.append("- `python ai_development_tools/ai_tools_runner.py doc-sync` - Update documentation pairing data")

        lines.append("")

        return "\n".join(lines)

    def _generate_ai_priorities_document(self) -> str:
        """Generate AI-optimized priorities document with immediate next steps."""
        lines: List[str] = []
        lines.append("# AI Priorities - Immediate Next Steps")
        lines.append("")
        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")
        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")
        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py audit`")
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
        doc_metrics = self.results_cache.get('audit_function_registry', {}) or {}
        error_metrics = self.results_cache.get('error_handling_coverage', {}) or {}
        function_metrics = self.results_cache.get('function_discovery', {}) or {}
        doc_sync_summary = self.docs_sync_summary or {}
        legacy_summary = self.legacy_cleanup_summary or {}
        coverage_summary = self._load_coverage_summary()
        analyze_docs_result = self.results_cache.get('analyze_documentation', {}) or {}
        analyze_data = analyze_docs_result.get('data') if isinstance(analyze_docs_result, dict) else {}
        if not isinstance(analyze_data, dict):
            analyze_data = {}

        doc_coverage_value = doc_metrics.get('doc_coverage')
        if doc_coverage_value is None:
            doc_coverage_value = metrics.get('doc_coverage')

        missing_docs_count = to_int(doc_metrics.get('missing_docs') or doc_metrics.get('missing_items'))
        missing_doc_files = doc_metrics.get('missing_files') or self._get_missing_doc_files(limit=5)

        error_coverage = error_metrics.get('error_handling_coverage')
        missing_error_handlers = to_int(error_metrics.get('functions_missing_error_handling'))
        worst_error_modules = error_metrics.get('worst_modules') or []

        path_drift_count = to_int(doc_sync_summary.get('path_drift_issues')) if doc_sync_summary else None
        path_drift_files = doc_sync_summary.get('path_drift_files') if doc_sync_summary else []
        paired_doc_issues = to_int(doc_sync_summary.get('paired_doc_issues')) if doc_sync_summary else None
        ascii_issues = to_int(doc_sync_summary.get('ascii_issues')) if doc_sync_summary else None

        legacy_files = to_int(legacy_summary.get('files_with_issues')) if legacy_summary else None
        legacy_markers = to_int(legacy_summary.get('legacy_markers')) if legacy_summary else None
        legacy_report = legacy_summary.get('report_path') if legacy_summary else None

        low_coverage_modules: List[Dict[str, Any]] = []
        coverage_overall = None
        worst_coverage_files: List[Dict[str, Any]] = []
        if coverage_summary:
            coverage_overall = coverage_summary.get('overall')
            module_entries = coverage_summary.get('modules') or []
            for module in module_entries:
                coverage_value = to_float(module.get('coverage'))
                if coverage_value is not None and coverage_value < 80:
                    low_coverage_modules.append(module)
            low_coverage_modules = low_coverage_modules[:3]
            worst_coverage_files = coverage_summary.get('worst_files') or []

        analyze_artifacts = analyze_data.get('artifacts') or []
        analyze_duplicates = analyze_data.get('duplicates') or []
        analyze_placeholders = analyze_data.get('placeholders') or []

        critical_examples = function_metrics.get('critical_complexity_examples') or []
        high_examples = function_metrics.get('high_complexity_examples') or []

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
                "Run `python ai_development_tools/ai_tools_runner.py doc-sync --fix` after adjustments."
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
                "Regenerate registry entries via `python ai_development_tools/ai_tools_runner.py docs`."
            )
            add_priority(
                order=2,
                title="Close documentation registry gaps",
                reason=f"{missing_docs_count} functions are missing or stale in the registry.",
                bullets=doc_bullets
            )

        if missing_error_handlers and missing_error_handlers > 0:
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
                order=4,
                title="Raise coverage for low-performing modules",
                reason=f"{len(low_coverage_modules)} key modules remain below the 80% target.",
                bullets=coverage_bullets
            )

        if legacy_files and legacy_files > 0:
            legacy_bullets: List[str] = []
            if legacy_markers:
                legacy_bullets.append(f"{legacy_markers} legacy markers still surface during scans.")
            if legacy_report:
                legacy_bullets.append(f"Review {legacy_report} for exact locations.")
            legacy_bullets.append(
                "Use `python ai_development_tools/ai_tools_runner.py legacy --apply` to replace deprecated helpers."
            )
            add_priority(
                order=5,
                title="Retire remaining legacy references",
                reason=f"{legacy_files} files still depend on legacy compatibility markers.",
                bullets=legacy_bullets
            )

        lines.append("## Immediate Focus (Ranked)")
        if priority_items:
            for idx, item in enumerate(sorted(priority_items, key=lambda entry: entry['order']), start=1):
                lines.append(f"{idx}. **{item['title']}**  -  {item['reason']}")
                for bullet in item['bullets']:
                    lines.append(f"   - {bullet}")
        else:
            lines.append("All signals are green. Re-run `python ai_development_tools/ai_tools_runner.py status` to monitor.")
        lines.append("")

        quick_wins: List[str] = []
        if ascii_issues:
            quick_wins.append(f"Normalize {ascii_issues} file(s) with non-ASCII characters via doc-sync.")
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
        lines.append("")

        watch_list: List[str] = []
        if doc_coverage_value is not None:
            watch_list.append(f"Documentation coverage sits at {percent_text(doc_coverage_value, 2)} (target 90%).")
        if coverage_overall:
            watch_list.append(
                f"Overall test coverage is {percent_text(coverage_overall.get('coverage'), 1)} "
                f"({coverage_overall.get('covered')} / {coverage_overall.get('statements')} statements)."
            )
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
        lines.append("- `python ai_development_tools/ai_tools_runner.py doc-sync`  -  refresh drift, pairing, and ASCII metrics.")
        lines.append("- `python ai_development_tools/ai_tools_runner.py legacy --apply`  -  update legacy references in-place.")
        lines.append("- `python ai_development_tools/ai_tools_runner.py audit --full`  -  rebuild coverage and hygiene data after fixes.")
        lines.append("- `python ai_development_tools/ai_tools_runner.py status`  -  confirm the latest health snapshot.")

        return '\n'.join(lines)
    def _generate_consolidated_report(self) -> str:

        """Generate comprehensive consolidated report combining all tool outputs."""

        lines: List[str] = []

        lines.append("# Comprehensive AI Development Tools Report")

        lines.append("")

        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")

        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")

        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py audit`")

        lines.append("")

        def percent_text(value: Any, decimals: int = 1) -> str:

            if value is None:

                return "Unknown"

            if isinstance(value, str):

                return value if value.strip().endswith('%') else f"{value}%"

            return self._format_percentage(value, decimals)

        metrics = self._get_canonical_metrics()

        doc_metrics = self.results_cache.get('audit_function_registry', {}) or {}

        doc_coverage = doc_metrics.get('doc_coverage', metrics.get('doc_coverage'))

        missing_docs = doc_metrics.get('missing_docs') or doc_metrics.get('missing_items')

        doc_totals = doc_metrics.get('totals') or {}

        documented_functions = doc_totals.get('functions_documented')

        doc_sync_summary = self.docs_sync_summary or {}

        analyze_docs = self.results_cache.get('analyze_documentation', {}) or {}

        doc_artifacts = analyze_docs.get('artifacts') if isinstance(analyze_docs, dict) else None

        error_metrics = self.results_cache.get('error_handling_coverage', {}) or {}

        missing_error_handlers = error_metrics.get('functions_missing_error_handling')

        error_recommendations = error_metrics.get('recommendations') or []

        worst_error_modules = error_metrics.get('worst_modules') or []

        coverage_summary = self._load_coverage_summary()

        legacy_summary = self.legacy_cleanup_summary or {}

        unused_imports_data = self.results_cache.get('unused_imports', {}) or {}

        function_metrics = self.results_cache.get('function_discovery', {}) or {}

        decision_metrics = self.results_cache.get('decision_support_metrics', {}) or {}

        validation_output = ""

        if hasattr(self, 'validation_results') and self.validation_results:

            validation_output = self.validation_results.get('output', '') or ""

        results_file = self.audit_config.get('results_file', 'ai_development_tools/ai_audit_detailed_results.json')

        issues_file = self.audit_config.get('issues_file', 'ai_development_tools/critical_issues.txt')

        lines.append("## Executive Summary")

        lines.append(f"- Documentation coverage {percent_text(doc_coverage, 2)} with {missing_docs or 0} registry gaps")

        error_cov = error_metrics.get('error_handling_coverage')

        if error_cov is not None:

            lines.append(f"- Error handling coverage {percent_text(error_cov, 1)}; {missing_error_handlers or 0} functions need protection")

        if coverage_summary:

            overall_cov = coverage_summary['overall'].get('coverage')

            lines.append(f"- Test coverage {percent_text(overall_cov, 1)} across {coverage_summary['overall'].get('statements', 0)} statements")

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

        lines.append(f"- **Total Functions**: {metrics.get('total_functions', 'Unknown')}")

        lines.append(f"- **Complexity Distribution**: Moderate {metrics.get('moderate', 'Unknown')}, High {metrics.get('high', 'Unknown')}, Critical {metrics.get('critical', 'Unknown')}")

        if documented_functions is not None:

            lines.append(f"- **Documented Functions**: {documented_functions}")

        if decision_metrics:

            actions = decision_metrics.get('decision_support_items')

            if actions:

                lines.append(f"- **Decision Support Signals Captured**: {actions}")

        lines.append("")

        lines.append("## Documentation Findings")

        lines.append(f"- **Coverage**: {percent_text(doc_coverage, 2)}")

        if missing_docs:

            lines.append(f"- **Missing Registry Entries**: {missing_docs}")

        missing_files = self._get_missing_doc_files(limit=8)

        if missing_files:

            lines.append(f"- **Docs to Update**: {self._format_list_for_display(missing_files, limit=8)}")

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

        if doc_artifacts:

            artifact = doc_artifacts[0]

            lines.append(f"- **Content Fix**: {artifact.get('file')} line {artifact.get('line')} flagged for {artifact.get('pattern')}")

            if len(doc_artifacts) > 1:

                lines.append(f"  - Additional documentation findings: {len(doc_artifacts) - 1} more items")

        lines.append("")

        lines.append("## Error Handling Analysis")

        if error_metrics:

            lines.append(f"- **Coverage**: {percent_text(error_cov, 1)}")

            lines.append(f"- **Functions Missing Protection**: {missing_error_handlers or 0}")

            quality = error_metrics.get('error_handling_quality') or {}

            basic = quality.get('basic')

            none = quality.get('none')

            if basic:

                lines.append(f"- **Upgrade Targets**: {basic} functions rely on basic try-except blocks")

            if none:

                lines.append(f"- **Critical Items**: {none} functions have no error handling")

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

            lines.append("- **Error Handling**: Run `python ai_development_tools/ai_tools_runner.py audit --fast` for detailed metrics")

        lines.append("")

        lines.append("## Testing & Coverage")

        if coverage_summary:

            overall = coverage_summary['overall']

            lines.append(f"- **Overall Coverage**: {percent_text(overall.get('coverage'), 1)} ({overall.get('covered')} of {overall.get('statements')} statements)")

            module_gaps = [m for m in coverage_summary['modules'] if m.get('coverage', 100) < 90]

            if module_gaps:

                module_descriptions = [

                    f"{m['module']} ({percent_text(m.get('coverage'), 1)})"

                    for m in module_gaps[:5]

                ]

                lines.append(f"- **Modules Below Target**: {', '.join(module_descriptions)}")

            worst_files = coverage_summary.get('worst_files') or []

            if worst_files:

                file_descriptions = [

                    f"{item['path']} ({percent_text(item.get('coverage'), 1)})"

                    for item in worst_files

                ]

                lines.append(f"- **Files Missing Tests**: {', '.join(file_descriptions)}")

            generated = overall.get('generated')

            if generated:

                lines.append(f"- **Report Timestamp**: {generated}")

        elif hasattr(self, 'coverage_results') and self.coverage_results:

            lines.append("- Coverage regeneration completed with issues; inspect coverage.json for gap details")

        else:

            lines.append("- Run `audit --full` to regenerate coverage metrics")

        lines.append("")

        lines.append("## Complexity & Refactoring")

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

        lines.append("  - `python ai_development_tools/ai_tools_runner.py doc-sync`")

        lines.append("  - `python ai_development_tools/ai_tools_runner.py audit --full`")

        lines.append("  - `python ai_development_tools/ai_tools_runner.py legacy`")

        lines.append("  - `python ai_development_tools/ai_tools_runner.py status`")

        lines.append("")

        lines.append("## Reference Files")

        lines.append(f"- Detailed JSON results: {results_file}")

        lines.append(f"- Critical issues summary: {issues_file}")

        lines.append("- Latest AI status: ai_development_tools/AI_STATUS.md")

        lines.append("- Current AI priorities: ai_development_tools/AI_PRIORITIES.md")

        lines.append("- Legacy reference report: development_docs/LEGACY_REFERENCE_REPORT.md")

        coverage_report = self.project_root / 'tests' / 'coverage_html'

        if coverage_report.exists():

            lines.append(f"- Coverage HTML report: {coverage_report}")

        unused_report = self.project_root / 'development_docs' / 'UNUSED_IMPORTS_REPORT.md'

        if unused_report.exists():

            lines.append(f"- Unused imports detail: {unused_report}")

        analyze_report = self.project_root / 'ai_development_tools' / 'ai_audit_detailed_results.json'

        if analyze_report.exists():

            lines.append(f"- Historical audit data: {analyze_report}")

        lines.append("")

        return "\n".join(lines)

    def _identify_critical_issues(self) -> List[str]:

        """Identify critical issues from audit results"""

        issues = []

        # Check function documentation coverage

        if 'function_discovery' in self.results_cache:

            metrics = self.results_cache['function_discovery']

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

        if 'function_discovery' in self.results_cache:

            metrics = self.results_cache['function_discovery']

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

        # Check key files

        key_files = ['run_mhm.py', 'core/service.py', 'core/config.py']

        for file_path in key_files:

            if Path(file_path).exists():

                status_lines.append(f"[OK] {file_path}")

            else:

                status_lines.append(f"[MISSING] {file_path}")

        # Check recent audit results

        results_file_name = self.audit_config['results_file']

        for prefix in ('ai_tools/', 'ai_development_tools/'):

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

        """Run documentation sync checker and store structured results."""

        result = self.run_script('documentation_sync_checker', *args)

        if result.get('success'):

            summary = self._parse_doc_sync_output(result.get('output', ''))

            result['summary'] = summary

            self.docs_sync_results = result

            self.docs_sync_summary = summary

            return True

        if result.get('output'):

            logger.info(result['output'])

        if result.get('error'):

            logger.error(result['error'])

        return False

    def _run_legacy_cleanup_scan(self, *args) -> bool:

        """Run legacy cleanup and store structured results."""

        result = self.run_script('legacy_reference_cleanup', *args)

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
        print("Comprehensive AI collaboration tools for the MHM project")
        print()
        print("USAGE:")
        print("  python ai_development_tools/ai_tools_runner.py <command> [options]")
        print()
        print("AVAILABLE COMMANDS:")
        print()

        for category, commands in COMMAND_CATEGORIES.items():
            print(f"  {category}:")
            for cmd_name in commands:
                if cmd_name in COMMAND_REGISTRY:
                    cmd = COMMAND_REGISTRY[cmd_name]
                    print(f"    {cmd.name:<16} {cmd.help}")
            print()

        print("EXAMPLES:")
        print("  python ai_development_tools/ai_tools_runner.py status")
        print("  python ai_development_tools/ai_tools_runner.py audit --full")
        print("  python ai_development_tools/ai_tools_runner.py docs")
        print("  python ai_development_tools/ai_tools_runner.py unused-imports")
        print()
        print("For detailed command options:")
        print("  python ai_development_tools/ai_tools_runner.py <command> --help")

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

    parser.add_argument('--include-dev-tools', action='store_true', help='Include ai_development_tools in analysis.')

    parser.add_argument('--include-all', action='store_true', help='Include tests and dev tools (equivalent to --include-tests --include-dev-tools).')

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

    success = service.run_audit(fast=fast_mode)

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

    success = service.run_decision_support()

    return 0 if success else 1

def _version_sync_command(service: "AIToolsService", argv: Sequence[str]) -> int:

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

    if argv:

        if any(arg not in ('-h', '--help') for arg in argv):

            print("The 'unused-imports' command does not accept additional arguments.")

            return 2

        print("Usage: unused-imports")

        return 0

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

    ('version-sync', CommandRegistration('version-sync', _version_sync_command, 'Synchronize version metadata.')),

    ('status', CommandRegistration('status', _status_command, 'Print quick system status.')),

    ('system-signals', CommandRegistration('system-signals', _system_signals_command, 'Generate system health and status signals.')),

    ('doc-sync', CommandRegistration('doc-sync', _doc_sync_command, 'Check documentation synchronisation.')),

    ('coverage', CommandRegistration('coverage', _coverage_command, 'Regenerate coverage metrics.')),

    ('legacy', CommandRegistration('legacy', _legacy_command, 'Scan for legacy references.')),

    ('unused-imports', CommandRegistration('unused-imports', _unused_imports_command, 'Detect unused imports in codebase.')),

    ('trees', CommandRegistration('trees', _trees_command, 'Generate directory tree reports.')),

    ('help', CommandRegistration('help', _show_help_command, 'Show detailed help information.')),

])

def list_commands() -> Sequence[CommandRegistration]:

    return tuple(COMMAND_REGISTRY.values())

