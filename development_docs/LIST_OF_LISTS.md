# List of Lists — Canonical Sources, Uses, and Alignment


> **File**: `development_docs/LIST_OF_LISTS.md`
**Purpose**: Single reference for list-like data (arrays, mappings, enumerated sets) in code and config. Align code/config first, then align docs to canonical lists.

**Audience**: Maintainers, AI collaborators.  
**Last updated**: 2026-03-17

**Principles**: (1) Every list has a single canonical source. (2) **Project-specific** lists → `development_tools_config.json`. **Non–project-specific** lists that are used in more than one place → `development_tools/shared/common.py`, `development_tools/shared/constants.py`, or `development_tools/shared/standard_exclusions.py` as appropriate. Single-use, non–project-specific lists can stay in the single file that uses them.

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
| **Tool metadata (name, path, tier, trust, description)** | `development_tools/shared/tool_metadata.py` — `_TOOLS` dict (key = tool name, value = `ToolInfo`)                                                   | Tier/audit logic, help, cache discovery, tool_guide; tool_wrappers call `run_<name>` | **Config**: `quick_audit.audit_scripts` is a *subset* of script names (e.g. `analyze_documentation.py`) — different naming (filename vs tool name). **Docs**: DEVELOPMENT_TOOLS_GUIDE.md, AI_DEVELOPMENT_TOOLS_GUIDE.md have tool tables. **verify_tool_storage.py**: `EXPECTED_TOOLS` — subset of tool names → storage domain; must stay subset of _TOOLS keys. |
| **Tools that use standardized storage**                  | `development_tools/shared/verify_tool_storage.py` — `EXPECTED_TOOLS` (dict: tool_name → domain)                                                     | Storage verification script; policy consistency tests                                | Must be subset of `tool_metadata._TOOLS`. No other canonical list; align by ensuring every EXPECTED_TOOLS key exists in _TOOLS.                                                                                                                                                                                                                                  |
| **Quick-audit script list**                              | `development_tools/config/development_tools_config.json` — `quick_audit.audit_scripts` (array of script filenames, e.g. `analyze_documentation.py`) | Quick audit mode (which scripts to run)                                              | Overlaps in *concept* with tool catalog; naming is script filename, not tool name (e.g. `analyze_documentation_sync` in _TOOLS vs `analyze_documentation_sync.py` in config). Keep config as canonical for "what runs in quick audit"; document mapping to _TOOLS if needed.                                                                                     |


| **Script name → path (run_script)** | `development_tools/shared/service/tool_wrappers.py` — `SCRIPT_REGISTRY` (dict: tool_name → rel path under development_tools/) | `run_script()`, tool_guide.run_tool_with_guidance fallback | Overlaps with `tool_metadata._TOOLS` (each ToolInfo has `.path`). Should be derived from _TOOLS or vice versa to avoid drift. |
| **Cache-aware tools (invalidation)** | `development_tools/shared/service/audit_orchestration.py` — `_CACHE_AWARE_TOOLS` (set of tool names) | Cache invalidation when those tools run | Subset of tool names; should stay in sync with _TOOLS. Consider moving to config or tool_metadata. |

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
| **Version-sync file lists (ai_docs, docs, etc.)** | `development_tools_config.json` — `fix_version_sync.ai_docs`, `fix_version_sync.docs`, `cursor_rules`, …                                                                                                                      | `development_tools/docs/fix_version_sync.py` (scope for version/date updates) | Overlap: ai_docs paths can match AI-side paths in paired_docs. Document that paired_docs = "heading sync", version-sync lists = "version metadata"; optionally derive ai_docs from paired_docs or add overlap check. |


**Alignment note**: See AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4 §7.8. Align config and DOCUMENTATION_GUIDE §4.1 first (one canonical); then ensure docs that reference "paired doc list" point to that canonical source.

---

## 5. Exclusions and ignore lists


