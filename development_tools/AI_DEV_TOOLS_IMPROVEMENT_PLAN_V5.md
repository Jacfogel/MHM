# AI Development Tools — Improvement Roadmap (V5)

> **File**: `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md`  
> **Audience**: Project maintainers and developers  
> **Purpose**: Single forward-looking backlog after V4; collapsed history; actionable next steps  
> **Style**: Direct and concise  
> **Last Updated**: 2026-04-23  
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

**2026-04-23 (V5 continuation — Phase A/B from attached execution plan)**: Phase **§5.1 — 1.1**: added [`test_commands_coverage_helpers.py`](../tests/development_tools/test_commands_coverage_helpers.py) cases for `_derive_tier3_state_from_classifications`, `_is_failure_state`, `_is_coverage_file_fresh` stat failure; [`test_analyze_unconverted_links.py`](../tests/development_tools/test_analyze_unconverted_links.py) for skip-outside-root, metadata line, `*.md`→`*.c` sibling, Example Code heading context. **§5.5 — 5.2**: [`EXPECTED_OVERLAPS`](shared/constants.py) **troubleshooting**, **additional resources** + [`test_analyze_documentation.py`](../tests/development_tools/test_analyze_documentation.py) numbered troubleshooting overlap regression. **§5.5 — 5.7**: [`analyze_test_markers.py`](tests/analyze_test_markers.py) — `domain_attribution_summary` / JSON `details.domain_attribution_summary` + [`test_analyze_test_markers_domain.py`](../tests/development_tools/test_analyze_test_markers_domain.py); `_FakeAnalyzer` in [`test_analyze_test_markers.py`](../tests/development_tools/test_analyze_test_markers.py). **§5.7 — 7.6**: [`test_pyright_config_paths.py`](../tests/development_tools/test_pyright_config_paths.py) `include` key parity. **§5.3 — 3.0**: example-marker advisory unchanged (clean); existing changelog/heading tests retained. **Evidence**: `pytest tests/development_tools -m "not e2e"`; `audit --full` post-change. **Next**: resume §4.3 only if new priorities emerge from fresh **AI_PRIORITIES**; optional product work §6 separate.

**2026-04-21 (V5 continuation — coverage tests, Section 3.21 closeout)**: Added unit tests for [`shared/measure_tool_timings.py`](shared/measure_tool_timings.py) and [`shared/verify_tool_storage.py`](shared/verify_tool_storage.py) (`tests/development_tools/test_measure_tool_timings.py`, `tests/development_tools/test_verify_tool_storage.py`). **Section 3.21** documented: log `issues=` mirrors `data.summary.total_issues` (see [`audit_orchestration._extract_issue_count`](shared/service/audit_orchestration.py)); paired notes in [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) Section 3 and [HOW_TO_RUN.md](../HOW_TO_RUN.md) Section 5.1.6. **Section 4.3** lists the next **medium backlog** execution order after this slice. Refresh **AI_STATUS** / **AI_PRIORITIES** after your next `audit --full` for live percentages.

**2026-04-20 (V5 continuation — static-check sharding, cache roadmap, §3.21 backlog)**: **Phase 2** landed: config-gated **sharded Ruff/Bandit** (merged JSON per `STATIC_ANALYSIS`); static-check **disk cache** still uses a **single whole-repo** `_compute_source_signature` — **directory-scoped** reuse is **§3.19.2** / backlog **7** (not implemented). Plan updates: **§3.19.1** distinguishes sharded **execution** from global cache keys; **§3.19.2** outlines per-shard caching steps; **§3.21** (**open**) tasks tracing large log `issues=` counts for `analyze_documentation` / `analyze_functions` / `analyze_package_exports` / `analyze_function_registry` vs **AI_PRIORITIES** / **AI_STATUS** / **CONSOLIDATED_REPORT**. Supporting work: shared **`STATIC_CHECK_CONFIG_RELATIVE_PATHS`** / pip-audit requirements-lock alignment, [`HOW_TO_RUN.md`](../HOW_TO_RUN.md) cache invalidation notes, expanded tests (`test_tool_wrappers_cache_helpers`, `test_tool_cache_inventory_policy`, `test_tool_wrappers_static_analysis`). Latest authoritative numbers: see **AI_STATUS.md** **Last Generated** (example snapshot: overall test coverage **70.5%**, development-tools coverage **63.6%**, static analysis **CLEAN**, documentation signals **CLEAN** including ASCII compliance).

**2026-04-17 (V5 continuation — post implementation + rebaseline audit)**: After targeted test additions in central service/wrapper paths (`tests/development_tools/test_commands_additional_helpers.py`, `tests/development_tools/test_tool_wrappers_static_analysis.py`) and a fresh `audit --full`, generated outputs were refreshed at **03:28**. Current evidence shows overall coverage **70.9%**, development-tools coverage **63.9%**, duplicate groups **9 across 7 files**, high-coupling modules **51**, static analysis **CLEAN**, legacy references **CLEAN (0 files)**, and documentation signals **CLEAN** with no doc-fix quick wins. Tier 3 state remains **clean** with subtrack rows `unknown/cache_only_precheck` for this pass.

**2026-04-16 (V5 continuation — post implementation/full audit refresh)**: After targeted tests for `shared/service/commands.py`, `shared/service/audit_orchestration.py`, and related report/data-loading paths, a fresh `audit --full` regenerated **AI_STATUS**, **AI_PRIORITIES**, and **CONSOLIDATED_REPORT**. Current evidence: overall coverage **69.9%**, development-tools coverage **63.4%**, duplicate-function groups **9 across 7 files**, Tier 3 test outcome **clean**, static analysis **CLEAN**, and legacy references **CLEAN (0 files)**. The earlier **full-vs-dev-tools-only coverage wording mismatch is resolved** in generated outputs, and the duplicate-groups priority now agrees with status/report file counts. The only live doc-sync issue remains **ASCII compliance: 1 issue in `TODO.md`**.

