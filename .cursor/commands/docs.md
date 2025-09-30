# Update Documentation and Versions

## Overview
Update all documentation, synchronize versions, and ensure consistency across all documentation files in the MHM project.

## Instructions for AI Assistant

### 1. **Execute Documentation Updates**
Run the complete documentation update sequence using PowerShell syntax:
```powershell
# Update function registry and module dependencies
python ai_development_tools/ai_tools_runner.py docs

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Documentation update failed" -ForegroundColor Red }
```

### 2. **Synchronize Versions**
```powershell
# Sync version numbers across all files
python ai_development_tools/ai_tools_runner.py version-sync all

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Version sync failed" -ForegroundColor Red }
```

### 3. **Generate Directory Trees**
```powershell
# Generate current directory structure
python ai_development_tools/ai_tools_runner.py trees

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Directory tree generation failed" -ForegroundColor Red }
```

### 4. **Verify Documentation Sync**
```powershell
# Verify documentation synchronization
python ai_development_tools/ai_tools_runner.py doc-sync

# Check exit code
if ($LASTEXITCODE -ne 0) { Write-Host "Documentation sync check failed" -ForegroundColor Red }
```

## Documentation Updates

### **Function Registry**
- Updates `ai_development_docs/AI_FUNCTION_REGISTRY.md`
- Analyzes all functions in the codebase
- Provides comprehensive function documentation
- Identifies missing or outdated function docs

### **Module Dependencies**
- Updates `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
- Maps relationships between modules
- Identifies dependency patterns
- Highlights circular dependencies

### **Version Synchronization**
- Updates version numbers across all documentation files
- Ensures consistency in version tracking
- Handles both manual and automatic version updates
- Maintains version history

### **Directory Trees**
- Generates `development_docs/DIRECTORY_TREE.md`
- Provides current project structure
- Helps with navigation and understanding
- Updates automatically with project changes

## Files Updated

### **AI Documentation Files**
- `ai_development_docs/AI_FUNCTION_REGISTRY.md`
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
- `ai_development_docs/AI_ARCHITECTURE.md`
- `ai_development_docs/AI_CHANGELOG.md`
- `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`
- `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`
- `ai_development_docs/AI_REFERENCE.md`
- `ai_development_docs/AI_SESSION_STARTER.md`

### **Development Documentation**
- `development_docs/DIRECTORY_TREE.md`
- `development_docs/CHANGELOG_DETAIL.md`
- `development_docs/FUNCTION_REGISTRY_DETAIL.md`
- `development_docs/MODULE_DEPENDENCIES_DETAIL.md`

### **Core Documentation** (Manual - Not Auto-Generated)
- `README.md` - Manual updates required
- `ARCHITECTURE.md` - Manual updates required  
- `DEVELOPMENT_WORKFLOW.md` - Manual updates required
- `DOCUMENTATION_GUIDE.md` - Manual updates required

### 5. **Analyze and Report Results**
**CRITICAL**: Always check these files for updates:
- `ai_development_docs/AI_FUNCTION_REGISTRY.md` - **Function documentation**
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md` - **Module relationships**
- `development_docs/DIRECTORY_TREE.md` - **Project structure**

### 6. **Provide Structured Report**
**ALWAYS provide this format in your response:**

#### **Documentation Updates**
- Function Registry: [Updated/No changes]
- Module Dependencies: [Updated/No changes]
- Directory Tree: [Generated/Updated]
- Version Sync: [Completed/Failed]

#### **Key Metrics**
- Functions Documented: [number]
- Modules Mapped: [number]
- Version Sync Status: [Success/Failed]
- Documentation Sync: [In sync/Issues found]

#### **Success Status**
- All Updates: [Completed/Failed]
- Version Sync: [Success/Failed]
- Documentation Sync: [In sync/Issues]
- Directory Tree: [Generated/Updated]

## Success Criteria
- All documentation files updated successfully
- Version numbers synchronized across files
- Directory trees generated correctly
- Documentation sync status verified
- No errors in the update process

## Output Files to Always Check
- `ai_development_docs/AI_FUNCTION_REGISTRY.md` - **Function documentation**
- `ai_development_docs/AI_MODULE_DEPENDENCIES.md` - **Module relationships**
- `development_docs/DIRECTORY_TREE.md` - **Project structure**