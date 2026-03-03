#!/usr/bin/env python3
"""
Measure execution times for all development tools individually.

This script runs each tool in isolation and measures its execution time,
providing data for optimizing tier assignments and identifying performance bottlenecks.

Usage:
    python development_tools/shared/measure_tool_timings.py
    python development_tools/shared/measure_tool_timings.py --output development_tools/TIMING_ANALYSIS.md
"""

import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from development_tools.shared.service import AIToolsService
from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def measure_tool_execution(
    service: AIToolsService, tool_name: str, tool_func
) -> tuple[bool, float, str]:
    """Measure execution time for a single tool."""
    try:
        start_time = time.time()
        result = tool_func()
        elapsed_time = time.time() - start_time

        if isinstance(result, dict):
            success = result.get("success", False)
            error = result.get("error", "")
        else:
            success = bool(result)
            error = ""

        return success, elapsed_time, error
    except Exception as e:
        elapsed_time = time.time() - start_time if "start_time" in locals() else 0.0
        return False, elapsed_time, str(e)


def run_timing_analysis(output_file: Path | None = None) -> dict:
    """Run timing analysis for all tools."""
    if output_file is None:
        output_file = project_root / "development_tools" / "TIMING_ANALYSIS.md"

    service = AIToolsService()

    # Define all tools by tier
    tier1_tools = [
        ("analyze_functions", service.run_analyze_functions),
        ("analyze_documentation_sync", service.run_analyze_documentation_sync),
        ("system_signals", service.run_analyze_system_signals),
        ("quick_status", lambda: service.run_script("quick_status", "json")),
    ]

    tier2_tools = [
        (
            "analyze_documentation",
            lambda: service.run_analyze_documentation(include_overlap=False),
        ),
        ("analyze_error_handling", service.run_analyze_error_handling),
        ("decision_support", service.run_decision_support),
        ("analyze_config", lambda: service.run_script("analyze_config")),
        ("analyze_ai_work", service.run_validate),
        ("analyze_function_registry", service.run_analyze_function_registry),
        ("analyze_module_dependencies", service.run_analyze_module_dependencies),
        ("analyze_module_imports", service.run_analyze_module_imports),
        ("analyze_dependency_patterns", service.run_analyze_dependency_patterns),
        ("analyze_function_patterns", service.run_analyze_function_patterns),
        ("analyze_package_exports", service.run_analyze_package_exports),
    ]

    # Tier 3 tools grouped by dependencies
    # Coverage group: must stay together (dependencies)
    tier3_coverage_group = [
        ("generate_test_coverage", service.run_coverage_regeneration),
        ("generate_dev_tools_coverage", service.run_dev_tools_coverage),
        ("analyze_test_markers", lambda: service.run_test_markers("check")),
        ("generate_test_coverage_report", service.run_generate_test_coverage_report),
    ]
    # Legacy group: must stay together (analyze then generate report)
    tier3_legacy_group = [
        ("analyze_legacy_references", service.run_analyze_legacy_references),
        (
            "generate_legacy_reference_report",
            service.run_generate_legacy_reference_report,
        ),
    ]
    # Unused imports group: must stay together (analyze then generate report)
    tier3_unused_imports_group = [
        ("analyze_unused_imports", service.run_analyze_unused_imports),
        ("generate_unused_imports_report", service.run_generate_unused_imports_report),
    ]

    tier3_tools = tier3_coverage_group + tier3_legacy_group + tier3_unused_imports_group

    all_tools = [
        ("Tier 1 (Quick Audit)", tier1_tools),
        ("Tier 2 (Standard Audit)", tier2_tools),
        ("Tier 3 (Full Audit)", tier3_tools),
    ]

    results = {
        "tier1": {},
        "tier2": {},
        "tier3": {},
        "summary": {
            "total_tools": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
        },
    }

    logger.info("=" * 70)
    logger.info("Tool Timing Analysis")
    logger.info("=" * 70)

    for tier_name, tools in all_tools:
        tier_key = tier_name.split()[1].lower()  # '1', '2', or '3'
        logger.info(f"\n{tier_name}:")
        logger.info("-" * 70)

        for tool_name, tool_func in tools:
            logger.info(f"  Measuring {tool_name}...", end=" ", flush=True)
            success, elapsed_time, error = measure_tool_execution(
                service, tool_name, tool_func
            )

            results[f"tier{tier_key}"][tool_name] = {
                "success": success,
                "time": elapsed_time,
                "error": error,
            }

            results["summary"]["total_tools"] += 1
            if success:
                results["summary"]["successful"] += 1
            else:
                results["summary"]["failed"] += 1
            results["summary"]["total_time"] += elapsed_time

            status = "✓" if success else "✗"
            logger.info(f"{status} {elapsed_time:.2f}s")
            if error and not success:
                logger.info(f"      Error: {error[:100]}")

    # Generate markdown report
    generate_timing_report(results, output_file)

    logger.info("\n" + "=" * 70)
    logger.info("Timing analysis complete!")
    logger.info(f"  Total tools: {results['summary']['total_tools']}")
    logger.info(f"  Successful: {results['summary']['successful']}")
    logger.info(f"  Failed: {results['summary']['failed']}")
    logger.info(f"  Total time: {results['summary']['total_time']:.2f}s")
    logger.info(f"  Report saved to: {output_file}")
    logger.info("=" * 70)

    return results


