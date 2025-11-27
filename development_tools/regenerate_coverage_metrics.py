#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: mhm-specific

"""
Test Coverage Metrics Regenerator for MHM

This script regenerates test coverage metrics and updates the 
TEST_COVERAGE_EXPANSION_PLAN.md with current data.

Usage:
    python ai_tools/regenerate_coverage_metrics.py [--update-plan] [--output-file]
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
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

class CoverageMetricsRegenerator:
    """Regenerates test coverage metrics for MHM."""
    
    def __init__(self, project_root: str = ".", parallel: bool = True, num_workers: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        self.coverage_plan_file = self.project_root / "development_docs" / "TEST_COVERAGE_EXPANSION_PLAN.md"
        self.coverage_config_path = self.project_root / "coverage.ini"
        self.coverage_data_file: Path = self.project_root / ".coverage"
        self.coverage_html_dir: Path = self.project_root / "htmlcov"
        self.coverage_logs_dir: Path = self.project_root / "development_tools" / "logs" / "coverage_regeneration"
        self.dev_tools_coverage_config_path: Path = self.project_root / "development_tools" / "coverage_dev_tools.ini"
        # Dev tools specific coverage paths
        self.dev_tools_coverage_data_file: Path = self.project_root / "development_tools" / ".coverage_dev_tools"
        self.dev_tools_coverage_json: Path = self.project_root / "development_tools" / "coverage_dev_tools.json"
        self.dev_tools_coverage_html_dir: Path = self.project_root / "development_tools" / "coverage_html_dev_tools"
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
        # Import constants from services.constants
        from development_tools.services.constants import CORE_MODULES
        self.core_modules = list(CORE_MODULES)
        
    def _configure_coverage_paths(self) -> None:
        """Load coverage configuration paths from coverage.ini."""
        if not self.coverage_config_path.exists():
            # Fall back to defaults
            self.coverage_data_file = self.project_root / ".coverage"
            self.coverage_html_dir = self.project_root / "htmlcov"
            return
        
        config = configparser.ConfigParser()
        config.read(self.coverage_config_path)
        
        data_file = config.get('run', 'data_file', fallback='').strip()
        if data_file:
            self.coverage_data_file = (self.coverage_config_path.parent / data_file).resolve()
        else:
            self.coverage_data_file = self.project_root / ".coverage"
        
        html_directory = config.get('html', 'directory', fallback='').strip()
        if html_directory:
            self.coverage_html_dir = (self.coverage_config_path.parent / html_directory).resolve()
        else:
            self.coverage_html_dir = self.project_root / "htmlcov"
        
        # Ensure parent directories exist when we later write artefacts
        self.coverage_data_file.parent.mkdir(parents=True, exist_ok=True)
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)

    def run_coverage_analysis(self) -> Dict[str, Dict[str, any]]:
        """Run pytest coverage analysis and extract metrics."""
        if logger:
            logger.info("Running pytest coverage analysis...")
        
        try:
            self.archived_directories.clear()
            self.command_logs.clear()
            self.pytest_stdout_log = None
            self.pytest_stderr_log = None
            
            coverage_output = self.project_root / "development_tools" / "coverage.json"
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
                cmd.extend(['-n', self.num_workers])
                # Use loadscope distribution to group tests by file/class for better isolation
                # This reduces race conditions by keeping related tests together
                cmd.extend(['--dist=loadscope'])
                if logger:
                    logger.info(f"Using parallel execution with {self.num_workers} workers (loadscope distribution)")
            
            cmd.extend([
                *cov_args,
                '--cov-report=term-missing',
                f'--cov-report=json:{coverage_output}',
                '--cov-config=coverage.ini',
                '--tb=line',  # Use line format for cleaner parallel output
                '-q',  # Quiet mode - reduces output noise
                '--maxfail=5',
                'tests/'
            ])
            
            # Log the command being run for debugging
            cmd_str = ' '.join(cmd[:10]) + (' ...' if len(cmd) > 10 else '')
            if logger:
                logger.info(f"Running pytest coverage command: {cmd_str}")
            
            # Check for problematic environment variables
            pytest_addopts = os.environ.get('PYTEST_ADDOPTS', '')
            if pytest_addopts and '--cov' in pytest_addopts:
                warning_msg = f"PYTEST_ADDOPTS contains --cov which may conflict: {pytest_addopts}"
                if logger:
                    logger.warning(warning_msg)
            
            env = os.environ.copy()
            env['COVERAGE_FILE'] = str(self.coverage_data_file)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env
            )
            
            self._record_pytest_output(result)
            
            # Parse test results to extract failures and random seed
            test_results = self._parse_pytest_test_results(result.stdout)
            
            # Check if coverage data was collected successfully
            coverage_data = self.parse_coverage_output(result.stdout)
            coverage_collected = bool(coverage_data) or coverage_output.exists()
            
            if not coverage_data and coverage_output.exists():
                coverage_data = self._load_coverage_json(coverage_output)
                coverage_collected = bool(coverage_data)
            
            overall_coverage = self.extract_overall_coverage(result.stdout)
            if not overall_coverage.get('overall_coverage') and coverage_output.exists():
                overall_coverage = self._extract_overall_from_json(coverage_output)
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
                self.finalize_coverage_outputs()
            except Exception as finalize_error:
                if logger:
                    logger.warning(f"Failed to finalize coverage artefacts: {finalize_error}")
            
            return {
                'modules': coverage_data,
                'overall': overall_coverage,
                'test_results': test_results,
                'coverage_collected': coverage_collected,
                'logs': {
                    'stdout': str(self.pytest_stdout_log) if self.pytest_stdout_log else None,
                    'stderr': str(self.pytest_stderr_log) if self.pytest_stderr_log else None,
                },
                'archived_directories': self.archived_directories,
                'command_logs': [str(path) for path in self.command_logs]
            }
            
        except Exception as e:
            if logger:
                logger.error(f"Error running coverage analysis: {e}")
            else:
                print(f"Error running coverage analysis: {e}")
            return {}

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
                '--maxfail=5',
                'tests/development_tools/'
            ]
            
            if logger:
                logger.info(f"Running dev tools coverage command: {' '.join(cmd[:5])} ...")
            
            env = os.environ.copy()
            env['COVERAGE_FILE'] = str(self.dev_tools_coverage_data_file)
            if dev_cov_config and dev_cov_config.exists():
                env['COVERAGE_RCFILE'] = str(dev_cov_config)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env
            )
            
            # Log stderr if there are errors
            if result.returncode != 0:
                if logger:
                    logger.warning(f"Dev tools coverage pytest exited with code {result.returncode}")
                    if result.stderr:
                        logger.warning(f"Pytest stderr: {result.stderr[:500]}")
            
            # Parse coverage results
            coverage_data = self.parse_coverage_output(result.stdout)
            if not coverage_data and coverage_output.exists():
                coverage_data = self._load_coverage_json(coverage_output)
            
            overall_coverage = self.extract_overall_coverage(result.stdout)
            if not overall_coverage.get('overall_coverage') and coverage_output.exists():
                overall_coverage = self._extract_overall_from_json(coverage_output)
            
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
            
            # Generate HTML report for dev tools
            if coverage_output.exists():
                self._generate_dev_tools_html_report()
            
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
                'html_dir': str(self.dev_tools_coverage_html_dir)
            }
            
        except Exception as e:
            if logger:
                logger.error(f"Error running dev tools coverage analysis: {e}")
            else:
                print(f"Error running dev tools coverage analysis: {e}")
            return {}

    def _generate_dev_tools_html_report(self) -> None:
        """Generate HTML coverage report for development tools."""
        env = os.environ.copy()
        env['COVERAGE_FILE'] = str(self.dev_tools_coverage_data_file)
        rcfile = self.dev_tools_coverage_config_path if self.dev_tools_coverage_config_path.exists() else self.coverage_config_path
        if rcfile and rcfile.exists():
            env['COVERAGE_RCFILE'] = str(rcfile)
        
        # Remove existing HTML directory
        if self.dev_tools_coverage_html_dir.exists():
            shutil.rmtree(self.dev_tools_coverage_html_dir)
        self.dev_tools_coverage_html_dir.mkdir(parents=True, exist_ok=True)
        
        coverage_cmd = [sys.executable, '-m', 'coverage']
        html_args = coverage_cmd + ['html', '-d', str(self.dev_tools_coverage_html_dir)]
        html_result = subprocess.run(
            html_args,
            capture_output=True,
            text=True,
            cwd=self.project_root,
            env=env
        )
        
        if html_result.returncode == 0:
            if logger:
                logger.info(f"Dev tools HTML coverage report generated: {self.dev_tools_coverage_html_dir}")
        else:
            if logger:
                logger.warning(f"Dev tools HTML report generation failed: {html_result.stderr}")

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
    
    def parse_coverage_output(self, output: str) -> Dict[str, Dict[str, any]]:
        """Parse the coverage output to extract module-specific metrics."""
        coverage_data = {}
        
        # Split output into sections
        sections = output.split('Name')
        if len(sections) < 2:
            return coverage_data
            
        coverage_section = sections[1]
        lines = coverage_section.strip().split('\n')
        
        for line in lines:
            if '---' in line or not line.strip():
                continue
                
            # Parse coverage line
            parts = line.split()
            if len(parts) >= 4:
                try:
                    module_name = parts[0]
                    statements = int(parts[1])
                    missed = int(parts[2])
                    coverage = int(parts[3].rstrip('%'))
                    
                    # Extract missing line numbers if available
                    missing_lines = []
                    if len(parts) > 4:
                        missing_part = ' '.join(parts[4:])
                        missing_lines = self.extract_missing_lines(missing_part)
                    
                    coverage_data[module_name] = {
                        'statements': statements,
                        'missed': missed,
                        'coverage': coverage,
                        'missing_lines': missing_lines,
                        'covered': statements - missed
                    }
                    
                except (ValueError, IndexError):
                    continue
                    
        return coverage_data

    def _load_coverage_json(self, json_path: Path) -> Dict[str, Dict[str, any]]:
        """Fallback parser that reads module metrics from coverage JSON output."""
        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            if logger:
                logger.warning(f"Unable to load coverage JSON data: {exc}")
            return {}
        
        files = data.get('files', {})
        coverage_data: Dict[str, Dict[str, any]] = {}
        
        for module_name, file_data in files.items():
            # Normalize path to use backslashes (Windows format) to match plan file format
            # Coverage JSON uses backslashes on Windows, but ensure consistency
            normalized_name = module_name.replace('/', '\\')
            
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
            
            coverage_data[normalized_name] = {
                'statements': statements,
                'missed': missed,
                'coverage': percent_value,
                'missing_lines': missing_line_strings,
                'covered': covered
            }
        
        return coverage_data
    
    def extract_missing_lines(self, missing_part: str) -> List[str]:
        """Extract missing line numbers from coverage output."""
        missing_lines = []
        
        # Look for patterns like "1-5, 10, 15-20"
        line_patterns = [
            r'(\d+)-(\d+)',  # Range like "1-5"
            r'(\d+)',        # Single line like "10"
        ]
        
        for pattern in line_patterns:
            matches = re.findall(pattern, missing_part)
            for match in matches:
                if len(match) == 2:  # Range
                    start, end = int(match[0]), int(match[1])
                    missing_lines.extend([str(i) for i in range(start, end + 1)])
                else:  # Single line
                    missing_lines.append(match[0])
                    
        return missing_lines
    
    def extract_overall_coverage(self, output: str) -> Dict[str, any]:
        """Extract overall coverage metrics."""
        overall_data = {
            'total_statements': 0,
            'total_missed': 0,
            'overall_coverage': 0.0
        }
        
        # Look for TOTAL line
        total_pattern = r'TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%'
        match = re.search(total_pattern, output)
        
        if match:
            total_statements = int(match.group(1))
            total_missed = int(match.group(2))
            overall_data['total_statements'] = total_statements
            overall_data['total_missed'] = total_missed
            # Calculate coverage with 1 decimal place for accuracy
            if total_statements > 0:
                overall_data['overall_coverage'] = round((total_statements - total_missed) / total_statements * 100, 1)
            else:
                overall_data['overall_coverage'] = 0.0
            
        return overall_data

    def _extract_overall_from_json(self, json_path: Path) -> Dict[str, any]:
        """Compute overall coverage using the JSON report."""
        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'total_statements': 0,
                'total_missed': 0,
                'overall_coverage': 0.0
            }
        
        files = data.get('files', {})
        total_statements = 0
        total_missed = 0
        
        for file_data in files.values():
            summary = file_data.get('summary', {})
            total_statements += int(summary.get('num_statements', 0))
            total_missed += int(summary.get('missing_lines', 0))
        
        if total_statements:
            percent = round((total_statements - total_missed) / total_statements * 100, 1)
        else:
            percent = 0.0
        
        return {
            'total_statements': total_statements,
            'total_missed': total_missed,
            'overall_coverage': percent
        }

    def finalize_coverage_outputs(self) -> None:
        """Combine coverage data, generate HTML, and clean up artefacts."""
        env = os.environ.copy()
        env['COVERAGE_FILE'] = str(self.coverage_data_file)
        if self.coverage_config_path.exists():
            env['COVERAGE_RCFILE'] = str(self.coverage_config_path)
        
        coverage_cmd = [sys.executable, '-m', 'coverage']
        
        shard_paths = self._collect_shard_paths()
        if shard_paths:
            combine_dirs = {
                self.project_root.resolve(),
                self.coverage_data_file.parent.resolve()
            }
            combine_args = coverage_cmd + ['combine'] + [str(path) for path in combine_dirs]
            combine_result = subprocess.run(
                combine_args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env
            )
            self._write_command_log('coverage_combine', combine_result)
            if combine_result.returncode != 0:
                stdout_message = (combine_result.stdout or "").strip()
                stderr_message = (combine_result.stderr or "").strip()
                if "No data to combine" in stdout_message:
                    if logger:
                        logger.info("coverage combine reported no data to combine; continuing.")
                elif logger:
                    logger.warning(
                        f"coverage combine exited with {combine_result.returncode}: {stderr_message or stdout_message}"
                    )
        else:
            skip_message = "Skipped coverage combine: no shard files detected."
            self._write_text_log('coverage_combine', skip_message)
            if logger:
                logger.info(skip_message)
        
        # Generate HTML report in the canonical directory
        if self.coverage_html_dir.exists():
            shutil.rmtree(self.coverage_html_dir)
        self.coverage_html_dir.mkdir(parents=True, exist_ok=True)
        
        html_args = coverage_cmd + ['html', '-d', str(self.coverage_html_dir)]
        html_result = subprocess.run(
            html_args,
            capture_output=True,
            text=True,
            cwd=self.project_root,
            env=env
        )
        self._write_command_log('coverage_html', html_result)
        if html_result.returncode != 0 and logger:
            logger.warning(
                f"coverage html exited with {html_result.returncode}: {html_result.stderr.strip()}"
            )
        
        self._cleanup_coverage_shards()
        self._archive_legacy_html_dirs()
        self._cleanup_shutdown_flag()
        self._cleanup_old_logs()

    def _write_command_log(self, command_name: str, result: subprocess.CompletedProcess) -> None:
        """Persist stdout/stderr for coverage helper commands."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.coverage_logs_dir / f"{command_name}_{timestamp}.log"
        latest_path = self.coverage_logs_dir / f"{command_name}.latest.log"
        
        content_lines = [
            f"# Command: {command_name}",
            f"# Return code: {result.returncode}",
            "",
            "## STDOUT",
            result.stdout or "",
            "",
            "## STDERR",
            result.stderr or ""
        ]
        log_text = "\n".join(content_lines)
        log_path.write_text(log_text, encoding='utf-8', errors='ignore')
        latest_path.write_text(log_text, encoding='utf-8', errors='ignore')
        self.command_logs.append(log_path)
        
        if logger:
            logger.info(f"Saved {command_name} logs to {log_path}")

    def _write_text_log(self, log_name: str, message: str) -> None:
        """Create a simple log file with a message."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.coverage_logs_dir / f"{log_name}_{timestamp}.log"
        latest_path = self.coverage_logs_dir / f"{log_name}.latest.log"
        content = f"# {log_name.replace('_', ' ').title()}\n\n{message}\n"
        log_path.write_text(content, encoding='utf-8', errors='ignore')
        latest_path.write_text(content, encoding='utf-8', errors='ignore')
        self.command_logs.append(log_path)

    def _collect_shard_paths(self) -> List[Path]:
        """Return a list of coverage shard files currently on disk."""
        shard_paths: List[Path] = []
        patterns = [
            self.project_root.glob('.coverage.*'),
            self.coverage_data_file.parent.glob(f"{self.coverage_data_file.name}.*")
        ]
        for iterator in patterns:
            for shard in iterator:
                if shard.exists():
                    shard_paths.append(shard)
        return shard_paths

    def _cleanup_coverage_shards(self) -> None:
        """Remove leftover .coverage.* files to prevent stale data."""
        removed = 0
        for shard in self._collect_shard_paths():
            try:
                shard.unlink()
                removed += 1
            except FileNotFoundError:
                continue
        
        # Remove root .coverage if different from configured data file
        root_coverage = self.project_root / ".coverage"
        if root_coverage.exists() and root_coverage.resolve() != self.coverage_data_file.resolve():
            try:
                root_coverage.unlink()
                removed += 1
            except FileNotFoundError:
                pass
        
        if logger and removed:
            logger.info(f"Removed {removed} stale coverage shard(s)")

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

    def _archive_legacy_html_dirs(self) -> None:
        """Archive and remove redundant legacy coverage HTML directories."""
        legacy_dirs = [
            self.project_root / "htmlcov",
            self.project_root / "tests" / "coverage_html",
            self.project_root / "tests" / "htmlcov"
        ]
        archive_root = self.project_root / "archive" / "coverage_artifacts"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        for legacy_dir in legacy_dirs:
            if not legacy_dir.exists():
                continue
            
            # Skip if this directory is the canonical destination
            if legacy_dir.resolve() == self.coverage_html_dir.resolve():
                continue
            
            destination = archive_root / timestamp / legacy_dir.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            if destination.exists():
                shutil.rmtree(destination)
            
            shutil.move(str(legacy_dir), str(destination))
            self.archived_directories.append({
                'source': str(legacy_dir),
                'destination': str(destination)
            })
            
            if logger:
                logger.info(f"Archived legacy coverage directory {legacy_dir} -> {destination}")

    def _cleanup_shutdown_flag(self) -> None:
        """Remove the transient shutdown_request.flag file if it was created."""
        flag_path = self.project_root / "shutdown_request.flag"
        if flag_path.exists():
            try:
                flag_path.unlink()
                if logger:
                    logger.info("Removed stray shutdown_request.flag")
            except OSError as exc:
                if logger:
                    logger.warning(f"Unable to remove shutdown_request.flag: {exc}")
    
    def _cleanup_old_logs(self) -> None:
        """Remove old coverage regeneration logs, keeping only the latest files."""
        if not self.coverage_logs_dir.exists():
            return
        
        # Group log files by base name (e.g., pytest_stdout, coverage_html)
        log_groups = {}
        for log_file in self.coverage_logs_dir.glob("*.log"):
            # Skip .latest.log files - always keep these
            if log_file.name.endswith(".latest.log"):
                continue
            
            # Extract base name (e.g., "pytest_stdout_20251103-010734.log" -> "pytest_stdout")
            base_name = log_file.stem
            # Remove timestamp pattern (YYYYMMDD-HHMMSS)
            parts = base_name.split("_")
            # Try to find the base name by removing timestamp
            if len(parts) >= 3:
                # Pattern: name_20251103_010734 or name_20251103-010734
                possible_base = "_".join(parts[:-2])  # Remove last two parts if timestamp
                if not (len(parts[-2]) == 8 and len(parts[-1]) == 6):  # Not a timestamp
                    possible_base = base_name
            else:
                possible_base = base_name
            
            # More robust: check if last part looks like a timestamp
            if "_" in base_name:
                parts = base_name.rsplit("_", 1)
                if len(parts) == 2 and len(parts[1]) in [15, 14]:  # timestamp length
                    possible_base = parts[0]
                else:
                    possible_base = base_name
            else:
                possible_base = base_name
            
            if "-" in possible_base:
                # Handle hyphenated timestamps like "20251103-010734"
                possible_base = possible_base.rsplit("-", 1)[0]
                if "_" in possible_base:
                    possible_base = possible_base.rsplit("_", 1)[0]
            
            if possible_base not in log_groups:
                log_groups[possible_base] = []
            log_groups[possible_base].append(log_file)
        
        removed_count = 0
        # For each group, keep only the 2 most recent files (plus the .latest.log)
        for base_name, log_files in log_groups.items():
            if len(log_files) <= 2:
                continue  # Keep all if we have 2 or fewer
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            # Keep only the 2 most recent, remove the rest
            files_to_remove = log_files[2:]
            
            for log_file in files_to_remove:
                try:
                    log_file.unlink()
                    removed_count += 1
                except Exception as exc:
                    if logger:
                        logger.warning(f"Unable to remove old log {log_file}: {exc}")
        
        if logger and removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old coverage log files")
    
    def categorize_modules(self, coverage_data: Dict[str, Dict[str, any]]) -> Dict[str, List[str]]:
        """Categorize modules by coverage level."""
        categories = {
            'excellent': [],      # 80%+
            'good': [],           # 60-79%
            'moderate': [],       # 40-59%
            'needs_work': [],     # 20-39%
            'critical': []        # <20%
        }
        
        for module_name, data in coverage_data.items():
            coverage = data['coverage']
            
            if coverage >= 80:
                categories['excellent'].append(module_name)
            elif coverage >= 60:
                categories['good'].append(module_name)
            elif coverage >= 40:
                categories['moderate'].append(module_name)
            elif coverage >= 20:
                categories['needs_work'].append(module_name)
            else:
                categories['critical'].append(module_name)
                
        return categories
    
    def generate_coverage_summary(self, coverage_data: Dict[str, Dict[str, any]], 
                                overall_data: Dict[str, any]) -> str:
        """Generate a coverage summary for the plan."""
        summary_lines = []
        
        # Overall coverage (format with 1 decimal place for accuracy)
        coverage_value = overall_data['overall_coverage']
        if isinstance(coverage_value, float):
            coverage_str = f"{coverage_value:.1f}"
        elif isinstance(coverage_value, int):
            coverage_str = f"{coverage_value:.0f}"
        else:
            coverage_str = str(coverage_value)
        summary_lines.append(f"### **Overall Coverage: {coverage_str}%**")
        summary_lines.append(f"- **Total Statements**: {overall_data['total_statements']:,}")
        summary_lines.append(f"- **Covered Statements**: {overall_data['total_statements'] - overall_data['total_missed']:,}")
        summary_lines.append(f"- **Uncovered Statements**: {overall_data['total_missed']:,}")
        summary_lines.append(f"- **Goal**: Expand to **80%+ coverage** for comprehensive reliability\n")
        
        # Coverage by category
        categories = self.categorize_modules(coverage_data)
        
        summary_lines.append("### **Coverage Summary by Category**")
        
        for category, modules in categories.items():
            if modules:
                avg_coverage = sum(coverage_data[m]['coverage'] for m in modules) / len(modules)
                summary_lines.append(f"- **{category.title()} ({avg_coverage:.0f}% avg)**: {len(modules)} modules")
                
        summary_lines.append("")
        
        # Detailed module breakdown
        summary_lines.append("### **Detailed Module Coverage**")
        
        # Sort modules by coverage (lowest first)
        sorted_modules = sorted(coverage_data.items(), key=lambda x: x[1]['coverage'])
        
        for module_name, data in sorted_modules:
            status_emoji = "*" if data['coverage'] >= 80 else "!" if data['coverage'] >= 60 else "X"
            summary_lines.append(f"- **{status_emoji} {module_name}**: {data['coverage']}% ({data['covered']}/{data['statements']} lines)")
            
        return '\n'.join(summary_lines)
    
    def update_coverage_plan(self, coverage_summary: str) -> bool:
        """Update the TEST_COVERAGE_EXPANSION_PLAN.md with new metrics."""
        generated_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Standard generated header
        standard_header = f"""# Test Coverage Expansion Plan

> **File**: `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`
> **Generated**: This file is auto-generated by regenerate_coverage_metrics.py. Do not edit manually.
> **Generated by**: regenerate_coverage_metrics.py - Coverage Metrics Regenerator
> **Last Generated**: {generated_timestamp}
> **Source**: `python development_tools/regenerate_coverage_metrics.py --update-plan`

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
                '> **Generated by**: regenerate_coverage_metrics.py' in content
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
            logger.error("Failed to get coverage data")
            return {}
        
        # Generate summary
        coverage_summary = self.generate_coverage_summary(
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
