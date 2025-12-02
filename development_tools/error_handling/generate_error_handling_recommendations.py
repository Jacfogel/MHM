#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
generate_error_handling_recommendations.py
Generates recommendations for improving error handling based on analysis results.

Configuration is loaded from external config file (development_tools_config.json)
if available, making this tool portable across different projects.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

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


def generate_recommendations(analysis_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations for improving error handling based on analysis results."""
    recommendations = []
    
    # Coverage recommendations
    coverage = analysis_results.get('analyze_error_handling', 0)
    if coverage < 80:
        recommendations.append(f"Improve error handling coverage (currently {coverage:.1f}%)")
    
    # Missing error handling recommendations
    missing_count = analysis_results.get('functions_missing_error_handling', 0)
    if missing_count > 0:
        recommendations.append(f"Add error handling to {missing_count} functions")
    
    # Quality recommendations
    error_handling_quality = analysis_results.get('error_handling_quality', {})
    if error_handling_quality.get('none', 0) > 0:
        recommendations.append("Replace basic try-except with @handle_errors decorator where appropriate")
    
    # Pattern recommendations (use first decorator from config)
    error_config = config.get_error_handling_config()
    decorator_names = error_config.get('decorator_names', ['@handle_errors'])
    primary_decorator = decorator_names[0] if decorator_names else '@handle_errors'
    decorator_key = primary_decorator.replace('@', '').replace('_', '_') + '_decorator'
    
    error_patterns = analysis_results.get('error_patterns', {})
    if error_patterns.get('try_except', 0) > error_patterns.get(decorator_key, 0):
        recommendations.append(f"Consider using {primary_decorator} decorator instead of manual try-except blocks")
    
    # Specific missing error handling
    missing_error_handling = analysis_results.get('missing_error_handling', [])
    critical_missing = [f for f in missing_error_handling if f.get('quality') == 'none']
    if critical_missing:
        recommendations.append(f"Priority: Add error handling to {len(critical_missing)} critical functions")
    
    return recommendations


def main():
    """Main entry point for recommendation generation."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Generate error handling recommendations')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file with analysis results')
    parser.add_argument('--output', type=str, help='Output file path (default: stdout)')
    
    args = parser.parse_args()
    
    # Load analysis results
    with open(args.input, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis_results)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({'recommendations': recommendations}, f, indent=2)
        logger.info(f"Recommendations written to {args.output}")
    else:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    main()

