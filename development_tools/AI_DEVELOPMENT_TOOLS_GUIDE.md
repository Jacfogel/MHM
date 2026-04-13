# AI Development Tools Guide

> **File**: `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`  
> **Audience**: AI collaborators and automated tooling  
> **Purpose**: Routing and constraints for all AI development tools used to analyze, audit, and maintain the MHM codebase  
> **Style**: Minimal, reference-only (no deep explanations)  
> **Pair**: [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) - keep both H2 headings identical and consider changes in the context of the human counterpart.

---

## 1. Purpose and Scope

This guide provides a precise, machine-friendly map of the AI development tools:
- Summarizes **what commands exist** and **when to run them**
- **Authoritative command list**: `python development_tools/run_development_tools.py help`; tool and tier metadata in `development_tools/shared/tool_metadata.py`. Guide tables are for orientation only.
- Delegates deeper explanations to the human guide and the AI workflow/docs references:
  - [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md)
  - [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)
  - [AI_DOCUMENTATION_GUIDE.md](../ai_development_docs/AI_DOCUMENTATION_GUIDE.md)

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
- `full-audit` - Alias command for `audit --full`.
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

**Additional commands**: `system-signals`, `validate`, `decision-support`, `unused-imports`, `unused-imports-report`, `flaky-detector` (manual only; not part of `audit --full`), `verify-process-cleanup` (Tier 3 audit), `duplicate-functions`, `module-refactor-candidates`, `workflow`, `trees`, `cleanup` (alias: `clean-up`), `backup`, `export-code`, `export-docs`, `version-sync` (experimental; delegates to `docs/fix_version_sync.py` - use `python development_tools/docs/fix_version_sync.py --help` for `show` / `status` / `sync` / `trim` / `check` / `validate` / `sync-todo`). For `duplicate-functions`, use `--consider-body-similarity` to include body/structural (AST) similarity; increases runtime and pair count (capped by `max_body_candidate_pairs` and `body_similarity_scope` in config). During **full audit** (`audit --full`), body similarity runs automatically only on *near-miss* name-token pairs (name similarity above `body_similarity_min_name_threshold` but below the normal reporting bar); disable with `run_body_similarity_on_full_audit: false` in config.

**Note**: Test marker analysis is automatically run during `audit --full` when coverage is generated. For fixing markers, use `development_tools/tests/fix_test_markers.py` directly.

**Service Architecture**: The tool suite uses a modular service architecture. `AIToolsService` is composed from mixin classes in `development_tools/shared/service/`: `development_tools/shared/service/core.py` (base class), `development_tools/shared/service/utilities.py` (formatting/extraction), `development_tools/shared/service/data_loading.py` (data parsing), `development_tools/shared/service/tool_wrappers.py` (tool execution), `development_tools/shared/service/audit_orchestration.py` (audit workflow), `development_tools/shared/service/report_generation.py` (report generation), and `development_tools/shared/service/commands.py` (command handlers). The CLI interface (`COMMAND_REGISTRY` and command handlers) is in `development_tools/shared/cli_interface.py`. Import `AIToolsService` from `development_tools.shared.service` and `COMMAND_REGISTRY` from `development_tools.shared.cli_interface`.

`run_development_tools.py` is the single dispatcher. All commands must:
- Respect shared configuration (`development_tools/config/config.py` with external config file support)
- Honor `shared/standard_exclusions.py`
- Avoid importing application modules directly

**Configuration**: External config file `development_tools/config/development_tools_config.json` can override paths, project settings, audit behavior, and other configuration. See `development_tools/config/development_tools_config.json.example` for structure. Config directory: `development_tools_config.json` is project-specific (not in git; copy from `.example`). `DEPRECATION_INVENTORY.json` lives in `development_tools/config/jsons/` (covered by `development_tools/**/jsons/` ignore). `ruff.toml` is generated by `development_tools/config/sync_ruff_toml.py` (run `python -m development_tools.config.sync_ruff_toml` to regenerate).

