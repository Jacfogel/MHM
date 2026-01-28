# AI Development Tools - Improvement Roadmap (V4)

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Provide a focused, actionable roadmap for remaining development tools improvements  
> **Style**: Direct, technical, and concise  
> **Last Updated**: 2026-01-20

This is an updated, condensed roadmap based on V3 and the 2026-01-13 full audit. Completed work is summarized, and all remaining tasks are grouped and ordered.

---

## Current State Snapshot (2026-01-13 audit --full)

- Development tools coverage: 40.8% (target 60%+)
- Overall coverage: 72.0% (target 80%)
- Unused imports: 358 across 124 files (CRITICAL)
- Legacy references: 38 files, 71 markers
- Doc sync + doc hygiene: CLEAN (path drift, ASCII, headings, addresses, links)
- System health: ISSUES (errors detected in logs/errors.log in last 24h)
- Quick Wins: none reported

---

## Completed Work (Condensed)

- Tiered audit system, standardized tool metadata, modular service architecture
- Standard JSON output format and unified report data flow
- Report integrity improvements (file locks, consistent snapshot data)
- Coverage tools split/renamed and audit orchestration fixes
- Caching infrastructure (file-based caching + test-file coverage caching)
- System signals enhancement and tool naming consistency cleanup
- Major report generation fixes (error handling section, unused imports reporting cleanup)

---

## Remaining Work - Grouped and Ordered

### 1. Reliability, Coverage, and Test Health (HIGH)

#### 1.1 Raise development tools coverage to 60%+
**Status**: IN PROGRESS  
**Tasks**:
- [ ] Add tests for `development_tools/ai_work/analyze_ai_work.py` (currently 0.0%)
- [ ] Add tests for `analyze_package_exports.py`, `run_dev_tools.py`, `data_freshness_audit.py` (0.0% per AI_PRIORITIES)
- [ ] Investigate skipped test increase (1 -> 2 skipped)
- [ ] Strengthen tests for fragile helpers across `tests/development_tools/`
- [ ] Update all dev tools tests to use `tests/development_tools/test_config.json` fixture
- [ ] Document coverage improvements and updated baseline

#### 1.2 Restore audit status tests without memory leak
**Status**: PENDING  
**Tasks**:
- [ ] Review commented-out tests in `tests/development_tools/test_audit_status_updates.py`
- [ ] Identify memory leak sources (file tracking, mocks, temp FS ops, service cleanup)
- [ ] Verify if leak is test isolation, mock retention, or service reference leakage
- [ ] Choose approach: fix, rewrite, replace with integration tests, or remove if redundant
- [ ] Implement cleanup or rewrite with simpler structure
- [ ] Verify no memory leak (memory profiler) and ensure test isolation
- [ ] Re-enable `tests/development_tools/test_audit_tier_comprehensive.py` if possible

#### 1.3 Investigate intermittent low coverage warning
**Status**: PENDING  
**Tasks**:
- [ ] Review coverage merge flow in `run_test_coverage.py`
- [ ] Verify timing of coverage merge vs analysis
- [ ] Investigate shard file detection and naming
- [ ] Add detailed logging for coverage file detection and merge steps
- [ ] Reproduce with controlled parallel runs and identify correlation patterns
- [ ] Implement fix (wait/retry, improved detection, path resolution, or merge ordering)
- [ ] Add validation to ensure all expected coverage files exist before analysis

#### 1.4 Coverage pipeline consistency and file locations
**Status**: PENDING  
**Tasks**:
- [ ] Confirm whether overall coverage includes or excludes `development_tools/`
- [ ] Ensure consistent policy across AI_STATUS, consolidated report, TEST_COVERAGE_REPORT
- [ ] Investigate why `htmlcov/` is recreated empty and fix root cause
- [ ] Standardize `.coverage` file location (root vs `development_tools/tests/`)
- [ ] Investigate `.coverage_dev_tools.*` and `.coverage_parallel.*` creation in `development_tools/tests/`
- [ ] Update `.gitignore` and documentation to match intended locations

#### 1.5 Coverage caching follow-ups (test-file cache)
**Status**: PENDING  
**Tasks**:
- [ ] Measure actual time savings of domain-based test execution
- [ ] Compare full vs domain-filtered runs and document results in changelog
- [ ] Add cross-domain dependency tracking (invalidate dependent domains)
- [ ] Extend MtimeFileCache to high-cost analyzers (`analyze_error_handling`, `analyze_functions`, `analyze_module_imports`, `analyze_module_dependencies`)

#### 1.6 Fixture status file regeneration
**Status**: PENDING  
**Tasks**:
- [ ] Check timestamps of fixture status files under `tests/fixtures/development_tools_demo/`
- [ ] Determine when regeneration should occur (format changes, fixture updates)
- [ ] Add or document a regeneration process
- [ ] Ensure tests are not relying on stale fixture data

---

### 2. Reporting, Recommendations, and Output Quality (HIGH/MEDIUM)

