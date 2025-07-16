# AI Orientation - Welcome to MHM Project

> **Purpose**: Entry point for AI assistants encountering this project  
> **Audience**: New AI Assistant (Cursor, Codex, etc.)  
> **Status**: **ACTIVE** - Read this first
> **Version**: 1.1.0 - AI Collaboration System Active
> **Last Updated**: 2025-07-15

## 🎯 **START HERE - Essential Context**

### **User Profile (CRITICAL)**
- **Beginner programmer** with ADHD/depression
- **Windows 11** environment, PowerShell syntax required
- **Personal project** - building mental health assistant for own use
- **Values learning and efficiency** over being right
- **Will miss things** and fail to consider things - relies on AI for thoroughness
- **Prefers correction** over inefficient approaches

### **Project Purpose**
Building a personal mental health assistant that helps manage executive functioning deficits and health needs, staying connected to life priorities and goals, providing motivation and hope for the future.

### **Your Role**
- **Support learning** - explain concepts, suggest better approaches
- **Ensure safety** - test changes, create backups, work incrementally
- **Prevent problems** - audit before documentation, check assumptions
- **Optimize for efficiency** - focus on what works, not perfection

## 🚨 **CRITICAL RULES (Always Apply)**

### **Safety First**
- **Test**: `python run_mhm.py` must work after changes
- **Backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
- **Incremental**: Make small, tested changes
- **Document**: Update `CHANGELOG.md` for all changes

### **Audit-First Protocol (CRITICAL)**
**BEFORE** creating any documentation, function registry, or comprehensive analysis:
1. **ALWAYS** run `python ai_tools/quick_audit.py` first
2. **ALWAYS** show audit results to user with statistics
3. **NEVER** create documentation from partial information
4. **ALWAYS** ask for user approval before proceeding

### **PowerShell Syntax (CRITICAL)**
- **ALWAYS check exit codes**: `$LASTEXITCODE` after commands
- **Use PowerShell syntax**: `;` for chaining, `-and`/`-or` for logic
- **Never assume success**: Check both exit codes and error patterns

## 📚 **WHERE TO FIND INFORMATION**

### **Quick Start**
- **`AI_QUICK_REFERENCE.md`** - One-page reference for common actions

### **Complete Rules**
- **`AI_RULES.md`** - All detailed rules, workflows, and troubleshooting

### **Full Context**
- **`AI_CONTEXT.md`** - Complete context, problem analysis, and system integration

### **Mandatory Steps**
- **`ai_tools/TRIGGER.md`** - Required steps before documentation work

## 🎯 **COMMON SCENARIOS**

### **User Asks for Documentation**
1. **STOP** - Don't create documentation immediately
2. **Run Audit**: `python ai_tools/quick_audit.py`
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

## 🔧 **KEY FILES (Don't Break These)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `core/config.py` - Configuration
- `data/users/` - User data

## 💬 **COMMUNICATION STYLE**
- **Simple explanations** - focus on one concept at a time
- **Step-by-step instructions** - break complex tasks into steps
- **Explain WHY** - always explain why changes are needed
- **Be patient and encouraging** - acknowledge progress and successes
- **Question assumptions** - suggest better alternatives when appropriate

## 🚀 **NEXT STEPS**
1. **Read `AI_QUICK_REFERENCE.md`** for common actions
2. **Review `AI_RULES.md`** for detailed workflows
3. **Understand `AI_CONTEXT.md`** for full context
4. **Check `ai_tools/TRIGGER.md`** for mandatory steps
5. **Test the system**: `python run_mhm.py`

---

**Remember**: You're here to help build an awesome mental health assistant. Optimize for learning and efficiency, not perfection! 