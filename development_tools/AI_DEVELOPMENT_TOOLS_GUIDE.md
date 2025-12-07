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
- `--config-path <path>` - Override config file path (default: `development_tools_config.json` in project root)

**Most commonly used commands**:
- `audit` - Standard audit (Tier 2 - default, includes quality checks)
- `audit --quick` - Quick audit (Tier 1 - core metrics only, ~30-60s)
- `audit --full` - Full audit (Tier 3 - comprehensive analysis, ~10-30min)
- `status` - Quick system status (uses cached audit data)
- `docs` - Regenerate static documentation artifacts (FUNCTION_REGISTRY, MODULE_DEPENDENCIES, DIRECTORY_TREE)
- `doc-sync` - Check documentation synchronization
- `doc-fix` - Fix documentation issues (addresses, ASCII, headings, links)
- `legacy` - Scan for legacy references
- `coverage` - Regenerate coverage metrics
- `unused-imports` - Detect unused imports
- `config` - Check configuration consistency

**Additional commands**: `quick-audit` (deprecated - use `audit --quick`), `system-signals`, `validate`, `decision-support`, `workflow`, `trees`, `cleanup`, `version-sync` (experimental)

**Note**: Test marker analysis is automatically run during `audit --full` when coverage is generated. For fixing markers, use `development_tools/tests/fix_test_markers.py` directly.

`run_development_tools.py` is the single dispatcher. All commands must:
- Respect shared configuration (`development_tools/config/config.py` with external config file support)
- Honor `shared/standard_exclusions.py`
- Avoid importing application modules directly

**Configuration**: External config file `development_tools_config.json` (in project root) can override paths, project settings, audit behavior, and other configuration. See `development_tools/development_tools_config.json.example` for structure.

---

## 3. Audit Modes and Outputs

### 3.1. Tier 1: Quick Audit - `audit --quick`
- **Duration**: ~30-60 seconds
- **Tools**: Core metrics only
  - `analyze_functions` - Function discovery and complexity metrics
  - `analyze_documentation_sync` - Documentation synchronization status
  - `system_signals` - System health signals
  - `quick_status` - Quick system status snapshot
- **Use case**: Fast health check, pre-commit validation

### 3.2. Tier 2: Standard Audit - `audit` (default)
- **Duration**: ~2-5 minutes
- **Tools**: Everything in Tier 1 PLUS:
  - `analyze_documentation` - Documentation quality analysis
  - `analyze_error_handling` - Error handling coverage
  - `decision_support` - Complexity insights and recommendations
  - `analyze_config` - Configuration validation
  - `analyze_ai_work` - AI work validation
  - `analyze_function_registry` - Function registry validation
  - `analyze_module_dependencies` - Module dependency validation
- **Use case**: Standard quality checks, daily development workflow

### 3.3. Tier 3: Full Audit - `audit --full`
- **Duration**: ~10-30 minutes (depends on test suite)
- **Tools**: Everything in Tier 1 & 2 PLUS:
  - `generate_test_coverage` - Full test coverage regeneration
  - `analyze_unused_imports` - Unused import detection
  - `analyze_legacy_references` - Legacy code scanning
  - `analyze_module_dependencies` - Full dependency analysis
  - Report generators:
    - `generate_legacy_reference_report` -> `development_docs/LEGACY_REFERENCE_REPORT.md`
    - `generate_test_coverage_reports` -> `development_docs/TEST_COVERAGE_REPORT.md`
    - `analyze_unused_imports` -> `development_docs/UNUSED_IMPORTS_REPORT.md`
- **Use case**: Comprehensive analysis, pre-release checks, periodic deep audits

**Note**: All three tiers update the same output files:
- AI-facing (root): `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`
- Central aggregation: `development_tools/reports/analysis_detailed_results.json`
- Domain-specific JSON: Individual tool results in `development_tools/{domain}/jsons/{tool}_results.json` (with automatic archiving)

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

All tools follow a 3-prefix naming system:

