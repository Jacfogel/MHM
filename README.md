# Mental Health Management (MHM)

> **File**: `README.md`
> **Audience**: Human developer (beginner-friendly)
> **Purpose**: High-level overview, navigation, and quick start
> **Style**: Beginner-friendly overview and navigation

MHM is a personal mental health assistant designed first for a single user and their real life.
It sends scheduled motivational and health reminders, helps with basic mood/health tracking, and keeps
everything on your local machine.

Current channels:

- Discord – primary production channel
- Email – present in the code, still evolving
- Telegram – present in code but currently disabled

The system consists of:

- A background service that handles scheduling, reminders, and data
- A PySide6/Qt admin UI used to configure schedules, messages, and users
- Optional local AI integration via LM Studio for contextual chat responses


## 1. Navigation

Use this section as your main entry point into the docs.

- Project vision and goals: `PROJECT_VISION.md`
- How to run and troubleshoot: `HOW_TO_RUN.md`
- Development workflow: `DEVELOPMENT_WORKFLOW.md`
- Architecture overview: `ARCHITECTURE.md`
- Documentation standards and sync rules: `DOCUMENTATION_GUIDE.md`
- Development tools (CLI and commands): `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`
- Testing strategy and commands: `tests/TESTING_GUIDE.md`
- Logging: `logs/LOGGING_GUIDE.md`
- Error handling: `core/ERROR_HANDLING_GUIDE.md`
- Current plans and priorities: `development_docs/PLANS.md` and `TODO.md`
- Change history (short): `ai_development_docs/AI_CHANGELOG.md`
- Change history (detailed): `development_docs/CHANGELOG_DETAIL.md`


## 2. Features

- Multi-channel messaging (Discord in production, Email evolving)
- Automated reminders and basic mood/health tracking
- Time-period-based schedule system (morning, work, evening, bedtime, etc.)
- Admin UI for managing users, schedules, and messages
- Optional AI-powered replies via LM Studio
- Centralized configuration and logging
- Centralized error handling wired into logging
- Modular architecture focused on maintainability and testability


## 3. Quick Start

This is the very short version. For step-by-step instructions and troubleshooting,
see `HOW_TO_RUN.md`.

1. Clone the repo

   ```powershell
   git clone https://github.com/Jacfogel/MHM.git
   cd MHM
   ```

