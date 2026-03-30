# AI Development Tools — Improvement Roadmap (V5)

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Single forward-looking backlog after V4; collapsed history; actionable next steps  
> **Style**: Direct and concise  
> **Last Updated**: 2026-03-29  
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
- **Scope-aware report content** for `--dev-tools-only` — **partial (2026-03-28)**: `DEV_TOOLS_*` titles, metadata, source command (`--dev-tools-only`), scope blurbs; domain-coverage priority omitted in `DEV_TOOLS_PRIORITIES.md`. **Remaining**: drive **Tier 3 coverage execution from audit scope** so a single run does not refresh both full-repo and dev-tools coverage when only one scope is intended (see **§5.1 — 1.9** and **§7.15**).
- **Flaky detector**: `scripts/flaky_detector.py` is **not** in the current tree; migration and CLI wiring **not done** (V4 §3.12).
- **Scripts migration inventory**, **3.14 review candidates**, **3.15 gap tasks** — open.
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
| **Dual Pyright / dual Ruff configs** | Root configs = IDE/whole-repo workflows; dev-tools configs = audit wrappers. **Diagnostic parity** between root and `development_tools/config/pyrightconfig.json` is **not** guaranteed yet — see next row. | **§5.7 — 7.6** |
| **Live metric snapshots** | Legacy file/marker counts, coverage %, duplicate groups, and coupling counts **change** after each `audit --full`. Prefer **AI_STATUS** / **LEGACY_REFERENCE_REPORT** over any numeric example embedded in V4/V5 prose. | §2 snapshot; **§5.6** |
| **Legacy report vs runtime legacy** | [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md) flags **legacy markers** and **injected inventory terms**. **2026-03-28**: active-bridge **inventory** may list **0 search terms** on purpose (`root_ruff_compat_mirror`); the report still shows **Deprecation Inventory** counts — not a broken generator. Executable `LEGACY COMPATIBILITY` branches — [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md). | §1.4; **§5.6** |
| **Tier 3 coverage vs audit scope** | Full audit may still run **both** main-track and dev-tools coverage today; `--dev-tools-only` should eventually run **only** dev-tools coverage so `DEV_TOOLS_*` metrics are not mixed with stale full-repo refreshes — **§5.1 — 1.9**. | **§5.1 — 1.9**; **§7.15** |
| **Tier 3 test outcome “cache” / unknown rows** | After a cache-only or precheck path, **AI_STATUS** Tier 3 lines may show `unknown` or `cache_only_precheck` — meaning “no fresh pytest run in this pass,” not necessarily a broken pipeline. Force a full Tier 3 run when you need live pytest counts. | Operational; not §5 backlog |

---

## 2. Current state snapshot (rolling)

Use **AI_STATUS.md** after each audit. Example **2026-03-28** (Tier 3 full, after `audit --full`): overall test coverage **~76.1%**; development-tools coverage **~61.9%**; doc sync **PASS**; static analysis **CLEAN**; legacy references **CLEAN (0 files)**; duplicate-function groups **12**; refresh **AI_PRIORITIES** / **CONSOLIDATED_REPORT** for module-refactor, coupling, and complexity counts before §6-style work.

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

---

## 4. Priority map (quick scan)

Rough ordering for triage (see **§5** for full V4-sourced detail):

| Tier | Themes |
|------|--------|
| **High** | **Tier 3 coverage driven by audit scope** (§5.1 — 1.9; orchestration in `audit_orchestration` / `run_test_coverage`, aligns §7.15); legacy executable paths + [DEPRECATION_INVENTORY.json](config/jsons/DEPRECATION_INVENTORY.json) (§6); portability / dual Pyright+Ruff baselines (§3.17, §7.6); directory taxonomy Phase 2–3 (§7.7). |
| **Medium** | Finish `--dev-tools-only` story after 1.9 (remaining §2.8 report/tool sections if any); coverage cache numeric benchmarks (§1.5); validation triggers (§3.2); external security/complexity tools (§4.1); doc overlap analyzer (§5.2); AI work validation thin profile (§5.3); TODO sync automation (§5.4); gap-analysis tool rollout (§5.5). |
| **Lower / backlog** | `test_config.json` migration (§1.1); example-marking checker (§3.0); flaky detector + scripts migration (§3.12–3.15); unused-imports fixer (§5.1); memory profiler (§5.6); large-file refactors (§3.16); human backlog §7.8–7.13, §7.15. |
| **Monitoring** | Intermittent low coverage warning (§1.3) — reopen if recurrence. |

