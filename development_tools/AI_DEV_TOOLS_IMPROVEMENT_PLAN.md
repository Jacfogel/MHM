# AI Development Tools – Current State and Improvement Roadmap

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md`
> **Audience**: Project maintainers and developers
> **Purpose**: Provide a detailed assessment of all AI development tools, identifying strengths, weaknesses, fragility, gaps, and a roadmap for improvement.
> **Style**: Direct, technical, and candid.

This document summarizes the current state of the `development_tools` suite based on source review.  
It is intended to guide decisions on tool maintenance, triage, and future enhancements.

---

# 1. Overall State of the AI Development Tools

The `development_tools` directory represents an ambitious and generally well‑structured attempt at creating an internal “analysis and audit platform” for the MHM project. The architecture includes:

- A unified dispatcher (`ai_tools_runner.py`)
- Configurable behavior (`config.py`)
- Centralized exclusions (`standard_exclusions.py`)
- Documentation-aware analysis tools
- Code-aware discovery, dependency analysis, and coverage generation
- Legacy cleanup tooling
- Higher-level decision support utilities

**Strengths:**

- The architecture is sound; the right abstractions exist.
- Tools share configuration and exclusion logic consistently.
- The audit pipeline is conceptually coherent.
- Many tools already have well-defined scopes.

**Weaknesses:**

- Quality is inconsistent across tools.
- Some tools are incomplete or experimental.
- There are no tests for the tools themselves.
- Write operations are high‑risk without strong safeguards.
- ~~No formal "tiering"~~ **RESOLVED (2025-11-25)**: Tiering system implemented via `services/tool_metadata.py` with tier markers in all tool modules and CLI help grouping.

**Summary:**  
Good bones, uneven execution. High potential, but needs consolidation, testing, and prioritization.

---

# 2. Per-Tool Breakdown

This section categorizes each tool into “Core,” “Supporting,” or “Experimental” based on reliability, purpose, and completeness.

---

## 2.1 Core Infrastructure (Strong, Foundational)

### `config.py`
- Centralizes scan roots, thresholds, audit modes.
- Widely used across tools.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 23 tests in `tests/development_tools/test_config.py` verify key settings and helper functions.

### `standard_exclusions.py`
- Good design: all tools call `should_exclude_file`.
- Patterns may need tuning but concept is sound.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 21 tests in `tests/development_tools/test_standard_exclusions.py` verify exclusion patterns work correctly.

### `constants.py`
- Holds doc pairing metadata and predefined doc lists.
- Needs regular updates to avoid drift.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 25 tests in `tests/development_tools/test_constants.py` verify paths exist and helper functions work correctly.

### `common.py`
- Provides consistent CLI patterns and file operations.
- Some tools bypass it; future tools should not.

### `services/tool_metadata.py` **NEW (2025-11-25)**
- Single source of truth for tool tier, portability, trust level, description, and command metadata.
- Drives CLI help grouping and documentation generation.
- All tools reference this registry for authoritative classification.
- Eliminates duplication and ensures consistency across CLI, docs, and code.

**Overall:** These modules form a reliable backbone and should be maintained carefully. The addition of `tool_metadata.py` provides the foundation for explicit tiering and consistent tool classification.

---

## 2.2 Runner and Operations Layer

### `ai_tools_runner.py`
- Central dispatcher with command registry.
- Good entry point; ties the system together.
- ✅ **HAS CLI SMOKE TESTS (Phase 2)**: 7 tests in `tests/development_tools/test_ai_tools_runner.py` verify command execution and exit codes.
- ✅ **HAS ENHANCED ERROR HANDLING (Phase 2)**: Try/except blocks with proper logging and exit code propagation.

### `operations.py`
- Implements core logic for each command.
- Has risk of becoming a "god module."
- Should eventually be split by domain (audit, docs, legacy, coverage).
- ✅ **HAS NORMALIZED LOGGING (Phase 2)**: Consistent "Starting..." and "Completed..." logging added to all major operations.

**Overall:** Strong concept; risks long-term sprawl without structure.

---

## 2.3 Documentation & Structure Tools (High Value, Complex)

### `documentation_sync_checker.py`
- Validates human/AI doc pairing (H2 headings, metadata).
- Important for MHM’s strict documentation system.
- Some fragility around edge cases.

### `generate_function_registry.py`
- Extracts full project function registry.
- High complexity; AST-based scanning.
- Very valuable but fragile without tests.

### `generate_module_dependencies.py`
- Computes dependency graph across modules.
- Preserves manual enhancement blocks.
- Large and sophisticated; needs validation.

### `analyze_documentation.py`
- Detects incomplete or corrupted docs.
- Good complement to doc-sync; some overlap.

**Overall:** These tools are sophisticated and incredibly useful, but require hardening.

---

## 2.4 Quality, Coverage & Validation Tools (High Value, Uneven)

### `regenerate_coverage_metrics.py`
- Full coverage regeneration with HTML output.
- Handles artifact rotation and aggregation.
- High-risk without tests; complex flows.

### `validate_ai_work.py`
- Lightweight structural validator.
- Useful but incomplete; not authoritative.

### `unused_imports_checker.py`
- AST-based unused import detector.
- Potentially noisy; requires tuning.

### `error_handling_coverage.py`
- Analyzes exception patterns, decorator usage, custom errors.
- Strong concept that aligns with ERROR_HANDLING_GUIDE.
- Static analysis limitations exist.

**Overall:** Valuable tools, but accuracy varies; should be validated individually.

---

## 2.5 Legacy, Versioning, Signals (Mixed Quality)

### `legacy_reference_cleanup.py`
- Supports find/verify/scan/clean (with dry-run).
- Very useful but high-risk; must rely heavily on dry-run.

### `version_sync.py`
- Attempts to synchronize versioning across files.
- Often fragile; underdeveloped; easy to break.

### `system_signals.py`
- Minimal; hooks for OS/system health.
- Used lightly.

### `quick_status.py`
- Fast snapshot for AI tools.
- Only reliable if audits are fresh.

**Overall:** Legacy cleanup is core; version_sync should be considered experimental; signals + quick status are safe but shallow.

---

## 2.6 Decision Support & Misc Utilities (Variable Quality)

### `decision_support.py`
- Aggregates outputs into priorities and complexity insights.
- Advisory only; not deterministic.

### `function_discovery.py`
- Parses function signatures, handlers, tests.
- Forms basis for several other tools.

### `auto_document_functions.py`
- Generates docstrings automatically.
- High-risk; should be treated as experimental.

### `config_validator.py`
- Checks config usage across tools.
- Helps detect drift; incomplete but useful.

### `file_rotation.py`
- Simple timestamp-based rotation and “latest” pointer.
- Solid utility.

### `audit_function_registry.py`, `audit_module_dependencies.py`, `audit_package_exports.py`
- Validate the outputs of code-to-doc generators.
- High value when paired with solid registry/dependency generators.

### `tool_guide.py`
- Generates help text.
- Safe and stable.

**Overall:** Some gems here, some fragile experiments.

---

# 3. Cross-Cutting Issues Identified

### **1. ~~No clear tiering (core vs supporting vs experimental)~~** **RESOLVED (2025-11-25)**
- ✅ Tier markers added to all tool modules (`# TOOL_TIER` and `# TOOL_PORTABILITY` headers)
- ✅ `services/tool_metadata.py` created as single source of truth for tier, portability, trust, and command metadata
- ✅ CLI help output groups commands by tier (Core, Supporting, Experimental) with warnings
- ✅ Documentation guides updated with tier information and trust levels
- ✅ Directory renamed from `ai_development_tools/` to `development_tools/` for clarity

