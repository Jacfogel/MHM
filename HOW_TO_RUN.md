# How to Run MHM


> **File**: `HOW_TO_RUN.md`
> **Audience**: New users and developers setting up the project  
> **Purpose**: Step-by-step setup and launch instructions  
> **Style**: Clear, beginner-friendly, troubleshooting-focused

> **See [README.md](README.md) for complete navigation and project overview.**

## 1. Quick Start (Recommended)

**Important**: Always use a virtual environment to keep your system Python clean and avoid dependency conflicts.

### 1.1. Step 1: Set up Virtual Environment
```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 1.2. Step 2: Install Dependencies
```powershell
# Make sure your virtual environment is activated (you should see (.venv) in your prompt)
pip install -r requirements.txt
```

### 1.3. Step 3: Install the Project in Editable Mode
Editable installation keeps the `core`, `communication`, `ui`, and `tasks` packages on the
Python path so you never need manual `sys.path` tweaks.

```powershell
pip install -e .

# If you want the optional UI dependencies in one step
pip install -e .[ui]
```

### 1.4. Step 4: Configure Environment (Optional)
The system uses sensible defaults, but you can customize settings in `.env`.

For the canonical list of settings, what they do, and common failure modes, see:
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)

Quick setup:
```powershell
# Copy the example configuration
Copy-Item .env.example .env
# Edit .env with your preferred settings
```

**Note**: The `.env` file is in `.cursorignore` for security (contains API keys and passwords).

### 1.5. Step 5: Launch the Application
```powershell
# For human users (UI interface)
python run_mhm.py

