#!/usr/bin/env python3
"""
Generate and update MODULE_DEPENDENCIES_DETAIL.md automatically.
Scans all .py files and creates comprehensive module dependency documentation.
"""

import ast
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from ai_development_tools.services.common import ensure_ascii
from ai_development_tools.services.constants import (
    is_local_module as _is_local_module,
    is_standard_library_module as _is_stdlib_module,
)


def extract_imports_from_file(file_path: str) -> Dict[str, List[Dict]]:
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
                    elif is_local_import(module_name):
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
                    elif is_local_import(module_name):
                        imports['local'].append(import_info)
                    else:
                        imports['third_party'].append(import_info)
                
    except Exception as e:
        print(ensure_ascii(f"Error parsing {file_path}: {e}"))
    
    return imports

def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    return _is_stdlib_module(module_name)

def is_local_import(module_name: str) -> bool:
    """Check if a module is a local import (part of our project)."""
    return _is_local_module(module_name)

def format_import_details(import_info: Dict) -> str:
    """Format import information for display."""
    module = import_info['module']
    imported_items = import_info['imported_items']
    
    if imported_items == [module] or '*' in imported_items:
        # Direct import or wildcard import
        return module
    else:
        # Specific items imported
        items_str = ', '.join(imported_items)
        return ensure_ascii(f"{module} ({items_str})")