2. Create and activate the virtual environment

   ```powershell
   # Create once
   python -m venv .venv

   # Activate (Windows, PowerShell)
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies

   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment

   - Copy `.env.example` to `.env`
   - Fill in required values (Discord token, paths, LM Studio, etc.)
   - See `HOW_TO_RUN.md` and comments in `core/config.py` for details

5. Launch the application

   ```powershell
   # For human users (admin UI)
   python run_mhm.py

   # For AI collaborators / headless service
   python run_headless_service.py start
   ```

### 3.1. Headless service commands

`run_headless_service.py` is a small command-line wrapper around the headless
service manager in `core/headless_service.py`.

Basic actions:

```powershell
python run_headless_service.py start      # Start the headless service
python run_headless_service.py stop       # Stop the headless service
python run_headless_service.py status     # Check if it is running
python run_headless_service.py info       # Show detailed process info
```

Developer-only actions (used mainly from the UI or for debugging):

```powershell
python run_headless_service.py test <user_id> <category>       # Trigger a test message
python run_headless_service.py reschedule <user_id> <category> # Reschedule messages
```

These commands use the same underlying backend (`core/service.py`) as the UI.

If any of these steps fail, go to `HOW_TO_RUN.md` and the troubleshooting section
in this README.


## 4. Documentation

Key documentation files:

- `README.md` – This file; overview and navigation
- `HOW_TO_RUN.md` – Environment setup, configuration, and run commands
- `ARCHITECTURE.md` – System structure, key modules, and data flows
- `DEVELOPMENT_WORKFLOW.md` – How to make safe, incremental changes
- `DOCUMENTATION_GUIDE.md` – Documentation standards and sync rules
- `logs/LOGGING_GUIDE.md` – Logging architecture and patterns
- `core/ERROR_HANDLING_GUIDE.md` – Error handling patterns and recovery rules
- `tests/TESTING_GUIDE.md` – Testing strategy and structure
- `development_docs/PLANS.md` – Medium/long-term plans and experiments
- `development_tools/DEVELOPMENT_TOOLS_GUIDE.md` – AI tooling and audit commands
- `TODO.md` – Practical current priorities and rough task list

AI-facing docs (for tools like Cursor and ChatGPT):

- `ai_development_docs/AI_SESSION_STARTER.md`
- `development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md`
- `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- `ai_development_docs/AI_ARCHITECTURE.md`
- `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
- `ai_development_docs/AI_TESTING_GUIDE.md`
- `ai_development_docs/AI_LOGGING_GUIDE.md`
- `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`
- `ai_development_docs/AI_REFERENCE.md`
- `ai_development_docs/AI_CHANGELOG.md`

Configuration-related files:

- `.env.example` – Template; safe to commit and share
- `.env` – Real credentials and secrets (local only; ignored by tools)
- `core/config.py` – Central configuration loader and validation
- `requirements.txt` – Python dependencies

For how documentation is kept in sync (especially human/AI pairs), see
`DOCUMENTATION_GUIDE.md` and `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`.


## 5. Architecture

High-level architecture (details in `ARCHITECTURE.md`):

- The background service is implemented under `core/` (for example `core/service.py`
  and related modules). It is responsible for scheduling, sending reminders,
  backups, and other periodic tasks.
- `run_mhm.py` launches the admin UI (PySide6/Qt) so a human can manage users,
  schedules, messages, and the service.
- `run_headless_service.py` uses `core/headless_service.py` to start and stop
  the backend service in a headless way (no UI). This is the typical entry
  point for AI collaborators and automated tools.
- All user data lives under `data/` and `resources/` on your local machine, using
  simple JSON and file-based storage (no remote database). Configuration controls
  where these directories live via `BASE_DATA_DIR`, `USER_INFO_DIR_PATH`, and other
  settings in `core/config.py`.

Recent improvements (see change logs for details):

- Centralized error handling with decorators and a shared `ErrorHandler` object
- Centralized logging via `core/logger.py` with component loggers and rotation
- More robust configuration loading and validation from `.env`
- Clearer separation of concerns between core logic, UI, and channel adapters
- Safer headless service management (`core/headless_service.py` and `run_headless_service.py`) that
  avoids conflicts with UI-managed services


## 6. AI Integration (Optional)

MHM can integrate with a local AI model via LM Studio:

- Configuration is controlled by `LM_STUDIO_*` and `AI_*` environment variables
  in `.env` / `.env.example` and read by `core/config.py`.
- If LM Studio is not installed or the model is not available, MHM still works
  as a scheduler/reminder system.
- For more detail, see the AI sections in `ARCHITECTURE.md`, the `ai/` package, and `SYSTEM_AI_GUIDE.md`.


## 7. Project Structure

A simplified view of the repository (names may evolve; see `ARCHITECTURE.md` for details):

```text
MHM/
- ai/                      # AI assistant components
- ai_development_docs/     # AI-focused documentation
- development_tools/    # Audit, coverage, and doc tools
- communication/           # Channels and orchestration
- core/                    # Core service logic and helpers
- data/                    # User data (gitignored)
- development_docs/        # Human-facing development docs
- logs/                    # Application and component logs
- resources/               # Message templates and other assets
- styles/                  # QSS themes for the admin UI
- tasks/                   # Task/reminder framework
- tests/                   # Unit, integration, behavior, and UI tests
- ui/                      # PySide6/Qt admin application
- user/                    # User-level preferences and settings
- run_mhm.py               # UI entry point (human users)
- run_headless_service.py  # Headless service entry (AI collaborators)
```

For deeper explanations of each area and how they connect, see `ARCHITECTURE.md`
and `ai_development_docs/AI_ARCHITECTURE.md`.


## 8. License and privacy

This is a personal project focused on one person's mental health and daily life.

- Treat forks as private unless explicitly agreed otherwise.
- Do not share real user data, logs, or configuration (`.env`) with anyone.
- If you reuse patterns or code, strip any personal context and keep privacy in mind.


## 9. Notes for beginners

This project is deliberately structured to support a beginner developer who is
learning as they go, with heavy AI assistance.

- Safety first – assume real data and a real machine. Prefer small, reversible
  changes and keep backups (see `ai_development_docs/AI_SESSION_STARTER.md` for
  backup commands and safety rules).
- Learning-focused – many improvements are an excuse to learn a concept
  (logging, error handling, scheduling, testing, UI). When in doubt, slow down
  and understand what is happening instead of blindly copying code.
- No rush – it is better to make one small, well-understood change per
  session than a big refactor you cannot debug later.
- Your control – you decide which improvements to tackle and in what order.
  Anything that feels too risky can be deferred or skipped.
- Recent progress – the project now has centralized logging, centralized
  error handling, clearer configuration, and better documentation. The goal is
  to keep that momentum without burning out.

For current priorities and a history of what has been done recently, see:

- `TODO.md`
- `ai_development_docs/AI_CHANGELOG.md`
- `development_docs/CHANGELOG_DETAIL.md`


## 10. Troubleshooting

This section collects a few common issues and practical fixes. For more detail,
see `HOW_TO_RUN.md` and the logging/error-handling docs.

### 10.1. Virtual environment or Python not recognized

If you see errors like "python is not recognized" or `ModuleNotFoundError`:

1. Make sure the virtual environment exists:

   ```powershell
   python -m venv .venv
   ```

2. Activate it:

   - Windows (PowerShell):

     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

   - macOS/Linux:

     ```bash
     source .venv/bin/activate
     ```

3. Reinstall dependencies inside `.venv`:

   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```

