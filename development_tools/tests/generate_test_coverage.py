#!/usr/bin/env python3
# TOOL_TIER: core

"""
Test Coverage Metrics Regenerator (Portable)

This script regenerates test coverage metrics and updates coverage plans.
It is configurable via development_tools_config.json to work with any project's
test setup and coverage configuration.

Usage:
    python tests/generate_test_coverage.py [--update-plan] [--output-file]
"""

import argparse
import configparser
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for core module imports
# Script is at: development_tools/tests/generate_test_coverage.py
# So we need to go up 3 levels: tests -> development_tools -> project_root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Import config module (absolute import for portability)
try:
    from development_tools import config
except ImportError:
    # Fallback for when run as script
    # Already have project_root from above, just ensure it's in path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config

# Import decomposed coverage analysis and report generation tools
try:
    from development_tools.tests.analyze_test_coverage import TestCoverageAnalyzer
    from development_tools.tests.generate_test_coverage_reports import TestCoverageReportGenerator
except ImportError:
    # Fallback for relative imports
    try:
        from .analyze_test_coverage import TestCoverageAnalyzer
        from .generate_test_coverage_reports import TestCoverageReportGenerator
    except ImportError:
        TestCoverageAnalyzer = None
        TestCoverageReportGenerator = None

# Load external config on module import (safe to call multiple times)
config.load_external_config()

logger = get_component_logger("development_tools")

