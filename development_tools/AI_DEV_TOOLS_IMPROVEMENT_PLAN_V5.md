# AI Development Tools — Improvement Roadmap (V5)

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Single forward-looking backlog after V4; collapsed history; actionable next steps  
> **Style**: Direct and concise  
> **Last Updated**: 2026-04-12  
> **Supersedes**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) (keep V4 for detailed checkbox history)

**Authoritative metrics**: [development_tools/AI_STATUS.md](AI_STATUS.md) and [development_tools/AI_PRIORITIES.md](AI_PRIORITIES.md) after `python development_tools/run_development_tools.py audit` or `audit --full`.

---

## 1. Audit of V4 “completed” claims (2026-03-27)

This section answers: *Were V4 completed items actually done? Was work thorough and aligned with [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md) and [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)?*

### 1.1 Substantively complete and verifiable

- **Tiered audit, caching, lock handling**: `development_tools/shared/lock_state.py`, stale-lock recovery in orchestration and CLI, tests referenced in V4 — present and consistent with reliability goals.
- **60%+ development-tools coverage**: Recent Tier 3 snapshot shows **Development Tools Coverage ~61.9%** (see AI_STATUS **Last Generated** after your latest `audit --full`). V4’s floor target is met; optional ~80% module nudges remain in AI_PRIORITIES.
- **Duplicate-function body similarity**: `--consider-body-similarity` and related config/CLI exist in `development_tools/functions/analyze_duplicate_functions.py` (V4 §3.5 / §5.0).
- **Tier 3 outcome contract, strict mode, cache invalidation, exclusion/tooling policy tests**: Implemented with regression tests per V4 notes; legacy Tier3 bridge removals were done with DEPRECATION_INVENTORY updates (see V4 §2.9 follow-ups).
- **Pyright/Ruff in audit, reporting, config-owned paths**: Integrated as described in V4 §7.2.
- **Quick Wins, dependency patterns in reports, docstring metric parity, cache cleanup semantics**: Align with V4 §2.x completed sections.

### 1.2 Complete with caveats (documentation or status drift)

| Topic | V4 claim | Finding |
|--------|-----------|---------|
| **Consolidated report filename** | Renamed to `CONSOLIDATED_REPORT.md` | **Resolved (2026-03-27)**: Git now tracks `development_tools/CONSOLIDATED_REPORT.md` (case-normalized) to match config and guides. |
| **§2.2 Logging** | Section status “IN PROGRESS” | Checklist is almost entirely closed; remaining gap is **optional** polish (e.g. any stray prints in rarely used scripts). Treat **substantive migration as done**; use AI_PRIORITIES if new noisy paths appear. |
| **§1.5 Coverage caching** | “IN PROGRESS” | Core invalidation and tool-hash behavior done; **numeric benchmark** (full vs domain) still intentionally **deferred** (machine-dependent). |
| **§3.3 Version sync** | “IN PROGRESS” | Discovery and docs spot-checks done; no large open feature — treat as **maintain unless regression**. |

### 1.3 Not complete (V4 correctly left open)

- **`tests/development_tools/test_config.json` migration** for all analyzer-using tests — still deferred (V4 §1.1).
- **Scope-aware report content** for `--dev-tools-only` — **expanded (2026-04-08)**: priorities/status quick wins and several ranked items filter to `development_tools/`; paired-doc quick wins intentionally omitted on dev-tools runs; see **§7.18**. **Remaining**: drive **Tier 3 coverage execution from audit scope** so a single run does not refresh both full-repo and dev-tools coverage when only one scope is intended (see **§5.1 — 1.9** and **§7.15**).
- **Flaky detector**: migrated from `scripts/flaky_detector.py` into tracked `development_tools/tests/flaky_detector.py` with CLI command wiring (`flaky-detector`) and tests — see **§5.3 — 3.12**.
- **Scripts migration inventory / 3.14 review candidates**: updated with concrete migrations for `flaky_detector` and `verify_process_cleanup`, plus canonical cleanup ownership (`development_tools/shared/fix_project_cleanup.py`) — see **§5.3 — 3.13/3.14**.
- **§3.15 gap tasks** — deferred unless a concrete replacement requirement reappears with active source.
- **§3.16** `report_generation.py` / `run_test_coverage.py` split — **plan only**, no implementation backlog beyond AI_PRIORITIES refactor candidates.
- **§6 Audit-driven remediation** (legacy markers, deprecation inventory items, domain coverage, complexity) — **ongoing product work**, not tool-suite bugs.

### 1.4 Compliance: legacy guide and workflow

- **AI_LEGACY_COMPATIBILITY_GUIDE**: V4’s completed **code** work that touched bridges (e.g. Tier3 cache normalization, inventory updates) matches expectations: inventory updates, tests, and phased removal rather than time-based deletes. **Section 6 backlog** (retire `sync_ruff_toml`-related bridge when exit criteria met) should use **`fix_legacy_references.py --find` / `--verify`**, update `DEPRECATION_INVENTORY.json` in the **same change** as removals, and follow search-and-close — **ongoing**; live report: [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md). **2026-03-28**: `root_ruff_compat_mirror` keeps **`search_terms`: `[]`** while the bridge remains `active_bridge` — inventory row still appears in the report’s **Deprecation Inventory** block (active entries: 1, active search terms: 0); **per-file inventory hits** stay at 0 because no grep patterns are injected (avoids false “issues” from `sync_ruff_toml` docstrings/CLI help). Executable `LEGACY COMPATIBILITY` code paths are tracked separately from this inventory wording.
- **AI_DEVELOPMENT_WORKFLOW**: Dev-tools changes described in V4 follow **small slices**, tests under `tests/development_tools/`, and documented entry points. Future large refactors should stay **incremental** per §3 and §5 “Refactor”.

### 1.5 Nuance index (same topics as §1.2, cross-linked to §5)

Use this block when a V4 **Status** line says “IN PROGRESS” or “COMPLETE” but behavior is subtle. Everything below is **also** expanded under **§5** where there is still work; items that are **not** backlog are called out so they are not mistaken for missing work.

