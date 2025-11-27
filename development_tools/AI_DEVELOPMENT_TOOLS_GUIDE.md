# AI Development Tools Guide

> **File**: `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`  
> **Audience**: AI collaborators and automated tooling  
> **Purpose**: Routing and constraints for all AI development tools used to analyze, audit, and maintain the MHM codebase  
> **Style**: Minimal, reference-only (no deep explanations)  
> **Pair**: `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`  
> This document is paired with `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`. Keep both H2 headings identical and consider changes in the context of the human counterpart.

---

## 1. Purpose and Scope

This guide provides a precise, machine-friendly map of the AI development tools:
- Summarizes **what commands exist** and **when to run them**
- Routes you to the authoritative metadata in `development_tools/services/tool_metadata.py`
- Delegates deeper explanations to the human guide and the AI workflow/docs references:
  - `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`
  - `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
  - `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`

Treat this file as the routing layer for AI collaborators; avoid duplicating human-facing narrative here.

---

## 2. Running the Tool Suite

```powershell
python development_tools/ai_tools_runner.py <command>
python development_tools/ai_tools_runner.py help
```

Most commonly used commands:
- `audit` / `audit --full`
- `status`
- `docs`
- `doc-sync`
- `legacy`
- `coverage`
- `unused-imports`
- `config`

`ai_tools_runner.py` is the single dispatcher. All commands must:
- Respect shared configuration (`config.py`)
- Honor `services/standard_exclusions.py`
- Avoid importing application modules directly

---

## 3. Audit Modes and Outputs

### 3.1. Fast mode - `audit`
- Documentation and legacy signals
- Validation summaries and quick metrics
- System signals + cached data

### 3.2. Full mode - `audit --full`
- Full pytest + coverage regeneration
- Unused import detection
- Dependency + registry regeneration
- HTML coverage reports

Outputs land in predictable locations:
- AI-facing: `AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.txt`, `ai_audit_detailed_results.json`
- Human-facing: `development_docs/FUNCTION_REGISTRY_DETAIL.md`, `development_docs/MODULE_DEPENDENCIES_DETAIL.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`, `development_docs/UNUSED_IMPORTS_REPORT.md`
- Coverage artifacts: `coverage.json`, `coverage_html/`, `archive/coverage_artifacts/<timestamp>/`
- Dev tools coverage (audit --full): `development_tools/coverage_dev_tools.json`, `development_tools/coverage_html_dev_tools/`

The `status` command surfaces cached summaries; rerun `audit` if the cache is stale.

---

## 4. Tool Catalog and Tiering

Each module declares:

```
# TOOL_TIER: core | supporting | experimental
# TOOL_PORTABILITY: portable | mhm-specific
```

The authoritative table lives in `services/tool_metadata.py`. Use this guide to pick the right group quickly:

- **Documentation & structure**: `documentation_sync_checker.py` [OK], `generate_function_registry.py` [OK], `generate_module_dependencies.py` [OK], `analyze_documentation.py`

[OK] = Has comprehensive test coverage (Phase 3)
- **Quality, validation, coverage**: `regenerate_coverage_metrics.py` [OK], `validate_ai_work.py`, `unused_imports_checker.py`, `error_handling_coverage.py`
- **Legacy, versioning, signals**: `legacy_reference_cleanup.py` [OK], `system_signals.py`, `quick_status.py`, `experimental/version_sync.py` (experimental)

[OK] = Has comprehensive test coverage (Phase 3)
- **Decision & utilities**: `decision_support.py`, `function_discovery.py`, `experimental/auto_document_functions.py` (experimental), `config_validator.py`, `file_rotation.py`, `audit_*` helpers, `tool_guide.py`

Consult `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` for the detailed tier, trust, and portability matrix.

---

## 5. Operating Standards and Maintenance

- Use shared infrastructure: `standard_exclusions.py`, `development_tools/services/constants.py`, `config.py`
- Never hardcode project paths; derive them from configuration helpers
- Keep tools isolated from MHM business logic
- Store tests under `tests/development_tools/` (with fixtures in `tests/fixtures/development_tools_demo/`)
- **Phase 3 Complete (2025-11-26)**: Core analysis tools now have comprehensive test coverage (55+ tests) using the synthetic fixture project
- **Phase 4 Follow-up (2025-11-27)**: Supporting tools `quick_status.py`, `system_signals.py`, and `file_rotation.py` now have targeted regression tests in `tests/development_tools/test_supporting_tools.py`
- Preserve the directory structure (`development_tools/`, `ai_development_docs/`, `development_docs/`, `archive/`, `logs/`) to ease eventual extraction
- Treat experimental tools cautiously (dry-run first, log outcomes)
- Keep this guide paired with the human document; update both whenever commands, tiers, or workflows change
