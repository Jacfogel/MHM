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
- The authoritative human-readable catalog of tools, tiers, and portability
- Rationale behind trust levels and roadmap priorities
- Links to supporting plans such as [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md)

The machine-readable metadata lives in `development_tools/services/tool_metadata.py` and is surfaced to AI collaborators through the paired guide.

---

## 2. Running the Tool Suite

All commands flow through `development_tools/ai_tools_runner.py`.

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

### 2.1. Command summary

- `audit` - fast mode; regenerates lightweight reports and cached signals.
- `audit --full` - long-running; adds pytest coverage, unused imports, dependency regeneration, HTML reports.
- `status` - surfaces cached health summaries (rerun `audit` if stale).
- `docs` - regenerates registries, dependency maps, and doc-signals.
- `doc-sync` - verifies paired doc headings, path drift, ASCII compliance.
- `legacy` - runs `legacy_reference_cleanup.py` via the dispatcher.
- `coverage` - invokes `regenerate_coverage_metrics.py` (HTML + JSON outputs).
- `unused-imports` - runs the AST-based unused import detector.
- `config` - prints active configuration contexts and validation warnings.

### 2.2. Entry point expectations

Regardless of command:
- Respect shared configuration from `config.py`.
- Honor universal exclusions defined in `services/standard_exclusions.py`.
- Avoid importing business logic modules (operate via filesystem + configs only).
- Route logging through the `development_tools` component logger.
- Emit ASCII output to stay Windows-safe.

---

## 3. Audit Modes and Outputs

**Fast mode (`audit`)** collects:
- Documentation drift metrics
- Legacy reference summaries
- Validation snapshots and quick system signals

**Full mode (`audit --full`)** adds:
- Full pytest execution with coverage regeneration
- Unused import detection
- Registry and dependency regeneration
- Coverage HTML/JSON refresh plus archival

Pipeline artifacts:
- AI-facing: [AI_STATUS.md](development_tools/AI_STATUS.md), `AI_PRIORITIES.md`, `consolidated_report.txt`, `ai_audit_detailed_results.json`
- Human-facing: [FUNCTION_REGISTRY_DETAIL.md](development_docs/FUNCTION_REGISTRY_DETAIL.md), [MODULE_DEPENDENCIES_DETAIL.md](development_docs/MODULE_DEPENDENCIES_DETAIL.md), [LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md), [UNUSED_IMPORTS_REPORT.md](development_docs/UNUSED_IMPORTS_REPORT.md)
- Coverage: `coverage.json`, `development_tools/coverage_html/`, `development_tools/archive/coverage_artifacts/<timestamp>/`
- Cached snapshots: `status` depends on the latest successful `audit`; confirm timestamps before trusting.

Ensure directories listed in `development_tools/services/constants.py` remain accurate so reports resolve predictably.

---

## 4. Tool Catalog and Tiering

### 4.1. Tier overview

| Tier | Trust Level | Description |
| --- | --- | --- |
| Core | stable | Safe for daily runs; required for audit-first workflow. |
| Supporting | partial / advisory | Helpful but dependent on fresh audit data; verify results manually. |
| Experimental | experimental | Prototype/high-risk commands; run only with explicit approval and backups. |

### 4.2. Detailed catalog

