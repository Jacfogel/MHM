# Documentation Guide

> **Audience**: Developers and contributors  
> **Purpose**: Documentation organization, standards, and maintenance  
> **Style**: Reference, organizational, comprehensive

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md) for AI-optimized quick reference**

## 🚀 Quick Reference

### **Document Selection Decision Tree**
1. **New to project?** → `README.md`
2. **Setting up?** → `HOW_TO_RUN.md`
3. **Developing?** → `DEVELOPMENT_WORKFLOW.md`
4. **Need commands?** → `QUICK_REFERENCE.md`
5. **Understanding system?** → `ARCHITECTURE.md`
6. **AI collaboration?** → `ai_development_docs/AI_*` files
7. **Current status?** → `ai_development_docs/AI_CHANGELOG.md`, `TODO.md`
8. **Complete history?** → `development_docs/CHANGELOG_DETAIL.md`

### **Documentation Categories**
- **Human-Facing**: `README.md`, `DEVELOPMENT_WORKFLOW.md`, `ARCHITECTURE.md`
- **AI-Facing**: `ai_development_docs/AI_*` files, `.cursor/rules/`
- **Status/History**: `ai_development_docs/AI_CHANGELOG.md`, `TODO.md`, `development_docs/PLANS.md`
- **Technical Reference**: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/MODULE_DEPENDENCIES_DETAIL.md`

## 📋 **DOCUMENTATION STANDARDS & TEMPLATES**

### **Standard Document Structure**
All documentation files should follow this consistent structure:

```markdown
# Document Title

> **Audience**: [Target audience]  
> **Purpose**: [Document purpose]  
> **Style**: [Writing style]

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_*](ai_development_docs/AI_*.md) for AI-optimized quick reference**

## 🚀 Quick Reference

### **Decision Tree/Quick Navigation**
[Step-by-step navigation for common scenarios]

### **Key Information**
[Essential information for the target audience]

## [Main Content Sections]
[Detailed content organized by topic]