**Dependencies**: Root `requirements.txt` supplies Ruff, Pyright, pytest, coverage, and other audit helpers (no separate `development_tools/requirements.txt`). **Porting the tool suite**: copy `development_tools/` into another repo, install a matching Python stack, and ensure tools referenced in `development_tools/config/development_tools_config.json` are available; optional future: `pip install .[devtools]` or a pinned `requirements-devtools.txt`. Details in **Section 2** of [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md).

**Static analysis config ownership**:
- Ruff owned config path: `static_analysis.ruff_config_path` (default `development_tools/config/ruff.toml`)
- Pyright owned project config path: `static_analysis.pyright_project_path` (default `pyproject.toml` for `[tool.pyright]`)
- Root Ruff compatibility mirror toggle: `static_analysis.ruff_sync_root_compat` (default `true`)
- `analyze_ruff` always passes explicit `--config` to the owned Ruff config path.
- `analyze_pyright` always passes explicit `--project` to the configured Pyright config path unless `--project` is already present in `static_analysis.pyright_args`.

**Lock handling**: Audit/coverage locks use metadata JSON payloads in the existing lock files. Stale or malformed locks are auto-cleaned; active locks (live PID within stale window) block conflicting `audit`, `full-audit`, and `docs` operations.

**Coverage worker config keys** (`coverage` section): `main_workers`, `dev_tools_workers`, `main_workers_when_concurrent`, `dev_tools_workers_when_concurrent`. Tier 3 concurrent defaults are `6` (main) and `2` (dev-tools) unless overridden.

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
- **Duration**: Environment-dependent (~6-30+ minutes); heaviest wall-clock is usually `run_test_coverage`
- **Tools**: Everything in Tier 1 & 2 PLUS tools >10s (or groups containing tools >10s):
  - **Coverage (full-repo scope)** - exactly **one** subprocess: `run_test_coverage` runs the **full** suite including `tests/development_tools/`, measures product packages **and** the `development_tools` tree per `development_tools/tests/coverage.ini`, writes `development_tools/tests/jsons/coverage.json`, derives `coverage_dev_tools.json` for dev-tools-only metrics, and persists `generate_dev_tools_coverage` results after success. Tier 3 schedules **no** separate `generate_dev_tools_coverage` in the same pass when scope is full-repo ([development_tools/shared/audit_tiers.py](shared/audit_tiers.py) `get_tier3_groups`).
  - **Coverage (`--dev-tools-only`)** - only `generate_dev_tools_coverage` (dev-tools tests + dev-tools coverage config); main `coverage.json` / `development_docs/TEST_COVERAGE_REPORT.md` are not refreshed this pass (reports document that).
  - **Coverage-dependent tools** (run sequentially after the coverage step for this scope, ~7s full-repo):
    - `analyze_test_markers` - Test marker analysis (~2s, requires coverage data)
    - `generate_test_coverage_report` - Coverage report generation (~5s; **full-repo only**, generates `development_docs/TEST_COVERAGE_REPORT.md` from main coverage data)
  - **Legacy group** (runs in parallel with the coverage step):
    - `analyze_legacy_references` - Legacy code scanning (~62s, >10s)
    - `generate_legacy_reference_report` - Legacy report generation (~1s, but part of legacy group)
  - **Static analysis group** (runs in parallel with coverage and legacy groups):
    - `analyze_ruff` - Ruff diagnostics summary (advisory)
    - `analyze_pyright` - Pyright diagnostics summary (advisory)
- **Execution**: The coverage subprocess group, legacy group, and static-analysis group run in parallel where the platform allows; coverage-dependent tools run sequentially after coverage completes
- **Use case**: Comprehensive analysis, pre-release checks, periodic deep audits
- **Tier 3 outcome states**: `clean`, `test_failures`, `crashed`, `infra_cleanup_error`, `coverage_failed`.
- **Strict mode behavior**: `audit --strict` returns non-zero for Tier 3 `test_failures`, `crashed`, or `infra_cleanup_error`; default audit mode remains non-strict.
- **Track classification fields**: Tier 3 `coverage_outcome.parallel`/`coverage_outcome.no_parallel` include `classification`, `classification_reason`, `actionable_context`, `log_file`, and `return_code_hex` in addition to legacy state/count fields.