### **2. ~~No tests for tooling~~** **PARTIALLY RESOLVED (2025-11-25)**
- ✅ Basic sanity tests added for core infrastructure (`config.py`, `standard_exclusions.py`, `constants.py`)
- ✅ CLI smoke tests added for `ai_tools_runner.py`
- ✅ Logging and error handling normalized in `operations.py` and `ai_tools_runner.py`
- ⚠️ Tests for complex analysis tools (AST parsing, doc generation) still needed (Phase 3)

### **3. Risky write operations**
- Tools like legacy cleanup, auto-documentation, coverage regeneration write real files.
- Without strong safeguards, they can corrupt code or docs.

### **4. Conceptual overlap / sprawl**
- Documentation tools overlap; analysis tools overlap; validation tools overlap.
- The audit pipeline needs clearer boundaries and flow.

### **5. ~~No explicit indicator of experimental tools~~** **RESOLVED (2025-11-25)**
- ✅ All tools now carry tier markers in source code
- ✅ CLI help explicitly warns about experimental commands
- ✅ Documentation guides list trust levels and portability status for each tool
- ✅ Reference list of partial/advisory/experimental tools documented in guides

---

## 4. AI Development Tools – Implementation Roadmap

> **File**: `development_tools/AI_DEV_TOOLS_ROADMAP.md`
> **Audience**: Project maintainers and developers
> **Purpose**: Provide a practical, phased roadmap with milestones to stabilize, test, and rationalize the AI development tools.
> **Style**: Direct, technical, and concise.

