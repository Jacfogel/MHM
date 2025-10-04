# AI Logging Guide - Quick Reference

> **Purpose**: Fast logging patterns and troubleshooting for AI collaborators  
> **Style**: Concise, pattern-focused, actionable  
> **For details**: See [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md)

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

## Resources
- **Full Guide**: `logs/LOGGING_GUIDE.md` - Complete logging system documentation
- **Error Handling**: `core/ERROR_HANDLING_GUIDE.md` - Exception handling patterns
- **Troubleshooting**: `ai_development_docs/AI_REFERENCE.md` - General troubleshooting patterns
