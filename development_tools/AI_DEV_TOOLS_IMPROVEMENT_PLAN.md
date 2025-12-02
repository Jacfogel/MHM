# AI Development Tools - Current State and Improvement Roadmap

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md`
> **Audience**: Project maintainers and developers
> **Purpose**: Provide a detailed assessment of all AI development tools, identifying strengths, weaknesses, fragility, gaps, and a roadmap for improvement.
> **Style**: Direct, technical, and candid.

This document summarizes the current state of the `development_tools` suite based on source review.  
It is intended to guide decisions on tool maintenance, triage, and future enhancements.

---

# 1. Overall State of the AI Development Tools

The `development_tools` directory represents an ambitious and generally well-structured attempt at creating an internal "analysis and audit platform" for the MHM project. The architecture includes:

- A unified dispatcher (`development_tools/run_development_tools.py`)
- Configurable behavior (`development_tools/config.py`)
- Centralized exclusions (`development_tools/services/standard_exclusions.py`)
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
- Write operations are high-risk without strong safeguards.
- ~~No formal "tiering"~~ **RESOLVED (2025-11-25)**: Tiering system implemented via `development_tools/services/tool_metadata.py` with tier markers in all tool modules and CLI help grouping.

**Summary:**  
Good bones, uneven execution. High potential, but needs consolidation, testing, and prioritization.

---

# 2. Per-Tool Breakdown

This section categorizes each tool into "Core," "Supporting," or "Experimental" based on reliability, purpose, and completeness.

---

## 2.1 Core Infrastructure (Strong, Foundational)

### `development_tools/config.py`
- Centralizes scan roots, thresholds, audit modes.
- Widely used across tools.
- [OK] **HAS VALIDATION TESTS (Phase 2)**: 23 tests in `tests/development_tools/test_config.py` verify key settings and helper functions.

### `development_tools/services/standard_exclusions.py`
- Good design: all tools call `should_exclude_file`.
- Patterns may need tuning but concept is sound.
- [OK] **HAS VALIDATION TESTS (Phase 2)**: 21 tests in `tests/development_tools/test_standard_exclusions.py` verify exclusion patterns work correctly.

### `development_tools/services/constants.py`
- Holds doc pairing metadata and predefined doc lists.
- Needs regular updates to avoid drift.
- [OK] **HAS VALIDATION TESTS (Phase 2)**: 25 tests in `tests/development_tools/test_constants.py` verify paths exist and helper functions work correctly.

### `development_tools/services/common.py`
- Provides consistent CLI patterns and file operations.
- Some tools bypass it; future tools should not.

### `development_tools/services/tool_metadata.py` **NEW (2025-11-25)**
- Single source of truth for tool tier, portability, trust level, description, and command metadata.
- Drives CLI help grouping and documentation generation.
- All tools reference this registry for authoritative classification.
- Eliminates duplication and ensures consistency across CLI, docs, and code.

**Overall:** These modules form a reliable backbone and should be maintained carefully. The addition of `development_tools/services/tool_metadata.py` provides the foundation for explicit tiering and consistent tool classification.

---

## 2.2 Runner and Operations Layer

### `development_tools/run_development_tools.py`
- Central dispatcher with command registry.
- Good entry point; ties the system together.
- [OK] **HAS CLI SMOKE TESTS (Phase 2)**: 7 tests in `tests/development_tools/test_run_development_tools.py` verify command execution and exit codes.
- [OK] **HAS ENHANCED ERROR HANDLING (Phase 2)**: Try/except blocks with proper logging and exit code propagation.

### `development_tools/services/operations.py`
- Implements core logic for each command.
- Has risk of becoming a "god module."
- Should eventually be split by domain (audit, docs, legacy, coverage).
- [OK] **HAS NORMALIZED LOGGING (Phase 2)**: Consistent "Starting..." and "Completed..." logging added to all major operations.

**Overall:** Strong concept; risks long-term sprawl without structure.

---

## 2.3 Documentation & Structure Tools (High Value, Complex)

### `development_tools/documentation_sync_checker.py`
- Validates human/AI doc pairing (H2 headings, metadata).
- Important for MHM's strict documentation system.
- Some fragility around edge cases.

### `development_tools/generate_function_registry.py`
- Extracts full project function registry.
- High complexity; AST-based scanning.
- Very valuable but fragile without tests.

### `development_tools/generate_module_dependencies.py`
- Computes dependency graph across modules.
- Preserves manual enhancement blocks.
- Large and sophisticated; needs validation.

### `development_tools/analyze_documentation.py`
- Detects incomplete or corrupted docs.
- Good complement to doc-sync; some overlap.

**Overall:** These tools are sophisticated and incredibly useful, but require hardening.

---

## 2.4 Quality, Coverage & Validation Tools (High Value, Uneven)

### `development_tools/tests/generate_test_coverage.py`
- Full coverage regeneration with HTML output.
- Handles artifact rotation and aggregation.
- High-risk without tests; complex flows.

### `development_tools/validate_ai_work.py`
- Lightweight structural validator.
- Useful but incomplete; not authoritative.

### `development_tools/unused_imports_checker.py`
- AST-based unused import detector.
- Potentially noisy; requires tuning.

### `development_tools/error_handling_coverage.py`
- Analyzes exception patterns, decorator usage, custom errors.
- Strong concept that aligns with ERROR_HANDLING_GUIDE.
- Static analysis limitations exist.

**Overall:** Valuable tools, but accuracy varies; should be validated individually.

---

## 2.5 Legacy, Versioning, Signals (Mixed Quality)

### `development_tools/legacy_reference_cleanup.py`
- Supports find/verify/scan/clean (with dry-run).
- Very useful but high-risk; must rely heavily on dry-run.

### `development_tools/docs/fix_version_sync.py`
- Attempts to synchronize versioning across files.
- Often fragile; underdeveloped; easy to break.

### `development_tools/system_signals.py`
- Minimal; hooks for OS/system health.
- Used lightly.

### `development_tools/quick_status.py`
- Fast snapshot for AI tools.
- Only reliable if audits are fresh.

**Overall:** Legacy cleanup is core; version_sync should be considered experimental; signals + quick status are safe but shallow.

---

## 2.6 Decision Support & Misc Utilities (Variable Quality)

### `development_tools/decision_support.py`
- Aggregates outputs into priorities and complexity insights.
- Advisory only; not deterministic.

### `development_tools/functions/analyze_functions.py`
- Parses function signatures, handlers, tests.
- Forms basis for several other tools.

### `development_tools/functions/generate_function_docstrings.py`
- Generates docstrings automatically.
- High-risk; should be treated as experimental.

### `development_tools/config_validator.py`
- Checks config usage across tools.
- Helps detect drift; incomplete but useful.

### `development_tools/file_rotation.py`
- Simple timestamp-based rotation and "latest" pointer.
- Solid utility.

### `development_tools/audit_function_registry.py`, `development_tools/audit_module_dependencies.py`, `development_tools/audit_package_exports.py`
- Validate the outputs of code-to-doc generators.
- High value when paired with solid registry/dependency generators.

### `development_tools/tool_guide.py`
- Generates help text.
- Safe and stable.

**Overall:** Some gems here, some fragile experiments.

---

# 3. Cross-Cutting Issues Identified

### **1. ~~No clear tiering (core vs supporting vs experimental)~~** **RESOLVED (2025-11-25)**
- [OK] Tier markers added to all tool modules (`# TOOL_TIER` and `# TOOL_PORTABILITY` headers)
- [OK] `development_tools/services/tool_metadata.py` created as single source of truth for tier, portability, trust, and command metadata
- [OK] CLI help output groups commands by tier (Core, Supporting, Experimental) with warnings
- [OK] Documentation guides updated with tier information and trust levels
- [OK] Directory renamed from `ai_development_tools/` to `development_tools/` for clarity