**2026-04-16 (V5 continuation — post full audit reconciliation)**: Fresh `audit --full` regenerated **AI_STATUS**, **AI_PRIORITIES**, and **CONSOLIDATED_REPORT**. Current evidence: static analysis **CLEAN**, legacy references **CLEAN (0 files)**, backup health **PASS**, config validation **CLEAN**, duplicate-function groups **9**, high-coupling modules **51**, overall coverage **69.9%**, and development-tools coverage **62.1%** in the detailed coverage report. Active plan focus now shifts away from already-landed audit infrastructure toward **targeted dev-tools coverage improvements**, **report-semantic clarity for full vs dev-tools-only coverage rows**, and a **small set of medium-priority backlog items** (example-marker follow-up only if the clean advisory result proves misleading, documentation-overlap tuning, portability parity follow-up). The only live doc-sync issue in the generated status is **ASCII compliance: 1 issue in `TODO.md`**.

**2026-04-15 (V5 plan execution — §4.3 pip-audit timing, §7.21 matrix, §3.19 cache inventory, §3.20 priorities, §3.0 changelog example-marker skip, §5.7 domain markers config)**: `pip_audit_execution_state` / subprocess seconds in JSON and logs; checked-in `config/audit_tool_matrix.json` + `config/tool_cache_inventory.json` with policy tests; `add_priority` defaults retarget dev-tools guides (paired §9.1); example-marker scan skips `*CHANGELOG*.md`; optional `test_markers.domain_markers` drives advisory `missing_domain` in `analyze_test_markers` JSON; see changelogs 2026-04-15.

Use **AI_STATUS.md** after each audit and prefer the latest generated values over any examples embedded here. As of **2026-04-20** (**Last Generated** on **AI_STATUS.md**): overall test coverage **70.5%**; development-tools coverage **63.6%**; static analysis **CLEAN**; legacy references **CLEAN (0 files)**; duplicate-function groups and high-coupling counts — see live **AI_STATUS** / **AI_PRIORITIES**; documentation signals **CLEAN** (including ASCII compliance). Refresh **AI_PRIORITIES** / **CONSOLIDATED_REPORT** before choosing follow-up work in §5–§6.

**2026-04-14 (V5 plan continuation — §2.8 copy, §4.1 Radon, §5.2 overlaps, §7.6 notes)**: **AI_STATUS** / **CONSOLIDATED_REPORT** Test Coverage lines now say **Skipped** with explicit reason (`--dev-tools-only` vs full-repo Tier 3 omitting dev-tools track) and the matching refresh command; [HOW_TO_RUN.md](../HOW_TO_RUN.md) §5.1 documents Tier 3 freshness (`--clear-cache`, `audit --full --dev-tools-only`). **EXPECTED_OVERLAPS** adds generic headings (`known limitations`, `scope`, `related reading`). Paired guides §10: Radon pilot alignment with V5 §4.1 (manual vs `analyze_functions`). **test_pyright_config_paths.py** docstring: update both Pyright configs when adding shared keys. Baseline: `audit --full --dev-tools-only` to refresh DEV_TOOLS_* artifacts when needed.

**2026-04-08 (this plan iteration)**: §2.8 scoped-report copy in `DEV_TOOLS_*` (snapshot coverage vs full-repo staleness, scope notes, consolidated reference links); overlap analyzer filters numbered generic headings; §4.1 external-tool stance recorded in paired guides §10; §1.5 benchmark recipe noted in paired changelogs (numeric wall-clock still machine-local).

**2026-04-09**: Legacy scan now clean after removing a false-positive "legacy paths" phrase from `fix_project_cleanup.py`; documentation-overlap noise reduced by adding `prerequisites` and `test suite structure` to `EXPECTED_OVERLAPS` so shared test-guide boilerplate is not flagged.

**2026-04-09 (scripts backlog execution slice)**: migrated local script utilities into tracked dev-tools paths: `scripts/flaky_detector.py` -> `development_tools/tests/flaky_detector.py` and `scripts/testing/verify_process_cleanup.py` -> `development_tools/tests/verify_process_cleanup.py`; added CLI commands (`flaky-detector`, `verify-process-cleanup`), command docs updates, and unit tests. `development_tools/shared/fix_project_cleanup.py` remains canonical cleanup implementation for the `cleanup_project` overlap.

**2026-04-09 (V5 plan continuation — tooling slice)**: `verify_process_cleanup` uses **Get-CimInstance Win32_Process** on Windows for real `CommandLine` (Section 3.18); `sync-todo --dry-run` prints the dry-run report; `EXPECTED_OVERLAPS` extended (generic doc headings); guides Section 10 record **2026-04-09** external-tool decisions + Section 10.1 gap-analysis alignment; policy tests for Phase 2 taxonomy gate and Pyright delta env documentation. **Section 1.5** numeric cache benchmark still deferred (recipe unchanged; machine-local).

**2026-04-10 (V5 §4.2)**: **Bandit** + **pip-audit** integrated into Tier 3 static-analysis group; `requirements.txt`; coverage subprocess KeyboardInterrupt logs demoted to **WARNING** for cleaner `logs/errors.log`; `EXPECTED_OVERLAPS` + `external tools`.

**2026-04-11 (V5 continuation — plan slice)**: Reconciled **§4.1** vs **§4.2** (Tier 3 Bandit/pip-audit complete; remaining §4.1 = Radon/pydeps/pre-commit/vulture/ruff depth + pip-audit CI residual). **§7.6**: policy test asserts owned [`pyrightconfig.json`](config/pyrightconfig.json) matches root [`pyproject.toml`](../pyproject.toml) `[tool.pyright]` for shared diagnostic/exclude keys. **pip-audit**: `MHM_PIP_AUDIT_SKIP` env skips subprocess (offline/CI); guides + [`config.py`](config/config.py) comment. **§5.6**: `test_deprecation_inventory_policy.py` structural check for `root_ruff_compat_mirror`. Targeted tests: pip-audit skip, `_coverage_path_to_rel_posix` outside-project absolute path → `None`, flaky_detector empty inputs.

**2026-04-12 (V5 plan continuation)**: Fresh **`audit --full --clear-cache`** run for live Tier 3 pytest metrics. **§1.5** numeric domain-cache benchmark still deferred (recipe unchanged). **§3.0** initial `example_marker_validation` + `--check-example-markers` on [`analyze_documentation_sync.py`](docs/analyze_documentation_sync.py) (advisory). **`sync_todo_with_changelog(apply_auto_clean=True)`** + CLI **`sync-todo --apply`** removes auto-cleanable `- [x]` lines; mutually exclusive with `--dry-run`. **§5.2** [`EXPECTED_OVERLAPS`](shared/constants.py) extended (`development workflow`, `testing guide`). **§1.1** additional demo-project tests pass [`test_config.json`](../tests/development_tools/test_config.json). **§7.7** policy test asserts [`DEVELOPMENT_TOOLS_GUIDE.md`](DEVELOPMENT_TOOLS_GUIDE.md) §9 references Phase 2 / V5; **`root_ruff_compat_mirror`** exit criteria string enforced in inventory policy test. **`analyze_ai_work`**: docstring reminds thin scope (§5.3).

