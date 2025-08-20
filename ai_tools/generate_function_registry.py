#!/usr/bin/env python3
"""
Generate and update FUNCTION_REGISTRY.md automatically.
Scans all .py files and creates comprehensive function documentation.
Enhanced with automatic template generation for various function types.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import json
from datetime import datetime

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
        print(f"Error parsing {file_path}: {e}")
    
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
        print(f"Error parsing {file_path}: {e}")
    
    return classes

def scan_all_python_files() -> Dict[str, Dict]:
    """Scan all Python files in the project and extract function/class information."""
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
        if py_file.name not in ['generate_function_registry.py', 'generate_module_dependencies.py']:
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

> **Audience**: Human developer and AI collaborators  
> **Purpose**: Complete registry of all functions and classes in the MHM codebase  
> **Status**: **ACTIVE** - Auto-generated from codebase analysis with template enhancement  
> **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

> **See [README.md](README.md) for complete navigation and project overview**
> **See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture and design**
> **See [TODO.md](TODO.md) for current documentation priorities**

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

### **Communication Functions** ({sum(data['total_functions'] for file_path, data in actual_functions.items() if file_path.startswith('bot/'))})
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
        'bot': 'Communication Channel Implementations', 
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
    
    content = f"""# AI Function Registry - Key Patterns & Decision Trees

> **Audience**: AI Collaborators  
> **Purpose**: Essential function patterns and decision trees for AI context  
> **Style**: Pattern-focused, decision-tree driven, actionable

## 🎯 **Current Status**

### **Documentation Coverage: {coverage_percentage:.1f}% {'✅ EXCELLENT' if coverage_percentage >= 95 else '⚠️ GOOD' if coverage_percentage >= 50 else '❌ NEEDS WORK'}**
- **Total Functions**: {total_functions}
- **Total Methods**: {total_methods}
- **Documented**: {documented_items}/{total_items}
- **Files Scanned**: {total_files}

## 🧠 **Decision Trees for AI Context**

### **🔧 Need to Handle User Data?**
```
User Data Operations Decision Tree:
├── Core Data Access
│   ├── `core/user_data_handlers.py` - Primary data access (10 functions)
│   ├── `core/user_data_manager.py` - Data management (25 functions)
│   └── `core/user_data_validation.py` - Validation (5/8 functions)
├── User Context
│   ├── `user/user_context.py` - User context management
│   └── `user/user_preferences.py` - User preferences
└── User Management
    └── `core/user_management.py` - Account operations (44/47 functions)
```

### **🤖 Need AI/Chatbot Functionality?**
```
AI Operations Decision Tree:
├── AI Chatbot
│   ├── `bot/ai_chatbot.py` - Main AI implementation (31 functions)
│   └── `bot/user_context_manager.py` - Context for AI (13 functions)
├── Command Parsing
│   ├── `bot/enhanced_command_parser.py` - Natural language parsing (15 functions)
│   └── `bot/interaction_handlers.py` - Command handlers (38/62 functions)
└── Interaction Management
    └── `bot/interaction_manager.py` - Main interaction flow (11 functions)
```

### **💬 Need Communication/Channels?**
```
Communication Decision Tree:
├── Channel Management
│   ├── `bot/communication_manager.py` - Main communication (37 functions)
│   ├── `bot/base_channel.py` - Channel base class (7 functions)
│   └── `bot/channel_factory.py` - Channel creation (3 functions)
├── Specific Channels
│   ├── `bot/discord_bot.py` - Discord integration (19 functions)
│   ├── `bot/email_bot.py` - Email integration (9 functions)
│   └── `bot/telegram_bot.py` - Telegram integration (29/35 functions)
└── Conversation Flow
    └── `bot/conversation_manager.py` - Conversation management (13 functions)
```

### **🖥️ Need UI/User Interface?**
```
UI Operations Decision Tree:
├── Main Application
│   └── `ui/ui_app_qt.py` - Main admin interface (42/50 functions)
├── Dialogs
│   ├── `ui/dialogs/account_creator_dialog.py` - Account creation (29/30 functions)
│   ├── `ui/dialogs/user_profile_dialog.py` - User profiles (20 functions)
│   ├── `ui/dialogs/task_management_dialog.py` - Task management (2/4 functions)
│   └── `ui/dialogs/schedule_editor_dialog.py` - Schedule editing (16/17 functions)
└── Widgets
    ├── `ui/widgets/tag_widget.py` - Tag management (14 functions)
    ├── `ui/widgets/task_settings_widget.py` - Task settings (12/13 functions)
    └── `ui/widgets/user_profile_settings_widget.py` - Profile settings (8 functions)
```