class CoverageMetricsRegenerator:
    """Regenerates test coverage metrics (portable across projects)."""
    
    def __init__(self, project_root: str = ".", parallel: bool = True, num_workers: Optional[str] = None,
                 pytest_command: Optional[List[str]] = None, coverage_config: Optional[str] = None,
                 artifact_directories: Optional[Dict[str, str]] = None):
        """
        Initialize coverage metrics regenerator.
        
        Args:
            project_root: Root directory of the project
            parallel: Whether to run tests in parallel (default: True)
            num_workers: Number of parallel workers or "auto" (default: "auto")
            pytest_command: Optional pytest command as list (e.g., ['python', '-m', 'pytest']).
                           If None, loads from config or uses default.
            coverage_config: Optional path to coverage config file (e.g., 'coverage.ini').
                            If None, loads from config or uses default.
            artifact_directories: Optional dict with keys: html_output, archive, logs, dev_tools_html.
                                If None, loads from config or uses defaults.
        """
        self.project_root = Path(project_root).resolve()
        
        # Load coverage configuration from external config
        coverage_config_data = config.get_external_value('coverage', {})
        
        # Pytest command (from parameter, config, or default)
        if pytest_command is not None:
            self.pytest_command = pytest_command
        else:
            config_pytest = coverage_config_data.get('pytest_command', [])
            if config_pytest:
                self.pytest_command = config_pytest if isinstance(config_pytest, list) else [config_pytest]
            else:
                # Default: use sys.executable with pytest module
                self.pytest_command = [sys.executable, '-m', 'pytest']
        
        # Pytest base arguments (from config or default)
        self.pytest_base_args = coverage_config_data.get('pytest_base_args', [
            '--cov-report=term-missing',
            '--tb=line',
            '-q',
            '--maxfail=5'
        ])
        
        # Test directory (from config or default)
        self.test_directory = coverage_config_data.get('test_directory', 'tests/')
        
        # Coverage config path (from parameter, config, or default)
        if coverage_config is not None:
            self.coverage_config_path = self.project_root / coverage_config
        else:
            config_path = coverage_config_data.get('coverage_config', 'coverage.ini')
            self.coverage_config_path = self.project_root / config_path
        
        # Artifact directories (from parameter, config, or defaults)
        if artifact_directories is not None:
            self.artifact_dirs = artifact_directories
        else:
            config_artifacts = coverage_config_data.get('artifact_directories', {})
            if config_artifacts:
                self.artifact_dirs = config_artifacts
            else:
                # Generic defaults
                self.artifact_dirs = {
                    'html_output': 'htmlcov',
                    'archive': 'development_tools/reports/archive/coverage_artifacts',
                    'logs': 'development_tools/tests/logs/coverage_regeneration',
                    'dev_tools_html': None  # Disabled - no longer generating dev tools HTML
                }
        
        # Set up paths from artifact directories
        self.coverage_plan_file = self.project_root / "development_docs" / "TEST_COVERAGE_EXPANSION_PLAN.md"
        self.coverage_data_file: Path = self.project_root / ".coverage"
        self.coverage_html_dir: Path = self.project_root / self.artifact_dirs.get('html_output', 'htmlcov')
        self.coverage_logs_dir: Path = self.project_root / self.artifact_dirs.get('logs', 'development_tools/tests/logs/coverage_regeneration')
        self.archive_root: Path = self.project_root / self.artifact_dirs.get('archive', 'development_tools/reports/archive/coverage_artifacts')
        
        # Dev tools specific coverage paths
        self.dev_tools_coverage_config_path: Path = self.project_root / "development_tools" / "tests" / "coverage_dev_tools.ini"
        self.dev_tools_coverage_data_file: Path = self.project_root / "development_tools" / "tests" / ".coverage_dev_tools"
        self.dev_tools_coverage_json: Path = self.project_root / "development_tools" / "tests" / "coverage_dev_tools.json"
        self.dev_tools_coverage_html_dir: Optional[Path] = None  # Disabled - no longer generating dev tools HTML
        
        self.pytest_stdout_log: Optional[Path] = None
        self.pytest_stderr_log: Optional[Path] = None
        self.archived_directories: List[Dict[str, str]] = []
        self.command_logs: List[Path] = []
        self.parallel = parallel
        self.num_workers = num_workers or "auto"  # "auto" lets pytest-xdist decide, or specify a number
        self._configure_coverage_paths()
        self._migrate_legacy_logs()
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Core modules to track coverage for
        # Import constants from shared.constants
        from development_tools.shared.constants import CORE_MODULES
        self.core_modules = list(CORE_MODULES)
        
        # Initialize analyzer and report generator
        # Try to import if not already available (handles cases where imports failed at module level)
        analyzer_class = TestCoverageAnalyzer
        if analyzer_class is None:
            try:
                from development_tools.tests.analyze_test_coverage import TestCoverageAnalyzer as AnalyzerClass
                analyzer_class = AnalyzerClass
            except ImportError:
                try:
                    from .analyze_test_coverage import TestCoverageAnalyzer as AnalyzerClass
                    analyzer_class = AnalyzerClass
                except ImportError:
                    analyzer_class = None
        
        if analyzer_class is not None:
            self.analyzer = analyzer_class(str(self.project_root))
        else:
            self.analyzer = None
            if logger:
                logger.warning("TestCoverageAnalyzer not available - coverage parsing may fail")
        
        report_generator_class = TestCoverageReportGenerator
        if report_generator_class is None:
            try:
                from development_tools.tests.generate_test_coverage_reports import TestCoverageReportGenerator as ReportGeneratorClass
                report_generator_class = ReportGeneratorClass
            except ImportError:
                try:
                    from .generate_test_coverage_reports import TestCoverageReportGenerator as ReportGeneratorClass
                    report_generator_class = ReportGeneratorClass
                except ImportError:
                    report_generator_class = None
        
        if report_generator_class is not None:
            artifact_dirs = {
                'html_output': str(self.coverage_html_dir.relative_to(self.project_root)),
                'archive': str(self.archive_root.relative_to(self.project_root)),
                'logs': str(self.coverage_logs_dir.relative_to(self.project_root))
            }
            self.report_generator = report_generator_class(
                project_root=str(self.project_root),
                coverage_config=str(self.coverage_config_path.relative_to(self.project_root)) if self.coverage_config_path.exists() else None,
                artifact_directories=artifact_dirs
            )
            # Update coverage_data_file path in report generator to match ours
            self.report_generator.coverage_data_file = self.coverage_data_file
        else:
            self.report_generator = None
            if logger:
                logger.warning("TestCoverageReportGenerator not available - report generation may fail")
        
    def _configure_coverage_paths(self) -> None:
        """Load coverage configuration paths from coverage.ini (if it exists and specifies paths)."""
        if not self.coverage_config_path.exists():
            # Fall back to defaults (already set in __init__)
            return
        
        coverage_ini = configparser.ConfigParser()
        coverage_ini.read(self.coverage_config_path)
        
        # Only override if coverage.ini explicitly specifies paths
        data_file = coverage_ini.get('run', 'data_file', fallback='').strip()
        if data_file:
            self.coverage_data_file = (self.coverage_config_path.parent / data_file).resolve()
        
        html_directory = coverage_ini.get('html', 'directory', fallback='').strip()
        if html_directory:
            # Override the default HTML directory if specified in coverage.ini
            self.coverage_html_dir = (self.coverage_config_path.parent / html_directory).resolve()
        
        # Ensure parent directories exist when we later write artefacts
        self.coverage_data_file.parent.mkdir(parents=True, exist_ok=True)
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)

    def _migrate_legacy_logs(self) -> None:
        """Move legacy coverage logs from the old location into the new directory."""
        legacy_dir = self.project_root / "logs" / "coverage_regeneration"
        if not legacy_dir.exists() or legacy_dir.resolve() == self.coverage_logs_dir.resolve():
            return
        
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
        for item in legacy_dir.iterdir():
            destination = self.coverage_logs_dir / item.name
            try:
                if destination.exists():
                    # Preserve existing new-format logs by appending timestamp suffix
                    suffix = datetime.now().strftime("%Y%m%d-%H%M%S")
                    destination = self.coverage_logs_dir / f"{destination.stem}_{suffix}{destination.suffix}"
                shutil.move(str(item), str(destination))
            except Exception as exc:
                if logger:
                    logger.warning(f"Failed to migrate legacy log {item}: {exc}")
        
        try:
            legacy_dir.rmdir()
        except OSError:
            # Directory not empty (maybe concurrent process); leave it alone
            pass

    def run_coverage_analysis(self) -> Dict[str, Dict[str, any]]:
        """Run pytest coverage analysis and extract metrics."""
        if logger:
            logger.info("Running pytest coverage analysis...")
        
        try:
            self.archived_directories.clear()
            self.command_logs.clear()
            self.pytest_stdout_log = None
            self.pytest_stderr_log = None
            
            coverage_output = self.project_root / "coverage.json"
            # Build coverage arguments dynamically from core modules
            cov_args = []
            for module in self.core_modules:
                # Validate module name before adding to arguments
                if not module or not module.strip():
                    error_msg = f"Invalid empty module name in core_modules: {self.core_modules}"
                    if logger:
                        logger.error(error_msg)
                    raise ValueError(error_msg)
                cov_args.extend(['--cov', module.strip()])
            
            # Validate no empty --cov arguments were created
            if '--cov' in cov_args and cov_args.index('--cov') < len(cov_args) - 1:
                # Check if any --cov is followed by another --cov (empty argument)
                for i in range(len(cov_args) - 1):
                    if cov_args[i] == '--cov' and cov_args[i + 1] == '--cov':
                        error_msg = f"Detected empty --cov argument in command construction. cov_args: {cov_args}"
                        if logger:
                            logger.error(error_msg)
                        raise ValueError(error_msg)
            
            cmd = [
                sys.executable, '-m', 'pytest',
            ]
            
            # Add parallel execution if enabled
            if self.parallel:
                # Exclude no_parallel tests from parallel execution (they should run separately in serial mode)
                # This matches the behavior in run_tests.py to prevent flaky failures
                cmd.extend(['-m', 'not no_parallel'])
                cmd.extend(['-n', self.num_workers])
                # Use loadscope distribution to group tests by file/class for better isolation
                # This reduces race conditions by keeping related tests together
                cmd.extend(['--dist=loadscope'])
                if logger:
                    logger.info(f"Using parallel execution with {self.num_workers} workers (loadscope distribution), excluding no_parallel tests")
            
            cmd.extend([
                *cov_args,
                '--cov-report=term-missing',
                f'--cov-report=json:{coverage_output.resolve()}',
                '--cov-config=coverage.ini',
                '--tb=line',  # Use line format for cleaner parallel output
                '-q',  # Quiet mode - reduces output noise
                '--maxfail=5',
                'tests/'
            ])
            
            # Check for problematic environment variables
            pytest_addopts = os.environ.get('PYTEST_ADDOPTS', '')
            if pytest_addopts and '--cov' in pytest_addopts:
                warning_msg = f"PYTEST_ADDOPTS contains --cov which may conflict: {pytest_addopts}"
                if logger:
                    logger.warning(warning_msg)
            
            env = os.environ.copy()
            env['COVERAGE_FILE'] = str(self.coverage_data_file)
            
            # Log the full command for debugging (single log entry instead of truncated + full)
            if logger:
                logger.info(f"Running pytest coverage command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env,
                timeout=1800  # 30 minute timeout for full test suite with coverage
            )
            
            # Log if the command completed too quickly (suspicious)
            if result.returncode is not None and logger:
                if not result.stdout or len(result.stdout) < 100:
                    logger.warning(f"Pytest completed very quickly with minimal output - may not have run tests properly")
                    if result.stderr:
                        logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            self._record_pytest_output(result)
            
            # Check if pytest actually ran by looking at log files (pytest with -q may not output to stdout)
            # Also check stdout/stderr for output indicators
            pytest_ran = False
            log_content = ""
            if self.pytest_stdout_log and self.pytest_stdout_log.exists():
                log_content = self.pytest_stdout_log.read_text(encoding='utf-8', errors='ignore')
                pytest_ran = bool(
                    'TOTAL' in log_content or 
                    'passed' in log_content.lower() or 
                    'failed' in log_content.lower() or
                    '[  ' in log_content or
                    'coverage:' in log_content.lower() or
                    'ERROR' in log_content or
                    'FAILED' in log_content
                )
            
            # Also check stdout/stderr if available
            if not pytest_ran and result.stdout:
                stdout_check = bool(
                    'TOTAL' in result.stdout or 
                    'passed' in result.stdout.lower() or 
                    '[  ' in result.stdout or
                    'coverage:' in result.stdout.lower()
                )
                if stdout_check:
                    pytest_ran = True
                    log_content = result.stdout
            
            # If we still don't have log content but pytest ran (based on return code or log file existence), use stdout
            if not log_content and (pytest_ran or result.returncode is not None):
                log_content = result.stdout or ""
            
            # Parse test results from log file if available, otherwise from stdout
            test_output = log_content if log_content else (result.stdout or "")
            test_results = self._parse_pytest_test_results(test_output)
            
            # Parse coverage from log file if available, otherwise from stdout
            coverage_output_text = log_content if log_content else (result.stdout or "")
            if self.analyzer:
                coverage_data = self.analyzer.parse_coverage_output(coverage_output_text)
            else:
                coverage_data = {}
            # Only use existing coverage.json as fallback if pytest actually ran but didn't produce output
            coverage_collected = bool(coverage_data)
            
            if not coverage_data and coverage_output.exists() and pytest_ran:
                if self.analyzer:
                    coverage_data = self.analyzer.load_coverage_json(coverage_output)
                else:
                    coverage_data = {}
                coverage_collected = bool(coverage_data)
            elif not pytest_ran and logger:
                logger.warning("Pytest appears not to have run - no test output detected in stdout or log files")
                if result.stderr:
                    logger.warning(f"Pytest stderr: {result.stderr[:500]}")
                if self.pytest_stderr_log and self.pytest_stderr_log.exists():
                    stderr_content = self.pytest_stderr_log.read_text(encoding='utf-8', errors='ignore')
                    if stderr_content:
                        logger.warning(f"Pytest stderr from log (first 500 chars): {stderr_content[:500]}")
            
            if self.analyzer:
                overall_coverage = self.analyzer.extract_overall_coverage(coverage_output_text)
            else:
                overall_coverage = {}
            # Always try to load from JSON file if it exists and pytest ran, as it's more accurate
            if coverage_output.exists() and pytest_ran:
                if self.analyzer:
                    json_data = self.analyzer.load_coverage_json(coverage_output)
                else:
                    json_data = {}
                if json_data:
                    # Recalculate overall from JSON data
                    total_statements = sum(f.get('statements', 0) for f in json_data.values())
                    total_covered = sum(f.get('covered', 0) for f in json_data.values())
                    if total_statements > 0:
                        overall_coverage['overall_coverage'] = round((total_covered / total_statements) * 100, 1)
                        overall_coverage['total_statements'] = total_statements
                        overall_coverage['total_missed'] = total_statements - total_covered
                    if not coverage_data:
                        coverage_data = json_data
            elif not overall_coverage.get('overall_coverage') and coverage_output.exists() and pytest_ran:
                if self.analyzer:
                    overall_coverage = self.analyzer.extract_overall_from_json(coverage_output)
                    coverage_collected = bool(overall_coverage.get('overall_coverage'))
            
            # Enhanced error detection and reporting
            if result.returncode != 0:
                # Distinguish between coverage collection failures and test failures
                if coverage_collected:
                    # Coverage was collected successfully, but tests failed
                    if logger:
                        logger.warning("Coverage data collected successfully, but some tests failed")
                    
                    # Report test failures separately
                    if test_results['failed_count'] > 0:
                        failure_msg = f"Test failures detected ({test_results['failed_count']} failed, {test_results['passed_count']} passed)"
                        if test_results['random_seed']:
                            failure_msg += f" (random seed: {test_results['random_seed']})"
                        
                        if logger:
                            logger.warning(failure_msg)
                            logger.warning(f"Test summary: {test_results['test_summary']}")
                        
                        if test_results['failed_tests']:
                            if logger:
                                logger.warning("Failed tests:")
                                for test_name in test_results['failed_tests']:
                                    logger.warning(f"  - {test_name}")
                        else:
                            if logger:
                                logger.warning(f"  See {self.pytest_stdout_log} for detailed test failure information")
                else:
                    # Coverage collection failed
                    error_details = []
                    
                    # Check for common error patterns
                    stderr_lower = result.stderr.lower() if result.stderr else ''
                    stdout_lower = result.stdout.lower() if result.stdout else ''
                    
                    if 'unrecognized arguments' in stderr_lower or 'unrecognized arguments' in stdout_lower:
                        error_details.append("Unrecognized arguments error detected")
                        # Extract the problematic arguments from stderr
                        if result.stderr:
                            for line in result.stderr.split('\n'):
                                if 'unrecognized arguments' in line.lower():
                                    error_details.append(f"  Problematic arguments: {line.strip()}")
                    
                    # Check for empty --cov pattern: "--cov --cov" (two --cov in a row)
                    if result.stderr and '--cov' in result.stderr:
                        stderr_parts = result.stderr.split()
                        for i in range(len(stderr_parts) - 1):
                            if stderr_parts[i] == '--cov' and stderr_parts[i + 1] == '--cov':
                                error_details.append("Detected empty --cov argument in pytest error output")
                                break
                    
                    if 'error: usage' in stderr_lower:
                        error_details.append("Pytest usage/argument error detected")
                    
                    error_msg = f"Coverage analysis failed (exit code {result.returncode})"
                    if error_details:
                        error_msg += ":\n  - " + "\n  - ".join(error_details)
                    error_msg += f"\n  See {self.pytest_stderr_log} for full stderr output"
                    cmd_str = ' '.join(cmd)  # Convert command list to string for error message
                    error_msg += f"\n  Command: {cmd_str}"
                    
                    if logger:
                        logger.error(error_msg)
                    else:
                        print(f"ERROR: {error_msg}")
            else:
                # All tests passed
                if logger and test_results['test_summary']:
                    logger.info(f"All tests passed: {test_results['test_summary']}")
                    if test_results['random_seed']:
                        logger.info(f"Random seed used: {test_results['random_seed']}")
            
            try:
                if self.report_generator:
                    self.report_generator.finalize_coverage_outputs()
                else:
                    # Fallback to old method if report generator not available
                    self._finalize_coverage_outputs_fallback()
            except Exception as finalize_error:
                if logger:
                    logger.warning(f"Failed to finalize coverage artefacts: {finalize_error}")
            
            return {
                'modules': coverage_data,
                'overall': overall_coverage,
                'test_results': test_results,
                'coverage_collected': coverage_collected and pytest_ran,  # Only true if pytest actually ran
                'pytest_ran': pytest_ran,  # Track whether pytest actually executed
                'logs': {
                    'stdout': str(self.pytest_stdout_log) if self.pytest_stdout_log else None,
                    'stderr': str(self.pytest_stderr_log) if self.pytest_stderr_log else None,
                },
                'archived_directories': self.archived_directories,
                'command_logs': [str(path) for path in self.command_logs]
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            if logger:
                logger.error(f"Error running coverage analysis: {e}")
                logger.error(f"Traceback: {error_trace}")
            else:
                print(f"Error running coverage analysis: {e}")
                print(f"Traceback: {error_trace}")
            # Return error info instead of empty dict so caller knows something went wrong
            return {
                'error': str(e),
                'traceback': error_trace,
                'modules': {},
                'overall': {},
                'coverage_collected': False
            }

    def run_dev_tools_coverage(self) -> Dict[str, Dict[str, any]]:
        """Run pytest coverage analysis specifically for development_tools directory."""
        if logger:
            logger.info("Running pytest coverage analysis for development_tools...")
        
        try:
            coverage_output = self.dev_tools_coverage_json
            coverage_output.parent.mkdir(parents=True, exist_ok=True)
            
            # Coverage only for development_tools directory
            # Note: coverage_output path is relative to project_root, so we need to make it absolute
            coverage_output_abs = coverage_output.resolve()
            dev_cov_config = self.dev_tools_coverage_config_path if self.dev_tools_coverage_config_path.exists() else self.coverage_config_path
            cmd = [
                sys.executable, '-m', 'pytest',
                '--cov=development_tools',
                '--cov-report=term-missing',
                f'--cov-report=json:{coverage_output_abs}',
                f'--cov-config={dev_cov_config}',
                '--tb=line',
                '-q',
                '--maxfail=10',  # Allow more failures before stopping (some tests may be flaky)
                '--continue-on-collection-errors',  # Continue even if collection fails
                'tests/development_tools/'
            ]
            
            if logger:
                logger.info(f"Running dev tools coverage command: {' '.join(cmd[:5])} ...")
            
            env = os.environ.copy()
            # Set COVERAGE_FILE to absolute path to ensure files are created in the correct location
            env['COVERAGE_FILE'] = str(self.dev_tools_coverage_data_file.resolve())
            if dev_cov_config and dev_cov_config.exists():
                env['COVERAGE_RCFILE'] = str(dev_cov_config.resolve())
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env
            )
            
            # Parse coverage results (even if pytest exited with non-zero code, coverage may still be available)
            if self.analyzer:
                coverage_data = self.analyzer.parse_coverage_output(result.stdout)
            else:
                coverage_data = {}
            if not coverage_data and coverage_output.exists():
                if self.analyzer:
                    coverage_data = self.analyzer.load_coverage_json(coverage_output)
            
            if self.analyzer:
                overall_coverage = self.analyzer.extract_overall_coverage(result.stdout)
            else:
                overall_coverage = {}
            if not overall_coverage.get('overall_coverage') and coverage_output.exists():
                if self.analyzer:
                    overall_coverage = self.analyzer.extract_overall_from_json(coverage_output)
            
            # Log status after attempting to extract coverage
            if result.returncode != 0:
                if logger:
                    # If we successfully extracted coverage, this is just test failures (not a coverage problem)
                    if overall_coverage.get('overall_coverage') or coverage_data:
                        logger.info(f"Dev tools coverage pytest completed with exit code {result.returncode} (some tests failed, but coverage data was successfully collected: {overall_coverage.get('overall_coverage', 'N/A')}%)")
                    else:
                        logger.warning(f"Dev tools coverage pytest exited with code {result.returncode} and no coverage data could be extracted")
                        if result.stderr:
                            logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            # If still no coverage data, check if the file was created
            if not overall_coverage.get('overall_coverage') and not coverage_output.exists():
                if logger:
                    logger.warning(f"Coverage JSON file not created at {coverage_output}")
                    logger.info(f"Pytest return code: {result.returncode}")
                    if result.stdout:
                        # Look for coverage summary in stdout
                        if 'TOTAL' in result.stdout:
                            logger.info("Coverage data found in stdout but JSON not created")
                        logger.debug(f"Pytest stdout (last 500 chars): {result.stdout[-500:]}")
                    if result.stderr:
                        logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            # Clean up temporary coverage data files after generating report
            self._cleanup_coverage_data_files()
            
            if logger:
                if overall_coverage.get('overall_coverage'):
                    logger.info(f"Dev tools coverage: {overall_coverage.get('overall_coverage', 0):.1f}%")
                else:
                    logger.warning("Dev tools coverage data not available")
            
            return {
                'modules': coverage_data,
                'overall': overall_coverage,
                'coverage_collected': bool(coverage_data) or coverage_output.exists(),
                'output_file': str(coverage_output),
                'html_dir': None  # HTML reports disabled
            }
            
        except Exception as e:
            if logger:
                logger.error(f"Error running dev tools coverage analysis: {e}")
            else:
                print(f"Error running dev tools coverage analysis: {e}")
            return {}

    def _cleanup_coverage_data_files(self) -> None:
        """Clean up temporary .coverage_dev_tools.* files after coverage analysis."""
        tests_dir = self.project_root / "development_tools" / "tests"
        root_dir = self.project_root / "development_tools"
        
        cleanup_count = 0
        
        # Clean up files in tests directory (current location)
        if tests_dir.exists():
            for coverage_file in tests_dir.glob(".coverage_dev_tools.*"):
                try:
                    coverage_file.unlink()
                    cleanup_count += 1
                except Exception as exc:
                    if logger:
                        logger.warning(f"Failed to clean up {coverage_file}: {exc}")
        
        # Clean up legacy files in root directory (old location)
        if root_dir.exists():
            for coverage_file in root_dir.glob(".coverage_dev_tools*"):
                try:
                    # Skip if it's a directory
                    if coverage_file.is_file():
                        coverage_file.unlink()
                        cleanup_count += 1
                except Exception as exc:
                    if logger:
                        logger.warning(f"Failed to clean up legacy file {coverage_file}: {exc}")
        
        # Also clean up the base .coverage_dev_tools file (without process ID) in tests directory
        if tests_dir.exists():
            base_file = tests_dir / ".coverage_dev_tools"
            if base_file.exists() and base_file.is_file():
                try:
                    base_file.unlink()
                    cleanup_count += 1
                except Exception as exc:
                    if logger:
                        logger.warning(f"Failed to clean up base coverage file {base_file}: {exc}")
        
        if cleanup_count > 0 and logger:
            logger.info(f"Cleaned up {cleanup_count} temporary coverage data file(s)")

    def _parse_pytest_test_results(self, stdout: str) -> Dict[str, Any]:
        """Parse pytest output to extract test results, failures, and random seed."""
        results = {
            'random_seed': None,
            'test_summary': None,
            'failed_tests': [],
            'passed_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'warnings_count': 0,
            'total_tests': 0
        }
        
        if not stdout:
            return results
        
        # Extract random seed if pytest-randomly is used
        seed_pattern = r'--randomly-seed=(\d+)'
        seed_match = re.search(seed_pattern, stdout)
        if seed_match:
            results['random_seed'] = seed_match.group(1)
        
        # Extract test summary (e.g., "4 failed, 2276 passed, 1 skipped, 4 warnings")
        summary_pattern = r'(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+(\d+)\s+skipped[,\s]+(\d+)\s+warnings'
        summary_match = re.search(summary_pattern, stdout)
        if summary_match:
            results['failed_count'] = int(summary_match.group(1))
            results['passed_count'] = int(summary_match.group(2))
            results['skipped_count'] = int(summary_match.group(3))
            results['warnings_count'] = int(summary_match.group(4))
            results['total_tests'] = results['failed_count'] + results['passed_count'] + results['skipped_count']
            results['test_summary'] = f"{results['failed_count']} failed, {results['passed_count']} passed, {results['skipped_count']} skipped, {results['warnings_count']} warnings"
        
        # Extract failed test names from "FAILED" section
        failed_section_pattern = r'FAILED\s+(.+?)(?=\n\n|\n===|$)'
        failed_matches = re.findall(failed_section_pattern, stdout, re.DOTALL)
        
        # Also look for "short test summary info" section
        short_summary_pattern = r'short test summary info[^\n]*\n(.*?)(?=\n===|$)'
        short_summary_match = re.search(short_summary_pattern, stdout, re.DOTALL)
        if short_summary_match:
            summary_lines = short_summary_match.group(1).strip().split('\n')
            for line in summary_lines:
                if line.strip().startswith('FAILED'):
                    # Extract test path from "FAILED tests/path/to/test.py::test_function"
                    test_match = re.search(r'FAILED\s+(.+)', line)
                    if test_match:
                        results['failed_tests'].append(test_match.group(1).strip())
        
        return results
    
    def _record_pytest_output(self, result: subprocess.CompletedProcess) -> None:
        """Persist pytest stdout/stderr for troubleshooting."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
        
        stdout_content = result.stdout or ""
        stderr_content = result.stderr or ""
        
        stdout_path = self.coverage_logs_dir / f"pytest_stdout_{timestamp}.log"
        stderr_path = self.coverage_logs_dir / f"pytest_stderr_{timestamp}.log"
        stdout_latest = self.coverage_logs_dir / "pytest_stdout.latest.log"
        stderr_latest = self.coverage_logs_dir / "pytest_stderr.latest.log"
        
        stdout_path.write_text(stdout_content, encoding='utf-8', errors='ignore')
        stderr_path.write_text(stderr_content, encoding='utf-8', errors='ignore')
        stdout_latest.write_text(stdout_content, encoding='utf-8', errors='ignore')
        stderr_latest.write_text(stderr_content, encoding='utf-8', errors='ignore')
        
        self.pytest_stdout_log = stdout_path
        self.pytest_stderr_log = stderr_path
        
        if logger:
            logger.info(f"Saved pytest output to {stdout_path} and {stderr_path}")
    
    def _finalize_coverage_outputs_fallback(self) -> None:
        """Fallback method for finalizing coverage outputs if report generator is not available."""
        # This is a minimal fallback - ideally the report generator should always be available
        if logger:
            logger.warning("Using fallback coverage finalization - report generator not available")
    
    def _generate_coverage_summary_fallback(self, coverage_data: Dict[str, Dict[str, any]], 
                                            overall_data: Dict[str, any]) -> str:
        """Fallback method for generating coverage summary if report generator is not available."""
        # This is a minimal fallback - ideally the report generator should always be available
        if logger:
            logger.warning("Using fallback coverage summary generation - report generator not available")
        return f"Overall Coverage: {overall_data.get('overall_coverage', 0):.1f}%"
    
    def update_coverage_plan(self, coverage_summary: str) -> bool:
        """Update the TEST_COVERAGE_EXPANSION_PLAN.md with new metrics."""
        generated_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Standard generated header
        standard_header = f"""# Test Coverage Expansion Plan

