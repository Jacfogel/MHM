# Run Comprehensive System Audit

## Overview
Conduct a thorough analysis of the MHM codebase to identify issues, assess system health, and provide actionable insights for development.

## Instructions for AI Assistant

### 1. **Execute Fast Audit (Recommended)**
Run the fast audit suite using PowerShell syntax (skips test coverage for speed):
```powershell
# Run fast audit (~30 seconds)
python ai_development_tools/ai_tools_runner.py audit --fast

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red }
```

**For Full Audit (includes test coverage):**
```powershell
# Run full audit (~3-4 minutes)
python ai_development_tools/ai_tools_runner.py audit

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red }
```

### 2. **Run Additional Analysis Tools**
Execute supporting analysis tools:
```powershell
# Documentation sync check
python ai_development_tools/ai_tools_runner.py doc-sync

# Legacy code scan
python ai_development_tools/ai_tools_runner.py legacy

# Configuration validation
python ai_development_tools/ai_tools_runner.py config

# System status check
python ai_development_tools/ai_tools_runner.py status
```

### 3. **Analyze and Report Results**
**CRITICAL**: Always read and analyze these files:
- `ai_development_tools/consolidated_report.txt` - **Main summary**
- `ai_development_tools/critical_issues.txt` - **Priority issues**
- `ai_development_tools/ai_audit_detailed_results.json` - **Detailed data**

**Key Metrics to Extract and Report:**
- **Function Complexity**: Count by level (Moderate: 50-99, High: 100-199, Critical: 200+ nodes)
- **Documentation Coverage**: Current coverage percentage
- **Legacy Code**: Number of legacy references found
- **Test Coverage**: Current coverage percentages by module
- **Documentation Sync**: Number of sync issues found
- **System Health**: Overall status (Healthy/Issues/Critical)

### 4. **Provide Structured Report**
**ALWAYS provide this format in your response:**

#### **📊 System Overview**
- Total Functions: [number]
- Complexity Distribution: [Moderate: X, High: Y, Critical: Z]
- Documentation Coverage: [percentage]
- System Health: [Healthy/Issues/Critical]

#### **🚨 Critical Issues**
- [List top 3-5 critical issues from critical_issues.txt]
- [Include specific file paths and descriptions]

#### **📈 Key Metrics**
- Function Complexity: [distribution]
- Test Coverage: [percentage by module]
- Legacy References: [number found]
- Documentation Sync: [number of issues]

#### **🎯 Immediate Action Items**
1. [Priority 1 - from critical issues]
2. [Priority 2 - from critical issues]
3. [Priority 3 - from critical issues]

#### **📋 Next Steps**
- [Specific recommendations based on findings]
- [Suggested follow-up actions]
- [Timeline for addressing issues]

## Success Criteria
- All audit tools complete successfully
- Critical issues identified and prioritized
- Actionable recommendations provided
- System health status determined
- Next steps clearly defined

## Output Files to Always Check
- `ai_development_tools/consolidated_report.txt` - **Main summary**
- `ai_development_tools/critical_issues.txt` - **Priority issues**
- `ai_development_tools/ai_audit_detailed_results.json` - **Detailed data**
- `development_docs/LEGACY_REFERENCE_REPORT.md` - **Legacy cleanup**
- `ai_development_tools/AI_STATUS.md` - **System status**
- `ai_development_tools/AI_PRIORITIES.md` - **Action priorities**
