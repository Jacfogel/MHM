#!/usr/bin/env python3
# TOOL_TIER: core

"""
Generate and update MODULE_DEPENDENCIES_DETAIL.md automatically.
Scans all .py files and creates comprehensive module dependency documentation.
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
# Check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

if __name__ != '__main__' and __package__ and '.' in __package__:
    # Running as part of a package, use relative imports
    from . import config
    from ..shared.common import ensure_ascii
else:
    # Running directly or not as a package, use absolute imports
    from development_tools import config
    from development_tools.shared.common import ensure_ascii
from development_tools.shared.constants import (
    is_local_module as _is_local_module,
    is_standard_library_module as _is_stdlib_module,
)

from core.logger import get_component_logger

# Load external config on module import
config.load_external_config()

logger = get_component_logger("development_tools")


def extract_imports_from_file(file_path: str, local_prefixes: Optional[Tuple[str, ...]] = None) -> Dict[str, List[Dict]]:
    """Extract all imports from a Python file with detailed information."""
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
                    import_info = {
                        'module': module_name,
                        'as_name': alias.asname,
                        'imported_items': [module_name]  # For direct imports, the module itself
                    }
                    
                    if is_standard_library(module_name):
                        imports['standard_library'].append(import_info)
                    elif is_local_import(module_name, local_prefixes):
                        imports['local'].append(import_info)
                    else:
                        imports['third_party'].append(import_info)
                        
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name:
                    # Extract specific imported items
                    imported_items = []
                    for alias in node.names:
                        if alias.name == '*':
                            imported_items.append('*')
                        else:
                            imported_items.append(alias.name)
                    
                    import_info = {
                        'module': module_name,
                        'as_name': None,  # ImportFrom doesn't have module-level aliases
                        'imported_items': imported_items
                    }
                    
                    if is_standard_library(module_name):
                        imports['standard_library'].append(import_info)
                    elif is_local_import(module_name, local_prefixes):
                        imports['local'].append(import_info)
                    else:
                        imports['third_party'].append(import_info)
                
    except Exception as e:
        logger.error(ensure_ascii(f"Error parsing {file_path}: {e}"))
    
    return imports

def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    return _is_stdlib_module(module_name)

def is_local_import(module_name: str, local_prefixes: Tuple[str, ...] = None) -> bool:
    """
    Check if a module is a local import (part of our project).
    
    Args:
        module_name: The module name to check
        local_prefixes: Optional tuple of module prefixes to treat as local.
                       If None, uses LOCAL_MODULE_PREFIXES from constants (loaded from config).
    
    Returns:
        True if the module is local, False otherwise.
    """
    if local_prefixes is not None:
        # Use provided prefixes
        if not module_name:
            return False
        base = module_name.split('.', 1)[0]
        return base in local_prefixes
    # Use default from constants (which loads from config)
    return _is_local_module(module_name)

def format_import_details(import_info: Dict) -> str:
    """Format import information for display - handles both list and set formats."""
    module = import_info['module']
    imported_items = import_info.get('imported_items', [])
    
    # Handle both list and set formats
    if isinstance(imported_items, set):
        imported_items = sorted(list(imported_items))
    elif not isinstance(imported_items, list):
        imported_items = [imported_items] if imported_items else []
    
    if imported_items == [module] or '*' in imported_items or not imported_items:
        # Direct import or wildcard import or no specific items
        return module
    else:
        # Specific items imported - deduplicate and sort
        unique_items = sorted(list(dict.fromkeys(imported_items)))  # Preserve order while deduplicating
        items_str = ', '.join(unique_items)
        return ensure_ascii(f"{module} ({items_str})")

def scan_all_python_files(local_prefixes: Optional[Tuple[str, ...]] = None) -> Dict[str, Dict]:
    """Scan all Python files in the project and extract import information."""
    # Handle both relative and absolute imports
    # Check if we're running as part of a package to avoid __package__ != __spec__.parent warnings
    if __name__ != '__main__' and __package__ and '.' in __package__:
        from . import config
    else:
        # Running directly, use absolute imports
        from development_tools import config
    
    project_root = config.get_project_root()
    results = {}
    
    # Directories to scan from configuration
    scan_dirs = config.get_scan_directories()
    
    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob('*.py'):
            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace('\\', '/')
            
            imports = extract_imports_from_file(str(py_file), local_prefixes=local_prefixes)
            
            results[file_key] = {
                'imports': imports,
                'total_imports': sum(len(imp_list) for imp_list in imports.values())
            }
    
    # Also scan root directory for .py files
    for py_file in project_root.glob('*.py'):
        if py_file.name not in ['generate_function_registry.py', 'generate_module_dependencies.py']:
            file_key = py_file.name
            
            imports = extract_imports_from_file(str(py_file), local_prefixes=local_prefixes)
            
            results[file_key] = {
                'imports': imports,
                'total_imports': sum(len(imp_list) for imp_list in imports.values())
            }
    
    return results

def find_usage_of_module(target_module: str, all_modules: Dict[str, Dict]) -> List[str]:
    """Find all modules that use the target module."""
    users = []
    for file_path, data in all_modules.items():
        if target_module in data['imports']['local']:
            users.append(file_path)
    return sorted(users)

def find_reverse_dependencies(target_module: str, all_modules: Dict[str, Dict]) -> List[str]:
    """Find all modules that import the target module."""
    users = []
    
    # Convert file path to module name (e.g., 'core/config.py' -> 'core.config')
    module_name = target_module.replace('/', '.').replace('.py', '')
    
    for file_path, data in all_modules.items():
        # Check local imports for the target module
        for import_info in data['imports']['local']:
            if import_info['module'] == module_name:
                users.append(file_path)
                break
    
    return sorted(users)

def analyze_dependency_changes(file_path: str, data: Dict, existing_content: str) -> Dict:
    """Analyze if dependencies have changed since last generation."""
    changes = {
        'added': [],
        'removed': [],
        'unchanged': True
    }
    
    # Extract current dependencies from the new structure
    current_deps = set()
    for import_info in data['imports']['local']:
        current_deps.add(import_info['module'])
    
    # Extract existing dependencies from content
    existing_deps = set()
    if existing_content:
        section_start = existing_content.find(ensure_ascii(f"#### `{file_path}`"))
        if section_start != -1:
            next_section = existing_content.find("#### `", section_start + 1)
            if next_section == -1:
                section_end = len(existing_content)
            else:
                section_end = next_section
            
            section_content = existing_content[section_start:section_end]
            
            # Extract dependencies from the section
            for line in section_content.split('\n'):
                if line.strip().startswith('- `') and line.strip().endswith('`'):
                    dep = line.strip()[3:-1]  # Remove '- `' and '`'
                    if '.' in dep:  # Only count local dependencies
                        # Extract module name from formatted string (e.g., "core.error_handling (func1, func2)" -> "core.error_handling")
                        module_name = dep.split(' (')[0]
                        existing_deps.add(module_name)
    
    # Calculate changes
    added = current_deps - existing_deps
    removed = existing_deps - current_deps
    
    if added or removed:
        changes['unchanged'] = False
        changes['added'] = sorted(added)
        changes['removed'] = sorted(removed)
    
    return changes

def infer_module_purpose(file_path: str, data: Dict, all_modules: Dict[str, Dict]) -> str:
    """Infer a more detailed purpose based on dependencies and usage patterns."""
    # Extract local dependencies from the new structure
    local_deps = [import_info['module'] for import_info in data['imports']['local']]
    reverse_deps = find_reverse_dependencies(file_path, all_modules)
    
    # Analyze dependency patterns
    core_deps = [d for d in local_deps if d.startswith('core.')]
    bot_deps = [d for d in local_deps if d.startswith('bot.')]
    ui_deps = [d for d in local_deps if d.startswith('ui.')]
    test_deps = [d for d in local_deps if 'test' in d]
    
    # Infer purpose based on patterns
    if file_path.startswith('communication/') or file_path.startswith('ai/'):
        if 'ai_chatbot' in file_path:
            return "AI chatbot implementation using LM Studio API"
        elif 'base_channel' in file_path:
            return "Abstract base class for communication channels"
        elif 'channel_factory' in file_path:
            return "Factory for creating communication channels"
        elif 'channel_registry' in file_path:
            return "Registry for all available communication channels"
        elif 'communication_manager' in file_path:
            return "Manages communication across all channels"
        elif 'conversation_manager' in file_path:
            return "Manages conversation flows and check-ins"
        elif 'discord_bot' in file_path:
            return "Discord bot implementation"
        elif 'email_bot' in file_path:
            return "Email bot implementation"

        elif 'user_context_manager' in file_path:
            return "Manages user context for AI conversations"
        else:
            return ensure_ascii(f"Communication channel implementation for {file_path.split('/')[-1].replace('.py', '')}")
    
    elif file_path.startswith('core/'):
        if 'config' in file_path:
            return "Configuration management and validation"
        elif 'error_handling' in file_path:
            return "Centralized error handling and recovery"
        elif 'file_operations' in file_path:
            return "File operations and data management"
        elif 'logger' in file_path:
            return "Logging system configuration and management"
        elif 'message_management' in file_path:
            return "Message management and storage"
        elif 'response_tracking' in file_path:
            return "Tracks user responses and interactions"
        elif 'schedule_management' in file_path:
            return "Schedule management and time period handling"
        elif 'scheduler' in file_path:
            return "Task scheduling and job management"
        elif 'service' in file_path:
            return "Main service orchestration and management"
        elif 'service_utilities' in file_path:
            return "Utility functions for service operations"
        elif 'ui_management' in file_path:
            return "UI management and widget utilities"
        elif 'user_data' in file_path:
            if 'handlers' in file_path:
                return "User data handlers with caching and validation"
            elif 'manager' in file_path:
                return "Enhanced user data management with references"
            elif 'validation' in file_path:
                return "User data validation and integrity checks"
        elif 'user_management' in file_path:
            return "Centralized user data access and management"
        elif 'validation' in file_path:
            return "Data validation utilities"
        elif 'auto_cleanup' in file_path:
            return "Automatic cache cleanup and maintenance"
        elif 'backup_manager' in file_path:
            return "Manages automatic backups and rollback operations"
        elif 'checkin_analytics' in file_path:
            return "Analyzes check-in data and provides insights"
        else:
            return ensure_ascii(f"Core system module for {file_path.split('/')[-1].replace('.py', '')}")
    
    elif file_path.startswith('ui/'):
        if 'dialogs' in file_path:
            return ensure_ascii(f"Dialog component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}")
        elif 'widgets' in file_path:
            return ensure_ascii(f"UI widget component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}")
        elif 'generated' in file_path:
            return ensure_ascii(f"Auto-generated UI component for {file_path.split('/')[-1].replace('.py', '').replace('_', ' ')}")
        elif 'ui_app' in file_path:
            return "Main UI application (PyQt6)"
        else:
            return ensure_ascii(f"User interface component for {file_path.split('/')[-1].replace('.py', '')}")
    
    elif file_path.startswith('tests/'):
        if 'behavior' in file_path:
            return ensure_ascii(f"Behavior tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}")
        elif 'integration' in file_path:
            return ensure_ascii(f"Integration tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}")
        elif 'unit' in file_path:
            return ensure_ascii(f"Unit tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}")
        elif 'ui' in file_path:
            return ensure_ascii(f"UI tests for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}")
        else:
            return ensure_ascii(f"Test file for {file_path.split('/')[-1].replace('.py', '').replace('test_', '').replace('_', ' ')}")
    
    elif file_path.startswith('user/'):
        if 'user_context' in file_path:
            return "User context management"
        elif 'user_preferences' in file_path:
            return "User preferences management"
        else:
            return ensure_ascii(f"User data module for {file_path.split('/')[-1].replace('.py', '')}")
    
    elif file_path.startswith('tasks/'):
        return "Task management and scheduling"
    
    elif file_path.endswith('run_tests.py') or 'test' in file_path.lower():
        return "Test runner for the application"
    elif any(main_file in file_path for main_file in ['run_', 'main.py']):
        return "Main entry point for the application"
    
    # Fallback based on dependency patterns
    if len(core_deps) > len(local_deps) * 0.7:
        return f"Core system module with heavy core dependencies"
    elif len(bot_deps) > 0:
        return f"Bot-related module with communication dependencies"
    elif len(ui_deps) > 0:
        return f"UI-related module with interface dependencies"
    elif len(test_deps) > 0:
        return ensure_ascii(f"Test-related module")
    else:
        return ensure_ascii(f"Module for {file_path}")


def generate_module_dependencies_content(actual_imports: Dict[str, Dict], existing_content: str = "") -> str:
    """Generate comprehensive module dependencies content with hybrid format."""
    timestamp = datetime.now()
    content: List[str] = []

    generated_at = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    generated_date = timestamp.strftime("%Y-%m-%d")

    # Get project name from config
    project_name = config.get_project_name('Project')
    
    content.append(f"# Module Dependencies - {project_name} Project")
    content.append("")
    content.append("> **File**: `development_docs/MODULE_DEPENDENCIES_DETAIL.md`")
    content.append("> **Generated**: This file is auto-generated by generate_module_dependencies.py. Do not edit manually.")
    content.append("> **Generated by**: generate_module_dependencies.py - Module Dependencies Generator")
    content.append(ensure_ascii(f"> **Last Generated**: {generated_at}"))
    content.append("> **Source**: python development_tools/generate_module_dependencies.py")
    content.append("")
    content.append("> **Audience**: Human developer and AI collaborators  ")
    content.append(f"> **Purpose**: Complete dependency map for all modules in the {project_name} codebase  ")
    content.append("> **Status**: **ACTIVE** - Hybrid auto-generated and manually enhanced  ")
    content.append("")
    content.append("> **See [README.md](README.md) for complete navigation and project overview**")
    content.append("> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**")
    content.append("> **See [TODO.md](../TODO.md) for current documentation priorities**")
    content.append("")

    total_files = len(actual_imports)
    total_imports = sum(data['total_imports'] for data in actual_imports.values())
    local_imports = sum(len(data['imports']['local']) for data in actual_imports.values())
    std_lib_imports = sum(len(data['imports']['standard_library']) for data in actual_imports.values())
    third_party_imports = sum(len(data['imports']['third_party']) for data in actual_imports.values())

    def percent(value: int) -> float:
        return (value / total_imports * 100.0) if total_imports else 0.0

    content.append("## Overview")
    content.append("")
    content.append("### Module Dependencies Coverage: 100.0% - COMPLETED")
    content.append(ensure_ascii(f"- **Files Scanned**: {total_files}"))
    content.append(ensure_ascii(f"- **Total Imports Found**: {total_imports}"))
    content.append(ensure_ascii(f"- **Dependencies Documented**: {total_files} (100% coverage)"))
    content.append(ensure_ascii(f"- **Standard Library Imports**: {std_lib_imports} ({percent(std_lib_imports):.1f}%)"))
    content.append(ensure_ascii(f"- **Third-Party Imports**: {third_party_imports} ({percent(third_party_imports):.1f}%)"))
    content.append(ensure_ascii(f"- **Local Imports**: {local_imports} ({percent(local_imports):.1f}%)"))
    content.append(ensure_ascii(f"- **Last Updated**: {generated_date}"))
    content.append("")
    content.append("**Status**: COMPLETED - All module dependencies have been documented with detailed dependency and usage information.")
    content.append("")
    content.append("**Note**: This dependency map uses a hybrid approach. Automated analysis discovers dependencies while manual enhancements record intent and reverse dependencies.")
    content.append("")

    content.append("## Import Statistics")
    content.append("")
    content.append(ensure_ascii(f"- **Standard Library**: {std_lib_imports} imports ({percent(std_lib_imports):.1f}%)"))
    content.append(ensure_ascii(f"- **Third-Party**: {third_party_imports} imports ({percent(third_party_imports):.1f}%)"))
    content.append(ensure_ascii(f"- **Local**: {local_imports} imports ({percent(local_imports):.1f}%)"))
    content.append("")

    content.append("## Module Dependencies by Directory")
    content.append("")

    dir_files: Dict[str, List[Tuple[str, Dict]]] = {}
    for file_path, data in actual_imports.items():
        dir_name = file_path.split('/')[0] if '/' in file_path else 'root'
        dir_files.setdefault(dir_name, []).append((file_path, data))

    dir_descriptions = {
            'core': 'Core system modules (foundation)',
            'bot': 'Communication channel implementations',
            'communication': 'Communication services and orchestration',
            'ui': 'User interface components',
            'user': 'User data and context',
            'tasks': 'Task management',
            'tests': 'Test files',
            'ai': 'AI services and support modules',
            'root': 'Project root files',
        }

    for dir_name in sorted(dir_files):
            description = dir_descriptions.get(dir_name)
            if description:
                content.append(ensure_ascii(f"### `{dir_name}/` - {description}"))
            else:
                content.append(ensure_ascii(f"### `{dir_name}/`"))
            content.append("")

            for file_path, data in sorted(dir_files[dir_name], key=lambda item: item[0]):
                content.extend(generate_module_section(file_path, data, actual_imports, existing_content))
                content.append("")

    return ensure_ascii("\n".join(content))



def get_directory_description(dir_name: str) -> str:
    """Get a description for a directory."""
    descriptions = {
        'core': 'Core System Modules (Foundation)',
        'bot': 'Communication Channel Implementations', 
        'ui': 'User Interface Components',
        'user': 'User Data and Context',
        'tasks': 'Task Management',
        'tests': 'Test Files',
        'root': 'Root Files'
    }
    return descriptions.get(dir_name, 'Unknown Directory')

def get_module_purpose(file_path: str) -> str:
    """Get a purpose description for a module based on its path and name."""
    purposes = {
        # Core modules
        'core/config.py': 'Configuration management - handles environment variables, validation, and system settings',
        'core/error_handling.py': 'Comprehensive error handling system - provides centralized error handling, custom exceptions, and recovery strategies',
        'core/logger.py': 'Centralized logging system for the application',
        'core/file_operations.py': 'File operations utilities - contains functions for file I/O, path determination, and file management',
        'core/user_management.py': 'User management utilities - contains functions for managing user accounts, preferences, context, and schedules',
        'core/message_management.py': 'Message management system - handles message categories, content, and delivery',
        'core/schedule_management.py': 'Schedule management system - handles user schedules, periods, and timing',
        'core/user_data_handlers.py': 'User data handlers - provides centralized access to user data with caching and validation',
        'core/user_data_manager.py': 'User data manager - manages user data storage, retrieval, and caching',
        'core/user_data_validation.py': 'User data validation - validates user input and data integrity',
        'core/validation.py': 'Validation system - provides validation utilities and error handling',
        'core/response_tracking.py': 'Response tracking system - tracks user responses and interactions',
        'core/scheduler.py': 'Scheduler system - manages scheduled tasks and operations',
        'core/service.py': 'Main service - coordinates all system components and manages the application lifecycle',
        'core/service_utilities.py': 'Service utilities - provides utility functions for the service layer',
        'core/ui_management.py': 'UI management - manages user interface components and interactions',
        'core/auto_cleanup.py': 'Auto cleanup system - handles automatic cleanup of temporary files and data',
        'core/backup_manager.py': 'Backup manager - handles system backups and data protection',
        'core/checkin_analytics.py': 'Check-in analytics - analyzes user check-in patterns and provides insights',
        
        # Bot modules
        'ai/chatbot.py': 'AI chatbot implementation using LM Studio API',
        'communication/communication_channels/base/base_channel.py': 'Abstract base class for all communication channels',
        'communication/core/factory.py': 'Factory for creating communication channels',
        'communication/core/channel_orchestrator.py': 'Manages communication across all channels',
        'communication/message_processing/conversation_flow_manager.py': 'Manages conversation flows and check-ins',
        'communication/communication_channels/discord/bot.py': 'Discord bot implementation',
        'communication/communication_channels/email/bot.py': 'Email bot implementation',

        'user/context_manager.py': 'Manages user context for AI conversations',
        
        # User modules
        'user/user_context.py': 'User context management - manages user context and personal information',
        'user/user_preferences.py': 'User preferences management - manages user preferences and settings',
        
        # Task modules
        'tasks/task_management.py': 'Task management system - manages user tasks and to-do items',
        
        # Root files (entry point - customize for your project)
        # 'run_mhm.py': 'Main entry point for the application',  # Example - replace with your entry point
        'run_tests.py': 'Test runner for the application',
    }
    
    return purposes.get(file_path, f'Module for {file_path}')

def generate_module_section(file_path: str, data: Dict, all_modules: Dict[str, Dict], existing_content: str = "") -> List[str]:
    """Generate a module section with enhanced automated analysis."""
    content = []
    
    # Enhanced purpose inference
    inferred_purpose = infer_module_purpose(file_path, data, all_modules)
    
    # Reverse dependency analysis
    reverse_deps = find_reverse_dependencies(file_path, all_modules)
    
    # Dependency change analysis
    dep_changes = analyze_dependency_changes(file_path, data, existing_content)
    
    # Auto-generated section marker
    content.append(ensure_ascii(f"#### `{file_path}`"))
    
    # Enhanced purpose
    content.append(ensure_ascii(f"- **Purpose**: {inferred_purpose}"))
    
    # Dependencies with enhanced details (deduplicated)
    # Deduplicate imports by module name and merge imported items
    local_deps_raw = data['imports']['local']
    std_lib_deps_raw = data['imports']['standard_library']
    third_party_deps_raw = data['imports']['third_party']
    
    # Deduplicate and merge imports
    def deduplicate_imports(imports_list):
        """Deduplicate imports by module, merging imported items."""
        import_map = {}
        for imp in imports_list:
            module = imp['module']
            if module not in import_map:
                import_map[module] = {
                    'module': module,
                    'as_name': imp.get('as_name'),
                    'imported_items': set()
                }
            # Merge imported items
            if 'imported_items' in imp:
                import_map[module]['imported_items'].update(imp['imported_items'])
        # Convert sets back to sorted lists
        for imp in import_map.values():
            imp['imported_items'] = sorted(list(imp['imported_items']))
        return list(import_map.values())
    
    local_deps = deduplicate_imports(local_deps_raw)
    std_lib_deps = deduplicate_imports(std_lib_deps_raw)
    third_party_deps = deduplicate_imports(third_party_deps_raw)
    
    if local_deps or std_lib_deps or third_party_deps:
        content.append("- **Dependencies**: ")
        
        # Local dependencies
        if local_deps:
            content.append("  - **Local**:")
            for import_info in sorted(local_deps, key=lambda x: x['module']):
                formatted_import = format_import_details(import_info)
                change_indicator = ""
                if not dep_changes['unchanged']:
                    if import_info['module'] in dep_changes['added']:
                        change_indicator = " (NEW)"
                    elif import_info['module'] in dep_changes['removed']:
                        change_indicator = " (REMOVED)"
                content.append(ensure_ascii(f"    - `{formatted_import}`{change_indicator}"))
        
        # Standard library dependencies
        if std_lib_deps:
            content.append("  - **Standard Library**:")
            for import_info in sorted(std_lib_deps, key=lambda x: x['module']):
                formatted_import = format_import_details(import_info)
                content.append(ensure_ascii(f"    - `{formatted_import}`"))
        
        # Third-party dependencies
        if third_party_deps:
            content.append("  - **Third-party**:")
            for import_info in sorted(third_party_deps, key=lambda x: x['module']):
                formatted_import = format_import_details(import_info)
                content.append(ensure_ascii(f"    - `{formatted_import}`"))
    else:
        content.append("- **Dependencies**: None (no imports)")
    
    # Reverse dependencies (automated)
    if reverse_deps:
        content.append("- **Used by**: ")
        for user in reverse_deps:
            content.append(ensure_ascii(f"  - `{user}`"))
    else:
        content.append("- **Used by**: None (not imported by other modules)")
    
    # Automated analysis summary
    if not dep_changes['unchanged']:
        content.append("")
        content.append("**Dependency Changes**:")
        if dep_changes['added']:
            content.append(ensure_ascii(f"- Added: {', '.join(dep_changes['added'])}"))
        if dep_changes['removed']:
            content.append(ensure_ascii(f"- Removed: {', '.join(dep_changes['removed'])}"))
    
    # Manual enhancement section marker (simplified)
    content.append("")
    content.append("<!-- MANUAL_ENHANCEMENT_START -->")
    content.append("<!-- Add any additional context, key functions, or special considerations here -->")
    content.append("<!-- MANUAL_ENHANCEMENT_END -->")
    
    return content

def preserve_manual_enhancements(existing_content: str, new_content: str) -> Tuple[str, Dict[str, str]]:
    """
    Preserve manual enhancements from existing content when regenerating.
    
    Returns:
        tuple: (final_content, preserved_enhancements)
            - final_content: The new content with manual enhancements preserved
            - preserved_enhancements: Dict mapping module names to their preserved enhancement content (without markers)
    """
    if not existing_content:
        return new_content, {}
    
    # Extract general manual enhancement section from existing content
    general_manual_enhancement = ""
    start_marker = "## **Circular Dependencies**"
    if start_marker in existing_content:
        # Find the start of the general manual enhancement section
        start_pos = existing_content.find(start_marker)
        # Find the end of the file
        end_pos = existing_content.find("<!-- MANUAL_ENHANCEMENT_END -->", start_pos)
        if end_pos != -1:
            end_pos += len("<!-- MANUAL_ENHANCEMENT_END -->")
            general_manual_enhancement = existing_content[start_pos:end_pos]
    
    # Split content into sections for module-specific enhancements
    sections = {}
    current_section = None
    current_content = []
    
    for line in existing_content.split('\n'):
        # Look for module headers in both formats:
        # 1. "#### `module_name.py`" (with #### prefix)
        # 2. "module_name.py" (without #### prefix)
        if (line.startswith('#### `') and line.endswith('`') and '.py`' in line):
            # Format: "#### `module_name.py`"
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            current_section = line[6:-1]  # Remove "#### `" and "`"
            current_content = [line]
        elif (line.strip().endswith('.py') and 
              not line.startswith('-') and
              not line.startswith('**') and
              '/' in line):
            # Format: "module_name.py" (legacy format)
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            current_section = line.strip()
            current_content = [line]
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    # Extract manual enhancements
    manual_enhancements = {}
    preserved_info = {}  # Track preserved enhancements for reporting
    
    for section_name, section_content in sections.items():
        start_marker = "<!-- MANUAL_ENHANCEMENT_START -->"
        end_marker = "<!-- MANUAL_ENHANCEMENT_END -->"
        
        start_pos = section_content.find(start_marker)
        end_pos = section_content.find(end_marker)
        
        if start_pos != -1 and end_pos != -1:
            # Extract the entire manual enhancement content including markers
            manual_content = section_content[start_pos:end_pos + len(end_marker)]
            # Extract content without markers for reporting
            content_without_markers = section_content[start_pos + len(start_marker):end_pos].strip()
            # Preserve if it contains any content beyond the placeholder
            if "Add any additional context" not in manual_content or len(manual_content.strip()) > len("<!-- MANUAL_ENHANCEMENT_START -->\n<!-- MANUAL_ENHANCEMENT_END -->"):
                manual_enhancements[section_name] = manual_content
                if content_without_markers and content_without_markers != "<!-- Add any additional context, key functions, or special considerations here -->":
                    # Store first line or summary for reporting
                    first_line = content_without_markers.split('\n')[0].strip()
                    preserved_info[section_name] = first_line[:100] + "..." if len(first_line) > 100 else first_line
            else:
                pass # No manual enhancement content found
    
    # Apply manual enhancements to new content
    result_lines = []
    current_section = None
    in_manual_section = False
    skip_until_end = False
    
    for line in new_content.split('\n'):
        # Look for module headers in the format "#### `module_name.py`" (with #### prefix)
        if line.startswith('#### `') and line.endswith('`'):
            # Extract the module name from the #### format
            module_name = line[6:-1]  # Remove "#### `" and "`"
            current_section = module_name
            in_manual_section = False
            skip_until_end = False
            result_lines.append(line)
        elif line == "<!-- MANUAL_ENHANCEMENT_START -->":
            in_manual_section = True
            if current_section and current_section in manual_enhancements:
                # Insert preserved manual enhancement
                result_lines.append(manual_enhancements[current_section])
                skip_until_end = True  # Skip all content until we find the end marker
            else:
                # Keep the placeholder
                result_lines.append(line)
        elif line == "<!-- MANUAL_ENHANCEMENT_END -->":
            in_manual_section = False
            skip_until_end = False
            # Only add this line if we didn't insert preserved content
            if not (current_section and current_section in manual_enhancements):
                result_lines.append(line)
        elif in_manual_section and skip_until_end:
            # Skip all content between start and end when we have preserved content
            continue
        elif in_manual_section:
            # Keep placeholder content when we don't have preserved content
            result_lines.append(line)
        else:
            result_lines.append(line)
    
    # Add general manual enhancement section at the end if it exists
    if general_manual_enhancement:
        result_lines.append("")
        result_lines.append(general_manual_enhancement)
    
    return '\n'.join(result_lines), preserved_info

def identify_modules_needing_enhancement(existing_content: str, actual_imports: Dict[str, Dict]) -> Dict[str, str]:
    """Identify modules that need manual enhancements or updates."""
    enhancement_status = {}
    
    # Parse existing manual enhancements
    existing_enhancements = {}
    if existing_content:
        sections = {}
        current_section = None
        current_content = []
        
        for line in existing_content.split('\n'):
            # Look for module headers in both formats:
            # 1. "#### `module_name.py`" (with #### prefix)
            # 2. "module_name.py" (without #### prefix)
            if (line.startswith('#### `') and line.endswith('`') and '.py`' in line):
                # Format: "#### `module_name.py`"
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line[6:-1]  # Remove "#### `" and "`"
                current_content = [line]
            elif (line.strip().endswith('.py') and 
                  not line.startswith('-') and
                  not line.startswith('**') and
                  '/' in line):
                # Format: "module_name.py" (legacy format)
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line.strip()
                current_content = [line]
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        # Extract manual enhancements
        for section_name, section_content in sections.items():
            start_marker = "<!-- MANUAL_ENHANCEMENT_START -->"
            end_marker = "<!-- MANUAL_ENHANCEMENT_END -->"
            
            start_pos = section_content.find(start_marker)
            end_pos = section_content.find(end_marker)
            
            if start_pos != -1 and end_pos != -1:
                manual_content = section_content[start_pos:end_pos + len(end_marker)]
                # Check if it's just the placeholder
                if "Add any additional context" in manual_content and "Enhanced Purpose" not in manual_content:
                    existing_enhancements[section_name] = "placeholder"
                else:
                    existing_enhancements[section_name] = "enhanced"
            else:
                existing_enhancements[section_name] = "missing"
    
    # Analyze each module
    for file_path, data in actual_imports.items():
        section_name = file_path  # Use file_path directly as section name
        
        if section_name not in existing_enhancements:
            enhancement_status[file_path] = "new_module"
        elif existing_enhancements[section_name] == "placeholder":
            enhancement_status[file_path] = "needs_enhancement"
        elif existing_enhancements[section_name] == "enhanced":
            # Check if dependencies have changed significantly
            # For now, just mark as up_to_date since we're preserving manual enhancements
            # The dependency comparison logic needs to be fixed to compare the same type of dependencies
            enhancement_status[file_path] = "up_to_date"
        else:
            enhancement_status[file_path] = "missing_enhancement"
    
    return enhancement_status


def generate_ai_module_dependencies_content(actual_imports: Dict[str, Dict]) -> str:
    """Generate the AI-facing dependency summary - dynamic and data-driven."""
    timestamp = datetime.now()
    generated_at = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    total_files = len(actual_imports)
    total_imports = sum(data['total_imports'] for data in actual_imports.values())
    std_lib = sum(len(data['imports']['standard_library']) for data in actual_imports.values())
    third_party = sum(len(data['imports']['third_party']) for data in actual_imports.values())
    local = sum(len(data['imports']['local']) for data in actual_imports.values())

    def percent(value: int) -> float:
        return (value / total_imports * 100.0) if total_imports else 0.0

    # Analyze patterns dynamically
    patterns = analyze_dependency_patterns(actual_imports)
    
    # Build decision trees dynamically
    decision_trees = _build_dynamic_decision_trees(actual_imports)
    
    # Find critical dependencies dynamically
    critical_deps = _find_critical_dependencies(actual_imports)
    
    # Detect risk areas dynamically
    risk_areas = _detect_risk_areas(actual_imports, patterns)
    
    lines: List[str] = []
    lines.extend([
        "# AI Module Dependencies - Key Relationships & Patterns",
        "",
        "> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`",
        "> **Generated**: This file is auto-generated by generate_module_dependencies.py. Do not edit manually.",
        "> **Generated by**: generate_module_dependencies.py - Module Dependencies Generator",
        ensure_ascii(f"> **Last Generated**: {generated_at}"),
        "> **Source**: python development_tools/generate_module_dependencies.py",
        "",
        "> **Audience**: AI collaborators",
        "> **Purpose**: Essential module relationships and dependency patterns for AI context",
        "> **Style**: Pattern-focused, relationship-driven, actionable",
        "",
        "## Current Status",
        "",
        "### Dependency Coverage: 100.0% - COMPLETED",
        ensure_ascii(f"- **Files Scanned**: {total_files}"),
        ensure_ascii(f"- **Total Imports**: {total_imports}"),
        ensure_ascii(f"- **Standard Library**: {std_lib} ({percent(std_lib):.1f}%)"),
        ensure_ascii(f"- **Third-Party**: {third_party} ({percent(third_party):.1f}%)"),
        ensure_ascii(f"- **Local Imports**: {local} ({percent(local):.1f}%)"),
        "",
        "## Dependency Decision Trees",
        "",
        decision_trees,
        "",
        "## Key Dependency Patterns",
        "",
        _generate_dependency_patterns_section(patterns, actual_imports),
        "",
        "## Critical Dependencies for AI Context",
        "",
        critical_deps,
        "",
        "## Dependency Risk Areas",
        "",
        risk_areas,
        "",
        "## Quick Reference for AI",
        "",
        _generate_quick_reference(actual_imports, patterns),
        "",
        "> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md)**",
    ])

    return ensure_ascii("\n".join(lines))


def _build_dynamic_decision_trees(actual_imports: Dict[str, Dict]) -> str:
    """Build dynamic decision trees based on actual imports."""
    lines = []
    
    # Core System Decision Tree
    core_modules = [f for f in actual_imports.keys() if f.startswith('core/')]
    if core_modules:
        lines.append("### Need Core System Access?")
        lines.append("Core System Dependencies:")
        
        # Group by common patterns
        config_modules = [f for f in core_modules if 'config' in f]
        logger_modules = [f for f in core_modules if 'logger' in f]
        data_modules = [f for f in core_modules if 'user_data' in f or 'file_operations' in f]
        error_modules = [f for f in core_modules if 'error' in f]
        
        if config_modules or logger_modules:
            lines.append("- Configuration and Setup")
            for mod in (config_modules + logger_modules)[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        if data_modules:
            lines.append("- Data Management")
            for mod in data_modules[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        if error_modules:
            lines.append("- Error Handling")
            for mod in error_modules[:2]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        lines.append("")
    
    # AI/Chatbot Decision Tree
    ai_modules = [f for f in actual_imports.keys() if f.startswith('ai/') or (f.startswith('user/') and 'context' in f)]
    comm_modules = [f for f in actual_imports.keys() if f.startswith('communication/')]
    if ai_modules or comm_modules:
        lines.append("### Need AI or Chatbot Support?")
        lines.append("AI System Dependencies:")
        
        if ai_modules:
            lines.append("- AI Core")
            for mod in ai_modules[:2]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        command_modules = [f for f in comm_modules if 'command' in f or 'interaction' in f]
        if command_modules:
            lines.append("- Command Processing")
            for mod in command_modules[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        if comm_modules:
            lines.append("- Communication Integration")
            channel_modules = [f for f in comm_modules if 'channel' in f or 'orchestrator' in f]
            for mod in channel_modules[:2]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        lines.append("")
    
    # Communication Channel Decision Tree
    if comm_modules:
        lines.append("### Need Communication Channel Coverage?")
        lines.append("Communication Dependencies:")
        
        base_modules = [f for f in comm_modules if 'base' in f or 'factory' in f]
        if base_modules:
            lines.append("- Channel Infrastructure")
            for mod in base_modules[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        channel_impls = [f for f in comm_modules if 'discord' in f or 'email' in f]
        if channel_impls:
            lines.append("- Specific Channels")
            for mod in channel_impls[:2]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        flow_modules = [f for f in comm_modules if 'conversation' in f or 'flow' in f]
        if flow_modules:
            lines.append("- Conversation Flow")
            for mod in flow_modules[:2]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        lines.append("")
    
    # UI Decision Tree
    ui_modules = [f for f in actual_imports.keys() if f.startswith('ui/')]
    if ui_modules:
        lines.append("### Need UI Dependencies?")
        lines.append("UI Dependencies:")
        
        main_ui = [f for f in ui_modules if 'ui_app' in f]
        if main_ui:
            lines.append("- Main Application")
            for mod in main_ui[:1]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        dialogs = [f for f in ui_modules if 'dialog' in f]
        if dialogs:
            lines.append("- Dialogs")
            for mod in dialogs[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        
        widgets = [f for f in ui_modules if 'widget' in f]
        if widgets:
            lines.append("- Widgets")
            for mod in widgets[:3]:
                deps = _format_module_dependencies(mod, actual_imports)
                lines.append(f"  - {mod} <- {deps}")
        lines.append("")
    
    return "\n".join(lines) if lines else "*No modules detected - patterns may need updating*"

def _format_module_dependencies(file_path: str, actual_imports: Dict[str, Dict], max_deps: int = 5) -> str:
    """Format module dependencies concisely - deduplicated and clean."""
    if file_path not in actual_imports:
        return "unknown"
    
    data = actual_imports[file_path]
    
    # Get unique dependencies (deduplicate)
    local_deps = list(dict.fromkeys([imp['module'] for imp in data['imports']['local']]))
    stdlib_deps = list(dict.fromkeys([imp['module'] for imp in data['imports']['standard_library']]))
    third_party_deps = list(dict.fromkeys([imp['module'] for imp in data['imports']['third_party']]))
    
    parts = []
    
    # Group dependencies (show top most common)
    if stdlib_deps:
        # Show most common stdlib modules
        stdlib_names = ', '.join(sorted(stdlib_deps)[:4])
        parts.append(f"standard library ({stdlib_names})")
    
    if third_party_deps:
        # Show most common third-party modules
        third_party_names = ', '.join(sorted(third_party_deps)[:3])
        parts.append(f"third-party ({third_party_names})")
    
    if local_deps:
        # Extract module names (last part of dotted path) and deduplicate
        local_names = list(dict.fromkeys([d.split('.')[-1] for d in local_deps]))
        # Show most relevant local dependencies
        local_display = ', '.join(local_names[:max_deps])
        if len(local_names) > max_deps:
            local_display += f" (+{len(local_names) - max_deps} more)"
        parts.append(local_display)
    
    return ', '.join(parts) if parts else "none"

def _find_critical_dependencies(actual_imports: Dict[str, Dict]) -> str:
    """Find critical dependencies dynamically."""
    lines = []
    
    # Entry points
    entry_points = [f for f in actual_imports.keys() if 'run_' in f or f.endswith('main.py')]
    if entry_points:
        lines.append("### Entry Points")
        for ep in entry_points[:5]:
            deps = _format_module_dependencies(ep, actual_imports)
            purpose = "main application entry" if 'run_' in ep else "application entry"
            lines.append(f"- `{ep}` -> {deps} ({purpose})")
        lines.append("")
    
    # Data flow
    data_modules = [f for f in actual_imports.keys() if 'user_data' in f or 'file_operations' in f]
    if data_modules:
        lines.append("### Data Flow")
        for mod in data_modules[:3]:
            deps = _format_module_dependencies(mod, actual_imports)
            lines.append(f"- {mod.split('/')[-1]}: {mod} <- {deps}")
        lines.append("")
    
    # Communication flow
    comm_modules = [f for f in actual_imports.keys() if f.startswith('communication/')]
    if comm_modules:
        lines.append("### Communication Flow")
        for mod in comm_modules[:3]:
            deps = _format_module_dependencies(mod, actual_imports)
            purpose = mod.split('/')[-1].replace('.py', '')
            lines.append(f"- {purpose}: {mod} <- {deps}")
        lines.append("")
    
    return "\n".join(lines) if lines else "*No critical dependencies detected*"

def _detect_risk_areas(actual_imports: Dict[str, Dict], patterns: Dict[str, Any]) -> str:
    """Detect dependency risk areas dynamically."""
    lines = []
    
    # High coupling
    high_coupling = patterns.get('high_coupling', [])
    if high_coupling:
        lines.append("### High Coupling")
        for item in sorted(high_coupling, key=lambda x: x['import_count'], reverse=True)[:5]:
            lines.append(f"- `{item['file']}` -> {item['import_count']} local dependencies (heavy coupling)")
        lines.append("")
    
    # Third-party risks
    third_party = patterns.get('third_party_dependencies', [])
    if third_party:
        lines.append("### Third-Party Risks")
        third_party_map = {}
        for item in third_party:
            for dep in item['dependencies']:
                if dep not in third_party_map:
                    third_party_map[dep] = []
                third_party_map[dep].append(item['file'])
        
        for dep, files in sorted(third_party_map.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            lines.append(f"- `{files[0]}` -> {dep} ({len(files)} modules use this)")
        lines.append("")
    
    # Circular dependencies (basic detection)
    circular = _detect_circular_dependencies(actual_imports)
    if circular:
        lines.append("### Circular Dependencies to Monitor")
        for pair in circular[:5]:
            lines.append(f"- `{pair[0]}` <-> `{pair[1]}`")
        lines.append("")
    
    return "\n".join(lines) if lines else "*No significant risk areas detected*"

def _detect_circular_dependencies(actual_imports: Dict[str, Dict]) -> List[tuple]:
    """Detect potential circular dependencies."""
    circular = []
    
    for file_path, data in actual_imports.items():
        local_imports = [imp['module'] for imp in data['imports']['local']]
        
        # Check if imported modules also import this module
        for imported_module in local_imports:
            # Convert module name to file path
            module_file = imported_module.replace('.', '/') + '.py'
            
            if module_file in actual_imports:
                imported_data = actual_imports[module_file]
                imported_local = [imp['module'] for imp in imported_data['imports']['local']]
                
                # Convert current file to module name
                current_module = file_path.replace('/', '.').replace('.py', '')
                
                if current_module in imported_local:
                    pair = tuple(sorted([file_path, module_file]))
                    if pair not in circular:
                        circular.append(pair)
    
    return circular

def _generate_dependency_patterns_section(patterns: Dict[str, Any], actual_imports: Dict[str, Dict]) -> str:
    """Generate dependency patterns section dynamically."""
    lines = []
    
    # Core -> Communication/AI pattern
    comm_ai_deps = patterns.get('communication_dependencies', [])
    if comm_ai_deps:
        lines.append("### Core -> Communication and AI (most common)")
        lines.append("Communication and AI modules depend on core system modules.")
        for item in comm_ai_deps[:3]:
            core_deps = [m for m in item['modules'] if m.startswith('core.')]
            if core_deps:
                lines.append(f"- `{item['file']}` -> {', '.join(core_deps[:3])}")
        lines.append("")
    
    # UI -> Core pattern
    ui_deps = patterns.get('ui_dependencies', [])
    if ui_deps:
        lines.append("### UI -> Core")
        lines.append("UI modules rely on core configuration and data access.")
        for item in ui_deps[:3]:
            core_deps = [m for m in item['modules'] if m.startswith('core.')]
            if core_deps:
                lines.append(f"- `{item['file']}` -> {', '.join(core_deps[:3])}")
        lines.append("")
    
    # Communication -> Communication pattern
    if comm_ai_deps:
        lines.append("### Communication -> Communication")
        lines.append("Communication modules compose other communication utilities for complete flows.")
        for item in comm_ai_deps[:3]:
            comm_deps = [m for m in item['modules'] if m.startswith('communication.') or m.startswith('ai.')]
            if comm_deps:
                lines.append(f"- `{item['file']}` -> {', '.join(comm_deps[:3])}")
        lines.append("")
    
    # Third-party integration
    third_party = patterns.get('third_party_dependencies', [])
    if third_party:
        lines.append("### Third-Party Integration")
        lines.append("External libraries provide channel and UI support.")
        for item in third_party[:5]:
            deps = ', '.join(item['dependencies'][:2])
            lines.append(f"- `{item['file']}` -> {deps}")
        lines.append("")
    
    return "\n".join(lines) if lines else "*No patterns detected*"

def _generate_quick_reference(actual_imports: Dict[str, Dict], patterns: Dict[str, Any]) -> str:
    """Generate quick reference section dynamically."""
    lines = []
    
    lines.append("### Common Patterns")
    lines.append("1. Core system modules expose utilities with minimal dependencies.")
    lines.append("2. Communication and AI modules depend on core and peer communication modules.")
    lines.append("3. UI modules rely on the UI framework and core services.")
    lines.append("4. Data access modules rely on configuration plus logging.")
    lines.append("")
    
    lines.append("### Dependency Guidelines")
    lines.append("- Prefer core modules for shared logic instead of duplicating functionality.")
    lines.append("- Avoid circular dependencies; break them with interfaces or utility modules.")
    lines.append("- Use dependency injection for testability when modules call into services.")
    lines.append("- Keep third-party usage wrapped by dedicated modules.")
    lines.append("")
    
    # Module organization
    lines.append("### Module Organisation")
    directories = {}
    for file_path in actual_imports.keys():
        parts = file_path.split('/')
        if len(parts) > 1:
            top_dir = parts[0]
            if top_dir not in directories:
                directories[top_dir] = []
            directories[top_dir].append(file_path)
    
    descriptions = {
        'core': 'System utilities (minimal dependencies)',
        'communication': 'Channels and message processing (depends on core)',
        'ai': 'Chatbot functionality (depends on core)',
        'ui': 'User interface (depends on core, limited communication dependencies)',
        'user': 'User context (depends on core)',
        'tasks': 'Task management (depends on core)'
    }
    
    for dir_name in sorted(directories.keys()):
        desc = descriptions.get(dir_name, 'Module directory')
        lines.append(f"- `{dir_name}/` - {desc}")
    
    return "\n".join(lines)

def analyze_dependency_patterns(actual_imports: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze dependency patterns for AI consumption."""
    patterns = {
        'core_dependencies': [],
        'communication_dependencies': [],
        'ui_dependencies': [],
        'third_party_dependencies': [],
        'circular_dependencies': [],
        'high_coupling': []
    }
    
    # Analyze dependency patterns
    for file_path, data in actual_imports.items():
        local_imports = data['imports'].get('local', [])
        third_party_imports = data['imports'].get('third_party', [])
        
        # Core dependencies
        if file_path.startswith('core/'):
            patterns['core_dependencies'].append({
                'file': file_path,
                'local_imports': len(local_imports),
                'third_party_imports': len(third_party_imports),
                'modules': [imp['module'] for imp in local_imports]
            })
        
        # Communication/AI dependencies
        elif file_path.startswith('communication/') or file_path.startswith('ai/'):
            patterns['communication_dependencies'].append({
                'file': file_path,
                'local_imports': len(local_imports),
                'third_party_imports': len(third_party_imports),
                'modules': [imp['module'] for imp in local_imports]
            })
        
        # UI dependencies
        elif file_path.startswith('ui/'):
            patterns['ui_dependencies'].append({
                'file': file_path,
                'local_imports': len(local_imports),
                'third_party_imports': len(third_party_imports),
                'modules': [imp['module'] for imp in local_imports]
            })
        
        # High coupling detection
        if len(local_imports) > 5:
            patterns['high_coupling'].append({
                'file': file_path,
                'import_count': len(local_imports),
                'modules': [imp['module'] for imp in local_imports]
            })
        
        # Third-party dependencies
        if third_party_imports:
            patterns['third_party_dependencies'].append({
                'file': file_path,
                'dependencies': [imp['module'] for imp in third_party_imports]
            })
    
    return patterns

