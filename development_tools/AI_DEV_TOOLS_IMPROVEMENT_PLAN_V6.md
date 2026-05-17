# AI Development Tools — Improvement Roadmap V6

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Forward-looking backlog for `development_tools/` after V5  
> **Style**: Direct, concise, action-oriented  
> **Last Updated**: 2026-05-17  
> **Supersedes**: `archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md` for active planning. Keep V4 and prior V5 snapshots for detailed checkbox history.

## Authoritative sources

Use this file for **planning and prioritization** only.

Use generated files for live metrics:

- `development_tools/AI_STATUS.md`
- `development_tools/AI_PRIORITIES.md`
- `development_tools/CONSOLIDATED_REPORT.md`
- `development_docs/TEST_COVERAGE_REPORT.md`
- `development_docs/LEGACY_REFERENCE_REPORT.md`

After running:

```powershell
python development_tools/run_development_tools.py audit
python development_tools/run_development_tools.py audit --full
python development_tools/run_development_tools.py audit --full --dev-tools-only
```

prefer the generated outputs over any numeric examples in this plan.

---

## 1. Current working priorities

### 1.1 Next execution slice

1. **Continue targeted dev-tools test performance work.**
   - The major slowdown is not collection count; it is per-test setup.
   - `temp_project_copy` was confirmed as the main cost driver.
   - Module-scoped fixture overrides have already helped.
   - Next best targets: `test_report_generation_quick_wins.py` and other high-count files using `temp_project_copy`.

2. **Continue targeted dev-tools coverage work only where it buys down real risk.**
   - Use live `AI_PRIORITIES.md` and `TEST_COVERAGE_REPORT.md`.
   - Prefer central service/orchestration paths over percentage-only tests.
   - Keep opportunistic `tests/development_tools/test_config.json` migration when touching analyzer-style tests.

3. **Keep portability cleanup active.**
   - `core.logger` coupling is already removed.
   - Remaining work is broader implicit MHM assumptions:
     - hardcoded package names,
     - inconsistent project-root resolution,
     - config-required assumptions,
     - static-tool packaging assumptions.

4. **Keep `pip-audit` warning in monitor mode.**
   - Current known watch item: `pip 26.0.1` / `CVE-2026-3219`.
   - Do not churn dependencies solely for a no-fixed-version advisory.

### 1.2 Current priority tiers

| Tier | Work |
|---|---|
| **Active** | Dev-tools test performance; targeted dev-tools coverage; portability / project-independence cleanup |
| **Medium** | Domain-marker analysis in `analyze_test_markers`; portability validation against minimal external projects; validation-warning cleanup if noisy |
| **Deferred** | Coverage-cache numeric benchmarks; external-tool expansion; TODO-sync workflow polish; gap-analysis expansion; memory profiler; arbitrary audit scopes |
| **Monitoring only** | Low-coverage warning recurrence; `pip-audit` no-fix advisory; example-marker/doc-overlap regressions; legacy-reference regressions |

---

## 2. Active backlog

### 2.1 Dev-tools test performance

**Status**: Active.

**Problem**: `tests/development_tools/` is slow mainly because setup is expensive, especially function-scoped `temp_project_copy`.

**Current evidence**:

- `pytest --collect-only -q -m "not e2e" tests/development_tools/` selected about **1479/1480** tests during the May 2026 investigation.
- The collection count stayed stable between May 11 and May 16.
- The wall-clock slowdown came from setup, not more tests.
- A targeted slice showed setup-heavy tests dominating runtime.
- Root cause: function-scoped `temp_project_copy` copies `tests/fixtures/development_tools_demo` once per test for hundreds of tests.
- `measure_tool_timings.py` profiles audit-tool runtime, not pytest runtime. Do not use it as the primary test-suite performance profiler.

**Already done**:

- Extracted `temp_project_copy_paths`.
- Added module-scoped `temp_project_copy` overrides in:
  - `test_audit_orchestration_helpers.py`
  - `test_commands_additional_helpers.py`
  - `test_data_loading_helpers.py`
  - `test_report_generation_helpers_pure.py`