### 4.1 Phase 2 scheduling (after §4 High / Phase 1 portability-legacy work)

Suggested order when returning from Phase 1: **(1)** **§5.1 — 1.9** — Tier 3 **test/coverage execution** follows audit scope (full audit → main/project coverage only; `--dev-tools-only` → dev-tools coverage only; clarify stale-vs-fresh rules for `AI_STATUS` / caches). **(2)** §2.8 any remaining scope-aware **sections** once 1.9 makes metrics honest without report-only filtering. **(3)** §1.5 coverage-cache benchmark session (methodology in §5.1 — 1.5; optional numeric capture). **(4)** §4.1 external tools evaluation (bandit, pip-audit, radon, pre-commit) per paired guides §10. **(5)** §5.2 documentation overlap analyzer improvements. **(6)** §5.3 AI work validation (keep thin). **(7)** §5.4 TODO sync dry-run automation. **(8)** §5.5 gap-analysis tool rollout (incremental).

---

## 5. Outstanding work — full detail (every open item from V4)

Each block mirrors **AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md** section numbering. Completed V4 checkboxes are omitted; use V4 for historical `[x]` audit trail.

**V4 sections with no remaining open tasks** (fully complete in V4; not expanded below): **1.4**, **1.6**, **1.7**; **2.1**, **2.3**, **2.6–2.7**, **2.9** (Tier 3 audit failure / exit semantics — completed follow-ups), **2.10–2.11**; **3.1**, **3.4–3.11**, **3.11.1**; **5.0**, **5.1.1**; **7.1–7.5**, **7.14**, **7.16–7.17**. **§1.7** also noted optional future caching for tools still uncached — discovery done; not a gated backlog item.

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
  - **Methodology (V4)**: On Windows PowerShell, `Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }` vs the same **without** `--no-domain-cache` after a warm cache; compare wall-clock and logs for hit/miss. Paired changelog may reference the recipe without numbers until benchmarks exist.

#### 1.8 Improve slow development tools tests (residual)

- **Deferred (no batch change)**: Consider `scope="module"` for `temp_project_copy` where tests do not mutate shared state — **2026-03-24 V4**: shared-state risk; prefer **per-test review** when touching slow tests.
- **Note**: Concurrent worker fallback 4→6 and `@pytest.mark.slow` on heavy tests were completed; full-suite timing remains environment-dependent.

#### 1.9 Tier 3 coverage and test execution by audit scope (orchestration)

- **Status**: **PRIORITY — not implemented (2026-03-28)**. Today, a full Tier 3 audit may still refresh **both** main/project coverage and **development_tools** coverage tracks; `--dev-tools-only` restricts **analyzers** via `get_scan_directories()` but coverage subprocess design should align so effort and artifacts match intent.
- **Goal**:
  - **`audit --full` (default, full-repo scope)** — run **project / main-track** pytest+coverage (existing domain summary, `TEST_COVERAGE_REPORT`, etc.) as today; do **not** require a separate dev-tools coverage run in the same pass unless policy explicitly keeps both (if both stay, document why).
  - **`audit --full --dev-tools-only`** — run **only** `tests/development_tools/` (or equivalent dev-tools coverage entrypoint); refresh **only** dev-tools coverage JSON/HTML consumed by `DEV_TOOLS_*` reports; avoid refreshing or implying fresh **full-repo** coverage in that pass.