You should see `(.venv)` at the start of your shell prompt when it is active.

### 10.2. Service will not start

1. Confirm your `.env` exists and is based on `.env.example`.
2. Run the configuration report:

   ```powershell
   python -m core.config
   ```

   or use the `config` command via the AI tools runner (see `development_tools/DEVELOPMENT_TOOLS_GUIDE.md`).

3. Check that required directories (for example `data/`, `logs/`) exist. They
   are usually created automatically; if they were deleted, config validation
   and the service will try to recreate them.
4. Look at the logs (start with `logs/errors.log` and `logs/app.log`).
5. Start the service directly and watch the output:

   ```powershell
   python run_headless_service.py start
   ```

### 10.3. Messages not sending (Discord)

1. Check that the service is actually running:

   ```powershell
   python run_headless_service.py status
   ```

2. Verify the Discord bot token in `.env` (`DISCORD_BOT_TOKEN`).
3. Check the bot’s role and permissions in your test server.
4. Inspect `logs/discord.log` and `logs/errors.log` for error messages.

### 10.4. Discord slash command warnings

If you see warnings about slash command syncing:

- The system usually still works, but the logs may be noisy.
- You can optionally add `DISCORD_APPLICATION_ID=your_application_id_here` to
  your `.env`.
- The application ID is available in the Discord Developer Portal for your bot.

### 10.5. Getting help

If you are stuck:

- Development workflow – see `DEVELOPMENT_WORKFLOW.md`.
- Architecture – see `ARCHITECTURE.md`.
- Current issues and priorities – see `TODO.md`.
- Recent changes – see `ai_development_docs/AI_CHANGELOG.md` and
  `development_docs/CHANGELOG_DETAIL.md`.

If you are using an AI assistant (Cursor, ChatGPT, etc.), point it at:

- `ai_development_docs/AI_SESSION_STARTER.md`
- `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`

before asking it to make non-trivial changes.