This roadmap assumes the following tiering for the AI development tools:

- **Tier 1 – Core**
  - `ai_tools_runner.py`, `operations.py`, `config.py`, `standard_exclusions.py`, `constants.py`, `common.py`
  - `documentation_sync_checker.py`, `generate_function_registry.py`, `generate_module_dependencies.py`
  - `legacy_reference_cleanup.py`, `regenerate_coverage_metrics.py`
  - `error_handling_coverage.py`, `function_discovery.py`

- **Tier 2 – Supporting**
  - `analyze_documentation.py`, `audit_function_registry.py`, `audit_module_dependencies.py`, `audit_package_exports.py`
  - `config_validator.py`, `validate_ai_work.py`, `unused_imports_checker.py`, `quick_status.py`, `system_signals.py`
  - `decision_support.py`, `file_rotation.py`, `tool_guide.py`

- **Tier 3 – Experimental**
  - `version_sync.py`, `auto_document_functions.py`

---

### Phase 1 – Make the Landscape Explicit **COMPLETED (2025-11-25)**

**Goal:** Turn the informal understanding of "which tools matter" into explicit structure and expectations.

**Status:** All milestones completed. Tiering system fully implemented and integrated into CLI, documentation, and codebase.

#### Milestone M1.1 – Add Tier Markers **COMPLETED**

- ✅ Created `services/tool_metadata.py` as authoritative registry for all tool metadata (tier, portability, trust, description, command name)
- ✅ Added `# TOOL_TIER: core | supporting | experimental` headers to all tool modules
- ✅ Added `# TOOL_PORTABILITY: portable | mhm-specific` headers to all tool modules
- ✅ Removed BOM characters discovered during header injection sweep
- ✅ All 25+ tools now have consistent tier and portability markers

#### Milestone M1.2 – Reflect Tiering in Help Output **COMPLETED**

- ✅ Updated `services/common.py` to build command groupings from `tool_metadata.py` (single source of truth)
- ✅ Updated `ai_tools_runner.py` to display commands grouped by tier in help output
- ✅ Updated `services/operations.py` to use tier-based grouping for help display
- ✅ Enhanced `tool_guide.py` to print tier overview sourced from `tool_metadata.py`
- ✅ Help output now groups commands under **Core**, **Supporting**, and **Experimental** headings with explicit warnings

#### Milestone M1.3 – Document "Partial / Experimental" Tools **COMPLETED**

- ✅ Split documentation into paired guides:
  - `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` (AI-facing, routing-focused)
  - `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` (human-facing, detailed catalog)
- ✅ Both guides include complete tool catalog with tier, trust level, portability, and notes
- ✅ Explicitly flagged partial/incomplete tools (e.g. `validate_ai_work.py`)
- ✅ Explicitly flagged advisory-only tools (e.g. `decision_support.py`)
- ✅ Explicitly flagged experimental/fragile tools (e.g. `version_sync.py`, `auto_document_functions.py`)
- ✅ Aligned both guides with documentation standards (metadata blocks, identical H2 headings)
- ✅ Updated all path references from `ai_development_tools/` to `development_tools/` throughout codebase
- ✅ Added guides to `DEFAULT_DOCS`, `PAIRED_DOCS`, directory tree, README, and other doc listings

This does not fix code, but it stops you from accidentally trusting the wrong tool.

**Reference list for documentation and CLI alignment**

- Partial / advisory (Supporting tier):
  - `analyze_documentation.py` — overlap/corruption detection with known edge cases.
  - `audit_function_registry.py` — validates registry output but depends on fixture freshness.
  - `audit_module_dependencies.py` / `audit_package_exports.py` — verification helpers that still lack regression tests.
  - `config_validator.py` — drift detector that needs broader coverage.
  - `validate_ai_work.py` — structural heuristics only; do not treat as authoritative.
  - `unused_imports_checker.py` — noisy on generated files; review manually.
  - `quick_status.py` / `system_signals.py` — cached views that require a recent audit.
  - `decision_support.py` — advisory scoring, not a blocker.
