#!/usr/bin/env python3
# TOOL_TIER: core

"""
generate_test_coverage_report.py
Generates coverage reports (JSON, HTML, summary, TEST_COVERAGE_REPORT.md) from analysis results.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

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

    def __init__(
        self,
        project_root: str = ".",
        coverage_config: Optional[str] = None,
        artifact_directories: Optional[Dict[str, str]] = None,
    ):
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
        coverage_config_data = config.get_external_value("coverage", {})

        # Coverage config path (from parameter, config, or default)
        if coverage_config is not None:
            self.coverage_config_path = self.project_root / coverage_config
        else:
            # Check for coverage.ini in development_tools/tests first (new location), then root (legacy)
            config_coverage_path = coverage_config_data.get(
                "coverage_config", "development_tools/tests/coverage.ini"
            )
            self.coverage_config_path = self.project_root / config_coverage_path
            if not self.coverage_config_path.exists():
                # Fall back to root location for backward compatibility
                self.coverage_config_path = self.project_root / "coverage.ini"

        # Artifact directories (from parameter, config, or defaults)
        if artifact_directories is not None:
            self.coverage_html_dir = Path(
                artifact_directories.get("html_output", "tests/coverage_html")
            )
            self.archive_root = Path(
                artifact_directories.get(
                    "archive", "development_tools/reports/archive/coverage_artifacts"
                )
            )
            self.coverage_logs_dir = Path(
                artifact_directories.get("logs", "development_tools/tests/logs")
            )
        else:
            config_dirs = coverage_config_data.get("artifact_directories", {})
            self.coverage_html_dir = Path(
                config_dirs.get("html_output", "tests/coverage_html")
            )
            self.archive_root = Path(
                config_dirs.get(
                    "archive", "development_tools/reports/archive/coverage_artifacts"
                )
            )
            self.coverage_logs_dir = Path(
                config_dirs.get("logs", "development_tools/tests/logs")
            )

        # Ensure directories exist
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)
        self.archive_root.mkdir(parents=True, exist_ok=True)
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)

        # Coverage data file
        self.coverage_data_file = self.project_root / ".coverage"

        # Coverage plan file (TEST_COVERAGE_REPORT.md)
        self.coverage_plan_file = (
            self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
        )

    def generate_coverage_summary(
        self, coverage_data: Dict[str, Dict[str, any]], overall_data: Dict[str, any]
    ) -> str:
        """Generate a coverage summary for the plan."""
        summary_lines = []

        # Overall coverage (format with 1 decimal place for accuracy)
        coverage_value = overall_data["overall_coverage"]
        if isinstance(coverage_value, float):
            coverage_str = f"{coverage_value:.1f}"
        elif isinstance(coverage_value, int):
            coverage_str = f"{coverage_value:.0f}"
        else:
            coverage_str = str(coverage_value)
        summary_lines.append(f"### **Overall Coverage: {coverage_str}%**")
        summary_lines.append(
            f"- **Total Statements**: {overall_data['total_statements']:,}"
        )
        summary_lines.append(
            f"- **Covered Statements**: {overall_data['total_statements'] - overall_data['total_missed']:,}"
        )
        summary_lines.append(
            f"- **Uncovered Statements**: {overall_data['total_missed']:,}"
        )
        summary_lines.append(
            f"- **Goal**: Expand to **80%+ coverage** for comprehensive reliability\n"
        )

        # Coverage by category
        try:
            from .analyze_test_coverage import TestCoverageAnalyzer
        except ImportError:
            from development_tools.tests.analyze_test_coverage import (
                TestCoverageAnalyzer,
            )
        analyzer = TestCoverageAnalyzer(str(self.project_root))
        categories = analyzer.categorize_modules(coverage_data)

        summary_lines.append("### **Coverage Summary by Category**")

        for category, modules in categories.items():
            if modules:
                avg_coverage = sum(coverage_data[m]["coverage"] for m in modules) / len(
                    modules
                )
                summary_lines.append(
                    f"- **{category.title()} ({avg_coverage:.0f}% avg)**: {len(modules)} modules"
                )

        summary_lines.append("")

        # Detailed module breakdown
        summary_lines.append("### **Detailed Module Coverage**")

        # Sort modules by coverage (lowest first)
        sorted_modules = sorted(coverage_data.items(), key=lambda x: x[1]["coverage"])

        for module_name, data in sorted_modules:
            status_emoji = (
                "*"
                if data["coverage"] >= 80
                else "!" if data["coverage"] >= 60 else "X"
            )
            summary_lines.append(
                f"- **{status_emoji} {module_name}**: {data['coverage']}% ({data['covered']}/{data['statements']} lines)"
            )

        return "\n".join(summary_lines)

    def update_coverage_plan(self, coverage_summary: str) -> bool:
        """Update the TEST_COVERAGE_REPORT.md with new metrics."""
        generated_timestamp = now_timestamp_full()

        # Standard generated header
        standard_header = f"""# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: {generated_timestamp}
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

