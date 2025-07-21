#!/usr/bin/env python3
"""
Audit script to verify MODULE_DEPENDENCIES.md completeness and accuracy.
Scans all .py files and extracts import information for comparison.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

def extract_imports_from_file(file_path: str) -> Dict[str, List[str]]:
    """Extract all imports from a Python file."""
    imports = {
        'standard_library': [],
        'third_party': [],
        'local': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if is_standard_library(module_name):
                        imports['standard_library'].append(module_name)
                    elif is_local_import(module_name):
                        imports['local'].append(module_name)
                    else:
                        imports['third_party'].append(module_name)
                        
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name:
                    if is_standard_library(module_name):
                        imports['standard_library'].append(module_name)
                    elif is_local_import(module_name):
                        imports['local'].append(module_name)
                    else:
                        imports['third_party'].append(module_name)
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    standard_lib_modules = {
        'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 'typing', 're', 'uuid',
        'shutil', 'zipfile', 'threading', 'asyncio', 'socket', 'psutil', 'requests',
        'logging', 'warnings', 'subprocess', 'signal', 'atexit', 'random', 'hashlib',
        'email', 'smtplib', 'urllib', 'http', 'ssl', 'pytz', 'calendar', 'math',
        'statistics', 'collections', 'itertools', 'functools', 'contextlib'
    }
    
    # Check if it's a standard library module
    if module_name in standard_lib_modules:
        return True
    
    # Check if it starts with common standard library prefixes
    std_prefixes = ['os.', 'sys.', 'json.', 'time.', 'datetime.', 'pathlib.', 'typing.']
    return any(module_name.startswith(prefix) for prefix in std_prefixes)

def is_local_import(module_name: str) -> bool:
    """Check if a module is a local import (part of our project)."""
    local_prefixes = ['core.', 'bot.', 'ui.', 'user.', 'tasks.', 'scripts.', 'tests.']
    return any(module_name.startswith(prefix) for prefix in local_prefixes)

def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract import information."""
    project_root = Path(__file__).parent.parent
    results = {}
    
    # Directories to scan
    scan_dirs = ['core', 'bot', 'ui', 'user', 'tasks', 'scripts', 'tests']
    
    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob('*.py'):
            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace('\\', '/')
            
            imports = extract_imports_from_file(str(py_file))
            
            results[file_key] = {
                'imports': imports,
                'total_imports': sum(len(imp_list) for imp_list in imports.values())
            }
    
    # Also scan root directory for .py files
    for py_file in project_root.glob('*.py'):
        if py_file.name not in ['audit_function_registry.py', 'audit_module_dependencies.py']:
            file_key = py_file.name
            
            imports = extract_imports_from_file(str(py_file))
            
            results[file_key] = {
                'imports': imports,
                'total_imports': sum(len(imp_list) for imp_list in imports.values())
            }
    
    return results