| Nuance | What to know | Where in V5 |
|--------|----------------|-------------|
| **Consolidated report filename casing** | **Resolved 2026-03-27**: Git tracks `development_tools/CONSOLIDATED_REPORT.md` to match config and guides. | §1.2 table. |
| **§2.2 Logging “IN PROGRESS”** | Substantive print→logger migration is done; V4 status lagged. Only **optional** stray prints in rare entrypoints may remain. | §1.2; **§5.2 — 2.2** |
| **§1.5 Coverage cache “IN PROGRESS”** | Invalidation, tool-hash, and logging are in place; **numeric** full-vs-domain benchmarks intentionally **deferred** (machine-specific). | §1.2; **§5.1 — 1.5** |
| **§3.3 Version sync “IN PROGRESS”** | Commands and paired-guide coverage exist; no large open feature — **maintain on drift**. | §1.2; **§5.3 — 3.3** |
| **§2.5 System signals “IN PROGRESS”** | Decision to **keep** tool + clarify scope is done; further overlap trim with doc-sync is **optional**. | **§5.2 — 2.5** |
| **§2.9 Console “IN PROGRESS”** | Stdout/logging review done; **spinners/TUI** still optional. | **§5.2 — 2.9** |
| **§3.17 Portability “IN PROGRESS”** | Many checklist items are `[x]` in V4, but **hardcoded-path hotspots** and **strict full-audit** validation in slow environments remain **ongoing** — not contradictory. | **§5.3 — 3.17** |
| **Dual Pyright / dual Ruff configs** | Root **`pyproject.toml` `[tool.pyright]`** = IDE/whole-repo workflows; `development_tools/config/pyrightconfig.json` = alternate audit `--project`. **Diagnostic parity** between them is **not** guaranteed yet — see next row. | **§5.7 — 7.6** |
| **Live metric snapshots** | Legacy file/marker counts, coverage %, duplicate groups, and coupling counts **change** after each `audit --full`. Prefer **AI_STATUS** / **LEGACY_REFERENCE_REPORT** over any numeric example embedded in V4/V5 prose. | §2 snapshot; **§5.6** |
| **Legacy report vs runtime legacy** | [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md) flags **legacy markers** and **injected inventory terms**. **2026-03-28**: active-bridge **inventory** may list **0 search terms** on purpose (`root_ruff_compat_mirror`); the report still shows **Deprecation Inventory** counts — not a broken generator. Executable `LEGACY COMPATIBILITY` branches — [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md). | §1.4; **§5.6** |
| **Tier 3 coverage vs audit scope** | Full audit may still run **both** main-track and dev-tools coverage today; `--dev-tools-only` should eventually run **only** dev-tools coverage so `DEV_TOOLS_*` metrics are not mixed with stale full-repo refreshes — **§5.1 — 1.9**. | **§5.1 — 1.9**; **§7.15** |
| **Tier 3 test outcome “cache” / unknown rows** | After a cache-only or precheck path, **AI_STATUS** Tier 3 lines may show `unknown` or `cache_only_precheck` — meaning “no fresh pytest run in this pass,” not necessarily a broken pipeline. Force a full Tier 3 run when you need live pytest counts. | Operational; not §5 backlog |

---

## 2. Current state snapshot (rolling)

Use **AI_STATUS.md** after each audit. Example **2026-04-08** (Tier 3 full, after `audit --full --strict`): overall test coverage **~69.9%**; development-tools coverage **~61.7%**; doc sync **PASS**; static analysis **CLEAN**; legacy references **CLEAN (0 files)**; duplicate-function groups **9**; high-coupling modules **51**; refresh **AI_PRIORITIES** / **CONSOLIDATED_REPORT** for module-refactor, coupling, and complexity counts before §6-style work.

**2026-04-08 (this plan iteration)**: §2.8 scoped-report copy in `DEV_TOOLS_*` (snapshot coverage vs full-repo staleness, scope notes, consolidated reference links); overlap analyzer filters numbered generic headings; §4.1 external-tool stance recorded in paired guides §10; §1.5 benchmark recipe noted in paired changelogs (numeric wall-clock still machine-local).

**2026-04-09**: Legacy scan now clean after removing a false-positive "legacy paths" phrase from `fix_project_cleanup.py`; documentation-overlap noise reduced by adding `prerequisites` and `test suite structure` to `EXPECTED_OVERLAPS` so shared test-guide boilerplate is not flagged.

**2026-04-09 (scripts backlog execution slice)**: migrated local script utilities into tracked dev-tools paths: `scripts/flaky_detector.py` -> `development_tools/tests/flaky_detector.py` and `scripts/testing/verify_process_cleanup.py` -> `development_tools/tests/verify_process_cleanup.py`; added CLI commands (`flaky-detector`, `verify-process-cleanup`), command docs updates, and unit tests. `development_tools/shared/fix_project_cleanup.py` remains canonical cleanup implementation for the `cleanup_project` overlap.

**2026-04-09 (V5 plan continuation — tooling slice)**: `verify_process_cleanup` uses **Get-CimInstance Win32_Process** on Windows for real `CommandLine` (Section 3.18); `sync-todo --dry-run` prints the dry-run report; `EXPECTED_OVERLAPS` extended (generic doc headings); guides Section 10 record **2026-04-09** external-tool decisions + Section 10.1 gap-analysis alignment; policy tests for Phase 2 taxonomy gate and Pyright delta env documentation. **Section 1.5** numeric cache benchmark still deferred (recipe unchanged; machine-local).

**2026-04-10 (V5 §4.2)**: **Bandit** + **pip-audit** integrated into Tier 3 static-analysis group; `requirements.txt`; coverage subprocess KeyboardInterrupt logs demoted to **WARNING** for cleaner `logs/errors.log`; `EXPECTED_OVERLAPS` + `external tools`.

**2026-04-11 (V5 continuation — plan slice)**: Reconciled **§4.1** vs **§4.2** (Tier 3 Bandit/pip-audit complete; remaining §4.1 = Radon/pydeps/pre-commit/vulture/ruff depth + pip-audit CI residual). **§7.6**: policy test asserts owned [`pyrightconfig.json`](config/pyrightconfig.json) matches root [`pyproject.toml`](../pyproject.toml) `[tool.pyright]` for shared diagnostic/exclude keys. **pip-audit**: `MHM_PIP_AUDIT_SKIP` env skips subprocess (offline/CI); guides + [`config.py`](config/config.py) comment. **§5.6**: `test_deprecation_inventory_policy.py` structural check for `root_ruff_compat_mirror`. Targeted tests: pip-audit skip, `_coverage_path_to_rel_posix` outside-project absolute path → `None`, flaky_detector empty inputs.

**2026-04-12 (V5 plan continuation)**: Fresh **`audit --full --clear-cache`** run for live Tier 3 pytest metrics. **§1.5** numeric domain-cache benchmark still deferred (recipe unchanged). **§3.0** initial `example_marker_validation` + `--check-example-markers` on [`analyze_documentation_sync.py`](docs/analyze_documentation_sync.py) (advisory). **`sync_todo_with_changelog(apply_auto_clean=True)`** + CLI **`sync-todo --apply`** removes auto-cleanable `- [x]` lines; mutually exclusive with `--dry-run`. **§5.2** [`EXPECTED_OVERLAPS`](shared/constants.py) extended (`development workflow`, `testing guide`). **§1.1** additional demo-project tests pass [`test_config.json`](../tests/development_tools/test_config.json). **§7.7** policy test asserts [`DEVELOPMENT_TOOLS_GUIDE.md`](DEVELOPMENT_TOOLS_GUIDE.md) §9 references Phase 2 / V5; **`root_ruff_compat_mirror`** exit criteria string enforced in inventory policy test. **`analyze_ai_work`**: docstring reminds thin scope (§5.3).

