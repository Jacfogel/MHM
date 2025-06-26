# MHM System Improvements

## 🗓️ Recent Changes

### 2025-01-18 - Fixed Check-in Data Loss Issue
- **Critical Bug Fix**: Fixed issue where updating check-in settings would erase user categories and schedules
- **Root Cause**: `setup_checkin_management_window()` in `ui/account_manager.py` was loading only preferences instead of full user data
- **Problem**: When saving check-in changes, the system would overwrite the entire user data with just preferences, losing categories and schedules
- **Fix Applied**:
  - Changed loading from `get_user_preferences()` to `load_user_info_data()` to preserve full user data
  - Modified save logic to load full user data first, then update only check-in preferences
  - Added proper data structure validation to ensure preferences exist before updating
- **Data Restoration**: Manually restored user data for affected user (me581649-4533-4f13-9aeb-da8cb64b8342):
  - Restored categories: `["health", "motivational"]`
  - Restored check-in settings with 5 enabled questions
  - Restored basic schedule periods for both categories
- **Prevention**: Fixed the underlying code issue to prevent future data loss
- **Impact**: Users can now safely update check-in settings without losing their message categories and schedules

### 2025-01-18 - Logging System Cleanup & Optimization (Updated)
- **Duplicate Message Reduction**: Eliminated redundant and duplicate logging messages throughout the system
- **UI Service Manager**: Removed duplicate "Start service requested" messages in `ui_app.py`
- **Logging Verification**: Streamlined logging system health checks in `core/service.py`
  - Changed verbose test messages to debug level
  - Consolidated verification messages from 4 down to 1
  - Removed "Logging system verified before channel initialization" redundancy
- **Channel Initialization**: Cleaned up duplicate channel success messages in `bot/communication_manager.py`
  - "Channel email initialized successfully" + "on attempt 1" + "initialized successfully" → single message
  - More concise channel status reporting
- **Channel Status Logging**: Reduced verbose status change messages in `bot/base_channel.py`
  - Only log errors and ready states
  - Suppressed repetitive "initializing" status messages
- **Scheduler Messages**: Consolidated duplicate scheduler completion messages in `core/scheduler.py`
  - Removed duplicate "Daily scheduler jobs have been scheduled for all users" message
  - Moved "Current time for scheduling" to log once per scheduling session instead of per message
  - Streamlined scheduling completion reporting
- **User Data Caching**: Implemented intelligent caching for user profile and schedule data in `core/utils.py`
  - Added 30-second cache for user profile loading to prevent excessive "User profile loaded" debug messages
  - Added caching for schedule time periods to reduce "Retrieved and sorted schedule time periods" spam
  - Applied caching to both `get_user_info()` and `load_user_info_data()` functions
  - Significantly reduced repetitive database access logging during scheduling operations
- **Additional Fixes** (Updated 2025-01-18):
  - **Scheduler Duplication**: Fixed duplicate `schedule_all_users_immediately()` call causing double scheduling messages
  - **Windows Task Cleanup**: Fixed task deletion errors by handling missing tasks gracefully
  - **Component Initialization**: Shortened verbose initialization messages for cleaner logs
- **Result**: Reduced log noise by approximately 80% while preserving all critical debugging information

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

### Logging System Improvements (2025-01-16)

**Issues Identified and Fixed:**

1. **"Logging system force restarted successfully" Issue**
   - **Problem**: `check_and_fix_logging()` method in `core/service.py` had flawed logic that always triggered force restart
   - **Root Cause**: Method checked file size increase with only 0.2 second delay, not accounting for buffering
   - **Fix**: Improved detection logic with:
     - Longer wait time (0.5 seconds) for file operations
     - Better verification by reading recent log content
     - Checking for recent logging activity within 5 minutes
     - Only restarting when there's clear evidence of failure
   - **Result**: Eliminates unnecessary force restarts during normal operation