- Kept `test_fix_project_cleanup.py` function-scoped because shared mutation caused failures under module scope.
- Confirmed large improvement in the targeted four-module run.

**Next actions**:

- Review `test_report_generation_quick_wins.py` for safe module-scoped `temp_project_copy`.
- Review other high-count modules that request `temp_project_copy`.
- Split pure helper tests so they do not request `temp_project_copy`.
- Mark remaining expensive integration-style tests as `slow` where appropriate.
- Re-run:

```powershell
python run_tests.py --mode development_tools --durations-all
```

and the targeted hot-module slice:

```powershell
python -m pytest tests/development_tools/test_audit_orchestration_helpers.py tests/development_tools/test_report_generation_quick_wins.py tests/development_tools/test_tool_wrappers_branch_paths.py tests/development_tools/test_fix_project_cleanup.py tests/development_tools/test_generate_consolidated_report.py tests/development_tools/test_commands_additional_helpers.py -q --durations=20 -o addopts= -m "not e2e"
```

---

### 2.2 Targeted dev-tools coverage

**Status**: Active, but do not chase percentage-only tests.

**Current state**:

- V4’s 60% floor is already met.
- Recent slices raised dev-tools coverage into the mid-to-high 60s depending on audit timing.
- The useful question is now: **which uncovered paths are risky enough to test next?**

**Preferred targets**:

- `development_tools/shared/service/commands.py`
- `development_tools/shared/service/audit_orchestration.py`
- `development_tools/shared/service/tool_wrappers.py`
- `development_tools/shared/service/data_loading.py`
- currently low-coverage helpers surfaced by live `TEST_COVERAGE_REPORT.md`

**Already done**:

- Added focused coverage tests for command helpers, audit orchestration helpers, module-dependency generation, tool timing, tool storage, version-sync TODO helpers, static-check sharding/cache behavior, documentation overlap, and test-marker domain summary paths.

**Next actions**:

- Pick targets from live `AI_PRIORITIES.md` and `TEST_COVERAGE_REPORT.md`.
- Prefer central service chokepoints and brittle branch paths.
- Migrate remaining analyzer-style tests to `tests/development_tools/test_config.json` when touching them.
- Avoid long duplicated module lists in this plan.

---

### 2.3 Dev-tools portability and project independence

**Status**: Active.

**Goal**: Make `development_tools/` capable of running against MHM and against a minimal external project without importing MHM runtime modules or relying on MHM-specific assumptions.

#### 2.3.1 Remove `core.logger` dependency

**Status**: Done.

**Completed**:

- Added `development_tools/shared/logging.py`.
- Replaced `core.logger` imports with `get_dev_tools_logger`.
- Updated import-boundary checks so any `core.*` import inside `development_tools/` fails analysis.
- Updated policy tests, guide references, `.cursor/rules/dev_tools.mdc`, and channel logger messaging.
- Added portability smoke coverage for a minimal fake project and subprocess import check.
- Verified `python development_tools/run_development_tools.py audit --quick`.

**Do not reopen unless regression occurs.**

#### 2.3.2 Eliminate remaining implicit MHM assumptions

**Status**: Active.

**Open work**:

- Audit and remove:
  - hardcoded package names,
  - direct `core.*` imports,
  - inconsistent project-root resolution,
  - config-required assumptions,
  - MHM-specific strings in generic dev-tools output.
- Standardize:
  - all tools rely on resolved `project_root`,
  - package detection is config-driven,
  - external-project assumptions are explicit and tested.
- Validate:
  - dev tools run against MHM,
  - dev tools run against a minimal fake project,
  - audit outputs do not assume MHM package layout unless config says so.

#### 2.3.3 Static tooling and packaging parity

**Status**: Medium priority.

**Open work**:

- Keep Pyright/Ruff structural parity tests.
- Treat diagnostic-count parity as optional and tolerance-gated.
- Validate behavior in a minimal external repo.
- Ensure static-check config dependencies invalidate the right caches.
- Keep periodic full-project Pyright runs because sharded Pyright can miss cross-package diagnostics.

---

### 2.4 Domain-marker analysis

**Status**: Medium priority.

