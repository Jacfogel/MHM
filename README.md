# Mental Health Management (MHM) System

A personal mental health and wellness assistant designed to support individuals with ADHD, depression, anxiety, and other mental health challenges through automated messaging, basic check-ins, and AI-powered contextual chat responses.

## 🌟 Current Features

### ✅ Fully Implemented
- **Multi-Channel Communication**: Discord, Email, and Telegram support
- **AI-Powered Chat Responses**: Contextual mental health support using local LLM (LM Studio integration)
- **Automated Messaging**: Scheduled delivery of pre-written messages across categories
- **Basic Daily Check-ins**: Simple mood, energy, and wellness tracking
- **Privacy-First Design**: All personal data stays on your local machine
- **Multi-User Support**: Manage multiple users from a single admin interface
- **Service Architecture**: Background service with comprehensive admin panel

### ✅ Message Categories (Implemented)
- **Motivational**: Encouraging daily messages (3,000+ messages)
- **Health**: Wellness tips and reminders (800+ messages)  
- **Fun Facts**: Educational and entertaining content (3,300+ messages)
- **Word of the Day**: Vocabulary building (basic implementation)
- **Quotes to Ponder**: Inspirational quotes for reflection (basic implementation)

### ⚠️ Partially Implemented / Basic
- **Task & Schedule Management**: Framework exists but limited functionality
- **Reminder System**: Basic structure in place, not fully functional
- **AI Personalization**: Works when LM Studio is running, with intelligent fallbacks

### ❌ Planned / Not Yet Implemented
- **Advanced Task Management**: Full ADHD-friendly task tracking and reminders
- **Comprehensive Progress Tracking**: Detailed wellness analytics and insights
- **Advanced Scheduling**: Complex time-based task and reminder systems
- **Crisis Detection**: Automated detection of mental health crisis keywords
- **Integration APIs**: External service integrations beyond current chat platforms

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- LM Studio (optional, for AI functionality)
- Communication channel accounts (Discord, Email, Telegram - optional)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Jacfogel/MHM.git
   cd MHM
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run_mhm.py
   ```

## 📖 Usage

### Starting the System

The easiest way to start MHM is through the main entry point:

```bash
python run_mhm.py
```

This opens the **Comprehensive Admin Panel** where you can:
- Create and manage users
- Start/stop the background service
- Configure communication channels
- Manage messages and schedules
- Monitor system health

### Creating Your First User

1. Open the Admin Panel (`python run_mhm.py`)
2. Click "Create New User"
3. Fill in your details with real-time validation
4. Configure your preferred communication channels
5. Start the service to begin receiving messages

### Communication Channels

- **Discord**: Personal bot messages in your DMs
- **Email**: Wellness emails sent to your inbox
- **Telegram**: Bot messages via Telegram

## 🏗️ Architecture

MHM uses a **separated service architecture** with two main components:

### Backend Service (`core/service.py`)
- Runs independently as a background service
- Handles message scheduling and delivery
- Manages AI message generation (when available)
- Processes user data and communications
- Operates 24/7 without GUI dependencies

### Admin Panel (`ui/ui_app.py`)
- Comprehensive management interface
- Multi-user administration
- Service control (start/stop/restart)
- Content and schedule management
- System monitoring and debug tools

## 🤖 AI Integration (Optional)

MHM can integrate with **LM Studio** using the **DeepSeek LLM 7B Chat** model for personalized mental health support.

### Setup Instructions:

1. **Install LM Studio** from [lmstudio.ai](https://lmstudio.ai/)
2. **Download the model**: `TheBloke/deepseek-llm-7B-chat-GGUF/deepseek-llm-7b-chat.Q4_K_M.gguf`
3. **Configure the system prompt** (specialized for mental health support)
4. **Start the local server** on localhost:1234
5. **Test connection** using the admin panel or direct API calls

### AI Features:
- **Contextual chat responses** tailored for neurodivergent individuals
- **Intelligent fallbacks** when AI is unavailable (system works without AI)
- **Privacy-focused** - all AI processing happens locally
- **Optional functionality** - system operates fully without AI

**Note**: AI functionality is completely optional. The system works fully without LM Studio installed.

## 📁 Project Structure

```
MHM/
├── core/                   # Backend service and core functionality
├── ui/                     # Admin panel and user interfaces  
├── bot/                    # Communication channel handlers
├── user/                   # User management and preferences
├── tasks/                  # Task and reminder management (basic)
├── default_messages/       # Pre-written message templates
├── data/                  # User data (gitignored for privacy)
└── run_mhm.py            # Main entry point
```

## 🔧 Configuration

### Communication Channels
Configure your communication preferences in the Admin Panel:
- **Discord**: Bot token and user settings
- **Email**: SMTP configuration for sending emails
- **Telegram**: Bot token and chat settings

### Message Categories
All message categories have extensive pre-written content:
- **Motivational**: 3,000+ encouraging messages
- **Health**: 800+ wellness tips and reminders
- **Fun Facts**: 3,300+ educational and entertaining facts
- **Quotes**: Inspirational quotes for reflection  
- **Word of the Day**: Vocabulary building messages

### Scheduling
Set up automated message delivery:
- Custom time periods for different message types
- Flexible scheduling based on user preferences
- Basic daily check-in prompts

## 🛡️ Privacy & Security

- **Local Data Storage**: All personal data stays on your machine
- **No Cloud Dependencies**: Core functionality works offline
- **Optional AI**: AI features are completely optional
- **Private Repository**: Keep your fork private for personal use
- **Configurable Logging**: Control what information is logged

## ⚠️ Current Limitations

- **Task Management**: Basic framework exists but not fully functional
- **Advanced Reminders**: Complex reminder system not yet implemented
- **Progress Analytics**: Limited wellness tracking and insights
- **AI Dependency**: Best features require LM Studio setup (though system works without it)

## 🤝 Contributing

This is a personal mental health management system. While the code is available for reference, please:
- Fork the repository for your own personal use
- Keep your fork private to protect your personal data
- Customize the system to meet your specific needs

## 📋 Requirements

See `requirements.txt` for full dependencies. Key requirements:
- `discord.py` - Discord bot functionality
- `python-telegram-bot` - Telegram integration
- `requests` - HTTP communications and LM Studio API
- `schedule` - Task scheduling
- `tkinter` - GUI components (usually included with Python)

## 🔗 Related Files

- **[HOW_TO_RUN.md](HOW_TO_RUN.md)**: Detailed setup and running instructions
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)**: Development progress and planned features
- **[requirements.txt](requirements.txt)**: Python dependencies

## 📝 License

This project is for personal use. Please respect privacy and mental health data sensitivity when forking or adapting this code.

## �� To Do / Consider

- Refactor user preference handling to consistently use the `UserPreferences` class for all preference operations, rather than direct utility function calls. This would improve encapsulation and future maintainability.

---

**Note**: This system is designed to supplement, not replace, professional mental health care. Always consult with healthcare providers for serious mental health concerns. 