---

## 3. Completed themes (V4 collapsed)

No per-task history here — see V4 for checkboxes.

- Tiered audits, standardized metadata, JSON/report pipeline, report integrity (locks, snapshots).
- Coverage tooling, domain cache, Pyright/Ruff mtime caching, failure-aware invalidation.
- Stale-lock recovery (metadata + PID), docs/CLI lock behavior, interrupt cleanup.
- Major reporting fixes (Quick Wins file detail, Tier 3 outcomes, strict exit, docstring parity, consolidated report content level).
- Exclusion consistency, tooling policy tests, CLI alias inventory, many targeted coverage tests.
- Duplicate detection enhancements (including optional body similarity), error-handling metric alignment, `fix_function_docstrings` rename with compat aliases.
- Config portability baseline (owned `ruff.toml` / `pyrightconfig.json` paths), import-boundary check, `tests/data` exclusions for legacy analyzers.
- Slow-test optimizations, worker fallback **4→6**, `@pytest.mark.slow` on heavy tests.
- Retired unapproved standalone docs (content folded into code/guides).
- **2026-03-28 (V5 continuation slice)**: `DEV_TOOLS_*` report scope (headers, `--dev-tools-only` source line, scope/role blurbs; omit domain-coverage priority in dev-tools priorities); legacy report noise fix (`root_ruff_compat_mirror` empty `search_terms`, inventory summary unchanged); portability bootstrap (`run_dev_tools.py`, `fix_legacy_references.py` `Path.resolve()`; `generate_function_registry` output paths use module `project_root`); owned [`pyrightconfig.json`](config/pyrightconfig.json) `venvPath` / `venv` for repo interpreter; paired changelogs — see [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) / [AI_CHANGELOG.md](../ai_development_docs/AI_CHANGELOG.md).
- **2026-04-06**: Unified full-repo Tier 3 coverage (§1.9 / §7.17): main `run_test_coverage` runs dev-tools tests, measures `development_tools` in `coverage.ini`, derives `coverage_dev_tools.json`, persists `generate_dev_tools_coverage` on success, `constants.derived_prefix_excludes.core` updated for this repo.
- **2026-04-06 (V5 continuation)**: §7.16 read-fallback removal (scoped aggregates/tool JSON only); Phase 2 taxonomy gate recorded inline (§7.7); paired-guide §5 overlap advisory + §10 Radon line; `DEPRECATION_INVENTORY` bridge record; `analyze_config` / DEV_TOOLS report header polish.
- **2026-04-08**: §2.8 `DEV_TOOLS_*` clarity (snapshot dev-tools coverage vs stale full-repo `coverage.json`, dependency/duplicate scope notes, `DEV_TOOLS_PRIORITIES` refactor pointer, quick commands, consolidated reference links); §5.2 numbered-heading overlap filter in `analyze_documentation.detect_section_overlaps`; §4.1 / §10 external-tool evaluation notes (manual-only, no `requirements.txt` change); §1.5 benchmark methodology in paired changelogs.

---

## 4. Priority map (quick scan)

Rough ordering for triage (see **§5** for full V4-sourced detail):

| Tier | Themes |
|------|--------|
| **High** | Legacy executable paths + [DEPRECATION_INVENTORY.json](config/jsons/DEPRECATION_INVENTORY.json) (§6); portability / dual Pyright+Ruff baselines (§3.17, §7.6); directory taxonomy Phase 2–3 (§7.7). |
| **Medium** | §2.8 remaining scoped-report polish; coverage cache numeric benchmarks (§1.5); validation triggers (§3.2); **§4.1** complementary tools (Radon, pydeps, pre-commit, vulture, deeper ruff) — Bandit + pip-audit **Tier 3 integration shipped (§5.4 — 4.2)**; **§4.2** residual (pip-audit CI/offline policy); doc overlap analyzer (§5.2); AI work validation thin profile (§5.3); TODO sync automation (§5.4); gap-analysis tool rollout (§5.5). |
| **Lower / backlog** | `test_config.json` migration (§1.1); example-marking checker (§3.0); flaky detector + scripts migration (§3.12–3.15); unused-imports fixer (§5.1); memory profiler (§5.6); large-file refactors (§3.16); human backlog §7.8–7.13, §7.15. |
| **Monitoring** | Intermittent low coverage warning (§1.3) — reopen if recurrence. |

### 4.1 Phase 2 scheduling (after §4 High / Phase 1 portability-legacy work)

Suggested order when returning from Phase 1: **(1)** §2.8 any remaining scope-aware **sections** (1.9 shipped 2026-04-06; DEV_TOOLS headers updated 2026-04-06). **(2)** §1.5 coverage-cache benchmark session (methodology in §5.1 — 1.5; optional numeric capture). **(3)** §4.1 **remaining** external tools (Radon, pydeps, pre-commit, vulture, deeper ruff evaluation) per paired guides §10 — **Bandit + pip-audit Tier 3** are **complete** (**§5.4 — 4.2**, 2026-04-10); optional **Tier 1** promotion is a separate decision. **(4)** §5.2 documentation overlap analyzer improvements (advisory note in paired guide §5). **(5)** §5.3 AI work validation (keep thin). **(6)** §5.4 TODO sync dry-run automation. **(7)** §5.5 gap-analysis tool rollout (incremental). ~~**(8)** §7.16~~ **done 2026-04-06**.

---

## 5. Outstanding work — full detail (every open item from V4)

Each block mirrors **AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md** section numbering. Completed V4 checkboxes are omitted; use V4 for historical `[x]` audit trail.

**V4 sections with no remaining open tasks** (fully complete in V4; not expanded below): **1.4**, **1.6**, **1.7**; **2.1**, **2.3**, **2.6–2.7**, **2.9** (Tier 3 audit failure / exit semantics — completed follow-ups), **2.10–2.11**; **3.1**, **3.4–3.11**, **3.11.1**; **5.0**, **5.1.1**; **7.1–7.5**, **7.14**. **§7.16** read-fallback removal completed in V5 (2026-04-06). **§1.7** also noted optional future caching for tools still uncached — discovery done; not a gated backlog item.

### 5.1 Section 1 — Reliability, coverage, and test health

#### 1.1 Raise development tools coverage to 60%+ (residual)