**Note**: All three tiers update the same output files:
- AI-facing (root): `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/CONSOLIDATED_REPORT.md`
- Central aggregation: `development_tools/reports/analysis_detailed_results.json`
- Domain-specific JSON: Individual tool results in `development_tools/{domain}/jsons/{tool}_results.json` (with automatic archiving)

**Report Format Standards**:
- **AI_STATUS.md**: High-level summary including Function Docstring Coverage (with missing count) and Registry Gaps (separate metrics)
- **AI_PRIORITIES.md**: Actionable priorities with prioritized example lists (functions and handler classes) using ", ... +N" format when there are more items
- **CONSOLIDATED_REPORT.md**: Comprehensive details including all metrics from AI_STATUS plus detailed example lists in the Function Patterns section

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

**When to run each command**: See "Standard Audit Recipe" in [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for guidance on day-to-day checks, pre-merge checks, and documentation work.

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
- **Documentation & structure**: `docs/analyze_documentation_sync.py` (paired doc sync only), `docs/analyze_path_drift.py`, `docs/analyze_ascii_compliance.py`, `docs/analyze_heading_numbering.py`, `docs/analyze_missing_addresses.py`, `docs/analyze_unconverted_links.py`, `docs/generate_directory_tree.py`, `docs/fix_documentation.py` (dispatcher), `docs/fix_documentation_addresses.py`, `docs/fix_documentation_ascii.py`, `docs/fix_documentation_headings.py`, `docs/fix_documentation_links.py`, `functions/generate_function_registry.py`, `functions/analyze_function_patterns.py`, `functions/analyze_duplicate_functions.py`, `functions/analyze_module_refactor_candidates.py`, `imports/generate_module_dependencies.py` (orchestrator), `imports/analyze_module_imports.py`, `imports/analyze_dependency_patterns.py`, `docs/analyze_documentation.py`
- **Quality, validation, coverage**: `tests/run_test_coverage.py`, `tests/analyze_test_coverage.py`, `tests/generate_test_coverage_report.py`, `ai_work/analyze_ai_work.py`, `imports/analyze_unused_imports.py`, `imports/generate_unused_imports_report.py`, `error_handling/analyze_error_handling.py`, `error_handling/generate_error_handling_report.py`
- **Legacy, versioning, signals**: `legacy/fix_legacy_references.py`, `reports/analyze_system_signals.py`, `reports/quick_status.py`, `docs/fix_version_sync.py` (experimental)
- **Static analysis**: `static_checks/analyze_ruff.py`, `static_checks/analyze_pyright.py`, `static_checks/check_channel_loggers.py`
- **Decision & utilities**: `reports/decision_support.py`, `functions/analyze_functions.py`, `functions/fix_function_docstrings.py` (experimental), `config/analyze_config.py`, `shared/file_rotation.py`, `functions/analyze_*` helpers, `shared/tool_guide.py`

Consult [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) for the detailed tier and trust matrix.

---

## 5. Operating Standards and Maintenance

- Use shared infrastructure: `shared/standard_exclusions.py`, `shared/constants.py`, `development_tools/config/config.py`, `shared/mtime_cache.py`
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
    - `python development_tools/run_development_tools.py audit --clear-cache` (alias: `--cache-clear`) clears development-tools audit caches: `**/jsons/scopes/{full,dev_tools}/**`, `reports/scopes/{full,dev_tools}/**`, `reports/archive/**`, legacy flat `reports/analysis_detailed_results.json` and `reports/jsons/tool_timings.json`, plus existing per-tool dot-caches and coverage JSON under `tests/jsons/` (not `__pycache__` / `.pytest_cache` / `reports/logs/`).
    - `python development_tools/run_development_tools.py cleanup --cache` clears all cache categories (tool caches/results + `__pycache__` + `.pytest_cache` + coverage cache artifacts).
  - **Backup policy workflows**:
    - `python development_tools/run_development_tools.py backup inventory` builds ownership and producer inventory from `backup_policy`.
    - `python development_tools/run_development_tools.py backup retention --dry-run|--apply` enforces Category-B retention on development-tools-owned artifacts.
    - `python development_tools/run_development_tools.py backup drill` executes isolated restore drill and writes drill reports.
    - `python development_tools/run_development_tools.py backup verify` runs end-to-end backup health checks (inventory + newest-backup validation + restore drill).
- **Documentation overlap (V5 Section 5.2 backlog)**: `analyze_documentation` / doc-sync can emit `section_overlaps` and consolidation hints; they also surface in `AI_STATUS.md` / `CONSOLIDATED_REPORT.md`. Treat as advisory-verify against [LIST_OF_LISTS.md](../development_docs/LIST_OF_LISTS.md) and paired-guide boundaries before large doc merges.
- **Parallel Execution**: Tools run in parallel where possible, with dependency-aware grouping:
  - **Tier 2**: Independent tools run in parallel; dependent groups (module imports, function patterns, decision support, function registry) run sequentially within groups but in parallel with each other
  - **Tier 3**: Coverage group runs sequentially; legacy and unused imports groups run in parallel with each other (tools within each group run sequentially)
  - **Tool Dependencies**: Some tools must stay together due to dependencies (see tool dependency notes in audit orchestration)
- **Output Format**: All analysis tools output standard format JSON with `summary` (total_issues, files_affected, status) and `details` (tool-specific data). Use `--json` flag when running tools standalone to get standard format output.
- Never hardcode project paths; derive them from configuration helpers
- Keep tools isolated from MHM business logic
- Store tests under `tests/development_tools/` (with fixtures in `tests/fixtures/development_tools_demo/`)
- For detailed testing guidance, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](../tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)

