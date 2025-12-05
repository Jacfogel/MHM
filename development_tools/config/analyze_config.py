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
import json
from datetime import datetime

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
                'issues': []
            }
            
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
            
            # Check for issues
            if not analysis['imports_config']:
                analysis['issues'].append("Does not import config module")
            
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
        
        # Tool-specific recommendations
        for tool_name, analysis in tools_analysis.items():
            if not analysis['imports_config']:
                recommendations.append(f"Update {tool_name} to import config module")
            
            if analysis['hardcoded_values']:
                recommendations.append(f"Replace hardcoded values in {tool_name} with config functions")
            
            if analysis['issues']:
                recommendations.append(f"Fix issues in {tool_name}: {', '.join(analysis['issues'])}")
        
        # Configuration recommendations
        if config_validation['missing_directories']:
            recommendations.append(f"Add missing directories to SCAN_DIRECTORIES or remove them: {', '.join(config_validation['missing_directories'])}")
        
        if not config_validation['config_structure_valid']:
            recommendations.append("Fix configuration structure issues")
        
        if not completeness['sections_complete']:
            recommendations.append(f"Add missing configuration fields: {', '.join(completeness['missing_fields'])}")
        
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
        
        # Compile results
        results = {
            'tools_analysis': tools_analysis,
            'config_validation': config_validation,
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
        
        return results
    
    def print_validation_report(self, results: Dict):
        """Print a comprehensive validation report."""
        logger.info("="*80)
        logger.info("CONFIGURATION VALIDATION REPORT")
        logger.info("="*80)
        
        summary = results['summary']
        logger.info(f"SUMMARY:")
        logger.info(f"   Tools using config: {summary['tools_using_config']}/{summary['total_tools']}")
        logger.info(f"   Configuration valid: {'YES' if summary['config_valid'] else 'NO'}")
        logger.info(f"   Configuration complete: {'YES' if summary['config_complete'] else 'NO'}")
        logger.info(f"   Recommendations: {summary['total_recommendations']}")
        
        # Tool analysis
        logger.info(f"TOOL ANALYSIS:")
        for tool_name, analysis in results['tools_analysis'].items():
            status = "OK" if analysis['imports_config'] and not analysis['issues'] else "WARN" if analysis['issues'] else "FAIL"
            if status == "OK":
                logger.info(f"   {status} {tool_name}")
            elif status == "WARN":
                logger.warning(f"   {status} {tool_name}")
            else:
                logger.error(f"   {status} {tool_name}")
            
            if analysis['config_functions_used']:
                logger.info(f"      Uses: {', '.join(analysis['config_functions_used'])}")
            
            if analysis['hardcoded_values']:
                logger.warning(f"      Hardcoded values: {len(analysis['hardcoded_values'])}")
            
            if analysis['issues']:
                for issue in analysis['issues']:
                    logger.warning(f"      Issue: {issue}")
        
        # Configuration validation
        config_validation = results['config_validation']
        if config_validation['missing_directories']:
            logger.warning(f"MISSING DIRECTORIES:")
            for directory in config_validation['missing_directories']:
                logger.warning(f"   - {directory}")
        
        if config_validation['issues']:
            logger.warning(f"CONFIGURATION ISSUES:")
            for issue in config_validation['issues']:
                logger.warning(f"   - {issue}")
        
        # Completeness
        completeness = results['completeness']
        if completeness['missing_fields']:
            logger.warning(f"MISSING CONFIGURATION FIELDS:")
            for field in completeness['missing_fields']:
                logger.warning(f"   - {field}")
        
        # Recommendations
        if results['recommendations']:
            logger.info(f"RECOMMENDATIONS:")
            for i, rec in enumerate(results['recommendations'], 1):
                logger.info(f"   {i}. {rec}")
        
        logger.info(f"Configuration validation complete!")

def main():
    """Main function to run configuration validation."""
    validator = ConfigValidator()
    results = validator.run_validation()
    validator.print_validation_report(results)
    
    # Save results with proper headers
    results_file = validator.ai_tools_dir / 'config' / 'jsons' / 'analyze_config_results.json'
    try:
        # Add generation headers to results
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamp_iso = datetime.now().isoformat()
        results_with_headers = {
            'generated_by': 'analyze_config.py - Configuration Validation Tool',
            'last_generated': timestamp_str,
            'source': 'python development_tools/config/analyze_config.py',
            'note': 'This file is auto-generated. Do not edit manually.',
            'timestamp': timestamp_iso,
            'validation_results': results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_with_headers, f, indent=2)
        logger.info(f"Results saved to: {results_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

if __name__ == "__main__":
    main() 