"""

        if not self.coverage_plan_file.exists():
            # Create new file with standard header and rotation
            from development_tools.shared.file_rotation import create_output_file

            try:
                content = (
                    standard_header + "## Current Status\n\n" + coverage_summary + "\n"
                )
                create_output_file(
                    str(self.coverage_plan_file),
                    content,
                    rotate=True,
                    max_versions=7,
                    project_root=self.project_root,
                )
                if logger:
                    logger.info(
                        f"Created coverage plan with standard header: {self.coverage_plan_file}"
                    )
                return True
            except Exception as e:
                if logger:
                    logger.error(f"Error creating coverage plan: {e}")
                return False

        try:
            with open(self.coverage_plan_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if file has standard generated header
            # LEGACY COMPATIBILITY
            # Accept both TEST_COVERAGE_REPORT.md (new) and TEST_COVERAGE_EXPANSION_PLAN.md (old) in header check.
            # New standardized filename: TEST_COVERAGE_REPORT.md
            # Removal plan: After one release cycle, remove check for TEST_COVERAGE_EXPANSION_PLAN.md in header.
            # Detection: Search for "TEST_COVERAGE_EXPANSION_PLAN.md" in header checks.
            has_standard_header = (
                (
                    "> **File**: `development_docs/TEST_COVERAGE_REPORT.md`" in content
                    or "> **File**: `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md`"
                    in content
                )
                and "> **Generated**: This file is auto-generated" in content
                and (
                    "> **Source**:" in content
                    or "> **Generated by**: generate_test_coverage.py" in content
                )
            )
            if (
                "TEST_COVERAGE_EXPANSION_PLAN.md" in content
                and "TEST_COVERAGE_REPORT.md" not in content
            ):
                logger.debug(
                    "LEGACY: Detected old filename TEST_COVERAGE_EXPANSION_PLAN.md in header (new name: TEST_COVERAGE_REPORT.md)"
                )

            # Find and replace the current status section
            section_header = "## Current Status"
            current_status_pattern = r"(## Current Status.*?)(?=\n## |\Z)"

            new_status_section = f"{section_header}\n\n{coverage_summary}\n"

            if has_standard_header:
                # File has standard header - just update the status section and timestamp
                if re.search(current_status_pattern, content, re.DOTALL):
                    updated_content = re.sub(
                        current_status_pattern,
                        lambda _: new_status_section,
                        content,
                        flags=re.DOTALL,
                    )
                else:
                    # Add status section after header
                    header_end = content.find("\n## ")
                    if header_end == -1:
                        header_end = len(content)
                    updated_content = (
                        content[:header_end]
                        + "\n\n"
                        + new_status_section
                        + content[header_end:]
                    )

                # Update the last generated timestamp
                timestamp_pattern = r"(> \*\*Last Generated\*\*: ).*"
                if re.search(timestamp_pattern, updated_content):
                    updated_content = re.sub(
                        timestamp_pattern,
                        lambda match: f"{match.group(1)}{generated_timestamp}",
                        updated_content,
                    )
                else:
                    # If timestamp not found, add it after the Source line
                    source_pattern = r"(> \*\*Source\*\*:.*\n)"
                    if re.search(source_pattern, updated_content):
                        updated_content = re.sub(
                            source_pattern,
                            lambda match: f"{match.group(1)}> **Last Generated**: {generated_timestamp}\n",
                            updated_content,
                        )

                # Remove duplicate headers - if we have multiple header sections, keep only the first one
                # Pattern: header section starts with "# Test Coverage Report" and ends before "## Current Status"
                header_pattern = (
                    r"(# Test Coverage Report.*?> \*\*Last Generated\*\*:.*?\n\n)"
                )
                matches = list(re.finditer(header_pattern, updated_content, re.DOTALL))
                if len(matches) > 1:
                    # Keep only the first header, remove the rest
                    first_header_end = matches[0].end()
                    # Find where the second header starts
                    second_header_start = matches[1].start()
                    # Remove everything from first header end to second header start, but keep the content after
                    updated_content = (
                        updated_content[:first_header_end]
                        + updated_content[second_header_start:]
                    )
                    # Now remove any remaining duplicate headers
                    while True:
                        new_matches = list(
                            re.finditer(header_pattern, updated_content, re.DOTALL)
                        )
                        if len(new_matches) <= 1:
                            break
                        # Remove second header
                        updated_content = (
                            updated_content[: new_matches[0].end()]
                            + updated_content[new_matches[1].end() :]
                        )
            else:
                # File doesn't have standard header - replace with standard header
                # Find the title
                title_match = re.search(
                    r"^# Test Coverage Expansion Plan.*?\n", content, re.MULTILINE
                )
                if title_match:
                    # Replace everything from title to first section with standard header
                    title_end = title_match.end()
                    first_section_match = re.search(r"\n## ", content[title_end:])
                    if first_section_match:
                        section_start = title_end + first_section_match.start()
                        updated_content = standard_header + content[section_start:]
                    else:
                        updated_content = standard_header + content[title_end:]
                else:
                    # No title found, prepend standard header
                    updated_content = standard_header + content

                # Ensure status section exists
                if "## Current Status" not in updated_content:
                    updated_content = (
                        updated_content.rstrip() + "\n\n" + new_status_section
                    )
                else:
                    # Replace existing status section
                    updated_content = re.sub(
                        current_status_pattern,
                        lambda _: new_status_section,
                        updated_content,
                        flags=re.DOTALL,
                    )

            # Write updated content
            # Use rotation system for archiving
            from development_tools.shared.file_rotation import create_output_file

            create_output_file(
                str(self.coverage_plan_file),
                updated_content,
                rotate=True,
                max_versions=7,
                project_root=self.project_root,
            )

            if logger:
                logger.info(f"Updated coverage plan: {self.coverage_plan_file}")
            return True

        except Exception as e:
            if logger:
                logger.error(f"Error updating coverage plan: {e}")
            return False

    def finalize_coverage_outputs(self) -> None:
        """Finalize coverage outputs by combining shards and generating HTML/JSON reports."""
        # Set up coverage command and environment
        coverage_cmd = [sys.executable, "-m", "coverage"]
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(self.coverage_data_file)
        if self.coverage_config_path.exists():
            env["COVERAGE_RCFILE"] = str(self.coverage_config_path)

        # Combine coverage data files if they exist
        coverage_data_files = list(self.project_root.glob(".coverage.*"))

        if coverage_data_files:
            if logger:
                logger.info(
                    f"Combining {len(coverage_data_files)} coverage data files..."
                )

            # Use coverage combine command
            combine_cmd = coverage_cmd + ["combine"]

            combine_result = subprocess.run(
                combine_cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                env=env,
            )

            if combine_result.returncode != 0 and logger:
                logger.warning(
                    f"coverage combine exited with {combine_result.returncode}: {combine_result.stderr.strip()}"
                )

            # Clean up shard files after combining
            for shard_file in coverage_data_files:
                try:
                    shard_file.unlink()
                    if logger:
                        logger.debug(f"Removed coverage shard file: {shard_file}")
                except Exception as e:
                    if logger:
                        logger.warning(f"Failed to remove shard file {shard_file}: {e}")

        # Generate HTML report
        if logger:
            logger.info("Generating HTML coverage report...")

        # Ensure HTML output directory exists
        self.coverage_html_dir.mkdir(parents=True, exist_ok=True)

        html_args = coverage_cmd + ["html", "-d", str(self.coverage_html_dir)]
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
                timeout=html_timeout,
            )
        except subprocess.TimeoutExpired:
            if logger:
                logger.warning(
                    f"coverage html timed out after {html_timeout} seconds - HTML generation may be incomplete"
                )
            html_result = subprocess.CompletedProcess(
                html_args,
                returncode=1,
                stdout="",
                stderr=f"coverage html timed out after {html_timeout} seconds",
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

            rotator = FileRotator(base_dir=str(archive_dir))
            # Use _cleanup_old_versions with the base name (without extension)
            rotator._cleanup_old_versions(
                "coverage", max_versions=6
            )  # Keep 6 archived (current is separate)

        # Generate JSON report
        json_args = coverage_cmd + ["json", "-o", str(coverage_output)]
        json_result = subprocess.run(
            json_args, capture_output=True, text=True, cwd=self.project_root, env=env
        )

        if json_result.returncode == 0:
            if logger:
                logger.info(f"Coverage JSON report generated: {coverage_output}")
        else:
            if logger:
                logger.warning(
                    f"coverage json exited with {json_result.returncode}: {json_result.stderr.strip()}"
                )


def main():
    """Main entry point for standalone report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate test coverage reports from existing coverage data"
    )
    parser.add_argument(
        "--coverage-json",
        type=str,
        default="development_tools/tests/jsons/coverage.json",
        help="Path to coverage.json file (default: development_tools/tests/jsons/coverage.json)",
    )
    parser.add_argument(
        "--update-plan",
        action="store_true",
        help="Update TEST_COVERAGE_REPORT.md with current coverage metrics",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print coverage summary to stdout"
    )

    args = parser.parse_args()

    # Load coverage data
    # Resolve path relative to project root if it's a relative path
    coverage_json_path = Path(args.coverage_json)
    if not coverage_json_path.is_absolute():
        # Assume relative to project root (where script is run from)
        # When run via run_script, cwd is project_root, so relative paths work
        # But we also need to handle when run directly, so resolve from script location
        script_project_root = Path(__file__).parent.parent.parent
        coverage_json_path = script_project_root / coverage_json_path

    if not coverage_json_path.exists():
        logger.error(f"Coverage JSON file not found: {coverage_json_path}")
        logger.error("Run test coverage first to generate coverage data")
        return 1

    # Determine project root from coverage.json path
    # coverage.json is at: project_root/development_tools/tests/jsons/coverage.json
    # So we need to go up 4 levels: coverage.json -> jsons -> tests -> development_tools -> project_root
    project_root = coverage_json_path.parent.parent.parent.parent

    # Load coverage data
    try:
        with open(coverage_json_path, "r", encoding="utf-8") as f:
            coverage_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load coverage JSON: {e}")
        return 1

    # Parse coverage data (coverage.json format)
    try:
        from .analyze_test_coverage import TestCoverageAnalyzer
    except ImportError:
        from development_tools.tests.analyze_test_coverage import TestCoverageAnalyzer
    analyzer = TestCoverageAnalyzer(str(project_root))
    analysis_results = analyzer.analyze_coverage(coverage_json_path=coverage_json_path)

    # Create report generator with project root
    generator = TestCoverageReportGenerator(project_root=str(project_root))

    # Generate summary
    coverage_data_dict = analysis_results.get("modules", {})
    overall_data = analysis_results.get("overall", {})
    coverage_summary = generator.generate_coverage_summary(
        coverage_data_dict, overall_data
    )

    # Update plan if requested
    if args.update_plan:
        success = generator.update_coverage_plan(coverage_summary)
        if success:
            print("\n* Coverage plan updated successfully!")
        else:
            print("\n* Failed to update coverage plan")
            return 1

    if args.summary:
        print(coverage_summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
