#!/usr/bin/env python3
"""
AI Tools Guide - Comprehensive Tool Usage and Output Interpretation

Provides specific guidance on when to use each audit tool and how to interpret their output.
This helps AI assistants make better decisions about which tools to use and how to understand results.
"""

import sys
import subprocess

# Tool configurations with usage guidance
TOOL_GUIDE = {
    "ai_tools_runner.py": {
        "purpose": "Comprehensive interface for all AI tools (single entry point)",
        "when_to_use": [
            "Primary tool for all AI tool operations",
            "Simple commands for basic operations (audit, docs, validate, config)",
            "Advanced commands for complex tasks (workflow, quick-audit, decision-support)",
            "When you want a unified interface for all tools",
            "For both simple user commands and advanced AI workflows"
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
    
    "function_discovery.py": {
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
    
    "validate_ai_work.py": {
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
    
    "audit_function_registry.py": {
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
    
    "audit_module_dependencies.py": {
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

def show_tool_guide(tool_name=None):
    """Show comprehensive guide for tool usage"""
    if tool_name:
        if tool_name in TOOL_GUIDE:
            tool = TOOL_GUIDE[tool_name]
            print(f"🔧 Tool Guide: {tool_name}")
            print("=" * 50)
            print(f"Purpose: {tool['purpose']}")
            print()
            
            print("📋 When to Use:")
            for i, scenario in enumerate(tool['when_to_use'], 1):
                print(f"   {i}. {scenario}")
            print()
            
            print("📊 Output Interpretation:")
            for key, description in tool['output_interpretation'].items():
                print(f"   • {key}: {description}")
            print()
            
            print("✅ Success Criteria:")
            for i, criterion in enumerate(tool['success_criteria'], 1):
                print(f"   {i}. {criterion}")
        else:
            print(f"❌ Tool '{tool_name}' not found in guide")
            print("Available tools:")
            for tool in TOOL_GUIDE.keys():
                print(f"   • {tool}")
    else:
        print("🔧 AI Tools Guide - When to Use Each Tool")
        print("=" * 50)
        print()
        
        for tool_name, tool_info in TOOL_GUIDE.items():
            print(f"📋 {tool_name}")
            print(f"   Purpose: {tool_info['purpose']}")
            print(f"   Command: python ai_development_tools/{tool_name}")
            print()
            
            print("   When to use:")
            for scenario in tool_info['when_to_use'][:3]:  # Show first 3
                print(f"     • {scenario}")
            if len(tool_info['when_to_use']) > 3:
                print(f"     • ... and {len(tool_info['when_to_use']) - 3} more")
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
    print(f"🎯 Tool Recommendations for: {scenario}")
    print("=" * 50)
    
    recommendations = get_tool_recommendation(scenario)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
            print(f"{priority_icon} {i}. {rec['tool']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Command: python ai_development_tools/{rec['tool']}")
            print()
    else:
        print("❌ No specific tool recommendations found.")
        print("💡 Try running the general audit first:")
        print("   python ai_development_tools/ai_tools_runner.py audit")

def run_tool_with_guidance(tool_name):
    """Run a tool and provide guidance on interpreting results"""
    if tool_name not in TOOL_GUIDE:
        print(f"❌ Tool '{tool_name}' not found")
        return
    
    print(f"🚀 Running {tool_name} with guidance...")
    print("=" * 50)
    
    # Show what to expect
    tool = TOOL_GUIDE[tool_name]
    print(f"Purpose: {tool['purpose']}")
    print()
    print("📊 What to look for in the output:")
    for key, description in tool['output_interpretation'].items():
        print(f"   • {key}: {description}")
    print()
    
    # Run the tool
    try:
        result = subprocess.run([sys.executable, f"ai_development_tools/{tool_name}"], 
                              capture_output=True, text=True, timeout=60)
        
        print("📋 Tool Output:")
        print("-" * 30)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        print()
        print("✅ Success Criteria Check:")
        for criterion in tool['success_criteria']:
            print(f"   • {criterion}")
        
    except subprocess.TimeoutExpired:
        print("⏰ Tool timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error running tool: {e}")

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
            tool_name = sys.argv[2] if len(sys.argv) > 2 else "ai_tools_runner.py"
            run_tool_with_guidance(tool_name)
        else:
            print("Usage:")
            print("  python ai_development_tools/tool_guide.py guide                    # Show all tools")
            print("  python ai_development_tools/tool_guide.py guide ai_tools_runner.py     # Show specific tool")
            print("  python ai_development_tools/tool_guide.py recommend 'documentation' # Get recommendations")
            print("  python ai_development_tools/tool_guide.py run ai_tools_runner.py       # Run with guidance")
    else:
        # Default: show all tools
        show_tool_guide()
        print("💡 For specific guidance:")
        print("   python ai_development_tools/tool_guide.py guide <tool_name>")
        print("   python ai_development_tools/tool_guide.py recommend 'your scenario'") 