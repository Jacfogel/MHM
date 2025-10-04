# Refactor Code Safely

## Overview
Plan and execute code refactoring with comprehensive safety checks, following MHM development standards and user preferences for clean, honest code.

## Steps

### 1. Pre-Refactoring Assessment
1. **If the audit hasn't been run this session - run audit to understand current state**:
   ```powershell
   python ai_development_tools/ai_tools_runner.py audit
   if ($LASTEXITCODE -ne 0) { Write-Host "Audit failed" -ForegroundColor Red; exit 1 }
   ```
2. **If tests haven't been run this session - test current system**:
   ```powershell
   python run_mhm.py
   if ($LASTEXITCODE -ne 0) { Write-Host "System not healthy" -ForegroundColor Red; exit 1 }
   ```
   **Note**: `run_mhm.py` launches the UI, not the background service. The background service must be started manually if needed.
3. **Create backup**:
   ```powershell
   Copy-Item -Path "." -Destination "../backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse
   if ($LASTEXITCODE -ne 0) { Write-Host "Backup failed" -ForegroundColor Red; exit 1 }
   ```

### 2. Refactoring Planning
1. **Identify refactoring scope**:
   - What specific code needs refactoring?
   - What are the current pain points?
   - What patterns need to be established/improved?
2. **Plan incremental changes**:
   - Break refactoring into small, testable steps
   - Identify all affected files and functions
   - Plan testing strategy for each step
3. **Consider legacy code**:
   - Question necessity: "Is this actually needed or just defensive programming?"
   - Mark any legacy compatibility with proper headers
   - Plan removal timeline for legacy code

### 3. Execute Refactoring
1. **Make one change at a time**
2. **Test after each change**:
   ```powershell
   python run_mhm.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Refactoring broke system" -ForegroundColor Red; exit 1 }
   ```
   **Note**: `run_mhm.py` launches the UI, not the background service. The background service must be started manually if needed.
3. **Update all references**:
   - Check all imports and function calls
   - Update documentation
   - Verify consistency across codebase
4. **Handle legacy code properly**:
   - Add `LEGACY COMPATIBILITY` comments where necessary
   - Log usage warnings for legacy paths
   - Document removal plans
   - **Update legacy cleanup tool**: Add new legacy patterns to `ai_development_tools/legacy_reference_cleanup.py`

### 4. Post-Refactoring Validation
1. **Run full test suite**:
   ```powershell
   python run_tests.py
   if ($LASTEXITCODE -ne 0) { Write-Host "Tests failed" -ForegroundColor Red; exit 1 }
   ```
2. **Verify system functionality**:
   ```powershell
   python run_mhm.py
   if ($LASTEXITCODE -ne 0) { Write-Host "System not working" -ForegroundColor Red; exit 1 }
   ```
   **Note**: `run_mhm.py` launches the UI, not the background service. The background service must be started manually if needed.
3. **Update documentation**:
   - Update any affected guides or READMEs

## Additional Guidance
- **Refactoring Patterns**: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` - Incremental refactoring approach
- **Error Handling**: `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` - Error handling patterns and recovery
- **Legacy Code Management**: `ai_development_tools/legacy_reference_cleanup.py` - Legacy pattern detection and cleanup
- **Code Quality**: `ai_development_docs/AI_REFERENCE.md` - Code analysis and troubleshooting patterns
- **Architecture**: `ai_development_docs/AI_ARCHITECTURE.md` - System architecture and design patterns
- **Safety First**: `.cursor/rules/critical.mdc` - Critical development rules and safety requirements

## Critical Rules

### **Safety First**
- **ALWAYS** test `python run_mhm.py` after changes
- **ALWAYS** create backup before starting
- **ALWAYS** make incremental changes
- **ALWAYS** update documentation

### **PowerShell Syntax**
- **ALWAYS** check exit codes: `$LASTEXITCODE` after commands
- **Use PowerShell syntax**: `;` for chaining, `-and`/`-or` for logic
- **Never assume success**: Check both exit codes and error patterns

### **Completeness and Consistency**
- **Identify ALL affected files and functions**
- **Update ALL relevant documentation**
- **Consider ALL edge cases and error conditions**
- **Test ALL affected functionality**
- **Maintain consistency with existing patterns**

### **Legacy Code Standards**
- **Question necessity**: "Is this actually needed or just defensive programming?"
- **Mark clearly**: Include `LEGACY COMPATIBILITY` headers and removal plans
- **Log usage**: Log warnings when legacy interfaces are accessed
- **Document removal**: Create clear removal plans with timelines
- **Update cleanup tool**: Add new legacy patterns to `ai_development_tools/legacy_reference_cleanup.py`

## Response Template

#### Refactoring Plan
- **Scope**: What code needs refactoring and why
- **Approach**: Incremental steps planned
- **Risk Assessment**: Potential issues and mitigation
- **Testing Strategy**: How each step will be validated

#### Execution Summary
- **Changes Made**: What was refactored
- **Files Modified**: Complete list of affected files
- **Patterns Established**: New patterns or improvements
- **Legacy Code Handled**: Any legacy compatibility added
- **Legacy Tool Updates**: New patterns added to `legacy_reference_cleanup.py`

#### Validation Results
- **System Health**: `python run_mhm.py` status
- **Test Results**: Test suite outcomes
- **Documentation Updates**: What was updated
- **Consistency Check**: Cross-reference validation

#### Follow-up Actions
- **Outstanding Work**: Any remaining tasks
- **Monitoring**: What to watch for
- **Next Steps**: Recommended follow-up actions
