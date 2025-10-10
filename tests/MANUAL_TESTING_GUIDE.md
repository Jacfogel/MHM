# MHM Manual Testing Guide

> **Audience**: Developers and testers performing manual testing for scenarios not covered by automation  
> **Purpose**: Comprehensive manual testing guide focusing on visual verification, user experience, and real-world integration  
> **Style**: Step-by-step, checklist-focused, testing-oriented  
> **Status**: **ACTIVE** - Focused on non-automated scenarios  
> **Last Updated**: 2025-09-28

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **Automated Testing Coverage**
✅ **Fully Automated**: All 7 UI dialog types, Discord commands, error handling, data persistence  
✅ **Test Commands**: `python -m pytest tests/behavior/test_*automation* -v`

### **Manual Testing Focus**
1. **Visual Design** - Layout, styling, responsive design
2. **User Experience** - Usability, accessibility, workflow efficiency
3. **Performance** - Real-world performance under user conditions
4. **Integration** - External system interactions (Discord, email, etc.)
5. **Cross-Platform** - Different operating systems, screen sizes


### **Before Starting**
- [ ] Run automated tests first: `python -m pytest tests/behavior/test_*automation* -v`
- [ ] Run `python run_headless_service.py start` to ensure system starts
- [ ] Have a test user ready (or create one)
- [ ] Focus on visual and UX aspects not covered by automation


---

## 📊 **Manual Testing Focus Areas**

### **Visual & UX Testing**
- **Layout Quality** - Are dialogs properly sized and positioned?
- **Visual Consistency** - Do all dialogs follow the same design patterns?
- **Responsive Design** - Do dialogs work on different screen sizes?
- **Accessibility** - Are dialogs usable with keyboard navigation?

### **Performance Testing**
- **Load Times** - How quickly do dialogs open and close?
- **Memory Usage** - Does the system remain stable during extended use?
- **Resource Usage** - CPU and memory consumption under normal use

### **Integration Testing**
- **Discord Integration** - Real Discord server testing
- **Email Integration** - Actual email sending/receiving
- **File System** - Real file operations and permissions

---

## 📝 **Manual Testing Scenarios**

### **1. Visual Design & Layout Testing**
- [ ] **Dialog Sizing** - Are all dialogs properly sized and positioned?
- [ ] **Layout Consistency** - Do all dialogs follow consistent design patterns?
- [ ] **Widget Alignment** - Are buttons, fields, and labels properly aligned?
- [ ] **Color Scheme** - Is the color scheme consistent across all dialogs?
- [ ] **Typography** - Are fonts, sizes, and styles consistent?

### **2. User Experience Testing**
- [ ] **Navigation Flow** - Is the dialog opening/closing workflow intuitive?
- [ ] **Keyboard Navigation** - Can users navigate with Tab, Enter, Escape keys?
- [ ] **Accessibility** - Are dialogs usable for users with different needs?
- [ ] **Error Messages** - Are error messages clear and helpful?
- [ ] **Loading States** - Are loading indicators clear and informative?

### **3. Performance Testing**
- [ ] **Dialog Load Times** - How quickly do dialogs open and close?
- [ ] **Memory Usage** - Does memory usage remain stable during extended use?
- [ ] **CPU Usage** - Is CPU usage reasonable during normal operations?
- [ ] **Resource Cleanup** - Are resources properly cleaned up when dialogs close?

### **4. Integration Testing**
- [ ] **Discord Integration** - Test with real Discord server and bot
- [ ] **Email Integration** - Test actual email sending/receiving
- [ ] **File System** - Test file operations with real file system
- [ ] **Cross-Platform** - Test on different operating systems (if applicable)

### **5. Edge Case Testing**
- [ ] **Large Data Sets** - Test with users having many categories, tasks, etc.
- [ ] **Special Characters** - Test with special characters in names, descriptions
- [ ] **Network Issues** - Test behavior when network connectivity is poor
- [ ] **System Resources** - Test behavior when system resources are low

---

## 🤖 **Discord Manual Testing**

### **Prerequisites**
- Discord bot token configured (`DISCORD_BOT_TOKEN`)
- Bot invited to test server with appropriate permissions
- MHM service running (`python run_headless_service.py start`)
- Test user account available
- **Run automated tests first**: `python -m pytest tests/behavior/test_discord_automation_complete.py -v`

### **Automated Coverage Status**
✅ **All 15 Basic Scenarios** - Fully automated with comprehensive testing  
✅ **All Command Types** - Natural language, slash, and bang commands  
✅ **All Help Systems** - General help, category-specific help, examples  
✅ **All Flow Management** - Check-in flows, flow cancellation, flow clearing  
✅ **All Edge Cases** - Unknown commands, malformed commands, incomplete data  

### **A. Visual & UX Verification**

#### Discord Embed Quality
- [ ] **Rich Embeds** - Do slash commands display proper Discord embeds?
- [ ] **Button Interactions** - Do suggestion buttons work correctly?
- [ ] **Color Schemes** - Are embed colors consistent and appropriate?
- [ ] **Field Organization** - Are embed fields properly structured and readable?
- [ ] **Markdown Formatting** - Is text formatting consistent and readable?

