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

- A unified dispatcher (`development_tools/ai_tools_runner.py`)
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
- Write operations are high‑risk without strong safeguards.
- ~~No formal "tiering"~~ **RESOLVED (2025-11-25)**: Tiering system implemented via `development_tools/services/tool_metadata.py` with tier markers in all tool modules and CLI help grouping.

**Summary:**  
Good bones, uneven execution. High potential, but needs consolidation, testing, and prioritization.

---

# 2. Per-Tool Breakdown

This section categorizes each tool into “Core,” “Supporting,” or “Experimental” based on reliability, purpose, and completeness.

---

## 2.1 Core Infrastructure (Strong, Foundational)

### `development_tools/config.py`
- Centralizes scan roots, thresholds, audit modes.
- Widely used across tools.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 23 tests in `tests/development_tools/test_config.py` verify key settings and helper functions.

### `development_tools/services/standard_exclusions.py`
- Good design: all tools call `should_exclude_file`.
- Patterns may need tuning but concept is sound.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 21 tests in `tests/development_tools/test_standard_exclusions.py` verify exclusion patterns work correctly.

### `development_tools/services/constants.py`
- Holds doc pairing metadata and predefined doc lists.
- Needs regular updates to avoid drift.
- ✅ **HAS VALIDATION TESTS (Phase 2)**: 25 tests in `tests/development_tools/test_constants.py` verify paths exist and helper functions work correctly.

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

### `development_tools/ai_tools_runner.py`
- Central dispatcher with command registry.
- Good entry point; ties the system together.
- ✅ **HAS CLI SMOKE TESTS (Phase 2)**: 7 tests in `tests/development_tools/test_ai_tools_runner.py` verify command execution and exit codes.
- ✅ **HAS ENHANCED ERROR HANDLING (Phase 2)**: Try/except blocks with proper logging and exit code propagation.

### `development_tools/services/operations.py`
- Implements core logic for each command.
- Has risk of becoming a "god module."
- Should eventually be split by domain (audit, docs, legacy, coverage).
- ✅ **HAS NORMALIZED LOGGING (Phase 2)**: Consistent "Starting..." and "Completed..." logging added to all major operations.

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

### `development_tools/regenerate_coverage_metrics.py`
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

### `development_tools/version_sync.py`
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

### `development_tools/function_discovery.py`
- Parses function signatures, handlers, tests.
- Forms basis for several other tools.

### `development_tools/auto_document_functions.py`
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
- ✅ Tier markers added to all tool modules (`# TOOL_TIER` and `# TOOL_PORTABILITY` headers)
- ✅ `development_tools/services/tool_metadata.py` created as single source of truth for tier, portability, trust, and command metadata
- ✅ CLI help output groups commands by tier (Core, Supporting, Experimental) with warnings
- ✅ Documentation guides updated with tier information and trust levels
- ✅ Directory renamed from `ai_development_tools/` to `development_tools/` for clarity

### **2. ~~No tests for tooling~~** **RESOLVED (2025-11-26)**
- ✅ Basic sanity tests added for core infrastructure (`development_tools/config.py`, `development_tools/services/standard_exclusions.py`, `development_tools/services/constants.py`)
- ✅ CLI smoke tests added for `development_tools/ai_tools_runner.py`
- ✅ Logging and error handling normalized in `development_tools/services/operations.py` and `development_tools/ai_tools_runner.py`
- ✅ Comprehensive tests added for all five core analysis tools (Phase 3):
  - `development_tools/documentation_sync_checker.py` (12 tests)
  - `development_tools/generate_function_registry.py` (12 tests)
  - `development_tools/generate_module_dependencies.py` (11 tests)
  - `development_tools/legacy_reference_cleanup.py` (10 tests)
  - `development_tools/regenerate_coverage_metrics.py` (10 tests)