def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract import information."""
    import config
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
            
            imports = extract_imports_from_file(str(py_file))
            
            results[file_key] = {
                'imports': imports,
                'total_imports': sum(len(imp_list) for imp_list in imports.values())
            }
    
    # Also scan root directory for .py files
    for py_file in project_root.glob('*.py'):
        if py_file.name not in ['generate_function_registry.py', 'generate_module_dependencies.py']:
            file_key = py_file.name
            
            imports = extract_imports_from_file(str(py_file))
            
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
    
    elif file_path in ['run_mhm.py', 'run_tests.py']:
        if 'run_mhm' in file_path:
            return "Main entry point for the MHM application"
        elif 'run_tests' in file_path:
            return "Test runner for the MHM application"
    
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

    content.append("# Module Dependencies - MHM Project")
    content.append("")
    content.append("> **Generated**: This file is auto-generated by generate_module_dependencies.py. Do not edit manually.")
    content.append("> **Generated by**: generate_module_dependencies.py - Module Dependencies Generator")
    content.append(ensure_ascii(f"> **Last Generated**: {generated_at}"))
    content.append("> **Source**: python ai_development_tools/generate_module_dependencies.py")
    content.append("")
    content.append("> **Audience**: Human developer and AI collaborators  ")
    content.append("> **Purpose**: Complete dependency map for all modules in the MHM codebase  ")
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
        'core/config.py': 'Configuration management for MHM - handles environment variables, validation, and system settings',
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
        
        # Root files
        'run_mhm.py': 'Main entry point for the MHM application',
        'run_tests.py': 'Test runner for the MHM application',
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
    
    # Dependencies with enhanced details
    local_deps = data['imports']['local']
    std_lib_deps = data['imports']['standard_library']
    third_party_deps = data['imports']['third_party']
    
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

def preserve_manual_enhancements(existing_content: str, new_content: str) -> str:
    """Preserve manual enhancements from existing content when regenerating."""
    if not existing_content:
        return new_content
    
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
    for section_name, section_content in sections.items():
        start_marker = "<!-- MANUAL_ENHANCEMENT_START -->"
        end_marker = "<!-- MANUAL_ENHANCEMENT_END -->"
        
        start_pos = section_content.find(start_marker)
        end_pos = section_content.find(end_marker)
        
        if start_pos != -1 and end_pos != -1:
            # Extract the entire manual enhancement content including markers
            manual_content = section_content[start_pos:end_pos + len(end_marker)]
            # Preserve if it contains any content beyond the placeholder
            if "Add any additional context" not in manual_content or len(manual_content.strip()) > len("<!-- MANUAL_ENHANCEMENT_START -->\n<!-- MANUAL_ENHANCEMENT_END -->"):
                manual_enhancements[section_name] = manual_content
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
    
    return '\n'.join(result_lines)

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
    """Generate the AI-facing dependency summary with ASCII-safe formatting."""
    timestamp = datetime.now()
    generated_at = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    total_files = len(actual_imports)
    total_imports = sum(data['total_imports'] for data in actual_imports.values())
    std_lib = sum(len(data['imports']['standard_library']) for data in actual_imports.values())
    third_party = sum(len(data['imports']['third_party']) for data in actual_imports.values())
    local = sum(len(data['imports']['local']) for data in actual_imports.values())

    def percent(value: int) -> float:
        return (value / total_imports * 100.0) if total_imports else 0.0

        lines: List[str] = []
        lines.extend([
            "# AI Module Dependencies - Key Relationships & Patterns",
            "",
            "> **Generated**: This file is auto-generated by generate_module_dependencies.py. Do not edit manually.",
            "> **Generated by**: generate_module_dependencies.py - Module Dependencies Generator",
            ensure_ascii(f"> **Last Generated**: {generated_at}"),
            "> **Source**: python ai_development_tools/generate_module_dependencies.py",
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
            "### Need Core System Access?",
            "Core System Dependencies:",
            "- Configuration and Setup",
            "  - core/config.py <- standard library (os, json, typing)",
            "  - core/logger.py <- standard library (logging, pathlib)",
            "- Data Management",
            "  - core/file_operations.py <- standard library (json, pathlib)",
            "  - core/user_data_handlers.py <- core/config, core/logger",
            "  - core/user_data_manager.py <- core/user_data_handlers",
            "- Error Handling",
            "  - core/error_handling.py <- standard library (logging, traceback)",
            "",
            "### Need AI or Chatbot Support?",
            "AI System Dependencies:",
            "- AI Core",
            "  - ai/chatbot.py <- core/config, core/logger, core/user_data_handlers",
            "  - user/context_manager.py <- core/user_data_handlers",
            "- Command Processing",
            "  - communication/message_processing/command_parser.py <- ai/chatbot",
            "  - communication/command_handlers/interaction_handlers.py <- core/user_data_handlers, core/task_management",
            "  - communication/message_processing/interaction_manager.py <- command_parser, interaction_handlers",
            "- Communication Integration",
            "  - communication/core/channel_orchestrator.py <- ai/chatbot, conversation_flow_manager",
            "",
            "### Need Communication Channel Coverage?",
            "Communication Dependencies:",
            "- Channel Infrastructure",
            "  - communication/communication_channels/base/base_channel.py <- standard library (abc, dataclasses, enum)",
            "  - communication/core/factory.py <- base_channel",
            "  - communication/core/channel_orchestrator.py <- factory, base_channel",
            "- Specific Channels",
            "  - communication/communication_channels/discord/bot.py <- third-party (discord.py), base_channel",
            "  - communication/communication_channels/email/bot.py <- standard library (smtplib, imaplib), base_channel",
            "- Conversation Flow",
            "  - communication/message_processing/conversation_flow_manager.py <- core/user_data_handlers, user/context_manager",
            "",
            "### Need UI Dependencies?",
            "UI Dependencies:",
            "- Main Application",
            "  - ui/ui_app_qt.py <- third-party (PySide6), core/config, communication/core/channel_orchestrator",
            "- Dialogs",
            "  - ui/dialogs/account_creator_dialog.py <- ui/widgets, core/user_data_handlers",
            "  - ui/dialogs/user_profile_dialog.py <- ui/widgets, core/user_data_handlers",
            "  - ui/dialogs/task_management_dialog.py <- ui/widgets, core/task_management",
            "- Widgets",
            "  - ui/widgets/tag_widget.py <- third-party (PySide6)",
            "  - ui/widgets/task_settings_widget.py <- ui/widgets/tag_widget",
            "  - ui/widgets/user_profile_settings_widget.py <- third-party (PySide6)",
            "",
            "## Key Dependency Patterns",
            "",
            "### Core -> Communication and AI (most common)",
            "Communication and AI modules depend on core system modules.",
            "- ai/chatbot.py -> core/config.py, core/logger.py",
            "- communication/command_handlers/interaction_handlers.py -> core/user_data_handlers.py",
            "- communication/core/channel_orchestrator.py -> core/logger.py",
            "",
            "### UI -> Core",
            "UI modules rely on core configuration and data access.",
            "- ui/dialogs/ -> core/user_data_handlers.py",
            "- ui/ui_app_qt.py -> core/config.py",
            "- ui/widgets/ -> core/validation.py",
            "",
            "### Communication -> Communication",
            "Communication modules compose other communication utilities for complete flows.",
            "- communication/message_processing/interaction_manager.py -> command_parser",
            "- communication/core/channel_orchestrator.py -> ai/chatbot.py",
            "- communication/message_processing/conversation_flow_manager.py -> user/context_manager.py",
            "",
            "### Third-Party Integration",
            "External libraries provide channel and UI support.",
            "- communication/communication_channels/discord/bot.py -> discord.py",
            "- ui/ui_app_qt.py -> PySide6",
            "",
            "## Critical Dependencies for AI Context",
            "",
            "### Entry Points",
            "- `run_mhm.py` -> `core/service.py` (main application entry)",
            "- `ui/ui_app_qt.py` -> `communication/core/channel_orchestrator.py` (UI startup)",
            "- `communication/message_processing/interaction_manager.py` -> `ai/chatbot.py` (message handling)",
            "",
            "### Data Flow",
            "- User data: core/user_data_handlers.py <- core/config.py, core/logger.py",
            "- AI context: user/context_manager.py <- core/user_data_handlers.py",
            "- File operations: core/file_operations.py <- standard library (json, pathlib)",
            "",
            "### Communication Flow",
            "- Channel management: communication/core/channel_orchestrator.py <- communication/core/factory.py",
            "- Message handling: communication/message_processing/interaction_manager.py <- command_parser",
            "- AI integration: ai/chatbot.py <- core/config.py, core/user_data_handlers.py",
            "",
            "## Dependency Risk Areas",
            "",
            "### High Coupling",
            "- communication/command_handlers/interaction_handlers.py -> core/user_data_handlers.py (heavy dependency)",
            "- ui/dialogs/ -> core/user_data_handlers.py (UI tied to data layer)",
            "- communication/core/channel_orchestrator.py -> ai/chatbot.py (communication depends on AI)",
            "",
            "### Third-Party Risks",
            "- communication/communication_channels/discord/bot.py -> discord.py",
            "- ui/ui_app_qt.py -> PySide6",
            "",
            "### Circular Dependencies to Monitor",
            "- communication/core/channel_orchestrator.py <-> communication/message_processing/conversation_flow_manager.py",
            "- core/user_data_handlers.py <-> core/user_data_manager.py",
            "",
            "## Quick Reference for AI",
            "",
            "### Common Patterns",
            "1. Core system modules expose utilities with minimal dependencies.",
            "2. Communication and AI modules depend on core and peer communication modules.",
            "3. UI modules rely on the UI framework and core services.",
            "4. Data access modules rely on configuration plus logging.",
            "",
            "### Dependency Guidelines",
            "- Prefer core modules for shared logic instead of duplicating functionality.",
            "- Avoid circular dependencies; break them with interfaces or utility modules.",
            "- Use dependency injection for testability when modules call into services.",
            "- Keep third-party usage wrapped by dedicated modules.",
            "",
            "### Module Organisation",
            "- core/ - System utilities (minimal dependencies)",
            "- communication/ - Channels and message processing (depends on core)",
            "- ai/ - Chatbot functionality (depends on core)",
            "- ui/ - User interface (depends on core, limited communication dependencies)",
            "- user/ - User context (depends on core)",
            "- 	asks/ - Task management (depends on core)",
            "",
            "> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md)",
        ])

        return ensure_ascii("\n".join(lines))


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

def update_module_dependencies():
    """Update MODULE_DEPENDENCIES_DETAIL.md and AI_MODULE_DEPENDENCIES.md with hybrid approach."""
    print("[SCAN] Scanning all Python files for imports...")
    actual_imports = scan_all_python_files()
    
    # Read existing content to preserve manual enhancements
    detail_path = Path(__file__).parent.parent / 'development_docs' / 'MODULE_DEPENDENCIES_DETAIL.md'
    existing_content = ""
    if detail_path.exists():
        try:
            with open(detail_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except Exception as e:
            print(ensure_ascii(f"[WARN] Could not read existing file: {e}"))
    
    print("[GEN] Generating MODULE_DEPENDENCIES_DETAIL.md content...")
    detail_content = generate_module_dependencies_content(actual_imports, existing_content)
    
    print("[GEN] Generating AI_MODULE_DEPENDENCIES.md content...")
    ai_content = generate_ai_module_dependencies_content(actual_imports)
    
    # Identify modules needing enhancement
    enhancement_status = identify_modules_needing_enhancement(existing_content, actual_imports)
    
    # Preserve manual enhancements
    final_detail_content = preserve_manual_enhancements(existing_content, detail_content)
    
    # Write the DETAIL file
    try:
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write(final_detail_content)
        
        # Write the AI file
        ai_path = Path(__file__).parent.parent / 'ai_development_docs' / 'AI_MODULE_DEPENDENCIES.md'
        with open(ai_path, 'w', encoding='utf-8') as f:
            f.write(ai_content)
        
        print(ensure_ascii(f"[SUCCESS] Both module dependency files updated successfully!"))
        print(ensure_ascii(f"[FILES] Generated:"))
        print(ensure_ascii(f"   development_docs/MODULE_DEPENDENCIES_DETAIL.md - Complete detailed dependencies"))
        print(ensure_ascii(f"   ai_development_docs/AI_MODULE_DEPENDENCIES.md - Concise AI-focused dependencies"))
        print(ensure_ascii(f"[STATS] Statistics:"))
        print(ensure_ascii(f"   Files scanned: {len(actual_imports)}"))
        print(ensure_ascii(f"   Total imports: {sum(data['total_imports'] for data in actual_imports.values())}"))
        print(ensure_ascii(f"   Local dependencies: {sum(len(data['imports']['local']) for data in actual_imports.values())}"))
        print(ensure_ascii(f"   Coverage: 100% (all files documented)"))
        print(ensure_ascii(f"   Detail file: {detail_path}"))
        print(ensure_ascii(f"   AI file: {ai_path}"))
        
        # Report enhancement status
        print(ensure_ascii(f"\n[ENHANCEMENT] Manual Enhancement Status:"))
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
            print(ensure_ascii(f"   {status_display}: {count}"))
        
        # Show specific modules needing attention
        priority_modules = {k: v for k, v in enhancement_status.items() 
                          if v in ['new_module', 'needs_enhancement', 'dependencies_changed']}
        
        if priority_modules:
            print(f"\n[PRIORITY] Modules needing manual attention:")
            for file_path, status in sorted(priority_modules.items()):
                status_icon = {
                    'new_module': '[NEW]',
                    'needs_enhancement': '[ENH]',
                    'dependencies_changed': '[CHG]'
                }.get(status, '[?]')
                print(ensure_ascii(f"   {status_icon} {file_path} ({status})"))
        
        return True
        
    except Exception as e:
        print(ensure_ascii(f"[ERROR] Failed to write development_docs/MODULE_DEPENDENCIES_DETAIL.md: {e}"))
        return False

if __name__ == "__main__":
    update_module_dependencies() 
