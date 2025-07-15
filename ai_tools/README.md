# AI Tools Directory

This directory contains tools optimized for AI-assisted development collaboration.

## 🚨 TRIGGER.md
**CRITICAL**: Always read `TRIGGER.md` before creating documentation or making architectural decisions.

## 📋 Available Tools

### `quick_audit.py`
**Purpose**: One-click comprehensive audit of the entire codebase
**When to use**: Before any major decision, refactoring, or documentation work
**Command**: `python ai_tools/quick_audit.py`

### `function_discovery.py`
**Purpose**: Find and categorize all functions (handlers, tests, complex, undocumented)
**When to use**: Need to understand what functions exist and their characteristics
**Command**: `python ai_tools/function_discovery.py`

### `decision_support.py`
**Purpose**: Dashboard showing actionable insights for codebase improvement
**When to use**: Before making architectural decisions or suggesting changes
**Command**: `python ai_tools/decision_support.py`

### `validate_ai_work.py`
**Purpose**: Validate AI-generated work before presenting to user
**When to use**: Before showing any documentation, analysis, or recommendations
**Command**: `python ai_tools/validate_ai_work.py`

### `audit_function_registry.py`
**Purpose**: Check completeness and accuracy of function documentation
**When to use**: When creating or updating function registries
**Command**: `python ai_tools/audit_function_registry.py`

### `audit_module_dependencies.py`
**Purpose**: Analyze module dependencies and import relationships
**When to use**: When understanding code architecture or making structural changes
**Command**: `python ai_tools/audit_module_dependencies.py`

### `analyze_documentation.py`
**Purpose**: Find documentation overlap and redundancy
**When to use**: When consolidating documentation or identifying gaps
**Command**: `python ai_tools/analyze_documentation.py`

### `version_sync.py`
**Purpose**: Automatically synchronize version numbers and dates across all AI documentation, project docs, and core system files
**When to use**: After making changes to documentation or core files, before backups, before audits
**Command**: `python ai_tools/version_sync.py sync --scope=docs`
**Smart Features**: Only updates dates for files actually modified today or yesterday

#### **Scopes for Version Sync**
- `ai_docs` (default): AI documentation and cursor rules
- `docs`: All documentation files (`.md`, `.txt`, `.mdc`)
- `core`: Key system files (`run_mhm.py`, `core/service.py`, etc.)
- `all`: Everything (use with caution)

**Examples:**
```powershell
# Sync all documentation files
python ai_tools/version_sync.py sync --scope=docs

# Sync core system files
python ai_tools/version_sync.py sync --scope=core

# Show status for docs/core
python ai_tools/version_sync.py status docs
python ai_tools/version_sync.py status core
```

### `tool_guide.py`
**Purpose**: Comprehensive guide for when to use each tool and how to interpret output
**When to use**: When unsure which tool to use or how to understand results
**Command**: `python ai_tools/tool_guide.py guide`

## ⚙️ Configuration

### `config.py`
Central configuration file for all AI tools. Customize settings here:
- Function discovery thresholds
- Validation criteria
- Output formatting
- File patterns to include/exclude

## 🎯 Best Practices

1. **Always run `quick_audit.py` first** to get the full picture
2. **Use `decision_support.py`** for actionable insights
3. **Validate with `validate_ai_work.py`** before presenting to user
4. **Check `TRIGGER.md`** for mandatory steps
5. **Customize `config.py`** for project-specific needs
6. **Sync versions after documentation or core code changes** using the appropriate scope

## 🔧 Customization

Edit `config.py` to adjust:
- Complexity thresholds
- Handler keywords
- Documentation coverage requirements
- Output formatting preferences

## 📊 Output Files

- `ai_audit_results.json`: Saved results from quick audits (if enabled in config)
- Console output: Real-time results and recommendations

## 🚀 Quick Start

```powershell
# Get complete codebase overview
python ai_tools/quick_audit.py

# Get actionable insights
python ai_tools/decision_support.py

# Validate work before presenting
python ai_tools/validate_ai_work.py

# Sync all documentation files after changes
python ai_tools/version_sync.py sync --scope=docs

# Sync core system files after changes
python ai_tools/version_sync.py sync --scope=core

# Check which files were modified recently
python ai_tools/version_sync.py status docs
python ai_tools/version_sync.py status core

# Force update all dates (use sparingly)
python ai_tools/version_sync.py sync --force

# Get tool recommendations for specific scenarios
python ai_tools/tool_guide.py recommend 'documentation analysis'
```

---

**Remember**: These tools are designed to prevent incomplete documentation and ensure accurate, informed decision-making in AI-assisted development. 