#!/usr/bin/env python3
"""
Generate and update FUNCTION_REGISTRY.md automatically.
Scans all .py files and creates comprehensive function documentation.
Enhanced with automatic template generation for various function types.
"""

import ast
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Ensure we can import from ai_development_tools
# Add parent directory to path if running as script
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Add project root to path for core module imports
project_root = Path(_parent_dir)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("ai_development_tools")

def detect_function_type(file_path: str, func_name: str, decorators: List[str], args: List[str]) -> str:
    """Detect the type of function for template generation."""
    file_lower = file_path.lower()
    func_lower = func_name.lower()
    
    # Auto-generated Qt functions
    if file_lower.startswith('ui/generated/') and func_name == 'qtTrId':
        return 'qt_translation'
    
    # Auto-generated UI setup functions
    if file_lower.startswith('ui/generated/') and func_name in ['setupUi', 'retranslateUi']:
        return 'ui_generated'
    
    # Test functions
    if func_lower.startswith('test_') or 'test' in func_lower:
        return 'test_function'
    
    # Special Python methods
    if func_name.startswith('__') and func_name.endswith('__'):
        return 'special_method'
    
    # Constructor methods
    if func_name == '__init__':
        return 'constructor'
    
    # Main functions
    if func_name == 'main':
        return 'main_function'
    
    return 'regular_function'

def generate_function_template(func_type: str, func_name: str, file_path: str, args: List[str]) -> str:
    """Generate appropriate documentation template based on function type."""
    
    if func_type == 'qt_translation':
        return "Auto-generated Qt translation function for internationalization support"
    
    elif func_type == 'ui_generated':
        if func_name == 'setupUi':
            return f"Auto-generated Qt UI setup function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"
        elif func_name == 'retranslateUi':
            return f"Auto-generated Qt UI translation function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"
        else:
            return f"Auto-generated Qt UI function for {file_path.split('/')[-1].replace('_pyqt.py', '')}"
    
    elif func_type == 'test_function':
        # Extract test scenario from function name
        test_name = func_name.replace('test_', '').replace('_', ' ')
        if 'real_behavior' in func_name:
            return f"REAL BEHAVIOR TEST: {test_name.title()}"
        elif 'integration' in func_name:
            return f"INTEGRATION TEST: {test_name.title()}"
        elif 'unit' in func_name:
            return f"UNIT TEST: {test_name.title()}"
        else:
            return f"Test {test_name.title()}"
    
    elif func_type == 'special_method':
        if func_name == '__init__':
            return "Initialize the object"
        elif func_name == '__new__':
            return "Create a new instance"
        elif func_name == '__post_init__':
            return "Post-initialization setup"
        elif func_name == '__enter__':
            return "Context manager entry"
        elif func_name == '__exit__':
            return "Context manager exit"
        else:
            return f"Special Python method: {func_name}"
    
    elif func_type == 'constructor':
        return "Initialize the object"
    
    elif func_type == 'main_function':
        return "Main entry point for the module"
    
    else:
        return "No description"

def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract all function definitions from a Python file."""
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function signature
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                
                # Get decorators
                decorators = []
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorators.append(decorator.id)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            decorators.append(decorator.func.id)
                
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                # Detect function type
                func_type = detect_function_type(file_path, node.name, decorators, args)
                
                # Generate template if no docstring exists
                if not docstring.strip() and func_type != 'regular_function':
                    docstring = generate_function_template(func_type, node.name, file_path, args)
                
                # Check if it's a test function
                is_test = node.name.startswith('test_') or 'test' in node.name.lower()
                
                # Check if it's a main function
                is_main = node.name == 'main' or node.name == '__main__'
                
                # Get function complexity (rough estimate)
                complexity = len(list(ast.walk(node)))
                
                # Check if it's a handler/utility function
                is_handler = any(keyword in node.name.lower() for keyword in ['handle', 'process', 'validate', 'check', 'get', 'set', 'save', 'load'])
                
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': args,
                    'decorators': decorators,
                    'docstring': docstring,
                    'func_type': func_type,
                    'is_test': is_test,
                    'is_main': is_main,
                    'complexity': complexity,
                    'has_docstring': bool(docstring.strip()),
                    'is_handler': is_handler,
                    'arg_count': len(args),
                    'has_template': func_type != 'regular_function' and not ast.get_docstring(node)
                })
                
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return functions

def extract_classes_from_file(file_path: str) -> List[Dict]:
    """Extract all class definitions from a Python file."""
    classes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class methods
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        # Get method arguments
                        args = [arg.arg for arg in child.args.args]
                        
                        # Get decorators
                        decorators = []
                        for d in child.decorator_list:
                            if isinstance(d, ast.Name):
                                decorators.append(d.id)
                            elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                                decorators.append(d.func.id)
                            else:
                                decorators.append(str(d))
                        
                        # Get original docstring
                        original_docstring = ast.get_docstring(child)
                        
                        # Detect method type
                        method_type = detect_function_type(file_path, child.name, decorators, args)
                        
                        # Generate template if no docstring exists
                        docstring = original_docstring or ""
                        if not docstring.strip() and method_type != 'regular_function':
                            docstring = generate_function_template(method_type, child.name, file_path, args)
                        
                        methods.append({
                            'name': child.name,
                            'line': child.lineno,
                            'args': args,
                            'decorators': decorators,
                            'docstring': docstring,
                            'method_type': method_type,
                            'has_docstring': bool(docstring.strip()),
                            'has_template': method_type != 'regular_function' and not original_docstring
                        })
                
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods,
                    'docstring': ast.get_docstring(node)
                })
                
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    
    return classes

def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract function/class information."""
    # Import config - try relative import first, fallback to absolute
    try:
        from . import config
    except ImportError:
        import config
    from ai_development_tools.services.standard_exclusions import should_exclude_file
    project_root = config.get_project_root()
    results = {}
    
    # Directories to scan from configuration
    scan_dirs = config.get_scan_directories()
    
    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob('*.py'):
            # Use production context exclusions to match audit behavior
            if should_exclude_file(str(py_file), 'analysis', 'production'):
                continue
                
            relative_path = py_file.relative_to(project_root)
            file_key = str(relative_path).replace('\\', '/')
            
            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))
            
            results[file_key] = {
                'functions': functions,
                'classes': classes,
                'total_functions': len(functions),
                'total_classes': len(classes)
            }
    
    # Also scan root directory for .py files
    for py_file in project_root.glob('*.py'):
        if py_file.name in ['generate_function_registry.py', 'generate_module_dependencies.py']:
            continue
        # Include run_mhm.py and run_tests.py in registry even though they're in exclusions
        # They are important entry points and should be documented
        if py_file.name in ['run_mhm.py', 'run_tests.py']:
            file_key = py_file.name
            functions = extract_functions_from_file(str(py_file))
            classes = extract_classes_from_file(str(py_file))
            results[file_key] = {
                'functions': functions,
                'classes': classes,
                'total_functions': len(functions),
                'total_classes': len(classes)
            }
            continue
        # Use production context exclusions to match audit behavior
        if should_exclude_file(str(py_file), 'analysis', 'production'):
            continue
        file_key = py_file.name
        
        functions = extract_functions_from_file(str(py_file))
        classes = extract_classes_from_file(str(py_file))
        
        results[file_key] = {
            'functions': functions,
            'classes': classes,
            'total_functions': len(functions),
            'total_classes': len(classes)
        }
    
    return results

