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
- Links to supporting plans such as [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md)

The machine-readable metadata lives in `development_tools/shared/tool_metadata.py` and is surfaced to AI collaborators through the paired guide.

---

## 2. Running the Tool Suite

All commands flow through `development_tools/ai_tools_runner.py`.

### 2.1. Global Options

The runner supports global options that apply to all commands:

```powershell
# Specify a custom project root
python development_tools/ai_tools_runner.py --project-root /path/to/project status

# Specify a custom config file
python development_tools/ai_tools_runner.py --config-path /path/to/config.json audit

# Combine both
python development_tools/ai_tools_runner.py --project-root . --config-path development_tools_config.json status
```

**Configuration File**: By default, the tools look for `development_tools_config.json` in the project root. This file can override paths, project settings, audit behavior, and other configuration. See `development_tools/development_tools_config.json.example` for a template.

### 2.2. Command Examples

```powershell
python development_tools/ai_tools_runner.py --help
python development_tools/ai_tools_runner.py audit
python development_tools/ai_tools_runner.py audit --full
python development_tools/ai_tools_runner.py docs
python development_tools/ai_tools_runner.py status
python development_tools/ai_tools_runner.py legacy
python development_tools/ai_tools_runner.py coverage
python development_tools/ai_tools_runner.py unused-imports
python development_tools/ai_tools_runner.py config
```

### 2.3. Command Summary

**Core Commands** (daily-safe, audit-first workflow):
- `audit` - fast mode; regenerates lightweight reports and cached signals.
- `audit --full` - long-running; adds pytest coverage, unused imports, dependency regeneration, HTML reports.
- `quick-audit` - comprehensive audit without extras (alternative to `audit`).
- `docs` - regenerates registries, dependency maps, and doc-signals.
- `doc-sync` - verifies paired doc headings, path drift, ASCII compliance.
- `config` - prints active configuration contexts and validation warnings.
- `coverage` - invokes `regenerate_coverage_metrics.py` (HTML + JSON outputs).
- `legacy` - runs `legacy_reference_cleanup.py` via the dispatcher.

**Supporting Commands** (advisory, depend on fresh audits):
- `status` - surfaces cached health summaries (rerun `audit` if stale).
- `system-signals` - generates system health and status signals.
- `validate` - validates AI-generated work.
- `decision-support` - generates decision support insights.
- `unused-imports` - runs the AST-based unused import detector.
- `workflow` - executes an audit-first workflow task.
- `trees` - generates directory tree reports.
- `help` - shows detailed help information.

**Experimental Commands** (high-risk, run only with approval):
- `version-sync` - synchronizes version metadata across files (fragile, use with caution).

### 2.4. Entry Point Expectations

Regardless of command:
- Respect shared configuration from `config.py` (with external config file support via `development_tools_config.json`).
- Honor universal exclusions defined in `shared/standard_exclusions.py`.
- Avoid importing business logic modules (operate via filesystem + configs only).
- Route logging through the `development_tools` component logger.
- Emit ASCII output to stay Windows-safe.

**Configuration Priority**:
1. External config file (`development_tools_config.json` in project root, or path specified via `--config-path`)
2. Hardcoded defaults in `config.py` (generic/empty fallbacks for portability)
3. Environment-specific detection (project root, scan directories, etc.)

**Portability**: All tools are portable and can be used in other projects. Create a `development_tools_config.json` file in your project root (see `development_tools/development_tools_config.json.example` for a template) to customize paths, exclusions, constants, and other project-specific settings.

---

## 3. Audit Modes and Outputs

**Fast mode (`audit`)** collects:
- Documentation drift metrics
- Legacy reference summaries
- Complexity metrics (function complexity distribution: moderate/high/critical counts)
- Validation snapshots and quick system signals

**Full mode (`audit --full`)** adds:
- Full pytest execution with coverage regeneration
- Unused import detection
- Registry and dependency regeneration
- Coverage HTML/JSON refresh plus archival
- All fast mode data plus comprehensive coverage analysis

Pipeline artifacts:
- AI-facing (root): [AI_STATUS.md](development_tools/AI_STATUS.md), `AI_PRIORITIES.md`, `consolidated_report.txt`
- Domain-specific JSON: `reports/ai_audit_detailed_results.json`, `error_handling/error_handling_details.json`, `tests/coverage_dev_tools.json`, `validation/config_validation_results.json`, `imports/.unused_imports_cache.json`
  - `reports/ai_audit_detailed_results.json` caches complexity metrics, validation results, and system signals for `status` command
  - `AI_PRIORITIES.md` includes complexity refactoring priority when critical/high complexity functions exist
- Human-facing: [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md), [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md), [LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md), [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)
- Coverage: `coverage.json` (project root), `tests/coverage_html/` (project root), `development_tools/reports/archive/coverage_artifacts/<timestamp>/`
- Cached snapshots: `status` loads data from `reports/ai_audit_detailed_results.json` (complexity, validation, system signals); confirm timestamps before trusting.