- All core tools are portable via external configuration (`development_tools/config/development_tools_config.json`). Tools can be used in other projects with minimal setup.
- Preserve the directory structure (`development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) to ease eventual extraction
- Treat experimental tools cautiously (dry-run first, log outcomes)
- Keep this guide paired with the human document; update both whenever commands, tiers, or workflows change

---

## 6. Generated File Metadata Standards

All files generated by the development tools suite must include standardized metadata. See section 6 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) for detailed standards.

**Markdown files (.md):** Must include `File`, `Generated`, `Last Generated`, `Source`, and optionally `Audience`, `Purpose`, `Status`.

**JSON files (.json):** Must include `generated_by`, `last_generated`, `source`, `note`, and `timestamp` at the root level.

**Examples:**
- Markdown: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_tools/AI_STATUS.md`
- JSON: `development_tools/reports/scopes/full/analysis_detailed_results.json` (scoped aggregate), `development_tools/error_handling/error_handling_details.json`

**Note:** External tool outputs (e.g., `coverage.json` and `coverage_dev_tools.json` from pytest/coverage, located in `development_tools/tests/jsons/`) may not follow this standard.

---

## 7. Output Storage Standards

Status reports use `create_output_file()`; analysis results and caches use domain-specific directories. Path resolution: use `project_root` from config, never hardcode. See section 7 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) for file types, naming, and path rules.

---

## 8. Exclusion Rules

File-level exclusions: `shared/standard_exclusions.py` and `should_exclude_file()`. Universal exclusions include `.ruff_cache`, `mhm.egg-info`, `scripts`, `tests/ai/results`, `tests/coverage_html`, `tests/data/`. Context-specific exclusions (production/development/testing) and config override via `development_tools_config.json`.

**Import boundary (Section 8.5 in paired guide)**: Only `core.logger` is approved inside `development_tools/**`. Use `shared/time_helpers`, `shared/error_helpers`, and dynamic `importlib` for backup manager instead of other `core.*` imports. Checker: `analyze_dev_tools_import_boundaries` (Tier 1). Policy tests: `tests/development_tools/test_import_boundary_policy.py`.

See section 8 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) for full rules, function-level exclusions, and import-boundary detail.

---

## 9. Directory taxonomy and configuration surface (Phase 1)

