# AI Development Workflow - Quick Reference

> **Purpose**: Essential development patterns for AI collaborators  
> **For details**: See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md)

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

## 🔄 Git Workflow (AI Collaborators)

### **CRITICAL: PowerShell-Safe Git Commands**
**NEVER use these commands - they hang the terminal:**
- `git log` (use `git log --oneline -5 | Out-String`)
- `git show` (use `git show --name-only <commit> | Out-String`)
- `git diff` (use `git diff --name-only <commit1>..<commit2> | Out-String`)

### **Safe Git Operations**
```powershell
# Check status
git status --porcelain | Out-String

# View history
git log --oneline -5 | Out-String

# Check remote changes
git fetch origin
git diff --name-only HEAD..origin/main | Out-String

# Standard workflow
git add . && git commit -m "message" && git push origin main
```

**Why This Matters**: Git pager commands freeze PowerShell and require manual cancellation, breaking the development flow.

---

**Remember**: Small changes, frequent testing, clear communication. **ALWAYS use PowerShell-safe Git commands.**

---

## 🛡️ Safety First

### **Core Safety Rules**
1. **Always use virtual environments** - Never install packages globally
2. **Create backups before major changes** - Use PowerShell backup command
3. **Test incrementally** - Make small changes and test after each one
4. **Document everything** - Update CHANGELOG_DETAIL.md for all changes, AI_CHANGELOG.md for AI context
5. **Ask for help early** - Don't get stuck, ask specific questions
6. **Use the Audit-First Protocol** - Run audit tools before creating documentation

## 🧪 Testing Strategy

### **Incremental Testing**
- **Test after each change** - Don't make multiple changes without testing
- **Start with basic functionality** - UI launches, user creation, settings
- **Test edge cases** - Error conditions, missing data, invalid input
- **Verify no regressions** - Ensure existing features still work

### **Test Categories**
- **Unit Tests**: Individual functions and methods
- **Integration Tests**: Component interactions
- **Behavior Tests**: Real-world scenarios
- **UI Tests**: User interface functionality

## 🔧 Common Tasks

### **Adding New Features**
1. **Plan the feature** - Understand requirements and design
2. **Create backup** - Use PowerShell backup command
3. **Implement incrementally** - Small, testable changes
4. **Test thoroughly** - All scenarios and edge cases
5. **Update documentation** - CHANGELOG files and code comments

### **Fixing Bugs**
1. **Reproduce the bug** - Understand when and how it occurs
2. **Identify root cause** - Trace through code to find the issue
3. **Make minimal fix** - Don't change more than necessary
4. **Test the fix** - Verify bug is resolved and no regressions
5. **Document the fix** - Update CHANGELOG with fix details

### **Refactoring Code**
1. **Understand current code** - Read and analyze existing implementation
2. **Plan refactoring steps** - Break down into small, safe changes
3. **Make one change at a time** - Test after each change
4. **Update all references** - Ensure all code paths are updated
5. **Test thoroughly** - Verify functionality is preserved

## 🚀 Development Process

### **Daily Workflow**
1. **Activate environment** - `venv\Scripts\activate`
2. **Test current state** - `python run_mhm.py`
3. **Make planned changes** - Small, incremental steps
4. **Test after each change** - Verify functionality
5. **Document changes** - Update CHANGELOG files

### **Feature Development**
1. **Research and plan** - Understand requirements
2. **Create backup** - Before starting work
3. **Implement incrementally** - Small, testable pieces
4. **Test continuously** - After each change
5. **Document thoroughly** - Code comments and CHANGELOG

## 🚨 Emergency Procedures

### **System Won't Start**
1. **Check virtual environment** - Ensure it's activated
2. **Check dependencies** - `pip install -r requirements.txt`
3. **Check logs** - Look in `logs/` directory for errors
4. **Restore from backup** - If recent backup exists
5. **Ask for help** - Provide specific error messages

### **Tests Failing**
1. **Check test environment** - Ensure proper setup
2. **Run individual tests** - Isolate the problem
3. **Check test data** - Ensure test files exist
4. **Review recent changes** - What changed recently
5. **Restore working state** - Use git to revert if needed

### **Data Corruption**
1. **Stop the system** - Prevent further damage
2. **Restore from backup** - Use most recent backup
3. **Analyze the cause** - Understand what went wrong
4. **Fix the root cause** - Prevent recurrence
5. **Test thoroughly** - Verify system is working

## 💻 Virtual Environment Best Practices

### **Environment Management**
- **Always use virtual environment** - Never install globally
- **Activate before work** - `venv\Scripts\activate`
- **Deactivate when done** - `deactivate`
- **Keep requirements.txt updated** - Document all dependencies
- **Use consistent Python version** - Match project requirements

### **Dependency Management**
- **Install from requirements.txt** - `pip install -r requirements.txt`
- **Update requirements.txt** - When adding new packages
- **Test after dependency changes** - Ensure compatibility
- **Document version changes** - In CHANGELOG files

## 💬 Communication with AI Assistant

### **Effective Communication**
- **Ask specific questions** - "How do I fix X?" not "Help me"
- **Provide context** - What you're trying to achieve
- **Share error messages** - Include full error text
- **Explain your approach** - What you've tried so far
- **Ask for explanations** - "Why does this work?" not just "How?"

### **Getting Better Help**
- **Be specific about goals** - What outcome do you want?
- **Share relevant code** - The problematic section
- **Explain the problem** - What's not working as expected
- **Ask for alternatives** - "Is there a better way to do this?"
- **Request step-by-step guidance** - For complex tasks

## 🎯 Success Tips

### **Development Success**
- **Start small** - Don't try to do everything at once
- **Test frequently** - After every change
- **Ask questions early** - Don't get stuck for hours
- **Learn from mistakes** - Each error is a learning opportunity
- **Celebrate progress** - Acknowledge what you've accomplished

### **Learning and Growth**
- **Understand the why** - Don't just copy code
- **Experiment safely** - Use backups and test environments
- **Document your learning** - Keep notes on what you discover
- **Share your knowledge** - Help others learn from your experience
- **Stay curious** - Ask "why" and "how" questions

## 🔄 Git Workflow (PowerShell-Safe)

### **CRITICAL: PowerShell-Safe Git Commands**
**NEVER use these commands - they hang the terminal:**
- `git log` (use `git log --oneline -5 | Out-String`)
- `git show` (use `git show --name-only <commit> | Out-String`)
- `git diff` (use `git diff --name-only <commit1>..<commit2> | Out-String`)

### **Safe Git Operations**
```powershell
# Check status
git status --porcelain | Out-String

# View history
git log --oneline -5 | Out-String

# Check remote changes
git fetch origin
git diff --name-only HEAD..origin/main | Out-String

# Standard workflow
git add . && git commit -m "message" && git push origin main
```

**Why This Matters**: Git pager commands freeze PowerShell and require manual cancellation, breaking the development flow.

## What's In The Full Doc
- See `../DEVELOPMENT_WORKFLOW.md` for comprehensive guidance: Safety First, Virtual Environment Best Practices, Development Process, Testing Strategy, Emergency Procedures, Common Tasks, and PowerShell‑safe Git workflow.
