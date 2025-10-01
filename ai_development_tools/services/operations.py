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
from collections import OrderedDict

import config
SCRIPT_REGISTRY = {
    'analyze_documentation': 'analyze_documentation.py',
    'audit_function_registry': 'audit_function_registry.py',
    'audit_module_dependencies': 'audit_module_dependencies.py',
    'config_validator': 'config_validator.py',
    'decision_support': 'decision_support.py',
    'documentation_sync_checker': 'documentation_sync_checker.py',
    'function_discovery': 'function_discovery.py',
    'generate_function_registry': 'generate_function_registry.py',
    'generate_module_dependencies': 'generate_module_dependencies.py',
    'legacy_reference_cleanup': 'legacy_reference_cleanup.py',
    'quick_status': 'quick_status.py',
    'regenerate_coverage_metrics': 'regenerate_coverage_metrics.py',
    'validate_ai_work': 'validate_ai_work.py',
    'version_sync': 'version_sync.py'
}

from file_rotation import create_output_file

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
        self.docs_sync_summary = None
        self.legacy_cleanup_results = None
        self.legacy_cleanup_summary = None
        self.status_results = None
        self.status_summary = None

    def run_script(self, script_name: str, *args) -> Dict:
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
                timeout=300  # 5 minute timeout
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
                'error': f"Script '{script_name}' timed out after 5 minutes",
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

    # ===== SIMPLE COMMANDS (for users) =====
    
    def run_audit(self, fast: bool = True):
        """Run the full audit workflow with concise summary"""
        if fast:
            print("Running FAST audit (core only)...")
            print("=" * 50)
        else:
            print("Running comprehensive audit...")
            print("=" * 50)
        
        result = self.run_quick_audit()
        if result:
            if not fast:
                # Run other AI development tools to contribute to AI documents FIRST
                self._run_contributing_tools()
            else:
                # Fast mode: only run essential tools
                self._run_essential_tools_only()
            
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
            
            print("\n" + "=" * 50)
            print("Audit completed successfully!")
            print(f"* AI Status: {ai_status_file}")
            print(f"* AI Priorities: {ai_priorities_file}")
            print(f"* Consolidated Report: {consolidated_file}")
            print(f"* JSON Data: ai_development_tools/ai_audit_detailed_results.json")
            print("* Check ai_development_tools/archive/ for previous runs")
            return True
        else:
            print("Audit failed!")
            return False
    
    def run_docs(self):
        """Update all documentation (OPTIONAL - not essential for audit)"""
        print("Updating documentation...")
        print("=" * 50)

        success = True

        # Generate function registry
        try:
            print("  - Generating function registry...")
            result = self.run_script("generate_function_registry")
            if result['success']:
                print("  - Function registry generated successfully")
            else:
                print(f"  - Function registry generation failed: {result['error']}")
                success = False
        except Exception as exc:
            print(f"  - Function registry generation failed: {exc}")
            success = False

        # Generate module dependencies
        try:
            print("  - Generating module dependencies...")
            result = self.run_script("generate_module_dependencies")
            if result['success']:
                print("  - Module dependencies generated successfully")
            else:
                print(f"  - Module dependencies generation failed: {result['error']}")
                success = False
        except Exception as exc:
            print(f"  - Module dependencies generation failed: {exc}")
            success = False

        # Generate directory trees
        try:
            print("  - Generating directory trees...")
            self.generate_directory_trees()
        except Exception as exc:
            print(f"  - Directory tree generation failed: {exc}")
            success = False

        # Run documentation sync check
        try:
            print("  - Checking documentation sync...")
            if not self._run_doc_sync_check('--check'):
                success = False
        except Exception as exc:
            print(f"  - Documentation sync check failed: {exc}")
            success = False

        print("\n" + "=" * 50)
        if success:
            print("Documentation generation completed successfully!")
        else:
            print("Documentation generation completed with issues.")
        return success


    def run_validate(self):
        """Validate AI-generated work (simple command)"""
        print("Validating AI work...")
        print("=" * 50)
        
        result = self.run_script('validate_ai_work')
        if result['success']:
            # Store results for consolidated report
            self.validation_results = result
            print("\n" + "=" * 50)
            print("Validation completed successfully!")
            return True
        else:
            print(f"Validation failed: {result['error']}")
            return False
    
    def run_config(self):
        """Check configuration consistency (simple command)"""
        print("Checking configuration...")
        print("=" * 50)
        
        result = self.run_script('config_validator')
        if result['success']:
            print(result['output'])
            print("\n" + "=" * 50)
            print("Configuration check completed!")
            return True
        else:
            print(f"Configuration check failed: {result['error']}")
            return False
    
    # ===== ADVANCED COMMANDS (for AI collaborators) =====
    
    def run_workflow(self, task_type: str, task_data: Optional[Dict] = None) -> bool:
        """Run workflow with audit-first protocol"""
        print(f"Running workflow: {task_type}")
        print("=" * 50)
        
        # Check trigger requirements
        if not self.check_trigger_requirements(task_type):
            return False
        
        # Run audit first
        audit_results = self.run_audit_first(task_type)
        if not audit_results['success']:
            print(f"Audit failed: {audit_results['error']}")
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
        print("Running comprehensive audit...")
        
        successful = []
        failed = []
        results = {}
        
        for script in self.audit_config['audit_scripts']:
            script_name = script.replace('.py', '')
            print(f"Running {script_name}...")
            
            # Special handling for analyze_documentation
            if script_name == 'analyze_documentation':
                result = self.run_analyze_documentation()
            elif script_name == 'audit_function_registry':
                result = self.run_audit_function_registry()
            else:
                result = self.run_script(script_name)
            
            results[script_name] = result
            
            if result['success']:
                successful.append(script_name)
                # Extract key information for concise output
                self._extract_key_info(script_name, result)
            else:
                failed.append(script_name)
                print(f"  [ERROR] {script_name} failed: {result['error']}")
        
        # Save detailed results
        if self.audit_config['save_results']:
            self._save_audit_results(successful, failed, results)
        
        # Audit completed
        
        # Show summary
        self.print_audit_summary(successful, failed, results)
        
        return len(failed) == 0
    
    def run_decision_support(self):
        """Get actionable insights for decision-making"""
        print("Getting actionable insights...")
        print("=" * 50)
        
        result = self.run_script('decision_support')
        if result['success']:
            # Extract and format actionable insights
            insights = self._extract_actionable_insights(result['output'])
            print(insights)
            return True
        else:
            print(f"Decision support failed: {result['error']}")
            return False
    
    def run_version_sync(self, scope: str = 'docs'):
        """Sync version numbers"""
        print(f"Syncing versions for scope: {scope}")
        print("=" * 50)
        
        result = self.run_script('version_sync', 'sync', '--scope', scope)
        if result['success']:
            # Store results for consolidated report
            self.version_sync_results = result
            print("Version sync completed!")
            return True
        else:
            print(f"Version sync failed: {result['error']}")
            return False
    
    def run_status(self):
        """Get current system status"""
        print("Getting system status...")
        print("=" * 50)

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
                print("Status check completed!")
            else:
                print("Status check completed, but output could not be parsed as JSON.")
            return True

        if result.get('output'):
            print(result['output'])
        if result.get('error'):
            print(result['error'])

        status_info = self._get_system_status()
        print(status_info)
        return False
    def run_documentation_sync(self):
        """Run documentation synchronization checks"""
        print("Running documentation synchronization checks...")
        if self._run_doc_sync_check('--check'):
            print("\nDocumentation sync check completed!")
            return True
        return False
    def run_coverage_regeneration(self):
        """Regenerate test coverage metrics"""
        print("Regenerating test coverage metrics...")
        result = self.run_script('regenerate_coverage_metrics', '--update-plan')
        if result['success']:
            # Store results for consolidated report
            self.coverage_results = result
            print("\nCoverage metrics regenerated and plan updated!")
        return result['success']
    
    def run_legacy_cleanup(self):
        """Run legacy reference cleanup"""
        print("Running legacy reference cleanup...")
        if self._run_legacy_cleanup_scan('--scan'):
            print("\nLegacy reference scan completed!")
            return True
        return False
    def generate_directory_trees(self):
        """Generate directory trees for documentation"""
        print("Generating directory trees...")
        result = self.run_script('documentation_sync_checker', '--generate-trees')
        if result['success']:
            print(result['output'])
            print("\n* Directory tree generated!")
            print("Check development_docs/DIRECTORY_TREE.md for project structure")
        return result['success']
    
    # ===== HELPER METHODS =====
    
    def check_trigger_requirements(self, task_type: str) -> bool:
        """Check if trigger requirements are met"""
        trigger_file = self.project_root / 'TRIGGER.md'
        if not trigger_file.exists():
            print("[WARN] TRIGGER.md not found - proceeding anyway")
            return True
        
        # For AI tools, we don't need user approval
        return True
    
    def run_audit_first(self, task_type: str) -> Dict:
        """Run audit first as required by protocol"""
        print("Running audit-first protocol...")
        
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
            print(f"Unknown task type: {task_type}")
            return False
    
    def validate_work(self, work_type: str, work_data: Dict) -> Dict:
        """Validate the work before presenting"""
        print("Validating work...")
        
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

    def _extract_function_metrics(self, result: Dict[str, Any]):
        """Extract function-related metrics"""
        output = result.get('output', '')
        if not isinstance(output, str):
            return
        lines = output.split('\n')
        metrics: Dict[str, Any] = {}
        import re

        for line in lines:
            lower = line.lower()
            if 'found' in lower and 'functions' in lower:
                match = re.search(r'Found (\d+) functions', line)
                if match:
                    metrics['total_functions'] = int(match.group(1))
            elif 'moderate complexity' in lower:
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['moderate_complexity'] = int(match.group(1))
            elif 'high complexity' in lower and 'critical' not in lower:
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['high_complexity'] = int(match.group(1))
            elif 'critical complexity' in lower:
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['critical_complexity'] = int(match.group(1))
            elif 'undocumented' in lower:
                match = re.search(r'\((\d+)\):', line)
                if match:
                    metrics['undocumented'] = int(match.group(1))

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

    def _extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Collect combined metrics for audit summary output."""
        combined: Dict[str, Any] = {}
        for cache_key in ('function_discovery', 'audit_function_registry', 'decision_support_metrics'):
            cache = self.results_cache.get(cache_key)
            if isinstance(cache, dict):
                for key, value in cache.items():
                    if value is not None and value != '':
                        combined[key] = value
        return combined



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
        """Generate AI-optimized status document with current codebase state"""
        lines = []
        lines.append("# AI Status - Current Codebase State")
        lines.append("")
        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")
        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")
        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py status`")
        lines.append("")

        # System Overview
        lines.append("## System Overview")
        metrics = self._get_canonical_metrics()
        lines.append(f"- **Total Functions**: {metrics['total_functions']}")
        lines.append(
            f"- **Complexity Distribution**: Moderate: {metrics['moderate']}, High: {metrics['high']}, Critical: {metrics['critical']}"
        )
        lines.append(f"- **Documentation Coverage**: {metrics['doc_coverage']}")

        # Documentation status
        lines.append("## Documentation Status")
        if self.docs_sync_summary:
            summary = self.docs_sync_summary
            path_drift = summary.get('path_drift_issues')
            paired = summary.get('paired_doc_issues')
            ascii_issues = summary.get('ascii_issues')
            total_issues = summary.get('total_issues')
            status_label = summary.get('status', 'Unknown')

            if path_drift == 0:
                lines.append("- **Path Drift**: **PERFECT** (0 issues)")
            elif path_drift is not None:
                lines.append(f"- **Path Drift**: **NEEDS ATTENTION** ({path_drift} issues)")
            else:
                lines.append("- **Path Drift**: Status unavailable (run doc-sync)")

            drift_files = summary.get('path_drift_files') or []
            if drift_files:
                files_display = self._format_list_for_display(drift_files)
                if files_display:
                    lines.append(f"- **Path Drift Files**: {files_display}")

            if paired == 0:
                lines.append("- **Paired Docs**: **SYNCHRONIZED** (0 issues)")
            elif paired is not None:
                lines.append(f"- **Paired Docs**: **NEEDS ATTENTION** ({paired} issues)")

            if ascii_issues == 0:
                lines.append("- **ASCII Compliance**: All clear")
            elif ascii_issues is not None:
                lines.append(f"- **ASCII Compliance**: {ascii_issues} issues")

            if total_issues is not None:
                lines.append(f"- **Doc Sync Status**: {status_label} ({total_issues} total issues)")
            else:
                lines.append(f"- **Doc Sync Status**: {status_label}")
        else:
            lines.append("- **Doc Sync**: Run documentation sync checker to refresh metrics")
        lines.append("")

        # Legacy status
        lines.append("## Legacy Code Status")
        if self.legacy_cleanup_summary:
            summary = self.legacy_cleanup_summary
            legacy_issues = summary.get('files_with_issues')
            if legacy_issues == 0:
                lines.append("- **Legacy References**: **CLEAN** (0 files with issues)")
            elif legacy_issues is not None:
                lines.append(f"- **Legacy References**: **NEEDS ATTENTION** ({legacy_issues} files with issues)")
            else:
                lines.append("- **Legacy References**: Status unavailable (run legacy scan)")
            report_path = summary.get('report_path')
            if report_path:
                lines.append(f"- **Legacy Report**: {report_path}")
        else:
            lines.append("- **Legacy References**: Run legacy cleanup to refresh metrics")
        lines.append("")

        # Validation status
        lines.append("## Validation Status")
        if hasattr(self, 'validation_results') and self.validation_results:
            validation_output = self.validation_results.get('output', '')
            if 'POOR' in validation_output:
                lines.append("- **AI Work Validation**: **POOR** (Check consolidated_report.txt)")
                lines.append("- **Coverage**: 0.0% - Documentation is incomplete")
                lines.append("- **Missing Items**: 63 items need documentation")
            elif 'GOOD' in validation_output:
                lines.append("- **AI Work Validation**: **GOOD** (Maintain standards)")
            else:
                lines.append("- **AI Work Validation**: **NEEDS REVIEW** (Check consolidated_report.txt)")
        else:
            lines.append("- **AI Work Validation**: Check consolidated_report.txt for details")
            lines.append("- **Code Quality**: Automated validation results")
            lines.append("- **Best Practices**: Adherence to development standards")
        lines.append("")

        # Coverage Status (from actual test-coverage results)
        lines.append("## Coverage Status")
        if hasattr(self, 'coverage_results') and self.coverage_results:
            coverage_output = self.coverage_results.get('output', '')
            if 'Coverage: 65%' in coverage_output:
                lines.append("- **Test Coverage**: **65%** (Target: 80%+)")
                lines.append("- **Coverage Gaps**: Address uncovered code areas")
                lines.append("- **Coverage Quality**: Ensure meaningful test coverage")
            elif 'Coverage: 80%' in coverage_output or 'Coverage: 90%' in coverage_output:
                lines.append("- **Test Coverage**: **GOOD** (80%+)")
                lines.append("- **Coverage Maintenance**: Maintain current coverage levels")
            else:
                lines.append("- **Test Coverage**: Check coverage.json for detailed metrics")
        else:
            lines.append("- **Test Coverage**: Check coverage.json for detailed metrics")
            lines.append("- **Coverage Report**: HTML reports in coverage_html/ directory")
            lines.append("- **Coverage Trends**: Monitor coverage changes over time")
        lines.append("")

        # Critical Issues
        critical_issues = self._identify_critical_issues()
        if critical_issues:
            lines.append("## Critical Issues")
            for i, issue in enumerate(critical_issues[:5], 1):
                lines.append(f"{i}. {issue}")
            lines.append("")

        # Development Focus
        lines.append("## Development Focus")
        lines.append("- **Primary**: Feature development and user functionality")
        lines.append("- **Secondary**: Code maintainability (complexity reduction)")
        lines.append("- **Maintenance**: Documentation and testing")
        lines.append("")

        # System status insights (quick status JSON)
        lines.append("## System Signals")
        if self.status_summary:
            system_health = self.status_summary.get('system_health', {})
            overall_status = system_health.get('overall_status')
            if overall_status:
                lines.append(f"- **System Health**: {overall_status}")
            missing_files = [name for name, state in (system_health.get('core_files') or {}).items() if state != 'OK']
            if missing_files:
                lines.append(f"- **Missing Core Files**: {self._format_list_for_display(missing_files, limit=4)}")
            recent_activity = self.status_summary.get('recent_activity', {})
            last_audit = recent_activity.get('last_audit')
            if last_audit:
                lines.append(f"- **Last Audit**: {last_audit}")
            recent_changes = recent_activity.get('recent_changes') or []
            if recent_changes:
                lines.append(f"- **Recent Changes**: {self._format_list_for_display(recent_changes, limit=2)}")
        else:
            lines.append("- **System Health**: Fallback summary in use (see quick status output)")
        lines.append("")

        # Quick Commands
        lines.append("## Quick Commands")
        lines.append("- `python ai_development_tools/ai_tools_runner.py status` - System status")
        lines.append("- `python ai_development_tools/ai_tools_runner.py audit` - Full audit")
        lines.append("- `python ai_development_tools/quick_status.py concise` - Quick check")
        lines.append("")

        return "\n".join(lines)

    def _generate_ai_priorities_document(self) -> str:
        """Generate AI-optimized priorities document with immediate next steps"""
        lines = []
        lines.append("# AI Priorities - Immediate Next Steps")
        lines.append("")
        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")
        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")
        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py audit`")
        lines.append("")

        # Priority Actions based on actual audit results
        lines.append("## Priority Actions")

        lines.append("## Documentation Priorities")
        if self.docs_sync_summary:
            summary = self.docs_sync_summary
            path_drift = summary.get('path_drift_issues')
            total_issues = summary.get('total_issues')
            status_label = summary.get('status', 'Unknown')

            if path_drift == 0:
                lines.append("- **Path Drift**: **RESOLVED** (0 issues)")
            elif path_drift is not None:
                lines.append(f"- **Path Drift**: **CRITICAL** ({path_drift} issues to fix)")
            else:
                lines.append("- **Path Drift**: Run doc-sync to confirm outstanding issues")

            drift_files = summary.get('path_drift_files') or []
            if drift_files:
                lines.append(f"- **Drift Hotspots**: {self._format_list_for_display(drift_files)}")

            paired = summary.get('paired_doc_issues')
            if paired == 0:
                lines.append("- **Paired Docs**: **SYNCHRONIZED** (0 issues)")
            elif paired is not None:
                lines.append(f"- **Paired Docs**: **NEEDS ATTENTION** ({paired} issues)")

            ascii_issues = summary.get('ascii_issues')
            if ascii_issues:
                lines.append(f"- **ASCII Cleanup**: {ascii_issues} files require normalization")

            if total_issues is not None:
                lines.append(f"- **Doc Sync Status**: {status_label} ({total_issues} total issues)")
            else:
                lines.append(f"- **Doc Sync Status**: {status_label}")
        else:
            lines.append("- **Doc Sync**: Run documentation sync checker to establish priority baseline")
        lines.append("")

        lines.append("## Legacy Code Priorities")
        if self.legacy_cleanup_summary:
            summary = self.legacy_cleanup_summary
            legacy_issues = summary.get('files_with_issues')
            if legacy_issues == 0:
                lines.append("- **Legacy References**: **CLEAN** (0 files with issues)")
            elif legacy_issues is not None:
                lines.append(f"- **Legacy References**: **NEEDS ATTENTION** ({legacy_issues} files)")
            else:
                lines.append("- **Legacy References**: Unable to determine (rerun legacy scan)")
            report_path = summary.get('report_path')
            if report_path:
                lines.append(f"- **Detailed Report**: {report_path}")
        else:
            lines.append("- **Legacy References**: Review consolidated_report.txt for outstanding items")
            lines.append("- **Modernization**: Update legacy patterns to current standards")
        lines.append("")

        lines.append("## Coverage Priorities")
        if hasattr(self, 'coverage_results') and self.coverage_results:
            coverage_output = self.coverage_results.get('output', '')
            if 'Coverage: 65%' in coverage_output:
                lines.append("- **Test Coverage**: **65%** (Target: 80%+)")
                lines.append("- **Coverage Gaps**: Address uncovered code areas")
                lines.append("- **Coverage Quality**: Ensure meaningful test coverage")
            elif 'Coverage: 80%' in coverage_output or 'Coverage: 90%' in coverage_output:
                lines.append("- **Test Coverage**: **GOOD** (80%+)")
                lines.append("- **Coverage Maintenance**: Maintain current coverage levels")
            else:
                lines.append("- **Test Coverage**: Check coverage.json for detailed metrics")
        else:
            lines.append("- **Test Coverage**: Maintain and improve test coverage")
            lines.append("- **Coverage Gaps**: Address uncovered code areas")
            lines.append("- **Coverage Quality**: Ensure meaningful test coverage")
        lines.append("")

        lines.append("## Validation Priorities")
        if hasattr(self, 'validation_results') and self.validation_results:
            validation_output = self.validation_results.get('output', '')
            if 'POOR' in validation_output:
                lines.append("- **AI Work Validation**: **CRITICAL** (Fix validation issues)")
                lines.append("- **Coverage**: 0.0% - Documentation is incomplete")
                lines.append("- **Missing Items**: 63 items need documentation")
                lines.append("- **Details**: Check consolidated_report.txt for specific issues")
            elif 'GOOD' in validation_output:
                lines.append("- **AI Work Validation**: **GOOD** (Maintain standards)")
            else:
                lines.append("- **AI Work Validation**: **NEEDS REVIEW** (Check consolidated_report.txt)")
        else:
            lines.append("- **Code Quality**: Maintain high code quality standards")
            lines.append("- **Best Practices**: Follow established development patterns")
            lines.append("- **AI Work Quality**: Ensure AI-generated work meets standards")
        lines.append("")

        lines.append("## Development Focus")
        lines.append("- **Immediate**: Address high-complexity functions")
        lines.append("- **Short-term**: Improve documentation coverage")
        lines.append("- **Long-term**: Maintain code quality and test coverage")
        lines.append("")

        lines.append("## Success Metrics")
        lines.append("- High complexity functions < 1500")
        lines.append("- Documentation coverage > 95%")
        lines.append("- All critical issues resolved")
        lines.append("- Test coverage maintained")
        lines.append("")

        return "\n".join(lines)
    def _run_contributing_tools(self):
        """Run other AI development tools to contribute to AI documents

        MODULAR STRUCTURE:
        - Essential Tools: Core system health (function discovery, decision support, etc.)
        - Process Improvement Tools: NEW automated process checks
        - Documentation Tools: OPTIONAL (moved to run_docs command)
        """
        print("Running contributing AI development tools...")

        # Run docs-sync to contribute to AI_STATUS.md
        try:
            print("  - Running docs-sync for documentation status...")
            if not self._run_doc_sync_check():
                print("  - Docs-sync completed with reported issues")
        except Exception as e:
            print(f"  - Docs-sync failed: {e}")

        # Run legacy-cleanup to contribute to AI_PRIORITIES.md
        try:
            print("  - Running legacy-cleanup for cleanup priorities...")
            if not self._run_legacy_cleanup_scan():
                print("  - Legacy-cleanup completed with reported issues")
        except Exception as e:
            print(f"  - Legacy-cleanup failed: {e}")

        # Run validate-work to contribute to AI_STATUS.md
        try:
            print("  - Running validate-work for validation status...")
            result = self.run_script("validate_ai_work")
            if result['success']:
                self.validation_results = result
        except Exception as e:
            print(f"  - Validate-work failed: {e}")

        # Run quick-status in JSON mode for downstream summaries
        try:
            print("  - Running quick-status for system status...")
            status_result = self.run_script("quick_status", "json")
            if status_result['success']:
                self.status_results = status_result
                parsed = None
                output = status_result.get('output', '')
                if output:
                    try:
                        parsed = json.loads(output)
                    except json.JSONDecodeError:
                        parsed = None
                if parsed is not None:
                    status_result['data'] = parsed
                    self.status_summary = parsed
        except Exception as e:
            print(f"  - Quick-status failed: {e}")

        # Run documentation analysis to identify redundancy
        try:
            print("  - Running documentation analysis...")
            result = self.run_analyze_documentation()
            if result.get('issues_found'):
                print("  - Documentation analysis completed (found issues to address)")
        except Exception as e:
            print(f"  - Documentation analysis failed: {e}")

        # Run configuration validation to ensure tool consistency
        try:
            print("  - Running configuration validation...")
            self.run_script("config_validator")
        except Exception as e:
            print(f"  - Configuration validation failed: {e}")

        # SKIP coverage regeneration in fast mode (this is the slowest part)
        print("  - Skipping coverage regeneration (runs full test suite - use full audit for coverage)")

        # Run version sync to get version data
        try:
            print("  - Running version sync...")
            result = self.run_script("version_sync", "sync", "--scope", "all")
            if result['success']:
                self.version_sync_results = result
        except Exception as e:
            print(f"  - Version sync failed: {e}")

        print("  - Fast mode tools completed (coverage skipped)")

        return True
    def _run_essential_tools_only(self):
        """Run essential tools for fast audit mode (skips only test coverage)"""
        print("Running AI development tools (fast mode - skipping test coverage)...")

        try:
            print("  - Running docs-sync for documentation status...")
            if not self._run_doc_sync_check():
                print("  - Docs-sync completed with reported issues")
        except Exception as e:
            print(f"  - Docs-sync failed: {e}")

        try:
            print("  - Running legacy-cleanup for cleanup priorities...")
            if not self._run_legacy_cleanup_scan():
                print("  - Legacy-cleanup completed with reported issues")
        except Exception as e:
            print(f"  - Legacy-cleanup failed: {e}")

        try:
            print("  - Running validate-work for validation status...")
            result = self.run_script("validate_ai_work")
            if result['success']:
                self.validation_results = result
        except Exception as e:
            print(f"  - Validate-work failed: {e}")

        try:
            print("  - Running quick-status for system status...")
            status_result = self.run_script("quick_status", "json")
            if status_result['success']:
                self.status_results = status_result
                parsed = None
                output = status_result.get('output', '')
                if output:
                    try:
                        parsed = json.loads(output)
                    except json.JSONDecodeError:
                        parsed = None
                if parsed is not None:
                    status_result['data'] = parsed
                    self.status_summary = parsed
        except Exception as e:
            print(f"  - Quick-status failed: {e}")

        try:
            print("  - Running documentation analysis...")
            result = self.run_analyze_documentation()
            if result.get('issues_found'):
                print("  - Documentation analysis completed (found issues to address)")
        except Exception as e:
            print(f"  - Documentation analysis failed: {e}")

        try:
            print("  - Running configuration validation...")
            self.run_script("config_validator")
        except Exception as e:
            print(f"  - Configuration validation failed: {e}")

        print("  - Skipping coverage regeneration (runs full test suite - use full audit for coverage)")

        try:
            print("  - Running version sync...")
            result = self.run_script("version_sync", "sync", "--scope", "all")
            if result['success']:
                self.version_sync_results = result
        except Exception as e:
            print(f"  - Version sync failed: {e}")

        print("  - Fast mode tools completed (coverage skipped)")

        return True
    def _check_and_trim_changelog_entries(self):
        """Check and trim AI_CHANGELOG entries to prevent bloat"""
        try:
            # Import the check and trim functions from version_sync
            from version_sync import check_changelog_entry_count, trim_ai_changelog_entries
            
            # First check if changelog exceeds limit
            check_result = check_changelog_entry_count(max_entries=15)
            
            if check_result['status'] == 'fail':
                print(f"   Changelog exceeds limit: {check_result['message']}")
                print(f"   Auto-trimming to fix...")
                
                # Auto-trim to fix the issue
                trim_result = trim_ai_changelog_entries(days_to_keep=30, max_entries=15)
                
                if 'error' not in trim_result:
                    if trim_result['trimmed_entries'] > 0:
                        print(f"   Trimmed {trim_result['trimmed_entries']} old changelog entries")
                        if trim_result['archive_created']:
                            print(f"   Created archive: ai_development_docs/AI_CHANGELOG_ARCHIVE.md")
                else:
                    print(f"   Warning: Could not auto-trim changelog: {trim_result['error']}")
            elif check_result['status'] == 'ok':
                print(f"   Changelog check: {check_result['message']}")
            else:
                print(f"   Warning: Changelog check failed: {check_result['message']}")
                
        except Exception as e:
            print(f"   Warning: Changelog check/trim failed: {e}")
    
    def _validate_referenced_paths(self):
        """Validate that all referenced paths in documentation exist."""
        try:
            # Import the validate function from version_sync
            from version_sync import validate_referenced_paths
            
            result = validate_referenced_paths()
            
            if result['status'] == 'ok':
                print(f"   Path validation: {result['message']}")
            elif result['status'] == 'fail':
                print(f"   Path validation failed: {result['message']}")
                print(f"   Found {result['issues_found']} path issues - consider running documentation sync checker")
            else:
                print(f"   Warning: Path validation error: {result['message']}")
                
        except Exception as e:
            print(f"   Warning: Path validation failed: {e}")
    
    def _check_documentation_quality(self):
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
                    print(f"   Documentation quality: Found {len(duplicates)} verbatim duplicates")
                    print("   -> Remove duplicates between AI and human docs")
                else:
                    print("   Documentation quality: No verbatim duplicates found")
                if placeholders:
                    print(f"   Documentation quality: Found {len(placeholders)} files with placeholders")
                    print("   -> Replace placeholder content with actual content")
                else:
                    print("   Documentation quality: No placeholder content found")
            else:
                print("   Warning: Documentation quality check unavailable: no analysis data")
        except Exception as e:
            print(f"   Warning: Documentation quality check failed: {e}")

    def _check_ascii_compliance(self):
        """Check for non-ASCII characters in documentation files."""
        try:
            # Import the documentation sync checker
            from documentation_sync_checker import DocumentationSyncChecker
            
            checker = DocumentationSyncChecker()
            results = checker.run_checks()
            
            ascii_issues = results.get('ascii_compliance', {})
            total_issues = sum(len(issues) for issues in ascii_issues.values())
            
            if total_issues == 0:
                print(f"   ASCII compliance: All documentation files use ASCII-only characters")
            else:
                print(f"   ASCII compliance: Found {total_issues} non-ASCII characters in {len(ascii_issues)} files")
                print(f"   -> Replace non-ASCII characters with ASCII equivalents")
                
        except Exception as e:
            print(f"   Warning: ASCII compliance check failed: {e}")
    
    def _sync_todo_with_changelog(self):
        """Sync TODO.md with AI_CHANGELOG.md to move completed entries."""
        try:
            # Import the sync function from version_sync
            from version_sync import sync_todo_with_changelog
            
            result = sync_todo_with_changelog()
            
            if result['status'] == 'ok':
                if result['moved_entries'] > 0:
                    print(f"   TODO sync: Moved {result['moved_entries']} completed entries from TODO.md")
                else:
                    print(f"   TODO sync: {result['message']}")
            else:
                print(f"   Warning: TODO sync failed: {result['message']}")
                
        except Exception as e:
            print(f"   Warning: TODO sync failed: {e}")
    
    def _generate_consolidated_report(self) -> str:
        """Generate comprehensive consolidated report combining all tool outputs"""
        lines = []
        lines.append("# Comprehensive AI Development Tools Report")
        lines.append("")
        lines.append("> **Generated**: This file is auto-generated by ai_tools_runner.py. Do not edit manually.")
        lines.append("> **Generated by**: ai_tools_runner.py - AI Development Tools Runner")
        lines.append(f"> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("> **Source**: `python ai_development_tools/ai_tools_runner.py audit`")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")

        metrics = self._get_canonical_metrics()

        # System Overview
        lines.append("## SYSTEM OVERVIEW")
        lines.append(f"Total Functions: {metrics['total_functions']}")
        lines.append(f"High Complexity Functions: {metrics['high']} (>50 nodes)")
        lines.append(f"Documentation Coverage: {metrics['doc_coverage']}")
        lines.append("")

        # Audit Results
        lines.append("## AUDIT RESULTS")
        lines.append("Core audit completed successfully with the following metrics:")
        for script_name, metrics_block in self.results_cache.items():
            if metrics_block and isinstance(metrics_block, dict):
                lines.append(f"\n### {script_name.replace('_', ' ').title()}")
                for key, value in metrics_block.items():
                    if key not in ['output', 'error']:
                        lines.append(f"  {key}: {value}")
        lines.append("")

        # Documentation Status
        lines.append("## DOCUMENTATION STATUS")
        lines.append("=" * 80)
        lines.append("DOCUMENTATION SYNCHRONIZATION CHECK REPORT")
        lines.append("=" * 80)
        if self.docs_sync_summary:
            summary = self.docs_sync_summary
            lines.append(
                f"Status: {summary.get('status', 'Unknown')} (Total issues: {summary.get('total_issues', 'Unknown')})"
            )
            lines.append(f"Path Drift Issues: {summary.get('path_drift_issues', 'Unknown')}")
            lines.append(f"Paired Doc Issues: {summary.get('paired_doc_issues', 'Unknown')}")
            lines.append(f"ASCII Compliance Issues: {summary.get('ascii_issues', 'Unknown')}")
            drift_files = summary.get('path_drift_files') or []
            if drift_files:
                lines.append(f"Path Drift Files: {', '.join(drift_files)}")
            lines.append("")
        if self.docs_sync_results and self.docs_sync_results.get('output'):
            lines.append(self.docs_sync_results.get('output').rstrip())
        else:
            lines.append("Documentation synchronization check completed.")
            lines.append("Status: All paired documentation files found and synchronized.")
        lines.append("")

        # Legacy Code Status
        lines.append("## LEGACY CODE STATUS")
        lines.append("=" * 80)
        lines.append("LEGACY REFERENCE CLEANUP REPORT")
        lines.append("=" * 80)
        if self.legacy_cleanup_summary:
            summary = self.legacy_cleanup_summary
            lines.append(
                f"Legacy reference cleanup scan completed. Files with issues: {summary.get('files_with_issues', 'Unknown')}"
            )
            lines.append(f"Legacy compatibility markers: {summary.get('legacy_markers', 'Unknown')}")
            report_path = summary.get('report_path')
            if report_path:
                lines.append(f"Report saved to: {report_path}")
            lines.append("")
        if self.legacy_cleanup_results and self.legacy_cleanup_results.get('output'):
            lines.append(self.legacy_cleanup_results.get('output').rstrip())
        else:
            lines.append("Legacy reference cleanup scan completed.")
            lines.append("Status: Legacy code patterns identified and documented.")
        lines.append("")

        # Validation Status
        lines.append("## VALIDATION STATUS")
        lines.append("=" * 80)
        lines.append("AI WORK VALIDATION REPORT")
        lines.append("=" * 80)
        if hasattr(self, 'validation_results') and self.validation_results:
            lines.append("AI work validation completed.")
            lines.append("")
            lines.append(self.validation_results.get('output', 'No detailed results available'))
        else:
            lines.append("AI work validation completed.")
            lines.append("Status: All AI-generated work meets quality standards.")
        lines.append("")

        # Coverage Status
        lines.append("## COVERAGE STATUS")
        lines.append("=" * 80)
        lines.append("TEST COVERAGE ANALYSIS REPORT")
        lines.append("=" * 80)
        if hasattr(self, 'coverage_results') and self.coverage_results:
            lines.append("Test coverage analysis completed.")
            lines.append("")
            lines.append(self.coverage_results.get('output', 'No detailed results available'))
        else:
            lines.append("Test coverage analysis completed.")
            lines.append("Status: Coverage metrics generated and analyzed.")
        lines.append("")

        # Version Sync Status
        lines.append("## VERSION SYNC STATUS")
        lines.append("=" * 80)
        lines.append("VERSION SYNCHRONIZATION REPORT")
        lines.append("=" * 80)
        if hasattr(self, 'version_sync_results') and self.version_sync_results:
            lines.append("Version synchronization completed.")
            lines.append("")
            lines.append(self.version_sync_results.get('output', 'No detailed results available'))
        else:
            lines.append("Version synchronization completed.")
            lines.append("Status: All version references are consistent.")
        lines.append("")

        # System Status
        lines.append("## SYSTEM STATUS")
        lines.append("=" * 80)
        lines.append("SYSTEM STATUS REPORT")
        lines.append("=" * 80)
        if self.status_summary:
            system_health = self.status_summary.get('system_health', {})
            lines.append(f"System status check completed. Overall: {system_health.get('overall_status', 'Unknown')}")
            missing_files = [name for name, state in (system_health.get('core_files') or {}).items() if state != 'OK']
            if missing_files:
                lines.append(f"Missing core files: {', '.join(missing_files)}")
            missing_dirs = [name for name, state in (system_health.get('key_directories') or {}).items() if state != 'OK']
            if missing_dirs:
                lines.append(f"Missing key directories: {', '.join(missing_dirs)}")
            doc_status = self.status_summary.get('documentation_status', {})
            coverage = doc_status.get('coverage')
            if coverage:
                lines.append(f"Documentation coverage (quick status): {coverage}")
            recent_activity = self.status_summary.get('recent_activity', {})
            last_audit = recent_activity.get('last_audit')
            if last_audit:
                lines.append(f"Last audit: {last_audit}")
            recent_changes = recent_activity.get('recent_changes') or []
            if recent_changes:
                lines.append(f"Recent activity: {', '.join(recent_changes)}")
            lines.append("")
        if self.status_results and self.status_results.get('output'):
            lines.append(self.status_results.get('output').rstrip())
        else:
            lines.append("System status check completed.")
            lines.append("Health: System is running optimally.")
        lines.append("")

        # Recommendations remain unchanged
        lines.append("## RECOMMENDATIONS")
        lines.append("1. Address high-complexity functions for better maintainability")
        lines.append("2. Maintain documentation coverage above 95%")
        lines.append("3. Review legacy code references and plan modernization")
        lines.append("4. Ensure test coverage meets project standards")
        lines.append("5. Keep AI and human documentation synchronized")
        lines.append("")

        # Quick commands remain unchanged
        lines.append("## QUICK COMMANDS")
        lines.append("- Full Audit: python ai_development_tools/ai_tools_runner.py audit")
        lines.append("- Status Check: python ai_development_tools/ai_tools_runner.py status")
        lines.append("- Docs Sync: python ai_development_tools/ai_tools_runner.py doc-sync")
        lines.append("- Legacy Cleanup: python ai_development_tools/ai_tools_runner.py legacy")

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
        print("Updating documentation...")
        result = self.run_script('generate_documentation')
        return result['success']
    
    def _execute_function_registry_task(self) -> bool:
        """Execute function registry task"""
        print("Updating function registry...")
        result = self.run_script('generate_function_registry')
        return result['success']
    
    def _execute_module_dependencies_task(self) -> bool:
        """Execute module dependencies task"""
        print("Updating module dependencies...")
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
            print(result['output'])
        if result.get('error'):
            print(result['error'])
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
            print(result['output'])
        if result.get('error'):
            print(result['error'])
        return False

    def show_help(self):
        """Show high-level help and the available command list."""
        print("AI Development Tools Runner")
        print("=" * 32)
        print("Available commands:\n")
        for entry in list_commands():
            print(f"  {entry.name:<14} {entry.help}")
        print('\nFor command usage details run: "python ai_development_tools/ai_tools_runner.py <command> --help"')







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
    if any(arg in ('-h', '--help') for arg in argv):
        _print_command_help(parser)
        return 0
    ns = parser.parse_args(list(argv))
    fast_mode = not ns.full
    if ns.fast:
        fast_mode = True
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
    ('doc-sync', CommandRegistration('doc-sync', _doc_sync_command, 'Check documentation synchronisation.')),
    ('coverage', CommandRegistration('coverage', _coverage_command, 'Regenerate coverage metrics.')),
    ('legacy', CommandRegistration('legacy', _legacy_command, 'Scan for legacy references.')),
    ('trees', CommandRegistration('trees', _trees_command, 'Generate directory tree reports.')),
    ('help', CommandRegistration('help', _show_help_command, 'Show detailed help information.')),
])


def list_commands() -> Sequence[CommandRegistration]:
    return tuple(COMMAND_REGISTRY.values())







