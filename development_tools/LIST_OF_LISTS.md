# List of Lists - Canonical Sources


> **File**: `development_tools/LIST_OF_LISTS.md`
**Purpose**: Current ownership map for list-like data (arrays, mappings, enumerated sets) in **development tools** code and config. Product/runtime lists: [PRODUCT_LIST_OF_LISTS.md](../development_docs/PRODUCT_LIST_OF_LISTS.md). Planning ownership: [PLANS.md](../development_docs/PLANS.md) Section 2.

**Audience**: Maintainers, AI collaborators.
**Last updated**: 2026-08-10 (SSOT cleanup: omit default-copy JSON; retire `audit_scripts`; STORAGE_SCOPE re-export)

**Config shorthand**: `development_tools_config.json` means `development_tools/config/development_tools_config.json` (loaded by `development_tools/config/config.py`). Template: `development_tools/config/development_tools_config.json.example`.

**Principles**:
1. Every list has a single canonical source.
2. **Project-specific** lists -> `development_tools_config.json`. **Non-project-specific** lists used in more than one place -> `development_tools/shared/` (`development_tools/shared/common.py`, `development_tools/shared/constants.py`, or `development_tools/shared/standard_exclusions.py`). Single-use portable lists may stay in the one file that uses them.
3. **Consolidate when overlap is complete or appropriate**: derive subsets from the larger canonical list instead of maintaining both.
4. **Omit optional JSON keys when code defaults are correct** - do not duplicate a path or keyword list in JSON solely to "document" it.