**2026-04-13 (V5 continuation — audit observability + marker recalibration backlog)**: Added scoped backlog tasks for cache inventory/expansion, pip-audit elapsed-time diagnosis, domain-marker validation in `analyze_test_markers`, and audit-tier participation/report-inclusion matrix; at that point the example-marker advisory still showed high-volume changelog/guide noise after broad heading matching rollback. Treat that observation as **historical context only** until revalidated against the newer clean paired-doc scan noted on **2026-04-16**.

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

Current ordering after the latest **2026-04-17** full audit refresh (see **§5** for detail):

| Tier | Themes |
|------|--------|
| **Next execution slice** | Dev-tools coverage improvement work centered on low-coverage tooling modules (§5.1 — 1.1); short audit-reconciliation updates whenever fresh full-audit evidence changes priorities; then resume the medium backlog now that the report/status semantic clarity slice has landed (§5.1 — 1.9, §5.2 — 2.8). |
| **Active medium backlog** | Example-marker calibration before any stricter rollout (§5.3 — 3.0); documentation-overlap tuning / consolidation follow-up (§5.5 — 5.2); portability follow-up around Pyright/Ruff parity and minimal-external-repo validation (§5.3 — 3.17, §5.7 — 7.6); narrow validation-trigger cleanup only if it becomes noisy (§5.3 — 3.2). |
| **Deferred / optional** | Coverage cache numeric benchmarks (§5.1 — 1.5); external-tool expansion beyond shipped Bandit/pip-audit integration (§5.4 — 4.1); TODO sync workflow polish (§5.5 — 5.4); gap-analysis expansion (§5.5 — 5.5); memory profiler (§5.5 — 5.6); large-file refactor work (§5.3 — 3.16); broader human backlog (§5.7 — 7.7 onward). |
| **Monitoring only** | Intermittent low coverage warning (§1.3); deferred comprehensive audit-status tests (§1.2); legacy inventory follow-up only if future audits reintroduce active markers or new bridge-removal work (§6). |

### 4.1 Next execution slice (recommended)

Suggested order for the next work slice after the 2026-04-17 continuation slice:

1. Use **`TEST_COVERAGE_REPORT.md`** / dev-tools coverage artifacts to choose the next small set of low-coverage tooling modules for targeted tests, balancing central service chokepoints with the current lowest modules surfaced by the latest report (`shared/measure_tool_timings.py`, `shared/verify_tool_storage.py`, and remaining gaps in `shared/service/*`).
2. Rerun full-audit validation and refresh **AI_STATUS** / **AI_PRIORITIES** / **CONSOLIDATED_REPORT** so coverage movement and ranking shifts are captured before starting the next backlog theme.
3. Resume medium-priority tooling work in order: documentation-overlap tuning, then portability parity validation; keep doc-sync work in monitor mode unless generated signals regress from **CLEAN**.

### 4.3 Medium backlog queue (scheduled order after 2026-04-21 slice)

Execute when **§5.1 — 1.1** coverage iterations and **§3.21** operator clarity are satisfied for the current milestone:

1. **§5.5 — 5.2** — Documentation overlap tuning (`EXPECTED_OVERLAPS`, `detect_section_overlaps`); validate with a default-scope `doc-sync` / audit pass before expanding patterns.
2. **§5.3 — 3.0** — Example-marker advisory: revalidate scan scope vs “clean” output; tighten heuristics only if audits show false negatives or churn.
3. **§5.7 — 7.6** — Pyright portability / dual-config alignment; extend `test_pyright_config_paths.py` when tightening diagnostic parity.
4. **§5.7 — 5.7** — Domain markers in `analyze_test_markers` (coordinate with [TEST_PLAN.md](../development_docs/TEST_PLAN.md) §4.4 and `domain_mapper`).

### 4.2 Deferred after the next slice

Once the coverage/semantics slice is complete, revisit this order:

1. §1.5 coverage-cache benchmark session (methodology in §5.1 — 1.5; optional numeric capture).
2. §4.1 remaining external-tool evaluation (Radon, pydeps, pre-commit, vulture, deeper Ruff usage). **Bandit + pip-audit Tier 3 integration are already complete** (§5.4 — 4.2).
3. §5.4 TODO sync workflow polish.
4. §5.5 gap-analysis rollout.
5. §7.7 onward broader structure / human backlog items when they become active priorities.

---

## 5. Outstanding work — full detail (every open item from V4)

Each block mirrors **AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md** section numbering. Completed V4 checkboxes are omitted; use V4 for historical `[x]` audit trail.

**V4 sections with no remaining open tasks** (fully complete in V4; not expanded below): **1.4**, **1.6**, **1.7**; **2.1**, **2.3**, **2.6–2.7**, **2.9** (Tier 3 audit failure / exit semantics — completed follow-ups), **2.10–2.11**; **3.1**, **3.4–3.11**, **3.11.1**; **5.0**, **5.1.1**; **7.1–7.5**, **7.14**. **§7.16** read-fallback removal completed in V5 (2026-04-06). **§1.7** also noted optional future caching for tools still uncached — discovery done; not a gated backlog item.

### 5.1 Section 1 — Reliability, coverage, and test health

#### 1.1 Raise development tools coverage beyond the current floor

- **Status update (2026-04-17 rebaseline)**: The old V4 threshold is no longer the useful target. Latest generated reports show development-tools coverage at **~63.9%** in the dedicated track after this slice, so the active question is still **where targeted tests buy down the most risk next**, not whether the suite can clear 60%.
- **Next focus**: Prefer coverage work on low-coverage modules surfaced in `TEST_COVERAGE_REPORT.md`, balancing central orchestration paths (`development_tools/shared/service/commands.py`, `development_tools/shared/service/audit_orchestration.py`, `development_tools/shared/service/tool_wrappers.py`, optional follow-on `development_tools/shared/service/data_loading.py`) with currently lowest helper/tooling modules (`development_tools/shared/measure_tool_timings.py`, `development_tools/shared/verify_tool_storage.py`).
- **Open**: Migrate remaining analyzer-style tests to `tests/development_tools/test_config.json` via `test_config_path` when touching those tests; keep this as opportunistic cleanup, not the headline coverage strategy.
- **Guidance**: Use live `AI_PRIORITIES.md`, `TEST_COVERAGE_REPORT.md`, and `generate_dev_tools_coverage_results.json` to pick modules; do not duplicate long module lists in this plan.

