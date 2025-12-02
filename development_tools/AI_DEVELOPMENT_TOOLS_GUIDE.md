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
- `audit` / `audit --full` - Fast or comprehensive audit
- `status` - Quick system status (uses cached audit data)
- `docs` - Regenerate documentation artifacts
- `doc-sync` - Check documentation synchronization
- `doc-fix` - Fix documentation issues (addresses, ASCII, headings, links)
- `legacy` - Scan for legacy references
- `coverage` - Regenerate coverage metrics
- `unused-imports` - Detect unused imports
- `config` - Check configuration consistency

**Additional commands**: `quick-audit`, `system-signals`, `validate`, `decision-support`, `workflow`, `trees`, `version-sync` (experimental)

`run_development_tools.py` is the single dispatcher. All commands must:
- Respect shared configuration (`development_tools/config/config.py` with external config file support)
- Honor `shared/standard_exclusions.py`
- Avoid importing application modules directly

**Configuration**: External config file `development_tools_config.json` (in project root) can override paths, project settings, audit behavior, and other configuration. See `development_tools/development_tools_config.json.example` for structure.

---

## 3. Audit Modes and Outputs

### 3.1. Fast mode - `audit`
- Documentation and legacy signals
- Complexity metrics (moderate/high/critical function counts)
- Validation summaries and quick metrics
- System signals + cached data

### 3.2. Full mode - `audit --full`
- Full pytest + coverage regeneration
- Unused import detection
- Dependency + registry regeneration
- HTML coverage reports
- All fast mode data plus comprehensive coverage analysis

Outputs land in predictable locations:
- AI-facing (root): `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`
- Domain-specific JSON: `reports/analysis_detailed_results.json`, `error_handling/error_handling_details.json`, `tests/coverage_dev_tools.json`, `config/analyze_config_results.json`, `imports/.unused_imports_cache.json`
- Human-facing: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/MODULE_DEPENDENCIES_DETAIL.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`, `development_docs/UNUSED_IMPORTS_REPORT.md`
- Coverage artifacts: `coverage.json` (project root), `tests/coverage_html/` (project root), `development_tools/reports/archive/coverage_artifacts/<timestamp>/`
- Dev tools coverage (audit --full): `tests/coverage_dev_tools.json` (HTML reports disabled)

The `status` command surfaces cached summaries from `reports/analysis_detailed_results.json` (complexity, validation, system signals); rerun `audit` if the cache is stale.

**When to run each command**: See "Standard Audit Recipe" in [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for guidance on day-to-day checks, pre-merge checks, and documentation work.

---

## 4. Tool Catalog and Tiering

Each module declares:

```
# TOOL_TIER: core | supporting | experimental
```

The authoritative table lives in `shared/tool_metadata.py`. Use this guide to pick the right group quickly:

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

- Use shared infrastructure: `shared/standard_exclusions.py`, `shared/constants.py`, `config/config.py`
- Never hardcode project paths; derive them from configuration helpers
- Keep tools isolated from MHM business logic
- Store tests under `tests/development_tools/` (with fixtures in `tests/fixtures/development_tools_demo/`)
- **Phase 3 Complete (2025-11-26)**: Core analysis tools now have comprehensive test coverage (55+ tests) using the synthetic fixture project
- **Phase 4 Follow-up (2025-11-27)**: Supporting tools `reports/quick_status.py`, `reports/system_signals.py`, and `reports/file_rotation.py` now have targeted regression tests in `tests/development_tools/test_supporting_tools.py`
- **Phase 6 Complete (2025-11-28)**: All core tools are now portable via external configuration (`development_tools_config.json`). Tools can be used in other projects with minimal setup.
- Preserve the directory structure (`development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) to ease eventual extraction
- Treat experimental tools cautiously (dry-run first, log outcomes)
- Keep this guide paired with the human document; update both whenever commands, tiers, or workflows change
