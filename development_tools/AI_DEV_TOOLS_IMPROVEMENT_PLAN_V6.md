# AI Development Tools — Improvement Roadmap V6

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Forward-looking backlog for `development_tools/` after V5  
> **Style**: Direct, concise, action-oriented  
> **Last Updated**: 2026-07-19 (removed nested owned pyrightconfig.json)  
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

1. **Prefer targeted dev-tools coverage where it buys down real risk (highest leverage).**
   - Live full-repo Tier 3 (2026-07-18 refresh): `development_tools` package **~65.6%** (still above the V4 60% floor).
   - Prefer central service chokepoints over percentage-only tests. Hotspots after slices #1–#3:
     - `shared/service/report_generation.py` (~47%)
     - `shared/service/audit_orchestration.py` (~56%)
     - `shared/service/tool_wrappers.py` (~59%)
     - `commands.py` / `data_loading.py` (~61–63%; slice #3 added branch coverage — refresh % via `coverage` command)
     - next: remaining brittle branches in the five service modules, or product `AI_PRIORITIES` domains
   - Keep opportunistic `tests/development_tools/test_config.json` migration when touching analyzer-style tests.
   - Product-wide `AI_PRIORITIES.md` is a **parallel** track (domains below 80%, large modules, coupling); do not confuse it with this V6 slice.

2. **Continue residual dev-tools test performance work only.**
   - Root cause remains function-scoped `temp_project_copy` (demo-tree copy per test).
   - Module-scoped overrides cover the original hot modules, `test_report_generation_quick_wins.py`, and the 2026-07-18 residual pair:
     `test_tool_wrappers_static_analysis.py`, `test_generate_unused_imports_report.py`.
   - Leave intentionally function-scoped: `test_fix_project_cleanup.py`, `test_output_storage_archiving.py`,
     `test_legacy_reference_cleanup.py` (cleanup mutates demo files / inventory).
   - Further candidates only if profiling still shows high function-scoped copy cost.

3. **Keep portability as residual cleanup, not a greenfield slice.**
   - `core.logger` removal, external-`project_root` / config portability, MHM-string default cleanup, and minimal external-repo validation (B-003/B-004, 2026-07-18) are done (§2.3).
   - Remaining: only reopen on concrete external/smoke regressions. Pyright SSOT is `pyproject.toml` `[tool.pyright]` only (nested owned JSON removed).

4. **Do not reopen pip-audit `CVE-2026-3219`.**
   - Remediated with `pip>=26.1` floor; live audit shows **0** pip-audit findings. Reopen only on a new advisory.

### 1.2 Current priority tiers

| Tier | Work |
|---|---|
| **Active** | Targeted dev-tools coverage (service chokepoints); residual test-performance fixture review |
| **Residual / medium** | Portability/static packaging (B-003/B-004) maintenance only; validation-warning cleanup if noisy |
| **Maintenance** | Domain-marker policy (taxonomy + enforcement shipped; tune only on false positives) |
| **Deferred** | Coverage-cache numeric benchmarks; external-tool expansion; TODO-sync workflow polish; gap-analysis expansion; memory profiler; arbitrary audit scopes |
| **Monitoring only** | Low-coverage warning recurrence; example-marker/doc-overlap regressions; legacy-reference regressions |

---

## 2. Active backlog

### 2.1 Dev-tools test performance

**Status**: Active residual (major hot-module work done).

**Problem**: `tests/development_tools/` is slow mainly because setup is expensive, especially function-scoped `temp_project_copy`.

**Current evidence**:

- May 2026 investigation: collection ~**1479** tests; wall-clock cost was setup, not collection growth.
- Root cause: function-scoped `temp_project_copy` copies `tests/fixtures/development_tools_demo` once per test.
- `measure_tool_timings.py` profiles audit-tool runtime, not pytest runtime. Do not use it as the primary test-suite performance profiler.

**Already done**:

- Extracted `temp_project_copy_paths` (shared helper in `tests/development_tools/conftest.py`).
- Module-scoped `temp_project_copy` overrides in (at least):
  - `test_audit_orchestration_helpers.py`
  - `test_audit_strict_mode.py`
  - `test_commands_additional_helpers.py`
  - `test_data_loading_helpers.py`
  - `test_fix_documentation_headings.py`
  - `test_fix_documentation_links.py`
  - `test_fix_version_sync_changelog_archive_order.py`
  - `test_generate_consolidated_report.py`
  - `test_report_generation_dev_tools_scope.py`
  - `test_report_generation_helpers_pure.py`
  - `test_report_generation_quick_wins.py` (**was the previous next target; done**)
  - `test_static_analysis_tools.py`
  - `test_tool_wrappers_additional.py`
  - `test_tool_wrappers_branch_paths.py`
  - `test_tool_wrappers_static_analysis.py` (**2026-07-18 residual**)
  - `test_generate_unused_imports_report.py` (**2026-07-18 residual**)
- Intentionally left function-scoped (mutation / shared state):
  - `test_fix_project_cleanup.py`
  - `test_output_storage_archiving.py`
  - `test_legacy_reference_cleanup.py` (actual cleanup + inventory overwrites)

**Next actions**:

- **Profiled 2026-07-18**: `python run_tests.py --mode development_tools --durations-all` → **1564 passed in 182.48s** wall (6 workers, loadscope). Cost is still mostly `temp_project_copy` **setup**, not call time.
- Largest remaining setup sinks (intentionally function-scoped / mutators): `test_fix_project_cleanup.py` (~142s summed listed setups), `test_output_storage_archiving.py` (~49s), `test_legacy_reference_cleanup.py` (~16s setups + ~28s calls).
- Note: under `--dist loadscope`, **class-based** modules pay module-scoped fixture once **per class worker**, so module scope helps within a class but not across classes in the same file.
- Optional follow-ups only if suite time still hurts: slim demo tree, mark heavy cleanup/archiving as `slow`, or avoid `temp_project_copy` in pure helpers.
- Do not force module scope on `test_legacy_reference_cleanup.py` / cleanup / archiving mutators.

---

### 2.2 Targeted dev-tools coverage

**Status**: Active, but do not chase percentage-only tests.

**Current state** (prefer live `TEST_COVERAGE_REPORT.md`):

- V4’s 60% floor is already met.
- Full-repo Tier 3 (2026-07-18, later refresh): `development_tools` **~65.6%** (9461 lines missing in AI_PRIORITIES snapshot).
- Useful question: **which uncovered paths are risky enough to test next?**

**Preferred targets** (service chokepoints first):

- `development_tools/shared/service/report_generation.py` (~47%)
- `development_tools/shared/service/audit_orchestration.py` (~56%)
- `development_tools/shared/service/tool_wrappers.py` (~59%)
- `development_tools/shared/service/commands.py` (~60%)
- `development_tools/shared/service/data_loading.py` (~61%)
- `development_tools/functions/analyze_unused_functions.py` (was 0%; direct unit coverage started 2026-07-18)
- other low-coverage helpers from live `TEST_COVERAGE_REPORT.md`

**Already done**:

- Focused coverage tests for command helpers, audit orchestration helpers, module-dependency generation, tool timing, tool storage, version-sync TODO helpers, static-check sharding/cache behavior, documentation overlap, and test-marker domain summary paths.
- **2026-07-18 slice #1**: branch/unit coverage for service chokepoints in
  `test_report_generation_helpers_pure.py` (scoped paths, dependency filters, tier3 log/classification, results-file safety, critical/action helpers),
  `test_audit_orchestration_helpers.py` (tool-start log, test-dir reload skip, aggregated/additional save, docs-quality cache path),
  `test_tool_wrappers_additional.py` (inventory guard paths, unused/duplicate wrappers, doc-sync aggregate persist, pip-audit cache hit/miss).
- **2026-07-18 slice #2**: deeper chokepoint edges + direct analyzer coverage —
  docstring/marker/path helpers in `test_report_generation_helpers_pure.py`,
  cache-merge / docs-quality miss / ASCII compliance in `test_audit_orchestration_helpers.py`,
  unused-functions wrapper failure paths + facade/patterns/dependency cache in `test_tool_wrappers_additional.py`,
  new `test_analyze_unused_functions.py` (decorator/implicit-use/normalize + mini-project analyze). Validation: **129 passed** across the four modules.
- **2026-07-18 slice #3**: `commands` / `data_loading` branch coverage —
  `_load_coverage_summary` (primary/archive/bad JSON), `_load_coverage_json`, insights standard/reload,
  canonical-metrics cache + doc_coverage sanitize, tool-data normalize/stale-skip, config storage path,
  doc-sync section reset + markdown link aggregate;
  doc-subcheck freshness/mtime cache-hit, `_write_test_suite_output_file`, `execute_task` routing,
  `generate_directory_trees`, `run_cleanup(full=)`, `run_status(skip_status_files=True)`.
  Validation: **121 passed** across `test_data_loading_helpers` + `test_commands_coverage_helpers` + `test_commands_additional_helpers`.

**Next actions**:

- Re-check live `TEST_COVERAGE_REPORT.md` after an explicit `python development_tools/run_development_tools.py coverage` run (audit no longer regenerates coverage).
- Prefer remaining brittle branches (e.g. `_load_mtime_cached_tool_results`) over new percentage-only files.
- Migrate remaining analyzer-style tests to `tests/development_tools/test_config.json` when touching them.
- Avoid long duplicated module lists beyond the preferred-target shortlist above.

---

### 2.3 Dev-tools portability and project independence

**Status**: Residual active (major slices done).

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

**Status**: Substantively complete (2026-07-18 cleanup); maintenance only.

**Already done** (portability-first slice ~2026-05-20 and follow-ups):

- Explicit external `project_root` respected for copied-out `development_tools/` execution.
- Config preference for `project_root/development_tools/config/development_tools_config.json`.
- Tool wrappers prefer scripts under the supplied project root.
- MHM-only quick-status checks moved out of generic defaults into project config.
- Expanded `test_dev_tools_portability_smoke.py` and policy tests blocking `core.*` imports / MHM-only defaults.
- Live import-boundary status: CLEAN (full-repo Tier 3, 2026-07-18).
- **2026-07-18**: Portable code defaults no longer embed MHM package roots (`ruff`/`pyright` shards, `bandit_scan_roots` / `bandit_root_python`, channel-logger allowlist). MHM trees live in project JSON + `.example`. Cache/temp names and `DEV_TOOLS_PIP_AUDIT_SKIP` genericized (`MHM_PIP_AUDIT_SKIP` removed).

**Open work** (opportunistic only):

- Reopen only when a concrete assumption breaks an external or smoke run.
- Do not treat this as a greenfield rewrite.

#### 2.3.3 Static tooling and packaging parity

**Status**: Complete for intended B-004 scope (single Pyright SSOT + external-repo).

**Already done**:

- Pyright/Ruff structural policy tests (`test_pyright_config_paths.py`).
- **2026-07-18 B-004**: minimal external-repo validation in `test_dev_tools_portability_smoke.py` (Bandit `.` fallback, Ruff monolithic fallback, subprocess `audit --quick` on copied tree + host package).
- MHM project config carries first-party shards/roots so host audits stay sharded after portable defaults emptied.
- **2026-07-19 B-004**: removed nested `development_tools/config/pyrightconfig.json`; Pyright SSOT is
  `pyproject.toml` `[tool.pyright]` only. Cache deps, guides, LIST_OF_LISTS, and policy tests updated;
  deprecation inventory `owned_nested_pyrightconfig_json`.

**Open work** (monitoring / optional):

- Keep periodic full-project Pyright runs (`pyproject.toml`) because sharded Pyright can miss cross-package diagnostics.

---

### 2.4 Domain-marker analysis

**Status**: Substantively complete; maintenance only.

**Goal**: Extend `analyze_test_markers` so tests can be checked for domain-based markers in addition to category markers.

**Already done**:

- `domain_attribution_summary` / JSON details support and tests.
- Canonical three-layer taxonomy documented (category / domain / optional tier) in testing guides.
- `domain_markers` filled from `domain_mapper` union (`domain_marker_union_from_domain_mapper`); directory-only mappings can skip enforcement.
- Policy guard `test_pytest_tests_have_required_domain_marker`; `analyze_test_markers` on Tier 3; `--check` fails on marker issues.
- Domain migrations (`user_management` → `user`, `integrations` registered, etc.).
- Generated status: category and domain marker policy CLEAN on recent scoped/full audits.

**Open work**:

- Tune false positives / exemptions only if audits get noisy.
- Keep taxonomy docs and `domain_mapper` lists aligned when packages are added.
- Do not rebuild the feature from scratch; treat as maintenance.

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

### 4.3 pip-audit `CVE-2026-3219` (closed)

**Status**: Resolved (was monitoring).

- Fixed via `pip>=26.1` installer floor / venv upgrade; live Tier 3 (2026-07-18) reports **0** pip-audit findings.
- Do not reopen unless a new pip (or other) advisory appears in audit output.

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
- Domain-marker taxonomy + enforcement (category/domain/optional tier; policy guards; Tier 3 participation).

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
- External `project_root` + project-local config preference for copied-out execution.
- MHM-only quick-status checks moved into project config (not generic defaults).
- Several project-root and hardcoded-path issues were cleaned up.
- MHM first-party Ruff/Pyright/Bandit roots and channel-logger allowlist live in project JSON; portable code defaults are empty.
- External-repo validation: Bandit/Ruff fallbacks + subprocess `audit --quick` on a copied tree.

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
| Domain-marker taxonomy + Tier 3 enforcement | Shipped; maintenance only (B-005). |
| `pip` / `CVE-2026-3219` advisory | Remediated (`pip>=26.1`); B-018 closed. |

---

## 7. Backlog register

| ID | Area | Status | Next action |
|---|---|---|---|
| B-001 | Dev-tools test performance | Active residual | 2026-07-18: module-scoped static-analysis wrappers + unused-imports report; legacy cleanup stays function-scoped. Next: re-profile only if suite time still hurts. |
| B-002 | Targeted dev-tools coverage | Active | 2026-07-18 slices #1–#3 landed (chokepoints + unused-functions + `commands`/`data_loading`); next: refresh metrics via `coverage` command (not audit), then remaining brittle service branches. |
| B-003 | Portability: implicit MHM assumptions | Maintenance | 2026-07-18: MHM roots/allowlists moved to project JSON; portable defaults emptied. Reopen only on regression. |
| B-004 | Static-tool packaging parity | Maintenance | 2026-07-18 external-repo smokes; 2026-07-19 removed nested owned `pyrightconfig.json` (SSOT = `pyproject.toml` `[tool.pyright]`). |
| B-005 | Domain-marker analysis | Maintenance | Do not rebuild; tune false positives / keep `domain_mapper` aligned when packages change. |
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
| B-018 | `pip-audit` `CVE-2026-3219` | Resolved | Closed; reopen only on a new advisory in audit output. |
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