#### 1.2 Restore audit status tests (residual)

- **Open**: Re-enable `tests/development_tools/test_audit_tier_comprehensive.py` **only if** a narrow mocked subset is worth the maintenance cost (**deferred**). Replacement lightweight tests already landed per V4.

#### 1.3 Investigate intermittent low coverage warning

- **Status**: **MONITORING** (fixes landed in V4). Reopen if `generate_dev_tools_coverage_results.json` or audit shows suspicious low %; compare `run_test_coverage.py` with `--no-parallel` and shard merge logs.

#### 1.5 Coverage caching follow-ups (test-file cache)

- **Status**: **IN PROGRESS** (core behavior done in V4).
- **Open**:
  - Compare **full** vs **domain-filtered** runs and document **numeric** results in changelog — defer until a dedicated benchmark session captures stable numbers (machine-dependent).
  - **Methodology (V4)**: On Windows PowerShell, `Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }` vs the same **without** `--no-domain-cache` after a warm cache; compare wall-clock and logs for hit/miss. Paired changelog may reference the recipe without numbers until benchmarks exist. **2026-04-06**: The same style of comparison applies to unified full-repo runs (`python development_tools/run_development_tools.py audit --full` with vs without `--no-domain-cache` / `--clear-cache` as appropriate) when capturing domain-cache ROI after §1.9; numbers remain machine-specific. **2026-04-14**: [HOW_TO_RUN.md](../HOW_TO_RUN.md) §5.1 cross-links stale Tier 3 rows to `--clear-cache` and documents `audit --full --dev-tools-only` for DEV_TOOLS-only refresh (operational complement to numeric benchmarks).

#### 1.8 Improve slow development tools tests (residual)

- **Deferred (no batch change)**: Consider `scope="module"` for `temp_project_copy` where tests do not mutate shared state — **2026-03-24 V4**: shared-state risk; prefer **per-test review** when touching slow tests.
- **Note**: Concurrent worker fallback 4→6 and `@pytest.mark.slow` on heavy tests were completed; full-suite timing remains environment-dependent.

#### 1.9 Tier 3 coverage and test execution by audit scope (orchestration)

- **Status**: **COMPLETE — unified full-repo run (2026-04-06)**. Tier 3 schedules one heavy coverage subprocess per scope ([`shared/audit_tiers.py`](shared/audit_tiers.py) `get_tier3_groups`): full-repo runs **`run_test_coverage` only**; `--dev-tools-only` runs **`generate_dev_tools_coverage` only**. **Unified metrics (Option A / §7.17):** main `run_test_coverage` now **includes** `tests/development_tools/`, measures the **`development_tools`** package ([`tests/coverage.ini`](tests/coverage.ini); `development_tools` removed from `constants.derived_prefix_excludes.core` in project config), derives **`coverage_dev_tools.json`** from main **`coverage.json`**, persists **`generate_dev_tools_coverage`** after a successful full-repo run, and emits **`dev_tools_test_outcome`** for Tier 3; [`audit_orchestration._finalize_tier3_audit_scope`](shared/service/audit_orchestration.py) keeps dev-tools outcomes when present instead of always injecting “skipped this pass.”
- **Goals** (current behavior):
  - **`audit --full`** — single pytest+coverage pass for product **and** dev-tools tests; **Development Tools Coverage** in `AI_STATUS` refreshes with full-repo coverage.
  - **`audit --full --dev-tools-only`** — only dev-tools coverage/artifacts; main-repo coverage line documents staleness (unchanged).
- **Touchpoints**: [`shared/service/commands.py`](shared/service/commands.py) (`run_coverage_regeneration`), [`tests/run_test_coverage.py`](tests/run_test_coverage.py), [`config/development_tools_config.json`](config/development_tools_config.json).
- **2026-04-16 refresh**: The report-semantic clarity follow-up is **landed**. Generated outputs now present full-repo and development-tools coverage without the earlier contradictory **Skipped** wording in the full-audit path.
- **Related**: **§7.15** (optional: coverage outside audit); **§5.2 — 2.8** (report copy vs data).

---

### 5.2 Section 2 — Reporting, recommendations, and output quality

#### 2.2 Standardize logging and surface top offenders

- **Status**: V4 marked **IN PROGRESS** but checklist nearly complete. **Residual**: opportunistic scan for stray `print(` in rarely run standalone paths; treat as **maintenance**, not a tracked gate.

#### 2.5 System signals purpose and redundancy cleanup

- **Status**: **IN PROGRESS (keep + clarify)** — V4 decision (2026-03-24): keep tool; clarify scope in reports + `reports/analyze_system_signals.py`.
- **Open**: **2026-03-26 V4**: Optional further trim/merge with doc-sync overlap — **deferred** unless duplicate metrics appear in a future audit.

#### 2.8 Run all tools in development_tools-only mode

- **Status**: **SUBSTANTIVELY COMPLETE (2026-04-16 refresh)**. Implemented: `audit --dev-tools-only`, `DEV_TOOLS_*` output paths, `get_scan_directories() -> ['development_tools']`, report-layer scope, Tier 3 scope split (§1.9), and the wording cleanup so full-audit outputs no longer contradict the separate dev-tools-only refresh path.
- **Open**:
  - Reopen only if future generated sections reintroduce scoped/full-repo ambiguity or contradictory stale/refresh wording.

#### 2.9 Console output polish (optional)

- **Status**: **IN PROGRESS** — spot-check done; **progress indicators** (spinners/TUI) still **TBD**. Tier/tool logging and stdout discipline reviewed 2026-03-26 per V4.

---

### 5.3 Section 3 — Tooling integrity and validation

#### 3.0 Example marking standards checker (doc-sync validation)

