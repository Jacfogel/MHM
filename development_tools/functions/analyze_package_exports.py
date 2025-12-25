#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Package Exports Audit Script

Systematically identifies what should be exported at package level
based on:
1. Actual imports across the codebase (what's actually used)
2. Public API items (not starting with `_`)
3. Cross-module usage patterns
4. FUNCTION_REGISTRY_DETAIL.md documented functions
5. Module-level public functions/classes

Usage:
    python functions/analyze_package_exports.py.py
    python functions/analyze_package_exports.py.py --package core
    python functions/analyze_package_exports.py.py --package communication
"""

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
# Script is at: development_tools/functions/analyze_package_exports.py
# So we need to go up 2 levels to get to project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from .. import config  # Go up one level from functions/ to development_tools/
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file

from core.logger import get_component_logger

# Load external config on module import
config.load_external_config()

# Get configuration
AUDIT_EXPORTS_CONFIG = config.get_analyze_package_exports_config()
EXPORT_PATTERNS = AUDIT_EXPORTS_CONFIG.get('export_patterns', [])
EXPECTED_EXPORTS = AUDIT_EXPORTS_CONFIG.get('expected_exports', {})

logger = get_component_logger("development_tools")


def extract_imports_from_file(file_path: str) -> Dict[str, List[str]]:
    """Extract all imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        imports = {
            'from_imports': [],  # from package.module import item
            'direct_imports': [],  # import package
            'module_items': []  # Functions/classes defined in module (module-level only)
        }
        
        # Process all nodes for imports (these can appear anywhere)
        for node in ast.walk(tree):
            # From imports: from package.module import item
            if isinstance(node, ast.ImportFrom) and node.module:
                module_parts = node.module.split('.')
                for alias in node.names:
                    imports['from_imports'].append({
                        'module': node.module,
                        'name': alias.name,
                        'asname': alias.asname if alias.asname else alias.name,
                        'package': module_parts[0] if module_parts else None
                    })
            
            # Direct imports: import package
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module_parts = alias.name.split('.')
                    imports['direct_imports'].append({
                        'module': alias.name,
                        'asname': alias.asname if alias.asname else alias.name,
                        'package': module_parts[0] if module_parts else None
                    })
        
        # Only process module-level definitions (not methods inside classes)
        # Iterate over the module body directly to get top-level definitions only
        def process_node(node: ast.AST, is_module_level: bool = True):
            """Recursively process nodes, tracking if we're at module level."""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only include if at module level and public
                if is_module_level and node.name and not node.name.startswith('_'):
                    imports['module_items'].append({
                        'name': node.name,
                        'type': 'function'
                    })
                # Don't recurse into function bodies - we only care about definitions
            elif isinstance(node, ast.ClassDef):
                # Include class if at module level and public
                if is_module_level and node.name and not node.name.startswith('_'):
                    imports['module_items'].append({
                        'name': node.name,
                        'type': 'class'
                    })
                # Process class body but mark that we're no longer at module level
                for item in node.body:
                    process_node(item, is_module_level=False)
            elif isinstance(node, (ast.Module, ast.If, ast.Try, ast.With, ast.For, ast.While)):
                # Process child nodes at same level
                for child in node.body if hasattr(node, 'body') else []:
                    process_node(child, is_module_level)
                # Process else/except/finally blocks if present
                if hasattr(node, 'orelse') and node.orelse:
                    for child in node.orelse:
                        process_node(child, is_module_level)
                if hasattr(node, 'handlers') and node.handlers:
                    for handler in node.handlers:
                        if hasattr(handler, 'body'):
                            for child in handler.body:
                                process_node(child, is_module_level)
                if hasattr(node, 'finalbody') and node.finalbody:
                    for child in node.finalbody:
                        process_node(child, is_module_level)
        
        # Process the module body
        for node in tree.body:
            process_node(node, is_module_level=True)
        
        return imports
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")
        return {'from_imports': [], 'direct_imports': [], 'module_items': []}


def scan_package_modules(package_name: str) -> Dict[str, List[str]]:
    """Scan all modules in a package and extract public API items."""
    package_path = project_root / package_name
    
    if not package_path.exists() or not package_path.is_dir():
        return {}
    
    package_api = defaultdict(list)
    
    for py_file in package_path.rglob('*.py'):
        # Skip __init__.py for now
        if py_file.name == '__init__.py':
            continue
        
        # Skip generated files
        if should_exclude_file(str(py_file), 'analysis', 'production'):
            continue
        
        # Skip generated UI classes (ui.generated module)
        # These are auto-generated from .ui files and not intended for direct import
        if 'generated' in str(py_file) or 'generated' in str(py_file.parent):
            continue
        
        rel_path = py_file.relative_to(package_path.parent)
        module_path = str(rel_path).replace('\\', '/').replace('/', '.').replace('.py', '')
        
        imports = extract_imports_from_file(str(py_file))
        
        for item in imports['module_items']:
            package_api[module_path].append(item['name'])
    
    return dict(package_api)


def analyze_imports_for_package(package_name: str) -> Dict[str, Dict]:
    """Analyze what's actually imported from a package across the codebase."""
    usage_stats = defaultdict(lambda: {
        'import_count': 0,
        'import_locations': [],
        'import_types': set(),  # 'from_import', 'direct_import'
        'module_path': None
    })
    
    # Scan all Python files
    for py_file in project_root.rglob('*.py'):
        if should_exclude_file(str(py_file), 'analysis', 'production'):
            continue
        
        # Skip __pycache__ and test data directories
        if '__pycache__' in str(py_file) or 'pytest-of-' in str(py_file):
            continue
        
        imports = extract_imports_from_file(str(py_file))
        
        rel_path = py_file.relative_to(project_root)
        file_key = str(rel_path).replace('\\', '/')
        
        # Check from_imports
        for imp in imports['from_imports']:
            if imp['package'] == package_name:
                module_parts = imp['module'].split('.')
                
                # If importing from package directly or subpackage
                if len(module_parts) > 1 and module_parts[0] == package_name:
                    # Extract what's being imported
                    item_name = imp['asname']
                    module_path = imp['module']
                    
                    if item_name not in usage_stats:
                        usage_stats[item_name]['module_path'] = module_path
                    
                    usage_stats[item_name]['import_count'] += 1
                    usage_stats[item_name]['import_locations'].append(file_key)
                    usage_stats[item_name]['import_types'].add('from_import')
        
        # Check direct imports (import package)
        for imp in imports['direct_imports']:
            if imp['package'] == package_name and '.' not in imp['module']:
                # Direct package import
                usage_stats[imp['asname']]['import_count'] += 1
                usage_stats[item_name]['import_locations'].append(file_key)
                usage_stats[item_name]['import_types'].add('direct_import')
    
    # Convert sets to lists for JSON serialization
    result = {}
    for name, stats in usage_stats.items():
        result[name] = {
            'import_count': stats['import_count'],
            'import_locations': stats['import_locations'],
            'import_types': list(stats['import_types']),
            'module_path': stats['module_path']
        }
    
    return result


def check_current_exports(package_name: str) -> Set[str]:
    """Check what's currently exported in package __init__.py."""
    init_file = project_root / package_name / '__init__.py'
    
    if not init_file.exists():
        return set()
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract __all__ list
        tree = ast.parse(content, filename=str(init_file))
        exports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    exports.add(elt.value)
                                elif hasattr(ast, 'Str') and isinstance(elt, ast.Str):
                                    # Python < 3.8 compatibility
                                    exports.add(elt.s)
        
        # Also check what's imported at module level (even if not in __all__)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module_parts = node.module.split('.')
                if len(module_parts) > 1 and module_parts[0] == package_name:
                    # This is a re-export from submodule
                    for alias in node.names:
                        exports.add(alias.name if not alias.asname else alias.asname)
        
        return exports
    except Exception as e:
        logger.warning(f"Could not parse {init_file}: {e}")
        return set()


def parse_function_registry() -> Dict[str, Set[str]]:
    """Parse FUNCTION_REGISTRY_DETAIL.md to find documented public functions."""
    registry_file = project_root / 'development_docs' / 'FUNCTION_REGISTRY_DETAIL.md'
    
    if not registry_file.exists():
        return {}
    
    package_functions = defaultdict(set)
    
    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for function definitions in markdown
        # Pattern: `function_name` or - `function_name` or **function_name**
        function_pattern = r'[`*-]\s*(?:`)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)'
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            
            # Try to find package context (look for path indicators before the match)
            context_start = max(0, match.start() - 200)
            context = content[context_start:match.start()]
            
            # Extract package name from path references
            package_match = re.search(r'`([a-z_]+)/[^`]+\.py`', context)
            if package_match:
                package = package_match.group(1)
                package_functions[package].add(func_name)
        
        return dict(package_functions)
    except Exception as e:
        logger.warning(f"Could not parse function registry: {e}")
        return {}


def generate_audit_report(package_name: str) -> Dict:
    """Generate comprehensive audit report for a package."""
    logger.info(f"{'='*80}")
    logger.info(f"AUDITING PACKAGE: {package_name}")
    logger.info(f"{'='*80}")
    
    # 1. Check current exports
    current_exports = check_current_exports(package_name)
    logger.info(f"[1/5] Current exports: {len(current_exports)} items")
    
    # 2. Analyze actual imports
    logger.info(f"[2/5] Analyzing imports across codebase...")
    import_usage = analyze_imports_for_package(package_name)
    logger.info(f"   Found {len(import_usage)} unique items imported")
    
    # 3. Scan package modules for public API
    logger.info(f"[3/5] Scanning package modules for public API...")
    package_api = scan_package_modules(package_name)
    all_package_items = set()
    for module_items in package_api.values():
        all_package_items.update(module_items)
    logger.info(f"   Found {len(all_package_items)} public items in package")
    
    # 4. Check function registry
    logger.info(f"[4/5] Checking FUNCTION_REGISTRY_DETAIL.md...")
    registry_functions = parse_function_registry()
    registry_items = registry_functions.get(package_name, set())
    logger.info(f"   Found {len(registry_items)} items in registry")
    
    # 5. Identify what should be exported
    logger.info(f"[5/5] Identifying recommended exports...")
    
    # Items that should be exported:
    should_export = set()
    
    # Items imported from multiple modules (cross-module usage)
    cross_module_items = {
        name: stats for name, stats in import_usage.items()
        if stats['import_count'] >= 2
    }
    
    # Items in function registry (documented public API)
    # But only include items that are actually module-level (not instance methods)
    # Filter registry items to only those that are module-level or actually imported
    registry_items_module_level = {
        item for item in registry_items
        if item in all_package_items or item in import_usage
    }
    should_export.update(registry_items_module_level)
    
    # Items imported from package modules (actual usage) - these are clearly public API
    should_export.update(import_usage.keys())
    
    # Items defined in package modules (public API, not starting with _)
    # These are part of the public API even if not used elsewhere
    should_export.update(all_package_items)
    
    # Filter out items starting with _ (private/internal)
    should_export = {item for item in should_export if not item.startswith('_')}
    
    # Filter out generated UI classes (ui.generated module)
    # These are auto-generated from .ui files and not intended for direct import
    if package_name == 'ui':
        # Exclude items that start with Ui_ (generated UI classes)
        # and items that are imported from ui.generated modules
        generated_ui_classes = {
            item for item in should_export
            if item.startswith('Ui_') or (
                item in import_usage and 
                import_usage[item].get('module_path', '').startswith('ui.generated')
            )
        }
        should_export -= generated_ui_classes
    
    # Filter out config constants if we export config module (package-specific logic)
    if package_name == 'core':
        # We export config as a module, not individual constants
        # But keep functions/classes from config
        config_constants = {
            item for item in should_export
            if item.startswith(('AI_', 'BASE_', 'DEFAULT_', 'LOG_', 'USER_', 'MAX_', 'MIN_'))
            and item in import_usage  # Only if actually imported directly
        }
        # For core, we typically import config module, not constants directly
        # So remove constants that are only imported directly (rare pattern)
        should_export -= config_constants
    
    # Items currently exported
    already_exported = should_export & current_exports
    
    # Items that should be exported but aren't
    missing_exports = should_export - current_exports
    
    # Items currently exported but maybe shouldn't be (not used elsewhere)
    potentially_unnecessary = current_exports - should_export
    
    report = {
        'package': package_name,
        'current_exports_count': len(current_exports),
        'should_export_count': len(should_export),
        'already_exported': sorted(already_exported),
        'missing_exports': sorted(missing_exports),
        'potentially_unnecessary': sorted(potentially_unnecessary),
        'cross_module_usage': {name: stats for name, stats in cross_module_items.items()},
        'import_usage_details': import_usage,
        'package_api_items': sorted(all_package_items),  # Convert set to sorted list
        'registry_items': sorted(registry_items)  # Convert set to sorted list
    }
    
    return report


def generate_recommended_exports(report: Dict) -> str:
    """Generate recommended export code snippet."""
    missing = sorted(report['missing_exports'])
    
    if not missing:
        return "# No missing exports to add\n"
    
    # Group by usage count
    high_usage = []
    medium_usage = []
    low_usage = []
    
    for item in missing:
        usage = report['import_usage_details'].get(item, {})
        count = usage.get('import_count', 0)
        module_path = usage.get('module_path', 'unknown')
        
        if count >= 5:
            high_usage.append((item, count, module_path))
        elif count >= 2:
            medium_usage.append((item, count, module_path))
        else:
            low_usage.append((item, count, module_path))
    
    output = []
    output.append("# Recommended exports (prioritized by usage):\n")
    
    if high_usage:
        output.append("\n# High usage (>= 5 imports):")
        for item, count, module in sorted(high_usage, key=lambda x: x[1], reverse=True)[:20]:
            output.append(f"# from {module} import {item}  # used {count} times")
    
    if medium_usage:
        output.append("\n# Medium usage (2-4 imports):")
        for item, count, module in sorted(medium_usage, key=lambda x: x[1], reverse=True)[:20]:
            output.append(f"# from {module} import {item}  # used {count} times")
    
    if low_usage:
        output.append(f"\n# Low usage (0-1 imports, but part of public API):")
        output.append(f"# {len(low_usage)} items - see full report for details")
    
    return "\n".join(output)


def print_report(report: Dict, show_recommendations: bool = False):
    """Print formatted audit report."""
    logger.info(f"{'='*80}")
    logger.info(f"AUDIT REPORT: {report['package']}")
    logger.info(f"{'='*80}")
    
    logger.info(f"Current exports: {report['current_exports_count']}")
    logger.info(f"Should export: {report['should_export_count']}")
    logger.info(f"Already exported: {len(report['already_exported'])}")
    logger.info(f"Missing exports: {len(report['missing_exports'])}")
    logger.info(f"Potentially unnecessary: {len(report['potentially_unnecessary'])}")
    
    if report['missing_exports']:
        logger.warning(f"[MISSING] Items that should be exported but aren't ({len(report['missing_exports'])}):")
        for item in sorted(report['missing_exports'])[:20]:  # Show first 20
            usage = report['import_usage_details'].get(item, {})
            count = usage.get('import_count', 0)
            module = usage.get('module_path', 'unknown')
            logger.warning(f"  - {item} (imported {count} times from {module})")
        if len(report['missing_exports']) > 20:
            logger.warning(f"  ... and {len(report['missing_exports']) - 20} more")
    
    if report['cross_module_usage']:
        logger.info(f"[CROSS-MODULE] Items used across multiple modules ({len(report['cross_module_usage'])}):")
        sorted_cross = sorted(
            report['cross_module_usage'].items(),
            key=lambda x: x[1]['import_count'],
            reverse=True
        )
        for item, stats in sorted_cross[:10]:  # Show top 10
            logger.info(f"  - {item} (imported {stats['import_count']} times)")
        if len(sorted_cross) > 10:
            logger.info(f"  ... and {len(sorted_cross) - 10} more")
    
    if report['potentially_unnecessary']:
        logger.warning(f"[UNNECESSARY] Items exported but not used elsewhere ({len(report['potentially_unnecessary'])}):")
        logger.info("  Note: These might be legacy compatibility names or internal exports")
        for item in sorted(report['potentially_unnecessary'])[:10]:
            logger.warning(f"  - {item}")
        if len(report['potentially_unnecessary']) > 10:
            logger.warning(f"  ... and {len(report['potentially_unnecessary']) - 10} more")
    
    if show_recommendations:
        logger.info(f"{'='*80}")
        logger.info("RECOMMENDED EXPORTS")
        logger.info(f"{'='*80}")
        recommendations = generate_recommended_exports(report)
        # User-facing recommendations stay as print() for immediate visibility
        print(recommendations)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Audit package exports to determine what should be exported'
    )
    parser.add_argument(
        '--package',
        type=str,
        help='Package to audit (core, communication, ui, tasks, ai, user)',
        default=None
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Audit all packages'
    )
    parser.add_argument(
        '--recommendations',
        action='store_true',
        help='Show recommended export code snippets'
    )
    
    args = parser.parse_args()
    
    packages = ['core', 'communication', 'ui', 'tasks', 'ai', 'user']
    
    if args.package:
        if args.package not in packages:
            logger.error(f"Package '{args.package}' not recognized.")
            # User-facing error messages stay as print() for immediate visibility
            print(f"Error: Package '{args.package}' not recognized.")
            print(f"Available packages: {', '.join(packages)}")
            sys.exit(1)
        packages = [args.package]
    elif not args.all:
        # User-facing usage messages stay as print() for immediate visibility
        print("Specify --package <name> or --all to audit packages")
        sys.exit(1)
    
    reports = []
    for package in packages:
        try:
            report = generate_audit_report(package)
            print_report(report, show_recommendations=args.recommendations)
            reports.append(report)
        except Exception as e:
            logger.error(f"Error auditing {package}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    if len(reports) > 1:
        logger.info(f"{'='*80}")
        logger.info("SUMMARY")
        logger.info(f"{'='*80}")
        
        total_missing = sum(len(r['missing_exports']) for r in reports)
        total_unnecessary = sum(len(r['potentially_unnecessary']) for r in reports)
        
        logger.info(f"Total missing exports: {total_missing}")
        logger.info(f"Total potentially unnecessary exports: {total_unnecessary}")
        
        for report in reports:
            if report['missing_exports']:
                logger.warning(f"{report['package']}: {len(report['missing_exports'])} missing exports")


if __name__ == '__main__':
    main()