#### Message Formatting
- [ ] **Text Formatting** - Are natural language responses properly formatted?
- [ ] **Bullet Points** - Are lists properly formatted with bullet points?
- [ ] **Headers** - Are section headers clearly distinguished?
- [ ] **Code Blocks** - Are code examples properly formatted?
- [ ] **Line Breaks** - Are messages properly spaced and readable?

### **B. User Experience Testing**

#### Conversation Flow
- [ ] **Natural Flow** - Do conversations feel natural and intuitive?
- [ ] **Context Preservation** - Is user context maintained across interactions?
- [ ] **Response Timing** - Are response times acceptable for user experience?
- [ ] **Error Recovery** - Can users easily recover from errors?
- [ ] **Help Integration** - Is help easily accessible when needed?

#### Command Discovery
- [ ] **Command Suggestions** - Are users guided to available commands?
- [ ] **Help Navigation** - Is the help system easy to navigate?
- [ ] **Example Quality** - Are examples practical and useful?
- [ ] **Category Organization** - Are commands logically categorized?

### **C. Real-World Integration Testing**

#### Discord Server Integration
- [ ] **Bot Permissions** - Does the bot have all necessary permissions?
- [ ] **Server Settings** - Does the bot work with different server configurations?
- [ ] **User Permissions** - Does the bot respect user permission levels?
- [ ] **Channel Types** - Does the bot work in different channel types?

#### Performance Under Load
- [ ] **Multiple Users** - Does the bot handle multiple simultaneous users?
- [ ] **Long Conversations** - Does the bot maintain performance in long conversations?
- [ ] **Memory Usage** - Does the bot maintain stable memory usage?
- [ ] **Response Consistency** - Are responses consistent under load?

### **D. Cross-Platform Testing**

#### Different Discord Clients
- [ ] **Desktop App** - Does the bot work properly in Discord desktop app?
- [ ] **Web Browser** - Does the bot work properly in Discord web client?
- [ ] **Mobile App** - Does the bot work properly in Discord mobile app?
- [ ] **Feature Parity** - Are all features available across platforms?

#### Network Conditions
- [ ] **Slow Connections** - How does the bot behave with slow internet?
- [ ] **Intermittent Connectivity** - How does the bot handle connection drops?
- [ ] **High Latency** - How does the bot behave with high latency connections?
- [ ] **Recovery** - Does the bot recover gracefully from network issues?

---

## 🚨 **Critical Issues to Watch For**

### **High Priority**
- [ ] **Visual Issues**: Missing widgets, broken layouts, styling problems
- [ ] **Performance Issues**: Slow loading, unresponsive UI, memory leaks
- [ ] **Integration Issues**: Discord/email not working, file system problems
- [ ] **Accessibility Issues**: Keyboard navigation, screen reader compatibility

### **Medium Priority**
- [ ] **UX Issues**: Confusing workflows, unclear error messages
- [ ] **Cross-Platform Issues**: Different behavior on different systems
- [ ] **Resource Issues**: High CPU/memory usage, poor cleanup

### **Low Priority**
- [ ] **Minor Visual Issues**: Slight alignment problems, color inconsistencies
- [ ] **Minor UX Issues**: Non-critical workflow improvements

---

## 📋 **Testing Summary**

### **Overall Results**
- [ ] All dialogs open without errors
- [ ] All dialogs display correctly
- [ ] All integrations work properly
- [ ] Performance is acceptable
- [ ] User experience is intuitive

### **Issues Found**
```
Critical Issues: ________
High Priority Issues: ________
Medium Priority Issues: ________
Low Priority Issues: ________
```

### **Next Steps**
- [ ] Fix critical issues first
- [ ] Address high priority issues
- [ ] Document all findings
- [ ] Update TODO.md with results
- [ ] Plan fixes for identified issues

---

## 📊 **Expected Results**

### **✅ What Should Work**
- All dialogs should open without errors
- All widgets should display correctly
- Discord integration should work smoothly
- Performance should be acceptable
- UI should be responsive and user-friendly

### **⚠️ Known Issues**
- Some dialogs may need performance optimization
- Cross-platform compatibility may need testing
- Network connectivity issues may affect Discord integration

### **🔍 What to Look For**
- **Visual Issues**: Missing widgets, broken layouts, styling problems
- **Performance Issues**: Slow loading, unresponsive UI, memory issues
- **Integration Issues**: Discord/email not working, file system problems
- **UX Issues**: Confusing workflows, unclear error messages

---

## 📝 **Reporting Results**

When testing, document:
1. **Test Area**: Which area was tested (UI, Discord, Performance, etc.)
2. **Test Steps**: What was tested
3. **Expected Result**: What should happen
4. **Actual Result**: What actually happened
5. **Issues Found**: Any problems encountered
6. **Severity**: Critical, High, Medium, Low

## 🎯 **Success Criteria**

A feature is considered **fully functional** if:
- ✅ Opens without errors
- ✅ All widgets display correctly
- ✅ Integration works properly
- ✅ Performance is acceptable
- ✅ UI is responsive
- ✅ No crashes or error messages

---

**Remember**: Focus on visual verification, user experience, and real-world integration testing that cannot be automated!