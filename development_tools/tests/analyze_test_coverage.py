#!/usr/bin/env python3
# TOOL_TIER: core

"""
Test Coverage Analysis Tool

Analyzes test coverage data from pytest/coverage output. This tool provides
pure analysis of existing coverage data - it does NOT run tests or generate
coverage data.

NOTE: This tool ANALYZES existing coverage data. To run tests and generate
coverage data, use generate_test_coverage.py (which orchestrates pytest execution).

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

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

# Import caching utilities
try:
    from development_tools.shared.mtime_cache import MtimeFileCache
except ImportError:
    # Fallback for when run as script
    try:
        from ..shared.mtime_cache import MtimeFileCache
    except ImportError:
        MtimeFileCache = None

# Load external config on module import (safe to call multiple times)
config.load_external_config()

logger = get_component_logger("development_tools")


class TestCoverageAnalyzer:
    """Analyzes test coverage data from pytest/coverage output."""

    def __init__(self, project_root: str = ".", use_cache: bool = True):
        """
        Initialize coverage analyzer.

        Args:
            project_root: Root directory of the project
            use_cache: Whether to use caching for analysis results (default: True)
        """
        self.project_root = Path(project_root).resolve()
        self.use_cache = use_cache

        # Initialize cache for analysis results
        if MtimeFileCache and self.use_cache:
            self.cache = MtimeFileCache(
                project_root=self.project_root,
                use_cache=True,
                tool_name="analyze_test_coverage",
                domain="tests",
            )
        else:
            self.cache = None

    def parse_coverage_output(self, output: str) -> Dict[str, Dict[str, any]]:
        """Parse the coverage output to extract module-specific metrics."""
        coverage_data = {}

        # Split output into sections
        sections = output.split("Name")
        if len(sections) < 2:
            return coverage_data

        coverage_section = sections[1]
        lines = coverage_section.strip().split("\n")

        for line in lines:
            if "---" in line or not line.strip():
                continue

            # Parse coverage line
            parts = line.split()
            if len(parts) >= 4:
                try:
                    module_name = parts[0]
                    statements = int(parts[1])
                    missed = int(parts[2])
                    coverage = int(parts[3].rstrip("%"))

                    # Extract missing line numbers if available
                    missing_lines = []
                    if len(parts) > 4:
                        missing_part = " ".join(parts[4:])
                        missing_lines = self.extract_missing_lines(missing_part)

                    coverage_data[module_name] = {
                        "statements": statements,
                        "missed": missed,
                        "coverage": coverage,
                        "missing_lines": missing_lines,
                        "covered": statements - missed,
                    }

                except (ValueError, IndexError):
                    continue

        return coverage_data

    def load_coverage_json(self, json_path: Path) -> Dict[str, Dict[str, any]]:
        """Fallback parser that reads module metrics from coverage JSON output."""
        try:
            with open(json_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            if logger:
                logger.warning(f"Unable to load coverage JSON data: {exc}")
            return {}

        files = data.get("files", {})
        coverage_data: Dict[str, Dict[str, any]] = {}

        for module_name, file_data in files.items():
            # Normalize path to use backslashes (Windows format) to match plan file format
            # Coverage JSON uses backslashes on Windows, but ensure consistency
            normalized_name = module_name.replace("/", "\\")

            summary = file_data.get("summary", {})
            statements = int(summary.get("num_statements", 0))
            covered = int(
                summary.get(
                    "covered_lines", statements - summary.get("missing_lines", 0)
                )
            )
            missed = int(summary.get("missing_lines", statements - covered))
            percent = summary.get("percent_covered")
            if isinstance(percent, float):
                percent_value = int(round(percent))
            else:
                try:
                    percent_value = int(percent)
                except (TypeError, ValueError):
                    percent_value = 0

            missing_lines = file_data.get("missing_lines", [])
            missing_line_strings = [str(line) for line in missing_lines]

            coverage_data[normalized_name] = {
                "statements": statements,
                "missed": missed,
                "coverage": percent_value,
                "missing_lines": missing_line_strings,
                "covered": covered,
            }

        return coverage_data

    def extract_missing_lines(self, missing_part: str) -> List[str]:
        """Extract missing line numbers from coverage output."""
        missing_lines = []

        # Look for patterns like "1-5, 10, 15-20"
        line_patterns = [
            r"(\d+)-(\d+)",  # Range like "1-5"
            r"(\d+)",  # Single line like "10"
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
            "total_statements": 0,
            "total_missed": 0,
            "overall_coverage": 0.0,
        }

        # Look for TOTAL line
        total_pattern = r"TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%"
        match = re.search(total_pattern, output)

        if match:
            total_statements = int(match.group(1))
            total_missed = int(match.group(2))
            overall_data["total_statements"] = total_statements
            overall_data["total_missed"] = total_missed
            # Calculate coverage with 1 decimal place for accuracy
            if total_statements > 0:
                overall_data["overall_coverage"] = round(
                    (total_statements - total_missed) / total_statements * 100, 1
                )
            else:
                overall_data["overall_coverage"] = 0.0

        return overall_data

    def extract_overall_from_json(self, json_path: Path) -> Dict[str, any]:
        """Compute overall coverage using the JSON report."""
        try:
            with open(json_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_statements": 0, "total_missed": 0, "overall_coverage": 0.0}

        files = data.get("files", {})
        total_statements = 0
        total_missed = 0

        for file_data in files.values():
            summary = file_data.get("summary", {})
            total_statements += int(summary.get("num_statements", 0))
            total_missed += int(summary.get("missing_lines", 0))

        if total_statements:
            percent = round(
                (total_statements - total_missed) / total_statements * 100, 1
            )
        else:
            percent = 0.0

        return {
            "total_statements": total_statements,
            "total_missed": total_missed,
            "overall_coverage": percent,
        }

    def categorize_modules(
        self, coverage_data: Dict[str, Dict[str, any]]
    ) -> Dict[str, List[str]]:
        """Categorize modules by coverage level."""
        categories = {
            "excellent": [],  # 80%+
            "good": [],  # 60-79%
            "moderate": [],  # 40-59%
            "needs_work": [],  # 20-39%
            "critical": [],  # <20%
        }

        for module_name, data in coverage_data.items():
            coverage = data["coverage"]

            if coverage >= 80:
                categories["excellent"].append(module_name)
            elif coverage >= 60:
                categories["good"].append(module_name)
            elif coverage >= 40:
                categories["moderate"].append(module_name)
            elif coverage >= 20:
                categories["needs_work"].append(module_name)
            else:
                categories["critical"].append(module_name)

        return categories

    def analyze_coverage(
        self,
        coverage_output: Optional[str] = None,
        coverage_json_path: Optional[Path] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze coverage data from either text output or JSON file.

        Args:
            coverage_output: Optional text output from pytest coverage
            coverage_json_path: Optional path to coverage.json file
            use_cache: Whether to use caching for analysis results (default: True)

        Returns:
            Dictionary with 'modules' and 'overall' keys containing analysis results
        """
        # Determine the coverage JSON file path for caching
        json_file_for_cache = None
        if coverage_json_path and coverage_json_path.exists():
            json_file_for_cache = coverage_json_path
        elif not coverage_output:
            # Try to find coverage.json in default location
            default_json = (
                self.project_root
                / "development_tools"
                / "tests"
                / "jsons"
                / "coverage.json"
            )
            if not default_json.exists():
                default_json = self.project_root / "coverage.json"
            if default_json.exists():
                json_file_for_cache = default_json

        # Try to use cache if we have a JSON file and caching is enabled
        if (
            use_cache
            and json_file_for_cache
            and json_file_for_cache.exists()
            and self.cache
        ):
            # Check if we have cached results for this coverage JSON file
            cached_results = self.cache.get_cached(json_file_for_cache)
            if cached_results is not None:
                if logger:
                    logger.debug(
                        f"Using cached analysis results for {json_file_for_cache.relative_to(self.project_root)}"
                    )
                return cached_results

        # Analyze coverage data (cache miss or caching disabled)
        coverage_data = {}
        overall_data = {}

        if coverage_json_path and coverage_json_path.exists():
            # Use JSON file (preferred)
            coverage_data = self.load_coverage_json(coverage_json_path)
            overall_data = self.extract_overall_from_json(coverage_json_path)
        elif coverage_output:
            # Parse text output
            coverage_data = self.parse_coverage_output(coverage_output)
            overall_data = self.extract_overall_coverage(coverage_output)
        else:
            # Try to find coverage.json in project root
            default_json = self.project_root / "coverage.json"
            if default_json.exists():
                coverage_data = self.load_coverage_json(default_json)
                overall_data = self.extract_overall_from_json(default_json)

        # Categorize modules
        categories = self.categorize_modules(coverage_data)

        results = {
            "modules": coverage_data,
            "overall": overall_data,
            "categories": categories,
        }

        # Cache results if we have a JSON file and caching is enabled
        if (
            use_cache
            and json_file_for_cache
            and json_file_for_cache.exists()
            and self.cache
        ):
            self.cache.cache_results(json_file_for_cache, results)
            self.cache.save_cache()
            if logger:
                logger.debug(
                    f"Cached analysis results for {json_file_for_cache.relative_to(self.project_root)}"
                )

        return results


def main():
    """Main entry point for coverage analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze test coverage data")
    parser.add_argument("--input", type=str, help="Input coverage output text file")
    parser.add_argument("--json", type=str, help="Input coverage.json file path")
    parser.add_argument("--output", type=str, help="Output JSON file path")

    args = parser.parse_args()

    analyzer = TestCoverageAnalyzer()

    # Read input
    coverage_output = None
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            coverage_output = f.read()

    coverage_json_path = None
    if args.json:
        coverage_json_path = Path(args.json)
    elif not args.input:
        # Try default location
        default_json = analyzer.project_root / "coverage.json"
        if default_json.exists():
            coverage_json_path = default_json

    # Analyze
    results = analyzer.analyze_coverage(coverage_output, coverage_json_path)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Coverage analysis written to {args.output}")
    else:
        print(json.dumps(results, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