- **Open**: Migrate **all** dev-tools tests that invoke analyzers to use `tests/development_tools/test_config.json` via `test_config_path` (fixture config intentionally does **not** exclude `tests/fixtures/` so analyzers can process fixtures). **Deferred (2026-03-25)** in V4: many tests already pass `test_config_path`; full migration is low priority — track when touching those tests or via AI_PRIORITIES.
- **Optional hardening**: AI_PRIORITIES item #2 (~80% advisory targets) for modules still under advisory coverage; use live `AI_PRIORITIES.md` + `generate_dev_tools_coverage_results.json` — do not duplicate module lists in this plan.

#### 1.2 Restore audit status tests (residual)

- **Open**: Re-enable `tests/development_tools/test_audit_tier_comprehensive.py` **only if** a narrow mocked subset is worth the maintenance cost (**deferred**). Replacement lightweight tests already landed per V4.

#### 1.3 Investigate intermittent low coverage warning

- **Status**: **MONITORING** (fixes landed in V4). Reopen if `generate_dev_tools_coverage_results.json` or audit shows suspicious low %; compare `run_test_coverage.py` with `--no-parallel` and shard merge logs.

#### 1.5 Coverage caching follow-ups (test-file cache)

- **Status**: **IN PROGRESS** (core behavior done in V4).
- **Open**:
  - Compare **full** vs **domain-filtered** runs and document **numeric** results in changelog — defer until a dedicated benchmark session captures stable numbers (machine-dependent).
  - **Methodology (V4)**: On Windows PowerShell, `Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }` vs the same **without** `--no-domain-cache` after a warm cache; compare wall-clock and logs for hit/miss. Paired changelog may reference the recipe without numbers until benchmarks exist. **2026-04-06**: The same style of comparison applies to unified full-repo runs (`python development_tools/run_development_tools.py audit --full` with vs without `--no-domain-cache` / `--clear-cache` as appropriate) when capturing domain-cache ROI after §1.9; numbers remain machine-specific.

#### 1.8 Improve slow development tools tests (residual)

- **Deferred (no batch change)**: Consider `scope="module"` for `temp_project_copy` where tests do not mutate shared state — **2026-03-24 V4**: shared-state risk; prefer **per-test review** when touching slow tests.
- **Note**: Concurrent worker fallback 4→6 and `@pytest.mark.slow` on heavy tests were completed; full-suite timing remains environment-dependent.

#### 1.9 Tier 3 coverage and test execution by audit scope (orchestration)

- **Status**: **COMPLETE — unified full-repo run (2026-04-06)**. Tier 3 schedules one heavy coverage subprocess per scope ([`shared/audit_tiers.py`](shared/audit_tiers.py) `get_tier3_groups`): full-repo runs **`run_test_coverage` only**; `--dev-tools-only` runs **`generate_dev_tools_coverage` only**. **Unified metrics (Option A / §7.17):** main `run_test_coverage` now **includes** `tests/development_tools/`, measures the **`development_tools`** package ([`tests/coverage.ini`](tests/coverage.ini); `development_tools` removed from `constants.derived_prefix_excludes.core` in project config), derives **`coverage_dev_tools.json`** from main **`coverage.json`**, persists **`generate_dev_tools_coverage`** after a successful full-repo run, and emits **`dev_tools_test_outcome`** for Tier 3; [`audit_orchestration._finalize_tier3_audit_scope`](shared/service/audit_orchestration.py) keeps dev-tools outcomes when present instead of always injecting “skipped this pass.”
- **Goals** (current behavior):
  - **`audit --full`** — single pytest+coverage pass for product **and** dev-tools tests; **Development Tools Coverage** in `AI_STATUS` refreshes with full-repo coverage.
  - **`audit --full --dev-tools-only`** — only dev-tools coverage/artifacts; main-repo coverage line documents staleness (unchanged).
- **Touchpoints**: [`shared/service/commands.py`](shared/service/commands.py) (`run_coverage_regeneration`), [`tests/run_test_coverage.py`](tests/run_test_coverage.py), [`config/development_tools_config.json`](config/development_tools_config.json).
- **Related**: **§7.15** (optional: coverage outside audit); **§5.2 — 2.8** (report copy vs data).

---

### 5.2 Section 2 — Reporting, recommendations, and output quality

#### 2.2 Standardize logging and surface top offenders

- **Status**: V4 marked **IN PROGRESS** but checklist nearly complete. **Residual**: opportunistic scan for stray `print(` in rarely run standalone paths; treat as **maintenance**, not a tracked gate.

#### 2.5 System signals purpose and redundancy cleanup

- **Status**: **IN PROGRESS (keep + clarify)** — V4 decision (2026-03-24): keep tool; clarify scope in reports + `reports/analyze_system_signals.py`.
- **Open**: **2026-03-26 V4**: Optional further trim/merge with doc-sync overlap — **deferred** unless duplicate metrics appear in a future audit.

#### 2.8 Run all tools in development_tools-only mode

- **Status**: **PARTIAL (2026-03-28)**. Implemented: `audit --dev-tools-only`, `DEV_TOOLS_*` output paths, `get_scan_directories() -> ['development_tools']`, and **report-layer** scope (`ReportGenerationMixin`: titles, file blurbs, `--dev-tools-only` on source command, scope/role lines; domain-coverage priority omitted in dev-tools priorities).
- **Open**:
  - **Orchestration**: ~~Tier 3 coverage/test scope split~~ **Done (2026-04-06)** per §1.9.
  - ~~Ambiguous snapshot/scope copy~~ **Reduced (2026-04-08)**: snapshot coverage line, dependency/duplicate notes, quick commands, consolidated references; reopen if new sections confuse scoped vs full-repo readers.

#### 2.9 Console output polish (optional)

- **Status**: **IN PROGRESS** — spot-check done; **progress indicators** (spinners/TUI) still **TBD**. Tier/tool logging and stdout discipline reviewed 2026-03-26 per V4.

---

### 5.3 Section 3 — Tooling integrity and validation

#### 3.0 Example marking standards checker (doc-sync validation)

- **Status**: **PARTIAL (2026-04-12)** — advisory scan shipped; strict gating / CI failure TBD.
- **Done (2026-04-12)**: [`example_marker_validation.py`](docs/example_marker_validation.py); CLI flag `--check-example-markers` on [`analyze_documentation_sync.py`](docs/analyze_documentation_sync.py); unit tests [`test_example_marker_validation.py`](../tests/development_tools/test_example_marker_validation.py).
- **Open tasks**:
  - Tighten heuristics (reduce false positives); optional integration into default `doc-sync` / audit tiers once signal is trusted.
  - Validate example headings (`Examples:`, `Example Usage:`, `Example Code:`) beyond Markdown `##` patterns.
  - Report unmarked examples with file/line detail in consolidated output when promoted from advisory.

