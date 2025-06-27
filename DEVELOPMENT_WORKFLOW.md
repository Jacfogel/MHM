# Development Workflow Guide

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Safe development practices and procedures  
> **Style**: Comprehensive, step-by-step, supportive

This guide explains how to work safely and effectively on the MHM project, especially designed for beginner programmers.

## 🛡️ Safety First

### Before Making Changes
1. **Create a backup** of your working code
   ```powershell
   # Create a backup folder with timestamp
   $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
   Copy-Item -Path "." -Destination "../MHM_backup_$timestamp" -Recurse
   ```

2. **Test the current state** to make sure everything works
   ```powershell
   python run_mhm.py
   ```

3. **Make small changes** - don't try to fix everything at once

### During Development
1. **Test frequently** - after each small change
2. **Keep a log** of what you're changing
3. **Ask for help** if something doesn't make sense

## 🔄 Development Process

### Step 1: Plan
- What are you trying to accomplish?
- What could go wrong?
- How will you test it?

### Step 2: Implement
- Make the smallest change possible
- Test immediately
- If it works, move to the next small change
- If it breaks, fix it before continuing

### Step 3: Test
- Test the specific feature you changed
- Test related features that might be affected
- Test the full application workflow

### Step 4: Document
- Update `IMPROVEMENTS.md` with what you changed
- Update any relevant documentation
- Note any new dependencies in `requirements.txt`

## 🧪 Testing Strategy

### Manual Testing Checklist
- [ ] Does the UI launch without errors?
- [ ] Can you create a new user?
- [ ] Can you edit user settings?
- [ ] Can you add/edit messages?
- [ ] Can you modify schedules?
- [ ] Does the service start and stop properly?
- [ ] Do messages send correctly?

### Error Testing
- [ ] What happens with invalid input?
- [ ] What happens if files are missing?
- [ ] What happens if the network is down?
- [ ] What happens if AI service is unavailable?

## 📝 Communication with AI Assistant

### When Asking for Help
1. **Be specific** about what you're trying to do
2. **Describe the problem** clearly
3. **Share error messages** if any
4. **Tell me what you've already tried**

### Example Good Questions
- "I'm trying to add a new message category called 'meditation'. I added it to the UI but it's not showing up in the dropdown. Here's the error message: [paste error]"
- "The app crashes when I try to save a schedule. I think it might be related to the time format. Can you help me debug this?"

### Example Less Helpful Questions
- "The app is broken" (too vague)
- "Fix everything" (too broad)
- "Why doesn't this work?" (without context)

## 🛠️ Common Tasks

### Adding a New Feature
1. Plan the feature in detail
2. Break it into small steps
3. Implement one step at a time
4. Test after each step
5. Document the changes

### Fixing a Bug
1. Reproduce the bug consistently
2. Identify what's causing it
3. Make the smallest fix possible
4. Test that the fix works
5. Test that you didn't break anything else

### Refactoring Code
1. Understand what the code does
2. Plan the refactoring step by step
3. Make one small change at a time
4. Test after each change
5. Update all references to the changed code

## 🚨 Emergency Procedures

### If Something Breaks Badly
1. **Don't panic** - we can always restore from backup
2. **Stop making changes** - don't make it worse
3. **Restore from backup** if needed
4. **Ask for help** - describe what happened

### If You're Stuck
1. **Take a break** - sometimes stepping away helps
2. **Write down what you know** - organize your thoughts
3. **Ask specific questions** - the more specific, the better
4. **Consider a different approach** - maybe there's an easier way

## 📚 Learning Resources

### Python Basics
- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python](https://realpython.com/) - Excellent tutorials

### Debugging
- Use `print()` statements to see what's happening
- Use the debugger in your IDE
- Check the log files in the `data/` directory

### Best Practices
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