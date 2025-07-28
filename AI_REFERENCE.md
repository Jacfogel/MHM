# AI Reference - Troubleshooting & System Understanding

> **Purpose**: Complete reference for troubleshooting and deep system understanding  
> **Audience**: AI Assistant (Cursor, Codex, etc.)  
> **Style**: Concise, scannable, reference-focused  
> **Status**: **ACTIVE** - Reference when troubleshooting or needing deep insights  
> **Version**: 1.0.0 - Consolidated from AI_RULES.md and AI_CONTEXT.md

## 🚨 Critical Rules (Always Apply)

### **Core Context & User Profile**
- **Beginner programmer** with ADHD/depression
- **Windows 11** environment, PowerShell syntax required
- **Personal project** - building mental health assistant for own use
- **Values learning and efficiency** over being right
- **Will miss things** and fail to consider things - relies on AI for thoroughness
- **Prefers correction** over inefficient approaches

### **Project Purpose**
Building a personal mental health assistant that helps manage executive functioning deficits and health needs, staying connected to life priorities and goals, providing motivation and hope for the future.

### **Key Files**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface (admin only)
- `core/config.py` - Configuration
- `core/user_data_handlers.py`, `core/user_data_validation.py` - User data management
- `bot/` - Communication channel implementations
- `data/users/` - User data

## 🔧 Context Rules (Auto-Attach to *.py, *.md, *.txt)

### **PowerShell Critical Rules**
- **ALWAYS check exit codes**: `$LASTEXITCODE` after commands
- **Use PowerShell syntax**: `;` for chaining, `-and`/`-or` for logic, `$env:VARIABLE` for environment variables
- **Never assume success**: Check both exit codes and error patterns in output
- **Handle boolean returns**: Many PowerShell cmdlets return True/False without printing

### **Common Mistakes to Avoid**
- ❌ `command1 && command2` (bash syntax)
- ✅ `command1; command2` (PowerShell syntax)
- ❌ `$PATH` (bash syntax)
- ✅ `$env:PATH` (PowerShell syntax)
- ❌ Assuming empty output means failure
- ✅ Check `$LASTEXITCODE` for actual success/failure

### **Error Handling Pattern**
```python
try:
    # Operation that might fail
    result = some_operation()
except FileNotFoundError:
    logger.error(f"Required file not found: {file_path}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None
```

### **File Operations Pattern**
```python
def safe_file_operation(file_path):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None
```

## 💬 Communication Guidelines

### **Beginner Programmer Support**
**CRITICAL**: User prefers correction over inefficient approaches.

**When User Suggests Something:**
- Question their goals and reasoning
- Suggest better alternatives if you see them
- Educate about relevant concepts they might not know
- Point out potential problems or inefficiencies
- Ask clarifying questions when unsure

**Key Questions to Ask:**
- "What's your goal with this approach?"
- "Are you aware of [alternative]?"
- "What's driving this decision?"
- "Have you considered [potential issue]?"
- "Would you like me to explain [concept]?"

## 🎯 The Problem We're Solving

### **Why AI Documentation Fails**
1. **Context Window Limitations** - I can only see a small portion of your codebase at once
2. **Pattern Recognition vs. Reality** - I see patterns and assume they apply everywhere
3. **Assumption-Based Creation** - I create documentation from partial information
4. **No Verification** - I don't verify completeness before presenting
5. **Memory Limitations** - I can't remember commitments across conversations

### **The Trust Issue**
- You can't trust my work when it's only 15% complete
- This undermines our collaboration
- It wastes time and creates confusion
- It prevents us from building effectively

## 🚨 Critical Rules

### **Audit-First Protocol** (CRITICAL)
**BEFORE** creating any documentation, function registry, or comprehensive analysis:
1. **ALWAYS** run `python ai_tools/ai_tools_runner.py audit` first
2. **ALWAYS** show audit results to user with statistics
3. **NEVER** create documentation from partial information
4. **NEVER** assume patterns apply everywhere
5. **ALWAYS** ask for user approval before proceeding

### **Universal Triggers** (Stop and Audit)
- User asks for "complete" documentation
- User mentions "accuracy" or "completeness"
- User wants "function registry" or "dependency map"
- User mentions "systematic" or "comprehensive"
- User expresses concern about trust or reliability
- User asks for "support system" or "best practices"
- User requests any new documentation file
- User asks for "how to" or "what works" for collaboration
- User mentions "research" or "what others have done"
- User asks for any kind of system or framework