#### 3.2 Validation warnings cleanup (residual)

- **Open** (low priority):
  - Review `needs_enhancement` and `new_module` triggers.
  - Decide if **test files** should be excluded from these checks.

#### 3.3 Version sync functionality

- **Status**: **IN PROGRESS** in V4; substantive discovery/docs done. **Open**: ongoing maintenance if `fix_version_sync.py` / `run_version_sync` behavior drifts; experimental tier — see paired guides §2.

#### 3.12 Integrate flaky detector into development tools suite

- **Status**: **COMPLETE (2026-04-09)**.
- **Decision**: Migrated functionality to tracked `development_tools/tests/flaky_detector.py`.
- **Delivered**: CLI wiring (`flaky-detector`), tool metadata registration, and targeted unit tests.

#### 3.13 Scripts-to-development-tools migration (persistent scripts)

- **Status**: **COMPLETE (2026-04-09)**. **User priority**: Continue.
- **Completed this slice**:
  - Built a definitive inventory from local script sources and migrated persistent test utilities into tracked dev-tools ownership.
  - Migrated `scripts/testing/verify_process_cleanup.py` to `development_tools/tests/verify_process_cleanup.py`.
  - Updated active guidance docs to reflect migration/canonical ownership decisions.
- **Open tasks**:
  - Keep project-specific script ownership items in `TODO.md` (runtime/admin utilities that are not dev-tools portability work).
  - If new persistent scripts are introduced later, classify immediately (`migrate_to_development_tools` / `retain_as_project_script` / `retire`) using canonical-list and portability rules.

#### 3.14 Scripts review candidates (evaluate before retire/migrate)

- **Status**: **PARTIAL COMPLETE (2026-04-09)**. **User priority**: Systematic review.
- **Decision set (tracked tree)**:
  - `scripts/cleanup_project.py` vs `development_tools/shared/fix_project_cleanup.py`: canonical owner is `development_tools/shared/fix_project_cleanup.py`; script path treated as retired historical reference.
  - `flaky_detector` and `verify_process_cleanup` are now migrated to tracked dev-tools paths.
  - Remaining non-migrated `scripts/*` candidates continue as backlog items for later path-by-path review.
- **Operational rule**: keep `scripts/` temporary-only; if a script becomes persistent, migrate immediately to tracked ownership per [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md).

#### 3.15 Gap tasks from retired scripts (development-tools scope)

- **Status**: **DEFERRED (no active source files in tracked tree)**. **User priority**: Low.
- **Open**:
  - Incorporate heuristics from retired `scripts/cleanup_unused_imports.py` (missing logging / error-handling / type-hints categorization) into `analyze_unused_imports.py` and/or `generate_unused_imports_report.py` — **evaluate**.
  - Add dedicated per-function AST helper/fixer for try-except → decorator migration (inspired by `scripts/replace_try_except_with_decorator.py`), complementing `error_handling/analyze_error_handling.py` — **evaluate**.

#### 3.16 Explore refactoring `report_generation.py` and `run_test_coverage.py`

- **Status**: **PLAN DOCUMENTED; implementation deferred**.
- **User priority**: Medium/low; overlaps AI_PRIORITIES “large/high-complexity modules” (e.g. ~60 candidates).
- **V4 structure maps** (summarized): `report_generation.py` — extract Tier 3 helpers, AI_STATUS / AI_PRIORITIES / CONSOLIDATED builders, downstream action items. `run_test_coverage.py` — extract pytest argv, shard merge, domain cache, outcome classification; slim `CoverageMetricsRegenerator`.
- **Open**: Implement refactors in **small steps** with tests + full audit validation after each step.

#### 3.17 Portability and project-independence compliance sweep

- **Status**: **IN PROGRESS**. **User priority**: High.
- **Remaining focus (V4 narrative + inventory)**:
  - Hardcoded-path hotspots: **2026-03-28** slices landed for `run_dev_tools.py` / `legacy/fix_legacy_references.py` (`Path.resolve()` bootstrap), `generate_function_registry.py` output paths (module `project_root`); continue review for `run_development_tools.py`, `config/analyze_config.py`, and any new call sites.
  - Some environments: `audit --full --strict` may hit **runtime limits** — full portability validation still a goal.
  - Import-boundary check exists; keep enforcing isolation of `development_tools/**` from business domains.

#### 3.18 `verify_process_cleanup` — reliable Windows orphan detection

- **Status**: **COMPLETE (2026-04-09)** — primary path uses **PowerShell Get-CimInstance** `Win32_Process` (full `CommandLine`); **tasklist** CSV retained only as fallback when CIM fails.
- **Problem (resolved)**: Prior `tasklist`-only listing did not expose command lines; pytest/xdist heuristics were unreliable.
- **Goal**: Retrieve `CommandLine` reliably on Windows — **done** via CIM; fallback logs a warning.
- **Reporting**: Tier 3 JSON + STATUS snapshot + consolidated section unchanged; priorities list the item **only when** there are issues.

---

### 5.4 Section 4 — External tool evaluation

#### 4.1 Evaluate and integrate complementary tools

- **Status**: **IN PROGRESS**. **User priority**: Evaluate bandit, pip-audit, radon, pre-commit; ruff already in use for lint.
- **Done (V4)**: Evaluation stance + backlog pointer in paired guides §10.
- **Recorded (2026-04-09)**: Radon / pydeps remain **manual-only** pilots.
- **Recorded (2026-04-10)**: **Bandit** + **pip-audit** integrated into Tier 3 (`analyze_bandit`, `analyze_pip_audit`); listed in `requirements.txt`; paired guides §10 updated.
- **Open tasks** (post–Tier 3 Bandit/pip-audit):
  - Evaluate **ruff** (lint/format) and **radon** (complexity) for deeper integration beyond current audit usage.
  - Evaluate **pydeps** for dependency graphs vs existing dependency tooling.
  - Optional: promote **bandit** / **pip-audit** to **Tier 1** (quick audit) if latency and signal justify it — today they run in **Tier 3** only (**§5.4 — 4.2**).
  - Decide: replace, complement, or keep other complementary tools.
  - If integrating additional tools: wrappers, `requirements.txt`, docs.
  - Optional: **vulture** (dead code), **pre-commit** (hooks).

#### 4.2 Integrate Bandit and pip-audit into audit tiers

