# Code Review Checklist

## Overview
Comprehensive checklist for conducting thorough code reviews to ensure quality, security, and maintainability of MHM codebase.

## Instructions for AI Assistant

### 1. **Follow Structured Review Process**
Use this systematic approach for all code reviews:

1. **Understand the change** - What problem does it solve?
2. **Check functionality** - Does it work as intended?
3. **Verify quality** - Is it maintainable and readable?
4. **Security check** - Are there any vulnerabilities?
5. **Test coverage** - Are changes properly tested?
6. **Documentation** - Is everything documented?
7. **MHM standards** - Does it follow project conventions?

### 2. **Use Comprehensive Checklist**
Review Categories

### Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled appropriately
- [ ] Error handling is comprehensive and appropriate
- [ ] No obvious bugs or logic errors
- [ ] Follows MHM error handling patterns
- [ ] Uses proper PowerShell syntax for any commands

### Code Quality
- [ ] Code is readable and well-structured
- [ ] Functions are small and focused (avoid high complexity)
- [ ] Variable names are descriptive and follow MHM conventions
- [ ] No code duplication
- [ ] Follows MHM project conventions
- [ ] Uses consistent logging patterns
- [ ] Follows `_main_function__helper_name` pattern for helper functions

### Security
- [ ] No obvious security vulnerabilities
- [ ] Input validation is present and appropriate
- [ ] Sensitive data is handled properly
- [ ] No hardcoded secrets or credentials
- [ ] User data is properly validated
- [ ] File operations are secure

### MHM-Specific Standards
- [ ] Follows MHM development workflow
- [ ] Updates documentation appropriately
- [ ] Maintains consistency with existing patterns
- [ ] Uses proper error handling decorators
- [ ] Follows user data handling patterns
- [ ] Maintains communication channel compatibility

### Testing
- [ ] Adequate test coverage for changes
- [ ] Tests cover edge cases and error conditions
- [ ] Tests use proper MHM test utilities
- [ ] No test pollution or side effects
- [ ] Tests are deterministic and reliable

### Documentation
- [ ] Changes are documented in CHANGELOG files
- [ ] Code comments explain complex logic
- [ ] Function docstrings are complete
- [ ] README updates if needed
- [ ] AI documentation is updated if relevant

## MHM Development Context
- **User Profile**: Beginner programmer with ADHD/depression
- **Environment**: Windows 11, PowerShell syntax required
- **Project**: Personal mental health assistant
- **Values**: Learning and efficiency over being right
- **Prefers**: Correction over inefficient approaches

### 3. **Provide Structured Review Report**
**ALWAYS provide this format in your response:**

#### **✅ Review Summary**
- Overall Quality: [Excellent/Good/Needs Improvement]
- Security Status: [Secure/Issues Found]
- MHM Standards: [Compliant/Issues Found]
- Documentation: [Complete/Needs Updates]

#### **🔍 Detailed Findings**
- **Functionality**: [Issues found or "No issues"]
- **Code Quality**: [Issues found or "No issues"]
- **Security**: [Issues found or "No issues"]
- **Testing**: [Issues found or "No issues"]
- **Documentation**: [Issues found or "No issues"]

#### **🎯 Action Items**
1. [Priority 1 - if any]
2. [Priority 2 - if any]
3. [Priority 3 - if any]

#### **✅ Approval Status**
- **Approved**: [Yes/No]
- **Blocking Issues**: [List any blocking issues]
- **Recommendations**: [Specific improvement suggestions]

## Common MHM Issues to Watch For
- Hardcoded paths (should use environment-specific paths)
- Missing error handling (use @handle_errors decorator)
- Inconsistent logging (use component loggers)
- Test pollution (use proper test isolation)
- Documentation drift (keep AI/human docs in sync)
- Legacy code patterns (should be clearly marked)