- Experimental (prototype tier):
  - `version_sync.py` — fragile heuristic updates; run only with backup/approval.
  - `auto_document_functions.py` — generates docstrings automatically; high-risk edits.

---

### Phase 2 – Stabilize Core Infrastructure (Tier 1 Infra) **COMPLETED (2025-11-25)**

**Goal:** Make the backbone (runner + infra) solid enough that everything else can lean on it.

**Status:** All milestones completed. Core infrastructure now has test coverage and consistent logging/error handling.

#### Milestone M2.1 – Sanity Tests for Config and Exclusions **COMPLETED**

- ✅ Created `tests/development_tools/test_config.py` with 23 tests covering:
  - Key settings existence (PROJECT_ROOT, SCAN_DIRECTORIES, AI_COLLABORATION, FUNCTION_DISCOVERY, VALIDATION, AUDIT, OUTPUT, etc.)
  - Helper functions return expected types and structures
  - Path validation for project root and scan directories
- ✅ Created `tests/development_tools/test_standard_exclusions.py` with 21 tests covering:
  - Universal exclusion patterns (__pycache__, venv, .git, .pyc files, tests/data, scripts)
  - Representative paths that should be included (core, communication, ui files)
  - Tool-specific exclusions (coverage, analysis, documentation)
  - Context-specific exclusions (production, development, testing)
  - Path object handling (both string and Path objects)
- ✅ Created `tests/development_tools/test_constants.py` with 25 tests covering:
  - All DEFAULT_DOCS paths exist (with graceful handling for optional files)
  - All PAIRED_DOCS paths exist (both human and AI sides)
  - LOCAL_MODULE_PREFIXES contains expected modules
  - Helper functions (`is_local_module()`, `is_standard_library_module()`) work correctly
- ✅ Fixed path mismatch in constants.py (`tests/AI_FUNCTIONALITY_TEST_GUIDE.md` → `tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md`)

#### Milestone M2.2 – CLI Smoke Tests for Runner **COMPLETED**

- ✅ Created `tests/development_tools/test_ai_tools_runner.py` with 7 CLI smoke tests:
  - `status` command exits with code 0
  - `config` command exits with code 0
  - `help` command exits with code 0 and shows help
  - No command exits with code 1 and shows help
  - Unknown command exits with code 2 and shows error
  - Runner script exists and is executable
- ✅ All tests marked with appropriate markers (`@pytest.mark.integration`, `@pytest.mark.smoke`)
- ✅ Tests integrated into main test suite (run via `run_tests.py`)

#### Milestone M2.3 – Normalize Logging and Error Handling **COMPLETED**

- ✅ Added consistent logging to major operations in `operations.py`:
  - "Starting {operation_name}..." at operation start
  - "Completed {operation_name} successfully!" or "Completed {operation_name} with errors!" at completion
  - Applied to: `run_audit()`, `run_docs()`, `run_validate()`, `run_config()`, `run_status()`, `run_documentation_sync()`, `run_coverage_regeneration()`, `run_legacy_cleanup()`, `run_system_signals()`, `run_unused_imports_report()`
- ✅ Enhanced error handling in `ai_tools_runner.py`:
  - Added try/except around command execution to catch and log exceptions
  - Proper exit code propagation (0 for success, 1 for failures, 2 for usage errors)
- ✅ All command handlers return sensible exit codes consistently

**Result:** The infrastructure is now predictable and diagnosable. Tests provide regression protection, and logging makes operations traceable.

---

### Phase 3 – Harden the Core Analysis Tools (Tier 1+)

Focus on the most important tools in the pipeline:

- `documentation_sync_checker.py`
- `generate_function_registry.py`
- `generate_module_dependencies.py`
- `legacy_reference_cleanup.py`
- `regenerate_coverage_metrics.py`
- (optionally) `error_handling_coverage.py`

#### Milestone M3.1 – Create Synthetic Fixture Project

- Under `tests/fixtures/development_tools_demo/`, create a tiny project with:
  - A couple of modules importing each other.
  - Simple functions, handlers, and test functions.
  - Human/AI doc pairs with deliberate good and bad H2/metadata cases.
  - A known “legacy” import string.
  - A minimal test suite for coverage runs.

This fixture is the sandbox for all tool tests.

#### Milestone M3.2 – Tests for `documentation_sync_checker.py`