def generate_timing_report(results: dict, output_file: Path) -> None:
    """Generate markdown timing analysis report."""
    from datetime import datetime

    lines = [
        "# Tool Execution Timing Analysis",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Source**: `development_tools/shared/measure_tool_timings.py`",
        "",
        "## Summary",
        "",
        f"- **Total Tools Measured**: {results['summary']['total_tools']}",
        f"- **Successful**: {results['summary']['successful']}",
        f"- **Failed**: {results['summary']['failed']}",
        f"- **Total Execution Time**: {results['summary']['total_time']:.2f}s",
        "",
        "## Tier 1: Quick Audit Tools (<30 seconds target)",
        "",
        "| Tool | Time (s) | Status | Recommendation |",
        "|------|----------|--------|----------------|",
    ]

    tier1_sorted = sorted(
        results["tier1"].items(), key=lambda x: x[1]["time"], reverse=True
    )
    for tool_name, data in tier1_sorted:
        time_val = data["time"]
        status = "✓" if data["success"] else "✗"
        if time_val < 30:
            rec = "Keep in Tier 1"
        elif time_val < 60:
            rec = "Consider Tier 2"
        else:
            rec = "Move to Tier 2"
        lines.append(f"| {tool_name} | {time_val:.2f} | {status} | {rec} |")

    lines.extend(
        [
            "",
            "## Tier 2: Standard Audit Tools (30 seconds - 2 minutes target)",
            "",
            "| Tool | Time (s) | Status | Recommendation |",
            "|------|----------|--------|----------------|",
        ]
    )

    tier2_sorted = sorted(
        results["tier2"].items(), key=lambda x: x[1]["time"], reverse=True
    )
    for tool_name, data in tier2_sorted:
        time_val = data["time"]
        status = "✓" if data["success"] else "✗"
        if time_val < 30:
            rec = "Consider Tier 1"
        elif time_val < 120:
            rec = "Keep in Tier 2"
        else:
            rec = "Consider Tier 3"
        lines.append(f"| {tool_name} | {time_val:.2f} | {status} | {rec} |")

    lines.extend(
        [
            "",
            "## Tier 3: Full Audit Tools (>2 minutes acceptable)",
            "",
            "| Tool | Time (s) | Status | Recommendation |",
            "|------|----------|--------|----------------|",
        ]
    )

    tier3_sorted = sorted(
        results["tier3"].items(), key=lambda x: x[1]["time"], reverse=True
    )
    for tool_name, data in tier3_sorted:
        time_val = data["time"]
        status = "✓" if data["success"] else "✗"
        if time_val < 120:
            rec = "Consider Tier 2"
        else:
            rec = "Keep in Tier 3"
        lines.append(f"| {tool_name} | {time_val:.2f} | {status} | {rec} |")

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "Based on timing data:",
            "",
            "### Tool Dependencies (Must Stay Together):",
            "",
            "**Coverage Tools** (must stay in same tier):",
            "- `generate_test_coverage`, `generate_dev_tools_coverage`, `analyze_test_markers`, `generate_test_coverage_reports`",
            "- These tools depend on each other and should remain in Tier 3",
            "",
            "**Legacy Tools** (must stay in same tier):",
            "- `analyze_legacy_references`, `generate_legacy_reference_report`",
            "- Report generation depends on analysis results",
            "",
            "**Unused Imports Tools** (must stay in same tier):",
            "- `analyze_unused_imports`, `generate_unused_imports_report`",
            "- Report generation depends on analysis results",
            "",
            "**Module Imports Group** (must run in order):",
            "- `analyze_module_imports` → `analyze_dependency_patterns`, `analyze_module_dependencies`",
            "- `analyze_dependency_patterns` and `analyze_module_dependencies` use `analyze_module_imports` results",
            "",
            "**Function Discovery Group** (must run in order):",
            "- `analyze_functions` (Tier 1) → `decision_support`, `analyze_function_patterns`",
            "- `decision_support` and `analyze_function_patterns` use `analyze_functions` results",
            "",
            "**Function Registry Group** (must stay together):",
            "- `generate_function_registry` (runs in docs command) → `analyze_function_registry`",
            "- `analyze_function_registry` validates `generate_function_registry` output",
            "",
            "**Documentation Sync Group** (already grouped):",
            "- `analyze_documentation_sync` includes multiple sub-tools that run together",
            "- Sub-tools: `analyze_path_drift`, `analyze_ascii_compliance`, `analyze_heading_numbering`, `analyze_missing_addresses`, `analyze_unconverted_links`",
            "",
            "### Tools to Consider Moving (respecting dependencies):",
        ]
    )

    # Find tools that might need tier adjustment
    moves = []
    for tool_name, data in results["tier1"].items():
        if data["time"] > 30:
            moves.append(
                f"- **{tool_name}** (Tier 1 → Tier 2): {data['time']:.2f}s exceeds 30s target"
            )

    for tool_name, data in results["tier2"].items():
        if data["time"] < 30:
            moves.append(
                f"- **{tool_name}** (Tier 2 → Tier 1): {data['time']:.2f}s could be in quick audit"
            )
        elif data["time"] > 120:
            moves.append(
                f"- **{tool_name}** (Tier 2 → Tier 3): {data['time']:.2f}s exceeds 2min target"
            )

    for tool_name, data in results["tier3"].items():
        if data["time"] < 120:
            moves.append(
                f"- **{tool_name}** (Tier 3 → Tier 2): {data['time']:.2f}s could be in standard audit"
            )

    if moves:
        lines.extend(moves)
    else:
        lines.append("- No tier adjustments recommended based on current timing data")

    lines.extend(
        [
            "",
            "### Performance Optimization Opportunities:",
            "",
            "- Tools taking >60 seconds should be reviewed for optimization opportunities",
            "- Consider adding caching to frequently-run tools",
            "- Tools that scan files could benefit from mtime-based caching",
            "",
            "---",
            "",
            "**Note**: These timings are from individual tool execution. Actual audit times may vary due to:",
            "- Caching effects (subsequent runs may be faster)",
            "- System load",
            "- File system performance",
            "- Parallel execution opportunities",
        ]
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also save JSON data
    json_file = output_file.with_suffix(".json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Measure execution times for all development tools"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: development_tools/TIMING_ANALYSIS.md)",
    )

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    run_timing_analysis(output_path)