- ✅ Synthetic fixture project created at `tests/fixtures/development_tools_demo/` for isolated testing
- ✅ Total test coverage: 132 tests across all development tools

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

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN.md` (this file)  
> **Audience**: Project maintainers and developers  
> **Purpose**: Provide a practical, phased roadmap with milestones to stabilize, test, and rationalize the AI development tools.  
> **Style**: Direct, technical, and concise.

This roadmap assumes the following tiering for the AI development tools:

- **Tier 1 – Core**
  - `development_tools/ai_tools_runner.py`, `development_tools/services/operations.py`, `development_tools/config.py`, `development_tools/services/standard_exclusions.py`, `development_tools/services/constants.py`, `development_tools/services/common.py`
  - `development_tools/documentation_sync_checker.py`, `development_tools/generate_function_registry.py`, `development_tools/generate_module_dependencies.py`
  - `development_tools/legacy_reference_cleanup.py`, `development_tools/regenerate_coverage_metrics.py`
  - `development_tools/error_handling_coverage.py`, `development_tools/function_discovery.py`

- **Tier 2 – Supporting**
  - `development_tools/analyze_documentation.py`, `development_tools/audit_function_registry.py`, `development_tools/audit_module_dependencies.py`, `development_tools/audit_package_exports.py`
  - `development_tools/config_validator.py`, `development_tools/validate_ai_work.py`, `development_tools/unused_imports_checker.py`, `development_tools/quick_status.py`, `development_tools/system_signals.py`
  - `development_tools/decision_support.py`, `development_tools/file_rotation.py`, `development_tools/tool_guide.py`

- **Tier 3 – Experimental**
  - `development_tools/version_sync.py`, `development_tools/auto_document_functions.py`

---

### Phase 1 – Make the Landscape Explicit **COMPLETED (2025-11-25)**

**Goal:** Turn the informal understanding of "which tools matter" into explicit structure and expectations.

**Status:** All milestones completed. Tiering system fully implemented and integrated into CLI, documentation, and codebase.

#### Milestone M1.1 – Add Tier Markers **COMPLETED**

- ✅ Created `development_tools/services/tool_metadata.py` as authoritative registry for all tool metadata (tier, portability, trust, description, command name)
- ✅ Added `# TOOL_TIER: core | supporting | experimental` headers to all tool modules
- ✅ Added `# TOOL_PORTABILITY: portable | mhm-specific` headers to all tool modules
- ✅ Removed BOM characters discovered during header injection sweep
- ✅ All 25+ tools now have consistent tier and portability markers

#### Milestone M1.2 – Reflect Tiering in Help Output **COMPLETED**

- ✅ Updated `development_tools/services/common.py` to build command groupings from `development_tools/services/tool_metadata.py` (single source of truth)
- ✅ Updated `development_tools/ai_tools_runner.py` to display commands grouped by tier in help output
- ✅ Updated `development_tools/services/operations.py` to use tier-based grouping for help display
- ✅ Enhanced `development_tools/tool_guide.py` to print tier overview sourced from `development_tools/services/tool_metadata.py`
- ✅ Help output now groups commands under **Core**, **Supporting**, and **Experimental** headings with explicit warnings

#### Milestone M1.3 – Document "Partial / Experimental" Tools **COMPLETED**

- ✅ Split documentation into paired guides:
  - `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` (AI-facing, routing-focused)
  - `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` (human-facing, detailed catalog)
- ✅ Both guides include complete tool catalog with tier, trust level, portability, and notes
- ✅ Explicitly flagged partial/incomplete tools (e.g. `development_tools/validate_ai_work.py`)
- ✅ Explicitly flagged advisory-only tools (e.g. `development_tools/decision_support.py`)
- ✅ Explicitly flagged experimental/fragile tools (e.g. `development_tools/version_sync.py`, `development_tools/auto_document_functions.py`)
- ✅ Aligned both guides with documentation standards (metadata blocks, identical H2 headings)
- ✅ Updated all path references from `ai_development_tools/` to `development_tools/` throughout codebase
- ✅ Added guides to `DEFAULT_DOCS`, `PAIRED_DOCS`, directory tree, README, and other doc listings

This does not fix code, but it stops you from accidentally trusting the wrong tool.

**Reference list for documentation and CLI alignment**

