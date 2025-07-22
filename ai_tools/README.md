# AI Tools Directory

This directory contains tools optimized for AI-assisted development collaboration.

## 📋 Available Tools

### `ai_tools_runner.py` ⭐ **PRIMARY TOOL**
**Purpose**: Comprehensive interface for all AI tools (SINGLE ENTRY POINT)
**When to use**: Primary tool for all AI tool operations - both simple and advanced
**Simple Commands**: `python ai_tools_runner.py <command>` (audit, docs, validate, config, help, status)
**Advanced Commands**: `python ai_tools_runner.py <command>` (workflow, quick-audit, decision-support, version-sync)

### `quick_status.py` ⭐ **AI OPTIMIZED**
**Purpose**: Concise, actionable status information for AI collaboration
**When to use**: When you need quick overview of codebase status and actionable items
**Command**: `python ai_tools/quick_status.py concise` or `python ai_tools/quick_status.py json`
**Output**: Optimized for AI consumption with clear action items and critical issues

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

### `config_validator.py`
**Purpose**: Validates that all tools use configuration consistently and checks configuration completeness
**When to use**: After making configuration changes or when troubleshooting tool issues
**Command**: `python ai_tools/config_validator.py`

### `tool_guide.py`
**Purpose**: Comprehensive guide for when to use each tool and how to interpret output
**When to use**: When unsure which tool to use or how to understand results
**Command**: `python ai_tools/tool_guide.py guide`

## ⚙️ Configuration

### `config.py`
Central configuration file for all AI tools. Optimized for AI collaboration with:
- Concise output settings
- Actionable insights focus
- Priority issue highlighting
- Integration mode for data sharing

## 🎯 Best Practices

1. **Use `ai_tools_runner.py`** as the single entry point for all operations
2. **Use `quick_status.py`** for rapid status assessment and action items
3. **Use simple commands** (audit, docs, validate, config, status) for basic operations
4. **Use advanced commands** (workflow, quick-audit, decision-support) for complex tasks
5. **Always run audits first** before major decisions or documentation work
6. **Validate work** before presenting to user
7. **Customize `config.py`** for project-specific needs
8. **Run config validation** after configuration changes
9. **Sync versions** after documentation or core code changes

## 🔧 Customization

Edit `config.py` to adjust:
- Complexity thresholds
- Handler keywords
- Documentation coverage requirements
- Output formatting preferences
- AI collaboration optimization settings

## 📊 Output Files

- `ai_audit_detailed_results.json`: Detailed results from quick audits (for reference)
- `audit_summary.txt`: Concise summary for AI consumption
- `critical_issues.txt`: Priority issues requiring attention
- Console output: Real-time results and recommendations

## 🚀 Quick Start

### Simple Commands (For Users)
```powershell
# Get quick status overview
python ai_tools/ai_tools_runner.py status

# Run full audit of codebase and documentation
python ai_tools/ai_tools_runner.py audit

# Update all documentation (function registry, dependencies)
python ai_tools/ai_tools_runner.py docs

# Validate AI-generated work
python ai_tools/ai_tools_runner.py validate

# Check configuration consistency
python ai_tools/ai_tools_runner.py config

# Show help
python ai_tools/ai_tools_runner.py help
```

### Advanced Commands (For AI Collaborators)
```powershell
# Get concise status with action items
python ai_tools/quick_status.py concise

# Get detailed status as JSON
python ai_tools/quick_status.py json

# Run workflow with audit-first protocol
python ai_tools/ai_tools_runner.py workflow documentation
python ai_tools/ai_tools_runner.py workflow function_registry
python ai_tools/ai_tools_runner.py workflow code_analysis

# Run comprehensive audit
python ai_tools/ai_tools_runner.py quick-audit

# Get actionable insights
python ai_tools/ai_tools_runner.py decision-support

# Sync version numbers
python ai_tools/ai_tools_runner.py version-sync docs
python ai_tools/ai_tools_runner.py version-sync core
```

---

**Remember**: These tools are optimized for AI collaboration and provide concise, actionable information to improve development workflow and work around context limits. 