- **Why**: Reduces duplicate wall-clock, avoids **stale full-repo metrics** appearing next to **fresh dev-tools** metrics (or the reverse), and can **remove reliance** on report-layer omissions (e.g. hiding domain priorities) because the **data** simply is not produced out of scope.
- **Touchpoints**: [`shared/service/audit_orchestration.py`](shared/service/audit_orchestration.py) (Tier 3 sequencing), [`tests/run_test_coverage.py`](tests/run_test_coverage.py) (`CoverageMetricsRegenerator`, CLI), Tier 3 outcome/cache contracts, paired guides §10 / Standard Audit Recipe.
- **Acceptance**: After `--dev-tools-only` full audit, project-wide coverage files and `AI_STATUS` coverage lines either **omit** “last full-repo run” or **mark stale** per documented rules; after normal `--full`, dev-tools-only artifacts behave symmetrically. Tests under `tests/development_tools/` cover branching; `audit --quick` still passes.
- **Related**: **§7.15** (separate coverage from full audit — product direction); **§5.2 — 2.8** (report scope; metadata/priorities partial **2026-03-28**, orchestration here).

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
  - **Orchestration**: Tier 3 **coverage/test runs** should follow audit scope (**§5.1 — 1.9**) so metrics are not mixed or stale across scopes; reduces need for report-only filtering.
  - Any remaining **sections** in `DEV_TOOLS_STATUS` / `DEV_TOOLS_CONSOLIDATED_REPORT` that still read as full-repo after 1.9 — trim or label explicitly once data pipeline is scoped.

#### 2.9 Console output polish (optional)

- **Status**: **IN PROGRESS** — spot-check done; **progress indicators** (spinners/TUI) still **TBD**. Tier/tool logging and stdout discipline reviewed 2026-03-26 per V4.

---

### 5.3 Section 3 — Tooling integrity and validation

#### 3.0 Example marking standards checker (doc-sync validation)

- **Status**: **PENDING**. **User priority**: Low.
- **Open tasks**:
  - Add validation to `development_tools/docs/analyze_documentation_sync.py` or a **new** validation module.
  - Detect file path references in example contexts missing `[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]` markers.
  - Validate example headings (`Examples:`, `Example Usage:`, `Example Code:`).
  - Report unmarked examples with file/line detail.
  - Integrate into `doc-sync` workflow and document the new check.

#### 3.2 Validation warnings cleanup (residual)

- **Open** (low priority):
  - Review `needs_enhancement` and `new_module` triggers.
  - Decide if **test files** should be excluded from these checks.

#### 3.3 Version sync functionality

- **Status**: **IN PROGRESS** in V4; substantive discovery/docs done. **Open**: ongoing maintenance if `fix_version_sync.py` / `run_version_sync` behavior drifts; experimental tier — see paired guides §2.

#### 3.12 Integrate flaky detector into development tools suite

- **Status**: **PENDING**. **User priority**: Medium/low.
- **Context (V4)**: Backlog pointer in paired guides §10; `scripts/flaky_detector.py` may be **absent** from tree — restore from git history before move if needed; see [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md) §3.2.
- **Open tasks**:
  - Move `scripts/flaky_detector.py` to `development_tools/tests/` with clear ownership and module boundaries.
  - Wire flaky detection into dev-tools CLI + tool metadata (standalone command + optional audit hook).
  - Standardize logs/outputs (`development_tools/tests/logs` + JSON/markdown schema).
  - Add tests: runtime metrics, timeout behavior, worker-log consolidation on interrupted runs.
  - Update [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md), [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md), test workflow docs.

#### 3.13 Scripts-to-development-tools migration (persistent scripts)

