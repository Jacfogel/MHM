"""
Data Freshness Audit - Systematic verification of stale data prevention.

This module provides utilities to audit and verify that all data loading paths
properly filter out deleted files and use current audit data.

WHAT IT DOES:
1. Checks all JSON cache files for references to known deleted files
2. Performs static analysis to find code patterns that might process file paths
   without existence checks (these are warnings, not necessarily bugs)
3. Automatically checks generated reports (consolidated_report.md, AI_STATUS.md, etc.)
   for references to deleted files

WHAT THE RESULTS MEAN:
- Cache file issues: ACTUAL PROBLEMS - deleted files found in cache files
- Code pattern issues: WARNINGS - potential code paths that might need review
  (many are false positives where data is already filtered upstream)
- Report issues: ACTUAL PROBLEMS - deleted files found in generated reports

Usage:
    from development_tools.shared.service.data_freshness_audit import audit_data_freshness
    issues = audit_data_freshness(project_root)
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Known deleted files that should NOT appear in any reports
KNOWN_DELETED_FILES = {
    'development_tools/shared/operations.py',
    'development_docs/SESSION_SUMMARY_2025-12-07.md',
}


def find_all_json_cache_files(project_root: Path) -> List[Path]:
    """Find all JSON cache and results files."""
    cache_files = []
    
    # Standard results files
    cache_files.append(project_root / 'development_tools' / 'reports' / 'analysis_detailed_results.json')
    
    # Tool-specific cache files
    cache_dirs = [
        project_root / 'development_tools' / 'imports' / 'jsons',
        project_root / 'development_tools' / 'imports',
        project_root / 'development_tools' / 'docs' / 'jsons',
        project_root / 'development_tools' / 'docs',
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            # Look for cache files (usually start with .)
            for cache_file in cache_dir.glob('*.json'):
                if cache_file.name.startswith('.'):
                    cache_files.append(cache_file)
    
    return [f for f in cache_files if f.exists()]


def check_cache_file_for_deleted_files(cache_file: Path, project_root: Path, deleted_files: Set[str]) -> List[Tuple[str, str]]:
    """
    Check a cache file for references to deleted files.
    
    Returns:
        List of (file_path, issue_description) tuples
    """
    issues = []
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Recursively search for file paths
        def find_file_paths(obj, path=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    # Check if key looks like a file path
                    if isinstance(key, str) and ('/' in key or '\\' in key or key.endswith('.py') or key.endswith('.md')):
                        # Normalize path
                        normalized = key.replace('\\', '/')
                        if normalized in deleted_files:
                            issues.append((normalized, f"Found in cache file {cache_file.name} at path: {current_path}"))
                    find_file_paths(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_file_paths(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                # Check if string looks like a file path
                if ('/' in obj or '\\' in obj) and (obj.endswith('.py') or obj.endswith('.md')):
                    normalized = obj.replace('\\', '/')
                    if normalized in deleted_files:
                        issues.append((normalized, f"Found in cache file {cache_file.name} at path: {path}"))
    
    except Exception as e:
        issues.append(('', f"Error reading cache file {cache_file.name}: {e}"))
    
    return issues


def check_tool_results_for_deleted_files(project_root: Path, deleted_files: Set[str]) -> List[Tuple[str, str]]:
    """Check all tool result JSON files for deleted file references."""
    issues = []
    
    # Check standard results file
    results_file = project_root / 'development_tools' / 'reports' / 'analysis_detailed_results.json'
    if results_file.exists():
        cache_issues = check_cache_file_for_deleted_files(results_file, project_root, deleted_files)
        issues.extend(cache_issues)
    
    # Check tool-specific cache files
    cache_files = find_all_json_cache_files(project_root)
    for cache_file in cache_files:
        cache_issues = check_cache_file_for_deleted_files(cache_file, project_root, deleted_files)
        issues.extend(cache_issues)
    
    return issues


def verify_file_existence_checks(project_root: Path) -> List[str]:
    """
    Verify that code paths that process file paths check for file existence.
    
    This is a static analysis helper - checks for patterns in code.
    """
    issues = []
    
    # Files to check
    service_files = [
        project_root / 'development_tools' / 'shared' / 'service' / 'data_loading.py',
        project_root / 'development_tools' / 'shared' / 'service' / 'report_generation.py',
        project_root / 'development_tools' / 'shared' / 'service' / 'tool_wrappers.py',
    ]
    
    for service_file in service_files:
        if not service_file.exists():
            continue
        
        content = service_file.read_text(encoding='utf-8')
        
        # Check for patterns that process file paths without existence checks
        # Pattern 1: Iterating over file paths from data without checking existence
        if 'for file_path' in content or 'for file_path_str' in content:
            # Look for the pattern: for file_path in data.items() or similar
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if ('for file_path' in line or 'for file_path_str' in line) and 'in' in line:
                    # Check if next few lines have file existence check
                    next_lines = '\n'.join(lines[i:i+10])
                    if 'file_path.exists()' not in next_lines and 'file_path_obj.exists()' not in next_lines:
                        # Check if it's in extract_files_with_issue_counts (which we fixed)
                        if 'extract_files_with_issue_counts' not in '\n'.join(lines[max(0, i-5):i]):
                            issues.append(f"{service_file.name}:{i+1} - File path iteration without existence check")
    
    return issues


def check_generated_reports_for_deleted_files(project_root: Path, deleted_files: Set[str]) -> List[Tuple[str, str]]:
    """Check generated reports for references to deleted files."""
    issues = []
    
    # Reports to check
    reports = [
        project_root / 'development_tools' / 'consolidated_report.md',
        project_root / 'development_tools' / 'AI_STATUS.md',
        project_root / 'development_tools' / 'AI_PRIORITIES.md',
        project_root / 'development_docs' / 'UNUSED_IMPORTS_REPORT.md',
    ]
    
    for report_path in reports:
        if not report_path.exists():
            continue
        
        try:
            content = report_path.read_text(encoding='utf-8')
            for deleted_file in deleted_files:
                # Check for file name (with or without path)
                file_name = Path(deleted_file).name
                if file_name in content or deleted_file in content:
                    # Check if it's actually a reference (not just part of another word)
                    # Look for patterns like "operations.py" or "development_tools/shared/operations.py"
                    import re
                    patterns = [
                        rf'\b{re.escape(file_name)}\b',  # Word boundary for filename
                        rf'\b{re.escape(deleted_file)}\b',  # Word boundary for full path
                    ]
                    for pattern in patterns:
                        if re.search(pattern, content):
                            issues.append((deleted_file, f"Found in {report_path.name}"))
                            break
        except Exception as e:
            issues.append(('', f"Error reading {report_path.name}: {e}"))
    
    return issues


def audit_data_freshness(project_root: Path, deleted_files: Set[str] = None) -> Dict[str, any]:
    """
    Comprehensive audit of data freshness mechanisms.
    
    Args:
        project_root: Path to project root
        deleted_files: Set of deleted file paths (normalized with forward slashes)
                      If None, uses KNOWN_DELETED_FILES
    
    Returns:
        Dict with audit results
    """
    if deleted_files is None:
        deleted_files = KNOWN_DELETED_FILES
    
    project_root = Path(project_root).resolve()
    
    results = {
        'cache_file_issues': [],
        'report_issues': [],
        'code_pattern_issues': [],
        'summary': {}
    }
    
    # 1. Check cache files for deleted file references
    cache_issues = check_tool_results_for_deleted_files(project_root, deleted_files)
    results['cache_file_issues'] = cache_issues
    
    # 2. Check generated reports for deleted file references
    report_issues = check_generated_reports_for_deleted_files(project_root, deleted_files)
    results['report_issues'] = report_issues
    
    # 3. Verify code patterns (static analysis)
    code_issues = verify_file_existence_checks(project_root)
    results['code_pattern_issues'] = code_issues
    
    # 4. Summary
    results['summary'] = {
        'total_cache_issues': len(cache_issues),
        'total_report_issues': len(report_issues),
        'total_code_issues': len(code_issues),
        'deleted_files_checked': list(deleted_files),
        'cache_files_checked': len(find_all_json_cache_files(project_root))
    }
    
    return results


if __name__ == '__main__':
    import sys
    project_root = Path(__file__).parent.parent.parent.parent
    results = audit_data_freshness(project_root)
    
    print("=" * 70)
    print("DATA FRESHNESS AUDIT RESULTS")
    print("=" * 70)
    print("\nWHAT THIS AUDIT DOES:")
    print("  1. Checks JSON cache files for references to deleted files")
    print("  2. Checks generated reports (consolidated_report.md, AI_STATUS.md, etc.)")
    print("  3. Performs static code analysis (warnings only, many are false positives)")
    print("\nSummary:")
    print(f"  - Cache files checked: {results['summary']['cache_files_checked']}")
    print(f"  - Deleted files checked: {len(results['summary']['deleted_files_checked'])}")
    print(f"  - Cache file issues: {results['summary']['total_cache_issues']} (ACTUAL PROBLEMS)")
    print(f"  - Report issues: {results['summary']['total_report_issues']} (ACTUAL PROBLEMS)")
    print(f"  - Code pattern issues: {results['summary']['total_code_issues']} (WARNINGS - may be false positives)")
    
    if results['cache_file_issues']:
        print(f"\n[ERROR] Cache File Issues ({len(results['cache_file_issues'])}):")
        for file_path, issue in results['cache_file_issues']:
            print(f"  - {file_path}: {issue}")
    
    if results['report_issues']:
        print(f"\n[ERROR] Generated Report Issues ({len(results['report_issues'])}):")
        for file_path, issue in results['report_issues']:
            print(f"  - {file_path}: {issue}")
    
    if results['code_pattern_issues']:
        print(f"\n[WARNING] Code Pattern Issues ({len(results['code_pattern_issues'])}):")
        print("  (These are warnings - many are false positives where data is already filtered)")
        for issue in results['code_pattern_issues']:
            print(f"  - {issue}")
    
    total_actual_issues = results['summary']['total_cache_issues'] + results['summary']['total_report_issues']
    if total_actual_issues == 0:
        print("\n[SUCCESS] No actual issues found! Data freshness mechanisms appear to be working correctly.")
    else:
        print(f"\n[FAILURE] Found {total_actual_issues} actual issue(s) that need to be fixed.")
    
    sys.exit(0 if total_actual_issues == 0 else 1)
