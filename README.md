# Mental Health Management (MHM)

MHM is a simple personal assistant created by and for a single beginner programmer. It sends scheduled motivational messages and basic check-ins through Discord (email and Telegram are optional). The project also supports optional local AI integration via LM Studio for contextual chat responses.

## Features
- Multi-channel messaging
- Automated daily reminders and basic mood tracking
- Optional AI-powered replies
- Runs as a background service with an admin panel

### Partially Implemented
- AI personalization when LM Studio is running

### Planned
- Advanced task management and progress tracking
- Advanced scheduling
- Integration with additional services

## Quick Start
1. Clone the repo
   ```bash
   git clone https://github.com/Jacfogel/MHM.git
   cd MHM
   ```
2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the app
   ```bash
   python run_mhm.py
   ```
See **HOW_TO_RUN.md** for more details.

## Architecture
The background service (`core/service.py`) runs independently of the admin UI (`ui/ui_app.py`). `run_mhm.py` starts both together. All data stays on your local machine.

## AI Integration (Optional)
If LM Studio is installed with a compatible model, MHM can provide local AI chat. The system works without it.

## Project Structure
```
MHM/
├── core/        # Backend service
├── ui/          # Admin panel
├── bot/         # Communication handlers
├── tasks/       # Task/reminder framework
├── default_messages/
├── user/        # User preferences
├── data/        # User data (gitignored)
└── run_mhm.py   # Entry point
```

## License
This project is personal. Keep forks private and respect mental health data.

## Future Improvements
- Refactor user preference handling through `UserPreferences`
- Expand Discord check-ins with more interactive prompts
- Explore deeper AI integration
- Develop a simple task list with reminders sent via the scheduler, then expand into mood- and context-aware systems
- Add charts showing trends in mood and tasks using Matplotlib or Plotly, later providing detailed wellness analytics
- Use the AI backend to deliver motivational messages or coping strategies
- Break large modules into smaller files
- Introduce consistent snake_case naming
- Centralize configuration in a single module
- Add unit tests for utilities and basic integration tests
- Standardize logging levels and improve dependency error messages
- Build a more interactive Discord bot with quick reactions or forms