#### 2.1 Enhance Quick Wins with file details
**Status**: PENDING  
**Tasks**:
- [ ] Extract file paths for ASCII compliance issues in `report_generation.py`
- [ ] Extract file paths for missing addresses in `report_generation.py`
- [ ] Include top files with issue counts, fix command, and verification guidance
- [ ] Validate with real data to ensure file lists are correct
- [ ] Apply consistent format for ASCII, addresses, headings, and links

#### 2.2 Standardize logging and surface top offenders
**Status**: PENDING  
**Tasks**:
- [ ] Standardize log levels across tools (INFO/DEBUG/WARNING)
- [ ] Remove duplicate log entries and demote verbose enhancement logs
- [ ] Replace print statements with logging (except intentional audit progress prints)
- [ ] Review noisy logs in config validation and package auditing
- [ ] Add "Top offenders" list to Quick Wins in AI_PRIORITIES.md

#### 2.3 Dependency patterns visibility in AI_STATUS and AI_PRIORITIES
**Status**: PENDING  
**Tasks**:
- [ ] Add Dependency Patterns section to AI_STATUS.md (summary level)
- [ ] Add Dependency Patterns recommendations to AI_PRIORITIES.md
- [ ] Expand consolidated report with top circular chains and high-coupling modules
- [ ] Keep all three outputs consistent and sourced from report_generation

#### 2.4 Critical issues file creation decision
**Status**: PENDING  
**Tasks**:
- [ ] Decide whether `critical_issues.txt` should exist
- [ ] If yes: define contents, generation trigger, and write path
- [ ] If no: remove misleading console message
- [ ] Consider alternatives (consolidated report or AI_PRIORITIES section)

#### 2.5 System signals purpose and redundancy cleanup
**Status**: PENDING  
**Tasks**:
- [ ] Identify unique value provided by `analyze_system_signals`
- [ ] Remove redundant doc-sync statement from system signals section
- [ ] Decide to keep, enhance, or eliminate system signals
- [ ] Update report_generation to reflect decision

#### 2.6 Consolidated report improvements
**Status**: PENDING  
**Tasks**:
- [ ] Convert `consolidated_report.txt` to `.md`
- [ ] Expand consolidated report detail to at least AI_STATUS level

#### 2.7 Console output polish (optional)
**Status**: PENDING  
**Tasks**:
- [ ] Verify no raw dict/list dumps during audits
- [ ] Consider progress indicators for long-running tools


#### 2.7 Remove duplicate last updated field at the bottom of AI_FUNCTION_REGISTRY.md

#### 2.8 retire unapproved docs
- incorporate information from unapproved docs development_tools\shared\RESULT_FORMAT_STANDARD.md, development_tools\shared\OUTPUT_STORAGE_STANDARDS.md and development_tools\shared\EXCLUSION_RULES.md into development_tools\DEVELOPMENT_TOOLS_GUIDE.md and development_tools\AI_DEVELOPMENT_TOOLS_GUIDE.md
- then remove docs

---

### 3. Tooling Integrity and Validation (MEDIUM/HIGH)

#### 3.0 Example marking standards checker (doc-sync validation)
**Status**: PENDING  
**Tasks**:
- [ ] Add example marking validation to `development_tools/docs/analyze_documentation_sync.py` or create a new validation module
- [ ] Detect file path references in example contexts missing `[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]` markers
- [ ] Validate example headings ("Examples:", "Example Usage:", "Example Code:")
- [ ] Report unmarked examples with file/line detail
- [ ] Integrate into `doc-sync` workflow and document the new check

#### 3.1 Changelog trim tooling
**Status**: PENDING  
**Tasks**:
- [ ] Review `_check_and_trim_changelog_entries()` in `audit_orchestration.py`
- [ ] Fix `changelog_manager` import/availability issues
- [ ] Ensure module exists and is reachable
- [ ] Add error handling and logging for trim failures

#### 3.2 Validation warnings cleanup
**Status**: PENDING  
**Tasks**:
- [ ] Investigate "Only 60/82 manual enhancements found in written file"
- [ ] Review "needs_enhancement" and "new_module" triggers
- [ ] Decide if test files should be excluded from these checks
- [ ] Update validation logic accordingly

#### 3.3 Version sync functionality
**Status**: PENDING  
**Tasks**:
- [ ] Determine what `version_sync` does and intended scope
- [ ] Verify it is operating correctly
- [ ] Document version sync process

#### 3.4 dev tools scripts and tool_timings.json location
**Status**: PENDING  
**Tasks**:
- [ ] Review `development_tools/scripts/` purpose and contents
- [ ] Decide whether scripts belong under project `scripts/`
- [ ] Decide proper location for `tool_timings.json`
- [ ] Update `_save_timing_data()` if location changes
- [ ] Document the decision

#### 3.5 Error handling coverage metric consistency
**Status**: PENDING  
**Tasks**:
- [ ] Validate metrics when missing functions are non-zero
- [ ] Verify missing count vs percentage calculation
- [ ] Standardize calculation if discrepancy appears
- [ ] Ensure reports show consistent values