- **Status**: **COMPLETE (2026-04-10)** — Tier 3 static-analysis group; `tool_wrappers` + scoped JSON + mtime cache (bandit) / requirements-hash cache (pip-audit); **AI_STATUS** / **CONSOLIDATED_REPORT** / **AI_PRIORITIES**; tests in [`tests/development_tools/test_analyze_security_static_checks.py`](../tests/development_tools/test_analyze_security_static_checks.py).
- **Semantics shipped**: Bandit summary counts **MEDIUM/HIGH** only (tests/ trees excluded by default); pip-audit findings use summary **WARN** when vulnerabilities exist; **strict** exit still driven by pytest Tier 3 outcome, not these tools.
- **Residual / follow-up**: CI/offline policy for pip-audit (`MHM_PIP_AUDIT_SKIP` env + paired guide §10); optional noise tuning via `static_analysis` config keys in [`config/config.py`](config/config.py); Radon/pydeps manual pilots remain §4.1.
- **Related**: §5.4 — 4.1 (evaluation backlog); [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) Section 10.

---

### 5.5 Section 5 — Future enhancements

#### 5.1 Unused imports cleanup module

- **Status**: **PARTIAL** (investigation + regression + report clarity **done**; fix script / `--categorize` still open). **User priority**: Low.
- **All-zero report (2026-03-29)**: Not a pipeline bug. `ruff check --select F401` on this repo returns **no** violations (clean under current `.ruff.toml`). Stored runs often use **`cache_only`** (see `details.stats.cache_mode`): **Total Files Scanned** counts discovery; the linter is not re-run on every file. The markdown report now includes **backend**, **cache mode**, **files re-linted this run**, and a short note on interpreting zeros + `--clear-cache`. Ruff/pylint batch paths are keyed by **`Path.resolve()`** so JSON paths cannot silently miss the per-file issue map. Regression: `test_scan_minimal_project_finds_ruff_f401` (minimal tmp tree with an unused `import os`).
- **Open**:
  - Categorization logic; category-based reporting; implement `imports/fix_unused_imports.py`; cleanup recommendations; optional `--categorize` flag.

#### 5.2 Documentation overlap analysis enhancements

- **Status**: **IN PROGRESS**. **User priority**: Medium.
- **Done (2026-04-08)**: `detect_section_overlaps` treats numbered generic headings (`1. Purpose and Scope`, `1. Quick Start`, …) like `EXPECTED_OVERLAPS` entries to cut **AI_STATUS** / doc-sync noise.
- **Done (2026-04-09)**: Added `getting started`, `installation`, `configuration`, `related documents` to `EXPECTED_OVERLAPS` (shared guide boilerplate).
- **Open**: Review consolidation opportunities (Development Workflow, Testing); consolidation plan; improve actionable insights; further false-positive tuning beyond generic headings.

#### 5.3 AI work validation improvements

- **Status**: **IN PROGRESS**. **User priority**: High/medium (value uncertain).
- **Open**: Avoid overlap with domain-specific analyzers — keep tool **thin** (ongoing).

#### 5.4 TODO sync cleanup automation

- **Status**: **PARTIAL (2026-04-12)**. **User priority**: Low.
- **Done**: `python development_tools/docs/fix_version_sync.py sync-todo --dry-run` prints **dry_run_report** to stdout (no edits); documented in [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md). **`sync-todo --apply`** removes auto-cleanable `- [x]` / `- [X]` checklist lines only (`sync_todo_with_changelog(apply_auto_clean=True)`); mutually exclusive with `--dry-run`.
- **Open**: Broader workflow docs if needed; optional changelog cross-check before apply remains human responsibility.

#### 5.5 New tool creation based on gap analysis

- **Status**: **IN PROGRESS**. **Effort**: Large.
- **Done (V4)**: `module-refactor-candidates` tool and Tier 2 integration.
- **Done (2026-04-09)**: [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) §10.1 documents using **`module-refactor-candidates`** + priorities JSON as the practical gap signal until a multi-category matrix exists.
- **Open**:
  - Prioritize gaps across: Documentation, Code quality, Testing, Configuration/environment, AI/prompt, Integration/workflow.
  - Implement tools (analyze/generate/fix patterns).
  - Tests using `tests/fixtures/development_tools_demo/`.
  - Tool metadata + documentation.
  - Audit tier placement where appropriate.

#### 5.6 Memory profiler integration

- **Status**: **PENDING**. **Source**: `scripts/testing/memory_profiler.py`. **User priority**: TBD.
- **Open**: Integrate or not; approach (new tool vs enhancement vs standalone); JSON/report + CLI; tests + fixture; metadata + docs + tier placement.

---

### 5.6 Section 6 — Audit-driven remediation (non-tool code)

Outstanding product/codebase work **surfaced by tools**, not dev-tools implementation per se. **Use live counts** from [AI_STATUS.md](AI_STATUS.md), [AI_PRIORITIES.md](AI_PRIORITIES.md), [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md).

**User priorities (V4)**:

- **(a)** Retire legacy markers: proper retirement of legacy **code** first, then markers — follow [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md).
- **(d)** Unused imports: many “keep”; improve classification; consider relying on ruff; optional suppression in audit to avoid duplication with unused-imports tool.
- **(d)** Raise domain coverage (communication, ui, core) toward 80% when opportune.
- **(a)** Refactor critical-complexity functions — active but not top priority.

**Open tasks**:

- Retire remaining legacy reference markers (`fix_legacy_references.py --find` / `--verify`; `run_development_tools.py legacy` or `audit --full`).
- Work down [DEPRECATION_INVENTORY.json](config/jsons/DEPRECATION_INVENTORY.json) **active** entries (confirm IDs in file): **`root_ruff_compat_mirror`** remains until portability exit criteria; removed entries (`legacy_timestamp_parsing`, `backup_zip_compat_bridge`, `tier3_coverage_outcome_compat_bridge`, etc.) stay in `removed_inventory` for history.
- Validate and **document exit criteria** per item before removal; update inventory status **in the same change**.
- Reduce unused imports (see AI_PRIORITIES); verify via unused-imports report.
- Raise domain coverage for communication, ui, core (below target).
- Refactor critical-complexity functions (see AI_PRIORITIES counts).

---

### 5.7 Section 7 — Additional human/developer items

#### 7.6 Portability follow-up: static tooling and packaging (residual)

- **Open — acceptance criteria and tests**:
  - Fixture-based validation: suite runs in a **minimal external repo** with no root lint/type config files.
  - Validation: reports remain complete when host-repo lint/type configs differ from dev-tools defaults.
  - **Partial (V4)**: `tests/development_tools/test_pyright_config_paths.py` — root `pyproject.toml` `[tool.pyright]`, owned Pyright JSON, owned + root `ruff.toml` parse; owned `development_tools/config/pyrightconfig.json` has `typeCheckingMode` + non-empty `exclude`.