def update_module_dependencies(local_prefixes: Optional[Tuple[str, ...]] = None):
    """
    Update MODULE_DEPENDENCIES_DETAIL.md and AI_MODULE_DEPENDENCIES.md with hybrid approach.
    
    Args:
        local_prefixes: Optional tuple of module prefixes to treat as local.
                       If None, uses LOCAL_MODULE_PREFIXES from constants (loaded from config).
    """
    logger.info("[SCAN] Scanning all Python files for imports...")
    actual_imports = scan_all_python_files(local_prefixes=local_prefixes)
    
    # Read existing content to preserve manual enhancements
    # Script is at: development_tools/imports/generate_module_dependencies.py
    # So we need to go up 2 levels to get to project root
    detail_path = Path(__file__).parent.parent.parent / 'development_docs' / 'MODULE_DEPENDENCIES_DETAIL.md'
    existing_content = ""
    if detail_path.exists():
        try:
            with open(detail_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except Exception as e:
            logger.warning(ensure_ascii(f"Could not read existing file: {e}"))
    
    logger.info("[GEN] Generating MODULE_DEPENDENCIES_DETAIL.md content...")
    detail_content = generate_module_dependencies_content(actual_imports, existing_content)
    
    logger.info("[GEN] Generating AI_MODULE_DEPENDENCIES.md content...")
    ai_content = generate_ai_module_dependencies_content(actual_imports)
    
    # Identify modules needing enhancement
    enhancement_status = identify_modules_needing_enhancement(existing_content, actual_imports)
    
    # Preserve manual enhancements
    final_detail_content, preserved_enhancements = preserve_manual_enhancements(existing_content, detail_content)
    
    # Write the DETAIL file
    try:
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write(final_detail_content)
        
        # Write the AI file
        # Script is at: development_tools/imports/generate_module_dependencies.py
        # So we need to go up 2 levels to get to project root
        ai_path = Path(__file__).parent.parent.parent / 'ai_development_docs' / 'AI_MODULE_DEPENDENCIES.md'
        with open(ai_path, 'w', encoding='utf-8') as f:
            f.write(ai_content)
        
        logger.info(ensure_ascii(f"[SUCCESS] Both module dependency files updated successfully!"))
        logger.info(ensure_ascii(f"[FILES] Generated:"))
        logger.info(ensure_ascii(f"   development_docs/MODULE_DEPENDENCIES_DETAIL.md - Complete detailed dependencies"))
        logger.info(ensure_ascii(f"   ai_development_docs/AI_MODULE_DEPENDENCIES.md - Concise AI-focused dependencies"))
        logger.info(ensure_ascii(f"[STATS] Statistics:"))
        logger.info(ensure_ascii(f"   Files scanned: {len(actual_imports)}"))
        logger.info(ensure_ascii(f"   Total imports: {sum(data['total_imports'] for data in actual_imports.values())}"))
        logger.info(ensure_ascii(f"   Local dependencies: {sum(len(data['imports']['local']) for data in actual_imports.values())}"))
        logger.info(ensure_ascii(f"   Coverage: 100% (all files documented)"))
        logger.info(ensure_ascii(f"   Detail file: {detail_path}"))
        logger.info(ensure_ascii(f"   AI file: {ai_path}"))
        
        # Report preserved manual enhancements
        if preserved_enhancements:
            logger.info(ensure_ascii(f"[PRESERVED] Manual Enhancements Preserved ({len(preserved_enhancements)}):"))
            for module_name, enhancement_summary in sorted(preserved_enhancements.items()):
                logger.info(ensure_ascii(f"   {module_name}: {enhancement_summary}"))
        else:
            logger.info(ensure_ascii(f"[PRESERVED] No manual enhancements found to preserve"))
        
        # Report enhancement status
        logger.info(ensure_ascii(f"[ENHANCEMENT] Manual Enhancement Status:"))
        status_counts = {}
        for status in enhancement_status.values():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            status_display = {
                'new_module': 'New modules (need enhancement)',
                'needs_enhancement': 'Modules with placeholder content',
                'dependencies_changed': 'Modules with changed dependencies',
                'up_to_date': 'Modules with current enhancements',
                'missing_enhancement': 'Modules missing enhancement markers'
            }.get(status, status)
            logger.info(ensure_ascii(f"   {status_display}: {count}"))
        
        # Show specific modules needing attention
        priority_modules = {k: v for k, v in enhancement_status.items() 
                          if v in ['new_module', 'needs_enhancement', 'dependencies_changed']}
        
        if priority_modules:
            logger.warning(f"[PRIORITY] Modules needing manual attention: {len(priority_modules)}")
            for file_path, status in sorted(priority_modules.items()):
                status_icon = {
                    'new_module': '[NEW]',
                    'needs_enhancement': '[ENH]',
                    'dependencies_changed': '[CHG]'
                }.get(status, '[?]')
                logger.warning(ensure_ascii(f"   {status_icon} {file_path} ({status})"))
        
        # Validate that preserved enhancements are actually in the written file
        if preserved_enhancements:
            try:
                with open(detail_path, 'r', encoding='utf-8') as f:
                    written_content = f.read()
                
                preserved_count = 0
                for module_name, enhancement_summary in preserved_enhancements.items():
                    # Check if the enhancement content appears in the written file
                    if enhancement_summary.split('\n')[0] in written_content:
                        preserved_count += 1
                
                if preserved_count == len(preserved_enhancements):
                    logger.info(ensure_ascii(f"[VALIDATION] All {preserved_count} manual enhancements verified in written file"))
                else:
                    logger.warning(ensure_ascii(f"[VALIDATION] Warning: Only {preserved_count}/{len(preserved_enhancements)} manual enhancements found in written file"))
            except Exception as e:
                logger.error(ensure_ascii(f"[VALIDATION] Could not validate preserved enhancements: {e}"))
        
        return True
        
    except Exception as e:
        logger.error(ensure_ascii(f"[ERROR] Failed to write development_docs/MODULE_DEPENDENCIES_DETAIL.md: {e}"))
        return False

if __name__ == "__main__":
    update_module_dependencies() 
