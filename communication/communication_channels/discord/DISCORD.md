# Discord Commands and Usage

> **Audience**: Users and contributors  
> **Purpose**: Complete guide for Discord commands and natural language usage  
> **Style**: User-friendly, comprehensive, beginner-friendly

> **See [README.md](../../../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../../../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../../../QUICK_REFERENCE.md) for essential commands**

## Getting Started

### New Users
When you first authorize the MHM Discord app, you'll automatically receive a welcome message with interactive buttons:
- **Create a New Account** - Set up a new MHM account (username will be prefilled with your Discord username if available)
- **Link to Existing Account** - Link your Discord account to an existing MHM account (confirmation code sent via email)

You can also use the `/start` command to receive setup instructions if you didn't get the welcome message.

### Primary Method: Natural Language (Recommended)
Talk to the bot naturally! It understands context and intent.
- "I need to create a task to call mom tomorrow"
- "How am I feeling today?" (starts check-in)
- "Show me my tasks"

### Alternative Methods
- **Slash Commands**: `/command` - Discord-native commands (preferred, auto-complete in Discord)
- **Bang Commands**: `!command` - Classic prefix commands (also supported)

## Available Commands

### Task Management
**What it does**: Create, view, update, and complete your tasks

**Natural Language Examples:**
- "create a task to buy groceries due tomorrow"
- "show my tasks"
- "complete the groceries task"
- "update the task about groceries to be due on Friday"
- "delete the task about groceries"
- "how am I doing with my tasks this week?"

**Explicit Commands:**
- `/tasks` - Show all your tasks (preferred, Discord-native)
- `!tasks` - Show all your tasks (also supported)
- Natural: "task stats" - View task completion statistics

**Available Intents:**
- create_task, list_tasks, complete_task, delete_task, update_task, task_stats, task_analytics

---

### Check-ins (Conversational Flow)
**What it does**: Start an interactive check-in conversation about your mood, energy, and wellbeing

**Natural Language Examples:**
- "start a check-in"
- "how am I feeling?"
- "I want to check in"
- "let me check in"

**Explicit Commands:**
- `/checkin` - Start check-in flow (preferred, Discord-native)
- `!checkin` - Start check-in flow (also supported)

**Important**: Check-ins are conversational - the bot will ask you questions and wait for your responses. To cancel anytime, say "cancel" or "/cancel".

**Available Intents:**
- start_checkin, checkin_status, checkin_history, checkin_analysis

---

### Profile Management
**What it does**: View and update your personal information, health conditions, and preferences

**Natural Language Examples:**
- "show my profile"
- "update my name to Julie"
- "add health condition: diabetes"
- "show profile stats"

**Explicit Commands:**
- `/profile` - Show your profile (preferred, Discord-native)
- `!profile` - Show your profile (also supported)

**Available Intents:**
- show_profile, update_profile, profile_stats

---

### Schedule Management
**What it does**: View and manage your daily schedules and time periods

**Natural Language Examples:**
- "show my schedule"
- "add a schedule period for work"
- "update my schedule"
- "what's my schedule status?"

**Explicit Commands:**
- `/schedule` - Show your schedules (preferred, Discord-native)
- `!schedule` - Show your schedules (also supported)

**Available Intents:**
- show_schedule, update_schedule, schedule_status, add_schedule_period, edit_schedule_period

---

### Analytics & Insights
**What it does**: View your wellness analytics, mood trends, and performance insights

**Natural Language Examples:**
- "show my analytics"
- "what are my mood trends?"
- "how am I doing with habits?"
- "what's my wellness score?"
- "show my check-in history"
- "what's my completion rate?"

**Explicit Commands:**
- `/analytics` - Show wellness analytics (preferred, Discord-native)
- `!analytics` - Show wellness analytics (also supported)

**Available Intents:**
- show_analytics, mood_trends, habit_analysis, sleep_analysis, wellness_score, checkin_history, completion_rate, task_analytics, quant_summary

---

### Account Management
**What it does**: Create or link your MHM account to start using the system

**Getting Started:**
- When you authorize the MHM Discord app, you'll receive a welcome message with buttons
- Click **"Create a New Account"** to set up a new MHM account
- Click **"Link to Existing Account"** to link to an existing account (requires email confirmation code)

**Explicit Commands:**
- `/start` - Get setup instructions and account creation/linking options

**Account Creation:**
- Username will be prefilled with your Discord username if it's available
- Choose a unique username for your MHM account
- Your account is automatically linked to your Discord account

**Account Linking:**
- Enter your existing MHM username
- A confirmation code will be sent to the email address associated with your MHM account
- Enter the confirmation code to complete the linking process

**Available Intents:**
- create_account, link_account, check_account_status

---

### System Commands
**What it does**: Get help, view system status, and manage conversation flows

**Natural Language Examples:**
- "help"
- "what commands are available?"
- "show me examples"
- "what's my status?"
- "clear stuck conversations"

**Explicit Commands:**
- `/help` - Show help
- `/start` - Get setup instructions (for new users)
- `/status` - Show system status
- `/clear` - Clear stuck flows
- `/cancel` - Cancel current flow

**Available Intents:**
- help, commands, examples, status, clear_flows, cancel

---

## Command Types Explained

### Single-Turn Commands
Most commands are "single-turn" - you ask, bot responds once.
Examples: show profile, list tasks, show analytics

### Conversational Flows
Some commands start multi-turn conversations:
- **Check-ins**: Bot asks questions, waits for responses
- **Task creation**: May ask for clarification
- **Profile updates**: May prompt for missing information

To exit a flow: say "cancel" or "/cancel"

## Tips for Best Experience

1. **Use Natural Language**: More flexible and conversational
2. **Be Specific**: "complete the groceries task" vs "complete task"
3. **Ask for Help**: Say "help" anytime to see available commands
4. **Flow Management**: Use "/cancel" to exit stuck conversations

## Technical Notes

### Scales and Values
- Mood and energy values display on a 1–5 scale (e.g., `Mood 3/5`)
- Composite analytics scores use 0–100 scaling (e.g., `Overall Score: 78/100`)

### Slash Commands
- When `DISCORD_APPLICATION_ID` is set, dynamic slash commands are registered
- Unknown `/` or `!` prefixes fall back to the natural language parser if not matched

### Troubleshooting
- If a command isn't recognized, try `help` or `commands` to see supported forms
- For full setup and environment variables, see `README.md` and `QUICK_REFERENCE.md`

