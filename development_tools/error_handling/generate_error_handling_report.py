#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
generate_error_handling_report.py
Generates reports from error handling analysis results.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

# Handle both relative and absolute imports
try:
    from .. import config
except ImportError:
    from development_tools import config

# Ensure external config is loaded
config.load_external_config()

logger = get_component_logger("development_tools")


class ErrorHandlingReportGenerator:
    """Generates reports from error handling analysis results."""

    def __init__(self, analysis_results: Dict[str, Any]):
        """Initialize with analysis results."""
        self.results = analysis_results

    def print_summary(self):
        """Print a summary of error handling analysis."""
        logger.info("=" * 80)
        logger.info("ERROR HANDLING COVERAGE ANALYSIS")
        logger.info("=" * 80)

        logger.info(f"Total Functions: {self.results['total_functions']}")
        logger.info(
            f"Functions with Try-Except: {self.results['functions_with_try_except']}"
        )
        logger.info(
            f"Functions with Error Handling: {self.results['functions_with_error_handling']}"
        )
        logger.info(
            f"Functions with Decorators: {self.results['functions_with_decorators']}"
        )
        logger.info(
            f"Functions Missing Error Handling: {self.results['functions_missing_error_handling']}"
        )
        logger.info(
            f"Error Handling Coverage: {self.results['analyze_error_handling']:.1f}%"
        )

        logger.info("Error Handling Quality Distribution:")
        for quality, count in self.results["error_handling_quality"].items():
            logger.info(f"  {quality.title()}: {count}")

        logger.info("Error Patterns Found:")
        for pattern, count in self.results["error_patterns"].items():
            logger.info(f"  {pattern}: {count}")

        # Phase 1: Candidates for decorator replacement
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 1: CANDIDATES FOR DECORATOR REPLACEMENT")
        logger.info("=" * 80)
        logger.info(f"Total Phase 1 Candidates: {self.results['phase1_total']}")
        logger.info("By Priority:")
        for priority, count in self.results["phase1_by_priority"].items():
            logger.info(f"  {priority.title()}: {count}")

        if self.results["phase1_candidates"]:
            logger.info("High-Priority Candidates (first 10):")
            high_priority = [
                c for c in self.results["phase1_candidates"] if c["priority"] == "high"
            ]
            for candidate in high_priority[:10]:
                logger.info(
                    f"  {candidate['file_path']}:{candidate['function_name']} (line {candidate['line_start']}) - {candidate['operation_type']}"
                )
            if len(high_priority) > 10:
                logger.info(
                    f"  ... and {len(high_priority) - 10} more high-priority candidates"
                )

        # Phase 2: Generic exception raises
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 2: GENERIC EXCEPTION RAISES")
        logger.info("=" * 80)
        logger.info(f"Total Generic Exception Raises: {self.results['phase2_total']}")
        logger.info("By Exception Type:")
        for exc_type, count in self.results["phase2_by_type"].items():
            logger.info(f"  {exc_type}: {count}")

        if self.results["phase2_exceptions"]:
            logger.info("Generic Exception Raises (first 10):")
            for exc in self.results["phase2_exceptions"][:10]:
                logger.info(
                    f"  {exc['file_path']}:{exc['line_number']} - {exc['exception_type']} → {exc['suggested_replacement']}"
                )
                if exc["function_name"]:
                    logger.info(
                        f"    Function: {exc['function_name']} (line {exc['function_line']})"
                    )
            if len(self.results["phase2_exceptions"]) > 10:
                logger.info(
                    f"  ... and {len(self.results['phase2_exceptions']) - 10} more"
                )

        if self.results["missing_error_handling"]:
            logger.warning(
                f"Functions Missing Error Handling ({len(self.results['missing_error_handling'])}):"
            )
            for func in self.results["missing_error_handling"][:10]:  # Show first 10
                logger.warning(
                    f"  {func['file']}:{func['function']} (line {func['line']})"
                )
            if len(self.results["missing_error_handling"]) > 10:
                logger.warning(
                    f"  ... and {len(self.results['missing_error_handling']) - 10} more"
                )

        if self.results.get("recommendations"):
            logger.info("Recommendations:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                logger.info(f"  {i}. {rec}")

    def save_json_report(self, output_path: Path) -> None:
        """Save analysis results as JSON report with standardized metadata."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_iso = datetime.now().isoformat()
        report_data = {
            "generated_by": "generate_error_handling_report.py - Error Handling Report Generator",
            "last_generated": timestamp_str,
            "source": "python development_tools/error_handling/generate_error_handling_report.py",
            "note": "This file is auto-generated. Do not edit manually.",
            "timestamp": timestamp_iso,
            "error_handling_results": self.results,
        }

        # Use rotation system for archiving
        from development_tools.shared.file_rotation import FileRotator

        # Rotate existing file if it exists
        if output_path.exists():
            rotator = FileRotator(base_dir=str(output_path.parent))
            rotator.rotate_file(str(output_path), max_versions=5)

        # Write new file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Error handling coverage report written to {output_path}")


def main():
    """Main function for error handling report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate error handling reports from analysis results"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Input JSON file with analysis results"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: development_tools/error_handling/jsons/error_handling_details.json)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary", "both"],
        default="both",
        help="Output format",
    )

    args = parser.parse_args()

    # Load analysis results
    with open(args.input, "r", encoding="utf-8") as f:
        analysis_results = json.load(f)

    # Create report generator
    generator = ErrorHandlingReportGenerator(analysis_results)

    # Generate reports
    if args.format in ("json", "both"):
        if args.output:
            output_path = Path(args.output)
        else:
            # Default to development_tools/error_handling directory
            project_root = Path(args.input).parent.parent.parent
            tools_dir = project_root / "development_tools" / "error_handling"
            tools_dir.mkdir(exist_ok=True)
            output_path = tools_dir / "jsons" / "error_handling_details.json"

        generator.save_json_report(output_path)

    if args.format in ("summary", "both"):
        generator.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
