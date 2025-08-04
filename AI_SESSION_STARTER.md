# AI Session Starter - Essential Context for New Sessions

> **Purpose**: Complete context for AI assistants starting new chat sessions  
> **Audience**: AI Assistant (Cursor, Codex, etc.)  
> **Status**: **ACTIVE** - Always include this in new sessions  
> **Version**: 1.0.0  
> **Last Updated**: 2025-07-22

## 🎯 **USER PROFILE (CRITICAL)**

### **Who You're Working With**
- **Beginner programmer** with ADHD/depression
- **Windows 11** environment, PowerShell syntax required
- **Personal project** - building mental health assistant for own use
- **Values learning and efficiency** over being right
- **Will miss things** and fail to consider things - relies on AI for thoroughness
- **Prefers correction** over inefficient approaches

### **Communication Style**
- **Simple explanations** - focus on one concept at a time
- **Step-by-step instructions** - break complex tasks into steps
- **Explain WHY** - always explain why changes are needed
- **Be patient and encouraging** - acknowledge progress and successes
- **Question assumptions** - suggest better alternatives when appropriate

## 🚨 **CRITICAL RULES (Always Apply)**

### **Safety First**
- **Test**: `python run_mhm.py` must work after changes
- **Backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
- **Incremental**: Make small, tested changes
- **Document**: Update `CHANGELOG_DETAIL.md` for all changes, `AI_CHANGELOG.md` for AI context

### **Audit-First Protocol (CRITICAL)**
**BEFORE** creating any documentation, function registry, or comprehensive analysis:
1. **ALWAYS** run `python ai_tools/ai_tools_runner.py audit` first
2. **ALWAYS** show audit results to user with statistics
3. **NEVER** create documentation from partial information
4. **ALWAYS** ask for user approval before proceeding

### **PowerShell Syntax (CRITICAL)**
- **ALWAYS check exit codes**: `$LASTEXITCODE` after commands
- **Use PowerShell syntax**: `;` for chaining, `-and`/`-or` for logic
- **Never assume success**: Check both exit codes and error patterns

## 🏗️ **PROJECT OVERVIEW**

### **What We're Building**
Personal mental health assistant that helps manage executive functioning deficits and health needs, staying connected to life priorities and goals, providing motivation and hope for the future.

### **Architecture Vision**
- **Communication-First Design**: All user interactions through channels (Discord, email, etc.)
- **AI-Powered Interface**: Users interact primarily through AI chatbot with optional menus
- **No Required User UI**: Admin interface exists for management, but users never need separate UI
- **Channel-Agnostic Architecture**: Features work across all communication channels

### **Key Files (Don't Break These)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface (admin only)
- `core/config.py` - Configuration
- `core/user_data_handlers.py`, `core/user_data_validation.py` - User data management
- `bot/` - Communication channel implementations
- `data/users/` - User data

## 📊 **CURRENT SYSTEM STATUS**

### **System Health & Recent Activity**
- **Check `ai_tools/audit_summary.txt`** for current system health and metrics
- **Check `ai_tools/quick_status.py concise`** for real-time status
- **Check `AI_CHANGELOG.md`** for recent changes and activity
- **Check `TODO.md`** for current priorities and tasks

### **Known Issues & Priorities**
- **Check `ai_tools/critical_issues.txt`** for any critical issues (if file exists)
- **Check `TODO.md`** for current priorities and known issues
- **Run `python ai_tools/ai_tools_runner.py status`** for comprehensive status

## 🎯 **CURRENT PRIORITIES**

### **Getting Current Information**
- **Check `TODO.md`** for current high/medium/low priority tasks
- **Check `AI_CHANGELOG.md`** for recent development focus
- **Check `PLANS.md`** for testing status, UI migration status, and development patterns
- **Check `AI_FUNCTION_REGISTRY.md`** for function patterns and documentation status
- **Check `AI_MODULE_DEPENDENCIES.md`** for module dependency patterns and status
- **Run `python ai_tools/ai_tools_runner.py audit`** for comprehensive system analysis

## 🔧 **QUICK COMMANDS**

### **Essential Commands**
```powershell
# Test system
python run_mhm.py

# Get system status
python ai_tools/ai_tools_runner.py status

# Run full audit
python ai_tools/ai_tools_runner.py audit

# Quick status check
python ai_tools/quick_status.py concise

# Create backup
Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse
```

### **Version Sync Best Practices**
```powershell
# After doc or code changes
python ai_tools/version_sync.py sync --scope=docs
python ai_tools/version_sync.py sync --scope=core

# Before backups
python ai_tools/version_sync.py sync --scope=docs
python ai_tools/version_sync.py sync --scope=core

# Check status
python ai_tools/version_sync.py status docs
python ai_tools/version_sync.py status core
```

**Scopes:**
- `ai_docs` (default): AI documentation and cursor rules
- `docs`: All documentation files (`.md`, `.txt`, `.mdc`)
- `core`: Key system files (`run_mhm.py`, `core/service.py`, etc.)
- `all`: Everything (use with caution)

### **Development Workflow**
1. **Test Current**: `python run_mhm.py`
2. **Create Backup**: PowerShell backup command
3. **Make Small Changes**: Incremental approach
4. **Test After**: `python run_mhm.py`
5. **Update CHANGELOG**: Document changes

## 💬 **COMMON SCENARIOS**

### **User Asks for Documentation**
1. **STOP** - Don't create documentation immediately
2. **Run Audit**: `python ai_tools/ai_tools_runner.py audit`
3. **Show Results**: Display completeness statistics
4. **Get Approval**: Ask user if you should proceed
5. **Create from Data**: Use actual audit data, not assumptions

### **User Suggests Something**
1. **Question Goals**: "What's your goal with this approach?"
2. **Suggest Alternatives**: "Are you aware of [better option]?"
3. **Point Out Issues**: "Have you considered [potential problem]?"
4. **Educate**: Explain relevant concepts they might not know

### **Making Code Changes**
1. **Test Current**: `python run_mhm.py`
2. **Create Backup**: PowerShell backup command
3. **Make Small Changes**: Incremental approach
4. **Test After**: `python run_mhm.py`
5. **Update CHANGELOG**: Document changes

## 📚 **FOR MORE DETAILED INFORMATION**

### **When You Need More Context**
- **`AI_REFERENCE.md`** - Complete troubleshooting and system understanding
- **`CHANGELOG_DETAIL.md`** - Complete change history
- **`TODO.md`** - Full task list and priorities

### **When You Need Technical Details**
- **`ARCHITECTURE.md`** - System architecture and design
- **`DEVELOPMENT_WORKFLOW.md`** - Detailed development practices
- **`FUNCTION_REGISTRY_DETAIL.md`** - Complete function documentation
- **`MODULE_DEPENDENCIES_DETAIL.md`** - Module relationships and dependencies
- **`ai_tools/README.md`** - Complete tool usage and configuration

---

**Remember**: You're here to help build an awesome mental health assistant. Optimize for learning and efficiency, not perfection!

**Next Steps**: 
1. Understand the current task or request
2. Run appropriate audit if needed
3. Work incrementally with testing
4. Keep the user informed and involved