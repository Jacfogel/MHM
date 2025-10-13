# AI Development Tools

> **Audience**: AI assistants and developers using the MHM toolchain  
> **Purpose**: Provide audit, documentation, and validation utilities for collaborative development  
> **Style**: Technical, reference-oriented, tool-focused

> **See [README.md](../README.md) for the overall project view**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## Quick Reference
```powershell
# General form
python ai_development_tools/ai_tools_runner.py <command>

# List commands
python ai_development_tools/ai_tools_runner.py help
```

### Common Commands
- `audit` - run the comprehensive audit (fast by default)
- `audit --full` - rerun with coverage and full test suite
- `status` - print a concise status snapshot
- `docs` - regenerate documentation artefacts
- `legacy` - scan for legacy references
- `unused-imports` - detect unused imports in codebase
- `coverage` - refresh coverage metrics

## Main Entry Point
### `ai_tools_runner.py`
- **Role**: Command dispatcher for all AI development tooling
- **Usage**: `python ai_development_tools/ai_tools_runner.py <command>`

Available sub-commands include:
- `audit` / `audit --full`
- `quick-audit`
- `status`
- `docs`
- `doc-sync`
- `validate`
- `legacy`
- `unused-imports`
- `version-sync <scope>`
- `coverage`
- `workflow <task_type>`
- `trees`

Run any command with `--help` to see command-specific options.

## Fast Mode vs Full Mode
- **Fast mode** (`audit`): skips coverage regeneration; finishes in roughly 30 seconds.
- **Full mode** (`audit --full`): runs coverage and the full test suite; budget 3-4 minutes.

## Generated Outputs
The audit workflow produces:
- `ai_development_tools/AI_STATUS.md`
- `ai_development_tools/AI_PRIORITIES.md`
- `ai_development_tools/consolidated_report.txt`
- `ai_development_tools/ai_audit_detailed_results.json`
- `development_docs/UNUSED_IMPORTS_REPORT.md`

## Key Scripts
- `function_discovery.py`, `decision_support.py`, `audit_function_registry.py`, `audit_module_dependencies.py`
- `generate_function_registry.py`, `generate_module_dependencies.py`, `analyze_documentation.py`
- `documentation_sync_checker.py`, `legacy_reference_cleanup.py`, `validate_ai_work.py`, `config_validator.py`
- `quick_status.py`, `regenerate_coverage_metrics.py`, `version_sync.py`, `error_handling_coverage.py`

## Core Infrastructure
- **`standard_exclusions.py`**: Centralized exclusion patterns for consistent file filtering across all tools
- **`services/constants.py`**: Shared constants for paired docs, default doc sets, and standard-library names
- **`services/operations.py`**: Core service operations and report generation
- **`config.py`**: Configuration settings for scan directories, complexity thresholds, and tool behavior

## Standard Exclusions System
All tools use `standard_exclusions.py` for consistent file filtering:
- **Universal Exclusions**: Python cache, virtual environments, IDE files, generated files
- **Context-Based Exclusions**: 
  - `production`: Excludes development tools, tests, documentation, scripts
  - `development`: Includes most files, excludes sensitive data
  - `testing`: Excludes generated files and data directories
- **Usage**: `should_exclude_file(file_path, tool_type, context)` ensures consistent filtering

## Error Handling Coverage Analysis
The audit includes comprehensive error handling coverage analysis that:
- Analyzes every function for error handling patterns (try-except, decorators, custom error types)
- Identifies functions missing error handling, especially critical operations
- Provides quality assessment (excellent/good/basic/none) and actionable recommendations
- Tracks error handling patterns and coverage metrics in audit summaries
- Helps maintain robust error handling standards across the codebase

## Configuration and Context
Tools operate in different contexts for different purposes:
- **Production Context**: Used by audit tools to analyze only production code (excludes dev tools, tests, docs)
- **Development Context**: Used by development tools to include all relevant files
- **Testing Context**: Used by test tools to focus on test-relevant files

All tools respect the context-based exclusion system to ensure consistent and accurate analysis.

## File Organization
- Rotated outputs: `AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.txt`, archives under `ai_development_tools/archive/`
- Static assets: helper scripts in `ai_development_tools/`, configuration in `config.py`

## Quick Start
1. `python ai_development_tools/ai_tools_runner.py audit`
2. `python ai_development_tools/ai_tools_runner.py status`
3. `python ai_development_tools/ai_tools_runner.py doc-sync`

## File Rotation
All generated files rotate through `ai_development_tools/archive/` with a seven-version retention policy.

## Collaboration Notes
These tools support the expectations documented in the AI-facing guides:
- Maintain accuracy and completeness (see `ai_development_docs/AI_REFERENCE.md`).
- Avoid shortcuts and duplication; prefer end-to-end fixes.
- Keep documentation paired and up to date after every change.