| Tool | Tier | Trust | Portability | Notes |
| --- | --- | --- | --- | --- |
| ai_tools_runner.py | core | stable | mhm-specific | CLI dispatcher for every AI tooling command. |
| services/operations.py | core | stable | mhm-specific | Implements command handlers and shared execution paths. |
| config.py | core | stable | mhm-specific | Central configuration for audit contexts, paths, and workflow knobs. |
| services/standard_exclusions.py | core | stable | mhm-specific | Canonical exclusion patterns consumed by all scanners. |
| services/constants.py | core | stable | mhm-specific | Doc pairing metadata, directory maps, and shared enumerations. |
| services/common.py | core | stable | portable | IO helpers plus CLI utilities (command grouping, runners). |
| documentation_sync_checker.py | core | stable | mhm-specific | Validates doc pairing (human vs AI) and detects drift. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_documentation_sync_checker.py` |
| generate_function_registry.py | core | stable | mhm-specific | Builds the authoritative function registry via AST parsing. [OK] **HAS TESTS (Phase 3)**: 12 tests in `tests/development_tools/test_generate_function_registry.py` |
| generate_module_dependencies.py | core | stable | mhm-specific | Produces module dependency graphs and enhancement zones. [OK] **HAS TESTS (Phase 3)**: 11 tests in `tests/development_tools/test_generate_module_dependencies.py` |
| legacy_reference_cleanup.py | core | stable | mhm-specific | Finds/validates LEGACY COMPATIBILITY usage before cleanup. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_legacy_reference_cleanup.py` |
| regenerate_coverage_metrics.py | core | stable | mhm-specific | Rebuilds coverage artifacts, JSON, and HTML reports. [OK] **HAS TESTS (Phase 3)**: 10 tests in `tests/development_tools/test_regenerate_coverage_metrics.py` |
| error_handling_coverage.py | core | stable | mhm-specific | Audits decorator usage and exception handling depth. |
| function_discovery.py | core | stable | mhm-specific | AST discovery utility supporting registries and audits. |
| analyze_documentation.py | supporting | partial | mhm-specific | Secondary doc analysis that focuses on corruption/overlap. |
| audit_function_registry.py | supporting | partial | mhm-specific | Validates generated function registry output. |
| audit_module_dependencies.py | supporting | partial | mhm-specific | Cross-checks generated dependency graphs for accuracy. |
| audit_package_exports.py | supporting | partial | mhm-specific | Confirms package export declarations match filesystem reality. |
| config_validator.py | supporting | partial | mhm-specific | Detects configuration drift and missing values across tools. |
| validate_ai_work.py | supporting | partial | mhm-specific | Lightweight structural validator; advisory results only. |
| unused_imports_checker.py | supporting | partial | mhm-specific | AST-based unused import detector (tune noise thresholds). |
| quick_status.py | supporting | advisory | mhm-specific | Cached status snapshot that depends on the latest audit run. |
| system_signals.py | supporting | advisory | portable | Collects OS/process health signals for consolidated reports. |
| decision_support.py | supporting | advisory | mhm-specific | Aggregates metrics into improvement priorities. |
| file_rotation.py | supporting | stable | portable | Timestamped rotation utility used by coverage generation. |
| tool_guide.py | supporting | stable | mhm-specific | Provides contextual guidance and tier overviews for assistants. |
| version_sync.py | experimental | experimental | mhm-specific | Attempts cross-file version synchronization (fragile). |
| auto_document_functions.py | experimental | experimental | mhm-specific | Auto-generates docstrings; high-risk and currently prototype. |

Keep this table synchronized with `services/tool_metadata.py` and update both when tiers, trust levels, or portability change.

---

## 5. Operating Standards and Maintenance

- Follow the audit-first workflow (see [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)) before touching documentation or infrastructure
- When adding or relocating tools, update:
  - `services/tool_metadata.py`
  - This guide and the AI guide (paired H2 requirements)
  - [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md) if scope or gaps change
- Maintain directory integrity (`development_tools/`, `ai_development_docs/`, `development_docs/`, `archive/`, `logs/`) so automation can locate artifacts; keep generated reports under the paths enumerated in `services/constants.py`.
- Use the shared test locations: `tests/development_tools/` for suites and `tests/fixtures/development_tools_demo/` for synthetic inputs.
- **Phase 3 Complete (2025-11-26)**: All five core analysis tools have comprehensive test coverage (55+ tests total). The synthetic fixture project provides isolated testing environment for all tool tests.
- Context-specific behavior:
  - `config.py` defines production / development / testing contexts; commands must honor the active context.
  - Never hardcode project paths - always resolve via `services/common.py` helpers.
- Run `python development_tools/ai_tools_runner.py doc-sync` after documentation edits to ensure heading parity and ASCII compliance.
- Treat experimental tools (`version_sync.py`, `auto_document_functions.py`, etc.) as opt-in: dry-run first, capture logs, and record findings in [TODO.md](TODO.md) or the improvement plan.
- Keep file organization portable (mirroring `development_tools/`, `ai_development_docs/`, `development_docs/`, `archive/`, `logs/`) to support eventual extraction of the suite. The baseline structure should remain:

```
development_tools/
ai_development_docs/
development_docs/
tests/development_tools/
tests/fixtures/development_tools_demo/
archive/
logs/
```

- Do not implement bespoke exclusion logic inside individual tools - always import from `services/standard_exclusions.py` so rules remain centralized.
- Treat the tooling as a self-contained subproject: track follow-up work in [AI_DEV_TOOLS_IMPROVEMENT_PLAN.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md), document shipped changes in both changelogs, and keep the AI + human guides synchronized.

Keeping these standards ensures the tooling ecosystem remains predictable for both humans and AI collaborators.

