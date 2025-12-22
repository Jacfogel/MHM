# Development Tools Guide

> **File**: `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`  
> **Audience**: Human maintainers and contributors  
> **Purpose**: Detailed reference for every development tool, its tiers, trust level, and scope  
> **Style**: Explicit, actionable, high-signal  
> **Pair**: [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md)  
> This document is paired with [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md). Keep both H2 headings identical and keep the AI doc concise while this guide carries the detailed context.

---

## 1. Purpose and Scope

Use this guide when you need:
- The authoritative human-readable catalog of tools and tiers
- Rationale behind trust levels and roadmap priorities
- Links to supporting plans such as [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md)

The machine-readable metadata lives in `development_tools/shared/tool_metadata.py` and is surfaced to AI collaborators through the paired guide.

---

## 2. Running the Tool Suite

All commands flow through `development_tools/run_development_tools.py` (or the shorter alias `development_tools/run_dev_tools.py`).

### 2.1. Global Options

The runner supports global options that apply to all commands:

```powershell
# Specify a custom project root
python development_tools/run_development_tools.py --project-root /path/to/project status
# Or use the shorthand:
python development_tools/run_dev_tools.py --project-root /path/to/project status

# Specify a custom config file
python development_tools/run_development_tools.py --config-path /path/to/config.json audit

# Combine both
python development_tools/run_development_tools.py --project-root . --config-path development_tools_config.json status
```

**Configuration File**: By default, the tools look for `development_tools_config.json` in the project root. This file can override paths, project settings, audit behavior, and other configuration. See `development_tools/development_tools_config.json.example` for a template.

### 2.2. Command Examples

```powershell
python development_tools/run_development_tools.py --help
python development_tools/run_development_tools.py audit
python development_tools/run_development_tools.py audit --full
python development_tools/run_development_tools.py docs
python development_tools/run_development_tools.py status
python development_tools/run_development_tools.py legacy
python development_tools/run_development_tools.py coverage
python development_tools/run_development_tools.py unused-imports
python development_tools/run_development_tools.py unused-imports-report
python development_tools/run_development_tools.py config
```

### 2.3. Command Summary

**Core Commands** (daily-safe, audit-first workflow):
- `audit` - Standard audit (Tier 2, default); regenerates quality checks and cached signals.
- `audit --quick` - Quick audit (Tier 1); core metrics only (~30-60s).
- `audit --full` - Full audit (Tier 3); comprehensive analysis including coverage (~10-30min).
- `quick-audit` - [DEPRECATED] Use `audit --quick` instead.
- `docs` - regenerates registries, dependency maps, and doc-signals.
- `doc-sync` - verifies paired doc headings, path drift, ASCII compliance.
- `config` - prints configuration validation report with tool analysis and recommendations.
- `coverage` - invokes `development_tools/tests/generate_test_coverage.py` (HTML + JSON outputs).
- `legacy` - runs `development_tools/legacy/fix_legacy_references.py` via the dispatcher.

**Supporting Commands** (advisory, depend on fresh audits):
- `status` - surfaces cached health summaries (rerun `audit` if stale).
- `system-signals` - generates system health and status signals.
- `validate` - validates AI-generated work (lightweight structural validation).
- `decision-support` - generates decision support insights.
- `unused-imports` - runs the AST-based unused import detection tool (analysis only).
- `unused-imports-report` - generates unused imports report from analysis results.
- `workflow` - executes an audit-first workflow task.
- `trees` - generates directory tree reports.
- `cleanup` - cleans up project cache files, temporary directories, and artifacts.
- `help` - shows detailed help information.

**Experimental Commands** (high-risk, run only with approval):
- `version-sync` - synchronizes version metadata across files (fragile, use with caution).

### 2.4. Entry Point Expectations

Regardless of command:
- Respect shared configuration from `development_tools/config/config.py` (with external config file support via `development_tools_config.json`).
- Honor universal exclusions defined in `shared/standard_exclusions.py`.
- Avoid importing business logic modules (operate via filesystem + configs only).
- Route logging through the `development_tools` component logger.
- Emit ASCII output to stay Windows-safe.

**Configuration Priority**:
1. External config file (`development_tools_config.json` in project root, or path specified via `--config-path`)
2. Hardcoded defaults in `development_tools/config/config.py` (generic/empty fallbacks for portability)
3. Environment-specific detection (project root, scan directories, etc.)