- **`analyze_*`** - Finding + assessing (read-only examination, validation, detection)
  - Examples: `analyze_functions.py`, `analyze_documentation.py`, `analyze_error_handling.py`
- **`generate_*`** - Making artifacts (create/recreate documentation, registries, reports)
  - Examples: `generate_function_registry.py`, `generate_test_coverage.py`, `generate_module_dependencies.py`
- **`fix_*`** - Cleanup/repair (removal, cleanup operations)
  - Examples: `fix_legacy_references.py`, `fix_version_sync.py`, `fix_project_cleanup.py`
- **No prefix** - Reporting/utility tools (descriptive names)
  - Examples: `decision_support.py`, `quick_status.py`, `system_signals.py`, `file_rotation.py`

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
- **Documentation & structure**: `docs/analyze_documentation_sync.py` [OK] (paired doc sync only), `docs/analyze_path_drift.py`, `docs/analyze_ascii_compliance.py`, `docs/analyze_heading_numbering.py`, `docs/analyze_missing_addresses.py`, `docs/analyze_unconverted_links.py`, `docs/generate_directory_tree.py`, `docs/fix_documentation.py` [OK] (dispatcher), `docs/fix_documentation_addresses.py`, `docs/fix_documentation_ascii.py`, `docs/fix_documentation_headings.py`, `docs/fix_documentation_links.py`, `functions/generate_function_registry.py` [OK], `functions/analyze_function_patterns.py`, `imports/generate_module_dependencies.py` [OK] (orchestrator), `imports/analyze_module_imports.py` (extracted 2025-12-02), `imports/analyze_dependency_patterns.py` (extracted 2025-12-02), `docs/analyze_documentation.py`
- **Quality, validation, coverage**: `tests/generate_test_coverage.py` [OK], `tests/analyze_test_coverage.py`, `tests/generate_test_coverage_reports.py`, `ai_work/analyze_ai_work.py`, `imports/analyze_unused_imports.py`, `error_handling/analyze_error_handling.py`, `error_handling/generate_error_handling_report.py`, `error_handling/generate_error_handling_recommendations.py`
- **Legacy, versioning, signals**: `legacy/fix_legacy_references.py` [OK], `reports/system_signals.py`, `reports/quick_status.py`, `docs/fix_version_sync.py` (experimental)
- **Decision & utilities**: `reports/decision_support.py`, `functions/analyze_functions.py`, `functions/generate_function_docstrings.py` (experimental), `config/analyze_config.py`, `shared/file_rotation.py`, `functions/analyze_*` helpers, `shared/tool_guide.py`

[OK] = Has comprehensive test coverage (Phase 3)

Consult `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` for the detailed tier and trust matrix.

---

## 5. Operating Standards and Maintenance

- Use shared infrastructure: `shared/standard_exclusions.py`, `shared/constants.py`, `config/config.py`, `shared/mtime_cache.py`
- **Caching**: Use `shared/mtime_cache.py` (`MtimeFileCache`) for file-based analyzers to cache results based on file modification times. This significantly speeds up repeated runs by only re-processing changed files. Currently used by: `analyze_unused_imports.py`, `analyze_ascii_compliance.py`, `analyze_missing_addresses.py`
- Never hardcode project paths; derive them from configuration helpers
- Keep tools isolated from MHM business logic
- Store tests under `tests/development_tools/` (with fixtures in `tests/fixtures/development_tools_demo/`)
- **Phase 3 Complete (2025-11-26)**: Core analysis tools now have comprehensive test coverage (55+ tests) using the synthetic fixture project
- For detailed testing guidance, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)
- **Phase 4 Follow-up (2025-11-27)**: Supporting tools `reports/quick_status.py`, `reports/system_signals.py`, and `shared/file_rotation.py` now have targeted regression tests in `tests/development_tools/test_supporting_tools.py`
- **Phase 6 Complete (2025-11-28)**: All core tools are now portable via external configuration (`development_tools_config.json`). Tools can be used in other projects with minimal setup.
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

**Note:** External tool outputs (e.g., `coverage.json` from pytest/coverage) may not follow this standard.