#### 3.6 Pyright duplicate declaration investigation
**Status**: PENDING  
**Tasks**:
- [ ] Compare duplicate `generate_dependency_report()` implementations and merge/remove
- [ ] Ensure logger usage (no print) when consolidating
- [ ] Investigate duplicate methods in `tool_wrappers.py` and merge/remove
- [ ] Document the decision and remove orphaned code

#### 3.7 Rename generate_function_docstrings to fix_function_docstrings
**Status**: PENDING  
**Tasks**:
- [ ] Rename file: `development_tools/functions/generate_function_docstrings.py` -> `fix_function_docstrings.py`
- [ ] Update tool metadata and CLI wrappers to use new name
- [ ] Update documentation references (AI + human guides)
- [ ] Preserve experimental tier and any backward-compat wrapper if needed

---

### 4. External Tool Evaluation and Integration (MEDIUM)

#### 4.1 Evaluate and integrate complementary tools
**Status**: PENDING  
**Tasks**:
- [ ] Evaluate ruff (lint/format) and radon (complexity) for integration
- [ ] Evaluate pydeps for dependency graphs vs existing dependency tool
- [ ] Run bandit security scan and decide on Tier 1 integration
- [ ] Run pip-audit and decide on Tier 1 integration
- [ ] Make integration decision: replace, complement, or keep existing tools
- [ ] If integrating: add wrappers, update requirements, and update docs
- [ ] Optional: evaluate vulture (dead code) and pre-commit (hooks)

---

### 5. Future Enhancements (LOW)

#### 5.0 Explore adding a possible duplicate function/method analysis
**Status**: COMPLETED  
**Tasks**:
- [x] Add `functions/analyze_duplicate_functions.py` with similarity scoring (name/args/locals/imports)
- [x] Add config defaults + external overrides (`analyze_duplicate_functions`)
- [x] Register tool in metadata, CLI, and audit Tier 2
- [x] Document in AI + human development tools guides

#### 5.1 Unused imports cleanup module
**Status**: PENDING  
**Tasks**:
- [ ] Create categorization logic for unused imports
- [ ] Add category-based reporting
- [ ] Implement `imports/fix_unused_imports.py`
- [ ] Add cleanup recommendations and consider `--categorize` flag

#### 5.2 Documentation overlap analysis enhancements
**Status**: PENDING  
**Tasks**:
- [ ] Review consolidation opportunities (Development Workflow, Testing)
- [ ] Create consolidation plan for identified groups
- [ ] Improve actionable insights and reduce false positives

#### 5.3 AI work validation improvements
**Status**: PENDING  
**Tasks**:
- [ ] Review current AI work validation logic
- [ ] Add actionable recommendations beyond status text
- [ ] Avoid overlap with domain-specific analyzers

#### 5.4 TODO sync cleanup automation
**Status**: PENDING  
**Tasks**:
- [ ] Review current TODO sync logic
- [ ] Improve detection of completed entries
- [ ] Add auto-clean with dry-run option
- [ ] Improve reporting of manual vs auto-cleanable items
- [ ] Document workflow and best practices

#### 5.5 New tool creation based on gap analysis
**Status**: PENDING  
**Effort**: Large  
**Tasks**:
- [ ] Prioritize 29 identified gaps across 6 domains:
  - Documentation
  - Code quality
  - Testing
  - Configuration/environment
  - AI/prompt
  - Integration/workflow
- [ ] Implement tools following analyze/generate/fix patterns
- [ ] Add tests using `tests/fixtures/development_tools_demo/`
- [ ] Update tool metadata and documentation
- [ ] Integrate into audit tiers where appropriate

#### 5.6 Memory profiler integration
**Status**: PENDING  
**Source**: `scripts/testing/memory_profiler.py`  
**Tasks**:
- [ ] Decide whether to integrate `scripts/testing/memory_profiler.py`
- [ ] Choose approach (new tool vs enhancement vs standalone monitor)
- [ ] Design JSON/report outputs and CLI interface
- [ ] Implement tool and tests with fixture project
- [ ] Update tool metadata, docs, and audit tier placement

---

### 6. Audit-Driven Remediation (Non-Tool Code, Current Backlog)

These are surfaced by the tools and remain outstanding but are not tool-suite changes.

- [ ] Retire legacy reference markers (38 files, 71 markers); update references and rerun `legacy`
- [ ] Reduce unused imports (358 in 124 files) and verify via `unused-imports-report`
- [ ] Raise domain coverage for communication, ui, and core (below 80% target)
- [ ] Refactor critical-complexity functions (145 critical, 147 high)

---

## Related Documents

- `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md` - Prior version with detailed history
- `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` - AI-facing tool guide
- `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` - Human-facing tool guide
- `development_docs/LEGACY_REFERENCE_REPORT.md` - Current legacy reference marker inventory
- `development_docs/TEST_COVERAGE_REPORT.md` - Coverage details
