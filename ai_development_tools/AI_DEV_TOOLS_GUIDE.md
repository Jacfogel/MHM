# AI Development Tools Guide

> **File**: `ai_development_tools/AI_DEV_TOOLS_GUIDE.md`
> **Audience**: AI collaborators and automated tooling  
> **Purpose**: Routing and constraints for all AI development tools used to analyze, audit, and maintain the MHM codebase  
> **Style**: Minimal, reference-only (no deep explanations)

This guide provides a precise and verified map of every AI development tool in the project.  
It describes **what tools exist**, **when they should be used**, **what they output**, and **where to find their definitive behavior**.

For detailed standards and explanations, use:
- `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
- `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- Human-detailed paired documentation in `development_docs/`

---

## Quick Reference

```powershell
python ai_development_tools/ai_tools_runner.py <command>
python ai_development_tools/ai_tools_runner.py help
```

**Most common commands:**
- `audit` — run the full analysis suite (fast mode)
- `audit --full` — run tests, coverage, unused imports, all heavy tooling
- `status` — quick system snapshot (cached data + light checks)
- `docs` — regenerate registries, dependency maps, doc signals
- `doc-sync` — verify human/AI doc consistency & H2 alignment
- `legacy` — run legacy reference scanner + report
- `coverage` — regenerate coverage metrics and HTML reports
- `unused-imports` — run AST-based unused import analysis
- `config` — inspect active configuration and contexts

---

## 1. Main Entry Point — `ai_tools_runner.py`

Central dispatcher for all AI tooling commands.

All tools must:
- Respect shared configuration from `config.py`.  
- Respect universal exclusions from `standard_exclusions.py`.  
- Avoid importing MHM business-logic modules directly.  
- Operate strictly on filesystem + configuration.

---

## 2. Fast Mode vs Full Mode Audits

### Fast Mode — `audit`
Lightweight, cached signals:
- Documentation structure  
- Legacy references  
- Basic AI validation  
- System signals  
- Quick metrics  

### Full Mode — `audit --full`
Heavy operations:
- Full pytest + coverage regeneration  
- Unused import detection  
- Dependency regeneration  
- HTML coverage reports  

---

## 3. Generated Outputs

AI-facing:
- `AI_STATUS.md`
- `AI_PRIORITIES.md`
- `consolidated_report.md`
- `ai_audit_detailed_results.json`

Human-facing:
- `FUNCTION_REGISTRY_DETAIL.md`
- `MODULE_DEPENDENCIES_DETAIL.md`
- `LEGACY_REFERENCE_REPORT.md`
- `UNUSED_IMPORTS_REPORT.md`

Coverage:
- `coverage.json`  
- HTML reports under `coverage_html/`  
- Archived reports under `archive/coverage_artifacts/<timestamp>/`

---

## 4. Tools Summary (with Tier/Portability)

Every tool module must declare:

```
# TOOL_TIER: core | supporting | experimental
# TOOL_PORTABILITY: portable | mhm-specific
```

### Documentation & Structure
- documentation_sync_checker.py  
- generate_function_registry.py  
- generate_module_dependencies.py  
- analyze_documentation.py  

### Quality, Validation, Coverage
- regenerate_coverage_metrics.py  
- validate_ai_work.py  
- unused_imports_checker.py  
- error_handling_coverage.py  

### Legacy, Versioning, Signals
- legacy_reference_cleanup.py  
- system_signals.py  
- quick_status.py  
- version_sync.py (experimental)  

### Decision & Utilities
- decision_support.py  
- function_discovery.py  
- auto_document_functions.py (experimental)  
- config_validator.py  
- file_rotation.py  
- audit_function_registry.py  
- audit_module_dependencies.py  
- audit_package_exports.py  
- tool_guide.py  

---

## 5. Standard Exclusions System

All tools must use:
- `standard_exclusions.py`
- `constants.py`
- `config.py`

No tool may define custom exclusion logic.

---

## 6. Status Command & Cached Data

`status` provides fast health summaries:
- doc signals  
- legacy presence  
- error-handling depth  
- complexity hotspots  
- system signals  
- validation flags  

Must rerun `audit` if stale.

---

## 7. Configuration & Context

Contexts:
- production  
- development  
- testing  

Tools must:
- Read project structure from config/constants  
- Never hardcode MHM paths  
- Never import MHM business logic  

---

## 8. File Organization

Recommended structure for long-term portability:

```
ai_development_tools/
ai_development_docs/
development_docs/
tests/app/
tests/ai_tools/
tests/fixtures/ai_tools_demo/
archive/
logs/
```

This grouping enables eventual extraction of the tool suite.

---

## 9. Quick Start

```powershell
python ai_development_tools/ai_tools_runner.py audit
python ai_development_tools/ai_tools_runner.py audit --full
python ai_development_tools/ai_tools_runner.py docs
python ai_development_tools/ai_tools_runner.py status
```

---

## 10. Maintenance and Ongoing Use

- Treat tools as a self-contained subproject.  
- Keep MHM-specific assumptions centralized in:
  - `config.py`
  - `constants.py`
  - documentation guides  
- Tests for tools go in:
  - `tests/ai_tools/`
  - with synthetic fixtures under `tests/fixtures/ai_tools_demo/`  
- Avoid coupling tools to MHM internals.  
- Audit regularly; use full audits before major changes.  
- Handle experimental tools with caution (dry-run first).  

These practices keep tools reliable today while preserving future separability.