def generate_function_registry_content(actual_functions: Dict[str, Dict]) -> str:
    """Generate the complete FUNCTION_REGISTRY_DETAIL.md content."""
    
    # Calculate statistics
    total_files = len(actual_functions)
    total_functions = sum(data['total_functions'] for data in actual_functions.values())
    total_classes = sum(data['total_classes'] for data in actual_functions.values())
    total_methods = sum(len(cls['methods']) for data in actual_functions.values() for cls in data['classes'])
    
    # Function documentation stats
    documented_functions = sum(1 for data in actual_functions.values() 
                              for func in data['functions'] if func['has_docstring'])
    template_functions = sum(1 for data in actual_functions.values() 
                            for func in data['functions'] if func.get('has_template', False))
    
    # Method documentation stats
    documented_methods = sum(1 for data in actual_functions.values() 
                            for cls in data['classes'] 
                            for method in cls['methods'] if method['has_docstring'])
    template_methods = sum(1 for data in actual_functions.values() 
                          for cls in data['classes'] 
                          for method in cls['methods'] if method.get('has_template', False))
    
    # Class documentation stats
    documented_classes = sum(1 for data in actual_functions.values() 
                            for cls in data['classes'] if cls['docstring'])
    
    # Total coverage
    total_items = total_functions + total_methods
    documented_items = documented_functions + documented_methods
    template_items = template_functions + template_methods
    coverage_percentage = (documented_items / total_items * 100) if total_items > 0 else 0
    
    # Generate header
    content = f"""# Function Registry - MHM Project

> **Generated**: This file is auto-generated by generate_function_registry.py. Do not edit manually.
> **Generated by**: generate_function_registry.py - Function Registry Generator
> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Source**: `python ai_development_tools/generate_function_registry.py`

> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete registry of all functions and classes in the MHM codebase  
> **Status**: **ACTIVE** - Auto-generated from codebase analysis with template enhancement

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](../ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](../TODO.md) for current documentation priorities**

## 📋 **Overview**

### **Function Documentation Coverage: {coverage_percentage:.1f}% {'✅ COMPLETED' if coverage_percentage >= 95 else '⚠️ NEEDS ATTENTION' if coverage_percentage >= 50 else '❌ CRITICAL GAP'}**
- **Files Scanned**: {total_files}
- **Functions Found**: {total_functions}
- **Methods Found**: {total_methods}
- **Classes Found**: {total_classes}
- **Total Items**: {total_items}
- **Functions Documented**: {documented_functions}
- **Methods Documented**: {documented_methods}
- **Classes Documented**: {documented_classes}
- **Total Documented**: {documented_items}
- **Template-Generated**: {template_items}
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

**Status**: {'✅ **EXCELLENT** - All functions have proper documentation' if coverage_percentage >= 95 else '⚠️ **GOOD** - Most functions documented, some gaps remain' if coverage_percentage >= 50 else '❌ **CRITICAL GAP** - Many functions lack documentation'}

**Template Enhancement**: This registry now includes automatic template generation for:
- **Auto-generated Qt functions** (qtTrId, setupUi, retranslateUi)
- **Test functions** (with scenario-based descriptions)
- **Special Python methods** (__init__, __new__, __post_init__, etc.)
- **Constructor methods** and **main functions**

**Note**: This registry is automatically generated from the actual codebase. Functions without docstrings are marked as needing documentation. Template-generated documentation is applied to improve coverage.

## 🔍 **Function Categories**

### **Core System Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('core/'))})
Core system utilities, configuration, error handling, and data management functions.

### **Communication Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('communication/'))})
Bot implementations, channel management, and communication utilities.

### **User Interface Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('ui/'))})
UI dialogs, widgets, and user interaction functions.

### **User Management Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('user/'))})
User context, preferences, and data management functions.

### **Task Management Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('tasks/'))})
Task management and scheduling functions.

### **Test Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('tests/'))})
Test functions and testing utilities.

## 📁 **Module Organization**

"""
    
    # Group files by directory
    dir_files = {}
    for file_path, data in actual_functions.items():
        dir_name = file_path.split('/')[0] if '/' in file_path else 'root'
        if dir_name not in dir_files:
            dir_files[dir_name] = []
        dir_files[dir_name].append((file_path, data))
    
    # Generate content for each directory
    for dir_name in sorted(dir_files.keys()):
        content += f"### `{dir_name}/` - {get_directory_description(dir_name)}\n\n"
        
        for file_path, data in sorted(dir_files[dir_name], key=lambda x: x[0]):
            content += generate_file_section(file_path, data)
    
    return content

def get_directory_description(dir_name: str) -> str:
    """Get a description for a directory."""
    descriptions = {
        'core': 'Core System Modules',
        'communication': 'Communication Channel Implementations', 
        'ui': 'User Interface Components',
        'user': 'User Data and Context',
        'tasks': 'Task Management',
        'tests': 'Test Files',
        'root': 'Root Files'
    }
    return descriptions.get(dir_name, 'Unknown Directory')