### **2. ~~No tests for tooling~~** **RESOLVED (2025-11-27)**
- [OK] Basic sanity tests added for core infrastructure (`development_tools/config.py`, `development_tools/services/standard_exclusions.py`, `development_tools/services/constants.py`)
- [OK] CLI smoke tests added for `development_tools/ai_tools_runner.py`
- [OK] Logging and error handling normalized in `development_tools/services/operations.py` and `development_tools/ai_tools_runner.py`
- [OK] Comprehensive tests added for all five core analysis tools (Phase 3):
  - `development_tools/documentation_sync_checker.py` (12 tests)
  - `development_tools/generate_function_registry.py` (12 tests)
  - `development_tools/generate_module_dependencies.py` (11 tests)
  - `development_tools/legacy_reference_cleanup.py` (10 tests)
  - `development_tools/regenerate_coverage_metrics.py` (10 tests)
- [OK] Regression tests added for supporting tools (Phase 4 follow-up, 2025-11-27):
  - `development_tools/quick_status.py` (2 tests)
  - `development_tools/system_signals.py` (2 tests)
  - `development_tools/file_rotation.py` (2 tests)
- [OK] Synthetic fixture project created at `tests/fixtures/development_tools_demo/` for isolated testing
- [OK] Total test coverage: 138+ tests across all development tools

### **3. Risky write operations**
- Tools like legacy cleanup, auto-documentation, coverage regeneration write real files.
- Without strong safeguards, they can corrupt code or docs.

### **4. Conceptual overlap / sprawl**
- Documentation tools overlap; analysis tools overlap; validation tools overlap.
- The audit pipeline needs clearer boundaries and flow.

### **5. ~~No explicit indicator of experimental tools~~** **RESOLVED (2025-11-25)**
- [OK] All tools now carry tier markers in source code
- [OK] CLI help explicitly warns about experimental commands
- [OK] Documentation guides list trust levels and portability status for each tool
- [OK] Reference list of partial/advisory/experimental tools documented in guides

---

## 4. AI Development Tools - Implementation Roadmap

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md` (this file)  
> **Audience**: Project maintainers and developers  
> **Purpose**: Provide a practical, phased roadmap with milestones to stabilize, test, and rationalize the AI development tools.  
> **Style**: Direct, technical, and concise.

This roadmap assumes the following tiering for the AI development tools:

- **Tier 1 - Core**
  - `development_tools/ai_tools_runner.py`, `development_tools/services/operations.py`, `development_tools/config.py`, `development_tools/services/standard_exclusions.py`, `development_tools/services/constants.py`, `development_tools/services/common.py`
  - `development_tools/documentation_sync_checker.py`, `development_tools/generate_function_registry.py`, `development_tools/generate_module_dependencies.py`
  - `development_tools/legacy_reference_cleanup.py`, `development_tools/regenerate_coverage_metrics.py`
  - `development_tools/error_handling_coverage.py`, `development_tools/function_discovery.py`

- **Tier 2 - Supporting**
  - `development_tools/analyze_documentation.py`, `development_tools/audit_function_registry.py`, `development_tools/audit_module_dependencies.py`, `development_tools/audit_package_exports.py`
  - `development_tools/config_validator.py`, `development_tools/validate_ai_work.py`, `development_tools/unused_imports_checker.py`, `development_tools/quick_status.py`, `development_tools/system_signals.py`
  - `development_tools/decision_support.py`, `development_tools/file_rotation.py`, `development_tools/tool_guide.py`

- **Tier 3 - Experimental**
  - `development_tools/experimental/version_sync.py`, `development_tools/experimental/auto_document_functions.py`

---

### Phase 1 - Make the Landscape Explicit **COMPLETED (2025-11-25)**

**Goal:** Turn the informal understanding of "which tools matter" into explicit structure and expectations.

**Status:** All milestones completed. Tiering system fully implemented and integrated into CLI, documentation, and codebase.

#### Milestone M1.1 - Add Tier Markers **COMPLETED**

- [OK] Created `development_tools/services/tool_metadata.py` as authoritative registry for all tool metadata (tier, portability, trust, description, command name)
- [OK] Added `# TOOL_TIER: core | supporting | experimental` headers to all tool modules
- [OK] Added `# TOOL_PORTABILITY: portable | mhm-specific` headers to all tool modules
- [OK] Removed BOM characters discovered during header injection sweep
- [OK] All 25+ tools now have consistent tier and portability markers

#### Milestone M1.2 - Reflect Tiering in Help Output **COMPLETED**

- [OK] Updated `development_tools/services/common.py` to build command groupings from `development_tools/services/tool_metadata.py` (single source of truth)
- [OK] Updated `development_tools/ai_tools_runner.py` to display commands grouped by tier in help output
- [OK] Updated `development_tools/services/operations.py` to use tier-based grouping for help display
- [OK] Enhanced `development_tools/tool_guide.py` to print tier overview sourced from `development_tools/services/tool_metadata.py`
- [OK] Help output now groups commands under **Core**, **Supporting**, and **Experimental** headings with explicit warnings

#### Milestone M1.3 - Document "Partial / Experimental" Tools **COMPLETED**

- [OK] Split documentation into paired guides:
  - `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` (AI-facing, routing-focused)
  - `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` (human-facing, detailed catalog)
- [OK] Both guides include complete tool catalog with tier, trust level, portability, and notes
- [OK] Explicitly flagged partial/incomplete tools (e.g. `development_tools/validate_ai_work.py`)
- [OK] Explicitly flagged advisory-only tools (e.g. `development_tools/decision_support.py`)
- [OK] Explicitly flagged experimental/fragile tools (e.g. `development_tools/experimental/version_sync.py`, `development_tools/experimental/auto_document_functions.py`)
- [OK] Aligned both guides with documentation standards (metadata blocks, identical H2 headings)
- [OK] Updated all path references from `ai_development_tools/` to `development_tools/` throughout codebase
- [OK] Added guides to `DEFAULT_DOCS`, `PAIRED_DOCS`, directory tree, README, and other doc listings

This does not fix code, but it stops you from accidentally trusting the wrong tool.

**Reference list for documentation and CLI alignment**

- Partial / advisory (Supporting tier):
  - `development_tools/analyze_documentation.py` - overlap/corruption detection with known edge cases.
  - `development_tools/audit_function_registry.py` - validates registry output but depends on fixture freshness.
  - `development_tools/audit_module_dependencies.py` / `development_tools/audit_package_exports.py` - verification helpers that still lack regression tests.
  - `development_tools/config_validator.py` - drift detector that needs broader coverage.
  - `development_tools/validate_ai_work.py` - structural heuristics only; do not treat as authoritative.
  - `development_tools/unused_imports_checker.py` - noisy on generated files; review manually.
  - `development_tools/quick_status.py` / `development_tools/system_signals.py` - cached views that require a recent audit.
  - `development_tools/decision_support.py` - advisory scoring, not a blocker.
- Experimental (prototype tier):
  - `development_tools/experimental/version_sync.py` - fragile heuristic updates; run only with backup/approval.
  - `development_tools/experimental/auto_document_functions.py` - generates docstrings automatically; high-risk edits.

---

### Phase 2 - Stabilize Core Infrastructure (Tier 1 Infra) **COMPLETED (2025-11-25)**

**Goal:** Make the backbone (runner + infra) solid enough that everything else can lean on it.

**Status:** All milestones completed. Core infrastructure now has test coverage and consistent logging/error handling.

#### Milestone M2.1 - Sanity Tests for Config and Exclusions **COMPLETED**

- [OK] Created `tests/development_tools/test_config.py` with 23 tests covering:
  - Key settings existence (PROJECT_ROOT, SCAN_DIRECTORIES, AI_COLLABORATION, FUNCTION_DISCOVERY, VALIDATION, AUDIT, OUTPUT, etc.)
  - Helper functions return expected types and structures
  - Path validation for project root and scan directories
