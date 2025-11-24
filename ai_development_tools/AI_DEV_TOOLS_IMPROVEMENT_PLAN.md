# AI Development Tools – Current State and Improvement Roadmap

> **File**: `ai_development_tools/AI_DEV_TOOLS_ASSESSMENT.md`
> **Audience**: Project maintainers and developers
> **Purpose**: Provide a detailed assessment of all AI development tools, identifying strengths, weaknesses, fragility, gaps, and a roadmap for improvement.
> **Style**: Direct, technical, and candid.

This document summarizes the current state of the `ai_development_tools` suite based on source review.  
It is intended to guide decisions on tool maintenance, triage, and future enhancements.

---

# 1. Overall State of the AI Development Tools

The `ai_development_tools` directory represents an ambitious and generally well‑structured attempt at creating an internal “analysis and audit platform” for the MHM project. The architecture includes:

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
- No formal “tiering” — everything appears equally official whether robust or prototype.

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
- Needs validation tests but otherwise solid.

### `standard_exclusions.py`
- Good design: all tools call `should_exclude_file`.
- Patterns may need tuning but concept is sound.

### `constants.py`
- Holds doc pairing metadata and predefined doc lists.
- Needs regular updates to avoid drift.

### `common.py`
- Provides consistent CLI patterns and file operations.
- Some tools bypass it; future tools should not.

**Overall:** These modules form a reliable backbone and should be maintained carefully.

---

## 2.2 Runner and Operations Layer

### `ai_tools_runner.py`
- Central dispatcher with command registry.
- Good entry point; ties the system together.
- Needs clearer classification of safe vs heavy vs dangerous commands.

### `operations.py`
- Implements core logic for each command.
- Has risk of becoming a “god module.”
- Should eventually be split by domain (audit, docs, legacy, coverage).

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

### **1. No clear tiering (core vs supporting vs experimental)**
- Everything appears equally “official.”
- Some tools are essential; some are prototypes.
- Leads to confusion and accidental reliance on fragile components.

### **2. No tests for tooling**
- Given the AST parsing, file rewriting, and doc generation, this is risky.
- Even simple regression tests would dramatically increase trustworthiness.

### **3. Risky write operations**
- Tools like legacy cleanup, auto-documentation, coverage regeneration write real files.
- Without strong safeguards, they can corrupt code or docs.

### **4. Conceptual overlap / sprawl**
- Documentation tools overlap; analysis tools overlap; validation tools overlap.
- The audit pipeline needs clearer boundaries and flow.

### **5. No explicit indicator of experimental tools**
- Tools that are incomplete or fragile are not marked as such.
- Easy for a future contributor (or AI collaborator) to misuse them.

---

## 4. AI Development Tools – Implementation Roadmap

> **File**: `ai_development_tools/AI_DEV_TOOLS_ROADMAP.md`
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

### Phase 1 – Make the Landscape Explicit

**Goal:** Turn the informal understanding of “which tools matter” into explicit structure and expectations.

#### Milestone M1.1 – Add Tier Markers

- In each tool module, add a top-of-file comment:
  - `# TOOL_TIER: core`
  - `# TOOL_TIER: supporting`
  - `# TOOL_TIER: experimental`
- Keep this consistent and easy to grep.

#### Milestone M1.2 – Reflect Tiering in Help Output

- Update `ai_tools_runner.py` / `tool_guide.py` to group commands in help:
  - **Core commands**
  - **Supporting commands**
  - **Experimental commands (use with caution)**

#### Milestone M1.3 – Document “Partial / Experimental” Tools

- In `AI_DEV_TOOLS_GUIDE.md` or `AI_DEV_TOOLS_ASSESSMENT.md`, explicitly flag tools that are:
  - Partial/incomplete (e.g. `validate_ai_work.py`).
  - Advisory-only (e.g. `decision_support.py`).
  - Experimental or fragile (e.g. `version_sync.py`, `auto_document_functions.py`).

This does not fix code, but it stops you from accidentally trusting the wrong tool.

---

### Phase 2 – Stabilize Core Infrastructure (Tier 1 Infra)

**Goal:** Make the backbone (runner + infra) solid enough that everything else can lean on it.

#### Milestone M2.1 – Sanity Tests for Config and Exclusions

- Add basic tests for:
  - `config.py`:
    - Key settings exist.
    - Paths used in tests/fixtures are valid.
  - `standard_exclusions.py`:
    - A handful of representative paths must be excluded.
    - A handful of representative paths must be included.
  - `constants.py`:
    - All listed `File`/`Pair` paths in tests are valid.

#### Milestone M2.2 – CLI Smoke Tests for Runner

- Add simple tests that invoke:
  - `ai_tools_runner.py status`
  - `ai_tools_runner.py config`
  - A no-op / “help” call.
- Assert:
  - Exit code is 0 for supported commands.
  - Unknown commands produce clear, non-zero errors.

#### Milestone M2.3 – Normalize Logging and Error Handling

- In `operations.py` and core tools:
  - Log start/end of major operations.
  - Use consistent error patterns (`MHMError` or an equivalent).
  - Ensure each command returns a sensible exit code.

Result: the infrastructure becomes predictable and diagnosable.

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

- Under `tests/fixtures/ai_tools_demo/`, create a tiny project with:
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

- Create `ai_development_tools/experimental/`.
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

#### Milestone M5.1 – Update `AI_DEV_TOOLS_GUIDE.md`

- For each tool, add:
  - Tier (Core / Supporting / Experimental).
  - One-line scope description.
  - One-line trust level (e.g. “partial”, “advisory”, “high-risk”, “stable”).

#### Milestone M5.2 – Standard Audit Recipe in `AI_DEVELOPMENT_WORKFLOW.md`

Add a short section describing when to run:

- `ai_tools_runner.py audit` (day-to-day checks).
- `ai_tools_runner.py audit --full` (pre-merge / pre-release checks).
- `ai_tools_runner.py doc-sync` and `ai_tools_runner.py docs` (doc work).

#### Milestone M5.3 – Update `AI_SESSION_STARTER.md`

- When the user’s task touches dev tools, route:
  - First to `AI_DEV_TOOLS_GUIDE.md`.
  - Then to the correct tools by tier and purpose.

Result: the dev tools ecosystem becomes something you and future collaborators can reason about and trust.

---

This roadmap is intentionally incremental. You do **not** need to implement every milestone at once.  
Start with Phase 1 (tiering + visibility), then Phase 2/3 for the most important tools, and expand as your time and energy allow.

---

This document can now serve as the authoritative basis for improving or restructuring the AI development tools ecosystem.