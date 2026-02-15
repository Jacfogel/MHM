# AI Development Tools Guide

> **File**: `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`  
> **Audience**: AI collaborators and automated tooling  
> **Purpose**: Routing and constraints for all AI development tools used to analyze, audit, and maintain the MHM codebase  
> **Style**: Minimal, reference-only (no deep explanations)  
> **Pair**: [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md)  
> This document is paired with `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`. Keep both H2 headings identical and consider changes in the context of the human counterpart.

---

## 1. Purpose and Scope

This guide provides a precise, machine-friendly map of the AI development tools:
- Summarizes **what commands exist** and **when to run them**
- Routes you to the authoritative metadata in `development_tools/shared/tool_metadata.py`
- Delegates deeper explanations to the human guide and the AI workflow/docs references:
  - [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md)
  - [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)
  - [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)

Treat this file as the routing layer for AI collaborators; avoid duplicating human-facing narrative here.

---

## 2. Running the Tool Suite

```powershell
python development_tools/run_development_tools.py <command>
python development_tools/run_dev_tools.py <command>  # Shorthand alias
python development_tools/run_development_tools.py --project-root <path> <command>
python development_tools/run_development_tools.py --config-path <path> <command>
python development_tools/run_development_tools.py help
```

**Global Options**:
- `--project-root <path>` - Override project root directory
- `--config-path <path>` - Override config file path (default: `development_tools/config/development_tools_config.json`)

**Most commonly used commands**:
- `audit` - Standard audit (Tier 2 - default, includes quality checks)
- `audit --quick` - Quick audit (Tier 1 - core metrics only, ~30-60s)
- `audit --full` - Full audit (Tier 3 - comprehensive analysis, ~10-30min). Alias: `full-audit`.
- `audit --full --strict` - Full audit with fail-fast exit semantics for Tier 3 test failures/crashes.
- `status` - Quick system status (uses cached audit data)
- `docs` - Regenerate static documentation artifacts (FUNCTION_REGISTRY, MODULE_DEPENDENCIES, DIRECTORY_TREE)
- `doc-sync` - Check documentation synchronization
- `doc-fix` - Fix documentation issues (addresses, ASCII, headings, links). Alias: `--full` == `--all`.
- `legacy` - Scan for legacy references
- `coverage` - Regenerate coverage metrics
- `unused-imports` - Detect unused imports (analysis only)
- `unused-imports-report` - Generate unused imports report from analysis results
- `config` - Check configuration consistency

**Additional commands**: `system-signals`, `validate`, `decision-support`, `unused-imports`, `duplicate-functions`, `workflow`, `trees`, `cleanup` (alias: `clean-up`), `export-code`, `version-sync` (experimental)

**Note**: Test marker analysis is automatically run during `audit --full` when coverage is generated. For fixing markers, use `development_tools/tests/fix_test_markers.py` directly.

**Service Architecture**: The tool suite uses a modular service architecture. `AIToolsService` is composed from mixin classes in `development_tools/shared/service/`: `development_tools/shared/service/core.py` (base class), `development_tools/shared/service/utilities.py` (formatting/extraction), `development_tools/shared/service/data_loading.py` (data parsing), `development_tools/shared/service/tool_wrappers.py` (tool execution), `development_tools/shared/service/audit_orchestration.py` (audit workflow), `development_tools/shared/service/report_generation.py` (report generation), and `development_tools/shared/service/commands.py` (command handlers). The CLI interface (`COMMAND_REGISTRY` and command handlers) is in `development_tools/shared/cli_interface.py`. Import `AIToolsService` from `development_tools.shared.service` and `COMMAND_REGISTRY` from `development_tools.shared.cli_interface`.

`run_development_tools.py` is the single dispatcher. All commands must:
- Respect shared configuration (`development_tools/config/config.py` with external config file support)
- Honor `shared/standard_exclusions.py`
- Avoid importing application modules directly

**Configuration**: External config file `development_tools/config/development_tools_config.json` can override paths, project settings, audit behavior, and other configuration. See `development_tools/development_tools_config.json.example` for structure.

---

## 3. Audit Modes and Outputs