- Partial / advisory (Supporting tier):
  - `development_tools/analyze_documentation.py` — overlap/corruption detection with known edge cases.
  - `development_tools/audit_function_registry.py` — validates registry output but depends on fixture freshness.
  - `development_tools/audit_module_dependencies.py` / `development_tools/audit_package_exports.py` — verification helpers that still lack regression tests.
  - `development_tools/config_validator.py` — drift detector that needs broader coverage.
  - `development_tools/validate_ai_work.py` — structural heuristics only; do not treat as authoritative.
  - `development_tools/unused_imports_checker.py` — noisy on generated files; review manually.
  - `development_tools/quick_status.py` / `development_tools/system_signals.py` — cached views that require a recent audit.
  - `development_tools/decision_support.py` — advisory scoring, not a blocker.
- Experimental (prototype tier):
  - `development_tools/version_sync.py` — fragile heuristic updates; run only with backup/approval.
  - `development_tools/auto_document_functions.py` — generates docstrings automatically; high-risk edits.

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
- ✅ Fixed path mismatch in constants.py (`tests/AI_FUNCTIONALITY_TEST_GUIDE.md` → `tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md`) (archived reference - file no longer exists)

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

- ✅ Added consistent logging to major operations in `development_tools/services/operations.py`:
  - "Starting {operation_name}..." at operation start
  - "Completed {operation_name} successfully!" or "Completed {operation_name} with errors!" at completion
  - Applied to: `run_audit()`, `run_docs()`, `run_validate()`, `run_config()`, `run_status()`, `run_documentation_sync()`, `run_coverage_regeneration()`, `run_legacy_cleanup()`, `run_system_signals()`, `run_unused_imports_report()`
- ✅ Enhanced error handling in `ai_tools_runner.py`:
  - Added try/except around command execution to catch and log exceptions
  - Proper exit code propagation (0 for success, 1 for failures, 2 for usage errors)
- ✅ All command handlers return sensible exit codes consistently

**Result:** The infrastructure is now predictable and diagnosable. Tests provide regression protection, and logging makes operations traceable.

---

### Phase 3 – Harden the Core Analysis Tools (Tier 1+) **COMPLETED (2025-11-26)**

**Goal:** Add comprehensive test coverage for the five core analysis tools to make them trustworthy and provide regression protection.

**Status:** All milestones completed. Core analysis tools now have robust test coverage using a synthetic fixture project.

#### Milestone M3.1 – Create Synthetic Fixture Project **COMPLETED**

- ✅ Created `tests/fixtures/development_tools_demo/` with:
  - `tests/fixtures/development_tools_demo/demo_module.py` and `tests/fixtures/development_tools_demo/demo_module2.py` with functions, classes, and imports
  - `tests/fixtures/development_tools_demo/demo_tests.py` for coverage runs
  - `tests/fixtures/development_tools_demo/legacy_code.py` with known legacy patterns and markers
  - `docs/` directory with paired documentation (synced, mismatched, standalone cases)
  - `README.md` documenting the fixture structure
- ✅ Fixture provides controlled environment for testing without affecting main codebase

#### Milestone M3.2 – Tests for `development_tools/documentation_sync_checker.py` **COMPLETED**

- ✅ Created `tests/development_tools/test_documentation_sync_checker.py` with 12 tests:
  - Perfectly synced docs return no errors
  - Mismatched H2 headings are flagged
  - Missing files are detected
  - Path drift validation
  - ASCII compliance checks
  - Heading numbering validation
  - Full integration test
- ✅ Tests verify doc-sync's pass/fail signals are reliable

#### Milestone M3.3 – Tests for `development_tools/generate_function_registry.py` **COMPLETED**

- ✅ Created `tests/development_tools/test_generate_function_registry.py` with 12 tests:
  - Function and class extraction from files
  - Handler and test function detection
  - File scanning with exclusions
  - Content generation and categorization
  - File writing operations
- ✅ Tests verify registry generation accuracy and categorization

#### Milestone M3.4 – Tests for `development_tools/generate_module_dependencies.py` **COMPLETED**

- ✅ Created `tests/development_tools/test_generate_module_dependencies.py` with 11 tests:
  - Import extraction (standard library, third-party, local)
  - Reverse dependency finding
  - Content generation structure
  - Manual enhancement preservation
  - Dependency change analysis
  - Module purpose inference
- ✅ Tests verify dependency graph accuracy

#### Milestone M3.5 – Safe Legacy Cleanup Tests **COMPLETED**

