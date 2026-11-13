# MHM development-tools configuration

MHM keeps its paired-document mappings, backup policy, and deprecation inventory here. A local configuration at `development_tools/config/development_tools_config.json` takes precedence.

The `development_tools/` subtree is pinned to [upstream commit `9a7dd97c`](https://github.com/Jacfogel/development-tools/commit/9a7dd97c1dae2b3496295d2b55e31bc65c74de9e). MHM keeps its generated reports in the same directory for existing consumers. To bring in a reviewed upstream revision, run `git subtree pull --prefix=development_tools https://github.com/Jacfogel/development-tools.git main` on a clean branch, then run the development-tools tests.