### 3.1. Tier 1: Quick Audit - `audit --quick`
- **Duration**: ~5-10 seconds (with parallel execution)
- **Tools**: All tools <=2s execution time
  - **Core tools**: `analyze_system_signals`, `quick_status`
  - **Quick checks**: `analyze_documentation`, `analyze_config`, `analyze_ai_work`
  - **Module imports**: `analyze_module_imports`, `analyze_dependency_patterns`
  - **Function analysis**: `analyze_function_patterns`, `decision_support`, `analyze_function_registry`
- **Execution**: Tools run in parallel where possible, with dependency-aware grouping
- **Use case**: Fast health check, pre-commit validation

### 3.2. Tier 2: Standard Audit - `audit` (default)
- **Duration**: ~15-25 seconds (with parallel execution)
- **Tools**: All tools >2s but <=10s execution time
  - **Function discovery**: `analyze_functions` (required by dependent tools)
  - **Quality checks**: `analyze_error_handling`, `analyze_package_exports`
  - **Documentation sync**: `analyze_documentation_sync` (includes multiple sub-tools)
  - **Module dependencies**: `analyze_module_dependencies` (depends on `analyze_module_imports` from Tier 1)
  - **Unused imports**: `analyze_unused_imports`, `generate_unused_imports_report`
- **Execution**: Tools run in parallel where possible, with dependency-aware grouping
- **Use case**: Standard quality checks, daily development workflow

### 3.3. Tier 3: Full Audit - `audit --full`
- **Duration**: ~6-7 minutes (coverage tools run in parallel, reducing total time from ~460s to ~365s)
- **Tools**: Everything in Tier 1 & 2 PLUS tools >10s (or groups containing tools >10s):
  - **Coverage tools** (run in parallel, ~365s max):
    - `run_test_coverage` - Full test coverage execution (~365s, >10s)
    - `generate_dev_tools_coverage` - Dev tools test coverage (~94s, >10s, runs in parallel with main tests)
  - **Coverage-dependent tools** (run sequentially after coverage completes, ~7s):
    - `analyze_test_markers` - Test marker analysis (~2s, requires coverage data)
    - `generate_test_coverage_report` - Coverage report generation (~5s, generates TEST_COVERAGE_REPORT.md, HTML, JSON)
  - **Legacy group** (runs in parallel with coverage tools):
    - `analyze_legacy_references` - Legacy code scanning (~62s, >10s)
    - `generate_legacy_reference_report` - Legacy report generation (~1s, but part of legacy group)
- **Execution**: Coverage tools and legacy group run in parallel; coverage-dependent tools run sequentially after coverage completes
- **Use case**: Comprehensive analysis, pre-release checks, periodic deep audits
- **Tier 3 outcome states**: `clean`, `test_failures`, `crashed`, `infra_cleanup_error`, `coverage_failed`.
- **Strict mode behavior**: `audit --strict` returns non-zero for Tier 3 `test_failures` or `crashed`; default audit mode remains non-strict.

**Note**: All three tiers update the same output files:
- AI-facing (root): `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.md`
- Central aggregation: `development_tools/reports/analysis_detailed_results.json`
- Domain-specific JSON: Individual tool results in `development_tools/{domain}/jsons/{tool}_results.json` (with automatic archiving)

**Report Format Standards**:
- **AI_STATUS.md**: High-level summary including Function Docstring Coverage (with missing count) and Registry Gaps (separate metrics)
- **AI_PRIORITIES.md**: Actionable priorities with prioritized example lists (functions and handler classes) using ", ... +N" format when there are more items
- **consolidated_report.md**: Comprehensive details including all metrics from AI_STATUS plus detailed example lists in the Function Patterns section

**Tool Output Format (Standard Format)**:
- Analysis tools that participate in audit aggregation emit or are normalized to a standardized JSON structure:
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
- Tools can be run with `--json` flag to output standard format directly
- Results are expected to already be in standard format (strict validation)
- Report generation code accesses data from `details` section when in standard format

**Tool Output Storage**:
- Individual tool results: `development_tools/{domain}/jsons/{tool}_results.json` (e.g., `functions/jsons/analyze_functions_results.json`)
- Cache files: `development_tools/{domain}/jsons/.{tool}_cache.json`
- Archives: `development_tools/{domain}/jsons/archive/` (keeps last 5 versions)
- Central aggregation: `development_tools/reports/analysis_detailed_results.json` (aggregates all tool results)

