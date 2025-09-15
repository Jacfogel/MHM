# Development Workflow Guide

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Safe development practices and procedures  
> **Style**: Comprehensive, step-by-step, supportive

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for AI-optimized quick reference**

## 🚀 Quick Reference

### **Essential Commands**
```powershell
# Activate environment
venv\Scripts\activate

# Test system
python run_mhm.py

# Create backup
Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse

# Install dependencies
pip install -r requirements.txt
```

### **Development Decision Tree**
1. **Making Changes?** → Create backup first
2. **Adding Features?** → Test incrementally
3. **Fixing Bugs?** → Reproduce, fix, test
4. **Need Help?** → Ask specific questions
5. **Documenting?** → Update CHANGELOG files

## 🛡️ Safety First

### **Core Safety Rules**
1. **Always use virtual environments** - Never install packages globally
2. **Create backups before major changes** - Use PowerShell backup command
3. **Test incrementally** - Make small changes and test after each one
4. **Document everything** - Update CHANGELOG_DETAIL.md for all changes, AI_CHANGELOG.md for AI context
5. **Ask for help early** - Don't get stuck, ask specific questions
6. **Use the Audit-First Protocol** - Run audit tools before creating documentation

### **Before Making Changes**
1. **Ensure your virtual environment is activated**
   ```powershell
   # You should see (venv) at the start of your command prompt
   # If not, activate it:
   venv\Scripts\activate
   ```

2. **Create a backup** of your working code
   ```powershell
   # Create a backup folder with timestamp
   $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
   Copy-Item -Path "." -Destination "../MHM_backup_$timestamp" -Recurse
   ```

3. **Test the current state** to make sure everything works
   ```powershell
   python run_mhm.py
   ```

4. **Make small changes** - don't try to fix everything at once

## 🔧 Virtual Environment Best Practices

### **Why Use a Virtual Environment?**
- **Keeps your system Python clean** - no conflicts with other projects
- **Makes dependencies explicit** - all requirements are listed in `requirements.txt`
- **Prevents permission issues** - no need to install packages globally
- **Makes the project portable** - anyone can recreate the exact same environment

