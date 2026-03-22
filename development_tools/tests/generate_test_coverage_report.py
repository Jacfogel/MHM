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
import configparser
import ast
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

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

from development_tools.shared.standard_exclusions import should_exclude_file

logger = get_component_logger("development_tools")


class TestCoverageReportGenerator:
    """Generates coverage reports from analysis results."""

    def __init__(
        self,
        project_root: str = ".",
        coverage_config: str | None = None,
        artifact_directories: dict[str, str] | None = None,
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
            config_coverage_path = coverage_config_data.get(
                "coverage_config", "development_tools/tests/coverage.ini"
            )
            self.coverage_config_path = self.project_root / config_coverage_path

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
        self.coverage_data_file = self.project_root / ".coverage"
        self._configure_paths_from_coverage_ini()
        self.coverage_html_dir.parent.mkdir(parents=True, exist_ok=True)
        self.archive_root.mkdir(parents=True, exist_ok=True)
        self.coverage_logs_dir.mkdir(parents=True, exist_ok=True)

        # Coverage plan file (TEST_COVERAGE_REPORT.md)
        self.coverage_plan_file = (
            self.project_root / "development_docs" / "TEST_COVERAGE_REPORT.md"
        )

    def _configure_paths_from_coverage_ini(self) -> None:
        """Override default coverage paths when coverage.ini explicitly sets them."""
        if not self.coverage_config_path.exists():
            return
        parser = configparser.ConfigParser()
        parser.read(self.coverage_config_path)
        data_file = parser.get("run", "data_file", fallback="").strip()
        if data_file:
            # Resolve ${COVERAGE_DATA_DIR} to config dir so path works when env is unset
            if "${COVERAGE_DATA_DIR}" in data_file:
                data_file = data_file.replace(
                    "${COVERAGE_DATA_DIR}", str(self.coverage_config_path.parent)
                ).replace("/", os.sep)
            if not os.path.isabs(data_file):
                data_file = str(self.project_root / data_file)
            self.coverage_data_file = Path(data_file).resolve()
        html_directory = parser.get("html", "directory", fallback="").strip()
        if html_directory:
            self.coverage_html_dir = (self.project_root / html_directory).resolve()

    def generate_coverage_summary(
        self, coverage_data: dict[str, dict[str, Any]], overall_data: dict[str, Any]
    ) -> str:
        """Generate a coverage summary for the plan."""
        summary_lines = []
        # Derive domains from actual coverage data so all measured domains are shown.
        # Fallback to coverage.ini source or standard list if coverage_data is empty.
        configured_domains = []
        if coverage_data:
            seen = set()
            for module_name in coverage_data:
                normalized = str(module_name).replace("\\", "/")
                domain = normalized.split("/", 1)[0]
                if domain and domain != "development_tools" and domain not in seen:
                    seen.add(domain)
                    configured_domains.append(domain)
            configured_domains.sort()
        if not configured_domains:
            try:
                import configparser
                from pathlib import Path
                cov_ini = self.project_root / "development_tools" / "tests" / "coverage.ini"
                if cov_ini.exists():
                    parser = configparser.ConfigParser()
                    parser.read(cov_ini)
                    source = parser.get("run", "source", fallback="").strip()
                    if source:
                        configured_domains = [s.strip() for s in source.split(",") if s.strip()]
            except Exception:
                pass
        if not configured_domains:
            configured_domains = [
                "ai",
                "communication",
                "core",
                "notebook",
                "tasks",
                "ui",
                "user",
            ]

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
            f"- **Coverage Scope**: Main project domains only ({', '.join(f'`{d}`' for d in configured_domains)}); `development_tools/` coverage is tracked separately."
        )
        summary_lines.append(
            "- **Goal**: Expand to **80%+ coverage** for comprehensive reliability\n"
        )

        # Domain-level summary (based on module path prefixes).
        domain_bucket: dict[str, dict[str, int]] = {
            d: {"statements": 0, "covered": 0} for d in configured_domains
        }
        for module_name, module_data in coverage_data.items():
            normalized = str(module_name).replace("\\", "/")
            domain = normalized.split("/", 1)[0]
            if domain in domain_bucket:
                statements = int(module_data.get("statements", 0))
                covered = int(module_data.get("covered", 0))
                domain_bucket[domain]["statements"] += statements
                domain_bucket[domain]["covered"] += covered

        summary_lines.append("### **Coverage by Domain**")
        for domain in configured_domains:
            statements = domain_bucket[domain]["statements"]
            covered = domain_bucket[domain]["covered"]
            coverage_pct = (covered / statements * 100.0) if statements else 0.0
            missing = max(0, statements - covered)
            summary_lines.append(
                f"- **{domain}**: {coverage_pct:.1f}% ({covered}/{statements} lines, {missing} missing)"
            )
        summary_lines.append("")

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

    def _extract_marker_name(self, decorator: ast.AST) -> str | None:
        """Extract pytest marker name from decorator node when possible."""
        target = decorator
        if isinstance(target, ast.Call):
            target = target.func

        if not isinstance(target, ast.Attribute):
            return None

        # Match patterns like:
        # - pytest.mark.unit
        # - mark.unit
        # - pytest.mark.parametrize
        marker_name = target.attr
        value = target.value
        if isinstance(value, ast.Attribute) and value.attr == "mark":
            return marker_name
        if isinstance(value, ast.Name) and value.id == "mark":
            return marker_name
        return None

    def _collect_test_marker_counts(self) -> tuple[Counter, int]:
        """Count marker usage across discovered test functions/methods."""
        marker_counter: Counter = Counter()
        total_test_nodes = 0
        tests_root = self.project_root / "tests"
        if not tests_root.exists():
            return marker_counter, total_test_nodes

        for test_file in tests_root.rglob("test_*.py"):
            rel_path = str(test_file.relative_to(self.project_root)).replace("\\", "/")
            if should_exclude_file(rel_path, tool_type="coverage", context="development"):
                continue
            try:
                source = test_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    total_test_nodes += 1
                    markers = {
                        self._extract_marker_name(dec)
                        for dec in node.decorator_list
                    }
                    for marker in markers:
                        if marker:
                            marker_counter[marker] += 1
                elif isinstance(node, ast.ClassDef):
                    class_markers = {
                        self._extract_marker_name(dec)
                        for dec in node.decorator_list
                    }
                    class_markers = {m for m in class_markers if m}
                    for member in node.body:
                        if isinstance(member, ast.FunctionDef) and member.name.startswith(
                            "test_"
                        ):
                            total_test_nodes += 1
                            member_markers = {
                                self._extract_marker_name(dec)
                                for dec in member.decorator_list
                            }
                            combined = {m for m in member_markers if m} | class_markers
                            for marker in combined:
                                marker_counter[marker] += 1

        return marker_counter, total_test_nodes

    def generate_test_markers_section(self) -> str:
        """Generate the Test Markers section with current marker usage counts."""
        marker_counts, total_tests = self._collect_test_marker_counts()
        lines = [
            "## Test Markers",
            "",
            "**Note**: Marker counts are generated from test decorators in `tests/test_*.py` files.",
            "",
            f"- **Total discovered test nodes**: {total_tests}",
        ]

        if not marker_counts:
            lines.append("- **Marker usage**: No markers detected.")
            return "\n".join(lines) + "\n"

        lines.append("- **Marker usage counts**:")
        for marker, count in sorted(
            marker_counts.items(), key=lambda item: (-item[1], item[0])
        ):
            lines.append(f"  - `{marker}`: {count}")
        lines.append("")
        return "\n".join(lines)

    def update_coverage_plan(self, coverage_summary: str) -> bool:
        """Update the TEST_COVERAGE_REPORT.md with new metrics."""
        generated_timestamp = now_timestamp_full()
        test_markers_section = self.generate_test_markers_section()

        # Standard generated header
        standard_header = f"""# Test Coverage Report

> **File**: `development_docs/TEST_COVERAGE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: {generated_timestamp}
> **Source**: `python development_tools/tests/generate_test_coverage_report.py` - Test Coverage Report Generator

"""
        source_line = (
            "> **Source**: `python development_tools/tests/generate_test_coverage_report.py` "
            "- Test Coverage Report Generator"
        )

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
            with open(self.coverage_plan_file, encoding="utf-8") as f:
                content = f.read()

            # Check if file has standard generated header
            has_standard_header = (
                "> **File**: `development_docs/TEST_COVERAGE_REPORT.md`" in content
                and "> **Generated**: This file is auto-generated" in content
                and "> **Source**:" in content
            )

            # Find and replace the current status section
            section_header = "## Current Status"
            current_status_pattern = r"(## Current Status.*?)(?=\n## |\Z)"
            test_markers_pattern = r"(## Test Markers.*?)(?=\n## |\Z)"

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

                # Replace or append Test Markers section with generated content.
                if re.search(test_markers_pattern, updated_content, re.DOTALL):
                    updated_content = re.sub(
                        test_markers_pattern,
                        lambda _: test_markers_section + "\n",
                        updated_content,
                        flags=re.DOTALL,
                    )
                else:
                    updated_content = updated_content.rstrip() + "\n\n" + test_markers_section + "\n"

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

                # Normalize source command text in-place for older generated files.
                source_line_pattern = r"^> \*\*Source\*\*:.*$"
                if re.search(source_line_pattern, updated_content, re.MULTILINE):
                    updated_content = re.sub(
                        source_line_pattern,
                        source_line,
                        updated_content,
                        count=1,
                        flags=re.MULTILINE,
                    )
                else:
                    last_generated_pattern = r"(> \*\*Last Generated\*\*:.*\n)"
                    if re.search(last_generated_pattern, updated_content, re.MULTILINE):
                        updated_content = re.sub(
                            last_generated_pattern,
                            lambda match: f"{match.group(1)}{source_line}\n",
                            updated_content,
                            count=1,
                            flags=re.MULTILINE,
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

                # Ensure Test Markers section exists and is refreshed.
                if re.search(test_markers_pattern, updated_content, re.DOTALL):
                    updated_content = re.sub(
                        test_markers_pattern,
                        lambda _: test_markers_section + "\n",
                        updated_content,
                        flags=re.DOTALL,
                    )
                else:
                    updated_content = updated_content.rstrip() + "\n\n" + test_markers_section + "\n"

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
        # Set up coverage command and environment (absolute paths so subprocess finds data/config)
        coverage_cmd = [sys.executable, "-m", "coverage"]
        env = os.environ.copy()
        env["COVERAGE_FILE"] = str(Path(self.coverage_data_file).resolve())
        env["COVERAGE_DATA_DIR"] = str(Path(self.coverage_data_file).resolve().parent)
        if self.coverage_config_path.exists():
            env["COVERAGE_RCFILE"] = str(Path(self.coverage_config_path).resolve())

        # Combine coverage data files if they exist (check both project root and coverage dir)
        coverage_data_files = list(self.project_root.glob(".coverage.*"))
        if not coverage_data_files:
            cov_dir = Path(self.coverage_data_file).resolve().parent
            if cov_dir != self.project_root:
                coverage_data_files = list(cov_dir.glob(".coverage.*"))

        if coverage_data_files:
            if logger:
                logger.info(
                    f"Combining {len(coverage_data_files)} coverage data files..."
                )

            # Use coverage combine command; run from dir containing shards so it finds .coverage.*
            combine_cmd = coverage_cmd + ["combine"]
            combine_cwd = (
                coverage_data_files[0].parent
                if coverage_data_files
                else self.project_root
            )

            combine_result = subprocess.run(
                combine_cmd,
                capture_output=True,
                text=True,
                cwd=combine_cwd,
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

        # Generate HTML report (--data-file so coverage finds the file regardless of cwd/rc)
        data_file_abs = str(Path(self.coverage_data_file).resolve())
        if logger:
            logger.info("Generating HTML coverage report...")

        # Ensure HTML output directory exists
        self.coverage_html_dir.mkdir(parents=True, exist_ok=True)

        html_args = coverage_cmd + [
            "html",
            "-d",
            str(self.coverage_html_dir),
            "--data-file",
            data_file_abs,
        ]
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
            err = (html_result.stderr or "").strip()
            out = (html_result.stdout or "").strip()
            logger.warning(
                f"coverage html exited with {html_result.returncode}: {err or out or '(no output)'}"
            )
            if not Path(data_file_abs).exists():
                logger.warning(
                    f"Coverage data file does not exist: {data_file_abs}. "
                    "Run test coverage combine step first (e.g. run_test_coverage)."
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

        # Generate JSON report (--data-file so coverage finds the file)
        json_args = coverage_cmd + [
            "json",
            "-o",
            str(coverage_output),
            "--data-file",
            data_file_abs,
        ]
        json_result = subprocess.run(
            json_args, capture_output=True, text=True, cwd=self.project_root, env=env
        )

        if json_result.returncode == 0:
            if logger:
                logger.info(f"Coverage JSON report generated: {coverage_output}")
        else:
            if logger:
                err = (json_result.stderr or "").strip()
                out = (json_result.stdout or "").strip()
                logger.warning(
                    f"coverage json exited with {json_result.returncode}: {err or out or '(no output)'}"
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
        with open(coverage_json_path, encoding="utf-8") as f:
            json.load(f)
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

    # Always refresh TEST_COVERAGE_REPORT.md from current coverage data.
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
