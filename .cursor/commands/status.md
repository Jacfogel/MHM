# Get Quick System Status

## Overview
Get a rapid overview of the current MHM system status, recent activity, and immediate action items without running comprehensive analysis.

## Instructions for AI Assistant

### 1. **Execute Status Check**
Run the quick status check using PowerShell syntax:
```powershell
# Get system status
python ai_development_tools/ai_tools_runner.py status

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Status check failed" -ForegroundColor Red }
```

### 2. **Test System Startup (Optional)**
If status check shows issues, test system startup:
```powershell
# Test system startup
python run_mhm.py

# Check if system starts properly
if ($LASTEXITCODE -ne 0) { Write-Host "System startup failed" -ForegroundColor Red }
```

### 3. **Analyze and Report Results**
**CRITICAL**: Always read and analyze these files:
- `ai_development_tools/AI_STATUS.md` - **Current status**
- `ai_development_tools/AI_PRIORITIES.md` - **Action priorities**

**Key Information to Extract and Report:**
- **System Health**: Overall status (Healthy/Issues/Critical)
- **Recent Activity**: Latest changes and modifications
- **Critical Issues**: High-priority problems
- **Action Items**: Immediate tasks to address

### 4. **Provide Structured Report**
**ALWAYS provide this format in your response:**

#### **⚡ System Status**
- Overall Health: [Healthy/Issues/Critical]
- Recent Activity: [summary of recent changes]
- Critical Issues: [number] issues found

#### **🚨 Critical Issues (if any)**
- [List any critical issues found]
- [Include specific descriptions]

#### **📋 Immediate Action Items**
1. [Priority 1 - if any]
2. [Priority 2 - if any]
3. [Priority 3 - if any]

#### **✅ System Health**
- Status: [Healthy/Issues/Critical]
- Startup Test: [Passed/Failed/Not tested]
- Recent Activity: [Normal/Unusual]

## Success Criteria
- System status retrieved successfully
- Critical issues identified (if any)
- System health status determined
- Action items prioritized (if any)

## Output Files to Always Check
- `ai_development_tools/AI_STATUS.md` - **Current status**
- `ai_development_tools/AI_PRIORITIES.md` - **Action priorities**