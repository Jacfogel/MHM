#!/usr/bin/env python3
# TOOL_TIER: core

"""
generate_test_coverage_reports.py
Generates coverage reports (JSON, HTML, summary) from analysis results.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Import config module (absolute import for portability)
try:
    from development_tools import config
except ImportError:
    # Fallback for when run as script
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config

# Load external config on module import (safe to call multiple times)
config.load_external_config()

logger = get_component_logger("development_tools")


class TestCoverageReportGenerator:
    """Generates coverage reports from analysis results."""
    
    def __init__(self, project_root: str = ".", coverage_config: Optional[str] = None,
                 artifact_directories: Optional[Dict[str, str]] = None):
        """
        Initialize coverage report generator.
        
        Args:
            project_root: Root directory of the project
            coverage_config: Optional path to coverage config file (e.g., 'coverage.ini').
                            If None, loads from config or uses default.
            artifact_directories: Optional dict with keys: html_output, archive, logs.
                                 If None, loads from config or uses defaults.
        """
        self.project_root = Path(project_root).resolve()
        
        # Load coverage configuration from external config
        coverage_config_data = config.get_external_value('coverage', {})
        
        # Coverage config path (from parameter, config, or default)
        if coverage_config is not None:
            self.coverage_config_path = self.project_root / coverage_config
        else:
            # Check for coverage.ini in development_tools/tests first (new location), then root (legacy)
            config_coverage_path = coverage_config_data.get('coverage_config', 'development_tools/tests/coverage.ini')
            self.coverage_config_path = self.project_root / config_coverage_path
            if not self.coverage_config_path.exists():
                # Fall back to root location for backward compatibility
                self.coverage_config_path = self.project_root / "coverage.ini"
        
        # Artifact directories (from parameter, config, or defaults)
        if artifact_directories is not None:
            self.coverage_html_dir = Path(artifact_directories.get('html_output', 'tests/coverage_html'))
            self.archive_root = Path(artifact_directories.get('archive', 'development_tools/reports/archive/coverage_artifacts'))
            self.coverage_logs_dir = Path(artifact_directories.get('logs', 'development_tools/tests/logs'))
        else:
            config_dirs = coverage_config_data.get('artifact_directories', {})
            self.coverage_html_dir = Path(config_dirs.get('html_output', 'tests/coverage_html'))
            self.archive_root = Path(config_dirs.get('archive', 'development_tools/reports/archive/coverage_artifacts'))
            self.coverage_logs_dir = Path(config_dirs.get('logs', 'development_tools/tests/logs'))
        
        # Ensure directories exist
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)
        self.archive_root.mkdir(parents=True, exist_ok=True)
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Coverage data file
        self.coverage_data_file = self.project_root / ".coverage"
    
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
        from .analyze_test_coverage import TestCoverageAnalyzer
        analyzer = TestCoverageAnalyzer(str(self.project_root))
        categories = analyzer.categorize_modules(coverage_data)
        
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
            # Add timeout for combine operation (should be fast, but add safety timeout)
            combine_timeout = 60  # 1 minute should be plenty for combining coverage data
            try:
                combine_result = subprocess.run(
                    combine_args,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    env=env,
                    timeout=combine_timeout
                )
            except subprocess.TimeoutExpired:
                if logger:
                    logger.warning(f"coverage combine timed out after {combine_timeout} seconds")
                combine_result = subprocess.CompletedProcess(
                    combine_args,
                    returncode=1,
                    stdout="",
                    stderr=f"coverage combine timed out after {combine_timeout} seconds"
                )
            # No longer creating coverage_combine logs - user only uses stdout logs
            # self._write_command_log('coverage_combine', combine_result)
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
            # No longer creating coverage_combine logs - user only uses stdout logs
            # self._write_text_log('coverage_combine', skip_message)
            if logger:
                logger.info(skip_message)
        
        # Generate HTML report in the canonical directory
        if self.coverage_html_dir.exists():
            shutil.rmtree(self.coverage_html_dir)
        self.coverage_html_dir.mkdir(parents=True, exist_ok=True)
        
        html_args = coverage_cmd + ['html', '-d', str(self.coverage_html_dir)]
        # Add timeout for HTML generation (10 minutes should be plenty for most codebases)
        # If it takes longer, there may be an issue with the coverage data
        html_timeout = 600  # 10 minutes
        try:
            html_result = subprocess.run(
                html_args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env,
                timeout=html_timeout
            )
        except subprocess.TimeoutExpired:
            if logger:
                logger.warning(f"coverage html timed out after {html_timeout} seconds - HTML generation may be incomplete")
            html_result = subprocess.CompletedProcess(
                html_args,
                returncode=1,
                stdout="",
                stderr=f"coverage html timed out after {html_timeout} seconds"
            )
        # No longer creating coverage_html logs - user only uses stdout logs
        # self._write_command_log('coverage_html', html_result)
        if html_result.returncode != 0 and logger:
            logger.warning(
                f"coverage html exited with {html_result.returncode}: {html_result.stderr.strip()}"
            )
        
        # Regenerate JSON report after combine to ensure it reflects combined data
        # Use the same location as generate_test_coverage.py (development_tools/tests/jsons/coverage.json)
        jsons_dir = self.project_root / "development_tools" / "tests" / "jsons"
        jsons_dir.mkdir(parents=True, exist_ok=True)
        coverage_output = jsons_dir / "coverage.json"
        
        # Archive the old coverage.json BEFORE creating the new one (to keep current file in main directory)
        archive_dir = jsons_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        if coverage_output.exists():
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            archive_name = f"coverage_{timestamp}.json"
            archive_path = archive_dir / archive_name
            shutil.move(str(coverage_output), str(archive_path))
            if logger:
                logger.debug(f"Archived old coverage.json to {archive_name}")
            
            # Clean up old archives to keep only 7 versions (current + 6 archived = 7 total)
            from development_tools.shared.file_rotation import FileRotator
            rotator = FileRotator(base_dir=str(jsons_dir))
            rotator._cleanup_old_versions("coverage", max_versions=6)  # Keep 6 archived (current is separate)
        
        json_args = coverage_cmd + ['json', '-o', str(coverage_output.resolve())]
        # Add timeout for JSON generation (should be fast, but add safety timeout)
        json_timeout = 120  # 2 minutes should be plenty for JSON generation
        try:
            json_result = subprocess.run(
                json_args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env,
                timeout=json_timeout
            )
        except subprocess.TimeoutExpired:
            if logger:
                logger.warning(f"coverage json timed out after {json_timeout} seconds")
            json_result = subprocess.CompletedProcess(
                json_args,
                returncode=1,
                stdout="",
                stderr=f"coverage json timed out after {json_timeout} seconds"
            )
        if json_result.returncode != 0 and logger:
            logger.warning(f"coverage json exited with {json_result.returncode}: {json_result.stderr.strip()}")
        elif logger:
            logger.debug(f"Regenerated coverage.json after combine")
        
        self._cleanup_coverage_shards()
        self._archive_legacy_html_dirs()
        self._cleanup_shutdown_flag()
        self._cleanup_old_logs()
    
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
    
    def _archive_legacy_html_dirs(self) -> None:
        """Archive and remove redundant legacy coverage HTML directories."""
        legacy_dirs = [
            self.project_root / "htmlcov",
            self.project_root / "tests" / "coverage_html",
            self.project_root / "tests" / "htmlcov"
        ]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        for legacy_dir in legacy_dirs:
            if not legacy_dir.exists():
                continue
            
            # Skip if this directory is the canonical destination
            if legacy_dir.resolve() == self.coverage_html_dir.resolve():
                continue
            
            destination = self.archive_root / timestamp / legacy_dir.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            if destination.exists():
                shutil.rmtree(destination)
            
            shutil.move(str(legacy_dir), str(destination))
            
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
            # Skip .latest.log files - we no longer create these
            if log_file.name.endswith(".latest.log"):
                # Remove old .latest.log files
                try:
                    log_file.unlink()
                except Exception:
                    pass
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
        # For each group, keep only the 5 most recent files (archive older ones)
        for base_name, log_files in log_groups.items():
            if len(log_files) <= 5:
                continue  # Keep all if we have 5 or fewer
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            # Keep only the 5 most recent, archive the rest
            files_to_archive = log_files[5:]
            
            # Archive older files instead of deleting them
            archive_dir = self.coverage_logs_dir / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            for log_file in files_to_archive:
                try:
                    archive_path = archive_dir / log_file.name
                    shutil.move(str(log_file), str(archive_path))
                    removed_count += 1
                except Exception as exc:
                    if logger:
                        logger.debug(f"Failed to archive {log_file.name}: {exc}")
            
            # Clean up archive if it has more than 5 files
            archived_files = sorted(
                archive_dir.glob(f"{base_name}_*.log"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            if len(archived_files) > 5:
                for old_file in archived_files[5:]:
                    try:
                        old_file.unlink()
                    except Exception:
                        pass
        
        if logger and removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old coverage log files")
    
    def _write_command_log(self, command_name: str, result: subprocess.CompletedProcess) -> None:
        """Persist stdout/stderr for coverage helper commands."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.coverage_logs_dir / f"{command_name}_{timestamp}.log"
        # No longer creating .latest.log files - only timestamped versions
        # latest_path = self.coverage_logs_dir / f"{command_name}.latest.log"
        
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
        # No longer creating .latest.log files
        
        if logger:
            logger.info(f"Saved {command_name} logs to {log_path}")
    
    def _write_text_log(self, log_name: str, message: str) -> None:
        """Create a simple log file with a message."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = self.coverage_logs_dir / f"{log_name}_{timestamp}.log"
        # No longer creating .latest.log files
        content = f"# {log_name.replace('_', ' ').title()}\n\n{message}\n"
        log_path.write_text(content, encoding='utf-8', errors='ignore')


def main():
    """Main entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test coverage reports')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file with analysis results')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--summary', action='store_true', help='Generate summary text')
    
    args = parser.parse_args()
    
    # Load analysis results
    with open(args.input, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)
    
    generator = TestCoverageReportGenerator()
    
    if args.html:
        generator.finalize_coverage_outputs()
    
    if args.summary:
        coverage_data = analysis_results.get('modules', {})
        overall_data = analysis_results.get('overall', {})
        summary = generator.generate_coverage_summary(coverage_data, overall_data)
        print(summary)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

