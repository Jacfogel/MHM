# AI Session Starter - Essential Context for New Sessions

> **Purpose**: Essential context for AI assistants starting new chat sessions  
> **Audience**: AI Assistant (Cursor, Codex, etc.)  
> **Status**: **ACTIVE** - Always include this in new sessions  
> **Version**: --scope - AI Collaboration System Active
> **Last Updated**: 2025-09-27
> **Style**: Concise, essential-only, scannable

## 🎯 **USER PROFILE (CRITICAL)**
- **Beginner programmer** with ADHD/depression
- **Windows 11** environment, PowerShell syntax required
- **Personal project** - building mental health assistant for own use
- **Values learning and efficiency** over being right
- **Prefers correction** over inefficient approaches

## 🚨 **CRITICAL RULES (Always Apply)**

### **Safety First**
- **Test**: `python run_mhm.py` must work after changes
- **Backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
- **Incremental**: Make small, tested changes
- **Document**: Update `CHANGELOG_DETAIL.md` and `AI_CHANGELOG.md`

### **Audit-First Protocol (CRITICAL)**
**BEFORE** creating any documentation or comprehensive analysis:
1. **ALWAYS** run `python ai_development_tools/ai_tools_runner.py audit` first
2. **ALWAYS** show audit results to user with statistics
3. **NEVER** create documentation from partial information
4. **ALWAYS** ask for user approval before proceeding

### **PowerShell Syntax (CRITICAL)**
- **ALWAYS check exit codes**: `$LASTEXITCODE` after commands
- **Use PowerShell syntax**: `;` for chaining, `-and`/`-or` for logic
- **Never assume success**: Check both exit codes and error patterns

### **Paired Document Maintenance (CRITICAL)**
**When updating any human-facing document, check if corresponding AI-facing document needs updates:**
- **DEVELOPMENT_WORKFLOW.md** ↔ **AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **AI_ARCHITECTURE.md**
- **DOCUMENTATION_GUIDE.md** ↔ **AI_DOCUMENTATION_GUIDE.md**
- **CHANGELOG_DETAIL.md** ↔ **AI_CHANGELOG.md**

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
- `communication/` - Communication channel implementations
- `data/users/` - User data

## 📊 **CURRENT SYSTEM STATUS**

### **Quick Status Check**
- **Check `AI_CHANGELOG.md`** for recent changes and activity
- **Check `../TODO.md`** for current priorities and tasks
- **Run `python ai_development_tools/ai_tools_runner.py status`** for comprehensive status

## 🔧 **QUICK COMMANDS**

### **Essential Commands**
```powershell
# Test system
python run_mhm.py

# Get system status
python ai_development_tools/ai_tools_runner.py status

# Run full audit
python ai_development_tools/ai_tools_runner.py audit

# Create backup
Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse
```

### **Development Workflow**
1. **Test Current**: `python run_mhm.py`
2. **Create Backup**: PowerShell backup command
3. **Make Small Changes**: Incremental approach
4. **Test After**: `python run_mhm.py`
5. **Update CHANGELOGs**: Document changes fully in `../development_docs/CHANGELOG_DETAIL.md` and concisely `AI_CHANGELOG.md`

## 💬 **COMMUNICATION GUIDELINES**

### **Response Style**
- **Simple explanations** - focus on one concept at a time
- **Step-by-step instructions** - break complex tasks into steps
- **Explain WHY** - always explain why changes are needed
- **Be patient and encouraging** - acknowledge progress and successes
- **Question assumptions** - suggest better alternatives when appropriate

### **When User Suggests Something**
- Question their goals and reasoning
- Suggest better alternatives if you see them
- Educate about relevant concepts they might not know
- Point out potential problems or inefficiencies
- Ask clarifying questions when unsure

## 📚 **FOR MORE DETAILED INFORMATION**

### **When You Need More Context**
- **`AI_REFERENCE.md`** - Complete troubleshooting and system understanding
- **`development_docs/CHANGELOG_DETAIL.md`** - Complete change history
- **`../TODO.md`** - Full task list and priorities

### **When You Need Technical Details**
- **`../ARCHITECTURE.md`** - System architecture and design
- **`../DEVELOPMENT_WORKFLOW.md`** - Detailed development practices
- **`ai_development_tools/README.md`** - Complete tool usage and configuration

### **AI-Specific Quick References**
- **`AI_DEVELOPMENT_WORKFLOW.md`** - AI-optimized development patterns
- **`AI_ARCHITECTURE.md`** - AI-optimized architectural patterns
- **`AI_DOCUMENTATION_GUIDE.md`** - AI-optimized documentation navigation

---

**Remember**: You're here to help build an awesome mental health assistant. Optimize for learning and efficiency, not perfection!

**Next Steps**: 
1. Understand the current task or request
2. Run appropriate audit if needed
3. Work incrementally with testing
4. Keep the user informed and involved