- **Status**: **PARTIAL (2026-04-17)** — advisory scan shipped; currently low-noise/clean in generated output; strict gating / CI failure TBD.
- **Done (2026-04-12)**: [`example_marker_validation.py`](docs/example_marker_validation.py); CLI flag `--check-example-markers` on [`analyze_documentation_sync.py`](docs/analyze_documentation_sync.py); unit tests [`test_example_marker_validation.py`](../tests/development_tools/test_example_marker_validation.py).
- **Done (2026-04-13)**: Example-marker scan targets **`DEFAULT_DOCS`** from [`constants.py`](shared/constants.py) (merged config via [`get_constants_config()`](config/config.py): `paired_docs` + [`fix_version_sync` `ai_docs` / `docs`](../config/development_tools_config.json) + `default_docs_extra`), not only paired-doc endpoints — keeps the pass aligned with the approved documentation path list. Fallback if that set is empty: paired-doc keys only. Tests: [`test_documentation_sync_checker.py`](../tests/development_tools/test_documentation_sync_checker.py) `TestExampleMarkerScanPaths`.
- **Done (2026-04-17)**: Heading matcher expanded to include **Example Code** headings while suppressing changelog-style **example markers** heading noise; regression tests updated in [`test_example_marker_validation.py`](../tests/development_tools/test_example_marker_validation.py).
- **Open tasks**:
  - Tighten heuristics (reduce false positives); optional integration into default `doc-sync` / audit tiers once signal is trusted.
  - Validate example headings (`Examples:`, `Example Usage:`, `Example Code:`) beyond Markdown `##` patterns.
  - Report unmarked examples with file/line detail in consolidated output when promoted from advisory.
  - **Revalidation note (2026-04-16)**: Generated outputs now report **no example-marker hints** in the paired-doc advisory scan. Before doing more calibration work, confirm whether the clean result reflects the intended scan scope or whether an earlier noisy class simply moved out of scope.
    - If the clean result is expected: demote this backlog item behind the coverage/semantics slice and keep only future heading-shape improvements.
    - If the clean result is misleading: resume bounded filters (for example heading-shape allowlists, changelog-aware guardrails, command-reference exclusions) and keep tests covering both desired broad sections and false-positive classes.
    - Acceptance criteria: the advisory remains low-noise on this repo while still flagging intentionally unmarked true examples in the approved scan scope.
- **Priority note (2026-04-16)**: Keep this as one of the few **active medium-priority** tooling items, but below the coverage/coverage-semantic slice.
- **Priority note (2026-04-17)**: Keep this below active coverage slices and overlap/portability follow-ups unless future audits show advisory regressions.

#### 3.19 Caching coverage inventory and expansion (new)

- **Status**: **PARTIAL (2026-04-15)** — inventory artifact and policy test shipped; expansion of additional caches remains opportunistic.
- **Goal**: Build a definitive inventory of which tools currently use caching and where cache keys/invalidation live, then expand caching to high-cost uncached tools where safe.
- **Scope**:
  - Enumerate per-tool cache strategy (mtime cache, signature cache, requirements-hash cache, test-file cache, none), source(s) of invalidation, and artifact locations.
  - Add a report/table artifact (JSON + markdown pointer) so this remains auditable in future audits.
  - Prioritize additions for `analyze_pyright` and `analyze_bandit` (and any other high-latency tools identified).
- **Acceptance criteria**:
  - Inventory generated from code + runtime metadata (not hand-maintained only).
  - Policy tests cover cache invalidation on config/tool/source changes for newly cached tools.
  - Paired guides/documentation updated with cache behavior and troubleshooting notes.

- **Standardized invalidation (config + tool code) — backlog tasks**:
  1. **Done (2026-04-18 — slice 1)**: Include `development_tools/config/development_tools_config.json` in `ToolWrappersMixin._compute_source_signature` so Ruff/Pyright/Bandit static-check JSON invalidates when that file changes without any `.py` edit; regression test in `tests/development_tools/test_tool_wrappers_cache_helpers.py`; inventory invalidation text + [HOW_TO_RUN.md](../HOW_TO_RUN.md) §5.1.5 aligned.
  2. **Done (2026-04-18 — slice 2)**: [`cache_dependency_paths.py`](shared/cache_dependency_paths.py) exports `STATIC_CHECK_CONFIG_RELATIVE_PATHS` and `static_check_config_paths()`; [`tool_wrappers.py`](shared/service/tool_wrappers.py) `_compute_source_signature` and [`test_file_coverage_cache.py`](tests/test_file_coverage_cache.py) `_get_default_tool_paths` share the same tuple (plus coverage-only scripts) so config drift cannot split static-check vs coverage invalidation; optional root [`.ruff.toml`](../.ruff.toml) included when present; policy tests in [`test_cache_dependency_paths.py`](../tests/development_tools/test_cache_dependency_paths.py) + [`test_tool_wrappers_cache_helpers.py`](../tests/development_tools/test_tool_wrappers_cache_helpers.py); inventory + HOW_TO_RUN §5.1.5 point at the module.
  3. **Done (2026-04-18 — slice 3)**: `requirements_lock_signature` / `PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS` in [`cache_dependency_paths.py`](shared/cache_dependency_paths.py); [`tool_wrappers.py`](shared/service/tool_wrappers.py) and [`analyze_pip_audit.py`](static_checks/analyze_pip_audit.py) delegate; inventory invalidation text updated; [`dev_tools_coverage_cache.py`](tests/dev_tools_coverage_cache.py) uses `static_check_config_paths` like test coverage cache; tests in [`test_cache_dependency_paths.py`](../tests/development_tools/test_cache_dependency_paths.py).
  4. **Done (2026-04-18 — Phase 2 execution)**: Merge helpers + [`analyze_ruff.py`](../static_checks/analyze_ruff.py) / [`analyze_bandit.py`](../static_checks/analyze_bandit.py) sharding via `static_analysis.ruff_shard_scan` + `ruff_path_shards` / `bandit_shard_scan` (defaults **on** in `STATIC_ANALYSIS`; disable or empty shards for single subprocess / fallback); tests [`test_sharded_static_analysis.py`](../tests/development_tools/test_sharded_static_analysis.py), [`test_sharded_static_scan_wiring.py`](../tests/development_tools/test_sharded_static_scan_wiring.py). Per-shard **disk** reuse is **item 7** / **§3.19.2** (implemented in analyzers, not coarse wrapper cache). Pyright subset policy unchanged; periodic full pass still mandatory for whole-repo parity (**§3.19.1**).
  5. **Done (2026-04-20)**: See **§3.19.3** — [`analyze_unused_imports`](../imports/analyze_unused_imports.py) documents path-batch + per-root invalidation and surfaces `invalidation_summary` in JSON `details` for audit visibility (paired tests).
  6. **Done (2026-04-20)**: **Domain-scoped test coverage** — documented invalidation branches in [`test_file_coverage_cache.py`](../tests/test_file_coverage_cache.py); `last_invalidation_detail` + `invalidation_counters` on cache load; narrowed **test file set** changes to invalidate only domains implied by added/removed test files (with regression tests). Global bust remains for tool-hash and full-config changes by design.
  7. **Done (2026-04-18 — §3.19.2 shipped in analyzers; reconciled 2026-04-20)**: **Per-shard** signatures and partial disk reuse live in [`static_analysis_shard_cache.py`](shared/static_analysis_shard_cache.py) and [`analyze_ruff.py`](../static_checks/analyze_ruff.py) / [`analyze_bandit.py`](../static_checks/analyze_bandit.py) / [`analyze_pyright.py`](../static_checks/analyze_pyright.py) (not in [`tool_wrappers.py`](shared/service/tool_wrappers.py) early-return). [`run_analyze_*`](shared/service/tool_wrappers.py) invoke scripts via `run_script`; coarse `_try_static_check_cache` / `_save_static_check_cache` were **legacy** and removed. Config digest busts all shards; scoped Python signatures use [`compute_scoped_py_source_signature`](shared/cache_dependency_paths.py). Pyright: sharded runs may omit cross-package diagnostics — periodic full-project run (**§3.19.1**).