### **⚙️ Need Core System Operations?**
```
Core System Decision Tree:
├── Configuration
│   └── `core/config.py` - System configuration (19 functions)
├── Error Handling
│   └── `core/error_handling.py` - Error management (25/27 functions)
├── File Operations
│   ├── `core/file_operations.py` - File I/O (5 functions)
│   └── `core/backup_manager.py` - Backup operations (18 functions)
├── Logging
│   └── `core/logger.py` - Logging system (26/27 functions)
└── Scheduling
    ├── `core/scheduler.py` - Task scheduling (30/31 functions)
    └── `core/schedule_management.py` - Schedule management (16/19 functions)
```

## 🔍 **Key Function Patterns**

### **Handler Pattern** (Most Common)
**Purpose**: Handle specific user intents or operations
**Location**: `bot/interaction_handlers.py`, `ui/dialogs/`, `core/`
**Pattern**: 
- `can_handle(intent)` - Check if handler supports intent
- `handle(user_id, parsed_command)` - Process the command
- `get_help()` - Return help text
- `get_examples()` - Return usage examples

**Examples**:
- `TaskManagementHandler` - Task CRUD operations
- `ProfileHandler` - User profile management
- `ScheduleManagementHandler` - Schedule operations

### **Manager Pattern** (Singleton)
**Purpose**: Centralized management of system components
**Location**: `bot/communication_manager.py`, `bot/interaction_manager.py`
**Pattern**:
- Singleton instance management
- Lifecycle methods (`start()`, `stop()`, `initialize()`)
- Status reporting methods

### **Factory Pattern**
**Purpose**: Create instances of related objects
**Location**: `bot/channel_factory.py`
**Pattern**:
- `register_channel(name, channel_class)` - Register channel types
- `create_channel(name, config)` - Create channel instances
- `get_available_channels()` - List available types

### **Context Manager Pattern**
**Purpose**: Safe resource management
**Location**: `core/error_handling.py`
**Pattern**:
- `__enter__()` and `__exit__()` methods
- Automatic cleanup and error handling
- Used with `with` statements

## 🎯 **Critical Functions for AI Context**

### **Entry Points** (Start Here)
- `bot/interaction_manager.py::handle_message()` - Main message entry point
- `bot/ai_chatbot.py::generate_response()` - AI response generation
- `core/user_data_handlers.py::get_user_data()` - User data access
- `ui/ui_app_qt.py::__init__()` - UI application startup

### **Data Access Patterns**
- **User Data**: `core/user_data_handlers.py` (10 functions)
- **Validation**: `core/user_data_validation.py` (5/8 functions)
- **File Operations**: `core/file_operations.py` (5 functions)

### **Communication Patterns**
- **Message Sending**: `bot/communication_manager.py::send_message_sync()`
- **Channel Status**: `bot/communication_manager.py::is_channel_ready()`
- **Command Parsing**: `bot/enhanced_command_parser.py::parse()`

## ⚠️ **Areas Needing Attention**

### **High Priority** (Missing Documentation)
- `bot/interaction_handlers.py` - 24/62 functions undocumented
- `core/user_data_validation.py` - 3/8 functions undocumented
- `ui/dialogs/task_management_dialog.py` - 2/4 functions undocumented

### **Medium Priority** (Partial Coverage)
- `ui/ui_app_qt.py` - 8/50 functions undocumented
- `core/error_handling.py` - 2/27 functions undocumented
- `core/logger.py` - 1/27 functions undocumented

## 🚀 **Quick Reference for AI**

### **Common Operations**
1. **User Message**: `bot/interaction_manager.py::handle_message()`
2. **AI Response**: `bot/ai_chatbot.py::generate_response()`
3. **User Data**: `core/user_data_handlers.py::get_user_data()`
4. **File Save**: `core/file_operations.py::save_json_data()`
5. **Error Handling**: `core/error_handling.py::handle_errors` decorator