- On the fixture:
  - Case: perfectly synced docs → no errors.
  - Case: mismatched H2 headings → flagged.
  - Case: incorrect `File`/`Pair` metadata → flagged.
- Outcome: you can trust doc-sync’s pass/fail signals.

#### Milestone M3.3 – Tests for `generate_function_registry.py`

- On the fixture:
  - Run generator on a known set of functions.
  - Assert specific functions appear in FUNCTION_REGISTRY_DETAIL.
  - Assert categories (handlers/tests/etc.) are classified as intended.

#### Milestone M3.4 – Tests for `generate_module_dependencies.py`

- On the fixture:
  - Hand-write the expected small dependency graph.
  - Run generator.
  - Assert the generated dependencies match your expectations for that graph.

#### Milestone M3.5 – Safe Legacy Cleanup Tests

- On the fixture:
  - Introduce a known “legacy token” in code and docs.
  - Validate:
    - `--find` discovers the right locations.
    - `--verify` behaves as expected (ready/not ready).
    - `--clean --dry-run` reports planned actions but does not modify files.

#### Milestone M3.6 – Coverage Regeneration Tests

- On the fixture:
  - Run `regenerate_coverage_metrics.py` in a temp directory.
  - Assert:
    - `coverage.json` exists and has expected shape.
    - HTML coverage folder exists.
    - Running twice archives old results in `archive/coverage_artifacts/<timestamp>/` or equivalent.

Result: the “big five” tools become reasonably trustworthy.

---

### Phase 4 – Clarify Supporting vs Experimental Tools

**Goal:** Reduce cognitive noise and avoid accidental reliance on fragile scripts.

### Milestone M4.1 – Move Experimental Tools

- Create `development_tools/experimental/`.
- Move:
  - `version_sync.py`
  - `auto_document_functions.py`
- Update runner/help so they are clearly marked or only reachable via explicit flags.

#### Milestone M4.2 – Decide Fate of Each Tier-2 Tool

For each of:

- `analyze_documentation.py`
- `audit_function_registry.py`
- `audit_module_dependencies.py`
- `audit_package_exports.py`
- `config_validator.py`
- `validate_ai_work.py`
- `unused_imports_checker.py`
- `quick_status.py`
- `system_signals.py`
- `decision_support.py`
- `file_rotation.py`
- `tool_guide.py`

Decide:
- **Promote to Tier 1:** worth robust tests and core support, or
- **Keep as Tier 2:** useful but non-critical, or
- **Deprecate / Freeze:** rarely used or more confusing than helpful.

You do not need full test coverage here immediately; priority is clarity and reduced accidental use.

---

### Phase 5 – UX and Documentation Alignment

**Goal:** Make the tooling understandable and predictable for both humans and AI helpers.

#### Milestone M5.1 – Update `AI_DEVELOPMENT_TOOLS_GUIDE.md` **COMPLETED (2025-11-25)**

- ✅ Split into paired documentation guides (AI and human-facing)
- ✅ For each tool, added:
  - Tier (Core / Supporting / Experimental)
  - Trust level (stable, partial, advisory, experimental)
  - Portability status (portable, mhm-specific)
  - One-line scope description
- ✅ Complete tool catalog table in human guide with all 25+ tools
- ✅ Aligned guides with documentation standards (metadata, H2 headings)
- ✅ Verified all content preserved and enhanced in human guide

#### Milestone M5.2 – Standard Audit Recipe in `AI_DEVELOPMENT_WORKFLOW.md`

Add a short section describing when to run:

- `ai_tools_runner.py audit` (day-to-day checks).
- `ai_tools_runner.py audit --full` (pre-merge / pre-release checks).
- `ai_tools_runner.py doc-sync` and `ai_tools_runner.py docs` (doc work).

#### Milestone M5.3 – Update `AI_SESSION_STARTER.md`

- When the user’s task touches dev tools, route:
  - First to `AI_DEVELOPMENT_TOOLS_GUIDE.md`.
  - Then to the correct tools by tier and purpose.

Result: the dev tools ecosystem becomes something you and future collaborators can reason about and trust.

---

### Phase 6 – Portability Roadmap **ADDED (2025-11-25)**

**Goal:** Track every mhm-specific dependency and define concrete work needed to make tools portable.

**Status:** Roadmap defined and integrated into improvement plan. Per-tool portability checklist created for future work.