**§3.19.1 Sharded static analysis (design note; last reconciled 2026-04-20)**

- **Problem (historical)**: Coarse wrapper-level hashing of the full `*.py` tree would invalidate an entire tool JSON cache on any edit. **`analyze_pip_audit`** uses separate requirements-lock caching — not the static-check shard path.
- **Phase 2 — execution (done)**: Path-scoped subprocesses, then **merge** normalized tool JSON (dedupe; stable ordering). Merge helpers: [`sharded_static_analysis.py`](shared/sharded_static_analysis.py). **Defaults on** (`STATIC_ANALYSIS`): `static_analysis.ruff_shard_scan` + `ruff_path_shards` in [`analyze_ruff.py`](../static_checks/analyze_ruff.py); `static_analysis.bandit_shard_scan` in [`analyze_bandit.py`](../static_checks/analyze_bandit.py) when multiple scan targets exist; Pyright mirrors shards when `pyright_shard_scan` is set. Tests: [`test_sharded_static_analysis.py`](../tests/development_tools/test_sharded_static_analysis.py), [`test_sharded_static_scan_wiring.py`](../tests/development_tools/test_sharded_static_scan_wiring.py).
- **§3.19.2 — disk reuse (done in analyzers)**: Per-shard fragment manifests and scoped Python signatures — see **§3.19.2** below; [`run_analyze_*`](shared/service/tool_wrappers.py) do not short-circuit on a single global signature.
- **Execution vs wall-clock**: Sharding **splits** work per root; subprocesses run **serially**. Benefits are explicit scopes and merge semantics — **not** guaranteed faster wall-clock than one `ruff check .`.
- **Pyright**: Sharded runs may **drop** cross-package diagnostics versus one full-project invocation. Use periodic full Pyright (`pyright_shard_scan: false`, CI, or `--clear-cache` policy) for strict whole-repo parity (**§5.7 — 7.6** portability note).
- **When merged shard output is “enough”**: Merged JSON is authoritative for **paths included in shards/roots** (per tool rules). Use monolithic / wider scopes when policy needs a broader view.

**§3.19.2 Directory-scoped static-check cache (implemented)**

- **Where**: [`static_analysis_shard_cache.py`](shared/static_analysis_shard_cache.py) — versioned manifests `.{tool_name}_shard_cache.v1.json` under the scope `jsons` directory (e.g. `static_checks`). [`analyze_ruff.py`](../static_checks/analyze_ruff.py), [`analyze_bandit.py`](../static_checks/analyze_bandit.py), [`analyze_pyright.py`](../static_checks/analyze_pyright.py) load/save per-shard fragments; [`compute_scoped_py_source_signature`](shared/cache_dependency_paths.py) scopes Python churn; [`static_check_config_digest`](shared/cache_dependency_paths.py) busts **all** shards when any file in `STATIC_CHECK_CONFIG_RELATIVE_PATHS` changes.
- **Distinction**: **Sharded execution** (§3.19.1) and **per-shard disk reuse** (this section) work together: a **miss** runs that shard’s subprocess; **hits** reuse stored fragments; results merge as in §3.19.1.
- **Pyright caveat**: Sharded Pyright fragments are still **subset** views; keep periodic full-project runs for parity (see `parity_note` / `details.shard_run` in analyzer output).
- **Wrapper telemetry**: [`run_analyze_ruff` / `run_analyze_bandit` / `run_analyze_pyright`](shared/service/tool_wrappers.py) map `details.shard_run` into `cache_metadata` for orchestration logs.

**§3.19.3 Other cache-aware tools (expansion)**

- **Unused imports** ([`analyze_unused_imports`](../imports/analyze_unused_imports.py)): Ruff batch paths and per-root content signatures; `details.invalidation_summary` describes scope vs full-tree bust (see module docstring and tests under `tests/development_tools/`).
- Further Tier 2/3 tools: follow [`tool_cache_inventory.json`](config/tool_cache_inventory.json); each tool needs its own invalidation story — do not copy Ruff/Bandit blindly.

**§3.19.4 Test coverage cache invalidation**

- **Implementation**: [`test_file_coverage_cache.py`](tests/test_file_coverage_cache.py) — `get_changed_domains()` documents each branch; payload fields `last_invalidation_detail` and `invalidation_counters` support operator validation; test-file set add/remove narrows domain bust where safe (see docstring **Invalidation matrix**).

#### 3.20 AI_PRIORITIES `add_priority` guidance/details defaults — dev-tools guides (new)