| What                                                | Canonical source                                                                                                                                                                                                                                                                                                                    | Uses                                                     | Other locations / overlap                                                                                            |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Ruff exclude patterns**                           | **Source of truth**: `development_tools/shared/standard_exclusions.py` (defaults) + `development_tools_config.json` — `exclusions.base_exclusions`, etc., merged via `get_exclusions()`. **Generated**: `.ruff.toml` (root), `development_tools/config/ruff.toml` — both generated by `development_tools/config/sync_ruff_toml.py`. | Ruff lint; sync script writes TOML                       | Two TOML files are outputs; do not edit by hand. Regenerate after changing standard_exclusions or config exclusions. |
| **Pyright exclude**                                 | Root `pyrightconfig.json` — `exclude` array. Also `development_tools/config/pyrightconfig.json` — `exclude` array.                                                                                                                                                                                                                  | Pyright type checking                                    | Two independent lists; no shared generator. Align manually or add a small script to diff/sync if desired.            |
| **.gitignore**                                      | `.gitignore` (line-based)                                                                                                                                                                                                                                                                                                           | Git                                                      | Conceptual overlap with Ruff/Pyright/pytest exclusions; different tool, no single canonical "ignore" list.           |
| **Pytest collect_ignore**                           | `pytest.ini` — `collect_ignore` (multi-line list)                                                                                                                                                                                                                                                                                   | Pytest collection                                        | Overlaps conceptually with test exclusions elsewhere; pytest.ini is canonical for pytest.                            |
| **Coverage omit patterns**                         | `development_tools/tests/coverage.ini`, `development_tools/tests/coverage_dev_tools.ini` — `omit` (multi-line globs)                                                                                                                                                                                                                 | Coverage.py (main project vs dev-tools coverage)         | Conceptual overlap with base exclusions; coverage.ini is canonical for each coverage run.                           |
| **Dev-tools exclusions (base, context, generated)** | `development_tools_config.json` — `exclusions.base_exclusions`, `exclusions.context_exclusions`, `exclusions.generated_files`, etc.                                                                                                                                                                                                 | `development_tools/shared/standard_exclusions.py` (via config); various analyzers | Feeds Ruff via sync; also used for scan roots, cache cleanup.                                                        |


**Alignment note**: For Ruff, only change standard_exclusions + config; never edit the two ruff.toml files by hand. For Pyright, either keep two configs and document, or add a sync step. Coverage omit lists are independent per file; align with base exclusions when changing project ignore policy.

---

## 6. Config and code constants (development_tools_config.json)