- [OK] Created `tests/development_tools/test_standard_exclusions.py` with 21 tests covering:
  - Universal exclusion patterns (__pycache__, venv, .git, .pyc files, tests/data, scripts)
  - Representative paths that should be included (core, communication, ui files)
  - Tool-specific exclusions (coverage, analysis, documentation)
  - Context-specific exclusions (production, development, testing)
  - Path object handling (both string and Path objects)
- [OK] Created `tests/development_tools/test_constants.py` with 25 tests covering:
  - All DEFAULT_DOCS paths exist (with graceful handling for optional files)
  - All PAIRED_DOCS paths exist (both human and AI sides)
  - LOCAL_MODULE_PREFIXES contains expected modules
  - Helper functions (`is_local_module()`, `is_standard_library_module()`) work correctly
- [OK] Fixed path mismatch in constants.py (`tests/AI_FUNCTIONALITY_TEST_GUIDE.md` -> `tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md`) (archived reference - file no longer exists)

#### Milestone M2.2 - CLI Smoke Tests for Runner **COMPLETED**

- [OK] Created `tests/development_tools/test_ai_tools_runner.py` with 7 CLI smoke tests:
  - `status` command exits with code 0
  - `config` command exits with code 0
  - `help` command exits with code 0 and shows help
  - No command exits with code 1 and shows help
  - Unknown command exits with code 2 and shows error
  - Runner script exists and is executable
- [OK] All tests marked with appropriate markers (`@pytest.mark.integration`, `@pytest.mark.smoke`)
- [OK] Tests integrated into main test suite (run via `run_tests.py`)

#### Milestone M2.3 - Normalize Logging and Error Handling **COMPLETED**

- [OK] Added consistent logging to major operations in `development_tools/services/operations.py`:
  - "Starting {operation_name}..." at operation start
  - "Completed {operation_name} successfully!" or "Completed {operation_name} with errors!" at completion
  - Applied to: `run_audit()`, `run_docs()`, `run_validate()`, `run_config()`, `run_status()`, `run_documentation_sync()`, `run_coverage_regeneration()`, `run_legacy_cleanup()`, `run_system_signals()`, `run_unused_imports_report()`
- [OK] Enhanced error handling in `ai_tools_runner.py`:
  - Added try/except around command execution to catch and log exceptions
  - Proper exit code propagation (0 for success, 1 for failures, 2 for usage errors)
- [OK] All command handlers return sensible exit codes consistently

**Result:** The infrastructure is now predictable and diagnosable. Tests provide regression protection, and logging makes operations traceable.

---

### Phase 3 - Harden the Core Analysis Tools (Tier 1+) **COMPLETED (2025-11-26)**

**Goal:** Add comprehensive test coverage for the five core analysis tools to make them trustworthy and provide regression protection.

**Status:** All milestones completed. Core analysis tools now have robust test coverage using a synthetic fixture project.

#### Milestone M3.1 - Create Synthetic Fixture Project **COMPLETED**

- [OK] Created `tests/fixtures/development_tools_demo/` with:
  - `tests/fixtures/development_tools_demo/demo_module.py` and `tests/fixtures/development_tools_demo/demo_module2.py` with functions, classes, and imports
  - `tests/fixtures/development_tools_demo/demo_tests.py` for coverage runs
  - `tests/fixtures/development_tools_demo/legacy_code.py` with known legacy patterns and markers
  - `docs/` directory with paired documentation (synced, mismatched, standalone cases)
  - `README.md` documenting the fixture structure
- [OK] Fixture provides controlled environment for testing without affecting main codebase

#### Milestone M3.2 - Tests for `development_tools/documentation_sync_checker.py` **COMPLETED**

- [OK] Created `tests/development_tools/test_documentation_sync_checker.py` with 12 tests:
  - Perfectly synced docs return no errors
  - Mismatched H2 headings are flagged
  - Missing files are detected
  - Path drift validation
  - ASCII compliance checks
  - Heading numbering validation
  - Full integration test
- [OK] Tests verify doc-sync's pass/fail signals are reliable

#### Milestone M3.3 - Tests for `development_tools/generate_function_registry.py` **COMPLETED**

- [OK] Created `tests/development_tools/test_generate_function_registry.py` with 12 tests:
  - Function and class extraction from files
  - Handler and test function detection
  - File scanning with exclusions
  - Content generation and categorization
  - File writing operations
- [OK] Tests verify registry generation accuracy and categorization

#### Milestone M3.4 - Tests for `development_tools/generate_module_dependencies.py` **COMPLETED**

- [OK] Created `tests/development_tools/test_generate_module_dependencies.py` with 11 tests:
  - Import extraction (standard library, third-party, local)
  - Reverse dependency finding
  - Content generation structure
  - Manual enhancement preservation
  - Dependency change analysis
  - Module purpose inference
- [OK] Tests verify dependency graph accuracy

#### Milestone M3.5 - Safe Legacy Cleanup Tests **COMPLETED**

- [OK] Created `tests/development_tools/test_legacy_reference_cleanup.py` with 10 tests (for `development_tools/legacy_reference_cleanup.py`):
  - Legacy marker scanning
  - Preserve file handling
  - Reference finding for specific items
  - Removal readiness verification
  - Dry-run and actual cleanup operations
  - Report generation
  - File exclusion handling
  - Replacement mappings
- [OK] Fixed `should_skip_file` to use relative paths for proper exclusion checking
- [OK] Added class definition pattern to `find_all_references` for complete detection
- [OK] Tests verify safe cleanup operations with proper isolation

#### Milestone M3.6 - Coverage Regeneration Tests **COMPLETED**

- [OK] Created `tests/development_tools/test_regenerate_coverage_metrics.py` with 10 tests (for `development_tools/regenerate_coverage_metrics.py`):
  - Coverage output parsing
  - Overall coverage extraction
  - Module categorization by coverage
  - Coverage summary generation
  - Pytest execution integration
  - Coverage path configuration
  - Shard cleanup
  - Coverage plan updates
- [OK] Tests verify coverage regeneration accuracy and artifact handling

**Result:** All five core analysis tools now have comprehensive test coverage (55+ tests total). Tests use shared fixtures in `tests/development_tools/conftest.py` and the synthetic fixture project for isolation. The tools are now reasonably trustworthy with regression protection.

---

### Phase 4 - Clarify Supporting vs Experimental Tools **COMPLETED (2025-11-27)**

**Goal:** Reduce cognitive noise and avoid accidental reliance on fragile scripts.

**Status:** All milestones completed. Experimental tools moved, Tier-2 tools analyzed and documented, dev tools coverage tracking added, supporting tools regression tests created.

### Milestone M4.1 - Move Experimental Tools **COMPLETED (2025-11-27)**

- [OK] Created `development_tools/experimental/` directory with `__init__.py`
- [OK] Moved experimental tools:
  - `development_tools/version_sync.py` -> `development_tools/experimental/version_sync.py`
  - `development_tools/auto_document_functions.py` -> `development_tools/experimental/auto_document_functions.py`
- [OK] Updated all imports and references in `operations.py`, `tool_metadata.py`, and documentation
- [OK] Fixed import path in `version_sync.py` for `documentation_sync_checker` (changed from `.` to `..`)
- [OK] CLI help output correctly reflects experimental status with warnings

#### Milestone M4.2 - Decide Fate of Each Tier-2 Tool **COMPLETED (2025-11-27)**

**Decision**: All 12 Tier-2 tools will remain in the Supporting tier. None are being promoted to Tier 1 or deprecated at this time, but several require explicit follow-up.

##### Analysis methodology
- Reviewed usage paths in `operations.py`, CLI commands, and documentation to confirm each tool's role.
- Checked for existing tests under `tests/development_tools/` (none exist for Tier-2 tools today).
- Evaluated operational value (critical vs. advisory) and maintenance burden/fragility.