### **Success Criteria**
- Audit results shown before any documentation
- User approves data before proceeding
- Documentation based on actual code, not assumptions
- Completeness statistics provided
- User trusts the process

## 🔧 Troubleshooting Common Issues

### **If Documentation Seems Incomplete**
1. **Run Audit Script** - `python ai_tools/ai_tools_runner.py audit`
2. **Show Results** - Display completeness statistics
3. **Identify Gaps** - Point out what's missing
4. **Create Plan** - Plan how to fill gaps
5. **Get Approval** - Ask for user input

### **If Code Changes Break Something**
1. **Check Error Handling** - Look for error messages
2. **Run Tests** - `python run_mhm.py` to identify issues
3. **Review Changes** - Check what was modified
4. **Fix Incrementally** - Make small fixes and test
5. **Document Issues** - Update `CHANGELOG_DETAIL.md` and `AI_CHANGELOG.md`

### **If PowerShell Commands Fail**
1. **Check Exit Code** - `if ($LASTEXITCODE -ne 0)`
2. **Verify Syntax** - Use PowerShell syntax, not bash
3. **Check Paths** - Ensure files/directories exist
4. **Test Incrementally** - Run commands one at a time
5. **Log Errors** - Document what went wrong

### **If User Questions Accuracy**
1. **Run Audit** - Get actual data immediately
2. **Show Statistics** - Display completeness numbers
3. **Acknowledge Gaps** - Be honest about limitations
4. **Propose Solution** - Suggest how to improve
5. **Get Feedback** - Ask what would be most helpful

## 📊 Error Detection & Handling

### **Error Detection**
- Always check `$LASTEXITCODE` after commands
- Look for error keywords: "error", "exception", "failed", "not found"
- Don't assume success from empty output
- Handle PowerShell exceptions with try-catch

### **Error Handling**
- Check file existence before reading
- Clear error messages
- Handle missing data gracefully
- Log appropriately
- Always verify command success with exit codes

## 📊 Success Metrics

### **What Success Looks Like**
- **100% Audit-Based Documentation** - All documentation created from actual data
- **User Trust** - User can rely on AI work being accurate and complete
- **Efficient Collaboration** - No time wasted on incomplete or inaccurate work
- **Systematic Approach** - Consistent, reliable processes
- **Quality Output** - High-quality, maintainable code and documentation

### **How We Measure Success**
- **Completeness Statistics** - Audit scripts show actual coverage
- **User Confidence** - User trusts the process and results
- **Time Efficiency** - Less time spent on corrections and rework
- **Code Quality** - Fewer bugs and issues
- **Documentation Accuracy** - Documentation matches reality

## 🎯 Development Approach

### **Thoroughness**
- Always be thorough and check for consistency
- If changing a function or moving a file, check all references
- Update all related places appropriately
- Repeat as needed to ensure consistency
- You can always ask if deviating from a rule would be better

### **Safety First**
- Backup before major changes
- Test incrementally
- Make small, tested changes
- Explain the reasoning behind suggestions
- Prioritize reliability over cleverness

## 📈 Continuous Improvement

### **How We Improve the System**
1. **Track Issues** - Note when things don't work as expected
2. **Analyze Patterns** - Identify common problems
3. **Update Rules** - Modify Cursor rules based on experience
4. **Enhance Scripts** - Improve audit scripts for better analysis
5. **Refine Process** - Adjust workflows based on effectiveness

### **Success Indicators**
- **Reduced Rework** - Less time spent fixing incomplete work
- **Increased Trust** - You can rely on my output
- **Better Quality** - Higher quality code and documentation
- **Faster Progress** - More efficient development
- **Clearer Communication** - Better understanding between us

## 📚 **Related Documentation**

### **Session Starter**
- **`AI_SESSION_STARTER.md`** - Essential context for new sessions

### **Tool Documentation**
- **`ai_tools/README.md`** - Complete tool usage and configuration

---

**Remember**: This reference exists to optimize AI effectiveness and ensure accurate, trustworthy collaboration in building the mental health assistant. 