# MHM System Improvements

## 🗓️ Recent Changes

### 2025-01-08 - Removed Backwards Compatibility for Timestamp Formats
- **Backwards Compatibility Removal**: Systematically removed all Unix timestamp compatibility code from core system
- **Files Modified**: Updated `core/utils.py`, `bot/communication_manager.py`, `bot/user_context_manager.py`, and `core/auto_cleanup.py`
- **Timestamp Functions**: Simplified timestamp parsing functions to only handle human-readable format (`YYYY-MM-DD HH:MM:SS`)
- **Error Handling**: Improved error handling with combined ValueError/TypeError catching for timestamp parsing
- **Code Cleanup**: Removed dual-format parsing logic, reducing complexity and potential bugs
- **Verification**: Confirmed all existing timestamps are in human-readable format through comprehensive audit
- **Impact**: Cleaner, more maintainable code with single timestamp format; eliminates parsing ambiguity
- **Preserved**: Migration and testing scripts retained for reference and future migrations

### 2025-01-08 - UI Architecture Consolidation & Enhancement
- **UI Consolidation**: Consolidated `login.py` and `main_ui.py` functionality into unified admin panel architecture
- **Enhanced Admin Panel**: Complete redesign of `ui_app.py` with comprehensive user management capabilities
- **Account Management**: Enhanced `account_creator.py` with real-time validation and improved UX
- **Content Management**: Complete rewrite of `account_manager.py` with TreeView, sorting, undo functionality
- **Communication Settings**: Added comprehensive communication channel management with detailed change tracking
- **Category Management**: Added per-user category enable/disable functionality
- **Debug Tools**: Preserved and enhanced debug menu with cache management and system health checks
- **Test Messages**: Added test message functionality through service integration
- **Window Management**: Improved window sizing, geometry saving, and user feedback
- **Data Cleanup**: Created and ran duplicate message cleanup utility, removing 95 duplicate messages
- **Treeview Refresh**: Fixed treeview update issues when adding/editing messages
- **Schedule Management**: Enhanced schedule editing with better window sizing and validation
- **Impact**: Unified admin interface replaces fragmented login/main UI flow; significantly enhanced functionality

### 2025-06-06 - Service Architecture Separation
- **Backend Service**: Created `core/service.py` - runs MHM independently without UI
- **Management UI**: Created `ui/ui_app.py` - optional UI for service management and user interface
- **Fixed Shutdown**: Proper scheduler thread termination using threading.Event
- **Main Entry Point**: Created `run_mhm.py` - single way to launch the application
- **File Organization**: Moved core files to `core/` folder, launchers to `scripts/launchers/`
- **Fixed Import Paths**: Updated all import statements for new file locations
- **Impact**: Service can run continuously in background; UI is now optional for administration

### 2025-06-06 - Project Organization
- **Consolidated scripts**: Merged `tools/` into `scripts/` directory  
- **Moved migration code**: `core/data_migration.py` → `scripts/migration/`
- **Streamlined docs**: Consolidated multiple READMEs into single reference

### 2025-06-05 - Data Structure Migration  
- **File organization**: Migrated from flat files to user-specific directories
- **Backup system**: Automatic backup creation before migrations
- **Data safety**: Migration verification and rollback support

### 2025-06-04 - AI Performance Optimization
- **Response caching**: Reduced redundant AI generation 
- **Timeout increase**: 10s → 15s for AI requests
- **Context optimization**: Lighter context loading for speed
- **Fallback improvement**: Better user-aware fallback responses

## 🏗️ Current Architecture

### UI Architecture
```
ui/
├── ui_app.py              # Comprehensive admin panel (main interface)
├── account_creator.py     # Enhanced account creation with live validation
├── account_manager.py     # Complete content & settings management
├── main_ui.py            # Legacy (can be removed)
└── login.py              # Legacy (removed)
```