- ✅ Created `tests/development_tools/test_legacy_reference_cleanup.py` with 10 tests (for `development_tools/legacy_reference_cleanup.py`):
  - Legacy marker scanning
  - Preserve file handling
  - Reference finding for specific items
  - Removal readiness verification
  - Dry-run and actual cleanup operations
  - Report generation
  - File exclusion handling
  - Replacement mappings
- ✅ Fixed `should_skip_file` to use relative paths for proper exclusion checking
- ✅ Added class definition pattern to `find_all_references` for complete detection
- ✅ Tests verify safe cleanup operations with proper isolation

#### Milestone M3.6 – Coverage Regeneration Tests **COMPLETED**

- ✅ Created `tests/development_tools/test_regenerate_coverage_metrics.py` with 10 tests (for `development_tools/regenerate_coverage_metrics.py`):
  - Coverage output parsing
  - Overall coverage extraction
  - Module categorization by coverage
  - Coverage summary generation
  - Pytest execution integration
  - Coverage path configuration
  - Shard cleanup
  - Coverage plan updates
- ✅ Tests verify coverage regeneration accuracy and artifact handling

**Result:** All five core analysis tools now have comprehensive test coverage (55+ tests total). Tests use shared fixtures in `tests/development_tools/conftest.py` and the synthetic fixture project for isolation. The tools are now reasonably trustworthy with regression protection.

---

### Phase 4 – Clarify Supporting vs Experimental Tools

**Goal:** Reduce cognitive noise and avoid accidental reliance on fragile scripts.

### Milestone M4.1 – Move Experimental Tools

- Create `development_tools/experimental/`.
- Move:
  - `development_tools/version_sync.py`
  - `development_tools/auto_document_functions.py`
- Update runner/help so they are clearly marked or only reachable via explicit flags.

#### Milestone M4.2 – Decide Fate of Each Tier-2 Tool

For each of:

- `development_tools/analyze_documentation.py`
- `development_tools/audit_function_registry.py`
- `development_tools/audit_module_dependencies.py`
- `development_tools/audit_package_exports.py`
- `development_tools/config_validator.py`
- `development_tools/validate_ai_work.py`
- `development_tools/unused_imports_checker.py`
- `development_tools/quick_status.py`
- `development_tools/system_signals.py`
- `development_tools/decision_support.py`
- `development_tools/file_rotation.py`
- `development_tools/tool_guide.py`

Decide:
- **Promote to Tier 1:** worth robust tests and core support, or
- **Keep as Tier 2:** useful but non-critical, or
- **Deprecate / Freeze:** rarely used or more confusing than helpful.

You do not need full test coverage here immediately; priority is clarity and reduced accidental use.

#### Milestone M4.3 – Test Coverage Metrics for Development Tools

- Add coverage metrics tracking for the development tools themselves
- Generate coverage reports specifically for `development_tools/` directory
- Integrate into `audit --full` workflow
- Track coverage trends over time
- **Note**: Valuable for Phase 5+ but can be added in Phase 4 if time permits

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

#### Milestone M5.2 – Standard Audit Recipe in `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`

Add a short section describing when to run:

- `development_tools/ai_tools_runner.py audit` (day-to-day checks).
- `development_tools/ai_tools_runner.py audit --full` (pre-merge / pre-release checks).
- `development_tools/ai_tools_runner.py doc-sync` and `development_tools/ai_tools_runner.py docs` (doc work).

#### Milestone M5.3 – Update `ai_development_docs/AI_SESSION_STARTER.md`

- When the user’s task touches dev tools, route:
  - First to `AI_DEVELOPMENT_TOOLS_GUIDE.md`.
  - Then to the correct tools by tier and purpose.

Result: the dev tools ecosystem becomes something you and future collaborators can reason about and trust.

---

### Phase 6 – Portability Roadmap **ADDED (2025-11-25)**

**Goal:** Track every mhm-specific dependency and define concrete work needed to make tools portable.

**Status:** Roadmap defined and integrated into improvement plan. Per-tool portability checklist created for future work.