#### Core Tool Checklist
- `ai_tools_runner.py` — expose command registry + config paths via CLI arguments so it can point at any project root.
- `services/operations.py` — split command implementations from MHM-specific behaviors (Discord, account files) so a thin adapter can be swapped in.
- `config.py` — move default paths (docs, logs, data) into an external config file that can be overridden per environment.
- `services/standard_exclusions.py` — read exclusions from config/constants rather than hardcoding MHM directories.
- `services/constants.py` — relocate paired-doc metadata into a data file so non-MHM repos can supply their own doc lists.
- `documentation_sync_checker.py` — parameterize the doc root(s) and metadata schema instead of assuming the MHM structure.
- `generate_function_registry.py` / `function_discovery.py` — make scan roots and filters configurable; rely on passed-in include/exclude patterns.
- `generate_module_dependencies.py` — let callers provide module prefixes to treat as “local” vs “external”.
- `legacy_reference_cleanup.py` — treat LEGACY tokens and log locations as inputs so other projects can define their own markers.
- `regenerate_coverage_metrics.py` — accept pytest command, coverage config, and artifact directories as arguments.
- `error_handling_coverage.py` — read decorator names and exception base classes from config, not MHM-specific modules.

#### Supporting Tool Checklist
- `analyze_documentation.py` — parameterize the heading/metadata schema and let callers provide ignore rules.
- `audit_function_registry.py`, `audit_module_dependencies.py`, `audit_package_exports.py` — feed in the “expected” registries via config so tests are reusable elsewhere.
- `config_validator.py` — detect settings dynamically based on config schema rather than enumerating MHM-specific keys.
- `validate_ai_work.py` — read rule sets from YAML so new projects can define their validation heuristics.
- `unused_imports_checker.py` — allow custom ignore patterns and type stub locations.
- `quick_status.py`, `system_signals.py`, `decision_support.py` — provide plugin hooks so data sources (Discord, schedulers, etc.) can be swapped out.
- `tool_guide.py` — render guidance based on `services/tool_metadata.py` so another repo can simply override the metadata file.
- `file_rotation.py` — already portable; confirm it stays dependency-free.

#### Experimental Tool Checklist
- `version_sync.py` — read version files + patterns from config; avoid hardcoded MHM file list.
- `auto_document_functions.py` — ensure template paths, doc targets, and formatting rules are injectable.

Portable today: `services/common.py`, `system_signals.py`, and `file_rotation.py`—no action needed beyond keeping dependencies minimal.

---

### Phase 7 – Naming & Directory Strategy **ADDED (2025-11-25)**

**Goal:** Make the tool suite predictable by aligning names with actions and grouping related tools.

**Status:** Strategy defined and documented. Naming conventions and directory restructuring approach outlined for future implementation.

#### Milestone M7.1 – Establish Naming Conventions
- Adopt verb-based prefixes (`audit_*`, `generate_*`, `cleanup_*`, `report_*`) or domain-based prefixes (`docs_*`, `coverage_*`, `legacy_*`).
- Update `services/tool_metadata.py` with the agreed convention so new contributors can follow it.

#### Milestone M7.2 – Reorganize Directory Layout
- Proposed structure:  
  `development_tools/audit/` (audit/validate commands)  
  `development_tools/docs/` (doc generators + analyzers)  
  `development_tools/coverage/` (coverage + reporting)  
  `development_tools/legacy/` (cleanup scanners)  
  `development_tools/shared/` (config, constants, exclusions, metadata).
- Introduce package `__init__.py` files to keep imports stable during the migration.

#### Milestone M7.3 – Tool Gap & Future Additions
- Identify desired categories (e.g., test-data generators, AI prompt validators, environment health checks).
- Record missing tools or planned improvements in `DEVELOPMENT_TOOLS_GUIDE.md` + the roadmap so future work is scoped before implementation.

---

**Progress Summary:**
- ✅ **Phase 1 COMPLETED (2025-11-25)**: Tiering system fully implemented, documentation split and aligned, all path references updated
- ✅ **Phase 2 COMPLETED (2025-11-25)**: Core infrastructure stabilized with test coverage (76 tests), consistent logging, and normalized error handling
- 🔄 **Phase 3-7**: Defined and ready for implementation

This roadmap is intentionally incremental. You do **not** need to implement every milestone at once.  
Phases 1-2 (tiering + core infrastructure) are complete. Next focus on Phase 3 (harden core analysis tools) for the most important tools, then expand as time and energy allow.

---

This document can now serve as the authoritative basis for improving or restructuring the AI development tools ecosystem.