**Portability**: All tools are portable and can be used in other projects. Create a `development_tools_config.json` file in your project root (see `development_tools/development_tools_config.json.example` for a template) to customize paths, exclusions, constants, and other project-specific settings.

### 2.5. Service Architecture

The development tools suite uses a modular service architecture. The main `AIToolsService` class is composed from mixin classes located in `development_tools/shared/service/`:

- **`development_tools/shared/service/core.py`**: Base `AIToolsService` class with initialization and configuration
- **`development_tools/shared/service/utilities.py`**: `UtilitiesMixin` - Formatting and extraction utility methods
- **`development_tools/shared/service/data_loading.py`**: `DataLoadingMixin` - Data loading and parsing methods
- **`development_tools/shared/service/tool_wrappers.py`**: `ToolWrappersMixin` - Tool execution wrappers and `SCRIPT_REGISTRY`
- **`development_tools/shared/service/audit_orchestration.py`**: `AuditOrchestrationMixin` - Audit workflow and tier management
- **`development_tools/shared/service/report_generation.py`**: `ReportGenerationMixin` - Report generation methods
- **`development_tools/shared/service/commands.py`**: `CommandsMixin` - Command execution methods

The CLI interface (`COMMAND_REGISTRY` and command handlers) is in `development_tools/shared/cli_interface.py`. For new code, import `AIToolsService` from `development_tools.shared.service` and `COMMAND_REGISTRY` from `development_tools.shared.cli_interface`:

```python
from development_tools.shared.service import AIToolsService
from development_tools.shared.cli_interface import COMMAND_REGISTRY
```

The modular structure provides clear separation of concerns, making the codebase more maintainable and testable. Each module has a single responsibility and can be tested independently.

---

## 3. Audit Modes and Outputs

**Tier 1: Quick Audit (`audit --quick`)** collects all tools ≤2s execution time:
- **Core metrics**: System health, quick status
- **Quick checks**: Documentation analysis, config validation, AI work validation
- **Module imports**: Module import extraction, dependency patterns
- **Function analysis**: Function patterns, decision support, function registry validation
- **Duration**: ~5-10 seconds (with parallel execution)

**Tier 2: Standard Audit (`audit`, default)** includes all tools >2s but ≤10s execution time:
- **Function discovery**: Function discovery and complexity metrics (required by dependent tools)
- **Quality checks**: Error handling coverage, package export validation
- **Documentation sync**: Documentation synchronization (includes multiple sub-tools)
- **Module dependencies**: Module dependency validation (depends on module imports from Tier 1)
- **Unused imports**: Unused import detection and report generation
- **Duration**: ~15-25 seconds (with parallel execution)

**Tier 3: Full Audit (`audit --full`)** includes everything in Tier 1 & 2 plus tools >10s (or groups containing tools >10s):
- **Coverage group** (runs sequentially, ~460s total):
  - Full pytest execution with coverage regeneration (~365s, >10s)
  - Dev tools test coverage (~94s, >10s)
  - Test marker analysis (~2s, but part of coverage group)
  - Coverage report generation (~0s, but part of coverage group)
- **Legacy group** (runs in parallel with coverage group):
  - Legacy reference scanning (~62s, >10s)
  - Legacy reference report generation (~1s, but part of legacy group)
- Improvement opportunity reports (LEGACY_REFERENCE_REPORT.md, TEST_COVERAGE_REPORT.md, UNUSED_IMPORTS_REPORT.md)

**Performance**: Total full audit time: ~9-10 minutes (coverage tools dominate at ~460s)

Pipeline artifacts:
- AI-facing (root): [AI_STATUS.md](development_tools/AI_STATUS.md), `AI_PRIORITIES.md`, `consolidated_report.txt`
- Domain-specific JSON: `reports/analysis_detailed_results.json`, `error_handling/error_handling_details.json`, `tests/jsons/coverage_dev_tools.json`, `config/analyze_config_results.json`, `imports/.unused_imports_cache.json`
  - `reports/analysis_detailed_results.json` caches complexity metrics, validation results, and system signals for `status` command
  - `AI_PRIORITIES.md` includes complexity refactoring priority when critical/high complexity functions exist