##### Tool-by-tool findings
- **`analyze_documentation.py`** - *Trust: partial*  
  Usage: runs during full audit as corruption detector; overlaps doc-sync but focuses on duplicates.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; enhance over time instead of promoting.

- **`audit_function_registry.py`** - *Trust: partial*  
  Usage: validates `generate_function_registry.py` output after docs generation; results cached in audit.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; valuable for regressions but depends on fixture freshness.

- **`audit_module_dependencies.py`** - *Trust: partial*  
  Usage: verifies `MODULE_DEPENDENCIES_DETAIL.md`, but was not wired into the audit workflow.  
  Coverage: none.  
  Recommendation: **Keep Tier 2** and **run automatically after doc-sync** (done in this phase).

- **`audit_package_exports.py`** - *Trust: partial*  
  Usage: rarely invoked; checks declared exports.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**, but monitor usage and deprecate if unused for two audit cycles.

- **`config_validator.py`** - *Trust: partial*  
  Usage: runs in both fast/full audits to detect config drift.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; invest in broader rule coverage.

- **`validate_ai_work.py`** - *Trust: partial/advisory*  
  Usage: invoked during audits for structural linting; advisory only.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; clarify advisory nature in docs (already done).

- **`unused_imports_checker.py`** - *Trust: partial*  
  Usage: part of full audit; AST-based and noisy on generated files.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; continue tuning exclusions.

- **`quick_status.py`** - *Trust: advisory*  
  Usage: powers `status` command and audit snapshots; heavily used.  
  Coverage: [OK] Regression tests added (2025-11-27) - 2 tests in `test_supporting_tools.py`.  
  Recommendation: **Keep Tier 2**; tests now exist, Tier 1 promotion possible if desired.

- **`system_signals.py`** - *Trust: advisory*  
  Usage: runs every audit to collect OS/process health; portable.  
  Coverage: [OK] Regression tests added (2025-11-27) - 2 tests in `test_supporting_tools.py`.  
  Recommendation: **Keep Tier 2**; tests now exist, Tier 1 promotion possible if desired.

- **`decision_support.py`** - *Trust: advisory*  
  Usage: aggregates metrics for priorities/watch lists.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; advisory by design.

- **`file_rotation.py`** - *Trust: stable*  
  Usage: used by coverage regeneration for artifact rotation.  
  Coverage: [OK] Regression tests added (2025-11-27) - 2 tests in `test_supporting_tools.py`.  
  Recommendation: **Keep Tier 2** but flag as stable/portable; tests now exist, promotion possible if desired.

- **`tool_guide.py`** - *Trust: stable*  
  Usage: generates CLI help groupings.  
  Coverage: none.  
  Recommendation: **Keep Tier 2**; no further action needed beyond encoding fix completed in M4.3.

##### Summary & follow-up
- All Supporting tools remain Tier 2; regression tests now exist for `quick_status`, `system_signals`, and `file_rotation` (completed 2025-11-27), making future Tier 1 promotion feasible if desired.
- **Integration gap resolved**: `audit_module_dependencies.py` now runs inside the full audit workflow, so dependency docs drift surfaces in reports.
- **Monitoring**: `audit_package_exports.py` stays in Tier 2 but will be reviewed after two audit cycles; deprecate if still unused.
- **Trust levels**: Reviewed `tool_metadata.py`; current trust designations already match the analysis (no updates required).

**Next steps tracking (Phase 4 follow-through):**
1. Document the recommendations in-plan - [OK] (this section replaces the standalone file).  
2. Update `tool_metadata.py` if trust levels need changes - [OK] Reviewed; no changes required.  
3. Add tests for the three high-value utilities (`quick_status`, `system_signals`, `file_rotation`) - [OK] Completed (2025-11-27); see `tests/development_tools/test_supporting_tools.py` for 6 new regression tests covering:
   - Missing file detection and recent activity tracking (`quick_status`)
   - Missing directory reporting and recent activity listing (`system_signals`)
   - Archive version limiting and file rotation with `create_output_file` (`file_rotation`)
   - All tests passing; fixes applied for timestamp collisions, environment variable handling, and path normalization
4. Integrate `audit_module_dependencies.py` into the audit workflow - [OK] Hooked into `_run_contributing_tools` and quick audit parsing.  
5. Monitor `audit_package_exports.py`; if unused over the next two audit passes, schedule a deprecation review - [IN PROGRESS] In progress (tracked in this phase summary).

#### Milestone M4.3 - Test Coverage Metrics for Development Tools **COMPLETED (2025-11-27)**

- [OK] Added coverage metrics tracking for the development tools themselves
- [OK] Generate coverage reports specifically for `development_tools/` directory:
  - JSON report: `development_tools/coverage_dev_tools.json`
  - HTML report: `development_tools/coverage_html_dev_tools/`
  - Coverage data file: `development_tools/.coverage_dev_tools`
- [OK] Integrated into `audit --full` workflow in `operations.py`
- [OK] Added `run_dev_tools_coverage()` method to `CoverageMetricsRegenerator` class
- [OK] Coverage runs automatically during full audit and reports percentage

**Implementation details**:
- New method `run_dev_tools_coverage()` in `regenerate_coverage_metrics.py` runs pytest with `--cov=development_tools` on `tests/development_tools/`
- Integrated into `run_audit(full=True)` workflow - runs after main coverage regeneration
- Results logged and stored for consolidated reporting
- HTML report generated separately for easy viewing
- Dedicated coverage config file `development_tools/coverage_dev_tools.ini` created to avoid conflicts with main project coverage
- Coverage results integrated into `AI_STATUS.md`, `AI_PRIORITIES.md`, and `consolidated_report.txt` with detailed metrics and recommendations
- Fixed encoding issue in `tool_guide.py` (converted from UTF-16 to UTF-8) to eliminate coverage warnings

**Additional fixes applied during Phase 4:**
- Fixed missing `_load_coverage_json` method in `operations.py` that was causing status command failures
- Enhanced dev tools coverage reporting with module-level insights and recommendations
- Fixed double percentage sign display issue in coverage reports
- Fixed encoding issue in `tool_guide.py` (converted from UTF-16 to UTF-8) to eliminate coverage warnings

**Additional fixes applied during Phase 4:**
- Fixed missing `_load_coverage_json` method in `operations.py` that was causing status command failures
- Enhanced dev tools coverage reporting with module-level insights and recommendations
- Fixed double percentage sign display issue in coverage reports

---

### Phase 5 - UX and Documentation Alignment **COMPLETED (2025-11-27)**

**Goal:** Make the tooling understandable and predictable for both humans and AI helpers.

**Status:** All milestones completed. Documentation now includes standard audit recipes and routing guidance for development tools.

#### Milestone M5.1 - Update `AI_DEVELOPMENT_TOOLS_GUIDE.md` **COMPLETED (2025-11-25)**

- [OK] Split into paired documentation guides (AI and human-facing)
- [OK] For each tool, added:
  - Tier (Core / Supporting / Experimental)
  - Trust level (stable, partial, advisory, experimental)
  - Portability status (portable, mhm-specific)
  - One-line scope description
- [OK] Complete tool catalog table in human guide with all 25+ tools
- [OK] Aligned guides with documentation standards (metadata, H2 headings)
- [OK] Verified all content preserved and enhanced in human guide

#### Milestone M5.2 - Standard Audit Recipe in `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` **COMPLETED (2025-11-27)**