**When to run each command**: See "Standard Audit Recipe" section in [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for guidance on day-to-day checks (`audit`), pre-merge/pre-release checks (`audit --full`), and documentation work (`doc-sync`, `docs`).

Ensure directories listed in `development_tools/shared/constants.py` remain accurate so reports resolve predictably.

---

## 4. Tool Catalog and Tiering

### 4.1. Tier overview

| Tier | Trust Level | Description |
| --- | --- | --- |
| Core | stable | Safe for daily runs; required for audit-first workflow. |
| Supporting | partial / advisory | Helpful but dependent on fresh audit data; verify results manually. |
| Experimental | experimental | Prototype/high-risk commands; run only with explicit approval and backups. |

### 4.2. Detailed catalog

| Tool | Tier | Trust | Notes |
| --- | --- | --- | --- |
| ai_tools_runner.py | core | stable | CLI dispatcher for every AI tooling command. Supports `--project-root` and `--config-path` for portability. |
| shared/operations.py | core | stable | Implements command handlers and shared execution paths. Accepts project-specific config via external config file. |
| config.py | core | stable | Central configuration for audit contexts, paths, and workflow knobs. Loads from `development_tools_config.json` with generic fallbacks. |
| shared/standard_exclusions.py | core | stable | Canonical exclusion patterns consumed by all scanners. Loads exclusions from external config. |
| shared/constants.py | core | stable | Doc pairing metadata, directory maps, and shared enumerations. Loads constants from external config. |
| shared/common.py | core | stable | IO helpers plus CLI utilities (command grouping, runners). |
| documentation_sync_checker.py | core | stable | Validates doc pairing (human vs AI) and detects drift. Parameterized doc roots and metadata schema. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_documentation_sync_checker.py` |
| generate_function_registry.py | core | stable | Builds the authoritative function registry via AST parsing. Configurable scan roots and filters via external config. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_generate_function_registry.py` |
| generate_module_dependencies.py | core | stable | Produces module dependency graphs and enhancement zones. Accepts custom module prefixes for portability. [OK] **HAS TESTS (Phase 3)**: 11 tests in `tests/development_tools/test_generate_module_dependencies.py` |
| legacy_reference_cleanup.py | core | stable | Finds/validates LEGACY COMPATIBILITY usage before cleanup. Legacy patterns and mappings load from external config. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_legacy_reference_cleanup.py` |
| regenerate_coverage_metrics.py | core | stable | Rebuilds coverage artifacts, JSON, and HTML reports. Accepts pytest command, coverage config, and artifact directories via external config. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_regenerate_coverage_metrics.py` |
| error_handling_coverage.py | core | stable | Audits decorator usage and exception handling depth. Decorator names and exception classes load from external config. |
| function_discovery.py | core | stable | AST discovery utility supporting registries and audits. Configurable scan roots and filters via external config. |
| analyze_documentation.py | supporting | partial | Secondary doc analysis that focuses on corruption/overlap. |
| audit_function_registry.py | supporting | partial | Validates generated function registry output. |
| audit_module_dependencies.py | supporting | partial | Cross-checks generated dependency graphs for accuracy. |
| audit_package_exports.py | supporting | partial | Confirms package export declarations match filesystem reality. |
| config_validator.py | supporting | partial | Detects configuration drift and missing values across tools. |
| validate_ai_work.py | supporting | partial | Lightweight structural validator; advisory results only. |
| unused_imports_checker.py | supporting | partial | AST-based unused import detector (tune noise thresholds). |
| quick_status.py | supporting | advisory | Cached status snapshot that depends on the latest audit run. |
| system_signals.py | supporting | advisory | Collects OS/process health signals for consolidated reports. |
| decision_support.py | supporting | advisory | Aggregates metrics into improvement priorities. |
| shared/file_rotation.py | supporting | stable | Timestamped rotation utility used by coverage generation. |
| shared/tool_guide.py | supporting | stable | Provides contextual guidance and tier overviews for assistants. |
| docs/version_sync.py | experimental | experimental | Attempts cross-file version synchronization (fragile). |
| functions/auto_document_functions.py | experimental | experimental | Auto-generates docstrings; high-risk and currently prototype. |

Keep this table synchronized with `shared/tool_metadata.py` and update both when tiers or trust levels change.

---

## 5. Operating Standards and Maintenance

- Follow the audit-first workflow (see [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)) before touching documentation or infrastructure
- When adding or relocating tools, update:
  - `shared/tool_metadata.py`
  - This guide and the AI guide (paired H2 requirements)
  - [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md) if scope or gaps change
- Maintain directory integrity (`development_tools/`, `ai_development_docs/`, `development_docs/`, `development_tools/reports/archive/`, `development_tools/tests/logs/`) so automation can locate artifacts; keep generated reports under the paths enumerated in `shared/constants.py`.
- Use the shared test locations: `tests/development_tools/` for suites and `tests/fixtures/development_tools_demo/` for synthetic inputs.
- **Phase 3 Complete (2025-11-26)**: All five core analysis tools have comprehensive test coverage (55+ tests total). The synthetic fixture project provides isolated testing environment for all tool tests.
- Context-specific behavior:
  - `config.py` defines production / development / testing contexts; commands must honor the active context.
  - Never hardcode project paths - always resolve via `shared/common.py` helpers.
- Run `python development_tools/ai_tools_runner.py doc-sync` after documentation edits to ensure heading parity and ASCII compliance.
- Treat experimental tools (`docs/version_sync.py`, `functions/auto_document_functions.py`, etc.) as opt-in: dry-run first, capture logs, and record findings in [TODO.md](TODO.md) or the improvement plan.
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
- Treat the tooling as a self-contained subproject: track follow-up work in [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md), document shipped changes in both changelogs, and keep the AI + human guides synchronized.

Keeping these standards ensures the tooling ecosystem remains predictable for both humans and AI collaborators.

