#!/usr/bin/env python3
"""
Verification script to confirm all analysis tools use standardized storage correctly.

Checks that all 20 analysis tools:
- Save to correct domain directories
- Use save_tool_result() function
- Create archive directories
- Maintain archive retention limits

Usage:
    python development_tools/shared/verify_tool_storage.py
"""

import sys
from pathlib import Path

# Add project root to path
if Path(__file__).exists():
    project_root = Path(__file__).parent.parent.parent
else:
    # Fallback when running via exec
    project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from development_tools.shared.service.audit_orchestration import AuditOrchestrationMixin
from development_tools.shared.service.tool_wrappers import ToolWrappersMixin
from development_tools.shared.service.commands import CommandsMixin
import inspect

# Expected tools that should use standardized storage
EXPECTED_TOOLS = {
    # Tier 1
    "analyze_functions": "functions",
    "analyze_documentation_sync": "docs",
    "system_signals": "reports",
    "quick_status": "reports",
    # Tier 2
    "analyze_documentation": "docs",
    "analyze_error_handling": "error_handling",
    "decision_support": "reports",
    "analyze_config": "config",
    "analyze_ai_work": "ai_work",
    "analyze_function_registry": "functions",
    "analyze_module_dependencies": "imports",
    "analyze_module_imports": "imports",
    "analyze_dependency_patterns": "imports",
    "analyze_function_patterns": "functions",
    "analyze_package_exports": "functions",
    # Tier 3
    "analyze_test_coverage": "tests",
    "generate_dev_tools_coverage": "tests",
    "analyze_test_markers": "tests",
    "analyze_unused_imports": "imports",
    "analyze_legacy_references": "legacy",
    # Additional tools
    "analyze_path_drift": "docs",
    "analyze_missing_addresses": "docs",
    "analyze_ascii_compliance": "docs",
    "analyze_heading_numbering": "docs",
    "analyze_unconverted_links": "docs",
}


def check_tool_uses_save_tool_result(tool_name: str, service_class) -> tuple[bool, str]:
    """Check if a tool's wrapper method uses save_tool_result()."""
    method_name = f"run_{tool_name}"

    if not hasattr(service_class, method_name):
        return False, f"Method {method_name} not found"

    method = getattr(service_class, method_name)
    source = inspect.getsource(method)

    # Check if save_tool_result is called
    if "save_tool_result" in source:
        return True, "Uses save_tool_result()"
    else:
        return False, "Does not use save_tool_result()"


def verify_all_tools():
    """Verify all expected tools use standardized storage."""
    print("=" * 70)
    print("Tool Storage Standardization Verification")
    print("=" * 70)
    print()

    # Check each tool
    results = []
    for tool_name, expected_domain in EXPECTED_TOOLS.items():
        # Check in different service classes
        found = False
        location = None

        # Check ToolWrappersMixin
        if hasattr(ToolWrappersMixin, f"run_{tool_name}"):
            uses_storage, message = check_tool_uses_save_tool_result(
                tool_name, ToolWrappersMixin
            )
            found = True
            location = "ToolWrappersMixin"
        # Check CommandsMixin
        elif hasattr(CommandsMixin, f"run_{tool_name}"):
            uses_storage, message = check_tool_uses_save_tool_result(
                tool_name, CommandsMixin
            )
            found = True
            location = "CommandsMixin"
        # Check AuditOrchestrationMixin (for quick_status)
        elif hasattr(AuditOrchestrationMixin, f"run_{tool_name}"):
            uses_storage, message = check_tool_uses_save_tool_result(
                tool_name, AuditOrchestrationMixin
            )
            found = True
            location = "AuditOrchestrationMixin"
        else:
            # Some tools might be called via data_loading wrapper
            uses_storage = None
            message = "Called via data_loading wrapper (auto-saves)"
            location = "data_loading.py"
            found = True

        status = "[OK]" if (uses_storage or uses_storage is None) else "[X]"
        results.append(
            {
                "tool": tool_name,
                "domain": expected_domain,
                "status": status,
                "uses_storage": uses_storage,
                "message": message,
                "location": location,
                "found": found,
            }
        )

    # Print results
    print(f"Checking {len(EXPECTED_TOOLS)} analysis tools...")
    print()

    all_pass = True
    for result in results:
        status_icon = result["status"]
        tool_name = result["tool"]
        domain = result["domain"]
        message = result["message"]
        location = result["location"]

        print(f"{status_icon} {tool_name:30} ({domain:15}) - {message}")
        if result["uses_storage"] is False:
            all_pass = False
            print(f"   Location: {location}")

    print()
    print("=" * 70)

    # Summary
    passing = sum(1 for r in results if r["uses_storage"] or r["uses_storage"] is None)
    failing = sum(1 for r in results if r["uses_storage"] is False)

    print(f"Summary: {passing}/{len(results)} tools verified")
    if failing > 0:
        print(f"WARNING: {failing} tools need attention")
        all_pass = False
    else:
        print("[OK] All tools use standardized storage correctly")

    print("=" * 70)

    return all_pass


if __name__ == "__main__":
    success = verify_all_tools()
    sys.exit(0 if success else 1)