**Goal**: Extend `analyze_test_markers` so tests can be checked for domain-based markers in addition to category markers.

**Already done**:

- Added `domain_attribution_summary` / JSON details support.
- Added tests for domain attribution behavior.

**Open work**:

- Define canonical domain marker taxonomy and config location.
- Integrate with `domain_mapper` / `TEST_PLAN.md` guidance.
- Decide which tests require domain markers and which are exempt.
- Report missing domain markers without creating noisy false positives.
- Add policy tests once the rule is stable.

---

### 2.5 Validation warning cleanup

**Status**: Low / medium, only if noisy.

**Open work**:

- Review `needs_enhancement` and `new_module` triggers.
- Decide whether test files should be excluded.
- Tighten recommendations so warnings are actionable rather than generic.

---

### 2.6 Example-marker checker

**Status**: Partial; advisory only.

**Already done**:

- Added `example_marker_validation.py`.
- Added `--check-example-markers` on `analyze_documentation_sync.py`.
- Expanded scan paths to approved documentation sets.
- Suppressed changelog-style false-positive heading noise.
- Added JSON true-positive coverage.

**Open work**:

- Tighten heuristics before making it a default gate.
- Validate headings such as `Examples:`, `Example Usage:`, and `Example Code:` beyond Markdown `##` patterns.
- Report file/line details in consolidated output if promoted from advisory.
- Reopen only if future audits show missed true examples or renewed noise.

---

### 2.7 Documentation overlap analysis

**Status**: Mostly complete; monitor for real duplicate-content problems.

**Already done**:

- Generic numbered headings are filtered.
- Expected boilerplate headings are excluded.
- Configured paired-doc groups and specialized testing guides are skipped in consolidation recommendations.

**Open work**:

- Reopen only if future audits show real duplicated content outside paired/specialized docs.
- Improve actionable insight if a new noisy class appears.

---

### 2.8 System signals purpose and redundancy cleanup

**Status**: Deferred / optional.

**Decision**: Keep the tool.

**Open work**:

- Further trim or merge with doc-sync overlap only if duplicate metrics reappear.
- Clarify scope in reports if future generated output is confusing.

---

### 2.9 TODO sync cleanup automation

**Status**: Partial; low priority.

**Already done**:

- `sync-todo --dry-run` prints a dry-run report.
- `sync-todo --apply` removes auto-cleanable completed checklist lines.
- `--dry-run` and `--apply` are mutually exclusive.

**Open work**:

- Broader workflow docs if needed.
- Optional changelog cross-check before apply remains a human responsibility.

---

## 3. Deferred design/backlog items

These are real ideas, but they should not compete with the active slices unless the project focus changes.

### 3.1 Coverage-cache numeric benchmark

**Status**: Deferred.

**Goal**: Capture stable local numbers comparing full vs domain-filtered coverage runs.

**Benchmark recipe**:

```powershell
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel }
```

Also compare full-audit cache behavior with and without `--clear-cache` / domain-cache options where appropriate.

### 3.2 External-tool expansion

**Status**: Deferred.

**Already integrated**:

- Bandit
- pip-audit

**Possible future tools**:

- Radon
- pydeps
- vulture
- pre-commit
- deeper Ruff usage

**Rule**: Do not add tools just to add tools. Each one needs clear signal, acceptable runtime, metadata, tests, docs, and audit-tier placement.

### 3.3 Gap-analysis tool expansion

**Status**: Deferred / large.

**Potential categories**:

- Documentation
- Code quality
- Testing
- Configuration/environment
- AI/prompt
- Integration/workflow

Use `module-refactor-candidates` and priorities JSON as the practical current gap signal until a broader matrix is justified.

### 3.4 Memory profiler integration

**Status**: Deferred.

**Source**: `scripts/testing/memory_profiler.py`.

**Decision needed**:

- Integrate as a new tool,
- enhance an existing tool,
- keep standalone,
- or retire.

### 3.5 Refactor `report_generation.py` and `run_test_coverage.py`

**Status**: Deferred; implement only in small steps.

**Possible split for `report_generation.py`**:

- Tier 3 helpers
- `AI_STATUS` builder
- `AI_PRIORITIES` builder
- `CONSOLIDATED_REPORT` builder
- downstream action item helpers

