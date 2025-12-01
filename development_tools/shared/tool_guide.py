#!/usr/bin/env python3
# TOOL_TIER: supporting
"""
AI Tools Guide - Comprehensive Tool Usage and Output Interpretation

Provides specific guidance on when to use each audit tool and how to interpret their output.
This helps AI assistants make better decisions about which tools to use and how to understand results.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

try:
    from ..shared.tool_metadata import get_tools_by_tier
except ImportError:
    from development_tools.shared.tool_metadata import get_tools_by_tier

logger = get_component_logger("development_tools")

TIER_TITLES = {
    "core": "Core (stable)",
    "supporting": "Supporting (advisory)",
    "experimental": "Experimental (use with approval)",
}

# Tool configurations with usage guidance
TOOL_GUIDE = {
    "run_development_tools.py": {
        "purpose": "Comprehensive interface for all development tools (single entry point)",
        "when_to_use": [
            "Primary tool for all development tool operations",
            "Simple commands for basic operations (audit, docs, validate, config)",
            "Advanced commands for complex tasks (workflow, quick-audit, decision-support)",
            "When you want a unified interface for all tools",
            "For both simple user commands and advanced workflows"
        ],
        "output_interpretation": {
            "audit": "Comprehensive audit results with statistics",
            "docs": "Documentation update status and validation",
            "validate": "AI work validation with scores",
            "config": "Configuration consistency check",
            "workflow": "Workflow execution with audit-first protocol"
        },
        "success_criteria": [
            "Provides appropriate output for each command type",
            "Handles both simple and advanced operations",
            "Enforces audit-first protocol when needed",
            "Gives clear success/failure status"
        ]
    },
    
    "analyze_functions.py": {
        "purpose": "Find and categorize all functions with detailed analysis",
        "when_to_use": [
            "Need to understand what functions exist",
            "Want to see function relationships",
            "Looking for specific types of functions",
            "Planning refactoring or reorganization",
            "Creating function documentation"
        ],
        "output_interpretation": {
            "handlers": "Functions that handle user interactions or events",
            "tests": "Functions that test other code",
            "complex": "Functions with high complexity (need attention)",
            "undocumented": "Functions without docstrings or comments",
            "simple": "Basic utility functions"
        },
        "success_criteria": [
            "Categorizes functions by type",
            "Shows complexity metrics",
            "Identifies documentation gaps",
            "Provides function counts by category"
        ]
    },
    
    "decision_support.py": {
        "purpose": "Dashboard with actionable insights for codebase improvement",
        "when_to_use": [
            "Before making architectural decisions",
            "When suggesting refactoring",
            "Planning code organization changes",
            "Identifying improvement opportunities",
            "Making recommendations to user"
        ],
        "output_interpretation": {
            "complexity_hotspots": "Areas with high complexity that need attention",
            "documentation_gaps": "Functions or modules lacking documentation",
            "duplicate_patterns": "Potential code duplication",
            "maintenance_concerns": "Areas that may be hard to maintain",
            "improvement_opportunities": "Specific suggestions for improvement"
        },
        "success_criteria": [
            "Provides actionable recommendations",
            "Prioritizes issues by importance",
            "Gives specific improvement suggestions",
            "Shows impact of potential changes"
        ]
    },
    
    "analyze_ai_work.py": {
        "purpose": "Validate AI-generated work before presenting to user",
        "when_to_use": [
            "Before showing any documentation to user",
            "After creating analysis or recommendations",
            "Before making architectural suggestions",
            "When user questions accuracy",
            "Before presenting complex information"
        ],
        "output_interpretation": {
            "completeness_score": "How complete the work is (0-100%)",
            "accuracy_score": "How accurate the information is (0-100%)",
            "confidence_level": "How confident we can be in the work",
            "missing_information": "What information is missing",
            "validation_issues": "Specific problems found"
        },
        "success_criteria": [
            "Identifies gaps in information",
            "Flags potential inaccuracies",
            "Suggests improvements",
            "Provides confidence metrics"
        ]
    },
    
    "analyze_function_registry.py": {
        "purpose": "Check completeness and accuracy of function documentation",
        "when_to_use": [
            "Creating or updating function registries",
            "Checking documentation completeness",
            "Validating function documentation",
            "Planning documentation improvements"
        ],
        "output_interpretation": {
            "documented_functions": "Functions with complete documentation",
            "partial_documentation": "Functions with incomplete documentation",
            "missing_documentation": "Functions without documentation",
            "documentation_quality": "Quality assessment of existing documentation"
        },
        "success_criteria": [
            "Shows documentation coverage",
            "Identifies specific gaps",
            "Assesses documentation quality",
            "Provides improvement suggestions"
        ]
    },
    
    "analyze_module_dependencies.py": {
        "purpose": "Analyze module dependencies and import relationships",
        "when_to_use": [
            "Understanding code architecture",
            "Planning module reorganization",
            "Identifying circular dependencies",
            "Making structural changes",
            "Analyzing code complexity"
        ],
        "output_interpretation": {
            "dependency_graph": "Visual representation of module relationships",
            "circular_dependencies": "Modules that depend on each other",
            "high_coupling": "Modules with many dependencies",
            "isolated_modules": "Modules with few dependencies"
        },
        "success_criteria": [
            "Shows clear dependency relationships",
            "Identifies architectural issues",
            "Suggests structural improvements",
            "Provides complexity metrics"
        ]
    },
    
    "analyze_documentation.py": {
        "purpose": "Find documentation overlap and redundancy",
        "when_to_use": [
            "Consolidating documentation",
            "Identifying redundant information",
            "Planning documentation cleanup",
            "Finding documentation gaps"
        ],
        "output_interpretation": {
            "overlap_areas": "Topics covered in multiple places",
            "redundant_content": "Duplicate or similar information",
            "documentation_gaps": "Topics not covered anywhere",
            "consolidation_opportunities": "Areas that could be combined"
        },
        "success_criteria": [
            "Identifies specific overlaps",
            "Shows redundancy patterns",
            "Suggests consolidation strategies",
            "Maps documentation coverage"
        ]
    }
}


def _print_tier_overview():
    """Print tier summaries sourced from tool metadata."""
    print("Tier Overview")
    print("-------------")
    for tier_key in ("core", "supporting", "experimental"):
        tools = sorted(get_tools_by_tier(tier_key), key=lambda info: info.name)
        if not tools:
            continue
        title = TIER_TITLES.get(tier_key, tier_key.title())
        print(f"{title}:")
        for info in tools:
            print(f"  - {info.name} [{info.trust}]: {info.description}")
        print()

def show_tool_guide(tool_name=None):
    """Show comprehensive guide for tool usage"""
    if tool_name:
        if tool_name in TOOL_GUIDE:
            tool = TOOL_GUIDE[tool_name]
            print(f"Tool Guide: {tool_name}")
            print("=" * 50)
            print(f"Purpose: {tool['purpose']}")
            print()
            
            print("When to Use:")
            for i, scenario in enumerate(tool['when_to_use'], 1):
                print(f"   {i}. {scenario}")
            print()
            
            print("Output Interpretation:")
            for key, description in tool['output_interpretation'].items():
                print(f"   - {key}: {description}")
            print()
            
            print("Success Criteria:")
            for i, criterion in enumerate(tool['success_criteria'], 1):
                print(f"   {i}. {criterion}")
        else:
            logger.warning(f"Tool '{tool_name}' not found in guide")
            # User-facing help messages stay as print() for immediate visibility
            print("Available tools:")
            for tool in TOOL_GUIDE.keys():
                print(f"   - {tool}")
    else:
        print("AI Tools Guide - When to Use Each Tool")
        print("=" * 50)
        print()
        _print_tier_overview()
        for tool_name, tool_info in TOOL_GUIDE.items():
            print(tool_name)
            print(f"   Purpose: {tool_info['purpose']}")
            print(f"   Command: python development_tools/{tool_name}")
            print()
            
            print("   When to use:")
            for scenario in tool_info['when_to_use'][:3]:  # Show first 3
                print(f"     - {scenario}")
            if len(tool_info['when_to_use']) > 3:
                print(f"     - ... and {len(tool_info['when_to_use']) - 3} more")
            print()

def get_tool_recommendation(scenario):
    """Get tool recommendations for a specific scenario"""
    recommendations = []
    
    scenario_lower = scenario.lower()
    
    for tool_name, tool_info in TOOL_GUIDE.items():
        for use_case in tool_info['when_to_use']:
            if any(keyword in scenario_lower for keyword in use_case.lower().split()):
                recommendations.append({
                    'tool': tool_name,
                    'reason': use_case,
                    'priority': 'high' if 'documentation' in scenario_lower and 'audit' in tool_name else 'medium'
                })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x['priority'] == 'high', reverse=True)
    
    return recommendations

def show_recommendations(scenario):
    """Show tool recommendations for a specific scenario"""
    print(f"Tool Recommendations for: {scenario}")
    print("=" * 50)
    
    recommendations = get_tool_recommendation(scenario)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "[HIGH]" if rec['priority'] == 'high' else "[MED]"
            print(f"{priority_icon} {i}. {rec['tool']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Command: python development_tools/{rec['tool']}")
            print()
    else:
        logger.info("No specific tool recommendations found.")
        # User-facing help messages stay as print() for immediate visibility
        print("NOTE: Try running the general audit first:")
        print("   python development_tools/run_development_tools.py audit")

def run_tool_with_guidance(tool_name):
    """Run a tool and provide guidance on interpreting results"""
    if tool_name not in TOOL_GUIDE:
        logger.error(f"Tool '{tool_name}' not found")
        return
    
    logger.info(f"Running {tool_name} with guidance...")
    # User-facing help messages stay as print() for immediate visibility
    print(f"Running {tool_name} with guidance...")
    print("=" * 50)
    
    # Show what to expect
    tool = TOOL_GUIDE[tool_name]
    print(f"Purpose: {tool['purpose']}")
    print()
    print("What to look for in the output:")
    for key, description in tool['output_interpretation'].items():
        print(f"   - {key}: {description}")
    print()
    
    # Run the tool
    try:
        result = subprocess.run([sys.executable, f"development_tools/{tool_name}"], 
                              capture_output=True, text=True, timeout=60)
        
        print("Tool Output:")
        print("-" * 30)
        if result.stdout:
            print(result.stdout)
            logger.debug(f"Tool stdout: {result.stdout[:500]}")  # Log first 500 chars
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            logger.warning(f"Tool stderr: {result.stderr}")
        
        print()
        print("Success Criteria Check:")
        for criterion in tool['success_criteria']:
            print(f"   - {criterion}")
        
    except subprocess.TimeoutExpired:
        logger.error("Tool timed out after 60 seconds")
        print("Tool timed out after 60 seconds")
    except Exception as e:
        logger.error(f"Error running tool: {e}")
        print(f"Error running tool: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "guide":
            tool_name = sys.argv[2] if len(sys.argv) > 2 else None
            show_tool_guide(tool_name)
        elif command == "recommend":
            scenario = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "documentation"
            show_recommendations(scenario)
        elif command == "run":
            tool_name = sys.argv[2] if len(sys.argv) > 2 else "run_development_tools.py"
            run_tool_with_guidance(tool_name)
        else:
            print("Usage:")
            print("  python development_tools/shared/tool_guide.py guide                    # Show all tools")
            print("  python development_tools/shared/tool_guide.py guide run_development_tools.py     # Show specific tool")
            print("  python development_tools/shared/tool_guide.py recommend 'documentation' # Get recommendations")
            print("  python development_tools/shared/tool_guide.py run run_development_tools.py       # Run with guidance")
    else:
        # Default: show all tools
        show_tool_guide()
        print("NOTE: For specific guidance:")
        print("   python development_tools/shared/tool_guide.py guide <tool_name>")
        print("   python development_tools/shared/tool_guide.py recommend 'your scenario'") 