## 📚 **Cross-References**
[Links to related documents and resources]
```

### **Paired Documentation Maintenance**
**CRITICAL**: When updating any human-facing document, check if corresponding AI-facing document needs updates:

- **DEVELOPMENT_WORKFLOW.md** ↔ **AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **AI_ARCHITECTURE.md**
- **DOCUMENTATION_GUIDE.md** ↔ **AI_DOCUMENTATION_GUIDE.md**
- **CHANGELOG_DETAIL.md** ↔ **AI_CHANGELOG.md**

### **Audience-Specific Optimization**

#### **Human-Facing Documents**
- **Style**: Comprehensive, step-by-step, supportive
- **Structure**: Detailed explanations with context
- **Examples**: Full code examples and use cases
- **Navigation**: Clear section headers and cross-references

#### **AI-Facing Documents**
- **Style**: Concise, pattern-focused, actionable
- **Structure**: Quick reference and decision trees
- **Examples**: Essential patterns and critical information
- **Navigation**: Direct links to detailed human docs

### **Content Categories & Standards**

#### **Navigation Documents**
- **Purpose**: Help users find the right information quickly
- **Structure**: Decision trees, quick reference sections
- **Examples**: `README.md`, `QUICK_REFERENCE.md`

#### **Technical Documents**
- **Purpose**: Provide detailed technical information
- **Structure**: Comprehensive coverage with examples
- **Examples**: `ARCHITECTURE.md`, `DEVELOPMENT_WORKFLOW.md`

#### **Status Documents**
- **Purpose**: Track current state and priorities
- **Structure**: Brief, action-oriented, scannable
- **Examples**: `AI_CHANGELOG.md`, `TODO.md`, `PLANS.md`

#### **Process Documents**
- **Purpose**: Guide users through procedures
- **Structure**: Step-by-step with safety considerations
- **Examples**: `DEVELOPMENT_WORKFLOW.md`, `HOW_TO_RUN.md`

### **Cursor Commands Documentation Standards**

#### **Command Document Structure**
All `.cursor/commands/*.md` files should follow this structure:

```markdown
# Command Name

## Overview
[Brief description of what the command does]

## Instructions for AI Assistant

### 1. **Execute [Primary Action]**
[Step-by-step instructions with PowerShell syntax]

### 2. **Analyze and Report Results**
**CRITICAL**: Always read and analyze these files:
- [List of key files to check]

### 3. **Provide Structured Report**
**ALWAYS provide this format in your response:**

#### **[Category] Title**
- [Specific metrics to report]
- [Key findings to highlight]

## Success Criteria
- [Clear success indicators]

## Output Files to Always Check
- [List of critical files to read]
```

#### **Command Optimization Principles**
- **Structured Instructions**: Clear step-by-step guidance for AI assistants
- **PowerShell Syntax**: All commands use proper PowerShell with `$LASTEXITCODE` checking
- **Structured Reports**: Specific report formats for consistent AI responses
- **Critical File Lists**: Exact files to read and analyze
- **Action-Oriented**: Focus on what the AI should do, not just what tools to run

## 📊 Documentation Summary Table

| File | Audience | Purpose | Style |
|------|----------|---------|-------|
| **README.md** | New users & developers | Project overview and features | Comprehensive, beginner-friendly |
| **HOW_TO_RUN.md** | New users & developers | Setup and installation | Step-by-step, troubleshooting-focused |
| **DEVELOPMENT_WORKFLOW.md** | Developers & contributors | Safe development practices | Comprehensive, step-by-step, supportive |
| **QUICK_REFERENCE.md** | Developers & contributors | Essential commands and troubleshooting | Concise, scannable, action-oriented |
| **ARCHITECTURE.md** | Developers & contributors | System design and components | Technical, detailed, reference-oriented |
| **ai_development_docs/AI_CHANGELOG.md** | AI collaborators & developers | Brief summaries of recent changes for AI context | Concise, action-oriented, scannable |
| **development_docs/CHANGELOG_DETAIL.md** | Developers & contributors | Complete detailed changelog history | Chronological, detailed, reference-oriented |
| **TODO.md** | Developers & contributors | Current priorities and planned work | Organized, actionable, beginner-friendly |
| **development_docs/PLANS.md** | Human developer and AI collaborators | Development plans and strategies | Actionable, checklist-focused, progress-tracked |
| **development_docs/FUNCTION_REGISTRY_DETAIL.md** | Human developer and AI collaborators | Complete function documentation | Comprehensive, detailed, reference-oriented |
| **development_docs/MODULE_DEPENDENCIES_DETAIL.md** | Human developer and AI collaborators | Complete module dependency map | Comprehensive, detailed, reference-oriented |

## 📋 Documentation Categories

### 🤖 AI-Focused Documentation
*Intended for AI assistants (Cursor, Codex, etc.)*

#### Core AI Guidelines
- **`ai_development_docs/AI_SESSION_STARTER.md`** - Essential context for new AI sessions
- **`ai_development_docs/AI_REFERENCE.md`** - Troubleshooting and system understanding
- **`ai_development_docs/AI_CHANGELOG.md`** - Brief summaries for AI context
- **`ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`** - AI-optimized development patterns
- **`ai_development_docs/AI_ARCHITECTURE.md`** - AI-optimized architectural patterns
- **`ai_development_docs/AI_DOCUMENTATION_GUIDE.md`** - AI-optimized documentation navigation
- **`development_docs/PLANS.md`** - Development plans, testing status, and UI migration patterns
- **`ai_development_docs/AI_FUNCTION_REGISTRY.md`** - Function patterns and documentation status
- **`ai_development_docs/AI_MODULE_DEPENDENCIES.md`** - Module dependency patterns and status
- **`.cursor/rules/`** - Cursor-specific rules and guidelines

#### AI-Specific Rules
- **`.cursor/rules/audit.mdc`** - Audit rules for documentation and analysis
- **`.cursor/rules/context.mdc`** - Context rules for development work
- **`.cursor/rules/critical.mdc`** - Critical rules for development work

### 👤 User-Focused Documentation
*Intended for the human developer (you)*

#### Getting Started
- **`README.md`** - Project overview and features
- **`HOW_TO_RUN.md`** - Setup and installation instructions

#### Development Guides
- **`DEVELOPMENT_WORKFLOW.md`** - Safe development practices for beginners
- **`QUICK_REFERENCE.md`** - Essential commands and troubleshooting
- **`development_docs/PLANS.md`** - Development plans, UI migration, and testing strategies

#### Technical Reference
- **`ARCHITECTURE.md`** - System structure and data organization
- **`development_docs/CHANGELOG_DETAIL.md`** - Complete detailed changelog history
- **`TODO.md`** - Current development priorities
- **`development_docs/FUNCTION_REGISTRY_DETAIL.md`** - Complete function documentation
- **`development_docs/MODULE_DEPENDENCIES_DETAIL.md`** - Complete module dependency map

### 🔧 Configuration Files
*Used by both AI and human developers*

- **`requirements.txt`** - Python dependencies
- **`.env`** - Environment variables (in .cursorignore)
- **`.gitignore`** - Git ignore patterns
- **`.gitattributes`** - Git file handling

## 📝 Documentation Standards

### AI-Focused Documentation Should:
- Be concise and scannable
- Focus on essential rules and context
- Use clear, direct language
- Avoid verbose explanations
- Be organized for quick reference

### User-Focused Documentation Should:
- Be comprehensive and beginner-friendly
- Include detailed explanations
- Provide step-by-step instructions
- Use encouraging, supportive language
- Include examples and troubleshooting

## 🏗️ Coding Standards and Naming Conventions

### **Helper Function Naming Convention**

**Pattern**: `_main_function__helper_name`

**Purpose**: Improve code traceability and searchability by clearly indicating which main function owns each helper function.

**Examples**:
```python
def _handle_list_tasks(self, user_id: str, entities: Dict[str, Any]) -> InteractionResponse:
    # Main function logic
    filtered_tasks = self._handle_list_tasks__apply_filters(user_id, tasks, filter_type, priority_filter, tag_filter)
    sorted_tasks = self._handle_list_tasks__sort_tasks(filtered_tasks)
    task_list = self._handle_list_tasks__format_list(sorted_tasks)
    # ... more logic

def _handle_list_tasks__apply_filters(self, user_id, tasks, filter_type, priority_filter, tag_filter):
    """Apply filters to tasks and return filtered list."""
    # Helper function logic

def _handle_list_tasks__sort_tasks(self, tasks):
    """Sort tasks by priority and due date."""
    # Helper function logic

def _handle_list_tasks__format_list(self, tasks):
    """Format task list with enhanced details."""
    # Helper function logic
```

**Benefits**:
- **Searchability**: `grep "handle_list_tasks"` finds both main function and all helpers
- **Traceability**: Clear ownership of helper functions
- **Debugging**: Clearer call stack traces with meaningful function names
- **Maintainability**: Easy to find all related code for a specific feature

### **Function Type Distinctions**

#### **Implementation Functions** (Core API)
- **Purpose**: Core functionality used across multiple modules
- **Scope**: Public API, imported by other modules
- **Naming**: Standard Python snake_case (`create_task`, `get_user_data`)
- **Examples**: `create_task()`, `load_active_tasks()`, `get_user_data()`, `save_user_data()`

#### **Helper Functions** (Internal Support)
- **Purpose**: Break down complexity within a single main function
- **Scope**: Private to class/module, support specific main functions
- **Naming**: `_main_function__helper_name` pattern
- **Examples**: `_handle_list_tasks__format_due_date()`, `_handle_create_task__parse_relative_date()`

#### **Main Functions** (Public Interface)
- **Purpose**: Primary entry points for functionality
- **Scope**: Public methods that orchestrate helper functions
- **Naming**: Standard Python snake_case with descriptive names
- **Examples**: `_handle_list_tasks()`, `_handle_create_task()`, `handle()`

### **When to Use Each Type**

**Use Implementation Functions When**:
- Multiple modules need the same functionality
- Providing core business logic or data access
- Creating public API that other parts of the system should use
- Implementing reusable logic that doesn't belong to a specific handler

**Use Helper Functions When**:
- Breaking down complex logic within a single main function
- Improving readability of large, complex methods
- Each helper has a single, clear responsibility
- The helper clearly belongs to a specific main function

**Use Main Functions When**:
- Creating public interfaces for handlers or classes
- Orchestrating multiple helper functions
- Providing entry points for specific functionality
- Handling user interactions or external requests

## 🔄 Maintenance Guidelines

### **Paired Document Maintenance**
**CRITICAL**: When updating any human-facing document, check if corresponding AI-facing document needs updates:

- **DEVELOPMENT_WORKFLOW.md** ↔ **ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **ai_development_docs/AI_ARCHITECTURE.md**
- **DOCUMENTATION_GUIDE.md** ↔ **ai_development_docs/AI_DOCUMENTATION_GUIDE.md**
- **development_docs/CHANGELOG_DETAIL.md** ↔ **ai_development_docs/AI_CHANGELOG.md**

### When Updating AI Documentation:
- Keep it concise and focused
- Update both AI docs and relevant Cursor rules
- Test that AI assistants can understand the changes
- Remove any redundancy or duplication

### When Updating User Documentation:
- Maintain beginner-friendly language
- Include clear explanations of concepts
- Add examples where helpful
- Keep the encouraging, supportive tone

### When Adding New Documentation:
- Determine the primary audience (AI or User)
- Follow the appropriate style guidelines
- Update this guide to include the new file
- Consider if it could be consolidated with existing docs
- **Check if paired document is needed**

### Generated Documentation Standards

#### Generated File Identification
All generated files must clearly identify themselves with:

```markdown
# Generated File Title

> **Generated**: This file is auto-generated by [TOOL_NAME]. Do not edit manually.
> **Generated by**: [TOOL_NAME] - [TOOL_DESCRIPTION]
> **Last Generated**: [TIMESTAMP]
> **Source**: [SOURCE_FILES_OR_COMMANDS]

[Generated content...]
```

#### Generated File Standards
- **Clear Identification**: Must have `> **Generated**:` header
- **Tool Attribution**: Must specify which tool generated the file
- **Timestamp**: Must include generation timestamp
- **Source Information**: Must specify source files or commands
- **No Manual Editing**: Must clearly state "Do not edit manually"
- **Tool Updates**: Updates must be made to the generating tool, not the generated file

#### Generated File Maintenance
- **Tool-Based Updates**: Only update the tools that generate these files
- **Never Edit Generated Files**: Generated files should never be manually edited
- **Regeneration**: Regenerate files after updating the generating tools
- **Version Control**: Generated files should be tracked but not manually modified

#### Known Generated Documentation Files

**AI Development Tools Generated Documentation (2):**
- `ai_development_tools/AI_STATUS.md` - Generated by `ai_tools_runner.py status`
- `ai_development_tools/AI_PRIORITIES.md` - Generated by `ai_tools_runner.py audit`

**Development Documentation Generated Files (4):**
- `development_docs/DIRECTORY_TREE.md` - Generated by `ai_tools_runner.py trees`
- `development_docs/LEGACY_REFERENCE_REPORT.md` - Generated by `ai_tools_runner.py legacy`
- `development_docs/FUNCTION_REGISTRY_DETAIL.md` - Generated by `ai_tools_runner.py audit` (function registry)
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md` - Generated by `ai_tools_runner.py audit` (module dependencies)

**AI-Facing Generated Documentation (2):**
- `ai_development_docs/AI_FUNCTION_REGISTRY.md` - Generated by `ai_tools_runner.py audit` (AI-optimized function registry)
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md` - Generated by `ai_tools_runner.py audit` (AI-optimized module dependencies)

## 🎯 Quick Reference

### For AI Assistants:
- Start with `ai_development_docs/AI_SESSION_STARTER.md` for core rules
- Check `ai_development_docs/AI_REFERENCE.md` for troubleshooting
- Use `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` for development patterns
- Use `ai_development_docs/AI_ARCHITECTURE.md` for architectural patterns
- Use `ai_development_docs/AI_DOCUMENTATION_GUIDE.md` for documentation navigation
- Check `.cursor/rules/` for specific guidelines
- Keep responses concise and focused
- **ALWAYS** use Audit-First Protocol for documentation

### For Human Developer:
- Start with `README.md` for overview
- Use `DEVELOPMENT_WORKFLOW.md` for safe practices
- Reference `QUICK_REFERENCE.md` for common tasks
- Check `ARCHITECTURE.md` for system understanding

Remember: The goal is to make collaboration between human and AI as efficient and effective as possible! 