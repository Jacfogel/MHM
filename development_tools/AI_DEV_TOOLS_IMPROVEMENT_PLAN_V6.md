# AI Development Tools — Improvement Roadmap V6

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Forward-looking backlog for `development_tools/` after V5  
> **Style**: Direct, concise, action-oriented  
> **Last Updated**: 2026-07-20 (B-015 slice #3: report builder mixins)  
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

1. **Coverage work is tracked outside this plan** (product/domain coverage via `AI_PRIORITIES.md` / `TEST_COVERAGE_REPORT.md`; remaining B-002 chokepoint notes stay in §2.2 for history only).
   - Do not treat percentage-only `development_tools` coverage growth as the active V6 execution driver.

2. **Dev-tools test performance (B-001) is residual / maintenance.**
   - 2026-07-19: `test_fix_project_cleanup.py` moved to `tmp_path` (largest former demo-copy sink); module-scoped overrides added for docs-workflow / scoped-status / static-analysis report / cache-helpers; path-drift leftover demos → `tmp_path`.
   - Intentionally function-scoped + marked `slow` (Tier 3 quick profile skips): `test_output_storage_archiving.py` (module), legacy cleanup mutators that still need `temp_project_copy`.
   - Re-profile only if suite wall time regresses; do not force module scope on archive/legacy mutators.

3. **Keep portability as residual cleanup, not a greenfield slice.**
   - `core.logger` removal, external-`project_root` / config portability, MHM-string default cleanup, and minimal external-repo validation (B-003/B-004, 2026-07-18) are done (§2.3).
   - Remaining: only reopen on concrete external/smoke regressions. Pyright SSOT is `pyproject.toml` `[tool.pyright]` only (nested owned JSON removed).

4. **Do not reopen pip-audit `CVE-2026-3219`.**
   - Remediated with `pip>=26.1` floor; live audit shows **0** pip-audit findings. Reopen only on a new advisory.

### 1.2 Current priority tiers

| Tier | Work |
|---|---|
| **Active (outside V6)** | Product/domain coverage and refactor priorities from generated `AI_PRIORITIES.md` |
| **Residual / medium** | B-001 re-profile if suite time hurts; portability/static packaging maintenance; B-006/B-007/B-008 only on new noise |
| **Maintenance** | Domain-marker policy (taxonomy + enforcement shipped; tune only on false positives) |
| **Deferred** | External-tool expansion; gap-analysis expansion; further `run_test_coverage` splits (argv/shard/domain-cache); arbitrary audit scopes |
| **Monitoring only** | Low-coverage warning recurrence; example-marker/doc-overlap regressions; legacy-reference regressions |

---

## 2. Active backlog

### 2.1 Dev-tools test performance

**Status**: Residual / maintenance (2026-07-19 slice landed).

**Problem**: `tests/development_tools/` was slow mainly because setup is expensive, especially function-scoped `temp_project_copy`.

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
  - `test_commands_docs_workflow.py` (**2026-07-19**)
  - `test_data_loading_helpers.py`
  - `test_dev_tools_scoped_status_report.py` (**2026-07-19**)
  - `test_fix_documentation_headings.py`
  - `test_fix_documentation_links.py`
  - `test_fix_version_sync_changelog_archive_order.py`
  - `test_generate_consolidated_report.py`
  - `test_report_generation_dev_tools_scope.py`
  - `test_report_generation_helpers_pure.py`
  - `test_report_generation_quick_wins.py`
  - `test_report_generation_static_analysis.py` (**2026-07-19**)
  - `test_static_analysis_tools.py`
  - `test_tool_wrappers_additional.py`
  - `test_tool_wrappers_branch_paths.py`
  - `test_tool_wrappers_cache_helpers.py` (**2026-07-19**)
  - `test_tool_wrappers_static_analysis.py`
  - `test_generate_unused_imports_report.py`
- **2026-07-19**: `test_fix_project_cleanup.py` uses `tmp_path` (no demo copytree); unused Main fixture args dropped; path-drift leftover demos → `tmp_path`.
- Intentionally function-scoped mutators (still need demo tree):
  - `test_output_storage_archiving.py` — module `pytestmark = slow` (Tier 3 quick skips)
  - `test_legacy_reference_cleanup.py` — `temp_project_copy` mutators marked `slow`

**Next actions**:

- **Re-profiled 2026-07-19**: `python run_tests.py --mode development_tools --durations-all` → **1591 passed**, **0 failed**, wall **83.94s** (parallel phase **77.27s** / pytest **72.20s**, 6 workers loadscope). Prior baseline (2026-07-18): **1564 passed** / parallel **182.48s** / wall **~195s**.
- Largest remaining costs are one-time module-scoped demo setups (~4–5.7s each) plus `test_dev_tools_portability_smoke` call (~5.9s). Former cleanup copytree sink is gone from the top list.
- Function-scoped archive/legacy mutators still pay ~4s setup each when the full (non-quick) profile runs; Tier 3 quick continues to skip them via `slow`.
- Optional later only if wall time regresses: slim demo tree. Do not force module scope on archive / legacy mutators.

---

### 2.2 Targeted dev-tools coverage

**Status**: Tracked outside V6 active execution (product/`AI_PRIORITIES` + `coverage` command). History below kept for context.

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

**Status**: Residual complete for current noise (2026-07-19); reopen if logs flood again.

**Already done**:

- `needs_enhancement` placeholder modules are summarized at INFO (not per-file WARNING).
- Priority WARNING list is limited to `new_module` / `dependencies_changed` / `missing_enhancement`.
- Test files were already outside the scan set.

**Open work**:

- Reopen only if dependency-doc generation warnings become noisy again.

---

### 2.6 Example-marker checker

**Status**: Advisory hardened (2026-07-19); still not a default gate.

**Already done**:

- Added `example_marker_validation.py`.
- Added `--check-example-markers` on `analyze_documentation_sync.py`.
- Expanded scan paths to approved documentation sets.
- Suppressed changelog-style false-positive heading noise.
- Added JSON true-positive coverage.
- **2026-07-19**: skip fenced code blocks; open regions on prose/bold `Examples:` / `Example Usage:` / `Example Code:` labels.

**Open work**:

- Report file/line details in consolidated output only if promoted from advisory.
- Reopen only if future audits show missed true examples or renewed noise.
- Do not make this a failing default gate yet.

---

### 2.7 Documentation overlap analysis

**Status**: Mostly complete; monitor for real duplicate-content problems.

**Already done**:

- Generic numbered headings are filtered.
- Expected boilerplate headings are excluded.
- Configured paired-doc groups and specialized testing guides are skipped in consolidation recommendations.
- **2026-07-19**: `EXPECTED_OVERLAPS` adds Discord-spec boilerplate (`out of scope`, `manual test checklist`, `related documentation`).

**Open work**:

- Reopen only if future audits show real duplicated content outside paired/specialized docs.
- Improve actionable insight if a new noisy class appears.

---

### 2.8 System signals purpose and redundancy cleanup

**Status**: Complete (2026-07-20 B-009).

**Decision**: Keep the tool as the Tier 1 operational health pulse.

**Already done**:

- Stopped re-deriving `documentation_sync_status` from prior audit JSON (doc-sync / Documentation Signals own that).
- `critical_alerts` now projects `severity_levels.CRITICAL` (no second file/log scan).
- Module docstring, human CLI output, guide table, and tool metadata clarify scope.
- AI_STATUS / CONSOLIDATED already note Documentation Signals separately.

**Open work**:

- None. Reopen only if duplicate metrics confuse generated output again.

---

### 2.9 TODO sync cleanup automation

**Status**: Complete (2026-07-20 B-010).

**Already done**:

- `sync-todo --dry-run` prints a dry-run report.
- `sync-todo --apply` removes auto-cleanable completed checklist lines.
- `--dry-run` and `--apply` are mutually exclusive.
- **2026-07-20**: Documented a four-step workflow in paired guides (dry-run → human changelog cross-check for manual-review items → optional `--apply` → never combine flags). Changelog confirmation before hand-removal stays a human step by design.

**Open work**:

- None. Reopen only if the CLI or audit wiring drifts.

---

## 3. Deferred design/backlog items

These are real ideas, but they should not compete with the active slices unless the project focus changes.

### 3.1 Coverage-cache numeric benchmark

**Status**: Complete (2026-07-20 B-011).

**Goal**: Capture stable local numbers comparing no-domain-cache vs domain-cache coverage runs.

**Local results** (`--dev-tools-only --no-parallel`, 2026-07-20, venv active):

| Run | Flags | Wall time |
|---|---|---|
| Cold / no cache | `--no-domain-cache` | **298.67s** |
| Domain-cache build | default (first populated run after cold) | **326.99s** |
| Domain-cache hit | default (unchanged sources/tests) | **0.91s** |

**Takeaway**: Domain cache does not speed the first populated run after a cold/no-cache pass; on a true hit it collapses wall time from ~5 minutes to under 1 second. Prefer leaving domain cache on for iterative coverage; use `--no-domain-cache` only when validating a full recompute.

**Benchmark recipe** (re-run if cache semantics change):

```powershell
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel }
# True hit: repeat the second command without source/test edits
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel }
```

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

**Status**: Resolved (2026-07-20 B-014) — **keep standalone**.

**Decision**:

- Do **not** integrate into `development_tools` audit tiers.
- Keep `scripts/testing/memory_profiler.py` (and related local `*_memory_leak.py` helpers) as untracked/local diagnostics per [SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md).
- Suite mitigations in testing guides remain the primary path; optional local profiler or OS/`tracemalloc` for ad-hoc triage.
- Revisit migration only if memory profiling becomes a recurring multi-contributor workflow.

### 3.5 Refactor `report_generation.py` and `run_test_coverage.py`

**Status**: Partial (2026-07-20 slices #1–#3); continue only in small tested steps.

**No legacy shims**: move pure helpers to new modules; mixin methods may thin-delegate. Do not add `LEGACY COMPATIBILITY` bridges or dual public APIs.

**Already done**:

- Slice #1: `development_tools/tests/coverage_json_helpers.py` — `coverage_path_to_rel_posix`, `recompute_coverage_totals_from_files`.
- Slice #1: `development_tools/shared/service/report_generation_tier3_helpers.py` — pure Tier 3 helpers (`coerce_int`, node-id normalize, track/outcome classification); mixin methods delegate.
- Slice #2: `development_tools/tests/coverage_outcome_classification.py` — return-code/hex helpers, infra/xdist detectors, `build_track_outcome`, `classify_coverage_outcome`, `build_cache_only_coverage_outcome`, `strip_xdist_args`; `CoverageMetricsRegenerator` methods thin-delegate.
- Slice #3: report builders extracted as mixins composed by `ReportGenerationMixin`:
  - `report_generation_ai_status.py` (`AIStatusDocumentMixin`)
  - `report_generation_ai_priorities.py` (`AIPrioritiesDocumentMixin`)
  - `report_generation_consolidated.py` (`ConsolidatedReportDocumentMixin`)
  - Shared helpers + action-item helpers remain in `report_generation.py` (~978 lines).

**Possible later splits for `report_generation.py`**:

- downstream action item helpers (optional; already small)
- further pure-helper pulls from remaining shared helpers

**Possible later splits for `run_test_coverage.py`**:

- pytest argv construction
- shard merge logic
- domain cache

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
| Coverage-cache numeric benchmark | Captured 2026-07-20; B-011 closed. |
| Memory profiler audit integration | Keep standalone/local; B-014 closed. |
| TODO sync workflow polish | Recipe documented in paired guides; B-010 closed. |
| System signals doc-sync overlap | Trimmed; B-009 closed. |

---

## 7. Backlog register

| ID | Area | Status | Next action |
|---|---|---|---|
| B-001 | Dev-tools test performance | Maintenance | 2026-07-19 re-profile: **1591 passed / 83.94s** wall (was ~195s). Reopen only on regression. |
| B-002 | Targeted dev-tools coverage | Tracked elsewhere | Slices #1–#3 landed; further coverage via `AI_PRIORITIES` / `coverage` command, not as V6 active driver. |
| B-003 | Portability: implicit MHM assumptions | Maintenance | 2026-07-18: MHM roots/allowlists moved to project JSON; portable defaults emptied. Reopen only on regression. |
| B-004 | Static-tool packaging parity | Maintenance | 2026-07-18 external-repo smokes; 2026-07-19 removed nested owned `pyrightconfig.json` (SSOT = `pyproject.toml` `[tool.pyright]`). |
| B-005 | Domain-marker analysis | Maintenance | Do not rebuild; tune false positives / keep `domain_mapper` aligned when packages change. |
| B-006 | Validation warnings | Monitoring | 2026-07-19: placeholder flood demoted; escalate only new/missing/changed. |
| B-007 | Example-marker checker | Advisory | 2026-07-19: fence skip + prose `Examples:` openers; keep advisory (no default gate). |
| B-008 | Documentation overlap | Monitoring | 2026-07-19: Discord-spec boilerplate in `EXPECTED_OVERLAPS`. |
| B-009 | System signals overlap | Complete | 2026-07-20: dropped doc-sync re-derive; critical_alerts from severity; scope docs/metadata aligned. |
| B-010 | TODO sync workflow polish | Complete | 2026-07-20: four-step recipe in paired guides; changelog cross-check stays human. |
| B-011 | Coverage-cache benchmark | Complete | 2026-07-20: cold **298.67s** / cache-build **326.99s** / hit **0.91s** (`--dev-tools-only --no-parallel`). |
| B-012 | External-tool expansion | Deferred | Evaluate one tool at a time with clear signal/runtime value. |
| B-013 | Gap-analysis expansion | Deferred/large | Design matrix before implementing more tools. |
| B-014 | Memory profiler | Resolved | Keep standalone in untracked `scripts/`; do not audit-integrate. |
| B-015 | `report_generation.py` / `run_test_coverage.py` split | Partial | 2026-07-20: slices #1–#3 (helpers + outcome classification + AI_STATUS/AI_PRIORITIES/CONSOLIDATED mixins). Remaining: coverage argv/shard/domain-cache. |
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