# For AI collaborators (headless service)
python run_headless_service.py start
```
- `run_mhm.py` opens the admin panel so you can manage users and start the background service
- `run_headless_service.py` launches the service directly for AI collaborators

## 2. Alternative Commands

Once your virtual environment is set up and activated:
```powershell
python core/service.py  # run service only (no UI)
python ui/ui_app_qt.py     # admin panel only (PySide6/Qt)
```

## 3. Command Reference (Discord and Chat)

These commands work as Discord slash commands (`/command`), bang commands (`!command`), or plain text phrases. The mapped text shows what the assistant understands if you prefer to type the words instead of the slash command.

| Command | Slash / Bang | Mapped text (what the assistant hears) | What it does |
| --- | --- | --- | --- |
| Start | `/start`, `!start` | `start` | Sends the welcome/setup message. |
| Tasks | `/tasks`, `!tasks` | `show my tasks` | Lists your current tasks. |
| Profile | `/profile`, `!profile` | `show profile` | Shows your saved profile details. |
| Schedule | `/schedule`, `!schedule` | `show schedule` | Shows your saved schedules. |
| Messages | `/messages`, `!messages` | `show messages` | Shows your saved messages. |
| Analytics | `/analytics`, `!analytics` | `show analytics` | Shows wellness analytics and insights. |
| Status | `/status`, `!status` | `status` | Shows system/user status. |
| Help | `/help`, `!help` | `help` | Shows help and examples. |
| Check-in | `/checkin`, `!checkin` | `start checkin` | Starts a check-in flow. |
| Restart check-in | `/restart`, `!restart` | `restart checkin` | Restarts an in-progress check-in. |
| Clear flows | `/clear`, `!clear` | `clear flows` | Clears stuck conversation flows. |
| Cancel | `/cancel`, `!cancel` | `/cancel` | Cancels the current flow immediately. |

**Notes**
- Slash and bang commands are equivalent; use whichever is more convenient.
- If you forget the exact command, typing the mapped text (for example, "show my tasks") works the same way.
- Check-in related commands (`/checkin`, `/restart`, `/clear`, `/cancel`) operate on the conversation flow system.

## 4. Alternative Launch Methods

You can also run individual components directly if needed:

## 5. Important Notes

- **Always activate your virtual environment** before running the app

### 5.1. Development tools and full audit (optional)

If you run the development tools full audit on this or another PC:

- **Dependencies**: `pip install -r requirements.txt` installs everything needed, including `pytest-cov` for coverage. No extra steps are required.
- **First run**: The backup health check reports "no backups" (skipped) until you create backups via the app; that is normal on a fresh install and does not fail the audit.
- **Commands**: `python development_tools/run_development_tools.py audit --full` runs the full Tier 3 audit (tests + coverage + reports). See [development_tools/DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md) for details.

- **Tier 3 freshness (coverage / pytest rows in AI_STATUS)**: A default `audit --full` refreshes full-repo coverage and Tier 3 test outcomes. If **AI_STATUS** still shows `cache_only_precheck` or stale numbers, run again with `--clear-cache` to bypass Tier 3 caches (see [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) nuance index). To refresh **development_tools-only** coverage and DEV_TOOLS_* reports without re-running the full product test track, use `python development_tools/run_development_tools.py audit --full --dev-tools-only`.

#### 5.1.1. Choosing an audit tier (time vs coverage)

Pick the **smallest** command that answers your question; full Tier 3 can exceed wall-clock ten minutes when pytest + coverage dominate.

| Goal | Command |
|------|---------|
| Fast health signal (Tier 1) | `python development_tools/run_development_tools.py audit --quick` |
| Standard checks, no pytest/coverage (Tier 1 + 2) | `python development_tools/run_development_tools.py audit` |
| Full evidence including tests and coverage (Tier 3) | `python development_tools/run_development_tools.py audit --full` |
| Tier 3 but only dev-tools tests/coverage + scoped DEV_TOOLS_* reports | `python development_tools/run_development_tools.py audit --full --dev-tools-only` |
| Skip pip-audit subprocess (offline / CI) | Set environment variable `MHM_PIP_AUDIT_SKIP` (see [development_tools/DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md)) |

**Deferred (not default)**: Moving Bandit or pip-audit into Tier 1 (`audit --quick`) would make quick audits slower without addressing the main cost (pytest + coverage); see [development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) Section 5.4 - 4.1.

#### 5.1.2. Where full-audit time goes (baseline snapshot)

After a full Tier 3 run, see [development_tools/reports/scopes/full/jsons/tool_timings.json](development_tools/reports/scopes/full/jsons/tool_timings.json) for per-tool seconds. A representative snapshot (2026-04-17): **`run_test_coverage` ~473s** (~76% of summed tool durations); next largest single tools **`analyze_pyright` ~47s**, **`analyze_bandit` ~20s**, **`analyze_documentation_sync` ~12s**, **`analyze_pip_audit` ~8.6s**, **`analyze_legacy_references` ~7.6s**. Re-run `audit --full` to refresh; numbers are machine-specific.

#### 5.1.3. Coverage domain cache (warm vs cold)

Domain and test-file caching for coverage is **on** by default (`run_test_coverage` / unified audit). To measure cache benefit on your machine, compare wall time with and without `--no-domain-cache` after a warm cache (PowerShell):

```powershell
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel --no-domain-cache }
Measure-Command { python development_tools/tests/run_test_coverage.py --dev-tools-only --no-parallel }
```

The first command is a **cold** run (no domain/test-file cache). The second omits `--no-domain-cache` so it can reuse caches from the first run on an **unchanged** tree; it should be faster when caches hit. Use `--no-domain-cache` or `audit` / `audit --full` with `--clear-cache` when you need a cold, authoritative pass.

#### 5.1.4. Pytest parallel workers

`run_test_coverage` defaults to **parallel** pytest (`pytest-xdist`) with `--workers` defaulting to **`auto`**. Override only if you are diagnosing flakes or hardware limits, e.g. `python development_tools/tests/run_test_coverage.py --workers 6`. Re-check [development_tools/reports/scopes/full/jsons/tool_timings.json](development_tools/reports/scopes/full/jsons/tool_timings.json) after changes.

#### 5.1.5. Static checks (Ruff, Pyright, Bandit) and cache

Ruff, Pyright, and Bandit use **per-shard fragment caches** on disk (see [`development_tools/shared/static_analysis_shard_cache.py`](development_tools/shared/static_analysis_shard_cache.py)): each configured path shard has a Python-only source signature; a **static-check config digest** over `STATIC_CHECK_CONFIG_RELATIVE_PATHS` in [`development_tools/shared/cache_dependency_paths.py`](development_tools/shared/cache_dependency_paths.py) busts all shards when any listed config changes. The analyzer subprocess still runs only for **missed** shards; merged JSON is written as the tool result. Sharded Pyright may omit some cross-package diagnostics versus a single full-project run; use periodic full Pyright (e.g. `pyright_shard_scan: false` in config, or CI) for strict parity. Pip-audit uses a requirements-hash cache and optional `MHM_PIP_AUDIT_SKIP`. See [development_tools/config/tool_cache_inventory.json](development_tools/config/tool_cache_inventory.json) for the full matrix.

#### 5.1.6. Completion log lines (`issues=`)

Lines like `Completed analyze_functions: PASS issues=493` in [`development_tools/reports/logs/main.log`](development_tools/reports/logs/main.log) mean the tool **finished successfully** (`PASS`); **`issues=`** is the tool's **`total_issues`** summary field (often a **metric total**, not "493 test failures"). Use [development_tools/AI_STATUS.md](development_tools/AI_STATUS.md), [development_tools/AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md), and [development_tools/CONSOLIDATED_REPORT.md](development_tools/CONSOLIDATED_REPORT.md) for actionable next steps. Per-tool semantics: [development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) Section 3.21.

- **Never install dependencies globally** - this can cause conflicts
- **If you see (.venv) in your terminal prompt**, you're using the virtual environment correctly
- **To deactivate the virtual environment**, simply type `deactivate`
- **Windows Python Processes**: On Windows, you may see two Python processes when running the app. One is your actual code, while the system Python is a harmless Windows artifact.

## 6. Troubleshooting

### 6.1. "Command not found" errors
Make sure your virtual environment is activated. You should see `(.venv)` at the beginning of your command prompt.

### 6.2. Import errors
Try reinstalling dependencies in your virtual environment:
```powershell
pip install -r requirements.txt
```

### 6.3. Environment variable issues
Ensure your `.env` file (if used) is correctly configured and that you restarted the app after changes.

### 6.4. Python version problems
MHM expects a reasonably recent Python 3 version (for example 3.11). If you see syntax errors on valid code, check your Python version:
```powershell
python --version
```

### 6.5. Development tools audit fails with "unrecognized arguments: --cov"
The full audit needs `pytest-cov` for coverage. Install or refresh dependencies:
```powershell
pip install -r requirements.txt
```
Then run `python development_tools/run_development_tools.py audit --full` again.

### 6.6. Virtual environment not activating
If `.\.venv\Scripts\Activate.ps1` fails:
- Make sure `.venv` exists in the project root
- Check your PowerShell execution policy:
  ```powershell
  Get-ExecutionPolicy
  ```
  You may need to adjust it (for example, `RemoteSigned`) with administrator privileges.

**Q: Do I need to install Python globally?**
**A**: No! Always use a virtual environment. This keeps your system Python clean and prevents conflicts with other projects.

**Q: What if I see "(.venv)" but the app still doesn't work?**
**A**: Try deactivating and reactivating your virtual environment:
```powershell
deactivate
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Q: Can I run the service without the admin panel?**
**A**: Yes! Run `python run_headless_service.py start` for the background service only (no UI).

**Q: What's the difference between the launch options?**
**A**: 
- `run_mhm.py` starts the UI (admin panel), which you can then use to start/stop the service and manage users.
- `ui/ui_app_qt.py` does the same thing as `run_mhm.py` (it's the actual UI application that `run_mhm.py` launches).
- `run_headless_service.py start` runs the service without any UI (for AI collaborators or headless operation).

**Q: How do I know if the service is running?**
**A**: Check for Python processes: `Get-Process python | Where-Object {$_.CommandLine -like "*service.py*"}`

**Q: Where are my logs stored?**
**A**: Logs are stored in the `logs/` directory. The main application log is `logs/app.log`, with component-specific logs like `logs/discord.log`, `logs/ai.log`, `logs/errors.log`, etc. See section 4. "Component Log Files and Layout" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) for details.

**Q: Why do I see two Python processes when running the app on Windows?**
**A**: This is normal Windows behavior. Windows launches both your script and the underlying interpreter. The process running your actual code is the one that matters; the system Python is a harmless artifact.

## 7. Next Steps
- **Project Overview**: See [README.md](README.md) for features and architecture
- **Development Workflow**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe practices
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design