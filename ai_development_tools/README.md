# AI Development Tools

> **Audience**: AI assistants and developers using MHM development tools  
> **Purpose**: Tools optimized for AI-assisted development collaboration and codebase analysis  
> **Style**: Technical, reference-oriented, tool-focused

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **Main Tool**
```powershell
# Run AI development tools
python ai_development_tools/ai_tools_runner.py <command>

# Available commands
python ai_development_tools/ai_tools_runner.py help
```

### **Common Commands**
- `audit` - Comprehensive system audit
- `status` - Quick system status
- `docs` - Documentation updates
- `legacy` - Legacy code cleanup
- `coverage` - Test coverage analysis

This directory contains tools optimized for AI-assisted development collaboration and codebase analysis.

## 🎯 Primary Tool

### `ai_tools_runner.py` ⭐ **MAIN ENTRY POINT**
**Purpose**: Comprehensive interface for all AI development tools
**Usage**: `python ai_development_tools/ai_tools_runner.py <command>`

**Available Commands:**
- `audit` - Comprehensive audit with AI-optimized outputs
- `docs-sync` - Documentation synchronization check
- `legacy-cleanup` - Legacy code reference cleanup
- `quick-status` - System status overview
- `validate-work` - AI work validation
- `test-coverage` - Test coverage regeneration
- `version-sync` - Version synchronization

## 📊 AI-Optimized Outputs

The audit command creates AI-optimized documents:
- **`AI_STATUS.md`** - Current codebase state with actionable insights
- **`AI_PRIORITIES.md`** - Immediate next steps and focus areas
- **`audit_report.txt`** - Human-readable detailed report
- **`ai_audit_detailed_results.json`** - Raw audit data (rotated)

## 🔧 Core Audit Tools

### Function Analysis
- **`function_discovery.py`** - Discovers and categorizes all functions
- **`decision_support.py`** - AI decision support dashboard
- **`audit_function_registry.py`** - Audits function registry completeness
- **`audit_module_dependencies.py`** - Audits module dependencies

### Documentation Tools
- **`generate_function_registry.py`** - Creates AI_FUNCTION_REGISTRY.md
- **`generate_module_dependencies.py`** - Creates AI_MODULE_DEPENDENCIES.md
- **`analyze_documentation.py`** - Analyzes documentation redundancy

### Validation Tools
- **`documentation_sync_checker.py`** - Checks documentation synchronization
- **`legacy_reference_cleanup.py`** - Identifies legacy code references
- **`validate_ai_work.py`** - Validates AI-generated work
- **`config_validator.py`** - Validates tool configuration consistency

### Status Tools
- **`quick_status.py`** - Quick system status
- **`regenerate_coverage_metrics.py`** - Coverage analysis
- **`version_sync.py`** - Version synchronization

## 📁 File Organization

### Rotating Files (with automatic backup/archive)
- **AI Documents**: `AI_STATUS.md`, `AI_PRIORITIES.md`
- **Reports**: `audit_report.txt`, `docs_sync_report.txt`, `legacy_cleanup_report.txt`, etc.
- **Data**: `ai_audit_detailed_results.json`, `coverage.json`

### Static Files
- **Tool Scripts**: All `.py` files
- **Configuration**: `config.py`, `.coveragerc`
- **Documentation**: `README.md`

## 🚀 Quick Start

1. **Run Full Audit**: `python ai_development_tools/ai_tools_runner.py audit`
2. **Check Status**: `python ai_development_tools/ai_tools_runner.py quick-status`
3. **Sync Docs**: `python ai_development_tools/ai_tools_runner.py docs-sync`

## 📈 File Rotation

All output files are automatically rotated with:
- **Backup**: Previous versions moved to `archive/` with timestamps
- **History**: Execution history maintained
- **Cleanup**: Old versions automatically removed (7-day retention)

## 🤖 AI Collaboration

These tools are specifically designed for AI assistants to:
- **Understand** current codebase state
- **Identify** priorities and next steps
- **Track** progress and changes
- **Maintain** documentation consistency
- **Validate** work quality

## 📚 Generated Documentation

The tools create comprehensive documentation in:
- **`ai_development_docs/`** - AI-optimized static documentation
- **`development_docs/`** - Human-readable detailed documentation
- **`ai_development_tools/`** - Real-time status and priorities