**Report Format Standards**:
- **AI_STATUS.md**: High-level summary including Function Docstring Coverage (with missing count) and Registry Gaps (separate metrics)
- **AI_PRIORITIES.md**: Actionable priorities with prioritized example lists (functions and handler classes) using ", ... +N" format when there are more items
- **consolidated_report.txt**: Comprehensive details including all metrics from AI_STATUS plus detailed example lists in the Function Patterns section
- Human-facing: [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md), [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md), [LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md), [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)
- Coverage: `development_tools/tests/jsons/coverage.json`, `development_tools/tests/jsons/coverage_dev_tools.json`, `development_tools/tests/coverage_html/`, `development_tools/reports/archive/coverage_artifacts/<timestamp>/`
- Cached snapshots: `status` loads data from `reports/analysis_detailed_results.json` (complexity, validation, system signals); confirm timestamps before trusting

**Tool Output Format (Standard Format - 2025-12-14)**:
- All 19 analysis tools now output JSON in a standardized structure for consistent data aggregation:
  ```json
  {
    "summary": {
      "total_issues": <number>,
      "files_affected": <number>,
      "status": "<PASS|FAIL|WARN>" (optional)
    },
    "details": {
      // Tool-specific data (original metrics, findings, etc.)
    }
  }
  ```
- Tools support `--json` flag to output standard format directly when run standalone
- Normalization layer in `development_tools/shared/result_format.py` provides backward compatibility for any legacy formats
- Report generation code automatically detects and handles standard format, accessing data from `details` section
- This standardization enables consistent data aggregation, easier tool integration, and simplified report generation.