### **Virtual Environment Commands**
```powershell
# Create virtual environment (only needed once)
python -m venv venv

# Activate virtual environment (needed every time you work on the project)
venv\Scripts\activate

# Install dependencies (after activation)
pip install -r requirements.txt

# Add new dependencies
pip install package_name
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

### **Common Virtual Environment Issues**
- **"Command not found"**: Make sure virtual environment is activated
- **Import errors**: Try `pip install -r requirements.txt --force-reinstall`
- **Permission errors**: Run PowerShell as Administrator or adjust execution policy

## 🔄 Development Process

### **Step 1: Plan**
- What are you trying to accomplish?
- What could go wrong?
- How will you test it?
- **For new features**: How will users interact with this through communication channels?

### **Step 2: Implement**
- Make the smallest change possible
- Test immediately
- If it works, move to the next small change
- If it breaks, fix it before continuing
- **Remember**: All user-facing features must work through communication channels
- **User Data Access**: All user data access must use the unified `get_user_data()` handler. Legacy user data functions are no longer present in the codebase.

### **Step 3: Test**
- Test the specific feature you changed
- Test related features that might be affected
- Test the full application workflow
- **Test communication channels**: Verify features work through communication channels, especially Discord

### **Step 4: Document**
- Update `development_docs/CHANGELOG_DETAIL.md` with what you changed
- Update `ai_development_docs/AI_CHANGELOG.md` with brief summary for AI context
- Update any relevant documentation
- Note any new dependencies in `requirements.txt`
- **Update communication docs**: Document how users interact with new features

## 🧪 Testing Strategy

### **Manual Testing Checklist**
- [ ] Does the UI launch without errors?
- [ ] Can you create a new user with feature-based account creation?
- [ ] Can you edit user settings and personalization?
- [ ] Can you manage message categories and schedules?
- [ ] Does the service start and stop properly?
- [ ] Do messages send correctly through Discord/other channels?

### **Error Testing**
- [ ] What happens with invalid input?
- [ ] What happens if files are missing?
- [ ] What happens if the network is down?
- [ ] What happens if AI service is unavailable?

## 📝 Communication with AI Assistant

### **When Asking for Help**
1. **Be specific** about what you're trying to do
2. **Describe the problem** clearly
3. **Share error messages** if any
4. **Tell me what you've already tried**

### **Example Good Questions**
- "I'm trying to add a new message category called 'meditation'. I added it to the UI but it's not showing up in the dropdown. Here's the error message: [paste error]"
- "The app crashes when I try to save a schedule. I think it might be related to the time format. Can you help me debug this?"

### **Example Less Helpful Questions**
- "The app is broken" (too vague)
- "Fix everything" (too broad)
- "Why doesn't this work?" (without context)

## 🛠️ Common Tasks

### **Adding a New Feature**
1. Plan the feature in detail
2. Break it into small steps
3. Implement one step at a time
4. Test after each step
5. Document the changes

### **Fixing a Bug**
1. Reproduce the bug consistently
2. Identify what's causing it
3. Make the smallest fix possible
4. Test that the fix works
5. Test that you didn't break anything else

### **Refactoring Code**
1. Understand what the code does
2. Plan the refactoring step by step
3. Make one small change at a time
4. Test after each change
5. Update all references to the changed code

## 🚨 Emergency Procedures

### **If Something Breaks Badly**
1. **Don't panic** - we can always restore from backup
2. **Stop making changes** - don't make it worse
3. **Restore from backup** if needed
4. **Ask for help** - describe what happened

### **If You're Stuck**
1. **Take a break** - sometimes stepping away helps
2. **Write down what you know** - organize your thoughts
3. **Ask specific questions** - the more specific, the better
4. **Consider a different approach** - maybe there's an easier way

## 📚 Learning Resources

### **Python Basics**
- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/) - Excellent tutorials

### **Debugging**
- Use `print()` statements to see what's happening
- Use the debugger in your IDE
- Check the log files in the `data/` directory

### **Best Practices**
- Write clear, descriptive variable names
- Add comments to explain complex logic
- Keep functions small and focused
- Test your code frequently

## 🎯 Success Tips

1. **Start small** - don't try to build everything at once
2. **Test often** - catch problems early
3. **Ask questions** - there's no such thing as a stupid question
4. **Celebrate progress** - every small improvement counts
5. **Be patient** - learning takes time, and that's okay

Remember: You're building something important for your mental health. It's worth taking the time to do it right, and it's okay to ask for help along the way.

## 🔄 Git Workflow (PowerShell-Safe)

### **Critical: Avoid Git Paging Issues**
Git commands like `git log`, `git show`, and `git diff` can open in a pager that hangs the terminal. **Always use these PowerShell-safe alternatives:**

#### **❌ Commands That Hang (Avoid These)**
```powershell
git log                    # Hangs - opens pager
git show <commit>          # Hangs - opens pager  
git diff <commit>          # Hangs - opens pager
```

#### **✅ PowerShell-Safe Alternatives**
```powershell
# View commit history
git log --oneline -5 | Out-String

# View specific commit changes
git show --name-only <commit> | Out-String

# View file differences
git diff --name-only <commit1>..<commit2> | Out-String

# View status
git status --porcelain | Out-String
```

### **Standard Git Workflow**
```powershell
# 1. Check status (safe)
git status --porcelain | Out-String

# 2. Add changes
git add .

# 3. Commit changes
git commit -m "Descriptive commit message"

# 4. Pull remote updates (safe)
git fetch origin
git diff --name-only HEAD..origin/main | Out-String

# 5. Merge/pull (if needed)
git pull origin main

# 6. Push changes
git push origin main
```

### **Handling Merge Conflicts**
```powershell
# If merge conflicts occur:
git status --porcelain | Out-String

# Resolve conflicts in files, then:
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### **Why This Matters**
- **Terminal Hanging**: Git pager commands freeze PowerShell and require manual cancellation
- **Productivity**: Safe commands complete immediately and show results
- **Consistency**: Same workflow works every time without surprises
- **Team Collaboration**: Reliable Git operations for smooth development

**Remember**: Always use `| Out-String` with Git commands that might produce long output to avoid paging issues. 