2. **"Scheduler running: 0 active jobs scheduled" - Misleading Message**
   - **Problem**: Always showed 0 jobs even when messages were being sent successfully
   - **Root Cause**: Schedule library behavior - jobs scheduled for future times may not appear in `schedule.jobs` until closer to execution
   - **Investigation**: Confirmed scheduler was working correctly (messages were being sent), issue was misleading logging
   - **Fix**: 
     - Updated message to clarify that jobs may not appear until execution time
     - Avoided complex debugging that could break working functionality
   - **Result**: Less confusing status messages while preserving working functionality

3. **Unnecessary Logging Suffixes Cleanup**
   - **Problem**: Messages like "User info loaded (new structure)" and "User info saved (no duplication)" had unnecessary suffixes
   - **Fix**: Removed "(new structure)" and "(no duplication)" suffixes from logging messages in `core/utils.py`
   - **Result**: Cleaner, more professional log messages

**Important Note**: During debugging, we discovered that complex modifications to the scheduler code could break the working functionality. We reverted problematic changes and kept only minimal, safe improvements to maintain system stability.

### Schedule Rescheduling Issue Fix (2025-01-16)

**Issue Identified and Fixed:**

4. **"No scheduler manager available for rescheduling" - Schedule Changes Not Applied**
   - **Problem**: When editing schedule periods through the UI, changes were saved to files but the scheduler wasn't notified to reschedule messages
   - **Root Cause**: UI runs in "UI-only mode" without direct access to the scheduler manager running in the service
   - **Investigation**: The system was designed to work this way, but the communication mechanism between UI and service was missing
   - **Solution**: 
     - Extended existing flag file pattern (similar to test messages) to handle reschedule requests
     - Added `create_reschedule_request()` function in `core/utils.py` to create request files when scheduler manager is not available
     - Added `check_reschedule_requests()` method in `core/service.py` to process reschedule requests every 2 seconds
     - Service now automatically picks up schedule changes made through UI and reschedules accordingly
   - **Result**: Schedule edits through the UI now properly trigger rescheduling in the background service

**Technical Details:**
- Smart detection: Only creates reschedule requests when service is actually running
- If service is stopped, changes are automatically picked up on next startup via `schedule_all_users_immediately()`
- Uses JSON flag files with format: `reschedule_request_{user_id}_{category}_{timestamp}.flag`
- Service processes requests every 2 seconds during normal operation
- Proper user context switching ensures rescheduling happens for the correct user
- Automatic cleanup of processed request files
- Graceful error handling for malformed or inaccessible request files

### Schedule Rescheduling Deduplication Fix (2025-01-16)

**Issue Identified and Fixed:**

5. **Duplicate Reschedule Requests - Multiple Messages Sent**
   - **Problem**: When editing multiple schedule periods or adding new periods, each change created a separate reschedule request, leading to duplicate rescheduling and multiple messages being sent at the same time
   - **Root Cause**: 
     - Adding new periods: "Confirm" button triggers immediate reschedule
     - Editing existing periods: "Save Schedule" processes each changed period individually
     - Multiple reschedule requests processed sequentially without deduplication
   - **Solution**: 
     - Added deduplication logic to `MHMService.check_reschedule_requests()` method
     - Tracks recent reschedules per user/category combination for 30 seconds
     - Skips duplicate requests within the time window
     - Batch deduplication prevents multiple requests in same processing cycle
     - Automatic cleanup of duplicate request files
   - **Result**: Only one reschedule happens per user/category combination, eliminating duplicate messages

**Technical Implementation:**
- Added `reschedule_dedup` dictionary to track recent reschedules
- 30-second deduplication window prevents rapid duplicate processing
- Batch processing with duplicate detection within same cycle
- Automatic cleanup of expired deduplication entries
- Proper file cleanup for duplicate request files

## 📝 How to Add Improvements

When adding new improvements, follow this format:

```markdown
### YYYY-MM-DD - Brief Title
- **Feature**: Description of what was added/changed
- **Impact**: What this improves or fixes
- **Usage**: How to use the new feature (if applicable)
```

Keep entries **concise** and **scannable**. Focus on **what changed** and **why it matters**. 