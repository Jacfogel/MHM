# AI Logging Guide - Quick Reference

> **Purpose**: Fast logging patterns and troubleshooting for AI collaborators  
> **Style**: Concise, pattern-focused, actionable  
> **For details**: See [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md)

## Overview

The MHM logging system uses component-based separation with structured logging. Each component has its own log file for better organization and troubleshooting.

## Directory Structure

```
logs/
├── app.log                    # Main application logs (active)
├── discord.log               # Discord bot specific logs (active)
├── ai.log                    # AI interactions and processing (active)
├── user_activity.log         # User actions and check-ins (active)
├── errors.log                # Error and critical messages only (active)
├── communication_manager.log # Communication orchestration (active)
├── email.log                 # Email bot operations (active)
├── file_ops.log              # File operations (active)
├── scheduler.log             # Scheduler operations (active)
├── ui.log                    # UI operations (active)
├── message.log               # Message processing (active)
├── backup.log                # Backup operations (active)
├── schedule_utilities.log    # Schedule utilities (active)
├── analytics.log             # Analytics operations (active)
├── checkin_dynamic.log       # Dynamic check-in operations (active)
├── ai_cache.log              # AI cache operations (active)
├── ai_context.log            # AI context building (active)
├── ai_conversation.log       # AI conversation management (active)
├── ai_prompt.log             # AI prompt management (active)
├── channel_orchestrator.log  # Channel orchestration (active)
├── channel_monitor.log       # Channel monitoring (active)
├── retry_manager.log         # Retry management (active)
├── backups/                  # Rotated log files (daily rotation)
└── archive/                  # Compressed old logs (>7 days old)
```

## Configuration

### **Log Levels (Priority)**
- **ERROR/CRITICAL** - System failures, data corruption
- **WARNING** - Recoverable issues, deprecated usage
- **INFO** - Normal operations, user actions
- **DEBUG** - Detailed debugging information

### **Component Loggers**
```python
from core.logger import get_component_logger

# Component loggers (use these)
logger = get_component_logger(__name__)  # Automatic component detection
discord_logger = get_component_logger("discord")
ai_logger = get_component_logger("ai")
```

## Quick Reference

### **Log Files (Priority Order)**
- `errors.log` - Critical errors and failures (check first)
- `app.log` - Main application flow and operations
- `discord.log` - Communication channel issues
- `ai.log` - AI processing and chatbot interactions
- `user_activity.log` - User actions and check-ins

### **Logging Commands**
```powershell
# Check recent errors (most important)
Get-Content "logs/errors.log" -Tail 20

# Check application status
Get-Content "logs/app.log" -Tail 20

# Monitor live logs
Get-Content "logs/app.log" -Wait -Tail 10
```

## Common Logging Patterns

### **Error Investigation**
1. **Check errors.log first** - Critical issues and failures
2. **Check app.log** - Application flow and context
3. **Check specific component logs** - Discord, AI, user activity
4. **Look for patterns** - Repeated errors, timing issues

### **Component Loggers**
```python
# Use component-specific loggers
from core.logger import get_logger

# Component loggers (use these)
logger = get_logger(__name__)  # Automatic component detection
discord_logger = get_logger("discord")
ai_logger = get_logger("ai")
```

### **Log Levels (Priority)**
- **ERROR/CRITICAL** - System failures, data corruption
- **WARNING** - Recoverable issues, deprecated usage
- **INFO** - Normal operations, user actions
- **DEBUG** - Detailed troubleshooting information

## Troubleshooting Patterns

### **If System Won't Start**
1. Check `errors.log` for startup failures
2. Check `app.log` for configuration issues
3. Look for missing dependencies or permissions

### **If Communication Fails**
1. Check `discord.log` for bot connection issues
2. Check `errors.log` for authentication failures
3. Verify environment variables and tokens

### **If AI Features Don't Work**
1. Check `ai.log` for processing errors
2. Check `errors.log` for model or API issues
3. Verify AI configuration and dependencies

## Log Analysis Commands

### **PowerShell Log Analysis**
```powershell
# Find errors in last hour
Get-Content "logs/errors.log" | Where-Object { $_ -match "$(Get-Date -Format 'yyyy-MM-dd HH')" }

# Count error types
Get-Content "logs/errors.log" | Group-Object | Sort-Object Count -Descending

# Search for specific patterns
Select-String -Path "logs/*.log" -Pattern "ERROR|CRITICAL" -SimpleMatch
```

### **Common Error Patterns**
- **ImportError** - Missing dependencies
- **FileNotFoundError** - Configuration or data files missing
- **PermissionError** - File system access issues
- **ConnectionError** - Network or service connectivity
- **ValueError** - Data validation or parsing issues

## Log Maintenance

### **Log Rotation**
- Logs are automatically rotated when they reach size limits
- Old logs are archived in `logs/archive/`
- Keep recent logs for troubleshooting

### **Log Cleanup**
```powershell
# Check log sizes
Get-ChildItem "logs/*.log" | Select-Object Name, Length

# Archive old logs (if needed)
Move-Item "logs/*.log" "logs/archive/" -Force
```

## Component Loggers Reference

### **Available Component Loggers**
- `app` - Main application operations
- `discord` - Discord bot operations
- `ai` - AI processing and chatbot interactions
- `user_activity` - User actions and check-ins
- `communication_manager` - Communication orchestration
- `email` - Email bot operations
- `file_ops` - File operations
- `scheduler` - Scheduler operations
- `ui` - UI operations
- `message` - Message processing
- `backup` - Backup operations
- `analytics` - Analytics operations

### **Usage Pattern**
```python
from core.logger import get_component_logger

# Get component-specific logger
logger = get_component_logger("discord")
logger.info("Discord bot started")
logger.error("Failed to connect to Discord")
```

## Log Rotation and Archival

### **Rotation Schedule**
- **Daily Rotation**: Logs rotate at midnight
- **Size-based Rotation**: 5MB per file maximum
- **Retention**: 7 days for backups, 30 days for archives

### **Archival Process**
- **Backups**: Daily rotated files kept for 7 days
- **Archive**: Compressed files older than 7 days
- **Cleanup**: Automatic removal after 30 days

## Best Practices

### **Logging Guidelines**
1. **Use appropriate log levels** - ERROR for failures, INFO for operations
2. **Include context** - User ID, operation type, relevant data
3. **Avoid sensitive data** - No passwords, tokens, or personal information
4. **Use structured logging** - Consistent format for parsing
5. **Component separation** - Use component-specific loggers

### **Performance Considerations**
- **Async logging** - Non-blocking log operations
- **Buffered writes** - Efficient disk I/O
- **Rotation management** - Automatic cleanup and compression

## Migration from Old System

### **Key Changes**
- **Component-based separation** - Each component has its own log file
- **Structured logging** - Consistent format across all components
- **Automatic rotation** - Daily and size-based rotation
- **Enhanced filtering** - Better error detection and analysis

### **Migration Steps**
1. **Update imports** - Use `get_component_logger` instead of `get_logger`
2. **Component identification** - Specify component name for better organization
3. **Log level review** - Ensure appropriate levels for each message
4. **Performance testing** - Verify logging performance under load

## Resources
- **Full Guide**: `logs/LOGGING_GUIDE.md` - Complete logging system documentation
- **Error Handling**: `core/ERROR_HANDLING_GUIDE.md` - Exception handling patterns
- **Troubleshooting**: `ai_development_docs/AI_REFERENCE.md` - General troubleshooting patterns
