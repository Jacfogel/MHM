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
- `status` - print a concise status snapshot (reads from cached data)
- `system-signals` - generate system health and status signals
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
- `status`
- `system-signals`
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
- **Fast mode** (`audit`): runs core tools including documentation sync checker, legacy cleanup, validation, and system signals; finishes in roughly 30 seconds.
- **Full mode** (`audit --full`): runs coverage, unused imports checker, and the full test suite; budget 3-4 minutes.

## Generated Outputs
The audit workflow produces:
- `ai_development_tools/AI_STATUS.md` - Comprehensive status with all sections populated from cached data
- `ai_development_tools/AI_PRIORITIES.md` - Actionable priorities and recommendations
- `ai_development_tools/consolidated_report.txt` - Detailed consolidated report
- `ai_development_tools/ai_audit_detailed_results.json` - Cached results for fast status updates
- `ai_development_tools/critical_issues.txt` - Critical issues summary
- `development_docs/LEGACY_REFERENCE_REPORT.md` - Detailed legacy reference cleanup report
- `development_docs/UNUSED_IMPORTS_REPORT.md` (full mode only)

The `docs` command additionally generates:
- `development_docs/FUNCTION_REGISTRY_DETAIL.md` - Complete detailed function registry
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md` - Complete detailed module dependencies (hybrid auto-generated with manual enhancements preserved)
- `ai_development_docs/AI_FUNCTION_REGISTRY.md` - AI-optimized function registry
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md` - AI-optimized module dependencies

**Manual Enhancement Preservation**: The `generate_module_dependencies.py` script preserves manual enhancements in `MODULE_DEPENDENCIES_DETAIL.md`. Content marked between `<!-- MANUAL_ENHANCEMENT_START -->` and `<!-- MANUAL_ENHANCEMENT_END -->` is automatically preserved during regeneration, allowing you to add detailed descriptions, key functions, and special considerations without losing them when dependencies are updated.

## Key Scripts
- `function_discovery.py`, `decision_support.py`, `audit_function_registry.py`, `audit_module_dependencies.py`
- `generate_function_registry.py`, `generate_module_dependencies.py`, `analyze_documentation.py`
- `documentation_sync_checker.py`, `legacy_reference_cleanup.py`, `validate_ai_work.py`, `config_validator.py`
- `quick_status.py`, `system_signals.py`, `regenerate_coverage_metrics.py`, `version_sync.py`, `error_handling_coverage.py`

### Coverage Workflow Refresh
- `python ai_development_tools/regenerate_coverage_metrics.py [--update-plan]` now drives the end-to-end coverage refresh.
- The run executes the full pytest suite with coverage, writes `ai_development_tools/coverage.json`, and updates `development_docs/TEST_COVERAGE_EXPANSION_PLAN.md` when `--update-plan` is provided.
- Coverage artefacts are normalised: shard files are combined into `tests/.coverage`, legacy HTML directories are archived under `archive/coverage_artifacts/<timestamp>/`, and fresh HTML reports land in `ai_development_tools/coverage_html/`.
- Troubleshooting output is kept in `ai_development_tools/logs/coverage_regeneration/` (`pytest_*`, `coverage_combine*`, `coverage_html*`). These logs include timestamped history plus `.latest` convenience copies.
- Temporary files emitted during the run (including `shutdown_request.flag`) are auto-removed so the workspace stays clean between executions.

## Status Command and Cached Data
The `status` command provides a fast snapshot by reading from cached audit results:
- **Fast Execution**: Only runs `system_signals` for fresh data, reads everything else from `ai_audit_detailed_results.json`
- **Comprehensive Coverage**: All sections populated (Snapshot, Documentation Signals, Error Handling, Complexity Hotspots, Test Coverage, Legacy References, Validation Status, System Signals)
- **Git-Based Recent Changes**: Uses git commit history to determine "recent" files, excludes generated files
- **Fallback Logic**: If no recent files found, shows 15 most recently modified files with timestamps

## Core Infrastructure
- **`services/standard_exclusions.py`**: Centralized exclusion patterns for consistent file filtering across all tools
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

## Documentation Signals
The audit now includes documentation synchronization monitoring:
- **Path Drift Detection**: Identifies broken file path references in documentation
- **Paired Documentation Sync**: Monitors synchronization between human and AI documentation pairs
- **ASCII Compliance**: Ensures AI-facing documentation uses only ASCII characters
- **Content Quality**: Detects placeholder content and verbatim duplicates
- Results are displayed in the Documentation Signals section of `AI_STATUS.md`

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
1. `python ai_development_tools/ai_tools_runner.py audit` - Run comprehensive audit and cache results
2. `python ai_development_tools/ai_tools_runner.py status` - Get fast status snapshot from cached data
3. `python ai_development_tools/ai_tools_runner.py system-signals` - Generate fresh system health signals

## File Rotation
All generated files rotate through `ai_development_tools/archive/` with a seven-version retention policy.

## Collaboration Notes
These tools support the expectations documented in the AI-facing guides:
- Maintain accuracy and completeness (see `ai_development_docs/AI_REFERENCE.md`).
- Avoid shortcuts and duplication; prefer end-to-end fixes.
- Keep documentation paired and up to date after every change.