- **Status**: **PENDING**. **User priority**: Continue.
- **Open tasks**:
  - Build a **definitive migration inventory** from current tracked references to `scripts/` (exclude changelog-history-only references).
  - **Decision**: Move `scripts/testing/verify_process_cleanup.py` to `development_tools/tests/` **only if** kept as a maintained diagnostic; else retire and remove doc references.
  - Add/adjust tests for migrated scripts where behavior is non-trivial (argument parsing, output paths, failure codes).
  - Remove stale `scripts/` references from **active** docs after migration completes.
  - Track project-specific script ownership in `TODO.md` (not in this plan).
  - **Do not duplicate**: flaky detector stays under §3.12; memory profiler under §5.6.

#### 3.14 Scripts review candidates (evaluate before retire/migrate)

- **Status**: **PENDING**. **User priority**: Systematic review.
- **Open**: Review each path for durable value vs retirement:
  - `scripts/utilities/cleanup/cleanup_test_data.py`
  - `scripts/utilities/cleanup/cleanup_user_message_files.py`
  - `scripts/cleanup_project.py` vs `development_tools/shared/fix_project_cleanup.py`
  - AI/manual smoke: `scripts/testing/ai/script_test_ai_with_clear_cache.py`, `script_test_comprehensive_ai.py`, `script_test_data_integrity.py`, `script_test_lm_studio.py`, `scripts/testing/script_test_user_data_analysis.py`
  - Worker/memory diagnostics: `scripts/testing/parse_worker_from_terminal.py`, `extract_worker_test_assignments.py`, `extract_worker_tests_from_profiler_output.py`, `cross_reference_worker_runs.py`, `debug_memory_leak.py`, `investigate_memory_leak.py`, `analyze_memory_leak.py`, `cleanup_old_test_dirs.py`
  - `scripts/testing/validate_config.py` — runtime/admin vs retire
  - Ad-hoc: `scripts/debug/*.py`, `scripts/demo_dynamic_checkin.py`

#### 3.15 Gap tasks from retired scripts (development-tools scope)

- **Status**: **PENDING**. **User priority**: Low.
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

---

### 5.4 Section 4 — External tool evaluation

#### 4.1 Evaluate and integrate complementary tools

- **Status**: **IN PROGRESS**. **User priority**: Evaluate bandit, pip-audit, radon, pre-commit; ruff already in use for lint.
- **Done (V4)**: Evaluation stance + backlog pointer in paired guides §10.
- **Open tasks**:
  - Evaluate **ruff** (lint/format) and **radon** (complexity) for deeper integration.
  - Evaluate **pydeps** for dependency graphs vs existing dependency tooling.
  - Run **bandit** security scan; decide Tier 1 integration.
  - Run **pip-audit**; decide Tier 1 integration.
  - Decide: replace, complement, or keep existing tools.
  - If integrating: wrappers, `requirements.txt`, docs.
  - Optional: **vulture** (dead code), **pre-commit** (hooks).

---

### 5.5 Section 5 — Future enhancements

#### 5.1 Unused imports cleanup module

- **Status**: **PENDING**. **User priority**: Low.
- **Open**:
  - **Investigate all-zero report output**: [UNUSED_IMPORTS_REPORT.md](../development_docs/UNUSED_IMPORTS_REPORT.md) often shows **0** files with unused imports and **0** in every breakdown category while **Total Files Scanned** is large (hundreds). That is **unlikely to be correct** for a repo this size. Trace the pipeline (`development_tools/imports/analyze_unused_imports.py`, report generator, Ruff/pylint backend, JSON aggregation) to confirm findings are passed through, categorization buckets are filled, and nothing discards real hits; add a **regression test or small fixture** with a known unused import if the tool is behaving as designed.
  - Categorization logic; category-based reporting; implement `imports/fix_unused_imports.py`; cleanup recommendations; optional `--categorize` flag.

#### 5.2 Documentation overlap analysis enhancements

- **Status**: **PENDING**. **User priority**: Medium.
- **Open**: Review consolidation opportunities (Development Workflow, Testing); consolidation plan; improve actionable insights; reduce false positives.

#### 5.3 AI work validation improvements

- **Status**: **IN PROGRESS**. **User priority**: High/medium (value uncertain).
- **Open**: Avoid overlap with domain-specific analyzers — keep tool **thin** (ongoing).

