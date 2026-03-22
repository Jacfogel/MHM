# List of Lists — Canonical Sources, Uses, and Alignment


> **File**: `development_docs/LIST_OF_LISTS.md`
**Purpose**: Single reference for list-like data (arrays, mappings, enumerated sets) in code and config. Align code/config first, then align docs to canonical lists.

**Audience**: Maintainers, AI collaborators.  
**Last updated**: 2026-03-22 (consolidation scan: standard_exclusions, constants, audit_tiers, config; project-specific reorganization)

**Principles**: (1) Every list has a single canonical source. (2) **Project-specific** lists → `development_tools_config.json`. **Non–project-specific** lists that are used in more than one place → `development_tools/shared/common.py`, `development_tools/shared/constants.py`, or `development_tools/shared/standard_exclusions.py` as appropriate. Single-use, non–project-specific lists can stay in the single file that uses them. (3) **Consolidate when overlap is complete or appropriate**: Where lists overlap fully (e.g. subset A is entirely contained in list B), derive the subset from the canonical list instead of maintaining both. Where lists serve the same purpose with different scopes, derive from one canonical source or document when consolidation is appropriate.

**Quick index**: [1](#1-development-tools-commands-and-command-groups) Commands | [2](#2-development-tools-tool-catalog-modules--scripts) Tool catalog | [2b](#2b-audit-tier-tool-lists-tier-1--2--3--which-tools-run-in-each-audit-tier) Audit tiers | [3](#3-deprecation--legacy-inventory) Deprecation | [4](#4-paired-documentation-list) Paired docs | [5](#5-exclusions-and-ignore-lists) Exclusions | [6](#6-config-and-code-constants-development_tools_configjson) Config | [7](#7-code-only-lists-in-development_tools-align-or-pull-from-canonical) Code-only lists | [7b](#7b-test-and-coverage-lists-development_toolstests) Test lists | [8](#8-other-list-like-assets) Other assets | [9](#9-alignment-workflow-summary) Alignment | [9a](#9a-consolidation-criteria-and-workflow) Consolidation | [9b](#9b-consolidation-scan-standard_exclusions-constants-audit_tiers-development_tools_config) Scan (4 files) | [10](#10-documentation-analysis-and-path-drift-lists-candidates-for-canonical-sources) Doc/path-drift | [11](#11-other-lists-config-functions-error_handling--migration-candidates) Migration candidates | [12](#12-lists-that-dont-yet-meet-the-principles) Violations | [13](#13-config-list-inventory-consolidation-scan) Config inventory | [14](#14-quick-reference) Quick reference | [15](#15-next-action-steps-list-relocation) Next steps

---

## 1. Development-tools commands and command groups


| What                                                         | Canonical source                                                                                                               | Uses                                                                                                            | Other locations / overlap                                                                                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI command names**                                        | `development_tools/shared/cli_interface.py` — `COMMAND_REGISTRY` (OrderedDict of command name → `CommandRegistration`)         | `run_development_tools.py` (dispatch, help); tests (e.g. `test_tooling_policy_consistency.py`)                  | **Docs**: DEVELOPMENT_TOOLS_GUIDE.md, AI_DEVELOPMENT_TOOLS_GUIDE.md list commands in prose/tables — can drift. Align docs to code after code is stable. |
| **Command tier grouping (Core / Supporting / Experimental)** | `development_tools/shared/tool_metadata.py` — `COMMAND_GROUPS` (OrderedDict: group name → `{ tier, description, commands[] }`) | `development_tools/shared/common.py` — `COMMAND_TIERS = COMMAND_GROUPS`; `run_development_tools.py` help output | Same as above; guide "Core Commands" / "Supporting Commands" sections should match COMMAND_GROUPS.                                                      |
| **Backup subcommands**                                       | `development_tools/shared/cli_interface.py` — `_backup_command()`: subparsers for `inventory`, `retention`, `drill`, `verify`  | Backup policy operations; help text in same function                                                            | Doc guides that describe "backup inventory", "backup verify", etc. should match this set.                                                               |


**Alignment note**: COMMAND_REGISTRY is the single source of "what commands exist". COMMAND_GROUPS must list a subset (each `commands` array). Ensure every COMMAND_GROUPS command exists in COMMAND_REGISTRY; then align guides to COMMAND_GROUPS + COMMAND_REGISTRY.

---

## 2. Development-tools tool catalog (modules / scripts)


| What                                                     | Canonical source                                                                                                                                    | Uses                                                                                 | Other locations / overlap                                                                                                                                                                                                                                                                                                                                        |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tool metadata (name, path, tier, trust, description)** | `development_tools/shared/tool_metadata.py` — `_TOOLS` dict (key = tool name, value = `ToolInfo`)                                                   | Tier/audit logic, help, cache discovery, tool_guide; tool_wrappers call `run_<name>` | **Config**: `quick_audit.audit_scripts` is a *subset* of script names (e.g. `analyze_documentation.py`) — different naming (filename vs tool name). **Docs**: DEVELOPMENT_TOOLS_GUIDE.md, AI_DEVELOPMENT_TOOLS_GUIDE.md have tool tables. **`development_tools/shared/verify_tool_storage.py`**: `EXPECTED_TOOLS` — subset of tool names → storage domain; must stay subset of _TOOLS keys. |
| **Tools that use standardized storage**                  | `development_tools/shared/verify_tool_storage.py` — `EXPECTED_TOOLS` (dict: tool_name → domain)                                                     | Storage verification script; policy consistency tests                                | Must be subset of `tool_metadata._TOOLS`. No other canonical list; align by ensuring every EXPECTED_TOOLS key exists in _TOOLS. See `development_tools/shared/tool_metadata.py` and `development_tools/shared/verify_tool_storage.py`. |
| **Quick-audit script list**                              | `development_tools/config/development_tools_config.json` — `quick_audit.audit_scripts` (array of script filenames, e.g. `analyze_documentation.py`) | Quick audit mode (which scripts to run)                                              | Overlaps in *concept* with tool catalog; naming is script filename, not tool name (e.g. `analyze_documentation_sync` in _TOOLS vs `analyze_documentation_sync.py` in config). Keep config as canonical for "what runs in quick audit"; document mapping to _TOOLS if needed.                                                                                     |


| **Script name → path (run_script)** | `development_tools/shared/service/tool_wrappers.py` — `SCRIPT_REGISTRY` (from `tool_metadata.get_script_registry()`) | `run_script()`, tool_guide.run_tool_with_guidance fallback | Derived from `tool_metadata._TOOLS` (ToolInfo.path); single canonical source. |
| **Cache-aware tools (invalidation)** | `development_tools/shared/tool_metadata.py` — `CACHE_AWARE_TOOLS` (frozenset of tool names) | `audit_orchestration` (cache invalidation when those tools run) | Subset of _TOOLS; single canonical source in `development_tools/shared/tool_metadata.py`. |

**Alignment note**: _TOOLS is the single source for "all known tools". EXPECTED_TOOLS and audit_scripts are specialized subsets; when adding/removing tools, update _TOOLS first, then these subsets and docs. SCRIPT_REGISTRY should be derived from _TOOLS (ToolInfo.path) so paths stay canonical.

---

## 2b. Audit tier tool lists (Tier 1 / 2 / 3 — which tools run in each audit tier)

**Canonical source**: `development_tools/shared/audit_tiers.py` — `TIER1_TOOL_NAMES`, `TIER2_TOOL_NAMES`, `TIER3_TOOL_NAMES`, `get_expected_tools_for_tier(tier)`, `get_tier_runnables(service, tier)`.

| What | Location | Uses |
|------|----------|------|
| **Tier 1/2/3 tool names + runnables** | `development_tools/shared/audit_tiers.py` — flat names + `_get_runnable(service, name)` | `measure_tool_timings.run_timing_analysis()`, `audit_orchestration` (via `get_tier1_groups`, `get_tier2_groups`, `get_tier3_groups`) |
| **Expected tools for tier** | `audit_orchestration._get_expected_tools_for_tier(tier)` → calls `audit_tiers.get_expected_tools_for_tier(tier)` | Reporting, cache metadata, tier summary |

**Other locations to keep in sync**: `development_tools/shared/verify_tool_storage.py` — `EXPECTED_TOOLS` (tool name → storage domain) should remain a subset of tools that exist in `tool_metadata._TOOLS` and ideally align with tier tool names where applicable. No code should hardcode a duplicate tier tool list; all should import from `audit_tiers`.

---

## 3. Deprecation / legacy inventory


| What                                                                               | Canonical source                                                                                                                                                | Uses                                                                                                                                                                                                       | Other locations / overlap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Deprecation inventory (active/candidate/removed items, search terms, evidence)** | `development_tools/config/jsons/DEPRECATION_INVENTORY.json` — `sources`, `global_sweep_keywords`, `active_or_candidate_inventory`, `removed_inventory`          | `development_tools/legacy/analyze_legacy_references.py` (loads inventory); `development_tools/legacy/generate_legacy_reference_report.py`; tool_wrappers (guard removed) | **Config**: `development_tools_config.json` — `legacy_cleanup.deprecation_inventory_file` (path to JSON; **live config may have wrong path**: `config/DEPRECATION_INVENTORY.json` vs `config/jsons/DEPRECATION_INVENTORY.json` — align to `jsons/`). `legacy_cleanup.deprecation_inventory_sync_guard.trigger_keywords` — subset of keywords that trigger "did you update the inventory?" guard; overlaps with DEPRECATION_INVENTORY `global_sweep_keywords`. **Docs**: AI_LEGACY_COMPATIBILITY_GUIDE.md, AI_DEVELOPMENT_WORKFLOW.md, DEVELOPMENT_TOOLS_GUIDE.md reference the inventory path. |
| **Legacy scan patterns (old paths, deprecated functions, etc.)**                   | `development_tools/config/development_tools_config.json` — `legacy_cleanup.legacy_patterns` (e.g. old_bot_directory, old_import_paths, deprecated_functions, …) | `development_tools/legacy/analyze_legacy_references.py` merges config patterns with inventory-injected terms | DEPRECATION_INVENTORY entries can reference the same code/config; inventory is governance (status, search_terms), config is pattern definitions.                                                                                                                                                                                                                                                                                                                                                                                                                                               |


**Alignment note**: (1) Fix config `deprecation_inventory_file` to `development_tools/config/jsons/DEPRECATION_INVENTORY.json` everywhere. (2) Decide canonical source for "trigger keywords" (guard): either DEPRECATION_INVENTORY `global_sweep_keywords` or config `trigger_keywords`; document and have the other derive or stay in sync.

---

## 4. Paired documentation list


| What                                              | Canonical source                                                                                                                                                                                                              | Uses                                                                         | Other locations / overlap                                                                                                                                                                                            |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Paired docs (human doc → AI doc mapping)**      | **Runtime**: `development_tools_config.json` — `constants.paired_docs` (object); loaded by `development_tools/shared/constants.py` as `PAIRED_DOCS`. **Human-facing**: `DOCUMENTATION_GUIDE.md` §4.1 (bullet list). | `development_tools/docs/analyze_documentation_sync.py` (uses PAIRED_DOCS); doc-sync; heading checks | Config is canonical for tooling. A future generic list-sync mechanism (config-driven, multiple list types) could keep DOCUMENTATION_GUIDE §4.1 and other doc lists in sync. |
| **Version-sync file lists (ai_docs, docs, etc.)** | `development_tools_config.json` — `fix_version_sync.ai_docs`, `fix_version_sync.docs`, `cursor_rules`, …                                                                                                                      | `development_tools/docs/fix_version_sync.py` (scope for version/date updates) | **Consolidated**: `communication_docs`, `core_docs`, `logs_docs`, `scripts_docs`, `tests_docs` derived from `docs` by path prefix (config override optional). Exclusions: fix_version_sync uses `get_exclusions("fix_version_sync", "development")`; `exclude_patterns` removed from config. paired_docs = "heading sync"; version-sync lists = "version metadata". |


**Alignment note**: See AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4 §7.8. Align config and DOCUMENTATION_GUIDE §4.1 first (one canonical); then ensure docs that reference "paired doc list" point to that canonical source.

---

## 5. Exclusions and ignore lists


| What                                                | Canonical source                                                                                                                                                                                                                                                                                                                    | Uses                                                     | Other locations / overlap                                                                                            |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Ruff exclude patterns**                           | **Source of truth**: `development_tools/shared/standard_exclusions.py` (defaults) + `development_tools_config.json` — `exclusions.base_exclusions`, etc., merged via `get_exclusions()`. **Generated**: `.ruff.toml` (root), `development_tools/config/ruff.toml` — both generated by `development_tools/config/sync_ruff_toml.py`. | Ruff lint; sync script writes TOML                       | Two TOML files are outputs; do not edit by hand. Regenerate after changing standard_exclusions or config exclusions. |
| **Pyright exclude**                                 | Root `pyrightconfig.json` — `exclude` array. Also `development_tools/config/pyrightconfig.json` — `exclude` array.                                                                                                                                                                                                                  | Pyright type checking                                    | **Intentionally two canonical sources**: root = project type-checking; dev-tools = dev-tools subproject. Document when adding new exclusions to both. No sync script.            |
| **.gitignore**                                      | `.gitignore` (line-based)                                                                                                                                                                                                                                                                                                           | Git                                                      | Conceptual overlap with Ruff/Pyright/pytest exclusions; different tool, no single canonical "ignore" list.           |
| **Pytest collect_ignore**                           | `pytest.ini` — `collect_ignore` (multi-line list)                                                                                                                                                                                                                                                                                   | Pytest collection                                        | Overlaps conceptually with test exclusions elsewhere; pytest.ini is canonical for pytest.                            |
| **Coverage omit patterns**                         | `development_tools/tests/coverage.ini`, `development_tools/tests/coverage_dev_tools.ini` — `omit` (multi-line globs)                                                                                                                                                                                                                 | Coverage.py (main project vs dev-tools coverage)         | Conceptual overlap with base exclusions; coverage.ini is canonical for each coverage run.                           |
| **Dev-tools exclusions (base, context, generated)** | `development_tools_config.json` — `exclusions.base_exclusions`, `exclusions.context_exclusions`, `exclusions.generated_files`, etc.                                                                                                                                                                                                 | `development_tools/shared/standard_exclusions.py` (via config); various analyzers | Feeds Ruff via sync; also used for scan roots, cache cleanup.                                                        |


**Alignment note**: For Ruff, only change standard_exclusions + config; never edit the two ruff.toml files by hand. For Pyright, two exclude arrays are intentionally separate (root = project; dev-tools = subproject); document when adding new exclusions to both. Coverage omit lists are independent per file; align with base exclusions when changing project ignore policy.

---

## 6. Config and code constants (development_tools_config.json)


| What                                                                                                     | Canonical source                                                                                                                                                                                  | Uses                                                                                                                             | Other locations / overlap                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **default_docs, paired_docs, local_module_prefixes, test_markers, …** | `development_tools_config.json` — `constants`, `paths`, `fix_version_sync`, etc. | `development_tools/shared/constants.py`; config.py getters | **Consolidated**: `local_module_prefixes` is canonical. `scan_directories`, `core_modules`, `project_directories` are derived in `development_tools/shared/constants.py`; config override optional. See §9a. `file_patterns.exclude_patterns` removed; use `exclusions.base_exclusions`. |
| **Test markers (categories, directory map, etc.)**                                                       | `development_tools_config.json` — `test_markers.categories`, `test_markers.transient_data_path_markers`, etc.                                                                                     | Dev-tools test marker analysis                                                                                                   | `pytest.ini` — `markers` (pytest's own list). Overlap in purpose; config = dev-tools analysis, pytest.ini = pytest behavior. Keep both; document that they serve different tools. |


---

## 7. Code-only lists in development_tools (align or pull from canonical)

These lists live only in code. Many should pull from config or a single code canonical source to avoid overlap and drift.

| What | File | Canonical / overlap | Notes |
|------|------|---------------------|--------|
| **Tool guide (usage, when_to_use, output_interpretation)** | `development_tools/shared/tool_guide.py` — `TOOL_GUIDE_BY_TOOL_NAME` (derived from `tool_metadata._TOOLS`) + `TOOL_GUIDE_BY_SCRIPT_BASENAME` (compat map derived from basenames) | Single canonical tool identity/path in `tool_metadata._TOOLS`; `tool_guide` only adds user-facing guidance fields via a small override map keyed by tool name. | Filename-based lookups remain supported via a derived basename compat layer; collisions are guarded (fail fast) during module import. |
| **Tier display titles** | `development_tools/shared/tool_metadata.py` — `TIER_TITLES` (core/supporting/experimental → label) | Single canonical source; tool_guide imports from tool_metadata. | Moved from tool_guide 2026-03. |
| **Test keywords (function-level)** | `development_tools/shared/exclusion_utilities.py` — `_DEFAULT_TEST_KEYWORDS`; `_get_test_keywords()` loads from config `analyze_functions.test_keywords` | Config is canonical when present. | Already pulls from config; defaults are fallback. |
| **Generated file patterns (function-level)** | `development_tools/shared/constants.py` — `AUTO_GENERATED_FILE_PATTERNS`, `EXACT_GENERATED_NAMES`, `GENERATED_NAME_PATTERNS` | Single canonical source; exclusion_utilities imports from constants. | Used by is_generated_file / is_generated_function. Moved from exclusion_utilities 2026-03. |
| **Special Python methods (exclude from undocumented / error-handling)** | `development_tools/shared/constants.py` — `SPECIAL_METHODS`, `CONTEXT_METHODS` (frozensets) | Single canonical source. | Used by `exclusion_utilities.is_special_python_method()` and `analyze_error_handling`; no longer duplicated. |
| **Base/context exclusions defaults** | `development_tools/shared/standard_exclusions.py` — `_DEFAULT_BASE_EXCLUSIONS`, `_DEFAULT_CONTEXT_EXCLUSIONS` | Loaded from config when available; defaults are fallback. | Already config-driven. |
| **Generated files list (file-level)** | `development_tools/shared/standard_exclusions.py` — `GENERATED_FILES`, `GENERATED_FILE_PATTERNS`, `ALL_GENERATED_FILES` | From config `exclusions.generated_files`. | Canonical for **file-level** generated paths/patterns; consumed by multiple tools. |
| **Base exclusion shortlist** | `development_tools/shared/standard_exclusions.py` — `BASE_EXCLUSION_SHORTLIST` | From config `exclusions.base_exclusion_shortlist`. | Used by `development_tools/config/sync_ruff_toml.py`. |
| **Doc-sync placeholders** | `development_tools/shared/standard_exclusions.py` — `DOC_SYNC_PLACEHOLDERS` (dict path → placeholder text) | Hardcoded. | Could move to config if needed. |
| **Constants (stdlib, common names, patterns)** | `development_tools/shared/constants.py` — `STANDARD_LIBRARY_*`, `COMMON_FUNCTION_NAMES`, `COMMON_CLASS_NAMES`, `IGNORED_PATH_PATTERNS`, `COMMAND_PATTERNS`, `PATH_STARTSWITH_NON_FILE` (derived from `_NON_PATH_PREFIXES` + COMMAND_PATTERNS), `THIRD_PARTY_LIBRARIES`, `SPECIAL_METHODS`, `CONTEXT_METHODS`, `CORRUPTED_ARTIFACT_PATTERNS`, `TEMPLATE_PATTERNS`, `ASCII_COMPLIANCE_FILES`, `VERSION_SYNC_DIRECTORIES`, `TEST_CATEGORY_MARKERS`, `TEST_MARKER_*`, `AUTO_GENERATED_FILE_PATTERNS`, `EXACT_GENERATED_NAMES`, `GENERATED_NAME_PATTERNS`, etc. | Some loaded from config (PAIRED_DOCS, DEFAULT_DOCS, …); many are code-only. Single definition of PATH_STARTSWITH_NON_FILE (no duplicate). | Path-drift and analysis; consider config for project-specific names. |
| **Generated AI/docs lists (version-sync)** | `development_tools/docs/fix_version_sync.py` — `GENERATED_AI_DOCS`, `GENERATED_DOCS` (from ALL_GENERATED_FILES), `AI_DOCS`, `CURSOR_RULES`, `CURSOR_COMMANDS`, `COMMUNICATION_DOCS`, `CORE_DOCS`, `LOGS_DOCS`, `SCRIPTS_DOCS`, `TESTS_DOCS` (derived from docs), `DOCUMENTATION_PATTERNS`, `_EXCLUDE_PATTERNS` (from get_exclusions), `CORE_SYSTEM_FILES` | Config `fix_version_sync.*` + ALL_GENERATED_FILES. | Overlap with paired_docs; **version-sync** lists govern version/date updates, while **paired_docs** govern heading/content sync. Category lists derived from docs; exclusions from get_exclusions. |
| **Placeholder patterns (documentation)** | `development_tools/docs/analyze_documentation.py` — `PLACEHOLDER_PATTERNS` | Config `documentation_analysis.placeholder_patterns` in `development_tools_config.json`. | Canonical in config; analyze_documentation builds PLACEHOLDER_PATTERNS only from config (no hardcoded override). |
| **Required legacy pattern keys** | `development_tools/legacy/fix_legacy_references.py` — `REQUIRED_LEGACY_PATTERN_KEYS` | Fixed schema. | Low drift. |
| **Known deleted files** | `development_tools_config.json` — `data_freshness.known_deleted_files` | Config canonical; data_freshness_audit uses `get_data_freshness_config()`. | |
| **Static check allowlists/sets** | `development_tools/static_checks/check_channel_loggers.py` — `LOG_METHODS`, `IGNORED_DIR_NAMES` (code); `excluded_dirs`, `allowed_logging_import_paths` from config `static_checks.channel_loggers` | Config for project-specific dirs/import paths; code for generic method names and dir names. | **Done** — EXCLUDED_DIRS and ALLOWED_LOGGING_IMPORT_PATHS → config; `should_exclude_file` for dir exclusion. |
| **Output storage domain directories** | `development_tools/shared/output_storage.py` — `domains` derived from `EXPECTED_TOOLS` in `aggregate_all_tool_results()` | Used when collecting/listing tool result dirs | Derived from `verify_tool_storage.EXPECTED_TOOLS` (unique domain names); single canonical source. |
| **Tool/context exclusions and historical preserve** | `development_tools/shared/standard_exclusions.py` — `TOOL_EXCLUSIONS`, `CONTEXT_EXCLUSIONS`, `HISTORICAL_PRESERVE_FILES` | From config `exclusions.tool_exclusions`, `exclusions.context_exclusions`, `exclusions.historical_preserve_files`; defaults in module. | CONTEXT_EXCLUSIONS includes `recent_changes` (built from generated files). |
| **Doc snapshot / export discovery** | `development_tools/shared/standard_exclusions.py` — `DOC_EXPORT_BASE_EXCLUDE_GLOBS`; `development_tools/shared/export_docs_snapshot.py` imports it as `BASE_EXCLUDE_GLOBS` | Single canonical source in standard_exclusions. | Doc discovery and filtering; overlaps conceptually with base exclusions. |
| **Package exports (analyze_package_exports)** | `development_tools/functions/analyze_package_exports.py` — `EXPORT_PATTERNS`, `EXPECTED_EXPORTS` | From config `analyze_package_exports.export_patterns`, `analyze_package_exports.expected_exports`. | Config is canonical. |
| **Config default schema (default keys)** | `development_tools/config/config.py` — `SCAN_DIRECTORIES`, `AI_COLLABORATION`, `FUNCTION_DISCOVERY`, `VALIDATION`, `ERROR_HANDLING`, `AUDIT`, `FILE_PATTERNS`, `QUICK_AUDIT`, `AUDIT_TIERS`, `VERSION_SYNC`, `DOCUMENTATION_ANALYSIS`, `CONFIG_VALIDATOR`, etc. | Default structure for development_tools_config.json; config file overrides at runtime. | Section 6 covers config keys; this row documents the code-side default dicts. |
| **Sync Ruff TOML header** | `development_tools/config/sync_ruff_toml.py` — `_HEADER` (multi-line string) | Generated TOML file header. | Not a list; template string only. |

---

## 7b. Test and coverage lists (development_tools/tests)

Lists used by test coverage, test markers, and dev-tools coverage cache. Project-specific structure; could move to config if shared across projects.

| What | File | Canonical / overlap | Notes |
|------|------|---------------------|--------|
| **Source → test dir/markers mapping** | `development_tools_config.json` — `domain_mapper.source_to_test_mapping` (domain → [test_dirs[], markers[]]) | Config canonical; domain_mapper.py loads via `get_domain_mapper_config()`. | core, communication, ui, tasks, ai, user, notebook, development_tools. |
| **Domain dependencies** | `development_tools_config.json` — `domain_mapper.domain_dependencies` (domain → list of dependent domains) | Config canonical; domain_mapper.py loads via `get_domain_mapper_config()`. | Used for test ordering / dependency-aware runs. |
| **Domain keyword map** | `development_tools_config.json` — `domain_mapper.keyword_map` (domain → keywords for matching) | Config canonical; domain_mapper.py loads via `get_domain_mapper_config()`. | development_tools, communication, ai, tasks, ui, user, notebook, core. |
| **Test marker categories (files_by_dir keys)** | `development_tools/tests/analyze_test_markers.py` — `files_by_dir` keys: unit, integration, behavior, ui, other | Internal grouping. | Align with test_markers config / pytest markers if documented. |
| **Default coverage.json path** | `development_tools/tests/analyze_test_coverage.py` — default path `development_tools/tests/jsons/coverage.json` | Single default path. | Used when no explicit path; not a list. |
| **Cache-invalidation tool paths** | `development_tools/tests/test_file_coverage_cache.py` — `_get_default_tool_paths()` (tuple of Paths: run_test_coverage.py, test_file_coverage_cache.py, dev_tools_coverage_cache.py, domain_mapper.py) | Hardcoded. | Hash of these files used for cache invalidation; add new tool files here when they affect coverage logic. |

**Alignment note**: SOURCE_TO_TEST_MAPPING and EXPECTED_TOOLS domain names overlap conceptually (e.g. functions, docs, tests). domain_mapper is test-layout; EXPECTED_TOOLS is tool → storage domain. output_storage.domains should match unique values from EXPECTED_TOOLS.

---

## 8. Other list-like assets


| What                               | Canonical source                                                                                          | Uses                                                             | Other locations / overlap                                                     |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **.cursorignore**                  | `.cursorignore` (line-based)                                                                              | Cursor indexing                                                  | Single file; no duplication.                                                  |
| **.env.example list-like vars**    | `.env.example` — e.g. `CATEGORIES`, `FILE_AUDIT_DIRS`, `FILE_AUDIT_IGNORE_DIRS` (comma-separated strings) | Parsed by app/config; not read as list elsewhere in config files | Code that parses these is canonical consumer.                                 |
| **pyproject.toml include/exclude** | `pyproject.toml` — `[tool.setuptools.packages.find]` include, exclude                                     | Setuptools package discovery                                     | Distinct from "scan_directories" / exclusions; document if cross-referencing. |
| **requirements.txt**               | `requirements.txt` (line-based)                                                                           | pip; often same as pyproject.toml dependencies                   | Align with pyproject.toml when both are used.                                 |


---

## 9. Alignment workflow (summary)

1. **Code/config first**: For each list type, fix canonical source and all code consumers (e.g. deprecation_inventory_file path, COMMAND_REGISTRY vs COMMAND_GROUPS, PAIRED_DOCS vs config).
2. **Audit tier tool lists**: Canonical source is `development_tools/shared/audit_tiers.py`; `measure_tool_timings.py` and `audit_orchestration.py` use it. Keep `verify_tool_storage.EXPECTED_TOOLS` as a subset of tools from `tool_metadata._TOOLS` / tier names. See §2b.
3. **Other code-only lists**: Where lists in code overlap (e.g. SCRIPT_REGISTRY vs _TOOLS.path, TOOL_GUIDE vs _TOOLS), derive from the canonical source or document and keep in sync.
4. **Then docs**: Update DOCUMENTATION_GUIDE, DEVELOPMENT_TOOLS_GUIDE, AI_DEVELOPMENT_TOOLS_GUIDE, AI_LEGACY_COMPATIBILITY_GUIDE, etc., to reference canonical sources only (e.g. "command list: run_development_tools.py help" or "see COMMAND_GROUPS in `development_tools/shared/tool_metadata.py`").
5. **Tooling**: Add or extend checks where useful (e.g. COMMAND_GROUPS ⊆ COMMAND_REGISTRY; deprecation inventory path in config = jsons/DEPRECATION_INVENTORY.json). A **generic list-sync** mechanism (multiple list types across multiple docs, config-driven paths) is desired for the future; the previous paired-docs-only drift check was rolled back in favor of that design.

---

## 9a. Consolidation criteria and workflow

**When to consolidate**: (1) **Complete overlap** — list A is entirely a subset of list B; derive A from B. (2) **Same purpose, different scopes** — lists serve the same role (e.g. "docs to version-sync") but are split by category; consider deriving category lists from a single canonical list via path/pattern filters. (3) **Redundant maintenance** — two lists must be updated together; consolidate so only one needs updating.

**When not to consolidate**: (1) Different purposes (e.g. `paired_docs` = heading sync vs `fix_version_sync.docs` = version metadata). (2) Tool-specific formats (e.g. Ruff exclude vs Pyright exclude — different syntax). (3) Consolidation would obscure intent or make config harder to reason about.

**Workflow**: (1) Identify overlap (subset, superset, or conceptual equivalence). (2) Choose canonical source (usually the larger or more general list). (3) Derive the other list in code (filter, map, or extract). (4) Remove the redundant list from config/code. (5) Add a test or assertion that the derived list stays in sync. (6) Document in this file.

**Consolidation candidates** (see §4, §6, §10 for details):

| Candidate | Overlap type | Canonical source | Derived list(s) | Status |
|-----------|--------------|------------------|-----------------|--------|
| fix_version_sync category lists | Complete subset | `fix_version_sync.docs` | `communication_docs`, `core_docs`, `logs_docs`, `scripts_docs`, `tests_docs` | **Done** — derived from docs by path prefix; config override optional |
| fix_version_sync.exclude_patterns | Conceptual overlap | `get_exclusions("fix_version_sync", "development")` | — | **Done** — uses canonical exclusions; config key removed |
| file_patterns.exclude_patterns | Conceptual overlap | `exclusions.base_exclusions` | — | **Done** — removed from config; use exclusions.base_exclusions |
| scan_directories, core_modules, project_directories | Complete overlap | `constants.local_module_prefixes` | scan_directories (via get_scan_directories_derived), core_modules, project_directories | **Done** — derived in `development_tools/shared/constants.py`; config override optional (`paths.scan_directories`, `constants.project_directories`, `constants.core_modules` in development_tools_config.json) |
| **ruff_command** (unused_imports + static_analysis) | Redundant maintenance | `tool_commands.ruff_command` | `unused_imports.ruff_command`, `static_analysis.ruff_command` | **Done** — config.py `_get_ruff_command()`; both sections derive; per-section override optional |
| **test_markers.directory_to_marker** (identity map) | Redundant | `test_markers.categories` | `directory_to_marker` | **Done** — `get_test_markers_config()` derives from categories when absent; config override for non-identity |
| **historical_preserve_files** vs **tool_exclusions.documentation** | Partial overlap | — | — | **Resolved (no consolidation)** — historical_preserve = cleanup preserve (patterns); tool_exclusions.documentation = scan exclusions. Both include `development_docs/changelog_history/`; intentionally separate. |
| **legacy_documentation_files** vs **historical_preserve_files** | Conceptual overlap | — | — | **Resolved (no consolidation)** — legacy_documentation = path-drift exclusions (specific files); historical_preserve = cleanup preserve (patterns). Overlap in CHANGELOG_DETAIL, AI_CHANGELOG, changelog_history is acceptable; keep separate. |
| **fix_version_sync.docs** vs **constants.default_docs** | Partial overlap | Different purposes | — | **Assess (deferred)** — docs = version metadata; default_docs = analysis defaults. Overlap ~80%; different consumers. Optional future derivation if scope aligns. |
| **project.key_files** vs **project.core_system_files** | Partial overlap | `project.key_files` | `core_system_files` | **Assess (deferred)** — core_system_files falls back to key_files; overlap (core/config.py, run_mhm.py). core_system = version-sync subset; could derive from key_files via well-defined filter; low priority. |
| **TIER_TITLES** (tool_guide) | Redundant | `tool_metadata` | `tool_guide` | **Done** — TIER_TITLES moved to tool_metadata; tool_guide imports. |
| **Generated function patterns** (exclusion_utilities) | Multi-use | `development_tools/shared/constants.py` | exclusion_utilities | **Done** — AUTO_GENERATED_FILE_PATTERNS, EXACT_GENERATED_NAMES, GENERATED_NAME_PATTERNS in constants; exclusion_utilities imports. |

---

## 9b. Consolidation scan: standard_exclusions, constants, audit_tiers, development_tools_config

**Purpose**: Inventory lists across these four files; identify consolidation opportunities; ensure project-specific lists live in config and non–project-specific lists do not.

### Lists by file

| File | List(s) | Project-specific? | Canonical / action |
|------|---------|-------------------|--------------------|
| **development_tools/shared/standard_exclusions.py** | `_DEFAULT_BASE_EXCLUSIONS` | No (generic patterns) | Keep in code; config `exclusions.base_exclusions` overrides fully when present |
| | `BASE_EXCLUSIONS`, `TOOL_EXCLUSIONS`, `CONTEXT_EXCLUSIONS` | Loaded from config | Config canonical; code has fallbacks |
| | `GENERATED_FILES`, `BASE_EXCLUSION_SHORTLIST`, `HISTORICAL_PRESERVE_FILES` | Yes (project paths) | Config `exclusions.*` canonical |
| | `DOC_EXPORT_BASE_EXCLUDE_GLOBS` | No (generic doc-export globs) | Keep in code |
| | `DOC_SYNC_PLACEHOLDERS` | Optional (customizable per project) | Keep in code; add config override if projects need to customize |
| **development_tools/shared/constants.py** | `DEFAULT_DOCS`, `PAIRED_DOCS`, `LOCAL_MODULE_PREFIXES` | Yes | Config `constants.*` canonical |
| | `COMMON_FUNCTION_NAMES`, `COMMON_CLASS_NAMES` | **Yes** (MHM handlers, classes) | **Done** — config `constants.common_function_names`, `constants.common_class_names`; constants.py loads with fallback |
| | `THIRD_PARTY_LIBRARIES` | **Yes** (project deps: discord, PyQt, etc.) | **Done** — config `constants.third_party_libraries`; constants.py loads with fallback |
| | `COMMON_CODE_PATTERNS` | **Yes** (project module paths) | **Done** — config `constants.common_code_patterns`; constants.py loads with fallback |
| | `COMMON_VARIABLE_NAMES` | No (Python keywords / generic) | Stays in development_tools/shared/constants.py only; not in config |
| | `STANDARD_LIBRARY_*`, `SPECIAL_METHODS`, `CONTEXT_METHODS` | No | Keep in code |
| | `IGNORED_PATH_PATTERNS`, `COMMAND_PATTERNS`, path-drift constants | No | Keep in code |
| | `AUTO_GENERATED_FILE_PATTERNS`, `EXACT_GENERATED_NAMES`, `GENERATED_NAME_PATTERNS` | Borderline (PyQt-common) | Keep in code; config override optional |
| **development_tools/shared/audit_tiers.py** | `TIER1_TOOL_NAMES`, `TIER2_TOOL_NAMES`, `TIER3_TOOL_NAMES` | No (framework: dev-tools tier structure) | Keep in code; do **not** move to config |
| | `get_tier1_groups`, `get_tier2_groups`, `get_tier3_groups` | No | Derived from tier names; keep in code |
| **development_tools_config.json** | `quick_audit.audit_scripts` | Yes (which scripts run in quick audit) | Correct in config |
| | `exclusions.*`, `constants.*` (existing) | Yes | Correct in config |
| | `path_drift.legacy_documentation_files`, `data_freshness.known_deleted_files` | Yes | Correct in config |
| | `legacy_cleanup.legacy_patterns`, `domain_mapper.*` | Yes | Correct in config |

### Consolidation opportunities

| Opportunity | Overlap | Action |
|-------------|---------|--------|
| **constants common_* / third_party** | Project-specific values hardcoded in constants.py | **Done** — moved to config; constants.py loads with fallback |
| **exclusions.base_exclusions** vs `_DEFAULT_BASE_EXCLUSIONS` | Config replaces entirely; duplicates generic items | Optional: add merge strategy (config adds/removes from defaults) to reduce duplication; lower priority |
| **audit_tiers** group names vs flat TIER*_TOOL_NAMES | Groups are execution-order subsets | Could derive from tier names + grouping map; adds complexity; defer |
| **test_markers** (config vs constants defaults) | Config overrides; constants has generic defaults | Already correct; config can omit when matching defaults |

### Organization summary

- **Project-specific → config**: `common_function_names`, `common_class_names`, `third_party_libraries`, `common_code_patterns` (added under `constants`).
- **Non–project-specific → code**: `audit_tiers` tier tool names, `COMMON_VARIABLE_NAMES` (Python keywords), `DOC_EXPORT_BASE_EXCLUDE_GLOBS`, `STANDARD_LIBRARY_*`, `SPECIAL_METHODS`, `COMMAND_PATTERNS`, path-drift constants, etc. Remain in `development_tools/shared/standard_exclusions.py` / `development_tools/shared/constants.py` / `development_tools/shared/audit_tiers.py`.
- **Config-driven with code fallbacks**: All exclusion lists, `constants` docs/paired/local_module_prefixes, `test_markers`; code provides generic defaults when config is absent.

---

## 10. Documentation-analysis and path-drift lists (candidates for canonical sources)

These lists appear in `development_tools/docs/` (and a few in shared) and are duplicated or could be centralized in config, `development_tools/shared/constants.py`, or `development_tools/shared/standard_exclusions.py` so scripts pull from one place.

| List | Files (current) | Canonical location | Status |
|------|------------------|------------------------------|--------|
| **expected_overlaps** (section headings that may overlap across docs) | `development_tools/docs/analyze_documentation.py` | `development_tools/shared/constants.py` — `EXPECTED_OVERLAPS` | Done |
| **topic_keywords** (category → keywords for doc analysis) | `development_tools/docs/analyze_documentation.py` | config `documentation_analysis.topic_keywords` | Config-driven |
| **ignore_dirs** (directories to skip when scanning docs) | — | **Unified**: `should_exclude_file(rel_path, "documentation", "development")` → `BASE_EXCLUSIONS` in `development_tools/shared/standard_exclusions.py` | Done |
| **common_words** (path-drift: words that are generic in paths) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` — `DOC_COMMON_WORDS` | Done |
| **python_keywords** (path-drift: not valid in paths) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` — `PYTHON_KEYWORDS_PATH_DRIFT` | Done |
| **path file extensions** (allowed for path drift) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` — `PATH_DRIFT_VALID_EXTENSIONS` | Done |
| **path operator / char exclusions** (path-drift: not file paths) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` — `PATH_DRIFT_OPERATORS` | Done |
| **section_words** (path-drift: doc section terms) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` — `DOC_SECTION_WORDS` | Done |
| **example_phrases** | `development_tools/docs/analyze_path_drift.py`, `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` — `EXAMPLE_PHRASES` | Done |
| **example_markers** (regex) | `development_tools/docs/analyze_path_drift.py`, `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` — `EXAMPLE_MARKERS` | Done |
| **legacy_documentation_files** (paths to exclude from path-drift) | `development_tools/docs/analyze_path_drift.py` | **Config**: `path_drift.legacy_documentation_files` (project-specific) | Done |
| **path startswith prefixes** (not file paths in links) | `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` — `PATH_STARTSWITH_NON_FILE` | Done |
| **ASCII replacements / emoji & symbols** (Unicode → ASCII for docs) | `development_tools/docs/fix_documentation_ascii.py`, `development_tools/docs/analyze_ascii_compliance.py`, `development_tools/docs/fix_documentation_headings.py` | `development_tools/shared/constants.py` — `ASCII_REPLACEMENTS`, `EMOJI_SYMBOL_STRIP_PATTERN` | Done |

**Alignment note**: Most of the lists above live in `development_tools/shared/constants.py` (EXPECTED_OVERLAPS, DOC_COMMON_WORDS, PYTHON_KEYWORDS_PATH_DRIFT, DOC_SECTION_WORDS, EXAMPLE_PHRASES, EXAMPLE_MARKERS, PATH_STARTSWITH_NON_FILE, PATH_DRIFT_VALID_EXTENSIONS, PATH_DRIFT_OPERATORS, ASCII_REPLACEMENTS, EMOJI_SYMBOL_STRIP_PATTERN). **Project-specific** `legacy_documentation_files` is in `development_tools_config.json` → `path_drift.legacy_documentation_files`. `analyze_path_drift._DEFAULT_LEGACY_DOCUMENTATION_FILES` is fallback when config is missing. topic_keywords remains config-driven.

---

## 11. Other lists (config, functions, error_handling) – migration candidates

Focus: lists used in **2+ places** or with **project-specific** content. Many already come from `development_tools_config.json`; defaults live in `development_tools/config/config.py`.

| List | Location(s) | In 2+ places? | Project-specific? | Suggested canonical source |
|------|-------------|-----------------|-------------------|----------------------------|
| **config_functions** (analyze_config) | `development_tools/config/analyze_config.py` | No | Yes | **Config**: `analyze_config.expected_config_functions` in development_tools_config.json; defaults in config.py CONFIG_VALIDATOR. |
| **required_sections** (analyze_config) | `development_tools/config/analyze_config.py` | No | Yes | **Config**: `analyze_config.required_sections` in development_tools_config.json; defaults in config.py CONFIG_VALIDATOR. |
| **handler_keywords, test_keywords, critical_functions** | `development_tools/config/config.py` defaults | Yes (config + analyze_functions) | Partially | Already in config: `analyze_functions` in development_tools_config.json |
| **exception_base_classes, error_handler_functions, critical_function_keywords** | `development_tools/config/config.py` + `development_tools/error_handling/analyze_error_handling.py` | Yes | Yes | Already in config: `error_handling` in development_tools_config.json |
| **AUDIT_TIERS** (config.py) | `development_tools/config/config.py` | Overlaps `development_tools/shared/audit_tiers.py` | — | Tier tools canonical in `development_tools/shared/audit_tiers.py`; config.py default built from audit_tiers; external config can override |
| **sync_ruff_toml select/ignore** | `development_tools/config/sync_ruff_toml.py` | No | Partially | Config or keep in script (Ruff-specific) |
| **critical_function_keywords** (error_handling defaults) | `development_tools/error_handling/analyze_error_handling.py` | Same keys as config | Yes | Config already has `error_handling.critical_function_keywords`; script uses as default |
| **phase1_keywords** | `development_tools/error_handling/analyze_error_handling.py` | No | Partially | Could move to config `error_handling.phase1_keywords` |
| **special_methods** (exclude from error handling) | `development_tools/error_handling/analyze_error_handling.py` | Maybe (exclusion_utilities has similar) | No | `development_tools/shared/constants.py` or shared with exclusion_utilities |
| **file_io / network keyword lists** (717–718, 721–722, 783–799) | `development_tools/error_handling/analyze_error_handling.py` | Yes (repeated) | Partially | Derive from config `critical_function_keywords` where possible |
| **analyze_function_patterns** (entry_point_names, data_access_keywords, etc.) | `development_tools/functions/analyze_function_patterns.py` | Overlaps analyze_functions keywords | Partially | **Done** — config `analyze_function_patterns`; config.py defaults |
| **analyze_functions** keyword list (357–366) | `development_tools/functions/analyze_functions.py` | Yes (config has handler_keywords) | — | Already from config `analyze_functions.handler_keywords` |
| **fix_function_docstrings** special_method_docs, func_type list | `development_tools/functions/fix_function_docstrings.py` | No | No | `development_tools/shared/constants.py` if shared elsewhere |
| **generate_function_registry** descriptions, pattern_order, priority_order, trees | `development_tools/functions/generate_function_registry.py` | No | Yes (project structure) | Config or keep in script; large report-content lists |

**Summary**: `error_handling` and `analyze_functions` sections in development_tools_config.json are already the canonical source for many of these; scripts fall back to config.py defaults. **Done**: legacy_documentation_files → config; analyze_config → config; phase1_keywords → config; analyze_function_patterns entry_point_names, data_access_keywords, communication_keywords, decorator_names → config `analyze_function_patterns`. special_methods already in constants (analyze_error_handling imports from constants).

---

## 12. Lists that don't yet meet the principles

Evaluation against: (1) Single canonical source. (2) Project-specific → `development_tools_config.json`. (3) Non–project-specific, used in 2+ places → `development_tools/shared` (`development_tools/shared/common.py`, `development_tools/shared/constants.py`, `development_tools/shared/standard_exclusions.py`). (4) Single-use, non–project-specific → may stay in one file.

**Violation key**: **P** = project-specific but not in config; **S** = no single canonical source (duplicate or drift); **M** = multi-use non–project-specific but not in shared; **?** = optional / low priority. **Fixed** = addressed in code/config.

| List (or group) | Section | Violation | Issue | Suggested fix | Status |
|-----------------|---------|-----------|--------|----------------|--------|
| **SOURCE_TO_TEST_MAPPING**, **DOMAIN_DEPENDENCIES**, **keyword_map** (domain_mapper.py) | 7b | P | Project-specific test layout; hardcoded. | Move to config `domain_mapper` section. | **Fixed** — config `domain_mapper.source_to_test_mapping`, `domain_mapper.domain_dependencies`, `domain_mapper.keyword_map`; domain_mapper.py loads via `get_domain_mapper_config()`. |
| **Static check allowlists** (check_channel_loggers) | 7 | ? | Project-specific dirs/import paths. | Config `static_checks.channel_loggers`. | **Fixed** — excluded_dirs, allowed_logging_import_paths in config; LOG_METHODS and IGNORED_DIR_NAMES stay in code (generic). |
| **Doc-sync placeholders** (standard_exclusions.DOC_SYNC_PLACEHOLDERS) | 7 | ? | Hardcoded; could be project-specific. | Move to config only if projects need to customize. | Open (optional). |
| **SCRIPT_REGISTRY** (tool_name → path) | 2 | S | Duplicate of _TOOLS path data; doc says "should be derived from _TOOLS". | Derive SCRIPT_REGISTRY from `tool_metadata._TOOLS` (ToolInfo.path) so paths have one source. | **Fixed**: `get_script_registry()` in tool_metadata builds from _TOOLS. |
| **_CACHE_AWARE_TOOLS** | 2 | S / M | Subset of tool names lives in audit_orchestration; could drift from _TOOLS. | Move to `tool_metadata` or config; consumers import from there. | **Fixed**: Now `tool_metadata.CACHE_AWARE_TOOLS`; audit_orchestration imports it. |
| **Trigger keywords** (guard) vs **DEPRECATION_INVENTORY global_sweep_keywords** | 3 | S | Two sources for "keywords that trigger guard"; overlap. | Config canonical for guard; inventory global_sweep_keywords used for sweep scope elsewhere. | **Fixed**: Guard uses config `legacy_cleanup.deprecation_inventory_sync_guard.trigger_keywords` only; doc in code. |
| **DOCUMENTATION_GUIDE §4.1** (paired doc list in prose) | 4 | S | Doc list can drift from config `constants.paired_docs`. | Doc points to config only, or add tooling to sync from config. | **Fixed**: §4.1 now states config is canonical; list is human-readable summary; doc-sync validates. |
| **Pyright exclude** (root + development_tools/config) | 5 | S | Two independent exclude arrays; no single generator. | Document as two canonical sources; document when adding new exclusions to both. | **Fixed**: Intentionally two sources (root = project; dev-tools = subproject); no sync needed. |
| **TOOL_GUIDE** (tool_guide.py) | 7 | S | Was keyed by script filename and drifted from the canonical `_TOOLS` catalog. | Build tool guidance from `tool_metadata._TOOLS` and derive the filename/basename compat map from canonical paths. | **Fixed**: guidance is derived from `tool_metadata._TOOLS` with a derived basename compat map; import-time collision guard prevents ambiguous filename resolution. |
| **KNOWN_DELETED_FILES** (data_freshness_audit) | 7 | P | Project-specific; not in config. | Move to `development_tools_config.json` (e.g. `data_freshness.known_deleted_files`). | **Fixed**: Config `data_freshness.known_deleted_files`; data_freshness_audit uses `get_data_freshness_config()`. |
| **Output storage `domains`** (output_storage.py) | 7 | S | Duplicate of unique domain names from EXPECTED_TOOLS. | Derive `domains` from `EXPECTED_TOOLS`. | **Fixed**: `aggregate_all_tool_results()` derives domains from `EXPECTED_TOOLS` (lazy import). |
| **Doc snapshot BASE_EXCLUDE_GLOBS** (development_tools/shared/export_docs_snapshot.py) | 7 | M | Overlaps conceptually with base exclusions; hardcoded. | Move to standard_exclusions. | **Fixed**: Now `standard_exclusions.DOC_EXPORT_BASE_EXCLUDE_GLOBS`; export_docs_snapshot imports it. |
| **EXPECTED_TOOLS** vs **output_storage.domains** | 2, 7 | S | Domain set duplicated. | Derive domains from EXPECTED_TOOLS. | **Fixed**: see Output storage row. |
| **AUDIT_TIERS** (config.py) vs **audit_tiers** (module) | 11 | S | config.py has tier structure that overlaps `development_tools/shared/audit_tiers.py`. | Treat audit_tiers module as canonical; config.py thin wrapper or remove. | **Fixed**: Default `AUDIT_TIERS` built from `audit_tiers.TIER1_TOOL_NAMES` / `get_expected_tools_for_tier()`; external config can override. |
| **phase1_keywords** (analyze_error_handling) | 11 | P | Project-specific or shared; not in config. | Move to config `error_handling.phase1_keywords` if project-specific; else constants. | **Fixed**: Config `error_handling.phase1_keywords`; analyzer loads from config with fallback. |
| **TIER_TITLES** (tool_guide.py) | 7 | ? | Small; low drift. Could live in tool_metadata or config. | Move to tool_metadata. | **Fixed**: Now `tool_metadata.TIER_TITLES`; tool_guide imports it. |
| **Generated function patterns** (exclusion_utilities) | 7 | M | Hardcoded in exclusion_utilities; multi-use for is_generated_file/is_generated_function. | Move to `development_tools/shared/constants.py`. | **Fixed**: Now `constants.AUTO_GENERATED_FILE_PATTERNS`, `EXACT_GENERATED_NAMES`, `GENERATED_NAME_PATTERNS`; exclusion_utilities imports. |

**Summary**: **Fixed (this and previous pass)**: Output storage domains from EXPECTED_TOOLS; KNOWN_DELETED_FILES → config; _CACHE_AWARE_TOOLS → tool_metadata; trigger_keywords = config for guard; AUDIT_TIERS default from `development_tools/shared/audit_tiers.py`; phase1_keywords → config; DOCUMENTATION_GUIDE §4.1 config-canonical; file_patterns.exclude_patterns removed; BASE_EXCLUDE_GLOBS → standard_exclusions; Pyright documented as intentionally two canonical sources; TIER_TITLES → tool_metadata; generated function patterns (AUTO_GENERATED_FILE_PATTERNS, EXACT_GENERATED_NAMES, GENERATED_NAME_PATTERNS) → constants. **Still open**: optional items (doc-sync placeholders, static check allowlists). **Fixed (this pass)**: domain_mapper lists → config.

---

## 13. Config list inventory (consolidation scan)

Config keys that are list-like or array-valued. Use for consolidation audits.

| Config path | Purpose | Overlap / notes |
|-------------|---------|-----------------|
| `project.key_files` | Entry points, important files | Overlaps `core_system_files`; see §9a |
| `project.core_system_files` | Version-sync / core checks | Falls back to key_files; subset |
| `fix_version_sync.ai_docs` | AI docs for version sync | Subset of docs; derived from docs by prefix (done) |
| `fix_version_sync.docs` | Non-AI docs for version sync | Overlaps constants.default_docs; different purpose |
| `fix_version_sync.cursor_rules` | Cursor rules for version sync | Distinct |
| `constants.default_docs` | Default docs for analysis | Overlaps fix_version_sync.docs; see §9a |
| `constants.paired_docs` | Human→AI doc mapping | Distinct (heading sync) |
| `path_drift.legacy_documentation_files` | Path-drift exclusions | Overlaps historical_preserve conceptually |
| `exclusions.tool_exclusions.documentation` | Tool-specific doc exclusions | Overlaps historical_preserve (changelog_history/) |
| `exclusions.historical_preserve_files` | Preserve during cleanup | Overlaps tool_exclusions.documentation |
| `exclusions.generated_files` | Generated file patterns | Distinct |
| `test_markers.categories` | Pytest category names | directory_to_marker can derive when identity |
| `test_markers.directory_to_marker` | Dir→marker map | Derived from categories when absent; override for non-identity |
| `tool_commands.ruff_command` | Shared ruff command | Canonical; unused_imports and static_analysis derive from here |
| `unused_imports.ruff_command` | Override (optional) | Per-section override |
| `static_analysis.ruff_command` | Override (optional) | Per-section override |
| `coverage.pytest_command` | Pytest command | Distinct (different tool) |

---

## 14. Quick reference

| I need to… | Canonical source |
|------------|------------------|
| Add a tool | `development_tools/shared/tool_metadata.py` — `_TOOLS`; then update `EXPECTED_TOOLS` in `development_tools/shared/verify_tool_storage.py` if it uses storage |
| Add a CLI command | `development_tools/shared/cli_interface.py` — `COMMAND_REGISTRY`; add to `COMMAND_GROUPS` in `development_tools/shared/tool_metadata.py` |
| Add an exclusion (Ruff, scans) | `development_tools_config.json` — `exclusions.base_exclusions` or `development_tools/shared/standard_exclusions.py`; regenerate ruff.toml via `python -m development_tools.config.sync_ruff_toml` |
| Add a paired doc | `development_tools_config.json` — `constants.paired_docs`; update DOCUMENTATION_GUIDE.md §4.1 |
| Add a doc to version-sync | `development_tools_config.json` — `fix_version_sync.docs` or `fix_version_sync.ai_docs` |
| Add a deprecation/legacy item | `development_tools/config/jsons/DEPRECATION_INVENTORY.json`; config `legacy_cleanup.legacy_patterns` for patterns |
| Add a test marker | `development_tools_config.json` — `test_markers.categories`; `pytest.ini` for pytest behavior |
| Add a path-drift exclusion | `development_tools_config.json` — `path_drift.legacy_documentation_files` |
| Change tier display labels | `development_tools/shared/tool_metadata.py` — `TIER_TITLES` |
| Change generated function patterns (PyQt, etc.) | `development_tools/shared/constants.py` — `AUTO_GENERATED_FILE_PATTERNS`, `EXACT_GENERATED_NAMES`, `GENERATED_NAME_PATTERNS` |

---

## 15. Next action steps (list relocation)

Planned relocations and changes, with status.

| # | Item | Action | Status |
|---|------|--------|--------|
| 1 | **Doc-sync placeholders** | Leave in `development_tools/shared/standard_exclusions.py`; no action needed | **Accepted** — fine where it is |
| 2 | **Static check allowlists** (check_channel_loggers) | `EXCLUDED_DIRS` and `ALLOWED_LOGGING_IMPORT_PATHS` → config `static_checks.channel_loggers`; use `should_exclude_file` for directory exclusion | **Done** |
| 2a | | `LOG_METHODS` and `IGNORED_DIR_NAMES` stay in code (not project-specific) | — |
| 2b | | Directory exclusion: use shared `should_exclude_file`; excluded_dirs from config | — |
| 3 | **Error-handling file_io / network keyword lists** | Derive from config `error_handling.critical_function_keywords` and `phase1_keywords` | **Done** |
| 4 | **generate_function_registry report lists** | Move `descriptions`, `priority_order`, `trees` → config `analyze_function_registry` | **Done** |
| 4a | | `pattern_order` stays in code (less project-specific); not a priority to move | — |
| 5 | **fix_function_docstrings special_method_docs** | Single-use (only in fix_function_docstrings.py); no shared consumers | **Accepted** — no relocation |
| 6 | **analyze_function_patterns patterns** | `entry_point_names`, `data_access_keywords`, `communication_keywords`, `decorator_names` → config `analyze_function_patterns`; config.py defaults, projects override | **Done** |
| 7 | **exclusions.base_exclusions merge strategy** | Additive/merge: `base_exclusions_additions`, `base_exclusions_removals`; merge with defaults or base_exclusions | **Done** |