**Possible split for `run_test_coverage.py`**:

- pytest argv construction
- shard merge logic
- domain cache
- outcome classification
- coverage metric regeneration

### 3.6 Arbitrary audit scope

**Status**: Deferred / design-first.

**Goal**: Audit any repo subtree, not only full repo vs `development_tools/`.

**Hard part**: tools do not uniformly respect one scan root. A simple CLI flag is not enough.

**Possible future shape**:

```powershell
python development_tools/run_development_tools.py audit --full --audit-scope communication/
```

Only proceed after design sign-off.

---

## 4. Monitoring-only items

### 4.1 Intermittent low coverage warning

**Status**: Monitoring.

Reopen only if generated coverage artifacts show suspicious low percentages.

### 4.2 Comprehensive audit status tests

**Status**: Deferred.

Re-enable `tests/development_tools/test_audit_tier_comprehensive.py` only if a narrow mocked subset is worth the maintenance cost.

### 4.3 pip-audit no-fix advisory

**Status**: Monitoring.

Known item: `pip 26.0.1` / `CVE-2026-3219` with no fixed version reported at the time of the latest plan notes.

Do not change dependencies solely for this advisory until a trusted fixed version or explicit remediation policy exists.

### 4.4 Legacy reference regressions

**Status**: Monitoring.

Current generated legacy reports have been clean in recent plan history. If active markers return, use:

```powershell
python development_tools/legacy/fix_legacy_references.py --find
python development_tools/legacy/fix_legacy_references.py --verify
```

Update `DEPRECATION_INVENTORY.json` in the same change as any bridge removals.

---

## 5. Condensed completed history

The original V5 contained detailed dated entries. Keep those details in archive/history. This section keeps only the useful working memory.

### 5.1 Audit infrastructure and reliability

Completed themes:

- Tiered audit pipeline.
- Standardized metadata.
- JSON/report pipeline.
- Report integrity checks.
- Lock handling and stale-lock recovery.
- Strict mode and Tier 3 outcome contracts.
- Cache invalidation and cache cleanup semantics.
- Scope-aware report paths for full-repo vs dev-tools-only audit output.
- Audit-tier participation matrix.

### 5.2 Static analysis and external checks

Completed themes:

- Ruff and Pyright integrated into audit/reporting.
- Bandit and pip-audit integrated into Tier 3.
- Sharded Ruff/Bandit execution.
- Per-shard static-analysis cache.
- Static-check config dependency paths.
- Requirements-lock signature support for pip-audit.
- Policy tests for config/cache/tooling drift.

### 5.3 Coverage and tests

Completed themes:

- Dev-tools coverage floor exceeded.
- Unified full-repo Tier 3 coverage path includes dev-tools tests and package coverage.
- `coverage_dev_tools.json` derived from main coverage.
- `audit --full --dev-tools-only` remains available for narrow dev-tools work.
- Domain-scoped test coverage cache improved.
- Serial `no_parallel` phase now respects domain-filtered test path lists.
- `run_tests.py --mode all --full` is the audit-parity path.

### 5.4 Reporting and generated outputs

Completed themes:

- `CONSOLIDATED_REPORT.md` casing normalized.
- Quick Wins details improved.
- AI status/priority report semantics cleaned up.
- `DEV_TOOLS_STATUS.md`, `DEV_TOOLS_PRIORITIES.md`, and `DEV_TOOLS_CONSOLIDATED_REPORT.md` clarified.
- Full-repo `development_docs` markdown generators are skipped during dev-tools-only audits where appropriate.
- Large `issues=` log counts documented as summary metrics, not failures.

### 5.5 Documentation tooling

Completed themes:

- Documentation overlap noise reduced.
- Expected paired docs and specialized testing guides are no longer treated as consolidation debt.
- Example-marker checker exists as advisory tooling.
- TODO sync has dry-run and limited apply support.
- Dev-tools guide references were retargeted away from product docs where appropriate.

### 5.6 Script migration and cleanup utilities

Completed themes:

- Flaky detector migrated into tracked dev-tools ownership.
- `verify_process_cleanup` migrated and improved.
- Windows orphan detection now uses `Get-CimInstance Win32_Process` with command-line visibility.
- `fix_project_cleanup.py` remains canonical cleanup ownership.

### 5.7 Portability

Completed themes:

- `core.logger` dependency removed from `development_tools/`.
- Import-boundary checker rejects `core.*` imports.
- Minimal fake-project smoke coverage added.
- Several project-root and hardcoded-path issues were cleaned up.

---

## 6. Resolved items that should stay closed unless they regress

| Item | Resolution |
|---|---|
| Consolidated report filename casing | Resolved; Git tracks `development_tools/CONSOLIDATED_REPORT.md`. |
| V4 logging migration | Substantively done; only opportunistic stray-print cleanup remains. |
| Version-sync large feature work | Treat as maintenance unless behavior drifts. |
| Tier 3 coverage by audit scope | Unified full-repo run implemented; dev-tools-only narrow run preserved. |
| Audit artifact read fallbacks | Removed. |
| Bandit and pip-audit integration | Complete. |
| `analyze_pip_audit` elapsed-time ambiguity | Completion semantics clarified with subprocess timing/details. |
| Flaky detector migration | Complete. |
| `verify_process_cleanup` migration | Complete. |
| Full-repo `development_docs` overwrite issue during dev-tools-only audits | Complete; generators gated. |
| Audit/run_tests.py count disparity | Resolved by documenting `run_tests.py --mode all --full` as audit-parity path. |
| `no_parallel` tests bypassing domain cache | Fixed. |
| `core.logger` dependency | Removed. |

---

## 7. Backlog register

| ID | Area | Status | Next action |
|---|---|---|---|
| B-001 | Dev-tools test performance | Active | Continue module-scoped fixture review; start with `test_report_generation_quick_wins.py`. |
| B-002 | Targeted dev-tools coverage | Active | Pick next low-risk/high-value modules from live generated reports. |
| B-003 | Portability: implicit MHM assumptions | Active | Audit hardcoded names, root resolution, config assumptions, and external-project behavior. |
| B-004 | Static-tool packaging parity | Medium | Validate minimal external repo and periodic full Pyright parity. |
| B-005 | Domain-marker analysis | Medium | Define taxonomy/config and reduce false positives. |
| B-006 | Validation warnings | Low/medium | Tune only if warnings become noisy. |
| B-007 | Example-marker checker | Deferred/advisory | Improve heuristics before default gating. |
| B-008 | Documentation overlap | Monitoring | Reopen only on real duplicated content. |
| B-009 | System signals overlap | Deferred | Reopen only if duplicate metrics confuse generated output. |
| B-010 | TODO sync workflow polish | Low | Add docs/checks only if the workflow becomes active again. |
| B-011 | Coverage-cache benchmark | Deferred | Capture local numeric before/after timings. |
| B-012 | External-tool expansion | Deferred | Evaluate one tool at a time with clear signal/runtime value. |
| B-013 | Gap-analysis expansion | Deferred/large | Design matrix before implementing more tools. |
| B-014 | Memory profiler | Deferred | Decide integrate/enhance/standalone/retire. |
| B-015 | `report_generation.py` / `run_test_coverage.py` split | Deferred | Only small tested extractions. |
| B-016 | Arbitrary audit scope | Deferred/design | Design first; current scope model is binary. |
| B-017 | Low coverage warning | Monitoring | Reopen only on recurrence. |
| B-018 | `pip-audit` no-fix advisory | Monitoring | Wait for trusted fixed version or explicit remediation decision. |
| B-019 | Legacy references | Monitoring | Reopen only if generated reports show active markers. |

---

## 8. Related documents

- `development_tools/AI_STATUS.md`
- `development_tools/AI_PRIORITIES.md`
- `development_tools/CONSOLIDATED_REPORT.md`
- `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`
- `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`
- `development_docs/TEST_COVERAGE_REPORT.md`
- `development_docs/LEGACY_REFERENCE_REPORT.md`
- `ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md`
- `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- `scripts/SCRIPTS_GUIDE.md`
- `development_docs/LIST_OF_LISTS.md`
