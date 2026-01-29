# Motivational Health Messages (MHM)

> **File**: `README.md`  
> **Audience**: Developers, contributors, and AI development assistants  
> **Purpose**: High-level project overview, navigation, and orientation  
> **Style**: Introductory, accurate, and beginner-friendly  

---

## 1. Overview

Motivational Health Messages (MHM) is a personal support and scheduling system designed to reduce daily friction for neurodivergent users, particularly those with ADHD and depression.

The system focuses on externalizing reminders, routines, and check-ins, and can optionally use AI to support reflection, task-switching, and emotional regulation.

MHM is **not** a clinical or diagnostic tool. It does not provide therapy or medical advice. Its goal is to support day-to-day functioning through structure, gentle encouragement, and consistency.

The project began as a simple reminder system and has grown into a broader personal assistant platform, while remaining grounded in real-world use by its creator.

> **Scope note:** This README is intentionally high-level. Detailed behavior, design rationale, and operational specifics live in the linked documentation.

---

## 2. Navigation (Start Here)

If you are new to the project, use the following paths depending on your goal:

- **Understand the purpose and long-term direction**  
  -> [PROJECT_VISION.md](PROJECT_VISION.md)

- **Understand how the system is structured**  
  -> [ARCHITECTURE.md](ARCHITECTURE.md)

- **Run the system or troubleshoot issues**  
  -> [HOW_TO_RUN.md](HOW_TO_RUN.md)

- **Work on documentation or make changes safely**  
  -> [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)  
  -> [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md)

- **Use an AI assistant (Cursor, ChatGPT, etc.) to help with development**  
  -> [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md)  
  -> [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)

---

## 3. What MHM Currently Supports

This list reflects **implemented functionality**, not aspirational goals.

- **Automated Messages**  
  Scheduled, semi-randomized messages delivered within defined time windows.

- **Check-ins**  
  Lightweight mood and status check-ins for reflection and awareness.

- **Tasks**  
  Task reminders and task-related messaging to support initiation and follow-through.

- **Notebook**  
  Simple note capture for thoughts, context, and reflection.

- **Optional AI Assistance**  
  AI can assist with generating responses or reflections, but core functionality does not depend on AI availability.

---

## 4. Communication Channels

- **Discord (Primary, Production)**  
  Discord is the primary supported channel. Most interactive features are designed around Discord's two-way messaging capabilities.

- **Email (Limited Support)**  
  Email is supported for automated outbound messages only. Interactive features that require two-way communication are limited or unavailable via email.

- **Telegram**  
  Telegram has been almost entirely removed from the project and there are no current plans to reintroduce it.

- **SMS (Exploratory)**  
  SMS was an original design goal but is not currently implemented due to reliability and cost constraints.

---

## 5. Project Philosophy

- **Executive Function First**  
  Reduce cognitive load rather than adding complexity.

- **Adaptive, Not Rigid**  
  Use semi-random scheduling and contextual behavior to avoid habituation.

- **AI-Forward, Not AI-Dependent**  
  AI enhances the experience but is never required.

- **Local-First Where Possible**  
  Favor user control, transparency, and predictable behavior.

For long-term values and direction, see [PROJECT_VISION.md](PROJECT_VISION.md).

---

## 6. Architecture

High-level architecture (details in [ARCHITECTURE.md](ARCHITECTURE.md)):

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

  settings in `core/config.py`. For the canonical list of settings, what they do, and what breaks when misconfigured,
  see [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md).

- Canonical user data layout and persistence guarantees are documented in [USER_DATA_MODEL.md](USER_DATA_MODEL.md).


**Entry points at a glance:**
- **UI-driven:** `python run_mhm.py` (human administration)
- **Headless service:** `python run_headless_service.py` (automation / AI tools)

Recent improvements (see change logs for details):

- Centralized error handling with decorators and a shared `ErrorHandler` object
- Centralized logging via `core/logger.py` with component loggers and rotation
- More robust configuration loading and validation from `.env`
- Clearer separation of concerns between core logic, UI, and channel adapters
- Safer headless service management that avoids conflicts with UI-managed services

---

## 7. AI Integration (Optional)

MHM can integrate with a local AI model via LM Studio:

- Configuration is controlled by `LM_STUDIO_*` and `AI_*` environment variables
  in `.env` / `.env.example` and read by `core/config.py`.
- If LM Studio is not installed or the model is not available, MHM still works
  as a scheduler/reminder system.
- The headless service supports start/stop/status and diagnostic commands;
  see [HOW_TO_RUN.md](HOW_TO_RUN.md) for details.
- For deeper AI details, see the AI sections in [ARCHITECTURE.md](ARCHITECTURE.md),
  the `ai/` package, and [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).

---

## 8. Project Structure

A simplified view of the repository (names may evolve; see [ARCHITECTURE.md](ARCHITECTURE.md) for details):

```text
MHM/
- ai/                      # AI assistant components
- ai_development_docs/     # AI-focused documentation
- development_tools/       # Audit, coverage, and doc tools
- communication/           # Channels and orchestration
- core/                    # Core service logic and helpers
- data/                    # User data (gitignored)
- development_docs/        # Human-facing development docs
- logs/                    # Application and component logs
- notebook/                # Notebook Framework
- resources/               # Message templates and other assets
- styles/                  # QSS themes for the admin UI
- tasks/                   # Task/reminder framework
- tests/                   # Unit, integration, behavior, and UI tests
- ui/                      # PySide6/Qt admin application
- user/                    # User-level preferences and settings
- run_mhm.py               # UI entry point (human users)
- run_headless_service.py  # Headless service entry (AI collaborators)
```

For deeper explanations, see [ARCHITECTURE.md](ARCHITECTURE.md) and
[AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md).

---

## 9. License and Privacy

This is a personal project focused on one person's mental health and daily life.

- Treat forks as private unless explicitly agreed otherwise.
- Do not share real user data, logs, or configuration (`.env`) with anyone.
- If you reuse patterns or code, strip any personal context and keep privacy in mind.

---

## 10. Notes for Beginners

This project is deliberately structured to support a beginner developer who is
learning as they go, with heavy AI assistance.

- **Safety first** - Assume real data and a real machine. Prefer small, reversible
  changes and keep backups (see
  [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md)).
- **Learning-focused** - Many improvements exist to learn concepts (logging,
  error handling, scheduling, testing, UI). Slow down and understand changes.
- **No rush** - One small, well-understood change per session is better than a
  large refactor you cannot debug.
- **Your control** - You decide which improvements to tackle and when.
- **Recent progress** - Centralized logging, error handling, clearer configuration,
  and improved documentation.

For current priorities and recent history, see:

- [TODO.md](TODO.md)
- [PLANS.md](development_docs/PLANS.md)
- [AI_CHANGELOG.md](ai_development_docs/AI_CHANGELOG.md)
- [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md)

---

## 11. Troubleshooting

For more detail, see [HOW_TO_RUN.md](HOW_TO_RUN.md) and the logging/error-handling
documentation.

### 11.1. Virtual environment or Python not recognized

If you see errors like "python is not recognized" or `ModuleNotFoundError`:

1. Ensure the virtual environment exists:

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

3. Reinstall dependencies:

   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```

### 11.2. Service will not start

1. Confirm `.env` exists and is based on `.env.example`.
2. Run configuration validation:

   ```powershell
   python -m core.config
   ```

3. Check logs (`logs/errors.log`, `logs/app.log`).
4. Start the service directly:

   ```powershell
   python run_headless_service.py start
   ```

### 11.3. Messages not sending (Discord)

1. Confirm the service is running:
   ```powershell
   python run_headless_service.py status
   ```
2. Verify `DISCORD_BOT_TOKEN` in `.env`.
3. Check bot permissions in Discord.
4. Inspect `logs/discord.log` and `logs/errors.log`.

### 11.4. Discord slash command warnings

- Warnings are usually non-fatal.
- Optionally add `DISCORD_APPLICATION_ID` to `.env`.

### 11.5. Getting help

If you are stuck:

- Workflow: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Priorities: [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md)
- Changes: [AI_CHANGELOG.md](ai_development_docs/AI_CHANGELOG.md),
  [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md)

AI assistants should consult:

- [AI_SESSION_STARTER.md](ai_development_docs/AI_SESSION_STARTER.md)
- [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md)
- [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md)

before making non-trivial changes.