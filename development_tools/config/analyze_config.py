#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Configuration Validator - Ensures all tools use configuration consistently

This tool validates that all AI tools are using the centralized configuration
and checks for configuration consistency and completeness.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path for core module imports
# Script is at: development_tools/config/analyze_config.py
# So we need to go up 2 levels to get to project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from . import config
except ImportError:
    from development_tools import config

from core.logger import get_component_logger

# Load external config on module import
config.load_external_config()

# Get configuration
CONFIG_VALIDATOR_CONFIG = config.get_analyze_config_config()

logger = get_component_logger("development_tools")

class ConfigValidator:
    """Validates configuration usage across all AI tools."""
    
    def __init__(self):
        # Use the current config schema
        # Script is at: development_tools/config/analyze_config.py
        # So we need to go up 2 levels to get to project root
        self.project_root = Path(__file__).parent.parent.parent
        self.ai_tools_dir = self.project_root / 'development_tools'
        self.validation_results = {
            'config_usage': {},
            'hardcoded_values': {},
            'missing_imports': {},
            'inconsistent_settings': {},
            'recommendations': []
        }
    
    def scan_tools_for_config_usage(self) -> Dict:
        """Scan all AI tools to check configuration usage."""
        logger.info("Scanning AI tools for configuration usage...")
        
        tools = {}
        for py_file in self.ai_tools_dir.glob('*.py'):
            if py_file.name == 'config.py' or py_file.name == 'analyze_config.py':
                continue
                
            tool_name = py_file.name
            tools[tool_name] = self._analyze_tool_config_usage(py_file)
        
        return tools
    
    def _analyze_tool_config_usage(self, file_path: Path) -> Dict:
        """Analyze a single tool's configuration usage."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'imports_config': False,
                'uses_config_functions': False,
                'hardcoded_values': [],
                'config_functions_used': [],
                'issues': [],
                'is_wrapper_script': False
            }
            
            # Check if this is a wrapper script (just imports and calls main() from another module)
            # Wrapper scripts don't need config since they delegate to the actual implementation
            wrapper_patterns = [
                r'from\s+[\w\.]+\s+import\s+main',
                r'import\s+[\w\.]+\s+as\s+.*main',
                r'sys\.exit\(main\(\)\)',
                r'Shorthand alias|wrapper script|convenient.*name',
            ]
            is_wrapper = any(re.search(pattern, content, re.IGNORECASE) for pattern in wrapper_patterns)
            
            # If it's a wrapper script and doesn't use config functions, skip config import check
            if is_wrapper:
                analysis['is_wrapper_script'] = True
                # Wrapper scripts are exempt from config import requirement
                analysis['imports_config'] = True  # Mark as OK to skip recommendation
            
            # Check for config import
            if 'import config' in content or 'from config import' in content:
                analysis['imports_config'] = True
            
            # Check for config function usage
            config_functions = [
                'get_available_channels', 'get_channel_class_mapping', 'get_user_data_dir',
                'get_backups_dir', 'get_user_file_path', 'validate_core_paths',
                'validate_ai_configuration', 'validate_communication_channels',
                'validate_logging_configuration', 'validate_scheduler_configuration',
                'validate_file_organization_settings', 'validate_environment_variables',
                'validate_all_configuration', 'validate_and_raise_if_invalid',
                'print_configuration_report', 'ensure_user_directory',
                'validate_email_config', 'validate_discord_config', 'validate_minimum_config'
            ]
            
            for func in config_functions:
                if f'config.{func}' in content:
                    analysis['uses_config_functions'] = True
                    analysis['config_functions_used'].append(func)
            
            # Check for hardcoded values that should use config
            hardcoded_patterns = [
                (r"BASE_DATA_DIR\s*=\s*['\"].*?['\"]", "Should use config.BASE_DATA_DIR"),
                (r"USER_INFO_DIR_PATH\s*=\s*['\"].*?['\"]", "Should use config.USER_INFO_DIR_PATH"),
                (r"data_dir\s*=\s*['\"].*?['\"]", "Should use config.BASE_DATA_DIR"),
                (r"users_dir\s*=\s*['\"].*?['\"]", "Should use config.USER_INFO_DIR_PATH"),
                (r"backups_dir\s*=\s*['\"].*?['\"]", "Should use config.get_backups_dir()"),
                (r"user_data_dir\s*=\s*['\"].*?['\"]", "Should use config.get_user_data_dir()")
            ]
            
            for pattern, message in hardcoded_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    analysis['hardcoded_values'].append({
                        'pattern': pattern,
                        'message': message,
                        'matches': len(matches)
                    })
            
            # Check for issues (only add issues not already tracked by boolean flags)
            if not analysis['uses_config_functions'] and analysis['hardcoded_values']:
                analysis['issues'].append("Has hardcoded values but doesn't use config functions")
            
            return analysis
            
        except Exception as e:
            return {
                'imports_config': False,
                'uses_config_functions': False,
                'hardcoded_values': [],
                'config_functions_used': [],
                'issues': [f"Error analyzing file: {e}"]
            }
    
    def validate_configuration_consistency(self) -> Dict:
        """Validate that the configuration itself is consistent."""
        logger.info("Validating configuration consistency...")
        
        validation = {
            'scan_directories_exist': [],
            'missing_directories': [],
            'config_structure_valid': True,
            'issues': []
        }
        
        # Check if scan directories exist
        scan_dirs = config.get_scan_directories()
        for scan_dir in scan_dirs:
            dir_path = self.project_root / scan_dir
            if dir_path.exists():
                validation['scan_directories_exist'].append(scan_dir)
            else:
                validation['missing_directories'].append(scan_dir)
                validation['issues'].append(f"Scan directory '{scan_dir}' does not exist")
        
        # Check configuration structure
        required_sections = [
            'PROJECT_ROOT', 'SCAN_DIRECTORIES', 'FUNCTION_DISCOVERY', 
            'VALIDATION', 'AUDIT', 'OUTPUT', 'QUICK_AUDIT', 'VERSION_SYNC',
            'WORKFLOW', 'DOCUMENTATION', 'AUTO_DOCUMENT', 'AI_VALIDATION'
        ]
        
        for section in required_sections:
            if not hasattr(config, section):
                validation['config_structure_valid'] = False
                validation['issues'].append(f"Missing configuration section: {section}")
        
        return validation
    
    def check_configuration_completeness(self) -> Dict:
        """Check if all configuration sections have required fields."""
        logger.info("Checking configuration completeness...")
        
        completeness = {
            'sections_complete': True,
            'missing_fields': [],
            'recommendations': []
        }
        
        # Check FUNCTION_DISCOVERY
        func_discovery = config.get_analyze_functions_config()
        required_func_fields = [
            'moderate_complexity_threshold',
            'high_complexity_threshold',
            'critical_complexity_threshold',
            'min_docstring_length',
            'handler_keywords',
            'test_keywords',
        ]
        for field in required_func_fields:
            if field not in func_discovery:
                completeness['sections_complete'] = False
                completeness['missing_fields'].append(f"FUNCTION_DISCOVERY.{field}")
        
        # Check VALIDATION
        validation_config = config.get_validation_config()
        required_validation_fields = [
            'documentation_coverage_threshold',
            'moderate_complexity_warning',
            'high_complexity_warning',
            'critical_complexity_warning',
            'duplicate_function_warning',
            'missing_docstring_warning',
            'critical_issues_first',
        ]
        for field in required_validation_fields:
            if field not in validation_config:
                completeness['sections_complete'] = False
                completeness['missing_fields'].append(f"VALIDATION.{field}")
        
        # Check QUICK_AUDIT
        quick_audit = config.QUICK_AUDIT
        if 'audit_scripts' not in quick_audit:
            completeness['sections_complete'] = False
            completeness['missing_fields'].append("QUICK_AUDIT.audit_scripts")

        ai_validation = config.get_ai_validation_config()
        required_ai_fields = [
            'completeness_threshold',
            'accuracy_threshold',
            'consistency_threshold',
            'actionable_threshold',
            'critical_issues_weight',
            'warning_issues_weight',
            'info_issues_weight',
        ]
        for field in required_ai_fields:
            if field not in ai_validation:
                completeness['sections_complete'] = False
                completeness['missing_fields'].append(f"AI_VALIDATION.{field}")

        return completeness
    
    def generate_recommendations(self, tools_analysis: Dict, config_validation: Dict, completeness: Dict) -> List[str]:
        """Generate recommendations for improving configuration usage."""
        recommendations = []
        seen_recommendations = set()  # Track recommendations to avoid duplicates
        
        # Tool-specific recommendations
        for tool_name, analysis in tools_analysis.items():
            # Skip wrapper scripts - they don't need config since they delegate to other modules
            if analysis.get('is_wrapper_script', False):
                continue
            
            # Check if tool doesn't import config
            if not analysis['imports_config']:
                rec = f"Update {tool_name} to import config module"
                if rec not in seen_recommendations:
                    recommendations.append(rec)
                    seen_recommendations.add(rec)
            
            # Check for hardcoded values
            if analysis['hardcoded_values']:
                rec = f"Replace hardcoded values in {tool_name} with config functions"
                if rec not in seen_recommendations:
                    recommendations.append(rec)
                    seen_recommendations.add(rec)
            
            # Add "Fix issues" recommendation for any remaining issues (excluding config import issues)
            if analysis['issues']:
                # Filter out issues that are already covered by other recommendations
                filtered_issues = []
                for issue in analysis['issues']:
                    # Skip issues about missing config import (already covered above)
                    if 'import config' not in issue.lower() and 'does not import' not in issue.lower():
                        filtered_issues.append(issue)
                
                if filtered_issues:
                    issues_str = ', '.join(filtered_issues)
                    rec = f"Fix issues in {tool_name}: {issues_str}"
                    if rec not in seen_recommendations:
                        recommendations.append(rec)
                        seen_recommendations.add(rec)
        
        # Configuration recommendations
        if config_validation['missing_directories']:
            rec = f"Add missing directories to SCAN_DIRECTORIES or remove them: {', '.join(config_validation['missing_directories'])}"
            if rec not in seen_recommendations:
                recommendations.append(rec)
                seen_recommendations.add(rec)
        
        if not config_validation['config_structure_valid']:
            rec = "Fix configuration structure issues"
            if rec not in seen_recommendations:
                recommendations.append(rec)
                seen_recommendations.add(rec)
        
        if not completeness['sections_complete']:
            rec = f"Add missing configuration fields: {', '.join(completeness['missing_fields'])}"
            if rec not in seen_recommendations:
                recommendations.append(rec)
                seen_recommendations.add(rec)
        
        return recommendations
    
    def run_validation(self) -> Dict:
        """Run the complete configuration validation."""
        logger.info("Starting configuration validation...")
        
        # Scan tools for config usage
        tools_analysis = self.scan_tools_for_config_usage()
        
        # Validate configuration consistency
        config_validation = self.validate_configuration_consistency()
        
        # Check configuration completeness
        completeness = self.check_configuration_completeness()
        
        # Generate recommendations
        recommendations = self.generate_recommendations(tools_analysis, config_validation, completeness)
        
        # Calculate total issues
        validation_issues = len(config_validation.get('issues', []))
        tool_issues = sum(len(t.get('issues', [])) for t in tools_analysis.values())
        completeness_issues = len(completeness.get('missing_fields', []))
        total_issues = validation_issues + tool_issues + completeness_issues
        
        # Compile results in standard format
        results = {
            'summary': {
                'total_issues': total_issues,
                'files_affected': 0  # Not file-based
            },
            'details': {
                'tools_analysis': tools_analysis,
                'validation': config_validation,
                'completeness': completeness,
                'recommendations': recommendations,
                'summary': {
                    'tools_using_config': sum(1 for t in tools_analysis.values() if t['imports_config']),
                    'total_tools': len(tools_analysis),
                    'config_valid': config_validation['config_structure_valid'],
                    'config_complete': completeness['sections_complete'],
                    'total_recommendations': len(recommendations)
                }
            }
        }
        
        return results
    
    def print_validation_report(self, results: Dict):
        """Print a comprehensive validation report."""
        logger.info("="*80)
        logger.info("CONFIGURATION VALIDATION REPORT")
        logger.info("="*80)
        
        # Handle both standard format and legacy format
        if 'details' in results and 'summary' in results:
            # Standard format - summary is at top level, details contain the nested data
            top_summary = results['summary']
            details = results['details']
            nested_summary = details.get('summary', {})
            tools_analysis = details.get('tools_analysis', {})
            config_validation = details.get('validation', {})
            completeness = details.get('completeness', {})
            recommendations = details.get('recommendations', [])
        else:
            # Legacy format
            nested_summary = results.get('summary', {})
            tools_analysis = results.get('tools_analysis', {})
            config_validation = results.get('config_validation', {})
            completeness = results.get('completeness', {})
            recommendations = results.get('recommendations', [])
        
        logger.info(f"SUMMARY:")
        logger.info(f"   Tools using config: {nested_summary.get('tools_using_config', 0)}/{nested_summary.get('total_tools', 0)}")
        logger.info(f"   Configuration valid: {'YES' if nested_summary.get('config_valid', False) else 'NO'}")
        logger.info(f"   Configuration complete: {'YES' if nested_summary.get('config_complete', False) else 'NO'}")
        logger.info(f"   Recommendations: {nested_summary.get('total_recommendations', len(recommendations))}")
        
        # Tool analysis
        logger.info(f"TOOL ANALYSIS:")
        for tool_name, analysis in tools_analysis.items():
            # Skip wrapper scripts in the report - they don't need config
            if analysis.get('is_wrapper_script', False):
                status = "OK"
                logger.info(f"   {status} {tool_name} (wrapper script)")
                continue
            
            # Status logic: OK if imports config and no issues, WARN if has issues or doesn't import config (recommendation), FAIL only for critical issues
            if analysis['imports_config'] and not analysis['issues']:
                status = "OK"
                logger.info(f"   {status} {tool_name}")
            elif analysis['issues']:
                status = "WARN"
                logger.warning(f"   {status} {tool_name}")
            else:
                # Doesn't import config but no issues - this is a recommendation, not an error
                status = "WARN"
                logger.warning(f"   {status} {tool_name} (recommendation: import config module)")
            
            if analysis['config_functions_used']:
                logger.info(f"      Uses: {', '.join(analysis['config_functions_used'])}")
            
            if analysis['hardcoded_values']:
                logger.warning(f"      Hardcoded values: {len(analysis['hardcoded_values'])}")
            
            if analysis['issues']:
                for issue in analysis['issues']:
                    logger.warning(f"      Issue: {issue}")
        
        # Configuration validation
        if config_validation.get('missing_directories'):
            logger.warning(f"MISSING DIRECTORIES:")
            for directory in config_validation['missing_directories']:
                logger.warning(f"   - {directory}")
        
        if config_validation.get('issues'):
            logger.warning(f"CONFIGURATION ISSUES:")
            for issue in config_validation['issues']:
                logger.warning(f"   - {issue}")
        
        # Completeness
        if completeness.get('missing_fields'):
            logger.warning(f"MISSING CONFIGURATION FIELDS:")
            for field in completeness['missing_fields']:
                logger.warning(f"   - {field}")
        
        # Recommendations
        if recommendations:
            logger.info(f"RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info(f"Configuration validation complete!")

def main():
    """Main function to run configuration validation."""
    import sys
    import json
    
    validator = ConfigValidator()
    results = validator.run_validation()
    validator.print_validation_report(results)
    
    # Always output JSON to stdout for wrapper to capture and save via save_tool_result()
    # This matches the pattern used by other tools like analyze_functions
    # The report is printed above for human readability, JSON is for programmatic use
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main() 