#### Core Tool Checklist
- `development_tools/ai_tools_runner.py` — expose command registry + config paths via CLI arguments so it can point at any project root.
- `development_tools/services/operations.py` — split command implementations from MHM-specific behaviors (Discord, account files) so a thin adapter can be swapped in.
- `development_tools/config.py` — move default paths (docs, logs, data) into an external config file that can be overridden per environment.
- `development_tools/services/standard_exclusions.py` — read exclusions from config/constants rather than hardcoding MHM directories.
- `development_tools/services/constants.py` — relocate paired-doc metadata into a data file so non-MHM repos can supply their own doc lists.
- `development_tools/documentation_sync_checker.py` — parameterize the doc root(s) and metadata schema instead of assuming the MHM structure.
- `development_tools/generate_function_registry.py` / `development_tools/function_discovery.py` — make scan roots and filters configurable; rely on passed-in include/exclude patterns.
- `development_tools/generate_module_dependencies.py` — let callers provide module prefixes to treat as "local" vs "external".
- `development_tools/legacy_reference_cleanup.py` — treat LEGACY tokens and log locations as inputs so other projects can define their own markers.
- `development_tools/regenerate_coverage_metrics.py` — accept pytest command, coverage config, and artifact directories as arguments.
- `development_tools/error_handling_coverage.py` — read decorator names and exception base classes from config, not MHM-specific modules.

#### Supporting Tool Checklist
- `development_tools/analyze_documentation.py` — parameterize the heading/metadata schema and let callers provide ignore rules.
- `development_tools/audit_function_registry.py`, `development_tools/audit_module_dependencies.py`, `development_tools/audit_package_exports.py` — feed in the "expected" registries via config so tests are reusable elsewhere.
- `development_tools/config_validator.py` — detect settings dynamically based on config schema rather than enumerating MHM-specific keys.
- `development_tools/validate_ai_work.py` — read rule sets from YAML so new projects can define their validation heuristics.
- `development_tools/unused_imports_checker.py` — allow custom ignore patterns and type stub locations.
- `development_tools/quick_status.py`, `development_tools/system_signals.py`, `development_tools/decision_support.py` — provide plugin hooks so data sources (Discord, schedulers, etc.) can be swapped out.
- `development_tools/tool_guide.py` — render guidance based on `development_tools/services/tool_metadata.py` so another repo can simply override the metadata file.
- `development_tools/file_rotation.py` — already portable; confirm it stays dependency-free.

#### Experimental Tool Checklist
- `development_tools/version_sync.py` — read version files + patterns from config; avoid hardcoded MHM file list.
- `development_tools/auto_document_functions.py` — ensure template paths, doc targets, and formatting rules are injectable.

Portable today: `development_tools/services/common.py`, `development_tools/system_signals.py`, and `development_tools/file_rotation.py`—no action needed beyond keeping dependencies minimal.

---

### Phase 7 – Naming & Directory Strategy **ADDED (2025-11-25)**

**Goal:** Make the tool suite predictable by aligning names with actions and grouping related tools.

**Status:** Strategy defined and documented. Naming conventions and directory restructuring approach outlined for future implementation.

#### Milestone M7.1 – Establish Naming Conventions
- Adopt verb-based prefixes (`audit_*`, `generate_*`, `cleanup_*`, `report_*`) or domain-based prefixes (`docs_*`, `coverage_*`, `legacy_*`).
- Update `development_tools/services/tool_metadata.py` with the agreed convention so new contributors can follow it.

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
- ✅ **Phase 2 COMPLETED (2025-11-25)**: Core infrastructure stabilized with test coverage (77 tests), consistent logging, and normalized error handling
- ✅ **Phase 3 COMPLETED (2025-11-26)**: Core analysis tools hardened with comprehensive test coverage (55 tests), synthetic fixture project created, all five tools now trustworthy
- 🔄 **Phase 4-7**: Defined and ready for implementation

This roadmap is intentionally incremental. You do **not** need to implement every milestone at once.  
Phases 1-3 (tiering + core infrastructure + core analysis tools) are complete. Next focus on Phase 4 (clarify supporting vs experimental tools) or Phase 5 (UX and documentation alignment), then expand as time and energy allow.

---

This document can now serve as the authoritative basis for improving or restructuring the AI development tools ecosystem.