- **Config surface**: Repo root `pyproject.toml` (`[tool.pyright]`, `[tool.bandit]`, ...); `development_tools/config/` - `development_tools/config/config.py`, `development_tools/config/development_tools_config.json` (+ `.example`), `development_tools/config/sync_ruff_toml.py`, owned `development_tools/config/ruff.toml` / `development_tools/config/pyrightconfig.json`.
- **Implementation**: `development_tools/shared/**` (service mixins, scanners, caches); generated JSON under `reports/jsons/`, `tests/jsons/`.
- **Phase 2**: Gate is recorded in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) Section 7.7. Use shims only per [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md); see Section 9 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md).
- **Dual Pyright**: root `pyproject.toml` **`[tool.pyright]`** (IDE/whole repo) vs `development_tools/config/pyrightconfig.json` (alternate `--project` for audits/parity). Default `analyze_pyright` uses **`pyproject.toml`**. **Ruff**: owned `development_tools/config/ruff.toml`; root `.ruff.toml` mirror. Policy tests: `pytest tests/development_tools/test_pyright_config_paths.py`. Optional parity gate: set environment variable `PYRIGHT_ERROR_COUNT_MAX_DELTA` to a non-negative integer when running the e2e Pyright test so owned vs root `errorCount` may differ only within that bound (unset = advisory comparison only).
- **Portability (V5 Section 7.6)**: Structural checks today (valid configs, shared `tests/data` exclusions). Full diagnostic parity between root and owned Pyright remains goal-oriented; use `PYRIGHT_ERROR_COUNT_MAX_DELTA` for incremental tightening. Optional `pytest -m e2e` smoke in [`tests/development_tools/test_pyright_config_paths.py`](../tests/development_tools/test_pyright_config_paths.py).
- **Human detail**: Section 9 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md).

---

## 10. External tools evaluation (Bandit, pip-audit, Radon, pre-commit)

**Bandit** and **pip-audit** run in **Tier 3** full audits (`audit --full`) via `analyze_bandit` / `analyze_pip_audit`; they are in root `requirements.txt`. **`MHM_PIP_AUDIT_SKIP`** (truthy) skips pip-audit network use in [`development_tools/static_checks/analyze_pip_audit.py`](static_checks/analyze_pip_audit.py) (CI/offline; see [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) Section 10). **Radon** / **pydeps** / **vulture** remain manual pilots. Full detail and manual one-off commands: Section 10 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md). **Scripts backlog**: [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md). **Do not add** unapproved standalone migration markdown files; use approved guides + V5.

**TODO sync**: `python development_tools/docs/fix_version_sync.py sync-todo --dry-run` prints the dry-run summary to stdout (no file edits). **`sync-todo --apply`** removes auto-cleanable completed checklist lines (`- [x]` / `- [X]` only); do not combine `--apply` with `--dry-run`.

**Example markers (advisory, V5 Section 3.0)**: Tiered `audit` and `doc-sync` run `analyze_documentation_sync` with `--check-example-markers` over paths in **`DEFAULT_DOCS`** ([`shared/constants.py`](shared/constants.py), merged from `development_tools_config.json` via `get_constants_config()`). Hints are stored in doc-sync JSON and surfaced in **AI_STATUS** (summary), **CONSOLIDATED_REPORT**, and **AI_PRIORITIES** (Tier 4 when count > 0). Heuristics and exclusions: Section 10 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md). Standalone: `python development_tools/docs/analyze_documentation_sync.py --json --check-example-markers`.

**Evaluation note (2026-04-10)**: **radon** remains an optional one-off install for CC sampling. **pre-commit** remains optional on developer machines only; audit truth stays `run_development_tools.py` + `tests/development_tools/`.

**Manual pilot (venv active)** - optional extras beyond the integrated wrappers:

- `python -m pip install radon` (optional CC sampling).
- `python -m bandit -c pyproject.toml -r core communication ui user ai tasks -ll` - ad-hoc path experiments; audit uses `development_tools/static_checks/analyze_bandit.py` with `[tool.bandit]` excludes.
- `python -m pip_audit` - ad-hoc; audit uses `development_tools/static_checks/analyze_pip_audit.py` (requirements-hash cache).
- `python -m radon cc development_tools -a -s` - advisory complexity sample; overlaps internal analyzers-cross-check only until Tier policy exists.

### 10.1. Gap-analysis alignment (V5 Section 5.5)

Tier 2 **`module-refactor-candidates`** is the in-repo "large module / complexity" gap signal; pair it with `AI_PRIORITIES.md` and `analyze_module_refactor_candidates_results.json` when triaging Documentation / Code quality / Testing themes. Full detail: Section 10.1 in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md).