| What                                                                                                     | Canonical source                                                                                                                                                                                  | Uses                                                                                                                             | Other locations / overlap                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **default_docs, paired_docs, local_module_prefixes, project_directories, core_modules, test_markers, …** | `development_tools_config.json` — `constants`, `paths`, `fix_version_sync`, `analyze_functions`, `error_handling`, `documentation_analysis`, `test_markers`, `exclusions`, `legacy_cleanup`, etc. | `development_tools/shared/constants.py` (loads and exposes PAIRED_DOCS, DEFAULT_DOCS, etc.); config.py getters; individual tools | Many keys are list-valued. Code is consumer; config is canonical. Doc that references "e.g. paired_docs" should point to config (or to constants.py as the loader).               |
| **Test markers (categories, directory map, etc.)**                                                       | `development_tools_config.json` — `test_markers.categories`, `test_markers.transient_data_path_markers`, etc.                                                                                     | Dev-tools test marker analysis                                                                                                   | `pytest.ini` — `markers` (pytest's own list). Overlap in purpose; config = dev-tools analysis, pytest.ini = pytest behavior. Keep both; document that they serve different tools. |


---

## 7. Code-only lists in development_tools (align or pull from canonical)

These lists live only in code. Many should pull from config or a single code canonical source to avoid overlap and drift.

| What | File | Canonical / overlap | Notes |
|------|------|---------------------|--------|
| **Tool guide (usage, when_to_use, output_interpretation)** | `development_tools/shared/tool_guide.py` — `TOOL_GUIDE_BY_TOOL_NAME` (derived from `tool_metadata._TOOLS`) + `TOOL_GUIDE_BY_SCRIPT_BASENAME` (compat map derived from basenames) | Single canonical tool identity/path in `tool_metadata._TOOLS`; `tool_guide` only adds user-facing guidance fields via a small override map keyed by tool name. | Filename-based lookups remain supported via a derived basename compat layer; collisions are guarded (fail fast) during module import. |
| **Tier display titles** | `development_tools/shared/tool_guide.py` — `TIER_TITLES` (core/supporting/experimental → label) | Could live in tool_metadata or config. | Small; low drift risk. |
| **Test keywords (function-level)** | `development_tools/shared/exclusion_utilities.py` — `_DEFAULT_TEST_KEYWORDS`; `_get_test_keywords()` loads from config `analyze_functions.test_keywords` | Config is canonical when present. | Already pulls from config; defaults are fallback. |
| **Generated file patterns (function-level)** | `development_tools/shared/exclusion_utilities.py` — `auto_generated_file_patterns`, `exact_generated_names`, `generated_name_patterns` | Hardcoded. Could move to config (e.g. `exclusions.generated_function_patterns`). | Used by is_generated_file / is_generated_function. |
| **Special Python methods (exclude from undocumented / error-handling)** | `development_tools/shared/constants.py` — `SPECIAL_METHODS`, `CONTEXT_METHODS` (frozensets) | Single canonical source. | Used by `exclusion_utilities.is_special_python_method()` and `analyze_error_handling`; no longer duplicated. |
| **Base/context exclusions defaults** | `development_tools/shared/standard_exclusions.py` — `_DEFAULT_BASE_EXCLUSIONS`, `_DEFAULT_CONTEXT_EXCLUSIONS` | Loaded from config when available; defaults are fallback. | Already config-driven. |
| **Generated files list (file-level)** | `development_tools/shared/standard_exclusions.py` — `GENERATED_FILES`, `GENERATED_FILE_PATTERNS`, `ALL_GENERATED_FILES` | From config `exclusions.generated_files`. | Canonical for **file-level** generated paths/patterns; consumed by multiple tools. |
| **Base exclusion shortlist** | `development_tools/shared/standard_exclusions.py` — `BASE_EXCLUSION_SHORTLIST` | From config `exclusions.base_exclusion_shortlist`. | Used by sync_ruff_toml. |
| **Doc-sync placeholders** | `development_tools/shared/standard_exclusions.py` — `DOC_SYNC_PLACEHOLDERS` (dict path → placeholder text) | Hardcoded. | Could move to config if needed. |
| **Constants (stdlib, common names, patterns)** | `development_tools/shared/constants.py` — `STANDARD_LIBRARY_*`, `COMMON_FUNCTION_NAMES`, `COMMON_CLASS_NAMES`, `IGNORED_PATH_PATTERNS`, `COMMAND_PATTERNS`, `PATH_STARTSWITH_NON_FILE` (derived from `_NON_PATH_PREFIXES` + COMMAND_PATTERNS), `THIRD_PARTY_LIBRARIES`, `SPECIAL_METHODS`, `CONTEXT_METHODS`, `CORRUPTED_ARTIFACT_PATTERNS`, `TEMPLATE_PATTERNS`, `ASCII_COMPLIANCE_FILES`, `VERSION_SYNC_DIRECTORIES`, `TEST_CATEGORY_MARKERS`, `TEST_MARKER_*`, etc. | Some loaded from config (PAIRED_DOCS, DEFAULT_DOCS, …); many are code-only. Single definition of PATH_STARTSWITH_NON_FILE (no duplicate). | Path-drift and analysis; consider config for project-specific names. |
| **Generated AI/docs lists (version-sync)** | `development_tools/docs/fix_version_sync.py` — `GENERATED_AI_DOCS`, `GENERATED_DOCS` (from ALL_GENERATED_FILES), `AI_DOCS`, `CURSOR_RULES`, `CURSOR_COMMANDS`, `COMMUNICATION_DOCS`, `CORE_DOCS`, `LOGS_DOCS`, `SCRIPTS_DOCS`, `TESTS_DOCS`, `DOCUMENTATION_PATTERNS`, `EXCLUDE_PATTERNS`, `CORE_SYSTEM_FILES` | Config `fix_version_sync.*` + ALL_GENERATED_FILES. | Overlap with paired_docs; **version-sync** lists govern version/date updates, while **paired_docs** govern heading/content sync. They may overlap in paths but are conceptually distinct. |
| **Placeholder patterns (documentation)** | `development_tools/docs/analyze_documentation.py` — `PLACEHOLDER_PATTERNS` | Config `documentation_analysis.placeholder_patterns` in `development_tools_config.json`. | Canonical in config; analyze_documentation builds PLACEHOLDER_PATTERNS only from config (no hardcoded override). |
| **Required legacy pattern keys** | `development_tools/legacy/fix_legacy_references.py` — `REQUIRED_LEGACY_PATTERN_KEYS` | Fixed schema. | Low drift. |
| **Known deleted files** | `development_tools/shared/service/data_freshness_audit.py` — `KNOWN_DELETED_FILES` | Project-specific; could be config. | |
| **Static check allowlists/sets** | `development_tools/static_checks/check_channel_loggers.py` — `LOG_METHODS`, `EXCLUDED_DIRS`, `IGNORED_DIR_NAMES`, `ALLOWED_LOGGING_IMPORT_PATHS`; also `fallback_fragments` (path fragments to exclude, inside function) | Hardcoded for checker. | Could move to config if projects need to customize. |
| **Output storage domain directories** | `development_tools/shared/output_storage.py` — `domains` (list: functions, docs, error_handling, tests, imports, legacy, config, ai_work, reports, shared) | Used when collecting/listing tool result dirs; should match domain values in EXPECTED_TOOLS. | Keep in sync with `verify_tool_storage.EXPECTED_TOOLS` values (unique domain names). |
| **Tool/context exclusions and historical preserve** | `development_tools/shared/standard_exclusions.py` — `TOOL_EXCLUSIONS`, `CONTEXT_EXCLUSIONS`, `HISTORICAL_PRESERVE_FILES` | From config `exclusions.tool_exclusions`, `exclusions.context_exclusions`, `exclusions.historical_preserve_files`; defaults in module. | CONTEXT_EXCLUSIONS includes `recent_changes` (built from generated files). |
| **Doc snapshot / export discovery** | `development_tools/shared/export_docs_snapshot.py` — `DOC_EXTENSIONS`, `BASE_EXCLUDE_GLOBS` | Hardcoded. | Doc discovery and filtering; BASE_EXCLUDE_GLOBS overlaps conceptually with base exclusions. |
| **Package exports (analyze_package_exports)** | `development_tools/functions/analyze_package_exports.py` — `EXPORT_PATTERNS`, `EXPECTED_EXPORTS` | From config `analyze_package_exports.export_patterns`, `analyze_package_exports.expected_exports`. | Config is canonical. |
| **Config default schema (default keys)** | `development_tools/config/config.py` — `SCAN_DIRECTORIES`, `AI_COLLABORATION`, `FUNCTION_DISCOVERY`, `VALIDATION`, `ERROR_HANDLING`, `AUDIT`, `FILE_PATTERNS`, `QUICK_AUDIT`, `AUDIT_TIERS`, `VERSION_SYNC`, `DOCUMENTATION_ANALYSIS`, `CONFIG_VALIDATOR`, etc. | Default structure for development_tools_config.json; config file overrides at runtime. | Section 6 covers config keys; this row documents the code-side default dicts. |
| **Sync Ruff TOML header** | `development_tools/config/sync_ruff_toml.py` — `_HEADER` (multi-line string) | Generated TOML file header. | Not a list; template string only. |

---

## 7b. Test and coverage lists (development_tools/tests)

Lists used by test coverage, test markers, and dev-tools coverage cache. Project-specific structure; could move to config if shared across projects.

| What | File | Canonical / overlap | Notes |
|------|------|---------------------|--------|
| **Source → test dir/markers mapping** | `development_tools/tests/domain_mapper.py` — `SOURCE_TO_TEST_MAPPING` (domain → (test_dirs[], markers[])) | Hardcoded. | core, communication, ui, tasks, ai, user, notebook, development_tools. |
| **Domain dependencies** | `development_tools/tests/domain_mapper.py` — `DOMAIN_DEPENDENCIES` (domain → list of dependent domains) | Hardcoded. | Used for test ordering / dependency-aware runs. |
| **Domain keyword map** | `development_tools/tests/domain_mapper.py` — `keyword_map` (domain → keywords for matching) | Hardcoded inside method. | development_tools, communication, ai, tasks, ui, user, notebook, core. |
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
4. **Then docs**: Update DOCUMENTATION_GUIDE, DEVELOPMENT_TOOLS_GUIDE, AI_DEVELOPMENT_TOOLS_GUIDE, AI_LEGACY_COMPATIBILITY_GUIDE, etc., to reference canonical sources only (e.g. "command list: run_development_tools.py help" or "see COMMAND_GROUPS in tool_metadata.py").
5. **Tooling**: Add or extend checks where useful (e.g. COMMAND_GROUPS ⊆ COMMAND_REGISTRY; deprecation inventory path in config = jsons/DEPRECATION_INVENTORY.json). A **generic list-sync** mechanism (multiple list types across multiple docs, config-driven paths) is desired for the future; the previous paired-docs-only drift check was rolled back in favor of that design.

---

## 10. Documentation-analysis and path-drift lists (candidates for canonical sources)

These lists appear in `development_tools/docs/` (and a few in shared) and are duplicated or could be centralized in config, `development_tools/shared/constants.py`, or `development_tools/shared/standard_exclusions.py` so scripts pull from one place.

| List | Files (current) | Suggested canonical location | Notes |
|------|------------------|------------------------------|--------|
| **expected_overlaps** (section headings that may overlap across docs) | `development_tools/docs/analyze_documentation.py` | config `documentation_analysis.expected_overlaps` or `development_tools/shared/constants.py` | purpose, overview, introduction, summary, quick start, table of contents, see also, references, etc. |
| **topic_keywords** (category → keywords for doc analysis) | `development_tools/docs/analyze_documentation.py` | config `documentation_analysis.topic_keywords` (may already exist) | Setup & Installation, Development Workflow, Testing, Architecture, Troubleshooting, Code Quality, Project Structure |
| **ignore_dirs** (directories to skip when scanning docs) | — | **Unified**: both scripts use `should_exclude_file(rel_path, "documentation", "development")`, which uses `BASE_EXCLUSIONS` in `development_tools/shared/standard_exclusions.py`. No separate list; same as base exclusions. |
| **common_words** (path-drift: words that are generic in paths) | `development_tools/docs/analyze_path_drift.py` | config or `development_tools/shared/constants.py` | extraction, utility, module, package, function, class, data, config, documentation, test, etc. |
| **python_keywords** (path-drift: not valid in paths) | `development_tools/docs/analyze_path_drift.py` (two places) | `development_tools/shared/constants.py` or a single shared list | def, class, import, if, else, for, while, try, except, True, False, None, etc. |
| **path file extensions** (allowed for path drift) | `development_tools/docs/analyze_path_drift.py` | config or `development_tools/shared/constants.py` | .py, .md, .json, .txt, .yaml, .yml, .toml, .ini, .cfg |
| **path operator / char exclusions** (path-drift: not file paths) | `development_tools/docs/analyze_path_drift.py` | `development_tools/shared/constants.py` | ==, !=, <=, >=, +=, etc.; (, ), =, :, "def", "class" in path-like strings |
| **section_words** (path-drift: doc section terms) | `development_tools/docs/analyze_path_drift.py` | config or `development_tools/shared/constants.py` | overview, summary, introduction, background, recommendations, best practices, implementation, status, analysis, findings, conclusion, next steps, todo, etc. |
| **example_phrases** | `development_tools/docs/analyze_path_drift.py`, `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` or config | "for example", "e.g.", "example:", "examples:" |
| **example_markers** (regex) | `development_tools/docs/analyze_path_drift.py`, `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` | ^[OK], ^[AVOID], ^[GOOD], ^[BAD], ^[EXAMPLE] |
| **legacy_documentation_files** (paths to exclude from path-drift) | `development_tools/docs/analyze_path_drift.py` | **Config**: `development_tools_config.json` → `path_drift.legacy_documentation_files` (project-specific). Loader builds set with / and \\ variants. | LEGACY_REFERENCE_REPORT.md, CHANGELOG_DETAIL.md, AI_CHANGELOG.md |
| **path startswith prefixes** (not file paths in links) | `development_tools/docs/analyze_unconverted_links.py` | `development_tools/shared/constants.py` | `PATH_STARTSWITH_NON_FILE` derived from a small non-path prefix tuple plus `COMMAND_PATTERNS` so command prefixes are defined once. |
| **ASCII replacements / emoji & symbols** (Unicode → ASCII for docs) | `development_tools/docs/fix_documentation_ascii.py`, `development_tools/docs/analyze_ascii_compliance.py`, `development_tools/docs/fix_documentation_headings.py` | **Single canonical**: `development_tools/shared/constants.py` (`ASCII_REPLACEMENTS`, `EMOJI_SYMBOL_STRIP_PATTERN`) | Smart quotes, dashes, arrows, ellipsis, math symbols, bullets, emojis, and spacing characters. `fix_documentation_ascii` and `analyze_ascii_compliance` use `ASCII_REPLACEMENTS`; `fix_documentation_headings` now uses `ASCII_REPLACEMENTS` plus `EMOJI_SYMBOL_STRIP_PATTERN` from constants (no local regex). |

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
| **file_patterns.exclude_patterns** | `development_tools/config/config.py` + development_tools_config.json | Yes | Partially | Config `file_patterns.exclude_patterns`; overlap with exclusions.base_exclusions |
| **AUDIT_TIERS** (config.py) | `development_tools/config/config.py` | Overlaps `development_tools/shared/audit_tiers.py` | — | Tier tools canonical in `development_tools/shared/audit_tiers.py`; config.py may be legacy |
| **sync_ruff_toml select/ignore** | `development_tools/config/sync_ruff_toml.py` | No | Partially | Config or keep in script (Ruff-specific) |
| **critical_function_keywords** (error_handling defaults) | `development_tools/error_handling/analyze_error_handling.py` | Same keys as config | Yes | Config already has `error_handling.critical_function_keywords`; script uses as default |
| **phase1_keywords** | `development_tools/error_handling/analyze_error_handling.py` | No | Partially | Could move to config `error_handling.phase1_keywords` |
| **special_methods** (exclude from error handling) | `development_tools/error_handling/analyze_error_handling.py` | Maybe (exclusion_utilities has similar) | No | constants.py or shared with exclusion_utilities |
| **file_io / network keyword lists** (717–718, 721–722, 783–799) | `development_tools/error_handling/analyze_error_handling.py` | Yes (repeated) | Partially | Derive from config `critical_function_keywords` where possible |
| **analyze_function_patterns** (patterns dict, singleton methods, entry point names) | `development_tools/functions/analyze_function_patterns.py` | Overlaps analyze_functions keywords | Partially | config `analyze_functions` or constants; unify with handler_keywords |
| **analyze_functions** keyword list (357–366) | `development_tools/functions/analyze_functions.py` | Yes (config has handler_keywords) | — | Already from config `analyze_functions.handler_keywords` |
| **fix_function_docstrings** special_method_docs, func_type list | `development_tools/functions/fix_function_docstrings.py` | No | No | constants.py if shared elsewhere |
| **generate_function_registry** descriptions, pattern_order, priority_order, trees | `development_tools/functions/generate_function_registry.py` | No | Yes (project structure) | Config or keep in script; large report-content lists |

**Summary**: `error_handling` and `analyze_functions` sections in development_tools_config.json are already the canonical source for many of these; scripts fall back to config.py defaults. **Done**: (1) legacy_documentation_files → config `path_drift.legacy_documentation_files`; (2) analyze_config expected_config_functions + required_sections → config `analyze_config` (with defaults in config.py CONFIG_VALIDATOR). Next candidates: error_handling special_methods → constants if unified with exclusion_utilities; phase1_keywords → config.

---

## 12. Lists that don't yet meet the principles

Evaluation against: (1) Single canonical source. (2) Project-specific → `development_tools_config.json`. (3) Non–project-specific, used in 2+ places → `development_tools/shared` (common.py, constants.py, standard_exclusions.py). (4) Single-use, non–project-specific → may stay in one file.

**Violation key**: **P** = project-specific but not in config; **S** = no single canonical source (duplicate or drift); **M** = multi-use non–project-specific but not in shared; **?** = optional / low priority. **Fixed** = addressed in code/config.

| List (or group) | Section | Violation | Issue | Suggested fix | Status |
|-----------------|---------|-----------|--------|----------------|--------|
| **SCRIPT_REGISTRY** (tool_name → path) | 2 | S | Duplicate of _TOOLS path data; doc says "should be derived from _TOOLS". | Derive SCRIPT_REGISTRY from `tool_metadata._TOOLS` (ToolInfo.path) so paths have one source. | **Already derived**: `get_script_registry()` in tool_metadata builds from _TOOLS. |
| **_CACHE_AWARE_TOOLS** | 2 | S / M | Subset of tool names lives in audit_orchestration; could drift from _TOOLS. | Move to `tool_metadata` or config; consumers import from there. | **Fixed**: Now `tool_metadata.CACHE_AWARE_TOOLS`; audit_orchestration imports it. |
| **Trigger keywords** (guard) vs **DEPRECATION_INVENTORY global_sweep_keywords** | 3 | S | Two sources for "keywords that trigger guard"; overlap. | Config canonical for guard; inventory global_sweep_keywords used for sweep scope elsewhere. | **Fixed**: Guard uses config `legacy_cleanup.deprecation_inventory_sync_guard.trigger_keywords` only; doc in code. |
| **DOCUMENTATION_GUIDE §4.1** (paired doc list in prose) | 4 | S | Doc list can drift from config `constants.paired_docs`. | Doc points to config only, or add tooling to sync from config. | Open. |
| **Pyright exclude** (root + development_tools/config) | 5 | S | Two independent exclude arrays; no single generator. | Document as two canonical sources per tool, or add a sync script. | Open. |
| **TOOL_GUIDE** (tool_guide.py) | 7 | S | Was keyed by script filename and drifted from the canonical `_TOOLS` catalog. | Build tool guidance from `tool_metadata._TOOLS` and derive the filename/basename compat map from canonical paths. | **Fixed**: guidance is derived from `tool_metadata._TOOLS` with a derived basename compat map; import-time collision guard prevents ambiguous filename resolution. |
| **KNOWN_DELETED_FILES** (data_freshness_audit) | 7 | P | Project-specific; not in config. | Move to `development_tools_config.json` (e.g. `data_freshness.known_deleted_files`). | **Fixed**: Config `data_freshness.known_deleted_files`; data_freshness_audit uses `get_data_freshness_config()`. |
| **Output storage `domains`** (output_storage.py) | 7 | S | Duplicate of unique domain names from EXPECTED_TOOLS. | Derive `domains` from `EXPECTED_TOOLS`. | **Fixed**: `aggregate_all_tool_results()` derives domains from `EXPECTED_TOOLS` (lazy import). |
| **Doc snapshot BASE_EXCLUDE_GLOBS** (export_docs_snapshot.py) | 7 | M | Overlaps conceptually with base exclusions; hardcoded. | If used elsewhere, move to standard_exclusions or constants; else leave as single-use. | Open (optional). |
| **SOURCE_TO_TEST_MAPPING**, **DOMAIN_DEPENDENCIES**, **keyword_map** (domain_mapper.py) | 7b | P | Project-specific test layout; hardcoded. | Optionally move to config if projects need to customize. | Open (optional). |
| **EXPECTED_TOOLS** vs **output_storage.domains** | 2, 7 | S | Domain set duplicated. | Derive domains from EXPECTED_TOOLS. | **Fixed**: see Output storage row. |
| **AUDIT_TIERS** (config.py) vs **audit_tiers** (module) | 11 | S | config.py has tier structure that overlaps `development_tools/shared/audit_tiers.py`. | Treat audit_tiers module as canonical; config.py thin wrapper or remove. | **Fixed**: Default `AUDIT_TIERS` built from `audit_tiers.TIER1_TOOL_NAMES` / `get_expected_tools_for_tier()`; external config can override. |
| **phase1_keywords** (analyze_error_handling) | 11 | P | Project-specific or shared; not in config. | Move to config `error_handling.phase1_keywords` if project-specific; else constants. | **Fixed**: Config `error_handling.phase1_keywords`; analyzer loads from config with fallback. |
| **Static check allowlists** (check_channel_loggers) | 7 | ? | Single-use; if projects need to customize, not in config. | Leave as-is until needed; then add config keys. | Open (optional). |
| **Doc-sync placeholders** (standard_exclusions.DOC_SYNC_PLACEHOLDERS) | 7 | ? | Hardcoded; could be project-specific. | Move to config only if projects need to customize. | Open (optional). |
| **TIER_TITLES** (tool_guide.py) | 7 | ? | Small; low drift. Could live in tool_metadata or config. | Optional: move to tool_metadata or config. | Open (optional). |

**Summary**: **Fixed (this and previous pass)**: Output storage domains from EXPECTED_TOOLS; KNOWN_DELETED_FILES → config; _CACHE_AWARE_TOOLS → tool_metadata; trigger_keywords = config for guard; AUDIT_TIERS default from `development_tools/shared/audit_tiers.py`; phase1_keywords → config. **Still open**: DOCUMENTATION_GUIDE §4.1; Pyright; optional items.

