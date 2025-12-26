#!/usr/bin/env python3
# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""
Generate and update MODULE_DEPENDENCIES_DETAIL.md automatically.
Orchestrates import analysis, pattern analysis, and content generation.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Handle both relative and absolute imports
if __name__ != '__main__' and __package__ and '.' in __package__:
    # Running as part of a package, use relative imports
    from .. import config
    from .analyze_module_imports import (
        ModuleImportAnalyzer,
        find_reverse_dependencies,
        analyze_dependency_changes,
        infer_module_purpose,
        format_import_details
    )
    from .analyze_dependency_patterns import (
        DependencyPatternAnalyzer
    )
    from ..shared.common import ensure_ascii
else:
    # Running directly or not as a package, use absolute imports
    from development_tools import config
    from development_tools.imports.analyze_module_imports import (
        ModuleImportAnalyzer,
        find_reverse_dependencies,
        analyze_dependency_changes,
        infer_module_purpose,
        format_import_details
    )
    from development_tools.imports.analyze_dependency_patterns import (
        DependencyPatternAnalyzer
    )
    from development_tools.shared.common import ensure_ascii

from core.logger import get_component_logger

# Load external config on module import
config.load_external_config()

logger = get_component_logger("development_tools")


# Import analysis functions are now in analyze_module_imports.py
# Pattern analysis functions are now in analyze_dependency_patterns.py


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
    content.append("> **Generated**: This file is auto-generated. Do not edit manually.")
    content.append(ensure_ascii(f"> **Last Generated**: {generated_at}"))
    content.append("> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator")
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

    # Use pattern analyzer for pattern analysis
    pattern_analyzer = DependencyPatternAnalyzer()
    patterns = pattern_analyzer.analyze_dependency_patterns(actual_imports)
    
    # Build decision trees dynamically
    decision_trees = pattern_analyzer.build_dynamic_decision_trees(actual_imports)
    
    # Find critical dependencies dynamically
    critical_deps = pattern_analyzer.find_critical_dependencies(actual_imports)
    
    # Detect risk areas dynamically
    risk_areas = pattern_analyzer.detect_risk_areas(actual_imports, patterns)
    
    lines: List[str] = []
    lines.extend([
        "# AI Module Dependencies - Key Relationships & Patterns",
        "",
        "> **File**: `ai_development_docs/AI_MODULE_DEPENDENCIES.md`",
        "> **Generated**: This file is auto-generated. Do not edit manually.",
        ensure_ascii(f"> **Last Generated**: {generated_at}"),
        "> **Source**: `python development_tools/generate_module_dependencies.py` - Module Dependencies Generator",
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
        pattern_analyzer.generate_dependency_patterns_section(patterns, actual_imports),
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
        pattern_analyzer.generate_quick_reference(actual_imports, patterns),
        "",
        "> **For complete dependency details, see [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md)**",
    ])

    return ensure_ascii("\n".join(lines))


# Pattern analysis functions are now in analyze_dependency_patterns.py

def update_module_dependencies(local_prefixes: Optional[Tuple[str, ...]] = None):
    """
    Update MODULE_DEPENDENCIES_DETAIL.md and AI_MODULE_DEPENDENCIES.md with hybrid approach.
    
    Args:
        local_prefixes: Optional tuple of module prefixes to treat as local.
                       If None, uses LOCAL_MODULE_PREFIXES from constants (loaded from config).
    """
    logger.info("[SCAN] Scanning all Python files for imports...")
    # Use the import analyzer
    import_analyzer = ModuleImportAnalyzer(local_prefixes=local_prefixes)
    actual_imports = import_analyzer.scan_all_python_files()
    
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
    
    # Write the DETAIL file with rotation
    from development_tools.shared.file_rotation import create_output_file
    project_root = Path(__file__).parent.parent.parent
    try:
        create_output_file(str(detail_path), final_detail_content, rotate=True, max_versions=7,
                          project_root=project_root)
        
        # Write the AI file with rotation
        # Script is at: development_tools/imports/generate_module_dependencies.py
        # So we need to go up 2 levels to get to project root
        ai_path = project_root / 'ai_development_docs' / 'AI_MODULE_DEPENDENCIES.md'
        create_output_file(str(ai_path), ai_content, rotate=True, max_versions=7,
                          project_root=project_root)
        
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
