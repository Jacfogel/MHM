# MHM Cursor Commands

This directory contains custom Cursor commands that integrate with the MHM AI development tools. These commands provide quick access to common development tasks and system analysis.

## Available Commands

### 🔍 **audit** - Run Comprehensive Audit
- **Purpose**: Get complete system status and identify issues
- **When to use**: Before major changes, weekly maintenance, debugging
- **Output**: System health, critical issues, action items, metrics

### 📚 **docs-sync** - Check Documentation Synchronization  
- **Purpose**: Ensure paired AI/human docs stay synchronized
- **When to use**: Before updating docs, after changes, weekly maintenance
- **Output**: Sync status, path drift, broken links, recommendations

### 🧪 **test-coverage** - Regenerate Test Coverage Metrics
- **Purpose**: Update test coverage analysis and identify gaps
- **When to use**: After adding tests, before refactoring, weekly maintenance
- **Output**: Coverage percentages, missing lines, priority modules

### 🧹 **legacy-cleanup** - Scan for Legacy References
- **Purpose**: Find and clean up outdated code patterns
- **When to use**: Before refactoring, weekly maintenance, before releases
- **Output**: Legacy patterns found, cleanup recommendations, usage tracking

### ⚡ **quick-status** - Get Quick System Status
- **Purpose**: Get concise system overview and immediate action items
- **When to use**: Daily check-ins, before starting work, AI collaboration
- **Output**: System health, recent activity, critical issues, next steps

### ✅ **validate-work** - Validate AI Work
- **Purpose**: Ensure AI-generated work meets quality standards
- **When to use**: After AI collaboration, before commits, code reviews
- **Output**: Validation results, issues found, quality score, recommendations

### 🔄 **version-sync** - Sync Version Numbers
- **Purpose**: Keep version numbers synchronized across documentation
- **When to use**: After doc updates, before releases, weekly maintenance
- **Output**: Files updated, version numbers, sync status

## How to Use

1. **Type `/` in Cursor chat** to see available commands
2. **Select a command** from the dropdown
3. **Command runs automatically** with appropriate parameters
4. **Review output** for insights and action items

## Integration with AI Development Tools

These commands are powered by the comprehensive AI development tools in `ai_development_tools/`:

- **ai_tools_runner.py** - Main orchestrator for all commands
- **function_discovery.py** - Function analysis and complexity metrics
- **audit_function_registry.py** - Function documentation auditing
- **audit_module_dependencies.py** - Module dependency analysis
- **documentation_sync_checker.py** - Documentation synchronization
- **legacy_reference_cleanup.py** - Legacy code pattern detection
- **quick_status.py** - System status and health checks
- **version_sync.py** - Version number synchronization

## Benefits

- **Quick Access**: No need to remember complex command syntax
- **Consistent Results**: Standardized output format across all tools
- **AI Optimized**: Designed for AI collaboration and assistance
- **Comprehensive**: Covers all major development workflow needs
- **Integrated**: Works seamlessly with existing MHM development tools

## Development Workflow Integration

These commands support the **Audit-First Protocol** and **MHM Development Workflow**:

1. **Start with `/audit`** - Understand current system state
2. **Use `/quick-status`** - Get immediate context
3. **Run `/docs-sync`** - Ensure documentation is current
4. **Use `/validate-work`** - Verify quality standards
5. **Finish with `/version-sync`** - Keep versions consistent

## Maintenance

- Commands are automatically detected by Cursor
- No additional configuration required
- Commands use existing AI development tools
- Output is optimized for AI collaboration
- All commands follow MHM development standards
