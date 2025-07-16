# AI Quick Reference Card

> **Purpose**: One-page reference for most common AI assistant actions  
> **Version**: 1.0.0  
> **Status**: **ACTIVE**

## 🚨 **CRITICAL - ALWAYS DO FIRST**

### **Documentation Requests** → **AUDIT FIRST**
```
python ai_tools/quick_audit.py
python ai_tools/function_discovery.py
```
**Show results to user before proceeding**

### **PowerShell Commands** → **CHECK EXIT CODES**
```powershell
command; if ($LASTEXITCODE -ne 0) { "Failed" }
```

## 🔧 **COMMON WORKFLOWS**

### **Making Changes**
1. `python run_mhm.py` (test current)
2. `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
3. Make small changes
4. `python run_mhm.py` (test after)
5. Update `CHANGELOG.md`
6. **Sync versions:**
   - `python ai_tools/version_sync.py sync --scope=docs` (all docs)
   - `python ai_tools/version_sync.py sync --scope=core` (core system files)

### **Adding Dependencies**
1. Add to `requirements.txt`
2. Update `CHANGELOG.md`
3. Test: `pip install -r requirements.txt`

## 🔧 **VERSION SYNC BEST PRACTICES**
- **After doc or code changes:** Sync docs and core scopes
- **Before backups:** Sync both scopes
- **For audits/onboarding:** Use `show` and `status` for both scopes
- **Default scope:** `ai_docs` (AI docs only, fastest)
- **Expanded scopes:**
  - `docs`: All documentation files (`.md`, `.txt`, `.mdc`)
  - `core`: Key system files (`run_mhm.py`, `core/service.py`, etc.)
  - `all`: Everything (use with caution)

**Examples:**
```powershell
python ai_tools/version_sync.py sync --scope=docs
python ai_tools/version_sync.py sync --scope=core
python ai_tools/version_sync.py status docs
python ai_tools/version_sync.py status core
```

## 💬 **COMMUNICATION STYLE**

### **When User Suggests Something**
- Question their goals: "What's your goal with this approach?"
- Suggest alternatives: "Are you aware of [better option]?"
- Point out issues: "Have you considered [potential problem]?"

### **Response Guidelines**
- Simple explanations (one concept at a time)
- Step-by-step instructions
- Explain WHY changes are needed
- Acknowledge progress and successes

## 🛡️ **SAFETY RULES**

### **Key Files** (don't break these)
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `core/config.py` - Configuration
- `data/users/` - User data

### **Error Handling Pattern**
```python
try:
    result = operation()
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    return None
```

## 🎯 **USER CONTEXT**
- **Beginner programmer** with ADHD/depression
- **Windows 11** + PowerShell
- **Personal mental health assistant** project
- **Prefers correction** over inefficient approaches
- **Values learning and efficiency** over being right

## 📞 **WHEN IN DOUBT**

### **Decision Tree**
```
User Request → What Type?
├── Documentation/Registry → AUDIT FIRST
├── Code Changes → TEST FIRST  
├── PowerShell Commands → CHECK EXIT CODES
├── Architecture Decision → RUN DECISION SUPPORT
└── Unknown → ASK CLARIFYING QUESTIONS
```

### **Default Actions**
- Ask clarifying questions
- Suggest better alternatives
- Run audit scripts for data
- Test incrementally
- Explain your reasoning

## 🔧 **TROUBLESHOOTING QUICK REFERENCE**

### **Common Issues & Solutions**
- **Documentation seems incomplete** → Run `python ai_tools/quick_audit.py` and show results
- **Code changes break something** → Check `python run_mhm.py` and review recent changes
- **PowerShell commands fail** → Check `$LASTEXITCODE` and verify syntax
- **User questions accuracy** → Run audit immediately and show statistics

### **For Detailed Troubleshooting**
- **`AI_RULES.md`** - Complete troubleshooting section with step-by-step solutions
- **`AI_CONTEXT.md`** - Problem analysis and system integration guidance

## 📚 **FOR MORE INFORMATION**

### **Project Orientation**
- **`AI_ORIENTATION.md`** - Start here if you're new to this project

### **Complete Rules & Context**
- **`AI_RULES.md`** - All detailed rules and workflows
- **`AI_CONTEXT.md`** - Complete context and problem analysis
- **`ai_tools/TRIGGER.md`** - Mandatory steps for documentation

---

**Remember**: Optimize for user's learning and efficiency, not perfection! 