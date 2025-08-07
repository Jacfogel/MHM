# Enhanced Logging System Guide

## Overview

The MHM logging system has been enhanced with component-based separation, structured logging, and better organization. This guide explains how to use the new features.

## Directory Structure

```
logs/
├── app.log              # Main application logs (active)
├── discord.log          # Discord bot specific logs (active)
├── ai.log              # AI interactions and processing (active)
├── user_activity.log   # User actions and check-ins (active)
├── errors.log          # Error and critical messages only (active)
├── backups/            # Rotated log files (daily rotation)
└── archive/            # Compressed old logs (>7 days old)
```

### Directory Purposes

- **Active Logs**: Current log files being written to
- **Backups**: Daily rotated log files (kept for 7 days)
- **Archive**: Compressed log files older than 7 days (kept for 30 days)

## Using Component Loggers

### Basic Usage

```python
from core.logger import get_component_logger

# Get component-specific loggers
discord_logger = get_component_logger('discord')
ai_logger = get_component_logger('ai')
user_logger = get_component_logger('user_activity')
error_logger = get_component_logger('errors')
main_logger = get_component_logger('main')
```

### Logging with Structured Data

```python
# Simple logging
discord_logger.info("Discord bot connected")

# Structured logging with metadata
discord_logger.info("Discord bot connected", latency=0.1, guild_count=1)

# Error logging with context
error_logger.error("Database connection failed", retry_count=3, error_code="DB001")
```

### Available Log Levels

```python
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")
```

## Log Rotation and Archival

### Daily Rotation
- **When**: Logs rotate at midnight
- **Format**: `app.log.2025-08-07`, `discord.log.2025-08-07`, etc.
- **Location**: Rotated files stay in the same directory as active logs

### Backup Management
- **Retention**: 7 days of rotated logs kept by default
- **Location**: Rotated files remain in `logs/` directory

### Archival Process
- **Trigger**: Logs older than 7 days are automatically compressed
- **Compression**: Gzip compression to save space
- **Location**: Compressed files moved to `logs/archive/`
- **Retention**: Archived logs kept for 30 days by default

### Example File Lifecycle
1. **Day 1**: `app.log` (active)
2. **Day 2**: `app.log` (active) + `app.log.2025-08-07` (rotated)
3. **Day 8**: `app.log.2025-08-07` gets compressed to `logs/archive/app.log.2025-08-07.gz`
4. **Day 38**: `app.log.2025-08-07.gz` gets deleted

## Configuration

### Environment Variables

```bash
# Log level (WARNING, INFO, DEBUG, etc.)
LOG_LEVEL=WARNING

# Log file paths (optional, defaults shown)
LOGS_DIR=logs
LOG_MAIN_FILE=logs/app.log
LOG_DISCORD_FILE=logs/discord.log
LOG_AI_FILE=logs/ai.log
LOG_USER_ACTIVITY_FILE=logs/user_activity.log
LOG_ERRORS_FILE=logs/errors.log
```

### Component-Specific Configuration

Each component logger can be configured independently:

```python
# Get logger with custom level
discord_logger = ComponentLogger('discord', LOG_DISCORD_FILE, level=logging.DEBUG)
```

## Best Practices

### 1. Use Appropriate Components

- **Discord**: Use `discord` logger for Discord bot events
- **AI**: Use `ai` logger for AI interactions and processing
- **User Activity**: Use `user_activity` logger for user actions
- **Errors**: Use `errors` logger for error conditions
- **Main**: Use `main` logger for general application events

### 2. Include Relevant Context

```python
# Good: Include relevant metadata
user_logger.info("User check-in completed", 
                user_id="123", 
                checkin_type="daily",
                questions_answered=5)

# Avoid: Too much or irrelevant data
user_logger.info("User check-in completed", 
                user_id="123",
                timestamp="2025-08-07T01:00:00Z",  # Redundant
                random_data="unnecessary")
```

### 3. Use Structured Data for Analysis

```python
# Structured data makes logs easier to analyze
ai_logger.info("AI request processed", 
              model="phi-2", 
              response_time=2.5,
              tokens_used=150,
              confidence=0.85)
```

## Log Analysis

### Viewing Specific Logs

```bash
# View Discord logs
Get-Content logs/discord.log

# View recent errors
Get-Content logs/errors.log -Tail 20

# View user activity
Get-Content logs/user_activity.log
```

### Finding Specific Information

```bash
# Find all Discord connection events
Select-String "connected" logs/discord.log

# Find errors with specific error codes
Select-String "DB001" logs/errors.log

# Find user check-ins
Select-String "check-in" logs/user_activity.log
```

## Maintenance

### Automatic Cleanup

The system automatically:
- Rotates logs daily
- Compresses logs older than 7 days
- Maintains disk space usage

### Manual Cleanup

```python
from core.logger import cleanup_old_logs, compress_old_logs, cleanup_old_archives

# Clean up if total size exceeds 50MB
cleanup_old_logs(max_total_size_mb=50)

# Compress and archive old logs (>7 days)
compressed_count = compress_old_logs()

# Remove archived logs older than 30 days
removed_count = cleanup_old_archives(max_days=30)
```

### Automatic Maintenance

The system automatically:
- Rotates logs daily at midnight
- Compresses logs older than 7 days
- Moves compressed logs to archive directory
- Maintains disk space usage

## Migration from Old System

The new system is backward compatible. Existing code using `logging.getLogger()` will continue to work, but you can gradually migrate to component loggers for better organization.

### Before (Old System)
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Discord bot connected")
```

### After (New System)
```python
from core.logger import get_component_logger
discord_logger = get_component_logger('discord')
discord_logger.info("Discord bot connected", latency=0.1)
```

## Troubleshooting

### Log Files Not Created
- Ensure `logs/` directory exists
- Check file permissions
- Verify component name is valid

### Performance Issues
- Use appropriate log levels
- Avoid excessive structured data
- Consider using `debug` level sparingly

### Disk Space
- Monitor log file sizes
- Use `cleanup_old_logs()` if needed
- Check compression is working