- [OK] Added "## 10. Standard Audit Recipe" section to `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- [OK] Describes when to run:
  - `python development_tools/run_development_tools.py audit` (day-to-day checks)
  - `python development_tools/run_development_tools.py audit --full` (pre-merge / pre-release checks)
  - `python development_tools/run_development_tools.py doc-sync` and `python development_tools/run_development_tools.py docs` (doc work)
  - `python development_tools/run_development_tools.py status` (quick status snapshot)
- [OK] Includes reference to `AI_DEVELOPMENT_TOOLS_GUIDE.md` for detailed tool usage

#### Milestone M5.3 - Update `ai_development_docs/AI_SESSION_STARTER.md` **COMPLETED (2025-11-27)**

- [OK] Added routing guidance for development tools tasks
- [OK] When user's task touches dev tools, routes:
  - First to `AI_DEVELOPMENT_TOOLS_GUIDE.md` as primary reference
  - Includes examples: audits, status checks, tool tiers, generated reports, commands
- [OK] Added development tooling section in "2. Quick Reference" with specific routing to:
  - Main entry point (`ai_tools_runner.py` commands)
  - Fast mode vs full mode guidance
  - Generated outputs location
- [OK] Integrated with legacy removal guide routing

Result: the dev tools ecosystem becomes something you and future collaborators can reason about and trust.

---

### Phase 6 - Portability Roadmap **COMPLETED (2025-11-28)**

**Goal:** Track every mhm-specific dependency and define concrete work needed to make tools portable.

**Status:** All checklists completed. All 14 supporting and experimental tools now support external configuration via `development_tools_config.json` and can be used in other projects with minimal setup. All tools changed from `mhm-specific` to `portable` portability markers.

#### Core Tool Checklist **COMPLETED**
- [OK] `development_tools/ai_tools_runner.py` - Added `--project-root` and `--config-path` CLI arguments for portability. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/services/operations.py` - Made portable by accepting `project_root`, `config_path`, `project_name`, and `key_files` during initialization. Replaced hardcoded "MHM" references with generic "Project". Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/config.py` - External config file support added (`development_tools_config.json` in project root). All default paths, settings, and project-specific values now load from external config with generic fallbacks. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/services/standard_exclusions.py` - All exclusion lists now load from `config.get_exclusions_config()` with generic fallbacks. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/services/constants.py` - All project-specific constants (paired docs, module prefixes, core modules, etc.) now load from `config.get_constants_config()` with generic fallbacks. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/documentation_sync_checker.py` - Parameterized doc roots and metadata schema. Accepts `project_root` and `config_path` parameters. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/generate_function_registry.py` / `development_tools/function_discovery.py` - Made configurable via external config. Scan roots and filters load from config. `function_discovery.py` outputs JSON format. Changed `TOOL_PORTABILITY` markers to `portable`.
- [OK] `development_tools/generate_module_dependencies.py` - Accepts optional `local_prefixes` parameter for portability. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/legacy_reference_cleanup.py` - Legacy patterns, replacement mappings, and log locations now load from `config.get_legacy_cleanup_config()`. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/regenerate_coverage_metrics.py` - Accepts `pytest_command`, `coverage_config`, and `artifact_directories` parameters. All load from external config. Improved logging to distinguish test failures from coverage collection issues. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/error_handling_coverage.py` - Decorator names, exception base classes, and error handler functions now load from `config.get_error_handling_config()`. Changed `TOOL_PORTABILITY` marker to `portable`.

**Implementation Details:**
- Created `development_tools_config.json` in project root with all MHM-specific settings
- Created `development_tools/development_tools_config.json.example` as a template for other projects
- All tools now check for external config file on initialization
- Configuration priority: external config -> hardcoded defaults (generic/empty)
- Backward compatible: tools work without external config using generic defaults

