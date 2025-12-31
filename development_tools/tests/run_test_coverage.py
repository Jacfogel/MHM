#!/usr/bin/env python3
# TOOL_TIER: core

"""
Test Coverage Execution Tool (Portable)

This script orchestrates pytest execution with coverage collection and generates
coverage data files. It runs the actual test suite and collects coverage metrics.

NOTE: This tool EXECUTES tests and GENERATES coverage data. For pure analysis of
existing coverage data, use analyze_test_coverage.py instead.

It is configurable via development_tools_config.json to work with any project's
test setup and coverage configuration.

Usage:
    python tests/run_test_coverage.py [--output-file]
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
    from development_tools.tests.generate_test_coverage_report import TestCoverageReportGenerator
except ImportError:
    # Fallback for relative imports
    try:
        from .analyze_test_coverage import TestCoverageAnalyzer
        from .generate_test_coverage_report import TestCoverageReportGenerator
    except ImportError:
        TestCoverageAnalyzer = None
        TestCoverageReportGenerator = None

# Load external config on module import (safe to call multiple times)
config.load_external_config()

logger = get_component_logger("development_tools")

class CoverageMetricsRegenerator:
    """
    Executes test suite with coverage collection and regenerates coverage metrics.
    
    This class orchestrates pytest execution to run tests and collect coverage data.
    It does NOT analyze coverage data - for analysis, use TestCoverageAnalyzer
    from analyze_test_coverage.py.
    
    Portable across projects via external configuration.
    """
    
    def __init__(self, project_root: str = ".", parallel: bool = True, num_workers: Optional[str] = None,
                 pytest_command: Optional[List[str]] = None, coverage_config: Optional[str] = None,
                 artifact_directories: Optional[Dict[str, str]] = None, maxfail: Optional[int] = None):
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
            maxfail: Optional maximum number of test failures before stopping (default: 10).
                    If None, loads from config or uses default of 10.
        """
        self.project_root = Path(project_root).resolve()
        
        # Load coverage configuration from external config
        coverage_config_data = config.get_external_value('coverage', {})
        
        # Get maxfail threshold (from parameter, config, or default)
        if maxfail is not None:
            self.maxfail = maxfail
        else:
            self.maxfail = coverage_config_data.get('maxfail', 10)
        
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
        # Replace --maxfail in base args if present, otherwise add it
        base_args = coverage_config_data.get('pytest_base_args', [
            '--cov-report=term-missing',
            '--tb=line',
            '-q',
            '--maxfail=10'
        ])
        # Update maxfail in base args if it exists, otherwise add it
        self.pytest_base_args = []
        maxfail_added = False
        for arg in base_args:
            if arg.startswith('--maxfail='):
                self.pytest_base_args.append(f'--maxfail={self.maxfail}')
                maxfail_added = True
            else:
                self.pytest_base_args.append(arg)
        if not maxfail_added:
            self.pytest_base_args.append(f'--maxfail={self.maxfail}')
        
        # Test directory (from config or default)
        self.test_directory = coverage_config_data.get('test_directory', 'tests/')
        
        # Coverage config path (from parameter, config, or default)
        if coverage_config is not None:
            self.coverage_config_path = self.project_root / coverage_config
        else:
            # Check for coverage.ini in development_tools/tests first (new location), then root (legacy)
            config_path = coverage_config_data.get('coverage_config', 'development_tools/tests/coverage.ini')
            self.coverage_config_path = self.project_root / config_path
            if not self.coverage_config_path.exists():
                # Fall back to root location for backward compatibility
                self.coverage_config_path = self.project_root / "coverage.ini"
        
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
                    'logs': 'development_tools/tests/logs',
                    'dev_tools_html': None  # Disabled - no longer generating dev tools HTML
                }
        
        # Set up paths from artifact directories
        self.coverage_data_file: Path = self.project_root / ".coverage"
        self.coverage_html_dir: Path = self.project_root / self.artifact_dirs.get('html_output', 'htmlcov')
        self.coverage_logs_dir: Path = self.project_root / self.artifact_dirs.get('logs', 'development_tools/tests/logs')
        self.archive_root: Path = self.project_root / self.artifact_dirs.get('archive', 'development_tools/reports/archive/coverage_artifacts')
        
        # Dev tools specific coverage paths
        self.dev_tools_coverage_config_path: Path = self.project_root / "development_tools" / "tests" / "coverage_dev_tools.ini"
        self.dev_tools_coverage_data_file: Path = self.project_root / "development_tools" / "tests" / ".coverage_dev_tools"
        # Store coverage_dev_tools.json in development_tools/tests/jsons/
        jsons_dir = self.project_root / "development_tools" / "tests" / "jsons"
        jsons_dir.mkdir(parents=True, exist_ok=True)
        self.dev_tools_coverage_json: Path = jsons_dir / "coverage_dev_tools.json"
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
                from development_tools.tests.generate_test_coverage_report import TestCoverageReportGenerator as ReportGeneratorClass
                report_generator_class = ReportGeneratorClass
            except ImportError:
                try:
                    from .generate_test_coverage_report import TestCoverageReportGenerator as ReportGeneratorClass
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
        # data_file paths in coverage.ini are relative to project root (where pytest runs from)
        data_file = coverage_ini.get('run', 'data_file', fallback='').strip()
        if data_file:
            # Resolve relative to project root, not config file location
            self.coverage_data_file = (self.project_root / data_file).resolve()
        
        html_directory = coverage_ini.get('html', 'directory', fallback='').strip()
        if html_directory:
            # HTML directory paths are also relative to project root
            self.coverage_html_dir = (self.project_root / html_directory).resolve()
        
        # Ensure parent directories exist when we later write artefacts
        self.coverage_data_file.parent.mkdir(parents=True, exist_ok=True)
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_python_path_in_env(self, env: Dict[str, str]) -> Dict[str, str]:
        """Ensure PATH includes Python executable's directory for Windows DLL resolution.
        
        On Windows, subprocesses may fail with STATUS_DLL_NOT_FOUND (0xC0000135) if PATH
        doesn't include the Python executable's directory. This helper ensures PATH is
        set correctly for subprocess execution.
        
        Args:
            env: Environment dictionary (typically from os.environ.copy())
            
        Returns:
            Modified environment dictionary with PATH updated if needed
        """
        if sys.platform == 'win32':
            python_exe = Path(sys.executable)
            python_dir = str(python_exe.parent)
            current_path = env.get('PATH', '')
            
            # Add Python directory to PATH if not already present
            if python_dir not in current_path:
                # Prepend to ensure Python DLLs are found first
                env['PATH'] = f"{python_dir};{current_path}" if current_path else python_dir
        
        return env

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
        
        # Load coverage configuration from external config
        coverage_config_data = config.get_external_value('coverage', {})
        
        try:
            self.archived_directories.clear()
            self.command_logs.clear()
            self.pytest_stdout_log = None
            self.pytest_stderr_log = None
            
            # Store coverage.json in development_tools/tests/jsons/ instead of root
            jsons_dir = self.project_root / "development_tools" / "tests" / "jsons"
            jsons_dir.mkdir(parents=True, exist_ok=True)
            coverage_output = jsons_dir / "coverage.json"
            # Ensure directory exists
            coverage_output.parent.mkdir(parents=True, exist_ok=True)
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
                # Exclude no_parallel and e2e tests from parallel execution
                # no_parallel tests run separately in serial mode
                # e2e tests are slow and excluded from regular runs (per pytest.ini)
                # This matches the behavior in run_tests.py to prevent flaky failures
                cmd.extend(['-m', 'not (no_parallel or e2e)'])
                cmd.extend(['-n', self.num_workers])
                # Use loadscope distribution to group tests by file/class for better isolation
                # This reduces race conditions by keeping related tests together
                cmd.extend(['--dist=loadscope'])
                if logger:
                    logger.info(f"Using parallel execution with {self.num_workers} workers (loadscope distribution), excluding no_parallel tests")
            
            # When running in parallel mode, we'll combine coverage later, so don't generate JSON yet
            # When running in serial mode, generate JSON directly
            if self.parallel:
                # Don't generate JSON for parallel run - we'll combine coverage data files and regenerate JSON
                cmd.extend([
                    *cov_args,
                    '--cov-report=term-missing',
                    f'--cov-config={self.coverage_config_path.relative_to(self.project_root)}',
                    '--tb=line',  # Use line format for cleaner parallel output
                    '-q',  # Quiet mode - reduces output noise
                    f'--maxfail={self.maxfail}',
                    # Ignore temp directories to prevent collecting tests from temp files
                    '--ignore=tests/data/pytest-tmp-*',
                    '--ignore=tests/data/pytest-of-*',
                    'tests/'
                ])
            else:
                # Serial mode - generate JSON directly
                cmd.extend([
                    *cov_args,
                    '--cov-report=term-missing',
                    f'--cov-report=json:{coverage_output.resolve()}',
                    f'--cov-config={self.coverage_config_path.relative_to(self.project_root)}',
                    '--tb=line',
                    '-q',
                    f'--maxfail={self.maxfail}',
                    # Ignore temp directories to prevent collecting tests from temp files
                    '--ignore=tests/data/pytest-tmp-*',
                    '--ignore=tests/data/pytest-of-*',
                    'tests/'
                ])
            
            # Note: When using --cov-config, pytest-cov may still use the data_file from the config
            # even if COVERAGE_FILE is set. We need to ensure the coverage files are created in the
            # location we specify. The COVERAGE_FILE env var should override, but we'll verify after execution.
            
            # Check for problematic environment variables
            pytest_addopts = os.environ.get('PYTEST_ADDOPTS', '')
            if pytest_addopts and '--cov' in pytest_addopts:
                warning_msg = f"PYTEST_ADDOPTS contains --cov which may conflict: {pytest_addopts}"
                if logger:
                    logger.warning(warning_msg)
            
            # Use separate coverage data files for parallel and no_parallel runs, then combine them
            # This allows us to run no_parallel tests separately and merge their coverage
            # Only needed when parallel execution is enabled
            # Note: coverage.ini may specify data_file location, so we need to use the same directory
            parallel_coverage_file = None
            no_parallel_coverage_file = None
            if self.parallel:
                # Use the same directory as the main coverage file (respects coverage.ini data_file setting)
                parallel_coverage_file = self.coverage_data_file.parent / ".coverage_parallel"
                no_parallel_coverage_file = self.coverage_data_file.parent / ".coverage_no_parallel"
            
            env = os.environ.copy()
            # Ensure PATH includes Python executable's directory for Windows DLL resolution
            env = self._ensure_python_path_in_env(env)
            if self.parallel:
                # CRITICAL: Set COVERAGE_FILE to .coverage_parallel (not .coverage) so shard files aren't auto-combined
                # pytest-xdist workers will create .coverage_parallel.worker0, .coverage_parallel.worker1, etc.
                # in the same directory. If we used .coverage, pytest-cov would auto-combine them at the end.
                # We need the shard files to remain separate so we can combine them with no_parallel coverage.
                env['COVERAGE_FILE'] = str(parallel_coverage_file.resolve())
                # Also set COVERAGE_RCFILE to ensure workers use the same config
                if self.coverage_config_path.exists():
                    env['COVERAGE_RCFILE'] = str(self.coverage_config_path.resolve())
                if logger:
                    logger.debug(f"Set COVERAGE_FILE={env['COVERAGE_FILE']} for parallel execution (shard files will be created as .coverage_parallel.worker* in {parallel_coverage_file.parent})")
            else:
                env['COVERAGE_FILE'] = str(self.coverage_data_file.resolve())
            
            # Set unique pytest temp directory to avoid conflicts when running in parallel with dev tools coverage
            # Use a unique identifier based on process/coverage type to ensure isolation
            import uuid
            unique_id = f"main_{uuid.uuid4().hex[:8]}"
            pytest_temp_base = self.project_root / "tests" / "data" / f"pytest-tmp-{unique_id}"
            pytest_temp_base.mkdir(parents=True, exist_ok=True)
            # Set PYTEST_CACHE_DIR to ensure pytest uses unique cache directory
            env['PYTEST_CACHE_DIR'] = str(pytest_temp_base / ".pytest_cache")
            # Also set basetemp via command line argument for tmpdir fixture
            cmd.append(f'--basetemp={pytest_temp_base}')
            
            # Log the full command for debugging (single log entry instead of truncated + full)
            if logger:
                logger.debug(f"Running pytest coverage command: {' '.join(cmd)}")
            
            # Get timeout from config, with sensible defaults
            # Coverage collection adds overhead, so tests take longer than normal runs
            # Normal test runs take ~5 minutes, with coverage they may take 7-10 minutes
            # Default: 12 minutes (720 seconds) to allow for coverage overhead and system variations
            # Configurable via development_tools_config.json: {"coverage": {"pytest_timeout": 720}}
            pytest_timeout = coverage_config_data.get('pytest_timeout', 720)  # 12 minutes default
            if logger:
                logger.info(f"Pytest timeout set to {pytest_timeout // 60} minutes")
            
            # Create log files BEFORE running subprocess so we can see output even if it hangs
            # Only create stdout log - user doesn't use stderr logs
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Rotate old log files before creating new ones (keep 1 current + 7 archived = 8 total)
            self._rotate_log_files('pytest_parallel_stdout', max_versions=8)
            
            stdout_log_path = self.coverage_logs_dir / f"pytest_parallel_stdout_{timestamp}.log"
            self.pytest_stdout_log = stdout_log_path  # Keep variable name for backward compatibility
            self.pytest_stderr_log = None  # No longer creating stderr logs
            
            # Redirect output directly to files instead of capturing to avoid buffering/deadlock issues
            # This allows us to see progress even if the subprocess hangs
            # Capture stderr to stdout since we're not creating separate stderr logs
            try:
                with open(stdout_log_path, 'w', encoding='utf-8', buffering=1) as stdout_file:
                    result = subprocess.run(
                        cmd,
                        stdout=stdout_file,
                        stderr=subprocess.STDOUT,  # Merge stderr into stdout
                        text=True,
                        cwd=self.project_root,
                        env=env,
                        timeout=pytest_timeout
                    )
                # Read the captured output for processing
                result.stdout = stdout_log_path.read_text(encoding='utf-8', errors='ignore')
                result.stderr = ""  # Stderr was merged into stdout
            except subprocess.TimeoutExpired:
                # Pytest hung or took too long
                # Read log files to check for progress (they should exist since we created them before running)
                progress_indicator = False
                stdout_content = ""
                stderr_content = ""
                if self.pytest_stdout_log and self.pytest_stdout_log.exists():
                    try:
                        stdout_content = self.pytest_stdout_log.read_text(encoding='utf-8', errors='ignore')
                        # Check for progress indicators (test output, percentages, etc.)
                        progress_indicator = bool(
                            'passed' in stdout_content.lower() or
                            'failed' in stdout_content.lower() or
                            '[  ' in stdout_content or
                            '%' in stdout_content or
                            'TOTAL' in stdout_content or
                            'bringing up nodes' in stdout_content.lower()
                        )
                    except Exception as e:
                        if logger:
                            logger.debug(f"Failed to read stdout log: {e}")
                
                # Stderr is merged into stdout, so we don't need to read separate stderr log
                stderr_content = ""
                
                if logger:
                    if progress_indicator:
                        logger.warning(f"Pytest timed out after {pytest_timeout // 60} minutes, but tests were making progress")
                        logger.warning("Tests may be running slower than expected. Consider increasing timeout in config:")
                        logger.warning("  development_tools_config.json: {\"coverage\": {\"pytest_timeout\": <seconds>}}")
                    else:
                        logger.error(f"Pytest timed out after {pytest_timeout // 60} minutes - tests may have hung or deadlocked")
                        logger.error("This could indicate:")
                        logger.error("  - A deadlock in parallel execution (pytest-xdist)")
                        logger.error("  - A test that hangs indefinitely")
                        logger.error("  - Resource contention (file locks, network, etc.)")
                        logger.error("  - System resource exhaustion")
                        logger.error("Consider running with --no-parallel to isolate the issue")
                    logger.info(f"Timeout is configurable via development_tools_config.json: {{\"coverage\": {{\"pytest_timeout\": <seconds>}}}}")
                    if stdout_content:
                        logger.info(f"Last stdout output (last 500 chars): {stdout_content[-500:]}")
                    if stderr_content:
                        logger.info(f"Last stderr output (last 500 chars): {stderr_content[-500:]}")
                # Create a mock result to indicate timeout, but include any captured output
                result = subprocess.CompletedProcess(
                    cmd,
                    returncode=1,
                    stdout=stdout_content,
                    stderr=stderr_content or f"Pytest timed out after {pytest_timeout // 60} minutes"
                )
            
            # Log if the command completed too quickly (suspicious)
            if result.returncode is not None and logger:
                if not result.stdout or len(result.stdout) < 100:
                    logger.warning(f"Pytest completed very quickly with minimal output - may not have run tests properly")
                    if result.stderr:
                        logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            # Log files were already created and written to above
            if logger and self.pytest_stdout_log and self.pytest_stdout_log.exists():
                logger.info(f"Saved pytest output to {self.pytest_stdout_log}")
            
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
            # Note: In parallel mode, we don't generate JSON here - we'll combine coverage data files and regenerate JSON later
            # So this code will only execute in serial mode or if coverage.json exists from a previous run
            if coverage_output.exists() and pytest_ran and not self.parallel:
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
            elif not overall_coverage.get('overall_coverage') and coverage_output.exists() and pytest_ran and not self.parallel:
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
                        failure_msg = f"Test failures: {test_results['test_summary']}"
                        if test_results['random_seed']:
                            failure_msg += f" (random seed: {test_results['random_seed']})"
                        
                        if logger:
                            logger.warning(failure_msg)
                            
                            # Check if maxfail was reached
                            if test_results.get('maxfail_reached', False):
                                logger.warning("Test run was ABORTED due to reaching maximum failure limit (--maxfail)")
                            
                            if test_results['failed_tests']:
                                logger.warning("Failed tests:")
                                for test_name in test_results['failed_tests']:
                                    logger.warning(f"  - {test_name}")
                            else:
                                logger.warning(f"  See {self.pytest_stdout_log} for detailed test failure information")
                    
                    # Log skipped tests at info level
                    if test_results['skipped_count'] > 0:
                        if logger:
                            logger.info(f"Test skips: {test_results['skipped_count']} test(s) skipped")
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
                # Parallel tests passed (not all tests - no_parallel tests run separately)
                if logger and test_results['test_summary']:
                    if self.parallel:
                        logger.info(f"Parallel tests passed: {test_results['test_summary']}")
                    else:
                        logger.info(f"All tests passed: {test_results['test_summary']}")
                    if test_results['random_seed']:
                        logger.info(f"Random seed used: {test_results['random_seed']}")
            
            # If parallel execution was enabled, also run no_parallel tests separately in serial mode
            no_parallel_test_results = {'passed_count': 0, 'failed_count': 0, 'skipped_count': 0, 'test_summary': ''}
            if self.parallel and pytest_ran:
                if logger:
                    logger.debug("Running no_parallel tests separately in serial mode...")
                
                # Create command for no_parallel tests (serial execution, no parallel flags)
                no_parallel_cmd = [
                    sys.executable, '-m', 'pytest',
                    '-m', 'no_parallel and not e2e',  # Only run tests marked with no_parallel, but exclude e2e
                    *cov_args,
                    '--cov-report=term-missing',
                    # Don't write JSON for no_parallel run - we'll combine coverage data files and regenerate JSON
                    f'--cov-config={self.coverage_config_path.relative_to(self.project_root)}',
                    '--tb=line',
                    '-q',
                    f'--maxfail={self.maxfail}',
                    # Ignore temp directories to prevent collecting tests from temp files
                    '--ignore=tests/data/pytest-tmp-*',
                    '--ignore=tests/data/pytest-of-*',
                    'tests/'
                ]
                
                # Use separate coverage data file for no_parallel tests
                # Use absolute path to ensure coverage.py uses our specified location
                no_parallel_env = os.environ.copy()
                # Ensure PATH includes Python executable's directory for Windows DLL resolution
                no_parallel_env = self._ensure_python_path_in_env(no_parallel_env)
                no_parallel_env['COVERAGE_FILE'] = str(no_parallel_coverage_file.resolve())
                # Set unique pytest temp directory to avoid conflicts when running in parallel with dev tools coverage
                import uuid
                unique_id = f"no_parallel_{uuid.uuid4().hex[:8]}"
                pytest_temp_base = self.project_root / "tests" / "data" / f"pytest-tmp-{unique_id}"
                pytest_temp_base.mkdir(parents=True, exist_ok=True)
                # Set PYTEST_CACHE_DIR to ensure pytest uses unique cache directory
                no_parallel_env['PYTEST_CACHE_DIR'] = str(pytest_temp_base / ".pytest_cache")
                # Also set basetemp via command line argument for tmpdir fixture
                no_parallel_cmd.append(f'--basetemp={pytest_temp_base}')
                
                # Create log file for no_parallel run (only stdout, stderr merged)
                # Rotate old log files before creating new ones (keep 1 current + 7 archived = 8 total)
                self._rotate_log_files('pytest_no_parallel_stdout', max_versions=8)
                no_parallel_stdout_log = self.coverage_logs_dir / f"pytest_no_parallel_stdout_{timestamp}.log"
                
                # Log the full command for debugging (consistent with parallel run)
                if logger:
                    logger.debug(f"Running no_parallel tests: {' '.join(no_parallel_cmd)}")
                    logger.debug(f"No_parallel tests timeout set to {pytest_timeout // 60} minutes")
                
                try:
                    with open(no_parallel_stdout_log, 'w', encoding='utf-8', buffering=1) as stdout_file:
                        no_parallel_result = subprocess.run(
                            no_parallel_cmd,
                            stdout=stdout_file,
                            stderr=subprocess.STDOUT,  # Merge stderr into stdout
                            text=True,
                            cwd=self.project_root,
                            env=no_parallel_env,
                            timeout=pytest_timeout
                        )
                    # Read the captured output for processing
                    no_parallel_result.stdout = no_parallel_stdout_log.read_text(encoding='utf-8', errors='ignore')
                    no_parallel_result.stderr = ""  # Stderr was merged into stdout
                    
                    # Log where output was saved (consistent with parallel run)
                    if logger:
                        logger.info(f"Saved no_parallel pytest output to {no_parallel_stdout_log}")
                except subprocess.TimeoutExpired:
                    if logger:
                        logger.warning(f"No_parallel tests timed out after {pytest_timeout // 60} minutes")
                    no_parallel_result = subprocess.CompletedProcess(
                        no_parallel_cmd,
                        returncode=1,
                        stdout=no_parallel_stdout_log.read_text(encoding='utf-8', errors='ignore') if no_parallel_stdout_log.exists() else "",
                        stderr=f"No_parallel tests timed out after {pytest_timeout // 60} minutes"
                    )
                
                # Parse no_parallel test results
                # Read from log file if stdout is empty (can happen with quiet mode)
                no_parallel_output = no_parallel_result.stdout or ""
                if not no_parallel_output and no_parallel_stdout_log.exists():
                    no_parallel_output = no_parallel_stdout_log.read_text(encoding='utf-8', errors='ignore')
                
                # Check if output looks incomplete (just dots, no summary) - indicates early termination
                output_stripped = no_parallel_output.strip()
                has_summary = 'passed' in no_parallel_output.lower() or 'failed' in no_parallel_output.lower() or 'coverage' in no_parallel_output.lower() or 'TOTAL' in no_parallel_output
                is_only_dots = output_stripped and all(c in '.sF\n\r' for c in output_stripped.replace(' ', ''))
                
                if is_only_dots and not has_summary and len(output_stripped) < 200:
                    # Suspiciously short output with only dots - likely interrupted early
                    if logger:
                        logger.warning(f"No_parallel test run appears to have stopped early - log contains only {len(output_stripped)} progress dots with no summary")
                        logger.warning(f"Return code: {no_parallel_result.returncode}, Output length: {len(no_parallel_output)} chars")
                        if no_parallel_result.returncode != 0:
                            # Check for specific Windows error codes
                            # 0xC0000135 = 3221226505 (STATUS_DLL_NOT_FOUND)
                            # 0xC0000005 = 3221225477 (STATUS_ACCESS_VIOLATION)
                            if no_parallel_result.returncode == 3221226505:  # 0xC0000135 STATUS_DLL_NOT_FOUND
                                logger.error(f"Pytest crashed with Windows error 0xC0000135 (STATUS_DLL_NOT_FOUND) - missing DLL required by Python or dependencies")
                                logger.error(f"This usually indicates: missing system DLL, corrupted Python installation, or PATH issues")
                                logger.error(f"Check log for details: {no_parallel_stdout_log}")
                                logger.error(f"Troubleshooting: verify Python installation, check PATH, try reinstalling pytest/dependencies")
                            elif no_parallel_result.returncode == 3221225477:  # 0xC0000005 STATUS_ACCESS_VIOLATION
                                logger.error(f"Pytest crashed with Windows error 0xC0000005 (STATUS_ACCESS_VIOLATION) - memory access violation")
                                logger.error(f"This usually indicates: memory corruption, threading issue, or library conflict (common with Qt/PyQt UI tests)")
                                logger.error(f"Check log for details: {no_parallel_stdout_log}")
                                logger.error(f"Troubleshooting: check for UI test issues, threading problems, or library conflicts")
                            else:
                                logger.warning(f"Pytest exited with non-zero code {no_parallel_result.returncode} (0x{no_parallel_result.returncode:08X}) - check log for errors: {no_parallel_stdout_log}")
                            # Try to extract any error message from the output
                            if no_parallel_output:
                                lines = no_parallel_output.split('\n')
                                error_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed', 'interrupted'])]
                                if error_lines:
                                    logger.warning(f"Potential error indicators in output: {error_lines[-3:]}")
                        elif no_parallel_result.returncode == 0:
                            logger.warning(f"Pytest exited with code 0 but no summary found - possible interruption, crash, or incomplete output")
                            logger.warning(f"Check log file for details: {no_parallel_stdout_log}")
                
                no_parallel_test_results = self._parse_pytest_test_results(no_parallel_output)
                
                # Check if output was empty - this indicates tests didn't run or output wasn't captured
                if not no_parallel_output or (not no_parallel_test_results.get('total_tests', 0) and no_parallel_result.returncode != 0):
                    if logger:
                        logger.warning(f"No_parallel tests produced no output - subprocess may have failed silently")
                        logger.warning(f"Return code: {no_parallel_result.returncode} (0x{no_parallel_result.returncode:08X}), Log file exists: {no_parallel_stdout_log.exists()}, Log size: {no_parallel_stdout_log.stat().st_size if no_parallel_stdout_log.exists() else 0} bytes")
                        # Check for specific Windows error codes that indicate crashes
                        if no_parallel_result.returncode == 3221225477:  # 0xC0000005 STATUS_ACCESS_VIOLATION
                            logger.error(f"Pytest crashed with Windows error 0xC0000005 (STATUS_ACCESS_VIOLATION) - memory access violation")
                            logger.error(f"This usually indicates: memory corruption, threading issue, or library conflict (common with Qt/PyQt UI tests)")
                            logger.error(f"Check log for details: {no_parallel_stdout_log}")
                            logger.error(f"Troubleshooting: check for UI test issues, threading problems, or library conflicts")
                        elif no_parallel_result.returncode == 3221226505:  # 0xC0000135 STATUS_DLL_NOT_FOUND
                            logger.error(f"Pytest crashed with Windows error 0xC0000135 (STATUS_DLL_NOT_FOUND) - missing DLL required by Python or dependencies")
                            logger.error(f"This usually indicates: missing system DLL, corrupted Python installation, or PATH issues")
                            logger.error(f"Check log for details: {no_parallel_stdout_log}")
                            logger.error(f"Troubleshooting: verify Python installation, check PATH, try reinstalling pytest/dependencies")
                        if no_parallel_stdout_log.exists():
                            log_content = no_parallel_stdout_log.read_text(encoding='utf-8', errors='ignore')
                            if log_content:
                                logger.warning(f"Log file has {len(log_content)} chars but parser found no tests")
                                # Try to extract crash information from log
                                if 'Windows fatal exception' in log_content or 'access violation' in log_content.lower():
                                    logger.error("Log contains Windows fatal exception - this indicates a crash, not a test failure")
                                    # Extract the test that crashed
                                    lines = log_content.split('\n')
                                    for i, line in enumerate(lines):
                                        if 'File "' in line and 'test_' in line:
                                            logger.error(f"Crash occurred in: {line.strip()}")
                                            # Show a few lines of context
                                            for j in range(max(0, i-2), min(len(lines), i+3)):
                                                if j != i:
                                                    logger.debug(f"  {lines[j].strip()}")
                                            break
                            else:
                                logger.warning(f"Log file is empty - subprocess may not have started or output was not captured")
                
                # Combine test results
                test_results['passed_count'] += no_parallel_test_results.get('passed_count', 0)
                test_results['failed_count'] += no_parallel_test_results.get('failed_count', 0)
                test_results['skipped_count'] += no_parallel_test_results.get('skipped_count', 0)
                
                if logger:
                    if no_parallel_result.returncode == 0 and no_parallel_test_results.get('total_tests', 0) > 0:
                        logger.info(f"No_parallel tests completed: {no_parallel_test_results.get('passed_count', 0)} passed, {no_parallel_test_results.get('failed_count', 0)} failed, {no_parallel_test_results.get('skipped_count', 0)} skipped")
                    elif no_parallel_result.returncode == 0 and no_parallel_test_results.get('total_tests', 0) == 0:
                        logger.warning(f"No_parallel tests exited with code 0 but no tests were found in output - possible issue with test collection or output capture")
                    else:
                        logger.warning(f"No_parallel tests had failures: {no_parallel_test_results.get('failed_count', 0)} failed, {no_parallel_test_results.get('passed_count', 0)} passed, {no_parallel_test_results.get('skipped_count', 0)} skipped")
                    
                    # Check if maxfail was reached
                    if no_parallel_test_results.get('maxfail_reached', False):
                        logger.warning("No_parallel test run was ABORTED due to reaching maximum failure limit (--maxfail)")
                    
                    # Log skipped tests at info level
                    if no_parallel_test_results.get('skipped_count', 0) > 0:
                        logger.info(f"No_parallel test skips: {no_parallel_test_results.get('skipped_count', 0)} test(s) skipped")
                    
                    # Log failed tests if any
                    if no_parallel_test_results.get('failed_count', 0) > 0 and no_parallel_test_results.get('failed_tests'):
                        logger.warning("No_parallel failed tests:")
                        for test_name in no_parallel_test_results.get('failed_tests', [])[:10]:  # Limit to first 10
                            logger.warning(f"  - {test_name}")
                        if len(no_parallel_test_results.get('failed_tests', [])) > 10:
                            logger.warning(f"  ... and {len(no_parallel_test_results.get('failed_tests', [])) - 10} more (see log for full list)")
                
                # Check if coverage files were created and log their locations
                if logger:
                    if parallel_coverage_file:
                        logger.debug(f"Parallel coverage file path: {parallel_coverage_file}, exists: {parallel_coverage_file.exists()}")
                        # Also check what files actually exist in that directory
                        if parallel_coverage_file.parent.exists():
                            all_files = list(parallel_coverage_file.parent.glob(".coverage*"))
                            logger.debug(f"All .coverage* files in {parallel_coverage_file.parent}: {[f.name for f in all_files]}")
                    if no_parallel_coverage_file:
                        logger.debug(f"No_parallel coverage file path: {no_parallel_coverage_file}, exists: {no_parallel_coverage_file.exists()}")
                
                # Combine coverage data files using coverage combine
                # Check if coverage files exist (they may be in tests/ directory due to coverage.ini)
                # Also check for shard files from parallel execution (e.g., .coverage.worker0, .coverage.worker1, etc.)
                coverage_dir = self.coverage_data_file.parent
                parallel_exists = parallel_coverage_file and parallel_coverage_file.exists()
                no_parallel_exists = no_parallel_coverage_file and no_parallel_coverage_file.exists()
                
                # Check for shard files from parallel execution (pytest-xdist creates these)
                # When COVERAGE_FILE is set to .coverage_parallel, workers create .coverage_parallel.worker0, etc.
                # Shard files should be in the coverage directory (where COVERAGE_FILE points)
                parallel_shard_files = []
                if coverage_dir.exists():
                    # Look for shard files: .coverage_parallel.worker0, .coverage_parallel.worker1, etc.
                    parallel_shard_files.extend(list(coverage_dir.glob(".coverage_parallel.worker*")))
                    # Also check for .coverage.worker* files (in case COVERAGE_FILE wasn't set correctly)
                    parallel_shard_files.extend([f for f in coverage_dir.glob(".coverage.worker*") 
                                                if f.name not in ['.coverage']])
                    # Log all .coverage* files found for debugging
                    if logger:
                        all_coverage_files = list(coverage_dir.glob(".coverage*"))
                        logger.debug(f"All .coverage* files in {coverage_dir}: {[f.name for f in all_coverage_files]}")
                        # Check if .coverage exists (might have been auto-combined)
                        coverage_file = coverage_dir / ".coverage"
                        if coverage_file.exists():
                            file_size = coverage_file.stat().st_size
                            logger.debug(f"Found .coverage file ({file_size} bytes) - shard files may have been auto-combined")
                # Filter out the main parallel coverage file (we want shard files, not the combined one)
                parallel_shard_files = [f for f in parallel_shard_files 
                                      if f.name != '.coverage_parallel'
                                      and f.name != '.coverage_no_parallel'
                                      and f.name != '.coverage']
                if logger:
                    logger.debug(f"Found {len(parallel_shard_files)} shard files after filtering: {[f.name for f in parallel_shard_files]}")
                    
                # If no shard files found but .coverage exists, it might contain the parallel coverage
                # Check if we should use .coverage as the parallel coverage source
                coverage_file = coverage_dir / ".coverage"
                if not parallel_shard_files and not parallel_exists and coverage_file.exists() and logger:
                    logger.warning(
                        f"No shard files found and .coverage_parallel doesn't exist, but .coverage exists. "
                        f"This suggests pytest-cov may have auto-combined shard files into .coverage. "
                        f"Will attempt to use .coverage as parallel coverage source."
                    )
                
                # Check project root for shard files (shouldn't be there, but log if found)
                project_root_shards = []
                project_root_shards.extend([f for f in self.project_root.glob(".coverage_parallel.worker*")])
                project_root_shards.extend([f for f in self.project_root.glob(".coverage.worker*") 
                                           if f.name != '.coverage'])
                if project_root_shards and logger:
                    logger.warning(
                        f"Found {len(project_root_shards)} shard files in project root (should be in {coverage_dir}). "
                        f"This indicates COVERAGE_FILE environment variable may not have been respected by pytest-xdist workers. "
                        f"Shard files: {[f.name for f in project_root_shards[:5]]}"
                    )
                    # Copy them to the correct location so they can be combined
                    for shard_file in project_root_shards:
                        try:
                            dest_file = coverage_dir / shard_file.name
                            if not dest_file.exists():
                                shutil.copy2(shard_file, dest_file)
                                parallel_shard_files.append(dest_file)
                                if logger:
                                    logger.debug(f"Copied misplaced shard file {shard_file.name} from project root to coverage directory")
                        except Exception as copy_error:
                            if logger:
                                logger.warning(f"Failed to copy misplaced shard file {shard_file.name}: {copy_error}")
                
                if parallel_exists or no_parallel_exists or parallel_shard_files:
                    if logger:
                        logger.info("Combining coverage data from parallel and no_parallel test runs...")
                        if parallel_shard_files:
                            logger.debug(f"Found {len(parallel_shard_files)} parallel shard files: {[f.name for f in parallel_shard_files[:5]]}")
                    
                    # Copy coverage files to the coverage data file directory with .coverage.* naming for combine
                    # Coverage combine looks for .coverage.* files in the current directory
                    # Use the same directory as the coverage data file (respects coverage.ini data_file setting)
                    project_root_coverage_parallel = coverage_dir / ".coverage.parallel"
                    project_root_coverage_no_parallel = coverage_dir / ".coverage.no_parallel"
                    
                    try:
                        # Copy both coverage files to coverage directory with .coverage.* naming
                        # Also check for shard files from parallel execution
                        files_to_combine = []
                        
                        # Check for parallel coverage in multiple possible locations
                        parallel_coverage_source = None
                        if parallel_coverage_file and parallel_coverage_file.exists():
                            parallel_coverage_source = parallel_coverage_file
                        elif not parallel_shard_files:
                            # If no shard files and no .coverage_parallel, check if .coverage exists
                            # (pytest-cov might have auto-combined shard files into .coverage)
                            coverage_file = coverage_dir / ".coverage"
                            if coverage_file.exists():
                                parallel_coverage_source = coverage_file
                                if logger:
                                    logger.info(f"Using .coverage as parallel coverage source (shard files were likely auto-combined)")
                        
                        if parallel_coverage_source:
                            shutil.copy2(parallel_coverage_source, project_root_coverage_parallel)
                            files_to_combine.append(project_root_coverage_parallel)
                            if logger:
                                logger.debug(f"Copied parallel coverage file from {parallel_coverage_source} to {project_root_coverage_parallel}")
                        elif parallel_shard_files:
                            # If main parallel coverage file doesn't exist (e.g., due to timeout),
                            # but shard files exist, we can still combine using shard files
                            if logger:
                                logger.info(f"Parallel coverage file not found (may have timed out), but {len(parallel_shard_files)} shard files exist - will combine shard files")
                        else:
                            if logger:
                                logger.warning(f"Parallel coverage file not found: {parallel_coverage_file}, and no shard files found")
                        
                        if no_parallel_coverage_file and no_parallel_coverage_file.exists():
                            shutil.copy2(no_parallel_coverage_file, project_root_coverage_no_parallel)
                            files_to_combine.append(project_root_coverage_no_parallel)
                            if logger:
                                logger.debug(f"Copied no_parallel coverage file from {no_parallel_coverage_file} to {project_root_coverage_no_parallel}")
                        else:
                            if logger:
                                logger.warning(f"No_parallel coverage file not found: {no_parallel_coverage_file}")
                        
                        # Shard files should already be in the coverage directory (where COVERAGE_FILE points)
                        # They'll be picked up automatically by coverage combine
                        if parallel_shard_files:
                            if logger:
                                logger.debug(f"Will combine {len(parallel_shard_files)} shard files from parallel execution")
                        
                        # Use coverage combine to merge the coverage data files
                        # Set COVERAGE_FILE to the final combined file location
                        combine_env = os.environ.copy()
                        # Ensure PATH includes Python executable's directory for Windows DLL resolution
                        combine_env = self._ensure_python_path_in_env(combine_env)
                        combine_env['COVERAGE_FILE'] = str(self.coverage_data_file.resolve())
                        
                        combine_cmd = [
                            sys.executable, '-m', 'coverage', 'combine',
                            '--data-file', str(self.coverage_data_file.resolve())
                        ]
                        
                        if logger:
                            total_files = len(files_to_combine) + len(parallel_shard_files)
                            logger.debug(f"Running coverage combine from {coverage_dir} with {total_files} files to combine")
                            if parallel_shard_files:
                                logger.debug(f"Shard files to combine ({len(parallel_shard_files)}): {[f.name for f in parallel_shard_files[:10]]}")
                            if files_to_combine:
                                logger.debug(f"Copied files to combine: {[f.name for f in files_to_combine]}")
                        
                        # Run combine from the coverage directory so it finds the .coverage.* files
                        combine_result = subprocess.run(
                            combine_cmd,
                            capture_output=True,
                            text=True,
                            cwd=coverage_dir,
                            env=combine_env,
                            timeout=60  # Combine should be fast
                        )
                        
                        if combine_result.returncode != 0:
                            if logger:
                                stderr_msg = combine_result.stderr or combine_result.stdout or ""
                                if "No data to combine" not in stderr_msg:
                                    logger.warning(f"Coverage combine exited with code {combine_result.returncode}: {stderr_msg[:500]}")
                                else:
                                    logger.info("Coverage combine reported no data to combine - this may indicate coverage files weren't created properly")
                                    # Log what files exist for debugging
                                    all_files = list(coverage_dir.glob(".coverage*")) if coverage_dir.exists() else []
                                    if all_files:
                                        logger.debug(f"Coverage files found in {coverage_dir}: {[f.name for f in all_files]}")
                        elif logger:
                            logger.info("Successfully combined coverage data from parallel and no_parallel runs")
                            # Validate that we actually have coverage data (detect silent failures)
                            if self.coverage_data_file.exists():
                                file_size = self.coverage_data_file.stat().st_size
                                if file_size == 0:
                                    logger.warning("Combined coverage file is empty - combine may have failed silently")
                                else:
                                    logger.debug(f"Combined coverage file: {self.coverage_data_file.name} ({file_size} bytes)")
                            else:
                                logger.warning("Combined coverage file was not created after combine operation")
                        
                        # Clean up temporary .coverage.* files from project root
                        try:
                            if project_root_coverage_parallel.exists():
                                project_root_coverage_parallel.unlink()
                            if project_root_coverage_no_parallel.exists():
                                project_root_coverage_no_parallel.unlink()
                        except Exception:
                            pass
                    except Exception as combine_error:
                        if logger:
                            logger.warning(f"Failed to combine coverage data: {combine_error}")
                        # Clean up on error
                        try:
                            if project_root_coverage_parallel.exists():
                                project_root_coverage_parallel.unlink()
                            if project_root_coverage_no_parallel.exists():
                                project_root_coverage_no_parallel.unlink()
                        except Exception:
                            pass
                    
                    # Clean up temporary coverage files from original locations
                    # Also clean up process-specific files (e.g., .coverage_parallel.DESKTOP-*.X.*)
                    self._cleanup_process_specific_coverage_files(coverage_dir)
                    try:
                        if parallel_coverage_file and parallel_coverage_file.exists():
                            parallel_coverage_file.unlink()
                        if no_parallel_coverage_file and no_parallel_coverage_file.exists():
                            no_parallel_coverage_file.unlink()
                    except Exception as cleanup_error:
                        if logger:
                            logger.debug(f"Failed to cleanup temporary coverage files: {cleanup_error}")
                    
                    # Regenerate coverage JSON from combined data
                    if self.coverage_data_file.exists():
                        # Archive old coverage.json BEFORE regenerating (to keep current file in main directory)
                        archive_dir = coverage_output.parent / "archive"
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        if coverage_output.exists():
                            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                            archive_name = f"coverage_{timestamp}.json"
                            archive_path = archive_dir / archive_name
                            shutil.move(str(coverage_output), str(archive_path))
                            if logger:
                                logger.debug(f"Archived old coverage.json to {archive_name}")
                            
                            # Clean up old archives to keep only 6 versions (current + 6 archived = 7 total)
                            from development_tools.shared.file_rotation import FileRotator
                            rotator = FileRotator(base_dir=str(coverage_output.parent))
                            rotator._cleanup_old_versions("coverage", max_versions=6)  # Keep 6 archived (current is separate)
                        
                        json_cmd = [
                            sys.executable, '-m', 'coverage', 'json',
                            '-o', str(coverage_output),
                            '--data-file', str(self.coverage_data_file)
                        ]
                        try:
                            json_result = subprocess.run(
                                json_cmd,
                                capture_output=True,
                                text=True,
                                cwd=self.project_root,
                                timeout=120
                            )
                            if json_result.returncode == 0:
                                if logger:
                                    logger.info("Regenerated coverage.json from combined coverage data")
                                
                                # Reload coverage data from the regenerated JSON
                                if coverage_output.exists():
                                    if self.analyzer:
                                        coverage_data = self.analyzer.load_coverage_json(coverage_output)
                                        overall_coverage = self.analyzer.extract_overall_from_json(coverage_output)
                                        
                                        # Validate coverage percentage - if it's unexpectedly low, warn
                                        # Expected coverage should be around 70-75% based on historical data
                                        coverage_pct = overall_coverage.get('overall_coverage', 0)
                                        if coverage_pct > 0 and coverage_pct < 50:
                                            logger.warning(
                                                f"Coverage percentage ({coverage_pct}%) is unexpectedly low. "
                                                f"Expected ~70-75%. This may indicate parallel coverage data was not included. "
                                                f"Parallel file exists: {parallel_coverage_file.exists() if parallel_coverage_file else False}, "
                                                f"No_parallel file exists: {no_parallel_coverage_file.exists() if no_parallel_coverage_file else False}, "
                                                f"Shard files found: {len(parallel_shard_files)}"
                                            )
                                    else:
                                        coverage_data = {}
                                        overall_coverage = {}
                            else:
                                if logger:
                                    logger.warning(f"Failed to regenerate coverage JSON: {json_result.stderr}")
                        except Exception as json_error:
                            if logger:
                                logger.warning(f"Error regenerating coverage JSON: {json_error}")
            
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
            # Create timestamp for log file
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            cmd = [
                sys.executable, '-m', 'pytest',
                '-m', 'not e2e',  # Exclude e2e tests (slow, excluded from regular runs per pytest.ini)
                '--cov=development_tools',
                '--cov-report=term-missing',
                f'--cov-report=json:{coverage_output_abs}',
                f'--cov-config={dev_cov_config}',
                '--tb=line',
                '-q',
                '--maxfail=10',  # Allow more failures before stopping (some tests may be flaky)
                '--continue-on-collection-errors',  # Continue even if collection fails
                # Ignore temp directories to prevent collecting tests from temp files
                '--ignore=tests/data/pytest-tmp-*',
                '--ignore=tests/data/pytest-of-*',
                'tests/development_tools/'
            ]
            
            if logger:
                logger.debug(f"Running dev tools coverage command: {' '.join(cmd[:5])} ...")
            
            env = os.environ.copy()
            # Ensure PATH includes Python executable's directory for Windows DLL resolution
            env = self._ensure_python_path_in_env(env)
            # Set COVERAGE_FILE to absolute path to ensure files are created in the correct location
            env['COVERAGE_FILE'] = str(self.dev_tools_coverage_data_file.resolve())
            if dev_cov_config and dev_cov_config.exists():
                env['COVERAGE_RCFILE'] = str(dev_cov_config.resolve())
            # Set unique pytest temp directory to avoid conflicts when running in parallel with main coverage
            # Use a unique identifier based on process/coverage type to ensure isolation
            import uuid
            unique_id = f"dev_tools_{uuid.uuid4().hex[:8]}"
            pytest_temp_base = self.project_root / "tests" / "data" / f"pytest-tmp-{unique_id}"
            pytest_temp_base.mkdir(parents=True, exist_ok=True)
            # Set PYTEST_CACHE_DIR to ensure pytest uses unique cache directory
            env['PYTEST_CACHE_DIR'] = str(pytest_temp_base / ".pytest_cache")
            # Also set basetemp via command line argument for tmpdir fixture
            cmd.append(f'--basetemp={pytest_temp_base}')
            
            # Set up stdout logging for dev tools coverage (similar to main coverage)
            # Rotate old log files before creating new ones (keep 1 current + 7 archived = 8 total)
            self._rotate_log_files('pytest_dev_tools_stdout', max_versions=8)
            
            dev_tools_stdout_log = self.coverage_logs_dir / f"pytest_dev_tools_stdout_{timestamp}.log"
            dev_tools_stdout_log.parent.mkdir(parents=True, exist_ok=True)
            
            # Run pytest and capture output to both stdout and log file
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout
                    text=True,
                    cwd=self.project_root,
                    env=env,
                    timeout=720  # 12 minutes timeout
                )
                # Ensure stdout is not None
                if result.stdout is None:
                    result.stdout = ""
                if result.stderr is None:
                    result.stderr = ""
                # Write to log file
                with open(dev_tools_stdout_log, 'w', encoding='utf-8', errors='replace') as log_file:
                    log_file.write(result.stdout)
                    if result.stderr and result.stderr != result.stdout:
                        log_file.write("\n\n=== STDERR ===\n")
                        log_file.write(result.stderr)
            except subprocess.TimeoutExpired:
                if logger:
                    logger.error(f"Dev tools coverage pytest timed out after 12 minutes")
                with open(dev_tools_stdout_log, 'w', encoding='utf-8', errors='replace') as log_file:
                    log_file.write("ERROR: pytest timed out after 12 minutes\n")
                # Create a fake result object for error handling
                class FakeResult:
                    returncode = 1
                    stdout = "ERROR: pytest timed out after 12 minutes\n"
                    stderr = ""
                result = FakeResult()
            except Exception as e:
                if logger:
                    logger.error(f"Error running dev tools coverage pytest: {e}", exc_info=True)
                with open(dev_tools_stdout_log, 'w', encoding='utf-8', errors='replace') as log_file:
                    log_file.write(f"ERROR: Exception running pytest: {e}\n")
                # Create a fake result object for error handling
                class FakeResult:
                    returncode = 1
                    stdout = f"ERROR: Exception running pytest: {e}\n"
                    stderr = ""
                result = FakeResult()
            
            if logger:
                log_size = dev_tools_stdout_log.stat().st_size if dev_tools_stdout_log.exists() else 0
                logger.info(f"Saved dev tools pytest output to {dev_tools_stdout_log} ({log_size} bytes)")
            
            # Parse coverage results (even if pytest exited with non-zero code, coverage may still be available)
            if self.analyzer:
                coverage_data = self.analyzer.parse_coverage_output(result.stdout)
            else:
                coverage_data = {}
            if not coverage_data and coverage_output.exists():
                if self.analyzer:
                    coverage_data = self.analyzer.load_coverage_json(coverage_output)
                    
                    # Rotate coverage_dev_tools.json after loading
                    if coverage_output.exists():
                        from development_tools.shared.file_rotation import FileRotator
                        rotator = FileRotator(base_dir=str(coverage_output.parent))
                        rotator.rotate_file(str(coverage_output), max_versions=5)
            
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
                        if result.stdout:
                            # Log more of stdout to see what happened
                            logger.warning(f"Pytest stdout (last 1000 chars): {result.stdout[-1000:]}")
            
            # If still no coverage data, check if the file was created
            if not overall_coverage.get('overall_coverage') and not coverage_output.exists():
                if logger:
                    logger.warning(f"Coverage JSON file not created at {coverage_output}")
                    logger.info(f"Pytest return code: {result.returncode}")
                    if result.stdout:
                        # Look for coverage summary in stdout
                        if 'TOTAL' in result.stdout:
                            logger.info("Coverage data found in stdout but JSON not created")
                        # Log more of stdout to diagnose the issue
                        logger.warning(f"Pytest stdout (last 1000 chars): {result.stdout[-1000:]}")
                        # Also log first part to see if there are early errors
                        if len(result.stdout) > 1000:
                            logger.warning(f"Pytest stdout (first 500 chars): {result.stdout[:500]}")
                    if result.stderr:
                        logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            # Clean up temporary coverage data files after generating report
            self._cleanup_coverage_data_files()
            # Also clean up any process-specific files that may have been created
            self._cleanup_process_specific_coverage_files()
            
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

    def _cleanup_process_specific_coverage_files(self, coverage_dir: Optional[Path] = None) -> None:
        """Clean up process-specific coverage files (e.g., .coverage_parallel.DESKTOP-*.X.*).
        
        These files are created by coverage.py when multiple processes try to write to the same
        coverage file simultaneously. They need to be cleaned up after coverage collection.
        """
        if coverage_dir is None:
            coverage_dir = self.coverage_data_file.parent
        
        if not coverage_dir.exists():
            return
        
        cleanup_count = 0
        try:
            # Clean up process-specific parallel files
            for proc_file in coverage_dir.glob(".coverage_parallel.*"):
                if proc_file.is_file() and proc_file.name != ".coverage_parallel":
                    try:
                        proc_file.unlink()
                        cleanup_count += 1
                    except Exception:
                        pass
            # Clean up process-specific no_parallel files
            for proc_file in coverage_dir.glob(".coverage_no_parallel.*"):
                if proc_file.is_file() and proc_file.name != ".coverage_no_parallel":
                    try:
                        proc_file.unlink()
                        cleanup_count += 1
                    except Exception:
                        pass
            # Also clean up any process-specific .coverage files (from non-parallel runs)
            for proc_file in coverage_dir.glob(".coverage.*"):
                if proc_file.is_file() and proc_file.name != ".coverage":
                    # Check if it's a process-specific file (contains hostname and PID pattern)
                    # Pattern: .coverage.HOSTNAME.PID.RANDOM
                    if '.' in proc_file.name[10:]:  # After ".coverage."
                        try:
                            proc_file.unlink()
                            cleanup_count += 1
                        except Exception:
                            pass
        except Exception as exc:
            if logger:
                logger.debug(f"Failed to cleanup process-specific coverage files: {exc}")
        
        if cleanup_count > 0 and logger:
            logger.debug(f"Cleaned up {cleanup_count} process-specific coverage file(s)")

    def _cleanup_coverage_data_files(self) -> None:
        """Clean up temporary .coverage_dev_tools.* files after coverage analysis."""
        tests_dir = self.project_root / "development_tools" / "tests"
        root_dir = self.project_root / "development_tools"
        
        cleanup_count = 0
        
        # Clean up files in tests directory (current location)
        # Include process-specific files (e.g., .coverage_dev_tools.DESKTOP-*.X.*)
        if tests_dir.exists():
            # Clean up all .coverage_dev_tools.* files (including process-specific ones)
            for coverage_file in tests_dir.glob(".coverage_dev_tools*"):
                try:
                    # Skip directories
                    if coverage_file.is_file():
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
            'total_tests': 0,
            'maxfail_reached': False
        }
        
        if not stdout:
            return results
        
        # Check if maxfail was reached (pytest stops early when maxfail is hit)
        # Look for patterns like "interrupted: stopping after X failures" or "maxfail=X reached"
        maxfail_patterns = [
            r'interrupted:\s+stopping\s+after\s+\d+\s+failures?',
            r'maxfail\s*=\s*\d+\s+reached',
            r'stopping\s+after\s+\d+\s+failures?'
        ]
        for pattern in maxfail_patterns:
            if re.search(pattern, stdout, re.IGNORECASE):
                results['maxfail_reached'] = True
                break
        
        # Extract random seed if pytest-randomly is used
        seed_pattern = r'--randomly-seed=(\d+)'
        seed_match = re.search(seed_pattern, stdout)
        if seed_match:
            results['random_seed'] = seed_match.group(1)
        
        # Extract test summary (e.g., "4 failed, 2276 passed, 1 skipped, 4 warnings" or "145 passed, 3439 deselected")
        # Try full format first
        summary_pattern = r'(\d+)\s+failed[,\s]+(\d+)\s+passed[,\s]+(\d+)\s+skipped[,\s]+(\d+)\s+warnings'
        summary_match = re.search(summary_pattern, stdout)
        if summary_match:
            results['failed_count'] = int(summary_match.group(1))
            results['passed_count'] = int(summary_match.group(2))
            results['skipped_count'] = int(summary_match.group(3))
            results['warnings_count'] = int(summary_match.group(4))
            results['total_tests'] = results['failed_count'] + results['passed_count'] + results['skipped_count']
            results['test_summary'] = f"{results['failed_count']} failed, {results['passed_count']} passed, {results['skipped_count']} skipped, {results['warnings_count']} warnings"
        else:
            # Try simpler format (e.g., "145 passed, 3439 deselected" or "1 failed, 3437 passed, 1 skipped")
            # Look for patterns like "X passed, Y deselected" or "X failed, Y passed, Z skipped"
            # Search for all number-label pairs in the summary line
            simple_pattern = r'(\d+)\s+(failed|passed|skipped|deselected|warnings)'
            matches = re.findall(simple_pattern, stdout)
            for count_str, label in matches:
                count = int(count_str)
                if label == 'failed':
                    results['failed_count'] = count
                elif label == 'passed':
                    results['passed_count'] = count
                elif label == 'skipped':
                    results['skipped_count'] = count
                elif label == 'warnings':
                    results['warnings_count'] = count
                # deselected is not counted in total, but we note it
            
            # If no matches found but output contains only dots (quiet mode with all passed tests),
            # try to count dots as passed tests (rough estimate)
            if not matches and stdout.strip() and all(c in '.sF' for c in stdout.strip()):
                # Count dots as passed, 'F' as failed, 's' as skipped
                dot_count = stdout.count('.')
                f_count = stdout.count('F')
                s_count = stdout.count('s')
                if dot_count > 0 or f_count > 0 or s_count > 0:
                    results['passed_count'] = dot_count
                    results['failed_count'] = f_count
                    results['skipped_count'] = s_count
                    results['total_tests'] = dot_count + f_count + s_count
                    if results['total_tests'] > 0:
                        parts = []
                        if results['failed_count'] > 0:
                            parts.append(f"{results['failed_count']} failed")
                        if results['passed_count'] > 0:
                            parts.append(f"{results['passed_count']} passed")
                        if results['skipped_count'] > 0:
                            parts.append(f"{results['skipped_count']} skipped")
                        results['test_summary'] = ", ".join(parts) if parts else "0 tests"
            
            if not results.get('test_summary'):
                results['total_tests'] = results['failed_count'] + results['passed_count'] + results['skipped_count']
                if results['total_tests'] > 0 or results['passed_count'] > 0:
                    parts = []
                    if results['failed_count'] > 0:
                        parts.append(f"{results['failed_count']} failed")
                    if results['passed_count'] > 0:
                        parts.append(f"{results['passed_count']} passed")
                    if results['skipped_count'] > 0:
                        parts.append(f"{results['skipped_count']} skipped")
                    if results['warnings_count'] > 0:
                        parts.append(f"{results['warnings_count']} warnings")
                    results['test_summary'] = ", ".join(parts) if parts else "0 tests"
        
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
    
    def _rotate_log_files(self, base_name: str, max_versions: int = 7) -> None:
        """Rotate log files, keeping only the last max_versions copies total (consolidated)."""
        try:
            from development_tools.shared.file_rotation import FileRotator
            
            # Find all log files matching the base name pattern (both in main dir and archive)
            main_log_files = sorted(
                self.coverage_logs_dir.glob(f"{base_name}_*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            archive_dir = self.coverage_logs_dir / "archive"
            archived_files = []
            if archive_dir.exists():
                archived_files = sorted(
                    archive_dir.glob(f"{base_name}_*.log"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
            
            # Combine all files and sort by modification time (newest first)
            all_files = [(f, f.stat().st_mtime) for f in main_log_files] + \
                       [(f, f.stat().st_mtime) for f in archived_files]
            all_files.sort(key=lambda x: x[1], reverse=True)
            
            # Strategy: Keep 1 file in main (newest), max_versions-1 in archive
            # max_versions=8 means: 1 current + 7 archived = 8 total
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Separate files by location
            main_files = [f for f, _ in all_files if f.parent == self.coverage_logs_dir]
            archive_files = [f for f, _ in all_files if f.parent == archive_dir]
            
            # Sort by modification time (newest first)
            main_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            archive_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            if logger:
                logger.debug(f"Rotating {base_name} logs: {len(main_files)} in main, {len(archive_files)} in archive (target: 1 main + {max_versions-1} archive)")
            
            # Step 1: Move ALL files from main to archive (new file will be created after rotation)
            # This ensures only the new file (created after rotation) remains in main
            if len(main_files) > 0:
                for file_path in main_files:
                    try:
                        # Use original filename (it already has timestamp)
                        archive_path = archive_dir / file_path.name
                        if not archive_path.exists():
                            shutil.move(str(file_path), str(archive_path))
                            if logger:
                                logger.debug(f"Archived log file: {file_path.name}")
                        else:
                            # Archive file already exists, delete the duplicate from main
                            file_path.unlink()
                            if logger:
                                logger.debug(f"Removed duplicate log file: {file_path.name}")
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to archive {file_path.name}: {e}")
            
            # Step 2: Ensure archive has at most max_versions-1 files (since 1 is in main)
            max_archived = max_versions - 1  # Keep 7 archived files when max_versions=8
            final_archive = sorted(
                archive_dir.glob(f"{base_name}_*.log") if archive_dir.exists() else [],
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(final_archive) > max_archived:
                files_to_delete = final_archive[max_archived:]
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        if logger:
                            logger.debug(f"Removed old archived log: {file_path.name}")
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to remove old archive {file_path.name}: {e}")
            
            # Verify final count
            final_main = list(self.coverage_logs_dir.glob(f"{base_name}_*.log"))
            final_archive = list(archive_dir.glob(f"{base_name}_*.log")) if archive_dir.exists() else []
            final_total = len(final_main) + len(final_archive)
            
            if logger:
                logger.debug(f"Log rotation complete for {base_name}: {final_total} files total ({len(final_main)} in main, {len(final_archive)} in archive)")
            
            # Final safety check: if we still have too many, delete oldest
            if len(final_main) > 1:
                # Keep only newest in main
                main_sorted = sorted(final_main, key=lambda p: p.stat().st_mtime, reverse=True)
                for old_file in main_sorted[1:]:
                    try:
                        old_file.unlink()
                        if logger:
                            logger.debug(f"Removed excess main log: {old_file.name}")
                    except Exception as e:
                        if logger:
                            logger.warning(f"Failed to remove excess main file {old_file.name}: {e}")
            elif logger:
                logger.debug(f"No rotation needed for {base_name}: {len(all_files)} files (max: {max_versions})")
        except ImportError:
            # FileRotator not available, skip rotation
            if logger:
                logger.debug("FileRotator not available, skipping log rotation")
        except Exception as e:
            if logger:
                logger.debug(f"Failed to rotate log files: {e}")
    
    def _record_pytest_output(self, result: subprocess.CompletedProcess) -> None:
        """Persist pytest stdout/stderr for troubleshooting."""
        # This method is deprecated - logs are now created directly in run_coverage_analysis
        # Keeping for backward compatibility but it shouldn't be called
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
        
        stdout_content = result.stdout or ""
        
        stdout_path = self.coverage_logs_dir / f"pytest_parallel_stdout_{timestamp}.log"
        
        stdout_path.write_text(stdout_content, encoding='utf-8', errors='ignore')
        
        self.pytest_stdout_log = stdout_path
        self.pytest_stderr_log = None  # No longer creating stderr logs
        
        if logger:
            logger.info(f"Saved pytest output to {stdout_path}")
    
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
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in the format used by the plan."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def run(self, update_plan: bool = False, dev_tools_only: bool = False) -> Dict[str, any]:
        """Run the coverage metrics regeneration."""
        if dev_tools_only:
            # Run dev tools coverage analysis only
            coverage_results = self.run_dev_tools_coverage()
            
            if not coverage_results:
                error_msg = "Failed to get dev tools coverage data - run_dev_tools_coverage returned empty result"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}", file=sys.stderr)
                sys.exit(1)
            
            # Check if coverage was actually collected
            if not coverage_results.get('coverage_collected', False):
                error_msg = "Dev tools coverage analysis completed but no coverage data was collected - tests may not have run"
                logger.error(error_msg)
                # Print to stdout so run_script() can capture it
                print(f"ERROR: {error_msg}")
                # Still return the results dict so caller can check coverage_collected flag
                # Exit with non-zero code to indicate failure
                sys.exit(1)
            
            # Generate summary for dev tools
            if self.report_generator:
                coverage_summary = self.report_generator.generate_coverage_summary(
                    coverage_results.get('modules', {}), 
                    coverage_results.get('overall', {})
                )
            else:
                # Fallback to old method if report generator not available
                coverage_summary = self._generate_coverage_summary_fallback(
                    coverage_results.get('modules', {}), 
                    coverage_results.get('overall', {})
                )
            
            # Print summary (headers removed - added by consolidated report)
            print(coverage_summary)
            
            return coverage_results
        else:
            logger.info("Generating test coverage...")
            
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
            
            # Note: --update-plan flag is deprecated. TEST_COVERAGE_REPORT.md is now generated
            # by the generate_test_coverage_report tool, which runs after this tool in audit orchestration.
            if update_plan:
                logger.warning("--update-plan flag is deprecated. TEST_COVERAGE_REPORT.md is now generated by generate_test_coverage_report tool.")
                print("\n* Note: TEST_COVERAGE_REPORT.md will be generated by generate_test_coverage_report tool (runs after coverage execution)")
            
            return coverage_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run test coverage execution and collect coverage data")
    parser.add_argument('--update-plan', action='store_true', 
                       help='[DEPRECATED] TEST_COVERAGE_REPORT.md is now generated by generate_test_coverage_report tool. This flag does nothing.')
    parser.add_argument('--output-file', help='Output file for coverage report (optional)')
    parser.add_argument('--no-parallel', action='store_true',
                       help='Disable parallel test execution (parallel enabled by default)')
    parser.add_argument('--workers', default='auto',
                       help="Number of parallel workers (default: 'auto' to let pytest-xdist decide, or specify a number)")
    parser.add_argument('--dev-tools-only', action='store_true',
                       help='Run coverage analysis only for development_tools directory (separate evaluation)')
    
    args = parser.parse_args()
    
    # Only use num_workers if parallel is enabled
    parallel_enabled = not args.no_parallel
    regenerator = CoverageMetricsRegenerator(
        parallel=parallel_enabled,
        num_workers=args.workers if parallel_enabled else None
    )
    results = regenerator.run(update_plan=args.update_plan, dev_tools_only=args.dev_tools_only)
    
    if args.output_file and results:
        # Save detailed results to JSON file
        output_path = Path(args.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(results, f, indent=2)
        print(f"\n📊 Detailed coverage data saved to: {output_path}")


if __name__ == "__main__":
    main()
