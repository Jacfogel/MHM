# AI Reference - Troubleshooting & System Understanding

> **Purpose**: Troubleshooting patterns and deep system understanding for AI collaborators  
> **For context**: See [AI_SESSION_STARTER.md](AI_SESSION_STARTER.md)

## 🚨 **Troubleshooting Patterns**

### **If Documentation Seems Incomplete**
1. **Run Audit Script** - `python ai_development_tools/ai_tools_runner.py audit`
2. **Show Results** - Display completeness statistics
3. **Identify Gaps** - Point out what's missing
4. **Create Plan** - Plan how to fill gaps
5. **Get Approval** - Ask for user input

### **If Code Changes Break Something**
1. **Check Error Handling** - Look for error messages
2. **Run Tests** - `python run_mhm.py` to identify issues (launches UI only - background service started separately)
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

## 💬 **Communication Patterns**

### **When User Suggests Something**
- Question their goals and reasoning
- Suggest better alternatives if you see them
- Educate about relevant concepts they might not know
- Point out potential problems or inefficiencies
- Ask clarifying questions when unsure

### **Key Questions to Ask**
- "What's your goal with this approach?"
- "Are you aware of [alternative]?"
- "What's driving this decision?"
- "Have you considered [potential issue]?"
- "Would you like me to explain [concept]?"

## 🎯 **System Understanding**

### **Critical Files (Don't Break)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface
- `core/user_data_handlers.py` - Unified user data access
- `communication/core/channel_orchestrator.py` - Communication coordination

### **Data Flow Patterns**
- **User Data**: `data/users/{user_id}/` → `core/user_data_handlers.py` → UI/CommunicationManager
- **Messages**: `resources/default_messages/` → `data/users/{user_id}/messages/`
- **Configuration**: `.env` → `core/config.py` → Application

### **Common Issues**
- **Data Access**: Use `get_user_data()` handler only
- **UI Integration**: Use proper data handlers, not direct file manipulation
- **Configuration**: Use `core/config.py` for all configuration

## 📊 **Success Metrics**

### **What Success Looks Like**
- **100% Audit-Based Documentation** - All documentation created from actual data
- **User Trust** - User can rely on AI work being accurate and complete
- **Efficient Collaboration** - No time wasted on incomplete or inaccurate work
- **Systematic Approach** - Consistent, reliable processes

---

**Remember**: Run audits for accuracy unless the user explicitly says they already ran it, fix incrementally, maintain user trust. 

---

## What's In The Full Doc
- For deeper explanations and the full troubleshooting playbook, see `../DOCUMENTATION_GUIDE.md`, `../ARCHITECTURE.md`, and `../DEVELOPMENT_WORKFLOW.md`. This AI quick reference mirrors those docs at a high level for fast, context‑aware assistance.

## Specialized Technical Guides
- **`AI_LOGGING_GUIDE.md`** - Logging patterns, troubleshooting, and log analysis
- **`AI_TESTING_GUIDE.md`** - Testing patterns, test categories, and troubleshooting
- **`AI_ERROR_HANDLING_GUIDE.md`** - Error handling patterns, recovery strategies, and prevention