def generate_file_section(file_path: str, data: Dict) -> str:
    """Generate a section for a single file."""
    content = f"#### `{file_path}`\n"
    
    # Functions
    if data['functions']:
        content += "**Functions:**\n"
        for func in sorted(data['functions'], key=lambda x: x['name']):
            args_str = ', '.join(func['args'])
            doc_status = "✅" if func['has_docstring'] else "❌"
            content += f"- {doc_status} `{func['name']}({args_str})` - {func['docstring'] or 'No description'}\n"
    
    # Classes
    if data['classes']:
        content += "**Classes:**\n"
        for cls in sorted(data['classes'], key=lambda x: x['name']):
            doc_status = "✅" if cls['docstring'] else "❌"
            content += f"- {doc_status} `{cls['name']}` - {cls['docstring'] or 'No description'}\n"
            for method in sorted(cls['methods'], key=lambda x: x['name']):
                args_str = ', '.join(method['args'])
                method_doc_status = "✅" if method['has_docstring'] else "❌"
                content += f"  - {method_doc_status} `{cls['name']}.{method['name']}({args_str})` - {method['docstring'] or 'No description'}\n"
    
    content += "\n"
    return content

def generate_ai_function_registry_content(actual_functions: Dict[str, Dict]) -> str:
    """Generate AI-optimized function registry content focusing on patterns and decision trees."""
    
    # Calculate statistics
    total_files = len(actual_functions)
    total_functions = sum(data['total_functions'] for data in actual_functions.values())
    total_classes = sum(data['total_classes'] for data in actual_functions.values())
    total_methods = sum(len(cls['methods']) for data in actual_functions.values() for cls in data['classes'])
    
    # Function documentation stats
    documented_functions = sum(1 for data in actual_functions.values() 
                              for func in data['functions'] if func['has_docstring'])
    documented_methods = sum(1 for data in actual_functions.values() 
                            for cls in data['classes'] 
                            for method in cls['methods'] if method['has_docstring'])
    
    total_items = total_functions + total_methods
    documented_items = documented_functions + documented_methods
    coverage_percentage = (documented_items / total_items * 100) if total_items > 0 else 0
    
    # Analyze patterns
    patterns = analyze_function_patterns(actual_functions)
    
    # Find files needing attention
    needing_attention = find_files_needing_attention(actual_functions, threshold=0.8)
    high_priority = [f for f in needing_attention if f['coverage'] < 0.5 or f['missing'] >= 5]
    medium_priority = [f for f in needing_attention if f not in high_priority]
    
    # Generate dynamic pattern section
    pattern_section = generate_pattern_section(patterns, actual_functions)
    
    # Generate dynamic entry points section
    entry_points_section = generate_entry_points_section(patterns, actual_functions)
    
    # Generate dynamic common operations section
    common_operations_section = generate_common_operations_section(actual_functions, patterns)
    
    # Generate complexity metrics section
    complexity_section = generate_complexity_section(actual_functions)
    
    # Generate dynamic file organization section
    file_organization_section = generate_file_organization_section(actual_functions)
    
    # Generate dynamic communication patterns section
    communication_patterns_section = generate_communication_patterns_section(patterns, actual_functions)
    
    # Generate dynamic decision trees (using ASCII tree characters)
    user_data_tree = f"""User Data Operations Decision Tree:
+-- Core Data Access
|   +-- {format_file_entry('core/user_data_handlers.py', 'Primary data access', actual_functions)}
|   +-- {format_file_entry('core/user_data_manager.py', 'Data management', actual_functions)}
|   `-- {format_file_entry('core/user_data_validation.py', 'Validation', actual_functions)}
+-- User Context
|   +-- {format_file_entry('user/user_context.py', 'User context management', actual_functions)}
|   `-- {format_file_entry('user/user_preferences.py', 'User preferences', actual_functions)}
`-- User Management
    `-- {format_file_entry('core/user_management.py', 'Account operations', actual_functions)}
"""
    
    ai_tree = f"""AI Operations Decision Tree:
+-- AI Chatbot
|   +-- {format_file_entry('ai/chatbot.py', 'Main AI implementation', actual_functions)}
|   `-- {format_file_entry('user/context_manager.py', 'Context for AI', actual_functions)}
+-- Command Parsing
|   +-- {format_file_entry('communication/message_processing/command_parser.py', 'Natural language parsing', actual_functions)}
|   `-- {format_file_entry('communication/command_handlers/interaction_handlers.py', 'Command handlers', actual_functions)}
`-- Interaction Management
    `-- {format_file_entry('communication/message_processing/interaction_manager.py', 'Main interaction flow', actual_functions)}
"""
    
    comm_tree = f"""Communication Decision Tree:
+-- Channel Management
|   +-- {format_file_entry('communication/core/channel_orchestrator.py', 'Main communication', actual_functions)}
|   +-- {format_file_entry('communication/communication_channels/base/base_channel.py', 'Channel base class', actual_functions)}
|   `-- {format_file_entry('communication/core/factory.py', 'Channel creation', actual_functions)}
+-- Specific Channels
|   +-- {format_file_entry('communication/communication_channels/discord/bot.py', 'Discord integration', actual_functions)}
|   `-- {format_file_entry('communication/communication_channels/email/bot.py', 'Email integration', actual_functions)}
`-- Conversation Flow
    `-- {format_file_entry('communication/message_processing/conversation_flow_manager.py', 'Conversation management', actual_functions)}
"""
    
    ui_tree = f"""UI Operations Decision Tree:
+-- Main Application
|   `-- {format_file_entry('ui/ui_app_qt.py', 'Main admin interface', actual_functions)}
+-- Dialogs
|   +-- {format_file_entry('ui/dialogs/account_creator_dialog.py', 'Account creation', actual_functions)}
|   +-- {format_file_entry('ui/dialogs/user_profile_dialog.py', 'User profiles', actual_functions)}
|   +-- {format_file_entry('ui/dialogs/task_management_dialog.py', 'Task management', actual_functions)}
|   `-- {format_file_entry('ui/dialogs/schedule_editor_dialog.py', 'Schedule editing', actual_functions)}
`-- Widgets
    +-- {format_file_entry('ui/widgets/tag_widget.py', 'Tag management', actual_functions)}
    +-- {format_file_entry('ui/widgets/task_settings_widget.py', 'Task settings', actual_functions)}
    `-- {format_file_entry('ui/widgets/user_profile_settings_widget.py', 'Profile settings', actual_functions)}
"""
    
    core_tree = f"""Core System Decision Tree:
+-- Configuration
|   `-- {format_file_entry('core/config.py', 'System configuration', actual_functions)}
+-- Error Handling
|   `-- {format_file_entry('core/error_handling.py', 'Error management', actual_functions)}
+-- File Operations
|   +-- {format_file_entry('core/file_operations.py', 'File I/O', actual_functions)}
|   `-- {format_file_entry('core/backup_manager.py', 'Backup operations', actual_functions)}
+-- Logging
|   `-- {format_file_entry('core/logger.py', 'Logging system', actual_functions)}
`-- Scheduling
    +-- {format_file_entry('core/scheduler.py', 'Task scheduling', actual_functions)}
    `-- {format_file_entry('core/schedule_management.py', 'Schedule management', actual_functions)}
"""
    
    # Generate dynamic "Areas Needing Attention" section
    high_priority_section = ""
    if high_priority:
        high_priority_section = "### **High Priority** (Missing Documentation)\n"
        for item in high_priority[:10]:  # Top 10
            high_priority_section += f"- `{item['file']}` - {item['missing']}/{item['total']} functions undocumented ({item['coverage']*100:.0f}% coverage)\n"
        high_priority_section += "\n"
    
    medium_priority_section = ""
    if medium_priority:
        medium_priority_section = "### **Medium Priority** (Partial Coverage)\n"
        for item in medium_priority[:10]:  # Top 10
            medium_priority_section += f"- `{item['file']}` - {item['missing']}/{item['total']} functions undocumented ({item['coverage']*100:.0f}% coverage)\n"
        medium_priority_section += "\n"
    
    attention_section = "## [!] **Areas Needing Attention**\n\n"
    if high_priority_section or medium_priority_section:
        attention_section += high_priority_section + medium_priority_section
    else:
        attention_section += "[OK] **All files have excellent documentation coverage (>80%)**\n\n"
    
    status_indicator = '[OK] EXCELLENT' if coverage_percentage >= 95 else '[!] GOOD' if coverage_percentage >= 50 else '[X] NEEDS WORK'
    
    content = f"""# AI Function Registry - Key Patterns & Decision Trees

> **Generated**: This file is auto-generated by generate_function_registry.py. Do not edit manually.
> **Generated by**: generate_function_registry.py - Function Registry Generator
> **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Source**: `python ai_development_tools/generate_function_registry.py`

> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## [*] **Current Status**

### **Documentation Coverage: {coverage_percentage:.1f}% {status_indicator}**
- **Total Functions**: {total_functions}
- **Total Methods**: {total_methods}
- **Documented**: {documented_items}/{total_items}
- **Files Scanned**: {total_files}

## [DECISION TREES] **Decision Trees for AI Context**

### **[USER DATA] Need to Handle User Data?**
```
{user_data_tree}```

### **[AI] Need AI/Chatbot Functionality?**
```
{ai_tree}```

### **[COMM] Need Communication/Channels?**
```
{comm_tree}```

### **[UI] Need UI/User Interface?**
```
{ui_tree}```

### **[CORE] Need Core System Operations?**
```
{core_tree}```

## [PATTERNS] **Key Function Patterns**

{pattern_section}

## [ENTRY POINTS] **Critical Functions for AI Context**

### **Entry Points** (Start Here)
{entry_points_section}

### **Data Access Patterns**
- **User Data**: {format_file_entry('core/user_data_handlers.py', 'User data operations', actual_functions)}
- **Validation**: {format_file_entry('core/user_data_validation.py', 'Data validation', actual_functions)}
- **File Operations**: {format_file_entry('core/file_operations.py', 'File I/O', actual_functions)}

### **Communication Patterns**
{communication_patterns_section}

{attention_section}

## [QUICK REF] **Quick Reference for AI**

### **Common Operations**
{common_operations_section}

{complexity_section}

### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
{file_organization_section}

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md)**  
> **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return content

def get_file_stats(file_path: str, actual_functions: Dict[str, Dict]) -> Dict[str, int]:
    """Get statistics for a specific file from actual_functions."""
    if file_path not in actual_functions:
        return {'total': 0, 'documented': 0, 'functions': 0, 'methods': 0}
    
    data = actual_functions[file_path]
    total_functions = len(data['functions'])
    total_methods = sum(len(cls['methods']) for cls in data['classes'])
    total = total_functions + total_methods
    
    documented_functions = sum(1 for func in data['functions'] if func['has_docstring'])
    documented_methods = sum(1 for cls in data['classes'] 
                            for method in cls['methods'] if method['has_docstring'])
    documented = documented_functions + documented_methods
    
    return {
        'total': total,
        'documented': documented,
        'functions': total_functions,
        'methods': total_methods
    }

def format_file_entry(file_path: str, description: str, actual_functions: Dict[str, Dict]) -> str:
    """Format a file entry with dynamic function counts."""
    stats = get_file_stats(file_path, actual_functions)
    if stats['total'] == 0:
        return f"`{file_path}` - {description}"
    
    if stats['documented'] == stats['total']:
        return f"`{file_path}` - {description} ({stats['total']} functions)"
    else:
        return f"`{file_path}` - {description} ({stats['documented']}/{stats['total']} functions)"

def find_files_needing_attention(actual_functions: Dict[str, Dict], threshold: float = 0.8) -> List[Dict]:
    """Find files that need documentation attention (below threshold coverage)."""
    needing_attention = []
    
    for file_path, data in actual_functions.items():
        total_functions = len(data['functions'])
        total_methods = sum(len(cls['methods']) for cls in data['classes'])
        total = total_functions + total_methods
        
        if total == 0:
            continue
        
        documented_functions = sum(1 for func in data['functions'] if func['has_docstring'])
        documented_methods = sum(1 for cls in data['classes'] 
                                for method in cls['methods'] if method['has_docstring'])
        documented = documented_functions + documented_methods
        
        coverage = documented / total if total > 0 else 0.0
        
        if coverage < threshold:
            missing = total - documented
            needing_attention.append({
                'file': file_path,
                'total': total,
                'documented': documented,
                'missing': missing,
                'coverage': coverage
            })
    
    # Sort by missing count (descending), then by coverage (ascending)
    needing_attention.sort(key=lambda x: (-x['missing'], x['coverage']))
    
    return needing_attention

def generate_pattern_section(patterns: Dict[str, List], actual_functions: Dict[str, Dict]) -> str:
    """Generate dynamic pattern section based on ALL detected patterns - concise and high-signal."""
    section = ""
    
    # Pattern definitions with concise descriptions
    pattern_defs = {
        'handlers': {
            'title': 'Handler Pattern',
            'purpose': 'Handle specific user intents or operations',
            'pattern': ['`can_handle(intent)` - Check if handler supports intent', '`handle(user_id, parsed_command)` - Process the command', '`get_help()` - Return help text'],
            'min_examples': 3
        },
        'managers': {
            'title': 'Manager Pattern',
            'purpose': 'Centralized management of system components',
            'pattern': ['Singleton instance management', 'Lifecycle methods (`start()`, `stop()`, `initialize()`)', 'Status reporting methods'],
            'min_examples': 3
        },
        'factories': {
            'title': 'Factory Pattern',
            'purpose': 'Create instances of related objects',
            'pattern': ['`register_*(name, class)` - Register types', '`create_*(name, config)` - Create instances', '`get_available_*()` - List available types'],
            'min_examples': 2
        },
        'widgets': {
            'title': 'Widget Pattern',
            'purpose': 'Reusable UI components',
            'pattern': ['Inherit from QWidget', 'Implement `get_*()` and `set_*()` methods', 'Signal-based updates'],
            'min_examples': 3
        },
        'dialogs': {
            'title': 'Dialog Pattern',
            'purpose': 'Modal user interaction windows',
            'pattern': ['Inherit from QDialog', 'Use widgets for data entry', 'Return result on accept/reject'],
            'min_examples': 3
        },
        'validators': {
            'title': 'Validator Pattern',
            'purpose': 'Data validation and sanitization',
            'pattern': ['`validate_*(data)` - Validate input', 'Return validation results', 'Centralized validation logic'],
            'min_examples': 2
        },
        'schemas': {
            'title': 'Schema Pattern',
            'purpose': 'Data models with validation (Pydantic)',
            'pattern': ['Pydantic BaseModel classes', 'Type-safe data structures', 'Automatic validation'],
            'min_examples': 2
        },
        'context_managers': {
            'title': 'Context Manager Pattern',
            'purpose': 'Safe resource management',
            'pattern': ['`__enter__()` and `__exit__()` methods', 'Automatic cleanup', 'Used with `with` statements'],
            'min_examples': 2
        },
        'decorators': {
            'title': 'Decorator Pattern',
            'purpose': 'Function/method decoration (error handling, logging)',
            'pattern': ['`@handle_errors` - Error handling decorator', '`@<name>` - Custom decorators', 'Applied to functions/methods'],
            'min_examples': 1
        }
    }
    
    # Generate sections for all detected patterns (in priority order)
    pattern_order = ['handlers', 'managers', 'factories', 'widgets', 'dialogs', 'validators', 'schemas', 'context_managers', 'decorators']
    
    for pattern_key in pattern_order:
        if patterns.get(pattern_key) and len(patterns[pattern_key]) > 0:
            pattern_list = patterns[pattern_key]
            pattern_def = pattern_defs.get(pattern_key, {})
            
            count = len(pattern_list)
            # Get unique files and classes (prioritize files with documentation)
            items_with_doc = [p for p in pattern_list if p.get('has_doc', False)]
            items_without_doc = [p for p in pattern_list if not p.get('has_doc', False)]
            sorted_items = items_with_doc + items_without_doc
            
            # Get unique files (top 3)
            unique_files = []
            seen_files = set()
            for item in sorted_items:
                file_path = item.get('file', '')
                if file_path and file_path not in seen_files:
                    unique_files.append(file_path)
                    seen_files.add(file_path)
                    if len(unique_files) >= 3:
                        break
            
            locations = ", ".join([f"`{f}`" for f in unique_files[:3]])
            if len(seen_files) > 3:
                locations += f" (+{len(seen_files)-3} more)"
            
            # Get class/function names (top examples)
            if 'class' in pattern_list[0]:
                examples = sorted_items[:pattern_def.get('min_examples', 3)]
                example_text = "\n".join([f"- `{ex['class']}` ({ex['file']})" for ex in examples])
                if len(sorted_items) > pattern_def.get('min_examples', 3):
                    example_text += f"\n- ... and {len(sorted_items) - pattern_def.get('min_examples', 3)} more"
            else:
                examples = sorted_items[:pattern_def.get('min_examples', 3)]
                example_text = "\n".join([f"- `{ex.get('function', ex.get('class', 'unknown'))}` ({ex['file']})" for ex in examples])
                if len(sorted_items) > pattern_def.get('min_examples', 3):
                    example_text += f"\n- ... and {len(sorted_items) - pattern_def.get('min_examples', 3)} more"
            
            pattern_lines = "\n".join([f"- {p}" for p in pattern_def.get('pattern', [])])
            
            section += f"""### **{pattern_def.get('title', pattern_key)}** ({count} found)
