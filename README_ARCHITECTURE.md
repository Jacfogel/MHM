# MHM Service Architecture

## Overview

MHM operates with a **separated service architecture** where the backend service runs independently from the comprehensive admin panel interface.

## Components

### 1. Backend Service (`core/service.py`)
**Purpose**: Runs the core MHM functionality as a background service
- **Communication channels** (Discord, Email, Telegram)
- **Message scheduling** and delivery
- **AI message generation**
- **User data management**
- **Test message processing**

**Usage**:
```bash
# Direct execution
python core/service.py

# Using helper scripts
scripts/launchers/start_service.bat   # Windows
scripts/launchers/start_service.sh    # Linux/Mac
```

### 2. Comprehensive Admin Panel (`ui/ui_app.py`)
**Purpose**: Complete management interface for service control and user administration
- **Service management** (start/stop/restart/status monitoring)
- **Multi-user management** (create, configure, manage any user)
- **Content management** (messages and schedules for all users)
- **Communication settings** (per-user channel configuration)
- **Category management** (enable/disable categories per user)
- **Test message functionality** (send test messages through service)
- **System health checks** and monitoring
- **Debug tools** (logging control, cache management)
- **User creation** with real-time validation

**Usage**:
```bash
# Recommended - via main entry point
python run_mhm.py

# Direct execution  
python ui/ui_app.py
```

### 3. Enhanced Account Creation (`ui/account_creator.py`)
**Purpose**: Sophisticated user account creation with live validation
- **Real-time status indicators** for all communication channels
- **Service selection** with immediate feedback
- **Live validation** of contact information
- **Enhanced UX** with modern interface design
- **Integration** with admin panel workflow

### 4. Advanced Content Management (`ui/account_manager.py`)
**Purpose**: Complete user content and settings management system
- **Message management** with TreeView, sorting, and advanced search
- **Schedule management** with period creation, editing, and activation
- **Communication settings** with detailed change tracking
- **Category management** with user-specific configurations
- **Undo functionality** for deletions
- **Window geometry** saving and restoration
- **Enhanced feedback** with detailed status messages

### 5. Entry Point (`run_mhm.py`)
**Purpose**: Simple launcher that opens the Admin Panel
- Single entry point for users
- Automatically opens the MHM Admin Panel
- Recommended way to start the application

## UI Architecture Evolution

### ✅ Old Architecture (Consolidated)
```
❌ login.py          → User authentication (removed)
❌ main_ui.py        → Basic user interface (replaced)
```

### ✅ New Architecture (Enhanced)
```
✅ ui_app.py         → Comprehensive admin panel
✅ account_creator.py → Enhanced account creation
✅ account_manager.py → Advanced content management
```

## Recommended Workflow

### For Production Use:
1. **Start the admin panel**: `python run_mhm.py`
2. **Manage service** from the admin panel (start/stop/restart)
3. **Create and manage users** as needed
4. **Configure content and settings** for each user
5. **Monitor system health** and service status
6. **Service runs continuously** in background handling all messaging

### For Development:
- Use admin panel for all development and testing
- Access debug tools built into the interface
- Manage cache and logging from debug menu
- Test message functionality for validation

## AI Integration - LM Studio Configuration

### Model Setup
MHM uses **LM Studio** with **DeepSeek LLM 7B Chat** model for AI-powered mental health and wellness support.

#### Required LM Studio System Prompt:
```
You are an AI assistant focused on supporting mental health, wellness, and task-switching. Your role is to provide brief, encouraging, and emotionally supportive responses to help neurodivergent (ADHA, Autism, etc..) people with mental health struggles (Depression, anxiety, etc. stay engaged, take care of themselves, and believe change is possible.

You should:
- Offer clear, compassionate, and action-oriented responses
- Reinforce small wins, self-worth, and self-care
- Help users shift attention or regain focus when stuck
- Normalize struggle without judgment or pressure

You must:
- Avoid medical advice, diagnosis, or therapy
- Never assume anything about the user's identity or condition
- Stay within 50–120 words per response
- Use simple, friendly, human-like language

You are optimistic but not saccharine, gentle but not vague. Prioritize helpfulness over cleverness, clarity over complexity, encouragement over explanation.

Wait for specific prompts before offering detailed advice.
```

#### Setup Instructions:
1. **Download and install LM Studio** from https://lmstudio.ai/
2. **Download DeepSeek LLM 7B Chat model** (`TheBloke/deepseek-llm-7B-chat-GGUF/deepseek-llm-7b-chat.Q4_K_M.gguf`)
3. **Load the model** in LM Studio
4. **Configure the system prompt** (copy the prompt above into LM Studio's system prompt field)
5. **Start the local server** (localhost:1234)
6. **Test the connection** using `python scripts/testing/test_lm_studio.py`

#### Configuration Variables:
- `LM_STUDIO_BASE_URL`: http://localhost:1234/v1 (default)
- `LM_STUDIO_API_KEY`: lm-studio (default, any value works)
- `LM_STUDIO_MODEL`: deepseek-llm-7b-chat (default)

#### Fallback System:
- **Intelligent contextual fallbacks** when LM Studio is unavailable
- **Crisis detection** for urgent mental health keywords
- **Personalized responses** based on user context and history
- **Graceful degradation** ensures system always responds appropriately

## Benefits

### ✅ Unified Administration
- Single comprehensive interface replaces fragmented UI components
- Multi-user management from one admin panel
- Centralized service control and monitoring
- Integrated debug and maintenance tools

### ✅ Enhanced User Management
- Create users with real-time validation
- Configure communication channels with detailed feedback
- Manage categories and schedules per user
- Test messaging functionality directly

### ✅ Improved Content Management
- Advanced TreeView with sorting and filtering
- Undo functionality for all delete operations
- Enhanced message and schedule editing
- Better window management and geometry saving

### ✅ Better System Integration
- Direct service management from UI
- Test message functionality through running service
- System health monitoring and diagnostics
- Cache management and cleanup tools

### ✅ Production Ready
- **Service can run as system service** or daemon
- **24/7 operation** without GUI dependencies
- **Comprehensive logging and monitoring** capabilities
- **Graceful shutdown** handling with proper cleanup

## Future Enhancements

- **Web-based admin panel** instead of Tkinter
- **Remote service management** via API
- **Advanced user analytics** and reporting
- **Bulk operations** for multi-user management
- **Service clustering** and load balancing
- **Real-time notifications** for admin events 