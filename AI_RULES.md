# AI Rules - Consolidated Cursor Rules

> **Purpose**: All Cursor rules in one place for easy reference and maintenance  
> **Audience**: AI Assistant (Cursor, Codex, etc.)  
> **Style**: Concise, scannable, rule-focused  
> **Status**: **ACTIVE** - Optimized for AI effectiveness  
> **Version**: 1.0.0 - Consolidated from multiple files

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

### **Development Approach**
- Always be thorough and check for consistency
- If changing a function or moving a file, check all references
- Update all related places appropriately
- Repeat as needed to ensure consistency
- You can always ask if deviating from a rule would be better

### **Safety First**
- **Test**: `python run_mhm.py` must work after changes
- **Backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
- **Incremental**: Make small, tested changes
- **Document**: Update `CHANGELOG.md` for all changes

### **Key Files**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app.py` - Admin interface (admin only)
- `core/config.py` - Configuration
- `core/file_operations.py`, `core/user_management.py`, `core/message_management.py`, `core/schedule_management.py`, `core/response_tracking.py`, `core/service_utilities.py`, `core/validation.py`
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

### **Code Analysis Priority**
1. Check file existence before operations
2. Validate configuration at startup
3. Handle missing data gracefully
4. Log errors appropriately
5. Test changes incrementally

### **Common Pitfalls to Avoid**
- Don't assume files exist
- Don't make multiple changes without testing
- Don't forget to update documentation
- Don't ignore error conditions

### **Efficient Problem Solving**
1. Identify the specific issue
2. Check related files and functions
3. Make minimal changes
4. Test the fix
5. Document the solution

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

### **Configuration Validation Pattern**
```python
def validate_config():
    required_vars = ['DISCORD_BOT_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ConfigError(f"Missing required environment variables: {missing}")
```

### **Testing Pattern**
```python
# Always test after changes
def test_changes():
    try:
        subprocess.run([sys.executable, 'run_mhm.py'], 
                      capture_output=True, timeout=30)
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
```

## 📝 Documentation Rules (Auto-Attach to *.md)

### **Documentation Guidelines**
- Add new information to existing md files when possible
- Only create new md files in subdirectories that don't already have one
- Keep documentation concise and scannable

### **Scripts Organization**
- Place testing, migration, debug, and utility scripts in `scripts/` directory
- Use descriptive filenames and include comments
- Remove obsolete scripts when no longer needed
- Document significant scripts in `CHANGELOG.md`

## 🚨 Audit Rules (Auto-Attach to *.md, *.txt, *.mdc)

### **Audit-First Protocol** (CRITICAL)
**BEFORE** creating any documentation, function registry, or comprehensive analysis:
1. **ALWAYS** run `python ai_tools/quick_audit.py` first
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

### **Required Audit Scripts**
- `python ai_tools/quick_audit.py` - For comprehensive overview
- `python ai_tools/function_discovery.py` - For function analysis
- `python ai_tools/audit_function_registry.py` - For function documentation
- `python ai_tools/audit_module_dependencies.py` - For dependency maps
- `python ai_tools/analyze_documentation.py` - For documentation consolidation

### **Audit-First Workflow**
1. **Run audit script** to get actual data
2. **Show results** to user with statistics
3. **Ask for approval** before proceeding
4. **Use audit data** as foundation for documentation
5. **Verify completeness** before presenting

### **Success Criteria**
- Audit results shown before any documentation
- User approves data before proceeding
- Documentation based on actual code, not assumptions
- Completeness statistics provided
- User trusts the process

### **Failure Prevention**
- If no audit script exists, create one first
- If audit shows gaps, acknowledge them
- If user questions accuracy, run audit
- If documentation seems incomplete, run audit

## 💬 Communication Guidelines

### **Response Guidelines**
- Keep explanations simple and clear
- Focus on one concept at a time
- Provide step-by-step instructions
- Always suggest testing after changes
- Explain WHY changes are needed
- Break complex tasks into steps
- Acknowledge progress and successes
- Question assumptions and suggest better alternatives

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

## 🔄 Development Workflow

### **Standard Workflow**
1. **Test current state**: `python run_mhm.py`
2. **Create backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
3. **Make incremental changes**
4. **Test after each change**
5. **Update documentation**: `CHANGELOG.md`

### **Common Development Tasks**

#### **Adding New Feature**
1. Plan the feature
2. Create backup: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
3. Implement incrementally
4. Test: `python run_mhm.py`
5. Update `CHANGELOG.md`

#### **Fixing Bug**
1. Reproduce the bug
2. Identify root cause
3. Make minimal fix
4. Test fix works
5. Test nothing else broke

#### **Refactoring Code**
1. Understand current code
2. Plan refactoring steps
3. Make one change at a time
4. Test after each change
5. Update all references

#### **Adding Dependencies**
1. Add to `requirements.txt`
2. Update `CHANGELOG.md`
3. Test installation: `pip install -r requirements.txt`
4. Test functionality

#### **Configuration Changes**
1. Update `core/config.py`
2. Test configuration loading
3. Update documentation if needed
4. Test affected features

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

## 🔧 Troubleshooting Common Issues

### **If Documentation Seems Incomplete**
1. **Run Audit Script** - `python ai_tools/quick_audit.py`
2. **Show Results** - Display completeness statistics
3. **Identify Gaps** - Point out what's missing
4. **Create Plan** - Plan how to fill gaps
5. **Get Approval** - Ask for user input

### **If Code Changes Break Something**
1. **Check Error Handling** - Look for error messages
2. **Run Tests** - `python run_mhm.py` to identify issues
3. **Review Changes** - Check what was modified
4. **Fix Incrementally** - Make small fixes and test
5. **Document Issues** - Update `CHANGELOG.md`

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

## 📚 **Related Documentation**

### **Project Orientation**
- **`AI_ORIENTATION.md`** - Start here if you're new to this project

### **Quick Reference**
- **`AI_QUICK_REFERENCE.md`** - One-page reference for common actions

### **Complete Context**
- **`AI_CONTEXT.md`** - Full context, problem analysis, and system integration

### **Mandatory Steps**
- **`ai_tools/TRIGGER.md`** - Required steps before documentation work

---

**Remember**: These rules exist to optimize AI effectiveness and ensure accurate, trustworthy collaboration in building the mental health assistant. 