**When to run each command**: See "Standard Audit Recipe" section in [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for guidance on day-to-day checks (`audit`), pre-merge/pre-release checks (`audit --full`), and documentation work (`doc-sync`, `docs`).

Ensure directories listed in `development_tools/shared/constants.py` remain accurate so reports resolve predictably.

---

## 4. Tool Catalog and Tiering

### 4.1. Naming Conventions

All tools follow a 3-prefix naming system established in Phase 7:

- **`analyze_*`** - Finding + assessing (read-only examination, validation, detection)
  - Examples: `analyze_functions.py`, `analyze_documentation.py`, `analyze_error_handling.py`, `analyze_test_coverage.py`
  - These tools examine code/documentation and report findings without modifying anything
- **`generate_*`** - Making artifacts (create/recreate documentation, registries, reports)
  - Examples: `generate_function_registry.py`, `generate_test_coverage.py`, `generate_module_dependencies.py`
  - These tools create or regenerate documentation and report files
- **`fix_*`** - Cleanup/repair (removal, cleanup operations)
  - Examples: `fix_legacy_references.py`, `fix_version_sync.py`, `fix_project_cleanup.py`
  - These tools perform cleanup, removal, or repair operations (often support `--dry-run`)
- **No prefix** - Reporting/utility tools (descriptive names)
  - Examples: `decision_support.py`, `quick_status.py`, `system_signals.py`, `file_rotation.py`, `tool_guide.py`
  - These are utility or reporting tools that don't fit the analyze/generate/fix pattern

Tools are organized by domain (functions/, docs/, tests/, etc.) and follow these naming conventions consistently. This makes it easy to understand a tool's purpose at a glance.

### 4.2. Tier overview

| Tier | Trust Level | Description |
| --- | --- | --- |
| Core | stable | Safe for daily runs; required for audit-first workflow. |
| Supporting | partial / advisory | Helpful but dependent on fresh audit data; verify results manually. |
| Experimental | experimental | Prototype/high-risk commands; run only with explicit approval and backups. |

### 4.3. Detailed catalog

| Tool | Tier | Trust | Notes |
| --- | --- | --- | --- |
| run_development_tools.py | core | stable | CLI dispatcher for every development tooling command. Supports `--project-root` and `--config-path` for portability. |
| shared/cli_interface.py | core | stable | Implements command handlers and COMMAND_REGISTRY for CLI interface. |
| shared/service/ | core | stable | Modular service architecture with AIToolsService composed from mixin classes. Accepts project-specific config via external config file. |
| config/config.py | core | stable | Central configuration for audit contexts, paths, and workflow knobs. Loads from `development_tools_config.json` with generic fallbacks. |
| shared/standard_exclusions.py | core | stable | Canonical exclusion patterns consumed by all scanners. Loads exclusions from external config. |
| shared/constants.py | core | stable | Doc pairing metadata, directory maps, and shared enumerations. Loads constants from external config. |
| shared/common.py | core | stable | IO helpers plus CLI utilities (command grouping, runners). |
| analyze_documentation_sync.py | core | stable | Validates paired documentation (human vs AI) and detects heading sync issues. Refactored during Batch 2 decomposition to only handle paired doc sync. Parameterized doc roots and metadata schema. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_documentation_sync_checker.py` |
| docs/analyze_path_drift.py | core | stable | Analyzes path drift between codebase and documentation. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/analyze_ascii_compliance.py | core | stable | Checks ASCII compliance in documentation files. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/analyze_heading_numbering.py | core | stable | Validates H2 and H3 heading numbering in documentation. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/analyze_missing_addresses.py | core | stable | Detects missing file addresses in documentation files. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/analyze_unconverted_links.py | core | stable | Detects unconverted file path references in documentation. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/generate_directory_tree.py | core | stable | Generates directory tree reports for documentation. Extracted from analyze_documentation_sync.py during Batch 2 decomposition. |
| docs/fix_documentation.py | core | stable | Dispatcher that orchestrates all documentation fix operations. Refactored during Batch 2 decomposition to call specialized fixers. [OK] **HAS TESTS (Phase 3)**: Tests in `tests/development_tools/test_documentation_sync_checker.py` |
| docs/fix_documentation_addresses.py | core | stable | Adds file addresses to documentation files that don't have them. Extracted from fix_documentation.py during Batch 2 decomposition. |
| docs/fix_documentation_ascii.py | core | stable | Fixes non-ASCII characters in documentation files. Extracted from fix_documentation.py during Batch 2 decomposition. |
| docs/fix_documentation_headings.py | core | stable | Numbers H2 and H3 headings in documentation files. Extracted from fix_documentation.py during Batch 2 decomposition. |
| docs/fix_documentation_links.py | core | stable | Converts file path references to markdown links in documentation. Extracted from fix_documentation.py during Batch 2 decomposition. |
| imports/generate_module_dependencies.py | core | stable | Orchestrates module dependency analysis and generates dependency documentation. Refactored after M7.4 completion (2025-12-02) to use analyze_module_imports.py and analyze_dependency_patterns.py. Accepts custom module prefixes for portability. [OK] **HAS TESTS (Phase 3)**: 11 tests in `tests/development_tools/test_generate_module_dependencies.py` |
| imports/analyze_module_imports.py | core | stable | Extracts and analyzes imports from Python files. Extracted from generate_module_dependencies.py after M7.4 completion (2025-12-02). Provides import parsing, scanning, reverse dependencies, dependency changes, purpose inference, and import formatting. |
| imports/analyze_dependency_patterns.py | core | stable | Analyzes dependency patterns, circular dependencies, and risk areas. Extracted from generate_module_dependencies.py after M7.4 completion (2025-12-02). Provides pattern analysis, circular dependency detection, risk area detection, and critical dependency finding. |
| legacy/fix_legacy_references.py | core | stable | Finds/validates LEGACY COMPATIBILITY usage before cleanup. Legacy patterns and mappings load from external config. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_legacy_reference_cleanup.py` |
| tests/generate_test_coverage.py | core | stable | Orchestrates coverage execution (pytest runs), artifact management, and coverage plan updates. Refactored during Batch 3 decomposition to use analyze_test_coverage.py and generate_test_coverage_reports.py. Accepts pytest command, coverage config, and artifact directories via external config. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_regenerate_coverage_metrics.py` |
| analyze_test_coverage.py | core | stable | Parses coverage output and performs coverage analysis. Extracted from generate_test_coverage.py during Batch 3 decomposition. |
| generate_test_coverage_reports.py | core | stable | Generates coverage reports (JSON, HTML) from analysis results. Extracted from generate_test_coverage.py during Batch 3 decomposition. |
| analyze_error_handling.py | core | stable | Audits decorator usage and exception handling depth. Refactored during Batch 3 decomposition to keep only analysis methods. Decorator names and exception classes load from external config. |
| generate_error_handling_report.py | supporting | stable | Generates error handling reports from analysis results. Extracted from analyze_error_handling.py during Batch 3 decomposition. |
| generate_error_handling_recommendations.py | supporting | stable | Generates recommendations for improving error handling based on analysis results. Extracted from analyze_error_handling.py during Batch 3 decomposition. |
| analyze_functions.py | core | stable | AST discovery utility supporting registries and audits. Configurable scan roots and filters via external config. Enhanced with function/class discovery logic from generate_function_registry.py. |
| analyze_function_patterns.py | core | stable | Analyzes function patterns (handlers, managers, factories, etc.) for AI consumption. Extracted from generate_function_registry.py during Batch 3 decomposition. |
| generate_function_registry.py | core | stable | Builds the authoritative function registry via AST parsing. Refactored during Batch 3 decomposition to use analyze_functions.py and analyze_function_patterns.py. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_generate_function_registry.py` |
| analyze_documentation.py | supporting | partial | Secondary doc analysis that focuses on corruption/overlap. |
| analyze_function_registry.py | supporting | partial | Validates generated function registry output. |
| analyze_module_dependencies.py | supporting | partial | Cross-checks generated dependency graphs for accuracy. |
| analyze_package_exports.py | supporting | partial | Confirms package export declarations match filesystem reality. |
| analyze_config.py | supporting | partial | Detects configuration drift and missing values across tools. |
| analyze_ai_work.py | supporting | partial | Lightweight structural validator; advisory results only. |
| analyze_unused_imports.py | supporting | partial | AST-based unused import detector (analysis only, no report generation). |
| generate_unused_imports_report.py | supporting | partial | Generates markdown report from unused imports analysis results. Extracted from analyze_unused_imports.py (2025-12-18) to follow naming conventions. |
| quick_status.py | supporting | advisory | Cached status snapshot that depends on the latest audit run. |
| system_signals.py | supporting | advisory | Collects OS/process health signals for consolidated reports. |
| decision_support.py | supporting | advisory | Aggregates metrics into improvement priorities. |
| shared/file_rotation.py | supporting | stable | Timestamped rotation utility used by coverage generation. |
| shared/tool_guide.py | supporting | stable | Provides contextual guidance and tier overviews for assistants. |
| docs/fix_version_sync.py | experimental | experimental | Attempts cross-file version synchronization (fragile). |
| functions/generate_function_docstrings.py | experimental | experimental | Auto-generates docstrings; high-risk and currently prototype. |

Keep this table synchronized with `shared/tool_metadata.py` and update both when tiers or trust levels change.

---

## 5. Operating Standards and Maintenance

- Follow the audit-first workflow (see [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)) before touching documentation or infrastructure
- **Caching Infrastructure**: Use `shared/mtime_cache.py` (`MtimeFileCache`) for file-based analyzers to cache results based on file modification times. This significantly speeds up repeated runs by only re-processing changed files. The utility handles cache loading, saving, and validation automatically. Currently used by: `analyze_unused_imports.py`, `analyze_ascii_compliance.py`, `analyze_missing_addresses.py`, `analyze_legacy_references.py`. Other analyzers that scan files (e.g., `analyze_path_drift.py`, `analyze_unconverted_links.py`, `analyze_heading_numbering.py`) could benefit from this utility as well.
- **Parallel Execution**: Tools run in parallel where possible to reduce audit time:
  - **Tier 2**: Independent tools (5 tools) run in parallel; dependent groups run sequentially within groups but in parallel with each other
  - **Tier 3**: Coverage group runs sequentially (~450s); legacy and unused imports groups run in parallel with each other
  - **Tool Dependencies**: Some tools must run together due to dependencies (e.g., analysis → report, imports → patterns/dependencies). See `development_tools/shared/service/audit_orchestration.py` for dependency groupings.
- **Output Format Standardization (2025-12-14)**: All 19 analysis tools now output JSON in a standardized structure with `summary` (total_issues, files_affected, status) and `details` (tool-specific data). This enables consistent data aggregation and simplified report generation. Tools support `--json` flag for direct standard format output. The normalization layer in `shared/result_format.py` provides backward compatibility for any legacy formats.
- When adding or relocating tools, update:
  - `shared/tool_metadata.py`
  - This guide and the AI guide (paired H2 requirements)
  - [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md) if scope or gaps change
- Maintain directory integrity (`development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) so automation can locate artifacts; keep generated reports under the paths enumerated in `shared/constants.py`.
- Use the shared test locations: `tests/development_tools/` for suites and `tests/fixtures/development_tools_demo/` for synthetic inputs.
- **Phase 3 Complete (2025-11-26)**: All five core analysis tools have comprehensive test coverage (55+ tests total). The synthetic fixture project provides isolated testing environment for all tool tests.
- For detailed testing guidance, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md).
- Context-specific behavior:
  - `development_tools/config/config.py` defines production / development / testing contexts; commands must honor the active context.
  - Never hardcode project paths - always resolve via `shared/common.py` helpers.
- Run `python development_tools/run_development_tools.py doc-sync` after documentation edits to ensure heading parity and ASCII compliance.
- Treat experimental tools (`docs/fix_version_sync.py`, `functions/generate_function_docstrings.py`, etc.) as opt-in: dry-run first, capture logs, and record findings in [TODO.md](TODO.md) or the improvement plan.
- Keep file organization portable (mirroring `development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) to support eventual extraction of the suite. The baseline structure should remain:

```
development_tools/
ai_development_docs/
development_docs/
tests/development_tools/
tests/fixtures/development_tools_demo/
development_tools/reports/archive/
development_tools/tests/logs/
```

- Do not implement bespoke exclusion logic inside individual tools - always import from `shared/standard_exclusions.py` so rules remain centralized.
- Treat the tooling as a self-contained subproject: track follow-up work in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md), document shipped changes in both changelogs, and keep the AI + human guides synchronized.

