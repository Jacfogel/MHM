#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Lightweight structural validator for AI-generated work.
Helps verify basic completeness and consistency before presenting to user.

Note: This tool performs lightweight structural validation only. For comprehensive
analysis, use the domain-specific tools:
- Documentation: docs/analyze_documentation_sync.py
- Error handling: error_handling/analyze_error_handling.py
- Test coverage: tests/analyze_test_coverage.py
- Changelog sync: docs/fix_version_sync.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# YAML support removed - not needed for lightweight structural validation

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
try:
    from . import config
except ImportError:
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Load config at module level
VALIDATE_AI_WORK_CONFIG = config.get_analyze_ai_work_config()


def validate_documentation_completeness(doc_file: str, code_files: List[str]) -> Dict:
    """Validate that documentation covers all relevant code."""
    results = {
        "file_exists": False,
        "coverage": 100.0,  # Default to 100% for high-level docs like README.md
        "missing_items": [],
        "extra_items": [],
        "warnings": [],
    }

    # Check if documentation file exists
    doc_path = Path(doc_file)
    results["file_exists"] = doc_path.exists()

    if not results["file_exists"]:
        results["warnings"].append(f"Documentation file {doc_file} does not exist")
        return results

    # Read documentation content
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_content = f.read()
    except Exception as e:
        results["warnings"].append(f"Error reading {doc_file}: {e}")
        return results

    # Extract mentioned items from documentation
    mentioned_items = set()

    # Look for function/class names in backticks
    function_matches = re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*)`", doc_content)
    mentioned_items.update(function_matches)

    # Look for file paths
    file_matches = re.findall(r"`([^`]+\.py)`", doc_content)
    mentioned_items.update(file_matches)

    # Extract actual items from code files
    actual_items = set()
    for code_file in code_files:
        code_path = Path(code_file)
        if code_path.exists():
            try:
                with open(code_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                # Extract function names
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        actual_items.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        actual_items.add(node.name)

                # Add file name
                actual_items.add(code_path.name)

            except Exception as e:
                results["warnings"].append(f"Error parsing {code_file}: {e}")

    # Calculate coverage - for README.md, we don't expect it to mention every function
    if doc_file.endswith("README.md"):
        # README.md is a high-level overview, not comprehensive API docs
        results["coverage"] = 100.0
        results["missing_items"] = []
        results["extra_items"] = []
        results["warnings"].append(
            "README.md validation: High-level docs don't need to mention every function"
        )
    elif actual_items:
        covered_items = mentioned_items.intersection(actual_items)
        results["coverage"] = len(covered_items) / len(actual_items) * 100
        results["missing_items"] = list(actual_items - mentioned_items)
        results["extra_items"] = list(mentioned_items - actual_items)

    return results


def validate_code_consistency(changed_files: List[str]) -> Dict:
    """Validate that code changes are consistent across files."""
    results = {
        "import_consistency": True,
        "naming_consistency": True,
        "function_signatures": [],
        "warnings": [],
    }

    # Check for consistent imports
    import_patterns = {}
    for file_path in changed_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")

            import_patterns[file_path] = imports

            # Extract function signatures
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    results["function_signatures"].append(
                        {"file": file_path, "name": node.name, "args": args}
                    )

        except Exception as e:
            results["warnings"].append(f"Error parsing {file_path}: {e}")

    # Check for naming consistency
    function_names = {}
    for sig in results["function_signatures"]:
        name = sig["name"]
        if name not in function_names:
            function_names[name] = []
        function_names[name].append(sig["file"])

    # Find duplicate function names
    duplicates = {
        name: files for name, files in function_names.items() if len(files) > 1
    }
    if duplicates:
        results["naming_consistency"] = False
        results["warnings"].append(f"Duplicate function names found: {duplicates}")

    return results


def validate_file_structure(
    created_files: List[str], modified_files: List[str]
) -> Dict:
    """Validate that file structure changes are appropriate."""
    results = {
        "appropriate_locations": True,
        "naming_conventions": True,
        "warnings": [],
    }

    # Check file locations
    for file_path in created_files + modified_files:
        path = Path(file_path)

        # Check if file is in appropriate directory
        if path.suffix == ".py":
            if "test" in path.name.lower() and "tests" not in str(path):
                results["warnings"].append(
                    f"Test file {file_path} not in tests/ directory"
                )
                results["appropriate_locations"] = False

            if path.name.startswith("ui_") and "ui" not in str(path):
                results["warnings"].append(f"UI file {file_path} not in ui/ directory")
                results["appropriate_locations"] = False

    # Check naming conventions
    for file_path in created_files + modified_files:
        path = Path(file_path)

        if path.suffix == ".py":
            # Check for snake_case
            if "_" not in path.stem and path.stem.lower() != path.stem:
                results["warnings"].append(
                    f"Python file {file_path} should use snake_case"
                )
                results["naming_conventions"] = False

    return results


def generate_validation_report(validation_type: str, **kwargs) -> str:
    """Generate a comprehensive validation report."""
    report = []
    report.append(f"Validation Type: {validation_type}")
    report.append("")

    if validation_type == "documentation":
        results = validate_documentation_completeness(
            kwargs.get("doc_file", ""), kwargs.get("code_files", [])
        )

        report.append(f"Documentation File: {kwargs.get('doc_file', 'N/A')}")
        report.append(f"File Exists: {results['file_exists']}")
        report.append(f"Coverage: {results['coverage']:.1f}%")

        if results["missing_items"]:
            report.append(f"Missing Items: {len(results['missing_items'])}")
            for item in results["missing_items"][:5]:
                report.append(f"   - {item}")

        if results["extra_items"]:
            report.append(f"Extra Items: {len(results['extra_items'])}")
            for item in results["extra_items"][:5]:
                report.append(f"   - {item}")

    elif validation_type == "code_consistency":
        results = validate_code_consistency(kwargs.get("changed_files", []))

        report.append(f"Code Consistency Check")
        report.append(f"Import Consistency: {results['import_consistency']}")
        report.append(f"Naming Consistency: {results['naming_consistency']}")
        report.append(f"Functions Found: {len(results['function_signatures'])}")

        if results["warnings"]:
            report.append(f"Warnings: {len(results['warnings'])}")
            for warning in results["warnings"][:3]:
                report.append(f"   - {warning}")

    elif validation_type == "file_structure":
        results = validate_file_structure(
            kwargs.get("created_files", []), kwargs.get("modified_files", [])
        )

        report.append(f"File Structure Validation")
        report.append(f"Appropriate Locations: {results['appropriate_locations']}")
        report.append(f"Naming Conventions: {results['naming_conventions']}")

        if results["warnings"]:
            report.append(f"Warnings: {len(results['warnings'])}")
            for warning in results["warnings"][:3]:
                report.append(f"   - {warning}")

    # Overall assessment
    report.append("")
    report.append("OVERALL ASSESSMENT:")

    if validation_type == "documentation":
        completeness_threshold = VALIDATE_AI_WORK_CONFIG.get(
            "completeness_threshold", 90.0
        )
        if results["coverage"] >= completeness_threshold:
            report.append("GOOD - Documentation covers most items")
        elif results["coverage"] >= completeness_threshold * 0.5:
            report.append("FAIR - Documentation needs improvement")
        else:
            report.append("POOR - Documentation is incomplete")

    elif validation_type == "code_consistency":
        if results["naming_consistency"] and not results["warnings"]:
            report.append("GOOD - Code is consistent")
        else:
            report.append("NEEDS ATTENTION - Inconsistencies found")

    elif validation_type == "file_structure":
        if results["appropriate_locations"] and results["naming_conventions"]:
            report.append("GOOD - File structure is appropriate")
        else:
            report.append("NEEDS ATTENTION - File structure issues found")

    return "\n".join(report)


def analyze_ai_work(
    work_type: str,
    project_root: Optional[str] = None,
    config_path: Optional[str] = None,
    **kwargs,
) -> Dict:
    """
    Main validation function for AI work.

    Args:
        work_type: Type of validation to perform ("documentation", "code_changes", "file_creation")
        project_root: Optional project root path (for config loading)
        config_path: Optional path to config file (for config loading)
        **kwargs: Additional arguments for validation
    """
    global VALIDATE_AI_WORK_CONFIG

    # Load config if project_root or config_path provided
    if project_root or config_path:
        if config_path:
            config.load_external_config(config_path)
        # Reload config (project_root is handled via config file)
        VALIDATE_AI_WORK_CONFIG = config.get_analyze_ai_work_config()

        # Load rule sets if configured
        rule_set_paths = VALIDATE_AI_WORK_CONFIG.get("rule_set_paths", [])
        rule_sets = VALIDATE_AI_WORK_CONFIG.get("rule_sets", {})

        # Load rule sets from files if paths provided
        if rule_set_paths:
            for rule_path in rule_set_paths:
                rule_path_obj = Path(rule_path)
                if not rule_path_obj.is_absolute() and project_root:
                    rule_path_obj = Path(project_root) / rule_path_obj

                if rule_path_obj.exists():
                    try:
                        with open(rule_path_obj, "r", encoding="utf-8") as f:
                            if rule_path_obj.suffix in (".yaml", ".yml"):
                                logger.warning(
                                    f"YAML rule files not supported, skipping {rule_path}"
                                )
                                continue
                            else:
                                import json

                                loaded_rules = json.load(f)
                            if isinstance(loaded_rules, dict):
                                rule_sets.update(loaded_rules)
                    except Exception as e:
                        logger.warning(f"Failed to load rule set from {rule_path}: {e}")

    # Generate report text
    if work_type == "documentation":
        output = generate_validation_report("documentation", **kwargs)
    elif work_type == "code_changes":
        output = generate_validation_report("code_consistency", **kwargs)
    elif work_type == "file_creation":
        output = generate_validation_report("file_structure", **kwargs)
    else:
        output = "Unknown validation type"

    # Extract status from output
    status = "UNKNOWN"
    if isinstance(output, str):
        if "POOR" in output or "FAIL" in output:
            status = "POOR"
        elif "GOOD" in output or "PASS" in output:
            status = "GOOD"
        elif "NEEDS ATTENTION" in output or "FAIR" in output or "WARNING" in output:
            status = "NEEDS_ATTENTION"

    # Return standard format
    return {
        "summary": {
            "total_issues": 0 if status in ("GOOD", "UNKNOWN") else 1,
            "files_affected": 0,
            "status": status,
        },
        "details": {"output": output, "work_type": work_type},
    }


def execute(
    project_root: Optional[str] = None, config_path: Optional[str] = None, **kwargs
) -> Dict:
    """Execute validation (for use by run_development_tools)."""
    work_type = kwargs.pop("work_type", "documentation")
    return analyze_ai_work(
        work_type, project_root=project_root, config_path=config_path, **kwargs
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Lightweight structural validator for AI-generated work"
    )
    parser.add_argument(
        "--work-type",
        default="documentation",
        choices=["documentation", "code_changes", "file_creation"],
        help="Type of validation to perform",
    )
    parser.add_argument(
        "--doc-file", help="Documentation file to validate (for documentation type)"
    )
    parser.add_argument(
        "--code-files",
        nargs="*",
        help="Code files to validate (for documentation type)",
    )
    parser.add_argument(
        "--changed-files",
        nargs="*",
        help="Changed files to validate (for code_changes type)",
    )
    parser.add_argument(
        "--created-files",
        nargs="*",
        help="Created files to validate (for file_creation type)",
    )
    parser.add_argument(
        "--modified-files",
        nargs="*",
        help="Modified files to validate (for file_creation type)",
    )

    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON in standard format"
    )
    args = parser.parse_args()

    kwargs = {}
    if args.doc_file:
        kwargs["doc_file"] = args.doc_file
    if args.code_files:
        kwargs["code_files"] = args.code_files
    if args.changed_files:
        kwargs["changed_files"] = args.changed_files
    if args.created_files:
        kwargs["created_files"] = args.created_files
    if args.modified_files:
        kwargs["modified_files"] = args.modified_files

    result = analyze_ai_work(args.work_type, **kwargs)

    if args.json:
        # Output JSON in standard format
        import json

        print(json.dumps(result, indent=2))
    else:
        output = result.get("details", {}).get("output", "")
        print(output)
        # Also log for debugging (but not the full output)
        if len(output) < 500:  # Only log short outputs
            logger.info(output)
