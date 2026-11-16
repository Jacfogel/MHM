# MHM development-tools configuration

MHM keeps its paired-document mappings, backup policy, and deprecation inventory here. Run `python development_tools/run_development_tools.py audit` from the MHM root. The shared CLI reads MHM's config path from `[tool.development-tools]` in [pyproject.toml](../../pyproject.toml). A local config at `development_tools/config/development_tools_config.json` takes precedence over that declaration. Pass `--config-path` or set `DEVTOOLS_REPORT_CONFIG` to select a different file. The selected configuration supplies the deprecation inventory path through `legacy_cleanup.deprecation_inventory_file`.

If you use a local MHM override, retain `legacy_cleanup.deprecation_inventory_file` from the tracked configuration to keep using MHM's inventory. For direct calls to individual tools, set `DEVTOOLS_REPORT_CONFIG` to the desired configuration before running the script.

MHM uses the runtime from the [published branch](https://github.com/Jacfogel/development-tools/tree/published), currently [revision 05aa479](https://github.com/Jacfogel/development-tools/commit/05aa479). The [development branch](https://github.com/Jacfogel/development-tools/tree/development) owns the tools tests and synthetic fixtures. MHM keeps its generated reports and tests for the MHM integration in this repository.

To bring in a reviewed published revision, use a clean branch and run `git subtree pull --prefix=development_tools https://github.com/Jacfogel/development-tools.git published`. Run MHM's configuration and host checks afterward. For work on the tools themselves, follow the [development-tools testing guide](https://github.com/Jacfogel/development-tools/blob/development/tests/development_tools/DEVELOPMENT_TOOLS_TESTING_GUIDE.md).