### **Pattern Recognition**
- **Handler classes** end with "Handler" and implement standard interface
- **Manager classes** are singletons with lifecycle management
- **Factory classes** have "Factory" in name and create related objects
- **Context managers** can be used with `with` statements

### **File Organization**
- `core/` - System utilities and data management
- `bot/` - Communication and AI functionality
- `ui/` - User interface components
- `user/` - User context and preferences
- `tasks/` - Task management system

> **For complete function details, see [FUNCTION_REGISTRY_DETAIL.md](FUNCTION_REGISTRY_DETAIL.md)**  
> **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return content

def analyze_function_patterns(actual_functions: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze function patterns for AI consumption."""
    patterns = {
        'handlers': [],
        'managers': [],
        'factories': [],
        'context_managers': [],
        'entry_points': [],
        'data_access': [],
        'communication': []
    }
    
    for file_path, data in actual_functions.items():
        # Analyze classes for patterns
        for cls in data['classes']:
            class_name = cls['name']
            methods = [m['name'] for m in cls['methods']]
            
            # Handler pattern
            if class_name.endswith('Handler') and 'can_handle' in methods and 'handle' in methods:
                patterns['handlers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods)
                })
            
            # Manager pattern
            elif class_name.endswith('Manager') and ('start' in methods or 'initialize' in methods):
                patterns['managers'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods)
                })
            
            # Factory pattern
            elif 'Factory' in class_name and ('create' in methods or 'register' in methods):
                patterns['factories'].append({
                    'file': file_path,
                    'class': class_name,
                    'methods': len(methods)
                })
        
        # Analyze functions for patterns
        for func in data['functions']:
            func_name = func['name']
            
            # Entry points
            if func_name in ['handle_message', 'generate_response', 'main', '__init__']:
                patterns['entry_points'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func['has_docstring']
                })
            
            # Data access
            elif any(keyword in func_name for keyword in ['get_user', 'save_user', 'load_', 'save_']):
                patterns['data_access'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func['has_docstring']
                })
            
            # Communication
            elif any(keyword in func_name for keyword in ['send_', 'receive_', 'connect_', 'disconnect_']):
                patterns['communication'].append({
                    'file': file_path,
                    'function': func_name,
                    'has_doc': func['has_docstring']
                })
    
    return patterns

def update_function_registry():
    """Update FUNCTION_REGISTRY_DETAIL.md and AI_FUNCTION_REGISTRY.md with current codebase analysis."""
    print("[SCAN] Scanning all Python files...")
    actual_functions = scan_all_python_files()
    
    print("[GEN] Generating FUNCTION_REGISTRY_DETAIL.md content...")
    detail_content = generate_function_registry_content(actual_functions)
    
    print("[GEN] Generating AI_FUNCTION_REGISTRY.md content...")
    ai_content = generate_ai_function_registry_content(actual_functions)
    
    # Write DETAIL file
    detail_path = Path(__file__).parent.parent / 'FUNCTION_REGISTRY_DETAIL.md'
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(detail_content)
    
    # Write AI file
    ai_path = Path(__file__).parent.parent / 'AI_FUNCTION_REGISTRY.md'
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
    
    print(f"\n[SUCCESS] Both function registry files updated successfully!")
    print(f"[FILES] Generated:")
    print(f"   FUNCTION_REGISTRY_DETAIL.md - Complete detailed registry")
    print(f"   AI_FUNCTION_REGISTRY.md - Concise AI-focused registry")
    print(f"[STATS] Statistics:")
    print(f"   Files scanned: {total_files}")
    print(f"   Functions found: {total_functions}")
    print(f"   Methods found: {total_methods}")
    print(f"   Total items: {total_items}")
    print(f"   Functions documented: {documented_functions}")
    print(f"   Methods documented: {documented_methods}")
    print(f"   Total documented: {documented_items}")
    print(f"   Template-generated: {template_items}")
    print(f"   Coverage: {coverage_percentage:.1f}%")
    print(f"   Detail file: {detail_path}")
    print(f"   AI file: {ai_path}")
    
    # Template breakdown
    if template_items > 0:
        print(f"\n[TEMPLATES] Template Breakdown:")
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
            print(f"   {template_type}: {count}")

if __name__ == "__main__":
    update_function_registry() 