- **Status**: **COMPLETE (2026-04-15)** — defaults retargeted in `report_generation.add_priority`; paired guides §9.1 theme table.
- **Problem**: [`report_generation.py`](shared/service/report_generation.py) `add_priority` uses `guidance_defaults` / `details_defaults` keyed by priority title; many entries still point at **product** AI docs (e.g. `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`) rather than **development-tools-owned** guidance ([`DEVELOPMENT_TOOLS_GUIDE.md`](DEVELOPMENT_TOOLS_GUIDE.md), [`AI_DEVELOPMENT_TOOLS_GUIDE.md`](AI_DEVELOPMENT_TOOLS_GUIDE.md)).
- **Goal**:
  - Audit every `guidance_defaults` / `details_defaults` entry for dev-tools work items; where the actionable procedure lives in the tools suite, retarget bullets to the paired dev-tools guides (and only cite AI\_\* workflow/testing/error docs when the fix is genuinely product-wide).
  - Extend [`DEVELOPMENT_TOOLS_GUIDE.md`](DEVELOPMENT_TOOLS_GUIDE.md) / [`AI_DEVELOPMENT_TOOLS_GUIDE.md`](AI_DEVELOPMENT_TOOLS_GUIDE.md) so they contain the **necessary procedural detail** that was previously only in AI\_\* docs (or add explicit “see also” bridges with enough context to act without opening five files).
  - Prefer **config-relative** or **tool-output** pointers for “details” where that is the source of truth (JSON under `development_tools/**`, generated reports), not hardcoded product paths.
- **Acceptance criteria**:
  - Table or checklist in one of the paired dev-tools guides listing priority themes → primary guide section / JSON artifact (maintained alongside `add_priority` changes).
  - Spot-check: regenerate **AI_PRIORITIES** after `audit` and confirm dev-tools-tier items point readers to dev-tools guides first.
  - Tests unchanged or extended only if stringly defaults move behind a single helper (optional refactor).

#### 3.21 High `issues=` counts vs generated reports — trace and document (new)

- **Status**: **COMPLETE (2026-04-21)** — semantics documented; optional guide notes added.
- **Observation**: [`development_tools/reports/logs/main.log`](reports/logs/main.log) completion lines can show **large `issues=` counts** while the tool still reports **`PASS`** (tool completed successfully). Example from one `audit --full` pass (timestamps omitted): `Completed analyze_documentation: PASS issues=12`; `Completed analyze_functions: PASS issues=493`; `Completed analyze_package_exports: PASS issues=181`; `Completed analyze_function_registry: PASS issues=47`.
- **Orchestration source**: Completion lines use [`audit_orchestration._extract_issue_count`](shared/service/audit_orchestration.py): when present, **`issues=`** is `result["data"]["summary"]["total_issues"]` (integer). **`PASS`/`FAIL`** reflects whether the tool returned `success: true` for that run, not whether `total_issues` is zero.
- **Conclusion — per-tool semantics and report visibility**:

| Tool | What `total_issues` counts | Appears in AI_STATUS / priorities / consolidated? |
|------|---------------------------|---------------------------------------------------|
| **`analyze_documentation`** | Sum of **missing**, **duplicate**, **placeholder**, and **artifact** documentation rows from the doc inventory pass (see [`analyze_documentation.py`](docs/analyze_documentation.py)). | **Yes, indirectly**: overlap / consolidation themes pull from this tool’s JSON via `report_generation` (e.g. documentation overlaps, consolidate docs priorities). The **raw integer** is not always shown verbatim; sections use **derived** lists (e.g. overlap counts, file lists). |
| **`analyze_functions`** | Count of **moderate + high + critical complexity** functions plus **undocumented** functions (see [`analyze_functions.py`](functions/analyze_functions.py) metrics assembly). | **Yes**: primary source for docstring coverage, complexity counts, refactor/complexity priorities, and consolidated detail blocks. Large `issues=` here is **expected** on a big codebase and is already **ranked and summarized** in generated markdown (not “hidden”). |
| **`analyze_package_exports`** | **`total_missing_exports` + `total_unnecessary_exports`** across packages, computed in [`tool_wrappers.run_analyze_package_exports`](shared/service/tool_wrappers.py) (not only the standalone CLI `main()`). | **Yes** when exports need attention: priorities and consolidated can surface package-export work; if counts are low or below thresholds, items may **not** rank in AI_PRIORITIES while the log still shows the **aggregate** row count. |
| **`analyze_function_registry`** | **`missing_count` + `extra_count`** (registry vs inventory alignment). | **Yes**: registry gaps appear in AI_STATUS; priorities reference registry JSON when gaps or complexity warrant. |

- **Operator guidance**: Treat log **`issues=`** as the tool’s **summary metric total**, not as “pytest failures” or orchestration errors. Prefer **AI_PRIORITIES** / **AI_STATUS** / **CONSOLIDATED_REPORT** for **what to do next**; those apply thresholds, top-N lists, and theme wiring. If **`PASS`** with a large `issues=` surprises you, open the tool’s scoped JSON under `development_tools/**/jsons/` and read `summary` + `details` rather than inferring from the single integer alone.
- **Tasks** (closed): (1)–(3) verified 2026-04-21; (4) addressed by this subsection + guide notes (no log format change required).
- **Acceptance criteria**: Met — conclusion table above; see also [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md) Section 3 (completion lines) and [HOW_TO_RUN.md](../HOW_TO_RUN.md) Section 5.1.6.

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

- **Status**: **IN PROGRESS**. **User priority**: Medium after the 2026-04-16 audit.
- **Remaining focus (V4 narrative + inventory)**:
  - Hardcoded-path hotspots: **2026-03-28** slices landed for `run_dev_tools.py` / `legacy/fix_legacy_references.py` (`Path.resolve()` bootstrap), `generate_function_registry.py` output paths (module `project_root`); continue review for `run_development_tools.py`, `config/analyze_config.py`, and any new call sites.
  - Some environments: `audit --full --strict` may hit **runtime limits** — full portability validation still a goal.
  - Import-boundary check exists; keep enforcing isolation of `development_tools/**` from business domains.
  - **2026-04-16 framing**: keep active, but no longer treat portability as the top immediate slice while full-audit health is otherwise stable.

#### 3.18 `verify_process_cleanup` — reliable Windows orphan detection

