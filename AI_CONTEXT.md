# AI Context - Single Source of Truth

> **Purpose**: Complete context and rules for AI-assisted development  
> **Audience**: AI Assistant (Cursor, Codex, etc.)  
> **Style**: Concise, scannable, action-oriented  
> **Status**: **ACTIVE** - Optimized for AI effectiveness  
> **Version**: 1.0.0 - Consolidated from multiple files

## 🎯 Core Context

### **User Profile**
- **Beginner programmer** with ADHD/depression
- **Windows 11** environment, PowerShell syntax required
- **Personal project** - building mental health assistant for own use
- **Values learning and efficiency** over being right
- **Will miss things** and fail to consider things - relies on AI for thoroughness
- **Prefers correction** over inefficient approaches

### **Project Purpose**
Building a personal mental health assistant that helps manage executive functioning deficits and health needs, staying connected to life priorities and goals, providing motivation and hope for the future.

### **Project Vision**
- **Communication-First Design**: All user interactions through channels (Discord, email, etc.)
- **AI-Powered Interface**: Users interact primarily through AI chatbot with optional menus
- **No Required User UI**: Admin interface exists for management, but users never need separate UI
- **Channel-Agnostic Architecture**: Features work across all communication channels

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

## 🛡️ Core Development Rules

### **Safety First**
- **Test**: `python run_mhm.py` must work after changes
- **Backup**: `Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse`
- **Incremental**: Make small, tested changes
- **Document**: Update `CHANGELOG_DETAIL.md` for all changes, `CHANGELOG_BRIEF.md` for AI context

### **Key Files**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface (admin only)
- `core/config.py` - Configuration
- `core/file_operations.py`, `core/user_management.py`, `core/message_management.py`, `core/schedule_management.py`, `core/response_tracking.py`, `core/service_utilities.py`, `core/validation.py`, `core/user_data_validation.py`
- `bot/` - Communication channel implementations
- `data/users/` - User data

### **Development Workflow**
1. **Test current state**: `python run_mhm.py`
2. **Create backup**: PowerShell backup command
3. **Make incremental changes**
4. **Test after each change**
5. **Update documentation**: `CHANGELOG_DETAIL.md` and `CHANGELOG_BRIEF.md`

## 🚨 Critical Rules

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

### **Success Criteria**
- Audit results shown before any documentation
- User approves data before proceeding
- Documentation based on actual code, not assumptions
- Completeness statistics provided
- User trusts the process

## 💬 Communication Guidelines

### **Response Style**
- **Simple explanations** - focus on one concept at a time
- **Step-by-step instructions** - break complex tasks into steps
- **Explain WHY** - always explain why changes are needed
- **Be patient and encouraging** - acknowledge progress and successes
- **Question assumptions** - suggest better alternatives when appropriate

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

## 🔧 Error Handling & Quality

### **Error Handling Patterns**
- Check file existence before operations
- Clear error messages
- Handle missing data gracefully
- Log appropriately
- Always verify command success with exit codes

### **Code Quality Patterns**
```python
# File Operations Pattern
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

# Testing Pattern
def test_changes():
    try:
        subprocess.run([sys.executable, 'run_mhm.py'], 
                      capture_output=True, timeout=30)
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
```

## 🛠️ AI Tools Reference

### **Primary Tools** (in `ai_tools/` directory)
- **`quick_audit.py`** - One-click comprehensive audit of entire codebase
- **`function_discovery.py`** - Find and categorize all functions
- **`decision_support.py`** - Dashboard with actionable insights
- **`validate_ai_work.py`** - Validate work before presenting to user
- **`audit_function_registry.py`** - Check function documentation completeness
- **`audit_module_dependencies.py`** - Analyze module dependencies
- **`analyze_documentation.py`** - Find documentation overlap

### **Configuration**
- **`ai_tools/config.py`** - Centralized configuration for all tools
- **`ai_tools/TRIGGER.md`** - Mandatory steps before documentation

### **Best Practices**
1. **Always run `quick_audit.py` first** to get the full picture
2. **Use `decision_support.py`** for actionable insights
3. **Validate with `validate_ai_work.py`** before presenting to user
4. **Check `TRIGGER.md`** for mandatory steps
5. **Customize `config.py`** for project-specific needs

## 🔄 How This System Works Together

### **For Documentation Requests**
1. **Trigger**: You ask for documentation
2. **Constraint**: Audit-First Protocol activates
3. **Action**: I run relevant audit script
4. **Verification**: I show you results with statistics
5. **Approval**: You approve or request changes
6. **Creation**: I create documentation from actual data

### **For Code Changes**
1. **Trigger**: You request code changes
2. **Context**: Cursor rules provide guidance
3. **Safety**: Error handling framework catches issues
4. **Testing**: Testing framework verifies changes
5. **Documentation**: Changes are documented in CHANGELOG_DETAIL.md and CHANGELOG_BRIEF.md

### **For Problem Solving**
1. **Analysis**: I use audit scripts to understand current state
2. **Planning**: I create a plan based on actual data
3. **Implementation**: I make changes incrementally
4. **Verification**: I test changes and show results
5. **Documentation**: I update relevant documentation

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

---

## 🔧 Troubleshooting

### **If Documentation Seems Incomplete**
1. **Run Audit Script** - Get actual statistics
2. **Show Results** - Display completeness data
3. **Identify Gaps** - Point out what's missing
4. **Create Plan** - Plan how to fill gaps
5. **Get Approval** - Ask for your input

### **If Code Changes Break Something**
1. **Check Error Handling** - Look for error messages
2. **Run Tests** - Use testing framework to identify issues
3. **Review Changes** - Check what was modified
4. **Fix Incrementally** - Make small fixes and test
5. **Document Issues** - Update documentation with lessons learned

### **If Collaboration Feels Inefficient**
1. **Review Process** - Check if we're following the system
2. **Identify Bottlenecks** - Find what's slowing us down
3. **Adjust Approach** - Modify the process if needed
4. **Communicate** - Discuss what's working and what isn't
5. **Improve System** - Enhance the collaboration framework

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

### **Project Orientation**
- **`AI_ORIENTATION.md`** - Start here if you're new to this project

### **Quick Reference**
- **`AI_QUICK_REFERENCE.md`** - One-page reference for common actions

### **Complete Rules**
- **`AI_RULES.md`** - All detailed rules, workflows, and troubleshooting

### **Mandatory Steps**
- **`ai_tools/TRIGGER.md`** - Required steps before documentation work

---

**Remember**: The primary purpose is building an awesome mental health assistant. Documentation and tools exist to support this goal by optimizing AI effectiveness and ensuring accurate, trustworthy collaboration. 