def parse_module_dependencies() -> Dict[str, List[str]]:
    """Parse the existing MODULE_DEPENDENCIES.md to extract documented dependencies."""
    deps_path = Path(__file__).parent.parent / 'MODULE_DEPENDENCIES.md'
    documented = {}
    
    try:
        with open(deps_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract file sections and their dependencies (new format)
        # Pattern: #### `filename.py` followed by dependencies section
        sections = re.findall(r'#### `([^`]+)`\n(.*?)(?=#### `|$)', content, re.DOTALL)
        
        for file_path, section_content in sections:
            # Extract dependencies from the dependencies section
            # Look for the "Dependencies:" section and extract module names
            deps_section = re.search(r'- \*\*Dependencies\*\*: \n(.*?)(?=- \*\*Used by\*\*:|$)', section_content, re.DOTALL)
            if deps_section:
                # Extract individual dependencies (lines starting with "  - `")
                deps_matches = re.findall(r'  - `([^`]+)`', deps_section.group(1))
                documented[file_path] = deps_matches
            else:
                # Check if it says "None (no local imports)"
                if "None (no local imports)" in section_content:
                    documented[file_path] = []
                else:
                    documented[file_path] = []
            
    except Exception as e:
        print(f"Error parsing MODULE_DEPENDENCIES.md: {e}")
    
    return documented

def generate_dependency_report():
    """Generate a comprehensive dependency audit report."""
    print("[SCAN] Scanning all Python files for imports...")
    actual_imports = scan_all_python_files()
    
    print("[DOC] Parsing MODULE_DEPENDENCIES.md...")
    documented_deps = parse_module_dependencies()
    
    print("\n" + "="*80)
    print("MODULE DEPENDENCIES AUDIT REPORT")
    print("="*80)
    
    # Statistics
    total_files = len(actual_imports)
    total_actual_imports = sum(data['total_imports'] for data in actual_imports.values())
    total_documented_deps = sum(len(deps) for deps in documented_deps.values())
    
    print(f"\n[STATS] OVERALL STATISTICS:")
    print(f"   Files scanned: {total_files}")
    print(f"   Total imports found: {total_actual_imports}")
    print(f"   Dependencies documented: {total_documented_deps}")
    
    # Import breakdown
    std_lib_count = sum(len(data['imports']['standard_library']) for data in actual_imports.values())
    third_party_count = sum(len(data['imports']['third_party']) for data in actual_imports.values())
    local_count = sum(len(data['imports']['local']) for data in actual_imports.values())
    
    print(f"   Standard library imports: {std_lib_count}")
    print(f"   Third-party imports: {third_party_count}")
    print(f"   Local imports: {local_count}")
    
    # Missing dependencies
    print(f"\n[MISS] MISSING FROM DEPENDENCIES DOCUMENTATION:")
    missing_count = 0
    for file_path, data in actual_imports.items():
        if file_path not in documented_deps:
            print(f"   [DIR] {file_path} - ENTIRE FILE MISSING")
            missing_count += data['total_imports']
        else:
            documented_deps_set = set(documented_deps[file_path])
            actual_deps = set(data['imports']['local'])  # Focus on local dependencies
            missing_deps = actual_deps - documented_deps_set
            
            if missing_deps:
                print(f"   [FILE] {file_path}:")
                for dep in sorted(missing_deps):
                    print(f"      - {dep}")
                    missing_count += 1
    
    print(f"\n   Total missing dependencies: {missing_count}")
    
    # Detailed breakdown by directory
    print(f"\n[DIR] BREAKDOWN BY DIRECTORY:")
    dir_stats = {}
    for file_path, data in actual_imports.items():
        dir_name = file_path.split('/')[0] if '/' in file_path else 'root'
        if dir_name not in dir_stats:
            dir_stats[dir_name] = {'files': 0, 'imports': 0, 'local_deps': 0}
        dir_stats[dir_name]['files'] += 1
        dir_stats[dir_name]['imports'] += data['total_imports']
        dir_stats[dir_name]['local_deps'] += len(data['imports']['local'])
    
    for dir_name, stats in sorted(dir_stats.items()):
        print(f"   {dir_name}/: {stats['files']} files, {stats['imports']} imports, {stats['local_deps']} local deps")
    
    # Generate updated dependency sections
    print(f"\n[DOC] GENERATING UPDATED DEPENDENCY SECTIONS...")
    generate_updated_dependency_sections(actual_imports)

def generate_updated_dependency_sections(actual_imports: Dict[str, Dict]):
    """Generate updated dependency sections for missing files."""
    print("\n" + "="*80)
    print("UPDATED DEPENDENCY SECTIONS TO ADD:")
    print("="*80)
    
    for file_path, data in sorted(actual_imports.items()):
        if data['imports']['local']:  # Only show files with local dependencies
            print(f"\n#### `{file_path}`")
            print(f"- **Purpose**: [Add purpose description]")
            print(f"- **Dependencies**: {', '.join(sorted(data['imports']['local']))}")
            print(f"- **Used by**: [Add usage information]")

def analyze_circular_dependencies(actual_imports: Dict[str, Dict]):
    """Analyze potential circular dependencies."""
    print(f"\n[CIRC] CIRCULAR DEPENDENCY ANALYSIS:")
    
    # Build dependency graph
    dependency_graph = {}
    for file_path, data in actual_imports.items():
        dependency_graph[file_path] = set(data['imports']['local'])
    
    # Check for circular dependencies
    circular_deps = []
    for file_path, deps in dependency_graph.items():
        for dep in deps:
            # Check if this dependency also imports the original file
            if dep in dependency_graph:
                if file_path in dependency_graph[dep]:
                    circular_deps.append((file_path, dep))
    
    if circular_deps:
        print("   [WARN] POTENTIAL CIRCULAR DEPENDENCIES FOUND:")
        for file1, file2 in circular_deps:
            print(f"      {file1} ↔ {file2}")
    else:
        print("   [OK] No circular dependencies detected")

def identify_enhancement_needs(documented_deps: Dict[str, List[str]], actual_imports: Dict[str, Dict]) -> Dict[str, str]:
    """Identify modules that need manual enhancements or updates."""
    enhancement_status = {}
    
    # Check each documented module
    for file_path in documented_deps.keys():
        if file_path in actual_imports:
            # Check if it has manual enhancement markers
            deps_path = Path(__file__).parent.parent / 'MODULE_DEPENDENCIES.md'
            try:
                with open(deps_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find the section for this module
                section_start = content.find(f"#### `{file_path}`")
                if section_start != -1:
                    # Find the end of this section (next module or end of file)
                    next_section = content.find("#### `", section_start + 1)
                    if next_section == -1:
                        section_end = len(content)
                    else:
                        section_end = next_section
                    
                    section_content = content[section_start:section_end]
                    
                    # Check for manual enhancement markers
                    start_marker = "<!-- MANUAL_ENHANCEMENT_START -->"
                    end_marker = "<!-- MANUAL_ENHANCEMENT_END -->"
                    
                    start_pos = section_content.find(start_marker)
                    end_pos = section_content.find(end_marker)
                    
                    if start_pos != -1 and end_pos != -1:
                        manual_content = section_content[start_pos:end_pos + len(end_marker)]
                        if "TODO: Add detailed purpose description" in manual_content:
                            enhancement_status[file_path] = "needs_enhancement"
                        else:
                            enhancement_status[file_path] = "enhanced"
                    else:
                        enhancement_status[file_path] = "missing_markers"
                else:
                    enhancement_status[file_path] = "not_found"
            except Exception as e:
                enhancement_status[file_path] = "error"
        else:
            enhancement_status[file_path] = "not_in_codebase"
    
    return enhancement_status

def find_usage_of_module(module_name: str, all_modules: Dict[str, Dict]) -> List[str]:
    """Find all modules that import a given module."""
    using_modules = []
    for file_path, data in all_modules.items():
        if module_name in data['imports']['local']:
            using_modules.append(file_path)
    return using_modules

def analyze_module_complexity(file_path: str, data: Dict, all_modules: Dict[str, Dict]) -> Dict:
    """Analyze module complexity and provide insights."""
    local_deps = data['imports']['local']
    reverse_deps = find_usage_of_module(file_path, all_modules)
    
    analysis = {
        'dependency_count': len(local_deps),
        'reverse_dependency_count': len(reverse_deps),
        'complexity_level': 'low',
        'key_insights': [],
        'recommendations': []
    }
    
    # Determine complexity level
    if len(local_deps) > 15:
        analysis['complexity_level'] = 'high'
    elif len(local_deps) > 8:
        analysis['complexity_level'] = 'medium'
    
    # Analyze dependency patterns
    core_deps = [d for d in local_deps if d.startswith('core.')]
    bot_deps = [d for d in local_deps if d.startswith('bot.')]
    ui_deps = [d for d in local_deps if d.startswith('ui.')]
    
    # Generate insights
    if len(core_deps) > len(local_deps) * 0.7:
        analysis['key_insights'].append("Heavy core system dependencies")
    if len(bot_deps) > 0:
        analysis['key_insights'].append("Communication channel dependencies")
    if len(ui_deps) > 0:
        analysis['key_insights'].append("User interface dependencies")
    if len(reverse_deps) > 10:
        analysis['key_insights'].append("Highly used by other modules")
    elif len(reverse_deps) == 0:
        analysis['key_insights'].append("Not imported by other modules")
    
    # Generate recommendations
    if analysis['complexity_level'] == 'high':
        analysis['recommendations'].append("Consider breaking down into smaller modules")
    if len(core_deps) > 10:
        analysis['recommendations'].append("Review core dependency usage")
    if len(reverse_deps) == 0 and not file_path.startswith('tests/'):
        analysis['recommendations'].append("Verify if this module is still needed")
    
    return analysis

def generate_enhanced_dependency_report(actual_imports: Dict[str, Dict], documented_deps: Dict[str, List[str]]):
    """Generate an enhanced dependency report with automated insights."""
    print("\n" + "="*80)
    print("ENHANCED MODULE ANALYSIS REPORT")
    print("="*80)
    
    # Analyze each documented module
    for file_path in sorted(documented_deps.keys()):
        if file_path in actual_imports:
            data = actual_imports[file_path]
            analysis = analyze_module_complexity(file_path, data, actual_imports)
            reverse_deps = find_usage_of_module(file_path, actual_imports)
            
            print(f"\n#### `{file_path}`")
            print(f"- **Complexity**: {analysis['complexity_level'].upper()}")
            print(f"- **Dependencies**: {analysis['dependency_count']}")
            print(f"- **Used by**: {analysis['reverse_dependency_count']} modules")
            
            if analysis['key_insights']:
                print(f"- **Key Insights**: {', '.join(analysis['key_insights'])}")
            
            if analysis['recommendations']:
                print(f"- **Recommendations**: {', '.join(analysis['recommendations'])}")
            
            if reverse_deps:
                print(f"- **Reverse Dependencies**: {', '.join(reverse_deps[:5])}")
                if len(reverse_deps) > 5:
                    print(f"  ... and {len(reverse_deps) - 5} more")

def generate_dependency_report():
    """Generate the main dependency audit report."""
    print("[SCAN] Scanning all Python files for imports...")
    actual_imports = scan_all_python_files()
    
    print("[DOC] Parsing MODULE_DEPENDENCIES.md...")
    documented_deps = parse_module_dependencies()
    
    # Identify enhancement needs
    enhancement_status = identify_enhancement_needs(documented_deps, actual_imports)
    
    # Calculate statistics
    total_files = len(actual_imports)
    total_imports = sum(data['total_imports'] for data in actual_imports.values())
    documented_count = len(documented_deps)
    std_lib_count = sum(len(data['imports']['standard_library']) for data in actual_imports.values())
    third_party_count = sum(len(data['imports']['third_party']) for data in actual_imports.values())
    local_count = sum(len(data['imports']['local']) for data in actual_imports.values())
    
    # Find missing dependencies
    missing_deps = []
    for file_path, data in actual_imports.items():
        if file_path not in documented_deps:
            missing_deps.append(file_path)
    
    # Print report
    print("\n" + "="*80)
    print("MODULE DEPENDENCIES AUDIT REPORT")
    print("="*80)
    
    print("\n[STATS] OVERALL STATISTICS:")
    print(f"   Files scanned: {total_files}")
    print(f"   Total imports found: {total_imports}")
    print(f"   Dependencies documented: {documented_count}")
    print(f"   Standard library imports: {std_lib_count}")
    print(f"   Third-party imports: {third_party_count}")
    print(f"   Local imports: {local_count}")
    
    # Enhancement status summary
    enhancement_counts = {}
    for status in enhancement_status.values():
        enhancement_counts[status] = enhancement_counts.get(status, 0) + 1
    
    print(f"\n[ENHANCEMENT] Manual Enhancement Status:")
    for status, count in sorted(enhancement_counts.items()):
        status_display = {
            'enhanced': 'Modules with manual enhancements',
            'needs_enhancement': 'Modules needing manual enhancement',
            'missing_markers': 'Modules missing enhancement markers',
            'not_found': 'Modules not found in documentation',
            'error': 'Modules with parsing errors',
            'not_in_codebase': 'Documented modules not in codebase'
        }.get(status, status)
        print(f"   {status_display}: {count}")
    
    if missing_deps:
        print(f"\n[MISS] MISSING FROM DEPENDENCIES DOCUMENTATION:")
        for file_path in sorted(missing_deps):
            print(f"   [DIR] {file_path} - ENTIRE FILE MISSING")
        print(f"\n   Total missing dependencies: {len(missing_deps)}")
    
    # Show modules needing enhancement
    needs_enhancement = {k: v for k, v in enhancement_status.items() if v == 'needs_enhancement'}
    if needs_enhancement:
        print(f"\n[PRIORITY] Modules needing manual enhancement:")
        for file_path in sorted(needs_enhancement.keys()):
            print(f"   📝 {file_path}")
    
    # Directory breakdown
    print(f"\n[DIR] BREAKDOWN BY DIRECTORY:")
    dir_stats = {}
    for file_path, data in actual_imports.items():
        dir_name = file_path.split('/')[0] if '/' in file_path else 'root'
        if dir_name not in dir_stats:
            dir_stats[dir_name] = {'files': 0, 'imports': 0, 'local_deps': 0}
        dir_stats[dir_name]['files'] += 1
        dir_stats[dir_name]['imports'] += data['total_imports']
        dir_stats[dir_name]['local_deps'] += len(data['imports']['local'])
    
    for dir_name in sorted(dir_stats.keys()):
        stats = dir_stats[dir_name]
        print(f"   {dir_name}/: {stats['files']} files, {stats['imports']} imports, {stats['local_deps']} local deps")
    
    # Generate enhanced analysis report
    generate_enhanced_dependency_report(actual_imports, documented_deps)
    
    # Generate updated dependency sections
    print(f"\n[DOC] GENERATING UPDATED DEPENDENCY SECTIONS...")
    generate_updated_dependency_sections(actual_imports)
    
    # Also analyze circular dependencies
    analyze_circular_dependencies(actual_imports)

if __name__ == "__main__":
    generate_dependency_report() 