> **File**: `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: {generated_timestamp}
> **Source**: `python development_tools/tests/generate_test_coverage.py --update-plan` - Coverage Metrics Regenerator

"""
        
        if not self.coverage_plan_file.exists():
            # Create new file with standard header
            try:
                with open(self.coverage_plan_file, 'w', encoding='utf-8') as f:
                    f.write(standard_header)
                    f.write("## Current Status\n\n")
                    f.write(coverage_summary)
                    f.write("\n")
                if logger:
                    logger.info(f"Created coverage plan with standard header: {self.coverage_plan_file}")
                return True
            except Exception as e:
                if logger:
                    logger.error(f"Error creating coverage plan: {e}")
                return False
            
        try:
            with open(self.coverage_plan_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has standard generated header
            has_standard_header = (
                '> **File**: `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`' in content and
                '> **Generated**: This file is auto-generated' in content and
                '> **Generated by**: generate_test_coverage.py' in content
            )
            
            # Find and replace the current status section
            section_header = "## Current Status"
            current_status_pattern = r'(## Current Status.*?)(?=\n## |\Z)'
            
            new_status_section = f"{section_header}\n\n{coverage_summary}\n"
            
            if has_standard_header:
                # File has standard header - just update the status section and timestamp
                if re.search(current_status_pattern, content, re.DOTALL):
                    updated_content = re.sub(
                        current_status_pattern,
                        lambda _: new_status_section,
                        content,
                        flags=re.DOTALL
                    )
                else:
                    # Add status section after header
                    header_end = content.find('\n## ')
                    if header_end == -1:
                        header_end = len(content)
                    updated_content = content[:header_end] + '\n\n' + new_status_section + content[header_end:]
                
                # Update the last generated timestamp
                timestamp_pattern = r'(> \*\*Last Generated\*\*: ).*'
                if re.search(timestamp_pattern, updated_content):
                    updated_content = re.sub(
                        timestamp_pattern,
                        lambda match: f"{match.group(1)}{generated_timestamp}",
                        updated_content
                    )
            else:
                # File doesn't have standard header - replace with standard header
                # Find the title
                title_match = re.search(r'^# Test Coverage Expansion Plan.*?\n', content, re.MULTILINE)
                if title_match:
                    # Replace everything from title to first section with standard header
                    title_end = title_match.end()
                    first_section_match = re.search(r'\n## ', content[title_end:])
                    if first_section_match:
                        section_start = title_end + first_section_match.start()
                        updated_content = standard_header + content[section_start:]
                    else:
                        updated_content = standard_header + content[title_end:]
                else:
                    # No title found, prepend standard header
                    updated_content = standard_header + content
                
                # Ensure status section exists
                if '## Current Status' not in updated_content:
                    updated_content = updated_content.rstrip() + '\n\n' + new_status_section
                else:
                    # Replace existing status section
                    updated_content = re.sub(
                        current_status_pattern,
                        lambda _: new_status_section,
                        updated_content,
                        flags=re.DOTALL
                    )
            
            # Write updated content
            with open(self.coverage_plan_file, 'w', encoding='utf-8') as plan_file:
                plan_file.write(updated_content)
                
            if logger:
                logger.info(f"Updated coverage plan: {self.coverage_plan_file}")
            return True
            
        except Exception as e:
            if logger:
                logger.error(f"Error updating coverage plan: {e}")
            return False
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in the format used by the plan."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def run(self, update_plan: bool = False) -> Dict[str, any]:
        """Run the coverage metrics regeneration."""
        logger.info("Starting coverage metrics regeneration...")
        
        # Run coverage analysis
        coverage_results = self.run_coverage_analysis()
        
        if not coverage_results:
            logger.error("Failed to get coverage data - run_coverage_analysis returned empty result")
            return {}
        
        # Check if coverage was actually collected (not just using stale data)
        if not coverage_results.get('coverage_collected', False):
            logger.error("Coverage analysis completed but no coverage data was collected - tests may not have run")
            if coverage_results.get('error'):
                logger.error(f"Error from coverage analysis: {coverage_results.get('error')}")
            return {}
        
        # Generate summary
        if self.report_generator:
            coverage_summary = self.report_generator.generate_coverage_summary(
                coverage_results['modules'], 
                coverage_results['overall']
            )
        else:
            # Fallback to old method if report generator not available
            coverage_summary = self._generate_coverage_summary_fallback(
                coverage_results['modules'], 
                coverage_results['overall']
            )
        
        # Print summary (headers removed - added by consolidated report)
        print(coverage_summary)
        
        # Update plan if requested
        if update_plan:
            success = self.update_coverage_plan(coverage_summary)
            if success:
                print("\n* Coverage plan updated successfully!")
            else:
                print("\n* Failed to update coverage plan")
        
        return coverage_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Regenerate test coverage metrics")
    parser.add_argument('--update-plan', action='store_true', 
                       help='Update TEST_COVERAGE_EXPANSION_PLAN.md with new metrics')
    parser.add_argument('--output-file', help='Output file for coverage report (optional)')
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel test execution (parallel enabled by default)')
    parser.add_argument('--workers', default='auto',
                       help="Number of parallel workers (default: 'auto' to let pytest-xdist decide, or specify a number)")
    
    args = parser.parse_args()
    
    # Only use num_workers if parallel is enabled
    parallel_enabled = not args.no_parallel
    regenerator = CoverageMetricsRegenerator(
        parallel=parallel_enabled,
        num_workers=args.workers if parallel_enabled else None
    )
    results = regenerator.run(update_plan=args.update_plan)
    
    if args.output_file and results:
        # Save detailed results to JSON file
        output_path = Path(args.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(results, f, indent=2)
        print(f"\n📊 Detailed coverage data saved to: {output_path}")


if __name__ == "__main__":
    main()
