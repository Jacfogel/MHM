# AI Development Workflow - Quick Reference

> **Purpose**: Essential development patterns for AI collaborators  
> **For details**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)

## 🎯 **CRITICAL: Code Quality Philosophy**

### **User's Strong Preference: Clean, Well-Designed Code**
- **NEVER accept "worse is better" shortcuts** - User strongly prefers thorough, clean refactoring
- **Quality over speed**: Take time to do it right, not fast
- **Remove unnecessary wrappers**: Don't keep functions that just delegate to other functions
- **Consolidate duplicates**: Eliminate code duplication even if it requires more work
- **Clean architecture**: Prefer clean, maintainable code over quick hacks
- **Thorough refactoring**: When refactoring, do it completely and properly

### **Code Quality Standards**
- **No unnecessary wrappers**: Functions should add value, not just delegate
- **Consolidate duplicates**: Multiple identical functions should be unified
- **Clean interfaces**: APIs should be simple and consistent
- **Proper error handling**: Handle errors gracefully, not just ignore them
- **Comprehensive testing**: Test thoroughly, not just happy path

## 🚀 Quick Commands
```powershell
python run_mhm.py                    # Test system
Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse  # Backup
pip install -r requirements.txt      # Install deps
```

## 🛡️ Safety Rules
- **Always test**: `python run_mhm.py` before/after changes
- **Always backup**: Before major changes
- **Small changes**: One change at a time
- **Document**: Update CHANGELOG files

## 🔧 Development Patterns

### **New Feature**
1. Plan → Backup → Implement → Test → Document

### **Bug Fix**
1. Reproduce → Identify → Fix → Test → Verify

### **Refactoring**
1. Understand → Plan → Execute → Test → Update

## 🧪 Testing Checklist
- [ ] UI launches
- [ ] User creation works
- [ ] Settings editable
- [ ] Service starts/stops
- [ ] Communication channels work

## 📝 Documentation Updates
- **CHANGELOG_DETAIL.md**: Complete history
- **AI_CHANGELOG.md**: Brief AI context
- **requirements.txt**: New dependencies

## 🚨 Emergency
1. Stop → Restore → Analyze → Fix → Test

## 💬 Communication
- **Ask specifics**: "What are you trying to do?"
- **Guide don't solve**: Explain why, not just how
- **Encourage**: Acknowledge progress

---

**Remember**: Small changes, frequent testing, clear communication.