#### Supporting Tool Checklist **COMPLETED**
- [OK] `development_tools/analyze_documentation.py` - Parameterized heading/metadata schema, placeholder patterns, and topic keywords load from config. Accepts `project_root` and `config_path` parameters. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/audit_function_registry.py` - Registry path, thresholds, and limits load from config. Accepts `project_root` and `config_path` parameters. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/audit_module_dependencies.py` - Dependency doc path loads from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/audit_package_exports.py` - Export patterns and expected exports load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/config_validator.py` - Config schema and validation rules load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/validate_ai_work.py` - Validation rules and thresholds load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/unused_imports_checker.py` - Pylint command, ignore patterns, and type stub locations load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/quick_status.py` - Core files and directories load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/system_signals.py` - Core files load from config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/decision_support.py` - Already uses configurable function discovery config. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/tool_guide.py` - Already uses `tool_metadata.py`. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/file_rotation.py` - Already portable; verified dependency-free.

#### Experimental Tool Checklist **COMPLETED**
- [OK] `development_tools/experimental/version_sync.py` - Switched to use `get_version_sync_config()`. Changed `TOOL_PORTABILITY` marker to `portable`.
- [OK] `development_tools/experimental/auto_document_functions.py` - Template paths, doc targets, formatting rules, and function type detection load from config. Changed `TOOL_PORTABILITY` marker to `portable`.

Portable today: `development_tools/services/common.py`, `development_tools/system_signals.py`, and `development_tools/file_rotation.py` - no action needed beyond keeping dependencies minimal.

---

### Phase 7 - Naming & Directory Strategy **ADDED (2025-11-25)**

**Goal:** Make the tool suite predictable by aligning names with actions and grouping related tools.

**Status:** M7.1 completed (naming conventions applied to all files and references updated, including second batch of renames). M7.2 completed (directory reorganization). M7.3 pending (tool gap analysis).

#### Milestone M7.1 - Establish Naming Conventions **COMPLETED (2025-12-01)**
- [OK] Adopted 3-prefix naming system:
  - **`analyze_*`** - Finding + assessing (read-only examination, validation, detection)
  - **`generate_*`** - Making artifacts (create/recreate documentation, registries, reports)
  - **`fix_*`** - Cleanup/repair (removal, cleanup operations)
  - **No prefix** - Reporting/utility tools (descriptive names: `decision_support`, `quick_status`, `system_signals`, `consolidated_report`, `function_discovery`, `file_rotation`, `tool_guide`)
- [OK] Rename files that don't follow conventions:
  - `docs/documentation_sync_checker.py` → `docs/analyze_documentation_sync.py` ✓
  - `imports/unused_imports_checker.py` → `imports/analyze_unused_imports.py` ✓
  - `config/config_validator.py` → `config/analyze_config.py` ✓
  - `error_handling/error_handling_coverage.py` → `error_handling/analyze_error_handling.py` ✓
  - `legacy/legacy_reference_cleanup.py` → `legacy/fix_legacy_references.py` ✓
  - `tests/regenerate_coverage_metrics.py` → `tests/generate_test_coverage.py` ✓
  - `functions/audit_function_registry.py` → `functions/analyze_function_registry.py` ✓
  - `imports/audit_module_dependencies.py` → `imports/analyze_module_dependencies.py` ✓
  - `functions/audit_package_exports.py` → `functions/analyze_package_exports.py` ✓
  - `ai_work/validate_ai_work.py` → `ai_work/analyze_ai_work.py` ✓
- [ ] Files that stay (already correct or utilities):
  - `functions/generate_function_registry.py` ✓
  - `imports/generate_module_dependencies.py` ✓
  - `docs/analyze_documentation.py` ✓
  - `reports/decision_support.py` (utility, no prefix)
  - `reports/quick_status.py` (utility, no prefix)
  - `reports/system_signals.py` (utility, no prefix)
  - `reports/generate_consolidated_report.py` (utility, renamed from consolidated_report.py)
  - `functions/analyze_functions.py` (utility, no prefix - renamed from function_discovery) ✓
  - `shared/file_rotation.py` (utility, no prefix)
  - `shared/tool_guide.py` (utility, no prefix)
  - `docs/fix_version_sync.py` (experimental, renamed from version_sync) ✓
  - `functions/generate_function_docstrings.py` (experimental, renamed from auto_document_functions) ✓
- [OK] Second batch of renames completed (2025-12-01):
  - `ai_tools_runner.py` → `run_development_tools.py` ✓
  - `function_discovery.py` → `analyze_functions.py` ✓
  - `version_sync.py` → `fix_version_sync.py` ✓
  - `auto_document_functions.py` → `generate_function_docstrings.py` ✓
  - `generate_coverage_metrics.py` → `generate_test_coverage.py` ✓
  - `consolidated_report.py` → `generate_consolidated_report.py` ✓
  - `config_validation_results.json` → `analyze_config_results.json` ✓
  - `ai_audit_detailed_results.json` → `analysis_detailed_results.json` ✓
- [OK] Created shorthand alias `run_dev_tools.py` for `run_development_tools.py` ✓
- [OK] Update all references after renaming (imports, SCRIPT_REGISTRY, tool_metadata.py, documentation, test files, config files) ✓
- [OK] Document naming conventions in `development_tools/shared/tool_metadata.py` or a separate guide ✓

#### Milestone M7.2 - Reorganize Directory Layout **COMPLETED (2025-11-30)**
- [OK] Implemented domain-based directory structure with workflow patterns:
  - `development_tools/functions/` - Function discovery, registry generation, audits
  - `development_tools/imports/` - Import checking, module dependency analysis and audits (merged from `modules/`)
  - `development_tools/error_handling/` - Error handling coverage analysis
  - `development_tools/tests/` - Test coverage metrics
  - `development_tools/docs/` - Documentation analysis and sync checking
  - `development_tools/config/` - Configuration and validation (contains `config.py`, `config_validator.py`, and config files)
  - `development_tools/legacy/` - Legacy cleanup (finder + fixer)
  - `development_tools/ai_work/` - AI work validation
  - `development_tools/reports/` - Overarching analysis tools (consolidated reports go to development_tools/ root)
  - `development_tools/shared/` - Renamed from `services/` (shared infrastructure, utilities like `file_rotation.py`, `tool_guide.py`)
- [OK] Created package `__init__.py` files in all new directories
- [OK] Updated all imports and references throughout codebase
- [OK] Moved all tools to their respective domain directories
- [OK] Updated output file organization (domain-specific JSON files in their respective directories, consolidated reports in development_tools/ root)
- [OK] Updated `SCRIPT_REGISTRY` in `operations.py` with new paths
- [OK] Updated `tool_metadata.py` with all new paths
- [OK] Updated documentation guides with new structure
- [OK] Fixed all path calculations (`.parent.parent` → `.parent.parent.parent` for subdirectories)

#### Milestone M7.3 - Tool Gap & Future Additions **COMPLETED (2025-12-01)**
- [OK] Directory structure supports future additions (domain-based organization makes it clear where new tools belong)
- [OK] Identified desired categories across 6 domains (documentation, code quality, testing, config/environment, AI/prompt, integration)
- [OK] Recorded missing tools and planned improvements in `DEVELOPMENT_TOOLS_GUIDE.md` section 5 and `AI_DEVELOPMENT_TOOLS_GUIDE.md` section 5

**Gap Analysis Summary:**

**Documentation Domain (7 gaps identified):**
- H3 heading sync validation (currently only H2)
- Markdown link validation (existence, anchor validation)
- Cross-reference accuracy (section numbers, existence verification)
- Example marking standards validation
- Metadata standards adherence
- Markdown anchor integration in cross-references
- Enhanced overlap detection (currently basic)

**Code Quality Domain (6 gaps identified):**
- Type hint coverage analysis
- Docstring quality assessment (beyond presence/absence)
- Code duplication detection
- Complexity trend analysis
- Security pattern analysis
- Performance anti-pattern detection

**Testing Domain (6 gaps identified):**
- Test marker validation (scripts exist, need integration)
- Test isolation verification
- Test coverage gap analysis
- Test naming convention compliance
- Integration test gap analysis
- Test fixture organization analysis

**Configuration & Environment Domain (5 gaps identified):**
- Environment health checks
- Config value validation (beyond drift)
- Environment variable usage analysis
- Dependency version conflict detection
- Path normalization validation

**AI & Prompt Domain (3 gaps identified):**
- Prompt validation (structure, completeness)
- Prompt template consistency checking
- Response quality metrics (beyond structural)

**Integration & Workflow Domain (2 gaps identified):**
- End-to-end workflow validation
- Integration point analysis

**Total:** 29 gaps identified across 6 domains, with 25+ potential new tools documented. All findings recorded in both guides with priority classifications (High/Medium/Low).

#### Milestone M7.4 - Decompose Multi-Responsibility Tools **COMPLETED (2025-12-02)**

**Goal:** Break down tools that combine analysis, generation, and fixing into separate, focused tools following the naming conventions (analyze_*, generate_*, fix_*). Also decompose tools that are too broad/complex with multiple distinct concerns.

**Status:** All three batches completed. Batch 1 (Legacy Tools), Batch 2 (Documentation Tools), and Batch 3 (Remaining Tools) have been successfully decomposed. All tools are now modular, testable, and follow the established naming conventions.

**Tools to decompose:**

1. **`legacy/fix_legacy_references.py`** - Currently combines:
   - Analysis: `scan_for_legacy_references()`, `analyze_file_content()`, `find_all_references()`, `verify_removal_readiness()`
   - Report generation: `generate_cleanup_report()`
   - Fixing: `cleanup_legacy_references()`
   
   **Decomposition target:**
   - `legacy/analyze_legacy_references.py` - Analysis only (scan, find, verify)
   - `legacy/generate_legacy_reference_report.py` - Report generation from analysis results
   - `legacy/fix_legacy_references.py` - Cleanup operations only (uses analysis results)

2. **`docs/analyze_documentation_sync.py`** (1539 lines) - Very large, combines multiple distinct concerns:
   - Paired documentation checking (`check_paired_documentation()`)
   - Path drift analysis (`check_path_drift()`)
   - ASCII compliance checking (`check_ascii_compliance()`)
   - Heading numbering validation (`check_heading_numbering()`)
   - Missing address detection (`check_missing_addresses()`)
   - Unconverted link detection (`check_unconverted_links()`)
   - Directory tree generation (`generate_directory_tree()`)
   
   **Decomposition target:**
   - `docs/analyze_documentation_sync.py` - Keep only paired doc sync checking (H2/H3 heading sync)
   - `docs/analyze_path_drift.py` - Path drift analysis only
   - `docs/analyze_ascii_compliance.py` - ASCII compliance checking
   - `docs/analyze_heading_numbering.py` - Heading numbering validation
   - `docs/analyze_missing_addresses.py` - Missing address detection
   - `docs/analyze_unconverted_links.py` - Unconverted link detection
   - `docs/generate_directory_tree.py` - Directory tree generation

3. **`docs/fix_documentation.py`** - Combines 4 distinct fix operations:
   - Address insertion (`fix_add_addresses()`)
   - ASCII fixes (`fix_ascii()`)
   - Heading numbering (`fix_number_headings()`)
   - Link conversion (`fix_convert_links()`)
   
   **Decomposition target:**
   - `docs/fix_documentation_addresses.py` - Address insertion only
   - `docs/fix_documentation_ascii.py` - ASCII fixes only
   - `docs/fix_documentation_headings.py` - Heading numbering only
   - `docs/fix_documentation_links.py` - Link conversion only
   - Keep `docs/fix_documentation.py` as a dispatcher that calls all fixers (or remove if not needed)

4. **`functions/generate_function_registry.py`** (1475+ lines) - Very large, combines:
   - Function/class discovery (`extract_functions_from_file()`, `extract_classes_from_file()`, `scan_all_python_files()`)
   - Pattern analysis (`analyze_function_patterns()`)
   - Multiple report section generation (patterns, entry points, operations, complexity, organization, communication)
   - Registry content generation
   
   **Decomposition target:**
   - `functions/analyze_functions.py` - Already exists, but may need to extract discovery logic
   - `functions/analyze_function_patterns.py` - Pattern analysis only
   - `functions/generate_function_registry.py` - Registry generation only (uses analysis results)
   - Consider separate generators for different report sections if they become too complex

5. **`error_handling/analyze_error_handling.py`** (1016 lines) - Combines:
   - Error handling analysis (`analyze_file()`, `_analyze_function()`, `_analyze_class()`)
   - Recommendation generation (`_generate_recommendations()`)
   - Results aggregation and reporting
   
   **Decomposition target:**
   - `error_handling/analyze_error_handling.py` - Keep analysis only
   - `error_handling/generate_error_handling_report.py` - Report generation from analysis results
   - `error_handling/generate_error_handling_recommendations.py` - Recommendation generation

6. **`tests/generate_test_coverage.py`** (1371+ lines) - Combines:
   - Coverage execution (pytest runs)
   - Coverage parsing and analysis
   - Report generation (JSON, HTML)
   - Artifact management (rotation, archiving)
   - Coverage plan updates
   
   **Decomposition target:**
   - `tests/analyze_test_coverage.py` - Coverage analysis and parsing
   - `tests/generate_test_coverage_reports.py` - Report generation (JSON, HTML)
   - `tests/generate_test_coverage.py` - Keep as orchestrator that runs analysis and generation
   - Consider separate artifact management if it becomes complex

**Implementation steps:**
- [OK] Identify all functions in each tool and categorize by responsibility
- [OK] Extract analysis functions into separate `analyze_*.py` tools
- [OK] Extract report generation into separate `generate_*_report.py` tools
- [OK] Refactor fix tools to use analysis results (no analysis logic)
- [OK] Update CLI commands and operations.py to support separate tools
- [OK] Update tests to cover each decomposed tool independently
- [OK] Update documentation and tool_metadata.py with new tool entries

**Batch 1 (Legacy Tools) - COMPLETED:**
- [OK] Created `legacy/analyze_legacy_references.py` with analysis methods
- [OK] Created `legacy/generate_legacy_reference_report.py` with report generation
- [OK] Refactored `legacy/fix_legacy_references.py` to only contain fixing logic
- [OK] Updated `operations.py` and `tool_metadata.py` with new tool entries
- [OK] Updated tests to use decomposed tools

**Batch 2 (Documentation Tools) - COMPLETED:**
- [OK] Created 7 new analysis tools for `analyze_documentation_sync.py` decomposition
- [OK] Refactored `analyze_documentation_sync.py` to only handle paired doc sync
- [OK] Updated `operations.py` to call all decomposed documentation analysis tools
- [OK] Updated `tool_metadata.py` with all new tool entries
- [OK] Updated tests to use decomposed tools

**Batch 3 (Remaining Tools) - COMPLETED:**
- [OK] Enhanced `functions/analyze_functions.py` with discovery logic from `generate_function_registry.py`
- [OK] Created `functions/analyze_function_patterns.py` with pattern analysis
- [OK] Refactored `functions/generate_function_registry.py` to use analysis results
- [OK] Refactored `error_handling/analyze_error_handling.py` to keep only analysis methods
- [OK] Created `error_handling/generate_error_handling_report.py` for report generation
- [OK] Created `error_handling/generate_error_handling_recommendations.py` for recommendations
- [OK] Created `tests/analyze_test_coverage.py` for coverage parsing and analysis
- [OK] Created `tests/generate_test_coverage_reports.py` for report generation
- [OK] Refactored `tests/generate_test_coverage.py` to be an orchestrator
- [OK] Updated `operations.py` and `tool_metadata.py` with all new tool entries
- [OK] Updated tests to use decomposed tools
- [OK] Fixed all test failures and warnings

**Benefits:**
- Clearer separation of concerns
- Tools can be used independently
- Better testability (test analysis without fixing/generating)
- Follows established naming conventions
- More modular and reusable
- Easier to maintain (smaller, focused files)

**Cross-Cutting Tasks - COMPLETED:**
- [OK] Ran full test suite to verify no regressions (all tests passing)
- [OK] Updated `SCRIPT_REGISTRY` in `operations.py` with all new tool entries
- [OK] Updated `tool_metadata.py` with tier, trust, portability for all new tools
- [OK] Updated `AI_DEVELOPMENT_TOOLS_GUIDE.md` and `DEVELOPMENT_TOOLS_GUIDE.md` with new tool catalog entries
- [OK] Updated `AI_DEV_TOOLS_IMPROVEMENT_PLAN.md` to mark M7.4 progress (this section)
- [OK] Verified all CLI commands still work correctly
- [OK] Verified audit workflows function correctly (integration tested)

**Success Criteria - ALL MET:**
- [OK] All 6 original tools decomposed into focused tools (20+ new focused tools created)
- [OK] All existing functionality preserved (backward compatibility maintained)
- [OK] All CLI commands work correctly (tested and verified)
- [OK] All tests pass (full test suite passing, warnings addressed)
- [OK] All documentation updated (guides, metadata, and improvement plan)
- [OK] Tool metadata registry complete (all new tools registered)
- [OK] No regressions in audit workflows (integration verified)
- [OK] Clear separation of concerns (analyze vs generate vs fix) achieved

**Final Status:** Milestone M7.4 fully completed on 2025-12-02. All 6 original multi-responsibility tools have been successfully decomposed into 20+ focused, single-responsibility tools following the established naming conventions. All functionality preserved, tests passing, documentation updated, and audit workflows verified.

**Additional Decomposition (2025-12-02):**
- **`imports/generate_module_dependencies.py`** (1418 lines) - Decomposed after M7.4 completion:
  - **Before**: Combined import extraction, dependency analysis, pattern analysis, purpose inference, and content generation
  - **After**:
    - `imports/analyze_module_imports.py` (new) - Import extraction, scanning, reverse dependencies, dependency changes, purpose inference, import formatting
    - `imports/analyze_dependency_patterns.py` (new) - Dependency pattern analysis, circular dependency detection, risk area detection, critical dependency finding
    - `imports/generate_module_dependencies.py` (refactored) - Orchestrates the new analysis tools and focuses solely on content generation and manual enhancement preservation
  - **Updated**: `imports/analyze_module_dependencies.py` now uses `ModuleImportAnalyzer` from `analyze_module_imports.py` instead of duplicating code
  - **Fixed**: All import paths in `imports/` directory corrected (`from . import config` → `from .. import config`)
  - **Status**: All tests passing, all references updated, functionality preserved

---

### Phase 8 - Create New Tools to Fill Identified Gaps **PENDING**

**Goal:** Implement new tools based on gaps identified in Phase 7.3 to expand automated analysis, recommendations, and fixes. Also identify and create tools for entirely missing categories.

**Status:** Not started. Depends on completion of Phase 7.3 gap analysis.

#### Missing Tool Categories

**Current categories:**
- `ai_work/` - AI work validation
- `config/` - Configuration validation
- `docs/` - Documentation analysis and sync
- `error_handling/` - Error handling coverage
- `functions/` - Function discovery and registry
- `imports/` - Import checking and dependencies
- `legacy/` - Legacy cleanup
- `reports/` - Consolidated reports
- `shared/` - Shared infrastructure
- `tests/` - Test coverage metrics

**Missing categories that could benefit from tooling:**

1. **`logging/`** - Logging analysis and validation
   - Analyze logger usage patterns (component loggers vs root logger)
   - Validate log level appropriateness
   - Check for logging anti-patterns (print statements, debug in production)
   - Analyze log message quality and consistency
   - Validate logging configuration
   - **Potential tools:**
     - `logging/analyze_logger_usage.py` - Logger usage patterns
     - `logging/analyze_log_levels.py` - Log level appropriateness
     - `logging/analyze_logging_anti_patterns.py` - Anti-pattern detection
     - `logging/validate_logging_config.py` - Config validation

2. **`performance/`** - Performance analysis
   - Detect performance anti-patterns (N+1 queries, inefficient loops)
   - Analyze function complexity trends
   - Identify potential bottlenecks
   - Memory usage analysis
   - **Potential tools:**
     - `performance/analyze_performance_anti_patterns.py` - Anti-pattern detection
     - `performance/analyze_complexity_trends.py` - Complexity tracking
     - `performance/analyze_bottlenecks.py` - Bottleneck identification

3. **`security/`** - Security analysis
   - Security pattern validation (input validation, sensitive data handling)
   - Vulnerability detection
   - Secret/key exposure detection
   - **Potential tools:**
     - `security/analyze_security_patterns.py` - Security best practices
     - `security/analyze_secrets.py` - Secret exposure detection
     - `security/analyze_input_validation.py` - Input validation checks

4. **`dependencies/`** - Dependency management (beyond imports)
   - Dependency version conflict detection
   - Outdated dependency analysis
   - Security vulnerability scanning (dependencies)
   - Dependency graph visualization
   - **Potential tools:**
     - `dependencies/analyze_dependency_conflicts.py` - Version conflicts
     - `dependencies/analyze_outdated_dependencies.py` - Outdated packages
     - `dependencies/analyze_dependency_vulnerabilities.py` - Security vulnerabilities
     - `dependencies/generate_dependency_graph.py` - Visualization

5. **`refactoring/`** - Refactoring assistance
   - Code smell detection
   - Refactoring opportunity identification
   - Code duplication detection (could go here or in functions/)
   - **Potential tools:**
     - `refactoring/analyze_code_smells.py` - Code smell detection
     - `refactoring/analyze_refactoring_opportunities.py` - Opportunity identification
     - `refactoring/analyze_code_duplication.py` - Duplication detection

6. **`standards/`** - Code standards and style enforcement
   - Coding standard compliance (beyond what linters do)
   - Project-specific pattern enforcement
   - Naming convention validation
   - **Potential tools:**
     - `standards/analyze_coding_standards.py` - Standards compliance
     - `standards/analyze_naming_conventions.py` - Naming validation
     - `standards/enforce_project_patterns.py` - Pattern enforcement

7. **`integration/`** - Integration testing and validation
   - Integration point analysis
   - API contract validation
   - End-to-end workflow validation
   - **Potential tools:**
     - `integration/analyze_integration_points.py` - Integration mapping
     - `integration/validate_api_contracts.py` - Contract validation
     - `integration/validate_workflows.py` - Workflow validation

8. **`deployment/`** - Deployment and CI/CD
   - Deployment readiness checks
   - CI/CD configuration validation
   - Environment consistency checks
   - **Potential tools:**
     - `deployment/analyze_deployment_readiness.py` - Readiness checks
     - `deployment/validate_ci_config.py` - CI config validation
     - `deployment/analyze_environment_consistency.py` - Environment checks

**Note:** Some of these categories might overlap with existing categories (e.g., `config/analyze_environment_health.py` could be in `deployment/`). The categorization should be based on primary purpose and usage context.

**Implementation approach:**
- Prioritize gaps by value and effort
- Create tools following established patterns (analyze_*, generate_*, fix_*)
- Integrate into audit workflow where appropriate
- Add tests using synthetic fixture project
- Update tool_metadata.py and documentation

**Potential tool categories (from Phase 7.3 gap analysis):**

**Documentation Domain:**
- [ ] `docs/analyze_link_validity.py` - Validate markdown links point to existing files/sections
- [ ] `docs/analyze_cross_references.py` - Verify cross-references include section numbers and exist
- [ ] `docs/analyze_metadata_compliance.py` - Check metadata format adherence
- [ ] `docs/analyze_example_markers.py` - Validate example marking standards
- [ ] `docs/fix_cross_references.py` - Auto-fix cross-references with section numbers/anchors
- [ ] Enhance `docs/analyze_documentation_sync.py` to check H3 heading sync

**Code Quality Domain:**
- [ ] `functions/analyze_complexity_trends.py` - Track complexity changes over time
- [ ] `functions/analyze_type_hints.py` - Type hint coverage and quality
- [ ] `functions/analyze_docstring_quality.py` - Docstring completeness and style
- [ ] `functions/analyze_code_duplication.py` - Detect duplicate code patterns
- [ ] `functions/analyze_security_patterns.py` - Security best practices validation

**Testing Domain:**
- [ ] `tests/analyze_test_markers.py` - Validate test categorization markers (integrate existing scripts)
- [ ] `tests/analyze_test_isolation.py` - Verify tests don't have side effects
- [ ] `tests/analyze_test_coverage_gaps.py` - Identify untested code paths
- [ ] `tests/generate_test_suggestions.py` - Suggest tests for uncovered code

**Configuration & Environment Domain:**
- [ ] `config/analyze_environment_health.py` - Check environment setup and health
- [ ] `config/analyze_env_variables.py` - Track environment variable usage
- [ ] `config/validate_config_values.py` - Validate config value ranges and types
- [ ] `config/analyze_dependency_conflicts.py` - Detect dependency version issues

**AI & Prompt Domain:**
- [ ] `ai_work/analyze_prompt_quality.py` - Validate prompt structure and completeness
- [ ] `ai_work/analyze_prompt_consistency.py` - Check prompt template consistency
- [ ] `ai_work/analyze_response_quality.py` - Metrics beyond structural validation

**Integration & Workflow Domain:**
- [ ] `reports/analyze_workflow_integrity.py` - Validate end-to-end workflows
- [ ] `reports/analyze_integration_points.py` - Map and validate integration points

**Milestones:**
- M8.1 - Prioritize gaps and create implementation plan
- M8.2 - Implement high-priority documentation tools
- M8.3 - Implement code quality analysis tools
- M8.4 - Implement testing domain tools
- M8.5 - Implement configuration and environment tools
- M8.6 - Implement AI/prompt analysis tools
- M8.7 - Integrate new tools into audit workflow
- M8.8 - Add comprehensive tests for all new tools

---

**Progress Summary:**
- [OK] **Phase 1 COMPLETED (2025-11-25)**: Tiering system fully implemented, documentation split and aligned, all path references updated
- [OK] **Phase 2 COMPLETED (2025-11-25)**: Core infrastructure stabilized with test coverage (77 tests), consistent logging, and normalized error handling
- [OK] **Phase 3 COMPLETED (2025-11-26)**: Core analysis tools hardened with comprehensive test coverage (55 tests), synthetic fixture project created, all five tools now trustworthy
- [OK] **Phase 4 COMPLETED (2025-11-27)**: Experimental tools moved to dedicated directory, Tier-2 tools reviewed and documented, dev tools coverage tracking added, supporting tools regression tests created (6 tests for `quick_status`, `system_signals`, `file_rotation`)
- [OK] **Phase 5 COMPLETED (2025-11-27)**: Standard audit recipe added to workflow guide, session starter updated with dev tools routing, all documentation alignment milestones complete
- [OK] **Phase 6 COMPLETED (2025-11-28)**: All checklists completed - all 14 supporting and experimental tools made portable via external configuration (`development_tools_config.json`). All tools changed from `mhm-specific` to `portable` portability markers. Config getter functions added to `config.py`, config example file updated with all new sections.
- [OK] **Phase 7**: M7.1 completed (2025-12-01) - all naming conventions applied, both initial and second batch of renames complete, all references updated. M7.2 completed (directory reorganization done). M7.3 completed (2025-12-01) - tool gap analysis documented, 29 gaps identified across 6 domains, findings recorded in both guides. M7.4 completed (2025-12-02) - all three batches of tool decomposition completed (Legacy Tools, Documentation Tools, Remaining Tools). All 6 original multi-responsibility tools decomposed into 20+ focused tools. All tools now follow single-responsibility principle with clear separation of concerns. All cross-cutting tasks and success criteria met. Full test suite passing, documentation updated, audit workflows verified.

This roadmap is intentionally incremental. You do **not** need to implement every milestone at once.  
Phases 1-3 (tiering + core infrastructure + core analysis tools) are complete. Next focus on Phase 4 (clarify supporting vs experimental tools) or Phase 5 (UX and documentation alignment), then expand as time and energy allow.

---

This document can now serve as the authoritative basis for improving or restructuring the AI development tools ecosystem.