# TOOL_TIER: core

"""
Result format normalization for development tools.

Converts various tool result formats to a standardized structure for consistent
data access across all analysis tools.
"""

from typing import Dict, Any, Optional
from core.logger import get_component_logger

logger = get_component_logger("development_tools")


def normalize_to_standard_format(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize tool result data to standard format.
    
    Standard format structure:
    {
        "summary": {
            "total_issues": int,      # Required: Total issues found (0 if none)
            "files_affected": int,    # Required: Files with issues (0 if not file-based)
            "status": str             # Optional: Overall status
        },
        "files": {                    # Optional: For file-based tools
            "file_path": issue_count
        },
        "details": {                  # Optional: Tool-specific detailed data
            # All original fields preserved here
        }
    }
    
    Args:
        tool_name: Name of the tool (e.g., 'analyze_functions')
        data: Tool result data in any format
        
    Returns:
        Normalized data in standard format
    """
    if not isinstance(data, dict):
        logger.warning(f"Data for {tool_name} is not a dict, returning empty standard format")
        return _create_empty_standard_format()
    
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            logger.debug(f"{tool_name} already in standard format")
            return data
    
    # Route to appropriate converter based on tool name and data structure
    converter = _get_converter(tool_name, data)
    if converter:
        # Check if converter needs tool_name (only _normalize_fallback does)
        import inspect
        sig = inspect.signature(converter)
        if len(sig.parameters) == 2:
            normalized = converter(tool_name, data)
        else:
            normalized = converter(data)
        logger.debug(f"Normalized {tool_name} from {converter.__name__}")
        return normalized
    
    # Fallback: try to extract basic info and preserve all data in details
    logger.debug(f"Using fallback normalization for {tool_name}")
    return _normalize_fallback(tool_name, data)


def _get_converter(tool_name: str, data: Dict[str, Any]) -> Optional[callable]:
    """Get the appropriate converter function for a tool."""
    
    # Format 1: File-based analysis tools
    if tool_name in ('analyze_ascii_compliance', 'analyze_heading_numbering', 
                     'analyze_missing_addresses', 'analyze_unconverted_links'):
        if 'file_count' in data and 'total_issues' in data:
            return _normalize_file_based
    
    # Format 2: Path drift
    if tool_name == 'analyze_path_drift':
        if 'total_issues' in data and 'detailed_issues' in data:
            return _normalize_path_drift
    
    # Format 3: Unused imports
    if tool_name == 'analyze_unused_imports':
        if 'total_unused' in data or 'files_with_issues' in data:
            return _normalize_unused_imports
    
    # Format 4: Documentation sync (aggregator)
    if tool_name == 'analyze_documentation_sync':
        if 'status' in data and 'total_issues' in data:
            return _normalize_documentation_sync
    
    # Format 5: Functions analysis
    if tool_name == 'analyze_functions':
        if 'total_functions' in data:
            return _normalize_functions
    
    # Format 6: Error handling
    if tool_name == 'analyze_error_handling':
        if 'total_functions' in data or 'functions_missing_error_handling' in data:
            return _normalize_error_handling
    
    # Format 7: Function registry
    if tool_name == 'analyze_function_registry':
        if 'totals' in data or 'missing' in data:
            return _normalize_function_registry
    
    # Format 8: Legacy references
    if tool_name == 'analyze_legacy_references':
        if 'files_with_issues' in data:
            return _normalize_legacy_references
    
    # Format 9: Test markers
    if tool_name == 'analyze_test_markers':
        if 'files_needing_markers' in data:
            return _normalize_test_markers
    
    # Format 10: Module dependencies
    if tool_name == 'analyze_module_dependencies':
        if 'files_scanned' in data or 'missing_dependencies' in data:
            return _normalize_module_dependencies
    
    # Format 11: Package exports
    if tool_name == 'analyze_package_exports':
        if 'packages' in data or 'summary' in data:
            return _normalize_package_exports
    
    # Format 12: Pattern tools (function patterns, dependency patterns)
    if tool_name in ('analyze_function_patterns', 'analyze_dependency_patterns'):
        return _normalize_pattern_tools
    
    # Format 13: Documentation analysis
    if tool_name == 'analyze_documentation':
        if 'artifacts' in data or 'duplicates' in data or 'section_overlaps' in data:
            return _normalize_documentation
    
    # Format 14: AI work validation
    if tool_name == 'analyze_ai_work':
        return _normalize_ai_work
    
    # Fallback for unknown formats
    return _normalize_fallback

    # Format 11: Test coverage
    if tool_name == 'analyze_test_coverage':
        if 'overall' in data or 'modules' in data:
            return _normalize_test_coverage
    
    # Format 12: Config analysis
    if tool_name == 'analyze_config':
        if 'validation' in data or 'tool_analysis' in data:
            return _normalize_config
    
    # Format 13: Pattern/import tools (no issues, just data)
    if tool_name in ('analyze_function_patterns', 'analyze_module_imports', 
                     'analyze_dependency_patterns'):
        return _normalize_pattern_tools
    
    # Format 14: Documentation analysis
    if tool_name == 'analyze_documentation':
        if 'missing' in data or 'duplicates' in data or 'placeholders' in data:
            return _normalize_documentation
    
    # Format 15: AI work (string output)
    if tool_name == 'analyze_ai_work':
        return _normalize_ai_work
    
    return None


def _create_empty_standard_format() -> Dict[str, Any]:
    """Create an empty standard format structure."""
    return {
        'summary': {
            'total_issues': 0,
            'files_affected': 0
        },
        'details': {}
    }


def _normalize_file_based(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 1: File-based analysis tools."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': data.get('total_issues', 0),
        'files_affected': data.get('file_count', 0)
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve files dict if present
    if 'files' in data:
        result['files'] = data['files']
    
    # Move all other fields to details
    for key, value in data.items():
        if key not in ('files', 'file_count', 'total_issues'):
            result['details'][key] = value
    
    return result


def _normalize_path_drift(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 2: Path drift analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    files = data.get('files', {})
    summary = {
        'total_issues': data.get('total_issues', 0),
        'files_affected': len(files) if isinstance(files, dict) else 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve files dict
    if files:
        result['files'] = files
    
    # Move detailed_issues to details
    if 'detailed_issues' in data:
        result['details']['detailed_issues'] = data['detailed_issues']
    
    # Move all other fields to details
    for key, value in data.items():
        if key not in ('files', 'total_issues', 'detailed_issues'):
            result['details'][key] = value
    
    return result


def _normalize_unused_imports(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 3: Unused imports."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': data.get('total_unused', 0),
        'files_affected': data.get('files_with_issues', 0),
        'status': data.get('status', 'GOOD')
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Move category data to details
    if 'by_category' in data:
        result['details']['by_category'] = data['by_category']
    
    if 'files_scanned' in data:
        result['details']['files_scanned'] = data['files_scanned']
    
    # Move all other fields to details
    for key, value in data.items():
        if key not in ('total_unused', 'files_with_issues', 'status', 'by_category', 'files_scanned'):
            result['details'][key] = value
    
    return result


def _normalize_documentation_sync(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 4: Documentation sync (aggregator tool)."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': data.get('total_issues', 0),
        'files_affected': len(data.get('path_drift_files', [])) if isinstance(data.get('path_drift_files'), list) else 0,
        'status': data.get('status', 'UNKNOWN')
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details (this is an aggregator)
    for key, value in data.items():
        if key not in ('total_issues', 'status'):
            result['details'][key] = value
    
    return result


def _normalize_functions(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 5: Functions analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Calculate total_issues from complexity counts
    total_issues = (
        data.get('moderate_complexity', 0) +
        data.get('high_complexity', 0) +
        data.get('critical_complexity', 0) +
        data.get('undocumented', 0)
    )
    
    summary = {
        'total_issues': total_issues,
        'files_affected': 0  # Not file-based
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_error_handling(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 6: Error handling analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': data.get('functions_missing_error_handling', 0),
        'files_affected': 0  # Not file-based, but could calculate from missing_error_handling list
    }
    
    # Calculate files_affected from missing_error_handling list if present
    if 'missing_error_handling' in data and isinstance(data['missing_error_handling'], list):
        unique_files = set()
        for item in data['missing_error_handling']:
            if isinstance(item, dict) and 'file' in item:
                unique_files.add(item['file'])
        summary['files_affected'] = len(unique_files)
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_function_registry(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 7: Function registry analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Calculate total_issues from missing/extra items
    missing = data.get('missing', {})
    extra = data.get('extra', {})
    
    missing_count = missing.get('count', 0) if isinstance(missing, dict) else (missing if isinstance(missing, int) else 0)
    extra_count = extra.get('count', 0) if isinstance(extra, dict) else (extra if isinstance(extra, int) else 0)
    
    summary = {
        'total_issues': missing_count + extra_count,
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_legacy_references(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 8: Legacy references."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': data.get('legacy_markers', 0),
        'files_affected': data.get('files_with_issues', 0)
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_test_markers(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 9: Test markers."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Use missing_count (number of tests missing markers) as total_issues
    missing_count = data.get('missing_count', 0)
    missing_list = data.get('missing', [])
    
    # Count unique files with missing markers
    files_affected = 0
    if missing_list:
        files_affected = len(set(item.get('file', '') for item in missing_list if item.get('file')))
    elif data.get('files_needing_markers'):
        files_affected = data.get('files_needing_markers', 0)
    
    summary = {
        'total_issues': missing_count,
        'files_affected': files_affected
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_module_dependencies(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 10: Module dependencies."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    missing_deps = data.get('missing_dependencies', 0)
    missing_sections = len(data.get('missing_sections', [])) if isinstance(data.get('missing_sections'), list) else 0
    
    summary = {
        'total_issues': missing_deps + missing_sections,
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_test_coverage(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 11: Test coverage."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Coverage doesn't have "issues" in the traditional sense
    # Calculate gaps from overall coverage
    overall = data.get('overall', {})
    coverage = overall.get('coverage', 100) if isinstance(overall, dict) else 100
    missed = overall.get('missed', 0) if isinstance(overall, dict) else 0
    
    summary = {
        'total_issues': missed,  # Lines not covered
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 12: Config analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Count validation issues
    validation = data.get('validation', {})
    config_validation = data.get('config_validation', {})
    tool_analysis = data.get('tools_analysis', {})
    completeness = data.get('completeness', {})
    
    issues = 0
    if isinstance(validation, dict):
        issues += len(validation.get('errors', []))
        issues += len(validation.get('warnings', []))
    if isinstance(config_validation, dict):
        issues += len(config_validation.get('issues', []))
    if isinstance(tool_analysis, dict):
        if isinstance(tool_analysis, list):
            issues += sum(len(t.get('issues', [])) for t in tool_analysis if isinstance(t, dict))
        else:
            issues += sum(len(t.get('issues', [])) for t in tool_analysis.values() if isinstance(t, dict))
    if isinstance(completeness, dict):
        issues += len(completeness.get('missing_fields', []))
    
    summary = {
        'total_issues': issues,
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_pattern_tools(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 13: Pattern/import tools (no issues, just data)."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary = {
        'total_issues': 0,
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_documentation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 14: Documentation analysis."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # Aggregate issues from missing, duplicates, placeholders, artifacts
    missing_count = len(data.get('missing', []))
    duplicates_count = len(data.get('duplicates', []))
    placeholders_count = len(data.get('placeholders', []))
    artifacts_count = len(data.get('artifacts', []))
    
    summary = {
        'total_issues': missing_count + duplicates_count + placeholders_count + artifacts_count,
        'files_affected': 0
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_ai_work(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 15: AI work validation (string output)."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    # AI work typically has string output, wrap it
    output = data.get('output', '')
    
    # Try to extract status from output
    status = 'UNKNOWN'
    if isinstance(output, str):
        if 'POOR' in output:
            status = 'POOR'
        elif 'GOOD' in output:
            status = 'GOOD'
        elif 'NEEDS ATTENTION' in output or 'FAIR' in output:
            status = 'NEEDS_ATTENTION'
    
    summary = {
        'total_issues': 0 if status in ('GOOD', 'UNKNOWN') else 1,
        'files_affected': 0,
        'status': status
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        result['details'][key] = value
    
    return result


def _normalize_package_exports(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Format 11: Package exports."""
    # Check if already in standard format
    if 'summary' in data and isinstance(data.get('summary'), dict):
        if 'total_issues' in data['summary'] and 'files_affected' in data['summary']:
            return data
    
    # Legacy format normalization
    summary_data = data.get('summary', {})
    
    # Calculate total issues (missing + unnecessary exports)
    total_missing = summary_data.get('total_missing_exports', 0)
    total_unnecessary = summary_data.get('total_unnecessary_exports', 0)
    total_issues = total_missing + total_unnecessary
    
    # Count packages with issues
    packages = data.get('packages', {})
    packages_with_issues = sum(
        1 for pkg, report in packages.items()
        if isinstance(report, dict) and (
            report.get('missing_exports') or report.get('potentially_unnecessary')
        )
    )
    
    summary = {
        'total_issues': total_issues,
        'files_affected': packages_with_issues,  # Packages are like "files" here
        'status': 'NEEDS_ATTENTION' if total_issues > 0 else 'GOOD'
    }
    
    result = {
        'summary': summary,
        'details': data  # Preserve all original data
    }
    
    return result


def _normalize_fallback(tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback normalization when no specific converter matches."""
    # Try to extract basic info
    total_issues = 0
    files_affected = 0
    
    # Look for common issue count fields
    for key in ('total_issues', 'issues', 'count', 'total', 'errors', 'warnings'):
        if key in data:
            value = data[key]
            if isinstance(value, int):
                total_issues = value
                break
            elif isinstance(value, dict) and 'count' in value:
                total_issues = value['count']
                break
    
    # Look for file count fields
    for key in ('files_affected', 'file_count', 'files_with_issues', 'files'):
        if key in data:
            value = data[key]
            if isinstance(value, int):
                files_affected = value
                break
            elif isinstance(value, (dict, list)):
                files_affected = len(value)
                break
    
    summary = {
        'total_issues': total_issues,
        'files_affected': files_affected
    }
    
    result = {
        'summary': summary,
        'details': {}
    }
    
    # Preserve all original data in details
    for key, value in data.items():
        if key not in ('total_issues', 'issues', 'count', 'total', 'files_affected', 'file_count', 'files_with_issues'):
            result['details'][key] = value
    
    return result