- **Dual-config situation (V4 2026-03-02; root Pyright 2026-04-10 in `pyproject.toml`)**:
  - Root **`pyproject.toml` `[tool.pyright]`** = whole-repo IDE/direct baseline; `development_tools/config/pyrightconfig.json` = dev-tools-owned alternate `--project` (diagnostics not yet fully comparable).
  - Root `.ruff.toml` = compatibility mirror; `development_tools/config/ruff.toml` = owned path for wrappers.
- **Next steps before single baseline**:
  - Align dev-tools Pyright so `analyze_pyright` matches root diagnostic baseline (no artificial drops from scope drift).
  - Regression tests: both Pyright paths; fail if error/warning deltas exceed agreed tolerance without explicit exclusions. **Partial (2026-03-27)**: optional enforcement in `tests/development_tools/test_pyright_config_paths.py` e2e — set env `PYRIGHT_ERROR_COUNT_MAX_DELTA` to a non-negative integer when running the e2e Pyright test; unset by default (scopes differ). **2026-03-28**: owned [`pyrightconfig.json`](config/pyrightconfig.json) adds `venvPath` / `venv` so `pyright --project` resolves the repo `.venv` from the owned config path. **2026-04-10**: root baseline moved to [`pyproject.toml`](../pyproject.toml) `[tool.pyright]` (removed root `pyrightconfig.json`).
  - Decide: keep root `.ruff.toml` permanently as mirror vs deprecate after portability criteria met.
  - If deprecating root configs: migration + fallback documented in both guides before removal.

#### 7.7 Directory taxonomy and config boundary cleanup (residual)

- **Done (V4)**: Phase 1 taxonomy docs, configuration surface table (guides §9), phased plan outline.
- **Phase 2–3 evaluation (2026-03-27)**: No directory moves or new packages this session. **Decision**: keep `development_tools/config/` as the single config surface for JSON/TOML/Pyright entrypoints; `development_tools/shared/` remains shared runtime (locks, orchestration, exclusions).
  - **Gate for any Phase 2 move (recorded 2026-04-06)**: Do not move anything unless **(a)** `python development_tools/run_development_tools.py audit --quick` passes with no new import-boundary violations (`analyze_dev_tools_import_boundaries`), and **(b)** the change lists the exact files to move, temporary import re-exports for one deprecation window, and rollback steps in the same PR (or the paired changelog entry for that PR).
  - This keeps contributors oriented and avoids partial/half-migrated directory surfaces.
- **Open**:
  - Evaluate moving runtime/platform internals out of `development_tools/config/` (e.g. `development_tools/shared/runtime_config/`) with backward compatibility.
  - Evaluate overlap `development_tools/shared/` vs `development_tools/config/` — config plumbing vs generic utilities; ownership rules.
  - **Structure acceptance criteria**: new contributors find config entrypoints quickly; core commands unchanged during migration; import paths supported until deprecation window ends.

#### 7.8 Possible duplicate lists (from TODO.md)

- Investigate docs + code for duplicate or partial lists (constants, commands, files).
  - Establish canonical location per list type; code dynamic; docs point to canonical.
  - Extend dev-tools to detect duplicate-list candidates.
  - Reduce drift.

#### 7.9 Audit MHM project for duplicate, outdated, unnecessary backups

- Audit duplicate/outdated backups and archive copies.
  - Structured regular local backups (compression + rotation).
  - Integrate with `backup verify` and retention tooling.

#### 7.10 Tool: detect unused functions, variables, etc.

- Placeholder in V4 — define scope (e.g. vulture integration vs custom) when prioritized.

#### 7.11 Tool: detect facades, shims, etc.

- Placeholder — align with deprecation inventory and legacy guide when prioritized.

#### 7.12 Standardize exclusion marking systems across tools

- Unify how tools mark code exempt from compliance flags; document in [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md) and [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) (project-relative paths — not machine-specific).

#### 7.13 Duplicate function detector: argument similarity and related signals

- Extend beyond current name/body work when prioritized.

#### 7.15 Separate test coverage from full audit

- Product direction: full audit could run **tests only**; coverage via separate schedule or extra flag/tier — aligns with V4 intro (Tier 3 without embedded coverage).
- **2026-03-28**: Practical next step is **§5.1 — 1.9** (single coverage dimension per audit scope in one pass) as a subset of this direction; larger “coverage wholly outside audit” remains optional.

#### 7.16 Retire audit artifact read fallbacks (flat JSON / unscoped aggregates)

**Status**: **COMPLETE (2026-04-06)** — read fallbacks removed; `legacy_flat_jsons_dir()` retained for cleanup/`--clear-cache` orphan deletion and inventory history ([`DEPRECATION_INVENTORY.json`](config/jsons/DEPRECATION_INVENTORY.json) `legacy_flat_tool_json_and_unscoped_aggregate_read_bridges`).

| Location | Outcome |
| -------- | ------- |
| `development_tools/<domain>/jsons/*` (flat) | No longer read by `output_storage.load_tool_result` / `load_tool_cache` / `get_all_tool_results` |
| `development_tools/reports/analysis_detailed_results.json` (unscoped) | No longer a load fallback in `audit_orchestration` / `quick_status` / `data_loading` / `data_freshness_audit` |
| `development_tools/reports/jsons/tool_timings.json` (unscoped) | No longer merged in `_save_timing_data` load path |
| `analyze_system_signals` aggregate candidates | Scoped `reports/scopes/{full,dev_tools}/` only |

#### 7.17 Full audit includes development_tools tests and package coverage (resolved)

- **Decision (2026-04-06)**: **Option A — unified main run.** `run_test_coverage` executes **`tests/development_tools/`** with the main suite, measures **`development_tools`** via `coverage.ini` + `CORE_MODULES` (project config no longer excludes `development_tools` from derived `core_modules`), and writes **`coverage_dev_tools.json`** as a filtered view of **`coverage.json`** so `AI_STATUS` / `generate_dev_tools_coverage_results.json` stay aligned without a second pytest in the same full-repo Tier 3 pass. `--dev-tools-only` remains the narrow pass for dev-tools tree work without refreshing full-repo coverage.
- **Implementation refs**: [`tests/run_test_coverage.py`](tests/run_test_coverage.py) (`_write_dev_tools_coverage_json_from_main`, `_build_unified_dev_tools_test_outcome`), [`shared/service/commands.py`](shared/service/commands.py), [`shared/service/audit_orchestration.py`](shared/service/audit_orchestration.py).

#### 7.18 Scoped `DEV_TOOLS_*` reports and `--clear-cache`