### Data Structure
```
data/users/USER_ID/
├── profile.json          # Basic user info
├── preferences.json      # User settings  
├── schedules.json        # User schedules
├── daily_checkins.json   # Check-in responses
├── chat_interactions.json # AI chat history
├── survey_responses.json # Survey data
└── sent_messages.json    # Message log
```

### Scripts Organization
```
scripts/
├── migration/     # One-time data migrations
├── utilities/     # Admin and maintenance tools (including duplicate cleanup)
└── testing/       # Test utilities
```

## ⚙️ Key Configuration

```env
# Performance
AI_TIMEOUT_SECONDS=15
AI_CACHE_RESPONSES=true
USE_USER_SUBDIRECTORIES=true

# Logging  
LOG_LEVEL=WARNING          # Quiet by default
LOG_FILE_PATH=app.log
```

## 📈 Performance Improvements

- **Unified Admin Interface**: Single comprehensive panel replaces multiple fragmented UIs
- **Enhanced User Management**: Multi-user admin capabilities with detailed status tracking
- **Improved Content Management**: TreeView with sorting, filtering, and undo functionality
- **Better Communication Management**: Detailed change tracking and validation
- **Real-time Validation**: Live status updates during account creation and settings changes
- **50-70% reduction** in AI timeouts
- **Faster file operations** with smaller organized files  
- **Response caching** eliminates redundant AI generation
- **Better memory usage** through optimized data structures

## 🔧 Available Tools

- **Admin Panel**: `ui_app.py` - Comprehensive user and system management
- **User Data CLI**: `scripts/utilities/user_data_cli.py` - Admin interface
- **Duplicate Cleanup**: `scripts/utilities/cleanup_duplicate_messages.py` - Message deduplication
- **Migration Script**: `scripts/migration/migrate_data.py` - Data structure migration  
- **Debug Menu**: Built into admin panel - toggle logging, cache management, system health checks

---

## 📝 Recent Changes

### 2024-12-19 - Switched to LM Studio with DeepSeek LLM 7B Chat
- **Feature**: Replaced GPT4All with LM Studio HTTP API for AI functionality
- **Model**: Now uses DeepSeek LLM 7B Chat instead of Nous-Hermes-2-Mistral-7B
- **Impact**: Better AI responses, easier model management, no local model file needed
- **Configuration**: New environment variables for LM Studio connection
- **Usage**: Ensure LM Studio is running on localhost:1234 with DeepSeek LLM 7B Chat model loaded
- **Fallback**: Maintains intelligent contextual fallbacks when LM Studio unavailable

### 2024-01-29 - Check-in Preference System Implementation
- **Check-in Preferences**: Added comprehensive user preference system for daily check-ins
  - **Account Creation**: Added check-in preferences section to account creator with 10+ customizable questions
  - **Account Management**: Added check-in settings management window with frequency and question selection
  - **UI Integration**: Added "Check-in Settings" button to admin panel for per-user configuration
  - **Permission System**: Check-ins now require user opt-in and can be disabled per user
  - **Configurable Questions**: Expanded from 4 basic questions to 14 optional questions including:
    - Basic: mood, energy, breakfast, teeth (default enabled)
    - Extended: sleep quality/hours, anxiety, focus, medication, exercise, hydration, social interaction, stress, daily reflection
  - **Frequency Options**: Daily, weekly, or custom intervals (framework ready)
  - **Data Structure**: Clean preferences storage in user profile with enabled/disabled per question
  - **Channel Neutral**: Works with any communication channel (Discord, Telegram, etc.)

### 2024-01-29 - AI System Migration to LM Studio + DeepSeek
- **AI Backend Switch**: Completely replaced GPT4All with LM Studio hosting DeepSeek LLM 7B Chat

---

## 📝 How to Add Improvements

When adding new improvements, follow this format:

```markdown
### YYYY-MM-DD - Brief Title
- **Feature**: Description of what was added/changed
- **Impact**: What this improves or fixes
- **Usage**: How to use the new feature (if applicable)
```

Keep entries **concise** and **scannable**. Focus on **what changed** and **why it matters**. 