**Quick index**: [1 Commands](#1-commands-and-tool-catalog) | [2 Audit tiers](#2-audit-tiers) | [3 Deprecation](#3-deprecation--legacy) | [4 Docs](#4-documentation-lists) | [5 Exclusions](#5-exclusions-and-ignores) | [6 Config/constants](#6-config-and-shared-constants) | [7 Operational](#7-operational-lists) | [8 Alignment](#8-alignment-workflow) | [9 Consolidation status](#9-consolidation-status) | [10 Quick reference](#10-quick-reference)

---

## 1. Commands and tool catalog

| What | Canonical source | Notes |
|------|------------------|-------|
| **CLI command names** | `development_tools/shared/cli_interface.py` - `COMMAND_REGISTRY` | Guides may summarize; do not invent a second inventory |
| **Command tier groups** | `development_tools/shared/tool_metadata.py` - `COMMAND_GROUPS` | Each `commands[]` must be ⊆ `COMMAND_REGISTRY` |
| **Backup subcommands** | `development_tools/shared/cli_interface.py` - `_backup_command()` subparsers | `inventory`, `retention`, `drill`, `verify` |
| **Tool metadata** | `development_tools/shared/tool_metadata.py` - `_TOOLS` | Single catalog for name/path/tier/trust/description |
| **Script name -> path** | `development_tools/shared/tool_metadata.py` - `get_script_registry()` | Derived from `_TOOLS` (minus `_SCRIPT_REGISTRY_EXCLUDE`) |
| **Storage-using tools** | `development_tools/shared/verify_tool_storage.py` - `EXPECTED_TOOLS` | Must be ⊆ `_TOOLS` keys (policy test) |
| **Cache-aware tools** | `development_tools/shared/tool_metadata.py` - `CACHE_AWARE_TOOLS` | Must be ⊆ `_TOOLS` (policy test) |
| **Tool guide fields** | `development_tools/shared/tool_guide.py` - `TOOL_GUIDE_OVERRIDES` | Guide-only prose; path/tier/description enriched from `_TOOLS` |
| **Tier display titles** | `development_tools/shared/tool_metadata.py` - `TIER_TITLES` | Imported by tool_guide |
| **Quick-audit tool membership** | `development_tools/shared/audit_tiers.py` - `TIER1_*` | Orchestration uses tier groups; optional `quick_audit` JSON only overrides knobs like `results_file` (omit when defaults match). Do not maintain a parallel `audit_scripts` list |

---

## 2. Audit tiers

**Canonical**: `development_tools/shared/audit_tiers.py` - `TIER*_TOOL_NAMES`, `TIER*_GROUP_MAP`, `TIER*_ORCHESTRATION_OMIT`, `get_expected_tools_for_tier()`, `get_tier_runnables()`.

- Flat names = membership for expected/reporting.
- Group maps = orchestration order.
- Omit sets = intentional non-scheduled members (e.g. Tier 1 `quick_status`).
- Import-time check: groups ∪ omit == flat set.
- `development_tools/config/config.py` `AUDIT_TIERS` default is built from this module; external JSON may override.

Consumers: `development_tools/shared/service/audit_orchestration.py`, `development_tools/shared/measure_tool_timings.py`. Do not maintain a second tier inventory.

---

## 3. Deprecation / legacy

| What | Canonical source | Notes |
|------|------------------|-------|
| **Inventory** | `development_tools/config/jsons/DEPRECATION_INVENTORY.json` | `active_or_candidate_inventory`, `removed_inventory`, `global_sweep_keywords`, `legacy_scan_patterns` |
| **Scan patterns** | Inventory `legacy_scan_patterns` | Optional config `legacy_cleanup.legacy_patterns` override only |
| **Live `legacy_cleanup` knobs** | config `required_pattern_keys`, `replacement_mappings` | Path/guard/skip defaults live in code; omit from JSON unless overriding |
| **Guard trigger keywords** | Code defaults in `development_tools/shared/service/tool_wrappers.py` - `_check_deprecation_inventory_sync` | Distinct purpose from inventory `global_sweep_keywords` |

Never add a second top-level `"legacy_cleanup"` key (JSON keeps only the last).

---

## 4. Documentation lists

| What | Canonical source | Notes |
|------|------------------|-------|
| **Paired docs** | config `constants.paired_docs` -> `PAIRED_DOCS` in `development_tools/shared/constants.py` | DOCUMENTATION_GUIDE Section 4.1 is human summary; doc-sync validates |
| **Version-sync file lists** | config `fix_version_sync.ai_docs`, `.docs`, `.cursor_rules`, ... | Category lists (`communication_docs`, etc.) derived from `docs` by path prefix |
| **Default docs set** | Derived in `get_constants_config()` | From paired + version-sync + `default_docs_extra` unless `default_docs` set explicitly |
| **Behavior specs** | Included in `fix_version_sync.docs` + `constants.fix_version_sync_directories` | Index: `specs/SPECS_GUIDE.md` |
| **Doc-analysis / path-drift helpers** | Mostly `development_tools/shared/constants.py` | Project TOC fragments: config `path_drift.ignored_path_patterns`; legacy paths: `path_drift.legacy_documentation_files` |
| **Placeholder patterns** | config `documentation_analysis.placeholder_patterns` | |

Paired docs = heading/content sync. Version-sync lists = version/date metadata. Different purposes; do not merge.

---

## 5. Exclusions and ignores

| What | Canonical source | Notes |
|------|------------------|-------|
| **Dev-tools base/context/generated exclusions** | config `exclusions.*` merged via `get_exclusions()`; portable defaults in `development_tools/shared/standard_exclusions.py` | Live/example omit full `base_exclusions`; use `base_exclusions_additions` / `base_exclusions_removals` for project deltas |
| **Ruff exclude** | Generated from standard_exclusions + config via `development_tools/config/sync_ruff_toml.py` | Do not hand-edit `.ruff.toml` or `development_tools/config/ruff.toml` |
| **Pyright exclude** | Root `pyproject.toml` `[tool.pyright]` only | |
| **Pytest collection ignores** | `tests/conftest.py` `collect_ignore*` | `pytest.ini` owns CLI `--ignore` / markers / addopts |
| **Coverage omit** | `development_tools/tests/coverage.ini`, `development_tools/tests/coverage_dev_tools.ini` | Per coverage run |
| **.gitignore / .cursorignore** | Those files | Different tools; no single "ignore" SSOT |

**Intentional separate** (do not consolidate): `exclusions.historical_preserve_files` (cleanup preserve patterns) vs `exclusions.tool_exclusions.documentation` (doc-tool scan skips) vs `path_drift.legacy_documentation_files` (path-drift exclusions). Overlap on changelog paths is OK.

---

## 6. Config and shared constants

| What | Canonical source | Notes |
|------|------------------|-------|
| **local_module_prefixes** | config `constants.local_module_prefixes` | Drives derived `scan_directories` / `core_modules` / `project_directories` via `derived_prefix_excludes`. MHM `core` excludes omit `development_tools` so `CORE_MODULES` includes it (documented in live/example `_comment`); portable default excludes `development_tools` from core |
| **Common names / third-party / code patterns** | config `constants.common_*`, `third_party_libraries` | Loaded by `development_tools/shared/constants.py` with portable fallbacks |
| **Test markers** | config top-level `test_markers` | `directory_to_marker` derived from `categories` when absent; `development_tools/shared/constants.py` re-exports |
| **Domain mapper** | config `domain_mapper.*` | Portable `DOMAIN_MAPPER_DEFAULTS` empty; project maps in JSON (example for CI). Missing prefixes still augmented at runtime |
| **Static channel-logger paths** | config `static_checks.channel_loggers` | Component-name allowlist SSOT: `core/logger.py` |
| **Known deleted files** | config `data_freshness.known_deleted_files` | Portable default `[]`; MHM paths only in live JSON |
| **Function-registry narrative** | Portable defaults: `development_tools/config/config.py` - `AUDIT_FUNCTION_REGISTRY` | MHM path trees: JSON `analyze_function_registry.decision_trees` |
| **analyze_config expected functions / sections** | config `analyze_config` | Portable `CONFIG_VALIDATOR` lists empty; project values in JSON / example |
| **analyze_functions / error_handling keywords** | config sections (defaults in `development_tools/config/config.py`) | Prefer omitting JSON keys that match defaults exactly |
| **Portable keyword/pattern sets** | `development_tools/shared/constants.py` | e.g. `SPECIAL_METHODS`, `STANDARD_LIBRARY_*`, `ASCII_REPLACEMENTS`, path-drift operators |
| **Generated file-level patterns** | config `exclusions.generated_files` -> `development_tools/shared/standard_exclusions.py` | Function-level generated patterns: `AUTO_GENERATED_*` in constants |

---

## 7. Operational lists

| What | Canonical source | Notes |
|------|------------------|-------|
| **Static-check / coverage / pip-audit cache paths** | `development_tools/shared/cache_dependency_paths.py` | Add a path when config changes must bust caches |
| **Suite profiles** | `development_tools/config/config.py` - `SUITE_PROFILES`, `TEST_RUN_DEFAULTS` | Optional thin JSON `test_run` override |
| **Ruff / Pyright path shards** | Project JSON `static_analysis.*_path_shards` | Portable code default is empty |
| **Audit tool matrix** | Built by `development_tools/shared/audit_tool_matrix.py` from tiers + `_TOOLS` | Artifact JSON is generated - do not hand-edit as SSOT |
| **Tool cache inventory** | `development_tools/config/tool_cache_inventory.json` | Descriptive; runtime invalidation uses `CACHE_AWARE_TOOLS` |
| **Backup policy** | config `backup_policy.*` | |
| **Windows process-group scripts** | `development_tools/shared/service/tool_wrappers.py` - `_WIN_PROCESS_GROUP_SCRIPTS` | Small portable frozenset |

---

## 8. Alignment workflow

1. **Code/config first** - fix the canonical source and consumers; omit JSON that only copies correct defaults.
2. **Derive subsets** - if A ⊆ B and same purpose, derive A in code and delete the duplicate list.
3. **Then docs** - point guides at the canonical source; prefer structural tests over copying lists into prose.
4. **Record open work here** in [§9](#9-consolidation-status); do not keep long "Done" audit trails in this file (changelogs own history).

**When not to consolidate**: different purposes; tool-specific formats (Ruff vs Pyright); consolidation would obscure intent.

---

## 9. Consolidation status

Dev-tools list SSOT from the 2026-08-06 scan is closed. Product/runtime lists: [PRODUCT_LIST_OF_LISTS.md](../development_docs/PRODUCT_LIST_OF_LISTS.md).

### Healthy

- `_TOOLS` -> script registry; `EXPECTED_TOOLS` / `CACHE_AWARE_TOOLS` ⊆ `_TOOLS` (tier comments on `EXPECTED_TOOLS` aligned to `audit_tiers`).
- `audit_tiers` flat + group maps + omit sets with import-time coverage.
- `COMMAND_GROUPS` ⊆ `COMMAND_REGISTRY` (aliases like `full-audit` omitted from groups on purpose).
- Version-sync category lists and `default_docs` derivation; `local_module_prefixes` directory derivation.
- Live JSON omits optional keys/sections that match code defaults (`audit_tiers`, `default_docs`, `tool_commands`, `file_patterns`, `test_run`, `analyze_duplicate_functions`, `workflow`, `documentation`, `auto_document`, `ai_validation`, `ai_collaboration`, `audit`, `output`, `status`, `system_signals`, `validation`, `quick_audit`, matching `static_analysis` / `analyze_function_registry` scalars, …).
- `base_exclusions` via portable defaults + additions/removals; MHM `analyze_config` / `domain_mapper` / `known_deleted_files` live only in JSON (empty portable code defaults).
- MHM `derived_prefix_excludes.core` intentionally omits `development_tools` (includes it in `CORE_MODULES`); documented in live/example `_comment`.
- Path-drift keyword overlap: `_PYTHON_KEYWORDS_SHARED` in `development_tools/shared/constants.py` feeds `COMMON_VARIABLE_NAMES` and `PYTHON_KEYWORDS_PATH_DRIFT`.
- Legacy scan patterns in inventory; lean live `legacy_cleanup`.
- Quick-audit membership = `audit_tiers.TIER1_*` (retired unused `quick_audit.audit_scripts`).
- `STORAGE_SCOPE_*` string ids defined once in `development_tools/shared/audit_scope.py` and re-exported by `development_tools/shared/audit_storage_scope.py`.

### Optional leftover

None for the current scan. Product help curated lists remain intentional (see [PRODUCT_LIST_OF_LISTS.md](../development_docs/PRODUCT_LIST_OF_LISTS.md)).

---

## 10. Quick reference

| I need to... | Canonical source |
|------------|------------------|
| Add a tool | `development_tools/shared/tool_metadata.py` `_TOOLS`; add to `EXPECTED_TOOLS` in `development_tools/shared/verify_tool_storage.py` if it uses storage |
| Add a CLI command | `COMMAND_REGISTRY` in `development_tools/shared/cli_interface.py` + `COMMAND_GROUPS` in `development_tools/shared/tool_metadata.py` |
| Add an exclusion (Ruff/scans) | config `exclusions` (prefer additions/removals) + regenerate ruff via `python -m development_tools.config.sync_ruff_toml` |
| Add a paired doc | config `constants.paired_docs` + DOCUMENTATION_GUIDE Section 4.1 |
| Add a doc to version-sync | config `fix_version_sync.docs` or `.ai_docs` |
| Add a deprecation/legacy item | `development_tools/config/jsons/DEPRECATION_INVENTORY.json` |
| Add a test marker | config `test_markers.categories` (+ `pytest.ini` for pytest behavior) |
| Add a path-drift exclusion | config `path_drift.legacy_documentation_files` |
| Tune ignored heading/TOC fragments | config `path_drift.ignored_path_patterns` |
| Tune scan/core/project derivation | config `constants.derived_prefix_excludes` |
| Bust static-check/coverage caches | `development_tools/shared/cache_dependency_paths.py` |
| Change suite exclude markers | `SUITE_PROFILES` / `TEST_RUN_DEFAULTS` in `development_tools/config/config.py` (thin JSON `test_run` override) |
| Change Ruff/Pyright shard roots | Project JSON `static_analysis.*_path_shards` |
| Regenerate audit tool matrix | Edit builders/tiers in `development_tools/shared/audit_tool_matrix.py` / `development_tools/shared/audit_tiers.py`, regenerate artifact |
| Edit backup policy | config `backup_policy.*` |