- **`DEV_TOOLS_STATUS.md` / `DEV_TOOLS_PRIORITIES.md` / `DEV_TOOLS_CONSOLIDATED_REPORT.md`**: Built when `audit --full --dev-tools-only` (or other tiers with the same flag) runs. Text and ranked items should reflect **`development_tools/`** where the underlying JSON is repo-wide (duplicates, refactor candidates, dependency-pattern examples, unused-import **obvious** counts, doc quick wins from doc-fix tools, etc.). Paired-documentation quick wins (`TODO.md` / changelog pairing) are **omitted** from dev-tools priorities quick wins because they target repo docs outside `development_tools/`; use a default-scope audit for those.
- **`--clear-cache`**: For `audit` / `full-audit`, cache clearing is **scope-aligned**: with `--dev-tools-only` (global or on the command), only **`**/jsons/scopes/dev_tools/**`**, **`reports/scopes/dev_tools/**`**, and dev-tools coverage JSON siblings are removed; without it, only **full-repo** tool cache artifacts are removed (parallel **`scopes/full`** tree, main `coverage.json` inputs, archives, legacy aggregates), leaving dev-tools-only caches intact. A bare `cleanup --clear-cache` (non-audit) still clears **all** tool cache layouts.
- **Logging**: Report generation log lines use the real output filename (`DEV_TOOLS_STATUS.md`, etc.) when scope is dev-tools-only.
- **Residual full-repo rows**: Some tiered priorities (e.g. legacy reference counts, backup health) still use **aggregate audit payloads** that are not path-sliced in this pass; when in doubt, confirm against `AI_STATUS.md` / `AI_PRIORITIES.md` from a default-scope audit.
- **Full-repo `development_docs` reports vs narrow scope**: Do not rely on dev-tools-only runs to refresh whole-repo markdown under `development_docs/` — **§7.19** implements gating (analyzers may still run; markdown writers for those paths are skipped with INFO logs).

#### 7.19 Full-repo `development_docs` reports — skip regeneration on dev-tools-only / non–full-repo audits

- **Problem**: `audit --full --dev-tools-only` and other **non–full-repo** audit paths can still invoke generators that **overwrite** whole-repository evidence in `development_docs/`, so those files appear **wrong or misleadingly stale** until a **default-scope** (`full-repo`) audit runs.
- **Status**: **COMPLETE (2026-04-09)** — `development_tools/shared/audit_tiers.py` gates markdown generators when `dev_tools_only_mode` is true:
  - **[`UNUSED_IMPORTS_REPORT.md`](../development_docs/UNUSED_IMPORTS_REPORT.md)**: Tier 2 still runs `analyze_unused_imports`; `generate_unused_imports_report` is not scheduled.
  - **[`TEST_COVERAGE_REPORT.md`](../development_docs/TEST_COVERAGE_REPORT.md)**: Tier 3 omits `generate_test_coverage_report` from the coverage-dependent chain (unchanged from prior dev-tools-only Tier 3 split); INFO log documents skip.
  - **[`LEGACY_REFERENCE_REPORT.md`](../development_docs/LEGACY_REFERENCE_REPORT.md)**: Tier 3 still runs `analyze_legacy_references`; `generate_legacy_reference_report` is not scheduled.
  - **Logging**: INFO lines name the skipped tool and `development_docs/` target path. **Tests**: `tests/development_tools/test_audit_orchestration_helpers.py` (`get_tier2_groups`, `get_tier3_groups`, `_get_expected_tools_for_tier` with `dev_tools_only_mode`).
- **Alternatives** (deferred): write **scoped** markdown under `development_tools/reports/scopes/dev_tools/` instead of skipping — not implemented in this slice.
- **Related**: **§7.18** (scoped `DEV_TOOLS_*` reports); **§5.1 — 1.9** (coverage dimension vs audit scope); **§7.20** (future parameterized audit root).

#### 7.20 Future: audit scoped to an arbitrary directory

- **Goal**: Run a tiered audit against **any** repo subtree (e.g. `communication/` only), not only **full repo** vs **`development_tools/`** (`audit --full --dev-tools-only`). **Status**: **deferred / design-first** — not a small extension of §7.19.

- **What exists today**
  - [`audit_orchestration.py`](shared/service/audit_orchestration.py) temporarily replaces `get_scan_directories()` with `["development_tools"]` when `dev_tools_only_mode` is set — a **binary** narrow scope, not a parameterized path.
  - Individual tools combine `get_scan_directories()`, config exclusions, and domain-specific roots; behavior is **not** uniformly “restrict every analyzer to one directory.”

- **Incremental / easier pieces**
  - A future CLI flag (e.g. `--audit-scope <relative_dir>`) or service field such as `audit_scope_paths: list[str]` threaded into orchestration and **`get_scan_directories()`** for tools that already respect scan roots.

- **Hard pieces (separate epic after design sign-off)**
  - **Coverage / pytest**: `run_test_coverage` and `generate_dev_tools_coverage` assume fixed test layouts and [`coverage.ini`](tests/coverage.ini) / domain wiring; an arbitrary folder may not map to one coverage run without new semantics.
  - **Tier tools**: Many analyzers assume fixed package locations and repo-relative JSON outputs; a usable “audit this tree only” needs **per-tool scope contracts**, consistent **scoped** artifacts (partially modeled under `jsons/scopes/`), and regression tests.
  - **Report generators**: Same class of policy as **§7.19** — which `development_docs/` (or other) markdown files may be written for which scope; needs an explicit matrix, not ad hoc skips.

- **Recommendation**: Ship **§7.19** (full-repo vs dev-tools-only gating for the three reports) first. Then add a short **design doc** (CLI shape, which tiers honor scope, coverage behavior, DEV_TOOLS vs ad-hoc scope) and track implementation in phased PRs. **Related**: **§7.19**, **§7.18**, **§5.1 — 1.9**.

---

### 5.8 Monitoring and deferred test work (no active V4 tasks)

- **§1.3** — Intermittent low coverage: **MONITORING**; reopen on recurrence.
- **§1.2** — `test_audit_tier_comprehensive.py`: **deferred** unless cost/benefit justifies re-enable.

**Lower backlog (opportunistic, 2026-03-28)** — pick up when touching related code: §1.1 adopt `test_config.json` in analyzer tests you edit; §1.9 orchestration when refactoring Tier 3; §3.0 example-marking in doc-sync; §3.13–3.14 remaining scripts inventory/review candidates; §3.15 gap heuristics; §3.16 extract helpers from `report_generation.py` / `run_test_coverage.py`; §7.8–7.13, §7.15 as separately prioritized.

---

## 6. Related documents

- [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) — full V4 checklist history  
- [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md) / [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md)  
- [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)  
- [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) (Standard Audit Recipe §10)  
- [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md)  
- [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md) — scripts backlog and flaky detector notes  
- [LIST_OF_LISTS.md](../development_docs/LIST_OF_LISTS.md) — canonical list principles (relevant to §7.8)  
