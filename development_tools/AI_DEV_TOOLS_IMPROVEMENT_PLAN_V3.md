# AI Development Tools - Improvement Roadmap

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Provide a focused, actionable roadmap for remaining development tools improvements  
> **Style**: Direct, technical, and concise  
> **Last Updated**: 2025-12-25

This document provides a streamlined roadmap focusing on remaining work, organized into logical stages. For detailed historical context, see `AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md`.

---

## Completed Work Summary

### Core Infrastructure (Phases 1-7, 2025-11-25 to 2025-12-02)
- ✅ **Tiering system**: Tool metadata, CLI grouping, three-tier audit system (quick/standard/full)
- ✅ **Core infrastructure**: 138+ tests, consistent logging, error handling, domain-based directory structure
- ✅ **Portability**: All tools use external configuration, standardized output storage with archiving
- ✅ **Naming conventions**: Standardized patterns (`analyze_*`, `generate_*`, `fix_*`), 20+ focused tools created
- ✅ **Modular architecture**: Refactored monolithic `operations.py` into 7 focused service modules

### Recent Improvements (2025-12-06 to 2025-12-25)
- ✅ **Standard format migration**: All 19 analysis tools output consistent JSON structure
- ✅ **Report data flow**: Unified data loading, all findings appear in status reports
- ✅ **Status file integrity**: File-based locks prevent mid-audit writes
- ✅ **Coverage improvements**: Serial test execution, dev tools coverage tracking, file organization
- ✅ **Performance optimizations**: Caching for legacy references, parallel execution for Tier 2/3 tools (~10% time reduction)
- ✅ **Error handling analysis**: Enhanced exclusion logic, improved decorator detection
- ✅ **Analysis validation**: False negative detection, exclusion logic standardization, validation framework
- ✅ **Tool decomposition**: Unused imports tool split into analysis and report generation
- ✅ **Audit tier testing**: Comprehensive orchestration tests and E2E verification

**Key Metrics:**
- 138+ tests across all development tools
- 20/20 analysis tools use standardized storage (100%)
- 23 tools in audit tiers (7 Tier 1, 10 Tier 2, 6 Tier 3)
- All verification tasks completed

---

## Remaining Work - Organized by Stage

### Stage 1: Quality & Accuracy Improvements (HIGH PRIORITY)

#### 1.1 Improve Recommendation Quality
**Status**: COMPLETE ✅  
**Priority**: HIGH  
**Issue**: Recommendations have quality issues: redundancy, lack of specificity, inconsistent ordering, potential false positives.

**Implementation Complete (2025-12-31)**:
- ✅ Fixed unused imports recommendation logic - only suggests removing "Obvious Unused" imports (not test mocking, Qt testing, etc.)
- ✅ Fixed config validation recommendation deduplication using (tool_name, issue_type) tuples with regex extraction
- ✅ Simplified priority ordering with fixed tier system (tier * 100 + insertion_order) for predictable ordering
- ✅ Enhanced recommendation specificity - all recommendations now include Action, Effort, Why this matters, and Commands where applicable
- ✅ Added recommendation validation helper function to check for stale data and suspicious counts
- ✅ Improved context - all recommendations include impact assessment, effort estimates, and actionable steps

**Key Issues Resolved**:
- ✅ Unused imports recommendation now only shows when obvious_unused > 0 (was recommending 356 imports when only 1 was obvious)
- ✅ Config validation recommendations properly deduplicated using tool name and issue type
- ✅ Priority ordering now uses fixed tiers (Tier 1: 100-199, Tier 2: 200-299, etc.) instead of dynamic counters
- ✅ All recommendations include actionable steps, effort estimates, and context

**Tasks**:
- [x] Review unused imports recommendation logic - only suggest removing "Obvious Unused" imports
- [x] Fix config validation recommendation redundancy (deduplication)
- [x] Simplify priority ordering with fixed tiers instead of dynamic logic
- [x] Enhance recommendation specificity (add actionable steps, file paths, effort estimates)
- [x] Add recommendation validation (remove stale recommendations)
- [x] Improve context (impact assessment, effort estimates, related recommendations)

**Files**: `development_tools/shared/service/report_generation.py`, `development_tools/config/analyze_config.py`

#### 1.2 Improve Development Tools Test Coverage
**Status**: IN PROGRESS (46.4% → target 60%+)  
**Priority**: HIGH  
**Issue**: Development tools coverage tracked separately, currently at 42.6%. Specific modules at 0% coverage.

**Progress**:
- ✅ Created 260+ tests across 17 modules (analyze_documentation, analyze_error_handling, analyze_functions, etc.)
- ✅ Created structured test fixtures in `tests/fixtures/development_tools_demo/docs/analysis_validation/`
- ✅ Created `tests/development_tools/test_config.json` and `test_config_path` fixture
- [ ] Add tests for `analyze_ai_work.py` (0.0%, missing 206 lines)
- [ ] Target 60%+ coverage for development tools overall (currently 46.4%, up from 34.7%)
- [ ] Investigate skipped test increase (1 → 2 skipped tests) - may indicate test isolation issue
- [ ] Strengthen tests for fragile helpers
- [ ] Update all tests to use `test_config.json` fixture instead of default config
- [ ] Document test coverage improvements

**Files**: `development_tools/ai_work/analyze_ai_work.py`, `tests/development_tools/`

#### 1.3 Enhance Quick Wins Recommendations with File Details
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Quick Wins section for ASCII compliance and file address metadata only shows counts and commands, but doesn't list specific files or provide verification guidance.

**Current Behavior**:
- Shows: "Fix 17 ASCII compliance issue(s) in 2 file(s) - run `python development_tools/run_development_tools.py doc-fix --fix-ascii`"
- Shows: "Add file address metadata to 1 file(s) missing addresses - run `python development_tools/run_development_tools.py doc-fix --add-addresses`"
- Missing: Specific file paths, top issues, verification guidance

**Desired Behavior**:
- List top 3-5 files with issues (or all if fewer than 5)
- Show issue counts per file
- Advise using automated fixes with verification step
- Include guidance to verify fixes resolved issues and apply manual fixes if needed

**Tasks**:
- [ ] Update `_generate_ai_priorities_document()` in `report_generation.py` to extract file paths from ASCII compliance data
- [ ] Update `_generate_ai_priorities_document()` to extract file paths from missing addresses data
- [ ] Enhance Quick Wins format to show:
  - Top files with issues (limit to 3-5 files, or all if fewer)
  - Issue counts per file
  - Automated fix command
  - Verification guidance: "Run the automated fix, then verify issues are resolved. If not, apply manual fixes."
- [ ] Test with actual data to ensure file paths are correctly extracted and displayed
- [ ] Update format for all doc-fix related Quick Wins (ASCII, addresses, headings, links) for consistency

**Files**: `development_tools/shared/service/report_generation.py` (lines 2530-2556), `development_tools/docs/analyze_ascii_compliance.py`, `development_tools/docs/analyze_missing_addresses.py`

---

### Stage 2: Tool Enhancements & Consistency