Keeping these standards ensures the tooling ecosystem remains predictable for both humans and AI collaborators.

---

## 6. Generated File Metadata Standards

All files generated by the development tools suite must include standardized metadata to identify their origin, generation details, and purpose. This ensures consistency and traceability across all generated artifacts.

### 6.1. Markdown Files (.md)

All generated Markdown files must use this standardized metadata format at the beginning of the file:

```markdown
# Document Title

> **File**: `path/to/file.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: YYYY-MM-DD HH:MM:SS
> **Source**: `python development_tools/path/to/generator.py` - Tool Description
> **Audience**: [Target audience, e.g., "Human developer and AI collaborators"]
> **Purpose**: [What this document is for]
> **Status**: **ACTIVE** - [Brief status note]
```

**Required fields:**
- `File`: Full path from project root
- `Generated`: Standard warning message
- `Last Generated`: Timestamp in `YYYY-MM-DD HH:MM:SS` format
- `Source`: Command and tool description
- `Audience`: Target audience (optional but recommended)
- `Purpose`: Document purpose (optional but recommended)
- `Status`: Current status (optional but recommended)

**Files using this standard:**
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
- `development_docs/LEGACY_REFERENCE_REPORT.md`
- `development_docs/UNUSED_IMPORTS_REPORT.md`
- `development_docs/TEST_COVERAGE_REPORT.md`
- `development_docs/DIRECTORY_TREE.md`
- `ai_development_docs/AI_FUNCTION_REGISTRY.md`
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
- `development_tools/AI_STATUS.md`
- `development_tools/AI_PRIORITIES.md`
- `development_tools/consolidated_report.txt`

### 6.2. JSON Files (.json)

All generated JSON files must include standardized metadata fields at the root level:

```json
{
  "generated_by": "Tool Name - Tool Description",
  "last_generated": "YYYY-MM-DD HH:MM:SS",
  "source": "python development_tools/path/to/tool.py [command]",
  "note": "This file is auto-generated. Do not edit manually.",
  "timestamp": "YYYY-MM-DDTHH:MM:SS.ffffff",
  ...
}
```

**Required fields:**
- `generated_by`: Tool name and description
- `last_generated`: Human-readable timestamp in `YYYY-MM-DD HH:MM:SS` format
- `source`: Command used to generate the file
- `note`: Standard warning message
- `timestamp`: ISO 8601 timestamp for programmatic use

**Files using this standard:**
- `development_tools/reports/analysis_detailed_results.json`
- `development_tools/error_handling/error_handling_details.json`
- `development_tools/config/analyze_config_results.json`

**Note:** Some JSON files are generated by external tools (e.g., `coverage.json` and `coverage_dev_tools.json` by pytest/coverage, located in `development_tools/tests/jsons/`) and may not follow this internal metadata standard. Only files generated by the development tools suite should include this metadata.

For documentation-specific metadata standards, see section 5.1 in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md).