#### 5.4 TODO sync cleanup automation

- **Status**: **PENDING**. **User priority**: Low.
- **Open**: Auto-clean with **dry-run** option; document workflow and best practices (V4 already improved detection + manual vs auto-cleanable reporting).

#### 5.5 New tool creation based on gap analysis

- **Status**: **IN PROGRESS**. **Effort**: Large.
- **Done (V4)**: `module-refactor-candidates` tool and Tier 2 integration.
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
  - **Partial (V4)**: `tests/development_tools/test_pyright_config_paths.py` — Pyright JSON smoke, root JSONC markers; owned + root `ruff.toml` parse; owned `pyrightconfig.json` has `typeCheckingMode` + non-empty `exclude`.
- **Dual-config situation (V4 2026-03-02)**:
  - Root `pyrightconfig.json` = whole-repo IDE/direct baseline; `development_tools/config/pyrightconfig.json` = dev-tools-owned (diagnostics not yet fully comparable).
  - Root `.ruff.toml` = compatibility mirror; `development_tools/config/ruff.toml` = owned path for wrappers.
- **Next steps before single baseline**:
  - Align dev-tools Pyright so `analyze_pyright` matches root diagnostic baseline (no artificial drops from scope drift).
  - Regression tests: both Pyright paths; fail if error/warning deltas exceed agreed tolerance without explicit exclusions. **Partial (2026-03-27)**: optional enforcement in `tests/development_tools/test_pyright_config_paths.py` e2e — set env `PYRIGHT_ERROR_COUNT_MAX_DELTA` to a non-negative integer when running the e2e Pyright test; unset by default (scopes differ). **2026-03-28**: owned [`pyrightconfig.json`](config/pyrightconfig.json) adds `venvPath` / `venv` so `pyright --project` resolves the repo `.venv` from the owned config path.
  - Decide: keep root `.ruff.toml` permanently as mirror vs deprecate after portability criteria met.
  - If deprecating root configs: migration + fallback documented in both guides before removal.

#### 7.7 Directory taxonomy and config boundary cleanup (residual)

- **Done (V4)**: Phase 1 taxonomy docs, configuration surface table (guides §9), phased plan outline.
- **Phase 2–3 evaluation (2026-03-27)**: No directory moves or new packages this session. **Decision**: keep `development_tools/config/` as the single config surface for JSON/TOML/Pyright entrypoints; `development_tools/shared/` remains shared runtime (locks, orchestration, exclusions). Before any `runtime_config/` split: prototype a short ADR (or changelog note) listing **which** files would move, **import** re-exports for one deprecation window, and **rollback** steps. **Gate**: `python development_tools/run_development_tools.py audit --quick` still passes with no new import-boundary violations (`analyze_dev_tools_import_boundaries`).
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

---

### 5.8 Monitoring and deferred test work (no active V4 tasks)

- **§1.3** — Intermittent low coverage: **MONITORING**; reopen on recurrence.
- **§1.2** — `test_audit_tier_comprehensive.py`: **deferred** unless cost/benefit justifies re-enable.

**Lower backlog (opportunistic, 2026-03-28)** — pick up when touching related code: §1.1 adopt `test_config.json` in analyzer tests you edit; §1.9 orchestration when refactoring Tier 3; §3.0 example-marking in doc-sync; §3.12 restore `flaky_detector` from history if needed then migrate; §3.13–3.14 scripts inventory; §3.15 gap heuristics; §3.16 extract helpers from `report_generation.py` / `run_test_coverage.py`; §7.8–7.13, §7.15 as separately prioritized.

---

## 6. Related documents

- [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) — full V4 checklist history  
- [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md) / [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md)  
- [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)  
- [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) (Standard Audit Recipe §10)  
- [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md)  
- [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md) — scripts backlog and flaky detector notes  
- [LIST_OF_LISTS.md](../development_docs/LIST_OF_LISTS.md) — canonical list principles (relevant to §7.8)  