**Human-facing reports** (generated by Tier 3):
- `development_docs/LEGACY_REFERENCE_REPORT.md`
- `development_docs/TEST_COVERAGE_REPORT.md`
- `development_docs/UNUSED_IMPORTS_REPORT.md`

**Static documentation** (regenerated via `docs` command, not during audits):
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
- `ai_development_docs/AI_FUNCTION_REGISTRY.md`
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`
- `development_docs/DIRECTORY_TREE.md`

The `status` command surfaces cached summaries from `reports/analysis_detailed_results.json` (complexity, validation, system signals); rerun `audit` if the cache is stale.

**When to run each command**: See "Standard Audit Recipe" in [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for guidance on day-to-day checks, pre-merge checks, and documentation work.

---

## 4. Tool Catalog and Tiering

Each module declares:

```
# TOOL_TIER: core | supporting | experimental
```

The authoritative table lives in `shared/tool_metadata.py`. Use this guide to pick the right group quickly:

### 4.1. Naming Conventions

Most tools follow prefix-based naming to indicate primary intent; shared and orchestration tools may not:

- **`analyze_*`** - Finding + assessing (read-only examination, validation, detection)
  - Examples: `analyze_functions.py`, `analyze_documentation.py`, `analyze_error_handling.py`
- **`generate_*`** - Making artifacts (create/recreate documentation, registries, reports)
  - Examples: `generate_function_registry.py`, `tests/run_test_coverage.py`, `generate_module_dependencies.py`
- **`fix_*`** - Cleanup/repair (removal, cleanup operations)
  - Examples: `fix_legacy_references.py`, `fix_version_sync.py`, `fix_project_cleanup.py`
- **No prefix** - Reporting/utility tools (descriptive names)
  - Examples: `decision_support.py`, `quick_status.py`, `analyze_system_signals.py`, `file_rotation.py`

Tools are organized by domain (functions/, docs/, tests/, etc.) and follow these naming conventions consistently.

**Directory Structure** (domain-based organization):
- `functions/` - Function discovery, registry generation, audits
- `imports/` - Import checking, module dependency analysis and audits (merged from `modules/`)
- `error_handling/` - Error handling coverage analysis
- `tests/` - Test coverage metrics
- `docs/` - Documentation analysis and sync checking
- `config/` - Configuration validation
- `legacy/` - Legacy cleanup
- `ai_work/` - AI work validation
- `reports/` - Overarching analysis (consolidated reports)
- `shared/` - Shared infrastructure (config, constants, exclusions, metadata)

**Tool Categories**:
- **Documentation & structure**: `docs/analyze_documentation_sync.py` (paired doc sync only), `docs/analyze_path_drift.py`, `docs/analyze_ascii_compliance.py`, `docs/analyze_heading_numbering.py`, `docs/analyze_missing_addresses.py`, `docs/analyze_unconverted_links.py`, `docs/generate_directory_tree.py`, `docs/fix_documentation.py` (dispatcher), `docs/fix_documentation_addresses.py`, `docs/fix_documentation_ascii.py`, `docs/fix_documentation_headings.py`, `docs/fix_documentation_links.py`, `functions/generate_function_registry.py`, `functions/analyze_function_patterns.py`, `functions/analyze_duplicate_functions.py`, `imports/generate_module_dependencies.py` (orchestrator), `imports/analyze_module_imports.py`, `imports/analyze_dependency_patterns.py`, `docs/analyze_documentation.py`
- **Quality, validation, coverage**: `tests/run_test_coverage.py`, `tests/analyze_test_coverage.py`, `tests/generate_test_coverage_report.py`, `ai_work/analyze_ai_work.py`, `imports/analyze_unused_imports.py`, `imports/generate_unused_imports_report.py`, `error_handling/analyze_error_handling.py`, `error_handling/generate_error_handling_report.py`
- **Legacy, versioning, signals**: `legacy/fix_legacy_references.py`, `reports/analyze_system_signals.py`, `reports/quick_status.py`, `docs/fix_version_sync.py` (experimental)
- **Decision & utilities**: `reports/decision_support.py`, `functions/analyze_functions.py`, `functions/generate_function_docstrings.py` (experimental), `config/analyze_config.py`, `shared/file_rotation.py`, `functions/analyze_*` helpers, `shared/tool_guide.py`

Consult [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md) for the detailed tier and trust matrix.

---

## 5. Operating Standards and Maintenance

- Use shared infrastructure: `shared/standard_exclusions.py`, `shared/constants.py`, `config/config.py`, `shared/mtime_cache.py`
- Keep the standard exclusions + config aligned so `.ruff_cache`, `mhm.egg-info`, `scripts`, `tests/ai/results`, and `tests/coverage_html` are skipped by the majority of analyzer runs.
- **Caching**:
  - **General analyzer caching (`shared/mtime_cache.py`)**: Caches file-based analyzer outputs by input mtimes and auto-invalidates when either `development_tools/config/development_tools_config.json` or the tool source changes. Cache keys are namespaced by tool/domain/config-signature/tool-hash, and cache payload includes tool hash, tool mtimes, and last run status for failure-aware invalidation. Used by high-cost analyzers across `imports/`, `functions/`, `docs/`, `legacy/`, and `tests/analyze_test_coverage.py`.
  - **Coverage analysis cache**: `tests/analyze_test_coverage.py` caches coverage analysis from coverage JSON mtime.
  - **Domain test coverage cache (`tests/test_file_coverage_cache.py`)**:
    - Uses `tests/domain_mapper.py` to rerun only test files covering changed domains.
    - Stores run status and failed domains for failure-aware invalidation.
    - Stores tool hash/tool mtimes and config mtime for global invalidation when cache logic/config changes.
    - Cache file: `development_tools/tests/jsons/test_file_coverage_cache.json` (enabled by default; disable with `--no-domain-cache`).
  - **Dev tools coverage cache (`tests/dev_tools_coverage_cache.py`)**:
    - Caches `development_tools` coverage JSON keyed by dev-tools source/test/config mtimes.
    - Stores tool hash/tool mtimes for invalidation when coverage tooling code changes.
    - Stores last run success/exit code and invalidates after failed previous runs.
    - Cache file: `development_tools/tests/jsons/dev_tools_coverage_cache.json` (enabled by default; disable with `--no-domain-cache`).
  - **Cache management**:
    - `python development_tools/run_development_tools.py audit --clear-cache` clears development-tools cache artifacts only (tool cache/result artifacts used by development-tools freshness logic).
    - `python development_tools/run_development_tools.py cleanup --cache` clears all cache categories (tool caches/results + `__pycache__` + `.pytest_cache` + coverage cache artifacts).
- **Parallel Execution**: Tools run in parallel where possible, with dependency-aware grouping:
  - **Tier 2**: Independent tools run in parallel; dependent groups (module imports, function patterns, decision support, function registry) run sequentially within groups but in parallel with each other
  - **Tier 3**: Coverage group runs sequentially; legacy and unused imports groups run in parallel with each other (tools within each group run sequentially)
  - **Tool Dependencies**: Some tools must stay together due to dependencies (see tool dependency notes in audit orchestration)
- **Output Format**: All analysis tools output standard format JSON with `summary` (total_issues, files_affected, status) and `details` (tool-specific data). Use `--json` flag when running tools standalone to get standard format output.
- Never hardcode project paths; derive them from configuration helpers
- Keep tools isolated from MHM business logic
- Store tests under `tests/development_tools/` (with fixtures in `tests/fixtures/development_tools_demo/`)
- For detailed testing guidance, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)

- All core tools are portable via external configuration (`development_tools/config/development_tools_config.json`). Tools can be used in other projects with minimal setup.
- Preserve the directory structure (`development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) to ease eventual extraction
- Treat experimental tools cautiously (dry-run first, log outcomes)
- Keep this guide paired with the human document; update both whenever commands, tiers, or workflows change

---

## 6. Generated File Metadata Standards

All files generated by the development tools suite must include standardized metadata. See section 6 in [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md) for detailed standards.

**Markdown files (.md):** Must include `File`, `Generated`, `Last Generated`, `Source`, and optionally `Audience`, `Purpose`, `Status`.

**JSON files (.json):** Must include `generated_by`, `last_generated`, `source`, `note`, and `timestamp` at the root level.

**Examples:**
- Markdown: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_tools/AI_STATUS.md`
- JSON: `development_tools/reports/analysis_detailed_results.json`, `development_tools/error_handling/error_handling_details.json`

**Note:** External tool outputs (e.g., `coverage.json` and `coverage_dev_tools.json` from pytest/coverage, located in `development_tools/tests/jsons/`) may not follow this standard.