- **Status**: **COMPLETE (2026-04-09)** — primary path uses **PowerShell Get-CimInstance** `Win32_Process` (full `CommandLine`); **tasklist** CSV retained only as fallback when CIM fails.
- **Problem (resolved)**: Prior `tasklist`-only listing did not expose command lines; pytest/xdist heuristics were unreliable.
- **Goal**: Retrieve `CommandLine` reliably on Windows — **done** via CIM; fallback logs a warning.
- **Reporting**: Tier 3 JSON + STATUS snapshot + consolidated section unchanged; priorities list the item **only when** there are issues.

---

### 5.4 Section 4 — External tool evaluation

#### 4.1 Evaluate and integrate complementary tools

- **Status**: **IN PROGRESS**. **User priority**: Medium/low after Bandit + pip-audit shipped.
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

#### 4.3 Investigate `analyze_pip_audit` elapsed=`0.00s` runs (new)

- **Status**: **COMPLETE (2026-04-15)** — JSON `details` carry `pip_audit_execution_state` and `pip_audit_subprocess_seconds`; requirements-lock cache path injects `requirements_lock_cache_hit`; logs and consolidated static-analysis lines annotate semantics (V5 execution slice).
- **Problem (resolved)**: Near-zero orchestration time on cache hit or env skip was ambiguous vs subprocess duration.
- **Delivered**: Subprocess wall time measured in `analyze_pip_audit.run_pip_audit`; wrapper deep-copy labels cache hits; `CACHE_AWARE_TOOLS` + timing metadata; report suffix helper; tests in `test_analyze_security_static_checks.py`.

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
- **Priority note (2026-04-16)**: Keep active as a **medium-priority** follow-up because the latest full audit still reports overlap/consolidation opportunities, but do it after the coverage/semantics slice.

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

#### 5.7 Expand `analyze_test_markers` for domain-marker requirements (new)

- **Status**: **PENDING (2026-04-13)**.
- **Goal**: Extend test-marker analysis to flag tests that do not include at least one **domain-based marker** (in addition to category markers).
- **Tasks**:
  - Define canonical domain marker taxonomy and config location (project-owned, configurable).
  - **Domain marker analysis in [`development_tools/tests/analyze_test_markers.py`](tests/analyze_test_markers.py)** (2026-04-20): extend reporting so audit/consumers can see domain-attribution coverage explicitly—e.g. which tests/files lack markers that match `domain_mapper` lists, and how that compares to path-only inference—coordinated with the test-suite rollout in [`TEST_PLAN.md`](../development_docs/TEST_PLAN.md) §4.4.
  - Update analyzer to detect missing domain markers per test and summarize by file/module.
  - Decide migration strategy for legacy tests (warn-only phase vs enforced failure threshold).
  - Add fixture/demo tests for compliant/non-compliant combinations and edge cases.
- **Acceptance criteria**:
  - Reports expose counts + top files for missing domain markers.
  - AI_PRIORITIES includes actionable guidance when violations exceed threshold.
  - Guides updated with marker policy and examples.

---

### 5.6 Section 6 — Audit-driven remediation (non-tool code)

Outstanding product/codebase work **surfaced by tools**, not dev-tools implementation per se. **Use live counts** from [AI_STATUS.md](AI_STATUS.md), [AI_PRIORITIES.md](AI_PRIORITIES.md), [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md). **Tracking**: treat legacy marker reduction and deprecation-inventory closures as **product workstreams** (same PR as inventory updates per [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)); they are **not** blocked on further dev-tools suite features once reports are accurate.

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
  - **2026-04-16 priority**: keep this in the active backlog, but behind coverage work and report-semantic cleanup unless a portability regression appears in a fresh audit.

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

#### 7.21 Audit-tier participation and report-inclusion matrix (new)

- **Status**: **COMPLETE (2026-04-15)** — `development_tools/shared/audit_tool_matrix.py`, `config/audit_tool_matrix.json`, `test_audit_tool_matrix_policy.py`.
- **Goal**: Identify tools that do not run in audit tiers, explain why, and evaluate whether they should; also verify that outputs from tools that do run are represented in AI_STATUS/AI_PRIORITIES/CONSOLIDATED_REPORT.
- **Tasks**:
  - Generate tool matrix: `tool -> tier participation (quick/default/full) -> reason (dependency/runtime/manual-only)` from metadata + orchestration groups.
  - List non-audit tools and classify rationale (`manual investigative`, `unsafe to auto-run`, `too slow`, `redundant`, `not wired yet`).
  - Cross-check report inclusion: for each in-audit tool, identify where (if anywhere) its outputs appear in status/priorities/consolidated; flag missing or stale links.
  - Recommend tier moves or report-integration changes with risk/performance notes.
- **Acceptance criteria**:
  - Matrix artifact checked in (JSON + human-readable summary).
  - At least one policy test guards against silent drift between tool metadata/orchestration/report inclusion.

---

### 5.8 Monitoring and deferred test work (no active V4 tasks)

- **§1.3** — Intermittent low coverage: **MONITORING**; reopen on recurrence.
- **§1.2** — `test_audit_tier_comprehensive.py`: **deferred** unless cost/benefit justifies re-enable.

**Deferred backlog (2026-04-16 reset)** — pick up when the active slice is complete or when related code is already in motion: §1.1 opportunistic `test_config.json` migration in analyzer tests; §1.5 numeric cache benchmarks; §3.13–3.15 remaining scripts/gap heuristics; §3.16 helper extraction from `report_generation.py` / `run_test_coverage.py`; §4.1 additional external-tool evaluation; §5.4 TODO-sync workflow polish; §5.5 gap-analysis expansion; §5.6 memory profiler; §7.8–7.13 and §7.15 as separately prioritized work.

---

## 6. Related documents

- [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) — full V4 checklist history  
- [AI_DEVELOPMENT_TOOLS_GUIDE.md](AI_DEVELOPMENT_TOOLS_GUIDE.md) / [DEVELOPMENT_TOOLS_GUIDE.md](DEVELOPMENT_TOOLS_GUIDE.md)  
- [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)  
- [AI_DEVELOPMENT_WORKFLOW.md](../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) (Standard Audit Recipe §10)  
- [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md)  
- [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md) — scripts backlog and flaky detector notes  
- [LIST_OF_LISTS.md](../development_docs/LIST_OF_LISTS.md) — canonical list principles (relevant to §7.8)  