**Purpose**: {pattern_def.get('purpose', 'Pattern implementation')}
**Location**: {locations}
**Pattern**: 
{pattern_lines}

**Examples**:
{example_text}

"""
    
    return section

def generate_entry_points_section(patterns: Dict[str, List], actual_functions: Dict[str, Dict]) -> str:
    """Generate dynamic entry points section from detected entry points."""
    # Separate entry points by priority (higher priority functions first)
    priority_functions = ['handle_message', 'generate_response', 'main']
    regular_entry_points = []
    init_entry_points = []
    
    # Track seen file/function combinations to avoid duplicates
    seen = set()
    
    for ep in patterns['entry_points']:
        file_path = ep['file']
        func_name = ep['function']
        key = (file_path, func_name)
        
        if key in seen:
            continue
        seen.add(key)
        
        has_doc = "[OK]" if ep.get('has_doc', False) else "[X]"
        
        # Get description based on function name
        descriptions = {
            'handle_message': 'Main message entry point',
            'generate_response': 'AI response generation',
            'main': 'Application entry point',
            '__init__': 'Initialization'
        }
        description = descriptions.get(func_name, 'Entry point')
        
        entry_point = f"- {has_doc} `{file_path}::{func_name}()` - {description}"
        
        if func_name in priority_functions:
            regular_entry_points.append((priority_functions.index(func_name), entry_point))
        elif func_name == '__init__':
            # Only include __init__ from important entry point files
            important_files = ['ui/ui_app_qt.py', 'run_mhm.py', 'run_headless_service.py', 'run_tests.py']
            if any(imp_file in file_path for imp_file in important_files):
                init_entry_points.append(entry_point)
        else:
            regular_entry_points.append((999, entry_point))
    
    # Sort priority functions by their priority index, then others
    regular_entry_points.sort(key=lambda x: x[0])
    entry_points = [ep[1] for ep in regular_entry_points] + init_entry_points[:3]  # Max 3 init entries
    
    # If we don't have enough meaningful entry points, add some common ones
    if len(entry_points) < 4:
        common_entry_points = [
            "[OK] `communication/message_processing/interaction_manager.py::handle_message()` - Main message entry point",
            "[OK] `ai/chatbot.py::generate_response()` - AI response generation",
            "[OK] `core/user_data_handlers.py::get_user_data()` - User data access",
            "[OK] `ui/ui_app_qt.py::__init__()` - UI application startup"
        ]
        for common in common_entry_points:
            if common not in entry_points:
                entry_points.append(common)
    
    return "\n".join(entry_points[:10])  # Top 10 entry points

def generate_common_operations_section(actual_functions: Dict[str, Dict], patterns: Dict[str, List]) -> str:
    """Generate dynamic common operations section - comprehensive and based on actual patterns."""
    found_ops = {}
    
    # Priority 1: Entry points (most common operations)
    for ep in patterns.get('entry_points', []):
        func_name = ep['function']
        file_path = ep['file']
        if func_name == 'handle_message':
            found_ops['User Message'] = f"`{file_path}::{func_name}()`"
        elif func_name == 'generate_response':
            found_ops['AI Response'] = f"`{file_path}::{func_name}()`"
        elif func_name == 'main' and 'run_' in file_path:
            if 'Main Entry' not in found_ops:
                found_ops['Main Entry'] = f"`{file_path}::{func_name}()`"
    
    # Priority 2: Data access operations (skip internal helpers)
    for da in patterns.get('data_access', [])[:10]:
        func_name = da['function']
        file_lower = func_name.lower()
        # Skip internal helper functions (double underscore prefix or internal patterns)
        if func_name.startswith('_') and '__' in func_name:
            continue
        if 'get_user_data' in func_name or (func_name == 'get_user_data' or 'get_user' in func_name and not func_name.startswith('_')):
            if 'User Data Access' not in found_ops:
                found_ops['User Data Access'] = f"`{da['file']}::{func_name}()`"
        elif 'save_user' in func_name or ('save' in func_name and 'user' in da['file'] and not func_name.startswith('_')):
            if 'User Data Save' not in found_ops:
                found_ops['User Data Save'] = f"`{da['file']}::{func_name}()`"
        elif 'load' in func_name and 'user' in da['file'] and not func_name.startswith('_'):
            if 'User Data Load' not in found_ops:
                found_ops['User Data Load'] = f"`{da['file']}::{func_name}()`"
    
    # Priority 3: Communication operations
    for comm in patterns.get('communication', [])[:5]:
        func_name = comm['function']
        func_lower = func_name.lower()
        if 'send_' in func_lower and 'message' not in found_ops:
            found_ops['Send Message'] = f"`{comm['file']}::{func_name}()`"
        elif 'receive' in func_lower and 'Receive Message' not in found_ops:
            found_ops['Receive Message'] = f"`{comm['file']}::{func_name}()`"
    
    # Priority 4: Error handling
    for eh in patterns.get('error_handlers', [])[:3]:
        if 'Error Handling' not in found_ops:
            found_ops['Error Handling'] = f"`{eh['file']}::{eh['function']}()`"
    
    # Priority 5: Scheduling operations (skip internal helpers)
    for sched in patterns.get('schedulers', [])[:5]:
        func_name = sched['function']
        # Skip internal helper functions
        if not func_name.startswith('_') and 'Scheduling' not in found_ops:
            # Prefer scheduler.py over file_operations.py
            if 'scheduler' in sched['file'].lower():
                found_ops['Scheduling'] = f"`{sched['file']}::{func_name}()`"
                break
    
    # Priority 6: Look for common utility functions by searching actual functions
    utility_patterns = {
        'validate': 'Validation',
        'parse_command': 'Command Parsing',
        'get_config': 'Configuration',
        'log': 'Logging'
    }
    
    for file_path, data in actual_functions.items():
        if 'test' in file_path.lower():
            continue
        for func in data['functions']:
            func_name = func['name']
            func_lower = func_name.lower()
            
            # Command parsing (skip internal helpers)
            if (('parse' in func_lower and 'command' in func_lower) or func_name == 'parse_command') and not func_name.startswith('_'):
                if 'Command Parsing' not in found_ops:
                    found_ops['Command Parsing'] = f"`{file_path}::{func_name}()`"
            
            # Validation (skip internal helper functions)
            if 'validate' in func_lower and 'Validation' not in found_ops and 'test' not in func_lower:
                # Skip internal helper functions (those with double underscores or specific patterns)
                if not func_name.startswith('_') and 'validate' in file_path.lower():
                    if 'core' in file_path or 'user_data' in file_path:
                        found_ops['Validation'] = f"`{file_path}::{func_name}()`"
                        break
            
            # Configuration
            if 'get_config' in func_lower or 'get_user_data_dir' in func_lower:
                if 'Configuration' not in found_ops:
                    found_ops['Configuration'] = f"`{file_path}::{func_name}()`"
    
    # Build numbered list with priority order
    priority_order = [
        'User Message', 'AI Response', 'Main Entry',
        'User Data Access', 'User Data Save', 'User Data Load',
        'Send Message', 'Receive Message',
        'Command Parsing', 'Validation',
        'Error Handling', 'Scheduling', 'Configuration'
    ]
    
    numbered_ops = []
    counter = 1
    
    for op_name in priority_order:
        if op_name in found_ops:
            numbered_ops.append(f"{counter}. **{op_name}**: {found_ops[op_name]}")
            counter += 1
    
    # Return all found operations (no fallbacks - dynamic only)
    return "\n".join(numbered_ops) if numbered_ops else "*No common operations detected - patterns may need updating*"

def generate_complexity_section(actual_functions: Dict[str, Dict]) -> str:
    """Generate complexity metrics section showing most complex functions."""
    all_functions = []
    
    # Collect all functions with their complexity
    for file_path, data in actual_functions.items():
        for func in data['functions']:
            all_functions.append({
                'file': file_path,
                'name': func['name'],
                'complexity': func.get('complexity', 0),
                'has_doc': func.get('has_docstring', False)
            })
        
        for cls in data['classes']:
            for method in cls['methods']:
                all_functions.append({
                    'file': file_path,
                    'name': f"{cls['name']}.{method['name']}",
                    'complexity': 0,  # Methods don't track complexity separately
                    'has_doc': method.get('has_docstring', False)
                })
    
    # Find most complex functions (using AST node count as complexity metric)
    complex_functions = sorted([f for f in all_functions if f['complexity'] > 200], 
                               key=lambda x: x['complexity'], reverse=True)[:5]
    
    if not complex_functions:
        return ""
    
    complexity_lines = []
    complexity_lines.append("\n### **Complexity Metrics**")
    complexity_lines.append("Most complex functions (may need refactoring):")
    
    for i, func in enumerate(complex_functions, 1):
        status = "[OK]" if func['has_doc'] else "[!]"
        complexity_lines.append(f"{i}. {status} `{func['file']}::{func['name']}()` - Complexity: {func['complexity']}")
    
    complexity_lines.append("")
    
    return "\n".join(complexity_lines)

def generate_file_organization_section(actual_functions: Dict[str, Dict]) -> str:
    """Generate dynamic file organization section based on actual directory structure."""
    directories = {}
    
    # Organize files by directory
    for file_path in actual_functions.keys():
        parts = file_path.split('/')
        if len(parts) > 1:
            top_dir = parts[0]
        else:
            top_dir = 'root'
        
        if top_dir not in directories:
            directories[top_dir] = {'files': 0, 'functions': 0}
        
        directories[top_dir]['files'] += 1
        data = actual_functions[file_path]
        directories[top_dir]['functions'] += len(data['functions'])
        directories[top_dir]['functions'] += sum(len(cls['methods']) for cls in data['classes'])
    
    # Descriptions for common directories
    descriptions = {
        'core': 'System utilities and data management',
        'communication': 'Communication channels and message processing',
        'ai': 'AI chatbot functionality',
        'ui': 'User interface components',
        'user': 'User context and preferences',
        'tasks': 'Task management system',
        'tests': 'Test suite',
        'scripts': 'Utility scripts'
    }
    
    # Build organization list
    org_lines = []
    priority_dirs = ['core', 'communication', 'ai', 'ui', 'user', 'tasks']
    
    for dir_name in priority_dirs:
        if dir_name in directories:
            desc = descriptions.get(dir_name, '')
            file_count = directories[dir_name]['files']
            func_count = directories[dir_name]['functions']
            org_lines.append(f"- `{dir_name}/` - {desc} ({file_count} files, {func_count} functions)")
    
    # Add any other directories found
    for dir_name in sorted(directories.keys()):
        if dir_name not in priority_dirs and dir_name != 'root':
            desc = descriptions.get(dir_name, '')
            file_count = directories[dir_name]['files']
            func_count = directories[dir_name]['functions']
            org_lines.append(f"- `{dir_name}/` - {desc} ({file_count} files, {func_count} functions)")
    
    return "\n".join(org_lines) if org_lines else "- `core/` - System utilities and data management\n- `communication/` - Communication channels and message processing\n- `ai/` - AI chatbot functionality\n- `ui/` - User interface components\n- `user/` - User context and preferences\n- `tasks/` - Task management system"

def generate_communication_patterns_section(patterns: Dict[str, List], actual_functions: Dict[str, Dict]) -> str:
    """Generate dynamic communication patterns section from detected communication functions."""
    comm_patterns = []
    
    # Find message sending functions - prioritize communication directory
    send_funcs = []
    for c in patterns['communication']:
        if 'send_' in c['function'].lower() and 'test' not in c['function'].lower():
            priority = 2 if 'communication' in c['file'].lower() else 1
            send_funcs.append((priority, c))
    
    # Sort by priority (communication dir first), then by function name
    send_funcs.sort(key=lambda x: (-x[0], x[1]['function']))
    
    if send_funcs:
        send_func = send_funcs[0][1]
        comm_patterns.append(f"- **Message Sending**: `{send_func['file']}::{send_func['function']}()`")
    
    # Find channel status functions - prioritize communication directory
    status_funcs = []
    for c in patterns['communication']:
        func_lower = c['function'].lower()
        if any(kw in func_lower for kw in ['is_', 'status', 'ready']) and 'test' not in func_lower:
            priority = 2 if 'communication' in c['file'].lower() else 1
            status_funcs.append((priority, c))
    
    status_funcs.sort(key=lambda x: (-x[0], x[1]['function']))
    
    if status_funcs:
        status_func = status_funcs[0][1]
        comm_patterns.append(f"- **Channel Status**: `{status_func['file']}::{status_func['function']}()`")
    
    # Look for parse functions in communication files - prioritize command_parser
    parse_funcs = []
    for file_path, data in actual_functions.items():
        file_lower = file_path.lower()
        if 'communication' in file_lower:
            priority = 3 if 'command_parser' in file_lower else 2 if 'message' in file_lower else 1
            for func in data['functions']:
                func_lower = func['name'].lower()
                if func_lower == 'parse' or (func_lower.startswith('parse') and 'timestamp' not in func_lower):
                    parse_funcs.append((priority, {
                        'file': file_path,
                        'function': func['name'],
                        'has_doc': func.get('has_docstring', False)
                    }))
                    break
    
    parse_funcs.sort(key=lambda x: -x[0])
    
    if parse_funcs:
        parse_func = parse_funcs[0][1]
        comm_patterns.append(f"- **Command Parsing**: `{parse_func['file']}::{parse_func['function']}()`")
    
    # Return detected patterns (no fallbacks - dynamic only)
    if comm_patterns:
        return "\n".join(comm_patterns)
    
    # Return empty if no patterns found (no preset text)
    return ""

def analyze_function_patterns(actual_functions: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze function patterns for AI consumption - enhanced with more pattern detection."""
    patterns = {
        'handlers': [],
        'managers': [],
        'factories': [],
        'context_managers': [],
        'widgets': [],
        'dialogs': [],
        'validators': [],
        'decorators': [],
        'schemas': [],
        'entry_points': [],
        'data_access': [],
        'communication': [],
        'error_handlers': [],
        'schedulers': []
    }
    
    for file_path, data in actual_functions.items():
        file_lower = file_path.lower()
        
        # Analyze classes for patterns
        for cls in data['classes']:
            class_name = cls['name']
            methods = [m['name'] for m in cls['methods']]
            decorators = [d for d in cls.get('decorators', [])]
            
            # Handler pattern
            if class_name.endswith('Handler') and ('can_handle' in methods or 'handle' in methods):
                patterns['handlers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Manager pattern
            elif class_name.endswith('Manager') or 'Manager' in class_name:
                if any(m in methods for m in ['start', 'stop', 'initialize', 'shutdown', 'get_instance']):
                    patterns['managers'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Factory pattern
            elif 'Factory' in class_name:
                if any(m in methods for m in ['create', 'register', 'get', 'build']):
                    patterns['factories'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Widget pattern
            elif 'Widget' in class_name or file_lower.endswith('_widget.py'):
                patterns['widgets'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Dialog pattern
            elif 'Dialog' in class_name or file_lower.endswith('_dialog.py'):
                patterns['dialogs'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
            
            # Validator pattern
            elif 'Validator' in class_name or 'validate' in class_name.lower():
                if any('validate' in m.lower() for m in methods):
                    patterns['validators'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Schema pattern (Pydantic models)
            elif 'Schema' in class_name or 'Model' in class_name:
                if any(d in decorators for d in ['BaseModel', 'pydantic']):
                    patterns['schemas'].append({
                        'file': file_path,
                        'class': class_name,
                        'methods': len(methods),
                        'has_doc': cls.get('has_docstring', False)
                    })
            
            # Context manager pattern
            if '__enter__' in methods and '__exit__' in methods:
                patterns['context_managers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods),
                    'has_doc': cls.get('has_docstring', False)
                })
        
        # Analyze functions for patterns
        for func in data['functions']:
            func_name = func['name']
            func_lower = func_name.lower()
            decorators = func.get('decorators', [])
            
            # Entry points
            if func_name in ['handle_message', 'generate_response', 'main', '__init__']:
                patterns['entry_points'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func.get('has_docstring', False)
                })
            
            # Data access
            elif any(keyword in func_lower for keyword in ['get_user', 'save_user', 'load_user', 'save_', 'load_']):
                if 'test' not in file_lower:
                    patterns['data_access'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Communication
            elif any(keyword in func_lower for keyword in ['send_', 'receive_', 'connect_', 'disconnect_', 'message']):
                if 'test' not in file_lower:
                    patterns['communication'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Error handlers
            elif 'handle_errors' in func_lower or 'handle_error' in func_lower:
                if 'test' not in file_lower:
                    patterns['error_handlers'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Schedulers
            elif 'schedule' in func_lower and ('add' in func_lower or 'create' in func_lower or 'run' in func_lower):
                if 'test' not in file_lower:
                    patterns['schedulers'].append({
                        'file': file_path,
                        'function': func_name,
                        'has_doc': func.get('has_docstring', False)
                    })
            
            # Decorators - check if function is used as a decorator
            # Look for functions that are commonly used as decorators
            if func_name in ['handle_errors', 'handle_error', 'log_execution']:
                patterns['decorators'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func.get('has_docstring', False)
                })
    
    return patterns

def update_function_registry():
    """Update FUNCTION_REGISTRY_DETAIL.md and AI_FUNCTION_REGISTRY.md with current codebase analysis."""
    logger.info("[SCAN] Scanning all Python files...")
    actual_functions = scan_all_python_files()
    
    logger.info("[GEN] Generating FUNCTION_REGISTRY_DETAIL.md content...")
    detail_content = generate_function_registry_content(actual_functions)
    
    logger.info("[GEN] Generating AI_FUNCTION_REGISTRY.md content...")
    ai_content = generate_ai_function_registry_content(actual_functions)
    
    # Write DETAIL file
    detail_path = Path(__file__).parent.parent / 'development_docs' / 'FUNCTION_REGISTRY_DETAIL.md'
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(detail_content)
    
    # Write AI file
    ai_path = Path(__file__).parent.parent / 'ai_development_docs' / 'AI_FUNCTION_REGISTRY.md'
    with open(ai_path, 'w', encoding='utf-8') as f:
        f.write(ai_content)
    
    # Calculate statistics
    total_files = len(actual_functions)
    total_functions = sum(data['total_functions'] for data in actual_functions.values())
    total_methods = sum(len(cls['methods']) for data in actual_functions.values() for cls in data['classes'])
    
    # Function documentation stats
    documented_functions = sum(1 for data in actual_functions.values() 
                              for func in data['functions'] if func['has_docstring'])
    template_functions = sum(1 for data in actual_functions.values() 
                            for func in data['functions'] if func.get('has_template', False))
    
    # Method documentation stats
    documented_methods = sum(1 for data in actual_functions.values() 
                            for cls in data['classes'] 
                            for method in cls['methods'] if method['has_docstring'])
    template_methods = sum(1 for data in actual_functions.values() 
                          for cls in data['classes'] 
                          for method in cls['methods'] if method.get('has_template', False))
    
    # Total coverage
    total_items = total_functions + total_methods
    documented_items = documented_functions + documented_methods
    template_items = template_functions + template_methods
    coverage_percentage = (documented_items / total_items * 100) if total_items > 0 else 0
    
    logger.info(f"[SUCCESS] Both function registry files updated successfully!")
    logger.info(f"[FILES] Generated:")
    logger.info(f"   development_docs/FUNCTION_REGISTRY_DETAIL.md - Complete detailed registry")
    logger.info(f"   ai_development_docs/AI_FUNCTION_REGISTRY.md - Concise AI-focused registry")
    logger.info(f"[STATS] Statistics:")
    logger.info(f"   Files scanned: {total_files}")
    logger.info(f"   Functions found: {total_functions}")
    logger.info(f"   Methods found: {total_methods}")
    logger.info(f"   Total items: {total_items}")
    logger.info(f"   Functions documented: {documented_functions}")
    logger.info(f"   Methods documented: {documented_methods}")
    logger.info(f"   Total documented: {documented_items}")
    logger.info(f"   Template-generated: {template_items}")
    logger.info(f"   Coverage: {coverage_percentage:.1f}%")
    logger.info(f"   Detail file: {detail_path}")
    logger.info(f"   AI file: {ai_path}")
    
    # Template breakdown
    if template_items > 0:
        logger.info(f"[TEMPLATES] Template Breakdown:")
        template_types = {}
        for data in actual_functions.values():
            for func in data['functions']:
                if func.get('has_template', False):
                    func_type = func.get('func_type', 'unknown')
                    template_types[func_type] = template_types.get(func_type, 0) + 1
            for cls in data['classes']:
                for method in cls['methods']:
                    if method.get('has_template', False):
                        method_type = method.get('method_type', 'unknown')
                        template_types[method_type] = template_types.get(method_type, 0) + 1
        
        for template_type, count in sorted(template_types.items()):
            logger.info(f"   {template_type}: {count}")

if __name__ == "__main__":
    update_function_registry() 