#### 2.1 Fix Config Validation Issues
**Status**: COMPLETE ✅  
**Effort**: Small  
**Issue**: 4 config validation recommendations identified (run_development_tools.py and run_dev_tools.py don't import config module).

**Implementation Complete (2025-12-31)**:
- ✅ **Investigation**: Confirmed that `AIToolsService` handles all config internally (imports config in `core.py` line 16)
- ✅ **Decision**: Entry point scripts that create `AIToolsService` instances don't need config imports
- ✅ **Implementation**: Updated validation logic to detect entry point scripts (files that create `AIToolsService` instances)
- ✅ **Updated**: `_analyze_tool_config_usage()` to mark entry point scripts as exempt from config import requirement
- ✅ **Updated**: Recommendation generation to skip entry point scripts
- ✅ **Updated**: Logging/reporting to show entry point scripts as "OK (entry point script)"
- ✅ **Additional Fix**: Fixed Qt crash in `test_account_creation_real_behavior` by adding `stop_channel_monitor_threads` fixture
- ✅ **Test Updates**: Updated `test_decision_support.py` tests to include required fields for `categorize_functions()`

**Files**: `development_tools/config/analyze_config.py` (validation logic updated), `tests/ui/test_account_creation_ui.py` (crash fix), `tests/development_tools/test_decision_support.py` (test updates)

#### 2.2 Investigate "Symbol: unused-import" bullet points
**Status**: COMPLETE ✅  
**Effort**: Small  
**Description**: Check if these serve a purpose or are redundant noise in `UNUSED_IMPORTS_REPORT.md`.

**Implementation Complete (2025-12-31)**:
- ✅ **Investigation**: Confirmed that "Symbol: `unused-import`" lines are redundant
  - The symbol field from pylint is just the message ID (`unused-import`), not the actual symbol name
  - The message already identifies the unused import (e.g., "Unused List imported from typing")
  - It adds noise without providing useful information
- ✅ **Fix**: Removed symbol display from report generation (lines 209-210 in `generate_unused_imports_report.py`)
- ✅ **Verification**: Regenerated unused imports report - redundant bullets are gone
- ✅ **Note**: Symbol field kept in data structure for potential future use, just not displayed

**Files**: `development_tools/imports/generate_unused_imports_report.py` (lines 209-210 removed)

#### 2.3 Enhance System Health Analysis
**Status**: COMPLETE ✅  
**Issue**: Currently reports "OK" but may not provide actionable insights.

**Implementation Complete (2025-12-26)**:
- ✅ Enhanced `_check_system_health()` to include:
  - Audit freshness tracking (with specific time ranges: <1 hour, <24 hours, 25-72 hours, 4-10 days, 11-30 days, >30 days)
  - Test coverage status analysis
  - Documentation sync status checking
  - Error log analysis (recent errors, file size checks)
  - Severity levels (INFO, WARNING, CRITICAL)
  - Actionable recommendations
- ✅ Updated report generation to display enhanced health information
- ✅ Removed redundant information and recommendations from status documents

**Tasks**:
- [x] Investigate what System Health currently looks for
- [x] Enhance to provide actionable insights beyond "OK" status
- [x] Add specific health indicators and recommendations

**Files**: `development_tools/reports/analyze_system_signals.py` (renamed from `system_signals.py`)

#### 2.5 Rename system_signals to analyze_system_signals
**Status**: COMPLETE ✅  
**Issue**: Tool should follow naming convention `analyze_*` for consistency.

**Implementation Complete (2025-12-26)**:
- ✅ Renamed file: `system_signals.py` → `analyze_system_signals.py`
- ✅ Updated `SCRIPT_REGISTRY` entry in `tool_wrappers.py`
- ✅ Updated all references in `audit_orchestration.py` (Tier 1 tools)
- ✅ Updated function/class names (`SystemSignalsGenerator` → `SystemSignalsAnalyzer`)
- ✅ Added legacy compatibility wrapper `run_system_signals()` in `commands.py`
- ✅ Updated report generation to use new key name
- ✅ All tests updated and passing

**Note**: Old file `system_signals.py` still exists but is not used. Legacy wrapper provides backward compatibility.

**Tasks**:
- [x] Update `SCRIPT_REGISTRY` entry in `tool_wrappers.py`
- [x] Update all references in `audit_orchestration.py` (Tier 1 tools)
- [x] Rename file: `system_signals.py` → `analyze_system_signals.py`
- [x] Update function/class names and logging messages
- [x] Verify all tests still pass
- [x] Add legacy compatibility wrapper

**Files**: `development_tools/reports/analyze_system_signals.py`, `development_tools/shared/service/tool_wrappers.py`, `development_tools/shared/service/audit_orchestration.py`, `development_tools/shared/service/commands.py`

#### 2.6 Investigate quick_status Placement
**Status**: COMPLETE ✅  
**Issue**: `quick_status` runs at beginning of Tier 1, but reads from `analysis_detailed_results.json` which may not exist at audit start.

**Implementation Complete (2025-12-26)**: **Option A - Move to End of Tier 1** ✅
- ✅ Moved `quick_status` execution to end of Tier 1 (after other tools have run)
- ✅ Tool now has access to fresh audit data from current run
- ✅ Maintains graceful degradation if data is missing (works standalone)
- ✅ Comment added explaining placement rationale

**Decision**: Moved to end of Tier 1 to ensure it can access fresh audit data while still working gracefully if run standalone.

**Tasks**:
- [x] Analyze current behavior and dependencies
- [x] Compare outputs at beginning vs. end of audit
- [x] Evaluate value (beginning vs. end vs. standalone)
- [x] Make decision: Move to end, remove from audit, or keep with enhancements
- [x] Move `quick_status` to end of Tier 1 in `audit_orchestration.py`

**Files**: `development_tools/reports/quick_status.py`, `development_tools/shared/service/audit_orchestration.py`

#### 2.7 Review Coverage Tool Naming and Similarity
**Status**: COMPLETE ✅  
**Priority**: MEDIUM  
**Issue**: 
- `generate_test_coverage.py` orchestrates pytest execution, while `analyze_test_coverage.py` provides pure analysis. Naming may be confusing.
- `generate_test_coverage.py` and `generate_test_coverage_reports.py` are too similarly named and could cause confusion.
- `generate_test_coverage_reports` tool registration is misleading: it only verifies report exists, doesn't actually generate reports (reports are generated inside `generate_test_coverage.py`).

**Analysis Complete (2025-12-26)**:
- ✅ **Relationship**: `generate_test_coverage.py` imports and uses `TestCoverageReportGenerator` class from `generate_test_coverage_reports.py` as a utility
- ✅ **Actual Usage**: Report generation happens INSIDE `generate_test_coverage.py` via `self.report_generator.finalize_coverage_outputs()`
- ✅ **Tool Registration Issue**: `run_generate_test_coverage_reports()` only verifies `TEST_COVERAGE_REPORT.md` exists - it doesn't generate reports
- ✅ **TEST_COVERAGE_REPORT.md Generation**: Created by `generate_test_coverage.py` → `update_coverage_plan()` method when run with `--update-plan` flag
- ✅ **See**: `development_tools/tests/COVERAGE_TOOLS_ANALYSIS.md` for detailed analysis

**Implementation Complete (2025-12-26)**: **Option E - Break Up generate_test_coverage** ✅
1. ✅ **Split responsibilities**:
   - `generate_test_coverage.py` → `run_test_coverage.py` (execution only: runs pytest, collects data)
   - Moved `update_coverage_plan()` method to `generate_test_coverage_report.py`
   - `generate_test_coverage_reports.py` → `generate_test_coverage_report.py` (generates TEST_COVERAGE_REPORT.md + HTML/JSON)
2. ✅ **Updated all references**: SCRIPT_REGISTRY, audit_orchestration, commands, tests, documentation
3. ✅ **Fixed tool registration**: `run_generate_test_coverage_report()` now actually generates reports from existing coverage.json
4. ✅ **Maintained backward compatibility**: `--update-plan` flag deprecated but still accepted (logs warning)

**Tasks**:
- [x] Review current architecture and usage patterns
- [x] Evaluate naming similarity between `generate_test_coverage.py` and `generate_test_coverage_reports.py`
- [x] Document analysis in `COVERAGE_TOOLS_ANALYSIS.md`
- [x] Evaluate consolidation vs. breaking up options
- [x] **Implement Option E - Break Up generate_test_coverage**:
  - [x] Move `update_coverage_plan()` method from `generate_test_coverage.py` to `generate_test_coverage_report.py`
  - [x] Rename `generate_test_coverage.py` → `run_test_coverage.py`
  - [x] Rename `generate_test_coverage_reports.py` → `generate_test_coverage_report.py` (singular)
  - [x] Enhance `generate_test_coverage_report.py` to generate TEST_COVERAGE_REPORT.md (from moved method)
  - [x] Update `run_test_coverage.py` to remove `update_coverage_plan()` method
  - [x] Update `SCRIPT_REGISTRY` in `tool_wrappers.py`
  - [x] Update references in `audit_orchestration.py` (sequential: run_test_coverage → generate_test_coverage_report)
  - [x] Remove misleading verification-only tool registration
  - [x] Update import statements
  - [x] Update documentation
  - [x] Fix method name issues (`_load_coverage_json` → `load_coverage_json`)
  - [x] Fix import issues (relative vs absolute imports)
  - [x] Verify audit completes successfully (2025-12-27: ✅ All tests pass, coverage report generates correctly)

**Files**: `development_tools/tests/run_test_coverage.py`, `development_tools/tests/analyze_test_coverage.py`, `development_tools/tests/generate_test_coverage_report.py`

**Verification (2025-12-27)**:
- ✅ Full audit (`audit --full`) completes successfully
- ✅ All coverage tools execute correctly
- ✅ TEST_COVERAGE_REPORT.md generates successfully
- ✅ All references updated in code, tests, and tool registries
- ✅ Old files ready for deletion: `generate_test_coverage.py`, `generate_test_coverage_reports.py`, `COVERAGE_TOOLS_ANALYSIS.md`

#### 2.8 Review generate_* Tools That Don't Create .md Files
**Status**: COMPLETE ✅  
**Priority**: MEDIUM  
**Issue**: Most `generate_*` tools create markdown report files (`.md`), but two tools don't follow this pattern:
- `generate_error_handling_recommendations.py` - Generates recommendations (could be incorporated into analyzer)
- `generate_function_docstrings.py` - Actually modifies code (should be `fix_*` or `add_*` pattern)

**Investigation Complete (2025-12-31)**:

**1. `generate_error_handling_recommendations.py`**:
- ✅ **Implementation Complete (2025-12-31)**: **Option C - Moved function into `analyze_error_handling.py`** ✅
  - ✅ Moved `generate_recommendations()` function directly into `analyze_error_handling.py` as part of `_generate_recommendations()` method
  - ✅ Removed tool registration from `tool_metadata.py` and `tool_wrappers.py`
  - ✅ Updated documentation references in `DEVELOPMENT_TOOLS_GUIDE.md` and `AI_DEVELOPMENT_TOOLS_GUIDE.md`
  - ✅ Updated test file `test_generate_error_handling_recommendations.py` to test the method directly (all 11 tests passing)
  - ✅ Deleted `generate_error_handling_recommendations.py` file
  - ✅ **Rationale**: Recommendations are part of analysis, not artifact generation. `generate_*` prefix should be reserved for creating artifacts (like .md files). Moving the function into the analyzer simplifies the codebase and aligns with naming conventions.

**2. `generate_function_docstrings.py`**:
- ✅ **Functionality**: **MODIFIES CODE** by adding docstrings to functions (line 224 writes to files)
- ✅ **Naming Issue**: Should follow `fix_*` pattern (repairs missing docs) or `add_*` pattern (adds new content)
- ✅ **Current Behavior**: Scans Python files, detects function types, and adds appropriate docstrings where missing
- ✅ **Recommendation**: **Rename to `fix_function_docstrings.py`** - Better matches naming convention:
  - `fix_*` pattern is for cleanup/repair operations (this repairs missing documentation)
  - `generate_*` should be reserved for creating artifacts (like .md files), not modifying code
  - Tool is marked as `experimental` tier, so renaming is low-risk

**Naming Convention Clarification**:
- ✅ **`generate_*`**: Should create artifacts (typically `.md` files), not modify code
- ✅ **`fix_*`**: Cleanup/repair operations (removal, cleanup, repairs like adding missing docs)
- ✅ **`add_*`**: Alternative naming for tools that add new content (less common in current codebase)

**Implementation Tasks** (if renaming `generate_function_docstrings.py`):
- [ ] Rename file: `generate_function_docstrings.py` → `fix_function_docstrings.py`
- [ ] Update `SCRIPT_REGISTRY` entry in `tool_wrappers.py`
- [ ] Update `tool_metadata.py` entry
- [ ] Update all references in documentation
- [ ] Update function/class names if needed
- [ ] Verify all tests still pass

**Files**: 
- `development_tools/error_handling/analyze_error_handling.py` (now contains recommendations generation)
- `development_tools/error_handling/generate_error_handling_recommendations.py` (deleted - functionality moved to analyze_error_handling.py)
- `development_tools/functions/generate_function_docstrings.py` (reviewed, rename recommended)
- `development_tools/shared/tool_metadata.py` (removed tool registration)
- `development_tools/shared/service/tool_wrappers.py` (removed tool registration)
- `tests/development_tools/test_generate_error_handling_recommendations.py` (updated to test inlined method)

#### 2.9 Evaluate and Integrate Complementary Development Tools
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Learn about and test ruff, radon, pydeps, bandit, and pip-audit to determine if they should replace or complement parts of the development tools suite. These tools may be faster or more mature than custom implementations, and security tools (bandit, pip-audit) fill a critical gap since the project handles user data and credentials.

**Tasks**:
- [ ] **Learn about and try ruff** - Install ruff, test it on the codebase, compare speed/results with current `analyze_unused_imports.py` (pylint-based)
  - [ ] Install ruff: `pip install ruff`
  - [ ] Install Ruff VS Code extension in Cursor (optional but recommended for real-time feedback)
  - [ ] Run ruff to find unused imports: `ruff check . --select F401`
  - [ ] Compare results with current unused imports tool (357 unused imports found)
  - [ ] Test auto-fix capability: `ruff check --fix .`
  - [ ] Measure performance difference (ruff is 10-100x faster than pylint)
  - [ ] Determine if ruff should replace or complement `analyze_unused_imports.py`
- [ ] **Learn about and try radon** - Install radon, test complexity analysis, compare with current `analyze_functions.py` complexity tracking
  - [ ] Install radon: `pip install radon`
  - [ ] Run complexity analysis: `radon cc . --min B`
  - [ ] Compare complexity metrics with current tool (131 critical-complexity functions tracked)
  - [ ] Test maintainability index: `radon mi .`
  - [ ] Determine if radon should complement `analyze_functions.py` (keep your tool for docstring/pattern tracking, use radon for complexity)
- [ ] **Learn about and try pydeps** - Install pydeps, test dependency graph generation, compare with current `analyze_module_dependencies.py`
  - [ ] Install pydeps: `pip install pydeps`
  - [ ] Generate dependency graph for core module: `pydeps core/ --max-bacon=2`
  - [ ] Compare visualization quality with current dependency analysis
  - [ ] Test on communication and other modules
  - [ ] Determine if pydeps should complement `analyze_module_dependencies.py` (use pydeps for graphs, keep your tool for pattern analysis)
- [ ] **Learn about and try bandit** - Install bandit, test security scanning (HIGH PRIORITY - project handles user data and credentials)
  - [ ] Install bandit: `pip install bandit`
  - [ ] Install Bandit VS Code extension in Cursor (optional but recommended for real-time security feedback)
  - [ ] Run security scan: `bandit -r core/ communication/ -f json -o bandit-report.json`
  - [ ] Review findings for hardcoded secrets, SQL injection risks, insecure random, etc.
  - [ ] Determine if bandit should be added to development tools workflow (recommended: add to Tier 1 quick audit)
  - [ ] Configure bandit to exclude false positives (test files, development tools, etc.)
- [ ] **Learn about and try pip-audit** - Install pip-audit, test dependency vulnerability scanning (HIGH PRIORITY - project has 15+ dependencies)
  - [ ] Install pip-audit: `pip install pip-audit`
  - [ ] Run dependency check: `pip-audit --requirement requirements.txt --format json`
  - [ ] Review findings for known CVEs in dependencies
  - [ ] Determine if pip-audit should be added to development tools workflow (recommended: add to Tier 1 quick audit)
  - [ ] Set up regular checks (before deployments, in CI/CD if applicable)
- [ ] **Make integration decision** - Based on testing, decide whether to:
  - Replace tools entirely (if significantly better)
  - Use alongside existing tools (if complementary)
  - Keep existing tools (if they're better for your workflow)
- [ ] **If integrating**: Add selected tools to development tools workflow (update `development_tools/shared/service/tool_wrappers.py` or create new wrappers)
- [ ] **If integrating**: Update `requirements.txt` with new tool dependencies
- [ ] **If integrating**: Install VS Code extensions in Cursor for tools that support them (ruff, bandit)
- [ ] **If integrating**: Update documentation (AI_DEVELOPMENT_TOOLS_GUIDE.md, DEVELOPMENT_TOOLS_GUIDE.md) to reflect tool changes
- [ ] **Optional: Learn about vulture** - Dead code detection (finds unused functions/classes, not just imports)
  - [ ] Install vulture: `pip install vulture`
  - [ ] Run dead code scan: `vulture . --min-confidence 80 --exclude tests/`
  - [ ] Review findings (can be noisy with false positives)
  - [ ] Determine if useful for occasional cleanup runs (not in every audit)
- [ ] **Optional: Learn about pre-commit** - Git hooks for automated quality checks
  - [ ] Install pre-commit: `pip install pre-commit`
  - [ ] Create `.pre-commit-config.yaml` with hooks for ruff, bandit, etc.
  - [ ] Test hooks: `pre-commit run --all-files`
  - [ ] Determine if pre-commit adds value or is too complex for current workflow

**Files**: `development_tools/shared/service/tool_wrappers.py`, `requirements.txt`, `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`, `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`

**Note**: Cursor IDE Compatibility - All tools are compatible. Ruff and bandit have VS Code extensions (Cursor is VS Code-based), others work via command-line or pre-commit hooks.

#### 2.10 Investigate Caching to Accelerate Test Coverage Generation
**Status**: INTEGRATED - Test-File Caching Enabled by Default  
**Priority**: MEDIUM  
**Issue**: Test coverage generation can be time-consuming, especially for large codebases. Caching could potentially accelerate coverage collection by reusing coverage data when source files haven't changed.

**Progress** (2026-01-11):
- [x] Created comprehensive caching exploration plan
  - Plan includes test-file caching approach using test directory structure and pytest markers (user insight)
  - Plan documents investigation, evaluation, and implementation phases
  - Plan file: `.cursor/plans/caching_exploration_for_development_tools_fb102ab8.plan.md`
- [x] Added `--clear-cache` flag to development tools CLI for easy cache management
- [x] Removed all legacy `cache_file` parameter references - all tools now use standardized storage exclusively
- [x] **Investigated test coverage workflow**: Analyzed `run_test_coverage.py`, `analyze_test_coverage.py`, and `generate_test_coverage_report.py` to understand execution flow
- [x] **Built domain mapping infrastructure**: Created `tests/domain_mapper.py` (`DomainMapper`) to map source code directories to test directories and pytest markers
  - Maps source domains (core/, communication/, ui/, tasks/, ai/, user/, notebook/) to test directories and markers
  - Extracts pytest markers from test files using regex
  - Provides utilities for generating pytest marker filters and test path lists
- [x] **Implemented coverage analysis caching**: Added caching to `analyze_test_coverage.py` using `MtimeFileCache`
  - Caches analysis results based on coverage JSON file mtime
  - Saves ~2s per run when coverage data hasn't changed
  - Uses standardized storage: `development_tools/tests/jsons/.analyze_test_coverage_cache.json`
- [x] **Implemented test-file coverage cache (Integrated)**: Added `tests/test_file_coverage_cache.py`
  - Tracks source file mtimes per domain and maps domains to test files
  - Runs only test files covering changed domains, merges cached coverage for unchanged tests
  - Cache location: `development_tools/tests/jsons/test_file_coverage_cache.json`
  - **Status**: Integrated with `run_test_coverage.py` (enabled by default)
- [x] **Implemented dev tools coverage cache (Integrated)**: Added `tests/dev_tools_coverage_cache.py`
  - Caches dev tools coverage JSON keyed by development_tools source mtimes
  - Cache location: `development_tools/tests/jsons/dev_tools_coverage_cache.json`
- [x] **Documented caching strategy**: Updated `AI_DEVELOPMENT_TOOLS_GUIDE.md` with caching documentation
  - File-based caching (MtimeFileCache)
  - Coverage analysis caching
  - Domain-aware coverage caching (POC status)
  - Cache management (`--clear-cache` flag)

**Evaluation Results** (2026-01-11):
- [x] **Identified caching opportunities**: Evaluated all development tools for caching potential
  - **Already cached** (7 tools): `analyze_unused_imports`, `analyze_ascii_compliance`, `analyze_missing_addresses`, `analyze_legacy_references`, `analyze_heading_numbering`, `analyze_path_drift`, `analyze_unconverted_links`
  - **Good candidates for caching** (file-based analyzers):
    - `analyze_error_handling.py` - Scans files for error handling patterns (file-based, deterministic)
    - `analyze_functions.py` - Discovers functions across files (file-based, deterministic)
    - `analyze_module_imports.py` - Scans import statements (file-based, may have dependencies)
    - `analyze_module_dependencies.py` - Analyzes module dependencies (depends on imports analysis)
- [x] **Evaluated caching strategies**: 
  - **Test-file caching (RECOMMENDED)**: Tracks source file mtimes per domain, maps to test files, enables granular invalidation
  - **File-level caching**: Already implemented via `MtimeFileCache` for file-based analyzers
  - **Analysis result caching**: Implemented for `analyze_test_coverage.py` - caches analysis results based on coverage JSON mtime
  - **Test execution caching**: Deferred - complex due to coverage data merging requirements
- [x] **Designed cache storage mechanism**:
  - **Location**: Standardized storage at `development_tools/{domain}/jsons/.{tool}_cache.json` (for file-based caches)
  - **Test-file coverage cache**: `development_tools/tests/jsons/test_file_coverage_cache.json`
  - **Dev tools coverage cache**: `development_tools/tests/jsons/dev_tools_coverage_cache.json`
  - **Format**: JSON (human-readable, easy to debug)
  - **Versioning**: Cache version field in test-file cache to handle tool changes
  - **Invalidation**: File mtime checks (automatic), config file changes (automatic), manual via `--clear-cache` flag
- [x] **Baseline performance** (from plan and existing data):
  - **Test coverage execution**: ~365s (baseline)
  - **Coverage analysis**: ~2s (now cached, saves ~2s when coverage JSON unchanged)
  - **Report generation**: ~5s
  - **Potential savings with test-file caching**: ~83% when only one domain changes (e.g., only ui/ changes → only run tests covering ui/)

**Progress Updates** (2026-01-12):
- [x] **Integrated test-file caching with test execution**: `run_test_coverage.py` now uses `TestFileCoverageCache` for intelligent test selection
  - Uses `get_changed_domains()` to detect which domains need re-testing
  - Uses domain mappings to select test files covering changed domains
  - Only runs those tests, merges cached coverage data from unchanged tests
  - Enabled by default - disable with `--no-domain-cache` flag
  - Supports both serial and parallel test execution modes
- [x] **Dev tools coverage caching**: `run_test_coverage.py` caches dev tools coverage JSON based on development_tools source mtimes
- [x] **Fixed domain isolation and filtering**: Main coverage now filters out `development_tools` domain to prevent cross-contamination
  - Main coverage checks only main coverage domains (core, communication, ui, tasks, ai, user, notebook)
  - Dev tools coverage uses separate domain key and doesn't interfere with main coverage
  - Fixed duplicate log messages (changed to debug level)
  - Only tracks `.py` files (ignores .md, .txt, .json, .log files)
- [x] **Cache management integration**: Coverage caches now included in `--clear-cache` flag and cleanup command
  - `--clear-cache` flag clears test-file and dev tools coverage caches
  - `cleanup --coverage` includes coverage cache cleanup
  - Cleanup command updated to mirror audit structure (default = conservative, `--full` = everything)

**Remaining Tasks** (Future Enhancements):
- [ ] **Measure performance benefits**: Measure actual time savings with test-file-based test execution
  - Target: 50%+ time savings when only one domain changes (e.g., ~83% when only ui/ changes)
  - Compare full test run vs. domain-filtered test run
  - Document actual performance improvements in changelog
- [ ] **Add dependency tracking**: Track cross-domain dependencies (e.g., if `core/` changes, may need to re-run `communication/` tests that depend on core)
  - Identify cross-domain dependencies (e.g., communication/ depends on core/)
  - Automatically invalidate dependent domains when upstream domains change
  - Consider transitive dependencies (e.g., if core/ changes, invalidate communication/ and ui/ if they depend on core/)
- [ ] **Extend caching to other tools**: Apply `MtimeFileCache` pattern to additional file-based analyzers
  - Priority: `analyze_error_handling.py`, `analyze_functions.py` (prioritized candidates with highest execution time)
  - Evaluate other file-based analyzers for caching potential
  - Use existing `MtimeFileCache` pattern (already proven effective)

**Files**: 
- **Infrastructure**: `development_tools/tests/domain_mapper.py`, `development_tools/tests/test_file_coverage_cache.py`, `development_tools/tests/dev_tools_coverage_cache.py`
- **Implementation**: `development_tools/tests/analyze_test_coverage.py` (caching added), `development_tools/tests/run_test_coverage.py` (test-file caching integrated)
- **Cache Management**: `development_tools/run_development_tools.py` (`--clear-cache` flag), `development_tools/shared/fix_project_cleanup.py` (cleanup command), `development_tools/shared/service/commands.py` (cleanup handler), `development_tools/shared/cli_interface.py` (cleanup CLI)
- **Documentation**: `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` (caching section updated), `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` (caching section updated)
- **Plan**: `.cursor/plans/caching_exploration_for_development_tools_fb102ab8.plan.md`

---

### Stage 3: Code Quality & Maintenance

#### 3.1 Standardize Logging Across Development Tools
**Status**: PENDING  
**Issue**: Logging is inconsistent, with duplicate and messy log entries.

**Tasks**:
- [ ] Standardize log levels (INFO vs DEBUG vs WARNING)
- [ ] Remove duplicate log entries
- [ ] Demote verbose enhancement messages to DEBUG level
- [ ] Review verbose logging in config validation and package auditing
- [ ] Replace print statements with proper logging (47 files found) - **NOTE**: Print statements in `audit_orchestration.py` for console output during audits are intentional and should remain (they ensure visibility regardless of log level)
- [ ] Add "Top offenders" list to Quick Wins section in AI_PRIORITIES.md

**Files**: All development tools files, especially `report_generation.py`, `analyze_config.py`, `audit_orchestration.py`

#### 3.2 Improve Console Output During Audit Runs
**Status**: ✅ FIXED (2025-12-26)  
**Issue**: No console output during audit runs (logger.info messages not visible due to WARNING log level).

**Resolution (2025-12-26)**:
- ✅ **Fixed**: Added `print()` statements for key audit progress messages
- ✅ **Added**: Console output for audit start, tier progress, completion, and error messages
- ✅ **Result**: Users now see progress regardless of log level setting

**Remaining Tasks** (if needed):
- [ ] Verify no raw dictionary/list dumps occur during tool execution
- [ ] Consider adding progress indicators for long-running tools (if needed)

**Files**: `development_tools/shared/service/audit_orchestration.py` (lines 137-138, 168, 175, 182, 301-314)

#### 3.3 Standardize Function Counting and Complexity Metrics
**Status**: COMPLETE ✅  
**Issue**: Different tools report different numbers (analyze_functions: 153/138/128 vs decision_support: 352/376/321).

**Implementation Complete (2025-12-31)**:
- ✅ **Investigation**: Both tools use `scan_all_functions()` from `analyze_functions`, but used different categorization logic
- ✅ **Root Cause**: `decision_support` had its own `find_complexity_functions()` that filtered functions differently than `analyze_functions`'s `categorize_functions()`
- ✅ **Standardization**: Updated `decision_support` to use `categorize_functions()` from `analyze_functions` for consistency
- ✅ **Updated**: `print_dashboard()` in `decision_support.py` now uses `categorize_functions()` directly
- ✅ **Updated**: `find_complexity_functions()` now uses `categorize_functions()` internally for consistency
- ✅ **Updated**: `_get_canonical_metrics()` comments to clarify that `analyze_functions` is the single source of truth
- ✅ **Result**: Both tools now use the same categorization logic, ensuring consistent metrics

**Files**: `development_tools/reports/decision_support.py`, `development_tools/shared/service/data_loading.py`

#### 3.4 Standardize Error Handling Coverage Metrics
**Status**: PENDING (needs verification with non-zero missing functions)  
**Issue**: Error handling coverage percentage (99.9%) and "functions missing protection" count (2) don't align.

**Verification (2025-12-26)**:
- ✅ **Current Status**: AI_STATUS.md shows "Error Handling Coverage: 100.0% (0 functions without handlers)"
- ✅ **Code Analysis**: 
  - Coverage calculated as: `(functions_with_error_handling / total_functions * 100)` (line 1003 in analyze_error_handling.py)
  - Missing count tracked as: `functions_missing_error_handling` (line 1002)
- ⚠️ **Current State**: Both metrics align (100% coverage, 0 missing) - but issue was about discrepancy when there ARE missing functions
- **Possible explanations**: Issue was resolved, or discrepancy only appears when functions are missing

**Tasks**:
- [ ] Verify metrics align when there ARE missing functions (test with known missing functions)
- [ ] Investigate how error handling coverage percentage is calculated (verified: line 1003)
- [ ] Investigate how "functions missing protection" count is determined (verified: line 1002)
- [ ] Test with non-zero missing functions to verify if discrepancy still exists
- [ ] If discrepancy exists, standardize calculation method
- [ ] Update status reports to show consistent metrics

**Files**: `development_tools/error_handling/analyze_error_handling.py` (lines 1002-1003), `development_tools/shared/service/report_generation.py` (line 2756)

---

### Stage 4: Investigation & Cleanup Tasks

#### 4.1 Investigate Changelog Trim Tooling
**Status**: PENDING  
**Priority**: HIGH  
**Issue**: Changelog check reports "Tooling unavailable (skipping trim)" during audit runs.

**Tasks**:
- [ ] Review `audit_orchestration.py::_check_and_trim_changelog_entries()` implementation
- [ ] Check why `changelog_manager` import fails or is None
- [ ] Verify `ai_development_docs.changelog_manager` module exists
- [ ] Fix import or implementation issue
- [ ] Add proper error handling and logging

**Files**: `development_tools/shared/service/audit_orchestration.py`, `development_tools/docs/fix_version_sync.py`

#### 4.2 Investigate Validation Warnings
**Status**: PENDING  
**Issue**: Several validation warnings need investigation:
- "Only 60/82 manual enhancements found in written file"
- "needs_enhancement" and "new_module" warnings for test files

**Tasks**:
- [ ] Investigate manual enhancements count mismatch
- [ ] Review what triggers "needs_enhancement" and "new_module" flags
- [ ] Determine if test files should be excluded from these checks
- [ ] Update validation logic if needed

**Files**: Validation and enhancement detection logic (likely in `analyze_ai_work.py` or report generation)

#### 4.3 Verify Critical Issues File Creation
**Status**: PENDING (needs decision on resolution approach)  
**Issue**: Console claims "Critical issues saved to: development_tools/critical_issues.txt" but need to verify.

**Verification (2025-12-26)**:
- ✅ **Code Analysis**: 
  - Line 632 in `commands.py`: Prints "Critical issues saved to: {issues_file}" when `prioritize_issues=True`
  - Line 4041 in `report_generation.py`: References `issues_file` from config (default: 'critical_issues.txt')
  - Line 4043: Code checks `if issues_file.exists()` before linking (conditional)
  - Line 4101: `_identify_critical_issues()` method exists but **only returns a list, does NOT write to file**
- ✅ **File Status**: `critical_issues.txt` does not exist in codebase
- ✅ **Root Cause Identified**: **File is NEVER written** - `_identify_critical_issues()` returns issues but no code writes them to file. Message is printed but file creation logic is missing.

**Decision Needed**:
- [ ] Decide if critical issues file is needed/useful
- [ ] If yes: Determine what should be in the file and when it should be created
- [ ] If no: Remove the misleading message
- [ ] Consider alternatives: Include in consolidated report? Add to AI_PRIORITIES? Remove feature entirely?

**Files**: `development_tools/shared/service/report_generation.py` (lines 4041-4045, 4101-4116), `development_tools/shared/service/commands.py` (line 632)

#### 4.4 Investigate Version Sync Functionality
**Status**: PENDING  
**Issue**: Need to understand what version_sync does and what files it covers.

**Tasks**:
- [ ] Investigate what version_sync does
- [ ] Understand its purpose, scope, and ensure it's working correctly
- [ ] Document version synchronization process

**Files**: `development_tools/docs/fix_version_sync.py`

#### 4.5 Investigate development_tools/scripts/ Directory and tool_timings.json Location
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: 
- `development_tools/scripts/` directory contains utility scripts (`measure_tool_timings.py`, `verify_tool_storage.py`)
- `tool_timings.json` is created in `development_tools/reports/` but may belong elsewhere
- Need to determine if these should be moved to project root `scripts/` directory or organized differently

**Tasks**:
- [ ] Investigate purpose of `development_tools/scripts/` directory
- [ ] Review contents: `measure_tool_timings.py`, `verify_tool_storage.py`
- [ ] Determine if these scripts belong in project root `scripts/` instead
- [ ] Investigate `tool_timings.json` location (currently `development_tools/reports/tool_timings.json`)
- [ ] Decide if `tool_timings.json` should be:
  - Moved to `scripts/` directory (if scripts are moved there)
  - Moved to `development_tools/reports/jsons/` subfolder (for consistency with other tool outputs)
  - Kept in current location with justification
- [ ] Update `_save_timing_data()` in `audit_orchestration.py` if location changes
- [ ] Document decision and rationale

**Files**: `development_tools/scripts/measure_tool_timings.py`, `development_tools/scripts/verify_tool_storage.py`, `development_tools/shared/service/audit_orchestration.py` (line 991: `_save_timing_data()`)

#### 4.6 Investigate System Signals Purpose and Redundant Documentation Sync Statement
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: 
- System Signals section in `consolidated_report.txt` (line 105) shows "Documentation has 14 sync issue(s)" which is redundant (already documented in Documentation Sync section)
- Need to evaluate what purpose `system_signals`/`analyze_system_signals` actually serves
- Consider whether it should be eliminated, integrated into snapshot/executive summary, or enhanced

**Tasks**:
- [ ] Review what information `analyze_system_signals` provides that isn't already in other sections
- [ ] Identify redundant information (e.g., documentation sync issues already shown elsewhere)
- [ ] Evaluate options:
  - **Option A**: Eliminate system_signals entirely, integrate unique information into snapshot/executive summary
  - **Option B**: Keep but remove redundant information, focus on unique system health metrics
  - **Option C**: Enhance to provide unique value not available elsewhere
- [ ] Remove redundant "Documentation has X sync issue(s)" from System Signals section (already in Documentation Sync section)
- [ ] If keeping: Clarify what unique value system_signals provides
- [ ] If eliminating: Migrate unique information to appropriate sections (snapshot, executive summary, etc.)
- [ ] Update report generation to reflect decision

**Files**: `development_tools/reports/analyze_system_signals.py`, `development_tools/shared/service/report_generation.py` (System Signals sections), `development_tools/consolidated_report.txt`

#### 4.7 Add Dependency Patterns to AI_PRIORITIES.md and AI_STATUS.md
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Dependency Patterns section exists in `consolidated_report.txt` (lines 90-92) but is missing from `AI_PRIORITIES.md` and `AI_STATUS.md`.

**Tasks**:
- [ ] Add Dependency Patterns section to `AI_STATUS.md` with barebones details (matching current consolidated_report.txt format)
- [ ] Add Dependency Patterns section to `AI_PRIORITIES.md` with recommendations for addressing circular dependencies and high coupling
- [ ] Expand Dependency Patterns section in `consolidated_report.txt` to provide more detail:
  - List specific circular dependency chains (or top N)
  - List modules with high coupling (or top N)
  - Add context about impact and remediation strategies
- [ ] Ensure all three reports have consistent information (with appropriate level of detail for each)
- [ ] Update report generation logic in `report_generation.py` to include dependency patterns

**Files**: `development_tools/shared/service/report_generation.py`, `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.txt`

#### 4.8 Investigate DIRECTORY_TREE.md Regeneration During Audits
**Status**: RESOLVED (2025-12-31)  
**Priority**: MEDIUM  
**Issue**: `DIRECTORY_TREE.md` appears to have been regenerated during the last full audit, but it should only be generated by the `docs` command, not during audits.

**Root Cause**: Using test timestamp logging, identified that `test_main_integration_demo_project` in `tests/development_tools/test_generate_directory_tree.py` was regenerating `DIRECTORY_TREE.md` at 07:24:23 during test runs. The test was attempting to patch `development_tools.config.config.get_project_root` to return `demo_project_root`, but `generate_directory_tree.py` imports config as `from development_tools import config`, so the patch target was incorrect. This caused the test to use the real project root instead of the test fixture directory, leading to file regeneration in the real project.

**Resolution**: Fixed test isolation by correcting the config patch target:
1. Updated `test_main_integration_demo_project` to patch `directory_tree_module.config.get_project_root` (where config is actually imported in the module) instead of `development_tools.config.config.get_project_root`
2. Added fallback patch to `development_tools.config.config.get_project_root` for additional safety
3. Improved safeguard logging in `development_tools/shared/file_rotation.py` with more aggressive DIRECTORY_TREE detection (case-insensitive, multiple pattern checks)
4. Added test timestamp logging hooks (at DEBUG level) to help identify test execution timing issues in the future

The test now properly uses `demo_project_root` fixture and will not write to the real project directory. Existing safeguards in `create_output_file()` provide additional protection if test isolation fails.

**Files**: `tests/development_tools/test_generate_directory_tree.py`, `development_tools/shared/file_rotation.py`, `tests/conftest.py`, `tests/development_tools/conftest.py`

#### 4.9 Investigate and Fix Missing Error Handling Information in AI_STATUS
**Status**: RESOLVED (2025-12-31)  
**Priority**: MEDIUM  
**Issue**: AI_STATUS.md shows only the header `## Error Handling` but no content below it. Error handling information should be displayed but appears to be missing.

**Root Cause**: The report generation logic in `report_generation.py` line 780 had a condition `if missing_error_handlers is not None and missing_error_handlers > 0:` which prevented any content from being displayed when `missing_error_handlers` was 0 (perfect coverage). Additionally, `decorated` was being read from the wrong location (should use `get_error_field()` helper to access from `details` in standard format).

**Resolution**: Fixed `development_tools/shared/service/report_generation.py` lines 780-792 to:
- Always show missing error handling count (even when 0)
- Use `get_error_field()` helper to correctly access `functions_with_decorators` from standard format data
- Display error handling coverage and functions with error handling when available

The Error Handling section now displays complete information matching consolidated_report.txt.

**Files**: `development_tools/shared/service/report_generation.py`, `development_tools/AI_STATUS.md`, `development_tools/consolidated_report.txt`, `development_tools/reports/analysis_detailed_results.json`

#### 4.11 Investigate Test Coverage Inclusion/Exclusion Consistency
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Need to determine whether overall test coverage includes `development_tools` test coverage or excludes it, and most importantly whether it does so consistently across all reports and tools.

**Tasks**:
- [ ] Review how test coverage is calculated in `run_test_coverage.py` and `analyze_test_coverage.py`
- [ ] Check if `development_tools/` is included or excluded from overall coverage calculations
- [ ] Verify consistency across:
  - Overall project coverage reports
  - Development tools coverage reports (separate tracking)
  - Coverage metrics in `AI_STATUS.md`
  - Coverage metrics in `consolidated_report.txt`
  - Coverage metrics in `TEST_COVERAGE_REPORT.md`
- [ ] Document the inclusion/exclusion policy clearly
- [ ] Ensure all tools and reports follow the same policy consistently
- [ ] Update documentation to clarify coverage calculation methodology

**Files**: `development_tools/tests/run_test_coverage.py`, `development_tools/tests/analyze_test_coverage.py`, `development_tools/shared/service/report_generation.py`, `development_tools/AI_STATUS.md`, `development_docs/TEST_COVERAGE_REPORT.md`

#### 4.11 Investigate htmlcov/ Directory Recreation
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: `htmlcov/` directory keeps being recreated as an empty top-level directory. This suggests coverage HTML report generation is being triggered but not completing, or cleanup is removing files but not the directory.

**Tasks**:
- [ ] Review coverage report generation in `run_test_coverage.py` and `generate_test_coverage_report.py`
- [ ] Check if HTML report generation is being triggered but failing silently
- [ ] Verify if cleanup logic is removing HTML files but leaving the directory
- [ ] Check `.gitignore` to ensure `htmlcov/` is properly ignored
- [ ] Identify what triggers HTML report generation and why it's creating empty directories
- [ ] Fix the root cause (either complete HTML generation or prevent empty directory creation)
- [ ] Add cleanup logic to remove empty `htmlcov/` directories if HTML generation is disabled

**Files**: `development_tools/tests/run_test_coverage.py`, `development_tools/tests/generate_test_coverage_report.py`, `.gitignore`

#### 4.13 Investigate .coverage File Locations
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: `.coverage` files are appearing in both root directory and `development_tools/tests/` directory. This suggests coverage data collection is happening in multiple locations with different working directories.

**Tasks**:
- [ ] Review pytest coverage configuration in `pytest.ini` and `conftest.py` files
- [ ] Check if `--cov` arguments specify different data files or working directories
- [ ] Identify which test runs create `.coverage` in root vs `development_tools/tests/`
- [ ] Review `run_test_coverage.py` to see how coverage data file location is configured
- [ ] Determine if separate coverage files are intentional (separate tracking) or accidental
- [ ] Standardize coverage data file location (either root or `development_tools/tests/`, not both)
- [ ] Update `.gitignore` to ensure both locations are ignored if needed
- [ ] Document the intended coverage data file location

**Files**: `pytest.ini`, `tests/conftest.py`, `development_tools/tests/run_test_coverage.py`, `.gitignore`, `.coverage`, `development_tools/tests/.coverage`

#### 4.13 Investigate Coverage File Creation in development_tools/tests/
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Coverage data files (`.coverage_dev_tools.*`, `.coverage_parallel.*`) are being created in `development_tools/tests/` instead of in `tests/` like before. This suggests a change in working directory or coverage configuration.

**Tasks**:
- [ ] Review recent changes to coverage configuration or test execution
- [ ] Check if working directory changed when running development tools tests
- [ ] Review `run_test_coverage.py` to see how coverage data file paths are determined
- [ ] Check if `--cov` arguments or `COVERAGE_FILE` environment variable changed
- [ ] Compare current behavior with historical behavior (when files were created in `tests/`)
- [ ] Determine if this is intentional (separate dev tools coverage) or accidental
- [ ] If intentional: Document the separation and ensure `.gitignore` covers both locations
- [ ] If accidental: Fix coverage configuration to use `tests/` directory as before
- [ ] Clean up existing coverage files in `development_tools/tests/` if location is corrected

**Files**: `development_tools/tests/run_test_coverage.py`, `pytest.ini`, `tests/conftest.py`, `.gitignore`, `development_tools/tests/.coverage*`

#### 4.14 Investigate Fixture Status File Regeneration
**Status**: PENDING  
**Priority**: MEDIUM  
**Issue**: Status files in `tests/fixtures/development_tools_demo/` (`AI_PRIORITIES.md`, `AI_STATUS.md`, `consolidated_report.txt`) were last regenerated over a week ago. These fixture files should be updated when the demo project structure changes or when status file formats change, but they may not be getting regenerated as expected.

**Tasks**:
- [ ] Check when fixture status files were last modified (file timestamps)
- [ ] Review if there's a process or script that should regenerate these files
- [ ] Determine if fixture files should be updated:
  - When demo project structure changes
  - When status file formats change
  - During fixture setup/validation
  - Manually when needed
- [ ] Check if fixture files are used by tests and if stale files cause issues
- [ ] Create or update process to regenerate fixture status files when needed
- [ ] Document when and how fixture status files should be updated

**Files**: `tests/fixtures/development_tools_demo/AI_PRIORITIES.md`, `tests/fixtures/development_tools_demo/AI_STATUS.md`, `tests/fixtures/development_tools_demo/consolidated_report.txt`, `tests/development_tools/conftest.py`

#### 4.15 Investigate and Fix test_audit_status_updates.py Memory Leak
**Status**: PENDING  
**Priority**: HIGH  
**Issue**: `tests/development_tools/test_audit_status_updates.py` is completely commented out as it appears to be the source of a memory leak. The test file needs investigation to determine if it can be fixed or requires complete replacement.

'tests\development_tools\test_audit_tier_comprehensive.py' has also been completely commented out for the same reason.

**Current State**:
- Entire test file (375 lines) is commented out
- File contains tests for verifying status files only update at end of audit
- Tests use extensive mocking and file tracking which may be causing memory issues
- Tests were disabled due to memory leak concerns

**Investigation Tasks**:
- [ ] Review commented-out test code to understand what it was testing
- [ ] Identify potential memory leak sources:
  - [ ] File tracking mechanisms (`create_output_file` tracking)
  - [ ] Mock object creation and retention
  - [ ] File system operations in temp directories
  - [ ] Service instance creation and cleanup
- [ ] Check if memory leak is due to:
  - [ ] Test isolation issues (files not cleaned up)
  - [ ] Mock objects not being garbage collected
  - [ ] Service instances retaining references
  - [ ] File tracking data structures growing unbounded
- [ ] Evaluate options:
  - [ ] **Option A**: Fix existing tests by addressing memory leak sources
  - [ ] **Option B**: Rewrite tests with simpler approach (less mocking, better cleanup)
  - [ ] **Option C**: Replace with integration tests that verify behavior differently
  - [ ] **Option D**: Remove tests if functionality is covered elsewhere
- [ ] If fixing: Implement proper cleanup (fixtures, teardown, context managers)
- [ ] If rewriting: Design simpler test approach that avoids memory issues
- [ ] If replacing: Create new tests that verify status file update behavior without memory overhead
- [ ] Verify no memory leaks with new/fixed tests (run with memory profiler)
- [ ] Ensure test isolation (tests don't affect each other or real project files)

**Files**: `tests/development_tools/test_audit_status_updates.py`, `development_tools/shared/service/audit_orchestration.py`, `development_tools/shared/service/report_generation.py`

**Note**: These tests verify important behavior (status files only written at end of audit), so functionality should be preserved even if implementation changes.

#### 4.16 Investigate and Verify Pyright "Duplicate Declaration" Fixes
**Status**: PENDING  
**Priority**: HIGH  
**Issue**: Pyright reports "duplicate declaration" errors for several functions/variables. Initial fixes were attempted but reverted - full investigation needed to determine if these are true duplicates or serve different purposes.

**Current State (2025-12-31)**:
1. **`analyze_module_dependencies.py`**: TWO `generate_dependency_report()` functions exist:
   - First function (line 124): Uses `logger.info()`, simpler implementation, focuses on logging
   - Second function (line 384): Uses `print()`, includes `enhancement_status` tracking, more comprehensive
   - **User feedback**: Should use loggers not print, needs proper investigation
2. **`report_generation.py`**: Renamed second `complexity_bullets` variable to `high_complexity_bullets` (line 2256). These are in different code paths (`if critical_complex` vs `elif high_complex`), so NOT true duplicates - rename was correct.
3. **`run_test_coverage.py`**: Renamed second `FakeResult` class to `FakeResultException` (line 1353). These are in different exception handlers (`TimeoutExpired` vs general `Exception`), so NOT true duplicates - rename was correct.
4. **`tool_wrappers.py`**: Multiple duplicate method declarations exist:
   - First set (lines 460-842): More complete error handling (stderr logging, `script_succeeded` checks)
   - Second set (lines 1037+): Simpler implementations, less error handling
   - **User feedback**: Edit was undone, full investigation appropriate

**Investigation Tasks**:
- [ ] **Investigate `generate_dependency_report()` duplicates**: 
  - [ ] Compare both implementations (line 124 vs line 384) to identify differences
  - [ ] Determine if both are needed or if one should be removed/merged
  - [ ] If keeping one: Update to use loggers instead of print() as per user preference
  - [ ] If merging: Combine best features (logger-based output + enhancement_status tracking)
  - [ ] Check git history to understand why both exist
  - [ ] Document decision and rationale
- [ ] **Verify `complexity_bullets` rename**: Confirmed separate code paths - no further action needed.
- [ ] **Verify `FakeResult` rename**: Confirmed separate exception handlers - no further action needed.
- [ ] **Investigate `tool_wrappers.py` duplicate methods**: 
  - [ ] Compare all duplicate method pairs:
    - [ ] `run_analyze_error_handling()` (line 460 vs 1037) - first has stderr logging and `script_succeeded` checks
    - [ ] `run_analyze_documentation_sync()` (line 526 vs 1136)
    - [ ] `run_analyze_path_drift()` (line 601 vs 1286)
    - [ ] `run_generate_legacy_reference_report()` (line 702 vs 1502)
    - [ ] `run_analyze_legacy_references()` (line 842 vs 1674)
  - [ ] Determine if duplicates are truly identical or serve different purposes
  - [ ] If identical: Remove second set completely
  - [ ] If different: Merge best features or document why both are needed
  - [ ] Clean up any orphaned code

**Files**: 
- `development_tools/imports/analyze_module_dependencies.py`
- `development_tools/shared/service/report_generation.py`
- `development_tools/tests/run_test_coverage.py`
- `development_tools/shared/service/tool_wrappers.py`

**Risk**: Medium - Duplicate code may indicate missing functionality or code that needs consolidation.

#### 4.17 Investigate Intermittent Low Coverage Percentage Warning
**Status**: PENDING  
**Priority**: HIGH  
**Issue**: Recurring but intermittent warning: "Coverage percentage (47.2%) is unexpectedly low. Expected ~70-75%. This may indicate parallel coverage data was not included." Warning appears sporadically during coverage generation, suggesting a race condition or timing issue with parallel coverage data collection/merging.

**Warning Details**:
- Coverage percentage: 47.2% (expected ~70-75%)
- Parallel file existed before cleanup: True
- No_parallel file existed before cleanup: True
- Shard files found: 0
- Issue is intermittent (not consistently reproducible)

**Potential Root Causes**:
- Parallel coverage data files not being properly merged before analysis
- Race condition in coverage file cleanup/merging process
- Timing issue where coverage analysis runs before parallel data is fully collected
- Shard files (from pytest-xdist) not being detected or included in merge
- Coverage data file paths or naming inconsistencies

**Investigation Tasks**:
- [ ] Review coverage data collection and merging logic in `run_test_coverage.py`
- [ ] Check timing of coverage file cleanup vs. analysis execution
- [ ] Investigate why shard files are found as 0 when parallel execution occurred
- [ ] Review pytest-xdist coverage data file naming and detection logic
- [ ] Check if coverage file paths are consistent between parallel and no_parallel runs
- [ ] Review coverage data merging process for parallel test execution
- [ ] Add detailed logging around coverage file detection and merging
- [ ] Verify coverage file existence checks are working correctly
- [ ] Test with controlled parallel execution to reproduce issue consistently
- [ ] Check if issue correlates with specific test patterns or test counts
- [ ] Review coverage data file cleanup timing and ensure it happens after merge

**Potential Fixes**:
- [ ] Ensure coverage data merge completes before analysis runs
- [ ] Add retry logic or wait mechanism for coverage file availability
- [ ] Fix shard file detection if it's not finding parallel coverage files
- [ ] Improve coverage file path resolution for parallel execution
- [ ] Add validation to verify all expected coverage files exist before analysis
- [ ] Enhance error handling and logging around coverage data collection

**Files**: 
- `development_tools/tests/run_test_coverage.py` (coverage data collection and merging)
- `development_tools/tests/analyze_test_coverage.py` (coverage analysis that triggers warning)
- `development_tools/tests/generate_test_coverage_report.py` (coverage report generation)
- `pytest.ini` (pytest-xdist and coverage configuration)
- `tests/conftest.py` (coverage configuration)

**Risk**: High - Incorrect coverage percentages reduce trust in metrics and can mask actual coverage issues.

---

### Stage 5: Future Enhancements (Low Priority)

#### 5.1 Convert consolidated_report.txt to .md format
**Status**: PENDING  
**Effort**: Small  
**Description**: Change to `consolidated_report.md` for better markdown rendering and consistency.

#### 5.2 Expand consolidated report detail
**Status**: PENDING  
**Effort**: Medium  
**Description**: Consolidated report should contain at least as much detail as `AI_STATUS.md`, ideally more.

#### 5.3 Create Unused Imports Cleanup Module
**Status**: PENDING  
**Issue**: Need cleanup functionality with categorization and cleanup recommendations.

**Tasks**:
- [ ] Create categorization logic (missing error handling, missing logging, type hints, utilities, safe to remove)
- [ ] Add category-based reporting to unused imports analysis
- [ ] Create `imports/fix_unused_imports.py` for cleanup operations
- [ ] Add cleanup recommendation generation to unused imports report
- [ ] Consider `--categorize` flag for unused imports checker

**Files**: `development_tools/imports/analyze_unused_imports.py`, `development_tools/imports/fix_unused_imports.py` (to be created)

#### 5.4 Enhance Documentation Overlap Analysis
**Status**: PENDING  
**Issue**: Currently reports section overlaps but may not provide actionable insights. Specific consolidation opportunities: Development Workflow (27 files), Testing (3 files).

**Tasks**:
- [ ] Review identified consolidation opportunities
- [ ] Create consolidation plan for identified file groups
- [ ] Enhance to provide actionable insights beyond section overlaps
- [ ] Improve detection of actual issues vs. false positives

**Files**: `development_tools/docs/analyze_documentation.py`

#### 5.5 Enhance AI Work Validation
**Status**: PENDING  
**Issue**: Currently reports "GOOD - keep current standards" but may not provide actionable insights.

**Tasks**:
- [ ] Investigate what AI Work Validation currently looks for
- [ ] Enhance to provide actionable insights beyond status messages
- [ ] Add specific recommendations for maintaining code quality standards
- [ ] Ensure it doesn't duplicate logic from domain-specific tools

**Files**: `development_tools/ai_work/analyze_ai_work.py`

#### 5.6 Automate TODO Sync Cleanup
**Status**: PENDING  
**Issue**: 3 completed entries in TODO.md need review. Functionality exists but could be improved.

**Tasks**:
- [ ] Review current TODO sync implementation
- [ ] Enhance detection to better identify completed entries
- [ ] Add automated cleanup option (with dry-run mode)
- [ ] Improve reporting of what needs manual review vs. auto-cleaned
- [ ] Document TODO sync workflow and best practices

**Files**: `development_tools/docs/fix_version_sync.py`

#### 5.7 Investigate Legacy Reference Count Discrepancy
**Status**: RESOLVED (2025-12-31)  
**Effort**: Small  
**Issue**: Legacy reference report shows fewer issues than before (7 files/20 markers vs 8 files/28 markers previously). No legacy code was removed, so count should not have decreased.

**Root Cause**: The 8th file was a temporary test fixture (`tests/data/tmp*/demo_project/legacy_code.py`) that was being included in earlier scans but is now correctly excluded. The legacy scanner correctly excludes `tests/data/` directory per standard exclusions.

**Resolution**: This is correct behavior - temporary test fixture files should not be counted in legacy reference reports. The count decrease reflects improved exclusion logic, not a bug. No action needed.

**Files**: `development_tools/legacy/analyze_legacy_references.py`, `development_docs/LEGACY_REFERENCE_REPORT.md`

#### 5.8 Address Missing Category Markers Trend
**Status**: RESOLVED (2025-12-31)  
**Effort**: Medium  
**Issue**: Missing category markers count is increasing (316 → 332 tests) despite not making many test changes. This suggests either new tests are being added without markers, or detection is improving.

**Root Cause**: The test marker analyzer was including temporary pytest files in `tests/data/pytest-tmp-*` directories. These are temporary files created during parallel test execution and should be excluded from marker analysis, just like they are excluded from legacy reference scanning.

**Resolution**: Updated `development_tools/tests/analyze_test_markers.py` to exclude temporary pytest files in `tests/data/` directory (specifically `pytest-tmp-*` and `pytest-of-*` patterns). The analyzer now correctly skips these temporary files, matching the exclusion behavior of the legacy reference scanner.

**Files**: `development_tools/tests/analyze_test_markers.py`, `development_tools/tests/fix_test_markers.py`

#### 5.9 Create New Tools to Fill Identified Gaps

#### 5.10 Explore Integrating Memory Profiler Functionality into Development Tools
**Status**: PENDING  
**Priority**: LOW  
**Effort**: Medium  
**Issue**: Memory profiler (`scripts/testing/memory_profiler.py`) provides valuable test memory analysis capabilities that could be integrated into the development tools suite for ongoing monitoring and optimization.

**Current Capabilities** (in `scripts/testing/memory_profiler.py`):
- Real-time memory monitoring during test execution
- Per-test memory usage tracking
- Worker process monitoring (pytest-xdist)
- Memory spike detection and automatic termination
- Partial results saving for long-running test suites
- Worker test assignment extraction
- Cross-run analysis and pattern identification

**Potential Integration Options**:
1. **New Analysis Tool**: `analyze_test_memory_usage.py`
   - Run memory profiling during test execution
   - Generate memory usage reports (per-test, per-module, trends)
   - Identify memory-heavy tests and patterns
   - Provide recommendations for optimization
   - Could be Tier 2 or Tier 3 tool

2. **Enhanced Test Coverage Tool**: Extend `run_test_coverage.py` or `generate_test_coverage_report.py`
   - Add memory usage metrics alongside coverage metrics
   - Track memory trends over time
   - Identify tests with both low coverage and high memory usage

3. **Standalone Monitoring Tool**: `monitor_test_resources.py`
   - Monitor memory, CPU, and other resources during test execution
   - Provide real-time alerts for resource exhaustion
   - Generate resource usage reports

**Considerations**:
- Memory profiling adds overhead to test execution
- Should be optional (not run by default in quick audits)
- May require `psutil` dependency (already used in memory_profiler.py)
- Integration should preserve existing standalone functionality
- Consider whether this belongs in development tools or remains as testing utility

**Tasks**:
- [ ] Evaluate if memory profiling belongs in development tools or should remain as testing utility
- [ ] If integrating, decide on approach (new tool vs. enhancement to existing tools)
- [ ] Design tool interface and output format (JSON + report)
- [ ] Implement memory profiling tool following development tools patterns
- [ ] Add tests using synthetic fixture project
- [ ] Update tool metadata and documentation
- [ ] Consider adding to appropriate audit tier (likely Tier 2 or Tier 3)

**Files**: `scripts/testing/memory_profiler.py`, `development_tools/` (new tool location TBD)
**Status**: PENDING  
**Effort**: Large  
**Description**: Implement new tools based on gap analysis (29 gaps identified across 6 domains).

**Gap Categories**:
- Documentation Domain (7 gaps): H3 heading sync, markdown link validation, cross-reference accuracy, etc.
- Code Quality Domain (6 gaps): Type hint coverage, docstring quality, code duplication, etc.
- Testing Domain (6 gaps): Test isolation verification, coverage gap analysis, etc.
- Configuration & Environment Domain (5 gaps): Environment health checks, config validation, etc.
- AI & Prompt Domain (3 gaps): Prompt validation, template consistency, etc.
- Integration & Workflow Domain (2 gaps): E2E workflow validation, integration point analysis

**Implementation Approach**:
- Prioritize gaps by value and effort
- Create tools following established patterns (analyze_*, generate_*, fix_*)
- Integrate into audit workflow where appropriate
- Add tests using synthetic fixture project
- Update tool_metadata.py and documentation

---

## Work Organization

### Immediate Focus (This Week)
1. **Improve Recommendation Quality (Stage 1.1)** - HIGH PRIORITY, improves trust and actionability
2. **Improve Development Tools Test Coverage (Stage 1.2)** - HIGH PRIORITY, target 60%+
3. **Standardize Logging (Stage 3.1)** - Improves developer experience

### Short Term (Next 2 Weeks)
1. ✅ Fix Config Validation Issues (Stage 2.1) - COMPLETE
2. ✅ Standardize Function Metrics (Stage 3.3) - COMPLETE
3. **Investigate and Fix test_audit_status_updates.py Memory Leak (Stage 4.15)** - HIGH PRIORITY, test file completely commented out
4. **Enhance Quick Wins Recommendations with File Details (Stage 1.3)** - MEDIUM PRIORITY, improves actionability
5. Investigate "Symbol: unused-import" bullet points (Stage 2.2) - Small effort
6. Investigate Legacy Reference Count Discrepancy (Stage 5.7) - Small effort, needs investigation
7. Enhance tool analysis capabilities (Stage 2.3-2.8)
8. Standardize metrics (Stage 3.4)
9. Investigate and fix validation warnings (Stage 4.1-4.2)

### Medium Term (Next Month)
1. Complete tool enhancements (Stage 2)
2. Complete code quality improvements (Stage 3)
3. Complete investigation tasks (Stage 4)
4. Improve console output (Stage 3.2)

### Long Term (Future)
1. Future enhancements (Stage 5)
2. Create unused imports cleanup module (Stage 5.3) - Moved to lower priority
3. Enhance Documentation Overlap Analysis (Stage 5.4) - Moved to lower priority
4. Enhance AI Work Validation (Stage 5.5) - Moved to lower priority
5. Automate TODO Sync Cleanup (Stage 5.6) - Moved to lower priority
6. Address Missing Category Markers Trend (Stage 5.8) - Monitor and address
7. New tool creation based on gap analysis (Stage 5.9)
8. Explore integrating memory profiler functionality (Stage 5.10) - Evaluate integration approach

---

## Notes

- **Testing**: All new work should include tests using the synthetic fixture project at `tests/fixtures/development_tools_demo/`
- **Documentation**: Update both `AI_DEVELOPMENT_TOOLS_GUIDE.md` and `DEVELOPMENT_TOOLS_GUIDE.md` when adding/changing tools
- **Tool Metadata**: Update `development_tools/shared/tool_metadata.py` when adding new tools or changing tiers
- **Naming Conventions**: Follow established patterns: `analyze_*` (read-only), `generate_*` (create artifacts), `fix_*` (cleanup/repair)
- **Output Storage**: Use standardized storage via `development_tools/shared/output_storage.py` for all tool results

---

## Related Documents

- `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V2.md` - Previous version with detailed historical context
- `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md` - AI-facing tool guide
- `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` - Human-facing tool guide
- `TODO.md` - Project-wide TODO list

